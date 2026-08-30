"""Groups Kraken-detected text lines into the (row, column) grid of the
printed cadastral table.

The printed template only rules vertical column lines; entries are not all
the same height (an owner with several buildings/parcels spans several
handwritten lines under a single "numéro de la liste alphabétique"). So a
new row is started whenever a line lands in that first column, or when the
vertical gap since the previous line is unusually large.
"""
from __future__ import annotations

from .columns import column_index_for_x
from .segment import Line

ROW_GAP_FACTOR = 2.2  # gap > this * median line height also starts a new row
NUMERO_COLUMN = 0      # "N°s de la liste alphabétique" is always the first column


def _line_y(line: Line) -> float:
    return (line.bbox[1] + line.bbox[3]) / 2


def _line_x_start(line: Line) -> int:
    return line.bbox[0]


def _median_line_height(lines: list[Line]) -> float:
    heights = sorted(l.bbox[3] - l.bbox[1] for l in lines)
    return heights[len(heights) // 2] if heights else 20.0


def group_into_rows(lines: list[Line], boundaries: list[int]) -> list[dict[int, list[Line]]]:
    """Return a list of rows; each row maps a column index (see
    `config.COLUMNS`) to the list of lines that fall in it, in reading order.
    """
    ordered = sorted(lines, key=lambda l: (_line_y(l), _line_x_start(l)))
    if not ordered:
        return []

    median_h = _median_line_height(ordered)
    rows: list[dict[int, list[Line]]] = []
    current: dict[int, list[Line]] | None = None
    last_y = None

    for line in ordered:
        col = column_index_for_x(_line_x_start(line), boundaries)
        y = _line_y(line)
        starts_new_row = (
            current is None
            or col == NUMERO_COLUMN
            or (last_y is not None and (y - last_y) > median_h * ROW_GAP_FACTOR)
        )
        if starts_new_row:
            current = {}
            rows.append(current)
        current.setdefault(col, []).append(line)
        last_y = y

    return rows
