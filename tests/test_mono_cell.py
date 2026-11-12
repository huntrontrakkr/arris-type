"""Arris Mono's cell, both ways, as the font carries the ink: a glyph's ink
stands a quarter module inside its 600-unit cell (draw.CELL_GAP), in the
italic as slanted. Until 1.015 the italic was fitted upright and leaned out
of its cell by its slant (31 units at the median in Mono Bold Italic); the
signs were fitted to a margin of a figure body that grows at Bold (№ ₠ ℘
∫ 7 to 10 units from their neighbours), a sign drawn to its body (©'s
ring) did not get smaller as it was drawn smaller, and a horn or ď's
apostrophe at Bold Italic ran out of the cell with its letter as narrow as
it goes. The tool for every glyph of every built font is
tools/mono_cell_check.py; this is a sample of each mechanism."""
from __future__ import annotations

import pytest

import arris.glyphs  # noqa: F401  (the registry)
from arris import draw as D
from arris.instances import mono_weight, params
from arris.italic import italic

SAMPLE = ['d', 'b', 'O', 'zero', 'three', 'Uhorn', 'ohorn', 'uni1EE8', 'dcaron', 'lcaron', 'uni1ED1',
          'numero', 'weierstrass', 'copyright', 'integral', 'uni222C', 'arrowupright', 'perthousand',
          'uni20AA', 'uni20AD', 'uni220C', 'uni2124']
SLACK = 2.0     # font units: the fit's own tolerance and a horn's measure of its letter at its floor


def _mono(w, ital):
    p = params(mono_weight(w)).with_(mono=True)
    return italic(p).with_(cursive=True) if ital else p


@pytest.mark.parametrize('ital', [False, True], ids=['upright', 'italic'])
@pytest.mark.parametrize('name', SAMPLE)
def test_ink_stands_inside_the_cell(name, ital):
    p = _mono(700, ital)
    g = D.draw(name, p)
    x0, x1 = D._ink_x(g, p)               # (as the font slants it: with its own parameters)
    c0 = (g.W - p.fig_adv) / 2
    gap = D.CELL_GAP * p.m
    assert x0 - c0 >= gap - SLACK and c0 + p.fig_adv - x1 >= gap - SLACK, (name, x0 - c0, c0 + p.fig_adv - x1)


@pytest.mark.parametrize('narrow', [False, True], ids=['mono', 'narrow'])
@pytest.mark.parametrize('w', [300, 400, 450, 500, 600, 700])
def test_the_y_with_a_dot_below_stands_in_its_cell(w, narrow):
    """The ỵ's dot stands beside its tail, and for it the letter is drawn
    narrower than the cell (draw._cell_fit). The y's hook is the g's
    (lower.hook_span: one hook for the two), and held at the g's span it did
    not narrow as its body did: in Arris Mono Narrow Italic the ỵ's ink
    began 4 units left of its cell at Retina and 21 at Bold. In the cell
    the hook gives with the body."""
    from arris.font import place
    from arris.geom import rings_to_shapely
    from arris.instances import narrow_weight
    from arris.italic import polylines
    p = params(narrow_weight(w) if narrow else mono_weight(w)).with_(mono=True, narrow=narrow)
    for q, ital in ((p, False), (italic(p).with_(cursive=True), True)):
        for name in ('y', 'uni1EF5'):
            rings, adv = place(name, q)
            x0, _, x1, _ = rings_to_shapely(polylines(rings) if ital else rings).bounds
            assert x0 >= -0.5 and x1 <= adv + 0.5, (name, ital, round(x0, 1), round(x1, 1))


def test_a_sign_drawn_smaller_is_drawn_smaller_whole():
    # ©'s ring is drawn to its body: drawn smaller to fit the italic's cell,
    # ring and letter shrink together, and its strokes are never a hairline
    p = _mono(700, True)
    g = D.draw('copyright', p)
    assert g.p.sv >= 0.4 * p.sv


def _side_cut(g):
    """Ink a drawing's own clip box cuts off at its sides, in stem-squares."""
    import shapely
    from shapely.geometry import box

    from arris.geom import stroke_polygon
    g = getattr(g, 'fit_src', (g,))[0]
    if not isinstance(g.clip, tuple):
        return 0.0
    th = D._thickness(g.p, g.sh)
    raw = shapely.union_all([stroke_polygon(st, th, g.p.c) for st in g.strokes] + list(g.extra))
    x0, y0, x1, y1 = g.clip
    side = raw.intersection(box(-1e4, y0, x0, y1)).area + raw.intersection(box(x1, y0, 1e4, y1)).area
    return side / (g.p.sv * g.p.sv)


@pytest.mark.parametrize('ital', [False, True], ids=['upright', 'italic'])
@pytest.mark.parametrize('name', ['uni20AA', 'prescription', 'uni221B', 'uni221C'])
def test_a_sign_is_cut_on_its_own_frame_not_its_body(name, ital):
    # laid out by its parameters (₪'s four stems and three gaps), a sign
    # clipped at its body lost what ran past it in Mono's narrower cell (₪'s
    # right stem, ℞'s crossing stroke, the roots' rise and bar), and the
    # cell's fit, measuring what was left, saw it fit
    assert _side_cut(D.draw(name, _mono(700, ital))) < 0.05
