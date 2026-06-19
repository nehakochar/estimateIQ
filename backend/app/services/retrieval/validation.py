"""
validation.py — Validation utilities for retrieval operations.

Provides:
  - Input validation (queries, filters, parameters)
  - Category validation
  - UUID validation
  - Threshold validation
"""

import logging
import uuid as uuid_module
from typing import Any

logger = logging.getLogger(__name__)

# Valid categories for requirement classification
VALID_CATEGORIES = {
    "functional",
    "non_functional",
    "ui_ux",
    "integrations",
    "security_compliance",
    "data_validation",
    "workflow_roles",
    "infrastructure_deployment",
    "risks_assumptions_dependencies",
    "open_questions",
    "out_of_scope",
}

# Valid chunk types
VALID_CHUNK_TYPES = {"requirement", "workflow"}


def validate_project_id(project_id: str) -> bool:
    """
    Validate that project_id is a non-empty UUID string.

    Args:
        project_id: Project ID to validate.

    Returns:
        True if valid, False otherwise.
    """
    if not project_id or not isinstance(project_id, str):
        return False
    try:
        uuid_module.UUID(project_id)
        return True
    except (ValueError, AttributeError):
        return False


def validate_query(query: str, min_length: int = 1, max_length: int = 1000) -> bool:
    """
    Validate that query is a non-empty string within length bounds.

    Args:
        query: Query text to validate.
        min_length: Minimum query length.
        max_length: Maximum query length.

    Returns:
        True if valid, False otherwise.
    """
    if not query or not isinstance(query, str):
        return False
    query_len = len(query.strip())
    return min_length <= query_len <= max_length


def validate_category(category: str) -> bool:
    """
    Validate that category is one of the 11 valid categories.

    Args:
        category: Category to validate.

    Returns:
        True if valid, False otherwise.
    """
    return category in VALID_CATEGORIES


def validate_chunk_type(chunk_type: str) -> bool:
    """
    Validate that chunk_type is one of the valid types.

    Args:
        chunk_type: Chunk type to validate.

    Returns:
        True if valid, False otherwise.
    """
    return chunk_type in VALID_CHUNK_TYPES


def validate_top_k(top_k: int, min_k: int = 1, max_k: int = 100) -> bool:
    """
    Validate that top_k is within acceptable bounds.

    Args:
        top_k: Number of results to return.
        min_k: Minimum allowed value.
        max_k: Maximum allowed value.

    Returns:
        True if valid, False otherwise.
    """
    return isinstance(top_k, int) and min_k <= top_k <= max_k


def validate_similarity_threshold(threshold: float) -> bool:
    """
    Validate that similarity_threshold is between 0.0 and 1.0.

    Args:
        threshold: Similarity threshold to validate.

    Returns:
        True if valid, False otherwise.
    """
    return isinstance(threshold, (int, float)) and 0.0 <= threshold <= 1.0


def validate_uuid(value: str) -> bool:
    """
    Validate that value is a valid UUID string.

    Args:
        value: UUID string to validate.

    Returns:
        True if valid, False otherwise.
    """
    if not value or not isinstance(value, str):
        return False
    try:
        uuid_module.UUID(value)
        return True
    except (ValueError, AttributeError):
        return False


def validate_search_request(
    project_id: str,
    query: str,
    top_k: int = 10,
    category: str | None = None,
    similarity_threshold: float = 0.65,
) -> tuple[bool, str]:
    """
    Validate all parameters for a search request.

    Args:
        project_id: Project UUID.
        query: Search query.
        top_k: Number of results.
        category: Optional category filter.
        similarity_threshold: Minimum similarity score.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if not validate_project_id(project_id):
        return False, "Invalid project_id format"

    if not validate_query(query):
        return False, "Query must be 1-1000 characters"

    if not validate_top_k(top_k):
        return False, "top_k must be between 1 and 100"

    if category and not validate_category(category):
        return False, f"Invalid category. Valid categories: {sorted(VALID_CATEGORIES)}"

    if not validate_similarity_threshold(similarity_threshold):
        return False, "similarity_threshold must be between 0.0 and 1.0"

    return True, ""


def validate_category_search_request(
    project_id: str,
    category: str,
    top_k: int = 10,
    similarity_threshold: float = 0.65,
) -> tuple[bool, str]:
    """
    Validate all parameters for a category search request.

    Args:
        project_id: Project UUID.
        category: Category to search.
        top_k: Number of results.
        similarity_threshold: Minimum confidence score.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if not validate_project_id(project_id):
        return False, "Invalid project_id format"

    if not validate_category(category):
        return False, f"Invalid category. Valid categories: {sorted(VALID_CATEGORIES)}"

    if not validate_top_k(top_k):
        return False, "top_k must be between 1 and 100"

    if not validate_similarity_threshold(similarity_threshold):
        return False, "similarity_threshold must be between 0.0 and 1.0"

    return True, ""


def validate_similar_chunks_request(
    project_id: str,
    chunk_id: str,
    top_k: int = 10,
    similarity_threshold: float = 0.65,
) -> tuple[bool, str]:
    """
    Validate all parameters for a similar chunks request.

    Args:
        project_id: Project UUID.
        chunk_id: Reference chunk UUID.
        top_k: Number of results.
        similarity_threshold: Minimum similarity score.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if not validate_project_id(project_id):
        return False, "Invalid project_id format"

    if not validate_uuid(chunk_id):
        return False, "Invalid chunk_id format"

    if not validate_top_k(top_k):
        return False, "top_k must be between 1 and 100"

    if not validate_similarity_threshold(similarity_threshold):
        return False, "similarity_threshold must be between 0.0 and 1.0"

    return True, ""
