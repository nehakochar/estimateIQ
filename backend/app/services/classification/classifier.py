"""
RequirementClassifier — rule-based requirement category classifier.

Classifies a semantic chunk into one of eleven business categories using
keyword matching against the chunk's text, section, and subsection fields.

Confidence scoring:
  1.0 — keyword hit found in chunk text
  0.5 — keyword hit found only in section/subsection headings
  0.5 — no keyword match (default: "functional") — raised from 0.3
  0.0 — chunk text is too short to classify (< 15 chars) → "other"
"""

from app.services.classification.rules import CATEGORY_PRIORITY, CATEGORY_RULES


class RequirementClassifier:
    """Stateless rule-based classifier for semantic chunks."""

    def classify(self, chunk) -> tuple[str, float]:
        """Classify *chunk* into a business category.

        Parameters
        ----------
        chunk:
            Any object exposing ``text``, ``section``, and ``subsection``
            string attributes.

        Returns
        -------
        tuple[str, float]
            ``(category, confidence_score)``
        """
        # Chunks under 15 characters have no meaningful signal — mark as "other"
        if len((chunk.text or "").strip()) < 15:
            return "other", 0.0

        # --- 1. Normalise inputs -------------------------------------------
        text = (chunk.text or "").lower()
        section = (chunk.section or "").lower()
        subsection = (chunk.subsection or "").lower()
        heading = f"{section} {subsection}"

        # --- 2. Score each category ----------------------------------------
        text_hits: dict[str, int] = {}
        heading_hits: dict[str, int] = {}

        for category, keywords in CATEGORY_RULES.items():
            t_count = sum(1 for kw in keywords if kw in text)
            h_count = sum(1 for kw in keywords if kw in heading)
            if t_count:
                text_hits[category] = t_count
            if h_count:
                heading_hits[category] = h_count

        # --- 3. Winner selection -------------------------------------------
        if text_hits:
            confidence_score = 1.0
            winner = self._pick_winner(text_hits)
        elif heading_hits:
            confidence_score = 0.5
            winner = self._pick_winner(heading_hits)
        else:
            winner = "functional"
            confidence_score = 0.5  # raised from 0.3 — functional is a safe default

        return winner, confidence_score

    @staticmethod
    def _pick_winner(hits: dict[str, int]) -> str:
        """Return the category with the most hits, breaking ties by priority."""
        max_hits = max(hits.values())
        for category in CATEGORY_PRIORITY:
            if hits.get(category, 0) == max_hits:
                return category
        return "functional"
