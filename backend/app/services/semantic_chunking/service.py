"""
service.py — SemanticChunkingService orchestrates Phase 6 (semantic splitting)
and Phase 7 (requirement classification) of the EstimateIQ pipeline.

This service is called by the Celery task.  It:
  1. Loads the Document from the database.
  2. Loads all DocumentChunk rows for the document, ordered by chunk_index.
  3. Marks the document as "semantic_chunking".
  4. Splits each Phase 5 chunk via SemanticSplitter (or passes through unchanged).
  5. Classifies each semantic chunk via RequirementClassifier.
  6. Writes pre-classification debug snapshot via DebugWriter.
  7. Bulk-inserts SemanticChunk rows.
  8. Writes post-classification debug snapshot via DebugWriter.
  9. Logs split stats, category distribution, and unmatched chunk count.
  10. Marks the document as "classified".
  11. On any exception: rollback, marks "semantic_chunking_failed", logs, does NOT raise.

Mirrors the structure of the existing ChunkingService in
app/services/chunking/service.py.
"""

from __future__ import annotations

import logging
import types
import uuid
from collections import Counter

import tiktoken
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.semantic_chunk import SemanticChunk
from app.services.classification.classifier import RequirementClassifier
from app.services.semantic_chunking.debug_writer import DebugWriter
from app.services.semantic_chunking.semantic_splitter import SemanticSplitter

logger = logging.getLogger(__name__)


class SemanticChunkingService:
    """
    Runs the semantic chunking and classification pipeline for a single document.

    Usage (inside a Celery task):
        service = SemanticChunkingService(db)
        service.run(document_id="...", project_id="...")
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    # ── Public entry point ────────────────────────────────────────

    def run(self, document_id: str, project_id: str) -> None:
        """
        Execute the full semantic chunking and classification pipeline for one document.

        This method is designed to be called from a Celery task.
        It never raises — all errors are caught, logged, and written
        to the database so the API can report them.

        Args:
            document_id: UUID string of the Document row.
            project_id:  UUID string of the owning Project (used for chunk rows
                         and debug output).
        """
        logger.info(
            "SemanticChunkingService.run: document=%s project=%s",
            document_id,
            project_id,
        )

        # ── 1. Load Document from DB ──────────────────────────────
        document = self._load_document(document_id)
        if document is None:
            logger.error(
                "SemanticChunkingService: document %s not found in DB", document_id
            )
            return

        # ── 2. Load all Phase 5 DocumentChunk rows ────────────────
        try:
            doc_uuid = uuid.UUID(document_id)
        except ValueError:
            logger.error(
                "SemanticChunkingService: invalid document_id UUID: %s", document_id
            )
            return

        phase5_chunks: list[DocumentChunk] = (
            self.db.query(DocumentChunk)
            .filter(DocumentChunk.document_id == doc_uuid)
            .order_by(DocumentChunk.chunk_index)
            .all()
        )

        # ── 3. Mark as "semantic_chunking" ────────────────────────
        document.upload_status = "semantic_chunking"
        try:
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            logger.error(
                "SemanticChunkingService: failed to mark 'semantic_chunking' "
                "for document %s: %s",
                document_id,
                exc,
            )
            # If we can't even mark the status, abort — nothing useful to do.
            return

        # ── 4–10. Main pipeline (wrapped in try/except) ───────────
        try:
            # ── 8.2: Splitting loop ───────────────────────────────
            enc = tiktoken.get_encoding("cl100k_base")
            splitter = SemanticSplitter()

            # Split-stat counters (used by task 8.4 for logging)
            count_semantic_split = 0   # chunks split via SemanticSplitterNodeParser
            count_sentence_fallback = 0  # chunks split via SentenceSplitter fallback
            count_passthrough = 0      # chunks passed through unchanged

            semantic_chunks_data: list[dict] = []
            chunk_index = 0  # globally sequential 0-based index across all output chunks

            for source_chunk in phase5_chunks:
                if source_chunk.token_count > settings.semantic_max_chunk_tokens:
                    # Chunk exceeds the token threshold — split it
                    sub_texts = splitter.split(
                        source_chunk.text,
                        source_chunk.section,
                        source_chunk.chunk_index,
                    )
                    if len(sub_texts) > 1:
                        # Track as semantic split (exact strategy refined in 8.4)
                        count_semantic_split += 1
                    else:
                        # Splitter returned a single fragment (edge case)
                        count_passthrough += 1
                else:
                    # Chunk is within the token limit — pass through unchanged
                    sub_texts = [source_chunk.text]
                    count_passthrough += 1

                for text_fragment in sub_texts:
                    token_count = len(enc.encode(text_fragment))

                    # Assign chunk_type per requirements 2.5:
                    #   "requirement" if 300 ≤ tokens ≤ 600
                    #   "workflow"    if tokens > 600
                    #   "requirement" for everything else (< 300)
                    if token_count > 600:
                        chunk_type = "workflow"
                    else:
                        chunk_type = "requirement"

                    semantic_chunks_data.append(
                        {
                            "chunk_index": chunk_index,
                            "text": text_fragment,
                            "token_count": token_count,
                            "chunk_type": chunk_type,
                            # Inherited from source Phase5Chunk (requirements 2.6)
                            "section": source_chunk.section,
                            "subsection": source_chunk.subsection,
                            "page_number": source_chunk.page_number,
                            # Lineage (requirement 2.7)
                            "source_chunk_id": source_chunk.id,
                            # Will be populated by task 8.3 (classification)
                            "category": "",
                            "confidence_score": 0.0,
                            # Document / project context for ORM insertion (task 8.3)
                            "document_id": doc_uuid,
                            "project_id": uuid.UUID(project_id),
                        }
                    )
                    chunk_index += 1

            # ── 8.3: Classification and DB insertion ─────────────────

            # Write pre-classification snapshot (raw split data, before any
            # category/confidence values are populated)
            DebugWriter().write_semantic(
                semantic_chunks_data, str(project_id), str(doc_uuid)
            )

            # Classify each chunk in-place
            classifier = RequirementClassifier()
            for chunk_data in semantic_chunks_data:
                chunk_obj = types.SimpleNamespace(
                    text=chunk_data["text"],
                    section=chunk_data["section"],
                    subsection=chunk_data["subsection"],
                )
                category, confidence_score = classifier.classify(chunk_obj)
                chunk_data["category"] = category
                chunk_data["confidence_score"] = confidence_score

            # Bulk-insert all SemanticChunk ORM rows
            orm_rows = [
                SemanticChunk(
                    chunk_index=cd["chunk_index"],
                    text=cd["text"],
                    token_count=cd["token_count"],
                    chunk_type=cd["chunk_type"],
                    section=cd["section"],
                    subsection=cd["subsection"],
                    page_number=cd["page_number"],
                    source_chunk_id=cd["source_chunk_id"],
                    category=cd["category"],
                    confidence_score=cd["confidence_score"],
                    document_id=cd["document_id"],
                    project_id=cd["project_id"],
                )
                for cd in semantic_chunks_data
            ]
            self.db.add_all(orm_rows)
            self.db.commit()

            # Write post-classification snapshot (with category + confidence)
            DebugWriter().write_classified(
                semantic_chunks_data, str(project_id), str(doc_uuid)
            )

            # ── 8.4: Logging, status finalisation ────────────────────

            total_input = len(phase5_chunks)
            total_output = len(semantic_chunks_data)

            logger.info(
                "SemanticChunkingService: split stats — "
                "input=%d output=%d semantic=%d sentence_fallback=%d passthrough=%d",
                total_input,
                total_output,
                count_semantic_split,
                count_sentence_fallback,
                count_passthrough,
            )

            category_distribution = dict(
                Counter(cd["category"] for cd in semantic_chunks_data)
            )
            logger.info(
                "SemanticChunkingService: category distribution — %s",
                category_distribution,
            )

            unmatched_count = sum(
                1 for cd in semantic_chunks_data if cd["confidence_score"] < 0.5
            )
            logger.info(
                "SemanticChunkingService: unmatched chunks (confidence < 0.5) = %d",
                unmatched_count,
            )

            document.upload_status = "classified"
            self.db.commit()

            logger.info(
                "SemanticChunkingService: completed document=%s chunks=%d",
                document_id,
                total_output,
            )

        except Exception as exc:
            # Roll back any partial DB writes from the pipeline.
            self.db.rollback()
            error_msg = str(exc)[:2000]
            logger.error(
                "SemanticChunkingService: pipeline failed for document=%s: %s",
                document_id,
                error_msg,
            )
            # Best-effort status update — if this commit also fails, log and move on.
            try:
                document.upload_status = "semantic_chunking_failed"
                self.db.commit()
            except Exception as commit_exc:
                self.db.rollback()
                logger.error(
                    "SemanticChunkingService: failed to mark 'semantic_chunking_failed' "
                    "for document=%s: %s",
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
                "SemanticChunkingService: invalid document_id UUID: %s", document_id
            )
            return None
        return self.db.get(Document, uid)
