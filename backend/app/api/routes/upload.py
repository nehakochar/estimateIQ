"""
upload.py — POST /upload route handler
=======================================
Accepts 1–10 RFP files (PDF, DOCX, XLSX) via multipart/form-data,
delegates all validation, storage, and DB persistence to UploadService,
and returns a structured per-file result summary.
"""

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.upload import UploadResponse
from app.services.upload_service import UploadService

router = APIRouter(prefix="/upload", tags=["Upload"])


@router.post(
    "",
    response_model=UploadResponse,
    summary="Upload RFP documents",
    description=(
        "Upload between 1 and 10 RFP-related documents (PDF, DOCX, or XLSX). "
        "Each file is validated for type and size, stored on disk under a "
        "unique project directory, and recorded in the database. "
        "Returns a project ID and a per-file status summary. "
        "Individual file failures do not abort the entire batch — the response "
        "reports which files succeeded and which failed."
    ),
)
async def upload_rfp(
    files: list[UploadFile] = File(..., description="One or more RFP files to upload"),
    project_name: str = Form(default="", description="Optional name for this upload batch"),
    project_id: str = Form(default="", description="Optional existing project UUID"),
    db: Session = Depends(get_db),
) -> UploadResponse:
    contents: list[bytes] = [await f.read() for f in files]
    service = UploadService(db=db)
    return service.process_upload(
        files=files,
        contents=contents,
        project_name=project_name.strip(),
        project_id=project_id.strip() if project_id else None,
    )
