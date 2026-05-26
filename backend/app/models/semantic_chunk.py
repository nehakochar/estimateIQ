"""
semantic_chunk.py — SQLAlchemy ORM model for the `semantic_chunks` table.

Each row represents one semantically-split and classified chunk produced by
the Phase 6 / Phase 7 pipeline.  Chunks are derived from `DocumentChunk`
rows (Phase 5) and carry a classification category plus a confidence score.

Phase 6 / 7 additions:
  - `SemanticChunk` model with classification metadata
  - Optional FK back to the source `DocumentChunk` via `source_chunk_id`
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class SemanticChunk(Base):
    __tablename__ = "semantic_chunks"

    # ── Primary key ──────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ── Foreign key → documents table ────────────────────────────
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False
    )

    # ── Foreign key → projects table ─────────────────────────────
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False
    )

    # ── Optional FK → source DocumentChunk (nullable for standalone chunks) ──
    source_chunk_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_chunks.id"),
        nullable=True,
        default=None,
    )

    # ── Chunk position & content ──────────────────────────────────
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)

    # ── Hierarchical metadata ─────────────────────────────────────
    section: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    subsection: Mapped[str] = mapped_column(String(512), nullable=False, default="")

    # ── Classification metadata ───────────────────────────────────
    category: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    chunk_type: Mapped[str] = mapped_column(String(20), nullable=False)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)

    # ── Timestamps ────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Relationships ─────────────────────────────────────────────
    document: Mapped["Document"] = relationship("Document")
    project: Mapped["Project"] = relationship("Project")
    source_chunk: Mapped["DocumentChunk | None"] = relationship("DocumentChunk")

    # ── Explicit table-level indexes ──────────────────────────────
    __table_args__ = (
        Index("ix_semantic_chunks_document_id", "document_id"),
        Index("ix_semantic_chunks_project_id", "project_id"),
    )
