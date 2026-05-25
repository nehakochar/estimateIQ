"""
chunking.py — Pydantic response schemas for the chunk inspection API.

These schemas define the JSON shape returned by
GET /documents/{document_id}/chunks.

`model_config = ConfigDict(from_attributes=True)`:
  Allows Pydantic to construct these schemas directly from SQLAlchemy
  `DocumentChunk` ORM objects by reading their attributes.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


# ── Individual chunk ──────────────────────────────────────────────────────


class ChunkResponse(BaseModel):
    """
    Response schema for a single document chunk.

    Represents one hierarchical or sentence-fallback chunk produced
    by the chunking pipeline.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str
    chunk_index: int
    parent_chunk_id: str | None
    section: str
    subsection: str
    level: int
    page_number: int
    chunk_type: str
    token_count: int
    text: str


# ── Document-level chunk collection ──────────────────────────────────────


class DocumentChunksResponse(BaseModel):
    """
    Response schema for GET /documents/{document_id}/chunks.

    Returns all chunks for a document ordered by `chunk_index`,
    along with summary metadata.
    """

    document_id: str
    total_chunks: int
    chunks: list[ChunkResponse]
