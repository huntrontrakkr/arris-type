"""How the letters stand together (1.017): every letter keeps its share of
the line as weight is added, open sides are spaced as hand-spaced faces
space them, the open letters share one terminal and one balance of
storeys, and the corners of the D are the O's."""
from __future__ import annotations

import pytest
from shapely.geometry import LineString

import arris.glyphs  # noqa: F401  (the registry)
from arris.draw import OPTICAL, REGISTRY, draw
from arris.font import place
from arris.geom import rings_to_shapely
from arris.instances import params

CMAP = {chr(s.unicode): n for n, s in REGISTRY.items() if s.unicode}


def _ink(ch, p):
    return rings_to_shapely(draw(CMAP[ch], p).rings())


def _width(ch, p):
    x0, _, x1, _ = _ink(ch, p).bounds
    return x1 - x0


@pytest.mark.parametrize('ch', list('EFKLTZ'))
def test_a_one_stem_capital_keeps_its_share_of_the_line(ch):
    """Regular to Black the H grows a fifth; a letter with one stem grows
    with it (hand-drawn faces: 0.93 to 1.08 of its share; until 1.017 0.80
    to 0.84)."""
    share = lambda w: _width(ch, params(w)) / _width('H', params(w))
    assert share(900) / share(400) >= 0.9, ch


@pytest.mark.parametrize('ch', list('fktz'))
def test_a_one_stem_lowercase_letter_keeps_its_share(ch):
    share = lambda w: _width(ch, params(w)) / _width('n', params(w))
    assert share(900) / share(400) >= 0.9, ch


@pytest.mark.parametrize('w', [100, 300, 400, 600, 900])
def test_the_r_is_eight_ninths_of_the_h(w):
    """Its master's share at every weight: at Thin it was a third wider
    than the n."""
    p = params(w)
    assert REGISTRY['r'].width(p) == pytest.approx(8 / 9 * REGISTRY['H'].width(p))
    assert _width('r', p) <= 1.12 * _width('n', p)


def _whites(ch, p, at=0.5):
    """The whites a plumb line through the letter crosses, from the bottom up."""
    ink = _ink(ch, p)
    x0, y0, x1, y1 = ink.bounds
    x = x0 + at * (x1 - x0)
    cut = ink.intersection(LineString([(x, y0 - 10), (x, y1 + 10)]))
    runs = sorted((s.bounds[1], s.bounds[3]) for s in getattr(cut, 'geoms', [cut]) if s.length > 1)
    return [b[0] - a[1] for a, b in zip(runs, runs[1:])]


@pytest.mark.parametrize('w', [300, 400, 700, 900])
def test_the_open_storey_of_a_and_e(w):
    """The a, e and s stack their three bars with one white, and the optical
    centre raises the middle: the a's open storey is seven eighths of its
    bowl, the e's a seventh more than its bowl (until 1.017 both two
    thirds, the a's the tighter)."""
    p = params(w)
    r = OPTICAL['counters']
    bowl, upper = _whites('a', p)
    assert upper / bowl == pytest.approx(r, abs=0.08)
    lower, bowl = _whites('e', p)
    assert bowl / lower == pytest.approx(r, abs=0.08)
    lower, upper = _whites('s', p)
    assert upper / lower == pytest.approx(r, abs=0.08)


@pytest.mark.parametrize('w', [300, 400, 700])
def test_a_c_e_s_end_in_one_terminal(w):
    """Each open end turns through a cut corner into the c's beak: the a's
    arm, the e's arm and both ends of the s reach as far from their lines
    as the c's do."""
    p = params(w)

    def reach(ch, top, right):
        ink = _ink(ch, p)
        x0, y0, x1, y1 = ink.bounds
        x = x1 - 1 if right else x0 + 1
        cut = ink.intersection(LineString([(x, y0 - 10), (x, y1 + 10)]))
        runs = sorted((s.bounds[1], s.bounds[3]) for s in getattr(cut, 'geoms', [cut]) if s.length > 1)
        lo, hi = runs[-1] if top else runs[0]
        return hi - lo

    c = reach('c', True, True)
    for ch, top, right in (('a', True, False), ('e', False, True), ('s', True, True), ('s', False, False)):
        assert reach(ch, top, right) == pytest.approx(c, abs=0.12 * c), (ch, top)


@pytest.mark.parametrize('w', [400, 700, 900])
def test_the_ds_corners_are_the_os(w):
    p = params(w)

    def cut(ch):                              # how far in from its right side the letter's top edge starts
        ink = _ink(ch, p)
        x0, y0, x1, y1 = ink.bounds
        top = ink.intersection(LineString([(x0 - 10, y1 - 2), (x1 + 10, y1 - 2)]))
        return x1 - max(s.bounds[2] for s in getattr(top, 'geoms', [top]))

    assert cut('D') == pytest.approx(cut('O'), abs=3)


@pytest.mark.parametrize('w', [400, 700])
def test_dock_is_one_word(w):
    """The white between O and C, and between C and K: until 1.017 the C
    stood 79 units from the K and 141 from the O at Regular, and the word
    read DO CK."""
    p = params(w)

    def gap(a, b):
        ra, adv = place(CMAP[a], p)
        rb, _ = place(CMAP[b], p)
        return adv - max(x for r in ra for x, _ in r) + min(x for r in rb for x, _ in r)

    assert gap('C', 'K') >= 0.75 * gap('O', 'C')
    assert gap('D', 'O') == pytest.approx(gap('O', 'C'), rel=0.1)


@pytest.mark.parametrize('w', [300, 400, 700, 900])
def test_the_1_stands_on_its_stem(w):
    """A stem and a flag: at the baseline the 1 is as wide as its stem. In
    Arris Mono it keeps a foot."""
    p = params(w)
    foot = lambda q: rings_to_shapely(draw('one', q).rings()).intersection(
        LineString([(-500, q.sh / 2), (1500, q.sh / 2)])).length
    assert foot(p) == pytest.approx(p.sv, abs=1)
    assert foot(p.with_(mono=True)) > 2 * p.sv or w > 700


@pytest.mark.parametrize('w', [300, 400])
def test_the_x_steps_as_the_capital_does(w):
    """One drawing for X and x: at the light weights both step at the
    crossing (the 2's notch), and both lose the step as they grow."""
    p = params(w)
    points = lambda ch: sum(len(r) for r in draw(CMAP[ch], p).rings())
    assert points('x') == points('X')
