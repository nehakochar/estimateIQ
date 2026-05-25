# EstimateIQ — AI-powered Enterprise RFP Intelligence Platform

## What is this?

EstimateIQ automates the process of reading RFP (Request for Proposal) documents,
extracting requirements, and generating cost/effort estimates using AI.

This repository contains **Phase 1** — the backend foundation only.

---

## Project Structure

```
estimateIQ/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   │       └── health.py      ← health check endpoints
│   │   ├── core/
│   │   │   ├── config.py          ← reads .env into typed settings
│   │   │   ├── database.py        ← SQLAlchemy engine + session
│   │   │   └── celery_app.py      ← Celery task queue setup
│   │   ├── models/                ← SQLAlchemy DB models (future)
│   │   ├── schemas/               ← Pydantic request/response schemas (future)
│   │   ├── services/              ← business logic (future)
│   │   ├── tasks/                 ← Celery background tasks (future)
│   │   └── main.py                ← FastAPI app + router registration
│   ├── Dockerfile
│   └── requirements.txt
├── storage/                       ← uploaded files will go here (future)
├── docker-compose.yml
├── .env
└── README.md
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| API Framework | FastAPI |
| Database | PostgreSQL 16 |
| Vector DB | Qdrant |
| Task Queue | Celery + Redis |
| ORM | SQLAlchemy |
| Container | Docker + Docker Compose |
| Language | Python 3.12 |

---

## Prerequisites

Make sure you have these installed on your machine:

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (includes Docker Compose)
- Git

That's it. You do NOT need Python installed locally — everything runs inside Docker.

---

## How to Run Locally

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd estimateIQ
```

### 2. Create your `.env` file

The `.env` file is already included in this repo for local development.
For production, never commit real secrets — use a secrets manager instead.

### 3. Start all services

```bash
docker-compose up --build
```

This command:
- Builds the backend Docker image
- Starts PostgreSQL, Qdrant, Redis, the FastAPI backend, and the Celery worker
- All services start in the correct order (backend waits for DB to be healthy)

### 4. Verify everything is running

```bash
docker-compose ps
```

You should see all containers with status `running` or `healthy`.

### 5. Stop all services

```bash
docker-compose down
```

To also delete all stored data (database, vector store):

```bash
docker-compose down -v
```

---

## How to Test the APIs

### Option A — Swagger UI (recommended for beginners)

Open your browser and go to:

```
http://localhost:8000/docs
```

You'll see an interactive UI listing all endpoints. Click any endpoint → "Try it out" → "Execute".

### Option B — ReDoc (read-only documentation)

```
http://localhost:8000/redoc
```

### Option C — curl (command line)

**Liveness check** — is the app running?
```bash
curl http://localhost:8000/health
```
Expected response:
```json
{"status": "ok", "service": "estimateIQ API"}
```

**Database health** — can we reach PostgreSQL?
```bash
curl http://localhost:8000/health/db
```
Expected response:
```json
{"status": "ok", "database": "postgresql"}
```

**Qdrant health** — can we reach the vector database?
```bash
curl http://localhost:8000/health/qdrant
```
Expected response:
```json
{"status": "ok", "database": "qdrant", "collections_count": 0}
```

**Root endpoint**
```bash
curl http://localhost:8000/
```

---

## Environment Variables

All configuration lives in `.env`. Here's what each variable does:

| Variable | Description |
|---|---|
| `POSTGRES_USER` | PostgreSQL username |
| `POSTGRES_PASSWORD` | PostgreSQL password |
| `POSTGRES_DB` | Database name |
| `POSTGRES_PORT` | Host port mapped to PostgreSQL (default: 5433) |
| `DATABASE_URL` | Full SQLAlchemy connection string |
| `QDRANT_API_KEY` | API key to secure Qdrant |
| `QDRANT_PORT_HTTP` | Qdrant REST API port (default: 6333) |
| `QDRANT_PORT_GRPC` | Qdrant gRPC port (default: 6334) |
| `QDRANT_URL` | Full Qdrant URL |
| `BACKEND_PORT` | Host port for the FastAPI backend (default: 8000) |
| `REDIS_PORT` | Redis port (default: 6379) |
| `REDIS_URL` | Full Redis connection URL for Celery |

---

## Common Issues

**Port already in use**
If port 5433 or 8000 is taken, change the host port in `.env`:
```
POSTGRES_PORT=5434
BACKEND_PORT=8001
```

**Container won't start**
Check logs for a specific service:
```bash
docker-compose logs backend
docker-compose logs postgres
```

**Rebuild after code changes**
Auto-reload handles Python file changes automatically.
If you change `requirements.txt` or `Dockerfile`, rebuild:
```bash
docker-compose up --build
```
