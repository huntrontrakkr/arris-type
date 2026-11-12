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
from arris.instances import drawn, mono_weight, params
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
    """Regular to the watch's Black, the boldness the families were read
    at (a stem of 175; Bold 140), at one x-height: the n's counter 0.62 of
    what it was (0.80 before), the H's 0.72, the zero's 0.66; to Bold 0.79,
    0.84 and 0.80. Arris's own there: the n 0.62 and 0.78, the H 0.71 and
    0.83, the zero 0.69 and 0.81. At its own Bold and Black, which are
    other families' own (instances.STEMS: stems of 155 and 200), the n
    keeps 0.71 and 0.51 of its counter: wider than its stems to a stem of
    166, nine tenths of one at ExtraBold and two thirds at Black."""
    reg, bold, black = params(400), drawn(700), drawn(900)
    for name, to_bold, to_black in (('n', 0.78, 0.62), ('H', 0.83, 0.71)):
        assert _counter(name, bold) / _counter(name, reg) == pytest.approx(to_bold, abs=0.01), name
        assert _counter(name, black) / _counter(name, reg) == pytest.approx(to_black, abs=0.01), name
    zero = lambda p: p.fig_w - 2 * p.sv
    assert zero(bold) / zero(reg) == pytest.approx(0.81, abs=0.01)
    assert zero(black) / zero(reg) == pytest.approx(0.69, abs=0.01)
    # and a letter grows where it grew a quarter: the n 1.16 of its Regular's body at the watch's Black (1.27)
    assert REGISTRY['n'].width(black) / REGISTRY['n'].width(reg) == pytest.approx(1.157, abs=0.005)
    for w, left in ((700, 0.71), (900, 0.51)):                             # Arris's own Bold and Black
        assert _counter('n', params(w)) / _counter('n', reg) == pytest.approx(left, abs=0.01), w
    for w in range(400, 751, 50):
        assert _counter('n', params(w)) > params(w).sv, w
    assert _counter('n', params(800)) > 0.88 * params(800).sv and _counter('n', params(900)) > 0.65 * params(900).sv
    assert _counter('n', black) < black.sv                                  # (what the watch's Black had not)
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
    mono, watch = params(mono_weight(w)).with_(mono=True), params(900, watch=1.0)
    for p in (mono, mono.with_(narrow=True), italic(mono), watch):
        assert p.white_low == p.white_cap == 1.0
    assert watch.fig_w == watch.fig_own
    assert mono.fig_w == pytest.approx(min(max(mono.fig_own, 9 * 60.0), 600.0), abs=60.0)


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
    p = drawn(w)                                                        # (the watch's weights)
    own = own_width(lower.NARROW, 1)(p) + heft(p)
    whole = (own - p.sv) / 4
    d = lower.stub(p)
    assert d == pytest.approx(whole) if w <= 600 else d < 0.7 * whole
    assert lower.stub(params(500)) == pytest.approx((own_width(lower.NARROW, 1)(params(500)) + heft(params(500)) - params(500).sv) / 4)
    assert drawn(650).sv == 130 < params(600).sv                        # (Arris's SemiBold is past it)
    body = REGISTRY['t'].width(p)
    with zone('lower'):
        arm = max(own * narrowed(p) - whole - p.sv, lower.ARM_LEAST * p.sv)   # as a one-stem letter gives, the stub aside
    assert REGISTRY['f'].width(p) == body == pytest.approx(d + p.sv + arm)
    assert draw('t', p).defaults_used['stem'] == pytest.approx(d + p.sv / 2)
    assert REGISTRY['longs'].width(p) == body                           # (the f without its bar)


@pytest.mark.parametrize('w', [700, 800, 900])
def test_the_cursives_one_stem_letters_give_the_ns_share(w):
    """The cursive j, l, r and k: the share of their body the n gives, as
    the upright's one-stem letters (with all their white giving they stood
    a seventh narrower at Black, where the n is a twelfth); the j no more
    than leaves white inside its hook. The cursive f,
    a stem and a crossbar, gives nothing: what its body gave came off the
    bar's two ends, 35 units each at Black for 72, and the ss10 ligatures
    fi and fj, which run that bar on into the next letter, took the stem
    behind so short a bar for it: a bar as thick as the stem was tall, the
    ligature one black block at ExtraBold and Black."""
    from arris.font import place
    p = italic(params(w))
    for name, wm in (('l', 6), ('r', 8), ('k', 8)):
        share = REGISTRY[name + '.ital'].width(p) / REGISTRY['n'].width(p)
        assert share == pytest.approx(own_width(wm, 1)(p) / own_width(8, 2)(p)), name
    # the j too, down to a break of white inside its hook (or what its own body has there: 0.86 of one at Black)
    own, j = own_width(6, 1)(p), REGISTRY['j.ital'].width(p)
    given = own * REGISTRY['n'].width(p) / own_width(8, 2)(p)
    assert j == pytest.approx(max(given, min(own, 2 * p.sv + lower.J_SLOT * p.c)))
    assert j - 2 * p.sv >= min(0.85, lower.J_SLOT) * p.c
    assert REGISTRY['f.ital'].width(p) == pytest.approx(own_width(7, 1)(p))
    # and the turned f is the cursive f turned, in the cursive f's body (the upright f's is a seventh narrower)
    assert REGISTRY['uni214E'].width(p) == REGISTRY['f.ital'].width(p) > 1.05 * REGISTRY['f'].width(p)
    assert REGISTRY['uni214E'].width(params(w)) == REGISTRY['f'].width(params(w))
    for lig in ('f_i.ss10', 'f_j.ss10'):
        rings = place(lig, p)[0]
        assert len(rings) == 2, lig                                         # the two letters joined, and the dot
        xs = [q[0] for r in rings for q in r]
        ys = [q[1] for r in rings for q in r]
        from arris.geom import rings_to_shapely
        assert rings_to_shapely(rings).area < 0.5 * (max(xs) - min(xs)) * (max(ys) - min(ys)), lig


@pytest.mark.parametrize('w', [400, 700, 800, 900])
def test_the_dot_in_a_lunate_sigma_is_no_speck(w):
    """ͼ ͽ Ͼ Ͽ: the dot stands half a stem clear of the bowl's sides, or
    a quarter of the counter where that is less. Held to half a stem in
    the counters the letters have past the Regular, it was 65 units at
    Bold for a stem of 140, and a speck on the stroke's floor from
    ExtraBold (37 units at Black before the letters gave)."""
    p = params(w)
    for name in ('uni037C', 'uni03FE'):
        g = draw(name, p)
        box = lambda r: (max(q[0] for q in r) - min(q[0] for q in r), max(q[1] for q in r) - min(q[1] for q in r))
        dot = min((box(r) for r in g.rings()), key=lambda b: b[0] * b[1])
        q = g.p                                             # (the drawing's own stem: at Black Ͼ is drawn a hair lighter, its dot kept apart)
        counter = g.W - 2 * q.sv
        assert dot[0] == pytest.approx(dot[1]) == pytest.approx(min(q.dot(), counter - 2 * min(q.sv / 2, counter / 4))), name
        # (and where the counter is less than two stems wide, at ExtraBold and Black, half the counter: 67
        # units in a counter of 134 at Black, a third of a stem and as much as the counter holds)
        assert dot[0] == p.dot() if w == 400 else dot[0] >= min(0.45 * p.sv, counter / 2) - 0.1, name


@pytest.mark.parametrize('w', [100, 400, 700, 800, 900])
def test_the_j_stands_on_the_ls_foot(w):
    """The j is the l run down under the line: its body the l's, and its
    foot the l's own, turned to the left and set on the descender line,
    point for point (the owner, 2026-11-12, of the j that turned into a
    hook with a beak: "It should look more like the l with the same foot
    as our l and just kind of descend"; and of a bare stem: "I didn't want
    you to make it look like an i ... a small little crook at the bottom
    with a foot"). Arris Mono's j keeps its flag and its hook."""
    p = params(w)
    W = REGISTRY['l'].width(p)
    assert REGISTRY['j'].width(p) == REGISTRY['uni0237'].width(p) == W

    def foot(name, turned, drop):
        ring = max(draw(name, p).rings(), key=len)
        return sorted((round(W - x if turned else x, 2), round(y + drop, 2)) for x, y in ring if y + drop < p.xh / 2)
    theirs = foot('l', False, 0.0)
    for name in ('j', 'uni0237'):
        ours = foot(name, True, p.desc)
        assert len(ours) == len(theirs), name
        for a, b in zip(ours, theirs):                      # (to the three units the l's optical centre lifts its cut, in the x-height)
            assert a == pytest.approx(b, abs=3.5), (name, a, b)
    assert min(y for r in draw('j', p).rings() for _, y in r) == pytest.approx(-p.desc, abs=0.5)
    assert len(draw('j', p).rings()) == 2 and len(draw('uni0237', p).rings()) == 1        # a stem and its dot
    mono = params(w).with_(mono=True)                       # (Arris Mono's: a flag, a stem and a hook)
    assert len(max(draw('j', mono).rings(), key=len)) > len(max(draw('j', p).rings(), key=len))


@pytest.mark.parametrize('w', [400, 900])
def test_cv03_gives_the_hooked_j_back(w):
    """The owner, of the j on the l's foot: "you can have the old j using
    some type of rule that can be turned on, but I like the way it is right
    now". cv03 swaps the j, the dotless j and the accented j's for the
    hooked ones: the hooked j's body (lower.j_width), its hook ended in a
    beak that turns up. In the italic and in Arris Mono, whose j is the
    hooked one, the variant is their own j."""
    from arris.glyphs.features import fea
    from arris.glyphs.ligatures import HOOKED_J
    from arris.italic import italic
    assert HOOKED_J == ['j', 'uni0237', 'jcircumflex', 'uni01F0']
    for mono in (False, True):
        text = fea(mono)
        assert 'feature cv03' in text and all(f'sub {n} by {n}.cv03;' in text for n in HOOKED_J)
    p = params(w)
    assert REGISTRY['j.cv03'].width(p) == REGISTRY['uni0237.cv03'].width(p) == pytest.approx(lower.j_width(p))
    assert REGISTRY['j.cv03'].width(p) > REGISTRY['j'].width(p)
    hooked = max(draw('j.cv03', p).rings(), key=len)
    x0 = min(x for x, _ in hooked)
    tip = max(y for x, y in hooked if x < x0 + p.sv / 2)                # the beak's end, at the hook's left
    assert tip > -p.desc + p.sh * p.low + 0.5 * p.c                     # turned up over the hook's bar
    assert len(hooked) > len(max(draw('j', p).rings(), key=len))
    for name in ('j', 'uni0237'):
        for q in (italic(p), p.with_(mono=True)):
            a, b = draw(name, q).rings(), draw(f'{name}.cv03', q).rings()
            assert [len(r) for r in a] == [len(r) for r in b], (name, q.mono)
            assert all(u == pytest.approx(v, abs=0.01) for ra, rb in zip(a, b) for u, v in zip(ra, rb)), (name, q.mono)


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
    p = drawn(w)                                                        # (the watch's Bold, 750 and ExtraBold: stems of 140, 149 and 158)

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
        # (no wider than it was there, and seven tenths of it at the least: the notch is kept by its depth
        # down the stem's side now, lower.NOTCH_KEPT, a break and a half, and where the shoulder has not the
        # room to rise that far its cut meets the arch further along, the white at this height the narrower:
        # the h's 57 units for 79 at a stem of 140)
        assert was > 0 and 0.7 * was <= notch(name) <= was + 0.05 * p.c, name


def test_the_qs_bars_are_the_os_at_black():
    """Its tail is held to the bowl's own width where the bowl is narrower
    than the tail's share of the stem: unheld, the tail went to its limit,
    a stub on the bowl's floor, and every horizontal thinned to 0.7."""
    p = params(900)
    g = draw('Q', p)
    assert g.sh_auto == pytest.approx(1.0)
    assert g.overrides.get('tail', g.defaults['tail']) > p.cap * 3.5 / 12 + p.c
