"""
requirements.py — API routes for extracted requirements and estimation.

Endpoints:
    GET  /documents/{document_id}/requirements
    GET  /documents/{document_id}/requirements/summary
    GET  /projects/{project_id}/requirements
    POST /documents/{document_id}/requirements/reextract
    POST /projects/{project_id}/estimates/generate
    GET  /projects/{project_id}/estimates
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.document import Document
from app.models.extracted_requirement import ExtractedRequirement
from app.models.requirement_estimate import RequirementEstimate
from app.schemas.extraction import (
    DocumentRequirementsResponse,
    ExtractedRequirementItem,
    ProjectRequirementsResponse,
    RequirementsSummaryResponse,
)
from app.schemas.estimation import ProjectEstimatesResponse
from app.tasks.estimation_tasks import generate_estimates_task


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

# ── Estimation Endpoints ─────────────────────────────────────────────────────
# (imports for estimation are at the top of this file)

@router.post(
    "/projects/{project_id}/estimates/generate",
    summary="Generate estimates for all requirements in a project",
    description="Queues a Celery task to generate sub-feature estimates for each requirement.",
)
def generate_project_estimates(project_id: str, db: Session = Depends(get_db)) -> dict:
    try:
        proj_uuid = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project_id")

    # Idempotency guard — don't queue a second task if already generating/completed
    docs = db.query(Document).filter(Document.project_id == proj_uuid).all()
    if not docs:
        raise HTTPException(status_code=404, detail="Project not found or has no documents")

    statuses = {d.estimation_status for d in docs}
    if "generating" in statuses:
        return {"project_id": project_id, "status": "already_generating"}

    # Collect requirement IDs (only from extracted documents)
    req_ids = [
        str(r.id)
        for r in db.query(ExtractedRequirement.id)
        .filter(ExtractedRequirement.project_id == proj_uuid)
        .all()
    ]
    if not req_ids:
        raise HTTPException(status_code=400, detail="No extracted requirements found for this project")

    # Mark all documents as generating before queuing
    for doc in docs:
        doc.estimation_status = "generating"
    db.commit()

    generate_estimates_task.delay(req_ids, project_id)
    return {"project_id": project_id, "status": "generating"}


@router.get(
    "/projects/{project_id}/estimates",
    response_model=ProjectEstimatesResponse,
    summary="Get estimation results for a project",
)
def get_project_estimates(project_id: str, db: Session = Depends(get_db)) -> ProjectEstimatesResponse:
    try:
        proj_uuid = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project_id")

    # Determine status: if ANY document is still generating, report generating.
    # Fall back to not_started if no documents exist.
    docs = db.query(Document).filter(Document.project_id == proj_uuid).all()
    if not docs:
        estimation_status = "not_started"
    else:
        statuses = {d.estimation_status for d in docs}
        if "generating" in statuses:
            estimation_status = "generating"
        elif "failed" in statuses:
            estimation_status = "failed"
        elif statuses == {"completed"}:
            estimation_status = "completed"
        else:
            estimation_status = "not_started"

    # Fetch sub-features and group by requirement
    estimates = db.query(RequirementEstimate).filter(RequirementEstimate.project_id == proj_uuid).all()

    req_map: dict[uuid.UUID, dict] = {}
    for est in estimates:
        rid = est.requirement_id
        if rid not in req_map:
            req = db.get(ExtractedRequirement, rid)
            if req is None:
                continue  # orphaned estimate — skip
            req_map[rid] = {
                "requirement_id": rid,
                "req_id": req.req_id,
                "name": req.name,
                "req_type": req.req_type,
                "description": req.description,
                "sub_features": [],
                "subtotal_frontend": 0.0,
                "subtotal_backend": 0.0,
                "subtotal_mobile": 0.0,
                "subtotal_total": 0.0,
            }
        group = req_map[rid]
        sf = {
            "id": est.id,
            "sub_feature_name": est.sub_feature_name,
            "description": est.description,
            "frontend_hours": est.frontend_hours,
            "backend_hours": est.backend_hours,
            "mobile_hours": est.mobile_hours,
            "complexity": est.complexity,
            "assumptions": est.assumptions,
        }
        group["sub_features"].append(sf)
        group["subtotal_frontend"] += est.frontend_hours
        group["subtotal_backend"] += est.backend_hours
        group["subtotal_mobile"] += est.mobile_hours
        group["subtotal_total"] += est.frontend_hours + est.backend_hours + est.mobile_hours

    total_fe = sum(g["subtotal_frontend"] for g in req_map.values())
    total_be = sum(g["subtotal_backend"] for g in req_map.values())
    total_mob = sum(g["subtotal_mobile"] for g in req_map.values())
    grand_total = sum(g["subtotal_total"] for g in req_map.values())

    return ProjectEstimatesResponse(
        project_id=proj_uuid,
        estimation_status=estimation_status,
        total_frontend_hours=total_fe,
        total_backend_hours=total_be,
        total_mobile_hours=total_mob,
        grand_total_hours=grand_total,
        requirements=list(req_map.values()),
    )

