"""
semantic_chunking.py — Pydantic response schemas for the semantic chunk inspection API.

These schemas define the JSON shape returned by:
  GET /documents/{document_id}/semantic-chunks
  GET /documents/{document_id}/semantic-chunks/summary

`model_config = ConfigDict(from_attributes=True)`:
  Allows Pydantic to construct these schemas directly from SQLAlchemy
  `SemanticChunk` ORM objects by reading their attributes.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


# ── Individual semantic chunk ─────────────────────────────────────────────


class SemanticChunkResponse(BaseModel):
    """
    Response schema for a single semantic chunk.

    Represents one semantically coherent chunk produced by the semantic
    chunking pipeline, with classification metadata attached.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str
    chunk_index: int
    source_chunk_id: str | None
    section: str
    subsection: str
    category: str
    chunk_type: str
    page_number: int
    token_count: int
    confidence_score: float
    text: str


# ── Document-level semantic chunk collection ──────────────────────────────


class DocumentSemanticChunksResponse(BaseModel):
    """
    Response schema for GET /documents/{document_id}/semantic-chunks.

    Returns all semantic chunks for a document ordered by `chunk_index`,
    along with summary metadata. Supports optional filtering by category.
    """

    model_config = ConfigDict(from_attributes=True)

    document_id: str
    total_chunks: int
    chunks: list[SemanticChunkResponse]


# ── Category distribution summary ─────────────────────────────────────────


class SemanticChunkSummaryResponse(BaseModel):
    """
    Response schema for GET /documents/{document_id}/semantic-chunks/summary.

    Returns a high-level breakdown of semantic chunks by category,
    without returning the full chunk text.
    """

    model_config = ConfigDict(from_attributes=True)

    document_id: str
    total_chunks: int
    category_distribution: dict[str, int]
