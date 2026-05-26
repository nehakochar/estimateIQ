"""
status.py — Pydantic schemas for pipeline status responses.

These schemas are purpose-built for UI polling — they give a clear,
structured view of where a document is in the processing pipeline
without returning heavy data like parsed_content or chunk text.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PipelineStage(BaseModel):
    """Represents a single stage in the processing pipeline."""

    name: str = Field(description="Stage name")
    label: str = Field(description="Human-readable label for UI display")
    status: str = Field(description="'pending' | 'in_progress' | 'completed' | 'failed'")
    description: str = Field(description="What this stage does — shown below the stage label in the UI")


class DocumentStatusResponse(BaseModel):
    """
    Response schema for GET /documents/{document_id}/status.

    Purpose-built for UI polling — shows exactly where the document
    is in the pipeline without returning heavy data.
    """

    model_config = ConfigDict(from_attributes=True)

    document_id: uuid.UUID = Field(description="UUID of the document")
    project_id: uuid.UUID = Field(description="UUID of the project")
    file_name: str = Field(description="Original filename")
    file_type: str = Field(description="File type: pdf, docx, xlsx")
    file_size_bytes: int = Field(description="File size in bytes")

    # Current status — the raw value from the DB
    current_status: str = Field(
        description=(
            "Current pipeline status: uploaded | processing | parsed | "
            "chunked | classified | embedding | embedded | failed"
        )
    )

    # Human-readable message describing what's happening right now
    status_message: str = Field(
        description="Human-readable message about the current state — suitable for UI display"
    )

    # Whether the document is fully ready for search
    is_ready: bool = Field(
        description="True when status is 'embedded' and document is searchable"
    )

    # Ordered list of pipeline stages with their individual status
    pipeline: list[PipelineStage] = Field(
        description="Ordered pipeline stages showing progress"
    )

    created_at: datetime = Field(description="When the document was uploaded")


class ProjectStatusResponse(BaseModel):
    """
    Response schema for GET /projects/{project_id}/status.

    Shows the status of all documents in a project — useful for
    displaying an overall project progress view in the UI.
    """

    project_id: uuid.UUID = Field(description="UUID of the project")
    total_documents: int = Field(description="Total number of documents in project")
    ready_documents: int = Field(description="Number of documents fully embedded and searchable")
    failed_documents: int = Field(description="Number of documents that failed processing")
    is_ready: bool = Field(description="True when all documents are embedded")
    documents: list[DocumentStatusResponse] = Field(
        description="Status of each document in the project"
    )
