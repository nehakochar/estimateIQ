"""
QdrantService — manages all interactions with the Qdrant vector database.

Responsibilities:
  - Collection initialisation (ensure_collection)
  - Upserting PointStruct objects (upsert_points)
  - Deleting vectors by project_id (delete_project_vectors)
  - Counting vectors by project_id (get_vector_count)
  - Scrolling / inspecting vectors with arbitrary payload filters (inspect_vectors)

All operations use ``settings.embedding_collection_name`` as the collection name;
the string ``"rfp_chunks"`` is never hardcoded in this module.
"""

import logging
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from app.core.config import settings

logger = logging.getLogger(__name__)


class QdrantService:
    """Service class for all Qdrant vector-database operations."""

    def __init__(self) -> None:
        """Instantiate the Qdrant client using settings."""
        self._client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
        )

    # ------------------------------------------------------------------
    # Collection management
    # ------------------------------------------------------------------

    def ensure_collection(self) -> None:
        """Create the collection if it does not already exist.

        If the collection already exists this method is a no-op and will
        never raise an exception.
        """
        collection_name = settings.embedding_collection_name
        if not self._client.collection_exists(collection_name):
            self._client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )
            logger.info("QdrantService: created collection '%s'", collection_name)
        else:
            logger.debug(
                "QdrantService: collection '%s' already exists — no-op", collection_name
            )

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def upsert_points(self, points: list[PointStruct]) -> None:
        """Upsert all provided points into the collection in a single call.

        Any exception raised by the Qdrant client is re-raised so the
        caller (EmbeddingPipeline) can handle per-batch failure.
        """
        self._client.upsert(
            collection_name=settings.embedding_collection_name,
            points=points,
        )

    def delete_project_vectors(self, project_id: str) -> None:
        """Delete all points whose payload ``project_id`` matches *project_id*."""
        self._client.delete(
            collection_name=settings.embedding_collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="project_id",
                        match=MatchValue(value=project_id),
                    )
                ]
            ),
        )
        logger.info(
            "QdrantService: deleted vectors for project_id='%s'", project_id
        )

    # ------------------------------------------------------------------
    # Read / query operations
    # ------------------------------------------------------------------

    def get_vector_count(self, project_id: str) -> int:
        """Return the number of points whose payload ``project_id`` matches."""
        result = self._client.count(
            collection_name=settings.embedding_collection_name,
            count_filter=Filter(
                must=[
                    FieldCondition(
                        key="project_id",
                        match=MatchValue(value=project_id),
                    )
                ]
            ),
        )
        return result.count

    def inspect_vectors(self, filters: dict[str, Any]) -> list[dict]:
        """Scroll the collection and return payload dicts matching *filters*.

        Each key-value pair in *filters* becomes a ``FieldCondition`` in the
        ``must`` list of the scroll filter.  Vectors are not returned
        (``with_vectors=False``).
        """
        must_conditions = [
            FieldCondition(key=k, match=MatchValue(value=v))
            for k, v in filters.items()
        ]
        scroll_filter = Filter(must=must_conditions) if must_conditions else None

        records, _ = self._client.scroll(
            collection_name=settings.embedding_collection_name,
            scroll_filter=scroll_filter,
            with_payload=True,
            with_vectors=False,
        )

        return [record.payload for record in records if record.payload is not None]
