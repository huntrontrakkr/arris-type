"""Lowercase a-z, built from their pixel masters (``arris.masters.LOWER``).

Module coordinates: x-height 9, ascender 13, descender -3 (see letterframe).
The same moves as the capitals and figures: beaks on c and j, the 2's notch
in z, a notched shoulder on r (the 1's flag, turned), arches that meet in a
V on m, gables on v and w.
"""
from __future__ import annotations

from ..draw import B, Opening, glyph
from ..params import SQRT2, outer_leg
from .figures import beak_depth, jog
from .letterframe import Frame, k_arms, letter_width


def low(char, wm, stems, width=None, openings=()):
    return glyph(char, char, width or letter_width(wm, stems), kind='lower', openings=openings)


def _a_gap(g):
    """White between the a's arm and the top of its bowl."""
    return g.defaults_used['arm'] - g.defaults_used['bowl'] - g.sh


@low('a', 8, 2, openings=[Opening(_a_gap, 'bowl', lambda p: p.xh * 0.4, max_ratio=0.4)])
def a(g):
    g.stack(3, g.p.xh, ratio=0.75)
    f = Frame(g, 8, 'lower')
    small = g.p.m / 2                                       # a one-step corner, as drawn
    ya = f.Y(8)
    yb = g.free('bowl', f.Y(5))                             # heavy weights lower the bowl
    g.defaults_used.update(arm=ya, bowl=yb)
    g.stroke((f.X(1), ya), B(f.X(7), ya, small), f.P(7, 0))
    g.stroke((f.X(7), yb), B(f.X(1), yb), B(*f.P(1, 1)), f.P(7, 1), closed=True)


@low('b', 8, 2)
def b(g):
    f = Frame(g, 8, 'asc')
    g.stroke(f.P(1, 0), f.P(1, 13))
    g.stroke(f.P(1, 8), B(*f.P(7, 8)), B(*f.P(7, 1)), f.P(1, 1), closed=True)


@low('c', 8, 2)
def c(g):
    f = Frame(g, 8, 'lower')
    # The shortest beaks (the outer flank alone): an open mouth tells c from o.
    p = f.p
    d = outer_leg(p) + p.c
    g.stroke((f.X(7), p.xh - d), B(*f.P(7, 8)), B(*f.P(1, 8)), B(*f.P(1, 1)), B(*f.P(7, 1)), (f.X(7), d))


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


# --- Italic forms (arris.italic) ---------------------------------------------

@glyph('a.ital', None, letter_width(8, 2), kind='lower')
def a_ital(g):
    """The italic's single-storey a: the d's bowl on a stem that stops at
    the x-height."""
    f = Frame(g, 8, 'lower')
    g.stroke(f.P(7, 0), f.P(7, 9))
    g.stroke(f.P(7, 8), B(*f.P(1, 8)), B(*f.P(1, 1)), f.P(7, 1), closed=True)


@glyph('f.ital', None, letter_width(7, 1), kind='lower')
def f_ital(g):
    """The italic's f: the stem runs on below the baseline and turns back,
    the top's hook turned over."""
    if g.p.mono:
        f = Frame(g, 9, 'asc')
        g.stroke(f.P(8, 12), B(*f.P(4.5, 12)), B(*f.P(4.5, -2)), f.P(1, -2))
        g.stroke(f.P(1, 8), f.P(8, 8))
        return
    f = Frame(g, 7, 'asc')
    g.clip = (-f.W, -g.p.desc, 2 * f.W, g.p.asc)
    g.stroke(f.P(7, 12), B(*f.P(3.5, 12)), B(*f.P(3.5, -2)), f.P(0, -2))
    g.stroke(f.P(0.5, 8), f.P(6.5, 8))


@low('g', 8, 2)
def g_(g):
    f = Frame(g, 8, 'lower')
    g.stroke(f.P(7, 8), B(*f.P(1, 8)), B(*f.P(1, 1)), f.P(7, 1), closed=True)
    g.stroke(f.P(7, 9), B(*f.P(7, -2)), f.P(1, -2))


def shoulder(g, f, xs, x_right, top=8):
    """An arch's shoulder, as the r's: it leaves the stem at 45 degrees two
    modules below the arch, an edge break into the stem, and leaves a notch
    under it (the 1's flag, turned). Returns the arch's points up to its
    right corner, and how the stroke's start is cut.

    The diagonal needs room between the stems. Where there is less (the
    monospaced m, the heaviest weights) it rises less and starts further
    into the stem, down to the plain square join, so the arch keeps its
    counter and the drawing changes continuously with weight."""
    p = g.p
    k = p.sd / 2 ** 0.5
    y_top = f.Y(top)
    full = f.Y(top) - f.Y(top - 2)
    x_full = xs + p.sv / 2 + k - p.c
    room = x_right - p.leg - p.c - x_full                  # the diagonal ends clear of the corner
    rise = min(full, max(room, 0.0))
    if rise < 1e-3 * p.m:
        return [(xs, y_top), B(x_right, y_top)], 'flat'
    x0 = xs + rise / full * (x_full - xs)
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
    yc = max((p.xh + p.asc) / 2, p.xh + 0.4 * p.sv + p.sv / 2)
    g.stroke((x, yc - p.sv / 2), (x, yc + p.sv / 2))


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


@low('r', 8, 1)
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


@low('x', 8, 2)
def x(g):
    f = Frame(g, 8, 'lower')
    p = f.p
    xl, xr = f.X(1), f.X(7)
    half = (xr - xl) / 2
    yu, yl = p.xh / 2 + half, p.xh / 2 - half
    g.stroke((xl, p.xh), (xl, yu), (xr, yl), (xr, 0))
    g.stroke((xr, p.xh), (xr, yu), (xl, yl), (xl, 0))


@low('y', 8, 2)
def y(g):
    f = Frame(g, 8, 'lower')
    p, k_ = f.p, f.k
    xl, xr = f.X(1), f.X(7)
    # The left arm bends at 45 degrees into the right stem, its lower edge
    # meeting the stem one edge break above the baseline.
    a = (xr - p.sv / 2) + p.c - k_                          # x + y = a
    g.stroke((xl, p.xh), (xl, a - xl), (xr, a - xr))
    g.stroke(f.P(7, 9), B(*f.P(7, -2)), f.P(1, -2))


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
    g.stroke((y0 + a_up, y0), (yj + a_up, yj, step), (yj + a_lo, yj), (xl, xl - a_lo), (xl, y1), start='h')


@glyph('dotlessi', '\u0131', lambda p: p.sv, kind='lower')
def dotlessi(g):
    f = Frame(g, 2, 'lower')
    g.stroke(f.P(1, 0), f.P(1, 9))


@glyph('uni0237', '\u0237', letter_width(6, 1), kind='lower')
def dotlessj(g):
    f = Frame(g, 6, 'lower')
    p = f.p
    g.stroke(f.P(5, 9), B(*f.P(5, -2)), B(*f.P(1, -2)), (f.X(1), -p.desc + beak_depth(p)))
