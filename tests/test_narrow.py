"""Arris Mono Narrow: the Mono's cell, its letters narrower. A fifth of the
cell or more is white at every weight; the letters wide by nature keep the
Mono's width; the arch letters (n h r u) are a little wider than the body,
and what is made from them goes with them; and Arris Mono itself is as it
was."""
from __future__ import annotations

from statistics import mean

import pytest

import arris.glyphs  # noqa: F401  (the registry)
from arris.draw import ARCH, ARCH_MODULES, REGISTRY, body_width
from arris.font import place
from arris.instances import MONO_WEIGHTS, params
from arris.italic import italic
from arris.params import MONO_BODY, MONO_CELL, MONO_NARROW

LETTERS = tuple('abcdefghnopqrsuvwxyzHMNOW') + ('zero', 'one', 'two', 'three', 'four', 'five', 'seven')


def share(name, p):
    """The glyph's ink across, as a share of its cell."""
    rings, adv = place(name, p)
    xs = [q[0] for r in rings for q in r]
    return (max(xs) - min(xs)) / adv


@pytest.mark.parametrize('w', MONO_WEIGHTS)
def test_a_fifth_of_the_cell_is_white(w):
    p = params(w).with_(mono=True, narrow=True)
    assert p.fig_adv == MONO_CELL * p.m and p.fig_w == MONO_NARROW * p.m
    assert 1 - mean(share(n, p) for n in LETTERS) >= 0.20


@pytest.mark.parametrize('w', [300, 700])
def test_the_wide_letters_keep_the_monos_width(w):
    narrow, mono = params(w).with_(mono=True, narrow=True), params(w).with_(mono=True)
    for n in ('m', 'w', 'M', 'W'):
        assert share(n, narrow) == pytest.approx(share(n, mono), abs=0.005), n
    assert share('o', narrow) < share('o', mono) - 0.1


def body(name, p):
    """The glyph's drawing width, in modules."""
    return body_width(REGISTRY[name], p) / p.m


@pytest.mark.parametrize('w', [300, 700])
def test_the_arch_letters_and_what_is_made_from_them(w):
    p = params(w).with_(mono=True, narrow=True)
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
    p = params(w).with_(mono=True, narrow=True)
    for name in ('uni207F', 'uni2098', 'uni2099', 'uni2095', 'uni2090'):
        rings, adv = place(name, p)
        xs = [q[0] for r in rings for q in r]
        assert (min(xs) + max(xs)) / 2 == pytest.approx(adv / 2, abs=2), name
