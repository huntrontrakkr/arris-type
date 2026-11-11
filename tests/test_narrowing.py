"""Past the Regular the letters give white to their stems (1.017), as the
letters of other families do: Arris had got bolder outward, its counters
a fifth narrower at Black where theirs are two fifths, and a line of
lowercase a ninth longer where theirs is a twenty-fifth (the owner: "this
gets far too bold widthwise"; tools/width_survey.py, 60 families). The
Regular and the lighter weights, the watch's own drawing and Arris Mono
are as they were; and what a narrower body cannot hold as it was is kept
by rule: a one-stem letter's share, the f's and the t's crossbar, the j's
hook, the kink over a shoulder, the Q's bars."""
from __future__ import annotations

import pytest

import arris.glyphs  # noqa: F401  (the registry)
from arris.draw import REGISTRY, draw
from arris.glyphs import lower
from arris.glyphs.letterframe import heft, narrowed, own_width, zone
from arris.instances import params
from arris.italic import italic

CMAP = {chr(s.unicode): n for n, s in REGISTRY.items() if s.unicode}


def _counter(name, p, stems=2):
    return REGISTRY[name].width(p) - stems * p.sv


@pytest.mark.parametrize('w', [100, 200, 300, 400])
def test_the_regular_and_lighter_give_nothing(w):
    p = params(w)
    assert p.white_low == p.white_cap == 1.0 and p.fig_w == p.fig_own
    for name, wm in (('n', 8), ('o', 8), ('H', 9), ('O', 10)):
        assert REGISTRY[name].width(p) == own_width(wm, 2)(p), name
    for name in 'kzEKfty':                                               # (a body by a share, a floor or a measure)
        with zone(REGISTRY[name].kind):
            assert narrowed(p) == 1.0


def test_counters_narrow_as_other_families_counters_do():
    """Regular to Black, at one boldness and one x-height: the n's counter
    0.62 of what it was (0.80 before), the H's 0.72, the zero's 0.66; to
    Bold 0.79, 0.84 and 0.80. Arris's own: the n 0.62 and 0.78, the H 0.71
    and 0.83, the zero 0.69 and 0.81."""
    reg, bold, black = params(400), params(700), params(900)
    for name, to_bold, to_black in (('n', 0.78, 0.62), ('H', 0.83, 0.71)):
        assert _counter(name, bold) / _counter(name, reg) == pytest.approx(to_bold, abs=0.01), name
        assert _counter(name, black) / _counter(name, reg) == pytest.approx(to_black, abs=0.01), name
    zero = lambda p: p.fig_w - 2 * p.sv
    assert zero(bold) / zero(reg) == pytest.approx(0.81, abs=0.01)
    assert zero(black) / zero(reg) == pytest.approx(0.69, abs=0.01)
    # and a letter grows where it grew a quarter: the n 1.16 of its Regular's body at Black (1.27)
    assert REGISTRY['n'].width(black) / REGISTRY['n'].width(reg) == pytest.approx(1.157, abs=0.005)
    for a, b in zip(range(400, 900, 50), range(450, 901, 50)):          # and never narrower for a heavier stem
        for name in 'nHkrj':                                                # (the f and the t lose half their stub by 650)
            assert REGISTRY[name].width(params(b)) > REGISTRY[name].width(params(a)), (name, b)


@pytest.mark.parametrize('w', [500, 700, 900])
def test_the_italic_gives_as_the_upright_does(w):
    p = params(w)
    assert italic(p).white_low == p.white_low < 1.0 and italic(p).white_cap == p.white_cap < 1.0
    for name in 'noH':
        assert REGISTRY[name].width(italic(p)) == pytest.approx(REGISTRY[name].width(p))


@pytest.mark.parametrize('w', [400, 700])
def test_arris_mono_and_the_watchs_own_drawing_give_nothing(w):
    """Mono's letters fill one cell at every weight, and the watch's own
    drawing (WTCH 100) keeps its modules: neither takes the narrowing."""
    mono, watch = params(w).with_(mono=True), params(900, watch=1.0)
    for p in (mono, mono.with_(narrow=True), italic(mono), watch):
        assert p.white_low == p.white_cap == 1.0
    assert watch.fig_w == watch.fig_own
    assert params(w).with_(mono=True).fig_w == pytest.approx(min(max(params(w).fig_own, 9 * 60.0), 600.0), abs=60.0)


def test_a_set_drawn_smaller_gives_as_its_font_does():
    """The narrowing is carried in the parameters, not read off the stem
    against the module: a set with smaller modules inside a glyph (the
    Cyrillic small letters, small capitals) has a thicker stem for its
    module at Regular, and gives nothing there."""
    p = params(400)
    small = p.with_(cap=p.xh, m=p.m * 0.8)
    assert small.white_low == small.white_cap == 1.0
    heavy = params(800)
    assert heavy.with_(cap=heavy.xh, m=heavy.m * 0.8).white_low == heavy.white_low


@pytest.mark.parametrize('w', [700, 900])
def test_signs_of_fixed_geometry_and_two_letters_give_nothing(w):
    """The mathematical operators, the arrows and the technical signs
    measure the watch's own white (draw.white_of): bars a set white apart
    and strokes at 45 degrees, with no counter to give. Narrowed with the
    letters, ⊦ lost its stem to a wedge at Black, ⊫ its two stems to a
    slab, and the feet of ≎ ran out past its bars. The florin and the ϰ
    keep their bodies too (letterframe.ungiving): the one's crossbar and
    hook, the other's two curls. Punctuation and currency give as the
    capitals do."""
    from dataclasses import replace
    p = params(w)
    own = replace(p, white_low=1.0, white_cap=1.0)
    for ch in '⊦⊧⊫≎≏⊚∢→↔⌂':
        spec = REGISTRY[CMAP[ch]]
        assert spec.white == 'own' and spec.width(p) == pytest.approx(spec.width(own)), ch
    for ch in 'ƒϰ':
        assert REGISTRY[CMAP[ch]].width(p) == pytest.approx(REGISTRY[CMAP[ch]].width(own)), ch
    for ch in '$&?':
        spec = REGISTRY[CMAP[ch]]
        assert spec.white == 'cap' and spec.width(p) < spec.width(own), ch
    assert REGISTRY['n'].white == 'lower' and REGISTRY['H'].white == 'cap' and REGISTRY['zero'].white == 'cap'


@pytest.mark.parametrize('ch,ref', [('k', 'n'), ('z', 'n'), ('E', 'H'), ('L', 'H'), ('K', 'H'), ('Z', 'H')])
def test_a_one_stem_letter_gives_the_share_the_n_gives(ch, ref):
    """Its open side holds an arm or a diagonal as thick as a stem: with
    every module of it giving as a counter does, the k and the z stood at
    0.90 of their share at Black and the K and the Z at 0.93."""
    for w in (600, 700, 900):
        p = params(w)
        wm = {'k': 8, 'z': 8, 'E': 8, 'L': 8, 'K': 9, 'Z': 9}[ch]
        own = (own_width(wm, 1)(p) + heft(p)) / own_width(8 if ref == 'n' else 9, 2)(p)
        assert REGISTRY[ch].width(p) / REGISTRY[ref].width(p) == pytest.approx(own), (ch, w)


@pytest.mark.parametrize('w', [400, 600, 650, 700, 800, 900])
def test_f_and_t_give_on_the_arms_side(w):
    """The stem stands a stub in from the body's left edge (lower.stub:
    the stub of the body that gave nothing, to SemiBold; half of it by 650
    and that shape from there), and what the body gives past the Regular
    comes off the arm and the foot, down to ARM_LEAST stems past the stem:
    a quarter of it came off the stub, which is no longer than its two
    cuts, and at ExtraBold they came apart in a kink."""
    p = params(w)
    own = own_width(lower.NARROW, 1)(p) + heft(p)
    whole = (own - p.sv) / 4
    d = lower.stub(p)
    assert d == pytest.approx(whole) if w <= 600 else d < 0.7 * whole
    body = REGISTRY['t'].width(p)
    with zone('lower'):
        arm = max(own * narrowed(p) - whole - p.sv, lower.ARM_LEAST * p.sv)   # as a one-stem letter gives, the stub aside
    assert REGISTRY['f'].width(p) == body == pytest.approx(d + p.sv + arm)
    assert draw('t', p).defaults_used['stem'] == pytest.approx(d + p.sv / 2)
    assert REGISTRY['longs'].width(p) == body                           # (the f without its bar)


@pytest.mark.parametrize('w', [800, 850, 900])
def test_the_j_keeps_a_break_of_white_in_its_hook(w):
    p = params(w)
    assert REGISTRY['j'].width(p) == REGISTRY['uni0237'].width(p) >= 2 * p.sv + lower.J_SLOT * p.c - 1e-9


@pytest.mark.parametrize('w', [700, 750, 800])
def test_the_kink_over_a_shoulder_is_what_it_was(w):
    """An arch or a bowl leaves its stem through the notch it had before
    the letters gave white: where no step is drawn under the shoulder, its
    diagonal lies inside the arch and takes nothing from the counter (the
    owner: "preserving the kink ... at later weights to a small degree so
    that it matches what we had"). Without the rule the n was square from
    725, where it had kept its notch to ExtraBold."""
    from shapely.geometry import LineString

    from arris.geom import rings_to_shapely
    p = params(w)

    def notch(name, width=None):                                         # the white between stem and arch, under the x-height
        lower._measuring.append(p) if width else None
        try:
            ink = rings_to_shapely(draw(name, p, width=width).rings())
        finally:
            lower._measuring.pop() if width else None
        cut = ink.intersection(LineString([(-1e4, p.xh - 0.4 * p.c), (1e4, p.xh - 0.4 * p.c)]))
        runs = sorted((s.bounds[0], s.bounds[2]) for s in getattr(cut, 'geoms', [cut]) if s.length > 1)
        return runs[1][0] - runs[0][1] if len(runs) > 1 else 0.0
    for name in 'nh':
        was = notch(name, own_width(8, 2)(p))
        # (at Bold the body that gave nothing still drew a step under its shoulder, and rose a sixth of a break more)
        assert was > 0 and notch(name) == pytest.approx(was, abs=(0.2 if w == 700 else 0.05) * p.c), name


def test_the_qs_bars_are_the_os_at_black():
    """Its tail is held to the bowl's own width where the bowl is narrower
    than the tail's share of the stem: unheld, the tail went to its limit,
    a stub on the bowl's floor, and every horizontal thinned to 0.7."""
    p = params(900)
    g = draw('Q', p)
    assert g.sh_auto == pytest.approx(1.0)
    assert g.overrides.get('tail', g.defaults['tail']) > p.cap * 3.5 / 12 + p.c
