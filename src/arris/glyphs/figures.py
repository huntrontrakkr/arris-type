"""Figures 0-9 and the colon, after the Dymaxion zone numerals.

Proportions follow the 9x12 masters: ``u`` and ``v`` are one module of the
figure body horizontally and vertically, so positions read like the pixel
drawings (x = 8u is column 8). Stroke positions follow the weights, so
outer edges stay on the body box at every weight.
"""
from __future__ import annotations

import math

from ..draw import B, Opening, glyph
from ..params import SQRT2, inner_leg, outer_leg

STEEP = (1 / math.sqrt(5), 2 / math.sqrt(5))  # the 2:1 slope, as a unit vector


def frame(g):
    p = g.p
    # Figures that stack three bars thin their horizontals where an opening
    # needs it (see STACKED); elsewhere sh_k stays 1.
    g.sh_k = g.free('sh_k', 1.0)
    W, H = p.fig_w, p.cap
    u, v = W / 9, H / 12
    xl, xr = p.sv / 2, W - p.sv / 2
    yb, yt = g.sh / 2, H - g.sh / 2
    # Strokes may run past the body (a diagonal into a bar's end); the body
    # box trims them, so outer edges stay exactly on it.
    g.clip = (0, -g.ob, W, H + g.ot)
    return p, W, H, u, v, xl, xr, yb, yt


def beak_depth(p, sh=None):
    """How far a beak terminal reaches below the bowl's top (or above its
    bottom). Its outer flank under the corner chamfer is one edge break long,
    so the corner rule turns it into a point; at weights where that would leave
    the inner flank shorter than an edge break, the inner flank sets the depth.
    At the heritage weight both flanks are exactly one edge break."""
    sh = p.sh if sh is None else sh
    return max(outer_leg(p, sh=sh) + p.c, sh + inner_leg(p, sh) + p.c)


def beak_top(g):
    return g.p.cap + g.ot - beak_depth(g.p, g.sh)


def beak_bottom(g):
    # an opening may shorten the beak, but never past its outer flank
    shortest = outer_leg(g.p, sh=g.sh) + g.p.c
    return -g.ob + max(g.free('beak', beak_depth(g.p, g.sh)), shortest)


def _beak_limit(p):
    """The shortest beak: its outer flank alone, an edge break under the
    chamfer, at the thinnest horizontals a stack allows."""
    return outer_leg(p, sh=STACK_MIN * p.sh) + p.c


# Openings of the figures that stack three bars (3 5 6 8 9). Heavier strokes
# grow into the white between the bars; the horizontals thin, down to
# STACK_MIN of the weight's own, until the tightest opening has half its
# share of the stem in the watch's drawing again. Mouths (where a beak faces
# a bar) shorten the beak, and keep three quarters of their share.
STACK_MIN = 0.7
MOUTH_SHARE = 0.75
STACK_SHARE = 0.5


def _stacked(measure):
    return Opening(measure, 'sh_k', lambda p: STACK_MIN, max_ratio=STACK_SHARE)


def _mouth(measure):
    return Opening(measure, 'beak', _beak_limit, max_ratio=MOUTH_SHARE)


def _arm_gap(g):
    """White under the top bar of a 5 or 6 (over the bottom bar of a 9),
    measured at the middle of the body."""
    H = g.p.cap
    if g.defaults_used.get('flip'):
        return g.white_vertical(g.W / 2, -g.ob + g.sh, up=True)
    return g.white_vertical(g.W / 2, H + g.ot - g.sh)


def _counters(g):
    return g.tightest_counter()


def _upper_bowl(g):
    """The 3's upper bowl is open on the left: the largest circle in the white
    between its top bar and its waist."""
    import shapely
    from shapely.geometry import box
    from ..geom import rings_to_shapely
    p = g.p
    white = box(g.W / 9, p.cap / 2, g.W, p.cap).difference(rings_to_shapely(g.rings()))
    part = max(getattr(white, 'geoms', [white]), key=lambda q: q.area)
    return 2 * shapely.maximum_inscribed_circle(part, tolerance=1.0).length


def _mouth_gap(g):
    """White between a beak's tip (its ink above the bottom bar) and the bar
    it faces."""
    from shapely.geometry import box
    tip = g.part('beak').intersection(box(-1e4, g.sh - g.ob + 1e-3, 1e4, 1e4))
    return tip.distance(g.part('bar')) if not tip.is_empty else 1e4


def steep_thickness(p):
    return p.ss


def jog(p):
    """The step in the 2's and 4's diagonals: one pixel of the watch's
    two-pixel strokes (half a stem), but never less than a module, so the
    step stays visible at light weights."""
    return max(p.sv / 2, p.m)


@glyph('zero', '0', 'fig_w')
def zero(g):
    p, W, H, u, v, xl, xr, yb, yt = frame(g)
    g.stroke(B(xl, yb - g.ob), B(xr, yb - g.ob), B(xr, yt + g.ot), B(xl, yt + g.ot), closed=True)
    if p.mono:                                              # code wants 0 apart from O
        zero_dot(g)


def zero_dot(g):
    """The dot inside a zero: a stem wide (never more than half the counter)
    and three times as tall, clear of the bars by a module. Taller than a
    square dot, it survives blur and tells 0 from O; it never reaches the
    walls, so it does not push the 0 toward 8."""
    p, W, H = g.p, g.W, g.p.cap
    s = min(p.sv, 0.5 * (W - 2 * p.sv))
    h = min(3 * s, H - 2 * g.sh - 2 * max(p.m, 0.5 * p.sv))
    g.stroke((W / 2, H / 2 - h / 2, s), (W / 2, H / 2 + h / 2))


def _notch_white(g):
    """White under the 1's flag, between its foot and the stem."""
    p = g.p
    x1 = g.W / 2 + g.W / 18
    return g.white_left(g.defaults_used['yf'] + 1e-3 * p.m, x1 - p.sv / 2)


@glyph('one', '1', 'fig_w', openings=[Opening(_notch_white, 'yf', lambda p: p.cap / 3, max_ratio=0.5)])
def one(g):
    p, W, H, u, v, xl, xr, yb, yt = frame(g)
    x1 = W / 2 + u / 2
    top = H + g.ot
    g.stroke((x1 - 3 * u, yb), (x1 + 3 * u, yb))            # foot
    g.stroke((x1, yb), (x1, top))                           # stem
    # Flag: 45 degrees, its upper edge continuing the stem's cut top-left
    # corner (x - y = x1 - sv/2 + c - top); the centreline lies k inside. It
    # ends square on a horizontal four modules down (lower when heavy strokes
    # would close the notch), and the corner rule fills the crotch above it.
    fd = p.sd
    k = fd / SQRT2
    a = x1 - p.sv / 2 + p.c - top + k                       # centreline: x - y = a
    yf = g.free('yf', H - 4 * v)
    g.defaults_used['yf'] = yf
    g.stroke((x1, x1 - a, fd), (yf + a, yf), start='v', end='h')


@glyph('two', '2', 'fig_w')
def two(g):
    p, W, H, u, v, xl, xr, yb, yt = frame(g)
    top = yt + g.ot
    k = p.sd / SQRT2
    g.stroke((0, yb), (W, yb))                              # base
    # The spine: a 45-degree stroke that steps left by a jog on a short
    # horizontal (the notch), then lands on the base one edge break in from
    # its end (lower part's upper edge: x - y = c - sh).
    J = jog(p)
    a_lo = p.c - p.sh + k
    a_up = a_lo + J
    y_turn = xr - a_up                                      # where the spine leaves the stem
    yj = yb + (4.5 / 6.5) * (y_turn - yb)                   # the watch's step height, 5.5 of 7.5
    step = min(J, p.sh)
    g.stroke((xl, beak_top(g)), B(xl, top), B(xr, top), (xr, xr - a_up), (yj + a_up, yj, step),
             (yj + a_lo, yj), (yb + a_lo, yb), end='h')


@glyph('three', '3', 'fig_w', openings=[_stacked(_upper_bowl),
                                       Opening(_mouth_gap, 'bar_x', lambda p: p.fig_w / 2, max_ratio=MOUTH_SHARE),
                                       _mouth(_mouth_gap)])
def three(g):
    p, W, H, u, v, xl, xr, yb, yt = frame(g)
    ym = 6 * v
    bot = yb - g.ob
    xm = g.free('bar_x', 3 * u)                             # heavy small sizes pull the bar's end in
    # The upper bowl's lower corner is a module rounder than the lower bowl's
    # upper one; their outer chamfers meet in a sharp point at the waist.
    g.stroke((u, yt), B(xr, yt), B(xr, ym, p.leg + u), (xm, ym), part='bar')
    # parts that continue one another overlap by a quarter stem, so they
    # always join (end-to-end square cuts join only if they coincide exactly)
    g.stroke((xm, ym), B(xr, ym), B(xr, bot), (W / 2, bot))
    g.stroke((W / 2 + p.sv / 4, bot), B(xl, bot), (xl, beak_bottom(g)), part='beak')


def _four_gap(g):
    return g.part('diagonal').distance(g.part('stem'))


def heaviness(p):
    """0 at the watch's weight and below, 1 at Black."""
    return min(max((p.sv - 120.0) / (175.0 - 120.0), 0.0), 1.0)


def _four_bar(p):
    """The 4's crossbar centre: the watch's 5 modules, half a module lower at
    Black, where the counter needs the room."""
    return (5 - 0.5 * heaviness(p)) * p.cap / 12


def _four_jog_limit(p):
    """The deepest clip that still leaves the upper diagonal half a stem long."""
    u = p.fig_w / 9
    a_lo = p.sd / SQRT2 - (_four_bar(p) + p.sh / 2 + p.c)
    return p.cap - p.sv / 2 - (4 * u - a_lo)


@glyph('four', '4', 'fig_w', openings=[Opening(_four_gap, 'jog', _four_jog_limit)])
def four(g):
    p, W, H, u, v, xl, xr, yb, yt = frame(g)
    yc = _four_bar(p)
    xs = 7 * u
    top = H + g.ot
    fd = p.sd
    k = fd / SQRT2
    g.stroke((0, yc), (W, yc))                              # crossbar
    g.stroke((xs, 0), (xs, 10 * v), part='stem')
    # The diagonal steps left by a jog on a short vertical: the clip. Its lower
    # part's upper edge leaves the crossbar's end one edge break above its
    # top. At heavy weights the clip deepens so the 4 stays open at the top.
    J = g.free('jog', jog(p))
    a_lo = k - (yc + p.sh / 2 + p.c)
    a_up = a_lo - J
    xc = 4 * u
    g.stroke((yc + a_lo, yc, fd), (xc, xc - a_lo, p.sv), (xc, xc - a_up, fd), (top + a_up, top),
             start='h', end='h', part='diagonal')


FIVE_OPENINGS = [_stacked(_arm_gap), _mouth(_mouth_gap)]


@glyph('five', '5', 'fig_w', openings=FIVE_OPENINGS)
def five(g, junction=7):
    p, W, H, u, v, xl, xr, yb, yt = frame(g)
    yj = g.free('junction', junction) * v
    bot = yb - g.ob
    # the beak and the bar it faces (the 5's mouth, what tells it from a 6)
    g.stroke((8 * u, yt), (xl, yt), (xl, yj), (W / 2, yj), part='bar')
    g.stroke((W / 2 - p.sv / 4, yj), B(xr, yj), B(xr, bot), (W / 2, bot))
    g.stroke((W / 2 + p.sv / 4, bot), B(xl, bot), (xl, beak_bottom(g)), part='beak')


def _six(g, flip):
    p, W, H, u, v, xl, xr, yb, yt = frame(g)
    g.defaults_used['flip'] = flip
    ot, ob = (g.ob, g.ot) if flip else (g.ot, g.ob)
    yj = 7 * v
    top, bot = yt + ot, yb - ob
    T = (lambda x, y: (W - x, H - y)) if flip else (lambda x, y: (x, y))

    def b(x, y):
        return B(*T(x, y))

    g.stroke(T(8 * u, top), b(xl, top), T(xl, yj))
    g.stroke(T(xl, yj), b(xr, yj), b(xr, bot), b(xl, bot), closed=True)


@glyph('six', '6', 'fig_w', openings=[_stacked(_arm_gap)])
def six(g):
    _six(g, False)


@glyph('nine', '9', 'fig_w', openings=[_stacked(_arm_gap)])
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


@glyph('eight', '8', 'fig_w', openings=[_stacked(_counters)])
def eight(g):
    p, W, H, u, v, xl, xr, yb, yt = frame(g)
    yw = 6 * v
    top, bot = yt + g.ot, yb - g.ob
    big = p.leg + u
    g.stroke(B(xl, yw, big), B(xr, yw, big), B(xr, top), B(xl, top), closed=True)
    g.stroke(B(xl, bot), B(xr, bot), B(xr, yw), B(xl, yw), closed=True)


@glyph('five.ss02', None, 'fig_w',
       openings=[_stacked(_arm_gap), Opening(_arm_gap, 'junction', lambda p: 7.0, max_ratio=STACK_SHARE),
                 _mouth(_mouth_gap)])
def five_open(g):
    """The open five: its bowl's top one pixel row higher than the watch's.
    The one change that most separates 5 from 6 when blurred (see
    docs/research/legibility.md). Where even thinned horizontals leave no
    room under its arm, the bowl comes back down toward the 5's own."""
    five(g, junction=8)
