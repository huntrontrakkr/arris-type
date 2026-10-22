"""Pair kerning from outlines.

Spacing (``arris.spacing``) gives every side of every glyph the same light,
which suits pairs whose profiles face each other. Some pairs interlock: a T's
bar reaches over an o, an A's open side meets a V's, a period tucks under a
P's bowl. For those the white the eye sees between the two shapes is far
wider than their closest approach suggests the designer meant.

For each pair, on rows where both glyphs have ink, the gap between the left
glyph's right profile and the right glyph's left profile is measured. If
its narrowest point is much wider than two sidebearings, the pair closes
toward that; if it is narrower than a collision floor (an accent on a
capital against a T's bar), it opens. Everything else is left to spacing.
"""
from __future__ import annotations

import numpy as np
from shapely.geometry import LineString

from .geom import rings_to_shapely

ROWS = 160
INTERLOCK = 1.25    # a pair closes when its narrowest gap passes this many standard gaps ...
CLOSE = 0.8         # ... by this share of the excess
FLOOR = 0.35        # and opens when its narrowest gap is under this share of a standard gap
MIN_KERN = 10


def profiles(rings, ys):
    poly = rings_to_shapely(rings)
    left = np.full(len(ys), np.nan)
    right = np.full(len(ys), np.nan)
    if poly.is_empty:
        return left, right
    minx, _, maxx, _ = poly.bounds
    for i, y in enumerate(ys):
        cut = poly.intersection(LineString([(minx - 10, y), (maxx + 10, y)]))
        if cut.is_empty:
            continue
        xs = [c[0] for g in getattr(cut, 'geoms', [cut]) for c in getattr(g, 'coords', [])]
        if xs:
            left[i], right[i] = min(xs), max(xs)
    return left, right


def kerns(placed: dict, p, light: float, left_names=None, right_names=None):
    """placed: name -> (rings, advance). Returns {(left, right): kern}."""
    ys = np.linspace(-p.desc, p.asc + 0.3 * p.cap, ROWS)
    prof = {n: profiles(r, ys) for n, (r, _) in placed.items()}
    std = 2 * light
    out = {}
    lnames = left_names or list(placed)
    rnames = right_names or list(placed)
    R = np.array([placed[n][1] - prof[n][1] for n in lnames])      # white to the right of each left glyph
    L = np.array([prof[n][0] for n in rnames])                      # white to the left of each right glyph
    for i, a in enumerate(lnames):
        gap = R[i][None, :] + L                                     # rows x right glyphs
        both = ~np.isnan(gap)
        has = both.any(axis=1)
        g = np.where(both, gap, np.inf).min(axis=1)
        for j in np.nonzero(has)[0]:
            m = g[j]
            k = 0.0
            if m > INTERLOCK * std:
                k = -CLOSE * (m - INTERLOCK * std)
            elif m < FLOOR * std:
                k = FLOOR * std - m
            k = 5 * round(k / 5)
            if abs(k) >= MIN_KERN:
                out[(a, rnames[j])] = int(k)
    return out


def fea(pairs: dict) -> str:
    lines = ['feature kern {']
    for (a, b), k in sorted(pairs.items()):
        lines.append(f'    pos {a} {b} {k};')
    lines.append('} kern;')
    return '\n'.join(lines) + '\n'
