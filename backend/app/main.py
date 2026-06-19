from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.upload import router as upload_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.documents import router as documents_router
from app.api.routes.documents import router_projects as projects_status_router
from app.api.routes.projects import router as projects_router
from app.api.routes.requirements import router as requirements_router
from app.core.config import settings
from app.core.database import Base, engine
from app.core.logging_config import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()  # initialise file-based logging before anything else
    import app.models  # noqa: F401 — registers all models with Base.metadata
    Base.metadata.create_all(bind=engine, checkfirst=True)
    yield


app = FastAPI(
    title="EstimateIQ API",
    description="AI-powered RFP Requirement Extraction Platform.",
    version="1.0.0",
    lifespan=lifespan,
)

_cors_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(upload_router)
app.include_router(jobs_router)
app.include_router(documents_router)
app.include_router(projects_router)
app.include_router(projects_status_router)
app.include_router(requirements_router)


@app.get("/", tags=["Root"])
def root():
    return {"service": "EstimateIQ API", "version": "1.0.0", "docs": "/docs"}
