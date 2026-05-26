"""
semantic_search.py — Core semantic search service for Qdrant retrieval.

Responsibilities:
  - Generate query embeddings using EmbeddingService
  - Execute semantic similarity searches in Qdrant
  - Apply metadata filters (category, section, document_id, etc.)
  - Support project-scoped retrieval (mandatory)
  - Return ranked results with similarity scores

All searches are project-scoped — every query MUST filter by project_id.
This is mandatory because the platform supports multiple RFPs/projects.
"""

import logging
from typing import Any

from qdrant_client.models import FieldCondition, Filter, MatchValue

from app.core.config import settings
from app.services.embeddings.embedding_service import EmbeddingService
from app.services.vector.qdrant_service import QdrantService

logger = logging.getLogger(__name__)


class SemanticSearchService:
    """
    Performs semantic similarity searches in Qdrant with metadata filtering.

    All searches are project-scoped — project_id is mandatory and applied
    as a filter on every query.

    Usage:
        service = SemanticSearchService()
        results = service.search(
            project_id="project_123",
            query="authentication requirements",
            top_k=10,
            category="security_compliance",
        )
    """

    def __init__(self) -> None:
        """Initialize embedding and Qdrant services."""
        self._embedding_service = EmbeddingService()
        self._qdrant_service = QdrantService()

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
        Perform semantic similarity search with optional metadata filtering.

        All results are filtered by project_id (mandatory). Additional filters
        can be applied for category, section, document_id, and chunk_type.

        Args:
            project_id: UUID string of the project (mandatory, non-empty).
            query: Search query text to embed and match.
            top_k: Number of top results to return (default 10).
            category: Optional category filter (one of 11 valid categories).
            section: Optional section heading filter.
            document_id: Optional document UUID filter.
            chunk_type: Optional chunk type filter ("requirement" or "workflow").
            similarity_threshold: Minimum similarity score to include (0.0–1.0).

        Returns:
            List of result dicts with keys:
              - chunk_id: UUID of the chunk
              - text: Full chunk text
              - category: Classification category
              - section: Section heading
              - subsection: Subsection heading
              - page_number: Page number in document
              - score: Similarity score (0.0–1.0)
              - confidence_score: Classification confidence (0.0–1.0)
              - document_id: UUID of source document
              - chunk_type: "requirement" or "workflow"

        Raises:
            ValueError: If project_id is empty or query is empty.
            Exception: If Qdrant search fails (propagated from QdrantService).
        """
        # ── Validate inputs ───────────────────────────────────────
        if not project_id or not project_id.strip():
            raise ValueError("project_id is required and cannot be empty")
        if not query or not query.strip():
            raise ValueError("query is required and cannot be empty")
        if not (0.0 <= similarity_threshold <= 1.0):
            raise ValueError("similarity_threshold must be between 0.0 and 1.0")
        if top_k < 1:
            raise ValueError("top_k must be at least 1")

        logger.info(
            "SemanticSearchService.search: project=%s query_len=%d top_k=%d "
            "category=%s threshold=%.2f",
            project_id,
            len(query),
            top_k,
            category,
            similarity_threshold,
        )

        # ── Generate query embedding ──────────────────────────────
        try:
            query_embedding = self._embedding_service.embed([query])[0]
        except Exception as e:
            logger.error(
                "SemanticSearchService: failed to embed query: %s", str(e)
            )
            raise

        # ── Build metadata filter (project_id is mandatory) ────────
        filter_conditions = [
            FieldCondition(
                key="project_id",
                match=MatchValue(value=project_id),
            )
        ]

        # Add optional filters
        if category:
            filter_conditions.append(
                FieldCondition(
                    key="category",
                    match=MatchValue(value=category),
                )
            )
        if section:
            filter_conditions.append(
                FieldCondition(
                    key="section",
                    match=MatchValue(value=section),
                )
            )
        if document_id:
            filter_conditions.append(
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=document_id),
                )
            )
        if chunk_type:
            filter_conditions.append(
                FieldCondition(
                    key="chunk_type",
                    match=MatchValue(value=chunk_type),
                )
            )

        search_filter = Filter(must=filter_conditions)

        # ── Execute Qdrant search ─────────────────────────────────
        try:
            search_results = self._qdrant_service.search(
                query_vector=query_embedding,
                query_filter=search_filter,
                limit=top_k,
            )
        except Exception as e:
            logger.error(
                "SemanticSearchService: Qdrant search failed: %s", str(e)
            )
            raise

        # ── Format and filter results ─────────────────────────────
        formatted_results = []
        for result in search_results:
            # result is a ScoredPoint with score and payload
            score = result.score
            payload = result.payload

            # Apply similarity threshold
            if score < similarity_threshold:
                logger.debug(
                    "SemanticSearchService: skipping result with score %.3f "
                    "(below threshold %.2f)",
                    score,
                    similarity_threshold,
                )
                continue

            formatted_results.append({
                "chunk_id": payload.get("chunk_id", ""),
                "text": payload.get("text", ""),
                "category": payload.get("category", ""),
                "section": payload.get("section", ""),
                "subsection": payload.get("subsection", ""),
                "page_number": payload.get("page_number", 0),
                "score": score,
                "confidence_score": payload.get("confidence_score", 0.0),
                "document_id": payload.get("document_id", ""),
                "chunk_type": payload.get("chunk_type", ""),
            })

        logger.info(
            "SemanticSearchService.search: returned %d results (threshold=%.2f)",
            len(formatted_results),
            similarity_threshold,
        )

        return formatted_results

    def search_by_category(
        self,
        project_id: str,
        category: str,
        top_k: int = 10,
        similarity_threshold: float = 0.65,
    ) -> list[dict[str, Any]]:
        """
        Retrieve top chunks for a specific category without a query.

        Useful for browsing all chunks in a category or getting category
        statistics. Returns chunks ordered by confidence score (descending).

        Args:
            project_id: UUID string of the project.
            category: Category to retrieve (one of 11 valid categories).
            top_k: Number of results to return.
            similarity_threshold: Minimum confidence score to include.

        Returns:
            List of result dicts (same format as search()).
        """
        if not project_id or not project_id.strip():
            raise ValueError("project_id is required and cannot be empty")
        if not category or not category.strip():
            raise ValueError("category is required and cannot be empty")

        logger.info(
            "SemanticSearchService.search_by_category: project=%s category=%s top_k=%d",
            project_id,
            category,
            top_k,
        )

        # Build filter for project_id and category
        search_filter = Filter(
            must=[
                FieldCondition(
                    key="project_id",
                    match=MatchValue(value=project_id),
                ),
                FieldCondition(
                    key="category",
                    match=MatchValue(value=category),
                ),
            ]
        )

        # Use scroll to get all chunks matching the filter, then sort by confidence
        try:
            all_results = self._qdrant_service.scroll(
                query_filter=search_filter,
                limit=top_k * 2,  # Get extra to account for filtering
            )
        except Exception as e:
            logger.error(
                "SemanticSearchService: scroll failed for category %s: %s",
                category,
                str(e),
            )
            raise

        # Format and sort by confidence score (descending)
        formatted_results = []
        for point in all_results:
            payload = point.payload
            confidence = payload.get("confidence_score", 0.0)

            if confidence < similarity_threshold:
                continue

            formatted_results.append({
                "chunk_id": payload.get("chunk_id", ""),
                "text": payload.get("text", ""),
                "category": payload.get("category", ""),
                "section": payload.get("section", ""),
                "subsection": payload.get("subsection", ""),
                "page_number": payload.get("page_number", 0),
                "score": confidence,  # Use confidence as score for category search
                "confidence_score": confidence,
                "document_id": payload.get("document_id", ""),
                "chunk_type": payload.get("chunk_type", ""),
            })

        # Sort by confidence score descending
        formatted_results.sort(key=lambda x: x["confidence_score"], reverse=True)

        # Return top_k
        return formatted_results[:top_k]

    def find_similar_chunks(
        self,
        project_id: str,
        chunk_id: str,
        top_k: int = 10,
        similarity_threshold: float = 0.65,
    ) -> list[dict[str, Any]]:
        """
        Find chunks similar to a given chunk (excluding the chunk itself).

        Useful for finding related requirements or discovering duplicate/similar
        chunks across documents.

        Args:
            project_id: UUID string of the project.
            chunk_id: UUID of the reference chunk.
            top_k: Number of similar chunks to return.
            similarity_threshold: Minimum similarity score to include.

        Returns:
            List of result dicts (same format as search()).

        Raises:
            ValueError: If chunk_id is not found in Qdrant.
        """
        if not project_id or not project_id.strip():
            raise ValueError("project_id is required and cannot be empty")
        if not chunk_id or not chunk_id.strip():
            raise ValueError("chunk_id is required and cannot be empty")

        logger.info(
            "SemanticSearchService.find_similar_chunks: project=%s chunk=%s top_k=%d",
            project_id,
            chunk_id,
            top_k,
        )

        # Retrieve the reference chunk's vector from Qdrant
        try:
            reference_point = self._qdrant_service.get_point(chunk_id)
        except Exception as e:
            logger.error(
                "SemanticSearchService: failed to retrieve chunk %s: %s",
                chunk_id,
                str(e),
            )
            raise ValueError(f"Chunk {chunk_id} not found in vector store")

        if reference_point is None:
            raise ValueError(f"Chunk {chunk_id} not found in vector store")

        # Get the vector
        reference_vector = reference_point.vector

        # Build filter for project_id only (exclude the reference chunk itself)
        search_filter = Filter(
            must=[
                FieldCondition(
                    key="project_id",
                    match=MatchValue(value=project_id),
                )
            ]
        )

        # Search for similar vectors
        try:
            search_results = self._qdrant_service.search(
                query_vector=reference_vector,
                query_filter=search_filter,
                limit=top_k + 1,  # +1 to account for the reference chunk itself
            )
        except Exception as e:
            logger.error(
                "SemanticSearchService: similarity search failed: %s", str(e)
            )
            raise

        # Format results, excluding the reference chunk itself
        formatted_results = []
        for result in search_results:
            payload = result.payload
            score = result.score

            # Skip the reference chunk itself
            if payload.get("chunk_id") == chunk_id:
                continue

            # Apply similarity threshold
            if score < similarity_threshold:
                continue

            formatted_results.append({
                "chunk_id": payload.get("chunk_id", ""),
                "text": payload.get("text", ""),
                "category": payload.get("category", ""),
                "section": payload.get("section", ""),
                "subsection": payload.get("subsection", ""),
                "page_number": payload.get("page_number", 0),
                "score": score,
                "confidence_score": payload.get("confidence_score", 0.0),
                "document_id": payload.get("document_id", ""),
                "chunk_type": payload.get("chunk_type", ""),
            })

        logger.info(
            "SemanticSearchService.find_similar_chunks: returned %d results",
            len(formatted_results),
        )

        return formatted_results[:top_k]
