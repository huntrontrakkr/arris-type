"""The g's hook: as heavy as the letter's other horizontals, with a module
of white (or 0.6 of a stem) between hook and bowl, on the weight's
descender line with p q j and the y's tail (params.descender_line,
lower.hook_fit), and ended in a beak. Until 1.016 it thinned first, and
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


@pytest.mark.parametrize('w', [200, 300, 400, 500, 600, 700, 800, 900])
def test_the_ys_tail_is_its_right_arm_run_on(w):
    """The v's body, and its right arm run on at 45 degrees to the
    descender line, ended square to its own line and inside the body: one
    piece, every edge upright, level or at 45 degrees (within the few
    degrees the raised optical centre turns a diagonal)."""
    import math

    from shapely.geometry import box
    p = params(w)
    flat = p.with_(optical=0.0)                         # the drawings themselves, before the optical centre is raised
    yi, vi = (rings_to_shapely(draw(ch, flat).rings()) for ch in 'yv')
    over = box(-10, p.sv, 5000, 5000)
    assert yi.intersection(over).symmetric_difference(vi.intersection(over)).area < 2.0
    y = draw('y', p)
    yi = rings_to_shapely(y.rings())
    assert len(y.rings()) == 1
    assert yi.bounds[0] >= -0.5 and yi.bounds[1] == pytest.approx(-p.desc, abs=0.5)
    for ring in y.rings():
        for a, b in zip(ring, ring[1:] + ring[:1]):
            if math.dist(a, b) > 1.0:
                turn = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 45
                assert min(turn, 45 - turn) < 3.0, (a, b)


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
