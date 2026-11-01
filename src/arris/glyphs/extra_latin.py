"""Latin letters that do not decompose: barred and slashed letters, ligatures
and the sharp s, built from existing parts where they are composites.

``stamp`` draws a finished glyph (openings solved, clipped and cut) into
another at an offset, the general way to make a composite.
"""
from __future__ import annotations

from shapely import affinity

from ..draw import AUTO_SHARE, B, NUDGE, REGISTRY, Opening, _counter_white, draw, glyph
from ..geom import rings_to_shapely
from ..params import SQRT2
from .caps import big
from .figures import STACK_MIN, beak_depth
from .lower import shoulder
from .letterframe import Frame, k_arms, letter_width


def stamp(g, name, dx=0.0, dy=0.0, width=None, clear=False):
    """Draw ``name`` into g at (dx, dy). Returns how far right it reaches:
    its body, or its ink where that runs past (an italic's exit tail).
    ``clear``: shift it right by any ink left of its body (an italic's
    entry flag), so it keeps clear of what is already there."""
    sub = draw(name, g.p, width=width)
    xs = [x for r in sub.rings() for x, _ in r] or [0.0, sub.W]
    if clear:
        dx -= min(0.0, min(xs))
    g.add_glyph(sub, dx, dy)
    return max(sub.W, max(xs))


def width_of(name, extra=0.0, scale=1.0):
    return lambda p: REGISTRY[name].width(p) * scale + extra * p.m + (0 if extra >= 0 else 0)


def plus_width(*names, gap=0.0):
    return lambda p: sum(REGISTRY[n].width(p) for n in names) + gap * p.m


def _bar(g, x0, x1, y):
    g.stroke((x0, y), (x1, y))


# --- Bars and slashes over existing letters ----------------------------------

def _slashbar(g, x, y, e):
    """A short 45-degree stroke through a stem (the Polish l's stroke)."""
    g.stroke((x - e, y - e), (x + e, y + e), start='v', end='v')


@glyph('Lslash', 'Ł', width_of('L', 1.5), kind='cap')
def Lslash(g):
    p = g.p
    dx = 1.5 * p.m
    stamp(g, 'L', dx, width=g.W - dx)
    _slashbar(g, dx + p.sv / 2, 0.45 * p.cap, 1.5 * p.m + p.sv / 2)


@glyph('lslash', 'ł', width_of('l', 1.5), kind='lower')
def lslash(g):
    p = g.p
    sub = draw('l', p, width=g.W - 1.5 * p.m if p.mono else None)
    stamp(g, 'l', width=sub.W if p.mono else None)
    xs = sub.defaults_used['stem'] if not p.mono else g.W / 2
    _slashbar(g, xs, 0.55 * p.xh + p.m, 1.5 * p.m + p.sv / 2)


def _oslash(g, name, top):
    p = g.p
    w = stamp(g, name)
    k = p.sd / SQRT2
    # along the main diagonal, square to the lower-left and upper-right chamfers;
    # at heavy weights the slash thins so the two halves of the counter stay open
    a = w / 2 - top / 2                                     # x - y = a
    lo, hi = -0.75 * p.m, top + 0.75 * p.m
    g.stroke((lo + a, lo, p.sd * g.free('slash', 1.0)), (hi + a, hi), start='h', end='h')
    g.clip = (-p.m, lo, w + p.m, hi)


def _split_counters(n):
    """Opening for a stroke that crosses a bowl: the n counters it makes keep
    half their share of the stem (as every closed counter does), by thinning
    the crossing stroke to half."""
    return Opening(lambda g: _counter_white(g, n), 'slash', lambda p: 0.5, max_ratio=AUTO_SHARE, hold=True)


@glyph('Oslash', 'Ø', width_of('O'), kind='cap', openings=[_split_counters(2)])
def Oslash(g):
    _oslash(g, 'O', g.p.cap)


@glyph('oslash', 'ø', width_of('o'), kind='lower', openings=[_split_counters(2)])
def oslash(g):
    _oslash(g, 'o', g.p.xh)


@glyph('Dcroat', 'Đ', width_of('D', 1.5), kind='cap')
def Dcroat(g):
    p = g.p
    dx = 1.5 * p.m
    stamp(g, 'D', dx, width=g.W - dx)
    _bar(g, 0, dx + p.sv + 2.5 * p.m, p.cap / 2)


@glyph('Eth', 'Ð', width_of('D', 1.5), kind='cap')
def Eth(g):
    Dcroat(g)


@glyph('dcroat', 'đ', width_of('d', 1.5), kind='lower')
def dcroat(g):
    p = g.p
    w = stamp(g, 'd', width=g.W - 1.5 * p.m)
    xs = w - p.sv / 2
    _bar(g, xs - 2.5 * p.m, xs + 1.5 * p.m + p.sv / 2, (p.xh + p.asc) / 2 + p.m / 2)


@glyph('Hbar', 'Ħ', width_of('H', 2.0), kind='cap')
def Hbar(g):
    p = g.p
    w = stamp(g, 'H', p.m, width=g.W - 2 * p.m)
    _bar(g, 0, w + 2 * p.m, 0.75 * p.cap + g.sh / 4)


@glyph('hbar', 'ħ', width_of('h', 1.0), kind='lower')
def hbar(g):
    p = g.p
    w = stamp(g, 'h', p.m, width=g.W - p.m)
    _bar(g, 0, p.m + p.sv + 2 * p.m, (p.xh + p.asc) / 2 + p.m / 2)


@glyph('Tbar', 'Ŧ', width_of('T'), kind='cap')
def Tbar(g):
    p = g.p
    w = stamp(g, 'T')
    _bar(g, w / 2 - 2 * p.m, w / 2 + 2 * p.m, p.cap / 2)


def _slot(g, w, x1):
    """The t's slot: the white right of its stem between the crossbar and the
    hook, where the ŧ's bar lies. Read off the t's own ink along the bar's run
    there, six cuts from the stem to the bar's end: the slot's top and foot,
    the right edge of the t's ink, the t's rings and the first cut's x."""
    from shapely.geometry import LineString
    p = g.p
    rings, _ = draw('t', p).outline(record=False)
    ink = rings_to_shapely([[tuple(q[:2]) for q in r] for r in rings])
    col, wm = (3, 9) if p.mono else (2, 7)                     # the t's stem column in its frame (lower.t)
    xs = p.sv / 2 + (w - p.sv) * (col - 1) / (wm - 2) + p.sv / 2 + p.c
    top, foot = p.xh, 0.0
    for k in range(6):
        xc = xs + (x1 - p.c - xs) * k / 5
        cut = ink.intersection(LineString([(xc, -p.desc), (xc, p.asc)]))
        spans = [(gm.bounds[1], gm.bounds[3]) for gm in getattr(cut, 'geoms', [cut]) if not gm.is_empty]
        top = min([top] + [lo for lo, hi in spans if lo > p.xh / 2])
        foot = max([foot] + [hi for lo, hi in spans if hi < p.xh / 2])
    return top, foot, ink.bounds[2], rings, xs


@glyph('tbar', 'ŧ', width_of('t'), kind='lower')
def tbar(g):
    # The bar lies in the slot between the t's crossbar and its hook, at
    # 0.45 of the x-height, a stroke thick, from the left edge to a module
    # short of the right. Toward Black the slot narrows (at Black with the
    # watch's strokes it is 190 units for a 175-unit stroke) and the bar
    # filled it: the ŧ was a blob. The bar adapts, by the least that keeps
    # it a bar: it thins to what the slot holds with a module of white on
    # each side, no thinner than the stack minimum of a bar (0.7 of the
    # stroke), and moves off the x-height's 0.45 only as far as that asks;
    # and where even that leaves no white it runs on past the t's
    # right edge by a module, so a bump of bar stands clear of the mass
    # where the slot has closed (the owner: the tiny bump is fine).
    p = g.p
    w = stamp(g, 't')
    x1 = REGISTRY['t'].width(p) - p.m
    top, foot, right, rings, xs = _slot(g, w, x1)
    # Left of the stem the bar is a short nub, and the fill under it, a break
    # at 45 degrees, runs parallel to the hook's outer chamfer on the stem's
    # left edge: landing near that chamfer's top it leaves a step between
    # two parallel diagonals, a hairline or a jog, and bends the bowl's line
    # off 45 degrees, which the italic (curving that line) held straight at
    # 600 with the watch's strokes and curved again at 800. So the bar's
    # underside keeps its fill half a break above that top as well as a
    # module of white below it in the slot. (The fills on the stem's other
    # corners meet their neighbours mirrored, closing into a V: harmless.)
    stem_l = xs - p.c - p.sv
    leg = max([foot] + [q[1] for r in rings for q in r if abs(q[0] - stem_l) <= 1 and q[1] < p.xh / 2])
    low, high = max(foot + p.m, leg + 1.5 * p.c), top - p.m
    floor = STACK_MIN * g.sh
    thick = min(g.sh, max(floor, high - low))
    if high - low >= thick:
        y = min(max(p.xh * 0.45, low + thick / 2), high - thick / 2)
        cands, seen = [], set()
        for d in NUDGE:
            y_ = min(max(y + d, low + thick / 2), high - thick / 2)
            t_ = thick if y_ != y or d == 0 else thick - abs(d)      # pinned: thinner instead
            if t_ >= floor and (y_, t_) not in seen:
                seen.add((y_, t_))
                cands.append([((0, y_, t_), (x1, y_, t_))])
        g.settle(cands)
        return
    # no white to keep: right of the stem the bar fills the slot whole, a
    # break over, so no sliver is left, and runs on past the right edge, a
    # bump a module long; left of it the nub stays a stroke thick where it
    # fits between the hook's chamfer and the crossbar's arm with half a
    # break of notch above it (the two meet in the stem), and where it does
    # not the fill runs through to the left edge
    xc = stem_l + p.sv / 2
    y, thick, x1 = (top + foot) / 2, max(g.sh, top - foot + p.c), max(x1, right + p.m)
    tn = min(g.sh, top - p.c / 2 - low)
    cands, seen = [], set()
    if tn >= floor:
        for d in NUDGE:
            yn = min(max(low + tn / 2 + d, low + tn / 2), top - p.c / 2 - tn / 2)
            if yn not in seen:
                seen.add(yn)
                cands.append([((0, yn, tn), (xc, yn, tn)), ((xc, y, thick), (x1, y, thick))])
    cands.append([((0, y, thick), (x1, y, thick))])
    g.settle(cands)



@glyph('Ldot', 'Ŀ', width_of('L', 1.0), kind='cap')
def Ldot(g):
    p = g.p
    stamp(g, 'L', width=g.W)
    x = p.sv + 1.0 * p.m + p.sv / 2
    g.stroke((x, p.cap / 2 - p.sv / 2), (x, p.cap / 2 + p.sv / 2))


@glyph('ldot', 'ŀ', width_of('l', 0.5), kind='lower')
def ldot(g):
    p = g.p
    gap = max(p.m, 0.6 * p.sv)
    # in the monospaced cell the l narrows (to 0.85 of its own at most) so
    # that it and the dot fit the cell, and the pair then moves into it
    lw = None
    if p.mono:
        lw = max(min(g.W - 2 * p.m, p.fig_adv - gap - 1.5 * p.sv), 0.85 * REGISTRY['l'].width(p))
    sub = draw('l', p, width=lw)
    w = stamp(g, 'l', width=sub.W if p.mono else None)
    # beside the stem, over the tail
    x = (sub.defaults_used['stem'] if not p.mono else w) + p.sv / 2 + gap + p.sv / 2
    g.stroke((x, p.xh / 2 - p.sv / 2), (x, p.xh / 2 + p.sv / 2))
    if p.mono:                                               # the dot inside the cell: the pair moves left
        from .marks import _into_cell
        _into_cell(g)


# --- Pairs -------------------------------------------------------------------

@glyph('IJ', 'Ĳ', plus_width('I', 'J', gap=1.5), kind='cap')
def IJ(g):
    p = g.p
    gap = (0.75 if p.mono else 1.5) * p.m
    w = stamp(g, 'I', width=p.sv)
    stamp(g, 'J', w + gap, width=g.W - w - gap)


@glyph('ij', 'ĳ', plus_width('i', 'j', gap=1.0), kind='lower')
def ij(g):
    p = g.p
    w = stamp(g, 'dotlessi', width=p.sv)
    from .lower import _dot
    _dot(g, None, p.sv / 2)
    gap = (0.5 if p.mono else 1.0) * p.m
    stamp(g, 'j', w + gap, width=(g.W - w - gap) if p.mono else None, clear=True)


@glyph('napostrophe', 'ŉ', plus_width('quoteright', 'n', gap=0.5), kind='lower')
def napostrophe(g):
    p = g.p
    w = stamp(g, 'quoteright')
    stamp(g, 'n', w + 0.5 * p.m, width=(g.W - w - 0.5 * p.m) if p.mono else None, clear=True)


# --- Redrawn -----------------------------------------------------------------

@glyph('kgreenlandic', 'ĸ', letter_width(8, 1), kind='lower')
def kgreenlandic(g):
    f = Frame(g, 8, 'lower')
    g.stroke(f.P(1, 0), f.P(1, 9))
    for pts, a, b in k_arms(g, f.X(1), f.W, f.p.xh):
        g.stroke(*pts, start=a, end=b)


@glyph('longs', 'ſ', letter_width(7, 1), kind='lower')
def longs(g):
    f = Frame(g, 7, 'asc')
    g.stroke(f.P(2, 0), B(*f.P(2, 12)), f.P(7, 12))


@glyph('eng', 'ŋ', letter_width(8, 2), kind='lower')
def eng(g):
    f = Frame(g, 8, 'lower')
    p = f.p
    from .italic_forms import tail_run
    g.stroke(f.P(1, 0), f.P(1, 9))
    arch, cut = shoulder(g, f, f.X(1), f.X(7))
    g.stroke(*arch, B(*f.P(7, -2)), (f.X(7) - tail_run(p, f.X(7) - f.X(3)), f.Y(-2)), start=cut)


@glyph('Eng', 'Ŋ', letter_width(9, 2), kind='cap')
def Eng(g):
    f = Frame(g, 9)
    p = f.p
    from .italic_forms import tail_run
    g.clip = (0, -p.desc, f.W, p.cap)
    g.stroke(f.P(1, 0), f.P(1, 12))
    g.stroke(f.P(1, 11), B(*f.P(8, 11)), B(*f.P(8, -2)), (f.X(8) - tail_run(p, f.X(8) - f.X(4)), f.Y(-2)))


@glyph('Thorn', 'Þ', letter_width(9, 2), kind='cap')
def Thorn(g):
    f = Frame(g, 9)
    g.stroke(f.P(1, 0), f.P(1, 12))
    g.stroke(f.P(1, 9), B(*f.P(8, 9)), B(*f.P(8, 3)), f.P(1, 3))


@glyph('thorn', 'þ', letter_width(8, 2), kind='lower')
def thorn(g):
    f = Frame(g, 8, 'asc')
    p = f.p
    g.clip = (0, -p.desc, f.W, p.asc)
    g.stroke(f.P(1, -3), f.P(1, 13))
    g.stroke(f.P(1, 8), B(*f.P(7, 8)), B(*f.P(7, 1)), f.P(1, 1), closed=True)


@glyph('eth', '\u00f0', letter_width(8, 2), kind='lower')
def eth(g):
    """An o whose right side rises and bends back over it at 45 degrees,
    crossed level partway up (the barred d's bar)."""
    p = g.p
    f = Frame(g, 8, 'asc')
    W8 = letter_width(8, 2)(p)
    xr = W8 - p.sv / 2
    xl = p.sv / 2
    g.stroke(B(xl, g.sh / 2), B(xr, g.sh / 2), B(xr, p.xh - g.sh / 2), B(xl, p.xh - g.sh / 2), closed=True)
    y_bend = p.xh - g.sh / 2
    reach = p.asc - y_bend
    g.stroke((xr, p.xh / 2), (xr, y_bend), (xr - reach, p.asc), end='h')
    yb = p.xh + 0.45 * (p.asc - p.xh)
    xc = xr - (yb - y_bend)                                  # the diagonal's centre at the bar
    g.stroke((xc - 1.6 * p.m, yb), (xc + 1.6 * p.m, yb))
    g.clip = (0, 0, g.W, p.asc)


@glyph('germandbls', 'ß', letter_width(8, 2), kind='lower')
def germandbls(g):
    """A stem carrying the 3's right side: the waist's point, the flat end."""
    f = Frame(g, 8, 'asc')
    p = f.p
    g.stroke(f.P(1, 0), B(*f.P(1, 12)), B(*f.P(7, 12)), B(*f.P(7, 7.5), big(p)), f.P(3.5, 7.5))
    g.stroke(f.P(3.5, 7.5), B(*f.P(7, 7.5)), B(*f.P(7, 1)), f.P(3.5, 1))


@glyph('uni1E9E', 'ẞ', letter_width(9, 2), kind='cap')
def Germandbls(g):
    """Capital sharp s: a stem, a top bar, a 45-degree return, the 3's lower bowl."""
    f = Frame(g, 9)
    p = f.p
    x8 = f.X(8)
    y_mid = f.Y(11) - (x8 - f.X(4.5))
    g.stroke(f.P(1, 0), B(*f.P(1, 11)), (x8, f.Y(11)))
    g.stroke((x8, f.Y(11)), (f.X(4.5), y_mid))
    g.stroke((f.X(4.5), y_mid), B(x8, y_mid), B(*f.P(8, 1)), f.P(3, 1))


@glyph('AE', 'Æ', letter_width(13, 2), kind='cap')
def AE(g):
    f = Frame(g, 13)
    p, W, H, k = f.p, f.W, f.p.cap, f.k
    xs = f.X(7)
    xl = f.X(1)
    # the A's left leg, bending at 45 degrees into the top bar
    y_bend = f.Y(11) - (f.X(5) - xl)
    g.stroke((xl, 0), (xl, y_bend), (f.X(5), f.Y(11)), (W, f.Y(11)))
    g.stroke((xs, f.Y(11)), (xs, f.Y(1)), (W, f.Y(1)))
    g.stroke((xl, f.Y(6)), (f.X(12), f.Y(6)))


@glyph('ae', 'æ', lambda p: REGISTRY['a'].width(p) + REGISTRY['e'].width(p) - p.sv, kind='lower')
def ae(g):  # width: a + e sharing a stem
    p = g.p
    half = (g.W + p.sv) / 2
    wa = stamp(g, 'a', width=half)
    stamp(g, 'e', wa - p.sv, width=g.W - wa + p.sv)


@glyph('OE', 'Œ', letter_width(13, 2), kind='cap')
def OE(g):
    f = Frame(g, 13)
    p, W = f.p, f.W
    xs = f.X(7)
    g.stroke((xs, f.Y(1)), B(*f.P(1, 1)), B(*f.P(1, 11)), (xs, f.Y(11)), closed=True)
    g.stroke((W, f.Y(11)), (xs, f.Y(11)), (xs, f.Y(1)), (W, f.Y(1)))
    g.stroke((xs, f.Y(6)), (f.X(12), f.Y(6)))


@glyph('oe', 'œ', lambda p: REGISTRY['o'].width(p) + REGISTRY['e'].width(p) - p.sv, kind='lower')
def oe(g):
    p = g.p
    half = (g.W + p.sv) / 2
    wo = stamp(g, 'o', width=half)
    stamp(g, 'e', wo - p.sv, width=g.W - wo + p.sv)
