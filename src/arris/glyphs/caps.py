"""Capitals A-Z, built from their pixel masters (``arris.masters.CAPS``).

Coordinates in ``f.P(x, y)`` / ``f.X`` / ``f.Y`` are the master's modules;
see ``letterframe``. The moves are the figures':

* bowl corners and the 3's larger waist corner (B, D),
* beaks where an open bowl ends (C, G, J, S),
* diagonals anchored on a corner one edge break in (K's arm and leg, R's
  leg, M's V, Z's upper stroke), as the 4's diagonal is,
* the 2's notch: a 45-degree stroke stepping a jog on a short bar (Z),
* gables whose points are cut flat by the body (A, V, W),
* the 7's straight 2:1 stroke (N).
"""
from __future__ import annotations

import math

from ..draw import B, Opening, _thickness, glyph
from .figures import beak_depth, jog
from .letterframe import STEEP, Frame, k_arms, letter_width


def cap(char, wm, stems, width=None, openings=()):
    return glyph(char, char, width or letter_width(wm, stems), kind='cap', openings=openings)


def big(p):
    """The larger bowl corner: one module more than the standard leg."""
    return p.leg + p.m


@cap('A', 10, 2)
def A(g):
    f = Frame(g, 10)
    p, W, H, k = f.p, f.W, f.p.cap, f.k
    xl, xr = f.X(1), f.X(9)
    # The gable's outer edges meet an edge break above the cap; the body cuts
    # that point flat, two edge breaks wide.
    ya = H + p.c - k
    yt = ya - (W / 2 - xl)
    g.stroke((xl, 0), (xl, yt), (W / 2, ya), (xr, yt), (xr, 0))
    g.stroke(f.P(1, 4), f.P(9, 4))


@cap('B', 9, 2)
def B_(g):
    f = Frame(g, 9)
    p = f.p
    g.stroke(f.P(1, 0), f.P(1, 12))
    # the upper bowl a module narrower than the lower: the classic B, and
    # what tells it from an 8
    g.stroke(f.P(1, 11), B(*f.P(7, 11)), B(*f.P(7, 6), big(p)), f.P(1, 6), closed=True)
    g.stroke(f.P(1, 6), B(*f.P(8, 6)), B(*f.P(8, 1)), f.P(1, 1), closed=True)


@cap('C', 9, 2)
def C(g):
    c_shape(g)


def c_shape(g, foot_leg=None):
    """The C: a bowl open on the right, a beak over and under the opening.
    ``foot_leg``: the leg of the foot's corners (the default: the parameter
    leg); Ҫ's drop hangs between them (cyrillic_ext.drop_leg)."""
    f = Frame(g, 9)
    p, H, d = f.p, f.p.cap, beak_depth(f.p)
    g.stroke((f.X(8), H - d), B(*f.P(8, 11)), B(*f.P(1, 11)), B(*f.P(1, 1), foot_leg), B(*f.P(8, 1), foot_leg),
             (f.X(8), d))


@cap('D', 9, 2)
def D(g):
    f = Frame(g, 9)
    p = f.p
    g.stroke(f.P(1, 1), B(*f.P(8, 1), big(p)), B(*f.P(8, 11), big(p)), f.P(1, 11), closed=True)


@cap('E', 8, 1)
def E(g):
    f = Frame(g, 8)
    g.stroke(f.P(8, 11), f.P(1, 11), f.P(1, 1), f.P(8, 1))
    g.stroke(f.P(1, 6), f.P(7, 6))


@cap('F', 8, 1)
def F(g):
    f = Frame(g, 8)
    g.stroke(f.P(8, 11), f.P(1, 11), f.P(1, 0))
    g.stroke(f.P(1, 6), f.P(7, 6))


@cap('G', 9, 2)
def G(g):
    f = Frame(g, 9)
    p, H, d = f.p, f.p.cap, beak_depth(f.p)
    # the bar below the middle and deep into the bowl, clear of the S and B
    g.stroke((f.X(8), H - d), B(*f.P(8, 11)), B(*f.P(1, 11)), B(*f.P(1, 1)), B(*f.P(8, 1)), f.P(8, 5), f.P(4, 5))


@cap('H', 9, 2)
def H(g):
    f = Frame(g, 9)
    g.stroke(f.P(1, 0), f.P(1, 12))
    g.stroke(f.P(8, 0), f.P(8, 12))
    g.stroke(f.P(1, 6), f.P(8, 6))


@cap('I', 2, 1, width=lambda p: p.sv)
def I(g):
    if g.p.mono:                                            # slabs, as the 1's foot, top and bottom
        f = Frame(g, 9)
        u, x = g.W / 9, g.W / 2
        g.stroke((x, 0), (x, g.p.cap))
        for y in (f.Y(11), f.Y(1)):
            g.stroke((x - 3 * u, y), (x + 3 * u, y))
        return
    f = Frame(g, 2)
    g.stroke(f.P(1, 0), f.P(1, 12))


@cap('J', 9, 1)
def J(g):
    f = Frame(g, 9)
    p = f.p
    g.stroke(f.P(3, 11), f.P(9, 11))                        # the 1's foot, on top
    g.stroke(f.P(6, 11), B(*f.P(6, 1)), B(*f.P(1, 1)), (f.X(1), beak_depth(p)))


@cap('K', 9, 1)
def K(g):
    f = Frame(g, 9)
    g.stroke(f.P(1, 0), f.P(1, 12))
    for pts, a, b in k_arms(g, f.X(1), f.W, f.p.cap):
        g.stroke(*pts, start=a, end=b)


@cap('L', 8, 1)
def L(g):
    f = Frame(g, 8)
    g.stroke(f.P(1, 12), f.P(1, 1), f.P(8, 1))


@cap('M', 12, 2)
def M(g):
    f = Frame(g, 12)
    p, W, H, k = f.p, f.W, f.p.cap, f.k
    xl, xr = f.X(1), f.X(11)
    g.stroke((xl, 0), (xl, H))
    g.stroke((xr, 0), (xr, H))
    # The V's outer edges leave the stems' inner edges an edge break below
    # the cap: x + y = (xl + sv/2) + (H - c), centreline k inside.
    cl = xl + p.sv / 2 + H - p.c - k
    cr = (xr - p.sv / 2) - (H - p.c) + k                    # right arm: x - y = cr
    xm = W / 2
    g.stroke((xl, cl - xl), (xm, cl - xm), (xr, xr - cr))


N_NECK = 1.0      # strokes: how far below the cap (above the baseline) the diagonal meets each stem


def _n_neck(p, sh):
    """Depth of N's joins: the diagonal's inner edge meets each stem at
    least a full stroke from the cap and the baseline, so the ink joining
    stem and diagonal is as thick as the strokes it joins (the pixel
    master's half bar left a sliver, thinner still toward Black)."""
    return N_NECK * max(sh, p.sd)


def n_width(p):
    w = p.ss / STEEP[1]                                     # across-width of a 2:1 stroke
    return 2 * p.sv + w + (p.cap - 2 * _n_neck(p, p.sh)) / 2


def n_diagonal(g, xa, xb, H):
    """The centreline of N's diagonal, as a function of height, between
    stems whose inner edges stand at xa and xb (as drawn: grade keeps a
    stem's outer edge on the body's edge, so a thinner stem's inner edge
    moves outward). At 2:1, centred between the two inner edges, so its two
    joins are alike at every weight and grade, upright and italic (the
    diagonal's horizontal width is the drawn one, which the italic's
    strokes, set for the shear, make thinner); at the drawing's own grade
    each join lies a neck (_n_neck) from the cap and the baseline. In the
    monospaced cell it runs from join to join, whatever its slope."""
    p = g.p
    th = _thickness(p, g.sh)((1.0, -2.0))
    w = th * math.sqrt(5) / 2                                # horizontal width of the drawn 2:1 stroke
    if p.mono:
        d = _n_neck(p.ungraded(), p.ungraded().sh * g.sh / p.sh)
        x0, x1 = xa + w / 2, xb - w / 2
        k = (x1 - x0) / (H - 2 * d)
        return lambda y: (x0 + (H - d - y) * k, y)
    mid = (xa + xb) / 2
    return lambda y: (mid + (H / 2 - y) / 2, y)


@cap('N', 10, 2, width=n_width)
def N(g):
    f = Frame(g, 10)
    p, W, H = f.p, f.W, f.p.cap
    xl, xr = f.X(1), f.X(9)
    g.stroke((xl, 0), (xl, H))
    g.stroke((xr, 0), (xr, H))
    at = n_diagonal(g, xl + p.sv / 2, xr - p.sv / 2, H)
    g.stroke(at(H + p.sv), at(-p.sv), start='h', end='h')


@cap('O', 10, 2)
def O(g):
    f = Frame(g, 10)
    g.stroke(B(*f.P(1, 1)), B(*f.P(9, 1)), B(*f.P(9, 11)), B(*f.P(1, 11)), closed=True)


@cap('P', 9, 2)
def P(g):
    f = Frame(g, 9)
    g.stroke(f.P(1, 0), f.P(1, 12))
    g.stroke(f.P(1, 11), B(*f.P(8, 11)), B(*f.P(8, 6)), f.P(1, 6))


@cap('Q', 10, 2, openings=[Opening(lambda g: g.counter_size(), 'tail', lambda p: p.cap * 3.5 / 12, max_ratio=0.85)])
def Q(g):
    f = Frame(g, 10)
    p = f.p
    # The bowl's lower right corner is square, and the tail runs into it;
    # heavy weights shorten the tail so the counter stays open.
    g.stroke(B(*f.P(1, 1)), f.P(9, 1), B(*f.P(9, 11)), B(*f.P(1, 11)), closed=True)
    ct = (f.X(9) - p.sv / 2) + (f.Y(1) + g.sh / 2) - p.c   # tail: x + y = ct
    y0 = g.free('tail', f.Y(5))
    g.stroke((ct - y0, y0), (ct - f.Y(1), f.Y(1)), start='h')


@cap('R', 9, 2)
def R(g):
    f = Frame(g, 9)
    p, W, k = f.p, f.W, f.k
    g.stroke(f.P(1, 0), f.P(1, 12))
    g.stroke(f.P(1, 11), B(*f.P(8, 11)), B(*f.P(8, 6)), f.P(1, 6))
    a = W + p.c - k                                         # leg: x + y = a
    y0 = f.Y(6)
    g.stroke((a - y0, y0), (a, 0), start='h', end='h')


@cap('S', 9, 2)
def S(g):
    f = Frame(g, 9)
    p, H, d = f.p, f.p.cap, beak_depth(f.p)
    g.stroke((f.X(8), H - d), B(*f.P(8, 11)), B(*f.P(1, 11)), B(*f.P(1, 6)), B(*f.P(8, 6)), B(*f.P(8, 1)),
             B(*f.P(1, 1)), (f.X(1), d))


@cap('T', 10, 1)
def T(g):
    f = Frame(g, 10)
    g.stroke(f.P(0, 11), f.P(10, 11))
    g.stroke(f.P(5, 11), f.P(5, 0))


@cap('U', 9, 2)
def U(g):
    f = Frame(g, 9)
    g.stroke(f.P(1, 12), B(*f.P(1, 1)), B(*f.P(8, 1)), f.P(8, 12))


def _vee(f, x0, x1):
    """Centreline height of a V's point between stems at x0 and x1 (its outer
    point an edge break below the baseline, cut flat by the body), and where
    its arms leave the stems."""
    p = f.p
    ya = -p.c + f.k
    return ya, ya + (x1 - x0) / 2


@cap('V', 10, 2)
def V(g):
    f = Frame(g, 10)
    H, W = f.p.cap, f.W
    xl, xr = f.X(1), f.X(9)
    ya, yt = _vee(f, xl, xr)
    g.stroke((xl, H), (xl, yt), (W / 2, ya), (xr, yt), (xr, H))


@cap('W', 14, 3)
def W_(g):
    f = Frame(g, 14)
    H, W = f.p.cap, f.W
    xl, xm, xr = f.X(1), W / 2, f.X(13)
    q1, q3 = (xl + xm) / 2, (xm + xr) / 2
    ya, yt = _vee(f, xl, xm)
    g.stroke((xl, H), (xl, yt), (q1, ya), (xm, yt), (q3, ya), (xr, yt), (xr, H))
    g.stroke((xm, yt), (xm, f.Y(7)))


@cap('X', 10, 2)
def X(g):
    f = Frame(g, 10)
    p, H, W = f.p, f.p.cap, f.W
    xl, xr = f.X(1), f.X(9)
    # Each stroke steps sideways by a jog where they cross: the 2's notch,
    # twice. Upper halves pass the centre a half jog early, lower halves a
    # half jog late.
    J = jog(p)
    step = min(J, g.sh)
    up, lo = (W + H - J) / 2, (W + H + J) / 2                # x + y on the falling stroke
    g.stroke((xl, H), (xl, up - xl), (up - H / 2, H / 2, step), (lo - H / 2, H / 2), (xr, lo - xr), (xr, 0))
    # the rising stroke, mirrored: x -> W - x
    g.stroke((xr, H), (xr, up - xl), (W - (up - H / 2), H / 2, step), (W - (lo - H / 2), H / 2),
             (xl, lo - xr), (xl, 0))


@cap('Y', 10, 2)
def Y(g):
    f = Frame(g, 10)
    H, W = f.p.cap, f.W
    xl, xr = f.X(1), f.X(9)
    yj = f.Y(5.5)
    yg = yj + (W / 2 - xl)
    g.stroke((xl, H), (xl, yg), (W / 2, yj), (xr, yg), (xr, H))
    g.stroke((W / 2, yj), (W / 2, 0))


@cap('Z', 9, 1)
def Z(g):
    f = Frame(g, 9)
    p, W, H, k = f.p, f.W, f.p.cap, f.k
    g.stroke(f.P(0, 11), f.P(9, 11))
    g.stroke(f.P(0, 1), f.P(9, 1))
    # The 2's spine, mirrored into the Z: its upper stroke leaves the top
    # bar's end an edge break below it; a jog left on a short bar; then down.
    J = jog(p)
    a_up = W - (H - g.sh - p.c) - k                         # x - y = a_up
    a_lo = a_up - J
    yj = f.Y(6.5)
    step = min(J, g.sh)
    y0, y1 = f.Y(11), f.Y(1)
    xl = f.X(1)
    g.stroke((y0 + a_up, y0), (yj + a_up, yj, step), (yj + a_lo, yj), (xl, xl - a_lo), (xl, y1), start='h')
