"""
main.py — FastAPI Application Entry Point
==========================================
This is the heart of the backend. It:
  1. Creates the FastAPI app instance
  2. Registers all route modules (routers)
  3. Is the file uvicorn points to when starting the server

Think of this file as the "wiring board" — it connects everything together
but contains NO business logic itself. Logic lives in routes/ and services/.

How uvicorn uses this file:
  uvicorn app.main:app
  → looks in the 'app' package, finds 'main.py', uses the 'app' variable
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.upload import router as upload_router
from app.api.routes.jobs import router as jobs_router          # Phase 3
from app.api.routes.documents import router as documents_router, router_projects as projects_status_router  # Phase 3
from app.api.routes.projects import router as projects_router  # Project CRUD
from app.api.routes.semantic_chunks import router as semantic_chunks_router  # Phase 6
from app.api.routes.retrieval import router as retrieval_router  # Phase 9
from app.api.routes.requirements import router as requirements_router  # Extraction
from app.core.config import settings
from app.core.database import Base, engine


# ─────────────────────────────────────────────
# LIFESPAN — STARTUP / SHUTDOWN EVENTS
# ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs once on startup (before the first request) and once on shutdown.

    Startup:
      - Import all SQLAlchemy models so they register with Base.metadata.
      - Call Base.metadata.create_all to create any missing tables.
        This is idempotent — existing tables are left untouched.
    """
    # Side-effect import: registers Project, Document, ProcessingJob
    # with Base.metadata so create_all knows about all three tables.
    import app.models  # noqa: F401

    # Use checkfirst=True to avoid errors when indexes already exist
    Base.metadata.create_all(bind=engine, checkfirst=True)
    yield
    # (shutdown logic can be added here in the future)


# ─────────────────────────────────────────────
# CREATE THE FASTAPI APPLICATION INSTANCE
# ─────────────────────────────────────────────
app = FastAPI(
    title="EstimateIQ API",
    description=(
        "AI-powered Enterprise RFP Intelligence Platform. "
        "Automates RFP parsing, analysis, and estimation."
    ),
    version="0.2.0",
    lifespan=lifespan,
)


# ─────────────────────────────────────────────
# CORS MIDDLEWARE
# ─────────────────────────────────────────────
# Must be added before routers so preflight OPTIONS requests are handled.
# Origins are read from CORS_ORIGINS in .env (comma-separated).
_cors_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────
# REGISTER ROUTERS
# ─────────────────────────────────────────────
app.include_router(health_router)
app.include_router(upload_router)
app.include_router(jobs_router)              # GET /jobs/{job_id}
app.include_router(documents_router)         # GET /documents/{document_id}
app.include_router(projects_router)          # POST /projects, GET /projects, GET /projects/{id}
app.include_router(projects_status_router)   # GET /projects/{project_id}/status
app.include_router(semantic_chunks_router)   # GET /documents/{document_id}/semantic-chunks
app.include_router(retrieval_router)         # POST /search, /search/category, /search/similar
app.include_router(requirements_router)      # GET /documents/{id}/requirements, /projects/{id}/requirements


# ─────────────────────────────────────────────
# ROOT ENDPOINT
# ─────────────────────────────────────────────
@app.get("/", tags=["Root"], summary="API Root")
def root():
    """Root endpoint — confirms the API is reachable."""
    return {
        "service": "EstimateIQ API",
        "version": "0.2.0",
        "docs": "/docs",
        "health": "/health",
    }
