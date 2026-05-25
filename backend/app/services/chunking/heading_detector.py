"""
HeadingDetector — scans parsed_content pages and returns a list of DetectedHeading
objects representing the document's structural headings.

Detection priority (highest to lowest):
  1. 3-segment numbered  e.g. "1.1.1 Approval Workflow"  → level 3
  2. 2-segment numbered  e.g. "1.1 Vendor Mgmt"          → level 2
  3. 1-segment numbered  e.g. "1. Scope", "2) Overview"  → level 1
  4. ALL-CAPS line ≤ 80 chars, no terminal punctuation   → level 1
  5. Title-Case line ≤ 80 chars, no terminal punctuation → level 1

If no headings are detected, a synthetic level-1 heading is created from file_name.
"""

import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Compiled patterns — ordered from most-specific to least-specific so that
# the first match wins when we iterate through them.
# ---------------------------------------------------------------------------

# Level 3: three dot-separated numeric segments, e.g. "1.1.1 ..." or "1.2.3 Title"
_PATTERN_L3 = re.compile(r"^\d+\.\d+\.\d+")

# Level 2: two numeric segments with optional trailing dot/paren, e.g. "1.1 ...", "2.3. ...", "1.2) ..."
_PATTERN_L2 = re.compile(r"^\d+\.\d+[\.\)]?\s+\S")

# Level 1: single numeric segment with dot or paren, e.g. "1. ...", "2) ..."
_PATTERN_L1 = re.compile(r"^\d+[\.\)]\s+\S")

# Terminal punctuation characters that disqualify title-style headings
_TERMINAL_PUNCT = re.compile(r"[.?!]$")


@dataclass
class DetectedHeading:
    """A heading found (or synthesised) within a document."""

    text: str         # heading line, stripped
    level: int        # 1, 2, or 3
    page_number: int  # 1-based page where the heading was found
    char_offset: int  # character offset in the full concatenated document text


def _numbered_level(line: str) -> int | None:
    """Return the numbered-heading level (1–3) for *line*, or None if it is not
    a numbered heading.  Patterns are tested most-specific first."""
    if _PATTERN_L3.match(line):
        return 3
    if _PATTERN_L2.match(line):
        return 2
    if _PATTERN_L1.match(line):
        return 1
    return None


def _is_title_heading(line: str) -> bool:
    """Return True if *line* qualifies as a title-style heading (ALL-CAPS or
    Title-Case, ≤ 80 chars, no terminal punctuation)."""
    stripped = line.strip()
    if not stripped:
        return False
    if len(stripped) > 80:
        return False
    if _TERMINAL_PUNCT.search(stripped):
        return False
    # Must contain at least one alphabetic character to avoid matching
    # pure numeric or symbol lines.
    if not any(c.isalpha() for c in stripped):
        return False
    if stripped == stripped.upper():
        return True
    if stripped == stripped.title():
        return True
    return False


class HeadingDetector:
    """Detects structural headings in a list of parsed document pages."""

    def detect(
        self,
        pages: list[dict],
        file_name: str,
    ) -> list[DetectedHeading]:
        """Scan *pages* and return a list of :class:`DetectedHeading` objects.

        Parameters
        ----------
        pages:
            List of dicts in the ``parsed_content`` format:
            ``[{"page": N, "text": "..."}, ...]``
        file_name:
            Original file name used as the synthetic heading when no headings
            are detected.

        Returns
        -------
        list[DetectedHeading]
            Headings in document order.  Never empty — a synthetic heading is
            returned when the document contains no detectable headings.
        """
        headings: list[DetectedHeading] = []
        char_offset = 0  # running offset into the full concatenated text

        for page_dict in pages:
            page_number: int = page_dict.get("page", 1)
            page_text: str = page_dict.get("text", "")

            # Walk line-by-line, tracking the offset of each line within the
            # full document text (not just within the page).
            line_start = 0
            for line in page_text.splitlines(keepends=True):
                stripped = line.rstrip("\n\r")
                candidate = stripped.strip()

                if candidate:
                    level = _numbered_level(candidate)
                    if level is None and _is_title_heading(candidate):
                        level = 1

                    if level is not None:
                        headings.append(
                            DetectedHeading(
                                text=candidate,
                                level=level,
                                page_number=page_number,
                                char_offset=char_offset + line_start,
                            )
                        )

                line_start += len(line)

            # Advance the global offset by the full page text length.
            # Pages are concatenated without any separator, matching the
            # behaviour expected by HierarchyBuilder.
            char_offset += len(page_text)

        # Fallback: synthesise a root heading from the file name.
        if not headings:
            logger.info(
                "HeadingDetector: no headings found in document; "
                "creating synthetic heading from file_name=%r",
                file_name,
            )
            headings.append(
                DetectedHeading(
                    text=file_name,
                    level=1,
                    page_number=1,
                    char_offset=0,
                )
            )

        # Log summary.
        level_counts: dict[int, int] = {}
        for h in headings:
            level_counts[h.level] = level_counts.get(h.level, 0) + 1

        logger.info(
            "HeadingDetector: detected %d heading(s) — %s",
            len(headings),
            ", ".join(f"L{lvl}={cnt}" for lvl, cnt in sorted(level_counts.items())),
        )

        return headings
