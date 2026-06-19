import logging
from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.services.extraction.extraction_service import ExtractionService, RetryableExtractionError

logger = logging.getLogger(__name__)


@celery_app.task(
    name="app.tasks.extraction_tasks.extract_requirements_task",
    max_retries=4,
    acks_late=True,
)
def extract_requirements_task(document_id: str, project_id: str) -> dict:
    logger.info("extract_requirements_task: document=%s (attempt %d/%d)",
                document_id,
                extract_requirements_task.request.retries + 1,
                extract_requirements_task.max_retries + 1)
    db = SessionLocal()
    try:
        ExtractionService(db=db).run(
            document_id=document_id,
            project_id=project_id,
        )
        return {"document_id": document_id, "status": "done"}

    except RetryableExtractionError as exc:
        # Transient: 503 overloaded, 429 rate-limit, timeout.
        # Use exponential backoff: 60s → 120s → 240s → 480s
        retries = extract_requirements_task.request.retries
        countdown = 60 * (2 ** retries)
        logger.warning(
            "extract_requirements_task: transient error for document=%s, "
            "retry %d/%d in %ds — %s",
            document_id, retries + 1, extract_requirements_task.max_retries, countdown, exc,
        )
        raise extract_requirements_task.retry(exc=exc, countdown=countdown)

    except Exception as exc:
        # Permanent error (bad key, file missing, DB error).
        # Log it but do NOT retry — extraction_service already marked the document.
        logger.exception("extract_requirements_task: permanent failure for document=%s: %s",
                         document_id, exc)
        return {"document_id": document_id, "status": "failed", "error": str(exc)}

    finally:
        db.close()
