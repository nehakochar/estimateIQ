"""
retrieval.py — Pydantic schemas for retrieval API requests and responses.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ── Request schemas ───────────────────────────────────────────────────────


class SemanticSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="Search query text")
    top_k: int = Field(default=10, ge=1, le=100, description="Number of results to return")
    category: str | None = Field(default=None, description="Optional category filter")
    section: str | None = Field(default=None, description="Optional section heading filter")
    document_id: str | None = Field(default=None, description="Optional document UUID filter")
    chunk_type: str | None = Field(default=None, description="Optional chunk type filter")
    similarity_threshold: float = Field(default=0.65, ge=0.0, le=1.0, description="Minimum similarity score")


class CategorySearchRequest(BaseModel):
    category: str = Field(..., min_length=1, description="Category to retrieve")
    top_k: int = Field(default=10, ge=1, le=100, description="Number of results to return")
    similarity_threshold: float = Field(default=0.65, ge=0.0, le=1.0, description="Minimum confidence score")


class SimilarChunksRequest(BaseModel):
    chunk_id: str = Field(..., description="UUID of the reference chunk")
    top_k: int = Field(default=10, ge=1, le=100, description="Number of similar chunks to return")
    similarity_threshold: float = Field(default=0.65, ge=0.0, le=1.0, description="Minimum similarity score")


# ── Response schemas ──────────────────────────────────────────────────────


class RetrievalResultItem(BaseModel):
    """Single result item from a retrieval operation."""

    chunk_id: str = Field(description="UUID of the chunk")
    text: str = Field(description="Full chunk text")
    title: str = Field(default="", description="First line of the chunk — used as display title")
    description: str = Field(default="", description="Remaining chunk text after the title")
    req_id: str = Field(default="", description="Sequential requirement ID e.g. FR-01")
    type_label: str = Field(default="Functional", description="Human-readable category label")
    category: str = Field(description="Classification category")
    section: str = Field(description="Section heading")
    subsection: str = Field(description="Subsection heading")
    page_number: int = Field(description="Page number in document")
    score: float = Field(description="Similarity score (0.0-1.0)")
    confidence_score: float = Field(description="Classification confidence (0.0-1.0)")
    document_id: str = Field(description="UUID of source document")
    chunk_type: str = Field(description="Chunk type")


class SemanticSearchResponse(BaseModel):
    project_id: str
    query: str
    total_results: int
    results: list[RetrievalResultItem]


class CategorySearchResponse(BaseModel):
    project_id: str
    category: str
    total_results: int
    results: list[RetrievalResultItem]


class SimilarChunksResponse(BaseModel):
    project_id: str
    reference_chunk_id: str
    total_results: int
    results: list[RetrievalResultItem]


# ── Statistics schemas ────────────────────────────────────────────────────


class ProjectStatistics(BaseModel):
    project_id: str
    total_chunks: int
    chunks_by_category: dict[str, int]
    chunks_by_document: dict[str, int]
    chunks_by_type: dict[str, int]


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
