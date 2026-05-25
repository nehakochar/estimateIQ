"""
document.py — SQLAlchemy ORM model for the `documents` table.

Each row represents one uploaded file that belongs to a Project.

Phase 3 additions:
  - `parsed_content`  : stores the extracted text as a JSON array
                        e.g. [{"page": 1, "text": "..."}, ...]
  - `upload_status`   : now also accepts "processing" and "parsed"
                        (was only "uploaded" / "failed" in Phase 2)
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Document(Base):
    __tablename__ = "documents"

    # ── Primary key ──────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ── Foreign key → projects table ─────────────────────────────
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True
    )

    # ── File metadata ─────────────────────────────────────────────
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_type: Mapped[str] = mapped_column(
        String(10), nullable=False
    )  # "pdf", "docx", "xlsx"
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)

    # ── Status ────────────────────────────────────────────────────
    # Lifecycle: uploaded → processing → parsed
    #                                  → failed
    upload_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="uploaded"
    )

    # ── Parsed content (Phase 3) ──────────────────────────────────
    # Stores a JSON array of page/section objects after parsing.
    # Example value:
    #   [{"page": 1, "text": "Introduction..."}, {"page": 2, "text": "..."}]
    # NULL until the document has been successfully parsed.
    parsed_content: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSON, nullable=True, default=None
    )

    # ── Timestamps ────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Relationships ─────────────────────────────────────────────
    # String reference avoids circular import with project.py
    project: Mapped["Project"] = relationship("Project", back_populates="documents")

    # One document can have many processing jobs (retries, re-runs)
    processing_jobs: Mapped[list["ProcessingJob"]] = relationship(
        "ProcessingJob", back_populates="document", cascade="all, delete-orphan"
    )
