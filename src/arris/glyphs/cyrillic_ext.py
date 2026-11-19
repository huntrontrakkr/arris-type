"""Cyrillic beyond Russian: Central Asia, the Caucasus, the Volga, Siberia.

The letters are the Russian ones with a few added parts, each drawn once
and used wherever a letter carries it:

* **Descender** (Қ Ң Ҷ Ҭ Җ Ҳ Ԥ ...): Ц's tail. The foot runs on along the
  baseline and a short stem drops from its end into the descender, a
  module beyond the stem it hangs from.
* **Tail** (Ӆ Ӎ Ӊ Ҋ): the same drop, turning left at its foot like a
  comma: what tells "with tail" from "with descender".
* **Hook** (Ӈ Ԓ Ӽ, and Ҕ Ҧ Ӄ from mid-stem): a stem running on below the
  baseline and turning back on a bowl corner, as Ђ and Ŋ do.
* **Drop** (Ҙ Ҫ Ҿ): a stem dropped from the middle of a bowl's foot.
* **Bars** across stems (Ғ Ұ Ҟ Ӿ Ҹ Ҝ): the Đ's and Ħ's crossing bars.
* **Komi hook** (Ԃ Ԉ Ԋ Ԏ): a stem's foot running on into a small u.

Lowercase follows the Russian lowercase: small capitals (``smallcap``)
where the Russian letter is one, and the Latin letter's own drawing where
the Russian letter is Latin (ө is the o with a bar, ә the e turned, ҳ the
x with a descender). Accented letters are composed from their marks
(``marks.compose``) at the end of this module.
"""
from __future__ import annotations

from ..draw import B, REGISTRY, Opening, draw, glyph, lay_bar
from ..params import SQRT2, outer_leg
from .caps import big
from .cyrillic import ALIASES as RU_ALIASES, ZE_BOWLS, ccap, mirror, sc, smallcap
from .extra_latin import stamp
from .figures import MOUTH_SHARE, _beak_limit, beak_depth, jog, wedge_bars
from .letterframe import Frame, k_arms, least_white, letter_width, white_scale

# Code points that are Latin or Russian letters already.
ALIASES = {
    0x04AE: 'Y',            # Ү straight u: the Y
    0x04C0: 'I', 0x04CF: 'I',   # palochka (both cases, as Chechen and Avar write it)
    0x04D4: 'AE', 0x04D5: 'ae',
    0x051A: 'Q', 0x051B: 'q', 0x051C: 'W', 0x051D: 'w',
    0x0501: 'd',            # Komi de
    0x0511: 'uni03B5',      # reversed ze: the epsilon
}

TAIL = 0.8          # a descender's depth, of the descender (Ц's)


def room(p):
    """How far a descender stands beyond the stem it hangs from: a module
    of white, scaled as a letter's white is."""
    return p.m * white_scale(p)


def plus_room(name, k=1.0):
    return lambda p: REGISTRY[name].width(p) + k * room(p)


def _down(g, depth):
    """Let the ink reach ``depth`` below the baseline."""
    if g.clip is not None:
        x0, y0, x1, y1 = g.clip
        g.clip = (x0, min(y0, -depth), x1, y1)


def descender(g, f, xs, xd, turn=False):
    """Ц's tail: the foot of a stem at xs runs on along the baseline to a
    short stem at xd that drops into the descender. ``turn``: the drop
    turns left at 45 degrees at its foot, as a comma does (a tail rather
    than a descender)."""
    p = g.p
    yb = f.Y(1)
    if p.slant:
        # the cursive ц's (italic_forms._u_stems): one stroke through a small
        # bowl corner into the drop, which the italic curves. The upright's
        # two strokes meet in an L; slanted, the step between the stem's edge
        # and the drop's read as a notch at every weight from Regular up
        foot = [(xs, yb), B(xd, yb, p.m / 2)]
    else:
        side = p.sv / 2 if xd >= xs else -p.sv / 2
        g.stroke((xs, yb), (xd + side, yb))
        foot = [(xd, yb)]
    if not turn:
        g.stroke(*foot, (xd, -TAIL * p.desc))
        _down(g, TAIL * p.desc)
        return
    L = 0.75 * p.sv
    y_end = -p.desc
    y_turn = min(y_end + L, yb - p.sv)
    g.stroke(*foot, (xd, y_turn), (xd - L, y_turn - L), end='h')
    _down(g, p.desc)


def drop(g, x):
    """A stem dropped from the middle of a bowl's foot into the descender.
    In the italic it meets the foot's underside square (no corner-rule fill
    at the join, as the g's descender: lower.crotch_butt), and the foot's
    corners take drop_leg."""
    p = g.p
    g.stroke((x, g.sh / 2), (x, -TAIL * p.desc))
    _down(g, TAIL * p.desc)
    if p.slant:
        from ..draw import _thickness
        under = g.sh / 2 - _thickness(p, g.sh)((1.0, 0.0)) / 2    # the foot's underside (crotch_butt)
        g.butt += (('y', under, x - p.sv / 2 - 1.0, x + p.sv / 2 + 1.0),)


def drop_leg(p, span):
    """The leg of a bowl's foot corners with a drop between them, ``span``
    apart centre to centre: in the italic no longer than leaves the foot a
    flat of TAIL_FLAT corner breaks between each corner's outer chamfer and
    the drop's side (never under half a module, the tick's). With the
    parameter leg the chamfer reached the drop from 800 up, the two merged,
    and the italic curved the whole foot into a belly with no descender in
    it (Ҙ Ҫ ҫ ҿ). The upright keeps the parameter leg (None)."""
    if not p.slant:
        return None
    from .italic_forms import TAIL_FLAT
    beyond = outer_leg(p) - p.leg                   # the outer chamfer past the centreline leg
    return min(p.leg, max(p.m / 2, span / 2 - beyond - TAIL_FLAT * p.c))


def hook_y(g, f):
    """The centre of a hook's foot: as deep as Ђ's and Ŋ's on a capital, as
    the ŋ's on a letter drawn on the x-height (a small capital)."""
    p = g.p
    return -p.desc + g.sh / 2 if p.cap <= p.xh + 1e-6 else f.Y(-2)


def hook(g, f, x, y_from, reach=4.0):
    """A stem at x from y_from running on below the baseline and turning
    back left on a bowl corner (Ђ's and Ŋ's hook). Where the tail is shorter
    than its corner needs for a flat to its end (italic_forms.run_floor),
    the corner's chamfer is the smaller: the chamfer ate the tail of ԓ's
    hook whole at Black with the watch's strokes, a wedge to a point."""
    from .italic_forms import run_floor, tail_run
    p = g.p
    yh = hook_y(g, f)
    run = tail_run(p, reach * p.m * white_scale(p))
    leg = p.leg - max(0.0, run_floor(p) - run)
    g.stroke((x, y_from), ('bowl', x, yh, max(leg, p.c), None), (x - run, yh))
    _down(g, p.desc)


def cross_bar(g, x0, x1, y):
    """A bar added across a letter's stem: it keeps the Regular's weight
    (Glyph.held), is laid over the letter (Glyph.lay), and settles a few
    units off where its edge would land on one of the letter's
    (Glyph.settle)."""
    from ..draw import NUDGE
    t = g.held()
    g.settle([[((x0, y + d, t), (x1, y + d))] for d in NUDGE], lay=True)


def beak_free(g):
    """A beak's depth, which a mouth's opening may shorten, never past its
    outer flank (as the 3's and 5's: figures.beak_bottom), and never
    lengthens: the opening's limit is the shortest beak of the weight's own
    bars at their thinnest (figures._beak_limit), and where the letter's
    bars are thinner than that (the italic's Ә and Ҽ at Black, their bars
    at the height's common bar and thinned again for the bay,
    figures.bay_stack) the limit was the longer of the two: the mouth's own
    rule drew the beak out 24 units and left the mouth 31 for the 55 the
    bars had given way for."""
    from ..params import outer_leg
    from .figures import _shortest
    p = g.p
    own = beak_depth(p, g.sh)
    floor = _shortest(p, g.sh) if p.slant else outer_leg(p, sh=g.sh) + p.c
    return max(min(g.free('beak', own), own), floor)


def _mouth_frame(g, modules, rows, floor=None):
    """The frame of a letter whose beak faces a bar (Ә, Ҽ). Upright, its
    mouth's opening shortens the beak (MOUTH). In the italic the beak keeps
    its flank, which its corners need to be curved (beak_free), and the
    mouth ran out: 0.19 of a stem at Black. There the bars give instead,
    as the S's do (figures.bay_stack)."""
    from .figures import bay_stack
    if g.p.slant:
        return bay_stack(g, lambda: Frame(g, modules), [rows], floor=floor)
    return Frame(g, modules)


# A mouth, where a beak faces a bar (Ә Ҽ Ҩ), keeps three quarters of its
# share of the stem, the beak shortening as the figures' do. Each drawing
# records the white it leaves between the beak's tip and the bar.
MOUTH = Opening(lambda g: g.defaults_used['mouth'], 'beak', _beak_limit, max_ratio=MOUTH_SHARE)


# --- Capitals ------------------------------------------------------------

@ccap('uni0492', 'Ғ', 7, 1, width=plus_room('uni0413', 1.5))
def Ghestroke(g):
    """Г with the Đ's bar across its stem."""
    p = g.p
    dx = 1.5 * room(p)
    stamp(g, 'uni0413', dx, width=g.W - dx)
    cross_bar(g, 0, dx + p.sv + 2 * room(p), p.cap / 2)


@ccap('uni049A', 'Қ', 9, 1, width=plus_room('K'))
def Kadesc(g):
    f = Frame(g, 9)
    p = g.p
    Wk = g.W - room(p)
    stamp(g, 'K', width=Wk)
    k = p.sd / SQRT2
    x_leg = Wk + p.c - k - f.Y(1)                           # the leg's centre on the foot's line
    descender(g, f, x_leg, g.W - p.sv / 2)


@ccap('uni04A2', 'Ң', 10, 2)
def Endesc(g):
    f = Frame(g, 10)
    p = g.p
    g.stroke(f.P(1, 0), f.P(1, 12))
    g.stroke(f.P(8, 12), f.P(8, 1))
    g.stroke(f.P(1, 6), f.P(8, 6))
    descender(g, f, f.X(8), g.W - p.sv / 2)


@ccap('uni04E8', 'Ө', 10, 2)
def Obarred(g):
    """The O, barred wall to wall (Θ's bar floats)."""
    REGISTRY['O'].fn(g)
    f = Frame(g, 10)
    g.stroke(f.P(1, 6), f.P(9, 6))


@ccap('uni04B0', 'Ұ', 10, 2)
def Ustraightstroke(g):
    """Ү with a bar across its stem (``bar_reach`` past it each side)."""
    REGISTRY['Y'].fn(g)
    f = Frame(g, 10)
    _stem_bar(g, g.W / 2, f.Y(3))


def _stem_bar(g, x, y):
    cross_bar(g, x - (g.p.sv / 2 + bar_reach(g.p)), x + g.p.sv / 2 + bar_reach(g.p), y)


@glyph('uni04D8', 'Ә', letter_width(9, 2), kind='cap', openings=[MOUTH])
def Schwa(g):
    """Э whose lower beak runs on up into its bar: the e turned, at the
    capital height, with a beak where it opens."""
    f = _mouth_frame(g, 9, (6, 11))
    p, H, d = f.p, f.p.cap, beak_free(g)
    g.stroke((f.X(1), H - d), B(*f.P(1, 11)), B(*f.P(8, 11)), B(*f.P(8, 1)), B(*f.P(1, 1)), f.P(1, 6))
    g.stroke(f.P(1, 6), f.P(8, 6))
    g.defaults_used['mouth'] = (H - d) - (f.Y(6) + g.sh / 2)


@ccap('uni0498', 'Ҙ', 9, 2, squint=ZE_BOWLS)                # (its small capital's bays as the з's: at Black they were slits, the italic's lower one shut)
def Zedesc(g):
    from .cyrillic import ze_shape
    f = Frame(g, 9)
    ze_shape(g, drop_leg(g.p, f.X(8) - f.X(1)))
    drop(g, g.W / 2)


@ccap('uni04AA', 'Ҫ', 9, 2)
def Esdesc(g):
    from .caps import c_shape
    f = Frame(g, 9)
    c_shape(g, drop_leg(g.p, f.X(8) - f.X(1)))
    drop(g, g.W / 2)


def bar_reach(p):
    """How far a bar reaches past the stem it crosses or leads into: two
    modules, or three quarters of a stem where that is more, so it shows
    as a bar at every weight."""
    return max(2 * room(p), 0.75 * p.sv)


def lead(p):
    """How far Ҡ's bar leads in to its stem from the left (in the
    monospaced cell, half a bar's reach: the K beside it needs the room)."""
    return bar_reach(p) * (0.5 if p.mono else 1.0)


@ccap('uni04A0', 'Ҡ', 9, 1, width=lambda p: REGISTRY['K'].width(p) + lead(p))
def Kabashkir(g):
    """K with a bar at the top of its stem, leading in from the left (Ъ's)."""
    p = g.p
    f = Frame(g, 9)
    xs = lead(p) + p.sv / 2
    g.stroke((0, f.Y(11)), (xs, f.Y(11)))
    g.stroke((xs, 0), (xs, p.cap))
    for pts, a, b in k_arms(g, xs, f.W, p.cap):
        g.stroke(*pts, start=a, end=b)


@ccap('uni0496', 'Җ', 13, 3, width=plus_room('uni0416'))
def Zhedesc(g):
    f = Frame(g, 13)
    p = g.p
    Wk = g.W - room(p)
    stamp(g, 'uni0416', width=Wk)
    k = p.sd / SQRT2
    descender(g, f, Wk + p.c - k - f.Y(1), g.W - p.sv / 2)


@ccap('uni04B2', 'Ҳ', 10, 2, width=plus_room('X'))
def Hadesc(g):
    f = Frame(g, 10)
    p = g.p
    Wx = g.W - room(p)
    stamp(g, 'X', width=Wx)
    descender(g, f, Wx - p.sv / 2, g.W - p.sv / 2)


@ccap('uni04B6', 'Ҷ', 10, 2)
def Chedesc(g):
    f = Frame(g, 10)
    p = g.p
    g.stroke(f.P(1, 12), B(*f.P(1, 5)), f.P(8, 5))
    g.stroke(f.P(8, 12), f.P(8, 1))
    descender(g, f, f.X(8), g.W - p.sv / 2)


@ccap('uni04AC', 'Ҭ', 10, 1)
def Tedesc(g):
    f = Frame(g, 10)
    p = g.p
    g.stroke(f.P(0, 11), f.P(10, 11))
    xs = f.X(5)
    g.stroke((xs, f.Y(11)), (xs, f.Y(1)))
    descender(g, f, xs, xs + room(p))


@ccap('uni04A4', 'Ҥ', 12, 2)
def Enghe(g):
    """Н whose right stem carries Г's bar."""
    f = Frame(g, 12)
    g.stroke(f.P(1, 0), f.P(1, 12))
    g.stroke(f.P(8, 0), f.P(8, 11), f.P(12, 11))
    g.stroke(f.P(1, 6), f.P(8, 6))


@ccap('uni0494', 'Ҕ', 9, 2)
def Ghemidhook(g):
    """Г with Ђ's hook from the middle of its stem."""
    f = Frame(g, 9)
    p = g.p
    _down(g, p.desc)
    from .italic_forms import tail_run
    g.stroke(f.P(1, 0), f.P(1, 11), f.P(7, 11))
    yh = hook_y(g, f)
    g.stroke(f.P(1, 6), B(*f.P(8, 6)), B(f.X(8), yh), (f.X(8) - tail_run(p, f.X(8) - f.X(5)), yh))


def hook_reach(p):
    """How far a hook's side stands from the stem it leaves: a stem and two
    modules of white, so its white grows with the stroke. In the
    monospaced cell, no more than leaves the letter beside it two stems
    and a module and a half of white."""
    reach = p.sv + 2 * room(p)
    if p.slant:
        # in the italic at least an arm the hook's corner curves on (italic_forms.arm_floor)
        from .italic_forms import arm_floor
        reach = max(reach, arm_floor(p))
    if p.mono:
        reach = min(reach, max(p.fig_w - 2 * p.sv - 1.5 * room(p), 0.5 * p.sv))
    return reach


def frame_in(g, wm, W, zone='cap'):
    """A frame over the first W units of the body: the letter drawn there,
    an added part (a hook) beyond it."""
    W0 = g.W
    g.W = W
    f = Frame(g, wm, zone)
    g.W = W0
    x0, y0, _, y1 = g.clip
    g.clip = (x0, y0, W0, y1)
    return f


@ccap('uni04A6', 'Ҧ', 9, 2, width=lambda p: REGISTRY['uni041F'].width(p) + hook_reach(p))
def Pemidhook(g):
    """П with Ђ's hook from the middle of its right stem."""
    p = g.p
    f = frame_in(g, 9, g.W - hook_reach(p))
    _down(g, p.desc)
    g.stroke(f.P(1, 0), f.P(1, 11), f.P(8, 11), f.P(8, 0))
    from .italic_forms import tail_run
    xs = f.X(8)
    xh = xs + hook_reach(p)
    yh = hook_y(g, f)
    g.stroke((xs, f.Y(6)), B(xh, f.Y(6)), B(xh, yh), (xh - tail_run(p, 1.5 * room(p)), yh))


@ccap('uni0524', 'Ԥ', 10, 2)
def Pedesc(g):
    f = Frame(g, 10)
    p = g.p
    g.stroke(f.P(1, 0), f.P(1, 11), f.P(8, 11), f.P(8, 1))
    descender(g, f, f.X(8), g.W - p.sv / 2)


@ccap('uni049E', 'Ҟ', 9, 1, width=plus_room('K'))
def Kastroke(g):
    """K with Ħ's bar through the top of its stem, laid over it at the
    Regular's thickness (draw.lay_bar). Its right half sits in the V between
    the stem and the upper arm, which the K's own growth closes from below
    (at Black the arm's root reaches the bar), so the bar rises with the
    weight as far as it must to keep BAR_WHITE beside it at both ends
    (draw.bar_white): from about 600, to the top of the stem at Black (the
    owner, 2026-11-06)."""
    from shapely.geometry import LineString

    from ..draw import BAR_WHITE, Glyph, _thickness, bar_white
    from ..geom import rings_to_shapely
    p = g.p
    dx = room(p)
    stamp(g, 'K', dx, width=g.W - dx)
    x1 = dx + p.sv + room(p)
    t = g.held()
    y0 = 0.75 * p.cap + g.sh / 4

    def white(y):
        h = Glyph(p, g.name, W=g.W)
        stamp(h, 'K', dx, width=g.W - dx)
        h.clip = g.clip
        h.lay((0.0, y, t), (x1, y), c=p.c)
        return bar_white(h)
    y = y0
    least = BAR_WHITE * p.m
    if white(y0) < least:
        lo, hi = y0, p.cap - t / 2
        for _ in range(14):
            mid = (lo + hi) / 2
            lo, hi = (lo, mid) if white(mid) >= least else (mid, hi)
        y = hi
    # settled a few units up where its end lands a hairline off the arm (Mono's italic at 550 on the
    # heavy grade), never down into the white it rose for
    run = (_thickness(p, g.sh)((1.0, 0.0)) - t) / 2
    letter = rings_to_shapely(g.outline(record=False)[0])

    def ends(y_):
        # Where it has risen to the top and the arm still comes in under it (Arris Mono Narrow Italic from
        # 550, whose K stands in a narrow cell), its end stops the least white short of the arm's edge at its
        # underside, or a module past the stem where that is less: run on, the end's corner met the arm in a
        # pinch of a third of a unit at 600, and crossed it at 550. Where that is not clean either (the italic
        # at Black, the arm's root at the bar), it runs on into the arm as before.
        under = y_ - t / 2 - 0.5
        wall = letter.intersection(LineString([(dx + p.sv + 1.0, under), (g.W + p.m, under)]))
        xs = [q.coords[0][0] for q in getattr(wall, 'geoms', [wall]) if not q.is_empty and q.geom_type == 'LineString']
        short = min([x1] + [x - least_white(p) for x in xs if x > dx + p.sv])
        short = max(short, dx + p.sv + p.m)
        return [short, x1] if short < x1 else [x1]

    g.settle([[((-run, y_, t), (x, y_))]
              for y_ in sorted({min(y + d, p.cap - t / 2) for d in (0, 2, 4, 8, 12)}) for x in ends(y_)], lay=True)


@ccap('uni04B4', 'Ҵ', 13, 3)
def Tetse(g):
    """Т and Ц on one stem: the T's bar leads in from the left."""
    f = Frame(g, 13)
    p = g.p
    xs, xr = f.X(4), f.X(11)
    g.stroke(f.P(0, 11), (xs + p.sv / 2 + 0.5 * room(p), f.Y(11)))
    g.stroke((xs, f.Y(11)), (xs, f.Y(1)))
    g.stroke((xr, p.cap), (xr, f.Y(1)))
    descender(g, f, xs, g.W - p.sv / 2)


@ccap('uni04E0', 'Ӡ', 9, 2)
def Dzeabkhasian(g):
    """The 3 with a flat top and a 45-degree return (ẞ's), its lower bowl
    the 3's."""
    f = wedge_bars(g, lambda: Frame(g, 9), lambda f: f.X(8) - f.X(4))
    p, d = f.p, beak_depth(f.p, g.sh)
    x8, xm = f.X(8), f.X(4)
    ym = f.Y(11) - (x8 - xm)
    g.stroke(f.P(1, 11), (x8, f.Y(11)), (xm, ym))
    g.stroke((xm, ym), B(x8, ym), B(*f.P(8, 1)), B(*f.P(1, 1)), (f.X(1), d))


@ccap('uni04F6', 'Ӷ', 8, 1)
def Ghedesc(g):
    """Г with Ц's tail turned to the left of its foot."""
    f = Frame(g, 8)
    p = g.p
    xs = f.X(2)
    g.stroke((xs, f.Y(1)), (xs, f.Y(11)), f.P(8, 11))
    descender(g, f, xs, p.sv / 2)


@ccap('uni04CB', 'Ӌ', 9, 2)
def Chekhakassian(g):
    """Ч with its descender to the left of the stem's foot."""
    f = Frame(g, 9)
    p = g.p
    g.stroke(f.P(1, 12), B(*f.P(1, 5)), f.P(8, 5))
    g.stroke(f.P(8, 12), f.P(8, 1))
    descender(g, f, f.X(8), f.X(8) - room(p))


@ccap('uni04C7', 'Ӈ', 9, 2)
def Enhook(g):
    f = Frame(g, 9)
    g.stroke(f.P(1, 0), f.P(1, 12))
    g.stroke(f.P(1, 6), f.P(8, 6))
    hook(g, f, f.X(8), g.p.cap)


@ccap('uni0512', 'Ԓ', 9, 2)
def Elhook(g):
    from .cyrillic import _el_leg
    f = Frame(g, 9)
    g.stroke(f.P(2.5, 11), f.P(8, 11))
    _el_leg(g, f)
    hook(g, f, f.X(8), f.Y(11), reach=3.0)


def _tailed(name, base, turn=True):
    """A letter whose right stem carries a tail (or a descender)."""
    def fn(g, base=base):
        f = Frame(g, 9)
        g.clip = None                                        # (the base brings its marks)
        p = g.p
        Wb = g.W - room(p)
        stamp(g, base, width=Wb)
        descender(g, f, Wb - p.sv / 2, g.W - p.sv / 2, turn=turn)
    return fn


for _cp, _base, _turn in ((0x04C9, 'H', True), (0x04CD, 'M', True), (0x04C5, 'uni041B', True),
                          (0x048A, 'uni0419', True), (0x052E, 'uni041B', False)):
    ccap(f'uni{_cp:04X}', chr(_cp), 9, 2, width=plus_room(_base))(_tailed(f'uni{_cp:04X}', _base, _turn))


@ccap('uni04C3', 'Ӄ', 9, 2)
def Kahook(g):
    """K's arm, and from where it meets the stem Ђ's hook."""
    f = Frame(g, 9)
    p = g.p
    xs = f.X(1)
    g.stroke((xs, 0), (xs, p.cap))
    k = p.sd / SQRT2
    Wa = f.X(7) + p.sv / 2
    a = Wa - p.cap + p.c - k                                # the arm: x - y = a
    yj = xs - a
    g.stroke((p.cap + a, p.cap), (xs, yj), start='h')
    from .italic_forms import tail_run
    yh = min(yj, f.Y(6))
    yb = hook_y(g, f)
    g.stroke((xs, yh), B(f.X(8), yh), B(f.X(8), yb), (f.X(8) - tail_run(p, f.X(8) - f.X(4.5)), yb))
    _down(g, p.desc)


@ccap('uni049C', 'Ҝ', 10, 2)
def Kavertical(g):
    """K with a short stem through its arm: a stroke added to the letter,
    the Regular's thickness at every heavier weight and laid over it
    (draw.lay_bar). It crosses the arm where arm and leg have parted enough
    for it to show KV_SHOW of its thickness below the arm (a stem at most)
    with its foot's near corner half its thickness clear of the leg, and
    shows as much above
    the arm, up to the cap height; two modules of white from K's stem at
    least. Where the arm is too thick for that (ҝ toward Black) it shows
    less on both sides, never under KV_LEAST below the arm, and above it
    what the x-height leaves. Two modules from the stem, at
    the weight's own thickness, it stood where the arm meets the leg: from
    SemiBold it was a bump on the arm with no white under it, and ҝ's
    nothing at Black."""
    f = Frame(g, 10)
    p = g.p
    g.stroke(f.P(1, 0), f.P(1, 12))
    for pts, a, b in k_arms(g, f.X(1), f.W, p.cap):
        g.stroke(*pts, start=a, end=b)
    k = p.sd / SQRT2
    a_arm = f.W - p.cap + p.c - k                           # the arm's centre: x - y = a_arm
    a_leg = f.W + p.c - k                                   # the leg's: x + y = a_leg

    def ends(t, own):
        gap = t                                             # (at its centre: its near corner half of it, the leg rising to it at 45°)
        e = max(KV_LEAST * t, min(KV_SHOW * t, p.sv, (p.cap - 4 * k - gap) / 3))
        x_lo = (a_arm + a_leg + 2 * k + e + gap) / 2        # e below the arm, gap over the leg
        x_hi = a_arm + p.cap - k - e                        # e above the arm, under the cap height
        x = max(f.X(1) + p.sv + 2 * room(p), x_lo)
        if x > x_hi:                                        # (the arm too thick: it keeps the white under it)
            x = max(x_hi, x_lo)
        lo = max(x - a_arm - k - e, a_leg - x + k + gap)
        hi = min(x - a_arm + k + e, p.cap)
        return (x, lo), (x, hi)
    lay_bar(g, ends, direction=(0.0, 1.0))


KV_SHOW = 1.5     # Ҝ: its short stem shows this many of its thicknesses past the arm, each side ...
KV_LEAST = 0.5    # ... and never fewer than this


@ccap('uni04B8', 'Ҹ', 11, 3)
def Chevertical(g):
    """Ч with a short stem through its bar."""
    f = Frame(g, 11)
    g.stroke(f.P(1, 12), B(*f.P(1, 5)), f.P(10, 5))
    g.stroke(f.P(10, 12), f.P(10, 0))
    g.stroke(f.P(5.5, 2.5), f.P(5.5, 7.5))


def _tick(g, x_corner, y_corner, inside):
    """A short 45-degree stroke through a bowl's lower right corner, from
    ``inside`` (font units, along y) above it out as far below; heavy
    weights shorten it inside, as the Q's tail, so the counter stays open."""
    p = g.p
    a = x_corner + y_corner                                # x + y on the corner
    y0 = y_corner + g.free('tick', inside)
    y1 = y_corner - inside
    g.stroke((a - y0, y0), (a - y1, y1), start='h', end='h')


def _tick_least(p):
    """How short the tick may be drawn inside the bowl (``tick``, above the
    corner) and still start within the bowl's ink: its start, cut level, is
    sd·√2 wide about the stroke's centre, and on the corner it stood out of
    the bowl's side by sd/√2 - sv/2 (16 units at Bold), a ledge over the
    tick (ҏ at Bold and ExtraBold). A break short of that, at least."""
    return max(0.0, p.sd / SQRT2 - p.sv / 2 + p.c)


_TICK = Opening(lambda g: g.counter_size(), 'tick', _tick_least, max_ratio=0.85)


@glyph('uni048E', 'Ҏ', letter_width(9, 2), kind='cap', openings=[_TICK])
def Ertick(g):
    """Р with a short 45-degree stroke through its bowl's lower corner."""
    REGISTRY['P'].fn(g)
    f = Frame(g, 9)
    p = g.p
    g.clip = (0, 0, g.W + p.m, p.cap)
    _tick(g, f.X(8), f.Y(6), 2.0 * p.m)


@ccap('uni0480', 'Ҁ', 9, 2)
def Koppa(g):
    """C whose lower arm turns down into the descender."""
    f = Frame(g, 9)
    p, H, d = f.p, f.p.cap, beak_depth(f.p, g.sh)
    g.stroke((f.X(8), H - d), B(*f.P(8, 11)), B(*f.P(1, 11)), B(*f.P(1, 1)), f.P(7.5, 1), (f.X(7.5), -TAIL * p.desc))
    _down(g, TAIL * p.desc)


@ccap('uni04FE', 'Ӿ', 10, 2)
def Hastroke(g):
    """X with a bar across its crossing, the body's width less half a module
    each side, so it reaches past the diagonals at every weight."""
    REGISTRY['X'].fn(g)
    f = Frame(g, 10)
    lay_bar(g, lambda t, own: ((f.X(0.5) - (own - t) / 2, f.Y(6)), (f.X(9.5) + (own - t) / 2, f.Y(6))))


@ccap('uni04FC', 'Ӽ', 10, 2, width=plus_room('X', 0.5))
def Hahook(g):
    f = Frame(g, 10)
    p = g.p
    Wx = g.W - 0.5 * room(p)
    stamp(g, 'X', width=Wx)
    hook(g, f, Wx - p.sv / 2, g.sh, reach=3.0)


@ccap('uni04FA', 'Ӻ', 7, 1, width=plus_room('uni0413', 1.5))
def Ghestrokehook(g):
    """Ғ whose foot runs on into a hook below the baseline (Ҕ's, turned
    under the foot)."""
    p = g.p
    dx = 1.5 * room(p)
    stamp(g, 'uni0413', dx, width=g.W - dx)
    xs = dx + p.sv / 2
    cross_bar(g, 0, dx + p.sv + 2 * room(p), p.cap / 2)
    xh = xs + hook_reach(p)
    yb = -p.desc + g.sh / 2
    g.stroke((xs, g.sh / 2), B(xh, g.sh / 2), B(xh, yb), (xs, yb))


@ccap('uni0518', 'Ԙ', 14, 3, width=lambda p: REGISTRY['uni042F'].width(p) + 5 * room(p))
def Yae(g):
    """Я and Е on one stem."""
    f = Frame(g, 14)
    p = g.p
    Wy = REGISTRY['uni042F'].width(p) if not p.mono else 0.6 * g.W
    stamp(g, 'uni042F', width=Wy)
    xs = Wy - p.sv / 2
    for y in (11, 6, 1):
        g.stroke((xs, f.Y(y)), (g.W - (room(p) if y == 6 else 0), f.Y(y)))


@ccap('uni0510', 'Ԑ', 9, 2)
def Zereversed(g):
    REGISTRY['uni0417'].fn(g)
    mirror(g)


@ccap('uni0500', 'Ԁ', 9, 2)
def Dekomi(g):
    """The d at capital height: a stem on the right, the bowl at its foot."""
    f = Frame(g, 9)
    g.stroke(f.P(8, 0), f.P(8, 12))
    g.stroke(f.P(8, 7), B(*f.P(1, 7)), B(*f.P(1, 1)), f.P(8, 1), closed=True)


def _che_abkhaz(g, f, xl, xr, top, yb, ybot, beak, foot_leg=None):
    """Ҽ: an e (its eye closed above the bar, its arm open below) whose bar
    runs on to the left past the bowl and leaves on a 45-degree upstroke.
    ``foot_leg``: the foot corners' leg (Ҿ's drop hangs between them)."""
    p = g.p
    g.stroke((xl, yb), (xr, yb), B(xr, top), B(xl, top), closed=True)
    if beak:
        d = beak_free(g)
        g.stroke((xl, yb), B(xl, ybot, foot_leg), B(xr, ybot, foot_leg), (xr, d))
        g.defaults_used['mouth'] = (yb - g.sh / 2) - d
    else:
        g.stroke((xl, yb), B(xl, ybot, foot_leg), (xr, ybot))
    x1 = xl - p.sv / 2 - room(p)
    L = 1.5 * room(p) + p.sv / 2
    if p.mono:                                              # the cell's edge stops it
        x1 = max(x1, xl - p.sv / 2 - 0.5 * room(p))
        L = max(min(L, x1 - p.sd / SQRT2), 0.5 * p.sv)
    g.stroke((xl, yb), (x1, yb), (x1 - L, yb + L), end='h')
    x0, y0, x1_, y1 = g.clip
    g.clip = (min(x0, x1 - L - p.sv), y0, x1_, y1)


@glyph('uni04BC', 'Ҽ', letter_width(11, 2), kind='cap', openings=[MOUTH])
def Cheabkhasian(g):
    f = _mouth_frame(g, 11, (1, 6))
    _che_abkhaz(g, f, f.X(3.5), f.X(10), f.Y(11), f.Y(6), f.Y(1), beak=True)


@glyph('uni04BE', 'Ҿ', letter_width(11, 2), kind='cap', openings=[MOUTH])
def Chedescabkhasian(g):
    f = _mouth_frame(g, 11, (1, 6))
    _che_abkhaz(g, f, f.X(3.5), f.X(10), f.Y(11), f.Y(6), f.Y(1), beak=True,
                foot_leg=drop_leg(g.p, f.X(10) - f.X(3.5)))
    drop(g, (f.X(3.5) + f.X(10)) / 2)


def _ha_mouth(g):
    return g.defaults_used['mouth']


def _ha_loop_limit(p):
    """The lowest the loop's top may come: its counter keeps half a stem."""
    return 1.5 * p.sh + 0.5 * p.sv


# Ҩ stacks a beak, a mouth and a loop in its height, more than the x-height
# holds at Black: its mouth keeps 0.4 of a stem, the beak shortening first,
# then the loop coming down as far as its own counter allows.
@glyph('uni04A8', 'Ҩ', letter_width(11, 3), kind='cap',
       openings=[Opening(_ha_mouth, 'beak', _beak_limit, max_ratio=0.4),
                 Opening(_ha_mouth, 'loop', _ha_loop_limit, max_ratio=0.4)])
def Haabkhasian(g):
    """A big bowl open at the top, a closed loop inside its lower right,
    the foot running on past the loop. Its mouth (the beak over the loop)
    shortens the beak, then lowers the loop. Where even the shortest beak
    over the lowest loop would leave less of a mouth than that (the small
    letter at Black and a heavy grade), or the bowl is too narrow to turn
    down (the monospaced cell), the bowl ends flat on its top bar."""
    from ..params import outer_leg
    # (in the italic the beak keeps its flank and cannot shorten, _mouth_frame: the loop comes down all it may,
    # and past that the bars give, as the Ә's and the Ҽ's. Over the loop at its lowest the mouth was 26 units
    # at a stem of 189 and 5 at Black)
    f = _mouth_frame(g, 11, (6.5, 11), floor=_ha_loop_limit(g.p))
    p = g.p
    xr = f.X(10)
    xm = (f.X(1) + xr) / 2                                  # the loop as wide as the bowl beside it
    xl = f.X(1)
    d = beak_free(g)
    y_loop = f.Y(6.5)
    yl = min(g.free('loop', y_loop), y_loop)
    start = [(xm, p.cap - d), B(xm, f.Y(11))]
    g.defaults_used['mouth'] = (p.cap - d) - (yl + g.sh / 2)
    best = (p.cap - outer_leg(p) - p.c) - (min(y_loop, _ha_loop_limit(p)) + p.sh / 2)
    corner = B(xl, f.Y(11))
    if xm - xl < p.sv + 2 * p.c or best < 0.4 * p.sv:
        start = [(xm, f.Y(11))]
        g.defaults_used['mouth'] = 1e4
        if xm - xl < p.leg + g.sh:                          # too short a bar to chamfer
            corner = (xl, f.Y(11))
    g.stroke(*start, corner, B(xl, f.Y(1)), (g.W, f.Y(1)))
    if xr - xm >= p.sv + 2 * p.c:
        g.stroke((xm, f.Y(1)), (xm, yl), B(xr, yl), (xr, f.Y(1)))
    else:                                                   # (a crowded cell: the loop closes up)
        g.stroke((xm, f.Y(1)), (xm, yl), (xr, yl))
        g.stroke((xr, yl), (xr, f.Y(1)))


def komi_hook(g, f, x, y_top, rise):
    """A stem from y_top whose foot runs on into a small u: the Komi hook."""
    p = g.p
    xh = x + hook_reach(p)
    if xh - x >= p.sv + 2 * p.c:
        g.stroke((x, y_top), B(x, f.Y(1)), B(xh, f.Y(1)), (xh, rise))
    else:                                                   # (a crowded cell: the u closes up)
        g.stroke((x, y_top), (x, f.Y(1)), (xh, f.Y(1)))
        g.stroke((xh, f.Y(1)), (xh, rise))
    return xh


def komi_width(name):
    return lambda p: REGISTRY[name].width(p) + hook_reach(p)


@ccap('uni0502', 'Ԃ', 9, 2, width=komi_width('uni0500'))
def Djekomi(g):
    p = g.p
    f = frame_in(g, 9, g.W - hook_reach(p))
    g.stroke(f.P(8, 7), B(*f.P(1, 7)), B(*f.P(1, 1)), f.P(8, 1), closed=True)
    komi_hook(g, f, f.X(8), p.cap, 0.45 * p.cap)


@ccap('uni0508', 'Ԉ', 9, 2, width=komi_width('uni041B'))
def Ljekomi(g):
    from .cyrillic import _el_leg
    p = g.p
    f = frame_in(g, 9, g.W - hook_reach(p))
    g.stroke(f.P(2.5, 11), f.P(8, 11))
    _el_leg(g, f)
    komi_hook(g, f, f.X(8), f.Y(11), 0.45 * p.cap)


@ccap('uni050A', 'Ԋ', 9, 2, width=komi_width('H'))
def Njekomi(g):
    p = g.p
    f = frame_in(g, 9, g.W - hook_reach(p))
    g.stroke(f.P(1, 0), f.P(1, 12))
    g.stroke(f.P(1, 6), f.P(8, 6))
    komi_hook(g, f, f.X(8), p.cap, 0.45 * p.cap)


@ccap('uni050E', 'Ԏ', 10, 1, width=lambda p: REGISTRY['T'].width(p) + 0.5 * hook_reach(p))
def Tjekomi(g):
    p = g.p
    f = frame_in(g, 10, g.W - 0.5 * hook_reach(p))
    g.stroke(f.P(0, 11), f.P(10, 11))
    komi_hook(g, f, f.X(5), f.Y(11), 0.45 * p.cap)


@ccap('uni050C', 'Ԍ', 9, 2)
def Sjekomi(g):
    """G without its bar: the C whose foot turns up the right side."""
    f = Frame(g, 9)
    p, H, d = f.p, f.p.cap, beak_depth(f.p, g.sh)
    g.stroke((f.X(8), H - d), B(*f.P(8, 11)), B(*f.P(1, 11)), B(*f.P(1, 1)), B(*f.P(8, 1)), f.P(8, 6))


# --- Lowercase -----------------------------------------------------------

SMALLCAP = {
    0x0493: 'uni0492', 0x049B: 'uni049A', 0x04A3: 'uni04A2', 0x0499: 'uni0498', 0x04A1: 'uni04A0',
    0x0497: 'uni0496', 0x04B7: 'uni04B6', 0x04AD: 'uni04AC', 0x04A5: 'uni04A4', 0x0525: 'uni0524',
    0x04B5: 'uni04B4', 0x04F7: 'uni04F6', 0x04CC: 'uni04CB', 0x04C8: 'uni04C7', 0x0513: 'uni0512',
    0x04CA: 'uni04C9', 0x04CE: 'uni04CD', 0x04C6: 'uni04C5', 0x048B: 'uni048A', 0x052F: 'uni052E',
    0x04C4: 'uni04C3', 0x049D: 'uni049C', 0x04B9: 'uni04B8', 0x04FB: 'uni04FA', 0x0519: 'uni0518',
    0x04A9: 'uni04A8', 0x0509: 'uni0508', 0x050B: 'uni050A', 0x050F: 'uni050E',
}
for _cp, _cap in SMALLCAP.items():
    smallcap(f'uni{_cp:04X}', chr(_cp), _cap)


def _turned(g, H):
    """Turn the drawn strokes half round within the body (x, y -> W - x, H - y)."""
    W = g.W
    g.move(lambda x, y: (W - x, H - y))


@glyph('uni04D9', 'ә', letter_width(8, 2), kind='lower', openings=REGISTRY['e'].openings)
def schwa(g):
    """The e, turned."""
    REGISTRY['e'].fn(g)
    _turned(g, g.p.xh)
    g.clip = (0, 0, g.W, g.p.xh)


@glyph('uni04E9', 'ө', letter_width(8, 2), kind='lower')
def obarred(g):
    """The o barred across, its bars thinned as the e's."""
    g.stack(3, g.p.xh, ratio=0.75)
    REGISTRY['o'].fn(g)
    f = Frame(g, 8, 'lower')
    g.stroke(f.P(1, 4.5), f.P(7, 4.5))


def _ustraight(g, f, ya=None):
    """ү: the v's 2:1 arms meeting on the baseline (or at ya), a stem below."""
    p, W = f.p, f.W
    g.clip = (0, -p.desc, W, p.xh)
    xl, xr = f.X(1), f.X(7)
    ya = f.Y(1) if ya is None else ya
    yt = ya + 2 * (W / 2 - xl)
    if yt < p.xh - 0.25 * p.sv:
        g.stroke((xl, p.xh), (xl, yt), (W / 2, ya), (xr, yt), (xr, p.xh))
    else:                                                   # no room for upright arms: 2:1 to the x-height
        run = (p.xh - ya) / 2
        g.stroke((W / 2 - run, p.xh), (W / 2, ya), (W / 2 + run, p.xh), start='h', end='h')
    g.stroke((W / 2, ya), (W / 2, -p.desc))


@glyph('uni04AF', 'ү', letter_width(8, 2), kind='lower')
def ustraight(g):
    _ustraight(g, Frame(g, 8, 'lower'))


@glyph('uni04B1', 'ұ', letter_width(8, 2), kind='lower')
def ustraightstroke(g):
    """ү with a bar on the baseline: the arms meet higher, clear of it."""
    f = Frame(g, 8, 'lower')
    p = g.p
    yb = -0.2 * p.desc
    _ustraight(g, f, ya=yb + g.sh + 0.5 * p.sv)
    _stem_bar(g, g.W / 2, yb)


@glyph('uni04B3', 'ҳ', plus_room('x'), kind='lower')
def hadesc(g):
    f = Frame(g, 8, 'lower')
    p = g.p
    Wx = g.W - room(p)
    stamp(g, 'x', width=Wx)
    descender(g, f, Wx - p.sv / 2, g.W - p.sv / 2)


@glyph('uni04AB', 'ҫ', letter_width(8, 2), kind='lower')
def esdesc(g):
    from .lower import c_shape
    f = Frame(g, 8, 'lower')
    c_shape(g, drop_leg(g.p, f.X(7) - f.X(1)))
    drop(g, g.W / 2)


@glyph('uni0481', 'ҁ', letter_width(8, 2), kind='lower')
def koppa(g):
    f = Frame(g, 8, 'lower')
    p = f.p
    from ..params import outer_leg
    d = outer_leg(p) + p.c
    g.stroke((f.X(7), p.xh - d), B(*f.P(7, 8)), B(*f.P(1, 8)), B(*f.P(1, 1)), f.P(6.5, 1), (f.X(6.5), -TAIL * p.desc))
    _down(g, TAIL * p.desc)


TICK_END = 2.0     # edge breaks: the least the ҏ's tick's end stands upright, cut by the body's clip (ertick)


@glyph('uni048F', 'ҏ', letter_width(8, 2), kind='lower', openings=[_TICK])
def ertick(g):
    """р with the tick through its bowl's lower corner, as Ҏ's. The tick
    leaves the bowl a short way, and its end is cut level underneath and
    upright by the body's clip a module past it: at the Regular a face
    1.9 breaks tall between the two. That face is held at TICK_END breaks
    at least: as the tick grew with the weight its end came inside the
    clip, and from Bold the corner cut took the upright face whole and the
    end came to a point (the owner, of a pointed end: "I never want to see
    this shape in our typefaces")."""
    f = Frame(g, 8, 'lower')
    p = g.p
    stamp(g, 'p')
    inside = 1.5 * p.m
    x_corner, y_corner = f.X(7), f.Y(1)
    tip = x_corner + y_corner - (y_corner - inside) + p.sd / SQRT2      # the tick's end, its far corner underneath
    g.clip = (-p.cap, -p.desc, min(g.W + p.m, tip - TICK_END * p.c), p.xh)
    _tick(g, x_corner, y_corner, inside)


@glyph('uni04FF', 'ӿ', letter_width(8, 2), kind='lower')
def hastroke(g):
    REGISTRY['x'].fn(g)
    f = Frame(g, 8, 'lower')
    lay_bar(g, lambda t, own: ((f.X(0.5) - (own - t) / 2, f.Y(4.5)), (f.X(7.5) + (own - t) / 2, f.Y(4.5))))


@glyph('uni04FD', 'ӽ', plus_room('x', 0.5), kind='lower')
def hahook(g):
    f = Frame(g, 8, 'lower')
    p = g.p
    Wx = g.W - 0.5 * room(p)
    stamp(g, 'x', width=Wx)
    hook(g, f, Wx - p.sv / 2, g.sh, reach=3.0)


@glyph('uni049F', 'ҟ', lambda p: REGISTRY['k'].width(p) + room(p), kind='lower')
def kastroke(g):
    """The k (its upright drawing in the italic too: the looped k is
    Latin), Ħ's bar through its ascender."""
    from ..draw import _build
    p = g.p
    dx = room(p)
    g.add_glyph(_build(REGISTRY['k'], p, 0.0, 0.0, {}, g.W - dx), dx)
    y = (p.xh + p.asc) / 2 + p.m / 2
    lay_bar(g, lambda t, own: ((-(own - t) / 2, y), (dx + p.sv + room(p), y)))


@glyph('uni0495', 'ҕ', letter_width(8, 2), kind='lower')
def ghemidhook(g):
    f = Frame(g, 8, 'lower')
    p = g.p
    g.stroke(f.P(1, 0), f.P(1, 8), f.P(6, 8))
    g.stroke(f.P(1, 4.5), B(*f.P(7, 4.5)), B(*f.P(7, -2)), f.P(3.5, -2))


@glyph('uni04A7', 'ҧ', lambda p: REGISTRY['uni043F'].width(p) + hook_reach(p), kind='lower')
def pemidhook(g):
    """п with the hook from the middle of its right stem, drawn as the
    capital's and the italic's are: the п in its own body and the hook
    hook_reach beyond it, its white growing with the stroke. (In one frame
    of eleven modules the hook's arm and tail did not grow: from Bold up its
    corners' chamfers ate both and the hook was one wedge to a point.) The
    tail runs as far as its corner needs, a module short of the п's stem;
    where that is not far enough the corner's chamfer is the smaller, so the
    tail keeps a flat to its end at every weight."""
    from .italic_forms import run_floor
    p = g.p
    f = frame_in(g, 9, g.W - hook_reach(p), 'lower')
    g.stroke(f.P(1, 0), f.P(1, 8), f.P(8, 8), f.P(8, 0))
    xs = f.X(8)
    xh = xs + hook_reach(p)
    run = min(p.sv / 2 + room(p), max(1.5 * room(p), run_floor(p)))
    leg = p.leg - max(0.0, run_floor(p) - run)
    g.stroke((xs, f.Y(4.5)), B(xh, f.Y(4.5)), ('bowl', xh, f.Y(-2), leg, None), (xh - run, f.Y(-2)))
    g.clip = (0, -p.desc, g.W, p.xh)


@glyph('uni04E1', 'ӡ', letter_width(8, 2), kind='lower')
def dzeabkhasian(g):
    """The Ӡ on the x-height, its bowl in the descender (as ʒ)."""
    f = wedge_bars(g, lambda: Frame(g, 8, 'lower'), lambda f: f.X(7) - f.X(3.5))
    p = g.p
    x7, xm = f.X(7), f.X(3.5)
    ym = f.Y(8) - (x7 - xm)
    g.stroke(f.P(1, 8), (x7, f.Y(8)), (xm, ym))
    g.stroke((xm, ym), B(x7, ym), B(*f.P(7, -2)), B(*f.P(1, -2)), (f.X(1), -p.desc + beak_depth(p, g.sh)))


def _che_small(g, desc=False):
    from .lower import _e_gap  # noqa: F401  (the same opening as the e's)
    g.stack(3, g.p.xh, ratio=0.75)
    f = Frame(g, 10, 'lower')
    yb = g.free('bar', f.Y(4))                              # heavy weights raise the bar, as the e's
    g.defaults_used.update(bar=yb, arm=f.Y(1))
    _che_abkhaz(g, f, f.X(3), f.X(9), f.Y(8), yb, f.Y(1), beak=False,
                foot_leg=drop_leg(g.p, f.X(9) - f.X(3)) if desc else None)
    if desc:
        drop(g, (f.X(3) + f.X(9)) / 2)


@glyph('uni04BD', 'ҽ', letter_width(10, 2), kind='lower', openings=REGISTRY['e'].openings)
def cheabkhasian(g):
    _che_small(g)


@glyph('uni04BF', 'ҿ', letter_width(10, 2), kind='lower', openings=REGISTRY['e'].openings)
def chedescabkhasian(g):
    _che_small(g, desc=True)


@glyph('uni0503', 'ԃ', lambda p: REGISTRY['d'].width(p) + hook_reach(p), kind='lower')
def djekomi(g):
    """The d (its upright drawing), its stem's foot running on into the Komi hook."""
    p = g.p
    f = frame_in(g, 8, g.W - hook_reach(p), 'asc')
    g.stroke(f.P(7, 8), B(*f.P(1, 8)), B(*f.P(1, 1)), f.P(7, 1), closed=True)
    komi_hook(g, f, f.X(7), p.asc, 0.45 * p.xh)


@glyph('uni050D', 'ԍ', letter_width(8, 2), kind='lower')
def sjekomi(g):
    f = Frame(g, 8, 'lower')
    p = f.p
    from ..params import outer_leg
    d = outer_leg(p) + p.c
    g.stroke((f.X(7), p.xh - d), B(*f.P(7, 8)), B(*f.P(1, 8)), B(*f.P(1, 1)), B(*f.P(7, 1)), f.P(7, 4.5))


# --- Italic -----------------------------------------------------------------
# Where the Russian italic is cursive (и as a u, п as an n, т as an m), the
# letters built on them are too: ҋ is the italic й with a tail, ҭ the
# italic т with a descender, ԥ and ҧ the italic п with a descender or a
# hook. The tick into a descender is the cursive ц's (italic_forms).

from .italic_forms import BRANCH, _free, entry, ital  # noqa: E402
from .lower import shoulder  # noqa: E402


def _ctick(g, f, x):
    """The cursive ц's descender: a small corner off the foot into a tick
    a module and a half beyond the last stem (italic_forms._u_stems)."""
    p = g.p
    xd = x + 1.5 * p.m * white_scale(p)
    return [B(xd, f.Y(1), p.m / 2), (xd, f.Y(-2))]


@ital('uni048B', 8, 2)
def shortitail_ital(g):
    """The italic й (a u), its foot running on into the cursive ц's tick."""
    from .marks import breve, gap, kept, mark_params
    f = Frame(g, 8, 'lower')
    _free(g)
    p = g.p
    xl, xr = f.X(1), f.X(7)
    g.stroke(f.P(1, 9), B(*f.P(1, 1)), *_ctick(g, f, xr))
    entry(g, f, xl)
    g.stroke(f.P(7, 9), f.P(7, 1))
    x0, y0, x1, _ = g.clip
    g.clip = (x0, y0, x1, p.asc + p.cap)
    kept(g, breve, (xl + xr) / 2, p.xh + gap(mark_params(p)), 'lc')


@ital('uni04AD', 12, 3)
def tedesc_ital(g):
    """The italic т (an m), its last stem running into the cursive ц's tick."""
    f = Frame(g, 12, 'lower')
    _free(g)
    x1, x2, x3 = f.X(1), f.X(6), f.X(11)
    g.stroke(f.P(1, 0), f.P(1, 9))
    entry(g, f, x1)
    arch, cut = shoulder(g, f, x1, x2, drop=BRANCH)
    g.stroke(*arch, (x2, 0), start=cut)
    arch, cut = shoulder(g, f, x2, x3, drop=BRANCH, joined=True)
    g.stroke((x2, f.Y(4)), (x2, arch[0][1]))                # (the middle stem up to its own arch: italic_forms.m_ital)
    g.stroke(*arch, (x3, f.Y(1)), *_ctick(g, f, x3), start=cut)


@ital('uni0525', 8, 2)
def pedesc_ital(g):
    """The italic п (an n) with the cursive ц's tick."""
    f = Frame(g, 8, 'lower')
    _free(g)
    xs, xr = f.X(1), f.X(7)
    g.stroke(f.P(1, 0), f.P(1, 9))
    entry(g, f, xs)
    arch, cut = shoulder(g, f, xs, xr, drop=BRANCH)
    g.stroke(*arch, (xr, f.Y(1)), *_ctick(g, f, xr), start=cut)


@ital('uni04A7', 11, 3, width=lambda p: REGISTRY['uni043F.ital'].width(p) + hook_reach(p))
def pemidhook_ital(g):
    """The italic п (an n) with the hook from the middle of its right stem:
    the п in its own frame, the hook hook_reach beyond it, as the capital's
    (Pemidhook; drawn in one frame, its arm of three modules was too short
    for its corner from Regular up)."""
    from .italic_forms import tail_run
    p = g.p
    f = frame_in(g, 8, g.W - hook_reach(p), 'lower')
    _free(g)
    xs, xr = f.X(1), f.X(7)
    g.stroke(f.P(1, 0), f.P(1, 9))
    entry(g, f, xs)
    arch, cut = shoulder(g, f, xs, xr, drop=BRANCH)
    g.stroke(*arch, (xr, 0), start=cut)
    xh = xr + hook_reach(p)
    g.stroke((xr, f.Y(4.5)), B(xh, f.Y(4.5)), B(xh, f.Y(-2)), (xh - tail_run(p, 1.5 * room(p)), f.Y(-2)))


# --- Accented letters ------------------------------------------------------

def _compose():
    """Every letter of the Cyrillic extensions that decomposes into a base
    and marks (Ӑ Ӓ Ӗ Ӛ Ӝ Ӟ Ӣ Ӥ Ӧ Ӫ Ӭ Ӯ Ӱ Ӳ Ӵ Ӹ Ӂ ...), composed as the
    Russian ones are."""
    from . import greek, marks, symbols
    from .cyrillic import ALIASES as ru
    bases = {chr(s.unicode): n for n, s in REGISTRY.items() if s.unicode}
    for d in (ru, greek.ALIASES, symbols.ALIASES, ALIASES):
        bases.update({chr(cp): n for cp, n in d.items()})
    return marks.compose([chr(c) for c in range(0x0480, 0x0530)], bases)


ACCENTED = _compose()

