"""West African Latin: the letters of Bambara, Dyula, Ewe, Fanti, Fula, Hausa,
Twi, Yoruba and their neighbours (Google Fonts' African Latin set).

Drawn in Arris's own moves, from the letters they come from:

* open E and open O, Ɛ ɛ Ɔ ɔ: the Ze mirrored (as the Greek ε is, small)
  and C, c mirrored;
* hooks are Arris's arm, as the f's top: the stem turns at a bowl corner
  into a short arm; up and to the right on an ascender (ɓ ɗ ƙ), out of the
  top bar to the left and down on a capital's stem (Ɓ Ɗ), off the top of
  an arm to the right (Ƙ Ƴ ƴ);
* the left hooks of Ɲ ɲ are the j's tail, turned to the left under the
  stem.
"""
from __future__ import annotations

from ..draw import B, REGISTRY, glyph
from .cyrillic import mirror
from .extra_latin import stamp
from .figures import beak_depth
from .letterframe import Frame, k_arms, letter_width

HOOK_WHITE = 1.5   # modules of white between a hook and its stem, at every weight


def _mirrored(name, ch, src, kind):
    """``src`` drawn and mirrored left to right in its own body."""
    def fn(g, src=src):
        REGISTRY[src].fn(g)
        mirror(g)
    glyph(name, ch, lambda p, s=src: REGISTRY[s].width(p), kind=kind)(fn)


_mirrored('uni0190', 'Ɛ', 'uni0417', 'cap')     # open E: the Ze mirrored
_mirrored('uni0186', 'Ɔ', 'C', 'cap')           # open O
_mirrored('uni0254', 'ɔ', 'c', 'lower')

# ɛ is the Greek ε's drawing (the cmap maps it there)
ALIASES = {0x025B: 'uni03B5'}


def _hook_room(p):
    """How far a hook reaches from its stem, centre to centre: its white
    stays the same as the strokes grow, so heavy hooks do not close up. From
    the ungraded stem: grade changes strokes, never where they lie (the body
    is spaced ungraded)."""
    return HOOK_WHITE * p.m + p.ungraded().sv


def _left_tail(g, x, top):
    """From the stem at x, down from `top` under the baseline, turning left
    at the descender as the j's tail does, and up into a beak."""
    p = g.p
    f = Frame(g, 8, 'asc')
    yd = f.Y(-2)
    xl = x - _hook_room(p)
    g.stroke((x, top), B(x, yd), B(xl, yd), (xl, -p.desc + beak_depth(p)))


@glyph('uni019D', 'Ɲ', lambda p: REGISTRY['N'].width(p) + _hook_room(p), kind='cap')
def Nhookleft(g):
    """N with its left stem run on, in one stroke, down into the j's tail."""
    from .caps import n_diagonal
    p, H = g.p, g.p.cap
    o = _hook_room(p)
    f = Frame(g, 8, 'asc')
    xl, xr = o + p.sv / 2, g.W - p.sv / 2
    yd = f.Y(-2)
    g.stroke((xl, H), B(xl, yd), B(xl - o, yd), (xl - o, -p.desc + beak_depth(p)))
    g.stroke((xr, 0), (xr, H))
    at = n_diagonal(g, xl + p.sv / 2, xr - p.sv / 2, H)
    # cut flush on the cap line and the baseline (the N's clip does that; this
    # one is opened below the line for the tail)
    g.stroke(at(H), at(0), start='h', end='h')
    g.clip = (0, -p.desc, g.W, H)


@glyph('uni0272', 'ɲ', lambda p: REGISTRY['n'].width(p) + _hook_room(p), kind='lower')
def nhookleft(g):
    p = g.p
    o = _hook_room(p)
    stamp(g, 'n', dx=o, width=g.W - o)
    _left_tail(g, o + p.sv / 2, p.xh / 2)


def _cap_hook(g, x):
    """Out of a capital's top bar at the stem x: to the left, a bowl corner,
    and down into a beak."""
    p = g.p
    f = Frame(g, 9)
    yt = f.Y(11)
    xl = x - _hook_room(p)
    g.stroke((x, yt), B(xl, yt), (xl, yt - 2 * beak_depth(p)))


@glyph('uni0181', 'Ɓ', lambda p: REGISTRY['B'].width(p) + _hook_room(p), kind='cap')
def Bhook(g):
    p = g.p
    o = _hook_room(p)
    stamp(g, 'B', dx=o, width=g.W - o)
    _cap_hook(g, o + p.sv / 2)


@glyph('uni018A', 'Ɗ', lambda p: REGISTRY['D'].width(p) + _hook_room(p), kind='cap')
def Dhook(g):
    p = g.p
    o = _hook_room(p)
    stamp(g, 'D', dx=o, width=g.W - o)
    _cap_hook(g, o + p.sv / 2)


def _asc_hook(g, f, x):
    """An ascender at x turning right at the top, as the f's: a bowl corner
    and a short arm."""
    g.stroke((x, 0), B(x, f.Y(12)), (x + _hook_room(g.p) + g.p.sv / 2, f.Y(12)))


@glyph('uni0253', 'ɓ', letter_width(8, 2), kind='lower')
def bhook(g):
    f = Frame(g, 8, 'asc')
    _asc_hook(g, f, f.X(1))
    g.stroke(f.P(1, 8), B(*f.P(7, 8)), B(*f.P(7, 1)), f.P(1, 1), closed=True)


@glyph('uni0257', 'ɗ', lambda p: letter_width(8, 2)(p) + _hook_room(p), kind='lower')
def dhook(g):
    p = g.p
    W8 = g.W - _hook_room(p)
    f = Frame(g, 8, 'asc')
    xs = W8 - p.sv / 2                                      # the d's stem, where the d has it
    g.stroke((xs, 0), B(xs, f.Y(12)), (xs + _hook_room(p), f.Y(12)))
    x1 = p.sv / 2
    g.stroke((xs, f.Y(8)), B(x1, f.Y(8)), B(x1, f.Y(1)), (xs, f.Y(1)), closed=True)


@glyph('uni0199', 'ƙ', letter_width(8, 1), kind='lower')
def khook(g):
    f = Frame(g, 8, 'asc')
    _asc_hook(g, f, f.X(1))
    for pts, a, b in k_arms(g, f.X(1), f.W, f.p.xh):
        g.stroke(*pts, start=a, end=b)
    g.clip = (0, -f.p.desc, f.W + _hook_room(f.p), f.p.asc)


def _arm_flag(g, x, y):
    """A hook off the top of a diagonal arm ending at x: an arm on to the
    right along y, as the 1's flag runs off its stem."""
    g.stroke((x - g.p.sd / 2, y), (x + _hook_room(g.p), y))


@glyph('uni0198', 'Ƙ', lambda p: REGISTRY['K'].width(p) + _hook_room(p), kind='cap')
def Khook(g):
    """K whose arm ends in a hook to the right at the cap height."""
    p = g.p
    W9 = g.W - _hook_room(p)
    f = Frame(g, 9)
    x = p.sv / 2
    g.stroke((x, 0), (x, p.cap))
    for pts, a, b in k_arms(g, x, W9, p.cap):
        g.stroke(*pts, start=a, end=b)
    xa = max(q[0] for pts, a, b in k_arms(g, x, W9, p.cap) for q in pts)
    _arm_flag(g, xa, f.Y(11))
    g.clip = (0, 0, g.W, p.cap)


@glyph('uni01B3', 'Ƴ', lambda p: REGISTRY['Y'].width(p) + _hook_room(p), kind='cap')
def Yhook(g):
    """Y whose right arm turns right at the cap height."""
    p = g.p
    W10 = g.W - _hook_room(p)
    f = Frame(g, 10)
    H = p.cap
    xl, xr = p.sv / 2, W10 - p.sv / 2
    yj = f.Y(5.5)
    yg = yj + (W10 / 2 - xl)
    g.stroke((xl, H), (xl, yg), (W10 / 2, yj), (xr, yg), B(xr, f.Y(11)), (xr + _hook_room(p), f.Y(11)))
    g.stroke((W10 / 2, yj), (W10 / 2, 0))


@glyph('uni01B4', 'ƴ', lambda p: letter_width(8, 2)(p) + _hook_room(p), kind='lower')
def yhook(g):
    """y whose right stroke turns right at the x-height."""
    p = g.p
    W8 = g.W - _hook_room(p)
    f = Frame(g, 8, 'lower')
    k_ = f.k
    xl, xr = p.sv / 2, W8 - p.sv / 2
    a = (xr - p.sv / 2) + p.c - k_                          # x + y = a (as the y)
    g.stroke((xl, p.xh), (xl, a - xl), (xr, a - xr))
    g.stroke((xr + _hook_room(p), f.Y(8)), B(xr, f.Y(8)), B(xr, f.Y(-2)), (xl, f.Y(-2)))
