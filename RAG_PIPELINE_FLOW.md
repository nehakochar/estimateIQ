# RAG Pipeline Trigger Flow

## Starting Point: File Upload

```
POST /upload
├─ files: List[UploadFile]
├─ project_id: str (existing project UUID)
└─ UploadService.process_upload()
```

---

## Complete Pipeline Chain

```
1. USER UPLOADS FILES
   ├─ POST /upload endpoint
   └─ UploadService validates & stores files
                         ↓
2. CELERY TASK DISPATCHED
   └─ process_document.delay(job_id, document_id)
      (from: app/services/upload_service.py, line ~340)
                         ↓
3. PARSING (PHASE 1-2)
   └─ @celery_app.task: process_document()
      (file: app/tasks/processing_tasks.py)
      └─ ProcessingService.run(job_id, document_id)
         ├─ Load document & job from DB
         ├─ Resolve file path on disk
         ├─ Call parser factory (PDF, DOCX, XLSX)
         ├─ Save parsed_content to Document.parsed_content
         └─ Mark document.upload_status = "parsed"
            (from: app/services/processing_service.py, line ~115)
                         ↓
4. TWO PIPELINES START IN PARALLEL
   ├─ Pipeline A: CHUNKING (PHASE 3-5)
   │  └─ chunk_document.delay(document_id, project_id)
   │     (from: app/services/processing_service.py, line ~120)
   │     └─ @celery_app.task: chunk_document()
   │        (file: app/tasks/chunking_tasks.py)
   │        └─ ChunkingService.run(document_id, project_id)
   │           ├─ Hierarchical chunking
   │           ├─ Build document structure
   │           ├─ Create DocumentChunk records
   │           └─ Mark document.upload_status = "chunked"
   │              └─ TRIGGERS semantic_chunk_document.delay()
   │                 (from: app/tasks/chunking_tasks.py, line ~45)
   │
   └─ Pipeline B: LLM EXTRACTION (PARALLEL)
      └─ extract_requirements_task.delay(document_id, project_id)
         (from: app/services/processing_service.py, line ~125)
         └─ @celery_app.task: extract_requirements_task()
            (file: app/tasks/extraction_tasks.py)
            └─ ExtractionService.run(document_id, project_id)
               ├─ Extract requirements using LLM (Gemini/Groq/Anthropic)
               ├─ Create ExtractedRequirement records
               └─ Mark status
                         ↓
5. SEMANTIC CHUNKING & CLASSIFICATION (PHASE 6-7)
   └─ @celery_app.task: semantic_chunk_document()
      (file: app/tasks/semantic_chunking_tasks.py)
      └─ SemanticChunkingService.run(document_id, project_id)
         ├─ Semantic chunking (create meaningful segments)
         ├─ Classification (requirement types)
         ├─ Create SemanticChunk records
         └─ Mark document.upload_status = "classified"
            └─ TRIGGERS embed_document.delay()
               (from: app/tasks/semantic_chunking_tasks.py, line ~52)
                         ↓
6. VECTOR EMBEDDINGS (PHASE 8) - RAG CORE
   └─ @celery_app.task: embed_document()
      (file: app/tasks/embedding_tasks.py)
      └─ EmbeddingPipeline.run(document_id, project_id)
         ├─ Generate embeddings for each chunk
         ├─ Store vectors in Qdrant (vector DB)
         ├─ Update SemanticChunk with embedding_vector
         └─ Mark document.upload_status = "embedded"
            └─ ✅ RAG PIPELINE COMPLETE
```

---

## Key Trigger Points

| Phase | Task | Triggered From | File |
|-------|------|---|---|
| **Parsing** | `process_document.delay()` | `/upload` endpoint → `UploadService` | `app/api/routes/upload.py:48` |
| **Chunking** | `chunk_document.delay()` | `ProcessingService._mark_completed()` | `app/services/processing_service.py:120` |
| **LLM Extraction** | `extract_requirements_task.delay()` | `ProcessingService._mark_completed()` | `app/services/processing_service.py:125` |
| **Semantic Chunking** | `semantic_chunk_document.delay()` | `chunk_document` task completion | `app/tasks/chunking_tasks.py:45` |
| **Embedding/RAG** | `embed_document.delay()` | `semantic_chunk_document` task completion | `app/tasks/semantic_chunking_tasks.py:52` |

---

## Execution Context

- **Web Framework**: FastAPI (sync request handler)
- **Background Queue**: Celery + Redis
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Vector Store**: Qdrant (for RAG embeddings)

All Celery tasks run in **separate worker processes** with their own DB sessions (SessionLocal), so they don't block the API.

---

## Where RAG is Stored

Once `embed_document()` completes:

1. **SemanticChunk records** in PostgreSQL contain:
   - `embedding_vector` (vector field for similarity search)
   - `text_content`
   - `document_id`
   - `project_id`
   - Classification metadata

2. **Qdrant vector database** stores:
   - Vector embeddings (searchable)
   - Metadata (document_id, project_id, chunk_id)

3. **Retrieval endpoint** (`GET /retrieval/search`) uses these vectors for semantic search

---

## File References

- **Upload trigger**: `c:\Projects\estimateIQ\backend\app\api\routes\upload.py`
- **Upload service**: `c:\Projects\estimateIQ\backend\app\services\upload_service.py`
- **Processing service**: `c:\Projects\estimateIQ\backend\app\services\processing_service.py`
- **Celery tasks**: `c:\Projects\estimateIQ\backend\app\tasks\*_tasks.py`
- **RAG embedding**: `c:\Projects\estimateIQ\backend\app\services\processing\embedding_pipeline.py`
