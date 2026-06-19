# EstimateIQ — Project Command Reference

All commands are run from the **project root** (`c:\Projects\estimateIQ\`) unless noted otherwise.

---

## 🐳 Docker — Full Stack

```bash
# Start ALL services (postgres, redis, qdrant, backend, celery, frontend)
# Use this on first run — builds images from Dockerfiles
docker-compose up --build

# Start all services without rebuilding (faster, use after first run)
docker-compose up

# Start in detached/background mode
docker-compose up -d

# Stop all running services (keeps volumes/data intact)
docker-compose down

# Stop all services AND delete all persistent data (DB, vector store, redis)
# ⚠️  Destructive — you will lose all uploaded documents and embeddings
docker-compose down -v

# Rebuild only after changing requirements.txt or Dockerfile
docker-compose up --build backend celery_worker

# Start only infrastructure services (no backend/frontend)
docker-compose up postgres redis qdrant

# Start only backend + dependencies
docker-compose up postgres redis qdrant backend celery_worker
```

---

## 📋 Docker — Logs & Status

```bash
# Check which containers are running and their health status
docker-compose ps

# Stream logs for all services
docker-compose logs -f

# Stream logs for a specific service
docker-compose logs -f backend
docker-compose logs -f celery_worker
docker-compose logs -f frontend
docker-compose logs -f postgres
docker-compose logs -f qdrant
docker-compose logs -f redis

# View last 100 lines of backend logs
docker-compose logs --tail=100 backend
```

---

## 🐍 Backend — FastAPI (inside Docker)

```bash
# Open a shell inside the running backend container
docker-compose exec backend bash

# Run database migrations / check table creation
docker-compose exec backend python -c "from app.core.database import Base, engine; Base.metadata.create_all(engine); print('Tables OK')"

# Install a new Python package (then rebuild)
# 1. Add to backend/requirements.txt
# 2. Then:
docker-compose up --build backend celery_worker

# Run the test pipeline script
docker-compose exec backend python /app/../scripts/test_pipeline.py
```

---

## ⚡ Celery Worker

```bash
# Check active Celery tasks
docker-compose exec celery_worker celery -A app.core.celery_app inspect active

# Check registered Celery tasks
docker-compose exec celery_worker celery -A app.core.celery_app inspect registered

# Purge all pending tasks from the queue
# ⚠️  Destructive — clears the task queue
docker-compose exec celery_worker celery -A app.core.celery_app purge
```

---

## 🗄️ Database — PostgreSQL

```bash
# Open a psql shell inside the postgres container
docker-compose exec postgres psql -U $POSTGRES_USER -d $POSTGRES_DB

# List all tables
docker-compose exec postgres psql -U $POSTGRES_USER -d $POSTGRES_DB -c "\dt"

# Dump the database to a file
docker-compose exec postgres pg_dump -U $POSTGRES_USER $POSTGRES_DB > backup.sql

# Restore from a dump
docker-compose exec -T postgres psql -U $POSTGRES_USER -d $POSTGRES_DB < backup.sql
```

---

## 🔍 Qdrant — Vector Database

```bash
# Check Qdrant health
curl http://localhost:6333/healthz

# List all collections
curl http://localhost:6333/collections

# Get info about a specific collection
curl http://localhost:6333/collections/documents
```

---

## 🌐 Frontend — Vite Dev Server

```bash
# Run from: c:\Projects\estimateIQ\frontend\

# Install dependencies (first time or after package.json changes)
npm install

# Start dev server on port 7000 with hot reload
npm run dev

# Type-check without building
npm run type-check

# Build for production (outputs to dist/)
npm run build

# Preview the production build locally
npm run preview

# Lint all TypeScript/TSX files
npm run lint
```

---

## 🔗 Service URLs

| Service        | URL                          | Notes                        |
|----------------|------------------------------|------------------------------|
| Frontend       | http://localhost:7000        | Vite dev server              |
| Backend API    | http://localhost:8000        | FastAPI                      |
| Swagger UI     | http://localhost:8000/docs   | Interactive API docs         |
| ReDoc          | http://localhost:8000/redoc  | Alternative API docs         |
| Health Check   | http://localhost:8000/health | Backend liveness probe       |
| Qdrant UI      | http://localhost:6333/dashboard | Vector DB dashboard       |
| PostgreSQL     | localhost:5432               | Use psql or any DB client    |
| Redis          | localhost:6379               | Use redis-cli                |

---

## 🧹 Cleanup

```bash
# Remove all stopped containers
docker container prune

# Remove unused images (frees disk space)
docker image prune

# Remove everything — containers, images, volumes, networks
# ⚠️  Nuclear option — use only to fully reset
docker system prune -a --volumes

# Delete frontend build artifacts
# Run from: c:\Projects\estimateIQ\frontend\
rm -rf dist node_modules
```

---

## 🔄 Common Workflows

```bash
# --- After pulling latest code ---
docker-compose up --build

# --- After changing Python dependencies ---
# 1. Edit backend/requirements.txt
docker-compose up --build backend celery_worker

# --- After changing frontend dependencies ---
# Run from frontend/
npm install
# Vite hot-reloads automatically — no restart needed

# --- Full reset (wipe data and restart fresh) ---
docker-compose down -v
docker-compose up --build

# --- Check everything is healthy ---
docker-compose ps
curl http://localhost:8000/health
curl http://localhost:6333/healthz
```
