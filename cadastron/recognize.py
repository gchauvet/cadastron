"""Optional Kraken text-recognition step, meant to be used once a model
fine-tuned for this register's handwriting is available. Until then, run
the pipeline without --rec-model: lines are still segmented, cropped and
saved (output/lines/<sheet>/) for manual transcription or to build a Kraken
training set (e.g. with `ketos` / an eScriptorium export).

NOTE: this wraps kraken's line-recognition API (`kraken.rpred`) directly on
a single cropped line rather than through the usual whole-page pipeline; the
exact constructor arguments for the line record may need a small adjustment
to match the installed kraken version.
"""
from __future__ import annotations

import numpy as np
from PIL import Image


class Recognizer:
    def __init__(self, model_path: str):
        from kraken.lib import models

        self.model = models.load_any(model_path)

    def recognize(self, line_image: np.ndarray) -> str:
        from kraken import rpred
        from kraken.containers import BaselineLine, Segmentation

        pil_image = (
            Image.fromarray(line_image[:, :, ::-1])
            if line_image.ndim == 3
            else Image.fromarray(line_image)
        )
        h, w = line_image.shape[:2]
        # La ligne est deja recadree : sa baseline est le bas de l'image et
        # son polygone englobant est l'image entiere.
        line = BaselineLine(
            id="line",
            baseline=[(0, h - 1), (w - 1, h - 1)],
            boundary=[(0, 0), (w - 1, 0), (w - 1, h - 1), (0, h - 1)],
        )
        segmentation = Segmentation(
            type="baselines",
            imagename="line",
            text_direction="horizontal-lr",
            script_detection=False,
            lines=[line],
            regions={},
            line_orders=[],
        )

        predictions = list(rpred.rpred(self.model, pil_image, segmentation))
        return predictions[0].prediction if predictions else ""
