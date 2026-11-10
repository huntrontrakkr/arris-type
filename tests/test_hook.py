"""The hooks of g and y: as heavy as the letter's other horizontals, with a
module of white (or 0.6 of a stem) between hook and bowl, deepening into
the font's descent before they thin (lower.hook_fit). Until 1.016 they
thinned first, and from Light up the hook was about three quarters of the
bowl's strokes."""
from __future__ import annotations

import pytest
from shapely.geometry import LineString

import arris.glyphs  # noqa: F401  (the registry)
from arris.draw import draw
from arris.geom import rings_to_shapely
from arris.glyphs.letterframe import least_white
from arris.glyphs.lower import HOOK_ROOM, hook_fit
from arris.instances import params


def _bars(name, p):
    """The glyph's horizontals cut by a plumb line left of its middle: (bottom, thickness) from the lowest up."""
    g = draw(name, p)
    ink = rings_to_shapely(g.rings())
    x0, y0, x1, y1 = ink.bounds
    x = x0 + 0.42 * (x1 - x0)
    cut = ink.intersection(LineString([(x, y0 - 10), (x, y1 + 10)]))
    return sorted((s.bounds[1], s.length) for s in getattr(cut, 'geoms', [cut]) if s.length > 1)


@pytest.mark.parametrize('w', [100, 300, 400, 500, 600, 700, 800])
def test_the_gs_hook_is_as_heavy_as_its_bowl(w):
    p = params(w)
    (y_hook, hook), (y_foot, foot), (_, top) = _bars('g', p)
    assert hook == pytest.approx(foot, abs=0.5) and foot == pytest.approx(top, abs=0.5)
    assert y_foot - (y_hook + hook) >= least_white(p) - 0.5        # the white from hook to bowl


@pytest.mark.parametrize('w', [400, 700, 900])
def test_the_ys_hook_is_the_gs(w):
    p = params(w)
    assert _bars('y', p)[0] == pytest.approx(_bars('g', p)[0], abs=0.5)


def test_the_hook_deepens_before_it_thins():
    for w in range(100, 901, 50):
        p = params(w)
        thick, extra = hook_fit(p, p.sh)
        assert thick == pytest.approx(p.sh) or extra == pytest.approx(HOOK_ROOM), w
        assert thick >= 0.95 * p.sh, w
    assert hook_fit(params(600), params(600).sh)[1] == 0            # at the descender's own depth to SemiBold
