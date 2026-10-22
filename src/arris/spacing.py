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


def bearings(rings, y0: float, y1: float, light: float, depth_limit: float, n: int = 200,
             floor: float = -1e9):
    """(lsb, rsb) measured from the ink's extremes, such that each side carries
    ``light`` units of mean white (bearing plus white inside the profile)."""
    ys, left, right = profiles(rings, y0, y1, n)
    xmin, xmax = np.nanmin(left), np.nanmax(right)
    lw = side_light(left - xmin, depth_limit)
    rw = side_light(xmax - right, depth_limit)
    return max(light - lw, floor), max(light - rw, floor), xmin, xmax
