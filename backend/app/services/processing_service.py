"""
processing_service.py — Orchestrates the full document parsing pipeline.

This service is called by the Celery task.  It:
  1. Loads the Document and ProcessingJob from the database.
  2. Marks the job as "processing".
  3. Resolves the full file path on disk.
  4. Calls the correct parser via the factory.
  5. Saves the parsed content back to the Document row.
  6. Marks the job as "completed" and the document as "parsed".
  7. On any error: marks both as "failed" and records the error message.

Why is this a service and not just code inside the Celery task?
  - Services are testable without Celery running.
  - The task file stays thin — it just calls this service.
  - Follows the same layered architecture as the rest of the project.
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
from app.tasks.chunking_tasks import chunk_document

logger = logging.getLogger(__name__)


class ProcessingService:
    """
    Runs the parsing pipeline for a single document.

    Usage (inside a Celery task):
        service = ProcessingService(db)
        service.run(job_id="...", document_id="...")
    """

    def __init__(self, db: Session) -> None:
        # db is a SQLAlchemy session injected from outside.
        # The Celery task creates its own session and passes it in.
        self.db = db

    # ── Public entry point ────────────────────────────────────────

    def run(self, job_id: str, document_id: str) -> None:
        """
        Execute the full parsing pipeline for one document.

        This method is designed to be called from a Celery task.
        It never raises — all errors are caught, logged, and written
        to the database so the API can report them.

        Args:
            job_id:      UUID string of the ProcessingJob row.
            document_id: UUID string of the Document row.
        """
        logger.info(
            "ProcessingService.run: job=%s document=%s", job_id, document_id
        )

        # ── Load records from DB ──────────────────────────────────
        job = self._load_job(job_id)
        if job is None:
            # Nothing we can do — the job row doesn't exist.
            logger.error("ProcessingService: job %s not found in DB", job_id)
            return

        document = self._load_document(document_id)
        if document is None:
            logger.error(
                "ProcessingService: document %s not found in DB", document_id
            )
            self._mark_failed(job, None, f"Document {document_id} not found.")
            return

        # ── Mark as processing ────────────────────────────────────
        self._mark_processing(job, document)

        # ── Resolve file path ─────────────────────────────────────
        # stored_path is relative to upload_storage_root, e.g.:
        #   "abc-project-uuid/def-file-uuid.pdf"
        # We join it with the storage root to get the full path.
        file_path = Path(settings.upload_storage_root) / document.stored_path

        if not file_path.exists():
            error = f"File not found on disk: {file_path}"
            logger.error("ProcessingService: %s", error)
            self._mark_failed(job, document, error)
            return

        # ── Parse the document ────────────────────────────────────
        try:
            parser = get_parser(document.file_type)
            parsed_pages = parser.parse(file_path)
        except UnsupportedFileTypeError as exc:
            self._mark_failed(job, document, str(exc))
            return
        except ParserError as exc:
            self._mark_failed(job, document, str(exc))
            return
        except Exception as exc:
            # Catch-all for unexpected errors (e.g. memory errors)
            error = f"Unexpected error during parsing: {exc}"
            logger.exception("ProcessingService: unexpected error for job %s", job_id)
            self._mark_failed(job, document, error)
            return

        # ── Convert ParsedPage objects to plain dicts for JSON storage ──
        # PostgreSQL JSON column stores Python dicts/lists natively via
        # SQLAlchemy's JSON type.
        parsed_content = [page.to_dict() for page in parsed_pages]

        # ── Save results and mark success ─────────────────────────
        self._mark_completed(job, document, parsed_content)

        logger.info(
            "ProcessingService: completed job=%s document=%s pages=%d",
            job_id,
            document_id,
            len(parsed_pages),
        )

    # ── Private helpers ───────────────────────────────────────────

    def _load_job(self, job_id: str) -> ProcessingJob | None:
        """Fetch the ProcessingJob row by UUID string."""
        try:
            uid = uuid.UUID(job_id)
        except ValueError:
            logger.error("ProcessingService: invalid job_id UUID: %s", job_id)
            return None
        return self.db.get(ProcessingJob, uid)

    def _load_document(self, document_id: str) -> Document | None:
        """Fetch the Document row by UUID string."""
        try:
            uid = uuid.UUID(document_id)
        except ValueError:
            logger.error(
                "ProcessingService: invalid document_id UUID: %s", document_id
            )
            return None
        return self.db.get(Document, uid)

    def _mark_processing(self, job: ProcessingJob, document: Document) -> None:
        """
        Transition both the job and the document to "processing" status.
        Records the start timestamp on the job.
        """
        now = datetime.now(timezone.utc)
        job.status = "processing"
        job.started_at = now
        document.upload_status = "processing"
        try:
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            logger.error(
                "ProcessingService: failed to mark processing for job %s: %s",
                job.id,
                exc,
            )

    def _mark_completed(
        self,
        job: ProcessingJob,
        document: Document,
        parsed_content: list[dict],
    ) -> None:
        """
        Save parsed content and transition both records to success status.
        """
        now = datetime.now(timezone.utc)
        job.status = "completed"
        job.completed_at = now
        document.upload_status = "parsed"
        document.parsed_content = parsed_content
        try:
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            logger.error(
                "ProcessingService: failed to save results for job %s: %s",
                job.id,
                exc,
            )
            # Re-raise so the Celery task can mark the job as failed
            raise

        # Dispatch the chunking task now that the document is "parsed".
        chunk_document.delay(
            document_id=str(document.id),
            project_id=str(document.project_id),
        )

        # Dispatch LLM extraction in parallel with chunking.
        # Import here to avoid circular imports at module load time.
        from app.tasks.extraction_tasks import extract_requirements_task
        extract_requirements_task.delay(
            document_id=str(document.id),
            project_id=str(document.project_id),
        )

    def _mark_failed(
        self,
        job: ProcessingJob,
        document: Document | None,
        error_message: str,
    ) -> None:
        """
        Record the error and transition both records to "failed" status.
        """
        now = datetime.now(timezone.utc)
        job.status = "failed"
        job.completed_at = now
        # Truncate error message to avoid DB column overflow
        job.error_message = error_message[:2000]

        if document is not None:
            document.upload_status = "failed"

        try:
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            logger.error(
                "ProcessingService: failed to write failure status for job %s: %s",
                job.id,
                exc,
            )
