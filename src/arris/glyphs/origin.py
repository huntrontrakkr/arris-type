"""The figures as the watch drew them: ss20, "Watch pixels".

Every figure in Arris grew from a 9 by 12 pixel master on the Dymaxion
Chamfer watch (``arris.heritage``). This stylistic set gives the masters
back: each lit pixel a square on the module grid, nothing chamfered, the
squares a little apart so the grid shows. Heavier weights light bigger
pixels (the gap closes from about two fifths of a module at Thin to a
twentieth at Black), always apart, so every weight has the same squares
for the variable font. Upright in the italic, as a display's pixels are.
"""
from __future__ import annotations

from shapely.geometry import box

from .. import heritage
from ..draw import glyph
from .features import FIGS

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
