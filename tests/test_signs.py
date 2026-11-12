"""The signs that stand in text beside the letters, as 1.017 leaves them:
the percent's rings clear of its slash, the number sign's ends longer than
its strokes are thick, the straight quotes a third of the cap height."""
from __future__ import annotations

import itertools

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


BARS = ['hyphen', 'endash', 'emdash', 'underscore', 'underscoredbl', 'uni203E']
OPERATORS = ['plus', 'minus', 'equal', 'multiply', 'divide', 'less', 'greater', 'plusminus', 'logicalnot']


def test_a_sign_of_bars_keeps_its_share_of_the_line():
    """A dash's modules are the length of its bar, not white between stems.
    Read as white they widened toward Thin and past the Regular gave way to
    stems the sign has not got: against the H's advance the hyphen stood
    1.24 of its Regular's share at Thin and 0.60 of it at Black (a square
    of ink between its letters), the plus and the equals 1.12 and 0.81. In
    sixty other families each keeps its share from Thin to Black (1.00 or
    1.01 of the Regular's at the median at every weight). The body keeps
    the share of the H's body it has at the Regular (letterframe.kept_width),
    in the watch's own drawing too; in Arris Mono, whose signs are drawn to
    their cell, it is its modules as it was."""
    from arris.draw import REGISTRY
    from arris.font import place
    from arris.glyphs.letterframe import plain_width
    from arris.instances import mono_weight
    regular = params(400)
    h0 = REGISTRY['H'].width(regular)
    for name in BARS + OPERATORS:
        share = REGISTRY[name].width(regular) / h0
        for watch in (0.0, 1.0):
            for w in (100, 200, 300, 500, 600, 700, 800, 900):
                p = params(w, watch=watch)
                assert REGISTRY[name].width(p) / REGISTRY['H'].width(p) == pytest.approx(share, rel=1e-9), (name, w, watch)
    for name, least, most in (('hyphen', 0.94, 1.04), ('endash', 0.98, 1.02), ('emdash', 0.97, 1.06), ('plus', 0.99, 1.02),
                              ('equal', 0.99, 1.02)):
        at = {w: place(name, params(w))[1] / place('H', params(w))[1] for w in (100, 400, 700, 900)}
        assert all(least <= at[w] / at[400] <= most for w in at), (name, at)
    # Arris Mono's signs are drawn to their cell: nothing moved there
    for w in (300, 400, 700):
        p = params(mono_weight(w)).with_(mono=True)
        for name, wm, stems in (('endash', 9, 0), ('hyphen', 6, 0), ('underscore', 9, 0), ('minus', 8, 1)):
            assert REGISTRY[name].width(p) == pytest.approx(min(plain_width(wm, stems)(p), p.fig_w)), (name, w)


def test_the_dashes_are_as_long_as_other_families():
    """At six, nine and sixteen modules the hyphen stood 0.81 of the H's
    advance, the en dash 1.10 and the em dash 1.77, and the underscore, nine
    modules too, 1.10: longer than all but two or three of sixty families'
    (their middle ones 0.60, 0.79, 1.23 and 0.75). They are four, six, ten
    and a half and five and a half modules; Arris Mono's are its cell's."""
    from arris.font import place
    for w in (100, 400, 700, 900):
        p = params(w)
        h = place('H', p)[1]
        for name, theirs in (('hyphen', 0.60), ('endash', 0.79), ('emdash', 1.23), ('underscore', 0.75), ('underscoredbl', 0.75),
                             ('uni203E', 0.75)):
            assert place(name, p)[1] / h == pytest.approx(theirs, abs=0.075), (name, w)
        assert place('hyphen', p)[1] < place('endash', p)[1] < place('emdash', p)[1]


@pytest.mark.parametrize('w', [400, 600, 700, 800, 900])
def test_every_operator_stands_on_one_advance(w):
    """The plus, the minus, the equals and the rest stand on one advance at
    a weight. A sign drawn with lighter strokes to keep its whites took its
    body from those strokes: at Black the plus and the < stood 54 units
    narrower than the equals."""
    from arris.font import place
    p = params(w)
    advances = {n: round(place(n, p)[1]) for n in OPERATORS}
    assert len(set(advances.values())) == 1, advances


@pytest.mark.parametrize('w', [400, 500, 600, 700, 800, 900])
def test_less_or_equal_stands_between_the_baseline_and_the_cap_height(w):
    """The < over a bar: at the Regular the pair fills the cap height to 38
    units. Bolder it grew with every part of it, 805 units tall at SemiBold
    and 997 at Black, 150 under the baseline and 127 over the capitals. The
    white gives to the least white and the chevron to what is left."""
    p = params(w)
    for name in ('lessequal', 'greaterequal'):
        ink = _ink(name, p)
        _, y0, _, y1 = ink.bounds
        assert y0 >= -1.0 and y1 <= p.cap + 1.0, (name, round(y0), round(y1))
        assert len(list(getattr(ink, 'geoms', [ink]))) == 2          # the chevron and its bar, apart


@pytest.mark.parametrize('w', [400, 600, 700, 800, 900])
def test_the_not_equals_slash_passes_its_bars(w):
    """Four modules each way from the axis took the slash 98 units past the
    Regular's bars; Black's bars stand 306 from the axis, and the slash
    ended 66 units inside them: two bars and a tick between."""
    g = draw('notequal', params(w))
    ink = rings_to_shapely(g.rings())
    bars = [st for st in g.strokes]
    top = max(n.y for st in bars for n in st.nodes) + g.sh / 2
    bottom = min(n.y for st in bars for n in st.nodes) - g.sh / 2
    _, y0, _, y1 = ink.bounds
    assert y1 >= top + 0.75 * g.p.m and y0 <= bottom - 0.75 * g.p.m, (round(y0), round(bottom), round(top), round(y1))


@pytest.mark.parametrize('w', [500, 600, 700, 800, 900])
def test_the_not_equals_bars_are_the_equals(w):
    """The rule that lightens a sign to keep its whites counted the wedges
    between the ≠'s slash and its bars, outside the bars: six whites at the
    Regular for the two a reader sees. Four went from Medium, and from
    SemiBold the whole sign was drawn 0.8 of its weight without getting one
    back, its bars thinner than the equals' beside it (the owner, of Bold:
    it "looks like crap"). A sign's whites are the ones inside the outline
    of what its slash is laid over (draw.white_features): the ≠'s two, kept
    to Black, on the equals' own bars."""
    from arris.draw import REGISTRY, _build, white_features
    p = params(w)
    neq, eq = draw('notequal', p), draw('equal', p)
    assert neq.p.light == 1.0 and neq.sh == pytest.approx(eq.sh)
    assert sorted(n.y for st in neq.strokes for n in st.nodes) == pytest.approx(sorted(n.y for st in eq.strokes for n in st.nodes))
    raw = _build(REGISTRY['notequal'], p, 0.0, 0.0, {})
    assert white_features(raw.rings(), p, raw) == 2


def test_the_xi_stands_in_the_sigmas_body():
    """Three bars and no stem: in a body of nine modules of white the Ξ
    stood 1.05 of the H's advance at Light and 0.55 at Black, where it was
    three stubs. Other families' Ξ is 0.85 of their H at Regular and at
    Bold, a little over their Σ."""
    from arris.font import place
    for w in (100, 300, 400, 700, 900):
        p = params(w)
        assert draw('uni039E', p).W == pytest.approx(draw('uni03A3', p).W)
        assert place('uni039E', p)[1] == pytest.approx(place('uni03A3', p)[1], rel=0.02), w
        if w >= 300:
            assert 0.85 <= place('uni039E', p)[1] / place('H', p)[1] <= 0.96, w


ACCENTS = [('eacute', 'e'), ('egrave', 'e'), ('ecircumflex', 'e'), ('edieresis', 'e'), ('ccaron', 'c'), ('abreve', 'a'),
           ('emacron', 'e'), ('aring', 'a'), ('ntilde', 'n'), ('uhungarumlaut', 'u'), ('Eacute', 'E'), ('Odieresis', 'O'),
           ('uni0219', 's'), ('uni1EA1', 'a')]


def _accent(acc, base, p):
    """(the accent's ink: the accented letter less its letter; the letter's ink)."""
    from arris.font import place
    a, b = (rings_to_shapely(place(n, p)[0]) for n in (acc, base))
    return a.difference(b.buffer(0.5)), b


@pytest.mark.parametrize('cut', ['upright', 'italic', 'watch', 'mono'])
def test_an_accent_takes_half_of_what_its_letter_gains(cut):
    """Accents were drawn with their letter's own strokes at a size that
    grew with them: at Black they carried 1.3 to 2.0 times the ink of other
    families' for their letter (the owner, 2026-11-12: "all bloated and
    ugly at black"). Held at the Regular's weight they were hairlines on a
    Black letter, four tenths of its stem where fifty-nine other families'
    heaviest weights have 0.62 to 0.71 ("It looks wrong. Can we look at
    what other heavy or black weights look like"). In those families an
    accent's strokes take half of what the stem gains from Regular to
    heaviest (0.49 to 0.63 at the median, accent by accent) and the whites
    stay close to the Regular's. Past its cut's Regular an accent's strokes
    take MARK_GAIN of the letter's gain (marks.mark_params); its breaks,
    its size, the white between a dieresis's dots and the white between it
    and its letter stay the Regular's."""
    from arris.font import place
    from arris.glyphs.marks import MARK_GAIN, mark_params
    from arris.instances import mono_weight
    from arris.italic import italic
    at = {'upright': params, 'italic': lambda w: italic(params(w)), 'watch': lambda w: params(w, watch=1.0),
          'mono': lambda w: params(mono_weight(w)).with_(mono=True)}[cut]
    regular = at(400)
    assert mark_params(regular) is regular and mark_params(at(300)).sv == at(300).sv
    for w in (500, 700, 900):
        p, q = at(w), mark_params(at(w))
        assert q.sv == pytest.approx(regular.sv + MARK_GAIN * (p.sv - regular.sv)), w
        assert q.sd == pytest.approx(regular.sd + MARK_GAIN * (p.sd - regular.sd)), w
        assert q.c == pytest.approx(regular.c), w
    white = lambda a, b: max(a.bounds[1] - b.bounds[3], b.bounds[1] - a.bounds[3])  # above its letter, or below
    for acc, base in ACCENTS:
        a0, b0 = _accent(acc, base, regular)
        for w in (700, 900):
            a, b = _accent(acc, base, at(w))
            # (to a unit; the tilde's cut corners are broken 5 units higher on a thicker stroke)
            assert white(a, b) == pytest.approx(white(a0, b0), abs=6.0 if acc == 'ntilde' else 1.5), (acc, w)
            assert a0.area < a.area, (acc, w)                                       # heavier than the Regular's
    # the dots thicken; they do not drift apart
    def between(p):
        ink = rings_to_shapely(place('edieresis', p)[0])
        dots = sorted((q for q in ink.geoms if q.bounds[1] > 0.9 * p.xh and q.area < 0.2 * ink.area), key=lambda q: q.bounds[0])
        assert len(dots) == 2
        return dots[0].distance(dots[1])                    # (edge to edge: in the italic the dots lean)
    for w in (700, 900):
        assert between(at(w)) == pytest.approx(between(regular), abs=1.5), w


@pytest.mark.parametrize('cut', ['upright', 'italic'])
def test_an_accented_letter_does_not_step_at_the_regular(cut):
    """Up to the Regular an accent is drawn in its letter, past it in a
    drawing of its own (the Regular's), stamped in. One that hangs from
    its letter is finished with the letter's ink under it either way
    (marks.kept, joined): stamped in alone, the ogonek lost the fills of
    its join where it became the Regular's, 700 square units of į between
    weights 400 and 401 for the 180 of a weight's growth. Between 400 and
    401 an accented letter changes as it does between 401 and 402."""
    from arris.font import place
    from arris.italic import italic
    at = params if cut == 'upright' else (lambda w: italic(params(w)))
    for name in ('iogonek', 'aogonek', 'Eogonek', 'ccedilla', 'ohorn', 'eacute', 'edieresis', 'uni0219', 'dcaron'):
        inks = [rings_to_shapely(place(name, at(w))[0]) for w in (400, 401, 402)]
        step, next_ = (inks[i].symmetric_difference(inks[i + 1]).area for i in range(2))
        assert step <= 1.5 * next_ + 30, (name, round(step), round(next_))


def test_a_mark_that_hangs_off_its_letter_is_a_little_bolder():
    """The ogonek and the horn are a part of their letter's outline. At the
    Regular's weight on a Black letter they read as a hair on it (the
    owner, 2026-11-12: "if it's hanging off of the letter, it should
    probably be a little bolder"): they take a third of what the letter's
    strokes gain past the Regular (marks.HANG_GAIN). At two thirds the
    ogonek stood 0.92 of the stem and 0.64 of its letter's width where
    fifty-nine other families' heaviest weights have 0.71 and 0.45 ("It
    looks wrong"); at a third, 0.67 and 0.46."""
    from arris.glyphs.marks import HANG_GAIN, mark_params
    regular = params(400)
    assert mark_params(regular, HANG_GAIN) is regular
    for w in (500, 700, 900):
        p = params(w)
        q = mark_params(p, HANG_GAIN)
        assert q.sv == pytest.approx(regular.sv + HANG_GAIN * (p.sv - regular.sv))
        assert q.sh == pytest.approx(regular.sh + HANG_GAIN * (p.sh - regular.sh))
        assert regular.sv < q.sv < p.sv
    # as drawn: the ogonek's neck under the a, at Black
    p = params(900)
    (x0, x1), = _runs(_ink('aogonek', p), y=-0.6 * p.m)
    assert x1 - x0 == pytest.approx(regular.sv + HANG_GAIN * (p.sv - regular.sv), rel=0.12)


@pytest.mark.parametrize('cut', ['upright', 'italic'])
def test_the_cedilla_is_a_flat_tab(cut):
    """The cedilla was a hook: a neck down and a foot turning left. At
    Black it stood 0.92 of the stem thick and 0.62 of its letter wide where
    fifty-nine other families' heaviest weights have 0.68 and 0.48, a
    second foot under the letter (the owner, 2026-11-12: "It looks wrong";
    "the cedilla under the c ... just turns into a little flat tab"; of
    the tab at a third, two thirds and the whole of the letter's weight,
    "F. Definitely": the whole). After Tomorrow's: a short stroke leaning
    two down for one across, cut level underneath, two modules deep, as
    wide as the letter's stem at every weight, one drawing from Thin to
    Black (the ¸ alone no different from the one under a c)."""
    from shapely.geometry import box

    from arris.font import place
    from arris.glyphs.marks import TAB_DEPTH
    from arris.italic import italic
    at = params if cut == 'upright' else (lambda w: italic(params(w)))
    for w in (300, 400, 700, 900):
        p = at(w)
        depth = TAB_DEPTH * p.m
        below = lambda name, p=p: rings_to_shapely(place(name, p)[0]).intersection(box(-1e4, -1e4, 1e4, -1.0))
        tab = below('cedilla')
        assert tab.bounds[1] == pytest.approx(-depth, abs=1.0), w
        (a0, a1), = _runs(tab, y=-depth / 2)
        assert a1 - a0 == pytest.approx(p.sv, abs=1.5), w                           # a stem wide
        (b0, b1), = _runs(tab, y=-depth + 1.0)
        assert b1 - b0 >= p.sv - 2.2 * p.c - 2.0, w                                 # level underneath, its corners broken
        if cut == 'upright':
            (t0, t1), = _runs(tab, y=-10.0)
            lean = (t0 + t1) / 2 - (b0 + b1) / 2                                    # two down for one across
            assert lean == pytest.approx((depth - 11.0) / 2, abs=0.2 * p.c + 2.0), w
        # under a letter it is the same tab
        (c0, c1), = _runs(below('ccedilla'), y=-depth / 2)
        assert c1 - c0 == pytest.approx(a1 - a0, abs=1.5), w


@pytest.mark.parametrize('w', [300, 400, 700, 900])
def test_the_ring_is_an_octagon(w):
    """The ring was a square on four bowl corners. A bowl corner's diagonal
    is as thick as the alphabet's diagonals, thicker than the ring's sides:
    its counter came out a diamond and its outside all but square, a block
    with a pinhole at Black. After Tomorrow's (the owner, 2026-11-12: "Do
    Tomorrow because it's better"): a regular octagon inside and out,
    eight sides of one thickness."""
    ring = _ink('ring', params(w))
    assert len(ring.interiors) == 1
    x0, y0, x1, y1 = ring.bounds
    i0, j0, i1, j1 = ring.interiors[0].bounds
    assert x1 - x0 == pytest.approx(y1 - y0, abs=0.5) and i1 - i0 == pytest.approx(j1 - j0, abs=0.5)
    octagon = lambda across: 2 * (2 ** 0.5 - 1) * across ** 2                       # a regular octagon's area
    assert ring.area == pytest.approx(octagon(x1 - x0) - octagon(i1 - i0), rel=0.02)
    assert len(ring.exterior.coords) - 1 == 8 and len(ring.interiors[0].coords) - 1 == 8


def test_the_letter_under_an_italic_ogonek_is_the_plain_letter():
    """A hook must not change the letter it hangs from. Finished with its
    letter's ink stamped in a second time under it, the italic ą lost the
    curve of its bowl's upper left corner at Bold and ExtraBold (5,000
    square units cut straight): the italic no longer knew the letter's
    corners for its own. Only the mark and the fills of its join are
    stamped in (marks.kept). Above the baseline the ą is the a at every
    weight."""
    from shapely import affinity
    from shapely.geometry import box

    from arris.font import place
    from arris.italic import italic
    up = box(-1e4, 8.0, 1e4, 1e4)
    worst = {}
    for w in (400, 600, 700, 800, 900):
        p = italic(params(w))
        a, b = (rings_to_shapely(place(n, p)[0]).intersection(up) for n in ('aogonek', 'a'))
        worst[w] = affinity.translate(a, b.bounds[0] - a.bounds[0], 0).symmetric_difference(b).area
    assert max(worst.values()) <= 500.0, {w: round(v) for w, v in worst.items()}


DOLLAR_CUTS = {'upright': lambda w: params(w), 'italic': lambda w: _italic(params(w)),
               'watch': lambda w: params(w, watch=1.0)}


def _italic(p):
    from arris.italic import italic
    return italic(p)


@pytest.mark.parametrize('cut', list(DOLLAR_CUTS))
def test_the_dollar_with_stubs_is_its_weights_s(cut):
    """With stubs for a stem the dollar is the S and two stubs, in its
    weight's own strokes: its second form is a glyph of its own, held to its
    own Regular (draw._second_spec), as the variable font carries it.
    Measured against the first form's Regular it was lightened as far as the
    rules go, for the four counters its stem no longer cut: at Black bars of
    96 units on an S of 160, 0.75 of the S's ink."""
    from arris.font import place
    at = DOLLAR_CUTS[cut]
    stubs = 0
    for w in (400, 600, 700, 800, 900):
        p = at(w)
        d = draw('dollar', p)
        if d.overrides.get('stem', 1.0) >= 0.5:
            continue
        stubs += 1
        assert d.p.sv == pytest.approx(p.sv), w                 # not lightened
        assert 'sh_auto' not in d.overrides, w                  # nor its bars thinned for counters it has not got
        ink, s = (rings_to_shapely(place(n, p)[0]).area for n in ('dollar', 'S'))
        assert 1.02 <= ink / s <= 1.15, (w, ink / s)           # the S and its two stubs
        assert d.rings() == draw('dollar.stem', p).rings(), w   # the drawing the variable font swaps in
    assert stubs, cut


@pytest.mark.parametrize('cut', list(DOLLAR_CUTS))
def test_the_dollar_never_goes_lighter_as_the_weight_goes_up(cut):
    """Where the stem gives way to stubs the dollar loses the stem's run
    through the S, a tenth of its ink at most, and nothing else: it lost
    28% between 680 and 690."""
    from arris.font import place
    at = DOLLAR_CUTS[cut]
    ink = [rings_to_shapely(place('dollar', at(w))[0]).area for w in range(600, 901, 20)]
    for a, b, w in zip(ink, ink[1:], range(600, 900, 20)):
        assert b / a > 0.88, (w, b / a)
    assert ink[-1] > ink[0]


def test_the_equals_white_gives_as_its_bars_gain():
    """The white between the equals' bars is 1.6 bars to the Regular and
    gives a third of what the stem gains past it (punct.eq_white): in some
    seventy families it stands 1.72 bars at Regular and 0.62 at their
    heaviest, the sign 0.39 and 0.52 of the cap height tall (0.68 at the
    outside). Held at 1.6 bars the equals stood 0.86 tall at Black."""
    white, tall = {}, {}
    for w in (300, 400, 700, 900):
        p = params(w)
        g = _ink('equal', p)
        (b0, t0), (b1, t1) = _runs(g, x=g.centroid.x)
        white[w], tall[w] = (b1 - t0) / (t0 - b0), (t1 - b0) / p.cap
    assert white[400] == pytest.approx(1.6, abs=0.02)
    assert 0.7 <= white[700] <= 1.0 and 0.5 <= white[900] <= 0.7, white
    assert tall[400] < tall[700] < tall[900] <= 0.62, tall


@pytest.mark.parametrize('w', [400, 700, 900])
def test_the_stacked_signs_stand_in_the_capitals(w):
    """= ≡ ≈ ≅ ≋ ≃ ≊ between the baseline and the cap height at every
    weight, the ≈ no taller than three quarters of it (twenty-nine
    families': 0.79 at the outside), each in the equals' body. From Bold
    the ≈ and the ≡ ran past the capitals both ways."""
    from arris.font import place
    p = params(w)
    adv = place('equal', p)[1]
    for n in ('equal', 'equivalence', 'approxequal', 'congruent', 'uni224B', 'uni2243', 'uni224A'):
        g = _ink(n, p)
        assert g.bounds[1] >= -1 and g.bounds[3] <= p.cap + 1, (n, g.bounds)
        assert place(n, p)[1] == pytest.approx(adv, abs=1), n
    g = _ink('approxequal', p)
    assert (g.bounds[3] - g.bounds[1]) / p.cap <= 0.76
    assert len(g.geoms) == 2                                  # two waves, white between them all the way


@pytest.mark.parametrize('w', [300, 400, 700, 900])
def test_a_sign_of_dots_stands_as_tall_as_the_plus(w):
    """÷ ∶ ∷ ∴ ∵: the dots' outer edges where the plus's arms end. The
    ratio and the division sign stood 0.52 of the cap height tall at
    Regular (thirty families' ÷: 0.70) and 1.13 at Black."""
    p = params(w)
    plus = _ink('plus', p)
    for n in ('divide', 'uni2236', 'uni2237', 'therefore', 'uni2235'):
        g = _ink(n, p)
        assert g.bounds[1] == pytest.approx(plus.bounds[1], abs=2) and g.bounds[3] == pytest.approx(plus.bounds[3], abs=2), n
    div = sorted(_ink('divide', p).geoms, key=lambda q: q.bounds[1])
    assert len(div) == 3
    bar = div[1].bounds[3] - div[1].bounds[1]
    assert div[1].bounds[1] - div[0].bounds[3] >= 0.44 * bar          # white between a dot and the bar


@pytest.mark.parametrize('w', [400, 600, 700, 800, 900])
def test_the_daggers_bar_stays_high(w):
    """The dagger's bar crosses in the upper third at every weight, and the
    double dagger's two bars stand apart. Lowered to keep two stems of
    stem over it, the bar crossed at 0.39 of the cap height at Black: a
    plus, and the double dagger one blob."""
    p = params(w)
    g = _ink('dagger', p)
    (b, t), = _runs(g, x=g.bounds[0] + 0.1 * (g.bounds[2] - g.bounds[0]))
    assert (b + t) / 2 >= 0.62 * p.cap, (b, t)
    assert p.cap - t >= 0.5 * (t - b)                                  # a stub of stem over it
    g = _ink('daggerdbl', p)
    (b0, t0), (b1, _) = _runs(g, x=g.bounds[0] + 0.1 * (g.bounds[2] - g.bounds[0]))
    assert b1 - t0 >= 0.8 * (t0 - b0)                                  # white between the bars
    H = _ink('H', p)
    assert 0.66 <= (g.bounds[2] - g.bounds[0]) / (H.bounds[2] - H.bounds[0]) <= 0.86


@pytest.mark.parametrize('w', [300, 400, 700, 900])
def test_the_radical_has_its_tick(w):
    """The radical's tick starts near half the sign's height (368 fonts:
    0.50, the middle half 0.46 to 0.57). Two modules long, it stood at a
    fifth and was gone into its own stroke from Bold."""
    p = params(w)
    for n in ('radical', 'uni221B'):
        g = _ink(n, p)
        main = max(getattr(g, 'geoms', [g]), key=lambda q: q.area)
        x0, y0, x1, y1 = main.bounds
        tick = max(y for x, y in main.exterior.coords if x <= x0 + 0.1 * (x1 - x0))
        assert (0.40 if n == "radical" else 0.28) <= (tick - y0) / (y1 - y0) <= 0.60, (n, w, (tick - y0) / (y1 - y0))


def _wide(name, p):
    """A glyph's ink across, over the H's."""
    from arris.font import place
    a, h = (rings_to_shapely(place(n, p)[0]).bounds for n in (name, 'H'))
    return (a[2] - a[0]) / (h[2] - h[0])


def test_small_signs_keep_near_their_share_of_the_line():
    """Quotation marks, the bullet, brackets, braces and the multiplication
    sign grew with the stem and stood outside every family measured at
    Black (of the H's ink across: “ 1.16, • 0.79, { 1.04, [ 0.66, × 0.95;
    twenty-one families' heaviest at the outside 0.91, 0.77, 0.71, 0.54,
    0.93). Past the Regular a quotation mark's dot and the bullet take half
    of what the weight's would gain (punct.quote_dot, bullet_width), a
    bracket's arm stands out a little over half a stem (BRACKET_ARM), the
    brace's point is no longer than the Regular's (_brace_cut), and the
    multiplication sign is 0.85 of the plus across at every weight."""
    from arris.glyphs.punct import MULTIPLY, quote_dot
    regular, black = params(400), params(900)
    assert quote_dot(regular) == regular.dot()
    assert quote_dot(black) == pytest.approx(regular.dot() + 0.5 * (black.dot() - regular.dot()))
    at_regular = {'quotedblleft': 0.62, 'quotedblbase': 0.62, 'bullet': 0.42, 'braceleft': 0.61, 'bracketleft': 0.44}
    most = {'quotedblleft': 0.91, 'quotedblbase': 0.91, 'bullet': 0.77, 'braceleft': 0.71, 'bracketleft': 0.54}
    for name, share in at_regular.items():
        assert _wide(name, regular) == pytest.approx(share, abs=0.02), name      # the Regular as it was
        for w in (700, 900):
            assert _wide(name, params(w)) <= most[name], (name, w)
            assert _wide(name, params(w)) >= share - 0.02, (name, w)             # and none shrinks
    for w in (400, 700, 900):
        p = params(w)
        assert _wide('multiply', p) == pytest.approx(MULTIPLY * _wide('plus', p), abs=0.02), w
        assert _wide('braceright', p) == pytest.approx(_wide('braceleft', p)), w


def _adv(name, p):
    from arris.font import place
    return place(name, p)[1] / place('H', p)[1]


def test_struck_and_wavy_arrows_keep_near_their_length():
    """A negation is held at the Regular's weight past it, and so are its
    reach past the shafts and the room the arrow makes for it
    (arrows.strike_at); a wave's and a zigzag's whites, flats and lead are
    measured in the Regular's stem (arrows.pattern_stem). In the weight's
    own, of the H's advance at Regular, Bold and Black: ↛ 1.53, 2.05, 2.49;
    ↮ 1.71, 2.27, 2.80; ↝ 1.30, 1.54, 1.64; ⇝ 1.52, 1.82, 1.94, where the
    plain arrow went 1.18, 1.18, 1.40."""
    from arris.glyphs.arrows import pattern_stem, strike_at
    regular = params(400)
    assert strike_at(params(900)).sv == regular.sv and strike_at(params(300)).sv == params(300).sv
    assert pattern_stem(params(900)) == regular.sv and pattern_stem(params(300)) == params(300).sv
    at_regular = {'uni219B': 1.53, 'uni219A': 1.53, 'uni21AE': 1.71, 'uni21CF': 1.63, 'uni219D': 1.30, 'uni21DD': 1.52,
                  'uni21AD': 1.57}
    most = {'uni219B': 2.00, 'uni219A': 2.00, 'uni21AE': 2.35, 'uni21CF': 1.75, 'uni219D': 1.42, 'uni21DD': 1.76,
            'uni21AD': 1.76}
    for name, share in at_regular.items():
        assert _adv(name, regular) == pytest.approx(share, abs=0.02), name       # the Regular as it was
        for w in (700, 900):
            assert share - 0.02 <= _adv(name, params(w)) <= most[name], (name, w)
            assert len(getattr(_ink(name, params(w)), 'geoms', [0])) == 1, (name, w)


@pytest.mark.parametrize('w', [400, 600, 700, 800, 900])
def test_the_interrobang_is_a_question_mark_with_a_stroke_through_it(w):
    """Its exclamation stroke is added to the question mark: past the
    Regular it holds the Regular's weight, laid over. At the weight's own it
    filled the bowl's left half by Bold, the whole mark was lightened to
    keep the counter that was left (to 0.8 from Bold), and it read as a P.
    Under the top bar stand the beak, the stroke and the bowl's right side,
    white between them, and the mark is drawn in its weight's strokes, or
    all but (0.94 at Black)."""
    p = params(w)
    g = draw('uni203D', p)
    assert g.p.light >= 0.93
    (laid, _), = g.overlay
    assert laid.nodes[0].w == pytest.approx(min(p.sv, params(400).sv), rel=0.07)
    ink = rings_to_shapely(g.rings())
    runs = _runs(ink, y=p.cap - g.sh - 0.1 * p.sv)
    assert len(runs) == 3, runs
    (_, a1), (b0, b1), (c0, _) = runs
    assert b1 - b0 == pytest.approx(laid.nodes[0].w, abs=1.0)
    assert min(b0 - a1, c0 - b1) >= 0.4 * params(400).sv                    # (36 units under the beak at Regular)
    # and it stands on the bowl's return: nothing of it shows under the bowl's left end
    low = _runs(ink, y=laid.nodes[-1].y - 0.4 * g.sh)
    assert all(x0 >= b0 - p.sv for x0, _ in low), low


def test_a_column_of_dots_keeps_its_dots():
    """Four dots over the cap height keep 0.55 of the Regular's stem
    between them past it (genpunct.column_dot), and a dot smaller than the
    period's is broken in proportion. With 0.55 of the weight's own stem the
    dots were 119 units at Bold and 98 at Black, and broken on the weight's
    own leg they were diamonds."""
    from arris.glyphs.genpunct import column_dot
    sizes = [column_dot(params(w), 4) for w in (300, 400, 500, 600, 700, 800, 900)]
    assert sizes == sorted(sizes)
    for name, n in (('uni205D', 3), ('uni205E', 4)):
        for w in (400, 700, 900):
            p = params(w)
            dots = list(_ink(name, p).geoms)
            assert len(dots) == n, (name, w)
            for d in dots:
                x0, y0, x1, y1 = d.bounds
                assert d.area >= 0.8 * (x1 - x0) * (y1 - y0), (name, w)          # an octagon, not a diamond
            ys = sorted(d.bounds[1::2] for d in dots)
            assert min(b[0] - a[1] for a, b in itertools.pairwise(ys)) >= 0.5 * params(400).sv, (name, w)


@pytest.mark.parametrize('w', [300, 400, 700, 900])
def test_the_tironian_et_is_a_seven(w):
    """A bar on the x-height turning down at its right end into a stem to
    the descender. Until version 2 the bar ran on past the stem and the stem
    stopped on the line: a T."""
    p = params(w)
    g = draw('uni204A', p)
    ink = rings_to_shapely(g.rings())
    x0, y0, x1, y1 = ink.bounds
    assert y1 == pytest.approx(p.xh, abs=1.0) and y0 == pytest.approx(-p.under, abs=1.0)
    (a, b), = _runs(ink, y=0.0)
    assert b == pytest.approx(x1, abs=1.0) and b - a == pytest.approx(p.sv, abs=1.0)
    (a, b), = _runs(ink, y=p.xh - 0.5 * g.sh)
    assert a == pytest.approx(x0, abs=1.0) and b == pytest.approx(x1, abs=p.c + 1.0)


@pytest.mark.parametrize('name', ['uni231A', 'uni2328', 'uni23F0', 'uni23F1', 'uni23F2', 'uni2326', 'uni232B'])
def test_a_picture_is_the_regulars_drawing_at_every_heavier_weight(name):
    """The watch, the keyboard, the clocks and the erase keys
    (technical.picture). Their whites are the least a drawing may have at
    the Regular, so every unit a stroke gained past it went to the
    picture's size: at Black the watch stood 1.68 of the cap height tall
    for 1.25, the keyboard 1.48 for 0.90."""
    regular = _ink(name, params(400))
    for w in (500, 700, 900):
        g = draw(name, params(w))
        assert g.p.light == 1.0 and g.p.sv == params(400).sv, w
        assert rings_to_shapely(g.rings()).bounds == pytest.approx(regular.bounds, abs=0.5), w
        assert rings_to_shapely(g.rings()).area == pytest.approx(regular.area, rel=0.005), w


@pytest.mark.parametrize('w', [300, 400, 700, 900])
def test_integrals_side_by_side_stand_apart(w):
    """A hook's end keeps the least white off the next integral's stem
    (operators.int_step). The step left the beak's own half out: 22 units
    at Regular, 50 at Black."""
    from arris.glyphs.letterframe import least_white
    p = params(w)
    for name, n in (('uni222C', 2), ('uni222D', 3)):
        g = draw(name, p)
        parts = sorted(rings_to_shapely(g.rings()).geoms, key=lambda q: q.bounds[0])
        assert len(parts) == n
        for a, b in itertools.pairwise(parts):
            assert a.distance(b) >= 0.95 * least_white(g.p), (name, w)
    assert _adv('uni222C', params(900)) <= 1.7 and _adv('uni222D', params(900)) <= 2.35


def test_currency_signs_keep_their_share_of_the_line():
    """Of the H's ink across, from Regular to Black: the pound and the lira
    went 0.95 to 0.74 (a letter with one stem that made no room for its
    arms), the tenge and the tugrik 1.21 to 0.87, the sheqel 1.24 to 2.06,
    and the letters with bars grew with a bar that stood 0.9 of the
    weight's stem out of them (₦ 1.40 to 1.68, ₴ 1.32 to 1.59, ₩ 1.75 to
    2.06). The pound's body is the E's and the tenge's the T's; the
    bitcoin and the colón stand in their letters' bodies, and the cedi in
    the C's and a little more, its stroke the least white off the C's stem
    and beaks at Black; a bar's reach past its letter is the Regular's past
    it (currency.bar_out), as the bar is; the sheqel's four stems are a
    stack of parts."""
    from arris.glyphs.currency import bar_out
    regular, black = params(400), params(900)
    assert bar_out(black) == bar_out(regular) and bar_out(params(300)) <= bar_out(regular)
    same = {'sterling': 'E', 'lira': 'E', 'uni20B8': 'T', 'uni20AE': 'T', 'uni20BF': 'B', 'colonmonetary': 'C'}
    for name, letter in same.items():
        for w in (400, 700, 900):
            assert _wide(name, params(w)) == pytest.approx(_wide(letter, params(w)), abs=0.02), (name, w)
    at_regular = {'uni20A6': 1.40, 'uni20A9': 1.75, 'uni20B4': 1.32, 'uni20BD': 1.16, 'franc': 1.11, 'Euro': 1.17,
                  'uni20B1': 1.19, 'uni20AD': 1.24, 'uni20B3': 1.45}
    for name, share in at_regular.items():
        assert _wide(name, regular) == pytest.approx(share, abs=0.02), name      # the Regular as it was
        for w in (700, 900):
            assert share - 0.12 <= _wide(name, params(w)) <= share + 0.01, (name, w)
    from arris.glyphs.letterframe import least_white
    for w in (400, 700, 900):
        p = params(w)
        assert _wide('uni20B5', p) <= 1.14, w                                    # the cedi (it was 1.27 at Black)
        stem, stroke = _runs(_ink('uni20B5', p), y=p.cap / 2)
        assert stroke[0] - stem[1] >= 0.95 * least_white(p), w
    assert _wide('uni20AA', regular) == pytest.approx(1.24, abs=0.02)
    assert max(_wide('uni20AA', params(w)) for w in (700, 900)) <= 1.46
    for w in (400, 700, 900):
        assert 0.85 <= _wide('currency', params(w)) <= 1.0, w                    # (it was 0.70 at Regular)


def test_the_ellipsis_keeps_near_its_length_and_its_line():
    """Its dots stand the Regular's white apart past it (punct.dot_step):
    0.95 of the H's ink across at Regular, 1.20 at Bold, 1.35 at Black (it
    was 1.48 and 1.78; twenty-one families' heaviest 1.29, none over 1.62).
    In the monospaced cell its three dots are drawn for the cell
    (punct.ellipsis_dot) and stand on the baseline at every weight: fitted
    to it, they stood 89 units over the line at Bold."""
    from arris.instances import mono_weight, narrow_weight
    from arris.italic import italic
    assert _wide('ellipsis', params(400)) == pytest.approx(0.95, abs=0.02)
    assert _wide('ellipsis', params(700)) <= 1.25 and _wide('ellipsis', params(900)) <= 1.40
    assert _wide('uni22EF', params(900)) == pytest.approx(_wide('ellipsis', params(900)), abs=0.01)
    _, y0, _, y1 = _ink('uni22EE', params(900)).bounds
    assert y0 >= -0.1 * params(900).cap and y1 <= 1.1 * params(900).cap      # (it was -0.25 to 1.25)
    cuts = {'mono': lambda w: params(mono_weight(w)).with_(mono=True),
            'mono italic': lambda w: italic(params(mono_weight(w)).with_(mono=True)),
            'narrow': lambda w: params(narrow_weight(w)).with_(mono=True, narrow=True)}
    for cut, at in cuts.items():
        for w in (300, 400, 450, 500, 600, 700):
            p = at(w)
            dots = sorted(_ink('ellipsis', p).geoms, key=lambda q: q.bounds[0])
            assert len(dots) == 3, (cut, w)
            for d in dots:
                assert d.bounds[1] == pytest.approx(0.0, abs=0.5), (cut, w)
            sizes = [d.bounds[3] - d.bounds[1] for d in dots]
            assert min(sizes) >= 0.5 * p.dot(), (cut, w)
            whites = [b.bounds[0] - a.bounds[2] for a, b in itertools.pairwise(dots)]
            assert min(whites) >= 0.8 * max(sizes), (cut, w)
