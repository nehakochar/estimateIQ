"""
pdf_parser.py — Extracts text and tables from PDF files using PyMuPDF.

PyMuPDF is imported as `fitz` (its internal module name).
For each page the parser:
  1. Detects tables via page.find_tables() and records their bounding boxes.
  2. Extracts and formats table content (header-aware).
  3. Extracts plain body text from non-table regions of the page.
  4. Combines body text + formatted table blocks into a single string.

Why PyMuPDF?
  - Very fast — written in C under the hood.
  - Handles complex PDFs (multi-column, embedded fonts, scanned text).
  - find_tables() is available from PyMuPDF 1.23+ (we require 1.25.5).

Beginner note on `fitz`:
  `import fitz` is how you use PyMuPDF.  The package is installed as
  `PyMuPDF` in requirements.txt but the Python module is called `fitz`.
  This is a historical naming quirk of the library.
"""

import logging
from pathlib import Path

import fitz  # PyMuPDF — installed as PyMuPDF, imported as fitz

from app.services.parsers.base import BaseParser, ParsedPage, ParserError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper: header detection
# ---------------------------------------------------------------------------

def _is_header_row(row: list) -> bool:
    """
    Return True if the row looks like a table header.

    A row is considered a header when ALL non-empty cells satisfy:
      - The cell contains 5 words or fewer.
      - The cell does NOT end with a sentence-terminating character
        (period, question mark, or exclamation mark).

    Args:
        row: A list of cell strings (may contain None for empty cells).

    Returns:
        True if the row looks like a header row, False otherwise.
    """
    non_empty = [str(cell).strip() for cell in row if cell and str(cell).strip()]

    if not non_empty:
        return False

    for cell in non_empty:
        word_count = len(cell.split())
        if word_count > 5:
            return False
        if cell.endswith((".", "?", "!")):
            return False

    return True


# ---------------------------------------------------------------------------
# Helper: format a single table into readable text
# ---------------------------------------------------------------------------

def _format_table(rows: list) -> str:
    """
    Convert a 2-D list of cell strings into a human-readable text block.

    Formatting rules:
      - Skip rows where every cell is empty or None.
      - If the first non-empty row looks like a header, use it as field
        labels and format subsequent rows as "Label1: Value1. Label2: Value2."
      - If no header is detected, join non-empty cells with " | ".

    Args:
        rows: Table data as returned by fitz TableFinder.extract().

    Returns:
        A multi-line string representing the table content.
    """
    if not rows:
        return ""

    non_empty_rows = [
        row for row in rows
        if any(cell and str(cell).strip() for cell in row)
    ]

    if not non_empty_rows:
        return ""

    formatted_lines: list[str] = []

    first_row = non_empty_rows[0]
    has_header = _is_header_row(first_row)

    if has_header:
        headers = [str(cell).strip() if (cell and str(cell).strip()) else "" for cell in first_row]
        data_rows = non_empty_rows[1:]

        for row in data_rows:
            if not any(cell and str(cell).strip() for cell in row):
                continue

            parts: list[str] = []
            for label, cell in zip(headers, row):
                value = str(cell).strip() if (cell and str(cell).strip()) else ""
                if label and value:
                    parts.append(f"{label}: {value}")
                elif value:
                    parts.append(value)

            if parts:
                formatted_lines.append(". ".join(parts) + ".")
    else:
        for row in non_empty_rows:
            cells = [str(cell).strip() for cell in row if cell and str(cell).strip()]
            if cells:
                formatted_lines.append(" | ".join(cells))

    return "\n".join(formatted_lines)


# ---------------------------------------------------------------------------
# Helper: extract body text excluding table bounding boxes
# ---------------------------------------------------------------------------

def _extract_body_text(page: fitz.Page, table_rects: list) -> str:
    """
    Extract plain text from a page, excluding regions covered by tables.

    Strategy:
      - Retrieve all text blocks from the page via get_text("blocks").
      - A block is a tuple: (x0, y0, x1, y1, text, block_no, block_type).
      - Skip any block whose bounding box intersects a known table rectangle.
      - Join the remaining blocks into a single string.

    Args:
        page       : The fitz.Page to extract text from.
        table_rects: List of fitz.Rect objects covering detected tables.

    Returns:
        Plain text string with table regions omitted.
    """
    body_parts: list[str] = []

    blocks = page.get_text("blocks")

    for block in blocks:
        x0, y0, x1, y1, text, _block_no, block_type = block

        # Skip image blocks
        if block_type != 0:
            continue

        block_rect = fitz.Rect(x0, y0, x1, y1)

        # Skip this block if it overlaps with any table region
        in_table = any(block_rect.intersects(tr) for tr in table_rects)
        if in_table:
            continue

        stripped = text.strip()
        if stripped:
            body_parts.append(stripped)

    return "\n".join(body_parts)


# ---------------------------------------------------------------------------
# Main parser class
# ---------------------------------------------------------------------------

class PdfParser(BaseParser):
    """
    Parses PDF files and returns one ParsedPage per PDF page.

    For each page:
      - Tables are detected and formatted as labelled key-value lines
        (or pipe-separated rows when no header is present).
      - Body text is extracted from non-table regions.
      - The two are combined: body text first, then a [TABLE] block.

    Empty pages are included with empty text so page numbers stay accurate.
    """

    def parse(self, file_path: Path) -> list[ParsedPage]:
        """
        Open the PDF and extract text (and tables) from every page.

        Args:
            file_path: Path to the .pdf file on disk.

        Returns:
            List of ParsedPage objects, one per PDF page.
            Page numbers are 1-based (first page = page 1).

        Raises:
            ParserError: if the file cannot be opened or read.
        """
        logger.info("PdfParser: starting parse of '%s'", file_path)

        try:
            doc = fitz.open(str(file_path))
        except Exception as exc:
            raise ParserError(
                f"PdfParser: failed to open '{file_path}': {exc}"
            ) from exc

        pages: list[ParsedPage] = []

        try:
            for page_index, page in enumerate(doc):
                page_number = page_index + 1

                # ── Step 1: Detect tables ─────────────────────────
                table_rects: list = []
                table_texts: list[str] = []

                try:
                    table_finder = page.find_tables()
                    tables = table_finder.tables
                except Exception as exc:
                    logger.warning(
                        "PdfParser: find_tables() failed on page %d of '%s': %s — "
                        "falling back to plain text",
                        page_number, file_path.name, exc,
                    )
                    tables = []

                # ── Step 2 & 3: Extract and format each table ─────
                for table in tables:
                    table_rects.append(table.bbox)

                    try:
                        rows = table.extract()
                    except Exception as exc:
                        logger.warning(
                            "PdfParser: table.extract() failed on page %d of '%s': %s",
                            page_number, file_path.name, exc,
                        )
                        continue

                    formatted = _format_table(rows)
                    if formatted:
                        table_texts.append(formatted)

                # ── Step 4: Extract body text (skip table regions) ─
                body_text = _extract_body_text(page, table_rects)

                # ── Step 5: Combine body text and table blocks ─────
                if table_texts:
                    table_section = "\n\n[TABLE]\n" + "\n\n[TABLE]\n".join(table_texts)
                    combined = (body_text + table_section).strip()
                else:
                    combined = body_text.strip()

                pages.append(
                    ParsedPage(
                        page=page_number,
                        text=combined,
                        metadata={"source": "pdf"},
                    )
                )

            logger.info(
                "PdfParser: finished '%s' — %d pages extracted",
                file_path.name,
                len(pages),
            )

        except Exception as exc:
            raise ParserError(
                f"PdfParser: error reading pages from '{file_path}': {exc}"
            ) from exc
        finally:
            doc.close()

        return pages
