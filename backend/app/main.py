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

from fastapi import FastAPI

# Import the routers from their respective route files.
# As you add more features (rfp, users, estimates), you'll import their routers here.
from app.api.routes.health import router as health_router

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
    # Swagger UI will be available at http://localhost:8000/docs
    # ReDoc will be available at http://localhost:8000/redoc
)


# ─────────────────────────────────────────────
# REGISTER ROUTERS
# ─────────────────────────────────────────────
# include_router() mounts all routes from a router onto the main app.
# Adding a new feature = create a new router file + one line here.

app.include_router(health_router)
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
