"""Detects the printed vertical grid lines of the cadastral table so that
handwritten text lines can later be assigned to the correct column.

Three findings shape this module, all of them measured on the scans:

1. **Measure the body, not the page.** The header block is dense with
   horizontal text that floods the darkness profile. Restricting the profile
   to the table body took one page from 13 noisy rules to 15 clean ones at a
   single strict threshold.

2. **`preprocess.deskew` leaves up to ~1° of residual skew.** Over a 2100 px
   body band, 0.5° smears a vertical rule across ~19 px, so no single pixel
   column ever reaches threshold and the rule simply vanishes. This — not the
   column logic — was why detection failed. The fix is to measure in a
   *sheared frame*: rotating and re-binarising the image destroys the thin
   rules (measured: 12 rejects against 2), so the image is left untouched and
   only the measurement frame is skewed, positions being mapped back
   afterwards.

3. **The volume mixes several printed forms.** Roughly the first 200 scans are
   the "matrice des propriétés foncières" this template describes; later scans
   are a *tableau de classement / application du tarif* with a completely
   different column structure, and the first scan is an older matrice edition
   lacking two columns. A page that does not match is therefore a normal
   outcome and must be reported as such, never forced into this grid.

The fit itself is RANSAC-style: every pair of detected rules, matched against
every pair of template indices, proposes an affine placement of the template;
the placement explaining the most rules wins and is then refined by least
squares on its inliers. This tolerates both missing rules (faded ink, gutter
shadow) and spurious ones (handwriting stems), which a fit anchored on the
outer borders does not — those borders are frequently among the rules that
fail to be detected at all.
"""
from __future__ import annotations

import cv2
import numpy as np

from .config import COLUMNS

EXPECTED_BOUNDARIES = len(COLUMNS) + 1

# Vertical slice of the page used to measure the rules, as fractions of page
# height: below the header block, above the totals line at the foot.
BODY_TOP, BODY_BOTTOM = 0.25, 0.85

# Residual-skew search. Measured angles span roughly -1.2..+1.2 degrees, with
# a systematic negative bias on left-hand pages: `deskew` fits its rectangle
# on the content mask, which the gutter shadow drags on their inner edge.
SHEAR_MAX_DEG = 1.2
SHEAR_STEP_DEG = 0.05

# px, merge candidate columns closer than this. A printed rule is a few px
# wide and often splits in two under binarisation, so this must comfortably
# exceed the rule width (6 was one pixel short of merging real pairs).
MERGE_DISTANCE = 12

# Rules this close to the page edge are scan border, not table.
EDGE_MARGIN_FRACTION = 0.01

# The darkness threshold is swept: the rules fade unevenly across a scan, so a
# strict setting misses half the grid on one page while a loose one promotes
# handwriting into grid lines on the next.
COVERAGE_MAX, COVERAGE_MIN, COVERAGE_STEP = 0.90, 0.30, 0.05

# The printed table occupies most of the page but never all of it. Measured at
# 0.86..0.95 of page width across the volume; every bad fit seen while
# developing this had anchored on an interior rule and come out near 0.82.
WIDTH_MIN, WIDTH_MAX = 0.86, 0.95

# A boundary counts as landing on a rule within this distance.
SNAP_FRACTION = 0.008
MIN_SNAP_TOLERANCE = 10

# Template indices must be at least this far apart to propose a placement:
# close pairs give a wildly extrapolated span from a small measurement error.
MIN_INDEX_GAP = 5

# Below this many boundaries landing on real rules the page is not this form.
# 14 of 16 separates the matrice cleanly from the other forms in the volume
# (matrice pages score 15-16, pages of other forms 3-12).
MIN_HITS = 14


def _template() -> np.ndarray:
    """Template boundaries as fractions of the table width (0.0 .. 1.0)."""
    weights = np.array([c.weight for c in COLUMNS], dtype=float)
    return np.concatenate([[0.0], np.cumsum(weights) / weights.sum()])


def _body_profile(binary_page: np.ndarray) -> tuple[np.ndarray, float, float]:
    """Darkness profile of the table body, measured square to the printed rules.

    Returns the profile, the x offset to subtract to map a profile position
    back to page coordinates, and the residual skew angle in degrees.
    """
    height, width = binary_page.shape
    band = (binary_page[int(height * BODY_TOP):int(height * BODY_BOTTOM)] == 0)
    band = band.astype(np.float32)
    band_height = band.shape[0]

    best: tuple[float, np.ndarray, float] | None = None
    for degrees in np.arange(-SHEAR_MAX_DEG, SHEAR_MAX_DEG + 1e-9, SHEAR_STEP_DEG):
        shear = np.tan(np.radians(degrees))
        matrix = np.float32([[1, shear, 0], [0, 1, 0]])
        sheared = cv2.warpAffine(band, matrix, (width, band_height))
        profile = sheared.sum(axis=0) / band_height
        # Peakiness, not a count above some cutoff: a threshold-free criterion
        # that cannot be gamed by a shear that merely smears more ink into
        # fewer columns.
        energy = float((profile ** 4).sum())
        if best is None or energy > best[0]:
            best = (energy, profile, float(degrees))

    assert best is not None
    _, profile, degrees = best
    # The shear pivots on the top of the band; referring positions to its
    # mid-height halves the worst-case error over the band.
    offset = np.tan(np.radians(degrees)) * band_height / 2.0
    return profile, offset, degrees


def _rules_at(profile: np.ndarray, offset: float, page_width: int,
              coverage: float) -> list[int]:
    """Rule positions where the profile is dark over `coverage` of the body."""
    indices = np.where(profile >= coverage)[0]
    if indices.size == 0:
        return []
    runs = np.split(indices, np.where(np.diff(indices) > MERGE_DISTANCE)[0] + 1)
    margin = page_width * EDGE_MARGIN_FRACTION
    positions = [int(round(run.mean() - offset)) for run in runs]
    return [x for x in positions if margin <= x <= page_width - margin]


def _fit_template(rules: list[int], page_width: int) -> tuple[list[int], int] | None:
    """Place the template on the rules; return (boundaries, rules explained)."""
    if len(rules) < MIN_INDEX_GAP:
        return None

    template = _template()
    count = template.size
    observed = np.array(rules, dtype=float)
    tolerance = max(float(MIN_SNAP_TOLERANCE), page_width * SNAP_FRACTION)

    best: tuple[tuple[int, float], float, float] | None = None
    for k in range(count):
        for l in range(k + MIN_INDEX_GAP, count):
            # Every pair of rules, read as template indices k and l, implies a
            # table width; only plausible widths are worth scoring.
            spans = (observed[None, :] - observed[:, None]) / (template[l] - template[k])
            plausible = (spans >= WIDTH_MIN * page_width) & (spans <= WIDTH_MAX * page_width)
            for i, j in zip(*np.nonzero(plausible)):
                span = spans[i, j]
                origin = observed[i] - template[k] * span
                model = origin + template * span
                # Score both ways round: template -> rules alone is maximised
                # by a span that simply ignores every rule past its right edge.
                forward = np.abs(model[:, None] - observed[None, :]).min(axis=1)
                backward = np.abs(observed[:, None] - model[None, :]).min(axis=1)
                score = (
                    int((forward <= tolerance).sum()),
                    -float(np.minimum(forward, tolerance).sum()
                           + np.minimum(backward, tolerance).sum()),
                )
                if best is None or score > best[0]:
                    best = (score, origin, span)

    if best is None:
        return None
    _, origin, span = best
    model = origin + template * span

    # Refine on the inliers: the winning hypothesis rests on just two rules.
    nearest = [min(rules, key=lambda r: abs(r - m)) for m in model]
    inliers = [(f, r) for f, r, m in zip(template, nearest, model)
               if abs(r - m) <= tolerance]
    if len(inliers) >= MIN_INDEX_GAP:
        fractions = np.array([f for f, _ in inliers], dtype=float)
        positions = np.array([r for _, r in inliers], dtype=float)
        design = np.vstack([fractions, np.ones_like(fractions)]).T
        span_ls, origin_ls = np.linalg.lstsq(design, positions, rcond=None)[0]
        if WIDTH_MIN * page_width <= span_ls <= WIDTH_MAX * page_width:
            origin, span = origin_ls, span_ls
            model = origin + template * span

    boundaries = []
    for position in model:
        near = min(rules, key=lambda r: abs(r - position))
        boundaries.append(int(near if abs(near - position) <= tolerance else round(position)))
    # Snapping is per-boundary and can collide on a noisy page; enforce a
    # strictly increasing grid so column lookup stays well defined.
    for i in range(1, len(boundaries)):
        boundaries[i] = max(boundaries[i], boundaries[i - 1] + 1)

    distances = np.abs(np.array(boundaries, dtype=float)[:, None] - observed[None, :]).min(axis=1)
    return boundaries, int((distances <= tolerance).sum())


def detect_column_boundaries(binary_page: np.ndarray, page_width: int) -> list[int] | None:
    """x positions of the column boundaries, or None if this is not the form.

    None means the page carries no matrice table — another form, a summary
    page, or a scan too damaged to fit. The caller must skip such a page:
    stretching the template across it instead is exactly the bug this replaces,
    which silently shifted every column and dropped the last one entirely.
    """
    profile, offset, _ = _body_profile(binary_page)

    best: tuple[list[int], int] | None = None
    coverage = COVERAGE_MAX
    while coverage >= COVERAGE_MIN:
        fitted = _fit_template(_rules_at(profile, offset, page_width, coverage), page_width)
        if fitted is not None and (best is None or fitted[1] > best[1]):
            best = fitted
        coverage -= COVERAGE_STEP

    if best is None or best[1] < MIN_HITS:
        return None
    boundaries, _ = best
    width = boundaries[-1] - boundaries[0]
    if not (WIDTH_MIN * page_width <= width <= WIDTH_MAX * page_width):
        return None
    return boundaries


def column_index_for_x(x: int, boundaries: list[int]) -> int:
    for i in range(len(boundaries) - 1):
        if boundaries[i] <= x < boundaries[i + 1]:
            return i
    return len(boundaries) - 2
