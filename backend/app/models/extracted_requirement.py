"""
extracted_requirement.py — SQLAlchemy ORM model for the `extracted_requirements` table.

Each row is one structured requirement produced by the LLM extraction pipeline
(ExtractionService).  This table is separate from `semantic_chunks` — it stores
human-readable requirements with IDs (FR-01, NFR-02, etc.) rather than
embedding-ready text chunks.

The extraction pipeline runs in PARALLEL with the existing chunking pipeline.
Neither table modifies the other.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class ExtractedRequirement(Base):
    __tablename__ = "extracted_requirements"

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

    # ── Requirement fields ────────────────────────────────────────
    req_id: Mapped[str] = mapped_column(String(20), nullable=False)     # e.g. FR-01
    name: Mapped[str] = mapped_column(String(255), nullable=False)       # short label
    req_type: Mapped[str] = mapped_column(String(64), nullable=False)    # Functional, etc.
    description: Mapped[str] = mapped_column(Text, nullable=False)       # full description
    priority: Mapped[str] = mapped_column(String(64), nullable=False)    # Must Have, etc.
    section: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    page_number: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)

    # ── Timestamps ────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Relationships ─────────────────────────────────────────────
    document: Mapped["Document"] = relationship("Document")
    project: Mapped["Project"] = relationship("Project")

    # ── Indexes ───────────────────────────────────────────────────
    __table_args__ = (
        Index("ix_extracted_requirements_document_id", "document_id"),
        Index("ix_extracted_requirements_project_id", "project_id"),
        Index("ix_extracted_requirements_req_type", "req_type"),
    )
