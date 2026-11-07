"""Arris Mono Narrow: the Mono's cell, its letters narrower. A fifth of the
cell or more is white at every weight; the letters wide by nature keep the
Mono's width; the arch letters (n h r u) are a little wider than the body,
and what is made from them goes with them; each weight from Regular up is
drawn a little lighter than its name; no two neighbours come near touching;
and Arris Mono itself is as it was."""
from __future__ import annotations

from statistics import mean, median

import pytest
from shapely import affinity
from shapely.geometry import Polygon

import arris.glyphs  # noqa: F401  (the registry)
from arris.draw import ARCH, ARCH_MODULES, REGISTRY, body_width
from arris.font import place
from arris.instances import MONO_WEIGHTS, NARROW_LIGHTER, narrow_weight, params
from arris.italic import flatten, italic
from arris.params import MONO_BODY, MONO_CELL, MONO_NARROW

LETTERS = tuple('abcdefghnopqrsuvwxyzHMNOW') + ('zero', 'one', 'two', 'three', 'four', 'five', 'seven')


def narrow(w):
    """Mono Narrow's parameters for a weight, drawn where the build draws it."""
    return params(narrow_weight(w)).with_(mono=True, narrow=True)


def share(name, p):
    """The glyph's ink across, as a share of its cell."""
    rings, adv = place(name, p)
    xs = [q[0] for r in rings for q in r]
    return (max(xs) - min(xs)) / adv


@pytest.mark.parametrize('w', MONO_WEIGHTS)
def test_a_fifth_of_the_cell_is_white(w):
    p = narrow(w)
    assert p.fig_adv == MONO_CELL * p.m and p.fig_w == MONO_NARROW * p.m
    assert 1 - mean(share(n, p) for n in LETTERS) >= 0.20


@pytest.mark.parametrize('w', [300, 700])
def test_the_wide_letters_keep_the_monos_width(w):
    nw, mono = narrow(w), params(narrow_weight(w)).with_(mono=True)
    for n in ('m', 'w', 'M', 'W'):
        assert share(n, nw) == pytest.approx(share(n, mono), abs=0.005), n
    assert share('o', nw) < share('o', mono) - 0.1


def body(name, p):
    """The glyph's drawing width, in modules."""
    return body_width(REGISTRY[name], p) / p.m


@pytest.mark.parametrize('w', [300, 700])
def test_the_arch_letters_and_what_is_made_from_them(w):
    p = narrow(w)
    for n in ARCH:
        assert body(n, p) == pytest.approx(ARCH_MODULES), n
    assert body('o', p) == pytest.approx(MONO_NARROW)
    made = {'ntilde': 'n', 'nacute': 'n', 'hcircumflex': 'h', 'racute': 'r', 'udieresis': 'u',
            'uni01D6': 'u', 'uni0272': 'n', 'uni043F.loclBGR': 'n', 'uni0438.loclBGR': 'u'}
    for name, base in made.items():
        assert body(name, p) == pytest.approx(body(base, p)), name
    it = italic(p)
    for name in ('n', 'ntilde', 'u', 'udieresis', 'uni043F.loclBGR'):
        assert body(name, it) == pytest.approx(ARCH_MODULES), name


def test_arris_mono_is_as_it_was():
    for w in MONO_WEIGHTS:
        p = params(w).with_(mono=True)
        assert not p.narrow and MONO_BODY[0] * p.m <= p.fig_w <= MONO_BODY[1] * p.m


@pytest.mark.parametrize('w', [300, 700])
def test_the_small_letters_sit_in_the_middle_of_the_cell(w):
    """ⁿ ₘ ₙ ₕ ₐ: a small letter is drawn in its own letter's body (the m's
    and the n's wider than the cell's), so its ink is centred in the cell."""
    p = narrow(w)
    for name in ('uni207F', 'uni2098', 'uni2099', 'uni2095', 'uni2090'):
        rings, adv = place(name, p)
        xs = [q[0] for r in rings for q in r]
        assert (min(xs) + max(xs)) / 2 == pytest.approx(adv / 2, abs=2), name


def test_each_weight_from_regular_up_is_drawn_lighter():
    """In a terminal, light on dark, Mono Narrow's Regular puts as much ink in a
    cell as Fira Code's; its Light keeps its own weight."""
    assert narrow_weight(MONO_WEIGHTS[0]) == MONO_WEIGHTS[0]
    for w in MONO_WEIGHTS[1:]:
        assert narrow_weight(w) == w - NARROW_LIGHTER
        assert narrow(w).sv == params(w - NARROW_LIGHTER).sv < params(w).with_(mono=True).sv
    drawn = [narrow_weight(w) for w in MONO_WEIGHTS]
    assert drawn == sorted(set(drawn))


def _ink(name, p):
    """A glyph's ink as a renderer draws it: the italic's curves, not their
    control points, which stand outside a curved corner (21 units at u's in
    Mono Narrow Bold Italic: measured by them, k and u stood 36 units apart,
    drawn they stand 85)."""
    rings, adv = place(name, p)
    g = None
    for r in rings:
        curved = any(len(q) > 2 and not q[2] for q in r)
        poly = Polygon(flatten(r) if curved else [q[:2] for q in r]).buffer(0)
        g = poly if g is None else g.symmetric_difference(poly)
    return g, adv


NEIGHBOURS = tuple('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ') + \
    ('zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine')


@pytest.mark.parametrize('w, it', [(300, False), (700, False), (400, True), (700, True)])
def test_no_two_neighbours_come_near_touching(w, it):
    """Any two letters or figures set side by side keep two-thirds of a module
    of white between their inks at least (the wide m w M W, at Arris Mono's
    width, come closest), and two lowercase letters two modules as a rule
    (Arris Mono: one)."""
    p = narrow(w)
    if it:
        p = italic(p).with_(cursive=True)
    inks = {n: _ink(n, p) for n in NEIGHBOURS}
    gaps = {(a, b): ga.distance(affinity.translate(inks[b][0], adv))
            for a, (ga, adv) in inks.items() for b in NEIGHBOURS}
    worst = min(gaps, key=gaps.get)
    assert gaps[worst] >= 2 / 3 * p.m, (worst, gaps[worst])
    lower = [v for (a, b), v in gaps.items() if len(a) == len(b) == 1 and a.islower() and b.islower()]
    assert median(lower) >= 2 * p.m
