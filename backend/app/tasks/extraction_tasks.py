"""
extraction_tasks.py — Celery task for LLM-based requirement extraction.

Triggered after parsing completes (document.upload_status == "parsed").
Runs in parallel with the existing chunking pipeline — both are dispatched
from ProcessingService._mark_completed() independently.

Flow:
    ProcessingService._mark_completed()
      → chunk_document.delay(...)           ← existing pipeline (untouched)
      → extract_requirements_task.delay(...)  ← new extraction pipeline

Worker queue: uses the default "celery" queue unless EXTRACTION_QUEUE is set.
"""

import logging

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.services.extraction.extraction_service import ExtractionService

logger = logging.getLogger(__name__)


@celery_app.task(
    name="app.tasks.extraction_tasks.extract_requirements_task",
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
)
def extract_requirements_task(document_id: str, project_id: str) -> dict:
    """
    Background task: run LLM requirement extraction for one document.

    Args:
        document_id: UUID string of the Document row.
        project_id:  UUID string of the owning Project.

    Returns:
        Dict with document_id and final status.
    """
    logger.info(
        "extract_requirements_task started: document=%s project=%s",
        document_id,
        project_id,
    )

    db = SessionLocal()
    try:
        service = ExtractionService(db=db)
        service.run(document_id=document_id, project_id=project_id)
        logger.info(
            "extract_requirements_task completed: document=%s", document_id
        )
        return {"document_id": document_id, "status": "extracted"}

    except Exception as exc:
        logger.exception(
            "extract_requirements_task failed unexpectedly: document=%s error=%s",
            document_id,
            exc,
        )
        raise extract_requirements_task.retry(exc=exc)

    finally:
        db.close()
