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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False  # POSTGRES_USER matches postgres_user


settings = Settings()
