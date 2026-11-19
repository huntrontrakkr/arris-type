"""Grade changes strokes, never a width: a graded glyph is spaced as its
ungraded self (font._place_drawn). Until 1.016 that self was not always the
plain master: its strokes, times the grade's factor and over it again, were
a last bit off (so no rule that asks whose parameters these are knew them:
draw._cut, and the barred letters' strokes were another weight's), and a
grade that scales nothing (a positive one at Black) was not ungraded at
all. 42 glyphs' advances moved with the grade, ⁜ by 140 units."""
from __future__ import annotations

import pytest

import arris.glyphs  # noqa: F401  (the registry)
from arris.font import place
from arris.vf.space import params

WEIGHTS = (100, 200, 300, 400, 500, 600, 700, 750, 800, 850, 900)


@pytest.mark.parametrize('italic', [False, True], ids=['upright', 'italic'])
def test_a_grades_ungraded_self_is_the_plain_master(italic):
    for w in WEIGHTS:
        for g in (-100, -50, 50, 100):
            for watch in (0, 100):
                assert params((w, g, watch), italic).ungraded() == params((w, 0, watch), italic), (w, g, watch)


@pytest.mark.parametrize('name', ['uni205C', 'uni21FF', 'lslash', 'uni20B1', 'uni2271', 'Oslash', 'A', 'i'])
@pytest.mark.parametrize('w, g', [(900, 100), (600, -100), (400, 100)])
def test_grade_moves_no_advance(name, w, g):
    assert place(name, params((w, g, 0), False))[1] == pytest.approx(place(name, params((w, 0, 0), False))[1], abs=0.01)


LETTERS = ['n', 'a', 's', 'f', 't', 'r', 'k', 'H', 'S', 'eight']


@pytest.mark.parametrize('watch', [0.0, 0.5, 1.0], ids=['arris', 'half way', 'watch'])
@pytest.mark.parametrize('w', [300, 400, 500, 600, 700, 800, 900])
def test_along_the_grade_axis_every_rule_runs_one_way(w, watch):
    """The grade is an axis to go across as the watch is (the owner,
    2026-11-11, of the watch axis: "we treat that as a gradient that you
    can go across"; and then: "what about the other one?"). From -100 to
    100 at a weight the strokes grow and nothing else is told a different
    weight: the stem never thins for a heavier grade; what a rule reads as
    the weight (the stem past the Regular's, the white the letters give,
    the r's share of the H) is the ungraded weight's at every grade, or
    runs one way; the f's stub by its stem runs one way; no advance moves;
    and the engine knows every graded place for a font's own (draw._cut).
    Checked at Arris's end, at the watch's, and half way between."""
    from itertools import pairwise

    from arris.draw import REGISTRY, _cut
    from arris.glyphs import lower
    from arris.instances import params as at
    from arris.italic import italic as slanted
    along = [at(w, g, watch=watch) for g in range(-100, 101, 25)]
    plain = at(w, 0, watch=watch)
    assert along[4].same(plain)
    stems = [p.sv for p in along]
    assert all(b >= a - 1e-9 for a, b in pairwise(stems)) and stems[0] == pytest.approx(0.8 * plain.sv)
    for p in along:                                                     # the weight a rule reads is the ungraded one's
        assert p.past == pytest.approx(plain.past) and p.white_low == pytest.approx(plain.white_low)
        assert p.sh / p.sv == pytest.approx(plain.sh / plain.sv) and p.sd / p.sv == pytest.approx(plain.sd / plain.sv)
        assert _cut(p) is not None and _cut(slanted(p)) is not None
    one_way = {'stub by the stem': lambda p: lower.stub(p) / p.sv, 'crossbar short by the stem': lambda p: lower.bar_short(p) / p.sv,
               "the r's share": lambda p: REGISTRY['r'].width(p) / REGISTRY['H'].width(p)}
    for name, fn in one_way.items():
        vals = [fn(p) for p in along]
        d = [b - a for a, b in pairwise(vals)]
        assert all(x >= -1e-9 for x in d) or all(x <= 1e-9 for x in d), (name, [round(v, 4) for v in vals])
    for name in LETTERS:
        for cut in (lambda p: p, slanted):
            adv = place(name, cut(plain))[1]
            for p in (along[0], along[8]):
                assert place(name, cut(p))[1] == pytest.approx(adv, abs=0.01), (name, p.grad)


@pytest.mark.parametrize('w', [700, 800, 900])
def test_a_graded_letter_stands_where_its_ungraded_self_does(w):
    """A grade thickens a letter where it stands. The narrow ones (no wider
    than two and a half stems) thicken outward from their middle, in the
    body their drawing has at the grade; that body was read off the
    upright's drawing, and the cursive l, whose body gives another share
    from ExtraBold (italic_forms.letter_width), stood 27 units to the right
    of its ungraded self at any grade at Black, in the same advance: found
    going along the grade axis step by step."""
    from arris.instances import params as at
    from arris.italic import italic as slanted
    def left(name, p):
        rings, _ = place(name, p)
        return min(q[0] for r in rings for q in r)
    k = at(w, -10).sv / at(w, 0).sv
    for name in ('l', 'i', 'j', 'f', 't', 'r'):
        for cut in (lambda p: p, slanted):
            x0 = left(name, cut(at(w, 0)))
            for g in (-10, -1, 1, 10):
                # no further than the strokes thin or thicken by (half a stem's change each side, and the slant's share)
                assert left(name, cut(at(w, g))) == pytest.approx(x0, abs=abs(1 - k) * at(w, 0).sv + 1.0), (name, g)


def test_at_black_a_positive_grade_leaves_the_a_as_it_is():
    """A positive grade fades out to Black, where it adds nothing to a
    stroke. The a's bowl at Black broke its left corners 55 units for 131
    at grade 80 and 100, and not at 85 or 90. Its foot is cut along its
    bar's own edge (lower.shoulder), so the cut's end and the corner
    before it are one point to the last bit; which side of the other each
    came out on decided whether the stroke's outline crossed itself, and
    when it did the stroke was taken for one whose bowls do not fit and
    they were shrunk to whatever size passed (geom.stroke_polygon). Two
    points of a stroke's side that are one are one edge the less
    (geom.SAME)."""
    from arris.instances import params as at

    def corner(g):                                          # where the bowl's corner cut meets the baseline
        rings, _ = place('a', at(900, g))
        outer = max(rings, key=len)
        return min(q[0] for q in outer if abs(q[1]) < 0.5)
    cuts = [corner(g) for g in (0, 20, 50, 75, 80, 85, 90, 100)]
    assert max(cuts) - min(cuts) < 1.0, cuts
