"""
test_retrieval.py — Tests for the retrieval layer (Phase 9).

Tests cover:
  - Semantic search with various filters
  - Category-based search
  - Similar chunk search
  - Project statistics
  - Input validation
  - Error handling
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from app.services.retrieval.semantic_search import SemanticSearchService
from app.services.retrieval.retrieval_service import RetrievalService
from app.services.retrieval.validation import (
    validate_project_id,
    validate_query,
    validate_category,
    validate_top_k,
    validate_similarity_threshold,
    VALID_CATEGORIES,
)
from app.services.search.search_utils import (
    normalize_query,
    rank_results,
    filter_by_threshold,
    deduplicate_results,
    calculate_search_metrics,
)


# ─────────────────────────────────────────────────────────────────────────
# VALIDATION TESTS
# ─────────────────────────────────────────────────────────────────────────


class TestValidation:
    """Test input validation utilities."""

    def test_validate_project_id_valid(self):
        """Valid UUID should pass."""
        assert validate_project_id("550e8400-e29b-41d4-a716-446655440000")

    def test_validate_project_id_invalid(self):
        """Invalid UUID should fail."""
        assert not validate_project_id("not-a-uuid")
        assert not validate_project_id("")
        assert not validate_project_id(None)

    def test_validate_query_valid(self):
        """Valid query should pass."""
        assert validate_query("authentication requirements")
        assert validate_query("a")  # min length 1

    def test_validate_query_invalid(self):
        """Invalid query should fail."""
        assert not validate_query("")
        assert not validate_query("x" * 1001)  # exceeds max length
        assert not validate_query(None)

    def test_validate_category_valid(self):
        """Valid category should pass."""
        assert validate_category("security_compliance")
        assert validate_category("functional")

    def test_validate_category_invalid(self):
        """Invalid category should fail."""
        assert not validate_category("invalid_category")
        assert not validate_category("")

    def test_validate_top_k_valid(self):
        """Valid top_k should pass."""
        assert validate_top_k(10)
        assert validate_top_k(1)
        assert validate_top_k(100)

    def test_validate_top_k_invalid(self):
        """Invalid top_k should fail."""
        assert not validate_top_k(0)
        assert not validate_top_k(101)
        assert not validate_top_k(-1)

    def test_validate_similarity_threshold_valid(self):
        """Valid threshold should pass."""
        assert validate_similarity_threshold(0.65)
        assert validate_similarity_threshold(0.0)
        assert validate_similarity_threshold(1.0)

    def test_validate_similarity_threshold_invalid(self):
        """Invalid threshold should fail."""
        assert not validate_similarity_threshold(-0.1)
        assert not validate_similarity_threshold(1.1)


# ─────────────────────────────────────────────────────────────────────────
# SEARCH UTILS TESTS
# ─────────────────────────────────────────────────────────────────────────


class TestSearchUtils:
    """Test search utility functions."""

    def test_normalize_query(self):
        """Query should be normalized."""
        assert normalize_query("  Authentication  Requirements  ") == "authentication requirements"
        assert normalize_query("UPPERCASE") == "uppercase"

    def test_rank_results(self):
        """Results should be ranked by score."""
        results = [
            {"chunk_id": "1", "score": 0.5},
            {"chunk_id": "2", "score": 0.9},
            {"chunk_id": "3", "score": 0.7},
        ]
        ranked = rank_results(results, sort_by="score", reverse=True)
        assert ranked[0]["score"] == 0.9
        assert ranked[1]["score"] == 0.7
        assert ranked[2]["score"] == 0.5

    def test_filter_by_threshold(self):
        """Results below threshold should be filtered."""
        results = [
            {"chunk_id": "1", "score": 0.5},
            {"chunk_id": "2", "score": 0.9},
            {"chunk_id": "3", "score": 0.7},
        ]
        filtered = filter_by_threshold(results, threshold=0.65, field="score")
        assert len(filtered) == 2
        assert all(r["score"] >= 0.65 for r in filtered)

    def test_deduplicate_results(self):
        """Duplicate chunk_ids should be removed."""
        results = [
            {"chunk_id": "1", "text": "text1"},
            {"chunk_id": "2", "text": "text2"},
            {"chunk_id": "1", "text": "text1_duplicate"},
        ]
        deduped = deduplicate_results(results, key="chunk_id")
        assert len(deduped) == 2
        assert deduped[0]["chunk_id"] == "1"
        assert deduped[1]["chunk_id"] == "2"

    def test_calculate_search_metrics(self):
        """Metrics should be calculated correctly."""
        results = [
            {"chunk_id": "1", "score": 0.9, "confidence_score": 1.0},
            {"chunk_id": "2", "score": 0.8, "confidence_score": 0.5},
            {"chunk_id": "3", "score": 0.7, "confidence_score": 0.3},
        ]
        metrics = calculate_search_metrics(results)
        assert metrics["total_results"] == 3
        assert metrics["avg_score"] == pytest.approx(0.8, abs=0.01)
        assert metrics["score_range"] == (0.7, 0.9)

    def test_calculate_search_metrics_empty(self):
        """Empty results should return zero metrics."""
        metrics = calculate_search_metrics([])
        assert metrics["total_results"] == 0
        assert metrics["avg_score"] == 0.0


# ─────────────────────────────────────────────────────────────────────────
# SEMANTIC SEARCH SERVICE TESTS
# ─────────────────────────────────────────────────────────────────────────


class TestSemanticSearchService:
    """Test SemanticSearchService."""

    @patch("app.services.retrieval.semantic_search.EmbeddingService")
    @patch("app.services.retrieval.semantic_search.QdrantService")
    def test_search_valid_query(self, mock_qdrant, mock_embedding):
        """Valid search should return results."""
        # Setup mocks
        mock_embedding_instance = Mock()
        mock_embedding.return_value = mock_embedding_instance
        mock_embedding_instance.embed.return_value = [[0.1] * 384]

        mock_qdrant_instance = Mock()
        mock_qdrant.return_value = mock_qdrant_instance
        mock_qdrant_instance.search.return_value = [
            Mock(
                score=0.9,
                payload={
                    "chunk_id": "chunk_1",
                    "text": "Authentication requirement",
                    "category": "security_compliance",
                    "section": "Security",
                    "subsection": "Auth",
                    "page_number": 10,
                    "confidence_score": 1.0,
                    "document_id": "doc_1",
                    "chunk_type": "requirement",
                },
            )
        ]

        service = SemanticSearchService()
        results = service.search(
            project_id="project_123",
            query="authentication",
            top_k=10,
        )

        assert len(results) == 1
        assert results[0]["chunk_id"] == "chunk_1"
        assert results[0]["score"] == 0.9

    @patch("app.services.retrieval.semantic_search.EmbeddingService")
    def test_search_empty_project_id(self, mock_embedding):
        """Empty project_id should raise ValueError."""
        service = SemanticSearchService()
        with pytest.raises(ValueError, match="project_id is required"):
            service.search(project_id="", query="test")

    @patch("app.services.retrieval.semantic_search.EmbeddingService")
    def test_search_empty_query(self, mock_embedding):
        """Empty query should raise ValueError."""
        service = SemanticSearchService()
        with pytest.raises(ValueError, match="query is required"):
            service.search(project_id="project_123", query="")

    @patch("app.services.retrieval.semantic_search.EmbeddingService")
    @patch("app.services.retrieval.semantic_search.QdrantService")
    def test_search_with_category_filter(self, mock_qdrant, mock_embedding):
        """Search with category filter should apply filter."""
        mock_embedding_instance = Mock()
        mock_embedding.return_value = mock_embedding_instance
        mock_embedding_instance.embed.return_value = [[0.1] * 384]

        mock_qdrant_instance = Mock()
        mock_qdrant.return_value = mock_qdrant_instance
        mock_qdrant_instance.search.return_value = []

        service = SemanticSearchService()
        service.search(
            project_id="project_123",
            query="test",
            category="security_compliance",
        )

        # Verify search was called with filter
        mock_qdrant_instance.search.assert_called_once()
        call_args = mock_qdrant_instance.search.call_args
        assert call_args[1]["query_filter"] is not None


# ─────────────────────────────────────────────────────────────────────────
# RETRIEVAL SERVICE TESTS
# ─────────────────────────────────────────────────────────────────────────


class TestRetrievalService:
    """Test RetrievalService."""

    @patch("app.services.retrieval.retrieval_service.SemanticSearchService")
    def test_search_validates_project(self, mock_search_service):
        """Search should validate project exists."""
        mock_db = Mock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = RetrievalService(mock_db)
        with pytest.raises(ValueError, match="Project .* not found"):
            service.search(
                project_id="nonexistent_project",
                query="test",
            )

    @patch("app.services.retrieval.retrieval_service.SemanticSearchService")
    def test_search_with_valid_project(self, mock_search_service):
        """Search should succeed with valid project."""
        # Setup mocks
        mock_db = Mock(spec=Session)
        mock_project = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        mock_search_instance = Mock()
        mock_search_service.return_value = mock_search_instance
        mock_search_instance.search.return_value = [
            {
                "chunk_id": "chunk_1",
                "text": "test",
                "score": 0.9,
            }
        ]

        service = RetrievalService(mock_db)
        results = service.search(
            project_id="project_123",
            query="test",
        )

        assert len(results) == 1
        assert results[0]["chunk_id"] == "chunk_1"

    @patch("app.services.retrieval.retrieval_service.SemanticSearchService")
    def test_search_by_category_validates_project(self, mock_search_service):
        """Category search should validate project exists."""
        mock_db = Mock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = RetrievalService(mock_db)
        with pytest.raises(ValueError, match="Project .* not found"):
            service.search_by_category(
                project_id="nonexistent_project",
                category="security_compliance",
            )


# ─────────────────────────────────────────────────────────────────────────
# INTEGRATION TESTS
# ─────────────────────────────────────────────────────────────────────────


class TestRetrievalIntegration:
    """Integration tests for retrieval layer."""

    def test_valid_categories_defined(self):
        """All 11 valid categories should be defined."""
        expected_categories = {
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
        assert VALID_CATEGORIES == expected_categories

    def test_search_result_format(self):
        """Search results should have required fields."""
        result = {
            "chunk_id": "chunk_1",
            "text": "test",
            "category": "functional",
            "section": "Section",
            "subsection": "Subsection",
            "page_number": 1,
            "score": 0.9,
            "confidence_score": 1.0,
            "document_id": "doc_1",
            "chunk_type": "requirement",
        }

        required_fields = {
            "chunk_id",
            "text",
            "category",
            "section",
            "subsection",
            "page_number",
            "score",
            "confidence_score",
            "document_id",
            "chunk_type",
        }

        assert all(field in result for field in required_fields)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
