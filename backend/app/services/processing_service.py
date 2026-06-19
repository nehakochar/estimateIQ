"""
processing_service.py

Parses the uploaded file and saves text to Document.parsed_content.
After parsing succeeds, dispatches extract_requirements_task — the ONLY
downstream task. No chunking, no embeddings, no Qdrant.

Status lifecycle:  uploaded → processing → parsed → (extraction runs async)
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document
from app.models.processing_job import ProcessingJob
from app.services.parsers import get_parser
from app.services.parsers.base import ParserError
from app.services.parsers.factory import UnsupportedFileTypeError

logger = logging.getLogger(__name__)


class ProcessingService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def run(self, job_id: str, document_id: str) -> None:
        logger.info("ProcessingService.run: job=%s document=%s", job_id, document_id)

        job = self._load_job(job_id)
        if job is None:
            logger.error("ProcessingService: job %s not found", job_id)
            return

        document = self._load_document(document_id)
        if document is None:
            logger.error("ProcessingService: document %s not found", document_id)
            self._mark_failed(job, None, f"Document {document_id} not found.")
            return

        self._mark_processing(job, document)

        file_path = Path(settings.upload_storage_root) / document.stored_path
        if not file_path.exists():
            self._mark_failed(job, document, f"File not found: {file_path}")
            return

        try:
            parser = get_parser(document.file_type)
            parsed_pages = parser.parse(file_path)
        except (UnsupportedFileTypeError, ParserError) as exc:
            self._mark_failed(job, document, str(exc))
            return
        except Exception as exc:
            self._mark_failed(job, document, f"Unexpected parse error: {exc}")
            return

        parsed_content = [page.to_dict() for page in parsed_pages]
        self._mark_completed(job, document, parsed_content)

        logger.info(
            "ProcessingService: done job=%s document=%s pages=%d",
            job_id, document_id, len(parsed_pages),
        )

    def _load_job(self, job_id: str) -> ProcessingJob | None:
        try:
            return self.db.get(ProcessingJob, uuid.UUID(job_id))
        except ValueError:
            return None

    def _load_document(self, document_id: str) -> Document | None:
        try:
            return self.db.get(Document, uuid.UUID(document_id))
        except ValueError:
            return None

    def _mark_processing(self, job: ProcessingJob, document: Document) -> None:
        now = datetime.now(timezone.utc)
        job.status = "processing"
        job.started_at = now
        document.upload_status = "processing"
        try:
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            logger.error("ProcessingService: failed to mark processing: %s", exc)

    def _mark_completed(
        self, job: ProcessingJob, document: Document, parsed_content: list[dict]
    ) -> None:
        now = datetime.now(timezone.utc)
        job.status = "completed"
        job.completed_at = now
        document.upload_status = "parsed"
        document.parsed_content = parsed_content
        try:
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            logger.error("ProcessingService: failed to save results: %s", exc)
            raise

        # Dispatch extraction — the only downstream task
        from app.tasks.extraction_tasks import extract_requirements_task
        extract_requirements_task.delay(
            document_id=str(document.id),
            project_id=str(document.project_id),
        )
        logger.info(
            "ProcessingService: extraction queued for document=%s", document.id
        )

    def _mark_failed(
        self,
        job: ProcessingJob,
        document: Document | None,
        error_message: str,
    ) -> None:
        now = datetime.now(timezone.utc)
        job.status = "failed"
        job.completed_at = now
        job.error_message = error_message[:2000]
        if document is not None:
            document.upload_status = "failed"
        try:
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            logger.error("ProcessingService: failed to write failure: %s", exc)
