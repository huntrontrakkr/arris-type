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

from ..draw import B, Squint, glyph
from ..params import SQRT2, white_floor
from .figures import bay_stack, beak_depth, heaviness
from .letterframe import STEEP, Frame, growing_width, kept_width, least_white, plain_width as letter_width, white_scale


OPERATOR = kept_width(8, 1)     # the plus's body, and every operator's drawn in it: bars, which keep their share of the line


def punct(name, char, wm, stems=1, width=None, sides=1.0):
    # (no stems: bars alone, a dash's, which keep their share of the line as the operators do: letterframe.kept_width)
    return glyph(name, char, width or (letter_width(wm, stems) if stems else kept_width(wm, 0)), kind=('punct', sides))


# The dashes, in modules: the lengths other families give theirs. At six, nine and sixteen modules the
# hyphen stood 0.81 of the H's advance, the en dash 1.10 and the em dash 1.77, and the underscore, nine
# modules too, 1.10: of sixty families the en dash, the em dash and the underscore were longer than any
# but two or three, and the hyphen longer than all but three (their middle ones 0.60, 0.79, 1.23 and 0.75;
# tools/width_survey.py's families, 2026-11-12). Arris Mono keeps the lengths its cell is drawn to.
HYPHEN, EN_DASH, EM_DASH, LOW_LINE = 4, 6, 10.5, 5.5


def dash(wm: float, mono: float):
    """A dash's body: ``wm`` modules, and ``mono`` in Arris Mono's cell."""
    own, cell = kept_width(wm, 0), kept_width(mono, 0)
    return lambda p: cell(p) if p.mono else own(p)


def stem_w(n=1):
    return lambda p: n * p.sv


def dot_w(n=1):
    return lambda p: n * p.dot()


def dot(g, x, y0):
    """A square dot standing on y0, centred on x (Params.dot)."""
    s = g.p.dot()
    g.stroke((x, y0, s), (x, y0 + s))


def dot_gap(p):
    """White between a dot and a stroke above it: 0.8 of a stem, half a
    module at the least, and from the cut's Regular on the Regular's
    (draw.held_at), as the white between a letter's parts gives way to the
    stems past it. At 0.8 of the weight's own, 160 units at Black, the
    question mark's dot came up to its bowl from ExtraBold and its stem was
    gone, the stroke turning down into its own end; faces of this kind
    leave a third of a stem over the dot at Black (Tomorrow, Barlow, Kanit,
    Exo 2, Oxanium, Inter: 0.3 to 0.36)."""
    from ..draw import held_at
    return max(0.8 * min(p.sv, held_at(p).sv), 0.5 * p.m, DOT_WHITE * p.sv)


DOT_WHITE = 0.55    # stems: the least white over a dot, a tenth over the half stroke the white rule reads as white
                    # (draw.WHITE_OPEN): under it the exclamation mark had none and was lightened to 0.8 from Bold
QUESTION_NECK = 0.25    # stems: the least of the question mark's stem showing under its bowl's return


def question_return(g, f, bay=True):
    """Where the question mark's bowl returns (the centre line of its
    lower bar): on the frame's row 6, or higher where the dot and the white
    over it come up under it, so a quarter of a stem of the stem shows
    below it (QUESTION_NECK). At the weight's own white over the dot, its
    stem was gone from ExtraBold, the stroke turned down into its own end,
    and at Black it was another drawing; the bars give way for the bowl
    above as the S's do for its bays (figures.bay_stack, which reads where
    the stem would have it: ``bay`` False). Where they can give no more
    (the italic at Black, whose beak is the longer), it rises no further
    than leaves the beak its white over it, and the stem gives the rest:
    risen on, the beak's end and the return's corner met at a point."""
    from .figures import BAY_WHITE
    p = g.p
    y = max(f.Y(6), p.dot() + dot_gap(p) + QUESTION_NECK * p.sv + g.sh / 2)
    least = BAY_WHITE * white_floor(p.m, p.sv, p.optical)
    lead = getattr(g, 'lead', None)
    if bay and lead is not None:
        # led in (a ligature's lead-in bar in place of the beak: `#?`'s top bar of #), the bowl keeps the
        # beak's white under the lead's underside, the return coming down for it toward the dot, its stem
        # the less: risen to its own row, it met the # bar from Bold in the italic and the bowl shut
        y_lead, th = question_lead(g, f)
        return max(p.dot() + dot_gap(p) + g.sh / 2, min(y, y_lead - th / 2 - least - g.sh / 2))
    if bay:
        y = max(f.Y(6), min(y, f.Y(11) - beak_depth(p, g.sh) - least))
    return y


def question_lead(g, f):
    """(height, thickness) of the bar a question mark is led in on (a
    ligature's: g.lead's last point): a point of its own height, or None
    for the height its beak ends at, the bar's underside where the beak's
    end stands (`??`: the second ?'s beak leaves from the first's side)."""
    p = g.p
    pt = g.lead[-1]
    th = pt[2] if len(pt) > 2 else g.sh
    y = pt[1] if pt[1] is not None else p.cap - beak_depth(p, g.sh) + th / 2
    return y, th


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


def comma_sides(p):
    """A comma's sides: its head stands where a period's dot does, and its
    tail, half a dot to the left of the head, hangs into the white before
    it. Until 1.017 the side was measured from the tail's tip, so after
    any letter a comma's head stood half a dot further off than a period
    (a quarter of the white between two stems at Regular, 0.7 of it at
    Black: T and a comma 2.3 gaps apart for a period's 1.7, where faces of
    this kind set the two alike)."""
    from ..font import PUNCT_SIDE, light
    side = PUNCT_SIDE * light(p)
    return (side - 0.5 * p.dot(), side)


@glyph('comma', ',', dot_w(1.5), kind=('punct', comma_sides))
def comma(g):
    f = Frame(g, 3, 'lower')
    _comma(g, f, g.W - g.p.dot() / 2, g.p.dot())


@punct('colon', ':', 2, width=dot_w())
def colon(g):
    f = Frame(g, 2, 'lower')
    dot(g, f.X(1), 0)
    dot(g, f.X(1), g.p.xh - g.p.dot())


@glyph('semicolon', ';', dot_w(1.5), kind=('punct', comma_sides))
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
    # (from ExtraBold the stem the bowl returns into stands under the beak: the beak keeps its white
    # off the return, its bars giving as the S's do, figures.bay_stack; 0.23 of a stem in the italic at Black)
    f = bay_stack(g, lambda: Frame(g, 9, 'cap'), [(6, 11)], lower=lambda f: question_return(g, f, bay=False))
    p = g.p
    d = beak_depth(p, g.sh)
    # The 2's bowl, its right side turning back into a short stem at the centre.
    xs = f.X(4)
    yr = question_return(g, f)
    # a lead-in (the `#?` ligature: the top bar of #, in this frame, as (x, y,
    # thickness)): the bar runs on to the bowl's left side, which rises from it
    lead = getattr(g, 'lead', None)
    if lead is not None:
        y_lead, _ = question_lead(g, f)
        lead = [(q[0], y_lead, *q[2:]) if q[1] is None else q for q in lead]
    start = [(f.X(1), p.cap - d)] if lead is None else [*lead, (f.X(1), lead[-1][1])]
    # (where the stem is left none, the italic at Black, it ends flush with the return's underside: ended in
    # the return, a few units short of it, its end's breaks cut a nub out of the return's corner)
    g.stroke(*start, B(*f.P(1, 11)), B(*f.P(8, 11)), B(f.X(8), yr), (xs, yr),
             (xs, min(p.dot() + dot_gap(p), yr - g.sh / 2)))
    dot(g, xs, 0)


@punct('hyphen', '-', 6, 0, width=dash(HYPHEN, 6))
def hyphen(g):
    f = Frame(g, 6, 'lower')
    # in the monospaced cut the hyphen is a minus for code: on the math axis,
    # in line with + = < > and the arrows it ligates into
    y = axis(g.p) if g.p.mono else f.Y(5)
    g.stroke((0, y), (g.W, y))


@punct('endash', '–', 9, 0, width=dash(EN_DASH, 9))
def endash(g):
    f = Frame(g, 9, 'lower')
    g.stroke((0, f.Y(5)), (g.W, f.Y(5)))


@punct('emdash', '—', 16, 0,
       width=lambda p: min(letter_width(16, 0)(p), p.fig_adv) if p.mono else kept_width(EM_DASH, 0)(p))
def emdash(g):
    """A bar ten and a half modules long (EM_DASH); in the monospaced cut,
    the cell's full advance, as a code face's em dash runs (it shortens,
    never thins)."""
    f = Frame(g, 16, 'lower')
    g.stroke((0, f.Y(5)), (g.W, f.Y(5)))


@punct('underscore', '_', 9, 0, width=dash(LOW_LINE, 9))
def underscore(g):
    f = Frame(g, 9, 'lower')
    g.stroke((0, f.Y(-2)), (g.W, f.Y(-2)))


def tick(p):
    """How long a straight quote's tick is: a third of the cap height, or
    two dots where those are more (from Bold). Until 1.017 two dots at
    every weight, a quarter of the cap height at Regular and less below it:
    faces of this kind draw them 0.31 to 0.36 of it (Chakra Petch, Oxanium,
    Exo 2, Rajdhani, Tomorrow), and the pair read as two apostrophes."""
    return max(2 * p.dot(), p.cap / 3)


def tick_gap(p):
    """The white between the double quote's ticks: a module and a half of
    the weight's white, never under the least (it was two modules, a tick
    and a half at Regular: those faces' ticks stand about one apart)."""
    return max(1.5 * p.m * white_scale(p), least_white(p))


@punct('quotesingle', "'", 2, width=stem_w())
def quotesingle(g):
    f = Frame(g, 2, 'lower', top=g.p.cap)
    p = g.p
    g.stroke((f.X(1), p.cap - tick(p)), (f.X(1), p.cap))


@punct('quotedbl', '"', 6, 2, width=lambda p: 2 * p.sv + tick_gap(p))
def quotedbl(g):
    p = g.p
    g.clip = (0, 0, g.W, p.cap)
    for x in (p.sv / 2, g.W - p.sv / 2):
        g.stroke((x, p.cap - tick(p)), (x, p.cap))


QUOTE_GAIN = 0.5    # of what the dot gains past the Regular, the share a quotation mark's takes


def quote_dot(p):
    """A quotation mark's dot: the weight's to the Regular, and past it the
    Regular's and half of what the weight's has gained, as an accent's
    strokes (marks.MARK_GAIN). At the weight's own dot the marks grew with
    the stem and “ stood 1.16 of the H's ink wide at Black with an advance
    1.12 of the H's, where twenty-one families' heaviest stand 0.77 and
    0.72 (0.91 and 0.86 at the outside): 0.62 at Regular, 0.84 at Black."""
    from ..draw import held_at
    q = held_at(p)
    return p.dot() if q is p else q.dot() + QUOTE_GAIN * (p.dot() - q.dot())


def quote_w(n):
    return lambda p: n * quote_dot(p)


@punct('quoteright', '’', 3, width=quote_w(1.5))
def quoteright(g):
    f = Frame(g, 3, 'lower', top=g.p.cap)
    s = quote_dot(g.p)
    _comma(g, f, g.W - s / 2, g.p.cap, s=s)


@punct('quoteleft', '‘', 3, width=quote_w(1.5))
def quoteleft(g):
    f = Frame(g, 3, 'lower', top=g.p.cap)
    p = g.p
    s = quote_dot(p)
    # the comma turned half round: tail up-right, dot below
    x = s / 2
    y_bot = p.cap - 2.25 * s
    y_turn = y_bot + 1.5 * s
    g.stroke((x, y_bot, s), (x, y_turn, s * p.sd / p.sv), (x + 0.75 * s, y_turn + 0.75 * s), end='h')


@punct('quotedblright', '”', 7, width=quote_w(3.5))
def quotedblright(g):
    f = Frame(g, 7, 'lower', top=g.p.cap)
    s = quote_dot(g.p)
    for x in (s, g.W - s / 2):
        _comma(g, f, x, g.p.cap, s=s)


@punct('quotedblleft', '“', 7, width=quote_w(3.5))
def quotedblleft(g):
    f = Frame(g, 7, 'lower', top=g.p.cap)
    p = g.p
    s = quote_dot(p)
    for x in (s / 2, s / 2 + 2 * s):
        y_bot = p.cap - 2.25 * s
        y_turn = y_bot + 1.5 * s
        g.stroke((x, y_bot, s), (x, y_turn, s * p.sd / p.sv), (x + 0.75 * s, y_turn + 0.75 * s), end='h')


@glyph('quotesinglbase', '‚', quote_w(1.5), kind=('punct', comma_sides))
def quotesinglbase(g):
    f = Frame(g, 3, 'lower')
    s = quote_dot(g.p)
    _comma(g, f, g.W - s / 2, s, s=s)


@glyph('quotedblbase', '„', quote_w(3.5), kind=('punct', comma_sides))
def quotedblbase(g):
    f = Frame(g, 7, 'lower')
    s = quote_dot(g.p)
    for x in (s, g.W - s / 2):
        _comma(g, f, x, s, s=s)


def _paren(g, f, mirror=False):
    p = g.p
    W = g.W
    k = p.sd / SQRT2
    top, bot = p.cap + 0.5 * p.m, -p.under + 0.5 * p.m
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


BRACKET_ARM = 0.55      # of a stem: the least a bracket's (and a brace's) arm stands out past its spine


def bracket_width(p):
    """Four modules and a stem, and at heavy weights arms that stand out
    BRACKET_ARM of a stem past the spine at least (shorter, the arm's end
    chamfer and its inside corner's nearly meet). At a stem and a half
    from the spine's centre the bracket stood 0.66 of the H's ink wide at
    Black, where twenty-one families' heaviest stand 0.45 (0.54 at the
    outside)."""
    return max(letter_width(4, 1)(p), (1 + BRACKET_ARM) * p.sv)


def _bracket(g, mirror=False):
    p = g.p
    W = g.W
    top, bot = p.cap + 0.5 * p.m, -p.under + 0.5 * p.m
    T = (lambda x, y: (W - x, y)) if mirror else (lambda x, y: (x, y))
    yt, yb = top - g.sh / 2, bot + g.sh / 2
    g.stroke(T(W, yt), T(p.sv / 2, yt), T(p.sv / 2, yb), T(W, yb))
    g.clip = (0, bot, W, top)


@punct('bracketleft', '[', 4, 1, width=bracket_width)
def bracketleft(g):
    _bracket(g)


@punct('bracketright', ']', 4, 1, width=bracket_width)
def bracketright(g):
    _bracket(g, mirror=True)


BEAK = 1.0        # the brace's point: its centreline depth, in stems (a module and a half at least)


def _brace_parts(p, sh):
    """(arm, point depth, point ink) of the brace: arms a stem and a half
    from the spine's centre (two and a half modules at least, so a light
    brace keeps them), a point a stem deep on the shallow 2:1, whose ink
    runs on past it by its stroke's own reach."""
    from ..draw import _thickness, held_at
    t = _thickness(p, sh)((2, 1))
    q = held_at(p)
    if q is p:
        return max(1.5 * p.sv, 2.5 * p.m), max(BEAK * p.sv, 1.5 * p.m), t / (2 * math.sin(SLOPE))
    # past the Regular the arm stands out as the bracket's does and the point is as deep as the Regular's
    # and half of what the stem has gained: at a stem and a half and a stem they grew with the stem, and
    # the brace stood 1.04 of the H's ink wide at Black (twenty-one families' heaviest 0.56, 0.71 at
    # the outside)
    return (max((0.5 + BRACKET_ARM) * p.sv, 2.5 * p.m), max(BEAK * (q.sv + QUOTE_GAIN * (p.sv - q.sv)), 1.5 * p.m),
            t / (2 * math.sin(SLOPE)))


def _brace_cut(p, sh):
    """How much of the brace's point is cut off flat: what stands out past
    the spine further than the Regular's point does (its stroke's reach
    grows with the stroke, and at Black the point alone was a third of the
    sign). Just past the Regular, from the Regular's point as it stands:
    the corner rule cuts its tip back by its break on the 2:1 (a face as
    tall as the cut leaves here), and that allowance fades out over half a
    stem's gain, after which the point is cut from its full reach as it
    was. Cut from the full reach at once, the cut began a unit past the
    Regular at nothing: the tip stood 20 units further out, near sharp, and
    the brace a fifth of a stem wider at 401 than at 400."""
    from ..draw import held_at
    q = held_at(p)
    if q is p:
        return 0.0
    _, d, tip = _brace_parts(p, sh)
    _, d0, tip0 = _brace_parts(q, sh * q.sh / p.sh)
    fade = max(0.0, 1.0 - (p.sv - q.sv) / (0.5 * q.sv))
    return max(0.0, (d + tip - p.sv / 2) - (d0 + tip0 - q.sv / 2 - fade * q.c * math.cos(SLOPE)))


def brace_width(p):
    hook, d, tip = _brace_parts(p, p.sh)
    w = hook + d + tip - _brace_cut(p, p.sh)
    return min(w, p.fig_w) if p.mono else w


def _brace(g, mirror=False):
    """Flat arms that leave the spine with a curl (half their length on the
    shallow 2:1), on a spine that breaks at the middle into a point on the
    shallow 2:1: a brace, told from ( by its flat arms, from [ by its curl
    and point, from < by its spine."""
    p = g.p
    W = g.W
    top, bot = p.cap + 0.5 * p.m, -p.under + 0.5 * p.m
    mid = (top + bot) / 2
    hook, d, tip = _brace_parts(p, g.sh)
    xs = max(W - hook, tip + d - _brace_cut(p, g.sh))       # the spine (the arm gives way in a narrow cell)
    xp = xs - d                                             # the point
    T = (lambda x, y: (W - x, y)) if mirror else (lambda x, y: (x, y))
    # the arms leave the spine on the shallow 2:1 for half their length, then
    # run flat: a curl at each end, and still a brace's arm (not the
    # parenthesis's diagonal)
    yt, yb = top - g.sh / 2, bot + g.sh / 2
    L = W - xs
    r = L / 4
    g.stroke(T(W, yt), T(xs + L / 2, yt), T(xs, yt - r), T(xs, mid + d / 2), T(xp, mid),
             T(xs, mid - d / 2), T(xs, yb + r), T(xs + L / 2, yb), T(W, yb))
    g.clip = (0, bot, W, top)


@punct('braceleft', '{', 6, 1, width=brace_width)
def braceleft(g):
    _brace(g)


@punct('braceright', '}', 6, 1, width=brace_width)
def braceright(g):
    _brace(g, mirror=True)


def slash_lean(p, mirror=False):
    """A slash's run over its rise: a half, the steep 2:1. In the italic of
    the monospaced cuts the forward slash leans the slant less, so that
    slanted it leans as the upright's does. The slant leans a forward
    slash again: at its own lean and the slant's it was 700 units wide in
    a cell of 600, and a sign that does not fit its cell is drawn smaller
    until it does (symkit.mono_fitted): Arris Mono Italic's slash stood
    0.8 of its height with half its ink, Mono Narrow Italic's 0.7 with a
    third, and with it the // /* */ of a comment. (The backslash leans
    against the slant and narrows.)"""
    if p.mono and p.slant and not mirror:
        return 0.5 - p.slant
    return 0.5


def _slash(g, mirror=False):
    p = g.p
    top, bot = p.cap + 0.5 * p.m, -p.under + 0.5 * p.m
    w = p.ss / STEEP[1]
    W = g.W
    k = slash_lean(p, mirror)
    x_at = lambda y: w / 2 + (y - bot) * k
    pts = [(x_at(bot), bot), (x_at(top), top)]
    if k != 0.5:
        # as wide across as the 2:1 stroke it will lean as: the stroke's own thickness at this lean is a
        # little more, and a few units over the cell the sign was fitted smaller all the same
        pts[0] += (w / math.hypot(1.0, k),)
    if mirror:
        pts = [(W - x, y) for x, y in pts]
    g.stroke(*pts, start='h', end='h')
    g.clip = (0, bot, W, top)


def slash_width(p, mirror=False):
    top, bot = p.cap + 0.5 * p.m, -p.under + 0.5 * p.m
    return p.ss / STEEP[1] + (top - bot) * slash_lean(p, mirror)


@punct('slash', '/', 9, width=slash_width)
def slash(g):
    _slash(g)


@punct('backslash', '\\', 9, width=lambda p: slash_width(p, True))
def backslash(g):
    _slash(g, mirror=True)


@punct('bar', '|', 2, width=stem_w())
def bar(g):
    p = g.p
    top, bot = p.cap + 0.5 * p.m, -p.under + 0.5 * p.m
    g.stroke((p.sv / 2, bot), (p.sv / 2, top))
    g.clip = (0, bot, g.W, top)


# --- Mathematical: on the axis at half the cap height ----------------------

def axis(p):
    return p.cap / 2


@punct('plus', '+', 8, 1, width=OPERATOR)
def plus(g):
    p, W = g.p, g.W
    a, h = axis(p), W / 2
    g.stroke((0, a), (W, a))
    g.stroke((h, a - h), (h, a + h))
    g.clip = (0, a - h, W, a + h)


@punct('minus', '−', 8, 1, width=OPERATOR)
def minus(g):
    p, W = g.p, g.W
    g.stroke((0, axis(p)), (W, axis(p)))


EQ_WHITE = 1.6      # of a bar: the white between the bars of =, to the Regular
EQ_GIVES = 0.34     # past it, what that white gives of every unit the stem gains
EQ_LEAST = 0.5      # of a bar: the least it is


def eq_white(g):
    """White between the bars of = (and of every sign stacked from them):
    1.6 bars, two modules at the lightest weights, so the pair never clogs
    into one stroke at text sizes. Past the Regular it is the Regular's,
    less a third of what the stem has gained (EQ_GIVES), half a bar at
    least: 126 units at Regular, 89 at Black.

    In 397 fonts of some seventy families, read by their boldness (the
    H's stem over the cap height), the white stands 1.72 bars at Arris
    Regular's boldness, 1.04 at its SemiBold's, 0.86 at its Bold's and
    0.62 at its Black's: in cap heights 0.18 falling to 0.12, a third of a
    unit for every unit of stem. Held at 1.6 bars at every weight it grew
    with the bars, to 272 units at Black: the equals stood from 0.07 to
    0.93 of the cap height there (thirty families' heaviest: 0.11 to 0.81
    at the outside) and the ≈ and the ≡ ran past the capitals both ways."""
    from ..draw import held_at
    p = g.p
    q = held_at(p)
    if q is p:
        return max(EQ_WHITE * g.sh, 2 * p.m)
    reg = max(EQ_WHITE * g.sh * q.sh / p.sh, 2 * p.m)       # with this sign's own thinning, if it has any
    return max(reg - EQ_GIVES * (p.sv - q.sv), EQ_LEAST * g.sh)


def eq_offset(g):
    """Half the distance between the bars of =, centre to centre."""
    return (g.sh + eq_white(g)) / 2


@punct('equal', '=', 8, 1, width=OPERATOR)
def equal(g):
    p, W = g.p, g.W
    off = eq_offset(g)
    for y in (axis(p) - off, axis(p) + off):
        g.stroke((0, y), (W, y))


MULTIPLY = 0.85     # the multiplication sign across, of the plus's


@punct('multiply', '×', 8, 1, width=OPERATOR)
def multiply(g):
    p, W = g.p, g.W
    # its arms MULTIPLY of the plus's square across: corner to corner of the whole square they are
    # root two as long as the plus's, and the sign stood 0.95 of the H's ink wide at Black with 0.69 of
    # its ink (twenty-one families' heaviest 0.78 and 0.44, 0.93 and 0.55 at the outside)
    a, h = axis(p), MULTIPLY * W / 2
    x0, x1 = W / 2 - h, W / 2 + h
    g.stroke((x0, a - h), (x1, a + h), start='v', end='v')
    g.stroke((x0, a + h), (x1, a - h), start='v', end='v')
    g.clip = (x0, a - h, x1, a + h)


DIVIDE_WHITE = 0.45     # of a bar: the least white between the division sign's bar and a dot


@punct('divide', '÷', 8, 1, width=OPERATOR)
def divide(g):
    p, W = g.p, g.W
    a = axis(p)
    g.stroke((0, a), (W, a))
    # as tall as the plus: its dots' outer edges where the plus's arms end,
    # the dots the weight's, or what leaves DIVIDE_WHITE of a bar between a
    # dot and the bar. (The white was fixed and the dots the weight's: the
    # sign stood 0.24 to 0.76 of the cap height at Regular, where thirty
    # families' stands 0.10 to 0.80, and -0.06 to 1.06 at Black, past
    # every one of them.)
    s = min(p.dot(), (W - g.sh) / 2 - DIVIDE_WHITE * g.sh)
    for y in (a + W / 2 - s, a - W / 2):
        g.lay((W / 2, y, s), (W / 2, y + s), c=p.c * s / p.dot())      # a smaller dot's corners broken in its own measure


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


@punct('less', '<', 8, 1, width=OPERATOR)
def less(g):
    _chevron(g)


@punct('greater', '>', 8, 1, width=OPERATOR)
def greater(g):
    _chevron(g, mirror=True)


# --- ASCII symbols ---------------------------------------------------------

HASH_PARTS = 6.0    # the number sign up its height, in strokes: two bars, a counter of one, two ends of one and a half


@punct('numbersign', '#', 10, 2, width=growing_width(10, 2, 2.0))
def numbersign(g):
    """Two bars each way, never closer than a stroke, their ends never
    shorter than a stroke and a half. Where its height does not hold that
    at the weight's strokes (HASH_PARTS of them: from Bold) the sign's
    strokes thin together until it does, 0.91 of the weight's at Bold and
    0.72 at Black, as faces of this kind draw it (Chakra Petch Bold,
    Oxanium ExtraBold, Rajdhani Bold: 0.8 to 0.9 of a stem).

    The white between the bars gives to the ends first, down to a stroke;
    across, where the body holds what it holds, the same.

    Until 1.017 only the square between the bars was kept, at the full
    strokes: at Black the ends stood 100 units past bars 149 thick, two
    thirds of a stroke, and the sign was a cross with a hole in it."""
    f = Frame(g, 10, 'cap')
    p, W = g.p, g.W
    y0, y1 = f.Y(0.5), f.Y(11.5)
    k = min(1.0, (y1 - y0) / (HASH_PARTS * g.sh))
    tv, th = k * p.sv, k * g.sh
    gx = max(min(f.X(7) - f.X(3) - tv, W - 5 * tv), tv)     # white between the verticals
    gy = max(min(f.Y(8) - f.Y(4) - th, y1 - y0 - 5 * th), th)       # and between the horizontals
    for x in (W / 2 - (gx + tv) / 2, W / 2 + (gx + tv) / 2):
        g.stroke((x, y0, tv), (x, y1))
    for y in (p.cap / 2 - (gy + th) / 2, p.cap / 2 + (gy + th) / 2):
        g.stroke((0, y, th), (W, y))


def dollar_stem(p, sh, through):
    """(bottom, top) of the dollar's stem as runs: through the S while the
    counters it splits read when a reader squints; at the weights where
    they would close to slivers beside it (draw.Squint moves the dollar's
    'stem' to 0), only above and below the S, as heavy faces draw it."""
    top, bot = p.cap + 1.5 * p.m, -1.5 * p.m
    if through:
        return [(bot, top)]
    return [(bot, sh / 2), (p.cap - sh / 2, top)]


@glyph('dollar', '$', letter_width(9, 2), kind=('punct', 1.0), squint=(Squint('stem', lambda p: 0.0, form=True),))
def dollar(g):
    from .caps import S
    S(g)
    p = g.p
    from ..draw import held_c
    runs = dollar_stem(p, g.sh, g.free('stem', 1.0) >= 0.5)
    t = g.held((0.0, 1.0))                                  # its stroke, added: the Regular's from there on
    for y0, y1 in runs:
        g.lay((g.W / 2, y0, t), (g.W / 2, y1), c=held_c(p))
    g.clip = (0, runs[0][0], g.W, runs[-1][1])


def _ring(g, x0, y0, x1, y1, w=None, leg=None):
    """A small closed octagon, centreline box (x0, y0)-(x1, y1)."""
    p = g.p
    leg = p.leg * 0.6 if leg is None else leg
    pts = [B(x0, y0, leg, w), B(x1, y0, leg, w), B(x1, y1, leg, w), B(x0, y1, leg, w)]
    g.stroke(*pts, closed=True)


PCT_RING = 5.0      # the percent's rings across, in modules (up, half the cap height)


def pct_params(p):
    """The percent's own strokes: the small figures' (0.8 of the weight's,
    0.68 at Black: features.small), corners and edge breaks with them."""
    k = 0.8 - 0.12 * heaviness(p)
    return p.with_(sv=k * p.sv, sh=k * p.sh, sd=k * p.sd, ss=k * p.ss, c=k * p.c)


def pct(p):
    """The percent's parts: (its rings' stems, their bars, the slash's
    thickness, a ring's width, its height, the white it keeps). The sign is
    drawn in the small figures' strokes (pct_params), its rings half the
    cap height and five modules across, or what a counter of the least
    white needs; each stands that white clear of the slash. In the
    monospaced cell the rings run into the slash, as they did everywhere
    until 1.017."""
    if p.mono:
        return p.sv, p.sh, p.ss, 4.5 * p.m + p.sv, 5.0 * p.m + p.sv, p.m
    q = pct_params(p)
    white = max(p.m, 0.6 * q.sv)
    return q.sv, q.sh, q.ss, max(PCT_RING * p.m, 2 * q.sv + white), p.cap / 2, white


def pct_width(p):
    """The percent's body: its two rings, the slash between them, and the
    white from each ring's cut corner to the slash."""
    if p.mono:
        return letter_width(11, 3)(p)
    q = pct_params(p)
    vs, hs, ss, rw, _, white = pct(p)
    lo = 0.6 * p.leg + (vs + hs) / 2 - q.sd / SQRT2         # the corner's outer flank
    reach = max(white * math.sqrt(5) / 2 - lo / 2, 0.25 * white)     # ring to slash on the ring's foot line
    return 2 * (rw + reach) + ss / STEEP[1]


def pct_ring(g, x0, y0):
    """One of the percent's rings, its box's lower left corner at (x0, y0),
    in the sign's own strokes."""
    p = g.p
    vs, hs, _, rw, rh, _ = pct(p)
    if p.mono:
        _ring(g, x0 + vs / 2, y0 + g.sh / 2, x0 + rw - vs / 2, y0 + rh - g.sh / 2)
        return
    from ..draw import Glyph
    ring = Glyph(pct_params(p), W=g.W)
    _ring(ring, x0 + vs / 2, y0 + hs / 2, x0 + rw - vs / 2, y0 + rh - hs / 2, leg=0.6 * p.leg)
    g.add_glyph(ring)


def pct_rings_after(g, sub, n, gap):
    """n more of the percent's rings in g, after a % drawn as ``sub`` (at
    the glyph's left, its body sub.W), ``gap`` apart: drawn at the measures
    the % was drawn with. In the monospaced cell the % is fitted to its own
    cell, its rings drawn smaller, and rings drawn at the sign's own
    measures beside it stood larger than its own (‰ ‱ in Arris Mono Italic
    at every weight, in Mono Narrow from 500)."""
    from ..draw import Glyph
    q = sub.p
    rw = pct(q)[3]
    rings = Glyph(q, W=g.W)
    for i in range(n):
        pct_ring(rings, sub.W + gap + i * (rw + gap), 0)
    g.add_glyph(rings)


def percent_part(g):
    """The % as drawn into ‰ and ‱: at the glyph's own measures, never
    fitted to a cell of its own. The sign is fitted to the cell as a whole;
    drawn as a glyph, the % inside it was fitted again, to its own cell, at
    some of the measures the fit tries and not at others, and Arris Mono
    Narrow's ‰ stood a ninth taller at 500 than at 490 (‱ a fifth wider)."""
    from ..draw import Glyph
    sub = Glyph(g.p, name='percent', W=pct_width(g.p))
    percent(sub)
    return sub


@punct('percent', '%', 11, 3, width=pct_width)
def percent(g):
    """Two rings and the 2:1 slash between them, each ring clear of it by
    the least white (pct). Until 1.017 the rings were four and a half
    modules of counter in the full stem, in a body their two widths did not
    fit: each ran into the slash at every weight (50% read as 5096), and at
    Black the sign was one mass, its counters 0.66 of a stem. Faces of this
    kind draw the rings apart and lighter than the letters (Chakra Petch,
    Oxanium, Exo 2, Rajdhani: 0.2 to 0.8 of a stem between ring and slash)."""
    p, W, H = g.p, g.W, g.p.cap
    _, _, _, rw, rh, _ = pct(p)
    pct_ring(g, 0, H - rh)
    pct_ring(g, W - rw, 0)
    if p.mono:
        w = p.ss / STEEP[1]
        x_at = lambda y: (W - w) / 2 - H / 4 + w / 2 + y / 2
        g.stroke((x_at(0), 0), (x_at(H), H), start='h', end='h')
        return
    from ..draw import Glyph
    slash = Glyph(pct_params(p), W=W)
    slash.stroke((W / 2 - H / 4, 0), (W / 2 + H / 4, H), start='h', end='h')
    g.add_glyph(slash)
    g.clip = (0, 0, W, H)


@punct('ampersand', '&', 10, 2)
def ampersand(g):
    f = Frame(g, 10, 'cap')
    p, W, H, k = g.p, g.W, g.p.cap, p_k(g)
    # the leg's line: x + y = a, down to the baseline at the right
    a = W + p.c - k
    # upper loop: a small octagon, its lower right corner large (the 8's);
    # its lower left corner cut exactly on the leg's line, so the leg runs
    # on out of the loop's side through that chamfer (no second diagonal
    # beside it, nothing poking out of the loop)
    x2, yl = f.X(2), f.Y(6.5)
    cut = a - x2 - yl
    big = p.leg + p.m
    g.stroke(B(x2, yl, cut), B(*f.P(6, 6.5), big), B(*f.P(6, 11)), B(*f.P(2, 11)), closed=True)
    # the leg: from the loop's side, along the chamfer, down to the baseline
    g.stroke((x2, yl + cut), (a, 0), start='v', end='h')
    # lower bowl: off the loop's side where the leg leaves it, out at 45
    # degrees, round the bottom, open at the right
    y0 = yl + cut
    xb = f.X(1)
    g.stroke((x2, y0), B(xb, y0 - (x2 - xb), p.m / 2), B(xb, f.Y(1)), (a - f.Y(1), f.Y(1)), start='v')
    # the arm, up from the leg's centreline at the right
    g.stroke((f.X(8), a - f.X(8)), f.P(8, 5.5))


def p_k(g):
    return g.p.sd / SQRT2


def spread(at, least):
    """``at``, a row of strokes' centres, moved as little as leaves every
    two neighbours ``least`` apart, the first and the last where they
    stand: a gap that is short takes what it lacks from the ones that have
    more, each by its share of what they have over; with no more room than
    that for all of them they stand evenly. (Where one gap ran short the
    whole row used to go even at once: the at sign's inner a jumped 60
    units up its ring in one step of weight or grade, and a little heavier
    its uprights jumped across it.)"""
    n = len(at) - 1
    if at[-1] - at[0] <= n * least:
        return [at[0] + i * (at[-1] - at[0]) / n for i in range(n + 1)]
    gaps = [b - a for a, b in zip(at, at[1:])]
    for _ in range(n):
        short = [i for i in range(n) if gaps[i] < least - 1e-9]
        if not short:
            break
        need = sum(least - gaps[i] for i in short)
        for i in short:
            gaps[i] = least
        over = sum(v - least for v in gaps if v > least)
        gaps = [v - need * (v - least) / over if v > least else v for v in gaps]
    out = [at[0]]
    for v in gaps:
        out.append(out[-1] + v)
    return out


AT_DROP = 0.2       # how far the at sign's foot stands under the baseline, of the cap height
AT_BOWL = 0.39      # where the a's bowl begins, of the way from the sign's left side to its right


def at_width(p):
    """The at sign's body: eleven modules and three stems, or three stems
    and the least white between them."""
    return max(letter_width(11, 3)(p), 3 * p.sv + 2 * least_white(p))


@punct('at', '@', 11, 3, width=at_width)
def at(g):
    """One line round an a, after Tektur's (the owner, 2026-11-12: "our at
    symbol and the ligatures involved with that symbol should look a little
    bit more like [Tektur's] at symbol"): from its foot, open at the right,
    along the bottom, up the left side, over the top and down the right
    side, which is the a's stem; the a's bowl hangs on that stem, a closed
    stroke of its own. Three uprights cross the sign (its left side, the
    bowl's, the stem) and four bars stack up it (the foot, the bowl's two,
    the top): where at heavy weights a white between them would drop under
    the least a sign keeps it takes what it lacks from the others (spread),
    and the bars thin as tight stacks do. The foot stands AT_DROP of the
    cap height under the baseline, as most families' does.

    Until version 2 it was an a in a ring open at its foot, on the
    baseline: four uprights, the a's own stem inside the ring's right side,
    in a body a module wider."""
    p, W = g.p, g.W
    y0 = -AT_DROP * p.cap
    g.stack(4, p.cap - y0, 0.75)
    sv, sh = p.sv, g.sh
    xl, xb, xr = spread([sv / 2, sv / 2 + (W - sv) * AT_BOWL, W - sv / 2], sv + least_white(p))
    yf, yt = y0 + sh / 2, p.cap - sh / 2
    yf, yb, ya, yt = spread([yf, yf + (yt - yf) / 3, yf + 2 * (yt - yf) / 3, yt], 1.75 * sh)
    # the bowl's corners as large as its counter allows: a full leg on a
    # counter under a stroke and a half across leaves it a diamond
    leg = min(p.leg, max(p.m / 2, (min(xr - xb, ya - yb) - 1.5 * sv) / 2))
    g.clip = (0, y0, W, p.cap)
    # the bowl is a closed stroke, its right side the stem's lower end (one
    # line that ran on into its own side folded there)
    g.stroke(B(xr, yb, leg), B(xb, yb, leg), B(xb, ya, leg), (xr, ya), closed=True)
    side = [B(xr, yt), (xr, ya)]
    lead = getattr(g, 'lead', None)
    if lead is None:
        g.stroke((W, yf), B(xl, yf), B(xl, yt), *side)
        return
    # a lead-in (the `~@` ligature: the tilde, in this frame, its last point
    # where it rises): it climbs at the steep 2:1 from there to the sign's
    # top and on over it, so the sign is one line from the lead-in over the
    # top and down into the a's stem; the left side and the foot, which
    # would hang from where the lead-in meets it, are not drawn
    lx, ly = lead[-1]
    xt = lx + (yt - ly) / 2
    g.stroke(*lead, (xt, yt), *side, start='v')


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


@punct('asciicircum', '^', 8, 1, width=OPERATOR)
def asciicircum(g):
    p, W = g.p, g.W
    k = p.sd / SQRT2
    top = p.cap
    h = W / 2
    ya = top + p.c - k
    g.stroke((0, ya - h), (W / 2, ya), (W, ya - h), start='v', end='v')
    g.clip = (0, ya - h - p.sv, W, top)


@punct('asciitilde', '~', 8, 1, width=OPERATOR)
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

def _degree_t(p):
    """The degree ring's stroke: the weight's, up to the watch's two
    modules and no further, as the ring accent's (marks.ring)."""
    return min(p.sv, 2 * p.m)


@punct('degree', '°', 5, 2, width=lambda p: 2 * _degree_t(p) + max(white_scale(p) * p.m, 0.75 * _degree_t(p)))
def degree(g):
    """A ring a cap's height on top: two strokes and a module of white. At
    heavy weights its stroke stops at two modules and its counter keeps
    three quarters of it, so it stays a small open ring, not a pinhole in
    a blob."""
    p, W = g.p, g.W
    t = _degree_t(p)
    th = t * g.sh / p.sv
    top = p.cap
    x0, x1, y0, y1 = t / 2, W - t / 2, top - W + th / 2, top - th / 2
    leg = p.leg * 0.6
    g.stroke(B(x0, y0, leg, th), B(x1, y0, leg, t), B(x1, y1, leg, th), B(x0, y1, leg, t), closed=True)


def bullet_width(p):
    """The bullet: 2.4 stems across to the Regular, and past it the
    Regular's and half of what the weight's would gain (as a quotation
    mark's dot, quote_dot). At 2.4 of the weight's stem it stood 0.79 of
    the H's ink wide at Black with 0.73 of its ink, where twenty-one
    families' heaviest stand 0.51 and 0.25 (0.77 and 0.57 at the outside)."""
    from ..draw import held_at
    q = held_at(p)
    return 2.4 * (p.sv if q is p else q.sv + QUOTE_GAIN * (p.sv - q.sv))


@punct('bullet', '\u2022', 4, width=bullet_width)
def bullet(g):
    """A large dot on the x-height's centre: a square, chamfered."""
    p, W = g.p, g.W
    y = p.xh / 2
    g.stroke((W / 2, y - W / 2, W), (W / 2, y + W / 2))


@punct('periodcentered', '·', 2, width=dot_w())
def periodcentered(g):
    p = g.p
    dot(g, p.dot() / 2, p.xh / 2 - p.dot() / 2)


DOTS_WHITE = 1.2        # white between the dots of an ellipsis, in dots


def dot_step(p):
    """From one dot of an ellipsis to the next (and of ⋮ ⋯ ⋰ ⋱): a dot and
    DOTS_WHITE dots of white, the Regular's dots past it. With the white
    1.2 of the weight's own dot the ellipsis was 0.95 of the H's ink across
    at Regular, 1.48 at Bold and 1.78 at Black, where twenty-one families'
    stand 1.19 at Regular and 1.29 at their heaviest and none over 1.62,
    and ⋮ stood from a quarter of the cap height under the line to a
    quarter over the capitals."""
    from ..draw import held_at
    return p.dot() + DOTS_WHITE * min(p.dot(), held_at(p).dot())


MONO_DOTS_WHITE = 0.85  # ... in the monospaced cell, at least


def ellipsis_dot(p):
    """The ellipsis's dot: the period's; in the monospaced cell as large as
    leaves MONO_DOTS_WHITE of a dot between three of them across the cell's
    body. Drawn with the period's dots and fitted to the cell
    (symkit._mono_fit), Arris Mono's was drawn smaller about the math axis
    from Medium up and left the baseline: 24 units over it at Medium, 59
    at SemiBold, 89 at Bold."""
    if p.mono:
        return min(p.dot(), p.fig_w / (3 + 2 * MONO_DOTS_WHITE))
    return p.dot()


def ellipsis_w(p):
    return p.fig_w if p.mono else p.dot() + 2 * dot_step(p)


@punct('ellipsis', '…', 8, width=ellipsis_w)
def ellipsis(g):
    p = g.p
    s = ellipsis_dot(p)
    step = (g.W - s) / 2
    for i in range(3):
        x = s / 2 + i * step
        if s < p.dot():                                     # a smaller dot, broken in proportion
            g.lay((x, 0, s), (x, s), c=p.c * s / p.dot())
        else:
            g.stroke((x, 0, s), (x, s))


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
    g.move(lambda x, y: (g.W - x, p.cap - y + shift))
    g.clip = (0, shift, g.W, p.xh)


@punct('plusminus', '±', 8, 1, width=OPERATOR)
def plusminus(g):
    p, W = g.p, g.W
    a, h = axis(p) + p.m, W / 2 - p.sv / 4
    g.stroke((0, a), (W, a))
    g.stroke((W / 2, a - h), (W / 2, a + h))
    g.stroke((0, a - h - g.sh), (W, a - h - g.sh))


@punct('logicalnot', '¬', 8, 1, width=OPERATOR)
def logicalnot(g):
    p, W = g.p, g.W
    a = axis(p)
    g.stroke((0, a), (W - p.sv / 2, a), (W - p.sv / 2, a - 2.5 * p.m))


def _lessequal(g, mirror):
    """The < chevron itself over a bar, the equal sign's white between,
    the pair centred on the axis, between the baseline and the cap height.

    At the Regular the <'s own chevron, the white and the bar fill that
    height to 38 units. Bolder, the bar, the white (1.6 bars) and the arms'
    own ink all grow and the chevron grows with its body: the pair stood
    805 units tall at SemiBold and 997 at Black, 150 under the baseline and
    127 over the capitals. Where they do not fit, the white gives first,
    down to the least white a counter keeps, and then the chevron is drawn
    as large as the height leaves, its bar as wide as it is, the two
    centred in the operator's body."""
    p, W = g.p, g.W
    x_tip, reach = chevron_geometry(g)
    from ..draw import _thickness
    kv = _thickness(p, g.sh)((2, 1)) / (2 * math.cos(SLOPE))     # the arms' ink past their centreline ends, vertically
    white = eq_white(g)
    room = p.cap - g.sh - 2 * kv                             # what the bar and the arms' ink leave of the height
    if reach + white > room:
        white = max(min(white, least_white(p)), room - reach)
        reach = max(min(reach, room - white), 2 * kv)
    v = reach / 2
    x0 = (W - x_tip - reach) / 2                             # the narrower pair, centred
    a = axis(p) + (white + g.sh) / 2                         # the chevron's centre
    T = (lambda x, y: (W - x, y)) if mirror else (lambda x, y: (x, y))
    g.stroke(T(W - x0, a + v), T(x0 + x_tip, a), T(W - x0, a - v), start='v', end='v')
    yb = a - v - kv - white - g.sh / 2
    g.stroke((x0, yb), (W - x0, yb))


@punct('lessequal', '\u2264', 8, 1, width=OPERATOR)
def lessequal(g):
    _lessequal(g, False)


@punct('greaterequal', '\u2265', 8, 1, width=OPERATOR)
def greaterequal(g):
    _lessequal(g, True)


@punct('notequal', '≠', 8, 1, width=OPERATOR)
def notequal(g):
    from ..draw import held_c
    equal(g)
    p, W = g.p, g.W
    a = axis(p)
    # its slash, added: the Regular's from there on. Four modules each way from the axis, or a module past
    # the bars where they stand further out: at the Regular it passes them by 98 units, and with the bars
    # of Black, 306 from the axis, it ended 66 units inside them, the sign two bars and a tick between
    up = max(4 * p.m, eq_offset(g) + g.sh / 2 + p.m)
    g.lay((W / 2 - up / 2, a - up, g.held((1.0, 2.0))), (W / 2 + up / 2, a + up), c=held_c(p),
          start='h', end='h')


DAGGER_STUB = 0.8       # of a stem: the least of the dagger's stem that stands over its bar
DAGGER_GROWS = 1.2      # its body's gain for every unit its stem gains past the Regular


def dagger_bar(p):
    """Where a dagger's bar crosses: three and a half modules down, or lower
    where the stem over it would be shorter than DAGGER_STUB of a stem
    (the heaviest weights). At two stems and a fifth the bar went down the
    stem as the weight rose, to 0.39 of the cap height at Black, the middle
    of the stem: a plus, and the double dagger's two bars had 5 units
    between them and were lightened into one. It crosses at 0.71 of the
    cap height to the Bold and at 0.66 at Black."""
    return p.cap - max(3.5 * p.m, DAGGER_STUB * p.sv + p.sh / 2)


def dagger_width(p):
    """A dagger's body: a letter's of six modules and what its stem has
    gained past the Regular, DAGGER_GROWS times over: 0.69 of the H's ink
    at Regular, 0.77 at Bold, 0.82 at Black (thirty families: 0.80 at
    Regular and at their heaviest, 0.91 at the outside; at twice the gain
    it stood 0.96 at Black). Its weight's own stem: lightened for its
    whites (draw.white_features) it keeps the body, so its arms get the
    room the lightening is for."""
    from ..draw import _unlightened
    return growing_width(6, 1, DAGGER_GROWS)(_unlightened(p))


@punct('dagger', '†', 6, 1, width=dagger_width)
def dagger(g):
    p, W = g.p, g.W
    g.stroke((W / 2, -p.under + p.m), (W / 2, p.cap))
    g.stroke((0, dagger_bar(p)), (W, dagger_bar(p)))
    g.clip = (0, -p.under, W, p.cap)


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
