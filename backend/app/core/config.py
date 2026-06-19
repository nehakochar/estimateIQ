from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    # Postgres
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_port: int = 5432
    database_url: str

    # Redis / Celery
    redis_port: int = 6379
    redis_url: str = "redis://redis:6379/0"

    # App
    backend_port: int = 8000
    cors_origins: str = "http://localhost:3000,http://localhost:7000"

    # Upload limits
    upload_max_files: int = 10
    upload_max_total_mb: float = 100.0
    upload_max_pdf_mb: float = 50.0
    upload_max_docx_mb: float = 20.0
    upload_max_xlsx_mb: float = 15.0
    upload_storage_root: str = "storage/uploads"

    # LLM Extraction
    extraction_provider: str = "gemini"   # gemini | groq
    gemini_api_key: str = ""
    groq_api_key: str = ""

    @field_validator(
        "upload_max_files",
        "upload_max_total_mb",
        "upload_max_pdf_mb",
        "upload_max_docx_mb",
        "upload_max_xlsx_mb",
    )
    @classmethod
    def must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("must be a positive number")
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()
