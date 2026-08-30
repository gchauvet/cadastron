"""Detects the printed vertical grid lines of the cadastral table so that
handwritten text lines can later be assigned to the correct column.
"""
from __future__ import annotations

import numpy as np

from .config import COLUMNS

EXPECTED_BOUNDARIES = len(COLUMNS) + 1
MIN_LINE_COVERAGE = 0.55  # a grid line must be dark over >=55% of the page height
MERGE_DISTANCE = 6        # px, merge candidate columns closer than this


def _candidate_columns(binary: np.ndarray) -> np.ndarray:
    h, _ = binary.shape
    dark = (binary == 0).sum(axis=0)  # count of dark px per column
    return np.where(dark >= h * MIN_LINE_COVERAGE)[0]


def _merge_runs(indices: np.ndarray, gap: int = MERGE_DISTANCE) -> list[int]:
    if indices.size == 0:
        return []
    runs = np.split(indices, np.where(np.diff(indices) > gap)[0] + 1)
    return [int(round(run.mean())) for run in runs]


def detect_column_boundaries(binary_page: np.ndarray, page_width: int) -> list[int]:
    """Return the x pixel positions of the column boundaries (len == 15 for
    the 14 configured columns).

    Tries to detect the real printed grid lines; if the count found doesn't
    match the expected template, falls back to the fixed relative weights in
    `config.COLUMNS` so the pipeline always produces a usable (if less
    precise) result instead of crashing on a slightly damaged/curled scan.
    """
    candidates = _merge_runs(_candidate_columns(binary_page))
    if len(candidates) == EXPECTED_BOUNDARIES:
        return candidates
    return fallback_boundaries(page_width)


def fallback_boundaries(page_width: int) -> list[int]:
    weights = [c.weight for c in COLUMNS]
    total = sum(weights)
    boundaries = [0]
    acc = 0.0
    for w in weights:
        acc += w / total
        boundaries.append(int(round(acc * page_width)))
    boundaries[-1] = page_width
    return boundaries


def column_index_for_x(x: int, boundaries: list[int]) -> int:
    for i in range(len(boundaries) - 1):
        if boundaries[i] <= x < boundaries[i + 1]:
            return i
    return len(boundaries) - 2
