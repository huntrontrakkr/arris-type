"""The nesting check (arris.steady): a heavier counter lies inside a lighter one."""
from shapely.geometry import box

from arris import steady


def _square(x0, y0, x1, y1):
    return box(x0, y0, x1, y1)


def test_eroded_counter_is_nested():
    """A counter whose sides all move in (a stroke growing round it), moved
    as a whole as the body widens: nested."""
    light = _square(100, 100, 400, 500)
    heavy = _square(130, 120, 410, 470)            # eroded by 10-20 units each side, then shifted 20 right
    far, _ = steady._fit(light, heavy)
    assert far <= steady.SPILL


def test_counter_that_grows_one_way_spills():
    """A counter that shrinks overall but reaches out on one side (a loop
    dropped to keep it open, a notch opening into a slot): it spills."""
    light = _square(100, 100, 400, 500)
    heavy = _square(140, 60, 360, 470).union(_square(200, 60, 260, 470))   # 40 units lower at the bottom
    far, _ = steady._fit(light, heavy.convex_hull)
    assert far > steady.SPILL


def test_faults_along_a_line():
    """Counters paired by key along the weight: one opening where the
    lighter weight has none is faulted too."""
    weights = [100, 110, 120]
    series = [[(0, _square(0, 0, 100, 100))],
              [(0, _square(5, 5, 95, 95))],
              [(0, _square(10, 10, 90, 90)), (1, _square(200, 0, 260, 60))]]
    faults = steady._faults_along(series, weights, 0, 0)
    assert [f.kind for f in faults] == ['opens']
