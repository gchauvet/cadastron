"""End-to-end pipeline: images/ (double-page scans) -> output/cadastron.ods

For each scan:
  1. split into left/right physical pages (gutter detection)
  2. deskew each page
  3. detect the printed column grid
  4. segment handwritten/printed text lines with Kraken
  5. group lines into (row, column) cells
  6. save cropped line images (future manual transcription / model training)
  7. optionally run Kraken text recognition to fill the cells
  8. write one ODS sheet per page

Recognition is optional (--rec-model) since no trained model exists yet for
this handwriting; without it, cells are left empty but every detected line
is saved to output/lines/<sheet>/ together with a layout.json so
transcription (manual or automated later) can be reconciled back into the
spreadsheet.

Usage:
    python -m cadastron.pipeline --images-dir images --output output/cadastron.ods
    python -m cadastron.pipeline --limit 2 --debug   # smoke test on 2 scans
"""
from __future__ import annotations

import argparse
import json
import logging
import re
from pathlib import Path

import cv2

from .columns import detect_column_boundaries
from .config import IMAGE_EXTENSIONS
from .gutter import split_scan
from .ods_writer import add_page_sheet, new_document, save
from .preprocess import binarize, deskew
from .rows import group_into_rows
from .segment import Line, segment_lines

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("cadastron")


def natural_key(path: Path):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", path.stem)]


def list_scans(images_dir: Path) -> list[Path]:
    files = [p for p in images_dir.iterdir() if p.suffix.lower() in IMAGE_EXTENSIONS]
    return sorted(files, key=natural_key)


def crop_line(page_img, line: Line, pad: int = 4):
    x0, y0, x1, y1 = line.bbox
    h, w = page_img.shape[:2]
    x0, y0 = max(0, x0 - pad), max(0, y0 - pad)
    x1, y1 = min(w, x1 + pad), min(h, y1 + pad)
    return page_img[y0:y1, x0:x1]


def process_page(
    page_img,
    sheet_name: str,
    lines_dir: Path,
    seg_model: str | None,
    rec_model: str | None,
) -> list[dict[int, str]] | None:
    page_img = deskew(page_img)
    binary = binarize(page_img)
    boundaries = detect_column_boundaries(binary, page_img.shape[1])
    if boundaries is None:
        # Not a matrice page: another printed form, a summary page, or a scan
        # too damaged to fit. Better skipped than transcribed against a grid
        # that does not describe it.
        return None

    lines = segment_lines(page_img, seg_model)
    rows = group_into_rows(lines, boundaries)

    sheet_lines_dir = lines_dir / sheet_name
    sheet_lines_dir.mkdir(parents=True, exist_ok=True)

    recognizer = None
    if rec_model:
        from .recognize import Recognizer

        recognizer = Recognizer(rec_model)

    layout = []
    ods_rows: list[dict[int, str]] = []
    for r_idx, row in enumerate(rows):
        row_text: dict[int, str] = {}
        row_layout = {"row": r_idx, "cells": {}}
        for col_idx, col_lines in row.items():
            texts = []
            paths = []
            for l_idx, line in enumerate(col_lines):
                crop = crop_line(page_img, line)
                fname = f"r{r_idx:03d}_c{col_idx:02d}_l{l_idx:02d}.png"
                cv2.imwrite(str(sheet_lines_dir / fname), crop)
                paths.append(fname)
                if recognizer:
                    texts.append(recognizer.recognize(crop))
            row_layout["cells"][col_idx] = paths
            if texts:
                row_text[col_idx] = "\n".join(texts)
        layout.append(row_layout)
        ods_rows.append(row_text)

    (sheet_lines_dir / "layout.json").write_text(
        json.dumps(layout, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return ods_rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--images-dir", default="images")
    parser.add_argument("--output", default="output/cadastron.ods")
    parser.add_argument("--lines-dir", default="output/lines")
    parser.add_argument("--seg-model", default=None, help="chemin vers un modele de segmentation Kraken (.mlmodel)")
    parser.add_argument("--rec-model", default=None, help="chemin vers un modele de reconnaissance Kraken (.mlmodel)")
    parser.add_argument("--limit", type=int, default=None, help="ne traiter que les N premiers scans (tests)")
    args = parser.parse_args()

    images_dir = Path(args.images_dir)
    lines_dir = Path(args.lines_dir)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    scans = list_scans(images_dir)
    if args.limit:
        scans = scans[: args.limit]
    log.info("%d scans trouves dans %s", len(scans), images_dir)

    doc = new_document()
    sheets_written = 0
    skipped: list[str] = []

    for scan_path in scans:
        log.info("Traitement de %s", scan_path.name)
        image = cv2.imread(str(scan_path))
        if image is None:
            log.warning("Impossible de lire %s, ignore", scan_path)
            continue

        left, right = split_scan(image)
        stem = scan_path.stem
        for suffix, page_img in (("a", left), ("b", right)):
            sheet_name = f"{stem}_{suffix}"
            try:
                rows = process_page(page_img, sheet_name, lines_dir, args.seg_model, args.rec_model)
            except RuntimeError as exc:
                log.error("%s: %s", sheet_name, exc)
                return
            if rows is None:
                log.warning("%s: grille du tableau non reconnue, page ignoree", sheet_name)
                skipped.append(sheet_name)
                continue
            add_page_sheet(doc, sheet_name, rows)
            sheets_written += 1

    save(doc, str(output_path))
    log.info("ODS ecrit: %s (%d feuilles)", output_path, sheets_written)
    if skipped:
        log.warning("%d pages ignorees (grille non reconnue): %s",
                    len(skipped), ", ".join(skipped))


if __name__ == "__main__":
    main()
