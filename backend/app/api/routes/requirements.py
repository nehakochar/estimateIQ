"""
requirements.py — API routes for extracted requirements.

Endpoints:
    GET  /documents/{document_id}/requirements
         Returns all extracted requirements for a document.
         Supports optional ?req_type= and ?priority= filters.

    GET  /documents/{document_id}/requirements/summary
         Returns count breakdown by type and priority (no full text).

    GET  /projects/{project_id}/requirements
         Returns all extracted requirements across all documents in a project.
         Supports optional ?req_type= filter.

    POST /documents/{document_id}/requirements/reextract
         Triggers a fresh extraction run for a document (re-queues Celery task).
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.document import Document
from app.models.extracted_requirement import ExtractedRequirement
from app.schemas.extraction import (
    DocumentRequirementsResponse,
    ExtractedRequirementItem,
    ProjectRequirementsResponse,
    RequirementsSummaryResponse,
)

router = APIRouter(tags=["Requirements"])

_VALID_TYPES = {
    "Functional",
    "Non-Functional",
    "Technical",
    "Security",
    "Integration",
    "Compliance",
    "Infrastructure",
    "Support",
}

_VALID_PRIORITIES = {"Must Have", "Should Have", "Nice to Have", "Not Specified"}


# ── GET /documents/{document_id}/requirements ────────────────────────────────

@router.get(
    "/documents/{document_id}/requirements",
    response_model=DocumentRequirementsResponse,
    summary="Get extracted requirements for a document",
    description=(
        "Returns all LLM-extracted requirements for a document, ordered by req_id. "
        "Filter by req_type or priority via query params."
    ),
)
def get_document_requirements(
    document_id: str,
    req_type: Optional[str] = None,
    priority: Optional[str] = None,
    db: Session = Depends(get_db),
) -> DocumentRequirementsResponse:
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid document_id format: '{document_id}'.",
        )

    document = db.get(Document, doc_uuid)
    if document is None:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found.")

    if req_type and req_type not in _VALID_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid req_type '{req_type}'. Valid: {sorted(_VALID_TYPES)}",
        )

    query = db.query(ExtractedRequirement).filter(
        ExtractedRequirement.document_id == doc_uuid
    )
    if req_type:
        query = query.filter(ExtractedRequirement.req_type == req_type)
    if priority:
        query = query.filter(ExtractedRequirement.priority == priority)

    rows = query.order_by(ExtractedRequirement.req_id).all()

    return DocumentRequirementsResponse(
        document_id=document_id,
        project_id=str(document.project_id),
        total_requirements=len(rows),
        requirements=[
            ExtractedRequirementItem(
                id=str(r.id),
                req_id=r.req_id,
                name=r.name,
                req_type=r.req_type,
                description=r.description,
                priority=r.priority,
                section=r.section,
                page_number=r.page_number,
                confidence=r.confidence,
            )
            for r in rows
        ],
    )


# ── GET /documents/{document_id}/requirements/summary ────────────────────────

@router.get(
    "/documents/{document_id}/requirements/summary",
    response_model=RequirementsSummaryResponse,
    summary="Get requirement counts by type and priority",
)
def get_document_requirements_summary(
    document_id: str,
    db: Session = Depends(get_db),
) -> RequirementsSummaryResponse:
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid document_id: '{document_id}'.")

    document = db.get(Document, doc_uuid)
    if document is None:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found.")

    rows = (
        db.query(ExtractedRequirement)
        .filter(ExtractedRequirement.document_id == doc_uuid)
        .all()
    )

    by_type: dict[str, int] = {}
    by_priority: dict[str, int] = {}
    for r in rows:
        by_type[r.req_type] = by_type.get(r.req_type, 0) + 1
        by_priority[r.priority] = by_priority.get(r.priority, 0) + 1

    return RequirementsSummaryResponse(
        document_id=document_id,
        total_requirements=len(rows),
        by_type=by_type,
        by_priority=by_priority,
    )


# ── GET /projects/{project_id}/requirements ──────────────────────────────────

@router.get(
    "/projects/{project_id}/requirements",
    response_model=ProjectRequirementsResponse,
    summary="Get all requirements across a project",
    description=(
        "Returns all extracted requirements across every document in the project. "
        "Filter by req_type via query param."
    ),
)
def get_project_requirements(
    project_id: str,
    req_type: Optional[str] = None,
    db: Session = Depends(get_db),
) -> ProjectRequirementsResponse:
    try:
        proj_uuid = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid project_id: '{project_id}'.")

    if req_type and req_type not in _VALID_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid req_type '{req_type}'. Valid: {sorted(_VALID_TYPES)}",
        )

    query = db.query(ExtractedRequirement).filter(
        ExtractedRequirement.project_id == proj_uuid
    )
    if req_type:
        query = query.filter(ExtractedRequirement.req_type == req_type)

    rows = query.order_by(
        ExtractedRequirement.document_id,
        ExtractedRequirement.req_id,
    ).all()

    # Count distinct documents
    doc_ids = {str(r.document_id) for r in rows}

    return ProjectRequirementsResponse(
        project_id=project_id,
        total_requirements=len(rows),
        total_documents=len(doc_ids),
        requirements=[
            ExtractedRequirementItem(
                id=str(r.id),
                req_id=r.req_id,
                name=r.name,
                req_type=r.req_type,
                description=r.description,
                priority=r.priority,
                section=r.section,
                page_number=r.page_number,
                confidence=r.confidence,
            )
            for r in rows
        ],
    )


# ── POST /documents/{document_id}/requirements/reextract ─────────────────────

@router.post(
    "/documents/{document_id}/requirements/reextract",
    summary="Re-trigger extraction for a document",
    description="Re-queues the LLM extraction Celery task for the document.",
)
def reextract_document(
    document_id: str,
    db: Session = Depends(get_db),
) -> dict:
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid document_id: '{document_id}'.")

    document = db.get(Document, doc_uuid)
    if document is None:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found.")

    if not document.parsed_content:
        raise HTTPException(
            status_code=400,
            detail="Document has not been parsed yet. Run parsing first.",
        )

    from app.tasks.extraction_tasks import extract_requirements_task
    extract_requirements_task.delay(
        document_id=str(document.id),
        project_id=str(document.project_id),
    )

    return {
        "document_id": document_id,
        "status": "extraction_queued",
        "message": "Extraction task queued successfully.",
    }
