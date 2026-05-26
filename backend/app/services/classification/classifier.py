"""
RequirementClassifier — rule-based requirement category classifier.

Classifies a semantic chunk into one of eleven business categories using
keyword matching against the chunk's text, section, and subsection fields.

Confidence scoring:
  1.0 — keyword hit found in chunk text
  0.5 — keyword hit found only in section/subsection headings
  0.3 — no keyword match (default: "functional")
"""

from app.services.classification.rules import CATEGORY_PRIORITY, CATEGORY_RULES


class RequirementClassifier:
    """Stateless rule-based classifier for semantic chunks.

    Accepts any duck-typed object with ``text``, ``section``, and
    ``subsection`` string attributes and returns a
    ``(category, confidence_score)`` tuple.
    """

    def classify(self, chunk) -> tuple[str, float]:
        """Classify *chunk* into a business category.

        Parameters
        ----------
        chunk:
            Any object exposing ``text``, ``section``, and ``subsection``
            string attributes (e.g. a ``SemanticChunk`` ORM instance or a
            plain namespace/dataclass).

        Returns
        -------
        tuple[str, float]
            ``(category, confidence_score)`` where *category* is one of the
            eleven values defined in ``CATEGORY_RULES`` and *confidence_score*
            is ``1.0``, ``0.5``, or ``0.3``.
        """
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
            confidence_score = 0.3

        return winner, confidence_score

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _pick_winner(hits: dict[str, int]) -> str:
        """Return the category with the most hits, breaking ties by priority.

        ``CATEGORY_PRIORITY`` is ordered from highest to lowest priority
        (lower index = higher priority).  When two categories share the same
        hit count the one that appears earlier in ``CATEGORY_PRIORITY`` wins.
        """
        max_hits = max(hits.values())
        # Candidates with the maximum hit count, in priority order
        for category in CATEGORY_PRIORITY:
            if hits.get(category, 0) == max_hits:
                return category
        # Fallback — should never be reached if CATEGORY_PRIORITY is complete
        return "functional"
