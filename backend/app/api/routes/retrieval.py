"""
retrieval.py — API routes for semantic search and retrieval operations.

Endpoints:
  POST /search — semantic search with optional metadata filtering
  POST /search/category — retrieve chunks by category
  POST /search/similar — find chunks similar to a reference chunk
  GET /projects/{project_id}/statistics — project retrieval statistics

All endpoints are project-scoped — every query filters by project_id.
Frontend should NEVER query Qdrant directly; all retrieval goes through these APIs.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.retrieval import (
    CategorySearchRequest,
    CategorySearchResponse,
    ProjectStatistics,
    SemanticSearchRequest,
    SemanticSearchResponse,
    SimilarChunksRequest,
    SimilarChunksResponse,
)
from app.services.retrieval.retrieval_service import RetrievalService
from app.services.search.search_utils import format_result_for_display

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["Retrieval"])

# Valid categories for validation
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


@router.post(
    "",
    response_model=SemanticSearchResponse,
    summary="Semantic search with metadata filtering",
    description=(
        "Perform semantic similarity search across RFP chunks with optional "
        "metadata filtering by category, section, document, or chunk type. "
        "All results are project-scoped."
    ),
)
def semantic_search(
    project_id: str,
    request: SemanticSearchRequest,
    db: Session = Depends(get_db),
) -> SemanticSearchResponse:
    """
    Execute semantic search with optional metadata filters.

    Args:
        project_id: UUID string of the project (query parameter).
        request: SemanticSearchRequest with query and optional filters.
        db: Database session (injected by FastAPI).

    Returns:
        SemanticSearchResponse with matching chunks and metadata.

    Raises:
        HTTPException 400: If project not found or inputs invalid.
        HTTPException 500: If search fails.
    """
    if not project_id or not project_id.strip():
        raise HTTPException(status_code=400, detail="project_id is required")

    # Validate category if provided
    if request.category and request.category not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category '{request.category}'. Valid categories: {sorted(VALID_CATEGORIES)}",
        )

    logger.info(
        "semantic_search: project=%s query_len=%d top_k=%d",
        project_id,
        len(request.query),
        request.top_k,
    )

    try:
        service = RetrievalService(db)
        results = service.search(
            project_id=project_id,
            query=request.query,
            top_k=request.top_k,
            category=request.category,
            section=request.section,
            document_id=request.document_id,
            chunk_type=request.chunk_type,
            similarity_threshold=request.similarity_threshold,
        )

        # Deduplicate and format results for display
        from app.services.search.search_utils import deduplicate_results
        deduplicated_results = deduplicate_results(results, key="chunk_id")
        formatted_results = [format_result_for_display(r) for r in deduplicated_results]

        return SemanticSearchResponse(
            project_id=project_id,
            query=request.query,
            total_results=len(formatted_results),
            results=formatted_results,
        )

    except ValueError as e:
        logger.warning("semantic_search: validation error: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("semantic_search: unexpected error: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail="Search failed. Please try again.",
        )


@router.post(
    "/category",
    response_model=CategorySearchResponse,
    summary="Retrieve chunks by category",
    description=(
        "Retrieve all chunks in a specific category, ordered by classification "
        "confidence. Useful for browsing requirements by type or getting category "
        "statistics."
    ),
)
def search_by_category(
    project_id: str,
    request: CategorySearchRequest,
    db: Session = Depends(get_db),
) -> CategorySearchResponse:
    """
    Retrieve chunks by category.

    Args:
        project_id: UUID string of the project (query parameter).
        request: CategorySearchRequest with category and optional filters.
        db: Database session (injected by FastAPI).

    Returns:
        CategorySearchResponse with chunks in the category.

    Raises:
        HTTPException 400: If project not found or category invalid.
        HTTPException 500: If search fails.
    """
    if not project_id or not project_id.strip():
        raise HTTPException(status_code=400, detail="project_id is required")

    if request.category not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category '{request.category}'. Valid categories: {sorted(VALID_CATEGORIES)}",
        )

    logger.info(
        "search_by_category: project=%s category=%s top_k=%d",
        project_id,
        request.category,
        request.top_k,
    )

    try:
        service = RetrievalService(db)
        results = service.search_by_category(
            project_id=project_id,
            category=request.category,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold,
        )

        # Deduplicate and format results for display
        from app.services.search.search_utils import deduplicate_results
        deduplicated_results = deduplicate_results(results, key="chunk_id")
        formatted_results = [format_result_for_display(r) for r in deduplicated_results]

        return CategorySearchResponse(
            project_id=project_id,
            category=request.category,
            total_results=len(formatted_results),
            results=formatted_results,
        )

    except ValueError as e:
        logger.warning("search_by_category: validation error: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("search_by_category: unexpected error: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail="Search failed. Please try again.",
        )


@router.post(
    "/similar",
    response_model=SimilarChunksResponse,
    summary="Find chunks similar to a reference chunk",
    description=(
        "Find chunks semantically similar to a given chunk. Useful for discovering "
        "related requirements, duplicate chunks, or exploring requirement relationships."
    ),
)
def find_similar_chunks(
    project_id: str,
    request: SimilarChunksRequest,
    db: Session = Depends(get_db),
) -> SimilarChunksResponse:
    """
    Find chunks similar to a reference chunk.

    Args:
        project_id: UUID string of the project (query parameter).
        request: SimilarChunksRequest with reference chunk_id.
        db: Database session (injected by FastAPI).

    Returns:
        SimilarChunksResponse with similar chunks.

    Raises:
        HTTPException 400: If project or chunk not found.
        HTTPException 500: If search fails.
    """
    if not project_id or not project_id.strip():
        raise HTTPException(status_code=400, detail="project_id is required")

    logger.info(
        "find_similar_chunks: project=%s chunk=%s top_k=%d",
        project_id,
        request.chunk_id,
        request.top_k,
    )

    try:
        service = RetrievalService(db)
        results = service.find_similar_chunks(
            project_id=project_id,
            chunk_id=request.chunk_id,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold,
        )

        # Deduplicate and format results for display
        from app.services.search.search_utils import deduplicate_results
        deduplicated_results = deduplicate_results(results, key="chunk_id")
        formatted_results = [format_result_for_display(r) for r in deduplicated_results]

        return SimilarChunksResponse(
            project_id=project_id,
            reference_chunk_id=request.chunk_id,
            total_results=len(formatted_results),
            results=formatted_results,
        )

    except ValueError as e:
        logger.warning("find_similar_chunks: validation error: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("find_similar_chunks: unexpected error: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail="Search failed. Please try again.",
        )


@router.get(
    "/projects/{project_id}/statistics",
    response_model=ProjectStatistics,
    summary="Get project retrieval statistics",
    description=(
        "Get statistics about chunks in a project, including counts by category, "
        "document, and chunk type."
    ),
)
def get_project_statistics(
    project_id: str,
    db: Session = Depends(get_db),
) -> ProjectStatistics:
    """
    Get retrieval statistics for a project.

    Args:
        project_id: UUID string of the project.
        db: Database session (injected by FastAPI).

    Returns:
        ProjectStatistics with chunk counts by category, document, and type.

    Raises:
        HTTPException 400: If project not found.
        HTTPException 500: If query fails.
    """
    if not project_id or not project_id.strip():
        raise HTTPException(status_code=400, detail="project_id is required")

    logger.info("get_project_statistics: project=%s", project_id)

    try:
        service = RetrievalService(db)
        stats = service.get_project_statistics(project_id)

        return ProjectStatistics(
            project_id=project_id,
            total_chunks=stats["total_chunks"],
            chunks_by_category=stats["chunks_by_category"],
            chunks_by_document=stats["chunks_by_document"],
            chunks_by_type=stats["chunks_by_type"],
        )

    except ValueError as e:
        logger.warning("get_project_statistics: validation error: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("get_project_statistics: unexpected error: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve statistics. Please try again.",
        )
