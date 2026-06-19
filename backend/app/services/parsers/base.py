"""
base.py — Abstract base class for all document parsers.

Why an abstract base class?
  It defines a contract: every parser (PDF, DOCX, XLSX) MUST implement
  the `parse` method with the same signature.  This means the rest of
  the code can call `parser.parse(path)` without knowing which concrete
  parser it's talking to — that's the "factory pattern" in action.

Beginner note on `ABC` and `abstractmethod`:
  - `ABC` = Abstract Base Class.  You cannot instantiate it directly.
  - `@abstractmethod` = subclasses MUST override this method or Python
    will raise a TypeError when you try to create an instance.
"""

from abc import ABC, abstractmethod
from pathlib import Path


class ParsedPage:
    """
    A single unit of parsed content.

    For PDFs  → one entry per page.
    For DOCX  → one entry per paragraph (or the whole document as page 1).
    For XLSX  → one entry per sheet.

    Attributes:
        page    : 1-based page/sheet/section number.
        text    : The extracted plain text for that page/section.
        metadata: Optional extra info (e.g. sheet name for XLSX).
    """

    def __init__(self, page: int, text: str, metadata: dict | None = None) -> None:
        self.page = page
        self.text = text
        self.metadata = metadata or {}

    def to_dict(self) -> dict:
        """Convert to a plain dict for JSON storage in PostgreSQL."""
        result = {"page": self.page, "text": self.text}
        if self.metadata:
            result["metadata"] = self.metadata
        return result


class BaseParser(ABC):
    """
    Abstract base class that all parsers must inherit from.

    Usage:
        class PdfParser(BaseParser):
            def parse(self, file_path: Path) -> list[ParsedPage]:
                ...  # your implementation here
    """

    @abstractmethod
    def parse(self, file_path: Path) -> list[ParsedPage]:
        """
        Parse the document at `file_path` and return a list of ParsedPage objects.

        Args:
            file_path: Absolute or relative path to the file on disk.

        Returns:
            A list of ParsedPage objects, one per logical unit
            (page for PDF, paragraph block for DOCX, sheet for XLSX).

        Raises:
            ParserError: if the file cannot be read or parsed.
        """
        ...


class ParserError(Exception):
    """
    Raised when a parser encounters an unrecoverable error.

    Examples:
      - The file is corrupted and cannot be opened.
      - The file is password-protected.
      - An unexpected library error occurs.
    """
    pass
