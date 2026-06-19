# EstimateIQ Visual Reference Guide

**Diagrams, Flowcharts, and Visual Explanations**

---

## 1. Complete System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                           │
│                          USER BROWSER                                    │
│                                                                           │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                                                                  │   │
│  │                    FRONTEND (React + Redux)                     │   │
│  │                                                                  │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │   │
│  │  │   Upload    │  │ Requirements│  │  Documents  │             │   │
│  │  │   Panel     │  │   Panel     │  │   Panel     │             │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘             │   │
│  │         │                │                │                     │   │
│  │         └────────────────┼────────────────┘                     │   │
│  │                          │                                      │   │
│  │                   RTK Query (Data Fetching)                     │   │
│  │                   Redux (State Management)                      │   │
│  │                                                                  │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTP REST API
                                    │
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                           │
│                          BACKEND SERVER                                  │
│                                                                           │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                                                                  │   │
│  │                    FastAPI Application                          │   │
│  │                                                                  │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │   │
│  │  │  Upload  │  │  Search  │  │Documents │  │  Health  │        │   │
│  │  │  Routes  │  │  Routes  │  │  Routes  │  │  Routes  │        │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │   │
│  │         │            │             │             │             │   │
│  │         └────────────┼─────────────┼─────────────┘             │   │
│  │                      │             │                           │   │
│  │              Services Layer        │                           │   │
│  │                      │             │                           │   │
│  │  ┌──────────────────┼─────────────┼──────────────────┐        │   │
│  │  │                  │             │                  │        │   │
│  │  ▼                  ▼             ▼                  ▼        │   │
│  │ ┌────────┐  ┌────────────┐  ┌──────────┐  ┌──────────────┐   │   │
│  │ │Parsing │  │  Chunking  │  │Semantic  │  │Embeddings &  │   │   │
│  │ │Service │  │  Service   │  │Chunking  │  │Classification   │   │   │
│  │ └────────┘  └────────────┘  └──────────┘  └──────────────┘   │   │
│  │                                                                  │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                           │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                                                                  │   │
│  │                    Celery Task Queue                            │   │
│  │                                                                  │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │   │
│  │  │Parse Task    │  │Chunk Task    │  │Embed Task    │          │   │
│  │  │(Async)       │  │(Async)       │  │(Async)       │          │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘          │   │
│  │                                                                  │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
            ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
            │ PostgreSQL   │  │   Qdrant     │  │    Redis     │
            │ (Relational) │  │   (Vector)   │  │   (Cache)    │
            │              │  │              │  │              │
            │ - Projects   │  │ - Embeddings │  │ - Job Queue  │
            │ - Documents  │  │ - Metadata   │  │ - Sessions   │
            │ - Chunks     │  │              │  │              │
            │ - Jobs       │  │              │  │              │
            └──────────────┘  └──────────────┘  └──────────────┘
```

---

## 2. Document Processing Pipeline

```
INPUT: User uploads file (PDF, DOCX, XLSX)
│
├─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  PHASE 1: PARSING                                              │
│  ─────────────────                                             │
│  Extract text and tables from file                             │
│                                                                 │
│  PDF:  PyMuPDF → Extract text + detect tables                  │
│  DOCX: python-docx → Extract paragraphs + tables               │
│  XLSX: openpyxl → Extract cell values                          │
│                                                                 │
│  OUTPUT: Structured pages with text and metadata               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
│
├─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  PHASE 2: CHUNKING                                             │
│  ──────────────────                                            │
│  Split document into meaningful sections                       │
│                                                                 │
│  Step 1: Detect headings (H1, H2, H3)                          │
│  Step 2: Build hierarchy (sections → subsections)              │
│  Step 3: Create chunks (one per section)                       │
│                                                                 │
│  OUTPUT: 50-500 chunks per document                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
│
├─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  PHASE 3: SEMANTIC CHUNKING                                    │
│  ──────────────────────────                                    │
│  Split large chunks using AI embeddings                        │
│                                                                 │
│  For each chunk:                                               │
│    1. Compute embeddings for sentences                         │
│    2. Find natural break points                                │
│    3. Split at those points                                    │
│                                                                 │
│  OUTPUT: Smaller, more focused chunks                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
│
├─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  PHASE 4: CLASSIFICATION                                       │
│  ────────────────────────                                      │
│  Label each chunk by requirement type                          │
│                                                                 │
│  Categories:                                                   │
│    • Functional                                                │
│    • Non-Functional                                            │
│    • Security                                                  │
│    • Integration                                               │
│    • UI/UX                                                     │
│    • Workflow & Roles                                          │
│    • Data Validation                                           │
│    • Infrastructure                                            │
│    • Risks & Assumptions                                       │
│    • Open Questions                                            │
│    • Out of Scope                                              │
│                                                                 │
│  OUTPUT: Chunks with category labels and confidence scores     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
│
├─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  PHASE 5: EMBEDDING                                            │
│  ──────────────────                                            │
│  Convert text to AI vectors                                    │
│                                                                 │
│  Model: BAAI/bge-small-en-v1.5                                 │
│  Output: 384-dimensional vectors                               │
│                                                                 │
│  Example:                                                      │
│    Text: "User authentication via OAuth2"                      │
│    Vector: [0.123, -0.456, 0.789, ..., 0.234]                 │
│                                                                 │
│  OUTPUT: Vectors stored in Qdrant                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
│
├─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  PHASE 6: STORAGE                                              │
│  ────────────────                                              │
│  Save all data to databases                                    │
│                                                                 │
│  PostgreSQL:                                                   │
│    • Document metadata                                         │
│    • Chunk text and metadata                                   │
│    • Processing status                                         │
│                                                                 │
│  Qdrant:                                                       │
│    • 384-dimensional embeddings                                │
│    • Chunk metadata                                            │
│                                                                 │
│  OUTPUT: Fully indexed and searchable                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
│
OUTPUT: Requirements ready for browsing and search
```

---

## 3. Data Flow: Upload to Display

```
┌─────────────────────────────────────────────────────────────────┐
│ USER UPLOADS FILE                                               │
│ (Drag-and-drop or file picker)                                  │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND: UploadPanel                                           │
│ • Validates file type (.pdf, .docx, .xlsx)                     │
│ • Prepares FormData with files                                  │
│ • Calls POST /upload                                            │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ BACKEND: POST /upload                                           │
│ • Receives files                                                │
│ • Creates Project row                                           │
│ • Creates Document rows                                         │
│ • Saves files to disk                                           │
│ • Creates ProcessingJob rows                                    │
│ • Returns project_id and job_ids                                │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND: PipelineView                                          │
│ • Receives project_id                                           │
│ • Starts polling GET /projects/{id}/status every 2 seconds      │
│ • Shows progress bars and stage pills                           │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ BACKEND: Celery Tasks (Async)                                   │
│                                                                 │
│ Task 1: parse_document                                          │
│   • Extract text from file                                      │
│   • Save to document.parsed_content                             │
│   • Update status: "parsed"                                     │
│   • Queue Task 2                                                │
│                                                                 │
│ Task 2: chunk_document                                          │
│   • Detect headings                                             │
│   • Build hierarchy                                             │
│   • Create chunks                                               │
│   • Save to document_chunks table                               │
│   • Update status: "chunked"                                    │
│   • Queue Task 3                                                │
│                                                                 │
│ Task 3: semantic_chunk_document                                 │
│   • For each chunk, split using embeddings                      │
│   • Save sub-chunks                                             │
│   • Update status: "semantic_chunked"                           │
│   • Queue Task 4                                                │
│                                                                 │
│ Task 4: classify_chunks                                         │
│   • For each chunk, classify by type                            │
│   • Update category and confidence_score                        │
│   • Update status: "classified"                                 │
│   • Queue Task 5                                                │
│                                                                 │
│ Task 5: embed_chunks                                            │
│   • For each chunk, generate embedding                          │
│   • Store in Qdrant                                             │
│   • Update status: "embedded"                                   │
│                                                                 │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND: Polling Updates                                       │
│ • GET /projects/{id}/status returns updated progress            │
│ • Progress bars update in real-time                             │
│ • Stage pills show completed/in-progress stages                 │
│ • When is_ready = true, shows "Documents Ready"                 │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ USER CLICKS "REQUIREMENTS" TAB                                   │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND: RequirementsPanel                                     │
│ • Calls GET /search/category?category=functional                │
│ • Receives requirements list                                    │
│ • Displays in table format                                      │
│ • Shows category tabs                                           │
│ • Enables search                                                │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ BACKEND: GET /search/category                                   │
│ • Query Qdrant for chunks in category                           │
│ • Return top K results with metadata                            │
│ • Include: text, category, page, confidence, req_id             │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND: RequirementRow                                        │
│ • Display requirement in table row                              │
│ • Show ID, title, type badge, description                       │
│ • Allow expand to see metadata                                  │
│ • Color-code by type                                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Database Schema Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        PostgreSQL                               │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────┐
│     projects         │
├──────────────────────┤
│ id (UUID) [PK]       │
│ name (string)        │
│ description (text)   │
│ created_at (ts)      │
│ updated_at (ts)      │
└──────────────────────┘
         │
         │ 1:N
         │
┌──────────────────────────────────────┐
│         documents                    │
├──────────────────────────────────────┤
│ id (UUID) [PK]                       │
│ project_id (UUID) [FK]               │
│ file_name (string)                   │
│ file_type (string)                   │
│ stored_path (string)                 │
│ upload_status (string)               │
│ parsed_content (JSON)                │
│ created_at (ts)                      │
│ updated_at (ts)                      │
└──────────────────────────────────────┘
         │
         │ 1:N
         │
┌──────────────────────────────────────┐
│      document_chunks                 │
├──────────────────────────────────────┤
│ id (UUID) [PK]                       │
│ document_id (UUID) [FK]              │
│ project_id (UUID) [FK]               │
│ text (text)                          │
│ section (string)                     │
│ subsection (string)                  │
│ page_number (int)                    │
│ category (string)                    │
│ confidence_score (float)             │
│ chunk_type (string)                  │
│ token_count (int)                    │
│ created_at (ts)                      │
│ updated_at (ts)                      │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│     processing_jobs                  │
├──────────────────────────────────────┤
│ id (UUID) [PK]                       │
│ document_id (UUID) [FK]              │
│ status (string)                      │
│ started_at (ts)                      │
│ completed_at (ts)                    │
│ error_message (text)                 │
│ created_at (ts)                      │
└──────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                          Qdrant                                 │
└─────────────────────────────────────────────────────────────────┘

Collection: "rfp_chunks"
├─ Vector: [384 floats]
├─ Payload:
│  ├─ chunk_id (UUID)
│  ├─ text (string)
│  ├─ category (string)
│  ├─ page_number (int)
│  ├─ document_id (UUID)
│  └─ project_id (UUID)
```

---

## 5. Component Hierarchy (Frontend)

```
App
├── Router
│   ├── HomePage
│   │   └── CreateProjectModal
│   │
│   └── WorkspacePage
│       ├── WorkspaceLayout
│       │   ├── Sidebar
│       │   │   ├── ProjectList
│       │   │   └── PanelTabs
│       │   │
│       │   └── MainContent
│       │       ├── UploadPanel
│       │       │   ├── UploadZone
│       │       │   ├── FileList
│       │       │   └── PipelineView
│       │       │       └── DocCard (multiple)
│       │       │
│       │       ├── RequirementsPanel
│       │       │   ├── SearchBar
│       │       │   ├── CategoryTabs
│       │       │   └── RequirementsTable
│       │       │       └── RequirementRow (multiple)
│       │       │           └── MetaTags
│       │       │
│       │       ├── DocumentsPanel
│       │       │   └── DocumentList
│       │       │       └── DocumentCard (multiple)
│       │       │
│       │       └── EstimatePanel
│       │           ├── EstimateSummary
│       │           └── EstimateBreakdown
```

---

## 6. State Management Flow

```
Redux Store
│
├── upload slice
│   ├── isUploading (boolean)
│   ├── isSuccess (boolean)
│   ├── uploadError (string | null)
│   ├── currentProjectId (string | null)
│   └── toastShown (boolean)
│
├── workspace slice
│   ├── activePanel (string)
│   └── selectedProject (string | null)
│
└── RTK Query Cache
    ├── projectsApi
    │   ├── listProjects
    │   ├── createProject
    │   └── getProjectStatus
    │
    ├── documentsApi
    │   ├── getProjectStatus
    │   └── getDocumentDetails
    │
    └── retrievalApi
        ├── searchByCategory
        └── search
```

---

## 7. API Request/Response Flow

```
FRONTEND                          BACKEND
   │                                 │
   │  POST /upload                   │
   │  (multipart/form-data)          │
   ├────────────────────────────────►│
   │                                 │
   │                    Create Project
   │                    Create Documents
   │                    Queue Tasks
   │                                 │
   │  ◄────────────────────────────┤
   │  {project_id, documents}        │
   │                                 │
   │  GET /projects/{id}/status      │
   │  (polling every 2s)             │
   ├────────────────────────────────►│
   │                                 │
   │                    Query DB
   │                    Calculate progress
   │                                 │
   │  ◄────────────────────────────┤
   │  {total_docs, ready_docs,       │
   │   documents: [...]}             │
   │                                 │
   │  POST /search                   │
   │  {query, topK}                  │
   ├────────────────────────────────►│
   │                                 │
   │                    Convert query to embedding
   │                    Search Qdrant
   │                    Return results
   │                                 │
   │  ◄────────────────────────────┤
   │  {results: [...]}               │
   │                                 │
```

---

## 8. Processing Status Stages

```
Document Status Progression:

uploaded
   │
   ▼
parsing ──► parsed
   │
   ▼
chunking ──► chunked
   │
   ▼
semantic_chunking ──► semantic_chunked
   │
   ▼
classifying ──► classified
   │
   ▼
embedding ──► embedded ✓ COMPLETE
   │
   ▼
(Optional) failed ✗ ERROR

Progress Percentages:
uploaded:   5%
parsed:     30%
chunked:    55%
classified: 75%
embedded:   100%
```

---

## 9. Semantic Search Concept

```
Traditional Search:
  Query: "user login"
  Results: Only documents with "user" AND "login"
  ✗ Misses: "OAuth2 authentication", "sign in", "credentials"

Semantic Search:
  Query: "user login"
  Convert to embedding: [0.123, -0.456, ..., 0.234]
  
  Find similar embeddings:
    "OAuth2 authentication" [0.125, -0.450, ..., 0.240] ✓ Similar
    "sign in" [0.120, -0.460, ..., 0.235] ✓ Similar
    "database performance" [0.001, 0.999, ..., 0.100] ✗ Different
  
  Results: All semantically related requirements
  ✓ Finds: "OAuth2 authentication", "sign in", "credentials"
```

---

## 10. Requirement Classification Example

```
Input Text:
"The system must support OAuth2 and SAML authentication methods.
 Users can reset passwords via email. All authentication attempts
 must be logged for security auditing."

Classification Process:
  1. Scan for keywords
     - "OAuth2" → security keyword
     - "SAML" → security keyword
     - "authentication" → security keyword
     - "logged" → security keyword
     - "security auditing" → security keyword
  
  2. Calculate confidence
     - Security keywords: 5
     - Total keywords: 5
     - Confidence: 5/5 = 1.0 (100%)
  
  3. Assign category
     - Category: "security_compliance"
     - Confidence: 0.95 (high confidence)

Output:
  Category: "security_compliance"
  Confidence: 0.95
  Type Label: "Security"
```

---

## 11. File Upload Process

```
User selects files
       │
       ▼
Frontend validates
  • File type (.pdf, .docx, .xlsx)
  • File size (< 50MB for PDF, etc.)
       │
       ▼
User clicks "Upload"
       │
       ▼
Frontend creates FormData
  • Appends each file
  • Sets project name
       │
       ▼
Frontend calls POST /upload
       │
       ▼
Backend receives request
  • Validates files again
  • Creates project row
  • Creates document rows
  • Saves files to disk
  • Creates job rows
       │
       ▼
Backend returns response
  • project_id
  • documents array
  • job_ids
       │
       ▼
Frontend receives response
  • Stores in Redux
  • Navigates to workspace
  • Starts polling status
       │
       ▼
Frontend shows PipelineView
  • Progress bars
  • Stage pills
  • Real-time updates
```

---

## 12. Search Flow

```
User types query
       │
       ▼
User clicks "Search"
       │
       ▼
Frontend calls POST /search
  • query: "user authentication"
  • projectId: "proj-123"
  • topK: 50
       │
       ▼
Backend receives request
  • Convert query to embedding
  • Search Qdrant for similar vectors
  • Return top 50 results
       │
       ▼
Backend returns response
  • results array
  • total_results count
  • Each result includes:
    - chunk_id
    - text
    - category
    - page_number
    - confidence_score
    - req_id
    - type_label
       │
       ▼
Frontend receives response
  • Stores in RTK Query cache
  • Renders RequirementsTable
  • Shows results
       │
       ▼
User clicks on result
       │
       ▼
RequirementRow expands
  • Shows full metadata
  • Section, page, confidence
```

---

## 13. Technology Stack Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                       │
│                                                             │
│  React Components                                           │
│  ├── UploadPanel                                            │
│  ├── RequirementsPanel                                      │
│  ├── DocumentsPanel                                         │
│  └── EstimatePanel                                          │
│                                                             │
│  State Management                                           │
│  ├── Redux (global state)                                   │
│  └── RTK Query (data fetching)                              │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                    API LAYER                                │
│                                                             │
│  FastAPI Routes                                             │
│  ├── /upload                                                │
│  ├── /search                                                │
│  ├── /projects                                              │
│  └── /documents                                             │
│                                                             │
│  HTTP REST                                                  │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                    BUSINESS LOGIC LAYER                      │
│                                                             │
│  Services                                                   │
│  ├── ParsingService                                         │
│  ├── ChunkingService                                        │
│  ├── SemanticChunkingService                                │
│  ├── ClassificationService                                  │
│  ├── EmbeddingService                                       │
│  └── RetrievalService                                       │
│                                                             │
│  Celery Tasks                                               │
│  ├── parse_document                                         │
│  ├── chunk_document                                         │
│  ├── classify_chunks                                        │
│  └── embed_chunks                                           │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                    DATA LAYER                               │
│                                                             │
│  Databases                                                  │
│  ├── PostgreSQL (Relational)                                │
│  │   ├── projects                                           │
│  │   ├── documents                                          │
│  │   ├── document_chunks                                    │
│  │   └── processing_jobs                                    │
│  │                                                          │
│  ├── Qdrant (Vector)                                        │
│  │   └── rfp_chunks collection                              │
│  │                                                          │
│  └── Redis (Cache)                                          │
│      └── Job queue                                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 14. Error Handling Flow

```
Error occurs during processing
       │
       ▼
Service catches exception
       │
       ▼
Log error message
       │
       ▼
Update database status
  • document.upload_status = "failed"
  • job.status = "failed"
  • job.error_message = "..."
       │
       ▼
Frontend polls status
       │
       ▼
Frontend sees status = "failed"
       │
       ▼
Frontend shows error message
  • Red background
  • Error icon
  • Error text
       │
       ▼
User can retry or upload different file
```

---

## 15. Real-Time Progress Updates

```
Backend processes document
       │
       ├─► Update status: "parsing"
       │   └─► Frontend polls → Shows "Parsing: 5%"
       │
       ├─► Update status: "parsed"
       │   └─► Frontend polls → Shows "Parsing: 30%"
       │
       ├─► Update status: "chunking"
       │   └─► Frontend polls → Shows "Chunking: 55%"
       │
       ├─► Update status: "chunked"
       │   └─► Frontend polls → Shows "Chunking: 75%"
       │
       ├─► Update status: "embedding"
       │   └─► Frontend polls → Shows "Embedding: 90%"
       │
       └─► Update status: "embedded"
           └─► Frontend polls → Shows "Complete: 100%"

Polling Interval: 2 seconds
Update Frequency: Every 2 seconds
User Experience: Smooth, real-time progress
```

---

**These diagrams provide visual representations of:**
- System architecture
- Data flow
- Database schema
- Component hierarchy
- State management
- API communication
- Processing pipeline
- Error handling
- Real-time updates

**Use these diagrams alongside the detailed documentation for a complete understanding of the system.**
