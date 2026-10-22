"""Figures 0-9 and the colon, after the Dymaxion zone numerals.

Proportions follow the 9x12 masters: ``u`` and ``v`` are one module of the
figure body horizontally and vertically, so positions read like the pixel
drawings (x = 8u is column 8). Stroke positions follow the weights, so
outer edges stay on the body box at every weight.
"""
from __future__ import annotations

import math

from ..draw import B, glyph
from ..params import SQRT2, inner_leg, outer_leg

STEEP = (1 / math.sqrt(5), 2 / math.sqrt(5))  # the 2:1 slope, as a unit vector


def frame(g):
    p = g.p
    W, H = p.fig_w, p.cap
    u, v = W / 9, H / 12
    xl, xr = p.sv / 2, W - p.sv / 2
    yb, yt = p.sh / 2, H - p.sh / 2
    # Strokes may run past the body (a diagonal into a bar's end); the body
    # box trims them, so outer edges stay exactly on it.
    g.clip = (0, -g.ob, W, H + g.ot)
    return p, W, H, u, v, xl, xr, yb, yt


def beak_depth(p):
    """How far a beak terminal reaches below the bowl's top (or above its
    bottom). Its outer flank under the corner chamfer is one edge break long,
    so the corner rule turns it into a point; at weights where that would leave
    the inner flank shorter than an edge break, the inner flank sets the depth.
    At the heritage weight both flanks are exactly one edge break."""
    return max(outer_leg(p) + p.c, p.sh + inner_leg(p) + p.c)


def beak_top(g):
    return g.p.cap + g.ot - beak_depth(g.p)


def beak_bottom(g):
    return -g.ob + beak_depth(g.p)


def steep_thickness(p):
    from ..geom import Thickness
    return Thickness(p.sv, p.sh, p.sd)(STEEP)


@glyph('zero', '0', 'fig_w')
def zero(g):
    p, W, H, u, v, xl, xr, yb, yt = frame(g)
    g.stroke(B(xl, yb - g.ob), B(xr, yb - g.ob), B(xr, yt + g.ot), B(xl, yt + g.ot), closed=True)


@glyph('one', '1', 'fig_w')
def one(g):
    p, W, H, u, v, xl, xr, yb, yt = frame(g)
    x1 = W / 2 + u / 2
    top = H + g.ot
    g.stroke((x1 - 3 * u, yb), (x1 + 3 * u, yb))            # foot
    g.stroke((x1, yb), (x1, top))                           # stem
    # Flag: a 45-degree stroke whose upper edge leaves the stem's top-left corner.
    k = p.sd / SQRT2                                         # half the stroke, across x or y
    # upper edge: y = x + (top - x1 + sv/2); the centreline lies k lower
    c0 = top - x1 + p.sv / 2 - k
    y_end = H - 4 * v
    g.stroke((x1, x1 + c0), (y_end - c0, y_end), start='v', end='h')


@glyph('two', '2', 'fig_w')
def two(g):
    p, W, H, u, v, xl, xr, yb, yt = frame(g)
    top = yt + g.ot
    g.stroke((0, yb), (W, yb))                              # base
    # Spine: 45 degrees; its upper-left edge lands on the base's top at x = land.
    land = u
    k = p.sd / SQRT2
    # upper-left edge: y = x + sh - land; the centreline lies k lower
    c0 = p.sh - land - k
    y_turn = xr + c0
    g.stroke((xl, beak_top(g)), B(xl, top), B(xr, top), (xr, y_turn), (yb - c0, yb), end='h')


@glyph('three', '3', 'fig_w')
def three(g):
    p, W, H, u, v, xl, xr, yb, yt = frame(g)
    ym = 6 * v
    bot = yb - g.ob
    g.stroke((u, yt), B(xr, yt), B(xr, ym), (3 * u, ym))
    g.stroke((3 * u, ym), B(xr, ym), B(xr, bot), B(xl, bot), (xl, beak_bottom(g)))


@glyph('four', '4', 'fig_w')
def four(g):
    p, W, H, u, v, xl, xr, yb, yt = frame(g)
    yc = 5 * v
    xs = 7 * u
    top = H + g.ot
    g.stroke((0, yc), (W, yc))                              # crossbar
    g.stroke((xs, 0), (xs, 10 * v))                         # stem
    # Diagonal at 2:1; its upper-left edge leaves the crossbar's top-left corner.
    t = steep_thickness(p)
    nx, ny = STEEP[1], -STEEP[0]                            # unit normal, lower right
    ox, oy = 0.0, yc + p.sh / 2
    cx, cy = ox + nx * t / 2, oy + ny * t / 2               # a centreline point
    at = lambda y: (cx + (y - cy) / 2, y)
    g.stroke(at(yc), at(top), start='h', end='h')


@glyph('five', '5', 'fig_w')
def five(g):
    p, W, H, u, v, xl, xr, yb, yt = frame(g)
    yj = 7 * v
    bot = yb - g.ob
    g.stroke((8 * u, yt), (xl, yt), (xl, yj), B(xr, yj), B(xr, bot), B(xl, bot), (xl, beak_bottom(g)))


def _six(g, flip):
    p, W, H, u, v, xl, xr, yb, yt = frame(g)
    ot, ob = (g.ob, g.ot) if flip else (g.ot, g.ob)
    yj = 7 * v
    top, bot = yt + ot, yb - ob
    T = (lambda x, y: (W - x, H - y)) if flip else (lambda x, y: (x, y))

    def b(x, y):
        return B(*T(x, y))

    g.stroke(T(8 * u, top), b(xl, top), T(xl, yj))
    g.stroke(T(xl, yj), b(xr, yj), b(xr, bot), b(xl, bot), closed=True)


@glyph('six', '6', 'fig_w')
def six(g):
    _six(g, False)


@glyph('nine', '9', 'fig_w')
def nine(g):
    _six(g, True)


@glyph('seven', '7', 'fig_w')
def seven(g):
    p, W, H, u, v, xl, xr, yb, yt = frame(g)
    g.stroke((0, yt), (W, yt))                              # bar
    # Leg at 2:1; its right edge leaves the bar's right end.
    t = steep_thickness(p)
    nx, ny = -STEEP[1], STEEP[0]                            # unit normal, upper left
    ox, oy = W, H - p.sh
    cx, cy = ox + nx * t / 2, oy + ny * t / 2
    at = lambda y: (cx + (y - cy) / 2, y)
    g.stroke(at(yt), at(0), start='h', end='h')


@glyph('eight', '8', 'fig_w')
def eight(g):
    p, W, H, u, v, xl, xr, yb, yt = frame(g)
    yw = 6 * v
    top, bot = yt + g.ot, yb - g.ob
    big = p.leg + u
    g.stroke(B(xl, yw, big), B(xr, yw, big), B(xr, top), B(xl, top), closed=True)
    g.stroke(B(xl, bot), B(xr, bot), B(xr, yw), B(xl, yw), closed=True)
