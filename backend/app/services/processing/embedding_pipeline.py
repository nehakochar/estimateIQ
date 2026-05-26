"""
embedding_pipeline.py — EmbeddingPipeline orchestrates Phase 8 of the EstimateIQ
pipeline: embedding classified requirement chunks and storing them in Qdrant.

Responsibilities:
  1. Validate inputs (project_id must be non-empty).
  2. Ensure the Qdrant collection exists before any batch work.
  3. DB mode (json_path=None):
       - Load the Document row and mark upload_status = "embedding".
       - Query all SemanticChunk rows where chunk_type = "requirement",
         ordered by chunk_index.
  4. Standalone mode (json_path provided):
       - Load chunks from a JSON file on disk.
       - Filter to chunk_type = "requirement".
       - Skip all document-status DB writes.
  5. Process chunks in batches of settings.embedding_batch_size:
       - Call EmbeddingService.embed() to produce 384-dim vectors.
       - Assign a fresh uuid4 as the Qdrant point ID for each chunk.
       - Build PointStruct objects with the required 9-field payload.
       - Call QdrantService.upsert_points() to persist vectors.
       - On success (DB mode): set embedding_status = "embedded" and
         vector_id on each chunk; commit.
       - On batch failure: set embedding_status = "failed" for all chunks
         in the batch; commit; log; continue.
  6. After all batches:
       - Write the debug snapshot via DebugWriter.write_embedded().
       - Log a summary line.
  7. DB mode finalisation:
       - If any chunk was successfully embedded, set upload_status = "embedded".
       - On unhandled exception: set upload_status = "embedding_failed",
         rollback, then commit the status update.

Mirrors the structure of app/services/semantic_chunking/service.py.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document
from app.models.semantic_chunk import SemanticChunk
from app.services.embeddings.debug_writer import DebugWriter
from app.services.embeddings.embedding_service import EmbeddingService
from app.services.vector.qdrant_service import QdrantService
from qdrant_client.models import PointStruct

logger = logging.getLogger(__name__)


class EmbeddingPipeline:
    """Orchestrates the full embedding lifecycle for a single document.

    Usage (inside a Celery task or standalone script)::

        pipeline = EmbeddingPipeline(db=db)
        pipeline.run(document_id="...", project_id="...")

    Standalone (no DB required for chunk loading)::

        pipeline = EmbeddingPipeline(db=db)
        pipeline.run(document_id="...", project_id="...", json_path="/path/to/chunks.json")
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        # Let exceptions propagate — caller (EmbeddingTask) handles them.
        self._embedding_service = EmbeddingService()
        self._qdrant_service = QdrantService()

    # ── Public entry point ────────────────────────────────────────

    def run(
        self,
        document_id: str,
        project_id: str,
        json_path: str | None = None,
    ) -> None:
        """Execute the full embedding pipeline for one document.

        Args:
            document_id: UUID string of the Document row.
            project_id:  UUID string of the owning Project.  Required and
                         must be non-empty — raises ``ValueError`` otherwise.
            json_path:   Optional path to a JSON file of pre-classified chunks.
                         When provided the pipeline runs in standalone mode and
                         skips all document-status DB writes.
        """
        # ── Req 10.3: Validate project_id ────────────────────────
        if not project_id:
            raise ValueError("project_id is required and cannot be empty")

        logger.info(
            "EmbeddingPipeline.run: document=%s project=%s standalone=%s",
            document_id,
            project_id,
            json_path is not None,
        )

        # ── Req 5.11: Ensure Qdrant collection exists once ────────
        self._qdrant_service.ensure_collection()

        standalone = json_path is not None

        # ── Load chunks (DB mode or standalone mode) ──────────────
        if standalone:
            chunks = self._load_chunks_from_json(json_path)  # type: ignore[arg-type]
        else:
            chunks, document = self._load_chunks_from_db(document_id)
            if chunks is None:
                # Document not found — already logged inside helper.
                return
            # document is guaranteed non-None when chunks is not None.

        # ── Req 5.2: No qualifying chunks ────────────────────────
        if not chunks:
            logger.info(
                "EmbeddingPipeline: no requirement chunks found for document=%s",
                document_id,
            )
            return

        # ── Batch processing ──────────────────────────────────────
        batch_size = settings.embedding_batch_size
        success_count = 0
        failure_count = 0
        batch_number = 0
        chunk_results: list[dict] = []
        start_time = time.time()

        try:
            for batch_start in range(0, len(chunks), batch_size):
                batch = chunks[batch_start : batch_start + batch_size]
                batch_number += 1

                # Extract texts — dict in standalone mode, ORM object in DB mode.
                if standalone:
                    texts = [chunk["text"] for chunk in batch]
                else:
                    texts = [chunk.text for chunk in batch]

                try:
                    # ── Req 5.4: Embed the batch ──────────────────
                    vectors = self._embedding_service.embed(texts)

                    points: list[PointStruct] = []
                    point_ids: list[uuid.UUID] = []

                    for chunk, vector in zip(batch, vectors):
                        # ── Req 5.5: Assign a fresh UUID per point ─
                        point_id = uuid.uuid4()
                        point_ids.append(point_id)

                        # ── Req 10.1, 10.2: Build payload ─────────
                        if standalone:
                            payload = {
                                "project_id": str(project_id),
                                "document_id": str(document_id),
                                "section": chunk.get("section", ""),
                                "subsection": chunk.get("subsection", ""),
                                "category": chunk.get("category", ""),
                                "chunk_type": chunk.get("chunk_type", ""),
                                "page_number": chunk.get("page_number", 0),
                                "confidence_score": chunk.get("confidence_score", 0.0),
                                "text": chunk.get("text", ""),
                            }
                        else:
                            payload = {
                                "project_id": str(project_id),
                                "document_id": str(document_id),
                                "section": chunk.section,
                                "subsection": chunk.subsection,
                                "category": chunk.category,
                                "chunk_type": chunk.chunk_type,
                                "page_number": chunk.page_number,
                                "confidence_score": chunk.confidence_score,
                                "text": chunk.text,
                            }

                        # ── Req 5.5: Construct PointStruct ────────
                        points.append(
                            PointStruct(
                                id=str(point_id),
                                vector=vector,
                                payload=payload,
                            )
                        )

                    # ── Req 5.6: Upsert batch to Qdrant ──────────
                    self._qdrant_service.upsert_points(points)

                    # ── Req 5.7, 2.4: Update DB on success ────────
                    if not standalone:
                        for chunk, point_id in zip(batch, point_ids):
                            chunk.embedding_status = "embedded"
                            chunk.vector_id = point_id
                        self.db.commit()

                    # Track results for debug output
                    for chunk, point_id, payload in zip(batch, point_ids, [p.payload for p in points]):
                        success_count += 1
                        result = dict(payload)
                        result["point_id"] = str(point_id)
                        result["status"] = "embedded"
                        chunk_results.append(result)

                except Exception as batch_exc:
                    # ── Req 5.8, 2.5: Mark batch as failed ────────
                    if not standalone:
                        for chunk in batch:
                            chunk.embedding_status = "failed"
                        self.db.commit()

                    logger.error(
                        "EmbeddingPipeline: batch %d failed for document=%s: %s",
                        batch_number,
                        document_id,
                        batch_exc,
                    )

                    for chunk in batch:
                        failure_count += 1
                        if standalone:
                            text_val = chunk.get("text", "")
                        else:
                            text_val = chunk.text
                        chunk_results.append(
                            {
                                "document_id": str(document_id),
                                "project_id": str(project_id),
                                "text": text_val,
                                "status": "failed",
                                "error": str(batch_exc),
                            }
                        )
                    # Continue to next batch
                    continue

            # ── Req 5.9: Write debug snapshot ─────────────────────
            DebugWriter().write_embedded(chunk_results, project_id, document_id)

            # ── Req 5.10: Log summary ─────────────────────────────
            elapsed = time.time() - start_time
            logger.info(
                "EmbeddingPipeline: completed — total=%d embedded=%d failed=%d "
                "batches=%d elapsed=%.2fs",
                len(chunks),
                success_count,
                failure_count,
                batch_number,
                elapsed,
            )

            # ── Req 9.2: Finalise document status (DB mode) ───────
            if not standalone and success_count > 0:
                document.upload_status = "embedded"
                self.db.commit()

        except Exception as exc:
            # ── Req 9.3: Unhandled exception — mark as failed ─────
            if not standalone:
                self.db.rollback()
                logger.error(
                    "EmbeddingPipeline: unhandled exception for document=%s: %s",
                    document_id,
                    exc,
                )
                try:
                    document.upload_status = "embedding_failed"
                    self.db.commit()
                except Exception as commit_exc:
                    self.db.rollback()
                    logger.error(
                        "EmbeddingPipeline: failed to mark 'embedding_failed' "
                        "for document=%s: %s",
                        document_id,
                        commit_exc,
                    )
            raise

    # ── Private helpers ───────────────────────────────────────────

    def _load_chunks_from_db(
        self, document_id: str
    ) -> tuple[list[SemanticChunk] | None, Document | None]:
        """Load the Document and its requirement SemanticChunk rows from the DB.

        Returns ``(None, None)`` if the document is not found so the caller
        can return early without error.

        Also sets ``document.upload_status = "embedding"`` and commits before
        returning the chunk list (Req 9.1).
        """
        doc_uuid = uuid.UUID(document_id)
        document: Document | None = self.db.get(Document, doc_uuid)

        if document is None:
            logger.info(
                "EmbeddingPipeline: document %s not found in DB — skipping",
                document_id,
            )
            return None, None

        # ── Req 9.1: Mark as "embedding" ─────────────────────────
        document.upload_status = "embedding"
        self.db.commit()

        # ── Req 5.1: Query requirement chunks ────────────────────
        chunks: list[SemanticChunk] = (
            self.db.query(SemanticChunk)
            .filter(
                SemanticChunk.document_id == doc_uuid,
                SemanticChunk.chunk_type == "requirement",
            )
            .order_by(SemanticChunk.chunk_index)
            .all()
        )

        return chunks, document

    def _load_chunks_from_json(self, json_path: str) -> list[dict]:
        """Load and filter chunks from a JSON file (standalone mode).

        Raises:
            ValueError: If the file does not exist or cannot be parsed as JSON.
        """
        path = Path(json_path)

        # ── Req 6.5: Raise descriptive ValueError on missing/bad file ──
        if not path.exists():
            raise ValueError(
                f"EmbeddingPipeline: JSON file not found at path '{json_path}'"
            )

        try:
            with open(path, encoding="utf-8") as f:
                records: list[dict] = json.load(f)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"EmbeddingPipeline: failed to parse JSON file '{json_path}': {exc}"
            ) from exc

        # ── Req 6.3: Filter to requirement chunks only ────────────
        return [r for r in records if r.get("chunk_type") == "requirement"]
