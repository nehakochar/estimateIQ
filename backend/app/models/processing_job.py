"""
processing_job.py — SQLAlchemy ORM model for the `processing_jobs` table.

What is a ProcessingJob?
  Every time a document enters the parsing pipeline, we create a
  ProcessingJob row.  It tracks:
    - which document is being processed
    - the current status (queued → processing → completed / failed)
    - the Celery task ID (so we can look up the task in Redis)
    - error details if something goes wrong
    - timestamps for when it started and finished

Why a separate table instead of just updating Document?
  - A document might be re-processed (e.g. after a bug fix).
  - We want a full audit trail of every processing attempt.
  - The job table is the "receipt" for background work.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    # ── Primary key ──────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ── Foreign key → documents table ────────────────────────────
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id"),
        nullable=False,
        index=True,
    )

    # ── Celery task ID ────────────────────────────────────────────
    # When Celery accepts a task it returns a unique task_id string.
    # We store it here so we can query Celery for the task's result
    # or cancel it if needed.
    # NULL until the task has been dispatched to Celery.
    celery_task_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, default=None
    )

    # ── Status ────────────────────────────────────────────────────
    # Lifecycle: queued → processing → completed
    #                               → failed
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="queued"
    )

    # ── Error details ─────────────────────────────────────────────
    # If status == "failed", this column holds the error message.
    # NULL on success.
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    # ── Timestamps ────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    # Set when the Celery task actually starts running
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    # Set when the task finishes (success or failure)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    # ── Relationships ─────────────────────────────────────────────
    document: Mapped["Document"] = relationship(
        "Document", back_populates="processing_jobs"
    )
