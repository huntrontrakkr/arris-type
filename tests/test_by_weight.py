"""Glyphs read character by character along the weights (2.0): what changed
between one weight and the next where nothing should, and the faults that
came and went with it."""
from __future__ import annotations

from itertools import pairwise

import pytest

import arris.glyphs  # noqa: F401  (the registry)
from arris import topology
from arris.draw import draw
from arris.font import place
from arris.geom import rings_to_shapely
from arris.instances import mono_weight, narrow_weight, params
from arris.italic import italic, polylines

CUTS = {'upright': params, 'italic': lambda w: italic(params(w))}
MONO_CUTS = {
    'mono': lambda w: params(mono_weight(w)).with_(mono=True),
    'mono italic': lambda w: italic(params(mono_weight(w)).with_(mono=True)).with_(cursive=True),
    'narrow': lambda w: params(narrow_weight(w)).with_(mono=True, narrow=True),
    'narrow italic': lambda w: italic(params(narrow_weight(w)).with_(mono=True, narrow=True)).with_(cursive=True),
}


def _advances(name, mk, weights):
    return [place(name, mk(w))[1] for w in weights]


@pytest.mark.parametrize('cut', list(CUTS))
def test_an_ogonek_joins_its_letter(cut):
    """marks.kept, joined: the fills where the ogonek meets its letter are
    grown back over the hair they were cut clear of the two by, and only a
    fill at the join is kept. Cut clear, a fill lay beside them and met them
    at a point (ę ǫ Ę Ų at every weight, į ą ų Ą Į from Medium); at 450 one
    was a diamond off the į's stem."""
    mk = CUTS[cut]
    for name in ('aogonek', 'eogonek', 'iogonek', 'uogonek', 'uni01EB', 'Aogonek', 'Eogonek', 'Iogonek', 'Uogonek'):
        counts = set()
        for w in (300, 400, 450, 500, 600, 700, 800, 900):
            p = mk(w)
            rings, _ = place(name, p)
            assert not topology.faults(rings, p.c, bool(p.slant)), (name, cut, w)
            ink = rings_to_shapely(draw(name, p).rings())
            counts.add((len(getattr(ink, 'geoms', [ink])), sum(len(q.interiors) for q in getattr(ink, 'geoms', [ink]))))
        assert len(counts) == 1, (name, cut, counts)


@pytest.mark.parametrize('cut', list(CUTS))
def test_the_brace_is_as_wide_a_unit_past_the_regular(cut):
    """punct._brace_cut: the point cut from where the Regular's stands. From
    its full reach, the cut began a unit past the Regular at nothing and
    the brace stood a fifth of a stem wider there, its tip near sharp."""
    a, b = _advances('braceleft', CUTS[cut], (400, 401))
    assert abs(b - a) < 2 if cut == 'upright' else abs(b - a) < 10


@pytest.mark.parametrize('cut', list(CUTS))
def test_the_qs_tail_leaves_its_counter_whole(cut):
    """caps.Q: the tail's upper end stands half a break off the counter's
    left wall. Run on to the wall, from 850 it shut a pinhole under it."""
    for w in (700, 800, 850, 900):
        ink = rings_to_shapely(draw('Q', CUTS[cut](w)).rings())
        assert sum(len(q.interiors) for q in getattr(ink, 'geoms', [ink])) == 1, (cut, w)


@pytest.mark.parametrize('cut', list(CUTS))
def test_the_return_arrows_head_clears_its_leg(cut):
    """arrows.LArrow: the shaft long enough for the head's barb to stand
    half a stem from the leg. To the letter's width, ↵ and ⏎ shut at 850."""
    for name in ('carriagereturn', 'uni23CE'):
        for w in (800, 850, 900):
            p = CUTS[cut](w)
            rings, _ = place(name, p)
            assert not topology.faults(rings, p.c, bool(p.slant)), (name, cut, w)


@pytest.mark.parametrize('name, cut, weights', [
    ('uni0237', 'italic', range(300, 901, 20)),        # ȷ: its tail's tip over the baseline at 360
    ('weierstrass', 'upright', range(180, 341, 20)),    # ℘: its loop's at 240
    ('napostrophe', 'upright', range(300, 461, 20)),    # ŉ: the apostrophe under the x-height at 370
    ('tcaron', 'upright', range(820, 901, 10)),         # ť: the t's stem read from its bar's top
    ('uni03F0', 'upright', range(780, 901, 20)),        # ϰ: its curls in three strokes from 840
    ('prescription', 'upright', range(300, 801, 20)),   # ℞: its cross an arm, not a hanging tail
])
def test_no_advance_jumps_between_neighbouring_weights(name, cut, weights):
    """spacing._edges (font.HANG), marks._caron_apostrophe, greek_ext.kappa_symbol:
    a glyph's advance moves with its weight, never by a stem at one step."""
    adv = _advances(name, CUTS[cut], weights)
    assert max(abs(b - a) for a, b in pairwise(adv)) < 25, (name, cut, [round(a) for a in adv])


@pytest.mark.parametrize('cut', list(CUTS))
def test_a_digraph_keeps_its_letters_ends_at_every_grade(cut):
    """latin_plus._digraph, _digraph_x: each letter at its own width, centred
    in its ungraded body; its place measured slanted and against the
    heaviest grade. Drawn to the ungraded body at grade -100 the l's and the
    j's feet came to a point; slanted, the j's hook ran under the l's foot."""
    for name in ('uni01C8', 'uni01C9', 'uni01CC'):
        advances = set()
        for grade in (-100, 0, 100):
            for w in (400, 700, 850, 900):
                p = params(w, grade)
                p = italic(p) if cut == 'italic' else p
                ends = [e for e in topology.stroke_ends(draw(name, p).rings(), p.c) if e[0] in ('point', 'thin')]
                assert not ends, (name, cut, grade, w)
                rings, adv = place(name, p)
                assert not topology.faults(rings, p.c, bool(p.slant)), (name, cut, grade, w)
                if w == 700:
                    advances.add(round(adv, 1))
        assert len(advances) == 1, (name, cut, advances)                    # grade moves nothing


def test_the_white_rule_lightens_nothing_lighter_than_the_regular():
    """draw: the white rule acts past the Regular. At the lighter weights
    it lightened ↯ to 0.8 up to 362 and let go at 364."""
    for name in ('uni21AF', 'uni2326', 'uni21DD'):
        for w in range(100, 400, 20):
            assert getattr(draw(name, params(w)), 'lightened', 1.0) == 1.0, (name, w)


@pytest.mark.parametrize('cut', list(MONO_CUTS))
def test_the_ringed_numerals_keep_their_whites_in_the_cell(cut):
    """numberforms._rings: in a body narrower than its stems and whites
    take, stems, whites and bars are drawn lighter together, the corners'
    legs with them. At the weight's own stems in the monospaced cell ↈ was
    a block from Arris Mono Regular (seven stems and six whites want 1176
    units at the Regular, the cell gives 540) and ↂ from SemiBold."""
    mk = MONO_CUTS[cut]
    for name, n in (('uni2182', 2), ('uni2188', 3)):
        for w in (300, 400, 500, 700):
            p = mk(w)
            rings, _ = place(name, p)
            ink = rings_to_shapely(polylines(rings) if p.slant else [[q[:2] for q in r] for r in rings]).buffer(0)
            parts = list(getattr(ink, 'geoms', [ink]))
            assert (len(parts), sum(len(q.interiors) for q in parts)) == (1, 2 * n), (name, cut, w)


@pytest.mark.parametrize('cut', list(CUTS) + list(MONO_CUTS))
def test_the_ka_with_a_stem_shows_it_below_the_arm(cut):
    """cyrillic_ext.Kavertical: Ҝ's short stem is an added stroke (held at
    the Regular, laid over), crossing the arm where arm and leg have parted,
    with white under it and over the leg. Two modules from K's stem at the
    weight's own thickness it stood where arm and leg meet: from SemiBold
    a bump on the arm with no white under it, and ҝ's nothing at Black."""
    mk = (CUTS | MONO_CUTS)[cut]
    for w in ((300, 400, 700, 900) if cut in CUTS else (300, 400, 600, 700)):
        p = mk(w)
        rings, _ = place('uni049C', p)
        assert not topology.faults(rings, p.c, bool(p.slant)), (cut, w)
        if not p.slant:
            g = draw('uni049C', p)
            (stem,), = [[st] for st, _ in g.overlay]
            x, lo = stem.nodes[0].x, stem.nodes[0].y
            ink = rings_to_shapely(g.rings())
            foot = rings_to_shapely([[(x - 1, lo - 0.5 * p.m), (x + 1, lo - 0.5 * p.m), (x + 1, lo - 1), (x - 1, lo - 1)]])
            assert ink.intersection(foot).area < 1.0, (cut, w)              # white under its foot
        assert not topology.faults(place('uni049D', p)[0], p.c, bool(p.slant)), (cut, w)


@pytest.mark.parametrize('name, w, grade', [
    ('uni03C1', 500, 0), ('uni03F1', 500, 0), ('uni20AF', 500, 0),   # ρ ϱ ₯: the bowl's foot on the stem
    ('k', 700, -100), ('uni0137', 700, -100), ('uni01E9', 700, -100),   # k ķ ǩ: the leg's crotch
])
def test_no_spike_at_an_exact_weight(name, w, grade):
    """geom._ring_rule: a point where the outline runs back on itself goes
    with the collinear ones. Where two edges fell exactly on one line (the
    italic ρ at 500 and not at 499.9 or 500.1, the k at Bold and grade
    -100) the union left a spike of no width along it."""
    p = italic(params(w, grade))
    rings, _ = place(name, p)
    assert not topology.faults(rings, p.c, True), (name, w, grade)


def test_the_tonos_stands_clear_of_its_capital_in_the_italic():
    """greek._italic_room: the italic rounds the capital's top left corner
    out toward its tonos; half a break more between them. Έ Ή Ί Ύ kept 9
    units of white at the Regular and met their tonos from SemiBold."""
    for name in ('uni0388', 'uni0389', 'uni038A', 'uni038E'):
        for w, grade in ((400, 0), (600, 0), (700, 100), (900, 0), (900, 100)):
            p = italic(params(w, grade))
            rings, _ = place(name, p)
            ink = rings_to_shapely(polylines(rings)).buffer(0)
            tonos, letter = sorted(ink.geoms, key=lambda q: q.bounds[0])
            assert tonos.distance(letter) >= 15, (name, w, grade)


@pytest.mark.parametrize('name, cut, w', [
    ('uni04A2', 'italic', 900), ('uni04B6', 'italic', 900), ('uni0524', 'italic', 900),   # Ң Ҷ Ԥ: descender into tick
    ('uni04AC', 'italic', 900), ('uni04CB', 'italic', 900),                              # Ҭ Ӌ
    ('uni03B5', 'italic', 850), ('epsilontonos', 'italic', 850),                        # ε έ
    ('threequarters', 'italic', 600), ('three.sups', 'italic', 600),                    # the small italic 3
])
def test_no_edge_under_a_unit(name, cut, w):
    """geom._unjogged: the jog closer moves an edge onto its neighbour's
    line, and where that left a wall under a unit between two cuts the
    polish closes it as it closes any micro-flat."""
    p = CUTS[cut](w)
    rings, _ = place(name, p)
    assert not topology.faults(rings, p.c, bool(p.slant)), (name, cut, w)


@pytest.mark.parametrize('cut', list(MONO_CUTS))
def test_the_d_with_a_bar_keeps_one_counter(cut):
    """extra_latin.Dcroat: the bar stops the least white short of the
    bowl's inside. In Arris Mono Narrow at Bold, the D drawn narrow for its
    cell, it ran on to the bowl and cut the counter in two."""
    for name in ('Dcroat', 'Eth'):
        for w in (300, 400, 600, 700):
            p = MONO_CUTS[cut](w)
            rings, _ = place(name, p)
            ink = rings_to_shapely(polylines(rings) if p.slant else [[q[:2] for q in r] for r in rings]).buffer(0)
            assert sum(len(q.interiors) for q in getattr(ink, 'geoms', [ink])) == 1, (name, cut, w)


@pytest.mark.parametrize('cut', list(CUTS))
def test_the_prescription_sign_keeps_its_x(cut):
    """letterlike.prescription: the R keeps its leg at the weight's own
    thickness, the cross is held at the Regular and laid over it, and the
    crossing climbs the leg as the leg grows (RX_CLIMB). Crossed at the
    Regular's place with a cross as heavy as the leg, the x filled in from
    SemiBold and was a boot under the R from ExtraBold (the owner: "not
    legible at deep black"). Its four arms stand apart: two strokes across
    a line a fifth of the way up from the foot, and two over the
    crossing."""
    from shapely.geometry import LineString

    from arris.draw import held_at
    from arris.glyphs.letterlike import RX_CLIMB, _rx
    for w in (400, 600, 700, 800, 900):
        for grade in (0, 100):
            p = CUTS[cut](w) if not grade else (italic(params(w, grade)) if cut == 'italic' else params(w, grade))
            g = draw('prescription', p)
            ink, q = rings_to_shapely(g.rings()), g.p
            _, a, yc, e = _rx(q)
            yc += RX_CLIMB * max(0.0, q.sd - held_at(q).sd)
            bot = -0.9 * q.under
            for y in (bot + 0.2 * (yc - bot), yc + 0.6 * e):
                cut_ = ink.intersection(LineString([(a - yc - 1.2 * e, y), (a - yc + 1.2 * e, y)]))
                assert len(getattr(cut_, 'geoms', [cut_])) == 2, (cut, w, grade, round(y))
            rings, _ = place('prescription', p)
            assert not topology.faults(rings, p.c, bool(p.slant)), (cut, w, grade)


ALL_CUTS = {**CUTS, **MONO_CUTS}


@pytest.mark.parametrize('cut', list(ALL_CUTS))
def test_the_double_struck_q_keeps_its_tail_off_the_inner_stroke(cut):
    """letterlike.dsQ: ℚ is the Q drawn with its inner stroke, the tail cut
    back from the inner stroke as the Q's is from the counter's wall, and
    measured on the counter the inner stroke leaves. Stamped wider, its
    counter ran on under the inner stroke: from 850 the tail's end met it
    and shut a pinhole in the italic, and in Arris Mono from Bold the two
    crossed."""
    weights = (300, 400, 450, 500, 600, 700) if cut in MONO_CUTS else (400, 700, 800, 850, 900)
    for w in weights:
        p = ALL_CUTS[cut](w)
        rings, _ = place('uni211A', p)
        assert not topology.faults(rings, p.c, bool(p.slant)), (cut, w)
        ink = rings_to_shapely(polylines(rings) if p.slant else [[q[:2] for q in r] for r in rings]).buffer(0)
        assert len(getattr(ink, 'geoms', [ink])) == 1, (cut, w)
        assert sum(len(q.interiors) for q in getattr(ink, 'geoms', [ink])) == 2, (cut, w)


@pytest.mark.parametrize('cut', list(CUTS))
def test_the_question_mark_keeps_its_stem_over_the_dot(cut):
    """punct.dot_gap, question_return: the white over a dot is the
    Regular's past it, never under DOT_WHITE of a stem (the half stroke the
    white rule reads as white), and the question mark's bowl returns high
    enough to leave a quarter of a stem of its stem showing, its bars giving
    way above as the S's do. At 0.8 of the weight's own stem over the dot,
    the dot came up into the bowl from ExtraBold, the stem was gone and the
    stroke turned down into its own end; at Black it was another drawing.
    The italic, whose beak is the longer, keeps its stem to ExtraBold and
    ends the stroke in the return at Black. The marks are drawn at their
    weight: at the Regular's white over the dot, the exclamation mark had no
    white the rule could read and was lightened to 0.8 from Bold."""
    from arris.glyphs.letterframe import Frame
    from arris.glyphs.punct import DOT_WHITE, QUESTION_NECK, dot_gap, question_return
    for w in (400, 600, 700, 800, 850, 900):
        p = CUTS[cut](w)
        g = draw('question', p)
        q = g.p
        neck = question_return(g, Frame(g, 9, 'cap')) - g.sh / 2 - (q.dot() + dot_gap(q))
        if cut == 'upright' or w <= 800:
            assert neck >= 0.8 * QUESTION_NECK * q.sv, (cut, w, round(neck))
        assert dot_gap(q) >= DOT_WHITE * q.sv - 1e-6
        rings, _ = place('question', p)
        assert not topology.faults(rings, p.c, bool(p.slant)), (cut, w)
        for name in ('exclam', 'question', 'exclamdown', 'questiondown', 'uni203D', 'uni2047', 'uni2048', 'exclamdbl'):
            assert draw(name, p).p.light == 1.0, (name, cut, w)


@pytest.mark.parametrize('cut', list(CUTS))
def test_a_question_mark_led_in_keeps_its_bay(cut):
    """punct.question_lead: in `#?` and `??` a bar leads into the ? in
    place of its beak, and the bowl keeps the beak's white under it (the
    return comes down for it, its stem the less); the `??`'s bar comes in
    where the second ?'s own beak ends. Led in below the beak, with the
    return on its own row, the bowl shut on itself in a pinch in the italic
    from Bold. (`#?` from ExtraBold has no room under the # bar for the
    bowl's white at all, and its bowl closes: left for the owner.)"""
    for name, weights in (('numbersign_question.liga', (400, 600, 700, 750)),
                          ('question_question.liga', (400, 700, 750, 800, 850, 900))):
        for w in weights:
            for grade in (-100, 0, 100):
                p = params(w, grade)
                p = italic(p) if cut == 'italic' else p
                rings, _ = place(name, p)
                assert not topology.faults(rings, p.c, bool(p.slant)), (name, cut, w, grade)


@pytest.mark.parametrize('cut', list(MONO_CUTS))
def test_the_ka_with_a_stroke_keeps_its_bar_off_the_arm(cut):
    """cyrillic_ext.Kastroke: where the bar has risen to the top of the stem
    and the arm still comes in under it, its end stops the least white short
    of the arm. In Arris Mono Narrow Italic it met the arm in a pinch from
    500 and crossed it at 550."""
    for name in ('uni049E',):
        for w in (300, 400, 450, 500, 550, 600, 700):
            p = MONO_CUTS[cut](w)
            rings, _ = place(name, p)
            assert not topology.faults(rings, p.c, bool(p.slant)), (name, cut, w)


@pytest.mark.parametrize('cut', list(MONO_CUTS))
def test_the_diagonal_ellipses_keep_three_dots_in_the_cell(cut):
    """operators._diagonal_dots: where the cell is narrower than the step
    across, the step up stays the dots' own. Stepped as little up as across,
    ⋰'s dots ran into one in Arris Mono Narrow Italic from 650."""
    for name in ('uni22F0', 'uni22F1'):
        for w in (300, 400, 500, 600, 700):
            p = MONO_CUTS[cut](w)
            rings, _ = place(name, p)
            ink = rings_to_shapely(polylines(rings) if p.slant else [[q[:2] for q in r] for r in rings]).buffer(0)
            assert len(getattr(ink, 'geoms', [ink])) == 3, (name, cut, w)


def test_the_italic_delta_keeps_its_bowl_whole():
    """greek.delta: the neck, settled a little more upright where the italic's
    round of the bowl's top right corner would take the flat beside its
    foot. At Thin on the heavy grade the round took the flat and the neck's
    edge with it, and the outline cut across the counter."""
    for w in (100, 110, 120, 150, 400, 900):
        for grade in (-100, 0, 90, 100):
            p = italic(params(w, grade))
            rings, _ = place('uni03B4', p)
            assert not topology.faults(rings, p.c, True), (w, grade)
            ink = rings_to_shapely(polylines(rings)).buffer(0)
            assert sum(len(q.interiors) for q in getattr(ink, 'geoms', [ink])) == 1, (w, grade)


def test_the_tugrik_has_no_half_unit_edge_at_the_baseline():
    """currency.tugrik: its pair of strokes settled a unit or two down where
    the lower one's underside, cut by the baseline, left an edge of half a
    unit beside the stem's foot in the italic at Black on the heavy grade."""
    for grade in (0, 100):
        for w in (800, 850, 900):
            p = italic(params(w, grade))
            rings, _ = place('uni20AE', p)
            assert not topology.faults(rings, p.c, True), (w, grade)


def _bars_and_ink(name, p):
    """The outer edges of a sign's upright bars (read across their tops, under
    the corners) and its ink's extent, as drawn before the curves and the slant."""
    from shapely.geometry import LineString
    ink = rings_to_shapely([[q[:2] for q in r] for r in draw(name, p).rings()]).buffer(0)
    x0, _, x1, y1 = ink.bounds
    y = y1 - 1.5 * p.c
    across = ink.intersection(LineString([(x0 - 10, y), (x1 + 10, y)]))
    bars = sorted(s.bounds[::2] for s in getattr(across, 'geoms', [across]))
    return bars, (x0, x1)


@pytest.mark.parametrize('cut', list(ALL_CUTS))
def test_the_struck_bars_are_crossed_through(cut):
    """operators.negate_across: ∤ and ∦ are struck by the not-equal sign's
    stroke turned a quarter, reaching past the outer bars as far as an
    arrow's negation reaches past its shafts. Struck at 2:1 as the not-equal
    sign is, ∦'s stroke ended inside both bars at every weight and it read
    as a Cyrillic И. In a cell narrower than the sign the stroke's reach
    gives way before the white between the bars does."""
    weights = (300, 400, 500, 600, 700) if cut in MONO_CUTS else (100, 400, 700, 900)
    for w in weights:
        p = ALL_CUTS[cut](w)
        for name, n in (('uni2224', 1), ('uni2226', 2)):
            bars, (x0, x1) = _bars_and_ink(name, p)
            assert len(bars) == n, (name, cut, w, bars)
            assert bars[0][0] - x0 >= 0.5 * p.m and x1 - bars[-1][1] >= 0.5 * p.m, (name, cut, w, bars, x0, x1)
            rings, _ = place(name, p)
            assert not topology.faults(rings, p.c, bool(p.slant)), (name, cut, w)
        plain, _ = _bars_and_ink('uni2225', p)
        struck, _ = _bars_and_ink('uni2226', p)
        # (Arris Mono Italic draws it a tenth smaller to fit the cell, as it does any sign whose ink would lean out)
        assert struck[1][0] - struck[0][1] >= 0.85 * (plain[1][0] - plain[0][1]), (cut, w, plain, struck)


@pytest.mark.parametrize('cut', list(ALL_CUTS))
def test_the_open_headed_arrow_keeps_a_shaft_between_its_heads(cut):
    """arrows.Spec.depth: the run between ⇿'s two open heads is counted clear
    of their backs. Counted from the middle of each back, the white between
    the backs was half a stem from 550 (65 units at Black for a stem of 200,
    35 in Arris Mono Narrow) and the shaft's two joins met in a pinch."""
    from shapely.geometry import LineString
    weights = (300, 400, 500, 600, 700) if cut in MONO_CUTS else (400, 550, 700, 900)
    for w in weights:
        p = ALL_CUTS[cut](w)
        ink = rings_to_shapely([[q[:2] for q in r] for r in draw('uni21FF', p).rings()]).buffer(0)
        x0, y0, x1, y1 = ink.bounds
        y = (y0 + y1) / 2 + 0.5 * p.sh + 1.5 * p.c + 2         # just clear of the shaft and its joins
        across = ink.intersection(LineString([(x0 - 10, y), (x1 + 10, y)]))
        segs = sorted(s.bounds[::2] for s in getattr(across, 'geoms', [across]))
        mid = (x0 + x1) / 2
        white = [b[0] - a[1] for a, b in pairwise(segs) if a[1] <= mid <= b[0]]
        assert white and white[0] >= 0.7 * p.sv, (cut, w, white, p.sv)
        rings, _ = place('uni21FF', p)
        assert not topology.faults(rings, p.c, bool(p.slant)), (cut, w)


def test_the_benzene_ring_is_one_drawing_everywhere():
    """technical.benzene: ⌬ is the textbook ring (a regular hexagon on a
    point, a bond along every other side), the same outline in every font,
    at every weight and grade, upright in the italics. Drawn with each
    weight's strokes and 2:1 slopes, its ring shut in Arris Mono Narrow
    Italic at 450 and it leaned with the italic."""
    from shapely import affinity

    def ink(p):
        rings, _ = place('uni232C', p)
        assert not topology.faults(rings, p.c, False)
        shape = rings_to_shapely(polylines(rings) if p.slant else [[q[:2] for q in r] for r in rings]).buffer(0)
        return affinity.translate(shape, -shape.bounds[0], 0)
    ref = ink(params(400))
    parts = getattr(ref, 'geoms', [ref])
    assert len(parts) == 4 and sum(len(q.interiors) for q in parts) == 1
    for cut, mk in ALL_CUTS.items():
        for w in (300, 400, 700) if cut in MONO_CUTS else (100, 400, 900):
            assert ink(mk(w)).symmetric_difference(ref).area < 1.0, (cut, w)
    for grade in (-100, 100):
        for w in (100, 900):
            assert ink(params(w, grade)).symmetric_difference(ref).area < 1.0, (w, grade)
            assert ink(italic(params(w, grade))).symmetric_difference(ref).area < 1.0, (w, grade)


@pytest.mark.parametrize('cut', list(MONO_CUTS))
def test_the_hourglass_keeps_its_shape_in_the_cell(cut):
    """technical._hourglass: in a cell narrower than the glass its sides run
    steeper (to 4:1), the neck's white narrowing and the strokes lightening
    only where that does not fit. Kept at 2:1 and shortened, the sides were
    a third of the glass's height in Arris Mono Narrow at Bold and the white
    a third of the way up as narrow as at the waist (an I between two bars),
    and ⏳'s sand was gone there and in the italic cells from Bold."""
    from shapely.geometry import LineString

    def white_at(ink, y, x0, x1):
        across = ink.intersection(LineString([(x0 - 5, y), (x1 + 5, y)]))
        segs = sorted(s.bounds[::2] for s in getattr(across, 'geoms', [across]))
        mid = (x0 + x1) / 2
        return next((b[0] - a[1] for a, b in pairwise(segs) if a[1] <= mid <= b[0]), 0.0)

    def pieces(p):
        rings, _ = place('uni23F3', p)
        assert not topology.faults(rings, p.c, bool(p.slant)), (cut, p)
        ink = rings_to_shapely(polylines(rings) if p.slant else [[q[:2] for q in r] for r in rings]).buffer(0)
        return len(getattr(ink, 'geoms', [ink]))
    regular = pieces(MONO_CUTS[cut](400))
    for w in (300, 400, 450, 500, 600, 700):
        p = MONO_CUTS[cut](w)
        ink = rings_to_shapely([[q[:2] for q in r] for r in draw('uni231B', p).rings()]).buffer(0)
        x0, y0, x1, y1 = ink.bounds
        a, h = (y0 + y1) / 2, (y1 - y0) / 2
        waist = white_at(ink, a, x0, x1)
        bulbs = min(white_at(ink, a + h / 3, x0, x1), white_at(ink, a - h / 3, x0, x1))
        assert waist <= 0.75 * bulbs, (cut, w, waist, bulbs)
        assert pieces(p) == regular, (cut, w)


@pytest.mark.parametrize('cut', list(ALL_CUTS))
def test_the_per_mille_rings_are_one_size(cut):
    """punct.pct_rings_after: ‰'s and ‱'s rings after the % are drawn at
    the measures the % was drawn with. In the monospaced cell the % is
    fitted to its own cell, its rings drawn smaller, and the rings drawn
    beside it at the sign's own stood a third larger (Arris Mono Italic at
    every weight, Mono Narrow from 500)."""
    weights = (300, 400, 500, 600, 700) if cut in MONO_CUTS else (100, 400, 700, 900)
    for w in weights:
        p = ALL_CUTS[cut](w)
        for name in ('perthousand', 'uni2031'):
            from shapely.geometry import Polygon
            ink = rings_to_shapely([[q[:2] for q in r] for r in draw(name, p).rings()]).buffer(0)
            counters = [Polygon(h) for q in getattr(ink, 'geoms', [ink]) for h in q.interiors]
            sizes = [(q.bounds[2] - q.bounds[0], q.bounds[3] - q.bounds[1]) for q in counters]
            lower = [s for q, s in zip(counters, sizes) if q.bounds[1] < 0.25 * p.cap]
            assert len(lower) >= (2 if name == 'perthousand' else 3), (name, cut, w, sizes)
            assert max(s[0] for s in lower) - min(s[0] for s in lower) <= 2, (name, cut, w, lower)


@pytest.mark.parametrize('cut', list(MONO_CUTS))
def test_the_caron_apostrophe_stands_apart_in_the_cell(cut):
    """marks._caron_apostrophe: ď ľ ť Ľ keep a white between the letter and
    its apostrophe in the monospaced cells, the apostrophe placed by its own
    ink. Its tail reached past the measure that placed it, and from Arris
    Mono Regular it ran into the stem."""
    for name in ('dcaron', 'lcaron', 'tcaron', 'Lcaron'):
        for w in (300, 400, 500, 600, 700):
            p = MONO_CUTS[cut](w)
            rings, _ = place(name, p)
            ink = rings_to_shapely(polylines(rings) if p.slant else [[q[:2] for q in r] for r in rings]).buffer(0)
            assert len(getattr(ink, 'geoms', [ink])) == 2, (name, cut, w)


@pytest.mark.parametrize('cut', list(CUTS))
def test_the_tugrik_shows_its_pair_on_both_sides_of_the_stem(cut):
    """currency.tugrik: two strokes cross the T's stem rising one for two,
    each reaching past it alike on both sides, centred between the bar and
    the baseline. At 45 degrees from 800 the pair stood so low that the
    lower stroke's left arm went under the baseline: one arm left of the
    stem."""
    from shapely.geometry import LineString
    for w in (100, 400, 600, 700, 800, 900):
        p = CUTS[cut](w)
        g = draw('uni20AE', p)
        ink = rings_to_shapely([[q[:2] for q in r] for r in g.rings()]).buffer(0)
        y = p.cap - g.sh - 0.3 * p.m                       # just under the bar, over the pair
        x0, _, x1, _ = ink.intersection(LineString([(-1e3, y), (1e4, y)])).bounds
        for x in (x0 - 0.4 * p.m, x1 + 0.4 * p.m):
            across = ink.intersection(LineString([(x, 1), (x, y)]))
            assert len(getattr(across, 'geoms', [across])) == 2, (cut, w, x)


@pytest.mark.parametrize('cut', list(ALL_CUTS))
def test_the_cruzeiro_r_is_one_drawing_standing_in_the_c(cut):
    """currency.cruzeiro: ₢'s r is drawn apart from the C, one drawing in
    one place from the Regular to the cut's heaviest weight, its stem run
    down into the C's bottom bar and a white all round it elsewhere. Drawn
    at each weight's strokes against the C's mouth, the C's lower beak ran
    into it from Bold and at Black the two were one shape."""
    from shapely import affinity
    from shapely.geometry import box

    def parts(p):
        rings, _ = place('uni20A2', p)
        assert len(rings) == 1 and not topology.faults(rings, p.c, bool(p.slant)), (cut, p.sv)
        rr = polylines(rings) if p.slant else [[q[:2] for q in r] for r in rings]
        ink = rings_to_shapely(rr).buffer(0).intersection(box(-1e4, 0.36 * p.cap, 1e4, 1e4))
        from shapely.ops import unary_union
        pieces = sorted(getattr(ink, 'geoms', [ink]), key=lambda q: q.area)
        c = pieces[-1]                                      # (the italic's lower beak rises past the line: a piece)
        assert len(pieces) >= 2, (cut, p.sv)                # above its foot the r stands apart from the C
        r = min(pieces[:-1], key=lambda q: q.bounds[0])
        assert r.distance(unary_union([q for q in pieces if q is not r])) >= 30, (cut, p.sv)
        x0, y0 = r.bounds[:2]
        return affinity.translate(r, -x0, -y0), (x0 - c.bounds[0], y0)

    def same(a, b):
        return a[0].hausdorff_distance(b[0]) < 1.0 and abs(a[1][0] - b[1][0]) < 3 and abs(a[1][1] - b[1][1]) < 3
    mk = ALL_CUTS[cut]
    heavy = (400, 500, 600, 700) if cut in MONO_CUTS else (400, 600, 800, 900)
    ref = parts(mk(heavy[0]))
    for w in (100, 300) + heavy[1:]:
        r = parts(mk(w))
        assert w < heavy[0] or same(r, ref), (cut, w)
    if cut in CUTS:
        for grade in (-100, 100, 200):
            p = params(900, grade) if cut == 'upright' else italic(params(900, grade))
            assert same(parts(p), ref), (cut, grade)


@pytest.mark.parametrize('cut', list(MONO_CUTS))
def test_the_per_mille_signs_shrink_smoothly_in_the_cell(cut):
    """punct.percent_part: ‰ ‱ are fitted to the cell as a whole, the %
    inside them drawn at their measures. Drawn as a glyph, the % was fitted
    again, to its own cell, at some of the measures the fit tried and not at
    others: Arris Mono Narrow's ‰ stood a ninth taller at 500 than at 490,
    and ‱ a fifth wider."""
    for name in ('perthousand', 'uni2031'):
        sizes = []
        for w in (450, 475, 490, 500, 525, 550):
            rings, _ = place(name, MONO_CUTS[cut](w))
            rr = polylines(rings) if 'italic' in cut else [[q[:2] for q in r] for r in rings]
            xs = [q[0] for r in rr for q in r]
            ys = [q[1] for r in rr for q in r]
            sizes.append((max(xs) - min(xs), max(ys) - min(ys)))
        for (w0, h0), (w1, h1) in pairwise(sizes):
            assert w1 <= w0 + 4 and abs(h1 - h0) < 12, (name, cut, sizes)
