"""
chunking.py — Pydantic response schemas for the chunk inspection API.
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, field_validator


class ChunkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    chunk_index: int
    parent_chunk_id: uuid.UUID | None
    section: str
    subsection: str
    level: int
    page_number: int
    chunk_type: str
    token_count: int
    text: str


class DocumentChunksResponse(BaseModel):
    document_id: str
    total_chunks: int
    chunks: list[ChunkResponse]
