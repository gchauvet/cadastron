"""Light geometric preprocessing applied to a single split page before
segmentation: deskew, plus a binarisation used only for grid/column
detection (Kraken does its own binarisation internally and should receive
the deskewed but otherwise unmodified page).
"""
from __future__ import annotations

import cv2
import numpy as np


def deskew(image: np.ndarray, max_angle: float = 8.0) -> np.ndarray:
    """Rotate `image` so that the page content is level.

    Uses the minimum-area rectangle of the non-background pixels. Angles
    larger than `max_angle` are assumed to be a detection error (e.g. a
    near-square content mask) and are ignored to avoid corrupting the page.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    coords = cv2.findNonZero(255 - mask)
    if coords is None:
        return image

    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = 90 + angle
    if abs(angle) > max_angle:
        return image

    h, w = image.shape[:2]
    matrix = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    return cv2.warpAffine(image, matrix, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)


def binarize(image: np.ndarray) -> np.ndarray:
    """Adaptive binarisation used only for structural analysis (grid/column
    detection), not fed to Kraken directly.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    return cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 35, 15
    )
