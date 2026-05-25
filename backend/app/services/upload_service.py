"""
Upload service for RFP file ingestion.

This module provides validation, storage, and orchestration logic for the
POST /upload endpoint. Subsequent tasks (4.2–4.6) will add functions and
classes to this scaffold.
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings

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
# Validation helpers
# ---------------------------------------------------------------------------


def validate_count(files: list) -> None:
    """Validate the number of uploaded files.

    Raises:
        ValidationError: if the list is empty or exceeds the configured limit.
    """
    n = len(files)
    if n == 0:
        raise ValidationError("At least one file is required.")
    limit = settings.upload_max_files
    if n > limit:
        raise ValidationError(
            f"Too many files: received {n}, maximum allowed is {limit}."
        )


def validate_types(files: list[UploadFile]) -> list[str]:
    """Validate the extension and MIME type of every uploaded file.

    Checks both the file extension (derived from ``filename``) and the MIME
    type (from ``content_type``) against ``ALLOWED_TYPES``.  All files are
    evaluated before returning — no short-circuit.

    Rules:
    - If the extension is not in ``ALLOWED_TYPES`` → record an extension error
      and skip the MIME check for that file.
    - If the extension is valid but the MIME type does not match → record a
      MIME mismatch error.

    Args:
        files: list of UploadFile objects.

    Returns:
        A list of human-readable error strings (empty if all files are valid).
    """
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
            continue  # skip MIME check for files with an invalid extension

        expected_mime = ALLOWED_TYPES[ext]
        actual_mime = file.content_type or ""
        if actual_mime != expected_mime:
            errors.append(
                f"MIME type mismatch for '{name}': detected '{actual_mime}'."
            )

    return errors


def validate_sizes(files: list, sizes: list[int]) -> list[str]:
    """Validate per-file and total size limits.

    Checks every file against its type-specific byte limit and checks the
    combined total against the configured total limit.  All violations are
    collected before returning — no short-circuit.

    Args:
        files: list of UploadFile objects (parallel to ``sizes``).
        sizes: list of byte counts, one per file in the same order.

    Returns:
        A list of human-readable error strings.  Per-file errors appear first,
        followed by the total-size error (if any).  An empty list means all
        size checks passed.
    """
    # Derive byte thresholds from settings
    per_type_limits: dict[str, tuple[int, float]] = {
        ".pdf":  (int(settings.upload_max_pdf_mb * MB),  settings.upload_max_pdf_mb),
        ".docx": (int(settings.upload_max_docx_mb * MB), settings.upload_max_docx_mb),
        ".xlsx": (int(settings.upload_max_xlsx_mb * MB), settings.upload_max_xlsx_mb),
    }
    total_limit_bytes = int(settings.upload_max_total_mb * MB)

    errors: list[str] = []

    for file, size_bytes in zip(files, sizes):
        name: str = file.filename or ""
        # Determine extension (lowercase)
        dot_idx = name.rfind(".")
        ext = name[dot_idx:].lower() if dot_idx != -1 else ""

        # Only check per-file size for known extensions; unknown types are
        # handled by validate_types.
        if ext not in per_type_limits:
            continue

        limit_bytes, limit_mb = per_type_limits[ext]
        if size_bytes > limit_bytes:
            size_mb = size_bytes / MB
            # Derive the display type label (uppercase, without the dot)
            type_label = ext.lstrip(".").upper()
            errors.append(
                f"File '{name}' ({size_mb:.2f} MB) exceeds the "
                f"{limit_mb:g} MB limit for {type_label} files."
            )

    # Check total size
    total_bytes = sum(sizes)
    if total_bytes > total_limit_bytes:
        total_mb = total_bytes / MB
        errors.append(
            f"Total upload size ({total_mb:.2f} MB) exceeds the 100 MB limit."
        )

    return errors


# ---------------------------------------------------------------------------
# Storage helpers
# ---------------------------------------------------------------------------


def create_project_directory(project_id: str) -> None:
    """Create the per-project storage directory.

    Creates ``{storage_root}/{project_id}/`` (including any missing parent
    directories).  The call is idempotent — if the directory already exists
    no error is raised.

    Args:
        project_id: The UUID string that names the project subdirectory.

    Raises:
        StorageError: if the directory cannot be created due to an OS-level
            error (permissions, invalid path, etc.).
    """
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
    """Write file bytes to disk and return the relative stored path.

    Writes ``content`` to
    ``{storage_root}/{project_id}/{file_uuid}{extension}`` and returns the
    relative path ``{project_id}/{file_uuid}{extension}`` (i.e. relative to
    ``storage_root``).

    Args:
        project_id: The UUID string identifying the project directory.
        file_uuid:  A UUID4 string used as the on-disk filename stem.
        extension:  The lowercase file extension including the leading dot
                    (e.g. ``".pdf"``).
        content:    Raw bytes to write.

    Returns:
        The relative path string ``{project_id}/{file_uuid}{extension}``.

    Raises:
        StorageError: if the file cannot be written due to an I/O error.
    """
    full_path = Path(settings.upload_storage_root) / project_id / f"{file_uuid}{extension}"
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

import logging
import uuid

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.project import Project
from app.schemas.upload import FileResult, UploadResponse

logger = logging.getLogger(__name__)


class UploadService:
    """Orchestrates file validation, storage, and database persistence."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def process_upload(
        self,
        files: list[UploadFile],
        contents: list[bytes],
    ) -> UploadResponse:
        """Run the full upload pipeline and return a structured response.

        Steps:
        1. Validate file count (raises HTTP 400 on failure).
        2. Validate file types (raises HTTP 400 on failure).
        3. Validate file sizes (raises HTTP 400 on failure).
        4. Insert Project row (raises HTTP 500 on DB failure; no files written).
        5. Create project storage directory (raises HTTP 500 on failure).
        6. For each file: write to disk, then insert Document row.
        7. Return UploadResponse.

        Args:
            files:    List of UploadFile objects from the multipart request.
            contents: Pre-read bytes for each file, parallel to ``files``.

        Returns:
            UploadResponse with project_id and per-file results.

        Raises:
            HTTPException(400): on any validation failure.
            HTTPException(500): on project DB insert or directory creation failure.
        """
        sizes = [len(c) for c in contents]

        # ------------------------------------------------------------------
        # Step 1: Count validation
        # ------------------------------------------------------------------
        try:
            validate_count(files)
        except ValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)[:500]) from exc

        # ------------------------------------------------------------------
        # Step 2: Type validation
        # ------------------------------------------------------------------
        type_errors = validate_types(files)
        if type_errors:
            detail = "; ".join(type_errors)[:500]
            raise HTTPException(status_code=400, detail=detail)

        # ------------------------------------------------------------------
        # Step 3: Size validation
        # ------------------------------------------------------------------
        size_errors = validate_sizes(files, sizes)
        if size_errors:
            detail = "; ".join(size_errors)[:500]
            raise HTTPException(status_code=400, detail=detail)

        # ------------------------------------------------------------------
        # Step 4: Insert Project row
        # ------------------------------------------------------------------
        project = Project()
        try:
            self.db.add(project)
            self.db.commit()
            self.db.refresh(project)
        except Exception as exc:
            self.db.rollback()
            detail = f"Failed to create project record: {exc}"[:500]
            raise HTTPException(status_code=500, detail=detail) from exc

        # ------------------------------------------------------------------
        # Step 5: Create project storage directory
        # ------------------------------------------------------------------
        project_id_str = str(project.id)
        try:
            create_project_directory(project_id_str)
        except StorageError as exc:
            detail = f"Failed to create storage directory: {exc}"[:500]
            raise HTTPException(status_code=500, detail=detail) from exc

        # ------------------------------------------------------------------
        # Step 6: Write files and insert Document rows
        # ------------------------------------------------------------------
        file_results: list[FileResult] = []

        for file, content in zip(files, contents):
            name: str = file.filename or ""
            dot_idx = name.rfind(".")
            ext = name[dot_idx:].lower() if dot_idx != -1 else ""
            file_type = ext.lstrip(".")  # e.g. "pdf"
            file_uuid = str(uuid.uuid4())

            # --- 6a: Write file to disk ---
            stored_path = ""
            upload_status = "uploaded"
            error_reason: str | None = None

            try:
                stored_path = write_file(project_id_str, file_uuid, ext, content)
            except StorageError as exc:
                upload_status = "failed"
                error_reason = str(exc)
                stored_path = ""

            # --- 6b: Insert Document row ---
            doc = Document(
                id=uuid.uuid4(),
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
                    "Failed to insert Document record for '%s' in project %s: %s",
                    name,
                    project_id_str,
                    exc,
                )
                upload_status = "failed"
                error_reason = str(exc)

            file_results.append(
                FileResult(
                    file_name=name,
                    status=upload_status,  # type: ignore[arg-type]
                    error_reason=error_reason,
                )
            )

        # ------------------------------------------------------------------
        # Step 7: Return response
        # ------------------------------------------------------------------
        return UploadResponse(
            project_id=project_id_str,
            uploaded_files=file_results,
        )
