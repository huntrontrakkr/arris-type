"""Pair kerning from outlines.

Spacing (``arris.spacing``) gives every side of every glyph the same light,
which suits pairs whose profiles face each other. Some pairs interlock: a T's
bar reaches over an o, an L's foot runs under a Y's arm, a period tucks under
a P's bowl. For those the white the eye sees between the two shapes is far
wider than their closest approach suggests the designer meant.

For each pair, on rows where both glyphs have ink, the gap between the left
glyph's right profile and the right glyph's left profile is measured, in
standard gaps (two sidebearings: the white between two H's).

* Two letters whose narrowest gap is wider than a standard gap close to
  one, and never nearer than three quarters of one in any direction (rows
  a little apart count at their diagonal distance). That is where hand
  kerning leaves them: in seven kerned faces of this kind (Chakra Petch,
  Oxanium, Exo 2, Tomorrow, Regular and heavy) the L's foot stands 1.06
  standard gaps from the Y's stem, 0.96 from the T's, the T's bar 1.02
  from the A, the T 1.03 from the J; where the approach is on a slant the
  inks come to 0.86 (LV), 0.74 (LW), 0.87 (To), 0.78 (Ta), 0.75 (Tr).
  Until 1.017 a pair closed only past a gap and a quarter, and by four
  fifths of the excess: LY was left 1.36 to 1.47 gaps apart, LT 1.30 to
  1.39, TA 1.33 to 1.39, and the capitals read as loose wherever an L, a T
  or a Y stood (the owner: "L next to Y, super off").
* A pair with a mark of punctuation in it keeps more air, as it does in
  those faces (a period stands 1.2 to 1.5 gaps from what it follows): it
  closes past a gap and a quarter by four fifths of the excess, and a mark
  that lies low (a period, a comma: all its ink under half the x-height)
  comes no nearer than a gap and a fifth to any ink over it and is pulled
  in by no more than 0.45 of a gap, which is what those faces pull a period
  in by after any letter that overhangs it (P. 0.47, F. 0.42, T. 0.46,
  Y. 0.47, V. 0.37, r. 0.38, f. 0.33). Until 1.017 a period went under a
  P's bowl by 1.4 gaps at Regular and 2.2 at Black, 255 and 280 units.
* A pair narrower than a collision floor (an accent on a capital against
  a T's bar) opens. Everything else is left to spacing. (Still to do: a
  bowl standing against an arm over a long run is nearer than in those
  faces at the heavy weights, R and Y 0.38 gaps for their 0.63 to 0.74, P
  and A 0.47 for 0.62 to 0.85; tip to tip, as K and Y, they let letters
  all but touch, 0.05 to 0.46. A floor on the white averaged over a run a
  gap tall opened 277 pairs at Black, most of them bar ends: too blunt.)

A mark floating high kerns as if its sides ran down to half the x-height
(``_shadow``), so it never slides over a lowercase body. No pair is kerned
across scripts (a Latin letter and a Cyrillic or Greek one): shapers break
text into runs of one script before kerning, so such a pair is never
applied (it was 39% of the variable fonts' pairs).
"""
from __future__ import annotations

import numpy as np
from shapely.geometry import LineString

from .geom import rings_to_shapely

ROWS = 160
INTERLOCK = 1.0     # two letters close when their narrowest gap passes this many standard gaps ...
CLOSE = 1.0         # ... by this share of the excess (to a standard gap)
CLEAR = 0.75        # and their inks stay this share of a standard gap apart, in any direction
MARK_INTERLOCK = 1.25   # a pair with a mark of punctuation in it: when its gap passes this many ...
MARK_CLOSE = 0.8        # ... by this share of the excess
MARK_CLEAR = 0.5        # its inks this far apart in any direction
LOW_CLEAR = 1.2         # and a mark lying low (a period, a comma) this far from any ink,
LOW_PULL = 0.45         # pulled in by no more than this share of a standard gap
FLOOR = 0.35        # a pair opens when its narrowest gap is under this share of a standard gap
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
    raw = {n: profiles(r, ys) for n, (r, _) in placed.items()}
    prof = {n: _shadow(raw[n], ys, p.xh) for n in placed}
    std = 2 * light
    out = {}
    lnames = left_names or list(placed)
    rnames = right_names or list(placed)
    rscript = [scripts(n) for n in rnames]
    mark = {n: _mark(n) for n in placed}
    low = {n: mark[n] and _lies_low(raw[n], ys, p.xh) for n in placed}
    rmark, rlow = np.array([mark[n] for n in rnames]), np.array([low[n] for n in rnames])
    R = np.array([placed[n][1] - prof[n][1] for n in lnames])      # white to the right of each left glyph
    L = np.array([prof[n][0] for n in rnames])                      # white to the left of each right glyph
    for i, a in enumerate(lnames):
        gap = R[i][None, :] + L                                     # right glyphs x rows
        both = ~np.isnan(gap)
        has = both.any(axis=1)
        g = np.where(both, gap, np.inf).min(axis=1)
        marked = rmark | mark[a]
        inter = np.where(marked, MARK_INTERLOCK, INTERLOCK) * std
        share = np.where(marked, MARK_CLOSE, CLOSE)
        clear = np.where(rlow | low[a], LOW_CLEAR, np.where(marked, MARK_CLEAR, CLEAR)) * std
        ks = np.zeros(len(rnames))
        for j in np.nonzero(has)[0]:
            m = g[j]
            if m > inter[j]:
                ks[j] = -share[j] * (m - inter[j])
            elif m < FLOOR * std:
                ks[j] = FLOOR * std - m
        closing = np.nonzero(ks < 0)[0]
        for d in np.unique(clear[closing]):
            idx = closing[clear[closing] == d]
            ks[idx] = np.maximum(ks[idx], np.minimum(0.0, _clearance(R[i], L[idx], ys, d)))
        lows = closing[(rlow | low[a])[closing]]
        ks[lows] = np.maximum(ks[lows], -LOW_PULL * std)
        sa = scripts(a)
        for j in np.nonzero(has)[0]:
            k = 5 * round(ks[j] / 5)
            if abs(k) >= MIN_KERN and (not sa or not rscript[j] or sa & rscript[j]):
                out[(a, rnames[j])] = int(k)
    return out


def _mark(name: str) -> bool:
    """Whether a glyph is a mark of punctuation (not a letter): by its
    kind, a letter if it is not a glyph of the library's (a test shape)."""
    from .draw import REGISTRY
    spec = REGISTRY.get(name)
    return spec is not None and isinstance(spec.kind, tuple) and spec.kind[0] == 'punct'


def _lies_low(prof, ys, xh) -> bool:
    """Whether all a glyph's ink is under half the x-height (a period, a
    comma, an ellipsis, the low quotes)."""
    ink = ~np.isnan(prof[0])
    return bool(ink.any()) and ys[ink].max() < xh / 2


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
