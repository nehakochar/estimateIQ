"""
debug_utils.py — Debugging utilities for retrieval operations.

Provides tools for:
  - Inspecting retrieved chunks
  - Analyzing metadata filters
  - Examining similarity scores
  - Logging retrieval metrics
"""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class RetrievalDebugWriter:
    """Writes debug snapshots of retrieval operations to disk."""

    def __init__(self, debug_output_root: str = "storage/debug/retrieval") -> None:
        """Initialize debug writer with output directory."""
        self.debug_output_root = Path(debug_output_root)
        self.debug_output_root.mkdir(parents=True, exist_ok=True)

    def write_search_results(
        self,
        project_id: str,
        query: str,
        results: list[dict[str, Any]],
        filters: dict[str, Any] | None = None,
    ) -> None:
        """
        Write search results to a debug JSON file.

        Args:
            project_id: UUID of the project.
            query: Search query text.
            results: List of result dicts.
            filters: Optional metadata filters applied.
        """
        debug_data = {
            "project_id": project_id,
            "query": query,
            "filters": filters or {},
            "total_results": len(results),
            "results": results,
        }

        filename = self.debug_output_root / f"search_{project_id}_{len(results)}_results.json"
        try:
            with open(filename, "w") as f:
                json.dump(debug_data, f, indent=2, default=str)
            logger.debug("RetrievalDebugWriter: wrote search results to %s", filename)
        except Exception as e:
            logger.error("RetrievalDebugWriter: failed to write search results: %s", str(e))

    def write_category_results(
        self,
        project_id: str,
        category: str,
        results: list[dict[str, Any]],
    ) -> None:
        """
        Write category search results to a debug JSON file.

        Args:
            project_id: UUID of the project.
            category: Category searched.
            results: List of result dicts.
        """
        debug_data = {
            "project_id": project_id,
            "category": category,
            "total_results": len(results),
            "results": results,
        }

        filename = self.debug_output_root / f"category_{category}_{len(results)}_results.json"
        try:
            with open(filename, "w") as f:
                json.dump(debug_data, f, indent=2, default=str)
            logger.debug("RetrievalDebugWriter: wrote category results to %s", filename)
        except Exception as e:
            logger.error("RetrievalDebugWriter: failed to write category results: %s", str(e))

    def write_similarity_analysis(
        self,
        project_id: str,
        reference_chunk_id: str,
        results: list[dict[str, Any]],
    ) -> None:
        """
        Write similarity search analysis to a debug JSON file.

        Args:
            project_id: UUID of the project.
            reference_chunk_id: UUID of the reference chunk.
            results: List of similar chunk dicts.
        """
        debug_data = {
            "project_id": project_id,
            "reference_chunk_id": reference_chunk_id,
            "total_similar": len(results),
            "results": results,
        }

        filename = self.debug_output_root / f"similar_{reference_chunk_id}_{len(results)}_results.json"
        try:
            with open(filename, "w") as f:
                json.dump(debug_data, f, indent=2, default=str)
            logger.debug("RetrievalDebugWriter: wrote similarity analysis to %s", filename)
        except Exception as e:
            logger.error("RetrievalDebugWriter: failed to write similarity analysis: %s", str(e))


def inspect_retrieved_chunks(results: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Analyze and inspect retrieved chunks.

    Args:
        results: List of result dicts from retrieval.

    Returns:
        Dict with analysis:
          - total_chunks: Number of chunks
          - avg_score: Average similarity score
          - score_range: (min, max) scores
          - categories: Unique categories
          - documents: Unique documents
          - sections: Unique sections
          - avg_confidence: Average classification confidence
    """
    if not results:
        return {
            "total_chunks": 0,
            "avg_score": 0.0,
            "score_range": (0.0, 0.0),
            "categories": [],
            "documents": [],
            "sections": [],
            "avg_confidence": 0.0,
        }

    scores = [r.get("score", 0) for r in results]
    confidences = [r.get("confidence_score", 0) for r in results]
    categories = sorted(set(r.get("category") for r in results if r.get("category")))
    documents = sorted(set(r.get("document_id") for r in results if r.get("document_id")))
    sections = sorted(set(r.get("section") for r in results if r.get("section")))

    return {
        "total_chunks": len(results),
        "avg_score": sum(scores) / len(scores) if scores else 0.0,
        "score_range": (min(scores), max(scores)) if scores else (0.0, 0.0),
        "categories": categories,
        "documents": documents,
        "sections": sections,
        "avg_confidence": sum(confidences) / len(confidences) if confidences else 0.0,
    }


def inspect_metadata_filters(filters: dict[str, Any]) -> dict[str, Any]:
    """
    Analyze metadata filters applied to a search.

    Args:
        filters: Dict of filter key-value pairs.

    Returns:
        Dict with filter analysis.
    """
    return {
        "total_filters": len(filters),
        "filters": filters,
        "filter_keys": list(filters.keys()),
    }


def inspect_similarity_scores(results: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Analyze similarity score distribution.

    Args:
        results: List of result dicts.

    Returns:
        Dict with score analysis:
          - total_results: Number of results
          - avg_score: Average score
          - median_score: Median score
          - score_distribution: Histogram of scores
    """
    if not results:
        return {
            "total_results": 0,
            "avg_score": 0.0,
            "median_score": 0.0,
            "score_distribution": {},
        }

    scores = sorted([r.get("score", 0) for r in results])
    total = len(scores)
    avg = sum(scores) / total if total else 0.0
    median = scores[total // 2] if total else 0.0

    # Create histogram (0.0-0.1, 0.1-0.2, etc.)
    distribution = {}
    for i in range(10):
        bucket = f"{i * 0.1:.1f}-{(i + 1) * 0.1:.1f}"
        count = sum(1 for s in scores if i * 0.1 <= s < (i + 1) * 0.1)
        if count > 0:
            distribution[bucket] = count

    return {
        "total_results": total,
        "avg_score": round(avg, 4),
        "median_score": round(median, 4),
        "score_distribution": distribution,
    }


def log_retrieval_metrics(
    operation: str,
    project_id: str,
    results: list[dict[str, Any]],
    latency_ms: float | None = None,
) -> None:
    """
    Log retrieval operation metrics.

    Args:
        operation: Name of the operation (e.g., "semantic_search").
        project_id: UUID of the project.
        results: List of result dicts.
        latency_ms: Optional latency in milliseconds.
    """
    total = len(results)
    avg_score = sum(r.get("score", 0) for r in results) / total if total else 0.0
    categories = len(set(r.get("category") for r in results if r.get("category")))
    documents = len(set(r.get("document_id") for r in results if r.get("document_id")))

    latency_str = f" latency={latency_ms:.1f}ms" if latency_ms else ""
    logger.info(
        "RetrievalMetrics: operation=%s project=%s results=%d avg_score=%.3f "
        "categories=%d documents=%d%s",
        operation,
        project_id,
        total,
        avg_score,
        categories,
        documents,
        latency_str,
    )
