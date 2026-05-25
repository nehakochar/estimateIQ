from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings

# Engine — the core connection pool to Postgres
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,   # checks connection health before using it from the pool
    pool_size=10,         # number of persistent connections
    max_overflow=20,      # extra connections allowed beyond pool_size under load
)

# Session factory — each request gets its own session
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


# Base class — all SQLAlchemy models will inherit from this
class Base(DeclarativeBase):
    pass


# FastAPI dependency — yields a DB session per request, always closes it after
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
