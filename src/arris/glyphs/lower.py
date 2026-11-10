"""Lowercase a-z, built from their pixel masters (``arris.masters.LOWER``).

Module coordinates: x-height 9, ascender 13, descender -3 (see letterframe).
The same moves as the capitals and figures: beaks on c and j, the 2's notch
in z, a notched shoulder on r (the 1's flag, turned) which every arch
carries, and every bowl half as deep where it meets its stem, arches that
meet in a V on m, gables under high walls on v, w and y.
"""
from __future__ import annotations

import functools

from ..draw import B, Opening, glyph
from ..params import inner_leg, outer_leg, white_own
from .figures import STACK_MIN, beak_depth, jog
from .letterframe import ARM, Frame, heft, k_arms, least_white, letter_width, narrowed, own_width, share_width, white_scale, zone


def low(char, wm, stems, width=None, openings=(), arm=ARM):
    return glyph(char, char, width or letter_width(wm, stems, arm), kind='lower', openings=openings)


def placed(W, H, pts, mirror=False, flip=False):
    """A drawing's points mirrored left to right and/or flipped top to
    bottom in a body ``W`` wide and ``H`` tall (both: turned half round)."""
    X = (lambda x: W - x) if mirror else (lambda x: x)
    Y = (lambda y: H - y) if flip else (lambda y: y)
    out = []
    for q in pts:
        if q[0] == 'bowl':
            out.append(('bowl', X(q[1]), Y(q[2])) + tuple(q[3:]))
        else:
            out.append((X(q[0]), Y(q[1])) + tuple(q[2:]))
    return out


def turned(W, H, pts):
    """A drawing's points turned half round: the u is the n turned."""
    return placed(W, H, pts, mirror=True, flip=True)


def bowl_join(g, f, stem_left, at_top):
    """A bowl on a stem, joined to it as the n's arch is to its own: at 45
    degrees and with the notch (shoulder) at one join, square at the
    other. The n's arch and right side, closed along the far line, and
    placed: ``stem_left`` False mirrors it, ``at_top`` False flips it.

    The notch stands where the stem runs on past the bowl: at the top of
    the b and the d, under their ascenders, as the h's; at the foot of the
    p, the q and the g, over their descenders. (The a and the u, whose
    stems stop on both lines, have it at the foot: the n turned.)

    The owner, 2026-11-10: the notch came to the u and the a first, "like
    if you took the letter n and flipped it upside down"; then "if we're
    going to do it on the a and the u, then we need to do it on all the
    bowls". Tried at the stem's end first, where Chakra Petch, Tomorrow
    and Turret Road put theirs; he had it flipped, and a bowl's join made
    half as deep as an arch's (BOWL_DROP). Until 1.017 every bowl was a
    closed octagon laid square against its stem.

    The italic's q, g and y take it too, at the foot (the owner: "the
    descender should remain flat but ... a little bit of a crook in the
    bowls ... little teeny weeny notch"); its own a b d p u branch as they
    always have, and its hooks end flat as they always have."""
    arch, cut = shoulder(g, f, f.X(1), f.X(7), drop=BOWL_DROP)
    pts = [*arch, B(*f.P(7, 1)), f.P(1, 1)]
    g.stroke(*placed(f.W, f.p.xh, pts, mirror=not stem_left, flip=not at_top), start=cut)


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


A_RISE = 0.6    # the most the a's bowl rises into its stem, as a share of the bowl's white


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
    # The bowl's foot comes into the stem as the u's does, the n's shoulder
    # turned half round: at 45 degrees, with its notch at the foot of the
    # stem (the owner, 2026-11-10). It rises no more than A_RISE of the
    # bowl's white, so the counter keeps its wall under the bar. Until
    # 1.017 the bowl ran square into the stem on the baseline.
    drop = min(BOWL_DROP, A_RISE * low / (f.Y(8) - f.Y(7)))
    arch, cut = shoulder(g, f, f.X(1), f.X(7), drop=drop)
    g.stroke((f.X(7), yb, inner), B(f.X(1), yb), *reversed(turned(f.W, p.xh, arch)), end=cut)


@low('b', 8, 2)
def b(g):
    f = Frame(g, 8, 'asc')
    g.stroke(f.P(1, 0), f.P(1, 13))
    bowl_join(g, f, stem_left=True, at_top=True)


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
    bowl_join(g, f, stem_left=False, at_top=True)


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


# The letters with one stem and an arm (f t j) are a module narrower than
# their masters: against the n they stood wider than any face of this kind
# sets them (the j 0.65 of the n's advance for 0.41 to 0.49, the t 0.79 for
# 0.53 to 0.69, the f 0.72 for 0.48 to 0.66: review/widths, 2026-11-10),
# and a line with several of them (little, filter, jilt) lost the rhythm
# its stems set.
NARROW = 6      # the f's and the t's frame, in modules (their masters' seven, less one)


def narrow_frame(g):
    """The f's and the t's frame: the stem on its second module, the
    crossbar from the body's left edge to its fifth.

    Past the Regular, where the body gives (letterframe.narrowed), the
    stem stands where it stood in the body the watch's own white gives,
    and the arm, the foot and the crossbar's right end take all that is
    given. The crossbar's stub, left of the stem, is no longer than its
    end's cut and the fill of its crotch need to meet in one plane (f_leg):
    a quarter of what the body gave came off it, and at ExtraBold the two
    came apart in a kink, at Black the bar's right end and the hook's cut
    ran together in a wedge."""
    f = Frame(g, NARROW, 'asc')
    p = g.p
    own = own_width(NARROW, 1)(p) + ARM * heft(p)
    if own > g.W and not p.mono:
        f.xa = [(0, 0.0), (2, p.sv / 2 + (own - p.sv) / 4), (NARROW - 1, g.W - p.sv / 2), (NARROW, g.W)]
    return f


ARM_STUB = 2.6  # edge breaks: the least the f's and the t's crossbar runs past the stem on the arm's side


def narrow_width(p):
    """The f's and the t's body: a one-stem letter's (letter_width), giving
    past the Regular no more than leaves the crossbar ARM_STUB breaks past
    the stem on the arm's side (narrow_frame: the stub on the other side
    gives nothing). Shorter, its end's cut ran into the cut of the hook
    over it (the t's foot under it), a wedge where the bar's end had been:
    from 850, and at Black the two letters keep 19 units of the 41 the
    rule would take."""
    w = letter_width(NARROW, 1)(p)
    own = own_width(NARROW, 1)(p) + ARM * heft(p)
    return min(own, max(w, (own - p.sv) / 4 + 1.5 * p.sv + ARM_STUB * p.c))


@low('f', NARROW, 1, width=narrow_width)
def f_(g):
    """A stem, its hook and a crossbar. The hook at every weight: the top
    as one cut with no arm, tried to SemiBold in 1.017's making with the
    t's foot, was the l's end, and the owner kept it for the l alone
    (2026-11-10: "keep the hooks for the f and the t, and the l stays
    without a hook")."""
    if g.p.mono:
        f = Frame(g, 9, 'asc')
        g.stroke(f.P(3.5, 0), B(*f.P(3.5, 12)), f.P(9, 12))
        g.stroke(f.P(0.5, 8), f.P(8, 8))
        return
    f = narrow_frame(g)
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


BEAK_WHITE = 0.75   # the white a hook's beak keeps under the bowl, as a share of the least white (hook)


def hook(g, f, x_stem=7, x_end=1, white=None, turn=True):
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
    if p.slant or not turn:
        g.stroke(f.P(x_stem, 9), B(f.X(x_stem), yh, None, w), (f.X(x_end), yh))
        return
    # The hook ends as the c's arms do, in a beak: a cut corner and a short
    # terminal turned up, so the swoop is cut at both ends, as the top of
    # the 8 is (the owner, 2026-11-10: "a nice kind of bracketed curve to
    # it, like the top part of the eight"). The beak's tip, a short end and
    # not a bar, keeps BEAK_WHITE of the least white under the bowl's cut
    # corner over it; where even that leaves no room to turn, the hook ends
    # flat as before.
    bottom = -(p.desc + extra)
    over = max(0.0, outer_leg(p, sh=g.sh) - p.sv)           # the bowl's cut corner, over the beak's inner edge
    d = min(beak(g, w), over - bottom - BEAK_WHITE * (least_white(p) if white is None else white))
    # the corner's cut ends an edge break under the beak's end, as the c's
    # does (beak), so the rule turns that flank into a point at every weight
    leg = min(p.leg, d - p.c - (p.sv + w) / 2 + p.sd / 2 ** 0.5)
    if leg < p.c:
        g.stroke(f.P(x_stem, 9), B(f.X(x_stem), yh, None, w), (f.X(x_end), yh))
        return
    g.stroke(f.P(x_stem, 9), B(f.X(x_stem), yh, None, w), B(f.X(x_end), yh, leg), (f.X(x_end), bottom + d))


def g_strokes(g, white=None):
    """The g: its bowl and its hook (``white``: the room the hook leaves
    under the bowl, for a g that carries something there: ǥ's bar)."""
    f = Frame(g, 8, 'lower')
    bowl_join(g, f, stem_left=False, at_top=False)          # (the italic's too; its hook ends flat: hook)
    hook(g, f, white=white)
    g.butt += crotch_butt(g, f.Y(1))


@low('g', 8, 2)
def g_(g):
    g_strokes(g)


def shoulder_enter(p) -> float:
    """How far into its stem a shoulder's diagonal starts: its upper edge
    leaves the stem's side this far over its cut. An edge break, where a
    crotch is filled as the pixel rule fills it; and by as much more as
    the fill is less, so the notch over the shoulder stands on the stem
    where it always did and the join keeps its thickness: the fill went
    from two legs to one in the italic and stops growing at the Regular's
    in both (draw.crotch_fill, draw.fill_leg), and a shoulder still drawn a
    break into its stem lost that ink at its neck, where it is thinnest
    (the cursive r's arm at Black, 0.54 of a stem across where it leaves
    the stem, went to 0.37; the owner, of the smaller inside corners:
    "it's also important that we remain uniform in thickness")."""
    from ..draw import crotch_fill, fill_leg
    was = 2.0 if p.slant else 2.0 - p.optical               # the legs a crotch was filled until 1.017
    return (1.0 + was) * p.c - crotch_fill(p) * fill_leg(p)


def shoulder(g, f, xs, x_right, top=8, drop=None, notch=True, joined=False):
    """An arch's shoulder, as the r's: it leaves the stem at 45 degrees
    ``drop`` modules below the arch (SHOULDER_DROP, two; a bowl's join half
    that, BOWL_DROP; the italic's branch lower), an edge break into the
    stem (shoulder_enter), and leaves a notch under it (the 1's flag,
    turned). Returns the arch's points up to its right corner, and how the
    stroke's start is cut.

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
    drop = SHOULDER_DROP if drop is None else drop
    k = p.sd / 2 ** 0.5
    y_top = f.Y(top)
    full = f.Y(top) - f.Y(top - drop)
    x_full = xs + p.sv / 2 + k - p.c                        # (its room and its rise: as drawn a break into the stem,
    upright = notch and not p.slant                        # the italic keeps its own branch (italic_forms)

    def risen(x_right):
        room = x_right - p.leg - p.c - x_full              # so it goes square where it always did) the diagonal ends clear of the corner
        if upright:
            room = min(room, shoulder_room(g, xs, x_right, full))
        return min(full, max(room, 0.0))
    rise = risen(x_right)
    if upright and not _measuring and rise - g.sh / 2 < p.c:
        # The kink over the shoulder, where the counter has given white
        # (letterframe.white_scale): with no step drawn under the shoulder its
        # diagonal lies inside the arch, cut along the arch's underside, and
        # takes no room from the counter; it rises as far as it did in the
        # counter the watch's own white gives, short of a step that would be
        # drawn (KINK_STEP) and clear of the corner. (The owner, 2026-11-10,
        # of the narrowed n, square from 725 where it had kept its notch to
        # ExtraBold: "preserving the kink ... at later weights to a small
        # degree so that it matches what we had".)
        lost = (x_right - xs - p.sv) * (white_own(p.sv / (2 * p.m)) / white_scale(p) - 1.0)
        if lost > 0:
            clear = (x_right - p.leg - p.c - xs) / (1 + (x_full - xs) / full)
            rise = max(rise, min(risen(x_right + lost), g.sh / 2 + KINK_STEP * p.c, clear))
    plain = [(xs, y_top), B(x_right, y_top)], 'flat'
    if rise < 1e-3 * p.m:
        return plain
    r = rise / full
    x0 = xs + r * (x_full - xs)
    if not notch:
        return [(xs, y_top - rise - (x0 - xs)), (x0 + rise, y_top), B(x_right, y_top)], 'v'
    # deeper into the stem by what its crotch's fill is short (shoulder_enter), as far as leaves the cut
    # under it a flat the outline keeps (a step shorter than an edge break between two 45-degree edges is
    # taken for a miss and closed, geom.JOG: the italic m's arches, which rise half as far as the n's for
    # want of room, lost the step under each at Regular)
    from ..draw import fill_leg
    flat = x0 + k - (xs + p.sv / 2) - fill_leg(p)
    deeper = r * (shoulder_enter(p) - p.c)
    if flat > STEP_KEPT * p.c:
        deeper = min(deeper, flat - STEP_KEPT * p.c)
    x0 -= deeper
    step = rise - g.sh / 2                                  # the diagonal's cut, below the arch's underside
    if upright and step < p.c:
        over = g.sh / 2 + rise - (1 - r) * (p.sv / 2 + k) - r * p.c   # the diagonal's top at the stem's side, below the arch's
        if not joined and over < SHOULDER_NOTCH * p.c:
            return plain
        return [(x0 + step, y_top - g.sh / 2), (x0 + rise, y_top), B(x_right, y_top)], 'h'
    return [(x0, y_top - rise), (x0 + rise, y_top), B(x_right, y_top)], 'h'


# Two rule sets (the owner, 2026-11-10: "you shouldn't be changing the m's and the n's and the r's ... it's
# just a different rule set"). The arches (n h m r) leave their stems two modules under the arch, as they
# always have. A bowl's join (bowl_join, the a, the u, the y) is half as deep: at two modules, at the light
# weights, the bowl stood a long way off its stem and read as a stroke of its own; shown it at two, one and
# 0.6, he chose one.
SHOULDER_DROP = 2.0     # modules below the arch where an arch's shoulder leaves its stem
STEP_KEPT = 1.1         # edge breaks: the flat a shoulder's cut keeps past its fill (over geom.JOG, so the outline keeps the step)
KINK_STEP = 0.999       # edge breaks: the most a shoulder kept for its kink alone rises past the arch's underside (under one: no step is drawn)
BOWL_DROP = 1.0         # the same for a bowl's join to its stem
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
J_SLOT = 1.0    # edge breaks: the least white between the j's stem and the end of its hook


def j_width(p):
    """The j's body: a one-stem letter's (letter_width), giving past the
    Regular no more than leaves J_SLOT breaks of white between its stem
    and the end of its hook: narrower, the fill of that crotch shrank to a
    chord of 4 units at Black, a crumb on the stem's side."""
    return max(letter_width(J_FRAME, 1)(p), 2 * p.sv + J_SLOT * p.c)


@low('j', J_FRAME, 1, width=j_width)
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


def _toe(p, sh):
    """The thickness the l's cut is drawn at: three edge breaks (the
    weight's bar, where that is less). Its end's own break then takes up
    all of its top, so the corner's cut runs straight into the end's face,
    two breaks up."""
    return min(3 * p.c, sh)


def kick_reach(p, sh):
    """From the l's stem's centre to the end of its cut: the stem's end
    turned through the one cut a corner takes and stopped there, where the
    end stands an edge break tall over its own break."""
    return sh / 2 + p.leg + p.sd / 2 ** 0.5 - _toe(p, sh) + p.c


def l_width(p):
    """The l's body: its stem and its cut (kick_reach), at every weight."""
    return p.sv / 2 + kick_reach(p, p.sh * p.low)


@low('l', 3, 1, width=l_width)
def l(g):
    if g.p.mono:
        f = Frame(g, 9, 'asc')
        u = g.W / 9
        x = g.W / 2 + u / 2
        g.stroke((x - 3 * u, f.Y(12)), (x, f.Y(12)), (x, 0))
        _mono_foot(g, f, x - u / 2, u)
        return
    # A stem and one cut at its foot, at every weight: the corner the t's
    # foot turns through, run on to the baseline and ended upright with no
    # foot after it (the owner, 2026-11-10: "only one single notch", and
    # "the l stays without a hook"; the f and the t keep theirs). The cut
    # tells l from I, i and 1 (docs/research/legibility.md). The corner is
    # drawn on a line half its end's thickness (_toe) over the baseline, its
    # leg longer by what that thickness is short of the bar's, so the cut
    # lies where a foot's would.
    #
    # Until 1.017 the l carried the 1's flag at the top, a module to the
    # left of the stem, and three modules of tail: over the x-height, where
    # spacing lets a part hang into its neighbour's room, the flag stood 12
    # units from the body's edge at Regular for a stem's 88 and 21 outside
    # it at Black, and whatever stood before an l with ink that high was
    # crowded (F E T K and the l 0.3 of the white between two stems, 0.55
    # to 0.85 in faces of this kind; i d H and the l a third at Black,
    # theirs 0.84 to 1.0); the tail made the l the widest of its kind (0.65
    # of the n's advance for their 0.40 to 0.51).
    f = Frame(g, 3, 'asc')
    p = f.p
    xs = p.sv / 2
    g.defaults_used['stem'] = xs
    h = _toe(p, g.sh)
    g.stroke((xs, p.asc), B(xs, h / 2, p.leg + (g.sh - h) / 2, h), (g.W, h / 2))
    g.clip = (0, 0, g.W, p.asc)


M_BODY = 13             # modules: the m's body (its drawing's master is twelve)


@low('m', 12, 3, width=letter_width(M_BODY, 3))
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
    bowl_join(g, f, stem_left=True, at_top=False)


@low('q', 8, 2)
def q(g):
    f = Frame(g, 8, 'lower')
    g.stroke(f.P(7, -3), f.P(7, 9))
    bowl_join(g, f, stem_left=False, at_top=False)          # (the italic's too: it has no q of its own)


# The r's share of the line: six ninths of the H's width to the Regular,
# growing to seven at Black. With one stem and six modules of white it had
# grown as the white of a letter does toward Thin while the n, with two
# stems, lost them: a third wider than the n at Thin, a tenth at Regular,
# its arm long for the letter, and the owner had it trimmed twice, a module
# each time, to six ninths (2026-11-10). At one share for every weight the
# arm then shrank as the stem grew: under the shoulder's diagonal, as thick
# as a stem, nothing of the arm itself was left at Black, a stub on the
# stem's corner (the owner: "a little tiny clown nose"). Other families'
# r grows against their n as they get bolder (its advance 0.65 of the n's
# at Regular, 0.69 at Black, across 60 families: tools/width_survey.py),
# and so does this one now: 0.75 and 0.80, an arm of a stem and a half past
# the stem at Black for 1.1. (Shown it at eight ninths, seven, six growing
# to eight, six growing to seven and six, the owner chose this; and shown
# the arm with a flat kept under it by a shorter shoulder, past SemiBold
# where the shoulder's underside runs to the body's edge: "It looks great
# ... don't fix the R".)
R_SHARE = (6.0, 7.0)    # ninths of the H's width: to the Regular, at Black
R_BLACK = 85.0          # units the stem gains from Regular to Black


def r_width(p):
    a, b = R_SHARE
    return share_width(a + (b - a) * min(1.0, heft(p) / R_BLACK))(p)


@low('r', 8, 1, width=r_width)
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
    y8, y6 = f.Y(8), f.Y(8 - SHOULDER_DROP)
    x6 = xs + p.sv / 2 + k - p.c                             # starts an edge break into the stem
    rise = y8 - y6
    if p.mono:
        # in the cell the arm is short: the shoulder rises no further than
        # leaves the arm's underside an edge break of flat before its end's
        # cut (at Bold the diagonal ran into the end itself, and left it a
        # face of 7 units)
        rise = min(rise, max(0.0, f.X(8) - (k - g.sh / 2) - 2 * p.c - x6))
    x6 -= shoulder_enter(p) - p.c                           # and deeper by what its crotch's fill is short (shoulder_enter)
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


@low('t', NARROW, 1, width=narrow_width)
def t(g):
    """A stem, a crossbar and its foot, a module past the crossbar's end,
    at every weight (the f turned over: see f_)."""
    if g.p.mono:
        f = Frame(g, 9, 'asc')
        g.defaults_used['stem'] = f.X(3)
        g.stroke(f.P(3, 11), B(*f.P(3, 1)), f.P(8.5, 1))
        g.stroke(f.P(0.5, 8), f.P(8, 8))
        return
    f = narrow_frame(g)
    g.defaults_used['stem'] = f.X(2)                        # (extra_latin._slot reads it for the ŧ's bar)
    g.stroke(f.P(2, 11), B(*f.P(2, 1)), f.P(NARROW, 1))
    g.stroke(f.P(0, 8), f.P(NARROW - 1, 8))


@low('u', 8, 2)
def u(g):
    """The n turned half round: its bowl leaves the right stem as the n's
    arch leaves the left, at 45 degrees and with the notch (shoulder), here
    at the foot (the owner, 2026-11-10: "add a little notch into both the u
    and the lower part of the a, like if you took the letter n and flipped
    it upside down"). Until 1.017 its bowl ran square into the stem on the
    baseline."""
    f = Frame(g, 8, 'lower')
    turn = lambda pts: turned(f.W, f.p.xh, pts)
    g.stroke(*turn([f.P(1, 0), f.P(1, 9)]))
    arch, cut = shoulder(g, f, f.X(1), f.X(7), drop=BOWL_DROP)
    g.stroke(*turn([*arch, f.P(7, 0)]), start=cut)


V_HANG = 1.0    # how far a lowercase point (v w) hangs under the baseline, in edge breaks
V_FLAT = 1.5    # the width of the upright v's point where it is cut, in edge breaks (the 2:1 point's, by its slope)


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


def _point(f):
    """Centreline height of a 45-degree point (the upright v, the y's
    join) and the line it is cut on: it hangs an edge break under the
    baseline as the 2:1 point does (_vee) and is as wide there, V_FLAT
    breaks. (Its outer point lies f.k under the centre line's.)"""
    p = f.p
    return -(V_HANG + V_FLAT / 2) * p.c + f.k, -V_HANG * p.c


def _w_width(p):
    return letter_width(12.6, 3)(p)


def gable_run(p, cell=None):
    """A lowercase gable's arm on the centre line, from its wall to its
    point: the w's, a quarter of the white between its walls. The walls of
    v, w and y all turn into their 45-degree arms this far above the point
    (the owner, 2026-11-10: "where the crook occurs needs to be
    consistent"). ``cell``: the body in Arris Mono, where every letter is
    one width."""
    with zone('lower'):                                     # (a lowercase letter's white, whoever asks)
        return ((cell if p.mono and cell else _w_width(p)) / 2 - p.sv / 2) / 2


def v_width(p):
    """The v: as wide as its two arms. Its walls bend where the w's do and
    its arms still meet in a point, so it is narrower than the eight
    modules it had (0.8 of the n; the owner chose it over a flat foot, over
    longer arms on the w and over two heights). The italic's keeps its
    master's width, and Arris Mono's the cell."""
    if p.slant or p.mono:
        return letter_width(8, 2)(p)
    return p.sv + 2 * gable_run(p)


@low('v', 8, 2, width=v_width)
def v(g):
    f = Frame(g, 8, 'lower')
    p, W = f.p, f.W
    xl, xr = f.X(1), f.X(7)
    ya, cut = _vee(f) if p.slant else _point(f)
    # High walls over a 45-degree point, the capital's drawing in the
    # x-height (the owner, 2026-11-10: "it needs to have the 45 degrees
    # with the high walls"); the italic keeps its 2:1 arms, the 7's slope,
    # which he loves in the cursive. Until 1.017 the upright's were 2:1 as
    # well, because a 45-degree gable reads closer to the u (the measure is
    # in docs/DESIGN.md).
    yt = min(ya + 2 * (W / 2 - xl), p.xh) if p.slant else ya + (W / 2 - xl)
    g.stroke((xl, p.xh), (xl, yt), (W / 2, ya), (xr, yt), (xr, p.xh))
    g.clip = (0, cut, W, p.xh)
    g.butt += (('y', cut),)                                  # the point's end is the cut itself, flat


W_POST = 5.25   # modules: how high the w's middle stroke stands (the capital's seven of twelve, in the x-height)


@low('w', 14, 3, width=letter_width(12.6, 3))
def w(g):
    # A tenth narrower than its master's fourteen modules: at 1.46 of the
    # n's advance it was wider than any face of its kind draws it (1.24 to
    # 1.42) and the lightest letter of the alphabet after the r
    f = Frame(g, 14, 'lower')
    p, W = f.p, f.W
    xl, xm, xr = f.X(1), W / 2, f.X(13)
    q1, q3 = (xl + xm) / 2, (xm + xr) / 2
    if p.slant:
        # the italic's: 2:1 arms, the 7's slope, and the middle stroke in
        # the peak down to the sixth module, never over it (where the peak
        # is lower than that it was a post on the peak, a stub, a spearhead)
        ya, cut = _vee(f)
        yt = min(ya + 2 * (q1 - xl), p.xh)
        g.stroke((xl, p.xh), (xl, yt), (q1, ya), (xm, yt), (q3, ya), (xr, yt), (xr, p.xh))
        if yt > f.Y(6):
            g.stroke((xm, yt), (xm, f.Y(6)))
    else:
        # the capital's build in the x-height: high walls, 45-degree
        # valleys, and its middle stroke standing on the peak (the owner,
        # 2026-11-10: "if we're going to modify the v and the y then we
        # should definitely do the w"). Until 1.017 its arms were at 2:1.
        ya, cut = _point(f)
        yt = ya + (q1 - xl)
        g.stroke((xl, p.xh), (xl, yt), (q1, ya), (xm, yt), (q3, ya), (xr, yt), (xr, p.xh))
        g.stroke((xm, yt), (xm, f.Y(W_POST)))
    # the points end as the corner rule ends a point, a break's chord
    # across each; cut first on the x-height the middle was left a flat of
    # a few units that the rule made two crumbs of
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


def _line_runs(name, p, y, width=None):
    """The ink a glyph lays along the level line at ``y``, left to right."""
    from shapely.geometry import LineString

    from ..draw import draw
    from ..geom import rings_to_shapely
    cut = rings_to_shapely(draw(name, p, width=width).rings()).intersection(LineString([(-1e4, y), (1e4, y)]))
    return sorted((s.bounds[0], s.bounds[2]) for s in getattr(cut, 'geoms', [cut]) if s.length > 1)


_measuring = []    # set while the y is being measured for its own width: a drawing made meanwhile takes its master's


def y_width(p):
    """The y: as wide as leaves its foot, the flat between its arm and its
    join, as long as the flat on top of the m's arch (the owner,
    2026-11-10: "measuring the top of the m and making the flat part that
    long"). Read off the two drawings: the m's last arch along the
    x-height, the y in its master's width along the baseline; what the y's
    flat has over the m's comes off its width. The italic's and Arris
    Mono's keep their master's.

    Past the Regular, where the white gives way (letterframe.white_scale),
    the two are read in the bodies the watch's own white gives them, and
    the y then gives the share of its body the n gives (narrowed), as a
    one-stem letter does. The top of a narrower m's arch is no shorter (its
    shoulder and the notch between its arches take the loss: 231 units at
    Black for 216), and a y measured on it gave nothing: a ninth wider
    than the n at Black, where it had stood a fortieth wider."""
    if p.slant or p.mono or p.m < 2 or _measuring:          # (the watch's own drawing, in modules, too)
        return letter_width(8, 2)(p)
    with zone('lower'):
        return _y_width(p) * narrowed(p)


@functools.lru_cache(maxsize=None)
def _y_width(p):
    w0 = own_width(8, 2)(p)
    _measuring.append(p)
    try:
        a, b = _line_runs('m', p, p.xh - 0.5, width=own_width(M_BODY, 3)(p))[-1]
        foot = _line_runs('y', p, 0.5, width=w0)
    finally:
        _measuring.pop()
    flat = foot[0][1] - foot[0][0] - (p.sv if len(foot) == 1 else 0.0)   # (one piece where the join is square: less the stem)
    return w0 - (flat - (b - a))


@low('y', 8, 2, width=y_width)
def y(g):
    """The y: the v's left arm, a wall and 45 degrees, come into a stem as
    a bowl comes into its own, with the bowls' notch at the foot
    (BOWL_DROP), and the stem run on down into the g's hook. Its wall bends
    where the v's and the w's do (gable_run) and its foot is as long as
    the top of the m's arch (y_width).

    The owner, 2026-11-10: "make a g like it is today and ... take a v and
    then join it such that it has a little bit of a notch to it like the
    bowls". In 1.017's making it was first the v's body with its right arm
    run on as a tail, after Turret Road's ("the y does not have chamfering
    on its lower portion"); until 1.017 a bowl open at the top, its left
    corner cut all the way across to a flat a module short of the stem."""
    f = Frame(g, 8, 'lower')
    p = f.p
    xl, y1 = f.X(1), f.Y(1)
    ya, _ = _point(f)
    arch, cut = shoulder(g, f, f.X(1), f.X(7), drop=BOWL_DROP)
    join = turned(f.W, p.xh, arch)[:-1]                     # (the notch's cut,) where the foot leaves the flat
    d = min(ya + gable_run(p, g.W) - y1, join[-1][0] - xl - p.c)
    g.stroke((xl, p.xh), (xl, y1 + d), (xl + d, y1), *reversed(join), end=cut)
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


@glyph('uni0237', '\u0237', j_width, kind='lower')
def dotlessj(g):
    f = Frame(g, J_FRAME, 'lower')
    p = f.p
    xs = f.X(J_FRAME - 1)
    g.stroke((xs, f.Y(9)), B(xs, f.Y(-2)), B(*f.P(1, -2)), (f.X(1), -p.desc + beak_depth(p, g.sh)))
