"""
processing_tasks.py — Celery task definitions for document processing.

What is a Celery task?
  A Celery task is a Python function that runs in the background,
  in a separate process (the Celery worker), independently of the
  FastAPI web server.

  When the upload endpoint finishes saving files, it calls:
      process_document.delay(job_id, document_id)

  `.delay()` sends a message to Redis.  The Celery worker picks it up
  and runs `process_document` in the background.  The API response
  returns immediately — the user doesn't wait for parsing to finish.

Why a separate DB session here?
  The Celery worker is a completely separate process from FastAPI.
  It has no access to FastAPI's request-scoped DB sessions.
  We create a fresh session using SessionLocal() for each task.
  We always close it in the `finally` block to avoid connection leaks.
"""

import logging

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.services.processing_service import ProcessingService

logger = logging.getLogger(__name__)


@celery_app.task(
    name="app.tasks.processing_tasks.process_document",
    # Retry up to 3 times if an unexpected exception escapes the service.
    # The service itself catches all errors, so retries are a safety net.
    max_retries=3,
    # Wait 60 seconds before each retry (exponential backoff would be
    # better in production, but this is clear and simple for now).
    default_retry_delay=60,
    # Acknowledge the task only after it completes (not when it starts).
    # This prevents task loss if the worker crashes mid-execution.
    acks_late=True,
)
def process_document(job_id: str, document_id: str) -> dict:
    """
    Background task: parse one document and save the results.

    This function is called by Celery, not by FastAPI directly.
    FastAPI calls `.delay()` on this function, which sends a message
    to Redis.  The Celery worker picks up the message and runs this.

    Args:
        job_id:      UUID string of the ProcessingJob row.
        document_id: UUID string of the Document row to parse.

    Returns:
        A dict with the job_id and final status (for Celery's result backend).
    """
    logger.info(
        "process_document task started: job=%s document=%s", job_id, document_id
    )

    # Create a fresh DB session for this task.
    # The `with` statement ensures it's always closed, even on error.
    db = SessionLocal()
    try:
        service = ProcessingService(db=db)
        service.run(job_id=job_id, document_id=document_id)
        logger.info("process_document task completed: job=%s", job_id)
        return {"job_id": job_id, "status": "completed"}

    except Exception as exc:
        # This should rarely happen — ProcessingService catches everything.
        # If it does, log it and let Celery retry.
        logger.exception(
            "process_document task failed unexpectedly: job=%s error=%s",
            job_id,
            exc,
        )
        # `raise self.retry(exc=exc)` tells Celery to retry the task.
        # After max_retries, Celery marks the task as FAILURE.
        raise process_document.retry(exc=exc)

    finally:
        # Always close the DB session to return the connection to the pool.
        db.close()
