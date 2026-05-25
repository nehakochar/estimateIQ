"""
upload.py — POST /upload route handler
=======================================
Accepts 1–10 RFP files (PDF, DOCX, XLSX) via multipart/form-data,
delegates all validation, storage, and DB persistence to UploadService,
and returns a structured per-file result summary.
"""

from fastapi import APIRouter, Depends, File, UploadFile
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
    db: Session = Depends(get_db),
) -> UploadResponse:
    """
    Upload one or more RFP documents.

    - Validates file count (1–10), types (.pdf/.docx/.xlsx), and sizes.
    - Creates a Project record and per-project storage directory.
    - Writes each file to disk with a UUID-based name.
    - Creates a Document record for every file (uploaded or failed).
    - Returns HTTP 200 with per-file results even if some files fail.
    - Returns HTTP 400 for validation failures, HTTP 500 for server errors.
    """
    # Read all file bytes up front so we can pass sizes to the validator
    # and avoid multiple async reads inside the service layer.
    contents: list[bytes] = [await f.read() for f in files]

    service = UploadService(db=db)
    return service.process_upload(files=files, contents=contents)
