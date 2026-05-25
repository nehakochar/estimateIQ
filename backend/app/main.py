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

# Import the routers from their respective route files.
# As you add more features (rfp, users, estimates), you'll import their routers here.
from app.api.routes.health import router as health_router
from app.api.routes.upload import router as upload_router
from app.core.database import Base, engine

# ─────────────────────────────────────────────
# LIFESPAN — STARTUP / SHUTDOWN EVENTS
# ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs once on startup (before the first request) and once on shutdown.

    Startup:
      - Import all SQLAlchemy models so they are registered with Base.metadata
        before create_all is called.  The models/__init__.py re-exports both
        Project and Document, so a single import is enough.
      - Call Base.metadata.create_all to create any missing tables.
        This is idempotent — existing tables are left untouched.
    """
    # Ensure models are registered with Base.metadata before create_all.
    import app.models  # noqa: F401 — side-effect import registers Project & Document

    Base.metadata.create_all(bind=engine)
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
    version="0.1.0",
    lifespan=lifespan,
    # Swagger UI will be available at http://localhost:8000/docs
    # ReDoc will be available at http://localhost:8000/redoc
)


# ─────────────────────────────────────────────
# REGISTER ROUTERS
# ─────────────────────────────────────────────
# include_router() mounts all routes from a router onto the main app.
# Adding a new feature = create a new router file + one line here.

app.include_router(health_router)
app.include_router(upload_router)
# Future routers will be added here, for example:
# app.include_router(rfp_router)
# app.include_router(user_router)
# app.include_router(estimate_router)


# ─────────────────────────────────────────────
# ROOT ENDPOINT
# ─────────────────────────────────────────────
@app.get("/", tags=["Root"], summary="API Root")
def root():
    """
    Root endpoint — confirms the API is reachable.
    Returns basic info about the service.
    """
    return {
        "service": "EstimateIQ API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }
