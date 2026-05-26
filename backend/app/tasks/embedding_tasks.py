"""
embedding_tasks.py — Celery task definitions for vector embedding (Phase 8).

What is this task?
  After a document has been semantically chunked and classified
  (upload_status = "classified"), the SemanticChunkingService dispatches
  this task to run the embedding pipeline in the background.

  Flow:
    semantic_chunk_document (semantic_chunking_tasks.py)
      → embed_document.delay(document_id, project_id)
      → Redis (broker)
      → Celery worker picks up message
      → EmbeddingPipeline.run() executes the full embedding lifecycle
      → document.upload_status set to "embedded" (or "embedding_failed")

Why a separate DB session here?
  The Celery worker is a completely separate process from FastAPI.
  It has no access to FastAPI's request-scoped DB sessions.
  We create a fresh session using SessionLocal() for each task.
  We always close it in the `finally` block to avoid connection leaks.
"""

import logging

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.services.processing.embedding_pipeline import EmbeddingPipeline

logger = logging.getLogger(__name__)


@celery_app.task(
    name="app.tasks.embedding_tasks.embed_document",
    # Acknowledge the task only after it completes (not when it starts).
    # This prevents task loss if the worker crashes mid-execution.
    acks_late=True,
    # Retry up to 3 times if an unexpected exception escapes the pipeline.
    # EmbeddingPipeline catches batch-level errors internally, so retries
    # are a safety net for infrastructure failures (DB down, Qdrant down).
    max_retries=3,
    # Wait 60 seconds before each retry.
    default_retry_delay=60,
)
def embed_document(document_id: str, project_id: str) -> dict:
    """
    Background task: run the embedding pipeline for one document.

    This function is called by Celery, not by FastAPI directly.
    The semantic_chunk_document task calls `.delay()` on this function
    after Phase 6/7 completes, which sends a message to Redis.  The
    Celery worker picks up the message and runs this.

    Args:
        document_id: UUID string of the Document row to process.
        project_id:  UUID string of the owning Project.

    Returns:
        A dict with the document_id and final status (for Celery's result backend).
    """
    logger.info(
        "embed_document task started: document=%s project=%s",
        document_id,
        project_id,
    )

    # Create a fresh DB session for this task.
    db = SessionLocal()
    try:
        pipeline = EmbeddingPipeline(db=db)
        pipeline.run(document_id=document_id, project_id=project_id)
        logger.info(
            "embed_document task completed: document=%s", document_id
        )
        return {"document_id": document_id, "status": "embedded"}

    except Exception as exc:
        # This should rarely happen — EmbeddingPipeline catches batch-level
        # errors internally and marks individual chunks as "failed".
        # If an unhandled exception does escape (e.g. DB connection lost,
        # Qdrant unreachable at startup), log it and let Celery retry.
        logger.exception(
            "embed_document task failed unexpectedly: document=%s error=%s",
            document_id,
            exc,
        )
        # `raise self.retry(exc=exc)` tells Celery to retry the task.
        # After max_retries, Celery marks the task as FAILURE.
        raise embed_document.retry(exc=exc)

    finally:
        # Always close the DB session to return the connection to the pool.
        db.close()
