"""
health.py — Health Check Routes
================================
This file contains all health-related API endpoints.

Why separate health routes?
- Keeps main.py clean and focused on app setup only
- Health checks are a distinct concern — they belong in their own module
- Easy to extend (add more checks) without touching other files

Endpoints:
- GET /health         → simple liveness check (is the app running?)
- GET /health/db      → checks PostgreSQL connection
- GET /health/qdrant  → checks Qdrant vector DB connection
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse

from app.core.config import settings
from app.core.database import get_db

# APIRouter is like a mini FastAPI app — it groups related routes together.
# The prefix "/health" means all routes here will start with /health automatically.
router = APIRouter(
    prefix="/health",
    tags=["Health"],  # groups these endpoints under "Health" in the Swagger UI docs
)


# ─────────────────────────────────────────────
# 1. LIVENESS CHECK — Is the app alive?
# ─────────────────────────────────────────────
@router.get(
    "",
    summary="Liveness Check",
    description="Returns 200 OK if the application is running. No DB calls — pure liveness.",
)
def health_check():
    """
    The simplest possible health check.
    Used by Docker, Kubernetes, and load balancers to know if the app is alive.
    Does NOT check the database or any external service.
    """
    return {"status": "ok", "service": "estimateIQ API"}


# ─────────────────────────────────────────────
# 2. DATABASE HEALTH — Can we reach PostgreSQL?
# ─────────────────────────────────────────────
@router.get(
    "/db",
    summary="PostgreSQL Health Check",
    description="Runs a lightweight query against PostgreSQL to verify the connection is alive.",
)
def health_db(db: Session = Depends(get_db)):
    """
    Depends(get_db) automatically injects a database session for this request.
    We run 'SELECT 1' — the lightest possible query — just to confirm connectivity.
    If it fails, we return HTTP 503 (Service Unavailable) so monitoring tools know.
    """
    try:
        # 'SELECT 1' is the standard DB ping — it returns immediately with no table scan
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "postgresql"}
    except Exception as e:
        # HTTP 503 = service exists but is temporarily unavailable
        raise HTTPException(
            status_code=503,
            detail={"status": "error", "database": "postgresql", "error": str(e)},
        )


# ─────────────────────────────────────────────
# 3. QDRANT HEALTH — Can we reach the vector DB?
# ─────────────────────────────────────────────
@router.get(
    "/qdrant",
    summary="Qdrant Health Check",
    description="Connects to Qdrant and lists collections to verify the vector DB is reachable.",
)
def health_qdrant():
    """
    Creates a fresh Qdrant client and calls get_collections().
    This confirms both network connectivity and API key validity.
    The client is created per-request here (not shared) because Qdrant
    connections are lightweight and we don't need a persistent pool for health checks.
    """
    try:
        client = QdrantClient(
            host="qdrant",                    # Docker service name from docker-compose.yml
            port=settings.qdrant_port_http,   # default 6333
            api_key=settings.qdrant_api_key,  # from .env
            https=False,                      # no TLS inside Docker network
        )
        collections = client.get_collections()
        return {
            "status": "ok",
            "database": "qdrant",
            "collections_count": len(collections.collections),
        }
    except UnexpectedResponse as e:
        # Qdrant raises UnexpectedResponse for auth failures (wrong API key)
        raise HTTPException(
            status_code=503,
            detail={
                "status": "error",
                "database": "qdrant",
                "error": f"Auth error {e.status_code}: {e.reason_phrase}",
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={"status": "error", "database": "qdrant", "error": str(e)},
        )
