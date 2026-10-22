"""Capitals A-Z.

The language, from the figures and the watch's 5x7 Draft capitals:

* Bowls are chamfered boxes (octagons); bowls that open end in beaks.
* Stem-side corners are square, with the edge break (B D E F P R).
* Points are gables: verticals that bend at 45 degrees to meet (A V W X Y M).
* Diagonals that cross the full height run at 2:1 (N Z, like the 4 and 7).
* A diagonal leaving a stem or bar leaves from its corner (the elbow).

Widths are given in modules at the heritage (SemiBold) weight and grow by the
stem's change, so counters keep most of their size across weights.
"""
from __future__ import annotations

import math

from ..draw import B, glyph
from ..geom import Thickness
from ..params import SQRT2, inner_leg, outer_leg
from .figures import STEEP, beak_depth

HERITAGE_STEM = 120.0


def cap_width(mods):
    return lambda p: mods * p.m + (p.sv - HERITAGE_STEM)


def frame(g, W):
    p = g.p
    H = p.cap
    xl, xr = p.sv / 2, W - p.sv / 2
    yb, yt = p.sh / 2, H - p.sh / 2
    g.clip = (0, -p.desc, W, H + g.ot)
    return p, H, xl, xr, yb, yt


def mid(p, k=0.5):
    """Centre of a crossbar at fraction k of the cap height."""
    return k * p.cap


def caps(name, char, mods, sides):
    return glyph(name, char, cap_width(mods) if not callable(mods) else mods, kind=('cap',) + sides)


def steep_t(p):
    return p.ss


# --- Bowls -----------------------------------------------------------------

@caps('O', 'O', 9.5, ('round', 'round'))
def O(g):
    p, H, xl, xr, yb, yt = frame(g, g.W)
    g.stroke(B(xl, yb - g.ob), B(xr, yb - g.ob), B(xr, yt + g.ot), B(xl, yt + g.ot), closed=True)


@caps('Q', 'Q', 9.5, ('round', 'round'))
def Q(g):
    O(g)
    p, H, xl, xr, yb, yt = frame(g, g.W)
    # Tail: 45 degrees down-right through the middle of the bowl's lower-right
    # chamfer, square to it, from inside the counter to below the baseline.
    W, lo = g.W, outer_leg(p)
    cx, cy = W - lo / 2, lo / 2 - g.ob
    g.stroke((cx - 2.2 * p.m, cy + 2.2 * p.m), (cx + cy + 1.3 * p.m, -1.3 * p.m), end='h')
    g.clip = (0, -p.desc, W + 2 * p.m, H + g.ot)


@caps('C', 'C', 8.5, ('round', 'open'))
def C(g):
    p, H, xl, xr, yb, yt = frame(g, g.W)
    d = beak_depth(p)
    g.stroke((xr, H + g.ot - d), B(xr, yt + g.ot), B(xl, yt + g.ot), B(xl, yb - g.ob), B(xr, yb - g.ob), (xr, d - g.ob))


@caps('G', 'G', 9, ('round', 'stem'))
def G(g):
    p, H, xl, xr, yb, yt = frame(g, g.W)
    d = beak_depth(p)
    yg = mid(p, 0.46)
    g.stroke((xr, H + g.ot - d), B(xr, yt + g.ot), B(xl, yt + g.ot), B(xl, yb - g.ob), B(xr, yb - g.ob), (xr, yg),
             (g.W / 2, yg))


@caps('D', 'D', 9, ('stem', 'round'))
def D(g):
    p, H, xl, xr, yb, yt = frame(g, g.W)
    big = p.leg + 0.5 * p.m
    g.stroke((xl, yb), B(xr, yb - g.ob, big), B(xr, yt + g.ot, big), (xl, yt), closed=True)


@caps('U', 'U', 9, ('stem', 'stem'))
def U(g):
    p, H, xl, xr, yb, yt = frame(g, g.W)
    g.stroke((xl, H), B(xl, yb - g.ob), B(xr, yb - g.ob), (xr, H))


@caps('J', 'J', 7.5, ('open', 'stem'))
def J(g):
    p, H, xl, xr, yb, yt = frame(g, g.W)
    g.stroke((xr, H), B(xr, yb - g.ob), B(xl, yb - g.ob), (xl, beak_depth(p) - g.ob))


@caps('S', 'S', 8.5, ('round', 'round'))
def S(g):
    p, H, xl, xr, yb, yt = frame(g, g.W)
    d = beak_depth(p)
    ym = mid(p, 0.53)
    xlu = xl + 0.5 * p.m
    g.stroke((xr, H + g.ot - d), B(xr, yt + g.ot), B(xlu, yt + g.ot), B(xlu, ym), B(xr, ym), B(xr, yb - g.ob),
             B(xl, yb - g.ob), (xl, d - g.ob))


# --- Stem and bowl ---------------------------------------------------------

@caps('B', 'B', 8.5, ('stem', 'round'))
def B_(g):
    p, H, xl, xr, yb, yt = frame(g, g.W)
    ym = mid(p, 0.53)
    xru = xr - 0.5 * p.m
    g.stroke((xl, yt), B(xru, yt + g.ot), B(xru, ym), (xl, ym), closed=True)
    g.stroke((xl, ym), B(xr, ym), B(xr, yb - g.ob), (xl, yb), closed=True)


@caps('P', 'P', 8.5, ('stem', 'round'))
def P(g):
    p, H, xl, xr, yb, yt = frame(g, g.W)
    ym = mid(p, 0.45)
    g.stroke((xl, 0), (xl, H))
    g.stroke((xl, yt), B(xr, yt + g.ot), B(xr, ym), (xl, ym))


@caps('R', 'R', 8.5, ('stem', 'diag'))
def R(g):
    p, H, xl, xr, yb, yt = frame(g, g.W)
    ym = mid(p, 0.45)
    g.stroke((xl, 0), (xl, H))
    g.stroke((xl, yt), B(xr, yt + g.ot), B(xr, ym), (xl, ym))
    # Leg at 45 degrees; its lower-right edge lands on the baseline at the body's right.
    k = p.sd / SQRT2
    # lower-right edge: y = -(x - W); centreline is k up-left: y = -(x - W) + k
    c0 = g.W + k
    g.stroke((c0 - ym, ym), (c0, 0), start='h', end='h')


# --- Straight --------------------------------------------------------------

@caps('E', 'E', 7.5, ('stem', 'arm'))
def E(g):
    p, H, xl, xr, yb, yt = frame(g, g.W)
    g.stroke((g.W, yt), (xl, yt), (xl, yb), (g.W, yb))
    g.stroke((xl, mid(p, 0.52)), (g.W - 0.75 * p.m, mid(p, 0.52)))


@caps('F', 'F', 7.5, ('stem', 'arm'))
def F(g):
    p, H, xl, xr, yb, yt = frame(g, g.W)
    g.stroke((g.W, yt), (xl, yt), (xl, 0))
    g.stroke((xl, mid(p, 0.5)), (g.W - 0.75 * p.m, mid(p, 0.5)))


@caps('H', 'H', 9, ('stem', 'stem'))
def H(g):
    p, H_, xl, xr, yb, yt = frame(g, g.W)
    g.stroke((xl, 0), (xl, H_))
    g.stroke((xr, 0), (xr, H_))
    g.stroke((xl, mid(p, 0.52)), (xr, mid(p, 0.52)))


@caps('I', 'I', lambda p: p.sv, ('stem', 'stem'))
def I(g):
    p, H, xl, xr, yb, yt = frame(g, g.W)
    g.stroke((xl, 0), (xl, H))


@caps('L', 'L', 7, ('stem', 'open'))
def L(g):
    p, H, xl, xr, yb, yt = frame(g, g.W)
    g.stroke((xl, H), (xl, yb), (g.W, yb))


@caps('T', 'T', 8.5, ('arm', 'arm'))
def T(g):
    p, H, xl, xr, yb, yt = frame(g, g.W)
    g.stroke((0, yt), (g.W, yt))
    g.stroke((g.W / 2, yt), (g.W / 2, 0))


# --- Gables ----------------------------------------------------------------

def apex_centre(p, top):
    """Centreline height of a 45-degree apex whose edge-break chord sits at ``top``."""
    return top + p.c / SQRT2 - p.sd / SQRT2


@caps('A', 'A', 9, ('diag', 'diag'))
def A(g):
    p, H, xl, xr, yb, yt = frame(g, g.W)
    ac = apex_centre(p, H + g.ot)
    xm = g.W / 2
    yg = ac - (xm - xl)
    g.stroke((xl, 0), (xl, yg), (xm, ac), (xr, yg), (xr, 0))
    yc = mid(p, 0.38)
    g.stroke((xl, yc), (xr, yc))


@caps('V', 'V', 9, ('diag', 'diag'))
def V(g):
    p, H, xl, xr, yb, yt = frame(g, g.W)
    ac = H - apex_centre(p, H + g.ob)
    xm = g.W / 2
    yg = ac + (xm - xl)
    g.stroke((xl, H), (xl, yg), (xm, ac), (xr, yg), (xr, H))


@caps('Y', 'Y', 9, ('diag', 'diag'))
def Y(g):
    p, H, xl, xr, yb, yt = frame(g, g.W)
    xm = g.W / 2
    yj = mid(p, 0.42)
    yg = yj + (xm - xl)
    g.stroke((xl, H), (xl, yg), (xm, yj), (xr, yg), (xr, H))
    g.stroke((xm, yj), (xm, 0))


@caps('W', 'W', 13, ('diag', 'diag'))
def W(g):
    p, H, xl, xr, yb, yt = frame(g, g.W)
    xm = g.W / 2
    ac = H - apex_centre(p, H + g.ob)
    q1, q3 = (xl + xm) / 2, (xm + xr) / 2
    yg = ac + (q1 - xl)
    g.stroke((xl, H), (xl, yg), (q1, ac), (xm, yg), (q3, ac), (xr, yg), (xr, H))
    g.stroke((xm, yg), (xm, mid(p, 0.62)))


@caps('M', 'M', 11, ('stem', 'stem'))
def M(g):
    p, H, xl, xr, yb, yt = frame(g, g.W)
    g.stroke((xl, 0), (xl, H))
    g.stroke((xr, 0), (xr, H))
    # The V's upper edges leave the stems' inner top corners at 45 degrees:
    # y = H - (x - (xl + sv/2)), with the centreline k = sd/sqrt2 lower.
    k = p.sd / SQRT2
    xm = g.W / 2
    ys = H + p.sv / 2 - k              # centreline height at the stem centres
    g.stroke((xl, ys), (xm, ys - (xm - xl)), (xr, ys))


@caps('X', 'X', 9, ('diag', 'diag'))
def X(g):
    p, H, xl, xr, yb, yt = frame(g, g.W)
    span = xr - xl
    yu, yl = (H + span) / 2, (H - span) / 2
    g.stroke((xl, H), (xl, yu), (xr, yl), (xr, 0))
    g.stroke((xr, H), (xr, yu), (xl, yl), (xl, 0))


@caps('K', 'K', 8.5, ('stem', 'diag'))
def K(g):
    p, H, xl, xr, yb, yt = frame(g, g.W)
    W = g.W
    k = p.sd / SQRT2
    g.stroke((xl, 0), (xl, H))
    # Arm: its lower-right edge y = x + H - W meets the cap height at the
    # body's right; the centreline lies k above it.
    ca = H - W + k
    g.stroke((xl, xl + ca), (H - ca, H), end='h')
    # Leg: its upper-right edge y = W - x lands on the baseline at the right.
    cl = W - k
    g.stroke((xl, cl - xl), (cl, 0), end='h')


# --- 2:1 diagonals ---------------------------------------------------------

def _steep_hw(p):
    """Horizontal width of a 2:1 stroke."""
    return steep_t(p) / STEEP[1]


def n_width(p):
    return 2 * p.sv + p.cap / 2 - _steep_hw(p)


@caps('N', 'N', n_width, ('stem', 'stem'))
def N(g):
    p, H, xl, xr, yb, yt = frame(g, g.W)
    g.stroke((xl, 0), (xl, H))
    g.stroke((xr, 0), (xr, H))
    # Upper-right edge leaves the left stem's top-right corner at 2:1.
    hw = _steep_hw(p)
    x_top = xl + p.sv / 2 - hw / 2           # centreline x at y = H
    g.stroke((x_top, H), (x_top + H / 2, 0), start='h', end='h')


def z_width(p):
    return (p.cap - 2 * p.sh) / 2 + _steep_hw(p)


@caps('Z', 'Z', z_width, ('arm', 'arm'))
def Z(g):
    p, H, xl, xr, yb, yt = frame(g, g.W)
    W = g.W
    g.stroke((0, yt), (W, yt))
    g.stroke((0, yb), (W, yb))
    hw = _steep_hw(p)
    # right edge passes (W, H - sh); centreline hw/2 to its left
    x_at = lambda y: W - hw / 2 - (H - p.sh - y) / 2
    g.stroke((x_at(yt), yt), (x_at(yb), yb), start='h', end='h')
