"""
processing.py — Pydantic response schemas for processing jobs and documents.

These schemas define exactly what JSON shape the API returns.
They are separate from the SQLAlchemy models (which define DB tables).

Pydantic vs SQLAlchemy:
  - SQLAlchemy model  = maps to a database table row
  - Pydantic schema   = defines the JSON shape for API input/output
  They look similar but serve different purposes.

`model_config = ConfigDict(from_attributes=True)`:
  This tells Pydantic "you can create this schema from a SQLAlchemy
  model object by reading its attributes".  Without this, you'd have
  to manually convert every field.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


# ── ProcessingJob response ────────────────────────────────────────────────


class ProcessingJobResponse(BaseModel):
    """
    Response schema for GET /jobs/{job_id}.

    Returns the current state of a background processing job.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_id: uuid.UUID
    celery_task_id: str | None
    status: str          # "queued" | "processing" | "completed" | "failed"
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None


# ── Document response ─────────────────────────────────────────────────────


class DocumentResponse(BaseModel):
    """
    Response schema for GET /documents/{document_id}.

    Returns document metadata plus parsed content (if available).
    `parsed_content` is null until parsing completes successfully.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    file_name: str
    file_type: str
    file_size_bytes: int
    upload_status: str   # "uploaded" | "processing" | "parsed" | "failed"
    parsed_content: list[dict[str, Any]] | None
    created_at: datetime
