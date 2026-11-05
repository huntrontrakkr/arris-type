"""Arris Mono Narrow: the Mono's cell, its letters narrower. A fifth of the
cell or more is white at every weight; the letters wide by nature keep the
Mono's width; and Arris Mono itself is as it was."""
from __future__ import annotations

from statistics import mean

import pytest

import arris.glyphs  # noqa: F401  (the registry)
from arris.font import place
from arris.instances import MONO_WEIGHTS, params
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
    assert share('n', narrow) < share('n', mono) - 0.1


def test_arris_mono_is_as_it_was():
    for w in MONO_WEIGHTS:
        p = params(w).with_(mono=True)
        assert not p.narrow and MONO_BODY[0] * p.m <= p.fig_w <= MONO_BODY[1] * p.m
