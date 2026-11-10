"""Lowercase a-z, built from their pixel masters (``arris.masters.LOWER``).

Module coordinates: x-height 9, ascender 13, descender -3 (see letterframe).
The same moves as the capitals and figures: beaks on c and j, the 2's notch
in z, a notched shoulder on r (the 1's flag, turned), arches that meet in a
V on m, gables on v and w.
"""
from __future__ import annotations

from ..draw import B, Opening, glyph
from ..params import inner_leg, outer_leg
from .figures import STACK_MIN, beak_depth, jog
from .letterframe import ARM, Frame, k_arms, least_white, letter_width, share_width


def low(char, wm, stems, width=None, openings=(), arm=ARM):
    return glyph(char, char, width or letter_width(wm, stems, arm), kind='lower', openings=openings)


def bars3(g):
    """(outer, inner, outer): the three horizontals of a letter that stacks
    three in the x-height (a e s). Where three no longer fit at the zone's
    weight (g.stack), the bar at the open end keeps that weight, the one
    at the closed end takes the stack's, and the inner bar gives what the
    two need, as the inner bars of hand-drawn faces do (the a's 0.82, 0.72,
    0.78 of a stem in Chakra Petch Bold, the e's bar 0.54 to the top's 0.70
    in Inter Black; tools/stroke_roles.py). Until 1.017 all three thinned
    alike."""
    stacked = g.sh
    lead = g.sh0
    return lead, max(STACK_MIN * g.sh0, 2 * stacked - lead), stacked


def beak(g, w):
    """How far the c's beak reaches from the line its bar lies on, for a
    bar ``w`` thick: the corner's outer flank alone, an edge break under
    the cut (the shortest beak: an open mouth tells c from o, a from d, e
    from o)."""
    return outer_leg(g.p, sh=w) + g.p.c


@low('a', 8, 2)
def a(g):
    """The a: an arch over a bowl. The arm starts in the c's beak at the
    left, a short terminal hanging from a cut corner, runs along the
    x-height and comes into the stem through a bowl's corner. The three
    bars are drawn with the same white between them, and the optical centre
    raises the middle as it does in every letter (draw.OPTICAL), so the open
    storey comes to seven eighths of the bowl, as in the chamfered faces
    this follows (Chakra Petch 0.89, Oxanium 0.89).

    Until 1.017 the upper storey was a bare bar on a tall bowl: square at
    its left end, all but square at the stem (the pixel master's one-step
    corner), over a white two thirds of the bowl's (0.65), thinned with the
    other bars from Bold. It had none of the font's corners, and no room."""
    g.stack(3, g.p.xh, ratio=0.75)
    f = Frame(g, 8, 'lower')
    p = g.p
    arm, inner, foot = bars3(g)
    low = (p.xh - arm - inner - foot) / 2                   # the bowl's white, and the open storey's
    ya = p.xh - arm / 2
    yb = foot + low + inner / 2
    g.defaults_used.update(arm=ya, bowl=yb)
    g.stroke((f.X(1), p.xh - beak(g, arm)), B(f.X(1), ya, None, arm), B(f.X(7), ya), f.P(7, 0))
    g.stroke((f.X(7), yb, inner), B(f.X(1), yb), B(*f.P(1, 1)), f.P(7, 1), closed=True)


@low('b', 8, 2)
def b(g):
    f = Frame(g, 8, 'asc')
    g.stroke(f.P(1, 0), f.P(1, 13))
    g.stroke(f.P(1, 8), B(*f.P(7, 8)), B(*f.P(7, 1)), f.P(1, 1), closed=True)


@low('c', 8, 2)
def c(g):
    c_shape(g)


def c_shape(g, foot_leg=None):
    """The c. ``foot_leg``: the leg of the foot's corners (the default: the
    parameter leg); ҫ's drop hangs between them (cyrillic_ext.drop_leg)."""
    f = Frame(g, 8, 'lower')
    # The shortest beaks (the outer flank alone): an open mouth tells c from o.
    p = f.p
    d = beak(g, g.sh)                                       # by the zone's own bar (thinner than the capitals' from Bold)
    g.stroke((f.X(7), p.xh - d), B(*f.P(7, 8)), B(*f.P(1, 8)), B(*f.P(1, 1), foot_leg), B(*f.P(7, 1), foot_leg),
             (f.X(7), d))


@low('d', 8, 2)
def d(g):
    f = Frame(g, 8, 'asc')
    g.stroke(f.P(7, 0), f.P(7, 13))
    g.stroke(f.P(7, 8), B(*f.P(1, 8)), B(*f.P(1, 1)), f.P(7, 1), closed=True)


def _e_gap(g):
    """White between a bar and the arm under it (the Abkhasian che's, an e
    in its drawing: cyrillic_ext; the e itself sets its storeys by rule)."""
    return g.defaults_used['bar'] - g.defaults_used['arm'] - g.sh


@low('e', 8, 2)
def e(g):
    """The e: a bowl over an arm that ends in the c's beak. Its lower arm
    turns up at the right through a cut corner into a short terminal, the
    a's turned over. The three bars are drawn with the same white between
    them and the optical centre raises the bar, so the open storey comes to
    a seventh more than the bowl (Chakra Petch 1.14).

    Until 1.017 the arm ended square and the bar stood below the middle
    (the open storey 0.64 of the closed one), raised only as the weight
    closed it."""
    g.stack(3, g.p.xh, ratio=0.75)
    f = Frame(g, 8, 'lower')
    p = g.p
    arm, bar, top = bars3(g)
    open_ = (p.xh - arm - bar - top) / 2                    # the white over the arm, and the bowl's
    y1 = arm / 2
    yb = arm + open_ + bar / 2
    yt = p.xh - top / 2
    g.defaults_used.update(bar=yb, arm=y1)
    g.stroke((f.X(1), yb, bar), (f.X(7), yb), B(f.X(7), yt), B(f.X(1), yt), closed=True)
    g.stroke((f.X(1), yb), B(f.X(1), y1, None, arm), B(f.X(7), y1), (f.X(7), beak(g, arm)))


# The letters with one stem and an arm (f t l j) are a module narrower than
# their masters: against the n they stood wider than any face of this kind
# sets them (the l 0.65 of the n's advance for 0.40 to 0.51, the j 0.65 for
# 0.41 to 0.49, the t 0.79 for 0.53 to 0.69, the f 0.72 for 0.48 to 0.66:
# review/widths, 2026-11-10), and a line with several of them (little,
# filter, jilt) lost the rhythm its stems set.
NARROW = 6      # the f's and the t's frame, in modules (their masters' seven, less one)


@low('f', NARROW, 1)
def f_(g):
    if g.p.mono:
        f = Frame(g, 9, 'asc')
        g.stroke(f.P(3.5, 0), B(*f.P(3.5, 12)), f.P(9, 12))
        g.stroke(f.P(0.5, 8), f.P(8, 8))
        return
    f = Frame(g, NARROW, 'asc')
    g.stroke(f.P(2, 0), B(*f.P(2, 12), f_leg(g, f)), f.P(NARROW, 12))
    g.stroke(f.P(0, 8), f.P(NARROW - 1, 8))


def f_leg(g, f):
    """The leg of the f's corner: its cut comes down the stem as far as the
    cut of the t's top does (an edge break under the t's top, f.Y(11)), so
    the f's and the t's left sides are one drawing from the crossbar up to
    there, and where the t's cut and its crossbar's meet in one flat plane
    (Black) the f's do too. With the bowl's own leg the f's cut stopped 67
    units above the crossbar's at Black, over a break: two planes and a
    step where the t has one."""
    p = g.p
    cut = p.asc - (f.Y(11) - p.c)                           # from the ascender down to where the t's cut ends
    return max(p.leg, cut - (p.sv + g.sh) / 2 + p.sd / 2 ** 0.5)


def crotch_butt(g, y):
    """In the italic, the line along the bottom edge of a horizontal drawn on
    ``y`` (as the strokes take its thickness), for ``Glyph.butt``: a bowl's
    foot meeting a stem that runs on down into a descender (g y д) meets it
    square there, without the corner rule's 45-degree fill. With the fill,
    the white between it and the descender's corner below ran out from about
    500 to 750 (the fill takes up to a corner break of the stem's edge; the
    corner's inner chamfer then started on the fill's diagonal), and the
    italic, which curves a corner only between straight edges, held that
    corner straight on both its edges there and curved it either side. Flush,
    the corner always meets the stem's edge or, heavier, the foot's, and
    curves at every weight."""
    if not g.p.slant:
        return ()
    from ..draw import _thickness
    return (('y', y - _thickness(g.p, g.sh)((1.0, 0.0)) / 2),)


def hook_room(p) -> float:
    """How far below its descender line a hook may still deepen: down to
    the font's descent."""
    return max(0.0, p.deep - p.desc)


def hook_fit(p, sh, white=None):
    """(the hook's thickness, how far it deepens past the descender line)
    for horizontals ``sh`` thick: the white between the hook and what stands
    over it (the g's bowl) stays ``white`` tall (least_white). The weight's
    descender line is set for exactly that (params.descender_line), so the
    g's and y's hooks stand on it at their full weight, with p q and j;
    a hook that keeps more white (ǥ's, for its bar) makes room first,
    deepening toward the font's descent, and only where that is spent
    (Black) does a hook thin, never under the stack minimum of a bar.

    Until 1.016 it thinned first, and measured its white past the corner's
    inner leg, not from bar to bar: the hook was 0.73 of the letter's other
    horizontals at Regular (57 units to the bowl's 79) and 0.7 from Medium
    up, with 123 units of white over it, a stem and a third. It read as a
    mistake (and the j's hook, with nothing over it, kept its weight)."""
    white = least_white(p) if white is None else white
    extra = min(hook_room(p), max(0.0, sh + white - p.desc))
    w = min(sh, max(STACK_MIN * sh, p.desc + extra - white))
    return w, extra


def hook(g, f, x_stem=7, x_end=1, white=None):
    """The descending hook of g, y and the italic y: the stem down from the
    body into a bowl corner and a horizontal back under it, as thick as the
    letter's other horizontals (hook_fit), on the weight's descender line.
    (The owner's rule: a feature weight would swallow grows or makes room
    by the smallest change that keeps it.)"""
    p = g.p
    w, extra = hook_fit(p, g.sh, white)
    yh = -(p.desc + extra) + w / 2
    if extra:
        x0, y0, x1, y1 = g.clip
        g.clip = (x0, min(y0, -(p.desc + extra)), x1, y1)
    g.stroke(f.P(x_stem, 9), B(f.X(x_stem), yh, None, w), (f.X(x_end), yh))


def g_strokes(g, white=None):
    """The g: its bowl and its hook (``white``: the room the hook leaves
    under the bowl, for a g that carries something there: ǥ's bar)."""
    f = Frame(g, 8, 'lower')
    g.stroke(f.P(7, 8), B(*f.P(1, 8)), B(*f.P(1, 1)), f.P(7, 1), closed=True)
    hook(g, f, white=white)
    g.butt += crotch_butt(g, f.Y(1))


@low('g', 8, 2)
def g_(g):
    g_strokes(g)


def shoulder(g, f, xs, x_right, top=8, drop=2, notch=True, joined=False):
    """An arch's shoulder, as the r's: it leaves the stem at 45 degrees
    ``drop`` modules below the arch (two; the italic's branch lower), an
    edge break into the stem, and leaves a notch
    under it (the 1's flag, turned). Returns the arch's points up to its
    right corner, and how the stroke's start is cut.

    The diagonal needs room between the stems. Where there is less (the
    monospaced m, the heaviest weights) it rises less and starts further
    into the stem, down to the plain square join, so the arch keeps its
    counter and the drawing changes continuously with weight.

    The room is the arch's own underside: past the shoulder it keeps a flat
    an edge break long before the right corner's cut (shoulder_room). And
    nothing of the shoulder is drawn smaller than an edge break: where the
    step under it would be, the diagonal is cut along the arch's underside
    and the counter's top is the arch's alone; where the notch over it
    would be (the diagonal's top entering the stem less than a break and a
    half under the arch's: SHOULDER_NOTCH), the arch leaves the stem
    square. So the shoulder goes as the X's step does: the n keeps both to
    Bold, the notch alone at ExtraBold, and is square at Black, as the m is
    from SemiBold. ``joined``: the stem is another arch's (the m's second),
    and the notch is the V the two meet in, kept at every weight.

    Until 1.017 the room was measured to the corner's outside, on the
    diagonal's centre line: from Medium the diagonal's edge ran into the
    corner's cut and the counter came to a point under the arch, at Black a
    spike 39 units tall beside a flat of 106, the arch a third thicker over
    the flat than its bar.

    ``notch`` False: the notch filled, the diagonal's underside running
    straight into the stem (the italic k at its heavy weights, k_ital).
    The diagonal then starts at the stem's centre, cut along it: cut level,
    its start is k = sd/√2 each side of x0, 16 units more than half a stem
    at Black, and far into the stem its left corner comes out of the
    stem's back (a nub of three points)."""
    p = g.p
    k = p.sd / 2 ** 0.5
    y_top = f.Y(top)
    full = f.Y(top) - f.Y(top - drop)
    x_full = xs + p.sv / 2 + k - p.c
    room = x_right - p.leg - p.c - x_full                  # the diagonal ends clear of the corner
    upright = notch and not p.slant                        # the italic keeps its own branch (italic_forms)
    if upright:
        room = min(room, shoulder_room(g, xs, x_right, full))
    rise = min(full, max(room, 0.0))
    plain = [(xs, y_top), B(x_right, y_top)], 'flat'
    if rise < 1e-3 * p.m:
        return plain
    r = rise / full
    x0 = xs + r * (x_full - xs)
    if not notch:
        return [(xs, y_top - rise - (x0 - xs)), (x0 + rise, y_top), B(x_right, y_top)], 'v'
    step = rise - g.sh / 2                                  # the diagonal's cut, below the arch's underside
    if upright and step < p.c:
        over = g.sh / 2 + rise - (1 - r) * (p.sv / 2 + k) - r * p.c   # the diagonal's top at the stem's side, below the arch's
        if not joined and over < SHOULDER_NOTCH * p.c:
            return plain
        return [(x0 + step, y_top - g.sh / 2), (x0 + rise, y_top), B(x_right, y_top)], 'h'
    return [(x0, y_top - rise), (x0 + rise, y_top), B(x_right, y_top)], 'h'


SHOULDER_NOTCH = 1.5    # the least notch over a shoulder, in edge breaks down the stem's side: a break deep where the stem
                        # stops at the arch (n), and where it goes on (h) a break of it is the corner's own fill


def shoulder_room(g, xs, x_right, full):
    """The most a shoulder between stems at xs and x_right can rise and
    leave the arch's underside a flat of an edge break: across the counter
    lie the shoulder's cut, its rise, that flat and the right corner's
    inner cut. (The shoulder starts rise/full of its way out of the stem,
    so the rise it has room for is its own share of what is left.)"""
    p = g.p
    k = p.sd / 2 ** 0.5
    counter = (x_right - p.sv / 2 - inner_leg(p, g.sh)) - (xs + p.sv / 2)
    return (counter - p.c - k + p.sv / 2 + g.sh / 2) / (1 + (p.sv / 2 + k - p.c) / full)


@low('h', 8, 2)
def h(g):
    f = Frame(g, 8, 'asc')
    g.stroke(f.P(1, 0), f.P(1, 13))
    arch, cut = shoulder(g, f, f.X(1), f.X(7))
    g.stroke(*arch, f.P(7, 0), start=cut)


def _dot(g, f, x):
    """The tittle: a square as wide as the stem, centred between x-height and
    ascender, but never closer to the x-height than 0.4 of a stem."""
    p = g.p
    s = p.dot()
    yc = max((p.xh + p.asc) / 2, p.xh + 0.4 * s + s / 2)
    g.stroke((x, yc - s / 2, s), (x, yc + s / 2))


def _mono_foot(g, f, x, u):
    g.stroke((x - 3 * u, f.Y(1)), (x + 3 * u, f.Y(1)))


@low('i', 2, 1, width=lambda p: p.sv)
def i(g):
    if g.p.mono:                                            # flag at the x-height, foot on the line
        f = Frame(g, 9, 'asc', top=g.p.asc + g.p.sv)
        u = g.W / 9
        x = g.W / 2 + u / 2
        g.stroke((x - 3 * u, f.Y(8)), (x, f.Y(8)), (x, 0))
        _mono_foot(g, f, x - u / 2, u)
        _dot(g, f, x)
        return
    f = Frame(g, 2, 'asc', top=g.p.asc + g.p.sv)
    g.stroke(f.P(1, 0), f.P(1, 9))
    _dot(g, f, f.X(1))


J_FRAME = 5     # the j's frame, in modules: its hook three modules of white across, room for its two corners


@low('j', J_FRAME, 1)
def j(g):
    if g.p.mono:
        f = Frame(g, 9, 'asc', top=g.p.asc + g.p.sv)
        p, u = f.p, g.W / 9
        x = g.W / 2 + 1.5 * u
        g.stroke((x - 3 * u, f.Y(8)), (x, f.Y(8)), B(x, f.Y(-2)), B(f.X(1), f.Y(-2)), (f.X(1), -p.desc + beak_depth(p, g.sh)))
        _dot(g, f, x)
        return
    f = Frame(g, J_FRAME, 'asc', top=g.p.asc + g.p.sv)
    p = f.p
    xs = f.X(J_FRAME - 1)
    g.stroke((xs, f.Y(9)), B(xs, f.Y(-2)), B(*f.P(1, -2)), (f.X(1), -p.desc + beak_depth(p, g.sh)))
    _dot(g, f, xs)


@low('k', 8, 1)
def k(g):
    f = Frame(g, 8, 'asc')
    g.stroke(f.P(1, 0), f.P(1, 13))
    for pts, a, b in k_arms(g, f.X(1), f.W, f.p.xh):
        g.stroke(*pts, start=a, end=b)
    g.clip = (0, -f.p.desc, f.W, f.p.asc)


L_TAIL = 2.0    # modules of white the l's tail runs past its stem: room for its corner and a flat past it at every weight


@low('l', 2 + L_TAIL, 1)
def l(g):
    if g.p.mono:
        f = Frame(g, 9, 'asc')
        u = g.W / 9
        x = g.W / 2 + u / 2
        g.stroke((x - 3 * u, f.Y(12)), (x, f.Y(12)), (x, 0))
        _mono_foot(g, f, x - u / 2, u)
        return
    # A stem and the t's foot: the tail tells l from I, i and 1
    # (docs/research/legibility.md). Until 1.017 it also carried the 1's
    # flag at the top, a module to the left of the stem: over the x-height,
    # where spacing lets a part hang into its neighbour's room, the flag
    # stood 12 units from the body's edge at Regular for a stem's 88 and 21
    # outside it at Black, and whatever stood before an l with ink that high
    # was crowded (F E T K and the l 0.3 of the white between two stems,
    # 0.55 to 0.85 in faces of this kind; i d H and the l a third at Black,
    # theirs 0.84 to 1.0). No longer than it was thick, it read as a bump on
    # the stem, and three modules of tail made the l the widest of its kind.
    f = Frame(g, 2 + L_TAIL, 'asc')
    g.defaults_used['stem'] = f.X(1)
    g.stroke(f.P(1, 13), B(*f.P(1, 1)), f.P(2 + L_TAIL, 1))


@low('m', 12, 3, width=letter_width(13, 3))
def m(g):
    # Its counters are seven eighths of the n's (the master's twelve modules
    # made them three quarters, and the m the darkest of the arch letters:
    # its advance 1.36 of the n's, where faces of this kind give it 1.44 to
    # 1.59; tools/letter_colour.py)
    f = Frame(g, 12, 'lower')
    g.stroke(f.P(1, 0), f.P(1, 9))
    for xs, xr in ((f.X(1), f.X(6)), (f.X(6), f.X(11))):
        arch, cut = shoulder(g, f, xs, xr, joined=xs > f.X(1))
        if xs > f.X(1):
            # the middle stem stands up to where its own arch leaves it: the
            # first arch's corner is cut deeper than the bar is thick at the
            # heavy weights, and took a wedge out of the stem under the
            # second (its counter's corner broken 9 units for the first's 44)
            g.stroke((xs, f.Y(4)), (xs, min(arch[0][1], f.Y(8) - g.sh / 2)))
        g.stroke(*arch, (xr, 0), start=cut)


@low('n', 8, 2)
def n(g):
    f = Frame(g, 8, 'lower')
    g.stroke(f.P(1, 0), f.P(1, 9))
    arch, cut = shoulder(g, f, f.X(1), f.X(7))
    g.stroke(*arch, f.P(7, 0), start=cut)


@low('o', 8, 2)
def o(g):
    f = Frame(g, 8, 'lower')
    g.stroke(B(*f.P(1, 1)), B(*f.P(7, 1)), B(*f.P(7, 8)), B(*f.P(1, 8)), closed=True)


@low('p', 8, 2)
def p_(g):
    f = Frame(g, 8, 'lower')
    g.stroke(f.P(1, -3), f.P(1, 9))
    g.stroke(f.P(1, 8), B(*f.P(7, 8)), B(*f.P(7, 1)), f.P(1, 1), closed=True)


@low('q', 8, 2)
def q(g):
    f = Frame(g, 8, 'lower')
    g.stroke(f.P(7, -3), f.P(7, 9))
    g.stroke(f.P(7, 8), B(*f.P(1, 8)), B(*f.P(1, 1)), f.P(7, 1), closed=True)


# The r keeps its master's share of the line at every weight: eight ninths
# of the H's width, the n's eight modules. With one stem and six modules of
# white it had grown as the white of a letter does toward Thin while the n,
# with two stems, lost them: a third wider than the n at Thin (1.37), a
# tenth at Regular (1.09), its arm long for the letter (the owner,
# 2026-11-10: trim it back at the lighter weights); now 1.08 and 1.02.
@low('r', 8, 1, width=share_width(6))
def r(g):
    f = Frame(g, 8, 'lower')
    p = g.p
    # In the monospaced cell the r stands two and a half modules in, on a foot.
    dx = 2.5 * g.W / 9 if p.mono else 0.0
    xs = f.X(1) + dx
    g.stroke((xs, 0), (xs, p.xh))
    # The shoulder: a 45-degree stroke from the stem to the arm, leaving a
    # notch under the arm (the 1's flag, turned).
    k = p.sd / 2 ** 0.5
    y8, y6 = f.Y(8), f.Y(6)
    x6 = xs + p.sv / 2 + k - p.c                             # starts an edge break into the stem
    rise = y8 - y6
    if p.mono:
        # in the cell the arm is short: the shoulder rises no further than
        # leaves the arm's underside an edge break of flat before its end's
        # cut (at Bold the diagonal ran into the end itself, and left it a
        # face of 7 units)
        rise = min(rise, max(0.0, f.X(8) - (k - g.sh / 2) - 2 * p.c - x6))
    g.stroke((x6, y8 - rise), (x6 + rise, y8), f.P(8, 8), start='h')
    if p.mono:                                              # a foot, as the 1's
        u = g.W / 9
        g.stroke((xs - 2.5 * u, f.Y(1)), (xs + 2.5 * u, f.Y(1)))


@low('s', 8, 2)
def s(g):
    """The s: three bars and two beaks. Each end turns through a cut
    corner into the c's short terminal, the upper one down over the spine's
    right corner and the lower one up under its left, as the capital's do;
    the two whites are alike, and the spine, the inner bar, is the one that
    thins (bars3).

    Until 1.017 both ends were square and the upper white was two thirds
    of the lower (the spine on the fifth module)."""
    g.stack(3, g.p.xh, ratio=0.75)
    f = Frame(g, 8, 'lower')
    p = g.p
    top, mid, foot = bars3(g)
    white = (p.xh - top - mid - foot) / 2
    y1, ym, yt = foot / 2, foot + white + mid / 2, p.xh - top / 2
    g.stroke((f.X(7), p.xh - beak(g, top)), B(f.X(7), yt, None, top), B(f.X(1), yt), B(f.X(1), ym, None, mid),
             B(f.X(7), ym), B(f.X(7), y1, None, foot), B(f.X(1), y1), (f.X(1), beak(g, foot)))


@low('t', NARROW, 1)
def t(g):
    if g.p.mono:
        f = Frame(g, 9, 'asc')
        g.stroke(f.P(3, 11), B(*f.P(3, 1)), f.P(8.5, 1))
        g.stroke(f.P(0.5, 8), f.P(8, 8))
        return
    f = Frame(g, NARROW, 'asc')
    g.stroke(f.P(2, 11), B(*f.P(2, 1)), f.P(NARROW, 1))
    g.stroke(f.P(0, 8), f.P(NARROW - 1, 8))


@low('u', 8, 2)
def u(g):
    f = Frame(g, 8, 'lower')
    g.stroke(f.P(1, 9), B(*f.P(1, 1)), f.P(7, 1))
    g.stroke(f.P(7, 0), f.P(7, 9))


V_HANG = 1.0    # how far a lowercase point (v w) hangs under the baseline, in edge breaks


def _vee(f):
    """Centreline height of a lowercase point (v w), its arms at 2:1, and
    the line it is cut on: an edge break under the baseline (V_HANG), where
    the point is a break and a half wide.

    The point hangs: until 1.017 it ran on under the line 38 units at
    Regular and 73 at Black to a flat one break wide, half the capitals'
    and the sharpest end in the alphabet. Cut on the baseline (a first
    1.017) the letters lost the drop that was theirs; the point keeps it
    for one break, 22 units at Regular and 44 at Black, and ends blunt."""
    p = f.p
    return -p.c + f.k, -V_HANG * p.c


@low('v', 8, 2)
def v(g):
    f = Frame(g, 8, 'lower')
    p, W = f.p, f.W
    xl, xr = f.X(1), f.X(7)
    ya, cut = _vee(f)
    # 2:1 arms (the 7's slope): a 45-degree gable in an x-height leaves too
    # little diagonal, and the v reads as a u (docs/research/legibility.md)
    yt = min(ya + 2 * (W / 2 - xl), p.xh)
    g.stroke((xl, p.xh), (xl, yt), (W / 2, ya), (xr, yt), (xr, p.xh))
    g.clip = (0, cut, W, p.xh)
    g.butt += (('y', cut),)                                  # the point's end is the cut itself, flat


@low('w', 14, 3, width=letter_width(12.6, 3))
def w(g):
    # A tenth narrower than its master's fourteen modules: at 1.46 of the
    # n's advance it was wider than any face of its kind draws it (1.24 to
    # 1.42) and the lightest letter of the alphabet after the r
    f = Frame(g, 14, 'lower')
    p, W = f.p, f.W
    xl, xm, xr = f.X(1), W / 2, f.X(13)
    q1, q3 = (xl + xm) / 2, (xm + xr) / 2
    ya, cut = _vee(f)
    yt = min(ya + 2 * (q1 - xl), p.xh)                      # 2:1, as the v
    g.stroke((xl, p.xh), (xl, yt), (q1, ya), (xm, yt), (q3, ya), (xr, yt), (xr, p.xh))
    # the middle stroke stands in the peak, down to the sixth module, and
    # never over it: where the peak is lower than that (Thin to Regular) it
    # was a post on the peak, 65 units at Thin, a stub at Light and at
    # Regular a spearhead 43 units tall with a barb of 11 each side
    if yt > f.Y(6):
        g.stroke((xm, yt), (xm, f.Y(6)))
    # the middle peak ends as the corner rule ends a point, a break's chord
    # across it; from ExtraBold it reaches the x-height, and cut there first
    # it was left a flat of a few units that the rule made two crumbs of
    g.clip = (0, cut, W, p.xh + p.c)
    g.butt += (('y', cut),)                                  # the point's end is the cut itself, flat


def x_strokes(g, xl, xr, W, H):
    """The X and the x: two 45-degree strokes between vertical stubs, each
    stepping sideways by a jog where they cross (the 2's notch, twice):
    upper halves pass the centre a half jog early, lower halves a half jog
    late. The step is the watch's pixel; as the strokes grow past it the
    crossing takes it up and the kinks go."""
    p = g.p
    J = jog(p)
    step = min(J, g.sh)
    up, lo = (W + H - J) / 2, (W + H + J) / 2                # x + y on the falling stroke
    g.stroke((xl, H), (xl, up - xl), (up - H / 2, H / 2, step), (lo - H / 2, H / 2), (xr, lo - xr), (xr, 0))
    # the rising stroke, mirrored: x -> W - x
    g.stroke((xr, H), (xr, up - xl), (W - (up - H / 2), H / 2, step), (W - (lo - H / 2), H / 2),
             (xl, lo - xr), (xl, 0))


@low('x', 8, 2)
def x(g):
    """The capital's drawing in the x-height (until 1.017 the x crossed
    plain at every weight, and the X stepped)."""
    f = Frame(g, 8, 'lower')
    x_strokes(g, f.X(1), f.X(7), f.W, f.p.xh)


Y_FLAT = 1.0     # modules: the flat the y's arm lands on before the stem


@low('y', 8, 2)
def y(g):
    """The y: a bowl open at the top whose left corner is cut all the way
    across, and the g's hook. The arm comes down the left stem, turns at 45
    degrees and lands flat on the baseline, a module short of the stem: it
    meets the stem as the p's bowl meets its own and the g's its own, a
    horizontal on the baseline, and the stem runs on down into the hook as
    one line.

    Until 1.017 the arm ran straight into the stem, its lower edge an edge
    break above the baseline: a diagonal entering a vertical takes a stem
    and a fifth of the stem's height to do it (252 units at Black), with
    the hook's corner straight under it, and from Bold the three made one
    lump at the foot of the letter."""
    f = Frame(g, 8, 'lower')
    p = f.p
    xl, xr = f.X(1), f.X(7)
    leg = max(p.leg, (xr - p.sv / 2) - Y_FLAT * p.m - xl)
    g.stroke((xl, p.xh), B(xl, f.Y(1), leg), (xr, f.Y(1)))
    hook(g, f)
    g.butt += crotch_butt(g, f.Y(1))


@low('z', 8, 1)
def z(g):
    f = Frame(g, 8, 'lower')
    p, W, k_ = f.p, f.W, f.k
    g.stroke(f.P(0, 8), f.P(8, 8))
    g.stroke(f.P(0, 1), f.P(8, 1))
    J = jog(p)
    a_up = W - (p.xh - g.sh - p.c) - k_                     # x - y
    a_lo = a_up - J
    yj = f.Y(4.5)
    step = min(J, g.sh)
    y0, y1 = f.Y(8), f.Y(1)
    xl = f.X(1)
    # Where the diagonal reaches the left edge; in a narrow cell it meets the
    # bottom bar first, and lands on it there (running on inside the bar)
    # rather than below it: the same points either way, so the masters vary.
    ye = xl - a_lo
    g.stroke((y0 + a_up, y0), (yj + a_up, yj, step), (yj + a_lo, yj), (max(xl, y1 + a_lo), max(ye, y1)),
             (xl, y1), start='h')


@glyph('dotlessi', '\u0131', lambda p: p.sv, kind='lower')
def dotlessi(g):
    f = Frame(g, 2, 'lower')
    g.stroke(f.P(1, 0), f.P(1, 9))


@glyph('uni0237', '\u0237', letter_width(J_FRAME, 1), kind='lower')
def dotlessj(g):
    f = Frame(g, J_FRAME, 'lower')
    p = f.p
    xs = f.X(J_FRAME - 1)
    g.stroke((xs, f.Y(9)), B(xs, f.Y(-2)), B(*f.P(1, -2)), (f.X(1), -p.desc + beak_depth(p, g.sh)))
