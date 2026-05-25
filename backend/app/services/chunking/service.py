"""
service.py — ChunkingService orchestrates the full hierarchical chunking pipeline.

This service is called by the Celery task.  It:
  1. Loads the Document from the database.
  2. Marks the document as "chunking".
  3. Concatenates parsed_content pages into full_text.
  4. Runs HeadingDetector → HierarchyBuilder → ChunkProducer.
  5. Bulk-inserts DocumentChunk rows.
  6. Writes a debug JSON snapshot via DebugWriter.
  7. Marks the document as "chunked".
  8. On any exception: marks "chunking_failed", logs the error, does NOT raise.

Why is this a service and not just code inside the Celery task?
  - Services are testable without Celery running.
  - The task file stays thin — it just calls this service.
  - Follows the same layered architecture as ProcessingService.
"""

from __future__ import annotations

import logging
import uuid

from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.chunking.chunk_producer import ChunkProducer, ChunkRecord
from app.services.chunking.debug_writer import DebugWriter
from app.services.chunking.heading_detector import HeadingDetector
from app.services.chunking.hierarchy_builder import HierarchyBuilder

logger = logging.getLogger(__name__)


class ChunkingService:
    """
    Runs the hierarchical chunking pipeline for a single document.

    Usage (inside a Celery task):
        service = ChunkingService(db)
        service.run(document_id="...", project_id="...")
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    # ── Public entry point ────────────────────────────────────────

    def run(self, document_id: str, project_id: str) -> None:
        """
        Execute the full chunking pipeline for one document.

        This method is designed to be called from a Celery task.
        It never raises — all errors are caught, logged, and written
        to the database so the API can report them.

        Args:
            document_id: UUID string of the Document row.
            project_id:  UUID string of the owning Project (used for chunk rows
                         and debug output).
        """
        logger.info(
            "ChunkingService.run: document=%s project=%s", document_id, project_id
        )

        # ── 1. Load Document from DB ──────────────────────────────
        document = self._load_document(document_id)
        if document is None:
            logger.error("ChunkingService: document %s not found in DB", document_id)
            return

        # ── 2. Guard: parsed_content must exist ───────────────────
        if document.parsed_content is None:
            logger.error(
                "ChunkingService: document %s has null parsed_content; "
                "cannot chunk",
                document_id,
            )
            document.upload_status = "chunking_failed"
            try:
                self.db.commit()
            except Exception:
                self.db.rollback()
            return

        # ── 3. Mark as "chunking" ─────────────────────────────────
        document.upload_status = "chunking"
        try:
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            logger.error(
                "ChunkingService: failed to mark 'chunking' for document %s: %s",
                document_id,
                exc,
            )
            # If we can't even mark the status, abort — nothing useful to do.
            return

        # ── 4–8. Main pipeline (wrapped in try/except) ────────────
        try:
            parsed_content: list[dict] = document.parsed_content

            # 4a. Concatenate page texts into full_text
            full_text: str = "".join(
                page["text"] for page in parsed_content
            )

            # 4b. Detect headings
            detector = HeadingDetector()
            headings = detector.detect(
                pages=parsed_content,
                file_name=document.file_name,
            )

            # 4c. Build hierarchy
            builder = HierarchyBuilder()
            root_nodes = builder.build(headings=headings, full_text=full_text)

            # 4d. Produce chunk records
            producer = ChunkProducer()
            chunks: list[ChunkRecord] = producer.produce(
                root_nodes=root_nodes,
                project_id=project_id,
                document_id=document_id,
            )

            # 5. Bulk-insert DocumentChunk rows
            #    We first create all ORM objects without parent_chunk_id so they
            #    get their UUIDs assigned, then resolve parent references by index.
            doc_uuid = uuid.UUID(document_id)
            proj_uuid = uuid.UUID(project_id)

            db_chunks: list[DocumentChunk] = [
                DocumentChunk(
                    document_id=doc_uuid,
                    project_id=proj_uuid,
                    parent_chunk_id=None,  # resolved below
                    chunk_index=chunk.chunk_index,
                    text=chunk.text,
                    section=chunk.section,
                    subsection=chunk.subsection,
                    level=chunk.level,
                    page_number=chunk.page_number,
                    chunk_type=chunk.chunk_type,
                    token_count=chunk.token_count,
                )
                for chunk in chunks
            ]

            # Resolve parent_chunk_id by looking up the parent's DB object
            # using the parent_chunk_index stored on each ChunkRecord.
            for i, chunk in enumerate(chunks):
                if chunk.parent_chunk_index is not None:
                    parent_db_chunk = db_chunks[chunk.parent_chunk_index]
                    db_chunks[i].parent_chunk_id = parent_db_chunk.id

            self.db.add_all(db_chunks)
            self.db.commit()

            logger.info(
                "ChunkingService: inserted %d chunks for document=%s",
                len(db_chunks),
                document_id,
            )

            # 6. Write debug snapshot (failures are non-fatal — DebugWriter
            #    catches its own exceptions internally)
            writer = DebugWriter()
            writer.write(
                chunks=chunks,
                project_id=project_id,
                document_id=document_id,
            )

            # 7. Mark as "chunked"
            document.upload_status = "chunked"
            self.db.commit()

            logger.info(
                "ChunkingService: completed document=%s chunks=%d",
                document_id,
                len(db_chunks),
            )

        except Exception as exc:
            # Roll back any partial DB writes from the pipeline.
            self.db.rollback()
            error_msg = str(exc)[:2000]
            logger.error(
                "ChunkingService: pipeline failed for document=%s: %s",
                document_id,
                error_msg,
            )
            # Best-effort status update — if this commit also fails, log and move on.
            try:
                document.upload_status = "chunking_failed"
                self.db.commit()
            except Exception as commit_exc:
                self.db.rollback()
                logger.error(
                    "ChunkingService: failed to mark 'chunking_failed' for "
                    "document=%s: %s",
                    document_id,
                    commit_exc,
                )
            # Do NOT re-raise — the Celery task handles retries at its own level.

    # ── Private helpers ───────────────────────────────────────────

    def _load_document(self, document_id: str) -> Document | None:
        """Fetch the Document row by UUID string."""
        try:
            uid = uuid.UUID(document_id)
        except ValueError:
            logger.error(
                "ChunkingService: invalid document_id UUID: %s", document_id
            )
            return None
        return self.db.get(Document, uid)
