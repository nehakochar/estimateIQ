"""
pdf_parser.py — Extracts text from PDF files using PyMuPDF.

PyMuPDF is imported as `fitz` (its internal module name).
It opens a PDF, iterates over every page, and extracts the plain text.

Why PyMuPDF?
  - Very fast — written in C under the hood.
  - Handles complex PDFs (multi-column, embedded fonts, scanned text).
  - Simple API: open → iterate pages → get_text().

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


class PdfParser(BaseParser):
    """
    Parses PDF files and returns one ParsedPage per PDF page.

    Each page's text is extracted as plain text (no formatting).
    Empty pages are included with empty text so page numbers stay accurate.
    """

    def parse(self, file_path: Path) -> list[ParsedPage]:
        """
        Open the PDF and extract text from every page.

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
            # fitz.open() loads the PDF into memory.
            # Using a context manager (with) ensures the file is closed
            # even if an error occurs mid-way through.
            doc = fitz.open(str(file_path))
        except Exception as exc:
            raise ParserError(
                f"PdfParser: failed to open '{file_path}': {exc}"
            ) from exc

        pages: list[ParsedPage] = []

        try:
            # doc is iterable — each item is a fitz.Page object.
            # enumerate gives us (0-based index, page object).
            for page_index, page in enumerate(doc):
                # get_text("text") returns plain text for the page.
                # Other options: "html", "dict", "blocks" — we use "text"
                # because we only need raw content for now.
                text: str = page.get_text("text") or ""

                # Strip leading/trailing whitespace but preserve internal
                # newlines so paragraph structure is visible.
                text = text.strip()

                pages.append(
                    ParsedPage(
                        page=page_index + 1,  # convert 0-based to 1-based
                        text=text,
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
            # Always close the PDF document to free memory.
            doc.close()

        return pages
