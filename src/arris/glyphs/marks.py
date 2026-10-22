"""Diacritics, and every accented letter composed from its decomposition.

Marks are drawn in the same language: acute and grave are 45-degree strokes
cut flat top and bottom; circumflex and caron are small gables; dieresis
and dot are stem-square dots; the tilde steps at 45 degrees; breve and ring
are small chamfered bowls; cedilla and ogonek turn on a chamfered corner.

Placement is measured, not tabulated: a mark above sits a fixed gap above
the base's own highest ink (so it clears an ascender or a capital without a
per-letter list); a mark below hangs from the baseline. Capitals take a
flatter mark size, so accented capitals stay inside the line.
"""
from __future__ import annotations

import unicodedata

from fontTools import agl

from ..draw import B, REGISTRY, Glyph, glyph
from ..params import SQRT2


def gap(p):
    """White between a base and a mark above it (the i's dot gap)."""
    return max(p.m, 0.4 * p.sv)


def size(p, case):
    """Height of a stroke mark (acute, circumflex...)."""
    return (2.0 if case == 'lc' else 1.5) * p.m + 0.5 * p.sv


def _dot(g, x, y):
    s = g.p.sv
    g.stroke((x, y), (x, y + s))


def acute(g, x, y, case, sign=1):
    p = g.p
    a = size(p, case)
    k = p.sd / SQRT2
    # centreline rises a over a; flat cuts at y and y + a
    g.stroke((x - sign * a / 2, y), (x + sign * a / 2, y + a), start='h', end='h')


def grave(g, x, y, case):
    acute(g, x, y, case, sign=-1)


def circumflex(g, x, y, case, flip=False):
    """A small gable, its point cut flat an edge break each side (as the A's)."""
    p = g.p
    w = size(p, case)                                       # 45 degrees: as tall as each side is wide
    f = p.c
    if not flip:
        pts = [(x - w, y), (x - f, y + w - f), (x + f, y + w - f), (x + w, y)]
    else:
        pts = [(x - w, y + w), (x - f, y + f), (x + f, y + f), (x + w, y + w)]
    g.stroke(*pts, start='h', end='h')


def caron(g, x, y, case):
    circumflex(g, x, y, case, flip=True)


def dieresis(g, x, y, case):
    p = g.p
    d = p.sv + max(1.2 * p.m, 0.8 * p.sv)
    _dot(g, x - d / 2, y)
    _dot(g, x + d / 2, y)


def dotaccent(g, x, y, case):
    _dot(g, x, y)


def macron(g, x, y, case):
    p = g.p
    w = size(p, case)
    g.stroke((x - w, y + g.sh / 2), (x + w, y + g.sh / 2))


def tilde(g, x, y, case):
    """Up at 45 degrees, along, down, along, up: the tilde as a step."""
    p = g.p
    w = size(p, case)
    h = w / 2.5
    a = (2 * w - 3 * h) / 2
    x0 = x - w
    pts = [(x0, y), (x0 + h, y + h), (x0 + h + a, y + h), (x0 + 2 * h + a, y), (x0 + 2 * h + 2 * a, y),
           (x0 + 3 * h + 2 * a, y + h)]
    g.stroke(*pts, start='v', end='v')


def breve(g, x, y, case):
    p = g.p
    w = size(p, case)
    h = 0.75 * w
    g.stroke((x - w + p.sv / 2, y + h + g.sh / 2), B(x - w + p.sv / 2, y + g.sh / 2, p.m / 2),
             B(x + w - p.sv / 2, y + g.sh / 2, p.m / 2), (x + w - p.sv / 2, y + h + g.sh / 2))


def ring(g, x, y, case):
    """A small chamfered square ring."""
    p = g.p
    r = p.sv / 2 + (1.0 if case == 'lc' else 0.8) * p.m      # centreline half-size
    leg = p.m / 2
    yc = y + r + g.sh / 2
    g.stroke(B(x - r, yc - r, leg), B(x + r, yc - r, leg), B(x + r, yc + r, leg), B(x - r, yc + r, leg),
             closed=True)


def hungarumlaut(g, x, y, case):
    p = g.p
    d = 0.6 * size(p, case) + 0.5 * p.sv
    acute(g, x - d / 2, y, case)
    acute(g, x + d / 2, y, case)


def commabelow(g, x, y, case):
    from .punct import _comma
    p = g.p
    _comma(g, None, x + 0.25 * p.sv, -gap(p))


def commaabove(g, x, y, case):
    """The turned comma that stands for a cedilla over g."""
    p = g.p
    s = p.sv
    yb = y
    yt = yb + 1.5 * s
    g.stroke((x, yb), (x, yt), (x + 0.75 * s, yt + 0.75 * s), end='h')


def cedilla(g, x, y, case):
    p = g.p
    s = p.sv
    yb = -p.desc + g.sh / 2 + 0.25 * p.m
    g.stroke((x, g.sh / 2), (x, yb + 0.0), (x - 1.5 * p.m - s / 2, yb))


def ogonek(g, x, y, case):
    p = g.p
    yb = -p.desc + g.sh / 2 + 0.25 * p.m
    g.stroke((x, g.sh / 2), B(x, yb, p.m / 2), (x + 1.5 * p.m + p.sv / 2, yb))


ABOVE = {'̀': grave, '́': acute, '̂': circumflex, '̃': tilde, '̄': macron,
         '̆': breve, '̇': dotaccent, '̈': dieresis, '̊': ring, '̋': hungarumlaut,
         '̌': caron}
BELOW = {'̦': commabelow, '̧': cedilla, '̨': ogonek}

# Letters whose cedilla is written as a comma (Latvian, and Romanian's own
# comma-below letters come through U+0326 already).
CEDILLA_AS_COMMA = set('KkLlNnRrG')


def _name(ch):
    return agl.UV2AGL.get(ord(ch), f'uni{ord(ch):04X}')


def compose(chars, base_names):
    """Register a glyph for every char in ``chars`` that decomposes into a
    known base and known marks. ``base_names`` maps base chars to glyph names."""
    made = []
    for ch in chars:
        d = unicodedata.normalize('NFD', ch)
        if len(d) < 2:
            continue
        base, marks = d[0], d[1:]
        if not all(m in ABOVE or m in BELOW for m in marks):
            continue
        bname = base_names.get(base)
        if any(m in ABOVE for m in marks) and bname in ('i', 'j'):
            bname = {'i': 'dotlessi', 'j': 'uni0237'}[bname]
        if bname is None or bname not in REGISTRY:
            continue
        name = _name(ch)
        if name in REGISTRY:
            continue
        _register(name, ch, bname, base, marks)
        made.append(name)
    return made


def _register(name, ch, bname, base, marks):
    spec = REGISTRY[bname]
    case = 'uc' if base.isupper() else 'lc'

    def fn(g, bname=bname, marks=marks, base=base, case=case):
        from ..draw import draw
        from ..geom import rings_to_shapely
        # The base, finished (openings solved, clipped and cut), then the marks.
        p = g.p
        rings = draw(bname, p, g.ot, g.ob).rings()
        top = max(y for r in rings for _, y in r)
        g.extra, g.clip = [rings_to_shapely(rings)], None
        x = g.W / 2
        y = top + gap(p)
        for m in marks:
            if m in ABOVE:
                if m == '\u030c' and base in 'dlLt':
                    _caron_apostrophe(g, base)
                    continue
                ABOVE[m](g, x, y, case)
                y += size(p, case) + 0.6 * gap(p)
            elif m == '\u0327' and base in CEDILLA_AS_COMMA:
                if base == 'g':
                    commaabove(g, x, top + gap(p), case)
                else:
                    commabelow(g, x, 0, case)
            elif m == '\u0328':
                ogonek(g, _ogonek_x(g, base), 0, case)
            else:
                BELOW[m](g, x, 0, case)

    glyph(name, ch, spec.width, kind=spec.kind)(fn)


def _ogonek_x(g, base):
    p = g.p
    return g.W - p.sv / 2 if base in 'aeiouAEIOUy' else g.W / 2


def _caron_apostrophe(g, base):
    """The caron on d, l, L and t is written as an apostrophe beside the stem."""
    from .punct import _comma
    p = g.p
    top = p.cap if base == 'L' else (p.asc if base in 'dl' else p.cap)
    x = g.W + 0.5 * p.sv if base != 'L' else 0.55 * g.W
    _comma(g, None, x, top)
