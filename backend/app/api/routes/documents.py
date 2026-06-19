"""
documents.py — Document endpoints.

GET /documents/{document_id}         — document metadata + parsed_content
GET /documents/{document_id}/status  — pipeline status for UI polling
GET /projects/{project_id}/status    — status of all documents in a project
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.document import Document
from app.models.project import Project
from app.schemas.processing import DocumentResponse
from app.schemas.status import DocumentStatusResponse, PipelineStage, ProjectStatusResponse

router = APIRouter(prefix="/documents", tags=["Documents"])

# Simplified 3-stage pipeline: Upload → Parse → Extract
_STAGE_ORDER = ["uploaded", "parsed", "extracted"]

_STAGE_LABELS = {
    "uploaded":  "Upload",
    "parsed":    "Parse",
    "extracted": "Extract",
}

_STAGE_DESCRIPTIONS = {
    "uploaded":  "File received and saved.",
    "parsed":    "Text extracted from document.",
    "extracted": "Requirements identified by AI.",
}

_STATUS_MESSAGES = {
    "uploaded":          "Document uploaded. Starting text extraction...",
    "processing":        "Reading and extracting text from document...",
    "parsed":            "Text extracted. Running AI requirement extraction...",
    "extracted":         "Requirements extracted. Ready to view.",
    "failed":            "Processing failed. Please re-upload the document.",
    "extraction_failed": "AI extraction failed. Check your LLM API key or switch provider.",
}

_STATUS_TO_IN_PROGRESS = {
    "uploaded":          None,
    "processing":        "parsed",
    "parsed":            "extracted",
    "extracted":         None,
    "failed":            None,
    "extraction_failed": None,
}

_STATUS_TO_COMPLETED_UP_TO = {
    "uploaded":          "uploaded",
    "processing":        "uploaded",
    "parsed":            "parsed",
    "extracted":         "extracted",
    "failed":            None,
    "extraction_failed": "parsed",
}


def _build_pipeline(status: str) -> list[PipelineStage]:
    completed_up_to = _STATUS_TO_COMPLETED_UP_TO.get(status)
    completed_idx = (
        _STAGE_ORDER.index(completed_up_to)
        if completed_up_to and completed_up_to in _STAGE_ORDER
        else -1
    )
    in_progress = _STATUS_TO_IN_PROGRESS.get(status)
    is_failed = status in ("failed", "extraction_failed")

    stages = []
    for i, name in enumerate(_STAGE_ORDER):
        if i <= completed_idx:
            s = "completed"
        elif name == in_progress:
            s = "failed" if is_failed else "in_progress"
        elif is_failed and name == "extracted" and status == "extraction_failed":
            s = "failed"
        else:
            s = "pending"
        stages.append(PipelineStage(
            name=name,
            label=_STAGE_LABELS[name],
            description=_STAGE_DESCRIPTIONS[name],
            status=s,
        ))
    return stages


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: str, db: Session = Depends(get_db)) -> DocumentResponse:
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid document_id: '{document_id}'.")
    document = db.get(Document, doc_uuid)
    if document is None:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found.")
    return DocumentResponse.model_validate(document)


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
def get_document_status(document_id: str, db: Session = Depends(get_db)) -> DocumentStatusResponse:
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid document_id: '{document_id}'.")
    document = db.get(Document, doc_uuid)
    if document is None:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found.")

    return DocumentStatusResponse(
        document_id=document.id,
        project_id=document.project_id,
        file_name=document.file_name,
        file_type=document.file_type,
        file_size_bytes=document.file_size_bytes,
        current_status=document.upload_status,
        status_message=_STATUS_MESSAGES.get(document.upload_status, "Processing..."),
        extraction_error=getattr(document, "extraction_error", None),
        is_ready=document.upload_status == "extracted",
        pipeline=_build_pipeline(document.upload_status),
        created_at=document.created_at,
    )


router_projects = APIRouter(prefix="/projects", tags=["Documents"])


@router_projects.get("/{project_id}/status", response_model=ProjectStatusResponse)
def get_project_status(project_id: str, db: Session = Depends(get_db)) -> ProjectStatusResponse:
    try:
        proj_uuid = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid project_id: '{project_id}'.")
    project = db.get(Project, proj_uuid)
    if project is None:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")

    documents = (
        db.query(Document)
        .filter(Document.project_id == proj_uuid)
        .order_by(Document.created_at)
        .all()
    )

    doc_statuses = [
        DocumentStatusResponse(
            document_id=doc.id,
            project_id=doc.project_id,
            file_name=doc.file_name,
            file_type=doc.file_type,
            file_size_bytes=doc.file_size_bytes,
            current_status=doc.upload_status,
            status_message=_STATUS_MESSAGES.get(doc.upload_status, "Processing..."),
            extraction_error=getattr(doc, "extraction_error", None),
            is_ready=doc.upload_status == "extracted",
            pipeline=_build_pipeline(doc.upload_status),
            created_at=doc.created_at,
        )
        for doc in documents
    ]

    ready_count = sum(1 for d in doc_statuses if d.is_ready)
    failed_count = sum(
        1 for d in doc_statuses
        if d.current_status in ("failed", "extraction_failed")
    )

    return ProjectStatusResponse(
        project_id=proj_uuid,
        total_documents=len(doc_statuses),
        ready_documents=ready_count,
        failed_documents=failed_count,
        is_ready=len(doc_statuses) > 0 and ready_count == len(doc_statuses),
        documents=doc_statuses,
    )
