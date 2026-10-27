"""The italic: the same drawings, slanted, with curves where the upright
cuts chamfers.

* **Slant.** Every outline is sheared by ``SLANT_DEG`` about half the
  x-height, so a glyph keeps its place and its advance, and the upright's
  spacing carries over. Stroke weights are set before the shear so every
  stroke comes out as heavy across as its upright self (``geom.Thickness``):
  a shear alone would thin the strokes that lean with it and thicken those
  that lean against it.
* **Curves.** Every chamfer the drawing recorded as one (a bowl's corner,
  an edge break, the steps of the 2's notch and the 4's clip) becomes a
  quadratic curve tangent to the edges it joins, its control point the
  corner it cut. A bowl's corner curves on both its edges or on neither.
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


def _owners(a, b, record):
    """The recorded corners the segment a-b may belong to: [(owner, line,
    distance)], ('bowl', index) for each of a bowl's two chamfer lines it
    lies on (with its distance from where the line was recorded), ('chord',
    index) for an edge break whose ends it is."""
    out = []
    mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    for idx, r in enumerate(record):
        if r[0] == 'chord':
            if ((math.dist(a, r[1]) < ON and math.dist(b, r[2]) < ON)
                    or (math.dist(a, r[2]) < ON and math.dist(b, r[1]) < ON)):
                out.append((('chord', idx), 0, 0.0))
        else:
            for k, (q, d) in enumerate(r[1:]):
                if all(abs(_cross((pt[0] - q[0], pt[1] - q[1]), d)) < ON for pt in (a, b)):
                    # how far the segment lies from the recorded point
                    u = ((a[0] - q[0]) * d[0] + (a[1] - q[1]) * d[1], (b[0] - q[0]) * d[0] + (b[1] - q[1]) * d[1])
                    dd = math.hypot(*d) or 1.0
                    far = 0.0 if min(u) <= 0 <= max(u) else min(abs(u[0]), abs(u[1])) / dd
                    out.append((('bowl', idx), k, far))
    return out


def _joins_smoothly(v, seg) -> bool:
    """Whether a chamfer meets the edge v as a corner it stands in for: a
    horizontal or vertical edge, or a diagonal running straight on. Any
    other meeting is a point the upright keeps sharp (a waist, a beak's
    tip against a diagonal)."""
    return _axis(v) or (_diag(v) and abs(_cross(v, seg)) <= 1e-4 * math.hypot(*v) * math.hypot(*seg))


def _corner(a, b, turn_left):
    """The corner a 45-degree chamfer a-b cut: where the horizontal and the
    vertical through its ends meet, outside the ink for a cut (left turns,
    ink on the left), inside it for a fill."""
    c1, c2 = (a[0], b[1]), (b[0], a[1])
    seg = (b[0] - a[0], b[1] - a[1])
    side = _cross(seg, (c1[0] - a[0], c1[1] - a[1]))       # > 0: c1 on the left of a-b
    return c1 if (side > 0) != turn_left else c2


def _segments(rings_, record):
    """Every 45-degree recorded chamfer in the rings: (ring, i, owner,
    smooth, turn_left). Each recorded chamfer line is one edge: the
    segment on it nearest where it was recorded. (A 45-degree line runs on,
    and another corner's edge can lie on it far away, as an accent's on the
    line of a corner of the letter under it: claimed by that corner, the
    accent's sharp end held its curve straight, so á's a was not a's.)"""
    claims = {}
    for ri, ring in enumerate(rings_):
        pts = [tuple(q) for q in ring]
        n = len(pts)
        for i in range(n):
            a, b = pts[i], pts[(i + 1) % n]
            if not _diag((b[0] - a[0], b[1] - a[1])):
                continue
            for own, k, far in _owners(a, b, record):
                key = (own, k)
                if own[0] == 'chord' or key not in claims or far < claims[key][0]:
                    claims[key] = (far, ri, i)
    owner = {}
    for (own, k), (far, ri, i) in claims.items():
        owner.setdefault((ri, i), own)
    out = []
    for ri, ring in enumerate(rings_):
        pts = [tuple(q) for q in ring]
        n = len(pts)
        for i in range(n):
            a, b = pts[i], pts[(i + 1) % n]
            seg = (b[0] - a[0], b[1] - a[1])
            own = owner.get((ri, i))
            if own is None:
                continue
            prev, nxt = pts[i - 1], pts[(i + 2) % n]
            vin = (a[0] - prev[0], a[1] - prev[1])
            vout = (nxt[0] - b[0], nxt[1] - b[1])
            t1, t2 = _cross(vin, seg), _cross(seg, vout)
            turns = [t for t in (t1, t2) if abs(t) > 1e-6 * math.hypot(*seg)]
            corner = bool(turns) and not (len(turns) == 2 and (turns[0] > 0) != (turns[1] > 0))
            # an S-bend or a straight run is no corner: it cannot curve, and holds its pair straight
            smooth = corner and _joins_smoothly(vin, seg) and _joins_smoothly(vout, seg)
            out.append((ri, i, own, smooth, corner and turns[0] > 0))
    return out


def curve_rings(rings_, p: Params, record):
    """Rings of points -> contours of (x, y, on_curve), in the upright frame,
    with their corners made curves.

    A bowl's corner is a pair of chamfers, the stroke's outer and inner
    edges, and they are curved together or not at all: a curve on one edge
    against a straight other would swell the stroke (or, bulging across it,
    cross the outline). A corner whose either edge meets a sharp point (a
    waist, a beak's tip, a diagonal junction) stays straight on both, so the
    point stays sharp. Edge breaks curve on their own."""
    segs = _segments(rings_, record)
    blocked = {own for _, _, own, smooth, _ in segs if own[0] == 'bowl' and not smooth}
    curved = {(ri, i): left for ri, i, own, smooth, left in segs
              if smooth and own not in blocked}
    out = []
    for ri, ring in enumerate(rings_):
        pts = [tuple(q) for q in ring]
        if len(pts) > 1 and math.dist(pts[0], pts[-1]) < _TOL:
            pts = pts[:-1]
        n = len(pts)
        c = []
        for i in range(n):
            a, b = pts[i], pts[(i + 1) % n]
            c.append((a[0], a[1], True))
            if (ri, i) in curved:
                q = _corner(a, b, curved[(ri, i)])
                c.append((q[0], q[1], False))
        out.append(c)
    return out


def shear(contour, p: Params):
    yc = p.xh / 2
    return [(x + (y - yc) * p.slant, y, on) for x, y, on in contour]


def split_warp(record):
    """(record without warps, the optical correction's warp or None)."""
    warps = [r[1] for r in record if r and r[0] == 'warp']
    return [r for r in record if not (r and r[0] == 'warp')], (warps[0] if warps else None)


def warped(contours, warp):
    if warp is None:
        return contours
    return [[(x, warp(y), on) for x, y, on in c] for c in contours]


def outline(rings, record, p: Params):
    """The italic outline: contours of (x, y, on), sheared, ink on the left
    (as the upright rings). Chamfers are found and curved on the exact
    drawing; the optical corrections (a warp in the record) then move the
    curved outline, and the shear comes last."""
    record, warp = split_warp(record)
    return [shear(c, p) for c in warped(curve_rings(rings, p, record), warp)]


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
    for c in curve_rings(rings_, p, record):
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
    split = [split_warp(r) for r in records]               # curved on the exact drawing, then moved (outline)
    records = [r for r, _ in split]
    warps = [w for _, w in split]
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
            out[mi].append(shear(warped([c], warps[mi])[0], params_[mi]))
    return out
