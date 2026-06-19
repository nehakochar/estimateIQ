"""
jobs.py — GET /jobs/{job_id} route handler.

Returns the current status of a background processing job.

Why is this useful?
  After uploading files, the client gets a project_id back.
  But parsing happens in the background — the client doesn't know
  when it's done.  This endpoint lets the client poll for status.

  Typical client flow:
    1. POST /upload → get project_id + list of file results
    2. GET /jobs/{job_id} every few seconds → check status
    3. When status == "completed" → GET /documents/{document_id}
       to retrieve the parsed content
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.processing_job import ProcessingJob
from app.schemas.processing import ProcessingJobResponse

router = APIRouter(prefix="/jobs", tags=["Processing Jobs"])


@router.get(
    "/{job_id}",
    response_model=ProcessingJobResponse,
    summary="Get processing job status",
    description=(
        "Returns the current status of a background document processing job. "
        "Poll this endpoint after upload to track parsing progress. "
        "Status values: queued → processing → completed | failed."
    ),
)
def get_job(
    job_id: str,
    db: Session = Depends(get_db),
) -> ProcessingJobResponse:
    """
    Fetch a ProcessingJob by its UUID.

    Args:
        job_id: UUID string of the processing job (from the upload response).
        db:     Database session (injected by FastAPI).

    Returns:
        ProcessingJobResponse with current status and timestamps.

    Raises:
        HTTP 404: if no job with that ID exists.
        HTTP 400: if job_id is not a valid UUID.
    """
    import uuid

    # Validate that job_id is a proper UUID before hitting the DB.
    # This gives a clear 400 error instead of a cryptic DB error.
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid job ID format: '{job_id}'. Must be a UUID.",
        )

    job = db.get(ProcessingJob, job_uuid)
    if job is None:
        raise HTTPException(
            status_code=404,
            detail=f"Processing job '{job_id}' not found.",
        )

    return ProcessingJobResponse.model_validate(job)
