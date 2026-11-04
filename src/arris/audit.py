"""The optical audit: numbers along the weight that type is judged by and
the other checks never measured (the owner's issues #24-#27 measured them
by hand). From the engine's drawings, upright, at any weight:

* overshoot: how far each side of a letter reaches past its line (a bowl's
  past the x-height, cap height or baseline; a point's below the baseline)
* contact: how much of a letter's top runs along the x-height
* counter: the widest white inside a letter
* mono_white: the white a Mono cell keeps beside its letter (1 - ink / cell)

tools/optics_report.py prints them for every weight; tests/test_audit.py holds
the ones with a rule (overshoot that grows with the weight, flat sides on
their lines) and the one waiting on a decision (the Mono's white, #24).
"""
from __future__ import annotations

from statistics import mean

from shapely.geometry import LineString

import arris.glyphs  # noqa: F401  (the registry)

from .font import place
from .geom import rings_to_shapely
from .instances import params

FIGS = ('zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine')
ASC = set('bdfhklt')
# the letters #24 measured the Mono's white on
MONO_LETTERS = tuple('abcdefghnopqrsuvwxyzHMNOW') + FIGS


def _rings(name, p):
    rings, adv = place(name, p)
    return [[q[:2] for q in r] for r in rings], adv


def lines(name, p):
    """(bottom line, top line) a glyph is drawn between."""
    if name in FIGS or name[:1].isupper():
        return 0.0, p.cap
    return 0.0, (p.asc if name[:1] in ASC else p.xh)


def overshoot(name, p):
    """(top, bottom): how far the glyph reaches past its top line and below
    its baseline, in font units (positive is past the line)."""
    rings, _ = _rings(name, p)
    ys = [y for r in rings for _, y in r]
    lo, hi = lines(name, p)
    return max(ys) - hi, lo - min(ys)


def contact(name, p, band: float = 8.0):
    """How much of the glyph's top runs along its line: the ink across,
    within ``band`` units of the top."""
    rings, _ = _rings(name, p)
    ink = rings_to_shapely(rings)
    x0, _, x1, y1 = ink.bounds
    return max(ink.intersection(LineString([(x0 - 10, y), (x1 + 10, y)])).length
               for y in (y1 - band + 0.5, y1 - band / 2, y1 - 0.5))


def counter(name, p):
    """The widest counter (hole) in the glyph, in font units."""
    rings, _ = _rings(name, p)
    ink = rings_to_shapely(rings)
    best = 0.0
    for part in getattr(ink, 'geoms', [ink]):
        for hole in part.interiors:
            hx0, _, hx1, _ = hole.bounds
            best = max(best, hx1 - hx0)
    return best


def mono_white(wght: float, letters=MONO_LETTERS):
    """(mean white per cell, (tightest letter, its ink share of the cell))
    in Arris Mono at a weight."""
    p = params(wght).with_(mono=True)
    shares = {}
    for n in letters:
        rings, adv = _rings(n, p)
        xs = [x for r in rings for x, _ in r]
        shares[n] = (max(xs) - min(xs)) / adv
    tight = max(shares, key=shares.get)
    return 1 - mean(shares.values()), (tight, shares[tight])
