from celery.utils.log import get_task_logger

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.document import Document
from app.services.estimation.estimation_service import EstimationService

logger = get_task_logger(__name__)


@celery_app.task(
    name="app.tasks.estimation_tasks.generate_estimates_task",
    max_retries=4,
    acks_late=True,
)
def generate_estimates_task(requirement_ids: list[str], project_id: str) -> dict:
    """Generate estimates for a list of requirement IDs within a project.

    Runs each requirement through EstimationService sequentially.
    After all requirements are processed (success or partial failure),
    updates every document in the project to estimation_status='completed'.
    On a complete failure, marks them 'failed'.
    """
    logger.info(
        "generate_estimates_task: starting for %d requirements (project=%s)",
        len(requirement_ids),
        project_id,
    )
    db = SessionLocal()
    failed_ids: list[str] = []

    try:
        for req_id in requirement_ids:
            try:
                EstimationService(project_id=project_id, db=db).run(req_id)
            except Exception:
                logger.exception(
                    "generate_estimates_task: failed to estimate requirement %s — continuing",
                    req_id,
                )
                failed_ids.append(req_id)

        # Determine final status: completed even on partial failure (partial data is useful)
        final_status = "completed" if len(failed_ids) < len(requirement_ids) else "failed"

        # Write final status back to every document in the project
        import uuid as _uuid
        proj_uuid = _uuid.UUID(project_id)
        docs = db.query(Document).filter(Document.project_id == proj_uuid).all()
        for doc in docs:
            doc.estimation_status = final_status
        db.commit()

        logger.info(
            "generate_estimates_task: finished project=%s status=%s failed=%d/%d",
            project_id,
            final_status,
            len(failed_ids),
            len(requirement_ids),
        )

    except Exception:
        logger.exception(
            "generate_estimates_task: unhandled error for project=%s — marking failed",
            project_id,
        )
        try:
            import uuid as _uuid
            proj_uuid = _uuid.UUID(project_id)
            docs = db.query(Document).filter(Document.project_id == proj_uuid).all()
            for doc in docs:
                doc.estimation_status = "failed"
            db.commit()
        except Exception:
            logger.exception("generate_estimates_task: could not mark documents as failed")
        raise

    finally:
        db.close()

    return {"project_id": project_id, "status": final_status, "failed_count": len(failed_ids)}
