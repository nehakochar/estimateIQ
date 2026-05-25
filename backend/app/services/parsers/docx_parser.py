"""
docx_parser.py — Extracts text from Word (.docx) files using python-docx.

A .docx file is a ZIP archive containing XML.  python-docx handles all
the XML parsing and gives us a clean Python API.

Structure of a Word document:
  - Document → Paragraphs (body text, headings, list items)
  - Document → Tables → Rows → Cells → Paragraphs

Our strategy:
  1. Extract all paragraph text from the body.
  2. Extract all text from tables (cell by cell).
  3. Group everything into a single "page 1" entry.
     (Word documents don't have hard page boundaries in the XML,
      so we treat the whole document as one logical unit.)

Why group into one page?
  Word's page breaks are calculated by the rendering engine (Word app),
  not stored as explicit markers in the XML.  Splitting by page would
  require a full layout engine.  For RFP text extraction, having all
  the text in one block is sufficient for Phase 3.
"""

import logging
from pathlib import Path

from docx import Document as DocxDocument  # python-docx

from app.services.parsers.base import BaseParser, ParsedPage, ParserError

logger = logging.getLogger(__name__)


class DocxParser(BaseParser):
    """
    Parses .docx files and returns the full document text as a single page.

    Text is extracted from:
      - All body paragraphs (headings, body text, list items, etc.)
      - All table cells
    """

    def parse(self, file_path: Path) -> list[ParsedPage]:
        """
        Open the .docx file and extract all text content.

        Args:
            file_path: Path to the .docx file on disk.

        Returns:
            A list containing a single ParsedPage (page=1) with all
            extracted text joined by newlines.

        Raises:
            ParserError: if the file cannot be opened or read.
        """
        logger.info("DocxParser: starting parse of '%s'", file_path)

        try:
            # DocxDocument() opens and parses the .docx ZIP/XML structure.
            doc = DocxDocument(str(file_path))
        except Exception as exc:
            raise ParserError(
                f"DocxParser: failed to open '{file_path}': {exc}"
            ) from exc

        text_parts: list[str] = []

        try:
            # ── Extract paragraph text ────────────────────────────
            # doc.paragraphs gives every paragraph in the document body.
            # paragraph.text is the plain text of that paragraph.
            for para in doc.paragraphs:
                stripped = para.text.strip()
                if stripped:  # skip empty paragraphs
                    text_parts.append(stripped)

            # ── Extract table text ────────────────────────────────
            # doc.tables gives every table in the document.
            # We iterate: table → row → cell → paragraph.
            for table in doc.tables:
                for row in table.rows:
                    row_texts: list[str] = []
                    for cell in row.cells:
                        cell_text = cell.text.strip()
                        if cell_text:
                            row_texts.append(cell_text)
                    if row_texts:
                        # Join cells with a tab so table structure is visible
                        text_parts.append("\t".join(row_texts))

        except Exception as exc:
            raise ParserError(
                f"DocxParser: error reading content from '{file_path}': {exc}"
            ) from exc

        # Join all parts with newlines into one big text block
        full_text = "\n".join(text_parts)

        logger.info(
            "DocxParser: finished '%s' — %d characters extracted",
            file_path.name,
            len(full_text),
        )

        # Return as a single-element list (one "page" = whole document)
        return [
            ParsedPage(
                page=1,
                text=full_text,
                metadata={"source": "docx"},
            )
        ]
