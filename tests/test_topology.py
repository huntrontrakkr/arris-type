"""The topology check knows a fold from a corner: synthetic outlines, then a
sample of the engine's drawings at the heavy corners of the design space,
which must not cross themselves anywhere."""
from __future__ import annotations

import pytest

import arris.glyphs  # noqa: F401  (the registry)
from arris import italic as IT
from arris.font import place
from arris.instances import params
from arris.topology import HAIRPIN, PINCH, TINY, faults

C = 20.0    # a break, for the synthetic shapes


def _kinds(contours, c=C, **kw):
    return sorted({f.kind for f in faults(contours, c, **kw)})


def test_a_chamfered_square_is_clean():
    sq = [(0, 20), (20, 0), (180, 0), (200, 20), (200, 180), (180, 200), (20, 200), (0, 180)]
    assert _kinds([sq]) == []


def test_a_square_with_a_square_hole_is_clean():
    outer = [(0, 0), (300, 0), (300, 300), (0, 300)]
    hole = [(100, 100), (100, 200), (200, 200), (200, 100)]
    assert _kinds([outer, hole]) == []


def test_a_bow_tie_crosses_and_its_wedge_is_measured():
    bow = [(0, 0), (200, 200), (200, 0), (0, 200)]
    fs = faults([bow], C)
    assert [f.kind for f in fs if f.kind == 'cross'] == ['cross']
    assert next(f for f in fs if f.kind == 'cross').size >= 90


def test_a_spike_is_a_hairpin():
    spike = [(0, 0), (200, 0), (200, 200), (100, 200), (100, 260), (99, 200), (0, 200)]
    fs = faults([spike], C)
    assert any(f.kind == 'hairpin' and f.size > HAIRPIN for f in fs)


def test_a_tiny_edge_is_found_and_can_be_left_out():
    sq = [(0, 0), (200, 0), (200, 200), (100.5, 200), (100, 200), (0, 200)]
    assert 'tiny' in _kinds([sq])
    assert 'tiny' not in _kinds([sq], tiny=False)
    assert all(f.size < TINY for f in faults([sq], C) if f.kind == 'tiny')


def test_a_pinch_is_found_only_where_the_contour_is_large():
    # a U whose arms come within a sixth of a break of each other
    gap = PINCH * C / 4
    u = [(0, 0), (300, 0), (300, 300), (150 + gap, 300), (150 + gap, 100), (150 - gap, 100), (150 - gap, 300), (0, 300)]
    assert 'pinch' in _kinds([u])
    # the same shape at the size of a counter opening between two masters is not a pinch
    small = [(x / 20, y / 20) for x, y in u]
    assert 'pinch' not in _kinds([small])


def test_two_contours_that_cross_meet():
    a = [(0, 0), (200, 0), (200, 200), (0, 200)]
    b = [(100, 100), (300, 100), (300, 300), (100, 300)]
    assert 'meet' in _kinds([a, b])


def test_the_dense_pass_reports_crossings_alone():
    bow = [(0, 0), (200, 200), (200, 0), (0, 200), (0.5, 200)]
    assert _kinds([bow], every=False) == ['cross']


SAMPLE = ['t', 'tbar', 'ccedilla', 'uni04E1', 'uni01B7', 'a', 'e', 'g', 'eight', 'ampersand', 'uni0436']
PLACES = [(900, 100, 100), (900, 0, 0), (850, -100, 100), (700, 100, 0), (100, 100, 100)]


@pytest.mark.parametrize('style', ['upright', 'italic'])
def test_the_drawings_never_cross_themselves(style):
    crossed = []
    for name in SAMPLE:
        for w, g, x in PLACES:
            p = params(w, g, watch=x / 100)
            if style == 'italic':
                p = IT.italic(p)
            rings, _ = place(name, p)
            contours = rings if style == 'italic' else [[(q[0], q[1], True) for q in r] for r in rings]
            for f in faults(contours, p.c, style == 'italic', every=False):
                crossed.append((name, (w, g, x), f.kind, f.size))
    assert crossed == []


def test_the_build_sizes_a_fold_the_same_way():
    from arris.vf.measure import fold
    bow = [(0, 0), (200, 200), (200, 0), (0, 200)]
    square = [(0, 0), (200, 0), (200, 200), (0, 200)]
    assert fold([square]) == 0.0
    assert fold([bow]) >= 90
