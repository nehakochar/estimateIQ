"""
semantic_chunks.py — Route handlers for semantic chunk inspection endpoints.

GET /documents/{document_id}/semantic-chunks
  Returns all semantic chunks for a document, ordered by chunk_index.
  Supports optional filtering by category via the `category` query param.

  Returns HTTP 400 if the category value is not one of the 11 valid categories.
  Returns HTTP 404 if the document does not exist.

GET /documents/{document_id}/semantic-chunks/summary
  Returns a category distribution summary (chunk count per category) for a
  document without returning the full chunk text.

  Returns HTTP 404 if the document does not exist.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.document import Document
from app.schemas.semantic_chunking import (
    DocumentSemanticChunksResponse,
    SemanticChunkResponse,
    SemanticChunkSummaryResponse,
)
from app.services.semantic_chunking.query_service import (
    get_category_summary,
    get_chunks_for_document,
)

router = APIRouter(prefix="/documents", tags=["Semantic Chunks"])

# The 11 valid classification categories
VALID_CATEGORIES = {
    "functional",
    "non_functional",
    "ui_ux",
    "integrations",
    "security_compliance",
    "data_validation",
    "workflow_roles",
    "infrastructure_deployment",
    "risks_assumptions_dependencies",
    "open_questions",
    "out_of_scope",
}

# Sorted list for deterministic error messages
_VALID_CATEGORIES_LIST = sorted(VALID_CATEGORIES)


@router.get(
    "/{document_id}/semantic-chunks",
    response_model=DocumentSemanticChunksResponse,
    summary="Get semantic chunks for a document",
    description=(
        "Returns all semantic chunks for a document ordered by `chunk_index`. "
        "Optionally filter by `category`. "
        "Returns an empty list if the document has not been semantically chunked yet."
    ),
)
def get_document_semantic_chunks(
    document_id: str,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
) -> DocumentSemanticChunksResponse:
    """
    Fetch all SemanticChunk rows for a document, ordered by chunk_index.

    Args:
        document_id: UUID string of the document.
        category:    Optional category filter. Must be one of the 11 valid
                     categories if provided.
        db:          Database session (injected by FastAPI).

    Returns:
        DocumentSemanticChunksResponse with document_id, total_chunks, and
        chunks list.

    Raises:
        HTTP 400: if document_id is not a valid UUID.
        HTTP 400: if category is provided but is not a valid category.
        HTTP 404: if no document with that ID exists.
    """
    # Validate UUID format
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid document ID format: '{document_id}'. Must be a UUID.",
        )

    # Validate category if provided
    if category is not None and category not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid category: '{category}'. "
                f"Must be one of: {_VALID_CATEGORIES_LIST}."
            ),
        )

    # Verify the document exists
    document = db.get(Document, doc_uuid)
    if document is None:
        raise HTTPException(
            status_code=404,
            detail=f"Document '{document_id}' not found.",
        )

    chunks = get_chunks_for_document(db, document_id, category=category)

    return DocumentSemanticChunksResponse(
        document_id=document_id,
        total_chunks=len(chunks),
        chunks=[SemanticChunkResponse.model_validate(c) for c in chunks],
    )


@router.get(
    "/{document_id}/semantic-chunks/summary",
    response_model=SemanticChunkSummaryResponse,
    summary="Get semantic chunk category summary for a document",
    description=(
        "Returns a high-level breakdown of semantic chunks by category for a "
        "document, without returning the full chunk text."
    ),
)
def get_document_semantic_chunks_summary(
    document_id: str,
    db: Session = Depends(get_db),
) -> SemanticChunkSummaryResponse:
    """
    Fetch a category distribution summary for a document's semantic chunks.

    Args:
        document_id: UUID string of the document.
        db:          Database session (injected by FastAPI).

    Returns:
        SemanticChunkSummaryResponse with document_id, total_chunks, and
        category_distribution dict.

    Raises:
        HTTP 400: if document_id is not a valid UUID.
        HTTP 404: if no document with that ID exists.
    """
    # Validate UUID format
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid document ID format: '{document_id}'. Must be a UUID.",
        )

    # Verify the document exists
    document = db.get(Document, doc_uuid)
    if document is None:
        raise HTTPException(
            status_code=404,
            detail=f"Document '{document_id}' not found.",
        )

    category_distribution = get_category_summary(db, document_id)
    total_chunks = sum(category_distribution.values())

    return SemanticChunkSummaryResponse(
        document_id=document_id,
        total_chunks=total_chunks,
        category_distribution=category_distribution,
    )
