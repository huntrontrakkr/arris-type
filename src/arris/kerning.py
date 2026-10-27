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
A closing kern never brings the two inks closer than half a standard gap
in any direction (CLEAR): rows a little apart count at their diagonal
distance. A mark floating high kerns as if its sides ran down to half
the x-height (``_shadow``), so it never slides over a lowercase body.
No pair is kerned across scripts (a Latin letter and a Cyrillic or Greek
one): shapers break text into runs of one script before kerning, so such
a pair is never applied (it was 39% of the variable fonts' pairs).
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
CLEAR = 0.5         # a closing kern keeps the inks this share of a standard gap apart, in any direction


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


def _shadow(prof, ys, xh):
    """A mark floating high (above half the x-height: quotes, apostrophes,
    degree, ordinals) casts its sides straight down to half the x-height:
    it may tuck beside a tall stem (L’) but never over a lowercase body,
    where it would read as an accent (h’s, it's)."""
    left, right = prof
    ink = ~np.isnan(left)
    if not ink.any():
        return prof
    low = ys[ink].min()
    if low <= xh / 2:
        return prof
    i0 = int(np.argmax(ink))                                     # the mark's lowest row
    fill = (ys >= xh / 2) & (ys < low)
    left, right = left.copy(), right.copy()
    left[fill], right[fill] = left[i0], right[i0]
    return left, right


_SCRIPTS: dict = {}


def scripts(name: str) -> frozenset:
    """The scripts a glyph is set in as a shaper itemises text ({'Latn'},
    or {'Latn', 'Cyrl', 'Grek'} for an A that is all three: glyphs.ALIASES),
    from its characters or its base glyph's (a.sc, uni0434.loclBGR, f_i);
    empty for the common and inherited ones (punctuation, figures, marks),
    which join the run of their neighbours."""
    if not _SCRIPTS:
        from fontTools import unicodedata as ud
        from .draw import REGISTRY
        from .glyphs import ALIASES
        cps: dict = {}
        for n, spec in REGISTRY.items():
            if spec.unicode is not None:
                cps.setdefault(n, set()).add(spec.unicode)
        for cp, n in ALIASES.items():
            cps.setdefault(n, set()).add(cp)
        for n, cs in cps.items():
            _SCRIPTS[n] = frozenset(sc for sc in (ud.script(chr(c)) for c in cs) if sc not in ('Zyyy', 'Zinh', 'Zzzz'))
    for n in (name, name.split('.')[0], name.split('.')[0].split('_')[0]):
        if n in _SCRIPTS:
            return _SCRIPTS[n]
    return frozenset()


def kerns(placed: dict, p, light: float, left_names=None, right_names=None):
    """placed: name -> (rings, advance). Returns {(left, right): kern}."""
    ys = np.linspace(-p.desc, p.asc + 0.3 * p.cap, ROWS)
    prof = {n: _shadow(profiles(r, ys), ys, p.xh) for n, (r, _) in placed.items()}
    std = 2 * light
    out = {}
    lnames = left_names or list(placed)
    rnames = right_names or list(placed)
    rscript = [scripts(n) for n in rnames]
    R = np.array([placed[n][1] - prof[n][1] for n in lnames])      # white to the right of each left glyph
    L = np.array([prof[n][0] for n in rnames])                      # white to the left of each right glyph
    for i, a in enumerate(lnames):
        gap = R[i][None, :] + L                                     # rows x right glyphs
        both = ~np.isnan(gap)
        has = both.any(axis=1)
        g = np.where(both, gap, np.inf).min(axis=1)
        ks = np.zeros(len(rnames))
        for j in np.nonzero(has)[0]:
            m = g[j]
            if m > INTERLOCK * std:
                ks[j] = -CLOSE * (m - INTERLOCK * std)
            elif m < FLOOR * std:
                ks[j] = FLOOR * std - m
        closing = np.nonzero(ks < 0)[0]
        if len(closing):
            ks[closing] = np.maximum(ks[closing], np.minimum(0.0, _clearance(R[i], L[closing], ys, CLEAR * std)))
        sa = scripts(a)
        for j in np.nonzero(has)[0]:
            k = 5 * round(ks[j] / 5)
            if abs(k) >= MIN_KERN and (not sa or not rscript[j] or sa & rscript[j]):
                out[(a, rnames[j])] = int(k)
    return out


def _clearance(r, Ls, ys, d):
    """For a left glyph's right white ``r`` (per row) and right glyphs'
    left white ``Ls`` (glyphs x rows), the least kern that keeps their inks
    at least ``d`` apart in any direction: rows a little apart count too, at
    their diagonal distance. (Within a row the closing rule already keeps
    more; across rows nothing else would stop an apostrophe being pulled
    down onto an h's shoulder.)"""
    dy = ys[1] - ys[0]
    n = len(ys)
    bound = np.full(len(Ls), -np.inf)
    for off in range(-int(d // dy), int(d // dy) + 1):
        lo, hi = max(0, -off), min(n, n - off)
        gap = r[lo:hi][None, :] + Ls[:, lo + off:hi + off]       # left glyph's row i, right glyph's row i + off
        gap = np.where(np.isnan(gap), np.inf, gap).min(axis=1)
        need = np.sqrt(max(d * d - (off * dy) ** 2, 0.0))
        bound = np.maximum(bound, need - gap)
    return bound


def fea(pairs: dict) -> str:
    lines = ['feature kern {']
    for (a, b), k in sorted(pairs.items()):
        lines.append(f'    pos {a} {b} {k};')
    lines.append('} kern;')
    return '\n'.join(lines) + '\n'
