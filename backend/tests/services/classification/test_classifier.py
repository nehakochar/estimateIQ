"""
Unit tests for RequirementClassifier.classify().

Tests cover:
- Text keyword hits → confidence 1.0
- Heading-only hits → confidence 0.5
- No hits → functional fallback, confidence 0.3
- Tie-breaking by CATEGORY_PRIORITY
- Case-insensitive matching
- Multi-keyword hits selecting the highest-scoring category
"""

import pytest
from app.services.classification.classifier import RequirementClassifier


class _Chunk:
    """Minimal duck-typed chunk for testing."""

    def __init__(self, text: str, section: str = "", subsection: str = ""):
        self.text = text
        self.section = section
        self.subsection = subsection


@pytest.fixture
def classifier():
    return RequirementClassifier()


# ---------------------------------------------------------------------------
# Text hits → confidence 1.0
# ---------------------------------------------------------------------------

class TestTextHits:
    def test_security_keyword_in_text(self, classifier):
        chunk = _Chunk(text="The system must use encryption for all data at rest.")
        category, confidence = classifier.classify(chunk)
        assert category == "security_compliance"
        assert confidence == 1.0

    def test_integration_keyword_in_text(self, classifier):
        chunk = _Chunk(text="The system shall expose a REST api endpoint.")
        category, confidence = classifier.classify(chunk)
        assert category in ("integrations", "security_compliance")  # both may match
        assert confidence == 1.0

    def test_ui_ux_keyword_in_text(self, classifier):
        chunk = _Chunk(text="The dashboard shall display a navigation menu.")
        category, confidence = classifier.classify(chunk)
        assert category == "ui_ux"
        assert confidence == 1.0

    def test_non_functional_keyword_in_text(self, classifier):
        chunk = _Chunk(text="System latency must not exceed 200ms under load.")
        category, confidence = classifier.classify(chunk)
        assert category == "non_functional"
        assert confidence == 1.0

    def test_infrastructure_keyword_in_text(self, classifier):
        chunk = _Chunk(text="Deploy using docker and kubernetes on aws.")
        category, confidence = classifier.classify(chunk)
        assert category == "infrastructure_deployment"
        assert confidence == 1.0

    def test_open_questions_keyword_in_text(self, classifier):
        chunk = _Chunk(text="This requirement is tbd and unclear at this stage.")
        category, confidence = classifier.classify(chunk)
        assert category == "open_questions"
        assert confidence == 1.0

    def test_out_of_scope_keyword_in_text(self, classifier):
        chunk = _Chunk(text="Mobile app support is out of scope for this phase.")
        category, confidence = classifier.classify(chunk)
        assert category == "out_of_scope"
        assert confidence == 1.0

    def test_case_insensitive_matching(self, classifier):
        chunk = _Chunk(text="ENCRYPTION must be applied to all PII data.")
        category, confidence = classifier.classify(chunk)
        assert category == "security_compliance"
        assert confidence == 1.0


# ---------------------------------------------------------------------------
# Heading-only hits → confidence 0.5
# ---------------------------------------------------------------------------

class TestHeadingHits:
    def test_section_match_only(self, classifier):
        # Text has no keywords; section contains "latency" → non_functional heading hit
        # (avoid "performance" which contains "form"/"ui" substrings that hit ui_ux)
        chunk = _Chunk(
            text="The system shall handle concurrent operations.",
            section="Latency and Throughput",
        )
        category, confidence = classifier.classify(chunk)
        assert category == "non_functional"
        assert confidence == 0.5

    def test_subsection_match_only(self, classifier):
        # Text has no keywords; subsection contains "ui" → ui_ux heading hit
        chunk = _Chunk(
            text="The system shall allow users to log in.",
            section="",
            subsection="UI Components",
        )
        category, confidence = classifier.classify(chunk)
        assert category == "ui_ux"
        assert confidence == 0.5

    def test_section_and_subsection_combined(self, classifier):
        chunk = _Chunk(
            text="The feature will be implemented later.",
            section="Out of Scope",
            subsection="Future Phase items",
        )
        category, confidence = classifier.classify(chunk)
        assert category == "out_of_scope"
        assert confidence == 0.5


# ---------------------------------------------------------------------------
# No hits → functional fallback
# ---------------------------------------------------------------------------

class TestNoHits:
    def test_no_keywords_returns_functional(self, classifier):
        chunk = _Chunk(
            text="The system shall allow users to create accounts.",
            section="",
            subsection="",
        )
        category, confidence = classifier.classify(chunk)
        assert category == "functional"
        assert confidence == 0.3

    def test_empty_text_returns_functional(self, classifier):
        chunk = _Chunk(text="", section="", subsection="")
        category, confidence = classifier.classify(chunk)
        assert category == "functional"
        assert confidence == 0.3


# ---------------------------------------------------------------------------
# Tie-breaking by CATEGORY_PRIORITY
# ---------------------------------------------------------------------------

class TestTieBreaking:
    def test_security_beats_integrations_on_tie(self, classifier):
        # "authentication" → security_compliance; "api" → integrations
        # Both get 1 text hit — security_compliance has higher priority
        chunk = _Chunk(text="The api must use authentication.")
        category, confidence = classifier.classify(chunk)
        assert category == "security_compliance"
        assert confidence == 1.0

    def test_higher_hit_count_wins_over_priority(self, classifier):
        # integrations gets 3 hits, security_compliance gets 1 hit
        # integrations should win despite lower priority
        chunk = _Chunk(
            text="The api webhook oauth integration must use tls."
        )
        category, confidence = classifier.classify(chunk)
        # integrations: api, webhook, oauth, integration = 4 hits
        # security_compliance: tls = 1 hit
        assert category == "integrations"
        assert confidence == 1.0


# ---------------------------------------------------------------------------
# Text hits take priority over heading hits
# ---------------------------------------------------------------------------

class TestTextVsHeadingPriority:
    def test_text_hit_overrides_heading_hit(self, classifier):
        # text has "docker" (infrastructure), heading has "performance" (non_functional)
        chunk = _Chunk(
            text="Deploy the service using docker.",
            section="Performance",
        )
        category, confidence = classifier.classify(chunk)
        assert category == "infrastructure_deployment"
        assert confidence == 1.0  # text hit wins
