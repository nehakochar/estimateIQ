# Phase 9 — Retrieval Layer

## Overview

The Retrieval Layer is an enterprise-grade semantic search and retrieval system for EstimateIQ. It enables intelligent retrieval of relevant RFP chunks from Qdrant using semantic similarity, metadata filtering, and project-scoped queries.

**Key Principle**: Frontend should NEVER query Qdrant directly. All retrieval goes through FastAPI endpoints.

## Architecture

```
Frontend
   ↓
FastAPI Retrieval APIs (/search, /search/category, /search/similar)
   ↓
RetrievalService (orchestration + DB validation)
   ↓
SemanticSearchService (Qdrant queries)
   ↓
Qdrant + PostgreSQL
```

## Core Components

### 1. SemanticSearchService (`services/retrieval/semantic_search.py`)

Low-level semantic search operations against Qdrant.

**Methods**:
- `search()` — semantic similarity search with metadata filtering
- `search_by_category()` — retrieve chunks by category
- `find_similar_chunks()` — find chunks similar to a reference chunk

**Key Features**:
- All searches are project-scoped (mandatory project_id filter)
- Supports metadata filtering: category, section, document_id, chunk_type
- Configurable similarity threshold (0.0–1.0)
- Returns ranked results with similarity scores

**Example**:
```python
service = SemanticSearchService()
results = service.search(
    project_id="project_123",
    query="authentication requirements",
    top_k=10,
    category="security_compliance",
    similarity_threshold=0.65,
)
```

### 2. RetrievalService (`services/retrieval/retrieval_service.py`)

High-level retrieval orchestration with database integration.

**Methods**:
- `search()` — semantic search with DB validation
- `search_by_category()` — category search with DB validation
- `find_similar_chunks()` — similarity search with DB validation
- `get_project_statistics()` — project-level chunk statistics

**Key Features**:
- Validates project and document ownership
- Enriches results with database metadata
- Logs retrieval metrics
- Handles errors gracefully

**Example**:
```python
service = RetrievalService(db)
results = service.search(
    project_id="project_123",
    query="authentication requirements",
    top_k=10,
)
```

### 3. QdrantService Extensions (`services/vector/qdrant_service.py`)

Extended Qdrant operations for retrieval.

**New Methods**:
- `search()` — semantic similarity search with filters
- `scroll()` — retrieve all points matching a filter
- `get_point()` — retrieve a single point by ID

### 4. FastAPI Routes (`api/routes/retrieval.py`)

REST API endpoints for retrieval operations.

**Endpoints**:
- `POST /search?project_id=...` — semantic search
- `POST /search/category?project_id=...` — category search
- `POST /search/similar?project_id=...` — similarity search
- `GET /search/projects/{project_id}/statistics` — project statistics

## API Endpoints

### 1. Semantic Search

**Endpoint**: `POST /search?project_id={project_id}`

**Request**:
```json
{
  "query": "authentication requirements",
  "top_k": 10,
  "category": "security_compliance",
  "section": null,
  "document_id": null,
  "chunk_type": null,
  "similarity_threshold": 0.65
}
```

**Response**:
```json
{
  "project_id": "project_123",
  "query": "authentication requirements",
  "total_results": 5,
  "results": [
    {
      "chunk_id": "chunk_uuid",
      "text": "The system must support multi-factor authentication...",
      "category": "security_compliance",
      "section": "Security Requirements",
      "subsection": "Authentication",
      "page_number": 12,
      "score": 0.92,
      "confidence_score": 1.0,
      "document_id": "doc_uuid",
      "chunk_type": "requirement"
    }
  ]
}
```

### 2. Category Search

**Endpoint**: `POST /search/category?project_id={project_id}`

**Request**:
```json
{
  "category": "security_compliance",
  "top_k": 10,
  "similarity_threshold": 0.65
}
```

**Response**:
```json
{
  "project_id": "project_123",
  "category": "security_compliance",
  "total_results": 8,
  "results": [...]
}
```

### 3. Similar Chunks

**Endpoint**: `POST /search/similar?project_id={project_id}`

**Request**:
```json
{
  "chunk_id": "chunk_uuid",
  "top_k": 10,
  "similarity_threshold": 0.65
}
```

**Response**:
```json
{
  "project_id": "project_123",
  "reference_chunk_id": "chunk_uuid",
  "total_results": 3,
  "results": [...]
}
```

### 4. Project Statistics

**Endpoint**: `GET /search/projects/{project_id}/statistics`

**Response**:
```json
{
  "project_id": "project_123",
  "total_chunks": 245,
  "chunks_by_category": {
    "security_compliance": 45,
    "functional": 120,
    "ui_ux": 30,
    ...
  },
  "chunks_by_document": {
    "doc_uuid_1": 100,
    "doc_uuid_2": 145
  },
  "chunks_by_type": {
    "requirement": 200,
    "workflow": 45
  }
}
```

## Valid Categories

The 11 valid requirement categories:

1. `functional` — Core business functionality
2. `non_functional` — Performance, scalability, availability
3. `ui_ux` — User interface and experience
4. `integrations` — Third-party APIs and integrations
5. `security_compliance` — Security, authentication, compliance
6. `data_validation` — Input validation and data constraints
7. `workflow_roles` — Roles, permissions, workflows
8. `infrastructure_deployment` — Deployment, CI/CD, infrastructure
9. `risks_assumptions_dependencies` — Risks, assumptions, dependencies
10. `open_questions` — Unresolved or pending items
11. `out_of_scope` — Explicitly excluded items

## Metadata Filtering

Retrieval supports filtering by:

- **category** — One of the 11 valid categories
- **section** — Section heading (e.g., "Security Requirements")
- **document_id** — UUID of source document
- **chunk_type** — "requirement" or "workflow"
- **page_number** — Page number in document (via sorting)

## Similarity Scoring

Similarity scores range from 0.0 to 1.0:

- **0.9–1.0** — Highly relevant, exact semantic match
- **0.8–0.9** — Very relevant, strong semantic similarity
- **0.7–0.8** — Relevant, good semantic match
- **0.65–0.7** — Marginally relevant (default threshold)
- **< 0.65** — Filtered out by default threshold

## Project Scoping

**All retrieval is project-scoped**. Every query MUST filter by `project_id`.

This is mandatory because:
- EstimateIQ supports multiple RFPs/projects
- Data isolation is critical for multi-tenant scenarios
- Prevents accidental cross-project data leakage

**Example**: A query for "authentication" in project A will NOT return chunks from project B, even if they're semantically similar.

## Utility Modules

### SearchUtils (`services/search/search_utils.py`)

Helper functions for search operations:

- `normalize_query()` — normalize query text
- `validate_category()` — validate category
- `rank_results()` — sort results by field
- `filter_by_threshold()` — filter by minimum score
- `deduplicate_results()` — remove duplicates
- `extract_metadata()` — extract metadata from result
- `calculate_search_metrics()` — compute result statistics
- `format_result_for_display()` — format for API response

### Validation (`services/retrieval/validation.py`)

Input validation utilities:

- `validate_project_id()` — validate UUID format
- `validate_query()` — validate query text
- `validate_category()` — validate category
- `validate_chunk_type()` — validate chunk type
- `validate_top_k()` — validate result count
- `validate_similarity_threshold()` — validate threshold
- `validate_uuid()` — validate UUID format
- `validate_search_request()` — validate all search parameters

### Debug Utils (`services/retrieval/debug_utils.py`)

Debugging and inspection utilities:

- `RetrievalDebugWriter` — write debug snapshots to disk
- `inspect_retrieved_chunks()` — analyze chunk results
- `inspect_metadata_filters()` — analyze filters
- `inspect_similarity_scores()` — analyze score distribution
- `log_retrieval_metrics()` — log operation metrics

## Usage Examples

### Example 1: Search for Security Requirements

```python
from app.services.retrieval.retrieval_service import RetrievalService
from sqlalchemy.orm import Session

def search_security_requirements(db: Session, project_id: str):
    service = RetrievalService(db)
    results = service.search(
        project_id=project_id,
        query="authentication and authorization",
        category="security_compliance",
        top_k=10,
    )
    return results
```

### Example 2: Browse All UI/UX Requirements

```python
def browse_ui_requirements(db: Session, project_id: str):
    service = RetrievalService(db)
    results = service.search_by_category(
        project_id=project_id,
        category="ui_ux",
        top_k=20,
    )
    return results
```

### Example 3: Find Related Requirements

```python
def find_related_requirements(db: Session, project_id: str, chunk_id: str):
    service = RetrievalService(db)
    results = service.find_similar_chunks(
        project_id=project_id,
        chunk_id=chunk_id,
        top_k=5,
    )
    return results
```

### Example 4: Get Project Statistics

```python
def get_project_overview(db: Session, project_id: str):
    service = RetrievalService(db)
    stats = service.get_project_statistics(project_id)
    print(f"Total chunks: {stats['total_chunks']}")
    print(f"By category: {stats['chunks_by_category']}")
    return stats
```

## Performance Considerations

### Embedding Generation
- Query embedding is generated once per search
- Uses BAAI/bge-small-en-v1.5 (384-dimensional vectors)
- Typical latency: 10–50ms

### Qdrant Search
- Cosine distance metric for similarity
- Metadata filtering applied before scoring
- Typical latency: 50–200ms for 10 results

### Database Queries
- Project validation: indexed by project_id
- Statistics queries: aggregated with GROUP BY
- Typical latency: 10–50ms

### Optimization Tips
- Use metadata filters to reduce search space
- Increase similarity_threshold to reduce results
- Limit top_k to necessary results
- Cache project statistics if accessed frequently

## Error Handling

### Common Errors

**400 Bad Request**:
- Invalid project_id format
- Invalid category
- Query too short/long
- Invalid similarity_threshold

**404 Not Found**:
- Project doesn't exist
- Document doesn't belong to project
- Chunk not found

**500 Internal Server Error**:
- Qdrant connection failure
- Database connection failure
- Embedding service failure

### Error Response Format

```json
{
  "detail": "Invalid category 'invalid_cat'. Valid categories: [...]"
}
```

## Testing

### Unit Tests

Test individual services:

```python
def test_semantic_search():
    service = SemanticSearchService()
    results = service.search(
        project_id="test_project",
        query="test query",
        top_k=5,
    )
    assert len(results) <= 5
    assert all("score" in r for r in results)
```

### Integration Tests

Test with real database and Qdrant:

```python
def test_retrieval_service(db: Session):
    service = RetrievalService(db)
    results = service.search(
        project_id="test_project",
        query="test query",
    )
    assert isinstance(results, list)
```

### API Tests

Test endpoints:

```python
def test_search_endpoint(client):
    response = client.post(
        "/search?project_id=test_project",
        json={"query": "test query", "top_k": 5},
    )
    assert response.status_code == 200
    assert "results" in response.json()
```

## Future Enhancements

### Phase 10 — AI Assistant
- Use retrieval layer to fetch context
- Generate answers using LLM
- Maintain conversation history

### Phase 11 — Estimation Engine
- Use retrieval to find similar requirements
- Extract effort/cost estimates
- Generate project estimates

### Phase 12 — Advanced Search
- Full-text search integration
- Faceted search
- Search suggestions/autocomplete

### Phase 13 — Search Analytics
- Track popular queries
- Analyze search patterns
- Optimize retrieval performance

## Configuration

Retrieval settings in `.env`:

```bash
# Qdrant
QDRANT_URL=http://qdrant:6333
QDRANT_API_KEY=your_api_key
EMBEDDING_COLLECTION_NAME=rfp_chunks

# Embeddings
EMBEDDING_BATCH_SIZE=32

# Database
DATABASE_URL=postgresql://user:password@postgres:5432/estimateiq
```

## Logging

Retrieval operations are logged at INFO level:

```
INFO: SemanticSearchService.search: project=project_123 query_len=25 top_k=10 category=security_compliance threshold=0.65
INFO: SemanticSearchService.search: returned 5 results (threshold=0.65)
INFO: RetrievalService.search: project=project_123 query_len=25 top_k=10
INFO: RetrievalService.search: returned 5 results
```

## Summary

The Retrieval Layer provides:

✅ **Semantic search** — Find relevant chunks using AI embeddings
✅ **Metadata filtering** — Filter by category, section, document, type
✅ **Project scoping** — Mandatory project isolation
✅ **Similarity ranking** — Configurable relevance thresholds
✅ **Database integration** — Validation and enrichment
✅ **Production-ready** — Error handling, logging, validation
✅ **Extensible** — Modular architecture for future enhancements

This foundation powers future features like the AI assistant, estimation engine, and advanced search capabilities.
