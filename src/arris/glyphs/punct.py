"""Punctuation and symbols.

Same grid as the lowercase (x-height 9, cap 12, ascender 13, descender -3)
and the same moves: dots are stem-square and chamfered by the corner rule
(the watch's colon squares); the comma's tail turns at 45 degrees like the
4's clip; the question mark opens with the 2's beak; brackets and braces
turn at 45 degrees; slashes run at the 7's 2:1.

Spacing: punctuation takes plain bearings (a fraction of the letters'
light), not the area rule, which would pull a period into its neighbours.
"""
from __future__ import annotations

from ..draw import B, glyph
from ..params import SQRT2
from .figures import beak_depth
from .letterframe import STEEP, Frame, letter_width


def punct(name, char, wm, stems=1, width=None, sides=1.0):
    return glyph(name, char, width or letter_width(wm, stems), kind=('punct', sides))


def stem_w(n=1):
    return lambda p: n * p.sv


def dot(g, x, y0):
    """A stem-square dot standing on y0, centred on x."""
    s = g.p.sv
    g.stroke((x, y0), (x, y0 + s))


def dot_gap(p):
    """White between a dot and a stroke above it."""
    return max(0.8 * p.sv, 0.5 * p.m)


@punct('period', '.', 2, width=stem_w())
def period(g):
    f = Frame(g, 2, 'lower')
    dot(g, f.X(1), 0)


def _comma(g, f, x, y_top):
    """A dot whose foot turns down-left at 45 degrees: the comma's tail."""
    p = g.p
    s, k = p.sv, p.sd / SQRT2
    y_turn = y_top - s - 0.5 * s
    g.stroke((x, y_top), (x, y_turn), (x - 0.75 * s, y_turn - 0.75 * s), end='h')


@punct('comma', ',', 3, width=lambda p: 1.5 * p.sv)
def comma(g):
    f = Frame(g, 3, 'lower')
    _comma(g, f, g.W - g.p.sv / 2, g.p.sv)


@punct('colon', ':', 2, width=stem_w())
def colon(g):
    f = Frame(g, 2, 'lower')
    dot(g, f.X(1), 0)
    dot(g, f.X(1), g.p.xh - g.p.sv)


@punct('semicolon', ';', 3, width=lambda p: 1.5 * p.sv)
def semicolon(g):
    f = Frame(g, 3, 'lower')
    x = g.W - g.p.sv / 2
    _comma(g, f, x, g.p.sv)
    dot(g, x, g.p.xh - g.p.sv)


@punct('exclam', '!', 2, width=stem_w())
def exclam(g):
    f = Frame(g, 2, 'lower', top=g.p.cap)
    p = g.p
    dot(g, f.X(1), 0)
    g.stroke((f.X(1), p.sv + dot_gap(p)), (f.X(1), p.cap))


@punct('question', '?', 9, 2)
def question(g):
    f = Frame(g, 9, 'cap')
    p = g.p
    d = beak_depth(p)
    # The 2's bowl, its right side turning back into a short stem at the centre.
    xs = f.X(4)
    g.stroke((f.X(1), p.cap - d), B(*f.P(1, 11)), B(*f.P(8, 11)), B(*f.P(8, 6)), (xs, f.Y(6)),
             (xs, p.sv + dot_gap(p)))
    dot(g, xs, 0)


@punct('hyphen', '-', 6, 0)
def hyphen(g):
    f = Frame(g, 6, 'lower')
    g.stroke((0, f.Y(5)), (g.W, f.Y(5)))


@punct('endash', '–', 9, 0)
def endash(g):
    f = Frame(g, 9, 'lower')
    g.stroke((0, f.Y(5)), (g.W, f.Y(5)))


@punct('emdash', '—', 16, 0)
def emdash(g):
    f = Frame(g, 16, 'lower')
    g.stroke((0, f.Y(5)), (g.W, f.Y(5)))


@punct('underscore', '_', 9, 0)
def underscore(g):
    f = Frame(g, 9, 'lower')
    g.stroke((0, f.Y(-2)), (g.W, f.Y(-2)))


@punct('quotesingle', "'", 2, width=stem_w())
def quotesingle(g):
    f = Frame(g, 2, 'lower', top=g.p.cap)
    p = g.p
    g.stroke((f.X(1), p.cap - 2 * p.sv), (f.X(1), p.cap))


@punct('quotedbl', '"', 6, 2)
def quotedbl(g):
    f = Frame(g, 6, 'lower', top=g.p.cap)
    p = g.p
    for x in (f.X(1), f.X(5)):
        g.stroke((x, p.cap - 2 * p.sv), (x, p.cap))


@punct('quoteright', '’', 3, width=lambda p: 1.5 * p.sv)
def quoteright(g):
    f = Frame(g, 3, 'lower', top=g.p.cap)
    _comma(g, f, g.W - g.p.sv / 2, g.p.cap)


@punct('quoteleft', '‘', 3, width=lambda p: 1.5 * p.sv)
def quoteleft(g):
    f = Frame(g, 3, 'lower', top=g.p.cap)
    p = g.p
    s = p.sv
    # the comma turned half round: tail up-right, dot below
    x = s / 2
    y_bot = p.cap - 2.25 * s
    y_turn = y_bot + 1.5 * s
    g.stroke((x, y_bot), (x, y_turn), (x + 0.75 * s, y_turn + 0.75 * s), end='h')


@punct('quotedblright', '”', 7, width=lambda p: 3.5 * p.sv)
def quotedblright(g):
    f = Frame(g, 7, 'lower', top=g.p.cap)
    for x in (1.5 * g.p.sv - g.p.sv / 2, g.W - g.p.sv / 2):
        _comma(g, f, x, g.p.cap)


@punct('quotedblleft', '“', 7, width=lambda p: 3.5 * p.sv)
def quotedblleft(g):
    f = Frame(g, 7, 'lower', top=g.p.cap)
    p = g.p
    s = p.sv
    for x in (s / 2, s / 2 + 2 * s):
        y_bot = p.cap - 2.25 * s
        y_turn = y_bot + 1.5 * s
        g.stroke((x, y_bot), (x, y_turn), (x + 0.75 * s, y_turn + 0.75 * s), end='h')


@punct('quotesinglbase', '‚', 3, width=lambda p: 1.5 * p.sv)
def quotesinglbase(g):
    f = Frame(g, 3, 'lower')
    _comma(g, f, g.W - g.p.sv / 2, g.p.sv)


@punct('quotedblbase', '„', 7, width=lambda p: 3.5 * p.sv)
def quotedblbase(g):
    f = Frame(g, 7, 'lower')
    for x in (1.5 * g.p.sv - g.p.sv / 2, g.W - g.p.sv / 2):
        _comma(g, f, x, g.p.sv)


def _paren(g, f, mirror=False):
    p = g.p
    W = g.W
    k = p.sd / SQRT2
    top, bot = p.cap + 0.5 * p.m, -p.desc + 0.5 * p.m
    xs = p.sv / 2
    reach = W - xs                                          # 45 degrees in, then down
    T = (lambda x, y: (W - x, y)) if mirror else (lambda x, y: (x, y))
    g.stroke(T(xs + reach, top), T(xs, top - reach), T(xs, bot + reach), T(xs + reach, bot),
             start='h', end='h')
    g.clip = (0, bot, W, top)


@punct('parenleft', '(', 4, 1)
def parenleft(g):
    f = Frame(g, 4, 'lower')
    _paren(g, f)


@punct('parenright', ')', 4, 1)
def parenright(g):
    f = Frame(g, 4, 'lower')
    _paren(g, f, mirror=True)


def _bracket(g, mirror=False):
    p = g.p
    W = g.W
    top, bot = p.cap + 0.5 * p.m, -p.desc + 0.5 * p.m
    T = (lambda x, y: (W - x, y)) if mirror else (lambda x, y: (x, y))
    yt, yb = top - g.sh / 2, bot + g.sh / 2
    g.stroke(T(W, yt), T(p.sv / 2, yt), T(p.sv / 2, yb), T(W, yb))
    g.clip = (0, bot, W, top)


@punct('bracketleft', '[', 4, 1)
def bracketleft(g):
    _bracket(g)


@punct('bracketright', ']', 4, 1)
def bracketright(g):
    _bracket(g, mirror=True)


def _brace(g, mirror=False):
    p = g.p
    W = g.W
    top, bot = p.cap + 0.5 * p.m, -p.desc + 0.5 * p.m
    mid = (top + bot) / 2
    xs = W - p.sv / 2 - p.sv                               # the brace's spine
    xp = p.sv / 2                                           # its point
    reach = xs - xp
    T = (lambda x, y: (W - x, y)) if mirror else (lambda x, y: (x, y))
    g.stroke(T(W, top - g.sh / 2), B(*T(xs, top - g.sh / 2)), T(xs, mid + reach), T(xp, mid),
             T(xs, mid - reach), B(*T(xs, bot + g.sh / 2)), T(W, bot + g.sh / 2))
    g.clip = (0, bot, W, top)


@punct('braceleft', '{', 6, 1)
def braceleft(g):
    _brace(g)


@punct('braceright', '}', 6, 1)
def braceright(g):
    _brace(g, mirror=True)


def _slash(g, mirror=False):
    p = g.p
    top, bot = p.cap + 0.5 * p.m, -p.desc + 0.5 * p.m
    w = p.ss / STEEP[1]
    W = g.W
    x_at = lambda y: w / 2 + (y - bot) / 2
    pts = [(x_at(bot), bot), (x_at(top), top)]
    if mirror:
        pts = [(W - x, y) for x, y in pts]
    g.stroke(*pts, start='h', end='h')
    g.clip = (0, bot, W, top)


def slash_width(p):
    top, bot = p.cap + 0.5 * p.m, -p.desc + 0.5 * p.m
    return p.ss / STEEP[1] + (top - bot) / 2


@punct('slash', '/', 9, width=slash_width)
def slash(g):
    _slash(g)


@punct('backslash', '\\', 9, width=slash_width)
def backslash(g):
    _slash(g, mirror=True)


@punct('bar', '|', 2, width=stem_w())
def bar(g):
    p = g.p
    top, bot = p.cap + 0.5 * p.m, -p.desc + 0.5 * p.m
    g.stroke((p.sv / 2, bot), (p.sv / 2, top))
    g.clip = (0, bot, g.W, top)


# --- Mathematical: on the axis at half the cap height ----------------------

def axis(p):
    return p.cap / 2


@punct('plus', '+', 8, 1)
def plus(g):
    p, W = g.p, g.W
    a, h = axis(p), W / 2
    g.stroke((0, a), (W, a))
    g.stroke((h, a - h), (h, a + h))
    g.clip = (0, a - h, W, a + h)


@punct('minus', '−', 8, 0)
def minus(g):
    p, W = g.p, g.W
    g.stroke((0, axis(p)), (W, axis(p)))


@punct('equal', '=', 8, 0)
def equal(g):
    p, W = g.p, g.W
    off = (g.sh + max(0.8 * g.sh, p.m)) / 2
    for y in (axis(p) - off, axis(p) + off):
        g.stroke((0, y), (W, y))


@punct('multiply', '×', 8, 1)
def multiply(g):
    p, W = g.p, g.W
    a, h = axis(p), W / 2
    g.stroke((0, a - h), (W, a + h), start='v', end='v')
    g.stroke((0, a + h), (W, a - h), start='v', end='v')
    g.clip = (0, a - h, W, a + h)


@punct('divide', '÷', 8, 0)
def divide(g):
    p, W = g.p, g.W
    a = axis(p)
    g.stroke((0, a), (W, a))
    gap = dot_gap(p) * 0.75
    dot(g, W / 2, a + g.sh / 2 + gap)
    dot(g, W / 2, a - g.sh / 2 - gap - p.sv)


def _chevron(g, mirror=False, half=None):
    p, W = g.p, g.W
    a = axis(p)
    k = p.sd / SQRT2
    h = W - p.sv / 2 if half is None else half
    T = (lambda x, y: (W - x, y)) if mirror else (lambda x, y: (x, y))
    g.stroke(T(W, a + h), T(W - h, a), T(W, a - h), start='v', end='v')
    g.clip = (0, a - h - p.sv, W, a + h + p.sv)


@punct('less', '<', 7, 1)
def less(g):
    _chevron(g)


@punct('greater', '>', 7, 1)
def greater(g):
    _chevron(g, mirror=True)
