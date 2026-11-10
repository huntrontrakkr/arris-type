"""How the letters stand together (1.017): every letter keeps its share of
the line as weight is added, open sides are spaced as hand-spaced faces
space them, the open letters share one terminal and one balance of
storeys, and the corners of the D are the O's."""
from __future__ import annotations

import pytest
from shapely.geometry import LineString

import arris.glyphs  # noqa: F401  (the registry)
from arris.draw import OPTICAL, REGISTRY, draw
from arris.font import place
from arris.geom import rings_to_shapely
from arris.instances import params

CMAP = {chr(s.unicode): n for n, s in REGISTRY.items() if s.unicode}


def _ink(ch, p):
    return rings_to_shapely(draw(CMAP[ch], p).rings())


def _width(ch, p):
    x0, _, x1, _ = _ink(ch, p).bounds
    return x1 - x0


@pytest.mark.parametrize('ch', list('EFKLTZ'))
def test_a_one_stem_capital_keeps_its_share_of_the_line(ch):
    """Regular to Black the H grows a fifth; a letter with one stem grows
    with it (hand-drawn faces: 0.93 to 1.08 of its share; until 1.017 0.80
    to 0.84)."""
    share = lambda w: _width(ch, params(w)) / _width('H', params(w))
    assert share(900) / share(400) >= 0.9, ch


@pytest.mark.parametrize('ch', list('fktz'))
def test_a_one_stem_lowercase_letter_keeps_its_share(ch):
    share = lambda w: _width(ch, params(w)) / _width('n', params(w))
    assert share(900) / share(400) >= 0.9, ch


@pytest.mark.parametrize('w', [100, 300, 400, 600, 900])
def test_the_r_is_two_thirds_of_the_h(w):
    """One share of the H at every weight: at Thin it was a third wider
    than the n, and at eight ninths still the lightest letter of the
    alphabet, its advance 0.94 of the n's where faces of this kind give
    the r 0.62 to 0.72. Six ninths (the owner, twice: a module off the
    arm)."""
    p = params(w)
    assert REGISTRY['r'].width(p) == pytest.approx(6 / 9 * REGISTRY['H'].width(p))
    assert _width('r', p) <= 0.9 * _width('n', p)


@pytest.mark.parametrize('w', [300, 400, 700, 900])
def test_v_and_w_hang_a_break_under_the_line(w):
    """Their points hang one edge break under the baseline and end blunt,
    more than a break wide (until 1.017: 1.7 breaks down to a flat of
    0.9; then, for a while, cut on the line)."""
    p = params(w)
    for ch in 'vw':
        ink = _ink(ch, p)
        assert ink.bounds[1] == pytest.approx(-p.c, abs=1), ch
        foot = ink.intersection(LineString([(-50, -p.c + 0.5), (2000, -p.c + 0.5)]))
        flats = [s.length for s in getattr(foot, 'geoms', [foot])]
        assert len(flats) == (1 if ch == 'v' else 2) and min(flats) >= 1.2 * p.c, (ch, flats)


def _whites(ch, p, at=0.5):
    """The whites a plumb line through the letter crosses, from the bottom up."""
    ink = _ink(ch, p)
    x0, y0, x1, y1 = ink.bounds
    x = x0 + at * (x1 - x0)
    cut = ink.intersection(LineString([(x, y0 - 10), (x, y1 + 10)]))
    runs = sorted((s.bounds[1], s.bounds[3]) for s in getattr(cut, 'geoms', [cut]) if s.length > 1)
    return [b[0] - a[1] for a, b in zip(runs, runs[1:])]


@pytest.mark.parametrize('w', [300, 400, 700, 900])
def test_the_open_storey_of_a_and_e(w):
    """The a, e and s stack their three bars with one white, and the optical
    centre raises the middle: the a's open storey is seven eighths of its
    bowl, the e's a seventh more than its bowl (until 1.017 both two
    thirds, the a's the tighter)."""
    p = params(w)
    r = OPTICAL['counters']
    bowl, upper = _whites('a', p)
    assert upper / bowl == pytest.approx(r, abs=0.08)
    lower, bowl = _whites('e', p)
    assert bowl / lower == pytest.approx(r, abs=0.08)
    lower, upper = _whites('s', p)
    assert upper / lower == pytest.approx(r, abs=0.08)


@pytest.mark.parametrize('w', [300, 400, 700])
def test_a_c_e_s_end_in_one_terminal(w):
    """Each open end turns through a cut corner into the c's beak: the a's
    arm, the e's arm and both ends of the s reach as far from their lines
    as the c's do."""
    p = params(w)

    def reach(ch, top, right):
        ink = _ink(ch, p)
        x0, y0, x1, y1 = ink.bounds
        x = x1 - 1 if right else x0 + 1
        cut = ink.intersection(LineString([(x, y0 - 10), (x, y1 + 10)]))
        runs = sorted((s.bounds[1], s.bounds[3]) for s in getattr(cut, 'geoms', [cut]) if s.length > 1)
        lo, hi = runs[-1] if top else runs[0]
        return hi - lo

    c = reach('c', True, True)
    for ch, top, right in (('a', True, False), ('e', False, True), ('s', True, True), ('s', False, False)):
        assert reach(ch, top, right) == pytest.approx(c, abs=0.12 * c), (ch, top)


@pytest.mark.parametrize('w', [400, 700, 900])
def test_the_ds_corners_are_the_os(w):
    p = params(w)

    def cut(ch):                              # how far in from its right side the letter's top edge starts
        ink = _ink(ch, p)
        x0, y0, x1, y1 = ink.bounds
        top = ink.intersection(LineString([(x0 - 10, y1 - 2), (x1 + 10, y1 - 2)]))
        return x1 - max(s.bounds[2] for s in getattr(top, 'geoms', [top]))

    assert cut('D') == pytest.approx(cut('O'), abs=3)


@pytest.mark.parametrize('w', [400, 700])
def test_dock_is_one_word(w):
    """The white between O and C, and between C and K: until 1.017 the C
    stood 79 units from the K and 141 from the O at Regular, and the word
    read DO CK."""
    p = params(w)

    def gap(a, b):
        ra, adv = place(CMAP[a], p)
        rb, _ = place(CMAP[b], p)
        return adv - max(x for r in ra for x, _ in r) + min(x for r in rb for x, _ in r)

    assert gap('C', 'K') >= 0.75 * gap('O', 'C')
    assert gap('D', 'O') == pytest.approx(gap('O', 'C'), rel=0.1)


@pytest.mark.parametrize('w', [300, 400, 700, 900])
def test_the_1_stands_on_its_stem(w):
    """A stem and a flag: at the baseline the 1 is as wide as its stem. In
    Arris Mono it keeps a foot."""
    p = params(w)
    foot = lambda q: rings_to_shapely(draw('one', q).rings()).intersection(
        LineString([(-500, q.sh / 2), (1500, q.sh / 2)])).length
    assert foot(p) == pytest.approx(p.sv, abs=1)
    assert foot(p.with_(mono=True)) > 2 * p.sv or w > 700


@pytest.mark.parametrize('w', [300, 400])
def test_the_x_steps_as_the_capital_does(w):
    """One drawing for X and x: at the light weights both step at the
    crossing (the 2's notch), and both lose the step as they grow."""
    p = params(w)
    points = lambda ch: sum(len(r) for r in draw(CMAP[ch], p).rings())
    assert points('x') == points('X')


@pytest.mark.parametrize('w', [400, 700, 900])
def test_no_join_is_thicker_than_a_crossing(w):
    """The largest disk that fits a letter's ink, in its heaviest strokes
    (tools/stroke_audit.py): a T is 1.45 with its corners broken, a bar
    across a stem 1.7 (t f 4), and no join a diagonal makes with a stem is
    over a T's (K k M R Q 1: 1.5 to 1.6 until 1.017, the crotch filled two
    breaks deep)."""
    from shapely import maximum_inscribed_circle

    from arris.draw import _heaviest_stroke
    p = params(w)

    def bloat(ch):
        g = draw(CMAP[ch], p)
        ink = rings_to_shapely(g.rings())
        d = 0.0
        for part in getattr(ink, 'geoms', [ink]):
            r = maximum_inscribed_circle(part, tolerance=0.5)
            (cx, cy), (ex, ey) = r.coords[0], r.coords[-1]
            d = max(d, 2 * ((cx - ex) ** 2 + (cy - ey) ** 2) ** 0.5)
        return d / _heaviest_stroke(g, p)

    for ch in 'KkMRQNY1':
        assert bloat(ch) <= 1.52, (ch, round(bloat(ch), 2))
    for ch in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789':
        assert bloat(ch) <= 1.75, (ch, round(bloat(ch), 2))


@pytest.mark.parametrize('w', [800, 900])
def test_the_arch_of_n_is_its_bar(w):
    """The n's counter ends under the arch's own bar, flat from corner to
    corner: until 1.017 the shoulder's cut hung under it (the arch a third
    thicker over half the counter) and the counter came to a point beside
    it."""
    p = params(w)
    g = draw('n', p)
    ink = rings_to_shapely(g.rings())
    x0, x1 = p.sv + 1.6 * p.c, g.W - p.sv - 1.6 * p.c      # the counter, inside its corners' breaks
    for at in (0.0, 0.25, 0.5, 0.75, 1.0):
        x = x0 + at * (x1 - x0)
        cut = ink.intersection(LineString([(x, -10), (x, p.xh + 10)]))
        assert cut.bounds[1] == pytest.approx(p.xh - g.sh, abs=1.5), (w, at)


@pytest.mark.parametrize('w', [400, 600, 700, 900])
def test_the_m_stands_on_three_whole_stems(w):
    """Each of the m's counters is broken alike at its two top corners:
    the second's, on the middle stem, was a 9-unit facet at Black."""
    p = params(w)
    ink = rings_to_shapely(draw('m', p).rings())
    x0, _, x1, _ = ink.bounds
    stems = sorted({round(s.bounds[0]) for s in ink.intersection(LineString([(x0 - 5, p.xh / 3), (x1 + 5, p.xh / 3)])).geoms})
    whites = []
    for xs in stems[:2]:                                    # just inside each counter's left corner
        x = xs + p.sv + 0.5 * p.c
        whites.append(ink.intersection(LineString([(x, 1), (x, p.xh + 10)])).bounds[1])
    assert whites[0] == pytest.approx(whites[1], abs=1.5)


@pytest.mark.parametrize('w', [100, 400, 700, 900])
def test_the_j_is_an_arm_a_stem_and_a_hook(w):
    """One stroke: nothing right of the stem, an arm left of it at the cap
    height at least a stem long from SemiBold, and between arm and hook the
    bare stem."""
    p = params(w)
    ink = rings_to_shapely(draw('J', p).rings())
    x0, y0, x1, y1 = ink.bounds
    across = lambda y: ink.intersection(LineString([(x0 - 10, y), (x1 + 10, y)]))
    assert across(p.cap / 2).length == pytest.approx(p.sv, abs=1)
    assert across(p.cap / 2).bounds[2] == pytest.approx(x1, abs=1)        # the stem is the letter's right side
    arm = across(p.cap - p.sh / 2)
    assert arm.bounds[2] == pytest.approx(x1, abs=1)
    assert arm.length - p.sv >= min(p.sv, 0.3 * (x1 - x0)) - 1


def test_a_crotch_with_a_step_in_it_keeps_its_leg():
    """A diagonal that lands on a short edge square to the bar it runs
    into: the chord keeps a break's leg on the bar and runs square to the
    diagonal (until 1.017 it was no longer than the step: the Z's foot at
    Black, 9 units for 44). With a step a break long it is the right
    angle's own chord; the watch's rule (crotch 2) is as it was."""
    from arris.geom import _ring_rule

    def ring(v):                                            # a bar, a step v tall at x = 120, a diagonal off it
        pts = [(0, 0), (400, 0), (400, 100), (120, 100), (120, 100 + v), (400, 380 + v), (400, 460 + v), (0, 460 + v)]
        return pts + pts[:1]

    def near(pts, q):
        return any(abs(x - q[0]) < 1e-6 and abs(y - q[1]) < 1e-6 for x, y in pts)

    out = _ring_rule(ring(10), 40, +1, crotch=1.0)
    assert near(out, (160, 100)) and near(out, (135, 125))
    assert not near(out, (120, 100)) and not near(out, (120, 110))
    out = _ring_rule(ring(0.5), 40, +1, crotch=1.0)          # all but no step: the crotch's own chord
    assert near(out, (160, 100)) and near(out, (120 + 39.5 / 2, 100.5 + 39.5 / 2))
    out = _ring_rule(ring(40), 40, +1, crotch=1.0)           # a full step: the right angle's
    assert near(out, (160, 100)) and near(out, (120, 140))
    out = _ring_rule(ring(10), 40, +1, crotch=2.0)           # the pixel rule
    assert near(out, (130, 100)) and near(out, (120, 110))


@pytest.mark.parametrize('w', [700, 800, 900])
def test_the_zs_foot_is_broken_a_full_break(w):
    p = params(w)
    g = draw('Z', p)
    ring = max(g.rings(), key=len)
    on_bar = [x for x, y, *_ in ring if abs(y - g.sh) < 1 and x < g.W / 2]     # where the foot's inner corner starts on the bar
    assert max(on_bar) - p.sv == pytest.approx(p.c, abs=1.5)                   # a break from the foot's own side


@pytest.mark.parametrize('w', [300, 400, 700, 900])
def test_wide_and_narrow_letters_stand_where_such_faces_put_them(w):
    """Advances against the n's and the H's, inside what chamfered and
    squared faces give them (Chakra Petch, Oxanium, Rajdhani, Exo 2,
    Tomorrow, Share Tech at Regular and at their heaviest): the m 1.44 to
    1.59 of the n (it was 1.36, the darkest arch letter), the w 1.23 to
    1.54 (1.46 at Regular, wider than any), the M 1.14 to 1.33 and the W
    1.07 to 1.42 of the H, the T 0.79 to 0.84 (0.98)."""
    p = params(w)
    adv = lambda ch: place(CMAP[ch], p)[1]
    assert 1.42 <= adv('m') / adv('n') <= 1.59
    assert 1.23 <= adv('w') / adv('n') <= 1.42
    assert 1.12 <= adv('M') / adv('H') <= 1.33
    assert 1.07 <= adv('W') / adv('H') <= 1.42
    assert 0.76 <= adv('T') / adv('H') <= 0.86


LATIN = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'


@pytest.mark.parametrize('w', [300, 400, 500, 600, 700, 800, 900])
def test_no_letter_keeps_a_crumb(w):
    """No edge of a letter or figure is shorter than half an edge break, at
    any named weight (0.45 of one: the v's flank at Black is 0.48). Until
    1.017 twenty-two of the sixty-two kept one at some weight: the wall of
    a counter between its corners' cuts (a e s B G 3 5 6 8 9), the flat
    under a bar's stub between its two cuts (f t l 4), the flat the X's
    step left in its crotches at Regular (6 units)."""
    import math
    p = params(w)
    for ch in LATIN:
        for ring in draw(CMAP[ch], p).rings():
            pts = [(q[0], q[1]) for q in ring]
            short = [round(math.hypot(b[0] - a[0], b[1] - a[1]), 1) for a, b in zip(pts, pts[1:] + pts[:1])
                     if 0.5 < math.hypot(b[0] - a[0], b[1] - a[1]) < 0.45 * p.c]
            assert not short, (ch, w, short)


def test_a_wall_between_two_cuts_closes_to_a_point():
    """geom._polish: a facet under half a break between two cuts that turn
    into the ink is closed where the cuts meet; one as long stays, and so
    does a short flat on an outside corner (the outline's reach is kept)."""
    from arris.geom import _polish

    def pocket(wall):                                       # ink on the left: a notch into a block's right side,
        y0, y1 = 200 - wall / 2, 200 + wall / 2             # cut top and bottom at 45 degrees, a wall between
        return [(0, 0), (300, 0), (300, y0 - 60), (240, y0), (240, y1), (300, y1 + 60), (300, 400), (0, 400)]

    out = _polish(pocket(12), 10, {}, 20)
    assert (240, 194) not in out and any(abs(x - 234) < 1e-6 and abs(y - 200) < 1e-6 for x, y in out)
    assert _polish(pocket(24), 10, {}, 20) == pocket(24)
    assert _polish(pocket(12), 10, {}) == pocket(12)        # the watch's finish: slivers only
    bump = [(0, 0), (300, 0), (300, 140), (360, 194), (360, 206), (300, 260), (300, 400), (0, 400)]
    assert _polish(bump, 10, {}, 20) == bump


def test_a_step_between_two_equal_cuts_closes_evenly():
    """geom._close_jogs: under a bar's stub the end's break and the fill
    into the stem are chords of one length with a flat between; in Arris's
    own finish they become one plane through the flat's middle."""
    from arris.geom import _close_jogs
    stub = [(0, 100), (40, 60), (52, 60), (92, 20), (92, -200), (300, -200), (300, 300), (0, 300)]
    out = _close_jogs(stub, 40, {}, even=20)
    assert (40, 60) not in out and (52, 60) not in out
    assert any(abs(x) < 1e-6 and abs(y - 106) < 1e-6 for x, y in out) and any(abs(x - 92) < 1e-6 and abs(y - 14) < 1e-6 for x, y in out)
    assert _close_jogs(stub, 40, {}) == stub
    assert _close_jogs(stub, 40, {}, even=10) == stub      # a flat of half a break or more is a flat
