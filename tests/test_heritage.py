"""The engine at heritage parameters reproduces the watch's Chamfer figures."""
import json

import numpy as np
from shapely import contains_xy

import arris.glyphs.figures  # noqa: F401
from arris import heritage
from arris.draw import draw
from arris.geom import rings_to_shapely
from arris.params import HERITAGE

NAMES = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine']
# Every figure but the 7 is the zone master under the Chamfer rule, exactly;
# the 7 is the watch's straightened seven (its zone master's leg wobbles).
EXACT = set(NAMES) - {'seven'}


def watch_mask(poly, k=3, ss=8):
    """The watch's own sampler: 8x8 samples per pixel, ink if half are inside."""
    xs = (np.arange(27 * ss) + 0.5) / ss / k
    ys = 12 - (np.arange(36 * ss) + 0.5) / ss / k
    X, Y = np.meshgrid(xs, ys)
    inside = contains_xy(poly, X, Y).reshape(36, ss, 27, ss).sum(axis=(1, 3))
    return (inside * 2 >= ss * ss).astype(np.uint8)


def test_vector_trace_matches():
    for i, n in enumerate(NAMES):
        if n not in EXACT:
            continue
        new = rings_to_shapely(draw(n, HERITAGE).rings())
        old = heritage.trace(heritage.zone(str(i)))
        assert new.symmetric_difference(old).area < 1e-9, n


def test_watch_pixels_match():
    masters = json.loads((heritage.ROOT / 'heritage' / 'chamfer-clock.json').read_text())
    for i, n in enumerate(NAMES):
        mask = watch_mask(rings_to_shapely(draw(n, HERITAGE).rings()))
        ref = np.array([(masters[i][j >> 3] >> (j & 7)) & 1 for j in range(27 * 36)], np.uint8).reshape(36, 27)
        assert int((mask != ref).sum()) == 0, n


def test_shipped_watch_semibold_is_the_watch():
    """Arris Watch SemiBold, through the same instance pipeline the fonts are
    built with, rasterises to the watch's masters: 60 units per module, 3 px
    per module."""
    from shapely import affinity

    from arris.instances import HERITAGE_OPTICS, params
    p = params(600, optics=HERITAGE_OPTICS)
    masters = json.loads((heritage.ROOT / 'heritage' / 'chamfer-clock.json').read_text())
    for i, n in enumerate(NAMES):
        ink = affinity.scale(rings_to_shapely(draw(n, p).rings()), 1 / 60, 1 / 60, origin=(0, 0))
        ref = np.array([(masters[i][j >> 3] >> (j & 7)) & 1 for j in range(27 * 36)], np.uint8).reshape(36, 27)
        assert int((watch_mask(ink) != ref).sum()) == 0, n


def test_watch_axis_at_100_is_the_watch():
    """The variable font's Watch axis at 100, SemiBold, draws the same figures."""
    from shapely import affinity

    from arris.instances import params
    p = params(600, watch=1.0)
    masters = json.loads((heritage.ROOT / 'heritage' / 'chamfer-clock.json').read_text())
    for i, n in enumerate(NAMES):
        ink = affinity.scale(rings_to_shapely(draw(n, p).rings()), 1 / 60, 1 / 60, origin=(0, 0))
        ref = np.array([(masters[i][j >> 3] >> (j & 7)) & 1 for j in range(27 * 36)], np.uint8).reshape(36, 27)
        assert int((watch_mask(ink) != ref).sum()) == 0, n


def test_pixel_colon_is_the_watch_colon():
    """ss20's time colon lights the watch's colon pixels: two columns, rows
    3-4 and 8-9 of the twelve from the cap's top, and nothing else."""
    import arris.glyphs.origin  # noqa: F401
    from shapely.geometry import Point
    g = draw('colon.tf.px', HERITAGE)
    ink = rings_to_shapely(g.rings())
    u = HERITAGE.cap / 12
    x0 = (g.W - 2 * u) / 2
    lit = {(r, c) for r in range(12) for c in range(2)
           if ink.contains(Point(x0 + (c + 0.5) * u, HERITAGE.cap - (r + 0.5) * u))}
    assert lit == {(r, c) for r in (3, 4, 8, 9) for c in (0, 1)}
