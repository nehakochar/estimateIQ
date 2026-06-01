"""
search_utils.py — Utility functions for search operations.

Provides:
  - Query validation and normalization
  - Result ranking and filtering
  - Metadata extraction
  - Search metrics and logging
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def normalize_query(query: str) -> str:
    """
    Normalize a search query.

    - Strip leading/trailing whitespace
    - Convert to lowercase
    - Remove extra whitespace

    Args:
        query: Raw query string.

    Returns:
        Normalized query string.
    """
    return " ".join(query.strip().lower().split())


def validate_category(category: str, valid_categories: set[str]) -> bool:
    """
    Validate that a category is in the valid set.

    Args:
        category: Category string to validate.
        valid_categories: Set of valid category strings.

    Returns:
        True if category is valid, False otherwise.
    """
    return category in valid_categories


def rank_results(
    results: list[dict[str, Any]],
    sort_by: str = "score",
    reverse: bool = True,
) -> list[dict[str, Any]]:
    """
    Rank and sort search results.

    Args:
        results: List of result dicts.
        sort_by: Field to sort by ("score", "confidence_score", "page_number").
        reverse: Sort in descending order if True.

    Returns:
        Sorted list of results.
    """
    if not results:
        return results

    try:
        return sorted(results, key=lambda x: x.get(sort_by, 0), reverse=reverse)
    except Exception as e:
        logger.error("rank_results: failed to sort by %s: %s", sort_by, str(e))
        return results


def filter_by_threshold(
    results: list[dict[str, Any]],
    threshold: float,
    field: str = "score",
) -> list[dict[str, Any]]:
    """
    Filter results by a minimum threshold on a numeric field.

    Args:
        results: List of result dicts.
        threshold: Minimum value to include.
        field: Field name to check ("score", "confidence_score", "page_number").

    Returns:
        Filtered list of results.
    """
    return [r for r in results if r.get(field, 0) >= threshold]


def deduplicate_results(
    results: list[dict[str, Any]],
    key: str = "chunk_id",
) -> list[dict[str, Any]]:
    """
    Remove duplicate results based on a key field.

    Keeps the first occurrence of each key value.

    Args:
        results: List of result dicts.
        key: Field to use for deduplication.

    Returns:
        Deduplicated list of results.
    """
    seen = set()
    deduplicated = []
    for result in results:
        key_value = result.get(key)
        if key_value not in seen:
            seen.add(key_value)
            deduplicated.append(result)
    return deduplicated


def extract_metadata(result: dict[str, Any]) -> dict[str, Any]:
    """
    Extract metadata from a search result.

    Returns a dict with only metadata fields (excluding text).

    Args:
        result: Result dict from search.

    Returns:
        Dict with metadata fields.
    """
    return {
        "chunk_id": result.get("chunk_id"),
        "category": result.get("category"),
        "section": result.get("section"),
        "subsection": result.get("subsection"),
        "page_number": result.get("page_number"),
        "score": result.get("score"),
        "confidence_score": result.get("confidence_score"),
        "document_id": result.get("document_id"),
        "chunk_type": result.get("chunk_type"),
    }


def calculate_search_metrics(
    results: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Calculate metrics for a set of search results.

    Args:
        results: List of result dicts.

    Returns:
        Dict with metrics:
          - total_results: Number of results
          - avg_score: Average similarity score
          - avg_confidence: Average classification confidence
          - score_range: (min, max) of similarity scores
          - categories: Set of unique categories
          - documents: Set of unique document IDs
    """
    if not results:
        return {
            "total_results": 0,
            "avg_score": 0.0,
            "avg_confidence": 0.0,
            "score_range": (0.0, 0.0),
            "categories": set(),
            "documents": set(),
        }

    scores = [r.get("score", 0) for r in results]
    confidences = [r.get("confidence_score", 0) for r in results]
    categories = {r.get("category") for r in results}
    documents = {r.get("document_id") for r in results}

    return {
        "total_results": len(results),
        "avg_score": sum(scores) / len(scores) if scores else 0.0,
        "avg_confidence": sum(confidences) / len(confidences) if confidences else 0.0,
        "score_range": (min(scores), max(scores)) if scores else (0.0, 0.0),
        "categories": categories,
        "documents": documents,
    }


def format_result_for_display(result: dict[str, Any], max_text_length: int = 500) -> dict[str, Any]:
    """
    Format a search result for display/API response.

    Truncates text to max_text_length and ensures all fields are present.
    Passes through title and description fields from the search service.

    Args:
        result: Result dict from search.
        max_text_length: Maximum length of text field.

    Returns:
        Formatted result dict.
    """
    text = result.get("text", "")
    if len(text) > max_text_length:
        text = text[:max_text_length] + "..."

    return {
        "chunk_id": result.get("chunk_id", ""),
        "text": text,
        "title": result.get("title", ""),
        "description": result.get("description", ""),
        "req_id": result.get("req_id", ""),
        "type_label": result.get("type_label", ""),
        "category": result.get("category", ""),
        "section": result.get("section", ""),
        "subsection": result.get("subsection", ""),
        "page_number": result.get("page_number", 0),
        "score": round(result.get("score", 0.0), 4),
        "confidence_score": round(result.get("confidence_score", 0.0), 4),
        "document_id": result.get("document_id", ""),
        "chunk_type": result.get("chunk_type", ""),
    }
