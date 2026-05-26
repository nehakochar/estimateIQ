"""
query_service.py — DB query helpers for SemanticChunk rows.

Used by the API routes in app/api/routes/semantic_chunks.py to fetch
semantic chunk data without embedding query logic in the route layer.
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.semantic_chunk import SemanticChunk


def get_chunks_for_document(
    db: Session,
    document_id: str,
    category: str | None = None,
) -> list[SemanticChunk]:
    """
    Return all SemanticChunk rows for a document, ordered by chunk_index.

    Args:
        db:          Active SQLAlchemy session.
        document_id: UUID string of the target document.
        category:    Optional category filter.  When provided, only chunks
                     whose ``category`` column matches exactly are returned.

    Returns:
        List of SemanticChunk ORM objects, ordered by chunk_index ascending.
    """
    doc_uuid = uuid.UUID(document_id)

    stmt = (
        select(SemanticChunk)
        .where(SemanticChunk.document_id == doc_uuid)
        .order_by(SemanticChunk.chunk_index)
    )

    if category is not None:
        stmt = stmt.where(SemanticChunk.category == category)

    return list(db.execute(stmt).scalars().all())


def get_category_summary(
    db: Session,
    document_id: str,
) -> dict[str, int]:
    """
    Return a mapping of category name → chunk count for a document.

    Args:
        db:          Active SQLAlchemy session.
        document_id: UUID string of the target document.

    Returns:
        Dict mapping each category present in the document to its chunk count.
        Categories with zero chunks are not included.
    """
    doc_uuid = uuid.UUID(document_id)

    stmt = (
        select(SemanticChunk.category, func.count().label("cnt"))
        .where(SemanticChunk.document_id == doc_uuid)
        .group_by(SemanticChunk.category)
    )

    rows = db.execute(stmt).all()
    return {row.category: row.cnt for row in rows}
