"""Builds the final ODS workbook: one sheet per physical page, with the
column headers of the printed cadastral template.
"""
from __future__ import annotations

from odf.opendocument import OpenDocumentSpreadsheet
from odf.table import Table, TableCell, TableRow
from odf.text import P

from .config import COLUMNS

MAX_SHEET_NAME_LENGTH = 31


def new_document() -> OpenDocumentSpreadsheet:
    return OpenDocumentSpreadsheet()


def _cell(text: str = "") -> TableCell:
    cell = TableCell()
    if text:
        for part in str(text).split("\n"):
            cell.addElement(P(text=part))
    return cell


def add_page_sheet(doc: OpenDocumentSpreadsheet, sheet_name: str, rows: list[dict[int, str]]) -> None:
    """Add one sheet to `doc` for a single physical page.

    `rows` is a list of {column_index: cell_text} dicts, as produced by
    joining each cell's Kraken lines (see `pipeline.process_page`).
    """
    table = Table(name=sheet_name[:MAX_SHEET_NAME_LENGTH])

    header = TableRow()
    for col in COLUMNS:
        header.addElement(_cell(col.header))
    table.addElement(header)

    for row_data in rows:
        row = TableRow()
        for i in range(len(COLUMNS)):
            row.addElement(_cell(row_data.get(i, "")))
        table.addElement(row)

    doc.spreadsheet.addElement(table)


def save(doc: OpenDocumentSpreadsheet, path: str) -> None:
    doc.save(path)
