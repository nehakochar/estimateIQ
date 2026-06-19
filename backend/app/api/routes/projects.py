"""
projects.py — CRUD endpoints for the Project resource.

POST /projects         — create project
GET  /projects         — list all projects
GET  /projects/{id}    — get single project
POST /projects/{id}/reextract — re-trigger LLM extraction for all documents
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.document import Document
from app.models.extracted_requirement import ExtractedRequirement
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectListResponse, ProjectResponse

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("", response_model=ProjectResponse, status_code=201)
def create_project(body: ProjectCreate, db: Session = Depends(get_db)) -> ProjectResponse:
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
        raise HTTPException(status_code=500, detail=f"Failed to create project: {exc}"[:500])
    return ProjectResponse.model_validate(project)


@router.get("", response_model=ProjectListResponse)
def list_projects(db: Session = Depends(get_db)) -> ProjectListResponse:
    projects = db.query(Project).order_by(Project.created_at.desc()).all()
    return ProjectListResponse(
        total=len(projects),
        projects=[ProjectResponse.model_validate(p) for p in projects],
    )


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str, db: Session = Depends(get_db)) -> ProjectResponse:
    try:
        proj_uuid = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid project_id: '{project_id}'.")
    project = db.get(Project, proj_uuid)
    if project is None:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")
    return ProjectResponse.model_validate(project)


@router.post("/{project_id}/reextract", summary="Re-trigger LLM extraction for all documents")
def reextract_project(project_id: str, db: Session = Depends(get_db)) -> dict:
    """
    Clears existing extracted_requirements for every document in the project
    and re-queues the LLM extraction task. Use this after updating provider keys
    or after fixing issues.
    """
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
        .all()
    )

    if not documents:
        return {"project_id": project_id, "queued": 0, "message": "No documents found."}

    queued = 0
    from app.tasks.extraction_tasks import extract_requirements_task

    for doc in documents:
        if not doc.stored_path:
            continue
        # Clear old extraction results
        db.query(ExtractedRequirement).filter(
            ExtractedRequirement.document_id == doc.id
        ).delete(synchronize_session=False)
        queued += 1

    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"DB error: {str(exc)[:500]}")

    for doc in documents:
        if not doc.stored_path:
            continue
        extract_requirements_task.delay(
            document_id=str(doc.id),
            project_id=project_id,
        )

    return {
        "project_id": project_id,
        "queued": queued,
        "message": f"Extraction re-queued for {queued} document(s).",
    }
