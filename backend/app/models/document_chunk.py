"""
document_chunk.py — SQLAlchemy ORM model for the `document_chunks` table.

Each row represents one chunk produced by the hierarchical chunking pipeline.
Chunks are organised in a two-level hierarchy (parent / child) via the
self-referential `parent_chunk_id` foreign key.

Phase 5 additions:
  - `DocumentChunk` model with full hierarchical metadata
  - Self-referential FK for parent/child chunk relationships
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

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

    # ── Self-referential FK (parent chunk, nullable for root chunks) ──
    parent_chunk_id: Mapped[uuid.UUID | None] = mapped_column(
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
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_type: Mapped[str] = mapped_column(String(20), nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)

    # ── Timestamps ────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Relationships ─────────────────────────────────────────────
    document: Mapped["Document"] = relationship("Document")
    project: Mapped["Project"] = relationship("Project")

    # Self-referential: one parent chunk → many child chunks
    children: Mapped[list["DocumentChunk"]] = relationship(
        "DocumentChunk",
        back_populates="parent",
        foreign_keys=[parent_chunk_id],
    )
    parent: Mapped["DocumentChunk | None"] = relationship(
        "DocumentChunk",
        back_populates="children",
        remote_side=[id],
        foreign_keys=[parent_chunk_id],
    )

    # ── Explicit table-level indexes ──────────────────────────────
    # (document_id and project_id already have column-level index=True above;
    #  these named indexes make them easy to reference in migrations)
    __table_args__ = (
        Index("ix_document_chunks_document_id", "document_id"),
        Index("ix_document_chunks_project_id", "project_id"),
    )
