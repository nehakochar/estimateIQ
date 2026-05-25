from typing import Literal

from pydantic import BaseModel


class FileResult(BaseModel):
    file_name: str
    status: Literal["uploaded", "failed"]
    error_reason: str | None = None


class UploadResponse(BaseModel):
    project_id: str  # UUID as string
    uploaded_files: list[FileResult]
