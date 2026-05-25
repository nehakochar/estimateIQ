"""
factory.py — Parser factory function.

The factory pattern solves a simple problem:
  "Given a file type, which parser should I use?"

Instead of writing if/elif chains everywhere in the codebase, callers
just call `get_parser("pdf")` and get back the right parser object.

Benefits:
  - Adding a new file type = add one line to the registry dict.
  - The rest of the code never needs to change.
  - Easy to test: mock `get_parser` in unit tests.
"""

from app.services.parsers.base import BaseParser
from app.services.parsers.pdf_parser import PdfParser
from app.services.parsers.docx_parser import DocxParser
from app.services.parsers.xlsx_parser import XlsxParser


# ── Parser registry ───────────────────────────────────────────────
# Maps file_type string (as stored in the Document.file_type column)
# to the concrete parser class.
#
# To add a new file type:
#   1. Create a new parser class in its own file (e.g. pptx_parser.py)
#   2. Add one entry here: "pptx": PptxParser
_PARSER_REGISTRY: dict[str, type[BaseParser]] = {
    "pdf":  PdfParser,
    "docx": DocxParser,
    "xlsx": XlsxParser,
}


class UnsupportedFileTypeError(Exception):
    """
    Raised when `get_parser` is called with a file type that has no
    registered parser.

    Example:
        get_parser("pptx")  →  UnsupportedFileTypeError("pptx")
    """
    pass


def get_parser(file_type: str) -> BaseParser:
    """
    Return the appropriate parser instance for the given file type.

    Args:
        file_type: Lowercase file type string without the dot.
                   Examples: "pdf", "docx", "xlsx"

    Returns:
        An instance of the matching parser class.

    Raises:
        UnsupportedFileTypeError: if no parser is registered for
                                  the given file_type.

    Example:
        parser = get_parser("pdf")
        pages  = parser.parse(Path("/storage/uploads/abc/def.pdf"))
    """
    file_type = file_type.lower().strip()

    parser_class = _PARSER_REGISTRY.get(file_type)
    if parser_class is None:
        supported = ", ".join(sorted(_PARSER_REGISTRY.keys()))
        raise UnsupportedFileTypeError(
            f"No parser registered for file type '{file_type}'. "
            f"Supported types: {supported}."
        )

    # Instantiate and return the parser.
    # All parsers are stateless, so a new instance per call is fine.
    return parser_class()
