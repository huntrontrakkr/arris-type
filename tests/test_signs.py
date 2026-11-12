"""The signs that stand in text beside the letters, as 1.017 leaves them:
the percent's rings clear of its slash, the number sign's ends longer than
its strokes are thick, the straight quotes a third of the cap height."""
from __future__ import annotations

import pytest
from shapely.geometry import LineString

import arris.glyphs  # noqa: F401  (the registry)
from arris.draw import draw
from arris.geom import rings_to_shapely
from arris.glyphs.punct import pct, tick
from arris.instances import params


def _ink(name, p):
    return rings_to_shapely(draw(name, p).rings())


def _runs(ink, x=None, y=None):
    x0, y0, x1, y1 = ink.bounds
    line = LineString([(x, y0 - 10), (x, y1 + 10)]) if x is not None else LineString([(x0 - 10, y), (x1 + 10, y)])
    cut = ink.intersection(line)
    i = 1 if x is not None else 0
    return sorted((g.bounds[i], g.bounds[i + 2]) for g in getattr(cut, 'geoms', [cut]) if g.length > 0.5)


@pytest.mark.parametrize('w', [100, 300, 400, 700, 900])
def test_the_percents_rings_stand_clear_of_its_slash(w):
    """Three pieces, each ring the least white from the slash and open:
    until 1.017 one piece at every weight (50% read as 5096), its counters
    0.66 of a stem at Black."""
    p = params(w)
    parts = list(_ink('percent', p).geoms)
    assert len(parts) == 3
    slash = max(parts, key=lambda q: q.bounds[3] - q.bounds[1])
    vs, _, _, rw, _, white = pct(p)
    for ring in parts:
        if ring is slash:
            continue
        assert 0.95 * white <= ring.distance(slash) <= 1.3 * white
        assert len(ring.interiors) == 1
        assert rw - 2 * vs >= white - 0.5                   # the counter, across


@pytest.mark.parametrize('w', [400, 700, 800, 900])
def test_the_number_signs_ends_are_longer_than_its_strokes(w):
    """A stroke and a half past the bars up and down, and the square
    between them a stroke at least (at the watch's Black the ends were two
    thirds of a stroke: a cross with a hole in it). Across, what the body
    holds: a stroke and a half at Regular and at Black, least where the
    sign's strokes begin to thin, 1.17 at Bold."""
    p = params(w)
    ink = _ink('numbersign', p)
    x0, y0, x1, y1 = ink.bounds
    (hole,) = ink.interiors
    hx0, hy0, hx1, hy1 = hole.bounds
    bars = _runs(ink, x=x0 + (hx0 - x0) / 4)                # through the bars' left ends
    stems = _runs(ink, y=y0 + (hy0 - y0) / 4)               # through the stems' feet
    assert len(bars) == 2 and len(stems) == 2
    th, tv = bars[0][1] - bars[0][0], stems[0][1] - stems[0][0]
    assert tv <= p.sv + 0.5
    assert bars[0][0] - y0 >= 1.45 * th and y1 - bars[1][1] >= 1.45 * th
    assert stems[0][0] - x0 >= 1.15 * tv and x1 - stems[1][1] >= 1.15 * tv      # (1.17 at Bold, 1.32 at ExtraBold)
    assert hy1 - hy0 >= th - 0.5 and hx1 - hx0 >= tv - 0.5


@pytest.mark.parametrize('w', [300, 400, 700, 900])
def test_a_straight_quote_is_a_third_of_the_cap_height(w):
    """Or two dots, where those are more (they were two dots at every
    weight, a quarter of the cap height at Regular: 0.31 to 0.36 in faces
    of this kind); and the double quote's ticks stand about a tick apart,
    not a tick and a half."""
    p = params(w)
    one = _ink('quotesingle', p)
    assert one.bounds[3] - one.bounds[1] == pytest.approx(tick(p), abs=1.0)
    assert tick(p) >= p.cap / 3 - 0.5
    two = list(_ink('quotedbl', p).geoms)
    assert len(two) == 2
    a, b = sorted(two, key=lambda q: q.bounds[0])
    from arris.params import WHITE_HELD
    # (the white between the two, of no more stem than the least white grows with: params.white_floor)
    assert 0.55 * min(p.sv, WHITE_HELD) <= b.bounds[0] - a.bounds[2] <= 1.2 * max(p.sv, 1.5 * p.m)


@pytest.mark.parametrize('w', [300, 400, 700, 900])
def test_the_ring_is_a_third_of_the_cap_height_at_most(w):
    """0.25 of it at Light, 0.30 at Regular, 0.33 from Bold (faces of this kind: 0.26 to
    0.36), its stroke 0.7 of the stem at most; and Å no taller than a cap
    height and a half (it stood 1.47 to 1.60, into the line above)."""
    p = params(w)
    parts = sorted(_ink('Aring', p).geoms, key=lambda q: q.bounds[1])
    ring = parts[-1]
    x0, y0, x1, y1 = ring.bounds
    assert 0.24 * p.cap <= y1 - y0 <= 0.36 * p.cap and x1 - x0 == pytest.approx(y1 - y0, abs=2.0)
    (hole,) = ring.interiors
    assert (x1 - x0 - (hole.bounds[2] - hole.bounds[0])) / 2 <= 0.72 * p.sv
    assert y1 <= 1.45 * p.cap and len(parts) == 2


def test_a_row_of_strokes_gives_way_a_gap_at_a_time():
    """punct.spread: a gap that is short takes what it lacks from the
    others, by their shares of what they have over; all short, they stand
    evenly; none short, nothing moves."""
    from arris.glyphs.punct import spread
    assert spread([0, 40, 80, 120], 30) == [0, 40, 80, 120]
    assert spread([0, 20, 80, 120], 30) == pytest.approx([0, 30, 82.5, 120])      # 10 taken: 7.5 of the 30 over, 2.5 of the 10
    assert spread([0, 10, 20, 90], 30) == pytest.approx([0, 30, 60, 90])
    assert spread([0, 5, 50, 60], 30) == pytest.approx([0, 20, 40, 60])           # no room for all: even
    for t in range(41):                                                          # and it goes steadily as a gap closes
        a, b = spread([0, 40 - t, 80, 120], 30), spread([0, 39 - t, 80, 120], 30)
        assert all(abs(x - y) <= 1.0 + 1e-9 for x, y in zip(a, b, strict=True))


def test_the_at_signs_a_moves_by_steps_no_longer():
    """Four uprights cross the at sign and four bars stack up it; where one
    white ran short the whole row used to go even at once. At Medium the
    inner a stood 60 units higher in its ring than at Regular or SemiBold,
    and along the grade the sign changed by a hundred squares of an edge
    break in one step of a twentieth (the grade axis, gone across step by
    step). Each white takes what it lacks from the others now
    (punct.spread). What still moves the a's foot is the thinning of the
    sign's bars for its counter (draw's automatic counters), 31 units
    between SemiBold and 650. (At Medium it stood at 254 units for the
    Regular's 179 and the SemiBold's 180.)"""
    from itertools import pairwise

    def foot(w, g=0):                                       # the inner a's lower bar, on its centre line
        return draw('at', params(w, g)).strokes[0].nodes[0].y
    by_weight = [foot(w) for w in range(300, 901, 50)]
    # (44 units between Medium and 550 on the ladder whose Bold and Black are other families' own: the same
    # thinning, a step of weight the heavier)
    assert max(abs(b - a) for a, b in pairwise(by_weight)) < 45, [round(v) for v in by_weight]
    by_grade = [foot(500, g) for g in range(-100, 101, 10)]
    assert max(abs(b - a) for a, b in pairwise(by_grade)) < 25, [round(v) for v in by_grade]
