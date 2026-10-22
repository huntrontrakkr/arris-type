"""Outline geometry for font measurement: overlap-free, finely flattened
glyph outlines and exact line slicing.

Pipeline per glyph:
  1. Decompose components (DecomposingRecordingPen).
  2. Remove overlaps with skia-pathops `simplify` (variable-font outlines
     often overlap; without this a stem drawn as two overlapping contours
     would slice as two intervals).
  3. Flatten every quadratic/cubic segment into chords with a guaranteed
     maximum deviation of `tol` font units (default 0.01 u), keeping a
     record of which chords came from genuine straight `lineTo` segments.
  4. Slice with an arbitrary line p + u*d: intersect every chord, sort the
     crossings along the line, accumulate the winding number, and return the
     ink intervals (non-zero winding) as (u0, u1) pairs.

Bounding boxes come from fontTools' BoundsPen (exact curve extrema), not
from the flattened polygon.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
import pathops
from fontTools.pens.basePen import BasePen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen


class _FlattenPen(BasePen):
    """Flattens curves into chords with max deviation `tol`."""

    def __init__(self, tol: float):
        super().__init__(None)
        self.tol = tol
        self.contours: list[list[tuple[float, float]]] = []
        # straight segments as (contour index, p0, p1), from real lineTo's
        self.lines: list[tuple[int, tuple[float, float], tuple[float, float]]] = []

    def _moveTo(self, p):
        self.contours.append([tuple(p)])

    def _lineTo(self, p):
        c = self.contours[-1]
        p = tuple(p)
        if p != c[-1]:
            self.lines.append((len(self.contours) - 1, c[-1], p))
            c.append(p)

    def _qCurveToOne(self, p1, p2):
        c = self.contours[-1]
        p0 = c[-1]
        dev = math.hypot(p0[0] - 2 * p1[0] + p2[0], p0[1] - 2 * p1[1] + p2[1])
        # chord error of a uniformly split quadratic <= dev / (4 n^2)
        n = max(2, math.ceil(math.sqrt(dev / (4 * self.tol))))
        for i in range(1, n + 1):
            t = i / n
            mt = 1 - t
            c.append((mt * mt * p0[0] + 2 * mt * t * p1[0] + t * t * p2[0],
                      mt * mt * p0[1] + 2 * mt * t * p1[1] + t * t * p2[1]))

    def _curveToOne(self, p1, p2, p3):
        c = self.contours[-1]
        p0 = c[-1]
        m = max(math.hypot(p0[0] - 2 * p1[0] + p2[0], p0[1] - 2 * p1[1] + p2[1]),
                math.hypot(p1[0] - 2 * p2[0] + p3[0], p1[1] - 2 * p2[1] + p3[1]))
        # |B''| <= 6 m ; chord error <= |B''| / (8 n^2)
        n = max(2, math.ceil(math.sqrt(6 * m / (8 * self.tol))))
        for i in range(1, n + 1):
            t = i / n
            mt = 1 - t
            a, b, cc, d = mt ** 3, 3 * mt * mt * t, 3 * mt * t * t, t ** 3
            c.append((a * p0[0] + b * p1[0] + cc * p2[0] + d * p3[0],
                      a * p0[1] + b * p1[1] + cc * p2[1] + d * p3[1]))

    def _closePath(self):
        c = self.contours[-1]
        if len(c) > 1 and c[-1] != c[0]:
            self.lines.append((len(self.contours) - 1, c[-1], c[0]))
        elif len(c) > 1:
            c.pop()

    _endPath = _closePath


def _signed_area(poly: np.ndarray) -> float:
    x, y = poly[:, 0], poly[:, 1]
    return 0.5 * float(np.dot(x, np.roll(y, -1)) - np.dot(np.roll(x, -1), y))


@dataclass
class Outline:
    name: str
    advance: int
    bounds: tuple[float, float, float, float] | None  # xMin, yMin, xMax, yMax
    polys: list[np.ndarray]
    areas: list[float]
    lines: list[tuple[int, tuple, tuple]]
    A: np.ndarray = field(repr=False)
    B: np.ndarray = field(repr=False)

    # ---- construction -------------------------------------------------
    @classmethod
    def from_glyphset(cls, gs, name: str, tol: float = 0.01) -> "Outline":
        rec = DecomposingRecordingPen(gs)
        gs[name].draw(rec)
        bp = BoundsPen(None)
        rec.replay(bp)
        path = pathops.Path()
        rec.replay(path.getPen())
        path.simplify(fix_winding=True, keep_starting_points=False)
        fp = _FlattenPen(tol)
        path.draw(fp)
        polys = [np.asarray(c, dtype=float) for c in fp.contours if len(c) >= 3]
        areas = [_signed_area(p) for p in polys]
        if polys:
            A = np.concatenate(polys)
            B = np.concatenate([np.roll(p, -1, axis=0) for p in polys])
        else:
            A = B = np.zeros((0, 2))
        return cls(name, gs[name].width, bp.bounds, polys, areas, fp.lines, A, B)

    # ---- topology -------------------------------------------------------
    def classify_contours(self):
        """Return (outer_idx, holes, islands) using orientation: holes have
        the opposite winding sign to the largest contour; islands are
        same-sign contours other than the largest (e.g. a floating dot)."""
        if not self.polys:
            return None, [], []
        outer = int(np.argmax(np.abs(self.areas)))
        s = math.copysign(1, self.areas[outer])
        holes = [i for i, a in enumerate(self.areas) if math.copysign(1, a) != s]
        islands = [i for i, a in enumerate(self.areas)
                   if math.copysign(1, a) == s and i != outer]
        return outer, holes, islands

    # ---- slicing ---------------------------------------------------------
    def slice(self, p, d) -> list[tuple[float, float]]:
        """Ink intervals (u0, u1) along the line p + u*d (d normalised)."""
        p = np.asarray(p, dtype=float)
        d = np.asarray(d, dtype=float)
        d = d / np.hypot(*d)
        n = np.array([-d[1], d[0]])
        sa = (self.A - p) @ n
        sb = (self.B - p) @ n
        m = (sa > 0) != (sb > 0)
        if not m.any():
            return []
        sa_, sb_ = sa[m], sb[m]
        t = sa_ / (sa_ - sb_)
        q = self.A[m] + t[:, None] * (self.B[m] - self.A[m])
        u = (q - p) @ d
        w = np.where(sb_ > sa_, 1, -1)
        order = np.argsort(u, kind="stable")
        out, wind, start = [], 0, None
        for ui, wi in zip(u[order], w[order]):
            prev = wind
            wind += wi
            if prev == 0 and wind != 0:
                start = ui
            elif prev != 0 and wind == 0:
                if ui - start > 1e-6:
                    out.append((float(start), float(ui)))
        return out

    def hslice(self, y):
        """Ink intervals in x along the horizontal line at height y."""
        return self.slice((0.0, y), (1.0, 0.0))

    def vslice(self, x):
        """Ink intervals in y along the vertical line at abscissa x."""
        return self.slice((x, 0.0), (0.0, 1.0))

    # ---- helpers ---------------------------------------------------------
    def contour_lines(self, idx: int):
        return [(p0, p1) for ci, p0, p1 in self.lines if ci == idx]

    def support(self, idx_list, n, tol=0.5):
        """Points of the given contours that maximise <pt, n> (within tol)."""
        n = np.asarray(n, float) / np.hypot(*n)
        pts = np.concatenate([self.polys[i] for i in idx_list])
        proj = pts @ n
        mx = proj.max()
        return pts[proj >= mx - tol], mx


def dist_to_poly(pt, poly: np.ndarray) -> float:
    """Euclidean distance from a point to a closed polygon's boundary."""
    a = poly
    b = np.roll(poly, -1, axis=0)
    ab = b - a
    t = np.clip(((pt - a) * ab).sum(1) / np.maximum((ab * ab).sum(1), 1e-12), 0, 1)
    q = a + t[:, None] * ab
    return float(np.sqrt(((q - pt) ** 2).sum(1)).min())


def interval_at(intervals, u):
    for a, b in intervals:
        if a <= u <= b:
            return (a, b)
    return None


def raster(outline: Outline, scale: float, x0: float, y0: float, w: int, h: int,
           img: np.ndarray):
    """Rasterise (pixel-centre sampling) into img[h, w] via hslice."""
    for row in range(h):
        y = y0 + (h - 1 - row + 0.5) / scale
        for a, b in outline.hslice(y):
            c0 = max(0, math.ceil((a - x0) * scale - 0.5))
            c1 = min(w, math.floor((b - x0) * scale - 0.5) + 1)
            if c1 > c0:
                img[row, c0:c1] = 1
