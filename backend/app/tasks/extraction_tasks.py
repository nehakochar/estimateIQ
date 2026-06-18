import logging
from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.services.extraction.extraction_service import ExtractionService

logger = logging.getLogger(__name__)


@celery_app.task(
    name="app.tasks.extraction_tasks.extract_requirements_task",
    max_retries=3,
    default_retry_delay=30,
    acks_late=True,
)
def extract_requirements_task(document_id: str, project_id: str) -> dict:
    logger.info("extract_requirements_task: document=%s", document_id)
    db = SessionLocal()
    try:
        ExtractionService(db=db).run(
            document_id=document_id,
            project_id=project_id,
        )
        return {"document_id": document_id, "status": "done"}
    except Exception as exc:
        logger.exception("extract_requirements_task failed: %s", exc)
        raise extract_requirements_task.retry(exc=exc)
    finally:
        db.close()
