"""
HeadingDetector — scans parsed_content pages and returns a list of DetectedHeading
objects representing the document's structural headings.

Detection priority (highest to lowest):
  1. 3-segment numbered  e.g. "1.1.1 Approval Workflow"  → level 3
  2. 2-segment numbered  e.g. "1.1 Vendor Mgmt"          → level 2
  3. 1-segment numbered  e.g. "1. Scope", "2) Overview"  → level 1
  4. ALL-CAPS line, 10–80 chars, ≥ 2 words               → level 1
  5. Title-Case line, 10–80 chars, ≥ 2 words             → level 1

Strict guards prevent ordinary body text from matching:
  - Single words (e.g. "Contract", "Database") are NOT headings
  - Lines ending with punctuation are NOT headings
  - List items, labels, and table markers are skipped

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

# List marker prefixes to skip
_LIST_PREFIXES = ("- ", "• ", "* ", "– ", "— ")


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
    Title-Case) under strict rules that prevent ordinary body text from matching.

    A line qualifies ONLY when ALL of the following hold:
      1. Length between 10 and 80 characters (stripped).
      2. Contains at least 2 words.
      3. Contains at least one alphabetic character.
      4. Does NOT end with terminal punctuation (. ? !).
      5. Does NOT start with a list marker (- • * – —).
      6. Does NOT end with a colon (label pattern like "Note:").
      7. Is ALL CAPS with ≥ 2 words and ≥ 8 characters, OR
         is Title Case with ≥ 2 words.
    """
    stripped = line.strip()

    # 1. Length gate — eliminates very short words and very long sentences
    if len(stripped) < 10 or len(stripped) > 80:
        return False

    # 2. Word count gate — eliminates single-word matches like "Contract"
    words = stripped.split()
    if len(words) < 2:
        return False

    # 3. Must contain at least one alphabetic character
    if not any(c.isalpha() for c in stripped):
        return False

    # 4. No terminal punctuation — sentences are not headings
    if _TERMINAL_PUNCT.search(stripped):
        return False

    # 5. No list markers at the start
    if stripped[0] in ("-", "•", "*", "–", "—"):
        return False

    # 6. No label pattern (ends with colon)
    if stripped.endswith(":"):
        return False

    # 7a. ALL CAPS: need ≥ 2 words (already checked) AND ≥ 8 characters
    if stripped == stripped.upper():
        return len(stripped) >= 8

    # 7b. Title Case: need ≥ 2 words (already checked above)
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

            line_start = 0
            for line in page_text.splitlines(keepends=True):
                stripped = line.rstrip("\n\r")
                candidate = stripped.strip()

                if candidate:
                    # Skip common list-item prefixes
                    if any(candidate.startswith(pfx) for pfx in _LIST_PREFIXES):
                        line_start += len(line)
                        continue

                    # Skip purely numeric lines (e.g. "123", "1,234")
                    if re.fullmatch(r"[\d,]+", candidate):
                        line_start += len(line)
                        continue

                    # Skip table markers inserted by the parsers
                    if "[TABLE]" in candidate:
                        line_start += len(line)
                        continue

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
