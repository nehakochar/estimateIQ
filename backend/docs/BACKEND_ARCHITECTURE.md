# EstimateIQ Backend Architecture Guide

**For Beginners: A Complete Walkthrough of How Documents Are Processed**

---

## Table of Contents

1. [Overview](#overview)
2. [The Big Picture: Document Processing Pipeline](#the-big-picture-document-processing-pipeline)
3. [Technology Stack](#technology-stack)
4. [Detailed Pipeline Phases](#detailed-pipeline-phases)
5. [Database Schema](#database-schema)
6. [API Endpoints](#api-endpoints)
7. [How Data Flows Through the System](#how-data-flows-through-the-system)
8. [Key Concepts Explained](#key-concepts-explained)

---

## Overview

EstimateIQ is an **AI-powered RFP (Request for Proposal) parsing system**. When you upload a PDF, DOCX, or XLSX file, the backend:

1. **Extracts** text and tables from the document
2. **Chunks** the text into meaningful sections
3. **Classifies** each chunk as a requirement type (functional, security, etc.)
4. **Embeds** chunks into AI vectors for semantic search
5. **Stores** everything in a database for retrieval

The goal: **Turn messy RFP documents into searchable, structured requirements.**

---

## The Big Picture: Document Processing Pipeline

When you upload a file, here's what happens:

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. USER UPLOADS FILE (PDF, DOCX, XLSX)                          │
│    → Frontend sends file to POST /upload                         │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│ 2. PARSING (Extract text & tables)                              │
│    → PDF: PyMuPDF extracts text + table detection               │
│    → DOCX: python-docx extracts paragraphs + tables             │
│    → XLSX: openpyxl extracts cell values                        │
│    → Result: Structured pages with text + metadata              │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│ 3. CHUNKING (Split into sections)                               │
│    → Detect headings (H1, H2, H3)                               │
│    → Build hierarchy (sections → subsections)                   │
│    → Create chunks (one per section)                            │
│    → Result: ~50-500 chunks per document                        │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│ 4. SEMANTIC CHUNKING (Split large chunks further)               │
│    → Use AI embeddings to find natural break points             │
│    → Result: Smaller, more focused chunks                       │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│ 5. CLASSIFICATION (Label each chunk)                            │
│    → Functional, Non-Functional, Security, etc.                 │
│    → Uses keyword matching + confidence scoring                 │
│    → Result: Each chunk has a category label                    │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│ 6. EMBEDDING (Convert to AI vectors)                            │
│    → Use BAAI/bge-small-en-v1.5 model                           │
│    → Each chunk → 384-dimensional vector                        │
│    → Store in Qdrant vector database                            │
│    → Result: Searchable semantic vectors                        │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│ 7. STORAGE (Save to database)                                   │
│    → PostgreSQL: Document metadata + chunks                     │
│    → Qdrant: Vector embeddings for search                       │
│    → Result: Fully indexed and searchable                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Backend Framework
- **FastAPI** — Modern Python web framework for building APIs
  - Handles HTTP requests/responses
  - Auto-generates API documentation at `/docs`
  - Built-in validation using Pydantic

### Document Parsing
- **PyMuPDF (fitz)** — Extract text from PDFs
  - Detects tables and formats them as readable text
  - Preserves page numbers and layout info
  
- **python-docx** — Extract text from Word documents
  - Reads paragraphs, tables, and formatting
  - Converts tables to "Label: Value" format
  
- **openpyxl** — Extract data from Excel spreadsheets
  - Reads cell values and sheet structure

### Text Processing
- **LlamaIndex** — AI-powered text chunking and splitting
  - `SemanticSplitterNodeParser` — Uses embeddings to find natural break points
  - `SentenceSplitter` — Fallback token-based splitting
  
- **NLTK** — Natural Language Toolkit
  - Sentence tokenization
  - Text analysis

### AI & Embeddings
- **Sentence Transformers** — BAAI/bge-small-en-v1.5 model
  - Converts text to 384-dimensional vectors
  - Used for semantic search and similarity
  - Runs locally (no API calls needed)

### Databases
- **PostgreSQL** — Relational database
  - Stores documents, chunks, metadata
  - JSON columns for flexible data storage
  
- **Qdrant** — Vector database
  - Stores 384-dimensional embeddings
  - Enables fast semantic search
  - Similarity search in milliseconds

### Task Queue
- **Celery** — Distributed task queue
  - Runs long-running jobs asynchronously
  - Prevents blocking the API
  
- **Redis** — Message broker for Celery
  - Queues tasks for workers
  - Stores job status

### ORM (Object-Relational Mapping)
- **SQLAlchemy** — Python ORM
  - Maps Python classes to database tables
  - Handles queries and transactions

---

## Detailed Pipeline Phases

### Phase 1: Parsing

**What happens:** Extract text and tables from uploaded files.

**Input:** Raw file (PDF, DOCX, or XLSX)

**Output:** Structured pages with text and metadata

**Code location:** `backend/app/services/parsers/`

**How it works:**

```python
# Example: PDF parsing
from app.services.parsers import get_parser

parser = get_parser("pdf")  # Returns PDFParser instance
parsed_pages = parser.parse("path/to/file.pdf")

# Each page is a ParsedPage object:
# {
#   "page_number": 1,
#   "text": "Full text of page...",
#   "tables": [
#     {"header": ["Col1", "Col2"], "rows": [["Val1", "Val2"]]}
#   ]
# }
```

**Key features:**
- **PDF tables:** Detected and formatted as readable sentences
  - Example: `"Report Distribution: Support all types of printers"`
- **DOCX tables:** Converted to "Label: Value" format
- **XLSX sheets:** Each row becomes a text line
- **Page numbers:** Preserved for traceability

---

### Phase 2: Chunking

**What happens:** Split the full document into meaningful sections.

**Input:** Parsed pages with full text

**Output:** ~50-500 chunks per document

**Code location:** `backend/app/services/chunking/`

**How it works:**

```
Step 1: Detect Headings
  ├─ Scan all text for heading patterns
  ├─ Filter out single words and list items
  └─ Result: List of (heading_text, page_number, position)

Step 2: Build Hierarchy
  ├─ Organize headings into tree structure
  ├─ Assign levels (H1, H2, H3)
  └─ Result: Hierarchical section tree

Step 3: Produce Chunks
  ├─ For each section, create one chunk
  ├─ Include section title + content
  └─ Result: DocumentChunk objects ready for DB
```

**Example:**

```
Document: "System Requirements.pdf"

Detected headings:
  H1: "Functional Requirements"
    H2: "User Management"
      H3: "Authentication"
    H2: "Reporting"
  H1: "Non-Functional Requirements"
    H2: "Performance"

Chunks created:
  1. "Functional Requirements" (section)
  2. "User Management" (subsection)
  3. "Authentication" (sub-subsection)
  4. "Reporting" (subsection)
  5. "Non-Functional Requirements" (section)
  6. "Performance" (subsection)
```

**Key features:**
- **Strict heading detection:** Prevents false positives
- **Hierarchy preservation:** Maintains document structure
- **One chunk per section:** Keeps related content together
- **Metadata:** Each chunk stores section, subsection, page number

---

### Phase 3: Semantic Chunking

**What happens:** Split large chunks into smaller, semantically coherent pieces.

**Input:** Chunks from Phase 2

**Output:** Smaller chunks with better semantic boundaries

**Code location:** `backend/app/services/semantic_chunking/`

**How it works:**

```
For each chunk:
  1. Load BAAI/bge-small-en-v1.5 embedding model
  2. Compute embeddings for sentences in the chunk
  3. Find natural break points (where embeddings differ most)
  4. Split at those points
  5. Result: 2-5 sub-chunks per original chunk
```

**Example:**

```
Original chunk (too large):
"The system must support user authentication via OAuth2 and SAML. 
 Users can reset passwords via email. The system must log all 
 authentication attempts for security auditing."

After semantic chunking:
  Sub-chunk 1: "The system must support user authentication via OAuth2 and SAML."
  Sub-chunk 2: "Users can reset passwords via email."
  Sub-chunk 3: "The system must log all authentication attempts for security auditing."
```

**Why this matters:**
- Smaller chunks = better search results
- Semantic boundaries = more relevant matches
- Prevents mixing unrelated requirements

---

### Phase 4: Classification

**What happens:** Label each chunk with a requirement category.

**Input:** Chunks from Phase 3

**Output:** Chunks with category labels and confidence scores

**Code location:** `backend/app/services/classification/`

**Categories:**
- `functional` — Core features and capabilities
- `non_functional` — Performance, scalability, reliability
- `security_compliance` — Security, privacy, compliance
- `integrations` — Third-party integrations
- `ui_ux` — User interface and experience
- `workflow_roles` — User roles and workflows
- `data_validation` — Data validation rules
- `infrastructure_deployment` — Deployment and infrastructure
- `risks_assumptions_dependencies` — Risks and assumptions
- `open_questions` — Unclear or ambiguous items
- `out_of_scope` — Items explicitly out of scope

**How it works:**

```python
classifier = Classifier()
category, confidence = classifier.classify(chunk_text)

# Example:
# Input: "The system must support OAuth2 authentication"
# Output: ("security_compliance", 0.85)
```

**Classification rules:**
- **Keyword matching:** Look for domain-specific keywords
  - "authenticate", "encrypt", "secure" → security
  - "performance", "latency", "throughput" → non-functional
  - "button", "UI", "dashboard" → ui_ux
  
- **Confidence scoring:** 0.0 to 1.0
  - 0.5+ = confident classification
  - < 0.5 = uncertain, may need manual review

---

### Phase 5: Embedding

**What happens:** Convert text chunks into AI vectors for semantic search.

**Input:** Classified chunks

**Output:** 384-dimensional vectors stored in Qdrant

**Code location:** `backend/app/services/embeddings/`

**How it works:**

```python
from sentence_transformers import SentenceTransformer

# Load model once (384-dimensional output)
model = SentenceTransformer("BAAI/bge-small-en-v1.5")

# Convert text to vector
text = "The system must support OAuth2 authentication"
embedding = model.encode(text, normalize_embeddings=True)
# Result: [0.123, -0.456, 0.789, ..., 0.234]  (384 values)
```

**Why embeddings matter:**
- **Semantic search:** Find similar requirements even if wording differs
- **Example:** Query "user login" finds "OAuth2 authentication"
- **Fast:** Vector similarity search is milliseconds-fast
- **Scalable:** Works with thousands of chunks

**Storage:**
- Vectors stored in **Qdrant** (vector database)
- Metadata (text, category, page) stored in **PostgreSQL**
- Both linked by `chunk_id`

---

### Phase 6: Storage

**What happens:** Save all data to databases.

**Input:** Processed chunks with embeddings

**Output:** Data persisted and queryable

**Databases:**

**PostgreSQL (Relational):**
```
projects
├─ id (UUID)
├─ name (string)
└─ created_at (timestamp)

documents
├─ id (UUID)
├─ project_id (FK)
├─ file_name (string)
├─ file_type (pdf/docx/xlsx)
├─ upload_status (uploaded/parsed/chunked/classified/embedded)
├─ parsed_content (JSON)
└─ created_at (timestamp)

document_chunks
├─ id (UUID)
├─ document_id (FK)
├─ project_id (FK)
├─ text (string)
├─ section (string)
├─ subsection (string)
├─ page_number (int)
├─ category (string)
├─ confidence_score (float)
└─ created_at (timestamp)
```

**Qdrant (Vector Database):**
```
Collection: "rfp_chunks"
├─ Vector: [384 floats]
├─ Payload:
│  ├─ chunk_id (UUID)
│  ├─ text (string)
│  ├─ category (string)
│  └─ page_number (int)
```

---

## Database Schema

### Projects Table
```sql
CREATE TABLE projects (
  id UUID PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

### Documents Table
```sql
CREATE TABLE documents (
  id UUID PRIMARY KEY,
  project_id UUID NOT NULL REFERENCES projects(id),
  file_name VARCHAR(255) NOT NULL,
  file_type VARCHAR(10),  -- 'pdf', 'docx', 'xlsx'
  stored_path VARCHAR(512),  -- Path on disk
  upload_status VARCHAR(50),  -- 'uploaded', 'parsed', 'chunked', etc.
  parsed_content JSONB,  -- Raw parsed pages
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

### Document Chunks Table
```sql
CREATE TABLE document_chunks (
  id UUID PRIMARY KEY,
  document_id UUID NOT NULL REFERENCES documents(id),
  project_id UUID NOT NULL REFERENCES projects(id),
  text TEXT NOT NULL,
  section VARCHAR(255),
  subsection VARCHAR(255),
  page_number INT,
  category VARCHAR(50),  -- 'functional', 'security', etc.
  confidence_score FLOAT,  -- 0.0 to 1.0
  chunk_type VARCHAR(50),  -- 'requirement', 'note', etc.
  token_count INT,
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

## API Endpoints

### Upload Documents
```
POST /upload
Content-Type: multipart/form-data

Body:
  files: [file1.pdf, file2.docx]
  project_name: "My RFP"

Response:
  {
    "project_id": "uuid",
    "documents": [
      {
        "document_id": "uuid",
        "file_name": "file1.pdf",
        "job_id": "uuid"
      }
    ]
  }
```

### Get Project Status
```
GET /projects/{project_id}/status

Response:
  {
    "project_id": "uuid",
    "total_documents": 3,
    "ready_documents": 2,
    "is_ready": false,
    "documents": [
      {
        "document_id": "uuid",
        "file_name": "file1.pdf",
        "current_status": "embedded",
        "is_ready": true,
        "pipeline": [
          {"name": "parsing", "status": "completed", "label": "Parsing"},
          {"name": "chunking", "status": "completed", "label": "Chunking"},
          ...
        ]
      }
    ]
  }
```

### Search Requirements
```
POST /search
Content-Type: application/json

Body:
  {
    "project_id": "uuid",
    "query": "user authentication",
    "topK": 10
  }

Response:
  {
    "project_id": "uuid",
    "query": "user authentication",
    "total_results": 5,
    "results": [
      {
        "chunk_id": "uuid",
        "text": "The system must support OAuth2 authentication",
        "category": "security_compliance",
        "section": "Security Requirements",
        "page_number": 12,
        "confidence_score": 0.92,
        "score": 0.87,
        "req_id": "FR-001",
        "type_label": "Security"
      }
    ]
  }
```

### Search by Category
```
GET /search/category?project_id=uuid&category=functional&topK=50

Response:
  {
    "project_id": "uuid",
    "category": "functional",
    "total_results": 42,
    "results": [...]
  }
```

---

## How Data Flows Through the System

### Complete Example: Uploading an RFP

**Step 1: User uploads file**
```
Frontend → POST /upload (file: "RFP.pdf")
Backend receives file, saves to disk
```

**Step 2: Create database records**
```
INSERT INTO projects (name) → project_id = "proj-123"
INSERT INTO documents (project_id, file_name) → document_id = "doc-456"
INSERT INTO processing_jobs (document_id) → job_id = "job-789"
```

**Step 3: Queue parsing task**
```
Celery task: parse_document(job_id="job-789", document_id="doc-456")
```

**Step 4: Parse PDF**
```
PDFParser.parse("storage/uploads/proj-123/doc-456.pdf")
→ Extract text from each page
→ Detect and format tables
→ Return list of ParsedPage objects
```

**Step 5: Save parsed content**
```
UPDATE documents SET parsed_content = [...], upload_status = 'parsed'
```

**Step 6: Queue chunking task**
```
Celery task: chunk_document(document_id="doc-456", project_id="proj-123")
```

**Step 7: Chunk document**
```
HeadingDetector.detect() → Find headings
HierarchyBuilder.build() → Build section tree
ChunkProducer.produce() → Create chunks
```

**Step 8: Save chunks**
```
INSERT INTO document_chunks (document_id, text, section, category, ...)
→ 150 chunks inserted
```

**Step 9: Queue semantic chunking**
```
Celery task: semantic_chunk_document(document_id="doc-456")
```

**Step 10: Semantic chunking**
```
For each chunk:
  SemanticSplitter.split(text) → 2-5 sub-chunks
  Save sub-chunks to database
```

**Step 11: Queue classification**
```
Celery task: classify_chunks(document_id="doc-456")
```

**Step 12: Classify chunks**
```
For each chunk:
  Classifier.classify(text) → (category, confidence)
  UPDATE document_chunks SET category = ..., confidence_score = ...
```

**Step 13: Queue embedding**
```
Celery task: embed_chunks(document_id="doc-456")
```

**Step 14: Generate embeddings**
```
EmbeddingService.embed([chunk_texts]) → [[384 floats], ...]
Store vectors in Qdrant with metadata
```

**Step 15: Mark complete**
```
UPDATE documents SET upload_status = 'embedded'
```

**Step 16: Frontend polls status**
```
GET /projects/proj-123/status
→ Returns is_ready = true
→ Frontend shows "Documents Ready"
```

**Step 17: User searches**
```
POST /search (query="user authentication")
→ Convert query to embedding
→ Search Qdrant for similar vectors
→ Return top 10 results with metadata
```

---

## Key Concepts Explained

### What is a "Chunk"?

A **chunk** is a meaningful piece of text extracted from a document. Think of it as a paragraph or section.

**Example:**
```
Original document:
"2.1 User Authentication
The system must support OAuth2 and SAML authentication methods.
Users can reset passwords via email. All authentication attempts
must be logged for security auditing."

Chunks created:
  Chunk 1: "User Authentication - The system must support OAuth2 and SAML..."
  Chunk 2: "Users can reset passwords via email."
  Chunk 3: "All authentication attempts must be logged..."
```

### What is an "Embedding"?

An **embedding** is a mathematical representation of text as a vector (list of numbers).

**Why it matters:**
- Computers can't understand words directly
- Embeddings convert words to numbers
- Similar texts have similar embeddings
- Enables semantic search

**Example:**
```
Text: "user authentication"
Embedding: [0.123, -0.456, 0.789, ..., 0.234]  (384 numbers)

Text: "OAuth2 login"
Embedding: [0.125, -0.450, 0.785, ..., 0.240]  (similar!)

Text: "database performance"
Embedding: [0.001, 0.999, -0.500, ..., 0.100]  (different!)
```

### What is "Semantic Search"?

**Semantic search** finds results based on meaning, not just keywords.

**Example:**
```
Query: "user login"
Traditional search: Finds only documents with "user" AND "login"
Semantic search: Also finds "OAuth2 authentication", "sign in", "credentials"
```

### What is Qdrant?

**Qdrant** is a vector database optimized for storing and searching embeddings.

**Why not just PostgreSQL?**
- PostgreSQL is great for structured data (tables, rows)
- Qdrant is great for unstructured data (vectors)
- Qdrant can search 1 million vectors in milliseconds
- PostgreSQL would take seconds

**How it works:**
```
1. Store vector + metadata in Qdrant
2. User searches with a query
3. Convert query to embedding
4. Find nearest vectors (cosine similarity)
5. Return top K results instantly
```

### What is Celery?

**Celery** is a task queue that runs jobs asynchronously (in the background).

**Why it matters:**
- Parsing a 100-page PDF takes 10 seconds
- If we did this synchronously, the API would hang
- Celery runs it in the background
- API returns immediately with a job ID
- Frontend polls for status

**Example:**
```
Synchronous (bad):
  POST /upload → Wait 30 seconds → Return results

Asynchronous with Celery (good):
  POST /upload → Return immediately with job_id
  GET /status?job_id=... → Check progress
  → "Parsing: 50%"
  → "Chunking: 100%"
  → "Embedding: 75%"
```

### What is PostgreSQL?

**PostgreSQL** is a relational database that stores structured data.

**What it stores:**
- Projects (metadata)
- Documents (file info, status)
- Chunks (text, category, page number)
- Processing jobs (status, errors)

**Why not just files?**
- Files are slow to search
- Databases are optimized for queries
- Can join data across tables
- ACID compliance (data integrity)

---

## Summary

The EstimateIQ backend is a **document processing pipeline** that:

1. **Parses** files to extract text and tables
2. **Chunks** text into meaningful sections
3. **Semantically splits** large chunks
4. **Classifies** chunks by requirement type
5. **Embeds** chunks into AI vectors
6. **Stores** everything in PostgreSQL + Qdrant
7. **Serves** results via REST API

**Key technologies:**
- FastAPI (web framework)
- PostgreSQL (relational DB)
- Qdrant (vector DB)
- Celery (task queue)
- Sentence Transformers (embeddings)
- LlamaIndex (text processing)

**Key insight:** The system converts messy documents into structured, searchable requirements using AI and NLP.

---

## Next Steps

- Read `FRONTEND_ARCHITECTURE.md` to understand how the UI consumes this API
- Explore the code in `backend/app/services/` to see implementation details
- Check `backend/app/api/routes/` to see all available endpoints
