"""
chunking_tasks.py — Celery task definitions for hierarchical document chunking.

What is this task?
  After a document has been parsed (upload_status = "parsed"), the
  ProcessingService dispatches this task to run the chunking pipeline
  in the background.

  Flow:
    ProcessingService._mark_completed()
      → chunk_document.delay(document_id, project_id)
      → Redis (broker)
      → Celery worker picks up message
      → ChunkingService.run() executes the full pipeline
      → document.upload_status set to "chunked" (or "chunking_failed")

Why a separate DB session here?
  The Celery worker is a completely separate process from FastAPI.
  It has no access to FastAPI's request-scoped DB sessions.
  We create a fresh session using SessionLocal() for each task.
  We always close it in the `finally` block to avoid connection leaks.
"""

import logging

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.services.chunking.service import ChunkingService
from app.tasks.semantic_chunking_tasks import semantic_chunk_document

logger = logging.getLogger(__name__)


@celery_app.task(
    name="app.tasks.chunking_tasks.chunk_document",
    # Retry up to 3 times if an unexpected exception escapes the service.
    # ChunkingService catches all errors internally, so retries are a safety net.
    max_retries=3,
    # Wait 60 seconds before each retry.
    default_retry_delay=60,
    # Acknowledge the task only after it completes (not when it starts).
    # This prevents task loss if the worker crashes mid-execution.
    acks_late=True,
)
def chunk_document(document_id: str, project_id: str) -> dict:
    """
    Background task: run the hierarchical chunking pipeline for one document.

    This function is called by Celery, not by FastAPI directly.
    FastAPI calls `.delay()` on this function, which sends a message
    to Redis.  The Celery worker picks up the message and runs this.

    Args:
        document_id: UUID string of the Document row to chunk.
        project_id:  UUID string of the owning Project.

    Returns:
        A dict with the document_id and final status (for Celery's result backend).
    """
    logger.info(
        "chunk_document task started: document=%s project=%s",
        document_id,
        project_id,
    )

    # Create a fresh DB session for this task.
    db = SessionLocal()
    try:
        service = ChunkingService(db=db)
        service.run(document_id=document_id, project_id=project_id)
        logger.info("chunk_document task completed: document=%s", document_id)
        semantic_chunk_document.delay(document_id, project_id)
        return {"document_id": document_id, "status": "chunked"}

    except Exception as exc:
        # This should rarely happen — ChunkingService catches everything internally.
        # If it does, log it and let Celery retry.
        logger.exception(
            "chunk_document task failed unexpectedly: document=%s error=%s",
            document_id,
            exc,
        )
        # `raise self.retry(exc=exc)` tells Celery to retry the task.
        # After max_retries, Celery marks the task as FAILURE.
        raise chunk_document.retry(exc=exc)

    finally:
        # Always close the DB session to return the connection to the pool.
        db.close()
