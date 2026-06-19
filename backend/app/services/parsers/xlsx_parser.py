"""
xlsx_parser.py — Extracts text from Excel (.xlsx) files using openpyxl.

An Excel workbook contains one or more sheets.
Each sheet contains rows and columns of cells.

Our strategy:
  - One ParsedPage per sheet.
  - Each cell value is converted to a string.
  - Rows are joined with tabs (so columns are visible).
  - Sheets are joined as separate pages.

Why one page per sheet?
  RFP Excel files often have multiple sheets (e.g. "Pricing", "Timeline",
  "Requirements").  Keeping them separate makes it easier to reference
  which sheet a piece of text came from in later processing phases.
"""

import logging
from pathlib import Path
from typing import Any

import openpyxl  # reads .xlsx files

from app.services.parsers.base import BaseParser, ParsedPage, ParserError

logger = logging.getLogger(__name__)


def _cell_to_str(value: Any) -> str:
    """
    Convert a cell value to a clean string.

    openpyxl returns cell values as Python types:
      - str   → already a string
      - int   → convert to string
      - float → convert to string
      - bool  → "True" / "False"
      - None  → empty string (empty cell)
      - datetime → ISO format string

    Args:
        value: The raw cell value from openpyxl.

    Returns:
        A string representation, or "" for None/empty cells.
    """
    if value is None:
        return ""
    return str(value).strip()


class XlsxParser(BaseParser):
    """
    Parses .xlsx files and returns one ParsedPage per worksheet.

    Each page contains all non-empty rows from that sheet,
    with cells joined by tabs.
    """

    def parse(self, file_path: Path) -> list[ParsedPage]:
        """
        Open the .xlsx file and extract text from every sheet.

        Args:
            file_path: Path to the .xlsx file on disk.

        Returns:
            A list of ParsedPage objects, one per worksheet.
            Page numbers are 1-based.

        Raises:
            ParserError: if the file cannot be opened or read.
        """
        logger.info("XlsxParser: starting parse of '%s'", file_path)

        try:
            # read_only=True is faster — we don't need to modify the file.
            # data_only=True returns cell values instead of formulas.
            #   Without data_only, a cell with =SUM(A1:A10) would return
            #   the formula string, not the calculated number.
            workbook = openpyxl.load_workbook(
                str(file_path), read_only=True, data_only=True
            )
        except Exception as exc:
            raise ParserError(
                f"XlsxParser: failed to open '{file_path}': {exc}"
            ) from exc

        pages: list[ParsedPage] = []

        try:
            # workbook.sheetnames is a list of sheet name strings.
            for sheet_index, sheet_name in enumerate(workbook.sheetnames):
                sheet = workbook[sheet_name]
                row_texts: list[str] = []

                # sheet.iter_rows() yields one tuple of cells per row.
                # values_only=True gives us the cell values directly
                # instead of Cell objects.
                for row in sheet.iter_rows(values_only=True):
                    # Convert every cell in the row to a string
                    cell_strings = [_cell_to_str(cell) for cell in row]

                    # Skip rows where every cell is empty
                    if any(cell_strings):
                        row_texts.append("\t".join(cell_strings))

                # Join all rows with newlines
                sheet_text = "\n".join(row_texts)

                pages.append(
                    ParsedPage(
                        page=sheet_index + 1,  # 1-based page number
                        text=sheet_text,
                        metadata={
                            "source": "xlsx",
                            "sheet_name": sheet_name,
                        },
                    )
                )

            logger.info(
                "XlsxParser: finished '%s' — %d sheets extracted",
                file_path.name,
                len(pages),
            )

        except Exception as exc:
            raise ParserError(
                f"XlsxParser: error reading sheets from '{file_path}': {exc}"
            ) from exc
        finally:
            workbook.close()

        return pages
