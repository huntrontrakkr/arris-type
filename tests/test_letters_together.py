"""How the letters stand together (1.017): every letter keeps its share of
the line as weight is added, open sides are spaced as hand-spaced faces
space them, the open letters share one terminal and one balance of
storeys, and the corners of the D are the O's."""
from __future__ import annotations

from itertools import pairwise

import pytest
from shapely.geometry import LineString, box

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


@pytest.mark.parametrize('w', [100, 300, 400, 700, 900])
def test_the_narrow_letters_are_narrow(w):
    """Advances against the n's, inside what chamfered and squared faces
    give a letter with one stem and an arm (Chakra Petch, Oxanium,
    Rajdhani, Exo 2, Tomorrow, Share Tech, Regular and their heaviest): the
    l 0.40 to 0.56, the t 0.53 to 0.74, the f 0.48 to 0.72. On their
    masters' module widths the l stood at 0.65 at Regular, the t at 0.79
    and the f at 0.72, and a line with several of them lost its rhythm.
    The j's hook turns through two corners and needs their room: 0.54 for
    those faces' 0.41 to 0.51 (it was 0.65)."""
    p = params(w)
    adv = lambda ch: place(CMAP[ch], p)[1]
    assert 0.40 <= adv('l') / adv('n') <= 0.56
    assert 0.53 <= adv('t') / adv('n') <= 0.76
    assert 0.48 <= adv('f') / adv('n') <= 0.73
    assert 0.41 <= adv('j') / adv('n') <= 0.68


@pytest.mark.parametrize('w', [300, 400, 700, 900])
def test_the_l_is_a_stem_and_a_tail(w):
    """Over the x-height the l is its stem and nothing else, and its stem
    stands where an i's does: the flag it carried there (the 1's) hung
    into the room of whatever stood before it, 12 units from the body's
    edge at Regular for a stem's 88, and outside it at Black."""
    p = params(w)
    rings, _ = place('l', p)
    ink = rings_to_shapely(rings)
    x0, _, x1, _ = ink.intersection(LineString([(-1e4, p.xh + p.m), (1e4, p.xh + p.m)])).bounds
    top = ink.intersection(LineString([(-1e4, p.asc - p.c - 1), (1e4, p.asc - p.c - 1)])).bounds
    assert x1 - x0 == pytest.approx(p.sv, abs=1.0)
    assert top[0] == pytest.approx(x0, abs=1.0) and top[2] == pytest.approx(x1, abs=1.0)
    i_left = min(x for r in place('i', p)[0] for x, _ in r)
    assert 0.8 * i_left <= x0 <= i_left + 1.0               # (a little nearer: its foot's corner lets light in below)


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
    return [b[0] - a[1] for a, b in pairwise(runs)]


@pytest.mark.parametrize('w', [300, 400, 700, 900])
def test_the_open_storey_of_a_and_e(w):
    """The a, e and s stack their three bars with one white, and the optical
    centre raises the middle: the a's open storey is seven eighths of its
    bowl, the e's a seventh more than its bowl (until 1.017 both two
    thirds, the a's the tighter)."""
    p = params(w)
    r = OPTICAL['counters']
    bowl, upper = _whites('a', p, at=0.42)                  # left of where its bowl rises into the stem, right of its beak
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
        x0, _, x1, y1 = ink.bounds
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
    x0, _, x1, _ = ink.bounds
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
def test_the_zs_foot_is_broken_the_fills_whole_leg(w):
    from arris.draw import fill_leg
    p = params(w)
    g = draw('Z', p)
    ring = max(g.rings(), key=len)
    on_bar = [x for x, y, *_ in ring if abs(y - g.sh) < 1 and x < g.W / 2]     # where the foot's inner corner starts on the bar
    assert max(on_bar) - p.sv == pytest.approx(fill_leg(p), abs=1.5)           # a fill's leg from the foot's own side, step or none


def test_inside_corners_stop_growing_at_the_regular():
    """draw.fill_leg, geom._ring_rule: the chord that fills a concave
    corner has the weight's own leg up to the Regular and the Regular's
    from there to Black; the chord that cuts a convex one grows with the
    stem. The italic's crotches are filled one leg, as the upright's. The
    watch's own drawing keeps the pixel rule (one leg, crotches two)."""
    from arris.draw import crotch_fill, fill_leg
    from arris.geom import _ring_rule
    from arris.italic import italic
    reg = params(400).c
    assert fill_leg(params(300)) == pytest.approx(params(300).c)
    for w in (400, 600, 900):
        for p in (params(w), italic(params(w))):
            assert fill_leg(p) == pytest.approx(reg)
            assert crotch_fill(p) == pytest.approx(1.0)
    watch = params(900, watch=1.0)
    assert fill_leg(watch) == pytest.approx(watch.c) and crotch_fill(watch) == pytest.approx(2.0)

    def near(pts, q):
        return any(abs(x - q[0]) < 1e-6 and abs(y - q[1]) < 1e-6 for x, y in pts)
    ell = [(0, 0), (300, 0), (300, 100), (100, 100), (100, 300), (0, 300), (0, 0)]    # ink on the left
    out = _ring_rule(ell, 40, +1, fill=20)
    assert near(out, (120, 100)) and near(out, (100, 120))              # the inside corner, filled 20
    assert near(out, (260, 0)) and near(out, (300, 40))                 # an outside corner, cut 40
    assert near(_ring_rule(ell, 40, +1), (140, 100))                    # one leg where no fill is given


@pytest.mark.parametrize('w', [300, 400, 700, 900])
def test_a_shoulder_keeps_its_neck(w):
    """lower.shoulder_enter: a shoulder's diagonal starts deeper in its
    stem by what its crotch's fill is short of the fill it was drawn for
    (one leg of the weight's own in the upright, two in the italic), so
    the notch over it stands on the stem where it did and the join keeps
    its ink. To the Regular the upright's starts an edge break in, as
    ever."""
    from arris.draw import crotch_fill, fill_leg
    from arris.glyphs.lower import shoulder_enter
    from arris.italic import italic
    for p, was in ((params(w), 1.0), (italic(params(w)), 2.0)):
        assert shoulder_enter(p) + crotch_fill(p) * fill_leg(p) == pytest.approx((1 + was) * p.c)
    if w <= 400:
        assert shoulder_enter(params(w)) == pytest.approx(params(w).c)
    watch = params(w, watch=1.0)
    assert shoulder_enter(watch) == pytest.approx(watch.c)              # the watch's own drawing: the pixel rule


@pytest.mark.parametrize('w', [850, 900])
def test_a_bowls_inside_corner_is_what_its_strokes_make_of_it(w):
    """geom._stroke_polygon: from ExtraBold a bowl's inside chamfer was
    held at an edge break, more than its strokes leave it (the O's 44
    units for 32 at Black); it follows them down to the fill's leg."""
    from arris.draw import fill_leg
    p = params(w)
    g = draw('O', p)
    hole = min(g.rings(), key=lambda r: max(q[0] for q in r) - min(q[0] for q in r))
    legs = sorted(abs(b[0] - a[0]) for a, b in zip(hole, hole[1:] + hole[:1])           # (across: the optical centre moves heights)
                  if abs(b[0] - a[0]) > 1 and abs(b[1] - a[1]) > 1)
    want = max(fill_leg(p), p.leg - (p.sv + g.sh) / 2 + p.sd / 2 ** 0.5)
    assert legs and legs[0] == pytest.approx(want, abs=1.0) and legs[0] < p.c - 0.5


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
    assert 1.23 <= adv('w') / adv('n') <= 1.44                       # (with its walls it stands 1.37 to 1.43: the owner's build)
    assert 1.12 <= adv('M') / adv('H') <= 1.33
    assert 1.07 <= adv('W') / adv('H') <= 1.42
    assert 0.76 <= adv('T') / adv('H') <= 0.86


LATIN = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'


def test_the_l_ends_in_one_cut_at_every_weight():
    """One outline from Thin to Black: the stem turns through the corner a
    foot would take, runs on to the baseline and ends upright, an edge
    break tall over its own break, on half a stem of flat (the owner: "only
    one single notch", and "the l stays without a hook"; the f and the t
    keep theirs)."""
    import math
    counts = set()
    for w in range(100, 901, 50):
        p = params(w)
        ring = max(draw('l', p).rings(), key=len)
        counts.add(len(ring))
        short = min(math.dist(a, b) for a, b in zip(ring, ring[1:] + ring[:1]) if math.dist(a, b) > 1e-6)
        assert short >= 0.95 * p.c, w
        x1 = max(x for x, _ in ring)
        face = sorted(y for x, y in ring if x > x1 - 0.5)
        toe = min(3 * p.c, p.sh * p.low)                                    # the cut's own thickness (lower._toe)
        assert face[0] == pytest.approx(p.c, abs=1.0) and face[-1] == pytest.approx(toe - p.c, abs=1.5), w
        on_line = [x for x, y in ring if abs(y) < 0.5]
        assert max(on_line) - min(on_line) <= 0.7 * p.sv, w                # no foot
    assert len(counts) == 1


@pytest.mark.parametrize('w', [100, 300, 400, 500, 600, 700, 800, 900])
def test_f_and_t_keep_their_hooks_at_every_weight(w):
    """The corner and its arm, a module past the crossbar's end, the t
    the f turned over (the owner, 2026-11-10: "keep the hooks for the f
    and the t, and the l stays without a hook"; one cut with no arm, the
    l's end, was tried on them to SemiBold)."""
    p = params(w)
    bar_y = p.xh - 0.5 * p.sh * p.low
    for ch, y_line in (('t', 0.5), ('f', p.asc - 0.5)):
        ink = _ink(ch, p)
        flat = ink.intersection(LineString([(-1e4, y_line), (1e4, y_line)]))
        assert flat.length >= 0.9 * p.sv, ch                                # a foot, an arm (a cut's flat is half a stem)
        bar = ink.intersection(LineString([(-1e4, bar_y), (1e4, bar_y)])).bounds
        assert ink.bounds[2] >= bar[2] + 0.3 * p.sv, ch                     # past the crossbar's end
    assert REGISTRY['t'].width(p) == pytest.approx(REGISTRY['f'].width(p))


def _pieces(ch, p, y):
    cut = _ink(ch, p).intersection(LineString([(-1e4, y), (1e4, y)]))
    return len([s for s in getattr(cut, 'geoms', [cut]) if s.length > 1])


@pytest.mark.parametrize('w', [100, 300, 400, 600, 700, 800, 900])
def test_every_bowl_meets_its_stem_through_a_notch(w):
    """One notch a bowl, to ExtraBold, and square at Black as the n is:
    under the ascender on b and d (where the h has its own), over the
    descender on p, q and g, at the foot on a, u and y; the other join
    square. (The owner: "if we're going to do it on the a and the u, then
    we need to do it on all the bowls", flipped to where the stem runs
    on.)"""
    p = params(w)
    top, foot = p.xh - 0.4 * p.c, 0.4 * p.c
    notched = 1 if w == 900 else 2
    assert _pieces('n', p, top) == notched
    for ch in 'bd':
        assert (_pieces(ch, p, top), _pieces(ch, p, foot)) == (notched, 1), ch
    for ch in 'pqg':
        assert (_pieces(ch, p, foot), _pieces(ch, p, top)) == (notched, 1), ch
    for ch in 'auy':
        assert _pieces(ch, p, foot) == notched, ch


@pytest.mark.parametrize('w', [300, 400, 600, 700])
def test_the_italics_q_g_and_y_take_the_bowls_notch_and_keep_their_tails_flat(w):
    """The italic's bowls on a descending stem join it through the little
    notch too, at the foot; its hooks end flat, without the upright's
    terminal (the owner: "the descender should remain flat but ... a little
    bit of a crook in the bowls ... little teeny weeny notch", and of the
    y: "this should be on the y as well")."""
    from arris.italic import italic, polylines
    p = italic(params(w))

    def slanted(ch):                                    # the italic's outline as the font has it, its curves in chords
        return rings_to_shapely(polylines(place(CMAP[ch], p)[0]))
    for ch in 'qgy':
        ink = slanted(ch)
        foot = ink.intersection(LineString([(-1e4, 0.4 * p.c), (1e4, 0.4 * p.c)]))
        assert len([s for s in getattr(foot, 'geoms', [foot]) if s.length > 1]) == 2, ch       # the bowl's foot, the notch, the stem
    for ch in 'gy':                                     # the hook's end: nothing of it rises over the hook's bar
        ink = slanted(ch)
        x0, y0 = ink.bounds[0], ink.bounds[1]
        left = ink.intersection(box(x0 - 1, y0 - 1, x0 + 0.6 * p.sv, 0.0 - p.c))
        bar = ink.intersection(LineString([((ink.bounds[0] + ink.bounds[2]) / 2, y0 - 10), ((ink.bounds[0] + ink.bounds[2]) / 2, -p.c)]))
        assert left.bounds[3] <= bar.bounds[3] + 1.0, ch


def test_the_cursive_e_gives_only_its_top_and_bar_for_its_eye():
    """italic_forms._e_strokes: the foot is the alphabet's horizontal at
    every weight (the o's own), the exit stands over it, and the top and
    the bar give way together, for the eye alone: by less than a tenth to
    Black, and never thinner than at the weight before. Until 1.017 every
    horizontal of the letter thinned for the eye, the foot too (0.70 of the
    o's from SemiBold), the top fell by a quarter between Medium and
    SemiBold and the bar by a quarter from Bold to Black."""
    from arris.glyphs.italic_forms import EXIT_OVER
    from arris.italic import italic

    def run(ink, x):                                    # the ink's first run up the upright line at x, from under the baseline
        cut = ink.intersection(LineString([(x, -50), (x, 250)]))
        part = min((s for s in getattr(cut, 'geoms', [cut]) if s.length > 1), key=lambda s: s.bounds[1])
        return part.bounds[1], part.bounds[3]
    last = 0.0
    for w in (400, 500, 600, 700, 800, 900):
        p = italic(params(w))
        g, o = draw('e', p), draw('o', p)
        k = g.free('eye', 1.0)
        assert 0.9 <= k <= 1.0 and g.sh_auto == pytest.approx(1.0), (w, k)
        assert p.sh * k >= last - 1e-6, w               # the top (and the bar with it) never loses weight
        last = p.sh * k
        x_exit = p.sv / 2 + (g.W - p.sv) * 5 / 6        # where the exit leaves the foot (the frame's sixth module)
        y0, y1 = run(rings_to_shapely(g.rings()), x_exit - 1.5 * p.c)       # the foot, under the opening
        b0, b1 = run(rings_to_shapely(o.rings()), o.W / 2)
        assert y1 - y0 == pytest.approx(p.sh, abs=1.5), w                   # the weight's horizontal, whole
        assert y1 - y0 == pytest.approx(b1 - b0, rel=0.03), w               # and the o's (which thins its own a little for its counter)
        end = max(q[1] for r in g.rings() for q in r if q[0] > x_exit + p.c and q[1] < p.xh / 2)
        assert end >= y1 + EXIT_OVER * p.c - 1.5, w


@pytest.mark.parametrize('w', [100, 300, 400, 600, 700, 900])
def test_b_and_d_and_p_and_q_are_mirrors(w):
    from shapely import affinity
    p = params(w).with_(optical=0.0)                    # the drawings themselves, before the optical centre is raised
    for a, b in ('bd', 'pq'):
        ga, gb = draw(a, p), draw(b, p)
        assert ga.W == pytest.approx(gb.W)
        mirrored = affinity.scale(rings_to_shapely(gb.rings()), xfact=-1, origin=(gb.W / 2, 0))
        assert rings_to_shapely(ga.rings()).symmetric_difference(mirrored).area < 1.0, a + b


@pytest.mark.parametrize('w', [100, 300, 400, 500])
def test_arches_and_bowls_each_have_their_own_depth_of_notch(w):
    """Two rule sets (the owner: "you shouldn't be changing the m's and the
    n's and the r's ... it's just a different rule set"): the arches leave
    their stems two modules under the arch, as they always have; a bowl's
    join is one module, half as deep, the same on every bowl."""
    from arris.glyphs.lower import BOWL_DROP, SHOULDER_DROP
    assert (SHOULDER_DROP, BOWL_DROP) == (2.0, 1.0)
    p = params(w).with_(optical=0.0)

    def reach(ch, right=False, foot=False):             # from the stem's centre to where the notch ends, along the line it opens on
        g = draw(ch, p)
        y = 0.5 if foot else p.xh - 0.5
        cut = _ink(ch, p).intersection(LineString([(-1e4, y), (1e4, y)]))
        xs = sorted((s.bounds[0], s.bounds[2]) for s in cut.geoms if s.length > 1)
        return (g.W - p.sv / 2) - xs[-2][1] if right else xs[1][0] - p.sv / 2
    arch = reach('n')                                   # (each arch's own, as far as it has room: unchanged, and tested where it was)
    assert reach('h') == pytest.approx(arch, abs=1.0)
    bowl = reach('b')
    for ch, kw in (('d', {'right': True}), ('p', {'foot': True}), ('q', {'right': True, 'foot': True}),
                   ('g', {'right': True, 'foot': True}), ('u', {'right': True, 'foot': True}), ('y', {'right': True, 'foot': True})):
        assert reach(ch, **kw) == pytest.approx(bowl, abs=1.0), ch
    assert bowl < arch - 0.4 * p.m                      # shallower than the n's by most of a module


@pytest.mark.parametrize('w', [100, 300, 400, 600, 700, 900])
def test_the_v_has_high_walls_over_45_degrees(w):
    """The capital's drawing in the x-height (the owner: "it needs to have
    the 45 degrees with the high walls"): two upright walls more than half
    the x-height tall, a 45-degree point under them, no other slope
    (within the few degrees the raised optical centre turns a diagonal)."""
    import math
    p = params(w)
    g = draw('v', p)
    for ring in g.rings():
        for a, b in zip(ring, ring[1:] + ring[:1]):
            if math.dist(a, b) > 1.0:
                turn = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 45
                assert min(turn, 45 - turn) < 3.0, (a, b)
    cut = _ink('v', p).intersection(LineString([(-1e4, 0.7 * p.xh), (1e4, 0.7 * p.xh)]))
    walls = sorted(s.bounds for s in cut.geoms)
    assert len(walls) == 2 and all(b[2] - b[0] == pytest.approx(p.sv, abs=0.5) for b in walls)
    assert walls[0][0] == pytest.approx(0.0, abs=0.5) and walls[1][2] == pytest.approx(g.W, abs=0.5)
    foot = min(y for r in g.rings() for x, y in r if x < 0.5)          # where the left wall ends
    assert foot <= 0.45 * p.xh


@pytest.mark.parametrize('w', [100, 300, 400, 600, 700, 900])
def test_the_w_is_the_capitals_build(w):
    """High walls, 45-degree valleys, and its middle stroke a stem standing
    on the peak (the owner: "if we're going to modify the v and the y then
    we should definitely do the w"; until 1.017 its arms were at 2:1, and
    the italic's still are)."""
    import math

    from arris.glyphs.lower import W_POST
    p = params(w).with_(optical=0.0)
    g = draw('w', p)
    for ring in g.rings():
        for a, b in zip(ring, ring[1:] + ring[:1]):
            if math.dist(a, b) > 1.0:
                turn = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 45
                assert min(turn, 45 - turn) < 0.5, (a, b)
    sh = p.sh * p.low
    post = sh / 2 + (W_POST - 1) * (p.xh - sh) / 7                     # the height of module W_POST
    cut = _ink('w', p).intersection(LineString([(-1e4, post - p.c - 1), (1e4, post - p.c - 1)]))
    runs = sorted((s.bounds[0], s.bounds[2]) for s in cut.geoms if s.length > 1)
    assert len(runs) == 3                                               # two walls and the middle stroke
    assert runs[1][1] - runs[1][0] == pytest.approx(p.sv, abs=0.5)
    assert (runs[1][0] + runs[1][1]) / 2 == pytest.approx(g.W / 2, abs=0.5)
    assert _pieces('w', p, post + 1.0) == 2                             # and nothing of it over that


@pytest.mark.parametrize('w', [100, 300, 400, 600, 700, 900])
def test_v_w_and_y_bend_at_one_height(w):
    """Their walls turn into their 45-degree arms at one height (the owner:
    "where the crook occurs needs to be consistent"); the v, still pointed,
    is as wide as its two arms, narrower than the n."""
    from arris.glyphs.lower import gable_run
    p = params(w).with_(optical=0.0)
    bend = {ch: min(y for r in draw(ch, p).rings() for x, y in r if x < 0.5 and y > 0) for ch in 'vwy'}
    assert bend['v'] == pytest.approx(bend['w'], abs=0.5)
    if w <= 700:                                                        # (heavier, the y's arm lands where its foot has room)
        assert bend['y'] == pytest.approx(bend['v'] + (p.sh * p.low / 2 - (-(1.75) * p.c + p.sd / 2 ** 0.5)), abs=1.0) or \
            bend['y'] == pytest.approx(bend['v'], abs=1.0)
    assert REGISTRY['v'].width(p) == pytest.approx(p.sv + 2 * gable_run(p))
    assert REGISTRY['v'].width(p) < REGISTRY['n'].width(p)


@pytest.mark.parametrize('w', [300, 400, 500, 600, 700, 800, 900])
def test_no_letter_keeps_a_crumb(w):
    """No edge of a letter or figure is shorter than half an edge break, at
    any named weight (0.45 of one: the v's flank at Black is 0.48; of the
    fill's own leg, for an edge inside a corner: draw.fill_leg). Until
    1.017 twenty-two of the sixty-two kept one at some weight: the wall of
    a counter between its corners' cuts (a e s B G 3 5 6 8 9), the flat
    under a bar's stub between its two cuts (f t l 4), the flat the X's
    step left in its crotches at Regular (6 units)."""
    import math

    from arris.draw import fill_leg
    p = params(w)
    cross = lambda u, v: u[0] * v[1] - u[1] * v[0]
    for ch in LATIN:
        for ring in draw(CMAP[ch], p).rings():
            pts = [(q[0], q[1]) for q in ring]
            n = len(pts)
            short = []
            for i in range(n):
                h, a, b, k = pts[i - 1], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
                e_in, e, e_out = (a[0] - h[0], a[1] - h[1]), (b[0] - a[0], b[1] - a[1]), (k[0] - b[0], k[1] - b[1])
                # an edge the ring turns into the white at both ends of (ink on its left) is a fill's chord or
                # stands between two: those are measured on the fill's leg, the Regular's from there to Black
                # (a crotch's chord may run straight on into the cut beside it: a turn into the white at one
                # end and next to none at the other)
                turn = lambda u, v: math.degrees(math.atan2(cross(u, v), u[0] * v[0] + u[1] * v[1]))
                t_in, t_out = turn(e_in, e), turn(e, e_out)
                inside = min(t_in, t_out) < -20 and max(t_in, t_out) < 5
                if 0.5 < math.hypot(*e) < 0.45 * (fill_leg(p) if inside else p.c):
                    short.append(round(math.hypot(*e), 1))
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
    doubled = pocket(12)[:4] + [(240, 194)] + pocket(12)[4:]   # a point twice beside the wall: it goes, then the wall
    assert _polish(doubled, 10, {}, 20) == out


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
