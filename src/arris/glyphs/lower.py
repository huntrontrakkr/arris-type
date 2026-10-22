"""Lowercase a-z, built from their pixel masters (``arris.masters.LOWER``).

Module coordinates: x-height 9, ascender 13, descender -3 (see letterframe).
The same moves as the capitals and figures: beaks on c and j, the 2's notch
in z, a notched shoulder on r (the 1's flag, turned), arches that meet in a
V on m, gables on v and w.
"""
from __future__ import annotations

from ..draw import B, Opening, glyph
from ..params import SQRT2
from .figures import beak_depth, jog
from .letterframe import Frame, letter_width


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
    p, d = f.p, beak_depth(f.p)
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
    f = Frame(g, 7, 'asc')
    g.stroke(f.P(2, 0), B(*f.P(2, 12)), f.P(7, 12))
    g.stroke(f.P(0, 8), f.P(6, 8))


@low('g', 8, 2)
def g_(g):
    f = Frame(g, 8, 'lower')
    g.stroke(f.P(7, 8), B(*f.P(1, 8)), B(*f.P(1, 1)), f.P(7, 1), closed=True)
    g.stroke(f.P(7, 9), B(*f.P(7, -2)), f.P(1, -2))


@low('h', 8, 2)
def h(g):
    f = Frame(g, 8, 'asc')
    g.stroke(f.P(1, 0), f.P(1, 13))
    g.stroke(f.P(1, 8), B(*f.P(7, 8)), f.P(7, 0))


def _dot(g, f, x):
    """The tittle: a square as wide as the stem, centred between x-height and
    ascender, but never closer to the x-height than 0.4 of a stem."""
    p = g.p
    yc = max((p.xh + p.asc) / 2, p.xh + 0.4 * p.sv + p.sv / 2)
    g.stroke((x, yc - p.sv / 2), (x, yc + p.sv / 2))


@low('i', 2, 1, width=lambda p: p.sv)
def i(g):
    f = Frame(g, 2, 'asc', top=g.p.asc + g.p.sv)
    g.stroke(f.P(1, 0), f.P(1, 9))
    _dot(g, f, f.X(1))


@low('j', 6, 1)
def j(g):
    f = Frame(g, 6, 'asc', top=g.p.asc + g.p.sv)
    p = f.p
    g.stroke(f.P(5, 9), B(*f.P(5, -2)), B(*f.P(1, -2)), (f.X(1), -p.desc + beak_depth(p)))
    _dot(g, f, f.X(5))


@low('k', 8, 1)
def k(g):
    f = Frame(g, 8, 'asc')
    p, W, k_ = f.p, f.W, f.k
    xh = p.xh
    g.stroke(f.P(1, 0), f.P(1, 13))
    a_arm = W - xh + p.c - k_                               # arm: x - y
    a_leg = W + p.c - k_                                    # leg: x + y
    xj = f.X(1) + p.sv
    y_hi, y_lo = xj - a_arm, a_leg - xj
    if 2 * xj + p.sv <= a_arm + a_leg + 2 * k_ + 1e-6:
        xm = (a_arm + a_leg) / 2
        mid = [(xm, xm - a_arm)]
        g.stroke((xm, xm - a_arm), (f.X(1), xm - a_arm))
    else:
        mid = [(xj, y_hi), (xj, y_lo)] if y_hi > y_lo + 1e-9 else [(xj, y_hi)]
    g.stroke((xh + a_arm, xh), *mid, (a_leg, 0), start='h', end='h')
    g.clip = (0, -p.desc, W, p.asc)


@low('l', 4, 1)
def l(g):
    f = Frame(g, 4, 'asc')
    g.stroke(f.P(0, 12), f.P(3, 12), f.P(3, 0))


@low('m', 12, 3)
def m(g):
    f = Frame(g, 12, 'lower')
    g.stroke(f.P(1, 0), f.P(1, 9))
    g.stroke(f.P(1, 8), B(*f.P(6, 8)), f.P(6, 0))
    g.stroke(f.P(6, 4), B(*f.P(6, 8)), B(*f.P(11, 8)), f.P(11, 0))


@low('n', 8, 2)
def n(g):
    f = Frame(g, 8, 'lower')
    g.stroke(f.P(1, 0), f.P(1, 9))
    g.stroke(f.P(1, 8), B(*f.P(7, 8)), f.P(7, 0))


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
    g.stroke(f.P(1, 0), f.P(1, 9))
    # The shoulder: a 45-degree stroke from the stem to the arm, leaving a
    # notch under the arm (the 1's flag, turned).
    x0, y0 = f.P(3, 6.5)
    y8, y6 = f.Y(8), f.Y(6)
    g.stroke((x0 - (y0 - y6), y6), (x0 + (y8 - y0), y8), f.P(8, 8), start='h')


@low('s', 8, 2)
def s(g):
    g.stack(3, g.p.xh, ratio=0.75)
    f = Frame(g, 8, 'lower')
    g.stroke(f.P(8, 8), B(*f.P(1, 8)), B(*f.P(1, 5)), B(*f.P(7, 5), g.p.m / 2), B(*f.P(7, 1)), f.P(0, 1))


@low('t', 7, 1)
def t(g):
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
    yt = ya + (W / 2 - xl)
    g.stroke((xl, p.xh), (xl, yt), (W / 2, ya), (xr, yt), (xr, p.xh))


@low('w', 14, 3)
def w(g):
    f = Frame(g, 14, 'lower')
    p, W = f.p, f.W
    xl, xm, xr = f.X(1), W / 2, f.X(13)
    q1, q3 = (xl + xm) / 2, (xm + xr) / 2
    ya = _vee(f)
    yt = ya + (q1 - xl)
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
    g.stroke((y0 + a_up, y0), (yj + a_up, yj, step), (yj + a_lo, yj), (y1 + a_lo, y1), start='h', end='h')


@glyph('dotlessi', '\u0131', lambda p: p.sv, kind='lower')
def dotlessi(g):
    f = Frame(g, 2, 'lower')
    g.stroke(f.P(1, 0), f.P(1, 9))


@glyph('uni0237', '\u0237', letter_width(6, 1), kind='lower')
def dotlessj(g):
    f = Frame(g, 6, 'lower')
    p = f.p
    g.stroke(f.P(5, 9), B(*f.P(5, -2)), B(*f.P(1, -2)), (f.X(1), -p.desc + beak_depth(p)))
