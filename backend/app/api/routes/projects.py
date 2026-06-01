"""
projects.py — CRUD endpoints for the Project resource.

POST /projects        — create a new project (name + optional client_name)
GET  /projects        — list all projects, newest first
GET  /projects/{id}   — get a single project by UUID
POST /projects/{id}/reprocess — reset and re-run the pipeline for all documents
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.project import Project
from app.models.semantic_chunk import SemanticChunk
from app.schemas.project import ProjectCreate, ProjectListResponse, ProjectResponse

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=201,
    summary="Create a new project",
    description=(
        "Creates a new project with a name and optional client/organisation name. "
        "Returns the created project including its generated UUID and timestamp."
    ),
)
def create_project(
    body: ProjectCreate,
    db: Session = Depends(get_db),
) -> ProjectResponse:
    """
    Create a Project record.

    Args:
        body: ProjectCreate with name and optional client_name.
        db:   Database session (injected by FastAPI).

    Returns:
        The newly created ProjectResponse.

    Raises:
        HTTP 500: if the database insert fails.
    """
    project = Project(
        name=body.name.strip(),
        client_name=body.client_name.strip() if body.client_name else None,
    )
    try:
        db.add(project)
        db.commit()
        db.refresh(project)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create project: {exc}"[:500],
        ) from exc

    return ProjectResponse.model_validate(project)


@router.get(
    "",
    response_model=ProjectListResponse,
    summary="List all projects",
    description=(
        "Returns all projects ordered by creation date (newest first). "
        "Includes id, name, client_name, status, and created_at for each project."
    ),
)
def list_projects(
    db: Session = Depends(get_db),
) -> ProjectListResponse:
    """
    Fetch all Project rows, newest first.

    Args:
        db: Database session (injected by FastAPI).

    Returns:
        ProjectListResponse with total count and list of projects.
    """
    projects = (
        db.query(Project)
        .order_by(Project.created_at.desc())
        .all()
    )
    return ProjectListResponse(
        total=len(projects),
        projects=[ProjectResponse.model_validate(p) for p in projects],
    )


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get a project by ID",
    description="Returns a single project by its UUID.",
)
def get_project(
    project_id: str,
    db: Session = Depends(get_db),
) -> ProjectResponse:
    """
    Fetch a single Project by UUID.

    Args:
        project_id: UUID string of the project.
        db:         Database session (injected by FastAPI).

    Returns:
        ProjectResponse.

    Raises:
        HTTP 400: if project_id is not a valid UUID.
        HTTP 404: if no project with that ID exists.
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

    return ProjectResponse.model_validate(project)


@router.post(
    "/{project_id}/reprocess",
    summary="Re-process all documents in a project",
    description=(
        "Clears all existing chunks and embeddings for every document in the project, "
        "resets their status to 'parsed', and re-triggers the chunking → classification "
        "→ embedding pipeline. Use this after pipeline fixes to re-process existing documents."
    ),
)
def reprocess_project(
    project_id: str,
    db: Session = Depends(get_db),
) -> dict:
    """
    Reset and re-run the pipeline for all documents in a project.

    Steps:
      1. Validate project exists.
      2. For each document in the project:
         a. Delete all SemanticChunk rows.
         b. Delete all DocumentChunk rows.
         c. Reset upload_status to "parsed" (keeps parsed_content intact).
      3. Dispatch chunk_document Celery task for each document.

    Args:
        project_id: UUID string of the project.
        db:         Database session (injected by FastAPI).

    Returns:
        Dict with project_id and count of documents queued.

    Raises:
        HTTP 400: if project_id is not a valid UUID or project not found.
        HTTP 500: if database operations fail.
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

    # Load all documents for this project that have been parsed
    documents = (
        db.query(Document)
        .filter(
            Document.project_id == proj_uuid,
            Document.parsed_content.isnot(None),  # only re-process parsed docs
        )
        .all()
    )

    if not documents:
        return {
            "project_id": project_id,
            "queued": 0,
            "message": "No parsed documents found to re-process.",
        }

    try:
        queued = 0
        for doc in documents:
            doc_uuid = doc.id

            # Delete semantic chunks (embeddings) first — FK dependency
            db.query(SemanticChunk).filter(
                SemanticChunk.document_id == doc_uuid
            ).delete(synchronize_session=False)

            # Delete hierarchical chunks
            db.query(DocumentChunk).filter(
                DocumentChunk.document_id == doc_uuid
            ).delete(synchronize_session=False)

            # Reset status to "parsed" so chunking pipeline re-runs
            doc.upload_status = "parsed"
            queued += 1

        db.commit()

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset documents: {str(exc)[:500]}",
        ) from exc

    # Dispatch Celery tasks after DB is clean
    from app.tasks.chunking_tasks import chunk_document
    for doc in documents:
        chunk_document.delay(
            document_id=str(doc.id),
            project_id=project_id,
        )

    return {
        "project_id": project_id,
        "queued": queued,
        "message": f"Re-processing started for {queued} document(s). "
                   "Monitor status via GET /projects/{project_id}/status.",
    }
