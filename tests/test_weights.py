"""Arris's weights past the Regular. Each has the stem that gives a line of
its lowercase the colour other families' weight of that name has: sixty
families read at every weight (the ink of a line of lowercase in the band
of its x-height) stand at 0.33 at Regular, as Arris does, and at 0.39,
0.45, 0.50, 0.55 and 0.61 from Medium to Black, where Arris stood at 0.37,
0.40, 0.44, 0.47 and 0.51, its Bold their SemiBold and its Black their Bold
(the owner, 2026-11-11: "a true bold at the same color as other sets and a
true black"). Black is heavier than any weight the watch has; the engine
draws it on a rung past the watch's Black. The watch's own drawing, Arris
Watch and the watch's end of the variable font, keeps the watch's weights,
its SemiBold the watch's figures ("Watch cut keeps its weights"), and Arris
Mono the stems it had, at Fira Code's colour in its cell."""
from __future__ import annotations

from itertools import pairwise

import pytest

import arris.glyphs  # noqa: F401  (the registry)
from arris.draw import _cut
from arris.font import place
from arris.geom import rings_to_shapely
from arris.instances import (
    DRAWN_STEMS,
    MONO_STEMS,
    NAMES,
    OPTICS,
    STEMS,
    WATCH_STEMS,
    drawn,
    low_share,
    mono_weight,
    narrow_weight,
    params,
    stem,
    watch_weight,
    weight_of,
)
from arris.italic import italic
from arris.params import outer_leg

# the families' colour at each weight: the middle one, and the middle half (tools/width_survey.py's sixty, read
# the same way: 2026-11-11)
FAMILIES = {400: (0.333, 0.314, 0.352), 500: (0.387, 0.373, 0.418), 600: (0.447, 0.428, 0.467),
            700: (0.499, 0.478, 0.523), 800: (0.550, 0.526, 0.594), 900: (0.605, 0.565, 0.646)}
LINE = 'the quick brown fox jumps over the lazy dog and typography is the craft of endowing human language with a durable visual form'


def colour(p) -> float:
    """The ink of a line of lowercase, as a share of the band it stands in
    (its length by the x-height)."""
    from shapely.geometry import box

    from arris.draw import REGISTRY
    names = {chr(s.unicode): n for n, s in REGISTRY.items() if s.unicode}
    band, seen, ink, line = box(-2000, 0, 4000, p.xh), {}, 0.0, 0.0
    for ch in LINE:
        if ch == ' ':
            line += 0.45 * p.xh
            continue
        if ch not in seen:
            rings, adv = place(names[ch], p)
            seen[ch] = (rings_to_shapely([[q[:2] for q in r] for r in rings]).intersection(band).area, adv)
        ink, line = ink + seen[ch][0], line + seen[ch][1]
    return ink / (line * p.xh)


def test_past_the_regular_a_weight_is_heavier_than_the_watchs():
    assert set(STEMS) == set(WATCH_STEMS) == set(MONO_STEMS) == set(NAMES)
    for w in STEMS:
        assert STEMS[w] == WATCH_STEMS[w] == MONO_STEMS[w] if w <= 400 else STEMS[w] > WATCH_STEMS[w] > MONO_STEMS[w], w
    assert STEMS[700] == 155 and STEMS[900] == 200
    steps = [STEMS[b] - STEMS[a] for a, b in zip(range(400, 900, 100), range(500, 901, 100))]
    assert all(20 <= k <= 23 for k in steps), steps                        # an even step, a quarter of the Regular's stem
    assert DRAWN_STEMS[1000] == STEMS[900] and {w: s for w, s in DRAWN_STEMS.items() if w <= 900} == WATCH_STEMS


@pytest.mark.parametrize('w', sorted(FAMILIES))
def test_a_weight_has_the_colour_other_families_weight_has(w):
    """Within a hundredth of the families' middle one, at every weight
    from the Regular up to ExtraBold, and inside their middle half. At
    Black, where the lowercase stands on the bar the a's and the e's
    counters leave it (118 units for the weight's own 148: draw._start),
    Arris is 0.591 for their 0.605: a hundredth and a half under their
    middle one, inside their middle half (0.565 to 0.646)."""
    middle, low, high = FAMILIES[w]
    c = colour(params(w))
    assert abs(c - middle) < (0.01 if w < 900 else 0.015) and low < c < high, (w, round(c, 3))


def test_the_ladder_arris_had_was_a_weight_light_from_semibold():
    """The stems Arris Mono keeps: in Arris's widths its Bold has the
    families' SemiBold's colour and its Black their Bold's."""
    was = {w: colour(params(mono_weight(w))) for w in (600, 700, 900)}
    assert was[600] < FAMILIES[600][1] and was[700] < FAMILIES[700][1] and was[900] < FAMILIES[900][1]
    assert abs(was[700] - FAMILIES[600][0]) < 0.01 and abs(was[900] - FAMILIES[700][0]) < 0.015


@pytest.mark.parametrize('w', [400, 450, 500, 600, 700, 800, 900])
def test_past_the_regular_a_bowls_outside_cut_keeps_the_regulars_size(w):
    """The cut families that have a Black hold the outside cut one size and
    their insides go square; with one centreline leg at every weight
    Arris's outside cut grew to 156 units at a stem of 200 and the o's
    counter there, 134 units wide, was a diamond. The watch's own drawing
    keeps its leg."""
    from arris.draw import fill_leg
    regular = params(400)
    p = params(w)
    assert outer_leg(p) == pytest.approx(outer_leg(regular)) and p.leg <= regular.leg
    assert params(w, watch=1.0).leg == regular.leg == 90
    assert italic(p).leg == p.leg and p.with_(mono=True).leg == p.leg
    if w >= 700:
        # the o's counter: its corners cut no more than the corner rule's fill, the Regular's edge break
        rings, _ = place('o', p)
        hole = min(rings, key=lambda r: max(q[0] for q in r) - min(q[0] for q in r))
        cuts = [abs(b[0] - a[0]) for a, b in zip(hole, hole[1:] + hole[:1]) if abs(b[0] - a[0]) > 1 and abs(b[1] - a[1]) > 1]
        assert cuts and max(cuts) <= fill_leg(p) + 1.5, (w, cuts)


@pytest.mark.parametrize('w', [100, 250, 400, 433, 500, 600, 650, 700, 800, 850, 900])
def test_a_weight_of_arris_is_a_drawing_the_watchs_ladder_has(w):
    p = params(w)
    assert p.sv == pytest.approx(stem(w)) and weight_of(p.sv) == pytest.approx(w)
    d = watch_weight(p.sv)                                              # the watch's weight with that stem
    assert d == pytest.approx(w) if w <= 400 else w < d <= 1000         # (past its Black, the rung only Arris has)
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


@pytest.mark.parametrize('w,was', [(700, 650), (600, 560), (500, 480)])
def test_arris_monos_weight_is_the_drawing_of_the_watchs_weight_with_its_stem(w, was):
    """Arris Mono's Bold the watch's 650, the weight the owner chose the
    f's and the t's crossing at."""
    for name in ('n', 'e', 'a', 'g', 'k', 'dollar', 'ampersand', 'eight'):
        for cut in (lambda q: q.with_(mono=True), lambda q: italic(q.with_(mono=True))):
            assert _same_outline(place(name, cut(params(mono_weight(w)))), place(name, cut(drawn(was)))), (name, w)


@pytest.mark.parametrize('w', [100, 400, 600, 800, 900])
def test_the_watchs_own_drawing_keeps_its_weights(w):
    p = params(w, watch=1.0)
    assert p.sv == WATCH_STEMS[w] and drawn(w, watch=1.0).same(p)
    assert params(600, watch=1.0).sv == 2 * p.m                         # the watch's figures: stems of two modules
    half = params(w, watch=0.5)                                         # between the two, straight: as the variable font carries it
    assert half.sv == pytest.approx((STEMS[w] + WATCH_STEMS[w]) / 2)
    assert _cut(half) is not None and _cut(italic(half)) is not None


def test_a_positive_grade_adds_nothing_at_a_cuts_black():
    assert params(900, 100).sv == pytest.approx(200) and params(900, 100).grade_k == 1.0
    assert params(900, 100, watch=1.0).sv == pytest.approx(175)
    assert params(600, 100).sv == pytest.approx(1.2 * 133)
    heavier = [params(w, 100).sv for w in range(400, 901, 50)]
    assert heavier == sorted(heavier)                                   # never lighter for a heavier weight
    for g in (-100, 100):
        for q in (params(750, g), italic(params(750, g)), params(800, g, watch=1.0), params(850, g, watch=0.5)):
            assert _cut(q) is not None, g


def test_rules_that_name_a_weight_read_the_watchs():
    """The measured optics' ends and the lowercase's share were taken at
    the watch's Thin and Black; a rule that reads them reads the stem, so
    a letter of Arris is drawn as it was at that stem."""
    assert OPTICS.h_ratio(WATCH_STEMS[900]) == pytest.approx(OPTICS.h_heavy) == OPTICS.h_ratio(STEMS[900])
    assert OPTICS.h_ratio(STEMS[700]) > OPTICS.h_heavy
    assert low_share(WATCH_STEMS[900]) == pytest.approx(0.87) == low_share(STEMS[900])
    assert low_share(STEMS[700]) == pytest.approx(1 - 0.13 * 65 / 85)
    assert params(900).past == 110 and drawn(900).past == 85 and drawn(1000).same(params(900))


def test_arris_mono_keeps_its_stems():
    """In a 600 cell its Bold has Fira Code Bold's colour already, and a
    third stem of 155 has no room in the m: the engine is asked for the
    weight of Arris that has Mono's stem (mono_weight)."""
    assert [params(mono_weight(w)).with_(mono=True).sv for w in (300, 400, 450)] == [66, 90, 96]
    assert [round(params(mono_weight(w)).with_(mono=True).sv, 6) for w in (500, 600, 700)] == [102, 114, 130]
    assert params(narrow_weight(700)).with_(mono=True, narrow=True).sv == pytest.approx(122)
    assert params(narrow_weight(400)).with_(mono=True, narrow=True).sv == pytest.approx(78)
    assert params(600, watch=1.0).with_(mono=True).sv == 120
    for w in (500, 600, 700):
        q = params(mono_weight(w)).with_(mono=True)
        assert _cut(q) is not None and _cut(italic(q)) is not None


@pytest.mark.parametrize('w', [500, 600, 700, 800, 900])
def test_along_the_watch_axis_every_rule_runs_one_way(w):
    """From Arris's weight to the watch's own of that name the stem goes
    one way (down: Arris's is the heavier past the Regular), and with it
    goes everything a rule reads off it, one way and no step back: what of
    the stem is past the Regular, the white the letters give, their bodies,
    the bowl's leg, the f's stub and how far its crossbar ends short (the
    owner: "we treat that as a gradient that you can go across"). The f's
    and the t's rule has a threshold; read on Arris's share of the stem it
    came on somewhere along the axis, and the stub shrank three units
    before it grew (lower.between)."""
    from arris.draw import REGISTRY
    from arris.glyphs import lower
    along = [params(w, watch=t / 20) for t in range(21)]
    assert along[0].same(params(w)) and along[-1].same(params(w, watch=1.0))
    read = {'stem': lambda p: p.sv, 'white left': lambda p: p.white_low, 'capitals white': lambda p: p.white_cap,
            'horizontals': lambda p: p.sh / p.sv, 'diagonals': lambda p: p.sd / p.sv, 'past': lambda p: p.past,
            'leg': lambda p: p.leg, 'stub': lower.stub, 'crossbar': lower.bar_short}
    for name, fn in read.items():
        vals = [fn(p) for p in along]
        steps = [b - a for a, b in pairwise(vals)]
        slack = 0.2 if name == 'crossbar' else 1e-9             # (a tenth of a unit back where the crossbar's fade ends, at SemiBold)
        assert all(s >= -slack for s in steps) or all(s <= slack for s in steps), (name, [round(v, 2) for v in vals])
    # A body is its stems and its white, and along the axis the one falls as the other grows: it need not run one
    # way, but it stays by the straight line between its ends, which is what the variable font carries. Furthest
    # off it at Black: the r 16 units (its share of the H turns a fifth of the way along) and the f and the t 13
    # (Arris's arm is at its least there, 1.1 stems past the stem, and the watch's is not: lower.narrow_width).
    bodies = {'figures': lambda p: p.fig_w, 'n': lambda p: REGISTRY['n'].width(p), 'H': lambda p: REGISTRY['H'].width(p),
              'f': lambda p: REGISTRY['f'].width(p), 't': lambda p: REGISTRY['t'].width(p), 'r': lambda p: REGISTRY['r'].width(p)}
    for name, fn in bodies.items():
        vals = [fn(p) for p in along]
        off = max(abs(v - (vals[0] + (vals[-1] - vals[0]) * i / 20)) for i, v in enumerate(vals))
        assert off < 18, (name, round(off, 1), [round(v, 1) for v in vals])
    assert along[0].sv > along[-1].sv and along[0].leg < along[-1].leg and along[0].white_low < along[-1].white_low
    for g in (-100, 100):                                               # a grade is the weight's own at every watch balance
        assert {round(params(w, g, watch=t / 4).grade_k, 9) for t in range(5)} == {round(params(w, g).grade_k, 9)}
    # and the f's stub goes steadily: no step along the axis more than a fair share of the whole way
    stubs = [lower.stub(p) for p in along]
    assert max(abs(b - a) for a, b in pairwise(stubs)) <= 3 * abs(stubs[-1] - stubs[0]) / 20 + 1e-9
