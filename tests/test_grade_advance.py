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
