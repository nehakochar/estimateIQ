"""
extraction.py — Pydantic schemas for the requirement extraction API.

Response shapes mirror the table format shown in the requirements panel:
    ID | Requirement | Type | Description | Priority | Section
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ExtractedRequirementItem(BaseModel):
    """Single extracted requirement row."""

    id: str = Field(description="Row UUID")
    req_id: str = Field(description="Requirement ID, e.g. FR-01")
    name: str = Field(description="Short 2-5 word label")
    req_type: str = Field(description="Requirement type: Functional, Technical, etc.")
    description: str = Field(description="Full requirement description")
    priority: str = Field(description="Must Have | Should Have | Nice to Have | Not Specified")
    section: str = Field(description="Source section heading in document")
    page_number: int = Field(description="Source page number")
    confidence: float = Field(description="Extraction confidence 0.0-1.0")

    model_config = {"from_attributes": True}


class DocumentRequirementsResponse(BaseModel):
    """Response for GET /documents/{document_id}/requirements."""

    document_id: str
    project_id: str
    total_requirements: int
    requirements: list[ExtractedRequirementItem]


class ProjectRequirementsResponse(BaseModel):
    """Response for GET /projects/{project_id}/requirements."""

    project_id: str
    total_requirements: int
    total_documents: int
    requirements: list[ExtractedRequirementItem]


class RequirementsSummaryResponse(BaseModel):
    """Response for GET /documents/{document_id}/requirements/summary."""

    document_id: str
    total_requirements: int
    by_type: dict[str, int] = Field(description="Count per req_type")
    by_priority: dict[str, int] = Field(description="Count per priority")
