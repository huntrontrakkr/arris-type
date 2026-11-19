"""Optical spacing: sidebearings from the white beside each glyph.

Every side of every glyph should carry the same amount of light. Over a
vertical zone (baseline to cap height, or to x-height), the white between a
side's outermost ink and the ink in each row counts toward that light, up to a
depth limit (an open mouth like C's is not a lake to be filled). Each side's
bearing is then whatever brings its total light to the target, which is set by
a flat-sided reference (the H). This is the area method of HT Letterspacer
and of Tracy's straight-and-round rules, made exact for any outline.
"""
from __future__ import annotations

import numpy as np
from shapely.geometry import LineString

from .geom import rings_to_shapely


def profiles(rings, y0: float, y1: float, n: int = 200):
    """Per sampled row: (leftmost ink x, rightmost ink x), NaN where empty."""
    poly = rings_to_shapely(rings)
    ys = y0 + (np.arange(n) + 0.5) * (y1 - y0) / n
    minx, _, maxx, _ = poly.bounds
    left = np.full(n, np.nan)
    right = np.full(n, np.nan)
    for i, y in enumerate(ys):
        cut = poly.intersection(LineString([(minx - 10, y), (maxx + 10, y)]))
        if cut.is_empty:
            continue
        parts = getattr(cut, 'geoms', [cut])
        xs = [c[0] for g in parts for c in g.coords]
        left[i], right[i] = min(xs), max(xs)
    return ys, left, right


def side_light(depths: np.ndarray, depth_limit: float) -> float:
    """Mean white depth over the zone, rows without ink counting as fully open."""
    d = np.where(np.isnan(depths), depth_limit, np.minimum(depths, depth_limit))
    return float(d.mean())


def _edges(rings, y0: float, y1: float, xmin: float, xmax: float, hang: float):
    """The body's two edges, where pieces of it come into the zone from
    outside: a piece that is one stroke with a larger piece in the zone (a
    tail's tip that rises over the baseline, a hook's end) or a piece of its
    own that only dips into the zone, most of it outside (the ŉ's apostrophe
    under the x-height). Such a piece sets the edge in the measure it is
    tall, wholly from ``hang`` units: a sliver over the line is the hanging
    part's, an arm reaching into the zone the body's (the ℞'s cross).
    Counted whole at a unit's height, it moved the edge onto itself at the
    weight where it first came into the zone: the italic ȷ's advance jumped
    51 units between 350 and 360, the ℘'s 44 between 230 and 240, the ŉ's
    60 between 360 and 370."""
    import shapely
    from shapely.geometry import box
    poly = rings_to_shapely(rings)
    whole = [q for q in getattr(poly, 'geoms', [poly]) if q.area > 0]
    inside = poly.intersection(box(-1e5, y0, 1e5, y1))
    pieces = [q for q in getattr(inside, 'geoms', [inside]) if q.area > 0]
    if len(pieces) < 2:
        return xmin, xmax

    def stroke(q):
        return next((i for i, w in enumerate(whole) if w.intersects(q)), -1)
    of = [stroke(q) for q in pieces]

    def comes_in(q, k):
        if any(k == k2 and q2.area > q.area for q2, k2 in zip(pieces, of) if q2 is not q):
            return True
        return k >= 0 and whole[k].area > 2 * q.area
    body = [q for q, k in zip(pieces, of) if not comes_in(q, k)]
    if not body:
        return xmin, xmax
    b0, _, b1, _ = shapely.union_all(body).bounds
    lo, hi = b0, b1
    for q, k in zip(pieces, of):
        if q in body:
            continue
        t = min(1.0, (q.bounds[3] - q.bounds[1]) / hang)
        lo = min(lo, b0 + (q.bounds[0] - b0) * t)
        hi = max(hi, b1 + (q.bounds[2] - b1) * t)
    return lo, hi


def bearings(rings, y0: float, y1: float, light: float, depth_limit: float, n: int = 200,
             floor: float = -1e9, hang: float = 0.0):
    """(lsb, rsb) measured from the ink's extremes, such that each side carries
    ``light`` units of mean white (bearing plus white inside the profile).
    ``hang``: the height from which a piece that comes into the zone from
    outside sets the edge wholly (_edges); 0, every piece wholly."""
    ys, left, right = profiles(rings, y0, y1, n)
    xmin, xmax = np.nanmin(left), np.nanmax(right)
    if hang > 0.0:
        xmin, xmax = _edges(rings, y0, y1, xmin, xmax, hang)
    lw = side_light(np.maximum(left - xmin, 0.0), depth_limit)
    rw = side_light(np.maximum(xmax - right, 0.0), depth_limit)
    return max(light - lw, floor), max(light - rw, floor), xmin, xmax
