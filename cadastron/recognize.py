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
        from kraken.containers import BaselineLine

        pil_image = (
            Image.fromarray(line_image[:, :, ::-1])
            if line_image.ndim == 3
            else Image.fromarray(line_image)
        )
        h, w = line_image.shape[:2]
        baseline = [[0, h - 1], [w, h - 1]]
        boundary = [[0, 0], [w, 0], [w, h], [0, h]]
        line = BaselineLine(id="line", baseline=baseline, boundary=boundary)

        predictions = list(rpred.rpred(self.model, pil_image, [line]))
        return predictions[0].prediction if predictions else ""
