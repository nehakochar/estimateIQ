"""
retrieval.py — Pydantic schemas for retrieval API requests and responses.

Defines request/response shapes for:
  - Semantic search
  - Category search
  - Similar chunk search
  - Project statistics
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ── Request schemas ───────────────────────────────────────────────────────


class SemanticSearchRequest(BaseModel):
    """Request schema for semantic search."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Search query text",
    )
    top_k: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Number of results to return",
    )
    category: str | None = Field(
        default=None,
        description="Optional category filter (one of 11 valid categories)",
    )
    section: str | None = Field(
        default=None,
        description="Optional section heading filter",
    )
    document_id: str | None = Field(
        default=None,
        description="Optional document UUID filter",
    )
    chunk_type: str | None = Field(
        default=None,
        description="Optional chunk type filter ('requirement' or 'workflow')",
    )
    similarity_threshold: float = Field(
        default=0.65,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score to include (0.0-1.0)",
    )


class CategorySearchRequest(BaseModel):
    """Request schema for category-based search."""

    category: str = Field(
        ...,
        min_length=1,
        description="Category to retrieve (one of 11 valid categories)",
    )
    top_k: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Number of results to return",
    )
    similarity_threshold: float = Field(
        default=0.65,
        ge=0.0,
        le=1.0,
        description="Minimum confidence score to include (0.0-1.0)",
    )


class SimilarChunksRequest(BaseModel):
    """Request schema for finding similar chunks."""

    chunk_id: str = Field(
        ...,
        description="UUID of the reference chunk",
    )
    top_k: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Number of similar chunks to return",
    )
    similarity_threshold: float = Field(
        default=0.65,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score to include (0.0-1.0)",
    )


# ── Response schemas ──────────────────────────────────────────────────────


class RetrievalResultItem(BaseModel):
    """Single result item from a retrieval operation."""

    chunk_id: str = Field(description="UUID of the chunk")
    text: str = Field(description="Full chunk text")
    category: str = Field(description="Classification category")
    section: str = Field(description="Section heading")
    subsection: str = Field(description="Subsection heading")
    page_number: int = Field(description="Page number in document")
    score: float = Field(description="Similarity score (0.0-1.0)")
    confidence_score: float = Field(description="Classification confidence (0.0-1.0)")
    document_id: str = Field(description="UUID of source document")
    chunk_type: str = Field(description="Chunk type ('requirement' or 'workflow')")


class SemanticSearchResponse(BaseModel):
    """Response schema for semantic search."""

    project_id: str = Field(description="UUID of the project")
    query: str = Field(description="Original search query")
    total_results: int = Field(description="Number of results returned")
    results: list[RetrievalResultItem] = Field(description="List of matching chunks")


class CategorySearchResponse(BaseModel):
    """Response schema for category search."""

    project_id: str = Field(description="UUID of the project")
    category: str = Field(description="Category searched")
    total_results: int = Field(description="Number of results returned")
    results: list[RetrievalResultItem] = Field(description="List of chunks in category")


class SimilarChunksResponse(BaseModel):
    """Response schema for similar chunks search."""

    project_id: str = Field(description="UUID of the project")
    reference_chunk_id: str = Field(description="UUID of the reference chunk")
    total_results: int = Field(description="Number of similar chunks returned")
    results: list[RetrievalResultItem] = Field(description="List of similar chunks")


# ── Statistics schemas ────────────────────────────────────────────────────


class ProjectStatistics(BaseModel):
    """Project-level retrieval statistics."""

    project_id: str = Field(description="UUID of the project")
    total_chunks: int = Field(description="Total number of chunks in project")
    chunks_by_category: dict[str, int] = Field(
        description="Number of chunks per category"
    )
    chunks_by_document: dict[str, int] = Field(
        description="Number of chunks per document"
    )
    chunks_by_type: dict[str, int] = Field(
        description="Number of chunks per type"
    )


# ── Error response schemas ────────────────────────────────────────────────


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str = Field(description="Error message")
    detail: str | None = Field(default=None, description="Additional error details")
