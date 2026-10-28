"""The figures as the watch drew them: ss20, "Watch pixels".

Every figure in Arris grew from a 9 by 12 pixel master on the Dymaxion
Chamfer watch (``arris.heritage``). This stylistic set gives the masters
back: each lit pixel a square on the module grid, nothing chamfered, the
squares a little apart so the grid shows. Heavier weights light bigger
pixels (the gap closes from about two fifths of a module at Thin to a
twentieth at Black), always apart, so every weight has the same squares
for the variable font. Upright in the italic, as a display's pixels are.

The time colon between figures (calt's colon.tf) comes back as the watch
lights it too: two dots of 2 by 2 pixels on rows 3-4 and 8-9 of the
twelve (the watch's big clock, chamfer-numerals.js: colonTops 11 and 26,
colonWidth 6, at three pixels a module under a two-pixel cap top).
"""
from __future__ import annotations

from shapely.geometry import box

from .. import heritage
from ..draw import glyph
from .features import FIGS, _figure_side

FILL_THIN, FILL_BLACK, FILL_MAX = 0.6, 0.94, 0.96   # a pixel's side, as a share of the module


def _fill(p):
    from ..instances import STEMS
    sv = p.ungraded().sv
    t = min(max((sv - STEMS[100]) / (STEMS[900] - STEMS[100]), 0.0), 1.0)
    return min(FILL_MAX, (FILL_THIN + (FILL_BLACK - FILL_THIN) * t) * p.grade_k)


def pixel_figure(ch):
    def fn(g):
        p = g.p
        rows = heritage.zone(ch)
        u = p.cap / len(rows)                               # the module: twelve to the cap height
        s = _fill(p) * u
        x0 = (g.W - len(rows[0]) * u) / 2
        butt = []
        for r, row in enumerate(rows):
            for c, px in enumerate(row):
                if px != '#':
                    continue
                cx, cy = x0 + (c + 0.5) * u, p.cap - (r + 0.5) * u
                a, b, d, e = cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2
                g.extra.append(box(a, b, d, e))
                butt += [('x', a), ('x', d), ('y', b), ('y', e)]
        g.butt = tuple(dict.fromkeys(butt))                 # square corners: the corner rule leaves them
    return fn


PIXELS = [f'{n}.px' for n in FIGS]
for ch, n in zip('0123456789', FIGS):
    glyph(f'{n}.px', None, 'fig_w', cell=True)(pixel_figure(ch))


COLON_ROWS = (3, 4, 8, 9)                                   # lit rows of the twelve, from the cap's top


@glyph('colon.tf.px', None, lambda p: 2 * p.cap / 12, kind=('punct', _figure_side), cell=True)
def colon_pixels(g):
    """The watch's time colon in pixels: two dots of 2 x 2, the figures' squares."""
    p = g.p
    u = p.cap / 12
    s = _fill(p) * u
    x0 = (g.W - 2 * u) / 2
    butt = []
    for r in COLON_ROWS:
        for c in (0, 1):
            cx, cy = x0 + (c + 0.5) * u, p.cap - (r + 0.5) * u
            a, b, d, e = cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2
            g.extra.append(box(a, b, d, e))
            butt += [('x', a), ('x', d), ('y', b), ('y', e)]
    g.butt = tuple(dict.fromkeys(butt))
