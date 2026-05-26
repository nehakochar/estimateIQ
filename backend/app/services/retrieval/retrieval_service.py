"""
retrieval_service.py — Orchestrates retrieval operations and integrates with database.

Responsibilities:
  - Coordinate semantic search with database lookups
  - Enrich search results with additional metadata from PostgreSQL
  - Validate project and document ownership
  - Log retrieval metrics and performance
  - Handle retrieval errors gracefully

This service bridges the gap between the vector database (Qdrant) and
the relational database (PostgreSQL), ensuring data consistency and
providing a unified retrieval interface.
"""

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.project import Project
from app.models.semantic_chunk import SemanticChunk
from app.services.retrieval.semantic_search import SemanticSearchService

logger = logging.getLogger(__name__)


class RetrievalService:
    """
    Orchestrates retrieval operations with database integration.

    Provides high-level retrieval APIs that combine semantic search with
    database validation and enrichment.

    Usage:
        service = RetrievalService(db)
        results = service.search(
            project_id="project_123",
            query="authentication requirements",
            top_k=10,
        )
    """

    def __init__(self, db: Session) -> None:
        """Initialize with database session and semantic search service."""
        self.db = db
        self._search_service = SemanticSearchService()

    def search(
        self,
        project_id: str,
        query: str,
        top_k: int = 10,
        category: str | None = None,
        section: str | None = None,
        document_id: str | None = None,
        chunk_type: str | None = None,
        similarity_threshold: float = 0.65,
    ) -> list[dict[str, Any]]:
        """
        Perform semantic search with database validation.

        Validates that the project exists and (if provided) that the document
        belongs to the project before executing the search.

        Args:
            project_id: UUID string of the project.
            query: Search query text.
            top_k: Number of results to return.
            category: Optional category filter.
            section: Optional section filter.
            document_id: Optional document UUID filter.
            chunk_type: Optional chunk type filter.
            similarity_threshold: Minimum similarity score.

        Returns:
            List of result dicts with chunk metadata and similarity scores.

        Raises:
            ValueError: If project doesn't exist or document doesn't belong to project.
        """
        # Validate project exists
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project {project_id} not found")

        # Validate document if provided
        if document_id:
            document = (
                self.db.query(Document)
                .filter(
                    Document.id == document_id,
                    Document.project_id == project_id,
                )
                .first()
            )
            if not document:
                raise ValueError(
                    f"Document {document_id} not found in project {project_id}"
                )

        logger.info(
            "RetrievalService.search: project=%s query_len=%d top_k=%d",
            project_id,
            len(query),
            top_k,
        )

        # Execute semantic search
        results = self._search_service.search(
            project_id=project_id,
            query=query,
            top_k=top_k,
            category=category,
            section=section,
            document_id=document_id,
            chunk_type=chunk_type,
            similarity_threshold=similarity_threshold,
        )

        logger.info(
            "RetrievalService.search: returned %d results", len(results)
        )

        return results

    def search_by_category(
        self,
        project_id: str,
        category: str,
        top_k: int = 10,
        similarity_threshold: float = 0.65,
    ) -> list[dict[str, Any]]:
        """
        Retrieve top chunks for a category with database validation.

        Args:
            project_id: UUID string of the project.
            category: Category to retrieve.
            top_k: Number of results to return.
            similarity_threshold: Minimum confidence score.

        Returns:
            List of result dicts ordered by confidence score.

        Raises:
            ValueError: If project doesn't exist.
        """
        # Validate project exists
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project {project_id} not found")

        logger.info(
            "RetrievalService.search_by_category: project=%s category=%s top_k=%d",
            project_id,
            category,
            top_k,
        )

        results = self._search_service.search_by_category(
            project_id=project_id,
            category=category,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
        )

        logger.info(
            "RetrievalService.search_by_category: returned %d results",
            len(results),
        )

        return results

    def find_similar_chunks(
        self,
        project_id: str,
        chunk_id: str,
        top_k: int = 10,
        similarity_threshold: float = 0.65,
    ) -> list[dict[str, Any]]:
        """
        Find chunks similar to a given chunk with database validation.

        Args:
            project_id: UUID string of the project.
            chunk_id: UUID of the reference chunk.
            top_k: Number of similar chunks to return.
            similarity_threshold: Minimum similarity score.

        Returns:
            List of similar chunk dicts.

        Raises:
            ValueError: If project or chunk doesn't exist.
        """
        # Validate project exists
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project {project_id} not found")

        # Validate chunk exists and belongs to project
        chunk = (
            self.db.query(SemanticChunk)
            .filter(
                SemanticChunk.id == chunk_id,
                SemanticChunk.project_id == project_id,
            )
            .first()
        )
        if not chunk:
            raise ValueError(
                f"Chunk {chunk_id} not found in project {project_id}"
            )

        logger.info(
            "RetrievalService.find_similar_chunks: project=%s chunk=%s top_k=%d",
            project_id,
            chunk_id,
            top_k,
        )

        results = self._search_service.find_similar_chunks(
            project_id=project_id,
            chunk_id=chunk_id,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
        )

        logger.info(
            "RetrievalService.find_similar_chunks: returned %d results",
            len(results),
        )

        return results

    def get_project_statistics(self, project_id: str) -> dict[str, Any]:
        """
        Get retrieval statistics for a project.

        Returns counts of chunks by category, document, and chunk type.

        Args:
            project_id: UUID string of the project.

        Returns:
            Dict with statistics:
              - total_chunks: Total number of chunks in project
              - chunks_by_category: Dict of category -> count
              - chunks_by_document: Dict of document_id -> count
              - chunks_by_type: Dict of chunk_type -> count

        Raises:
            ValueError: If project doesn't exist.
        """
        # Validate project exists
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project {project_id} not found")

        logger.info(
            "RetrievalService.get_project_statistics: project=%s", project_id
        )

        # Query statistics from database
        total_chunks = (
            self.db.query(SemanticChunk)
            .filter(SemanticChunk.project_id == project_id)
            .count()
        )

        # Category distribution
        category_stats = (
            self.db.query(
                SemanticChunk.category,
                func.count(SemanticChunk.id).label("count"),
            )
            .filter(SemanticChunk.project_id == project_id)
            .group_by(SemanticChunk.category)
            .all()
        )
        chunks_by_category = {cat: count for cat, count in category_stats}

        # Document distribution
        document_stats = (
            self.db.query(
                SemanticChunk.document_id,
                func.count(SemanticChunk.id).label("count"),
            )
            .filter(SemanticChunk.project_id == project_id)
            .group_by(SemanticChunk.document_id)
            .all()
        )
        chunks_by_document = {str(doc_id): count for doc_id, count in document_stats}

        # Chunk type distribution
        type_stats = (
            self.db.query(
                SemanticChunk.chunk_type,
                func.count(SemanticChunk.id).label("count"),
            )
            .filter(SemanticChunk.project_id == project_id)
            .group_by(SemanticChunk.chunk_type)
            .all()
        )
        chunks_by_type = {chunk_type: count for chunk_type, count in type_stats}

        stats = {
            "total_chunks": total_chunks,
            "chunks_by_category": chunks_by_category,
            "chunks_by_document": chunks_by_document,
            "chunks_by_type": chunks_by_type,
        }

        logger.info(
            "RetrievalService.get_project_statistics: total_chunks=%d",
            total_chunks,
        )

        return stats


# Import func for aggregation queries
from sqlalchemy import func
