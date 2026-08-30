"""Text-line segmentation via Kraken's baseline (blla) layout analysis
model. This is the only step that requires `kraken` to be installed; every
earlier step (splitting, deskewing, column detection) works without it.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from PIL import Image


@dataclass
class Line:
    baseline: list[tuple[int, int]]
    bbox: tuple[int, int, int, int]  # x0, y0, x1, y1


def _bbox_from_points(baseline, boundary=None) -> tuple[int, int, int, int]:
    pts = boundary if boundary else baseline
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def segment_lines(image: np.ndarray, model_path: str | None = None) -> list[Line]:
    """Run Kraken's baseline layout analysis on a single (already split and
    deskewed) page image and return one `Line` per detected text line.

    `model_path` points to a `.mlmodel` segmentation model; if omitted,
    Kraken's bundled default model is used. That default is trained on
    printed/mixed Latin-script documents in general and was not fine-tuned
    for this register's handwriting, so line boundaries may need manual
    correction — but region/column detection here relies only on line
    position, not on recognised text, so it degrades gracefully.
    """
    try:
        from kraken import blla
        from kraken.lib import vgsl
    except ImportError as exc:
        raise RuntimeError(
            "kraken n'est pas installe. Installez-le avec `pip install kraken`, "
            "puis eventuellement recuperez un modele de segmentation dedie "
            "(`kraken get <model-id>`) et passez son chemin via --seg-model."
        ) from exc

    pil_image = Image.fromarray(image[:, :, ::-1]) if image.ndim == 3 else Image.fromarray(image)

    model = vgsl.TorchVGSLModel.load_model(model_path) if model_path else None
    segmentation = blla.segment(pil_image, model=model)

    lines: list[Line] = []
    for line in segmentation.lines:
        baseline = [tuple(p) for p in line.baseline]
        boundary = [tuple(p) for p in line.boundary] if getattr(line, "boundary", None) else None
        lines.append(Line(baseline=baseline, bbox=_bbox_from_points(baseline, boundary)))
    return lines
