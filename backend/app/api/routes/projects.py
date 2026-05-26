"""
projects.py — CRUD endpoints for the Project resource.

POST /projects        — create a new project (name + optional client_name)
GET  /projects        — list all projects, newest first
GET  /projects/{id}   — get a single project by UUID
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.project import Project
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
