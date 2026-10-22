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

JOG = None  # None: half a stem; a number: that many modules at every weight
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
    return p.ss


def jog(p, fixed=None):
    """The step in the 2's and 4's diagonals: one pixel of the watch's
    two-pixel strokes, i.e. half a stem."""
    return p.sv / 2 if JOG is None else JOG * p.m


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
    # Flag: 45 degrees, its upper edge continuing the stem's cut top-left
    # corner (x - y = x1 - sv/2 + c - top); the centreline lies k inside. It
    # ends square on a horizontal four modules down, and the corner rule
    # fills the crotch under it, which leaves the notch.
    k = p.sd / SQRT2
    a = x1 - p.sv / 2 + p.c - top + k                       # centreline: x - y = a
    yf = H - 4 * v
    g.stroke((x1, x1 - a), (yf + a, yf), start='v', end='h')


@glyph('two', '2', 'fig_w')
def two(g):
    p, W, H, u, v, xl, xr, yb, yt = frame(g)
    top = yt + g.ot
    k = p.sd / SQRT2
    g.stroke((0, yb), (W, yb))                              # base
    # The spine is two 45-degree strokes offset by a jog and overlapping by
    # it: the notch. The lower one's upper edge lands on the base one edge
    # break in from its end (x - y = c - sh); the upper one sits a jog right.
    a_lo = p.c - p.sh + k
    a_up = a_lo + jog(p)
    yj = 5.5 * v
    lo, hi = yj - jog(p) / 2, yj + jog(p) / 2
    g.stroke((xl, beak_top(g)), B(xl, top), B(xr, top), (xr, xr - a_up), (lo + a_up, lo), end='h')
    g.stroke((hi + a_lo, hi), (yb + a_lo, yb), start='h', end='h')


@glyph('three', '3', 'fig_w')
def three(g):
    p, W, H, u, v, xl, xr, yb, yt = frame(g)
    ym = 6 * v
    bot = yb - g.ob
    # The upper bowl's lower corner is a module rounder than the lower bowl's
    # upper one; their outer chamfers meet in a sharp point at the waist.
    g.stroke((u, yt), B(xr, yt), B(xr, ym, p.leg + u), (3 * u, ym))
    g.stroke((3 * u, ym), B(xr, ym), B(xr, bot), B(xl, bot), (xl, beak_bottom(g)))


@glyph('four', '4', 'fig_w')
def four(g):
    p, W, H, u, v, xl, xr, yb, yt = frame(g)
    yc = 5 * v
    xs = 7 * u
    top = H + g.ot
    k = p.sd / SQRT2
    g.stroke((0, yc), (W, yc))                              # crossbar
    g.stroke((xs, 0), (xs, 10 * v))                         # stem
    # The diagonal: two 45-degree strokes, the upper a jog to the left, cut
    # vertically where they overlap: the clip. The lower one's upper edge
    # leaves the crossbar's end one edge break above its top.
    a_lo = k - (yc + p.sh / 2 + p.c)
    a_up = a_lo - jog(p)
    xj = 3 * u
    g.stroke((yc + a_lo, yc), (xj + 2 * k, xj + 2 * k - a_lo), start='h', end='v')
    g.stroke((xj, xj - a_up), (top + a_up, top), start='v', end='h')


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
    # Leg at 2:1, straight (the watch's straightened seven): its right edge
    # leaves the bar's lower right corner; the corner rule trims the foot.
    w = steep_thickness(p) / STEEP[1]                        # across, horizontally
    x_at = lambda y: W - w / 2 - (H - p.sh - y) / 2
    g.stroke((x_at(yt), yt), (x_at(0), 0), start='h', end='h')


@glyph('eight', '8', 'fig_w')
def eight(g):
    p, W, H, u, v, xl, xr, yb, yt = frame(g)
    yw = 6 * v
    top, bot = yt + g.ot, yb - g.ob
    big = p.leg + u
    g.stroke(B(xl, yw, big), B(xr, yw, big), B(xr, top), B(xl, top), closed=True)
    g.stroke(B(xl, bot), B(xr, bot), B(xr, yw), B(xl, yw), closed=True)
