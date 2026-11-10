"""Lowercase a-z, built from their pixel masters (``arris.masters.LOWER``).

Module coordinates: x-height 9, ascender 13, descender -3 (see letterframe).
The same moves as the capitals and figures: beaks on c and j, the 2's notch
in z, a notched shoulder on r (the 1's flag, turned), arches that meet in a
V on m, gables on v and w.
"""
from __future__ import annotations

from ..draw import B, Opening, glyph
from ..params import outer_leg
from .figures import STACK_MIN, beak_depth, jog
from .letterframe import ARM, Frame, k_arms, least_white, letter_width


def low(char, wm, stems, width=None, openings=(), arm=ARM):
    return glyph(char, char, width or letter_width(wm, stems, arm), kind='lower', openings=openings)


def _a_gap(g):
    """White between the a's arm and the top of its bowl."""
    return g.defaults_used['arm'] - g.defaults_used['bowl'] - g.sh


A_WHITE = 1.0     # the white between the a's flag and its bowl's cut corner, in least whites


def a_flag(g, ya, yb):
    """Where the a's flag leaves its roof (x), and where it ends: the flag
    lies over the bowl's cut corner, parallel to it, the least white of a
    letter between the two, and ends where its point reaches the body's
    edge."""
    p = g.p
    k = p.sd / 2 ** 0.5
    cut = outer_leg(p, sh=g.sh)                              # the bowl's cut corner: x - y = cut - top
    xa = cut - (yb + g.sh / 2) + ya - k - A_WHITE * least_white(p) * 2 ** 0.5
    return xa, k


@low('a', 8, 2, openings=[Opening(_a_gap, 'bowl', lambda p: p.xh * 0.4, max_ratio=0.4)])
def a(g):
    """The a: the 1's flag and roof over a bowl. Its arm starts in a flag
    at the left, a 45-degree stroke ending on a horizontal as the 1's does,
    runs along the x-height and comes into the stem through a bowl's
    corner. The flag lies over the bowl's cut corner, the two parallel, and
    is as long as the white between them allows: long at Light, a point at
    Black.

    Until 1.017 the upper storey was a bare bar: square at its left end and
    all but square at the stem (the pixel master's one-step corner), the
    one letter whose top had none of the font's corners."""
    g.stack(3, g.p.xh, ratio=0.75)
    f = Frame(g, 8, 'lower')
    ya = f.Y(8)
    yb = g.free('bowl', f.Y(5))                             # heavy weights lower the bowl
    g.defaults_used.update(arm=ya, bowl=yb)
    xa, x0 = a_flag(g, ya, yb)
    xa = min(xa, f.X(7) - g.p.leg - g.p.sv / 2)             # (the roof keeps a flat before its corner)
    if xa > x0:
        g.stroke((x0, ya - (xa - x0)), (xa, ya), B(f.X(7), ya), f.P(7, 0), start='h')
    else:
        g.stroke((x0, ya), B(f.X(7), ya), f.P(7, 0))
    g.stroke((f.X(7), yb), B(f.X(1), yb), B(*f.P(1, 1)), f.P(7, 1), closed=True)


@low('b', 8, 2)
def b(g):
    f = Frame(g, 8, 'asc')
    g.stroke(f.P(1, 0), f.P(1, 13))
    g.stroke(f.P(1, 8), B(*f.P(7, 8)), B(*f.P(7, 1)), f.P(1, 1), closed=True)


@low('c', 8, 2)
def c(g):
    c_shape(g)


def c_shape(g, foot_leg=None):
    """The c. ``foot_leg``: the leg of the foot's corners (the default: the
    parameter leg); ҫ's drop hangs between them (cyrillic_ext.drop_leg)."""
    f = Frame(g, 8, 'lower')
    # The shortest beaks (the outer flank alone): an open mouth tells c from o.
    p = f.p
    d = outer_leg(p) + p.c
    g.stroke((f.X(7), p.xh - d), B(*f.P(7, 8)), B(*f.P(1, 8)), B(*f.P(1, 1), foot_leg), B(*f.P(7, 1), foot_leg),
             (f.X(7), d))


@low('d', 8, 2)
def d(g):
    f = Frame(g, 8, 'asc')
    g.stroke(f.P(7, 0), f.P(7, 13))
    g.stroke(f.P(7, 8), B(*f.P(1, 8)), B(*f.P(1, 1)), f.P(7, 1), closed=True)


def _e_gap(g):
    """White between the e's bar and its lower arm."""
    return g.defaults_used['bar'] - g.defaults_used['arm'] - g.sh


@low('e', 8, 2, openings=[Opening(_e_gap, 'bar', lambda p: p.xh * 0.6, max_ratio=0.4)])
def e(g):
    g.stack(3, g.p.xh, ratio=0.75)
    f = Frame(g, 8, 'lower')
    yb = g.free('bar', f.Y(4))                              # heavy weights raise the bar
    g.defaults_used.update(bar=yb, arm=f.Y(1))
    g.stroke((f.X(1), yb), (f.X(7), yb), B(*f.P(7, 8)), B(*f.P(1, 8)), closed=True)
    g.stroke((f.X(1), yb), B(*f.P(1, 1)), f.P(7, 1))


@low('f', 7, 1)
def f_(g):
    if g.p.mono:
        f = Frame(g, 9, 'asc')
        g.stroke(f.P(3.5, 0), B(*f.P(3.5, 12)), f.P(9, 12))
        g.stroke(f.P(0.5, 8), f.P(8, 8))
        return
    f = Frame(g, 7, 'asc')
    g.stroke(f.P(2, 0), B(*f.P(2, 12)), f.P(7, 12))
    g.stroke(f.P(0, 8), f.P(6, 8))


def crotch_butt(g, y):
    """In the italic, the line along the bottom edge of a horizontal drawn on
    ``y`` (as the strokes take its thickness), for ``Glyph.butt``: a bowl's
    foot meeting a stem that runs on down into a descender (g y д) meets it
    square there, without the corner rule's 45-degree fill. With the fill,
    the white between it and the descender's corner below ran out from about
    500 to 750 (the fill takes up to a corner break of the stem's edge; the
    corner's inner chamfer then started on the fill's diagonal), and the
    italic, which curves a corner only between straight edges, held that
    corner straight on both its edges there and curved it either side. Flush,
    the corner always meets the stem's edge or, heavier, the foot's, and
    curves at every weight."""
    if not g.p.slant:
        return ()
    from ..draw import _thickness
    return (('y', y - _thickness(g.p, g.sh)((1.0, 0.0)) / 2),)


def hook_room(p) -> float:
    """How far below its descender line a hook may still deepen: down to
    the font's descent."""
    return max(0.0, p.deep - p.desc)


def hook_fit(p, sh, white=None):
    """(the hook's thickness, how far it deepens past the descender line)
    for horizontals ``sh`` thick: the white between the hook and what stands
    over it (the g's bowl) stays ``white`` tall (least_white). The weight's
    descender line is set for exactly that (params.descender_line), so the
    g's and y's hooks stand on it at their full weight, with p q and j;
    a hook that keeps more white (ǥ's, for its bar) makes room first,
    deepening toward the font's descent, and only where that is spent
    (Black) does a hook thin, never under the stack minimum of a bar.

    Until 1.016 it thinned first, and measured its white past the corner's
    inner leg, not from bar to bar: the hook was 0.73 of the letter's other
    horizontals at Regular (57 units to the bowl's 79) and 0.7 from Medium
    up, with 123 units of white over it, a stem and a third. It read as a
    mistake (and the j's hook, with nothing over it, kept its weight)."""
    white = least_white(p) if white is None else white
    extra = min(hook_room(p), max(0.0, sh + white - p.desc))
    w = min(sh, max(STACK_MIN * sh, p.desc + extra - white))
    return w, extra


def hook(g, f, x_stem=7, x_end=1, white=None):
    """The descending hook of g, y and the italic y: the stem down from the
    body into a bowl corner and a horizontal back under it, as thick as the
    letter's other horizontals (hook_fit), on the weight's descender line.
    (The owner's rule: a feature weight would swallow grows or makes room
    by the smallest change that keeps it.)"""
    p = g.p
    w, extra = hook_fit(p, g.sh, white)
    yh = -(p.desc + extra) + w / 2
    if extra:
        x0, y0, x1, y1 = g.clip
        g.clip = (x0, min(y0, -(p.desc + extra)), x1, y1)
    g.stroke(f.P(x_stem, 9), B(f.X(x_stem), yh, None, w), (f.X(x_end), yh))


def g_strokes(g, white=None):
    """The g: its bowl and its hook (``white``: the room the hook leaves
    under the bowl, for a g that carries something there: ǥ's bar)."""
    f = Frame(g, 8, 'lower')
    g.stroke(f.P(7, 8), B(*f.P(1, 8)), B(*f.P(1, 1)), f.P(7, 1), closed=True)
    hook(g, f, white=white)
    g.butt += crotch_butt(g, f.Y(1))


@low('g', 8, 2)
def g_(g):
    g_strokes(g)


def shoulder(g, f, xs, x_right, top=8, drop=2, notch=True):
    """An arch's shoulder, as the r's: it leaves the stem at 45 degrees
    ``drop`` modules below the arch (two; the italic's branch lower), an
    edge break into the stem, and leaves a notch
    under it (the 1's flag, turned). Returns the arch's points up to its
    right corner, and how the stroke's start is cut.

    The diagonal needs room between the stems. Where there is less (the
    monospaced m, the heaviest weights) it rises less and starts further
    into the stem, down to the plain square join, so the arch keeps its
    counter and the drawing changes continuously with weight.

    ``notch`` False: the notch filled, the diagonal's underside running
    straight into the stem (the italic k at its heavy weights, k_ital).
    The diagonal then starts at the stem's centre, cut along it: cut level,
    its start is k = sd/√2 each side of x0, 16 units more than half a stem
    at Black, and far into the stem its left corner comes out of the
    stem's back (a nub of three points)."""
    p = g.p
    k = p.sd / 2 ** 0.5
    y_top = f.Y(top)
    full = f.Y(top) - f.Y(top - drop)
    x_full = xs + p.sv / 2 + k - p.c
    room = x_right - p.leg - p.c - x_full                  # the diagonal ends clear of the corner
    rise = min(full, max(room, 0.0))
    if rise < 1e-3 * p.m:
        return [(xs, y_top), B(x_right, y_top)], 'flat'
    x0 = xs + rise / full * (x_full - xs)
    if not notch:
        return [(xs, y_top - rise - (x0 - xs)), (x0 + rise, y_top), B(x_right, y_top)], 'v'
    return [(x0, y_top - rise), (x0 + rise, y_top), B(x_right, y_top)], 'h'


@low('h', 8, 2)
def h(g):
    f = Frame(g, 8, 'asc')
    g.stroke(f.P(1, 0), f.P(1, 13))
    arch, cut = shoulder(g, f, f.X(1), f.X(7))
    g.stroke(*arch, f.P(7, 0), start=cut)


def _dot(g, f, x):
    """The tittle: a square as wide as the stem, centred between x-height and
    ascender, but never closer to the x-height than 0.4 of a stem."""
    p = g.p
    s = p.dot()
    yc = max((p.xh + p.asc) / 2, p.xh + 0.4 * s + s / 2)
    g.stroke((x, yc - s / 2, s), (x, yc + s / 2))


def _mono_foot(g, f, x, u):
    g.stroke((x - 3 * u, f.Y(1)), (x + 3 * u, f.Y(1)))


@low('i', 2, 1, width=lambda p: p.sv)
def i(g):
    if g.p.mono:                                            # flag at the x-height, foot on the line
        f = Frame(g, 9, 'asc', top=g.p.asc + g.p.sv)
        u = g.W / 9
        x = g.W / 2 + u / 2
        g.stroke((x - 3 * u, f.Y(8)), (x, f.Y(8)), (x, 0))
        _mono_foot(g, f, x - u / 2, u)
        _dot(g, f, x)
        return
    f = Frame(g, 2, 'asc', top=g.p.asc + g.p.sv)
    g.stroke(f.P(1, 0), f.P(1, 9))
    _dot(g, f, f.X(1))


@low('j', 6, 1)
def j(g):
    if g.p.mono:
        f = Frame(g, 9, 'asc', top=g.p.asc + g.p.sv)
        p, u = f.p, g.W / 9
        x = g.W / 2 + 1.5 * u
        g.stroke((x - 3 * u, f.Y(8)), (x, f.Y(8)), B(x, f.Y(-2)), B(f.X(1), f.Y(-2)), (f.X(1), -p.desc + beak_depth(p)))
        _dot(g, f, x)
        return
    f = Frame(g, 6, 'asc', top=g.p.asc + g.p.sv)
    p = f.p
    g.stroke(f.P(5, 9), B(*f.P(5, -2)), B(*f.P(1, -2)), (f.X(1), -p.desc + beak_depth(p)))
    _dot(g, f, f.X(5))


@low('k', 8, 1)
def k(g):
    f = Frame(g, 8, 'asc')
    g.stroke(f.P(1, 0), f.P(1, 13))
    for pts, a, b in k_arms(g, f.X(1), f.W, f.p.xh):
        g.stroke(*pts, start=a, end=b)
    g.clip = (0, -f.p.desc, f.W, f.p.asc)


@low('l', 6, 1)
def l(g):
    if g.p.mono:
        f = Frame(g, 9, 'asc')
        u = g.W / 9
        x = g.W / 2 + u / 2
        g.stroke((x - 3 * u, f.Y(12)), (x, f.Y(12)), (x, 0))
        _mono_foot(g, f, x - u / 2, u)
        return
    # The 1's flag at the top and the t's foot at the bottom: a tail that
    # tells l from I, i and 1 (docs/research/legibility.md).
    f = Frame(g, 6, 'asc')
    g.defaults_used['stem'] = f.X(2)
    g.stroke(f.P(0, 12), f.P(2, 12), B(*f.P(2, 1)), f.P(6, 1))


@low('m', 12, 3)
def m(g):
    f = Frame(g, 12, 'lower')
    g.stroke(f.P(1, 0), f.P(1, 9))
    for xs, xr in ((f.X(1), f.X(6)), (f.X(6), f.X(11))):
        arch, cut = shoulder(g, f, xs, xr)
        g.stroke(*arch, (xr, 0), start=cut)


@low('n', 8, 2)
def n(g):
    f = Frame(g, 8, 'lower')
    g.stroke(f.P(1, 0), f.P(1, 9))
    arch, cut = shoulder(g, f, f.X(1), f.X(7))
    g.stroke(*arch, f.P(7, 0), start=cut)


@low('o', 8, 2)
def o(g):
    f = Frame(g, 8, 'lower')
    g.stroke(B(*f.P(1, 1)), B(*f.P(7, 1)), B(*f.P(7, 8)), B(*f.P(1, 8)), closed=True)


@low('p', 8, 2)
def p_(g):
    f = Frame(g, 8, 'lower')
    g.stroke(f.P(1, -3), f.P(1, 9))
    g.stroke(f.P(1, 8), B(*f.P(7, 8)), B(*f.P(7, 1)), f.P(1, 1), closed=True)


@low('q', 8, 2)
def q(g):
    f = Frame(g, 8, 'lower')
    g.stroke(f.P(7, -3), f.P(7, 9))
    g.stroke(f.P(7, 8), B(*f.P(1, 8)), B(*f.P(1, 1)), f.P(7, 1), closed=True)


@low('r', 8, 1, arm=0.5)      # its arm is the longest at Regular already (the r is wider than the n)
def r(g):
    f = Frame(g, 8, 'lower')
    p = g.p
    # In the monospaced cell the r stands two and a half modules in, on a foot.
    dx = 2.5 * g.W / 9 if p.mono else 0.0
    xs = f.X(1) + dx
    g.stroke((xs, 0), (xs, p.xh))
    # The shoulder: a 45-degree stroke from the stem to the arm, leaving a
    # notch under the arm (the 1's flag, turned).
    k = p.sd / 2 ** 0.5
    y8, y6 = f.Y(8), f.Y(6)
    x6 = xs + p.sv / 2 + k - p.c                             # starts an edge break into the stem
    g.stroke((x6, y6), (x6 + (y8 - y6), y8), f.P(8, 8), start='h')
    if p.mono:                                              # a foot, as the 1's
        u = g.W / 9
        g.stroke((xs - 2.5 * u, f.Y(1)), (xs + 2.5 * u, f.Y(1)))


@low('s', 8, 2)
def s(g):
    g.stack(3, g.p.xh, ratio=0.75)
    f = Frame(g, 8, 'lower')
    g.stroke(f.P(8, 8), B(*f.P(1, 8)), B(*f.P(1, 5)), B(*f.P(7, 5), g.p.m / 2), B(*f.P(7, 1)), f.P(0, 1))


@low('t', 7, 1)
def t(g):
    if g.p.mono:
        f = Frame(g, 9, 'asc')
        g.stroke(f.P(3, 11), B(*f.P(3, 1)), f.P(8.5, 1))
        g.stroke(f.P(0.5, 8), f.P(8, 8))
        return
    f = Frame(g, 7, 'asc')
    g.stroke(f.P(2, 11), B(*f.P(2, 1)), f.P(7, 1))
    g.stroke(f.P(0, 8), f.P(6, 8))


@low('u', 8, 2)
def u(g):
    f = Frame(g, 8, 'lower')
    g.stroke(f.P(1, 9), B(*f.P(1, 1)), f.P(7, 1))
    g.stroke(f.P(7, 0), f.P(7, 9))


def _vee(f):
    p = f.p
    ya = -p.c + f.k
    return ya


@low('v', 8, 2)
def v(g):
    f = Frame(g, 8, 'lower')
    p, W = f.p, f.W
    xl, xr = f.X(1), f.X(7)
    ya = _vee(f)
    # 2:1 arms (the 7's slope): a 45-degree gable in an x-height leaves too
    # little diagonal, and the v reads as a u (docs/research/legibility.md)
    yt = min(ya + 2 * (W / 2 - xl), p.xh)
    g.stroke((xl, p.xh), (xl, yt), (W / 2, ya), (xr, yt), (xr, p.xh))


@low('w', 14, 3)
def w(g):
    f = Frame(g, 14, 'lower')
    p, W = f.p, f.W
    xl, xm, xr = f.X(1), W / 2, f.X(13)
    q1, q3 = (xl + xm) / 2, (xm + xr) / 2
    ya = _vee(f)
    yt = min(ya + 2 * (q1 - xl), p.xh)                      # 2:1, as the v
    g.stroke((xl, p.xh), (xl, yt), (q1, ya), (xm, yt), (q3, ya), (xr, yt), (xr, p.xh))
    g.stroke((xm, yt), (xm, f.Y(6)))


def x_strokes(g, xl, xr, W, H):
    """The X and the x: two 45-degree strokes between vertical stubs, each
    stepping sideways by a jog where they cross (the 2's notch, twice):
    upper halves pass the centre a half jog early, lower halves a half jog
    late. The step is the watch's pixel; as the strokes grow past it the
    crossing takes it up and the kinks go."""
    p = g.p
    J = jog(p)
    step = min(J, g.sh)
    up, lo = (W + H - J) / 2, (W + H + J) / 2                # x + y on the falling stroke
    g.stroke((xl, H), (xl, up - xl), (up - H / 2, H / 2, step), (lo - H / 2, H / 2), (xr, lo - xr), (xr, 0))
    # the rising stroke, mirrored: x -> W - x
    g.stroke((xr, H), (xr, up - xl), (W - (up - H / 2), H / 2, step), (W - (lo - H / 2), H / 2),
             (xl, lo - xr), (xl, 0))


@low('x', 8, 2)
def x(g):
    """The capital's drawing in the x-height (until 1.017 the x crossed
    plain at every weight, and the X stepped)."""
    f = Frame(g, 8, 'lower')
    x_strokes(g, f.X(1), f.X(7), f.W, f.p.xh)


Y_FLAT = 1.0     # modules: the flat the y's arm lands on before the stem


@low('y', 8, 2)
def y(g):
    """The y: a bowl open at the top whose left corner is cut all the way
    across, and the g's hook. The arm comes down the left stem, turns at 45
    degrees and lands flat on the baseline, a module short of the stem: it
    meets the stem as the p's bowl meets its own and the g's its own, a
    horizontal on the baseline, and the stem runs on down into the hook as
    one line.

    Until 1.017 the arm ran straight into the stem, its lower edge an edge
    break above the baseline: a diagonal entering a vertical takes a stem
    and a fifth of the stem's height to do it (252 units at Black), with
    the hook's corner straight under it, and from Bold the three made one
    lump at the foot of the letter."""
    f = Frame(g, 8, 'lower')
    p = f.p
    xl, xr = f.X(1), f.X(7)
    leg = max(p.leg, (xr - p.sv / 2) - Y_FLAT * p.m - xl)
    g.stroke((xl, p.xh), B(xl, f.Y(1), leg), (xr, f.Y(1)))
    hook(g, f)
    g.butt += crotch_butt(g, f.Y(1))


@low('z', 8, 1)
def z(g):
    f = Frame(g, 8, 'lower')
    p, W, k_ = f.p, f.W, f.k
    g.stroke(f.P(0, 8), f.P(8, 8))
    g.stroke(f.P(0, 1), f.P(8, 1))
    J = jog(p)
    a_up = W - (p.xh - g.sh - p.c) - k_                     # x - y
    a_lo = a_up - J
    yj = f.Y(4.5)
    step = min(J, g.sh)
    y0, y1 = f.Y(8), f.Y(1)
    xl = f.X(1)
    # Where the diagonal reaches the left edge; in a narrow cell it meets the
    # bottom bar first, and lands on it there (running on inside the bar)
    # rather than below it: the same points either way, so the masters vary.
    ye = xl - a_lo
    g.stroke((y0 + a_up, y0), (yj + a_up, yj, step), (yj + a_lo, yj), (max(xl, y1 + a_lo), max(ye, y1)),
             (xl, y1), start='h')


@glyph('dotlessi', '\u0131', lambda p: p.sv, kind='lower')
def dotlessi(g):
    f = Frame(g, 2, 'lower')
    g.stroke(f.P(1, 0), f.P(1, 9))


@glyph('uni0237', '\u0237', letter_width(6, 1), kind='lower')
def dotlessj(g):
    f = Frame(g, 6, 'lower')
    p = f.p
    g.stroke(f.P(5, 9), B(*f.P(5, -2)), B(*f.P(1, -2)), (f.X(1), -p.desc + beak_depth(p)))
