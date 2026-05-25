from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Postgres
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_port: int = 5432
    database_url: str

    # Qdrant
    qdrant_api_key: str
    qdrant_port_http: int = 6333
    qdrant_port_grpc: int = 6334
    qdrant_url: str

    # Redis / Celery
    redis_port: int = 6379
    redis_url: str = "redis://redis:6379/0"

    # App
    backend_port: int = 8000

    # Upload limits
    upload_max_files: int = 10
    upload_max_total_mb: float = 100.0
    upload_max_pdf_mb: float = 50.0
    upload_max_docx_mb: float = 20.0
    upload_max_xlsx_mb: float = 15.0
    upload_storage_root: str = "storage/uploads"

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
        case_sensitive = False  # POSTGRES_USER matches postgres_user


settings = Settings()
