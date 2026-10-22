"""The italic: the same drawings, slanted, with curves where the upright
cuts chamfers.

* **Slant.** Every outline is sheared by ``SLANT_DEG`` about half the
  x-height, so a glyph keeps its place and its advance, and the upright's
  spacing carries over. Stroke weights are set before the shear so every
  stroke comes out as heavy across as its upright self (``geom.Thickness``):
  a shear alone would thin the strokes that lean with it and thicken those
  that lean against it.
* **Curves.** Every 45-degree chamfer that stands in for a right angle
  between a horizontal and a vertical edge (a bowl's corner, an edge break,
  the steps of the 2's notch and the 4's clip) becomes a quadratic curve
  tangent to both edges, its control point the corner it cut. A chamfer
  longer than any bowl's is a stroke, not a corner, and stays straight.
* **Sharp where the upright is sharp.** Corners the upright never chamfers
  stay sharp: beaks, the 3's and 8's waists, the meeting of two diagonals,
  a diagonal's end. Soft bowls against those points are what keeps the
  italic Arris.
* **Italic forms.** Where a glyph has an italic drawing (``name.ital``),
  the italic uses it (``draw.draw``): the single-storey a, the descending f.
"""
from __future__ import annotations

import math

from .params import Params

SLANT_DEG = 10.0
SLANT = math.tan(math.radians(SLANT_DEG))

_TOL = 1e-6


def italic(p: Params) -> Params:
    return p.with_(slant=SLANT)


def _axis(v) -> bool:
    n = math.hypot(*v)
    return n > _TOL and (abs(v[0]) <= 1e-4 * n or abs(v[1]) <= 1e-4 * n)


def _diag(v) -> bool:
    n = math.hypot(*v)
    return n > _TOL and abs(abs(v[0]) - abs(v[1])) <= 1e-4 * n


def _cross(a, b) -> float:
    return a[0] * b[1] - a[1] * b[0]


def _meet(p0, p1, q0, q1):
    """Intersection of the lines p0-p1 and q0-q1 (both axis-parallel here)."""
    d1 = (p1[0] - p0[0], p1[1] - p0[1])
    d2 = (q1[0] - q0[0], q1[1] - q0[1])
    den = _cross(d1, d2)
    t = _cross((q0[0] - p0[0], q0[1] - p0[1]), d2) / den
    return (p0[0] + t * d1[0], p0[1] + t * d1[1])


ON = 0.5   # font units: how near a segment must lie to a recorded chamfer


def _is_chamfer(a, b, record) -> bool:
    """Whether the segment a-b is one the drawing chamfered (``geom.ink``
    records them): a bowl's chamfer edge lies on a recorded line, an edge
    break is a recorded chord."""
    for r in record:
        if r[0] == 'chord':
            if ((math.dist(a, r[1]) < ON and math.dist(b, r[2]) < ON)
                    or (math.dist(a, r[2]) < ON and math.dist(b, r[1]) < ON)):
                return True
        else:
            q, d = r[1], r[2]
            if all(abs(_cross((pt[0] - q[0], pt[1] - q[1]), d)) < ON for pt in (a, b)):
                return True
    return False


def curve_ring(ring, p: Params, record):
    """A ring of points -> a contour of (x, y, on_curve) with its chamfers
    made curves. The ring is in the upright frame."""
    pts = [tuple(q) for q in ring]
    if len(pts) > 1 and math.dist(pts[0], pts[-1]) < _TOL:
        pts = pts[:-1]
    n = len(pts)
    out = []
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        prev, nxt = pts[i - 1], pts[(i + 2) % n]
        seg = (b[0] - a[0], b[1] - a[1])
        vin = (a[0] - prev[0], a[1] - prev[1])
        vout = (nxt[0] - b[0], nxt[1] - b[1])
        out.append((a[0], a[1], True))
        if (_diag(seg) and _axis(vin) and _axis(vout) and abs(_cross(vin, vout)) > _TOL
                and (_cross(vin, seg) > 0) == (_cross(seg, vout) > 0)
                and _is_chamfer(a, b, record)):
            c = _meet(prev, a, b, nxt)
            out.append((c[0], c[1], False))
    return out


def shear(contour, p: Params):
    yc = p.xh / 2
    return [(x + (y - yc) * p.slant, y, on) for x, y, on in contour]


def outline(rings, record, p: Params):
    """The italic outline: contours of (x, y, on), sheared, ink on the left
    (as the upright rings)."""
    return [shear(curve_ring(r, p, record), p) for r in rings]


def tt_contours(outline_):
    """Italic contours rounded, with TrueType orientation (outer clockwise)."""
    out = []
    for c in outline_:
        c = [(round(x), round(y), on) for x, y, on in c]
        clean = []
        for q in c:
            if clean and q[:2] == clean[-1][:2]:
                if q[2] and not clean[-1][2]:        # keep the on-curve point
                    clean[-1] = q
                continue
            clean.append(q)
        while len(clean) > 1 and clean[0][:2] == clean[-1][:2]:
            if clean[-1][2] and not clean[0][2]:
                clean[0] = clean[-1]
            clean.pop()
        if len(clean) >= 3:
            out.append(clean[::-1])
    return out


def draw_contours(pen, contours, dx=0.0):
    """Draw (x, y, on) contours on a segment pen: lines and quadratic curves."""
    for c in contours:
        k = next(i for i, q in enumerate(c) if q[2])
        c = c[k:] + c[:k]
        n = len(c)
        pen.moveTo((c[0][0] + dx, c[0][1]))
        i = 1
        while i <= n:
            q = c[i % n]
            if q[2]:
                if i < n:
                    pen.lineTo((q[0] + dx, q[1]))
                i += 1
            else:
                nxt = c[(i + 1) % n]
                pen.qCurveTo((q[0] + dx, q[1]), (nxt[0] + dx, nxt[1]))
                i += 2
        pen.closePath()


def flatten(contour, steps: int = 6):
    """A contour of (x, y, on) as a polyline, curves sampled."""
    n = len(contour)
    out = []
    for i, (x, y, on) in enumerate(contour):
        if on:
            out.append((x, y))
            continue
        a = contour[i - 1]
        b = contour[(i + 1) % n]
        for k in range(1, steps):
            t = k / steps
            out.append(((1 - t) ** 2 * a[0] + 2 * t * (1 - t) * x + t * t * b[0],
                        (1 - t) ** 2 * a[1] + 2 * t * (1 - t) * y + t * t * b[1]))
    return out


def polylines(outline_):
    """The italic outline as polylines, curves sampled (for kerning and
    proofs)."""
    return [flatten(c) for c in outline_]


# --- The variable italic ---------------------------------------------------

def _key(q):
    return (round(q[0], 6), round(q[1], 6))


def _chamfer_map(rings_, record, p: Params):
    """{(a, b): control} for every chamfer segment a-b a drawing curves."""
    out = {}
    for ring in rings_:
        c = curve_ring(ring, p, record)
        n = len(c)
        for i, (x, y, on) in enumerate(c):
            if not on:
                out[(_key(c[i - 1]), _key(c[(i + 1) % n]))] = (x, y)
    return out


def aligned_outlines(aligned, originals, records, params_):
    """Italic outlines for point-compatible upright masters
    (``variable.align``). A segment that is a chamfer in any master carries
    a control point in every master: at the corner it cut where it is a
    chamfer, at its middle (a straight curve) where it is not. So a curve
    grows from a straight edge as the weight moves, and every master has the
    same points with the same flags."""
    k = len(aligned)
    maps = [_chamfer_map(originals[mi], records[mi], params_[mi]) for mi in range(k)]
    out = [[] for _ in range(k)]
    for ci in range(len(aligned[0])):
        n = len(aligned[0][ci])
        curved = [any((_key(aligned[mi][ci][j]), _key(aligned[mi][ci][(j + 1) % n])) in maps[mi]
                      for mi in range(k)) for j in range(n)]
        for mi in range(k):
            ring = aligned[mi][ci]
            c = []
            for j in range(n):
                a, b = ring[j], ring[(j + 1) % n]
                c.append((a[0], a[1], True))
                if curved[j]:
                    ctrl = maps[mi].get((_key(a), _key(b)), ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2))
                    c.append((ctrl[0], ctrl[1], False))
            out[mi].append(shear(c, params_[mi]))
    return out
