"""Figures 0-9 and the colon, after the Dymaxion zone numerals.

Proportions follow the 9x12 masters: ``u`` and ``v`` are one module of the
figure body horizontally and vertically, so positions read like the pixel
drawings (x = 8u is column 8). Stroke positions follow the weights, so
outer edges stay on the body box at every weight.
"""
from __future__ import annotations

import math

from ..draw import B, Opening, glyph
from ..params import SQRT2, inner_leg, outer_leg, white_floor

STEEP = (1 / math.sqrt(5), 2 / math.sqrt(5))  # the 2:1 slope, as a unit vector


def frame(g):
    p = g.p
    # Figures that stack three bars thin their horizontals where an opening
    # needs it (see STACKED); elsewhere sh_k stays 1.
    g.sh_k = g.free('sh_k', 1.0)
    W, H = g.W, p.cap                       # the body: the figures' own, or in Mono's cell narrower (draw._cell_fit)
    u, v = W / 9, H / 12
    xl, xr = p.sv / 2, W - p.sv / 2
    yb, yt = g.sh / 2, H - g.sh / 2
    # Strokes may run past the body (a diagonal into a bar's end); the body
    # box trims them, so outer edges stay exactly on it.
    g.clip = (0, -g.ob, W, H + g.ot)
    return p, W, H, u, v, xl, xr, yb, yt


def _inside(p, sh):
    """The inside cut of the corner a beak hangs from, as it is drawn
    upright in Arris: what the strokes leave of the centreline's leg, no
    less than the corner rule's fill (lower.inside_cut). The weight's own
    edge break was its least until the fill was held at the Regular's, and
    stayed the beak's measure: past the Regular the beak stood a break and
    its flank past a bar whose inside is cut half a break, 100 units into a
    bay of 105 on the 3 at a stem of 200, and the 3's upper storey was shut
    (the owner, 2026-11-12: "you need the black three to look like the
    original one a little bit better"). The italic's and the watch's own
    keep the break (their corners' curves and the pixel rule)."""
    if p.slant or not p.optical:
        return inner_leg(p, sh)
    from ..draw import fill_leg
    drawn = max(fill_leg(p), p.leg - (p.sv + sh) / 2 + p.sd / SQRT2)
    own = inner_leg(p, sh)
    return own - (own - min(own, drawn)) * p.optical


def beak_depth(p, sh=None, low=False):
    """How far a beak terminal reaches below the bowl's top (or above its
    bottom). Its outer flank under the corner chamfer is one edge break long,
    so the corner rule turns it into a point; at weights where that would leave
    the inner flank shorter than an edge break, the inner flank sets the depth.
    At the heritage weight both flanks are exactly one edge break. ``low``:
    the letter stands in the x-height (the epsilon), and in the italic takes
    the small capital's beak (_small_italic): with the capital's, 264 units
    at Black, its two beaks stood 12 units apart across a mouth of 540."""
    sh = p.sh if sh is None else sh
    if _small_italic(p) or (low and p.slant):
        return outer_leg(p, sh=sh) + p.c
    d = sh + _inside(p, sh) + _flank(p)
    if p.slant:
        d = min(d, (p.cap - p.c) / 2)                   # two beaks across a height never meet
    return max(_shortest(p, sh), d)


BAY_WHITE = 0.6     # the white a beak keeps off the bar it turns toward, as a share of the least white (lower.beak_in, bay_stack)
BAY_STACK_MIN = 0.64    # the least an italic capital's bars thin to for its bays, of the height's bar (bay_stack: past STACK_MIN, at Black)


def bay_stack(g, frame, rows, floor=None, lower=None):
    """Thin a letter's horizontals where its beaks turn into bays, the
    whites between its bars (the S's two, the Ze's, the reversed E's, the
    epsilon's, the question mark's one), so far that each beak's end keeps
    BAY_WHITE of the least white off the bar it turns toward, 0.36 of a
    stem from Bold; never under STACK_MIN of the weight's own, as the
    figures' stacks. ``frame``: makes the letter's frame at the
    horizontals as they stand; ``rows``: each bay's two bars, by their
    frame rows; ``floor``: the lowest the lower bar may come for the bay
    by a rule of its own (the Ҩ's loop, which comes down for its mouth
    before its bars give); ``lower``: where the lower bar stands in a
    frame, where a rule of its own raises it off its row (the question
    mark's return, over its stem: punct.question_return). Returns the
    frame to draw in.

    The lowercase a, e and s shorten their beaks for the same white
    (lower.beak_in). A capital's cannot in the italic: there its beak keeps
    a flank TAIL_FLAT breaks longer than the upright's (_flank), which its
    corners need to be curved; shortened to what the bay wanted, the S's
    and the Ze's corners were cut straight at ExtraBold and Black and
    curved below. So the bars give instead, as the 3's and the 5's do. In
    the italic the S's beak stood 29 units off its spine at Black, 0.18 of
    a stem, for the upright's 78, and the Ze, the reversed E, the epsilon
    and the question mark with it; in the watch's own drawing, its bars as
    thick as its stems, the upright S 0.24 of a stem and the italic
    epsilon's mouth shut (the owner, 2026-11-11, of the a's and the s's:
    "where it meets the bottom storey or where it does not meet. That gap
    ..."; of the italic's: "let's go ahead and fix all those things")."""
    p = g.p
    least = BAY_WHITE * white_floor(p.m, p.sv, p.optical)
    k1 = g.sh_k

    def spare(k):
        g.sh_k = k
        f = frame()
        return min(f.Y(hi) - (lower(f) if lower is not None else f.Y(lo) if floor is None else min(f.Y(lo), floor))
                   - g.sh for lo, hi in rows) - (beak_depth(p, g.sh) - g.sh) - least
    k = k1
    if spare(k1) < 0:
        k, thick = STACK_MIN * k1, k1               # (the thinner the bars, the more room: the most bar that leaves it)
        if spare(k) < 0 and p.optical and p.slant:
            # (the italic's capitals at a stem of 200, whose beak is the longer: at the stack's least the S's
            # bays still stood 44 units wide for 54, and its bars give as far as BAY_STACK_MIN for them)
            k = BAY_STACK_MIN * k1
        if spare(k) >= 0:
            for _ in range(24):
                mid = (k + thick) / 2
                k, thick = (mid, thick) if spare(mid) >= 0 else (k, mid)
    g.sh_k = k
    return frame()


def wedge_bars(g, frame, run):
    """Thin a letter's horizontals for the wedge of white under a 45-degree
    return (the ezh's, the Abkhasian dze's: a top bar, a diagonal back to
    the middle, the 3's lower bowl), so far that it keeps BAY_WHITE of the
    least white at its mouth; never under the stack's least. The return
    runs as far down as across (``run``, of the frame), and the white
    between the bar it leaves and the bar it lands on is that run less a
    bar. Returns the frame to draw in.

    Nothing kept that white. In the italic, whose bars in the x-height are
    the weight's own, the small ezh's two bars met at Black, 170 units
    thick on a run of 167, and what was left of the diagonal's end stood
    out of the join in teeth; upright it had 49 units for the 57 a bay
    keeps."""
    p = g.p
    least = BAY_WHITE * white_floor(p.m, p.sv, p.optical)
    f = frame()
    room = run(f) - least                                   # the most bar that leaves the wedge its white
    if g.sh > room:
        k1 = g.sh_k
        g.sh_k = max((BAY_STACK_MIN if p.optical and p.slant else STACK_MIN) * k1, k1 * room / g.sh)
        f = frame()
    return f


def off_the_beak(g, f, x_beak, x_end, row, top, bottom, d=None):
    """Where a bar's end stands, on frame row ``row``, beside the beaks of
    the bars on rows ``top`` and ``bottom`` (the Ze's waist, the reversed
    E's bar, the Ukrainian E's, the epsilon's): no nearer the beak at
    ``x_beak`` than leaves BAY_WHITE of the least white between the bar's
    end and the beak's, measured corner to corner; ``x_end`` where there is
    that already.

    These beaks do not face their bar, they pass its end, and where a beak
    is short the two stand corner to corner with room to spare: the
    upright Ze at Black, 82 units. The italic's beak is TAIL_FLAT breaks
    longer and comes down beside the bar's end (the italic Ze 37 units at
    Black, the italic epsilon 15, 0.09 of a stem), and so does the watch's
    own drawing, its bars as thick as its stems (the epsilon's mouth shut
    in its italic at Black). The bar's end steps back; the beak and its
    curves are as they were."""
    p = g.p
    least = BAY_WHITE * white_floor(p.m, p.sv, p.optical)
    d = beak_depth(p, g.sh) if d is None else d
    over = (f.Y(top) + g.sh / 2 - d) - (f.Y(row) + g.sh / 2)       # white between the upper beak's end and the bar's top
    under = (f.Y(row) - g.sh / 2) - (f.Y(bottom) - g.sh / 2 + d)    # and between the bar's underside and the lower beak's
    dy = min(over, under)
    if p.slant:
        # (the italic rounds both corners: they stand as far apart as their points)
        need = least if dy <= 0 else math.sqrt(max(0.0, least * least - dy * dy))
    else:
        # (upright each is broken an edge break, and the two cuts face each other: the white between
        # them is (dx + dy + 2c)/√2, or dx where the beak has come down past the bar's edge)
        need = max(0.0, min(least, SQRT2 * least - dy - 2 * p.c))
    side = 1.0 if x_end >= x_beak else -1.0
    edge = x_beak + side * p.sv / 2
    return edge + side * max(side * (x_end - edge), need)


def _small_italic(p) -> bool:
    """An italic small capital (э з є, cyrillic.sc). Its beaks are the
    lowercase c's, the outer flank alone, chamfered at every weight: with
    the capital's longer flank (_flank) two beaks across its height met
    from 650 up (at 800/+100 they crossed and the stroke could not be
    drawn), and with the upright's the corner above the flank was held at
    some weights and curved at others, as the capital's was."""
    return bool(p.slant) and p.cap <= p.xh + 1e-6


def _flank(p):
    """The inner flank under the corner's inner chamfer: an edge break, and
    in the italic TAIL_FLAT breaks more (italic_forms), clear of the jog
    cleanup. One break long, it merged with the end's break at some weights
    and not others (geom.JOG closes a step up to a break), the corner above
    it was no corner there, and the italic held its shoulder straight at
    those weights and curved it at the rest: the C's at 350 and 400."""
    if p.slant:
        from .italic_forms import TAIL_FLAT
        return (1 + TAIL_FLAT) * p.c
    return p.c


def _shortest(p, sh):
    """The shortest beak an opening may leave: its outer flank alone, an edge
    break under the chamfer. In the italic the inner flank keeps its length
    too (_flank): shortened under it, the beak's corner is held at the
    weights the opening binds and curved at the rest (the Ҽ's and Ә's
    mouths from 600)."""
    outer = outer_leg(p, sh=sh) + p.c
    if _small_italic(p) or not p.slant:
        return outer
    return max(outer, sh + inner_leg(p, sh) + _flank(p))


def beak_top(g):
    return g.p.cap + g.ot - beak_depth(g.p, g.sh)


def beak_bottom(g):
    # an opening may shorten the beak, but never past its outer flank
    return -g.ob + max(g.free('beak', beak_depth(g.p, g.sh)), _shortest(g.p, g.sh))


def _beak_limit(p):
    """The shortest beak at the thinnest horizontals a stack allows."""
    return _shortest(p, STACK_MIN * p.sh)


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
    tip = g.part('beak').intersection(box(-1e4, getattr(g, 'arm', g.sh) - g.ob + 1e-3, 1e4, 1e4))
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
    x1 = g.defaults_used['x1']
    return g.white_left(g.defaults_used['yf'] + 1e-3 * p.m, x1 - p.sv / 2)


ONE_FLAG = 3.0    # modules: how far left of the stem the 1's flag ends, at every weight (Chakra Petch's: 2.1 stems at Regular, 1.1 at Bold)


@glyph('one', '1', 'fig_w', openings=[Opening(_notch_white, 'yf', lambda p: p.cap / 3, max_ratio=0.5)])
def one(g):
    """The 1: a stem, its top left corner cut and the cut run out into a
    flag. The flag is a 45-degree stroke whose upper edge continues the
    stem's cut corner; it ends plumb, as the flags of the chamfered faces
    do (Chakra Petch's, whose 1 this follows: a stem, a flag, no foot), and
    stands free of the stem by more than its own thickness at every weight
    (ONE_FREE), so it stays a stroke. The stem stands right of the middle
    by what centres the two. In Arris Mono, whose cell it must fill beside
    l and I, it keeps a foot: the slab of Mono's I.

    Until 1.017 it was the watch's 1 in every cut: on a foot six modules
    wide, half the figure's ink, the corner rule filling in on both sides
    of the stem, its flag ending on a horizontal, in a point; from Bold the
    flag, the fills and the foot were three lumps. (The owner, 2026-11-10:
    redesign it, and the watch's cut with it.)"""
    p, W, H, u, v, xl, xr, yb, yt = frame(g)
    top = H + g.ot
    k = p.sd / SQRT2
    free = ONE_FLAG * u                                     # the flag's run left of the stem, to its plumb end
    x1 = W / 2 + (u / 2 if p.mono else min(1.5 * u, free / 2))
    g.defaults_used['x1'] = x1
    if p.mono:
        g.stroke((x1 - 3 * u, yb), (x1 + 3 * u, yb))        # foot
    g.stroke((x1, yb if p.mono else 0), (x1, top))          # stem
    a = x1 - p.sv / 2 + p.c - top + k                       # the flag's centreline: x - y = a
    yf = g.free('yf', x1 - p.sv / 2 - free - a)             # (lower when heavy strokes would close the notch over a foot)
    g.defaults_used['yf'] = yf
    g.stroke((x1, x1 - a, p.sd), (yf + a, yf), start='v', end='v')


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


def _heavy_stack(p):
    """How far a figure's bars may thin for its mouth alone: not at all to
    a stem of 158, the heaviest the figures were drawn at until Arris's
    weights took other families' colour, and to the stack's least
    (STACK_MIN) at 200."""
    t = min(1.0, max(0.0, (p.sv / p.grade_k - 158.0) / (200.0 - 158.0)))
    return 1.0 - (1.0 - STACK_MIN) * t * p.optical


# The 3's waist bar pulls its end in and its beak shortens where the mouth between them runs short. Past a stem
# of 158 that was all there was: at 200 the bar's end stood on the middle of the figure, a nub on the stem's
# side, the beak had no rise left, and the 3 was a 7's top over a foot (the owner, 2026-11-12: "you need the
# black three to look like the original one a little bit better"). There the three bars thin first, as the
# stack's bars do for the upper bowl, and the waist and the beak keep what the Regular's have.
@glyph('three', '3', 'fig_w', openings=[_stacked(_upper_bowl),
                                       Opening(_mouth_gap, 'sh_k', _heavy_stack, max_ratio=MOUTH_SHARE),
                                       Opening(_mouth_gap, 'bar_x', lambda p: p.fig_w / 2, max_ratio=MOUTH_SHARE),
                                       _mouth(_mouth_gap)])
def three(g):
    p, W, H, u, v, xl, xr, yb, yt = frame(g)
    ym = 6 * v
    # Its top and its foot are the cap height's bar at every weight, as the 2's and the 5's beside it
    # (draw._cap_bar), and the waist alone gives for the bowl and the mouth (frame's sh_k): thinned all three
    # alike, the 3 stood on arms of 130 units at ExtraBold and 119 at Black beside figures on 147 (the owner,
    # 2026-11-12: "let's make sure that we're extremely consistent like this across everything ... fix the
    # 3"). The italic, which keeps the weight's own bars, thins the three as it did.
    arm = g.sh if p.slant else g.sh0
    g.arm = arm                                             # (_mouth_gap: the bar the beak rises from)
    yt, bot = H - arm / 2, arm / 2 - g.ob
    xm = g.free('bar_x', 3 * u)                             # heavy small sizes pull the bar's end in
    # The upper bowl's lower corner is a module rounder than the lower bowl's
    # upper one; their outer chamfers meet in a sharp point at the waist.
    g.stroke((u, yt, arm), B(xr, yt), B(xr, ym, p.leg + u), (xm, ym), part='bar')
    # parts that continue one another overlap by a quarter stem, so they
    # always join (end-to-end square cuts join only if they coincide exactly)
    g.stroke((xm, ym), B(xr, ym), B(xr, bot, None, arm), (W / 2, bot))
    # (an opening may shorten the beak, but never past its outer flank: beak_bottom, on the arm's thickness)
    reach = max(g.free('beak', beak_depth(p, arm)), _shortest(p, arm))
    g.stroke((W / 2 + p.sv / 4, bot, arm), B(xl, bot), (xl, -g.ob + reach), part='beak')


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
    # the clip stands a module of white from the stem, as the watch drew it
    # (its column 4, the stem's 7, two-module strokes); where the strokes
    # are heavier than the watch's it moves left to keep that module (at
    # Black it had 33 units, a fifth of a stem: a slit)
    xc = min(4 * u, xs - p.sv - u)
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
