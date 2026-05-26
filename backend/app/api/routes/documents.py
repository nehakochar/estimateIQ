"""
documents.py — Route handlers for /documents endpoints.

GET /documents/{document_id}
  Returns document metadata and parsed content.

GET /documents/{document_id}/status
  Returns a lightweight pipeline progress view — purpose-built for UI polling.
  Shows each pipeline stage (uploaded → parsed → chunked → classified → embedded)
  with its individual status. Does NOT return heavy data like parsed_content.

GET /documents/{document_id}/chunks
  Returns all hierarchical chunks for a document ordered by chunk_index.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.schemas.chunking import ChunkResponse, DocumentChunksResponse
from app.schemas.processing import DocumentResponse
from app.schemas.status import DocumentStatusResponse, PipelineStage, ProjectStatusResponse
from app.models.project import Project

router = APIRouter(prefix="/documents", tags=["Documents"])


# ── Pipeline stage builder ────────────────────────────────────────────────

# Maps each upload_status value to which stages are complete
_STAGE_ORDER = ["uploaded", "parsed", "chunked", "classified", "embedded"]

_STAGE_LABELS = {
    "uploaded":   "Upload",
    "parsed":     "Parse",
    "chunked":    "Chunk",
    "classified": "Classify",
    "embedded":   "Embed",
}

# Human-readable description for each stage shown below the label
_STAGE_DESCRIPTIONS = {
    "uploaded":   "File received and saved securely.",
    "parsed":     "Extracting text and structure from the document.",
    "chunked":    "Breaking the document into sections and paragraphs.",
    "classified": "Identifying requirement types (functional, security, UI/UX, etc.).",
    "embedded":   "Generating AI vectors so the document can be searched semantically.",
}

# Human-readable message for the overall current status
_STATUS_MESSAGES = {
    "uploaded":   "Document uploaded. Starting processing...",
    "processing": "Reading and extracting text from the document...",
    "parsed":     "Text extracted. Breaking document into chunks...",
    "chunked":    "Chunking complete. Classifying requirements...",
    "classified": "Requirements classified. Generating search vectors...",
    "embedding":  "Generating AI search vectors. This may take a few minutes...",
    "embedded":   "Document is ready. You can now search and query this RFP.",
    "failed":     "Processing failed. Please try re-uploading the document.",
}

# Maps DB status values to which named stage is currently in progress
_STATUS_TO_IN_PROGRESS_STAGE = {
    "uploaded":   None,        # just uploaded, nothing in progress yet
    "processing": "parsed",    # parsing in progress
    "parsed":     "chunked",   # chunking in progress
    "chunked":    "classified", # semantic chunking in progress
    "classified": "embedded",  # embedding in progress
    "embedding":  "embedded",  # embedding in progress
    "embedded":   None,        # all done
    "failed":     None,        # failed somewhere
}


def _build_pipeline(current_status: str) -> list[PipelineStage]:
    """
    Build the ordered list of pipeline stages with their individual status.

    Rules:
    - Stages before the current one are 'completed'
    - The current active stage is 'in_progress'
    - Stages after are 'pending'
    - If status is 'failed', the in-progress stage becomes 'failed'
    """
    in_progress_stage = _STATUS_TO_IN_PROGRESS_STAGE.get(current_status)
    is_failed = current_status == "failed"

    # Determine how far we've gotten
    # Map DB status to the last completed stage name
    _STATUS_TO_COMPLETED_UP_TO = {
        "uploaded":   "uploaded",
        "processing": "uploaded",
        "parsed":     "parsed",
        "chunked":    "chunked",
        "classified": "classified",
        "embedding":  "classified",
        "embedded":   "embedded",
        "failed":     None,
    }
    completed_up_to = _STATUS_TO_COMPLETED_UP_TO.get(current_status)
    completed_index = (
        _STAGE_ORDER.index(completed_up_to)
        if completed_up_to and completed_up_to in _STAGE_ORDER
        else -1
    )

    stages = []
    for i, stage_name in enumerate(_STAGE_ORDER):
        if i <= completed_index:
            stage_status = "completed"
        elif stage_name == in_progress_stage:
            stage_status = "failed" if is_failed else "in_progress"
        else:
            stage_status = "pending"

        stages.append(PipelineStage(
            name=stage_name,
            label=_STAGE_LABELS[stage_name],
            description=_STAGE_DESCRIPTIONS[stage_name],
            status=stage_status,
        ))

    return stages


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get document details and parsed content",
    description=(
        "Returns metadata and parsed text content for a document. "
        "`parsed_content` is null until parsing completes. "
        "Each element in `parsed_content` has a `page` number and `text` field."
    ),
)
def get_document(
    document_id: str,
    db: Session = Depends(get_db),
) -> DocumentResponse:
    """
    Fetch a Document by its UUID.

    Args:
        document_id: UUID string of the document.
        db:          Database session (injected by FastAPI).

    Returns:
        DocumentResponse with metadata and parsed_content.

    Raises:
        HTTP 404: if no document with that ID exists.
        HTTP 400: if document_id is not a valid UUID.
    """
    # Validate UUID format
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid document ID format: '{document_id}'. Must be a UUID.",
        )

    document = db.get(Document, doc_uuid)
    if document is None:
        raise HTTPException(
            status_code=404,
            detail=f"Document '{document_id}' not found.",
        )

    return DocumentResponse.model_validate(document)


@router.get(
    "/{document_id}/status",
    response_model=DocumentStatusResponse,
    summary="Get document pipeline status",
    description=(
        "Returns a lightweight pipeline progress view for a document. "
        "Purpose-built for UI polling — shows each stage (Upload, Parse, Chunk, "
        "Classify, Embed) with its individual status. "
        "Poll this every few seconds after upload to track progress. "
        "When `is_ready` is true, the document is fully searchable."
    ),
)
def get_document_status(
    document_id: str,
    db: Session = Depends(get_db),
) -> DocumentStatusResponse:
    """
    Get pipeline progress for a document — lightweight, UI-friendly.

    Args:
        document_id: UUID string of the document.
        db:          Database session (injected by FastAPI).

    Returns:
        DocumentStatusResponse with pipeline stages and is_ready flag.

    Raises:
        HTTP 404: if no document with that ID exists.
        HTTP 400: if document_id is not a valid UUID.
    """
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid document ID format: '{document_id}'. Must be a UUID.",
        )

    document = db.get(Document, doc_uuid)
    if document is None:
        raise HTTPException(
            status_code=404,
            detail=f"Document '{document_id}' not found.",
        )

    return DocumentStatusResponse(
        document_id=document.id,
        project_id=document.project_id,
        file_name=document.file_name,
        file_type=document.file_type,
        file_size_bytes=document.file_size_bytes,
        current_status=document.upload_status,
        status_message=_STATUS_MESSAGES.get(document.upload_status, "Processing..."),
        is_ready=document.upload_status == "embedded",
        pipeline=_build_pipeline(document.upload_status),
        created_at=document.created_at,
    )


@router.get(
    "/{document_id}/chunks",
    response_model=DocumentChunksResponse,
    summary="Get chunks for a document",
    description=(
        "Returns all hierarchical chunks for a document ordered by chunk_index. "
        "Returns an empty list if the document has not been chunked yet."
    ),
)
def get_document_chunks(
    document_id: str,
    db: Session = Depends(get_db),
) -> DocumentChunksResponse:
    """
    Fetch all DocumentChunk rows for a document, ordered by chunk_index.

    Args:
        document_id: UUID string of the document.
        db:          Database session (injected by FastAPI).

    Returns:
        DocumentChunksResponse with document_id, total_chunks, and chunks list.

    Raises:
        HTTP 400: if document_id is not a valid UUID.
        HTTP 404: if no document with that ID exists.
    """
    # Validate UUID format
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid document ID format: '{document_id}'. Must be a UUID.",
        )

    # Verify the document exists
    document = db.get(Document, doc_uuid)
    if document is None:
        raise HTTPException(
            status_code=404,
            detail=f"Document '{document_id}' not found.",
        )

    # Query all chunks for this document ordered by chunk_index
    chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == doc_uuid)
        .order_by(DocumentChunk.chunk_index)
        .all()
    )

    return DocumentChunksResponse(
        document_id=document_id,
        total_chunks=len(chunks),
        chunks=[ChunkResponse.model_validate(c) for c in chunks],
    )


# ── Project-level status ──────────────────────────────────────────────────

router_projects = APIRouter(prefix="/projects", tags=["Documents"])


@router_projects.get(
    "/{project_id}/status",
    response_model=ProjectStatusResponse,
    summary="Get pipeline status for all documents in a project",
    description=(
        "Returns the pipeline status of every document in a project. "
        "Useful for showing an overall project progress view in the UI. "
        "`is_ready` is true only when ALL documents are fully embedded and searchable."
    ),
)
def get_project_status(
    project_id: str,
    db: Session = Depends(get_db),
) -> ProjectStatusResponse:
    """
    Get pipeline status for all documents in a project.

    Args:
        project_id: UUID string of the project.
        db:         Database session (injected by FastAPI).

    Returns:
        ProjectStatusResponse with per-document status and overall is_ready flag.

    Raises:
        HTTP 404: if no project with that ID exists.
        HTTP 400: if project_id is not a valid UUID.
    """
    try:
        proj_uuid = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid project ID format: '{project_id}'. Must be a UUID.",
        )

    project = db.get(Project, proj_uuid)
    if project is None:
        raise HTTPException(
            status_code=404,
            detail=f"Project '{project_id}' not found.",
        )

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
            is_ready=doc.upload_status == "embedded",
            pipeline=_build_pipeline(doc.upload_status),
            created_at=doc.created_at,
        )
        for doc in documents
    ]

    ready_count = sum(1 for d in doc_statuses if d.is_ready)
    failed_count = sum(1 for d in doc_statuses if d.current_status == "failed")

    return ProjectStatusResponse(
        project_id=proj_uuid,
        total_documents=len(doc_statuses),
        ready_documents=ready_count,
        failed_documents=failed_count,
        is_ready=len(doc_statuses) > 0 and ready_count == len(doc_statuses),
        documents=doc_statuses,
    )
