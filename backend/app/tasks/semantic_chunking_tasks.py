"""
semantic_chunking_tasks.py — Celery task definitions for semantic chunking
and requirement classification (Phase 6 + Phase 7).

What is this task?
  After a document has been hierarchically chunked (upload_status = "chunked"),
  the ChunkingService dispatches this task to run the semantic chunking and
  classification pipeline in the background.

  Flow:
    chunk_document (chunking_tasks.py)
      → semantic_chunk_document.delay(document_id, project_id)
      → Redis (broker)
      → Celery worker picks up message
      → SemanticChunkingService.run() executes the full pipeline
      → document.upload_status set to "classified" (or "semantic_chunking_failed")

Why a separate DB session here?
  The Celery worker is a completely separate process from FastAPI.
  It has no access to FastAPI's request-scoped DB sessions.
  We create a fresh session using SessionLocal() for each task.
  We always close it in the `finally` block to avoid connection leaks.
"""

import logging

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.services.semantic_chunking.service import SemanticChunkingService

logger = logging.getLogger(__name__)


@celery_app.task(
    name="app.tasks.semantic_chunking_tasks.semantic_chunk_document",
    # Retry up to 3 times if an unexpected exception escapes the service.
    # SemanticChunkingService catches all errors internally, so retries are a safety net.
    max_retries=3,
    # Wait 60 seconds before each retry.
    default_retry_delay=60,
    # Acknowledge the task only after it completes (not when it starts).
    # This prevents task loss if the worker crashes mid-execution.
    acks_late=True,
)
def semantic_chunk_document(document_id: str, project_id: str) -> dict:
    """
    Background task: run the semantic chunking and classification pipeline
    for one document.

    This function is called by Celery, not by FastAPI directly.
    The chunk_document task calls `.delay()` on this function after Phase 5
    completes, which sends a message to Redis.  The Celery worker picks up
    the message and runs this.

    Args:
        document_id: UUID string of the Document row to process.
        project_id:  UUID string of the owning Project.

    Returns:
        A dict with the document_id and final status (for Celery's result backend).
    """
    logger.info(
        "semantic_chunk_document task started: document=%s project=%s",
        document_id,
        project_id,
    )

    # Create a fresh DB session for this task.
    db = SessionLocal()
    try:
        service = SemanticChunkingService(db=db)
        service.run(document_id=document_id, project_id=project_id)
        logger.info(
            "semantic_chunk_document task completed: document=%s", document_id
        )
        return {"document_id": document_id, "status": "classified"}

    except Exception as exc:
        # This should rarely happen — SemanticChunkingService catches everything
        # internally.  If it does, log it and let Celery retry.
        logger.exception(
            "semantic_chunk_document task failed unexpectedly: document=%s error=%s",
            document_id,
            exc,
        )
        # `raise self.retry(exc=exc)` tells Celery to retry the task.
        # After max_retries, Celery marks the task as FAILURE.
        raise semantic_chunk_document.retry(exc=exc)

    finally:
        # Always close the DB session to return the connection to the pool.
        db.close()
