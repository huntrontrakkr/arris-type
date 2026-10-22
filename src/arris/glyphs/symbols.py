"""Currency, signs, arrows and spacing accents.

Arrows are octilinear by nature: a shaft and a head of two 45-degree
strokes, in all eight directions. Currency grows from the letters (the
euro and cent from C and c, the yen from Y), the copyright and registered
signs ring a small capital in a light octagon, and the spacing accents are
the combining marks set on their own.
"""
from __future__ import annotations

import math

from shapely import affinity

from ..draw import AUTO_SHARE, B, REGISTRY, Opening, _counter_white, draw, glyph
from ..geom import rings_to_shapely
from ..params import SQRT2
from . import marks
from .cyrillic import sc
from .letterframe import STEEP, Frame, letter_width
from .punct import _ring, axis, dot, punct

ALIASES = {0x2206: 'uni0394', 0x2126: 'uni03A9', 0x00B5: 'uni03BC', 0x2010: 'hyphen', 0x2011: 'hyphen',
           0x00AD: 'hyphen', 0x2012: 'endash'}


def stamp(g, name, p=None, dx=0.0, dy=0.0, width=None):
    sub = draw(name, p or g.p, width=width)
    g.add_glyph(sub, dx, dy)
    return sub.W


# --- Currency ----------------------------------------------------------------

@glyph('Euro', '€', letter_width(10, 2), kind='cap')
def Euro(g):
    """C with two bars through its waist, reaching out past its left side."""
    p = g.p
    w = stamp(g, 'C', dx=p.m, width=g.W - p.m)
    for y in (0.4 * p.cap, 0.6 * p.cap):
        g.stroke((0, y), (0.6 * g.W, y))


@glyph('cent', '¢', letter_width(8, 2), kind='lower',
       openings=[Opening(lambda g: _counter_white(g, 1), 'slash', lambda p: 0.5, max_ratio=AUTO_SHARE)])
def cent(g):
    p = g.p
    stamp(g, 'c', width=g.W)
    # the bar thins at heavy weights so the counter it closes stays open
    g.stroke((g.W / 2, -0.15 * p.cap, p.sv * g.free('slash', 1.0)), (g.W / 2, p.xh + 0.15 * p.cap))
    g.clip = None


@glyph('sterling', '£', letter_width(8, 1), kind='cap')
def sterling(g):
    """A stem rising into a hooked top, a bar across, a base."""
    f = Frame(g, 8)
    p = f.p
    g.stroke(f.P(8, 11), B(*f.P(2.5, 11)), f.P(2.5, 1))
    g.stroke((0, f.Y(1)), (f.W, f.Y(1)))
    g.stroke(f.P(0.5, 6), f.P(6, 6))


@glyph('yen', '¥', letter_width(10, 2), kind='cap')
def yen(g):
    p = g.p
    stamp(g, 'Y', width=g.W)
    for y in (0.25 * p.cap, 0.42 * p.cap):
        g.stroke((g.W * 0.2, y), (g.W * 0.8, y))


@glyph('currency', '¤', letter_width(8, 2), kind=('punct', 1.0))
def currency(g):
    p, W = g.p, g.W
    a = axis(p)
    r = W / 2 - 1.2 * p.m - p.sv / 2
    _ring(g, W / 2 - r, a - r, W / 2 + r, a + r)
    # four ticks on the diagonals, running out of the ring's corners: always
    # joined to it, at every weight
    for sx in (-1, 1):
        for sy in (-1, 1):
            x0, y0 = W / 2 + sx * (r - p.leg * 0.3), a + sy * (r - p.leg * 0.3)
            g.stroke((x0, y0), (x0 + sx * 1.2 * p.m, y0 + sy * 1.2 * p.m), start='flat', end='flat')


# --- Signs -------------------------------------------------------------------

@glyph('brokenbar', '¦', lambda p: p.sv, kind=('punct', 1.0))
def brokenbar(g):
    p = g.p
    top, bot = p.cap + 0.5 * p.m, -p.desc + 0.5 * p.m
    mid = (top + bot) / 2
    gap = max(p.m, 0.6 * p.sv) / 2
    g.stroke((p.sv / 2, bot), (p.sv / 2, mid - gap))
    g.stroke((p.sv / 2, mid + gap), (p.sv / 2, top))


def _section_mouth(g):
    """White between the upper beak and the loop below it (the lower mouth
    is its 180-degree turn)."""
    return g.part('beak').distance(g.part('loop'))


def _section_frame(p):
    """Top, bottom, bar thickness and the even gap between the four bars."""
    top, bot = p.cap, -0.15 * p.cap
    h = top - bot
    sh = min(p.sh, h / (4 + 3 * 0.9))                       # Glyph.stack(4, h, 0.9)
    return top, bot, sh, (h - 4 * sh) / 3


def _section_beak_min(p):
    from ..params import outer_leg
    return outer_leg(p, sh=_section_frame(p)[2]) + p.c


@glyph('section', '\u00a7', letter_width(7, 2), kind=('punct', 1.0),
       openings=[Opening(_section_mouth, 'beak', _section_beak_min, max_ratio=0.75),
                 Opening(_section_mouth, 'hook_gap', lambda p: 1.15 * _section_frame(p)[3], max_ratio=0.75)])
def section(g):
    """An S whose middle closes into a chamfered loop: beaks at the top right
    and the bottom left, a 180-degree turn of itself. Four bars share the
    height, so they thin in a tight stack and sit evenly. At heavy weights
    the mouths stay open: first the beaks shorten, then the loop's bars move
    in, giving the mouths white from the loop's counter."""
    from .figures import beak_depth
    p, W = g.p, g.W
    xl, xr, xm = p.sv / 2, W - p.sv / 2, W / 2
    top, bot, _, gap = _section_frame(p)
    sh = g.stack(4, top - bot, ratio=0.9)
    gap = g.free('hook_gap', gap)
    yt, yb = top - sh / 2, bot + sh / 2
    y1, y2 = yt - sh - gap, yb + sh + gap                  # the loop's top and bottom bars
    ym = (y1 + y2) / 2
    d = g.free('beak', beak_depth(p))
    # the S strokes run into the loop's straight sides, clear of its corners,
    # so the joins are the same at every weight
    g.stroke((xr, top - d), B(xr, yt), (xm, yt), part='beak')
    g.stroke((xm, yt), B(xl, yt), (xl, ym))
    g.stroke(B(xl, y1), B(xr, y1), B(xr, y2), B(xl, y2), closed=True, part='loop')
    g.stroke((xr, ym), B(xr, yb), (xm, yb))
    g.stroke((xm, yb), B(xl, yb), (xl, bot + d))
    g.clip = (0, bot, W, top)


@glyph('paragraph', '¶', letter_width(9, 3), kind=('punct', 1.0), solid=True)
def paragraph(g):
    """Two stems and a solid chamfered bowl."""
    p, W = g.p, g.W
    xs1, xs2 = W - 3 * p.m - p.sv, W - p.sv / 2
    top = p.cap
    g.stroke((xs1 + p.sv / 2, top - g.sh / 2), (W, top - g.sh / 2))
    for x in (xs1 + p.sv / 2, xs2):
        g.stroke((x, -0.15 * p.cap), (x, top))
    h = 0.55 * p.cap
    from shapely.geometry import Polygon
    leg = 1.5 * p.m
    x0, x1, y0, y1 = 0.0, xs1 + p.sv / 2, top - h, top
    g.extra.append(Polygon([(x0, y0 + leg), (x0 + leg, y0), (x1, y0), (x1, y1), (x0 + leg, y1), (x0, y1 - leg)]))
    g.clip = (0, -0.15 * p.cap, W, top)


def _ringed(g, letter):
    """A small capital inside a light octagon."""
    p, W = g.p, g.W
    s = 0.6 * p.sv
    g_ring = p.with_(sv=s, sh=s, sd=s, ss=s, c=0.25 * s)
    from ..geom import Thickness, ink
    from ..draw import Glyph
    ring = Glyph(g_ring, W=W)
    r = W / 2 - s / 2
    ring.stroke(B(s / 2, p.cap / 2 - r, 2 * p.m), B(W - s / 2, p.cap / 2 - r, 2 * p.m),
                B(W - s / 2, p.cap / 2 + r, 2 * p.m), B(s / 2, p.cap / 2 + r, 2 * p.m), closed=True)
    g.add_glyph(ring)
    # a half-size capital whose strokes stay in proportion to it
    k = 0.5
    t = min(0.6, 0.18 * k * p.cap / p.sv)
    pl = p.with_(cap=k * p.cap, m=k * p.m, sv=t * p.sv, sh=t * p.sh, sd=t * p.sd, ss=t * p.ss, c=t * p.c)
    wl = REGISTRY[letter].width(pl)
    stamp(g, letter, pl, dx=(W - wl) / 2, dy=p.cap / 2 - pl.cap / 2, width=wl)


@glyph('copyright', '©', lambda p: p.cap + 0.0, kind=('punct', 1.0))
def copyright(g):
    _ringed(g, 'C')


@glyph('registered', '®', lambda p: p.cap + 0.0, kind=('punct', 1.0))
def registered(g):
    _ringed(g, 'R')


@glyph('trademark', '™', lambda p: 0.55 * (REGISTRY['T'].width(p) + REGISTRY['M'].width(p)) + 0.6 * p.m,
       kind=('punct', 0.8))
def trademark(g):
    p = g.p
    k = 0.55
    ps = p.with_(cap=k * p.cap, m=k * p.m, sv=0.8 * p.sv, sh=0.8 * p.sh, sd=0.8 * p.sd, ss=0.8 * p.ss, c=0.8 * p.c)
    wt = stamp(g, 'T', ps, dy=p.cap - ps.cap)
    stamp(g, 'M', ps, dx=wt + 0.6 * p.m, dy=p.cap - ps.cap)


@glyph('perthousand', '‰', lambda p: REGISTRY['percent'].width(p) + 5.5 * p.m, kind=('punct', 1.0))
def perthousand(g):
    p = g.p
    w = stamp(g, 'percent')
    s = p.sv
    rw, rh = 4.5 * p.m + s, 5.0 * p.m + s
    x0 = w + 1.0 * p.m
    _ring(g, x0 + s / 2, g.sh / 2, x0 + rw - s / 2, rh - g.sh / 2)


@glyph('daggerdbl', '‡', letter_width(6, 1), kind=('punct', 1.0))
def daggerdbl(g):
    p, W = g.p, g.W
    g.stroke((W / 2, -p.desc + p.m), (W / 2, p.cap))
    g.stroke((0, p.cap - 3.5 * p.m), (W, p.cap - 3.5 * p.m))
    g.stroke((0, 2.5 * p.m), (W, 2.5 * p.m))
    g.clip = (0, -p.desc, W, p.cap)


@glyph('numero', '№', lambda p: REGISTRY['N'].width(p) + 5 * p.m, kind='cap')
def numero(g):
    p = g.p
    w = stamp(g, 'N')
    ps = p.with_(xh=0.5 * p.cap, m=0.6 * p.m)
    wo = REGISTRY['o'].width(ps)
    stamp(g, 'o', ps, dx=w + 0.8 * p.m, dy=p.cap - ps.xh, width=wo)
    y = p.cap - ps.xh - 0.8 * p.m - g.sh / 2
    g.stroke((w + 0.8 * p.m, y), (w + 0.8 * p.m + wo, y))


@glyph('infinity', '∞', letter_width(12, 4), kind=('punct', 1.0))
def infinity(g):
    """Two octagons, side by side, sharing a side."""
    p, W = g.p, g.W
    a = axis(p)
    s = p.sv
    h = 2.2 * p.m + s
    _ring(g, s / 2, a - h, W / 2, a + h, leg=1.2 * p.m)
    _ring(g, W / 2, a - h, W - s / 2, a + h, leg=1.2 * p.m)


@glyph('radical', '\u221a', lambda p: 2.0 * p.m + (p.cap + 0.5 * p.m) / 2 + 3.5 * p.m, kind=('punct', 0.6))
def radical(g):
    """A short 45-degree tick down to the baseline, a long 2:1 rise, a bar
    along the top."""
    p, W = g.p, g.W
    top = p.cap + 0.5 * p.m
    t = 2.0 * p.m
    g.stroke((0, t), (t, 0), start='v', end='h')
    g.stroke((t, 0), (t + top / 2, top), start='h', end='h')
    g.stroke((t + top / 2 - p.sv / 2, top - g.sh / 2), (W, top - g.sh / 2))
    g.clip = (0, 0, W, top)


# --- Arrows ------------------------------------------------------------------

def _arrow(g, angle):
    """Shaft and a two-stroke 45-degree head, pointing at ``angle`` degrees,
    centred on the axis."""
    p, W = g.p, g.W
    a = axis(p)
    cx = W / 2
    half = W / 2 - p.sv / 2 if angle % 180 == 0 else (W / 2 - p.sv / 2 if angle % 90 else 0.42 * p.cap)
    if angle % 90 == 45:
        half = (W / 2 - p.sv / 2) * SQRT2 * 0.9
    t = math.radians(angle)
    d = (math.cos(t), math.sin(t))
    tip = (cx + d[0] * half, a + d[1] * half)
    tail = (cx - d[0] * half, a - d[1] * half)
    head = 3.2 * p.m + 0.5 * p.sv
    g.stroke(tail, tip)
    for side in (1, -1):
        r = t + math.pi - side * math.pi / 4
        g.stroke(tip, (tip[0] + head * math.cos(r), tip[1] + head * math.sin(r)))


ARROWS = {'arrowleft': ('←', 180), 'arrowup': ('↑', 90), 'arrowright': ('→', 0),
          'arrowdown': ('↓', 270), 'arrowupleft': ('↖', 135), 'arrowupright': ('↗', 45),
          'arrowdownright': ('↘', 315), 'arrowdownleft': ('↙', 225)}
for nm, (ch, ang) in ARROWS.items():
    glyph(nm, ch, letter_width(11, 1), kind=('punct', 0.8))(lambda g, ang=ang: _arrow(g, ang))


@glyph('arrowboth', '↔', letter_width(13, 1), kind=('punct', 0.8))
def arrowboth(g):
    p, W = g.p, g.W
    a = axis(p)
    head = 3.2 * p.m + 0.5 * p.sv
    g.stroke((p.sv / 2, a), (W - p.sv / 2, a))
    for x, sgn in ((p.sv / 2, 1), (W - p.sv / 2, -1)):
        for s in (1, -1):
            g.stroke((x, a), (x + sgn * head / SQRT2, a + s * head / SQRT2))


@glyph('arrowupdn', '↕', letter_width(8, 1), kind=('punct', 0.8))
def arrowupdn(g):
    p, W = g.p, g.W
    top, bot = p.cap, 0.0
    head = 3.2 * p.m + 0.5 * p.sv
    g.stroke((W / 2, bot + p.sv / 2), (W / 2, top - p.sv / 2))
    for y, sgn in ((top - p.sv / 2, -1), (bot + p.sv / 2, 1)):
        for s in (1, -1):
            g.stroke((W / 2, y), (W / 2 + s * head / SQRT2, y + sgn * head / SQRT2))


# --- Spacing accents -----------------------------------------------------------

SPACING = {'circumflex': ('ˆ', '̂'), 'caron': ('ˇ', '̌'), 'breve': ('˘', '̆'),
           'dotaccent': ('˙', '̇'), 'ring': ('˚', '̊'), 'tilde': ('˜', '̃'),
           'hungarumlaut': ('˝', '̋'), 'dieresis': ('¨', '̈'), 'acute': ('´', '́'),
           'macron': ('¯', '̄')}


def _spacing_width(p):
    return 2 * marks.size(p, 'lc') + 1.5 * p.sv


for nm, (ch, comb) in SPACING.items():
    def fn(g, comb=comb):
        p = g.p
        marks.ABOVE[comb](g, g.W / 2, p.xh + marks.gap(p), 'lc')
    glyph(nm, ch, _spacing_width, kind=('punct', 0.6))(fn)


@glyph('cedilla', '¸', lambda p: 3 * p.m + p.sv, kind=('punct', 0.6))
def cedilla(g):
    marks.cedilla(g, g.W - g.p.sv / 2 - 0.5 * g.p.m, 0, 'lc')


@glyph('ogonek', '˛', lambda p: 3 * p.m + p.sv, kind=('punct', 0.6))
def ogonek(g):
    p = g.p
    yb = -p.desc + g.sh / 2 + 0.25 * p.m
    x = p.sv / 2
    g.stroke((x, g.sh), B(x, yb, p.m / 2), (x + 1.5 * p.m + p.sv / 2, yb))
