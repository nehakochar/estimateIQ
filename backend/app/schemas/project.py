"""
project.py — Pydantic schemas for Project create / list endpoints.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    """Request body for POST /projects."""

    name: str = Field(..., min_length=1, max_length=200, description="Project name")
    client_name: str | None = Field(
        None, max_length=200, description="Client or organisation name"
    )


class ProjectResponse(BaseModel):
    """Single project returned by the API."""

    id: uuid.UUID
    name: str
    client_name: str | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ProjectListResponse(BaseModel):
    """Paginated list of projects."""

    total: int
    projects: list[ProjectResponse]
