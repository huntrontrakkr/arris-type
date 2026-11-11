"""Arris's weights past the Regular (1.017). Each adds to the Regular's stem
four fifths of what the watch's weight of that name adds, so Black draws
the stem of the watch's ExtraBold, 158 units, where it drew 175: there, in
the widths the letters have past the Regular, the n's counter was narrower
than its stems, and the round's repairs were all at that end (the owner,
2026-11-11, to dropping that Black: "we should do that but we need to
rescale everything after regular"). The watch's own drawing, Arris Watch
and the watch's end of the variable font, keeps the watch's weights, its
SemiBold the watch's figures ("Watch cut keeps its weights"). Nothing is
drawn that was not: a weight of Arris is the drawing the watch's ladder has
at its stem."""
from __future__ import annotations

from itertools import pairwise

import pytest

import arris.glyphs  # noqa: F401  (the registry)
from arris.draw import _cut
from arris.font import place
from arris.instances import (
    NAMES,
    OPTICS,
    PAST_REGULAR,
    STEMS,
    WATCH_STEMS,
    drawn,
    low_share,
    narrow_weight,
    params,
    stem,
    watch_weight,
    weight_of,
)
from arris.italic import italic


def test_past_the_regular_a_weight_adds_four_fifths_of_what_the_watchs_adds():
    assert set(STEMS) == set(WATCH_STEMS) == set(NAMES)
    regular = WATCH_STEMS[400]
    for w, s in WATCH_STEMS.items():
        assert STEMS[w] == pytest.approx(s if w <= 400 else regular + PAST_REGULAR * (s - regular)), w
    assert STEMS[900] == WATCH_STEMS[800] == 158 and STEMS[700] == 130     # Black the watch's ExtraBold, Bold its 650
    steps = [STEMS[b] / STEMS[a] for a, b in zip(range(400, 900, 100), range(500, 901, 100))]
    assert all(1.09 < k < 1.15 for k in steps), steps                      # each a tenth to a seventh heavier than the last


@pytest.mark.parametrize('w', [100, 250, 400, 433, 500, 600, 650, 700, 800, 850, 900])
def test_a_weight_of_arris_is_a_drawing_the_watchs_ladder_has(w):
    p = params(w)
    assert p.sv == pytest.approx(stem(w)) and weight_of(p.sv) == pytest.approx(w)
    d = watch_weight(p.sv)                                              # the watch's weight with that stem
    assert d == pytest.approx(w) if w <= 400 else 400 < d < w
    assert drawn(d).same(p)
    # and the engine knows it for a font's own, at the watch's weight: until 1.017 only a weight
    # round to a thousandth was (a set it took for a derived one, small capitals', is filled otherwise)
    for q in (p, italic(p), p.with_(mono=True)):
        cut = _cut(q)
        assert cut is not None and cut[0] == pytest.approx(d), w
        assert cut[1](400).sv == STEMS[400]


def _same_outline(a, b):
    (ra, wa), (rb, wb) = a, b
    return wa == pytest.approx(wb, abs=0.01) and len(ra) == len(rb) and all(
        len(x) == len(y) and all(p[:2] == pytest.approx(q[:2], abs=0.01) for p, q in zip(x, y)) for x, y in zip(ra, rb))


@pytest.mark.parametrize('w,was', [(900, 800), (700, 650), (600, 560), (500, 480)])
def test_each_weight_is_the_drawing_of_the_watchs_weight_with_its_stem(w, was):
    """Black to the last point the ExtraBold it was, Bold the 650 the owner
    chose the f's and the t's crossing at."""
    for name in ('n', 'e', 'a', 'g', 'k', 'dollar', 'ampersand', 'eight'):
        for cut in (lambda q: q, italic, lambda q: q.with_(mono=True)):
            assert _same_outline(place(name, cut(params(w))), place(name, cut(drawn(was)))), (name, w)


@pytest.mark.parametrize('w', [100, 400, 600, 800, 900])
def test_the_watchs_own_drawing_keeps_its_weights(w):
    p = params(w, watch=1.0)
    assert p.sv == WATCH_STEMS[w] and drawn(w, watch=1.0).same(p)
    assert params(600, watch=1.0).sv == 2 * p.m                         # the watch's figures: stems of two modules
    half = params(w, watch=0.5)                                         # between the two, straight: as the variable font carries it
    assert half.sv == pytest.approx((STEMS[w] + WATCH_STEMS[w]) / 2)
    assert _cut(half) is not None and _cut(italic(half)) is not None


def test_a_positive_grade_adds_nothing_at_a_cuts_black():
    assert params(900, 100).sv == pytest.approx(158) and params(900, 100).grade_k == 1.0
    assert params(900, 100, watch=1.0).sv == pytest.approx(175)
    assert params(600, 100).sv == pytest.approx(1.2 * 114)
    heavier = [params(w, 100).sv for w in range(400, 901, 50)]
    assert heavier == sorted(heavier)                                   # never lighter for a heavier weight
    for g in (-100, 100):
        for q in (params(750, g), italic(params(750, g)), params(800, g, watch=1.0), params(850, g, watch=0.5)):
            assert _cut(q) is not None, g


def test_rules_that_name_a_weight_read_the_watchs():
    """The measured optics' ends and the lowercase's share were taken at
    the watch's Thin and Black; a rule that reads them reads the stem, so
    a letter of Arris is drawn as it was at that stem."""
    assert OPTICS.h_ratio(WATCH_STEMS[900]) == pytest.approx(OPTICS.h_heavy)
    assert OPTICS.h_ratio(STEMS[900]) > OPTICS.h_heavy
    assert low_share(WATCH_STEMS[900]) == pytest.approx(0.87) and low_share(STEMS[900]) == pytest.approx(1 - 0.13 * 68 / 85)
    assert params(900).past == 68 and drawn(900).past == 85


def test_arris_mono_takes_arriss_weights():
    assert params(700).with_(mono=True).sv == 130
    assert params(narrow_weight(700)).with_(mono=True, narrow=True).sv == pytest.approx(122)
    assert params(600, watch=1.0).with_(mono=True).sv == 120


@pytest.mark.parametrize('w', [500, 600, 700, 800, 900])
def test_along_the_watch_axis_every_rule_runs_one_way(w):
    """From Arris's weight to the watch's own of that name the stem grows,
    and with it goes everything a rule reads off it, one way and no step
    back: what of the stem is past the Regular, the white the letters give,
    their bodies, the r's share of the H, the f's stub and how far its
    crossbar ends short (the owner: "we treat that as a gradient that you
    can go across"). The f's and the t's rule has a threshold; read on
    Arris's share of the stem it came on somewhere along the axis, half way
    at Black, and the stub shrank three units before it grew (lower.between)."""
    from arris.draw import REGISTRY
    from arris.glyphs import lower
    along = [params(w, watch=t / 20) for t in range(21)]
    assert along[0].same(params(w)) and along[-1].same(params(w, watch=1.0))
    rising = {'stem': lambda p: p.sv, 'white left': lambda p: p.white_low, 'capitals white': lambda p: p.white_cap,
              'figures': lambda p: p.fig_w, 'n': lambda p: REGISTRY['n'].width(p), 'H': lambda p: REGISTRY['H'].width(p),
              'horizontals': lambda p: p.sh / p.sv, 'stub': lower.stub, 'crossbar': lower.bar_short,
              'f': lambda p: REGISTRY['f'].width(p), 't': lambda p: REGISTRY['t'].width(p)}
    falling = {'past': lambda p: p.past, 'r': lambda p: REGISTRY['r'].width(p) / REGISTRY['H'].width(p),
               'diagonals': lambda p: p.sd / p.sv}
    for name, fn in rising.items():
        vals = [fn(p) for p in along]
        assert all(b >= a - 1e-9 for a, b in pairwise(vals)), (name, [round(v, 2) for v in vals])
    for name, fn in falling.items():
        vals = [fn(p) for p in along]
        assert all(b <= a + 1e-9 for a, b in pairwise(vals)), (name, [round(v, 2) for v in vals])
    for g in (-100, 100):                                               # a grade is the weight's own at every watch balance
        assert {round(params(w, g, watch=t / 4).grade_k, 9) for t in range(5)} == {round(params(w, g).grade_k, 9)}
    # and the f's stub goes steadily: no step along the axis more than a fair share of the whole way
    stubs = [lower.stub(p) for p in along]
    assert max(b - a for a, b in pairwise(stubs)) <= 2.5 * (stubs[-1] - stubs[0]) / 20
