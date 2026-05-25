from typing import Literal

from pydantic import BaseModel


class FileResult(BaseModel):
    file_name: str
    status: Literal["uploaded", "failed"]
    # These IDs are returned so the client can immediately poll for
    # processing status and retrieve parsed content after upload.
    document_id: str | None = None  # UUID of the Document row
    job_id: str | None = None       # UUID of the ProcessingJob row
    error_reason: str | None = None


class UploadResponse(BaseModel):
    project_id: str  # UUID as string
    uploaded_files: list[FileResult]
