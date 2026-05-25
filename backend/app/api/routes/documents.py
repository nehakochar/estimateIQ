"""
documents.py — Route handlers for /documents endpoints.

GET /documents/{document_id}
  Returns document metadata and parsed content.

  When to call this:
    After GET /jobs/{job_id} returns status == "completed",
    call this endpoint to retrieve the extracted text.

    The `parsed_content` field will be null if:
      - Parsing hasn't finished yet (status is "queued" or "processing")
      - Parsing failed (status is "failed")

GET /documents/{document_id}/chunks
  Returns all hierarchical chunks for a document ordered by chunk_index.
  Returns an empty list if the document has not been chunked yet.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.schemas.chunking import ChunkResponse, DocumentChunksResponse
from app.schemas.processing import DocumentResponse

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get document details and parsed content",
    description=(
        "Returns metadata and parsed text content for a document. "
        "`parsed_content` is null until parsing completes. "
        "Each element in `parsed_content` has a `page` number and `text` field."
    ),
)
def get_document(
    document_id: str,
    db: Session = Depends(get_db),
) -> DocumentResponse:
    """
    Fetch a Document by its UUID.

    Args:
        document_id: UUID string of the document.
        db:          Database session (injected by FastAPI).

    Returns:
        DocumentResponse with metadata and parsed_content.

    Raises:
        HTTP 404: if no document with that ID exists.
        HTTP 400: if document_id is not a valid UUID.
    """
    # Validate UUID format
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid document ID format: '{document_id}'. Must be a UUID.",
        )

    document = db.get(Document, doc_uuid)
    if document is None:
        raise HTTPException(
            status_code=404,
            detail=f"Document '{document_id}' not found.",
        )

    return DocumentResponse.model_validate(document)


@router.get(
    "/{document_id}/chunks",
    response_model=DocumentChunksResponse,
    summary="Get chunks for a document",
    description=(
        "Returns all hierarchical chunks for a document ordered by chunk_index. "
        "Returns an empty list if the document has not been chunked yet."
    ),
)
def get_document_chunks(
    document_id: str,
    db: Session = Depends(get_db),
) -> DocumentChunksResponse:
    """
    Fetch all DocumentChunk rows for a document, ordered by chunk_index.

    Args:
        document_id: UUID string of the document.
        db:          Database session (injected by FastAPI).

    Returns:
        DocumentChunksResponse with document_id, total_chunks, and chunks list.

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

    # Query all chunks for this document ordered by chunk_index
    chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == doc_uuid)
        .order_by(DocumentChunk.chunk_index)
        .all()
    )

    return DocumentChunksResponse(
        document_id=document_id,
        total_chunks=len(chunks),
        chunks=[ChunkResponse.model_validate(c) for c in chunks],
    )
