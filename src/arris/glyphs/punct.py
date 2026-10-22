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

import math

from ..draw import B, glyph
from ..params import SQRT2
from .figures import beak_depth, heaviness
from .letterframe import STEEP, Frame, growing_width, letter_width


def punct(name, char, wm, stems=1, width=None, sides=1.0):
    return glyph(name, char, width or letter_width(wm, stems), kind=('punct', sides))


def stem_w(n=1):
    return lambda p: n * p.sv


def dot_w(n=1):
    return lambda p: n * p.dot()


def dot(g, x, y0):
    """A square dot standing on y0, centred on x (Params.dot)."""
    s = g.p.dot()
    g.stroke((x, y0, s), (x, y0 + s))


def dot_gap(p):
    """White between a dot and a stroke above it."""
    return max(0.8 * p.sv, 0.5 * p.m)


@punct('period', '.', 2, width=dot_w())
def period(g):
    f = Frame(g, 2, 'lower')
    dot(g, f.X(1), 0)


def _comma(g, f, x, y_top, stub=None, s=None):
    """A dot whose foot turns down-left at 45 degrees: the comma's tail.
    ``stub`` is the dot's height above the turn (a stem and a half); ``s``
    its thickness (the stem's, unless a mark must be lighter to fit)."""
    p = g.p
    s = p.dot() if s is None else s
    y_turn = y_top - (1.5 * s if stub is None else stub)
    g.stroke((x, y_top, s), (x, y_turn, s * p.sd / p.sv), (x - 0.75 * s, y_turn - 0.75 * s), end='h')


@punct('comma', ',', 3, width=dot_w(1.5))
def comma(g):
    f = Frame(g, 3, 'lower')
    _comma(g, f, g.W - g.p.dot() / 2, g.p.dot())


@punct('colon', ':', 2, width=dot_w())
def colon(g):
    f = Frame(g, 2, 'lower')
    dot(g, f.X(1), 0)
    dot(g, f.X(1), g.p.xh - g.p.dot())


@punct('semicolon', ';', 3, width=dot_w(1.5))
def semicolon(g):
    f = Frame(g, 3, 'lower')
    x = g.W - g.p.dot() / 2
    _comma(g, f, x, g.p.dot())
    dot(g, x, g.p.xh - g.p.dot())


@punct('exclam', '!', 2, width=dot_w())
def exclam(g):
    f = Frame(g, 2, 'lower', top=g.p.cap)
    p = g.p
    dot(g, f.X(1), 0)
    g.stroke((f.X(1), p.dot() + dot_gap(p)), (f.X(1), p.cap))


@punct('question', '?', 9, 2)
def question(g):
    f = Frame(g, 9, 'cap')
    p = g.p
    d = beak_depth(p)
    # The 2's bowl, its right side turning back into a short stem at the centre.
    xs = f.X(4)
    g.stroke((f.X(1), p.cap - d), B(*f.P(1, 11)), B(*f.P(8, 11)), B(*f.P(8, 6)), (xs, f.Y(6)),
             (xs, p.dot() + dot_gap(p)))
    dot(g, xs, 0)


@punct('hyphen', '-', 6, 0)
def hyphen(g):
    f = Frame(g, 6, 'lower')
    # in the monospaced cut the hyphen is a minus for code: on the math axis,
    # in line with + = < > and the arrows it ligates into
    y = axis(g.p) if g.p.mono else f.Y(5)
    g.stroke((0, y), (g.W, y))


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
    g.stroke((f.X(1), p.cap - 2 * p.dot()), (f.X(1), p.cap))


@punct('quotedbl', '"', 6, 2)
def quotedbl(g):
    f = Frame(g, 6, 'lower', top=g.p.cap)
    p = g.p
    for x in (f.X(1), f.X(5)):
        g.stroke((x, p.cap - 2 * p.dot()), (x, p.cap))


@punct('quoteright', '’', 3, width=dot_w(1.5))
def quoteright(g):
    f = Frame(g, 3, 'lower', top=g.p.cap)
    _comma(g, f, g.W - g.p.dot() / 2, g.p.cap)


@punct('quoteleft', '‘', 3, width=dot_w(1.5))
def quoteleft(g):
    f = Frame(g, 3, 'lower', top=g.p.cap)
    p = g.p
    s = p.dot()
    # the comma turned half round: tail up-right, dot below
    x = s / 2
    y_bot = p.cap - 2.25 * s
    y_turn = y_bot + 1.5 * s
    g.stroke((x, y_bot, s), (x, y_turn, s * p.sd / p.sv), (x + 0.75 * s, y_turn + 0.75 * s), end='h')


@punct('quotedblright', '”', 7, width=dot_w(3.5))
def quotedblright(g):
    f = Frame(g, 7, 'lower', top=g.p.cap)
    s = g.p.dot()
    for x in (s, g.W - s / 2):
        _comma(g, f, x, g.p.cap)


@punct('quotedblleft', '“', 7, width=dot_w(3.5))
def quotedblleft(g):
    f = Frame(g, 7, 'lower', top=g.p.cap)
    p = g.p
    s = p.dot()
    for x in (s / 2, s / 2 + 2 * s):
        y_bot = p.cap - 2.25 * s
        y_turn = y_bot + 1.5 * s
        g.stroke((x, y_bot, s), (x, y_turn, s * p.sd / p.sv), (x + 0.75 * s, y_turn + 0.75 * s), end='h')


@punct('quotesinglbase', '‚', 3, width=dot_w(1.5))
def quotesinglbase(g):
    f = Frame(g, 3, 'lower')
    _comma(g, f, g.W - g.p.dot() / 2, g.p.dot())


@punct('quotedblbase', '„', 7, width=dot_w(3.5))
def quotedblbase(g):
    f = Frame(g, 7, 'lower')
    s = g.p.dot()
    for x in (s, g.W - s / 2):
        _comma(g, f, x, s)


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


BEAK = 0.5        # the brace's beak: its centreline depth, in stems


def _brace_parts(p, sh):
    """(hook, beak depth, point ink) of the brace: hooks a stem and a half
    from the spine's centre, a beak half a stem deep whose 2:1 point runs
    on past it by its stroke's own reach."""
    from ..draw import _thickness
    t = _thickness(p, sh)((2, 1))
    return 1.5 * p.sv, max(BEAK * p.sv, 2 * p.floor), t / (2 * math.sin(SLOPE))


def brace_width(p):
    hook, d, tip = _brace_parts(p, p.sh)
    w = hook + d + tip
    return min(w, p.fig_w) if p.mono else w


def _brace(g, mirror=False):
    """Hooks at the ends, long straight spines, and a small sharp beak at
    the middle on the shallow 2:1: a brace, distinct from ( and from <."""
    p = g.p
    W = g.W
    top, bot = p.cap + 0.5 * p.m, -p.desc + 0.5 * p.m
    mid = (top + bot) / 2
    hook, d, tip = _brace_parts(p, g.sh)
    xs = max(W - hook, tip + d)                             # the spine (the hook gives way in a narrow cell)
    xp = xs - d                                             # the beak's point
    T = (lambda x, y: (W - x, y)) if mirror else (lambda x, y: (x, y))
    g.stroke(T(W, top - g.sh / 2), B(*T(xs, top - g.sh / 2)), T(xs, mid + d / 2), T(xp, mid),
             T(xs, mid - d / 2), B(*T(xs, bot + g.sh / 2)), T(W, bot + g.sh / 2))
    g.clip = (0, bot, W, top)


@punct('braceleft', '{', 6, 1, width=brace_width)
def braceleft(g):
    _brace(g)


@punct('braceright', '}', 6, 1, width=brace_width)
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


@punct('minus', '−', 8, 1)
def minus(g):
    p, W = g.p, g.W
    g.stroke((0, axis(p)), (W, axis(p)))


def eq_white(g):
    """White between the bars of = (and of every sign stacked from them):
    1.6 bars, two modules at the lightest weights, so the pair never clogs
    into one stroke at text sizes."""
    return max(1.6 * g.sh, 2 * g.p.m)


def eq_offset(g):
    """Half the distance between the bars of =, centre to centre."""
    return (g.sh + eq_white(g)) / 2


@punct('equal', '=', 8, 1)
def equal(g):
    p, W = g.p, g.W
    off = eq_offset(g)
    for y in (axis(p) - off, axis(p) + off):
        g.stroke((0, y), (W, y))


@punct('multiply', '×', 8, 1)
def multiply(g):
    p, W = g.p, g.W
    a, h = axis(p), W / 2
    g.stroke((0, a - h), (W, a + h), start='v', end='v')
    g.stroke((0, a + h), (W, a - h), start='v', end='v')
    g.clip = (0, a - h, W, a + h)


@punct('divide', '÷', 8, 1)
def divide(g):
    p, W = g.p, g.W
    a = axis(p)
    g.stroke((0, a), (W, a))
    gap = dot_gap(p) * 0.75
    dot(g, W / 2, a + g.sh / 2 + gap)
    dot(g, W / 2, a - g.sh / 2 - gap - p.dot())


SLOPE = math.atan2(1, 2)       # chevrons run at the shallow 2:1


def chevron_geometry(g, W=None):
    """(point x, reach) of the < chevron across a body W wide: its arms at
    2:1 end cut square at the body's right edge, and its point's ink (which
    runs 1/(2 sin) of the stroke past the centreline's point) at the left
    edge. Half its height is half its reach: the chevron fills the operator
    box, as + does."""
    from ..draw import _thickness
    W = g.W if W is None else W
    t = _thickness(g.p, g.sh)((2, 1))
    x_tip = t / (2 * math.sin(SLOPE))
    return x_tip, W - x_tip


def _chevron(g, mirror=False):
    p, W = g.p, g.W
    a = axis(p)
    x_tip, reach = chevron_geometry(g)
    v = reach / 2
    T = (lambda x, y: (W - x, y)) if mirror else (lambda x, y: (x, y))
    g.stroke(T(W, a + v), T(x_tip, a), T(W, a - v), start='v', end='v')


@punct('less', '<', 8, 1)
def less(g):
    _chevron(g)


@punct('greater', '>', 8, 1)
def greater(g):
    _chevron(g, mirror=True)


# --- ASCII symbols ---------------------------------------------------------

@punct('numbersign', '#', 10, 2, width=growing_width(10, 2, 2.0))
def numbersign(g):
    """Two bars each way, never closer than a stroke: the square between
    them stays open at every weight."""
    f = Frame(g, 10, 'cap')
    p, W = g.p, g.W
    gx = max(f.X(7) - f.X(3) - p.sv, p.sv)                 # white between the verticals
    gy = max(f.Y(8) - f.Y(4) - g.sh, g.sh)                  # and between the horizontals
    for x in (W / 2 - (gx + p.sv) / 2, W / 2 + (gx + p.sv) / 2):
        g.stroke((x, f.Y(0.5)), (x, f.Y(11.5)))
    for y in (p.cap / 2 - (gy + g.sh) / 2, p.cap / 2 + (gy + g.sh) / 2):
        g.stroke((0, y), (W, y))


@punct('dollar', '$', 9, 2)
def dollar(g):
    from .caps import S
    S(g)
    p = g.p
    f = Frame(g, 9, 'cap')
    top, bot = p.cap + 1.5 * p.m, -1.5 * p.m
    g.stroke((g.W / 2, bot), (g.W / 2, top))
    g.clip = (0, bot, g.W, top)


def _ring(g, x0, y0, x1, y1, w=None, leg=None):
    """A small closed octagon, centreline box (x0, y0)-(x1, y1)."""
    p = g.p
    leg = p.leg * 0.6 if leg is None else leg
    pts = [B(x0, y0, leg, w), B(x1, y0, leg, w), B(x1, y1, leg, w), B(x0, y1, leg, w)]
    g.stroke(*pts, closed=True)


@punct('percent', '%', 11, 3)
def percent(g):
    f = Frame(g, 11, 'cap')
    p, W, H = g.p, g.W, g.p.cap
    s = p.sv
    rw = 4.5 * p.m + s                                       # ring outer width
    rh = 5.0 * p.m + s
    _ring(g, s / 2, H - rh + g.sh / 2, rw - s / 2, H - g.sh / 2)
    _ring(g, W - rw + s / 2, g.sh / 2, W - s / 2, rh - g.sh / 2)
    w = p.ss / STEEP[1]
    x_at = lambda y: (W - w) / 2 - H / 4 + w / 2 + y / 2
    g.stroke((x_at(0), 0), (x_at(H), H), start='h', end='h')


@punct('ampersand', '&', 10, 2)
def ampersand(g):
    f = Frame(g, 10, 'cap')
    p, W, H, k = g.p, g.W, g.p.cap, p_k(g)
    # upper loop: a small octagon, its lower corners large (the 8's)
    big = p.leg + p.m
    g.stroke(B(*f.P(2, 6.5), big), B(*f.P(6, 6.5), big), B(*f.P(6, 11)), B(*f.P(2, 11)), closed=True)
    # lower bowl: from the loop's lower left, round the bottom, open at the right
    a = W + p.c - k                                          # the leg: x + y = a
    g.stroke(f.P(2, 8.5), f.P(2, 6.5), B(*f.P(1, 5.5), p.m / 2), B(*f.P(1, 1)), (a - f.Y(1), f.Y(1)))
    # the leg: 45 degrees from inside the loop down to the baseline at the right
    y0 = f.Y(8.5)
    g.stroke((a - y0, y0), (a, 0), start='h', end='h')
    # the arm, up from the leg at the right
    g.stroke((f.X(8), a - f.X(8) - p.sv), f.P(8, 5.5))


def p_k(g):
    return g.p.sd / SQRT2


@punct('at', '@', 12, 3)
def at(g):
    f = Frame(g, 12, 'cap')
    p = g.p
    # inner a: bowl and stem, kept a stroke's white inside the ring
    yb = max(f.Y(3), f.Y(1) + g.sh + max(p.m, 0.5 * p.sv))
    g.stroke((f.X(8), yb), B(f.X(4.5), yb), B(*f.P(4.5, 7.5)), f.P(8, 7.5), closed=True)
    # stem, then out along the bottom and round the outside, open at the foot
    g.stroke(f.P(8, 7.5), (f.X(8), yb), B(f.X(11), yb, p.m / 2), f.P(11, 7))
    g.stroke(f.P(11, 6), B(*f.P(11, 11)), B(*f.P(1, 11)), B(*f.P(1, 1)), f.P(10, 1))


SPOKE = math.atan2(1, 2)       # the asterisk's slanted spokes: the shallow 2:1
SPOKE_WHITE = 0.5              # the share of a spoke that keeps white beside it, at least


def _asterisk_r(p):
    """The asterisk's radius (centre to a spoke's end): in the monospaced cut
    0.35 of the cap height (the asterisk 0.7 of it tall, as code faces set
    it, on the axis between the operands of `a*b`); in the proportional cut
    0.27, raised to the cap height as text sets it. It grows toward
    Black (three tenths), where the strokes need the room."""
    return (0.35 if p.mono else 0.27) * p.cap * (1 + 0.3 * heaviness(p))


@punct('asterisk', '*', 7, 1,
       width=lambda p: 2 * _asterisk_r(p) * math.cos(SPOKE) + max(p.sv, p.sd))
def asterisk(g):
    """Six spokes, near sixty degrees apart in the figures' own directions:
    the vertical and the four shallow 2:1 slopes, crossing at the centre,
    each cut square at its end. The strokes keep their weight unless the
    white between two spokes would begin outside the inner (1 - SPOKE_WHITE)
    of their length; past that (toward Black) they lighten, so the
    asterisk stays a star rather than a knot."""
    from ..draw import _thickness
    from .shapes import slanted
    p, W = g.p, g.W
    r = _asterisk_r(p)
    t_max = 2 * math.sin(SPOKE) * (1 - SPOKE_WHITE) * r       # white begins at t / (2 sin SPOKE) from the centre
    th = _thickness(p, g.sh)
    xc = W / 2
    yc = axis(p) if p.mono else p.cap - r
    g.stroke((xc, yc - r, slanted(g, min(max(p.sv, p.floor), t_max), (0, 1))), (xc, yc + r))
    c, s_ = r * math.cos(SPOKE), r * math.sin(SPOKE)
    for sy in (1, -1):
        d = (2, sy)
        g.stroke((xc - c, yc - sy * s_, slanted(g, min(th(d), t_max), d)), (xc + c, yc + sy * s_))


@punct('asciicircum', '^', 8, 1)
def asciicircum(g):
    p, W = g.p, g.W
    k = p.sd / SQRT2
    top = p.cap
    h = W / 2
    ya = top + p.c - k
    g.stroke((0, ya - h), (W / 2, ya), (W, ya - h), start='v', end='v')
    g.clip = (0, ya - h - p.sv, W, top)


@punct('asciitilde', '~', 8, 1)
def asciitilde(g):
    """A step on the axis: up at 45 degrees, along, down, along, up."""
    p, W = g.p, g.W
    a = axis(p)
    d = W / 4
    g.stroke((0, a - d / 2), (d, a + d / 2), (2 * d, a + d / 2), (3 * d, a - d / 2), (W, a + d / 2 - d),
             start='v', end='v')


@punct('grave', '`', 4, 1)
def grave(g):
    p, W = g.p, g.W
    k = p.sd / SQRT2
    top = p.cap
    g.stroke((0, top + k), (W, top - W + k), start='h', end='h')
    g.clip = (0, top - W, W, top)


# --- Typographic -------------------------------------------------------------

@punct('degree', '°', 5, 2)
def degree(g):
    p, W = g.p, g.W
    s = p.sv * 0.8
    top = p.cap
    _ring(g, s / 2, top - W + g.sh / 2, W - s / 2, top - g.sh / 2)


@punct('bullet', '\u2022', 4, width=lambda p: 2.4 * p.sv)
def bullet(g):
    """A large dot on the x-height's centre: a square, chamfered."""
    p, W = g.p, g.W
    y = p.xh / 2
    g.stroke((W / 2, y - W / 2, W), (W / 2, y + W / 2))


@punct('periodcentered', '·', 2, width=dot_w())
def periodcentered(g):
    p = g.p
    dot(g, p.dot() / 2, p.xh / 2 - p.dot() / 2)


@punct('ellipsis', '…', 8, width=dot_w(3 + 2 * 1.2))
def ellipsis(g):
    p = g.p
    for i in range(3):
        dot(g, p.dot() / 2 + i * 2.2 * p.dot(), 0)


def _guil_reach(p):
    """How far a guillemet's chevron reaches across (and half its height):
    never less than a diagonal stroke and a half, so its arms stay strokes."""
    return max(min((letter_width(7, 2)(p) - 1.4 * p.sv) / 2, p.xh / 3), 1.5 * p.sd)


def _guil_step(p):
    """From one chevron to the next: an arm's width across (a 45-degree
    stroke is sqrt2 of its thickness wide) and white as wide as a counter's
    least, so the pair never runs together."""
    return SQRT2 * (p.sd + max(0.8 * p.m, 0.7 * p.sd))


def _guil_width(n):
    return lambda p: (n - 1) * _guil_step(p) + _guil_reach(p) + p.sv


def _guil(g, n, mirror):
    p, W = g.p, g.W
    a = p.xh / 2
    h = _guil_reach(p)
    for i in range(n):
        x0 = i * _guil_step(p)
        pts = [(x0 + h + p.sv / 2, a + h), (x0 + p.sv / 2, a), (x0 + h + p.sv / 2, a - h)]
        if mirror:
            pts = [(W - x, y) for x, y in pts]
        g.stroke(*pts, start='v', end='v')


@punct('guilsinglleft', '‹', 4, 1, width=_guil_width(1))
def guilsinglleft(g):
    _guil(g, 1, False)


@punct('guilsinglright', '›', 4, 1, width=_guil_width(1))
def guilsinglright(g):
    _guil(g, 1, True)


@punct('guillemotleft', '«', 7, 2, width=_guil_width(2))
def guillemotleft(g):
    _guil(g, 2, False)


@punct('guillemotright', '»', 7, 2, width=_guil_width(2))
def guillemotright(g):
    _guil(g, 2, True)


@punct('exclamdown', '¡', 2, width=dot_w())
def exclamdown(g):
    f = Frame(g, 2, 'lower')
    p = g.p
    top = p.xh
    dot(g, f.X(1), top - p.dot())
    g.stroke((f.X(1), top - p.dot() - dot_gap(p)), (f.X(1), top - p.cap))
    g.clip = (0, top - p.cap, g.W, top)


@punct('questiondown', '¿', 9, 2)
def questiondown(g):
    from shapely.affinity import rotate
    question(g)
    # turned half round about the x-height's centre line
    p = g.p
    shift = p.xh - p.cap
    g.strokes = [type(s)(tuple(type(n)(g.W - n.x, p.cap - n.y + shift, n.bowl, n.w) for n in s.nodes),
                         s.closed, s.start, s.end) for s in g.strokes]
    g.clip = (0, shift, g.W, p.xh)


@punct('plusminus', '±', 8, 1)
def plusminus(g):
    p, W = g.p, g.W
    a, h = axis(p) + p.m, W / 2 - p.sv / 4
    g.stroke((0, a), (W, a))
    g.stroke((W / 2, a - h), (W / 2, a + h))
    g.stroke((0, a - h - g.sh), (W, a - h - g.sh))


@punct('logicalnot', '¬', 8, 1)
def logicalnot(g):
    p, W = g.p, g.W
    a = axis(p)
    g.stroke((0, a), (W - p.sv / 2, a), (W - p.sv / 2, a - 2.5 * p.m))


def _lessequal(g, mirror):
    """The < chevron itself over a bar, the equal sign's white between,
    the pair centred on the axis."""
    p, W = g.p, g.W
    x_tip, reach = chevron_geometry(g)
    v = reach / 2
    from ..draw import _thickness
    kv = _thickness(p, g.sh)((2, 1)) / (2 * math.cos(SLOPE))     # the arms' ink past their centreline ends, vertically
    white = eq_white(g)
    a = axis(p) + (white + g.sh) / 2                         # the chevron's centre
    T = (lambda x, y: (W - x, y)) if mirror else (lambda x, y: (x, y))
    g.stroke(T(W, a + v), T(x_tip, a), T(W, a - v), start='v', end='v')
    yb = a - v - kv - white - g.sh / 2
    g.stroke((0, yb), (W, yb))


@punct('lessequal', '\u2264', 8, 1)
def lessequal(g):
    _lessequal(g, False)


@punct('greaterequal', '\u2265', 8, 1)
def greaterequal(g):
    _lessequal(g, True)


@punct('notequal', '≠', 8, 1)
def notequal(g):
    equal(g)
    p, W = g.p, g.W
    a = axis(p)
    w = p.ss / STEEP[1]
    g.stroke((W / 2 - 2 * p.m, a - 4 * p.m), (W / 2 + 2 * p.m, a + 4 * p.m), start='h', end='h')


def dagger_bar(p):
    """Where a dagger's bar crosses: three and a half modules down, or lower
    where the stem above it would be shorter than two stems thick."""
    return p.cap - max(3.5 * p.m, 2.2 * p.sv)


@punct('dagger', '†', 6, 1, width=growing_width(6, 1, 2.0))
def dagger(g):
    p, W = g.p, g.W
    g.stroke((W / 2, -p.desc + p.m), (W / 2, p.cap))
    g.stroke((0, dagger_bar(p)), (W, dagger_bar(p)))
    g.clip = (0, -p.desc, W, p.cap)


@punct('minute', '′', 3, 1)
def minute(g):
    p, W = g.p, g.W
    w = p.ss / STEEP[1]
    g.stroke((w / 2, p.cap - 4 * p.m), (w / 2 + 2 * p.m, p.cap), start='h', end='h')


@punct('second', '″', 6, 2)
def second(g):
    p, W = g.p, g.W
    w = p.ss / STEEP[1]
    for x0 in (w / 2, w / 2 + 2.2 * p.m + w / 2):
        g.stroke((x0, p.cap - 4 * p.m), (x0 + 2 * p.m, p.cap), start='h', end='h')
