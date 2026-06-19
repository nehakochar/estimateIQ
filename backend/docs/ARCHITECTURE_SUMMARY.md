# EstimateIQ Architecture Summary

**Quick Reference Guide**

---

## What is EstimateIQ?

EstimateIQ is an **AI-powered RFP parsing platform** that automatically extracts and organizes requirements from documents.

**In one sentence:** Upload a PDF/DOCX/XLSX → Get searchable, categorized requirements.

---

## The Complete Flow

```
USER UPLOADS FILE
        ↓
BACKEND PARSES (extract text + tables)
        ↓
BACKEND CHUNKS (split into sections)
        ↓
BACKEND SEMANTICALLY CHUNKS (split large sections)
        ↓
BACKEND CLASSIFIES (label by type: functional, security, etc.)
        ↓
BACKEND EMBEDS (convert to AI vectors)
        ↓
BACKEND STORES (PostgreSQL + Qdrant)
        ↓
FRONTEND DISPLAYS (browse, search, view)
```

---

## Backend (Python + FastAPI)

### What it does:
- Receives uploaded files
- Parses text and tables
- Chunks documents into sections
- Classifies requirements
- Generates AI embeddings
- Stores everything in databases

### Key technologies:
- **FastAPI** — Web framework
- **PostgreSQL** — Relational database
- **Qdrant** — Vector database
- **Celery** — Task queue
- **Sentence Transformers** — AI embeddings
- **LlamaIndex** — Text processing

### Key files:
```
backend/app/
├── main.py                          # FastAPI app
├── core/
│   ├── config.py                    # Configuration
│   ├── database.py                  # DB connection
│   └── celery_app.py                # Task queue
├── api/routes/                      # API endpoints
├── services/
│   ├── parsers/                     # PDF/DOCX/XLSX parsing
│   ├── chunking/                    # Document chunking
│   ├── semantic_chunking/           # Semantic splitting
│   ├── classification/              # Requirement classification
│   ├── embeddings/                  # AI embeddings
│   └── retrieval/                   # Search
├── models/                          # Database models
└── schemas/                         # API request/response schemas
```

### Processing pipeline:
1. **Parsing** — Extract text from files
2. **Chunking** — Split into sections
3. **Semantic Chunking** — Split large sections further
4. **Classification** — Label by type
5. **Embedding** — Convert to vectors
6. **Storage** — Save to databases

---

## Frontend (React + TypeScript)

### What it does:
- Provides user interface
- Handles file uploads
- Shows real-time progress
- Displays requirements
- Enables search

### Key technologies:
- **React 18** — UI framework
- **TypeScript** — Type safety
- **Redux Toolkit** — State management
- **RTK Query** — Data fetching
- **React Router** — Routing
- **Vite** — Build tool

### Key files:
```
frontend/src/
├── App.tsx                          # Root component
├── main.tsx                         # Entry point
├── features/
│   ├── discovery/
│   │   └── CreateProjectModal.tsx   # Create project
│   └── workspace/
│       ├── panels/
│       │   ├── UploadPanel.tsx      # File upload
│       │   ├── RequirementsPanel.tsx # Browse requirements
│       │   ├── DocumentsPanel.tsx   # Document list
│       │   └── EstimatePanel.tsx    # Estimation
│       └── WorkspaceLayout.tsx      # Main layout
├── services/                        # API clients
│   ├── projectsApi.ts
│   ├── documentsApi.ts
│   └── retrievalApi.ts
└── store/                           # Redux state
    └── slices/
        ├── uploadSlice.ts
        └── workspaceSlice.ts
```

### User workflows:
1. **Create Project** — Name your RFP project
2. **Upload Files** — Drag-and-drop PDF/DOCX/XLSX
3. **Monitor Progress** — Watch real-time processing
4. **Browse Requirements** — View by category
5. **Search** — Find requirements by keyword

---

## Databases

### PostgreSQL (Relational)
Stores structured data:
- **projects** — Project metadata
- **documents** — File info and status
- **document_chunks** — Extracted requirements
- **processing_jobs** — Task status

### Qdrant (Vector)
Stores AI embeddings:
- **rfp_chunks** collection
  - Vector: 384-dimensional embedding
  - Metadata: chunk_id, text, category, page_number

---

## API Endpoints

### Projects
```
POST   /projects                     # Create project
GET    /projects                     # List projects
GET    /projects/{id}                # Get project
GET    /projects/{id}/status         # Get processing status
```

### Upload
```
POST   /upload                       # Upload files
```

### Search
```
POST   /search                       # Semantic search
GET    /search/category              # Browse by category
```

### Documents
```
GET    /documents/{id}               # Get document
GET    /documents/{id}/semantic-chunks  # Get chunks
```

---

## Key Concepts

### Chunk
A meaningful piece of text from a document (e.g., a section or requirement).

### Embedding
A mathematical representation of text as a vector (384 numbers). Enables semantic search.

### Semantic Search
Finding results based on meaning, not just keywords. Example: "user login" finds "OAuth2 authentication".

### Classification
Labeling chunks by type: Functional, Security, Non-Functional, etc.

### Celery
Background task queue that processes documents asynchronously.

### RTK Query
Data fetching library that handles API calls, caching, and polling.

---

## Processing Stages

Each document goes through these stages:

1. **uploaded** — File received
2. **parsing** — Extracting text
3. **parsed** — Text extracted
4. **chunking** — Splitting into sections
5. **chunked** — Sections created
6. **classifying** — Labeling requirements
7. **classified** — Labels assigned
8. **embedding** — Generating vectors
9. **embedded** — Vectors stored (COMPLETE)

---

## File Types Supported

- **PDF** — PyMuPDF extracts text + tables
- **DOCX** — python-docx extracts paragraphs + tables
- **XLSX** — openpyxl extracts cell values

---

## Requirement Categories

- **Functional** — Core features
- **Non-Functional** — Performance, scalability
- **Security** — Security, privacy, compliance
- **Integration** — Third-party integrations
- **UI/UX** — User interface and experience
- **Workflow & Roles** — User roles and workflows
- **Data Validation** — Data validation rules
- **Infrastructure** — Deployment and infrastructure
- **Risks & Assumptions** — Risks and assumptions
- **Open Questions** — Unclear items
- **Out of Scope** — Explicitly out of scope

---

## Development Setup

### Backend
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Services
- PostgreSQL: `localhost:5432`
- Qdrant: `localhost:6333`
- Redis: `localhost:6379`
- Backend API: `localhost:8000`
- Frontend: `localhost:3000`

---

## Common Tasks

### Upload a document
1. Click "Create Project"
2. Enter project name
3. Drag files into upload zone
4. Click "Upload"
5. Watch progress

### Search requirements
1. Click "Requirements" tab
2. Type search query
3. Click "Search"
4. View results

### Browse by category
1. Click "Requirements" tab
2. Click category tab (e.g., "Security")
3. View requirements in that category

### View requirement details
1. Click on a requirement row
2. Expands to show metadata
3. See section, page, confidence score

---

## Troubleshooting

### API returns empty results
- Check that documents finished processing (status = "embedded")
- Verify database connection
- Check Qdrant is running

### Frontend can't connect to backend
- Verify backend is running on `localhost:8000`
- Check CORS settings in `.env`
- Check network tab in browser DevTools

### Processing stuck
- Check Celery worker is running
- Check Redis is running
- Check database connection

### Search not working
- Verify embeddings were generated
- Check Qdrant collection exists
- Try re-processing document

---

## For More Details

- **Backend:** Read `BACKEND_ARCHITECTURE.md`
- **Frontend:** Read `FRONTEND_ARCHITECTURE.md`
- **Code:** Explore `backend/app/` and `frontend/src/`

---

## Quick Stats

- **Embedding model:** BAAI/bge-small-en-v1.5 (384-dimensional)
- **Max file size:** 50MB (PDF), 20MB (DOCX), 15MB (XLSX)
- **Max files per upload:** 10
- **Chunk size:** ~1-2KB per chunk
- **Search speed:** <100ms for 1000 chunks
- **Categories:** 11 requirement types

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND (React)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Upload     │  │ Requirements │  │  Documents   │       │
│  │   Panel      │  │   Panel      │  │   Panel      │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│         │                  │                  │              │
│         └──────────────────┼──────────────────┘              │
│                            │                                 │
│                    Redux + RTK Query                         │
│                            │                                 │
└────────────────────────────┼─────────────────────────────────┘
                             │
                    HTTP REST API
                             │
┌────────────────────────────┼─────────────────────────────────┐
│                        BACKEND (FastAPI)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Upload     │  │   Search     │  │  Documents   │       │
│  │   Routes     │  │   Routes     │  │   Routes     │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│         │                  │                  │              │
│         └──────────────────┼──────────────────┘              │
│                            │                                 │
│                    Services Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Parsing    │  │   Chunking   │  │ Embeddings   │       │
│  │   Service    │  │   Service    │  │   Service    │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│         │                  │                  │              │
│         └──────────────────┼──────────────────┘              │
│                            │                                 │
│                    Celery Task Queue                         │
│                            │                                 │
└────────────────────────────┼─────────────────────────────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
         ┌──────────▼──────────┐  ┌──▼──────────────┐
         │   PostgreSQL        │  │   Qdrant        │
         │   (Relational DB)   │  │   (Vector DB)   │
         │                     │  │                 │
         │ - Projects          │  │ - Embeddings    │
         │ - Documents         │  │ - Metadata      │
         │ - Chunks            │  │                 │
         │ - Jobs              │  │                 │
         └─────────────────────┘  └─────────────────┘
```

---

## Next Steps

1. **Read the detailed guides:**
   - `BACKEND_ARCHITECTURE.md` — Deep dive into backend
   - `FRONTEND_ARCHITECTURE.md` — Deep dive into frontend

2. **Explore the code:**
   - Backend: `backend/app/services/`
   - Frontend: `frontend/src/features/`

3. **Run locally:**
   - Start backend: `python -m uvicorn app.main:app --reload`
   - Start frontend: `npm run dev`
   - Open `http://localhost:3000`

4. **Test the API:**
   - Visit `http://localhost:8000/docs` for interactive API docs
   - Try uploading a test PDF
   - Monitor processing in real-time

---

**Created:** June 1, 2026  
**For:** EstimateIQ Development Team  
**Audience:** Beginners and new team members
