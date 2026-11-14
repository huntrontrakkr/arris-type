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
