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

from ..draw import AUTO_SHARE, B, REGISTRY, Opening, Squint, _counter_white, draw, glyph
from ..geom import rings_to_shapely
from ..params import SQRT2
from . import marks
from .symkit import sign
from .cyrillic import sc
from .letterframe import STEEP, Frame, growing_width, least_white, letter_width
from .punct import _ring, axis, dot, punct

ALIASES = {0x2206: 'uni0394', 0x2126: 'uni03A9', 0x00B5: 'uni03BC', 0x2010: 'hyphen', 0x2011: 'hyphen'}
# (no soft hyphen, U+00AD: where a word may break is the shaper's business, and it is never drawn)


def stamp(g, name, p=None, dx=0.0, dy=0.0, width=None):
    sub = draw(name, p or g.p, width=width)
    g.add_glyph(sub, dx, dy)
    return sub.W


# --- Currency ----------------------------------------------------------------

def _bars_inset(p):
    from .currency import bar_inset
    return bar_inset(p)


def _bars_limit(p):
    """How far the squint rule may thin a pair of bars: to PAIR_T_MIN of the
    horizontal, never under the font's stroke floor."""
    from .currency import PAIR_T_MIN, pair_t
    return max(PAIR_T_MIN * p.sh, min(p.floor, pair_t(p))) / pair_t(p)


# The squint rule for a sign with a pair of bars (here and in currency): the
# bars thin, from the drawing's own down to PAIR_T_MIN of the horizontal,
# until their white reads.
BARS = (Squint('bars', _bars_limit),)
# A sign written with one bar as well as two (¥ ₩ ₦): in Mono's narrow cell,
# where even the thinned pair cannot keep its white (held to what reads, not
# to the Regular, which reads no better), the pair becomes one bar if one
# reads better. Not for a sign whose second bar is its identity (€, ₳, ₤
# against £).
BARS_OR_ONE = BARS + (Squint('one', lambda p: 1.0 if p.mono else 0.0, absolute=True),)


@glyph('Euro', '€', lambda p: letter_width(10, 2)(p) + max(0.0, _bars_inset(p) - p.m), kind='cap', squint=BARS)
def Euro(g):
    """C with two bars through its waist, running out past its back by a
    bar's own reach (currency.bar_out) and into its counter; the pair keeps
    the white of every barred sign (currency.bar_pair)."""
    from .currency import bar_hang, bar_pair, inset_letter
    p = g.p
    o = max(p.m, _bars_inset(p))
    inset_letter(g, 'C', o, g.W - o)
    bar_pair(g, p.cap / 2, -bar_hang(p), o + 0.6 * (g.W - o))


@glyph('cent', '¢', letter_width(8, 2), kind='lower',
       openings=[Opening(lambda g: _counter_white(g, 1), 'slash', lambda p: 0.5, max_ratio=AUTO_SHARE)],
       squint=(Squint('stem', lambda p: 0.0),))
def cent(g):
    p = g.p
    stamp(g, 'c', width=g.W)
    # the bar thins at heavy weights so the counter it closes stays open; where
    # even then the white beside it closes under the squint, it stops at the
    # c and stands only above and below it, as the dollar's does
    t = p.sv * g.free('slash', 1.0)
    lo, hi = -0.15 * p.cap, p.xh + 0.15 * p.cap
    runs = [(lo, hi)] if g.free('stem', 1.0) >= 0.5 else [(lo, g.sh / 2), (p.xh - g.sh / 2, hi)]
    for y0, y1 in runs:
        g.stroke((g.W / 2, y0, t), (g.W / 2, y1))
    g.clip = None


@glyph('sterling', '£', letter_width(8, 1), kind='cap')
def sterling(g):
    """A stem rising into a hooked top, a bar across, a base."""
    f = Frame(g, 8)
    p = f.p
    g.stroke(f.P(8, 11), B(*f.P(2.5, 11)), f.P(2.5, 1))
    g.stroke((0, f.Y(1)), (f.W, f.Y(1)))
    g.stroke(f.P(0.5, 6), f.P(6, 6))


@glyph('yen', '¥', letter_width(10, 2), kind='cap', squint=BARS_OR_ONE)
def yen(g):
    """Y with two bars across its stem, in the room under its arms: centred
    a third of the way up, but a stroke's white under where the arms meet
    the stem's sides, and over the baseline; they run out past the stem by
    a bar's own reach."""
    from shapely.geometry import LineString
    from .currency import bar_out, bar_pair, pair, wmin
    p = g.p
    stamp(g, 'Y', width=g.W)
    xc = g.W / 2
    y_arm = p.cap
    for x in (xc - p.sv / 2 - 1, xc + p.sv / 2 + 1):        # just outside the stem's sides
        cut = g.extra[-1].intersection(LineString([(x, -1), (x, p.cap + 1)]))
        y_arm = min([y_arm] + [s.bounds[1] for s in getattr(cut, 'geoms', [cut]) if not s.is_empty])
    t, gap = pair(g)
    band = 2 * t + gap
    yc = max(min(p.cap / 3, y_arm - wmin(p) - band / 2), band / 2 + wmin(p))
    bar_pair(g, yc, xc - p.sv / 2 - bar_out(p), xc + p.sv / 2 + bar_out(p))


@glyph('currency', '¤', lambda p: max(letter_width(8, 2)(p), 2.4 * p.m + 2 * p.sv + least_white(p)),
       kind=('punct', 1.0))
def currency(g):
    """A ring on the axis, its counter never under least_white (the sign
    widens), four ticks running out of its corners."""
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
    g.stroke((xm + p.sv / 4, yt), B(xl, yt), (xl, ym))     # (overlapping the beak's stroke)
    g.stroke(B(xl, y1), B(xr, y1), B(xr, y2), B(xl, y2), closed=True, part='loop')
    g.stroke((xr, ym), B(xr, yb), (xm, yb))
    g.stroke((xm + p.sv / 4, yb), B(xl, yb), (xl, bot + d))
    g.clip = (0, bot, W, top)


@glyph('paragraph', '¶', growing_width(9, 3, 1.5), kind=('punct', 1.0), solid=True)
def paragraph(g):
    """Two stems and a solid chamfered bowl."""
    p, W = g.p, g.W
    # the white between the stems: three modules less a stem, never less
    # than three quarters of a stem
    gap = max(3 * p.m - p.sv, 0.75 * p.sv)
    xs1, xs2 = W - gap - 2 * p.sv, W - p.sv / 2
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


@glyph('daggerdbl', '‡', growing_width(6, 1, 2.0), kind=('punct', 1.0))
def daggerdbl(g):
    """The dagger with a second bar; the stem's ends beyond the bars stay
    longer than a stem is thick."""
    from .punct import dagger_bar
    p, W = g.p, g.W
    g.stroke((W / 2, -p.desc + p.m), (W / 2, p.cap))
    yt = dagger_bar(p)
    yb = -p.desc + p.m + (p.cap - yt)
    g.stroke((0, yt), (W, yt))
    g.stroke((0, yb), (W, yb))
    g.clip = (0, -p.desc, W, p.cap)


@sign('numero', '№', lambda p: REGISTRY['N'].width(p) + 5 * p.m, kind='cap')
def numero(g):
    """N and a small underlined o: a sign, drawn with the plain letters
    (not Mono's cell-wide ones), so in the monospaced cut it is fitted to
    its cell as signs are (symkit.sign)."""
    p = g.p.with_(mono=False)
    w = stamp(g, 'N', p)
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

def arrow_head(p):
    """Length of an arrowhead's barbs: the module design (3.2 modules and
    half a stem), but never so short that the white between a barb's end
    and the shaft drops below half a stem: at 45 degrees that white is
    0.71 L - sv/2 - 0.71 sd, so L is at least sqrt2 sv + sd."""
    return max(3.2 * p.m + 0.5 * p.sv, SQRT2 * p.sv + p.sd)


def _arrow_width(p):
    """Wide enough for the head and two and a half stems of shaft beyond it."""
    return max(letter_width(11, 1)(p), p.sv + arrow_head(p) / SQRT2 + 2.5 * p.sv)


def _arrow(g, angle):
    """Shaft and a two-stroke 45-degree head, pointing at ``angle`` degrees,
    centred on the axis."""
    p, W = g.p, g.W
    a = axis(p)
    cx = W / 2
    half = W / 2 - p.sv / 2 if angle % 180 == 0 else (W / 2 - p.sv / 2 if angle % 90 else 0.42 * p.cap)
    if angle % 90 == 45:
        half = (W / 2 - p.sv / 2) * SQRT2 * 0.9
    if angle % 180 == 90:                                   # vertical: room for the head and a shaft
        half = max(half, 0.5 * (arrow_head(p) / SQRT2 + 2.5 * p.sv + p.sv))
    t = math.radians(angle)
    d = (math.cos(t), math.sin(t))
    tip = (cx + d[0] * half, a + d[1] * half)
    tail = (cx - d[0] * half, a - d[1] * half)
    head = arrow_head(p)
    g.stroke(tail, tip)
    for side in (1, -1):
        r = t + math.pi - side * math.pi / 4
        g.stroke(tip, (tip[0] + head * math.cos(r), tip[1] + head * math.sin(r)))
    g.clip = None


ARROWS = {'arrowleft': ('←', 180), 'arrowup': ('↑', 90), 'arrowright': ('→', 0),
          'arrowdown': ('↓', 270), 'arrowupleft': ('↖', 135), 'arrowupright': ('↗', 45),
          'arrowdownright': ('↘', 315), 'arrowdownleft': ('↙', 225)}
for nm, (ch, ang) in ARROWS.items():
    glyph(nm, ch, _arrow_width, kind=('punct', 0.8))(lambda g, ang=ang: _arrow(g, ang))


@glyph('arrowboth', '↔', lambda p: max(letter_width(13, 1)(p), 2 * arrow_head(p) / SQRT2 + 3.5 * p.sv),
       kind=('punct', 0.8))
def arrowboth(g):
    p, W = g.p, g.W
    a = axis(p)
    head = arrow_head(p)
    g.stroke((p.sv / 2, a), (W - p.sv / 2, a))
    for x, sgn in ((p.sv / 2, 1), (W - p.sv / 2, -1)):
        for s in (1, -1):
            g.stroke((x, a), (x + sgn * head / SQRT2, a + s * head / SQRT2))


@glyph('arrowupdn', '↕', lambda p: max(letter_width(8, 1)(p), 2 * arrow_head(p) / SQRT2 + p.sv), kind=('punct', 0.8))
def arrowupdn(g):
    p, W = g.p, g.W
    head = arrow_head(p)
    # the cap height, or as much more (shared above and below) as two heads
    # and a stem and a half of shaft between them need
    need = 2 * head / SQRT2 + 2.5 * p.sv
    extra = max(0.0, need - p.cap) / 2
    top, bot = p.cap + extra, -extra
    g.stroke((W / 2, bot + p.sv / 2), (W / 2, top - p.sv / 2))
    for y, sgn in ((top - p.sv / 2, -1), (bot + p.sv / 2, 1)):
        for s in (1, -1):
            g.stroke((W / 2, y), (W / 2 + s * head / SQRT2, y + sgn * head / SQRT2))
    g.clip = None


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
