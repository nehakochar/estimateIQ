"""
service.py — SemanticChunkingService orchestrates Phase 6 (semantic splitting)
and Phase 7 (requirement classification) of the EstimateIQ pipeline.

This service is called by the Celery task.  It:
  1. Loads the Document from the database.
  2. Loads all DocumentChunk rows for the document, ordered by chunk_index.
  3. Marks the document as "semantic_chunking".
  4. Splits each Phase 5 chunk via SentenceSplitter (or passes through unchanged).
  5. Classifies each semantic chunk via RequirementClassifier.
  6. Writes pre-classification debug snapshot via DebugWriter.
  7. Bulk-inserts SemanticChunk rows.
  8. Writes post-classification debug snapshot via DebugWriter.
  9. Logs split stats, category distribution, and unmatched chunk count.
  10. Marks the document as "classified".
  11. On any exception: rollback, marks "semantic_chunking_failed", logs, does NOT raise.
"""

from __future__ import annotations

import logging
import types
import uuid
from collections import Counter

import tiktoken
from llama_index.core import Document as LlamaDocument
from llama_index.core.node_parser import SentenceSplitter
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.semantic_chunk import SemanticChunk
from app.services.classification.classifier import RequirementClassifier
from app.services.semantic_chunking.debug_writer import DebugWriter

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

    def run(self, document_id: str, project_id: str) -> None:
        """
        Execute the full semantic chunking and classification pipeline for one document.
        """
        logger.info(
            "SemanticChunkingService.run: document=%s project=%s",
            document_id,
            project_id,
        )

        document = self._load_document(document_id)
        if document is None:
            logger.error(
                "SemanticChunkingService: document %s not found in DB", document_id
            )
            return

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
            return

        try:
            enc = tiktoken.get_encoding("cl100k_base")

            count_semantic_split = 0
            count_passthrough = 0

            semantic_chunks_data: list[dict] = []
            chunk_index = 0

            for source_chunk in phase5_chunks:
                if source_chunk.token_count > settings.semantic_max_chunk_tokens:
                    # Chunk exceeds the token threshold — split with SentenceSplitter
                    splitter = SentenceSplitter(
                        chunk_size=settings.semantic_max_chunk_tokens,
                        chunk_overlap=64,
                    )
                    doc = LlamaDocument(text=source_chunk.text)
                    nodes = splitter.get_nodes_from_documents([doc])
                    sub_texts = [n.get_content() for n in nodes if n.get_content().strip()]
                    if not sub_texts:
                        sub_texts = [source_chunk.text]
                    if len(sub_texts) > 1:
                        count_semantic_split += 1
                    else:
                        count_passthrough += 1
                else:
                    # Chunk is within the token limit — pass through unchanged
                    sub_texts = [source_chunk.text]
                    count_passthrough += 1

                for text_fragment in sub_texts:
                    token_count = len(enc.encode(text_fragment))

                    # All chunks are requirements — no workflow type
                    chunk_type = "requirement"

                    semantic_chunks_data.append(
                        {
                            "chunk_index": chunk_index,
                            "text": text_fragment,
                            "token_count": token_count,
                            "chunk_type": chunk_type,
                            "section": source_chunk.section,
                            "subsection": source_chunk.subsection,
                            "page_number": source_chunk.page_number,
                            "source_chunk_id": source_chunk.id,
                            "category": "",
                            "confidence_score": 0.0,
                            "document_id": doc_uuid,
                            "project_id": uuid.UUID(project_id),
                        }
                    )
                    chunk_index += 1

            # Write pre-classification snapshot
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

            # Write post-classification snapshot
            DebugWriter().write_classified(
                semantic_chunks_data, str(project_id), str(doc_uuid)
            )

            total_input = len(phase5_chunks)
            total_output = len(semantic_chunks_data)

            logger.info(
                "SemanticChunkingService: split stats — "
                "input=%d output=%d split=%d passthrough=%d",
                total_input,
                total_output,
                count_semantic_split,
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
            self.db.rollback()
            error_msg = str(exc)[:2000]
            logger.error(
                "SemanticChunkingService: pipeline failed for document=%s: %s",
                document_id,
                error_msg,
            )
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
