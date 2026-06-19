"""
semantic_search.py — Core semantic search service for Qdrant retrieval.

All searches are project-scoped — every query MUST filter by project_id.
Results include title and description fields extracted from chunk text.
"""

import logging
from typing import Any

from qdrant_client.models import FieldCondition, Filter, MatchValue

from app.services.embeddings.embedding_service import EmbeddingService
from app.services.vector.qdrant_service import QdrantService

logger = logging.getLogger(__name__)

# Minimum text length for a chunk to be included in results
_MIN_TEXT_LENGTH = 15


def _extract_title_description(text: str) -> tuple[str, str]:
    """
    Split chunk text into a title (first line) and description (remaining lines).

    Args:
        text: Full chunk text.

    Returns:
        (title, description) tuple.
    """
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    title = lines[0] if lines else ""
    description = " ".join(lines[1:]) if len(lines) > 1 else text.strip()
    return title, description


class SemanticSearchService:
    """
    Performs semantic similarity searches in Qdrant with metadata filtering.
    All searches are project-scoped — project_id is mandatory.
    """

    def __init__(self) -> None:
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
        """
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
            project_id, len(query), top_k, category, similarity_threshold,
        )

        try:
            query_embedding = self._embedding_service.embed([query])[0]
        except Exception as e:
            logger.error("SemanticSearchService: failed to embed query: %s", str(e))
            raise

        filter_conditions = [
            FieldCondition(key="project_id", match=MatchValue(value=project_id))
        ]
        if category:
            filter_conditions.append(FieldCondition(key="category", match=MatchValue(value=category)))
        if section:
            filter_conditions.append(FieldCondition(key="section", match=MatchValue(value=section)))
        if document_id:
            filter_conditions.append(FieldCondition(key="document_id", match=MatchValue(value=document_id)))
        if chunk_type:
            filter_conditions.append(FieldCondition(key="chunk_type", match=MatchValue(value=chunk_type)))

        search_filter = Filter(must=filter_conditions)

        try:
            search_results = self._qdrant_service.search(
                query_vector=query_embedding,
                query_filter=search_filter,
                limit=top_k,
            )
        except Exception as e:
            logger.error("SemanticSearchService: Qdrant search failed: %s", str(e))
            raise

        formatted_results = []
        for result in search_results:
            score = result.score
            payload = result.payload

            if score < similarity_threshold:
                continue

            raw_text = payload.get("text", "")
            if len(raw_text) < _MIN_TEXT_LENGTH:
                continue

            title, description = _extract_title_description(raw_text)

            formatted_results.append({
                "chunk_id": payload.get("chunk_id", ""),
                "text": raw_text,
                "title": title,
                "description": description,
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
            len(formatted_results), similarity_threshold,
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
        Uses a low fixed threshold (0.3) for category browsing.
        """
        if not project_id or not project_id.strip():
            raise ValueError("project_id is required and cannot be empty")
        if not category or not category.strip():
            raise ValueError("category is required and cannot be empty")

        logger.info(
            "SemanticSearchService.search_by_category: project=%s category=%s top_k=%d",
            project_id, category, top_k,
        )

        search_filter = Filter(
            must=[
                FieldCondition(key="project_id", match=MatchValue(value=project_id)),
                FieldCondition(key="category", match=MatchValue(value=category)),
            ]
        )

        try:
            all_results = self._qdrant_service.scroll(
                query_filter=search_filter,
                limit=top_k * 2,
            )
        except Exception as e:
            logger.error(
                "SemanticSearchService: scroll failed for category %s: %s", category, str(e)
            )
            raise

        formatted_results = []
        for point in all_results:
            payload = point.payload
            confidence = payload.get("confidence_score", 0.0)

            # Use a low fixed threshold for category browsing
            if confidence < 0.3:
                continue

            raw_text = payload.get("text", "")
            if len(raw_text) < _MIN_TEXT_LENGTH:
                continue

            title, description = _extract_title_description(raw_text)

            formatted_results.append({
                "chunk_id": payload.get("chunk_id", ""),
                "text": raw_text,
                "title": title,
                "description": description,
                "category": payload.get("category", ""),
                "section": payload.get("section", ""),
                "subsection": payload.get("subsection", ""),
                "page_number": payload.get("page_number", 0),
                "score": confidence,
                "confidence_score": confidence,
                "document_id": payload.get("document_id", ""),
                "chunk_type": payload.get("chunk_type", ""),
            })

        formatted_results.sort(key=lambda x: x["confidence_score"], reverse=True)
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
        """
        if not project_id or not project_id.strip():
            raise ValueError("project_id is required and cannot be empty")
        if not chunk_id or not chunk_id.strip():
            raise ValueError("chunk_id is required and cannot be empty")

        logger.info(
            "SemanticSearchService.find_similar_chunks: project=%s chunk=%s top_k=%d",
            project_id, chunk_id, top_k,
        )

        try:
            reference_point = self._qdrant_service.get_point(chunk_id)
        except Exception as e:
            logger.error(
                "SemanticSearchService: failed to retrieve chunk %s: %s", chunk_id, str(e)
            )
            raise ValueError(f"Chunk {chunk_id} not found in vector store")

        if reference_point is None:
            raise ValueError(f"Chunk {chunk_id} not found in vector store")

        reference_vector = reference_point.vector

        search_filter = Filter(
            must=[FieldCondition(key="project_id", match=MatchValue(value=project_id))]
        )

        try:
            search_results = self._qdrant_service.search(
                query_vector=reference_vector,
                query_filter=search_filter,
                limit=top_k + 1,
            )
        except Exception as e:
            logger.error("SemanticSearchService: similarity search failed: %s", str(e))
            raise

        formatted_results = []
        for result in search_results:
            payload = result.payload
            score = result.score

            if payload.get("chunk_id") == chunk_id:
                continue
            if score < similarity_threshold:
                continue

            raw_text = payload.get("text", "")
            title, description = _extract_title_description(raw_text)

            formatted_results.append({
                "chunk_id": payload.get("chunk_id", ""),
                "text": raw_text,
                "title": title,
                "description": description,
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
