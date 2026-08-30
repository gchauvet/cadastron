"""Splits a double-page cadastral scan into its two constituent pages.

Each scan shows two facing pages separated by the book's binding, which
appears as a dark vertical band (the "gutter") somewhere near the horizontal
centre of the image, plus a black scanner background around the page edges.
"""
from __future__ import annotations

import cv2
import numpy as np

DARK_THRESHOLD = 60      # a pixel this dark or darker is considered background/gutter
SEARCH_BAND = 0.30        # look for the gutter within the central 30% of the width
MIN_GUTTER_WIDTH = 3      # px, minimum plausible spine width at full resolution


def _column_darkness(gray: np.ndarray) -> np.ndarray:
    return gray.mean(axis=0)


def find_gutter_x(gray: np.ndarray) -> int:
    """Return the x pixel coordinate of the centre of the binding gutter.

    Falls back to the image's horizontal midpoint if no clear dark band is
    found in the central search band.
    """
    h, w = gray.shape
    means = _column_darkness(gray)
    lo = int(w * (0.5 - SEARCH_BAND / 2))
    hi = int(w * (0.5 + SEARCH_BAND / 2))
    band = means[lo:hi]
    dark_mask = band < DARK_THRESHOLD
    if dark_mask.sum() < MIN_GUTTER_WIDTH:
        return w // 2

    dark_idx = np.where(dark_mask)[0]
    center = len(band) // 2
    runs = np.split(dark_idx, np.where(np.diff(dark_idx) > 1)[0] + 1)
    best_run = min(runs, key=lambda r: abs(((r[0] + r[-1]) / 2) - center))
    return lo + int((best_run[0] + best_run[-1]) / 2)


def content_bbox(gray: np.ndarray, dark_threshold: int = DARK_THRESHOLD) -> tuple[int, int, int, int]:
    """Bounding box (x0, y0, x1, y1) of the non-black page content."""
    mask = gray > dark_threshold
    rows = np.where(mask.any(axis=1))[0]
    cols = np.where(mask.any(axis=0))[0]
    if rows.size == 0 or cols.size == 0:
        h, w = gray.shape
        return 0, 0, w, h
    return int(cols[0]), int(rows[0]), int(cols[-1]) + 1, int(rows[-1]) + 1


def split_scan(image: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Split a full double-page scan into (left_page, right_page) BGR images,
    each cropped to its non-black content bounding box.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    split_x = find_gutter_x(gray)

    left, left_gray = image[:, :split_x], gray[:, :split_x]
    right, right_gray = image[:, split_x:], gray[:, split_x:]

    lx0, ly0, lx1, ly1 = content_bbox(left_gray)
    rx0, ry0, rx1, ry1 = content_bbox(right_gray)

    return left[ly0:ly1, lx0:lx1], right[ry0:ry1, rx0:rx1]
