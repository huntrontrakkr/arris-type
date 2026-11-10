"""The g's hook: as heavy as the letter's other horizontals, with a module
of white (or 0.6 of a stem) between hook and bowl, on the weight's
descender line with p q and j (params.descender_line, lower.hook_fit),
ended in a beak, and the y's too. Until 1.016 it thinned first, and
from Light up it was about three quarters of the bowl's strokes; and it
went deeper alone from Bold."""
from __future__ import annotations

import pytest
from shapely.geometry import LineString

import arris.glyphs  # noqa: F401  (the registry)
from arris.draw import draw
from arris.geom import rings_to_shapely
from arris.glyphs.letterframe import least_white
from arris.glyphs.lower import BEAK_WHITE, hook_fit
from arris.instances import params


def _bars(name, p):
    """The glyph's horizontals cut by a plumb line left of its middle: (bottom, thickness) from the lowest up."""
    g = draw(name, p)
    ink = rings_to_shapely(g.rings())
    x0, y0, x1, y1 = ink.bounds
    x = x0 + 0.42 * (x1 - x0)
    cut = ink.intersection(LineString([(x, y0 - 10), (x, y1 + 10)]))
    return sorted((s.bounds[1], s.length) for s in getattr(cut, 'geoms', [cut]) if s.length > 1)


@pytest.mark.parametrize('w', [100, 300, 400, 500, 600, 700, 800, 900])
def test_the_gs_hook_is_as_heavy_as_its_bowl(w):
    p = params(w)
    (y_hook, hook), (y_foot, foot), (_, top) = _bars('g', p)
    assert hook == pytest.approx(foot, abs=0.5) and foot == pytest.approx(top, abs=0.5)
    assert y_foot - (y_hook + hook) >= least_white(p) - 0.5        # the white from hook to bowl


@pytest.mark.parametrize('w', [300, 400, 500, 600, 700, 800, 900])
def test_the_gs_hook_ends_in_a_beak(w):
    """The hook is cut at both ends, as the top of the 8 is: at its left a
    cut corner and a short terminal turned up, as the c's arms end. The
    terminal rises over the hook, and keeps three quarters of the least
    white under the bowl."""
    p = params(w)
    ink = rings_to_shapely(draw('g', p).rings())
    (y_hook, hook), *_ = _bars('g', p)

    def column(x):
        cut = ink.intersection(LineString([(x, -1000), (x, p.xh / 2)]))
        return sorted((s.bounds[1], s.bounds[3]) for s in getattr(cut, 'geoms', [cut]) if s.length > 1)
    tip = column(p.sv / 2)[0][1]
    assert tip >= y_hook + hook + 0.8 * p.c, (tip, y_hook + hook)
    for x in (p.sv / 2, p.sv - 1.0):                    # the white over it, to the bowl's cut corner
        runs = column(x)
        assert runs[1][0] - runs[0][1] >= BEAK_WHITE * least_white(p) - 1.0, (x, runs)


@pytest.mark.parametrize('w', [300, 400, 700, 900])
def test_the_y_stands_on_the_gs_hook(w):
    """The same hook, bar for bar (the owner: "make a g like it is
    today")."""
    p = params(w)
    assert _bars('y', p)[0] == pytest.approx(_bars('g', p)[0], abs=0.5)


@pytest.mark.parametrize('w', [100, 300, 400, 500, 600, 700])
def test_the_ys_foot_is_as_long_as_the_top_of_the_ms_arch(w):
    """The flat between its arm and its join, along the baseline, against
    the flat on top of the m's last arch, along the x-height (the owner:
    "measuring the top of the m and making the flat part that long")."""
    p = params(w)

    def runs(name, y):
        ink = rings_to_shapely(draw(name, p).rings())
        cut = ink.intersection(LineString([(-1e4, y), (1e4, y)]))
        return sorted((s.bounds[0], s.bounds[2]) for s in getattr(cut, 'geoms', [cut]) if s.length > 1)
    m, foot = runs('m', p.xh - 0.5)[-1], runs('y', 0.5)[0]
    assert foot[1] - foot[0] == pytest.approx(m[1] - m[0], abs=1.5)


def test_the_hook_keeps_its_weight_on_the_descender_line():
    for w in range(100, 901, 50):
        p = params(w)
        for sh in (p.sh, p.sh * p.low):                 # the italic's horizontals, and the upright lowercase's
            thick, extra = hook_fit(p, sh)
            assert extra == 0 and (thick == pytest.approx(sh) or p.desc == p.deep), w


def _lowest(name, p):
    return min(y for r in draw(name, p).rings() for _, y in r)


@pytest.mark.parametrize('w', [300, 400, 600, 700, 800, 900])
def test_every_descender_stands_on_one_line(w):
    """g j p q y: one depth a weight, three modules to SemiBold and deeper
    from there, never past the font's descent."""
    p = params(w)
    depths = {n: _lowest(n, p) for n in 'gjpqy'}
    assert max(depths.values()) - min(depths.values()) < 0.5, depths
    assert depths['p'] == pytest.approx(-p.desc, abs=0.5) and 180 <= p.desc <= p.deep == 250
