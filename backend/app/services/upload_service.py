"""
Upload service for RFP file ingestion.

Phase 2: validation, storage, DB persistence.
Phase 3: after each file is saved, create a ProcessingJob and enqueue
         a Celery task so parsing starts automatically in the background.
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document
from app.models.processing_job import ProcessingJob
from app.models.project import Project
from app.schemas.upload import FileResult, UploadResponse

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MB = 1_048_576  # bytes per megabyte

ALLOWED_TYPES: dict[str, str] = {
    ".pdf":  "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}

# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------


class ValidationError(Exception):
    """Raised when uploaded files fail count, type, or size validation."""
    pass


class StorageError(Exception):
    """Raised when a filesystem operation (mkdir, write) fails."""
    pass


# ---------------------------------------------------------------------------
# Validation helpers (unchanged from Phase 2)
# ---------------------------------------------------------------------------


def validate_count(files: list) -> None:
    """Validate the number of uploaded files."""
    n = len(files)
    if n == 0:
        raise ValidationError("At least one file is required.")
    limit = settings.upload_max_files
    if n > limit:
        raise ValidationError(
            f"Too many files: received {n}, maximum allowed is {limit}."
        )


def validate_types(files: list[UploadFile]) -> list[str]:
    """Validate extension and MIME type for every file."""
    errors: list[str] = []
    for file in files:
        name: str = file.filename or ""
        dot_idx = name.rfind(".")
        ext = name[dot_idx:].lower() if dot_idx != -1 else ""

        if ext not in ALLOWED_TYPES:
            errors.append(
                f"Invalid file type for '{name}': "
                "supported types are .pdf, .docx, .xlsx."
            )
            continue

        expected_mime = ALLOWED_TYPES[ext]
        actual_mime = file.content_type or ""
        if actual_mime != expected_mime:
            errors.append(
                f"MIME type mismatch for '{name}': detected '{actual_mime}'."
            )
    return errors


def validate_sizes(files: list, sizes: list[int]) -> list[str]:
    """Validate per-file and total size limits."""
    per_type_limits: dict[str, tuple[int, float]] = {
        ".pdf":  (int(settings.upload_max_pdf_mb * MB),  settings.upload_max_pdf_mb),
        ".docx": (int(settings.upload_max_docx_mb * MB), settings.upload_max_docx_mb),
        ".xlsx": (int(settings.upload_max_xlsx_mb * MB), settings.upload_max_xlsx_mb),
    }
    total_limit_bytes = int(settings.upload_max_total_mb * MB)
    errors: list[str] = []

    for file, size_bytes in zip(files, sizes):
        name: str = file.filename or ""
        dot_idx = name.rfind(".")
        ext = name[dot_idx:].lower() if dot_idx != -1 else ""
        if ext not in per_type_limits:
            continue
        limit_bytes, limit_mb = per_type_limits[ext]
        if size_bytes > limit_bytes:
            size_mb = size_bytes / MB
            type_label = ext.lstrip(".").upper()
            errors.append(
                f"File '{name}' ({size_mb:.2f} MB) exceeds the "
                f"{limit_mb:g} MB limit for {type_label} files."
            )

    total_bytes = sum(sizes)
    if total_bytes > total_limit_bytes:
        total_mb = total_bytes / MB
        errors.append(
            f"Total upload size ({total_mb:.2f} MB) exceeds the 100 MB limit."
        )
    return errors


# ---------------------------------------------------------------------------
# Storage helpers (unchanged from Phase 2)
# ---------------------------------------------------------------------------


def create_project_directory(project_id: str) -> None:
    """Create the per-project storage directory (idempotent)."""
    target = Path(settings.upload_storage_root) / project_id
    try:
        target.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise StorageError(
            f"Failed to create storage directory '{target}': {exc}"
        ) from exc


def write_file(
    project_id: str,
    file_uuid: str,
    extension: str,
    content: bytes,
) -> str:
    """Write file bytes to disk and return the relative stored path."""
    full_path = (
        Path(settings.upload_storage_root) / project_id / f"{file_uuid}{extension}"
    )
    try:
        full_path.write_bytes(content)
    except IOError as exc:
        raise StorageError(
            f"Failed to write file '{full_path}': {exc}"
        ) from exc
    return f"{project_id}/{file_uuid}{extension}"


# ---------------------------------------------------------------------------
# Upload service orchestration
# ---------------------------------------------------------------------------


class UploadService:
    """Orchestrates file validation, storage, DB persistence, and job queuing."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def process_upload(
        self,
        files: list[UploadFile],
        contents: list[bytes],
        project_name: str = "",
    ) -> UploadResponse:
        """
        Run the full upload pipeline and return a structured response.

        Steps:
        1. Validate file count.
        2. Validate file types.
        3. Validate file sizes.
        4. Insert Project row.
        5. Create project storage directory.
        6. For each file: write to disk → insert Document → create ProcessingJob
           → enqueue Celery task.
        7. Return UploadResponse.
        """
        sizes = [len(c) for c in contents]

        # ── Step 1: Count validation ──────────────────────────────
        try:
            validate_count(files)
        except ValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)[:500]) from exc

        # ── Step 2: Type validation ───────────────────────────────
        type_errors = validate_types(files)
        if type_errors:
            raise HTTPException(
                status_code=400, detail="; ".join(type_errors)[:500]
            )

        # ── Step 3: Size validation ───────────────────────────────
        size_errors = validate_sizes(files, sizes)
        if size_errors:
            raise HTTPException(
                status_code=400, detail="; ".join(size_errors)[:500]
            )

        # ── Step 4: Insert Project row ────────────────────────────
        # Use provided name, or fall back to first filename stem
        if not project_name and files:
            first_name = files[0].filename or ""
            project_name = first_name.rsplit(".", 1)[0] if "." in first_name else first_name
        project = Project(name=project_name, client_name=None)
        try:
            self.db.add(project)
            self.db.commit()
            self.db.refresh(project)
        except Exception as exc:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create project record: {exc}"[:500],
            ) from exc

        # ── Step 5: Create project storage directory ──────────────
        project_id_str = str(project.id)
        try:
            create_project_directory(project_id_str)
        except StorageError as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create storage directory: {exc}"[:500],
            ) from exc

        # ── Step 6: Per-file processing ───────────────────────────
        file_results: list[FileResult] = []

        for file, content in zip(files, contents):
            name: str = file.filename or ""
            dot_idx = name.rfind(".")
            ext = name[dot_idx:].lower() if dot_idx != -1 else ""
            file_type = ext.lstrip(".")  # "pdf", "docx", "xlsx"
            file_uuid = str(uuid.uuid4())

            upload_status = "uploaded"
            error_reason: str | None = None
            stored_path = ""

            # ── 6a: Write file to disk ────────────────────────────
            try:
                stored_path = write_file(project_id_str, file_uuid, ext, content)
            except StorageError as exc:
                upload_status = "failed"
                error_reason = str(exc)

            # ── 6b: Insert Document row ───────────────────────────
            doc_id = uuid.uuid4()
            doc = Document(
                id=doc_id,
                project_id=project.id,
                file_name=name,
                stored_path=stored_path,
                file_type=file_type,
                file_size_bytes=len(content),
                upload_status=upload_status,
            )
            try:
                self.db.add(doc)
                self.db.commit()
            except Exception as exc:
                self.db.rollback()
                logger.error(
                    "Failed to insert Document for '%s' in project %s: %s",
                    name, project_id_str, exc,
                )
                upload_status = "failed"
                error_reason = str(exc)
                file_results.append(
                    FileResult(
                        file_name=name,
                        status="failed",  # type: ignore[arg-type]
                        document_id=str(doc_id),  # ID was generated even though DB insert failed
                        job_id=None,
                        error_reason=error_reason,
                    )
                )
                continue  # skip job creation for this file

            # ── 6c: Create ProcessingJob row ──────────────────────
            # Only create a job if the file was written successfully.
            # A failed file write means there's nothing to parse.
            job_id: str | None = None
            if upload_status == "uploaded":
                job = ProcessingJob(
                    document_id=doc_id,
                    status="queued",
                )
                try:
                    self.db.add(job)
                    self.db.commit()
                    self.db.refresh(job)
                    job_id = str(job.id)
                except Exception as exc:
                    self.db.rollback()
                    logger.error(
                        "Failed to create ProcessingJob for document %s: %s",
                        doc_id, exc,
                    )
                    # Non-fatal: upload succeeded, processing just won't start.
                    job_id = None

            # ── 6d: Enqueue Celery task ───────────────────────────
            # Import here (not at top) to avoid circular imports.
            # The task module imports celery_app which imports config —
            # all fine, but keeping the import local is cleaner.
            if job_id is not None:
                try:
                    from app.tasks.processing_tasks import process_document

                    celery_result = process_document.delay(
                        job_id=job_id,
                        document_id=str(doc_id),
                    )
                    # Store the Celery task ID so we can look it up later
                    job.celery_task_id = celery_result.id
                    self.db.commit()
                    logger.info(
                        "Enqueued processing task %s for document %s",
                        celery_result.id,
                        doc_id,
                    )
                except Exception as exc:
                    logger.error(
                        "Failed to enqueue Celery task for job %s: %s",
                        job_id, exc,
                    )
                    # Non-fatal: the job row exists with status "queued"
                    # and can be retried manually later.

            file_results.append(
                FileResult(
                    file_name=name,
                    status=upload_status,  # type: ignore[arg-type]
                    document_id=str(doc_id),  # always returned so client can query the document
                    job_id=job_id,            # None if job creation failed, otherwise the polling ID
                    error_reason=error_reason,
                )
            )

        # ── Step 7: Return response ───────────────────────────────
        return UploadResponse(
            project_id=project_id_str,
            uploaded_files=file_results,
        )
