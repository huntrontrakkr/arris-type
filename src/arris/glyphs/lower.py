"""Lowercase a-z, built from their pixel masters (``arris.masters.LOWER``).

Module coordinates: x-height 9, ascender 13, descender -3 (see letterframe).
The same moves as the capitals and figures: beaks on c and j, the 2's notch
in z, a notched shoulder on r (the 1's flag, turned) which every arch
carries, and every bowl half as deep where it meets its stem, arches that
meet in a V on m, gables under high walls on v, w and y.
"""
from __future__ import annotations

import functools

from ..draw import REGISTRY, B, Opening, glyph
from ..params import inner_leg, outer_leg, white_floor, white_own
from .figures import BAY_WHITE, STACK_MIN, beak_depth, jog
from .letterframe import ARM, Frame, k_arms, least_white, letter_width, narrowed, own_width, share_width, white_scale, zone


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


EVEN = 1.0      # the closed end's bar as a share of the open end's, at least (bars3): the two are one thickness


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
    inner = max(STACK_MIN * g.sh0, 2 * stacked - lead)
    if g.p.optical and stacked < EVEN * lead:
        # Past ExtraBold the inner bar is at its least and the closed end gave alone: at a stem of 200 the e's
        # top was 89 units over a bar of 104 and an arm of 148, 0.44 of a stem beside 0.74, and the a's foot
        # the same (the owner, 2026-11-12: "at black the e. And the a in the middle needs to be about the
        # same size too"). The two outer bars share it from there, and share it alike (EVEN): the bar the a's
        # hook hangs from is the bar every letter of the lowercase stands on (draw._start), and with the closed
        # end at nine tenths of it, as the e's top is of its foot in other families' Blacks, the a's foot and
        # the e's top stood 12 units thinner than the bars of the o, the c and the s beside them (the owner,
        # 2026-11-12, of o c e a s: "it's no longer aligned appropriately. Is that because it's not divvied up
        # correctly between its top and the bottom ...? And if so, everything needs to be rebalanced").
        # (and the three take no more than the stack shares out: where the inner bar stood at its least the
        # open end's whole weight came off the two whites)
        rest = min(lead + stacked, 3 * stacked - inner)
        lead = rest / (1 + EVEN)
        stacked = rest - lead
        g.sh_k *= stacked / g.sh                            # (the letter's own horizontal is the closed end's: what is drawn without a width)
    return lead, inner, stacked


@functools.lru_cache(maxsize=512)
def hook_ref(p):
    """(bar, reach, corner's leg, inner bar) of the hook the a and the e
    are drawn with at ``p``: the bar it hangs from (the open end's, bars3,
    as their closed counters' rule leaves it), how far its end stands from
    the line the bar lies on (beak_in), and the bar between their storeys. The c and the s take it from them, so
    the four hang their hooks from one bar and end them on one line (the
    owner, 2026-11-12, of c a e s side by side at ExtraBold and Black: "all
    these letters have hooks and none of them are completely aligned ... a
    couple points off from each other", and of which was to move: "a and e
    are perfect. C needs to change"). None where the letters keep the
    zone's own bar (the watch's drawing)."""
    if not p.optical or p.slant:                            # (the italic keeps its own strokes: draw._start)
        return None
    from ..draw import _as_own, draw
    with _as_own():                                         # (the e as a letter of its own, whoever asks first)
        return draw('e', p).hook


def spine3(g):
    """(top, spine, foot, white): the s, whose two ends are both open. In
    Arris it is drawn on the a's and the e's bars (hook_ref): both arms
    the bar their hooks hang from, the spine their inner bar, and so its
    two whites theirs: the three stand on one set of lines at every
    weight. Until 1.017 the upper arm kept the zone's weight and the lower
    took the stack's, 12 units thinner than the c's at ExtraBold."""
    top, mid, foot = bars3(g)
    p = g.p
    ref = hook_ref(p)
    if ref is None:
        return top, mid, foot, (p.xh - top - mid - foot) / 2
    arm, inner = ref[0], ref[3]
    return arm, inner, arm, (p.xh - 2 * arm - inner) / 2


BEAK_OVER = 1.5     # legs of the fill (the Regular's edge break past the Regular): the least a beak rises over its bar


def beak_least(g, w) -> float:
    """The least reach of a beak on a bar ``w`` thick: BEAK_OVER over the
    bar. A shorter step between the bar's edge and the beak's end is not a
    drawn one (geom.JOG_FILLS: the outline's finish closes it)."""
    from ..draw import fill_leg
    return w + BEAK_OVER * fill_leg(g.p)


def beak(g, w):
    """How far the c's beak reaches from the line its bar lies on, for a
    bar ``w`` thick: the corner's outer flank alone, an edge break under
    the cut (the shortest beak: an open mouth tells c from o, a from d, e
    from o), and in Arris no less than beak_least. Past the Regular the
    outer cut keeps its size (instances._params) while the bar goes on
    growing, and the flank alone stood 30 units over the bar at Bold, 21 at
    ExtraBold and 9 at Black, where the outline's finish took it for a
    miss and the arm ended flat."""
    least = beak_least(g, w) if g.p.optical else 0.0
    return max(outer_leg(g.p, sh=w) + g.p.c, least)


def beak_in(g, w, room):
    """(reach, corner's leg) of a beak that turns into a bay: the white
    ``room`` tall between its bar, ``w`` thick, and the next (the a's upper
    storey, the e's lower, the s's two). Its end keeps BAY_WHITE of the
    least white off the bar it turns toward, 0.36 of a stem from Bold; the
    corner it hangs from is cut that much shorter, its flank still ending
    an edge break short of the beak's end (beak).

    Until 1.017 the beak was the c's at every weight, and the bay's white
    ran out under it as the bars grew: on the a 90 units at Regular, 57 at
    Bold, 46 at ExtraBold and 37 at Black, 0.23 of a stem, a slit as long
    as the beak is wide between its flat end and the bar's flat top (the
    owner, 2026-11-11: "a weird optical effect ... with the hooks ... the
    a's upper storey, the way it meets it ... at the bolder weights. If I
    were to zoom out ... where it meets the bottom storey or where it does
    not meet. That gap ..."). Measured the same way on 339 fonts of 60
    families at Regular and heavier (the least width of the passage into
    each bay, by the n's stem), those of Arris's boldness keep 0.54 of a
    stem at its Bold (quartiles 0.37 and 0.62), 0.41 at its ExtraBold (0.35,
    0.48) and 0.36 at its Black (0.30, 0.44; the least 0.24), and the
    squared faces nearest it (Oxanium, Tomorrow, Exo 2, Saira) have no
    beak there at all. The gap is 57 units at Bold, 52 at ExtraBold and 57
    at Black now: it stops closing where the families' middle stands."""
    p = g.p
    d = min(beak(g, w), w + room - BAY_WHITE * least_white(p))
    least = beak_least(g, w)
    if p.optical and d < least - 1e-6:
        # The least beak holds where the bay is short of both, and the bay keeps what the room leaves (the
        # owner, 2026-11-12, of the ends that went flat: "anything that goes flat like that ... needs to be
        # like a little hump"): between a stem of 160 and one of 180 the two were 0.6 of a unit more than the
        # white between the bars, and a, e and s ended flat there, with a beak at Bold and one again at Black.
        # Only where the room is not twice the beak's rise (a beak and as much white beyond it) does the arm
        # end on its bar's own edge.
        d = least if room >= 2 * (least - w) else w
    # (the corner's flank ends an edge break short of the beak's end at every reach: where the least beak
    # is longer than the weight's corner leaves it, the corner is cut that much longer, and the end stays
    # the point it is to Bold. With the weight's own leg the end kept an upright face under its cut, 13
    # units tall on the a at Black)
    leg = d - p.c - (p.sv + w) / 2 + p.sd / 2 ** 0.5
    return d, max(0.0, leg if p.optical and d > w else min(p.leg, leg))


A_RISE = 0.6    # the most the a's bowl rises into its stem, as a share of the bowl's white


def a_like_e(p) -> float:
    """How far the a has taken the e's corners (a): nothing to Bold, all of
    them at Black, in Arris."""
    from ..instances import STEMS
    return min(1.0, max(0.0, (p.sv / p.grade_k - STEMS[700]) / (STEMS[900] - STEMS[700]))) * p.optical


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
    p = g.p
    arm, inner, foot = bars3(g)
    f = Frame(g, 8, 'lower')                                # (after the bars are shared out: its rows stand on the foot's thickness)
    low = (p.xh - arm - inner - foot) / 2                   # the bowl's white, and the open storey's
    ya = p.xh - arm / 2
    yb = foot + low + inner / 2
    g.defaults_used.update(arm=ya, bowl=yb)
    d, leg = beak_in(g, arm, low)
    g.hook = (arm, d, leg, inner)                           # (hook_ref: the c and the s take theirs from here)
    g.arm = arm                                             # (draw._optical: the bar on its line)
    # At Black the a is the e turned half round, all but the notch at the foot of its stem (the owner,
    # 2026-11-12: "at black, the e and the lowercase a should practically be identical flipped, aside from
    # the smallest little notch on a at the bottom"; "maybe bold and extra bold can use a little bit of
    # adjustment too ... it shouldn't mess up any of ... the lighter weights"). Their bars and their
    # counters are one size there already (bars3, draw.OPTICAL); two corners were not: the foot of the
    # a's stem kept an edge break where the e's back turns through a corner's cut, 50 units by 88, and the
    # bowl's shoulder was a corner's cut where the e's bar ends in an edge break, 84 by 50. Both come in
    # from Bold with the middles (like): nothing at Bold, whole at Black.
    k = p.sd / 2 ** 0.5
    stem = [f.P(7, 0)]
    shoulder_leg = None
    if like := a_like_e(p):
        cut = p.c + (p.leg + (p.sv + foot) / 2 - k - p.c) * like          # the e's back's own cut at Black
        # (the stem turned through that cut into its foot, which ends on the stem's own inside: no ink but
        # the corner's is changed)
        stem = [B(f.X(7), foot / 2, max(0.0, cut - (p.sv + foot) / 2 + k)), (f.X(7) - p.sv / 2, foot / 2)]
        shoulder_leg = p.leg + (p.c - (p.sv + inner) / 2 + k - p.leg) * like
    g.stroke((f.X(1), p.xh - d), B(f.X(1), ya, leg, arm), B(f.X(7), ya), *stem)
    # The bowl's foot comes into the stem as the u's does, the n's shoulder
    # turned half round: at 45 degrees, with its notch at the foot of the
    # stem (the owner, 2026-11-10). It rises no more than A_RISE of the
    # bowl's white, so the counter keeps its wall under the bar. Until
    # 1.017 the bowl ran square into the stem on the baseline.
    drop = min(BOWL_DROP, A_RISE * low / (f.Y(8) - f.Y(7)))
    arch, cut = shoulder(g, f, f.X(1), f.X(7), drop=drop)
    g.stroke((f.X(7), yb, inner), B(f.X(1), yb, shoulder_leg), *reversed(turned(f.W, p.xh, arch)), end=cut)


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
    # Its hooks are the a's and the e's (hook_ref): their reach and their corner, on the bar the whole
    # lowercase takes from them (draw._start).
    ref = hook_ref(g.p)
    f = Frame(g, 8, 'lower')
    # The shortest beaks (the outer flank alone): an open mouth tells c from o.
    p = f.p
    d = beak(g, g.sh)                                       # by the zone's own bar (thinner than the capitals' from Bold)
    # (its corner's flank an edge break short of its end, where the least beak is longer than the weight's
    # corner leaves it: beak_in)
    leg = max(p.leg, d - p.c - (p.sv + g.sh) / 2 + p.sd / 2 ** 0.5) if p.optical else None
    if ref is not None:
        d, leg = ref[1], ref[2] or None
    g.stroke((f.X(7), p.xh - d), B(*f.P(7, 8), leg), B(*f.P(1, 8)), B(*f.P(1, 1), foot_leg),
             B(*f.P(7, 1), leg if foot_leg is None else foot_leg), (f.X(7), d))


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
    p = g.p
    arm, bar, top = bars3(g)
    f = Frame(g, 8, 'lower')
    open_ = (p.xh - arm - bar - top) / 2                    # the white over the arm, and the bowl's
    y1 = arm / 2
    yb = arm + open_ + bar / 2
    yt = p.xh - top / 2
    g.defaults_used.update(bar=yb, arm=y1)
    g.stroke((f.X(1), yb, bar), (f.X(7), yb), B(f.X(7), yt), B(f.X(1), yt), closed=True)
    d, leg = beak_in(g, arm, open_)
    g.hook = (arm, d, leg, bar)                             # (hook_ref: the c and the s take theirs from here)
    g.arm = arm                                             # (draw._optical: the bar on its line)
    g.stroke((f.X(1), yb), B(f.X(1), y1, None, arm), B(f.X(7), y1, leg), (f.X(7), d))


# The letters with one stem and an arm (f t j) are a module narrower than
# their masters: against the n they stood wider than any face of this kind
# sets them (the j 0.65 of the n's advance for 0.41 to 0.49, the t 0.79 for
# 0.53 to 0.69, the f 0.72 for 0.48 to 0.66: review/widths, 2026-11-10),
# and a line with several of them (little, filter, jilt) lost the rhythm
# its stems set.
NARROW = 6      # the f's and the t's frame, in modules (their masters' seven, less one)


STUB_FADE = (30.0, 40.0)    # units of stem past the Regular's (the watch's SemiBold and 650; the second Arris's Bold): to where the f's and the t's crossbar keeps
                            # its whole stub left of the stem, and from where stub and crossbar are held as they stand there


def narrow_stub(p) -> float:
    """What of its stub the f's or the t's crossbar keeps, left of the
    stem: all to SemiBold, half from 650 (STUB_FADE), and no less at any
    heavier weight.

    The stub is a quarter of the letter's white, about 70 units at every
    weight, and the cuts on it double from Regular to Black: at SemiBold
    its end still has a face between its two cuts, at Bold they met in a
    point, and from ExtraBold the stub was one plane with the cut of the
    t's top (the f's hook), a wedge on the stem's side (the owner,
    2026-11-10: "it just turns into this gnarled, ugly thing when it comes
    to the way that everything joins ... especially for smaller ones, it
    just looks like a big old knot"). And the crossbar ended half a stem
    short of the arm, more with every weight ("they don't keep track of the
    same length"). Shown the stub going into the stem between SemiBold and
    Bold, the crossbar coming out to the arm's end as it went, he chose
    the letter half way: "Look at how it is currently at weight 650 and
    make it the exact same shape throughout all the way to 900. It needs
    to not move one bit. It needs to be exactly the same for both the
    stems." """
    return 1.0 - 0.5 * _faded(p.past)


def _faded(past) -> float:
    a, b = STUB_FADE
    return min(1.0, max(0.0, (past - a) / (b - a)))


def between(p, own, watchs: float) -> float:
    """A rule of Arris's weights (``own``: of the units a stem is past its
    Regular's) at a watch balance between Arris and the watch's own
    drawing, which keeps ``watchs``: as far from the one as from the other,
    as the variable font carries the watch axis from end to end. Read on
    Arris's share of the stem alone (Params.past), a rule with a threshold
    came on somewhere along the axis, later the heavier the weight: at
    Black the f's stub was Arris's half way to the watch's drawing and the
    watch's two thirds of the way, and shrank three units before it grew
    (the owner, of the weights between the watch's and Arris's: "we treat
    that as a gradient that you can go across")."""
    o = p.optical
    if o >= 1.0:
        return own(p.past)
    return watchs if o <= 0.0 else o * own(p.past / o) + (1.0 - o) * watchs


def _stub(p, sv=None) -> float:
    """The stub's length in the body the watch's own white gives: a
    quarter of the letter's white (the stem stands on the frame's second
    module). ``sv``: at another stem of the same modules."""
    sv = p.sv if sv is None else sv
    return (4 * p.m * white_own(sv / (2 * p.m)) + ARM * max(0.0, sv - 1.5 * p.m)) / 4


def stub(p) -> float:
    """How far the f's and the t's crossbar stands out left of the stem:
    narrow_stub of its whole stub to 650, and from there what it is at 650
    in edge breaks, a break and a seventeenth, so the bump on the stem's
    side is one shape at every heavier weight: a face between two cuts
    that take its whole depth. (Toward the watch's own drawing, which
    keeps the whole stub: between.)"""
    from ..draw import fill_leg

    def own(past):
        if past <= STUB_FADE[1]:
            return (1.0 - 0.5 * _faded(past)) * _stub(p)
        held = p.sv - past + STUB_FADE[1]                   # (the font's stem at 650)
        # (no deeper than two legs of its crotch's fill: half of it is its end's cut and half the fill, and
        # past that the fill, which stops growing at the Regular, no longer runs on in the cut's line: a
        # kink of a unit in the bump's side at Black)
        # (the fill by the grade this weight's stems take: it is the Regular's, and a positive grade grows the
        # Regular's a fifth where it may grow a stem of 178 a fifteenth; held to two legs of that, the stub by
        # its stem went up a fortieth at the first step of grade and down again, where every rule runs one way)
        from ..instances import grade_k
        with_stems = min(1.0, p.grade_k / grade_k(400, p.grad)) if p.grad else 1.0
        return min(0.5 * _stub(p, held) / (held / 4) * p.c, 2 * fill_leg(p) * with_stems)
    return between(p, own, _stub(p))


def bar_short(p) -> float:
    """How far the f's and the t's crossbar ends short of the arm and the
    foot: half a stem to SemiBold, nothing from 650 (STUB_FADE), where the
    three end level (the owner, of the two at Black with the crossbar an
    edge break short, as it stood at 650: "they don't seem to be sticking
    out in level with either the foot or the ascender, respectively, with
    the cross")."""
    return between(p, lambda past: p.sv / 2 * (1.0 - _faded(past)), p.sv / 2)


def narrow_frame(g):
    """The f's and the t's frame: the stem a stub in from the body's left
    edge (stub), the arm and the foot out to its right edge, and the
    crossbar with them from 650 (bar_short: half a stem short of them to
    SemiBold).

    Past the Regular, where the body gives (letterframe.narrowed), what is
    given comes off the arm's side: the stub is as short as its two cuts
    allow."""
    f = Frame(g, NARROW, 'asc')
    p = g.p
    if not p.mono:
        f.xa = [(0, 0.0), (2, stub(p) + p.sv / 2), (NARROW - 1, g.W - bar_short(p)), (NARROW, g.W)]
    return f


ARM_LEAST = 1.1     # stems: the least the f's arm and the t's foot run past the stem (a flat of nine tenths of a stem on the arm)


def narrow_width(p):
    """The f's and the t's body: a one-stem letter's (letter_width), less
    what of the crossbar's stub has gone into the stem (stub): the arm and
    the foot keep their length past the stem. Past the Regular the body
    gives (letterframe.narrowed) no more than leaves the arm ARM_LEAST
    stems past the stem: the hook stays an arm, not a cut."""
    return stub(p) + max(letter_width(NARROW, 1)(p) - _stub(p), (1.0 + ARM_LEAST) * p.sv)


def crossbar(g, f):
    """The f's and the t's crossbar, from the body's left edge out to the
    arm's and the foot's end (half a stem short of it, to SemiBold)."""
    g.stroke((0.0, f.Y(8)), f.P(NARROW - 1, 8))


@low('f', NARROW, 1, width=narrow_width)
def f_(g):
    """A stem, its hook and a crossbar. The hook at every weight: the top
    as one cut with no arm, tried to SemiBold in 1.017's making with the
    t's foot, was the l's end, and the owner kept it for the l alone
    (2026-11-10: "keep the hooks for the f and the t, and the l stays
    without a hook"). From 650 to Black its crossing is one shape, the
    t's (narrow_stub)."""
    if g.p.mono:
        f = Frame(g, 9, 'asc')
        g.stroke(f.P(3.5, 0), B(*f.P(3.5, 12)), f.P(9, 12))
        g.stroke(f.P(0.5, 8), f.P(8, 8))
        return
    f = narrow_frame(g)
    g.stroke(f.P(2, 0), B(*f.P(2, 12), f_leg(g, f)), f.P(NARROW, 12))
    crossbar(g, f)


def f_leg(g, f):
    """The leg of the f's corner: its cut comes down the stem as far as the
    cut of the t's top does (an edge break under the t's top, f.Y(11)), so
    the f's and the t's left sides are one drawing from the crossbar up to
    there, and where the t's cut and its crossbar's meet in one flat plane
    (the watch's own drawing at Black: Arris holds the stub short of that
    from 650, stub) the f's do too. With the bowl's own leg the f's cut stopped 67
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
    white = hook_white(p) if white is None else white
    extra = min(hook_room(p), max(0.0, sh + white - p.desc))
    w = min(sh, max(STACK_MIN * sh, p.desc + extra - white))
    return w, extra


def hook_white(p) -> float:
    """The white a hook keeps under what stands over it: a module, or 0.6
    of the stem, at every weight (the descender line is set for it:
    params.descender_line). Not the least white the letters keep inside
    the x-height, which in Arris stops growing at a stem of 158
    (params.white_floor): the owner, of the g at a stem of 200 with 102
    units over its hook, "the black letter g does not have enough
    space"."""
    return white_floor(p.m, p.sv, 0.0)


def hook_stack(g, white=None):
    """The horizontals of a letter that stands on a hook (the g's three,
    the y's two) thin together where the hook, as heavy as they are, has
    not its white on the descender line and the line is the font's
    deepest: by 2% at a stem of 189 and 12% at Black, where the hook is 130
    units under 120 of white. The hook alone gave before (hook_fit), and
    to 1.016 at every weight, which read as a mistake; with all three as
    heavy as each other the letter is one weight and has its room."""
    w, _ = hook_fit(g.p, g.sh, white)
    if w < g.sh - 1e-9:
        g.sh_k *= w / g.sh


def hook_span(p) -> float:
    """From the centre of the stem a hook hangs from to the centre of its
    end: the g's, on every letter that carries the hook. Each ran its own
    body's width, and the y's, a wider letter than the g past the Regular
    and a narrower one to it, was 19 units the shorter at Regular and 34
    the longer at Bold, 65 at Black (the owner, 2026-11-12: "The g and the
    y don't have the same descender at bold ... They need to look exactly
    the same")."""
    from ..draw import drawn_spec
    return drawn_spec('g', p).width(p) - p.sv


BEAK_WHITE = 0.75   # the white a hook's beak keeps under the bowl, as a share of the least white (hook)


def hook(g, f, x_stem=7, x_end=1, white=None, turn=True, span=None):
    """The descending hook of g, y and the italic y: the stem down from the
    body into a bowl corner and a horizontal back under it, as thick as the
    letter's other horizontals (hook_fit), on the weight's descender line.
    (The owner's rule: a feature weight would swallow grows or makes room
    by the smallest change that keeps it.) ``span``: how far its end stands
    from its stem, where that is not the frame's (hook_span)."""
    p = g.p
    w, extra = hook_fit(p, g.sh, white)
    yh = -(p.desc + extra) + w / 2
    xe = f.X(x_end) if span is None else f.X(x_stem) - span
    if extra:
        x0, y0, x1, y1 = g.clip
        g.clip = (x0, min(y0, -(p.desc + extra)), x1, y1)
    if p.slant or not turn:
        g.stroke(f.P(x_stem, 9), B(f.X(x_stem), yh, None, w), (xe, yh))
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
    room = hook_white(p) if white is None else white
    d = min(beak(g, w), over - bottom - BEAK_WHITE * room)
    if p.optical and d < beak_least(g, w):
        # (the least beak, where the room leaves it a bay's white under the bowl: the hook ends in a hump
        # and not flat; the owner, 2026-11-12: "anything that goes flat like that ... needs to be like a
        # little hump")
        d = min(beak_least(g, w), over - bottom - BAY_WHITE * room)
    # the corner's cut ends an edge break under the beak's end, as the c's
    # does (beak), so the rule turns that flank into a point at every weight
    leg = min(p.leg, d - p.c - (p.sv + w) / 2 + p.sd / 2 ** 0.5)
    # (flat where the corner would be cut under an edge break on the watch's leg, a module and a half, or the
    # beak would rise under its least over the hook)
    if leg < p.c - (1.5 * p.m - p.leg) or (p.optical and d < beak_least(g, w) - 1e-6):
        g.stroke(f.P(x_stem, 9), B(f.X(x_stem), yh, None, w), (xe, yh))
        return
    g.stroke(f.P(x_stem, 9), B(f.X(x_stem), yh, None, w), B(xe, yh, leg), (xe, bottom + d))


def g_strokes(g, white=None):
    """The g: its bowl and its hook (``white``: the room the hook leaves
    under the bowl, for a g that carries something there: ǥ's bar)."""
    hook_stack(g, white)
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
    square. So in the watch's own drawing the shoulder goes as the X's step
    does: the n keeps both to Bold, the notch alone at ExtraBold, and is
    square at Black, as the m is from SemiBold. In Arris the notch is kept
    at every weight (NOTCH_KEPT: a break and a half of the weight's own
    down the stem's side, a bowl's three quarters of that): where the
    shoulder has not the room to rise that far its cut meets the arch
    further along. Arris's Bold, ExtraBold and Black are heavier than the
    weights the rule was made on, and by it the n, the h and every bowl
    left their stems square from a stem of 160 (the owner: "arches keep
    their notch depth"; "if we're going to do it on the a and the u, then
    we need to do it on all the bowls"). ``joined``: the stem is another arch's (the m's second),
    and the notch is the V the two meet in, kept at every weight: with no
    room to rise at all the arch still starts on its cut (in the narrower
    body Arris Mono Italic's m is drawn in, from Medium, it began square on
    the stem's centre, and the V had an upright side at Medium and was the
    corner rule's own, twice as deep, from SemiBold).

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
    if rise < 1e-3 * p.m and not joined:
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
    if p.slant and drop < SHOULDER_DROP and p.optical and not p.mono:
        # The italic's bowls keep their notch too. The italic's shoulder goes deeper into its stem than the
        # upright's, by two breaks of the weight's own less the fill, and the notch over it is that much
        # shallower: at the foot of the cursive q, g and y it lost 11 units with every hundred of weight, 44
        # deep at Regular, 12 at Bold and gone from ExtraBold (the owner, of the upright's: "if we're going
        # to do it on the a and the u, then we need to do it on all the bowls"; of the italic's: "a little
        # bit of a crook in the bowls"). It keeps BOWL_NOTCH_ITAL of a break past the corner's fill: the
        # shoulder goes no deeper than leaves it, from a little past SemiBold.
        over = bar_half(g) + rise - (1 - r) * (p.sv / 2 + k) - r * p.c   # the notch's corner on the stem's side, as entered a break
        kept = (BOWL_NOTCH_ITAL * p.c + fill_leg(p) / 2 ** 0.5) * p.optical
        deeper = min(deeper, max(0.0, over - kept))
    x0 -= deeper
    step = rise - g.sh / 2                                  # the diagonal's cut, below the arch's underside
    if upright and step < p.c:
        over = g.sh / 2 + rise - (1 - r) * (p.sv / 2 + k) - r * p.c   # the diagonal's top at the stem's side, below the arch's
        if joined:
            meet = max(x0 + rise, notch_meet(g, xs, g.sh / 2))
        elif p.optical and not p.mono:
            # (Arris: the notch keeps NOTCH_KEPT; where the shoulder has not the room to rise that far, its cut
            # meets the arch that much further along, as a joined arch's does. Arris Mono's arches, in their cell,
            # keep the rule they had)
            least = NOTCH_KEPT * p.c * (1.0 + drop / SHOULDER_DROP) / 2 * p.optical
            if over < SHOULDER_NOTCH * fill_leg(p) and not least:
                return plain
            meet = x0 + rise + max(0.0, least - over)
        else:
            if over < SHOULDER_NOTCH * fill_leg(p):
                return plain
            meet = x0 + rise
        return [(meet - g.sh / 2, y_top - g.sh / 2), (meet, y_top), B(x_right, y_top)], 'h'
    if p.slant:
        # An arch in the italic too: the cursive's branch (deeper than the upright's shoulder,
        # italic_forms.BRANCH) and the upright's own, slanted (Arris Mono Italic's n, m and h). The
        # italic's arch is not held to the upright's room; where its branch would show under an edge
        # break below the arch it is cut along the arch's underside, and the counter's top is the
        # arch's alone. Drawn whole, the cursive m's stood under a tenth of a break below its arches at
        # Bold and inside them from ExtraBold, and the white ran up into the arch beside it in a pocket,
        # another under each arch (the owner: "some funky stuff going on under the loops"); Arris Mono
        # Italic's m had the pocket under its second arch at Regular. The underside is the arch's as the
        # italic draws it, a horizontal cos(slant) thinner than its name (geom.Thickness).
        # A bowl's join (BOWL_DROP: the cursive q, g and y) the same. It was left to start where its
        # diagonal does, and from SemiBold that is inside the bar: the stroke's level end cut the bar it
        # joins, and the bowl's foot was drawn that much thinner than its top beside the join (124 units
        # for 131 at Bold, 137 for 168 at Black), with a kink in the counter's far corner where the cut
        # ran out.
        half = bar_half(g)
        if rise - half < p.c:
            meet = max(x0 + rise, notch_meet(g, xs, half)) if joined else x0 + rise
            return [(meet - half, y_top - half), (meet, y_top), B(x_right, y_top)], 'h'
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
BOWL_NOTCH_ITAL = 0.5   # edge breaks, the weight's own: the notch a bowl's join keeps in the italic, clear of its corner's fill (the
                        # upright's q has 24 units at Black, half a break)
NOTCH_KEPT = 1.5        # edge breaks, the weight's own: the notch an arch keeps over its shoulder at every weight of Arris (a
                        # bowl's, three quarters of it)
SHOULDER_NOTCH = 1.5    # the least notch over a shoulder, in edge breaks down the stem's side: a break deep where the stem
                        # stops at the arch (n), and where it goes on (h) a break of it is the corner's own fill. The
                        # break is the inside's (draw.fill_leg: the Regular's past the Regular, as every inside corner
                        # keeps): counted in the weight's own, which is twice that at Black, the notch was gone from a
                        # stem of 160 and the n, the h, the b and the u left their stems square at ExtraBold and Black
                        # (the owner: "arches keep their notch depth")


def notch_meet(g, xs, half) -> float:
    """The least x at which a joined arch's cut meets its line: so far past
    the stem's centre that the notch it leaves with the corner of the arch
    before it, the V over the m's middle stem, is an edge break deep. With
    no room to rise the cut stood on the stem's centre, and the V shrank
    with the weight to 18 units at Arris Mono's Bold, a little over half a
    break: nothing of a shoulder is drawn smaller than a break. (The V's
    foot is where the cut's upper edge, k left of its line, meets the
    corner's outer flank, outer_leg down the stem's far side.)"""
    p = g.p
    return xs + 2 * p.c - half + p.sd / 2 ** 0.5 + p.sv / 2 - outer_leg(p, sh=2 * half)


def bar_half(g) -> float:
    """Half an arch's bar as it is drawn: in the italic a horizontal stroke
    is cos(slant) thinner than its name (geom.Thickness), and its underside
    that much higher."""
    from ..draw import _thickness
    return _thickness(g.p, g.sh)((1.0, 0.0)) / 2


def shoulder_room(g, xs, x_right, full):
    """The most a shoulder between stems at xs and x_right can rise and
    leave the arch's underside a flat of an edge break: across the counter
    lie the shoulder's cut, its rise, that flat and the right corner's
    inner cut. (The shoulder starts rise/full of its way out of the stem,
    so the rise it has room for is its own share of what is left.)"""
    p = g.p
    k = p.sd / 2 ** 0.5
    counter = (x_right - p.sv / 2 - inside_cut(g)) - (xs + p.sv / 2)
    return (counter - p.c - k + p.sv / 2 + g.sh / 2) / (1 + (p.sv / 2 + k - p.c) / full)


def inside_cut(g) -> float:
    """The cut of a bowl's inside corner as it is drawn: what the strokes
    leave of the centreline's leg, and no less than the corner rule's fill
    (geom.stroke_polygon; draw.fill_leg, the Regular's edge break past the
    Regular). params.inner_leg keeps the weight's own break for its least,
    which the inside had until 1.017; past the Regular, where the outside
    cut holds its size (instances._params), the inside is at the fill from
    Bold, half that at Black."""
    from ..draw import fill_leg
    p = g.p
    return max(fill_leg(p), p.leg - (p.sv + g.sh) / 2 + p.sd / 2 ** 0.5)


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


J_FRAME = 5     # the hooked j's frame, in modules (Arris Mono's, the double-struck ⅉ's): its hook three modules of white across
J_SLOT = 1.0    # edge breaks: the least white between a hooked j's stem and the end of its hook


def j_width(p):
    """A hooked j's body (Arris Mono's j in its cell, ⅉ): a one-stem
    letter's (letter_width), giving past the Regular no more than leaves
    J_SLOT breaks of white between its stem and the end of its hook:
    narrower, the fill of that crotch shrank to a chord of 4 units at
    Black, a crumb on the stem's side."""
    return max(letter_width(J_FRAME, 1)(p), 2 * p.sv + J_SLOT * p.c)


def j_body(p):
    """The j's body: the l's, a stem and its cut (l_width)."""
    return l_width(p)


def _j_strokes(g, f):
    """The j's stem, from the x-height down to the l's foot turned to the
    left on the descender line: the same corner, the same cut two breaks
    thick landing as the k's leg does, the body's clip taking what hangs
    under the line (see l). Returns the stem's centre."""
    p = f.p
    xs = g.W - p.sv / 2
    h, t, leg = _kick(p, g.sh)
    y = -p.desc + h - t / 2
    g.stroke((xs, p.xh), B(xs, y, leg, t), (0.0, y))
    g.end_cut = POINTED
    g.clip = (0, -p.desc, g.W, f.Y(13) + p.sv)
    return xs


@low('j', 3, 1, width=j_body)
def j(g):
    """The l run down under the line: a stem, its dot, and the l's foot at
    the descender line, turned to the left, where a j turns. Until 1.017 it
    turned into a hook that ended in a beak, the g's in little (the owner,
    2026-11-12: "the j with a little hook. It shouldn't look like that. It
    should look more like the l with the same foot as our l and just kind
    of descend"; and shown a bare stem: "I didn't want you to make it look
    like an i. I wanted you to make it look like our l, where it has a
    small little crook at the bottom with a foot"). Arris Mono's j keeps
    its flag and its hook in its cell. The italic's j is its own."""
    if g.p.mono:
        f = Frame(g, 9, 'asc', top=g.p.asc + g.p.sv)
        p, u = f.p, g.W / 9
        x = g.W / 2 + 1.5 * u
        g.stroke((x - 3 * u, f.Y(8)), (x, f.Y(8)), B(x, f.Y(-2)), B(f.X(1), f.Y(-2)), (f.X(1), -p.desc + beak_depth(p, g.sh)))
        _dot(g, f, x)
        return
    f = Frame(g, 3, 'asc', top=g.p.asc + g.p.sv)
    _dot(g, f, _j_strokes(g, f))


@low('k', 8, 1)
def k(g):
    f = Frame(g, 8, 'asc')
    g.stroke(f.P(1, 0), f.P(1, 13))
    for pts, a, b in k_arms(g, f.X(1), f.W, f.p.xh):
        g.stroke(*pts, start=a, end=b)
    g.clip = (0, -f.p.desc, f.W, f.p.asc)


def _toe(p, sh):
    """The thickness the l's body is measured for (kick_reach): three edge
    breaks (the weight's bar, where that is less), what its cut was drawn
    at until its end took the form of the k's leg's (END): its end's own
    break then took up all of its top, and the corner's cut ran straight
    into the end's face, two breaks up."""
    return min(3 * p.c, sh)


END = 2.0       # edge breaks: how thick the l's cut is at its end, the k's leg's: its lower cut and its upper, a point between
POINTED = 0.5   # the share of such an end each of its two cuts takes: all of it between them (Glyph.end_cut). Everywhere else
                # a stroke's flat end keeps a face a third of it between its cuts (geom._share: no bar ends in an arrowhead);
                # the l's foot and the j's are the k's leg's landing, drawn to a point on the owner's word (see l), and the
                # r's arm ends as its owner has it, a short face over the shoulder's underside ("don't fix the R")


def _kick_inside(p, sh):
    """How much the inside of the l's corner is short of the fill every
    inside corner keeps (draw.fill_leg), in Arris: nothing to a stem of
    160. Past it the corner's leg, shorter by what a bowl's outside cut is
    held from the Regular (instances._params), left the inside of the turn
    less than the fill and at Black inside out: the corner rule then filled
    a square corner at one end of the cut's top while the end's own break
    took the other, the two sharing a top no longer than both, and the l
    ended in a bent cut at ExtraBold and an upright face 14 units tall at
    Black. The corner's leg and the body grow by this much, and the cut's
    upper edge is one line from its point to the stem at every weight."""
    from ..draw import fill_leg
    h = min(END * p.c, sh)
    t = max(h, p.floor)
    reach = _toe(p, sh)
    inside = p.leg + (sh - reach) / 2 - (reach - h) / 2 + (t - h) / 2 - (p.sv + t) / 2 + p.sd / 2 ** 0.5
    return max(0.0, fill_leg(p) - inside) * p.optical


def _kick(p, sh):
    """The l's cut at its end: how tall it is (END), how thick it is drawn
    (the stroke floor's, toward Thin) and the leg of the corner the stem
    turns through into it."""
    reach = _toe(p, sh)                                     # the thickness the body is measured for (kick_reach)
    h = min(END * p.c, sh)
    # (toward Thin two breaks are under the stroke floor: the end is drawn a floor thick with its top
    # where it belongs, and the body's clip takes what hangs under the baseline, as it takes the k's leg)
    t = max(h, p.floor)
    return h, t, p.leg + (sh - reach) / 2 - (reach - h) / 2 + (t - h) / 2 + _kick_inside(p, sh)


def kick_reach(p, sh):
    """From the l's stem's centre to the end of its cut: the stem's end
    turned through the one cut a corner takes and stopped there (measured
    for an end an edge break tall over its own break, _toe: the body it
    had before its end took the k's leg's form)."""
    return sh / 2 + p.leg + p.sd / 2 ** 0.5 - _toe(p, sh) + p.c + _kick_inside(p, sh)


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
    # foot turns through, run on to the baseline with no foot after it
    # (the owner, 2026-11-10: "only one single notch", and
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
    # The cut lands as the k's leg does (the owner, 2026-11-10: "the L kind
    # of descends and it lands ... the K has descender at the same angle,
    # but the way that it hits it is kind of different, the way that the
    # chamfering looks. The L should follow the form that K sets"): a flat
    # on the baseline as long as the leg's, and one break up to a point
    # where the cut's upper edge leaves at 45 degrees. Its end is two breaks
    # thick, all of it its two cuts (END), where it was three, a break of
    # upright face between them; the corner's leg is shorter by half of
    # that, so the body and the cut's thickness are what they were and the
    # cut stands a break lower on the stem.
    h, t, leg = _kick(p, g.sh)
    g.stroke((xs, p.asc), B(xs, h - t / 2, leg, t), (g.W, h - t / 2))
    g.end_cut = POINTED
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
            # (to the arch's underside as it is drawn, bar_half: in Arris Mono Italic, its arches square
            # in the narrower body its slant leaves it, the stem stopped 0.9 of a unit under the arch
            # at Bold, its corner there was broken as a stroke's end is, and the counter bit into it)
            g.stroke((xs, f.Y(4)), (xs, min(arch[0][1], f.Y(8) - bar_half(g))))
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
R_SHARE = (6.0, 7.0)    # ninths of the H's width: to the Regular, at the watch's Black (6.8 at Arris's: instances.STEMS)
R_BLACK = 85.0          # units the stem gains from Regular to the watch's Black, the boldness the families were read at


def r_width(p):
    """(By the font's weight past its Regular, Params.past: the watch's
    own drawing keeps six ninths at every weight, and the small r inside a
    sign, ₢, is its font's.)"""
    a, b = R_SHARE
    return share_width(a + (b - a) * min(1.0, p.past / R_BLACK))(p)


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
    g.end_cut = POINTED                                     # (the arm's end as its owner has it: see POINTED)
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
    top, mid, foot, white = spine3(g)
    y1, ym, yt = foot / 2, foot + white + mid / 2, p.xh - top / 2
    (dt, lt), (df, lf) = beak_in(g, top, white), beak_in(g, foot, white)
    ref = hook_ref(p)
    if ref is not None and white >= 2 * (ref[1] - ref[0]):
        dt, lt = df, lf = ref[1], ref[2]                    # the a's and the e's own, at both ends
    g.stroke((f.X(7), p.xh - dt), B(f.X(7), yt, lt, top), B(f.X(1), yt), B(f.X(1), ym, None, mid),
             B(f.X(7), ym), B(f.X(7), y1, None, foot), B(f.X(1), y1, lf), (f.X(1), df))


@low('t', NARROW, 1, width=narrow_width)
def t(g):
    """A stem, a crossbar and its foot, at every weight (the f turned
    over: see f_; the crossbar half a stem short of the foot to SemiBold,
    level with it from 650: bar_short)."""
    if g.p.mono:
        f = Frame(g, 9, 'asc')
        g.defaults_used['stem'] = f.X(3)
        g.stroke(f.P(3, 11), B(*f.P(3, 1)), f.P(8.5, 1))
        g.stroke(f.P(0.5, 8), f.P(8, 8))
        return
    f = narrow_frame(g)
    g.defaults_used['stem'] = f.X(2)                        # (extra_latin._slot reads it for the ŧ's bar)
    g.stroke(f.P(2, 11), B(*f.P(2, 1)), f.P(NARROW, 1))
    crossbar(g, f)


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
    hook_stack(g)
    f = Frame(g, 8, 'lower')
    p = f.p
    xl, y1 = f.X(1), f.Y(1)
    ya, _ = _point(f)
    arch, cut = shoulder(g, f, f.X(1), f.X(7), drop=BOWL_DROP)
    join = turned(f.W, p.xh, arch)[:-1]                     # (the notch's cut,) where the foot leaves the flat
    d = min(ya + gable_run(p, g.W) - y1, join[-1][0] - xl - p.c)
    g.stroke((xl, p.xh), (xl, y1 + d), (xl + d, y1), *reversed(join), end=cut)
    span = hook_span(p)                                     # the g's own hook, to the unit
    if p.mono:
        # (in the cell a letter is drawn narrower than its body where its ink would run out of it, the ỵ for
        # the dot beside its tail, draw._cell_fit, and the hook gives with the body: held at the g's span its
        # ink did not narrow as its body did, and in Arris Mono Italic the ỵ stood 32 units out of the cell's
        # left side at Bold. In its own body the two spans are one: the cell's)
        span = min(span, f.X(7) - f.X(1))
    hook(g, f, span=span)
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


def _hooked_j(g, f):
    """The j's stem turned left under the line into a hook that ends in a
    beak: Arris's own j until 1.017, Arris Mono's dotless j, and the j of
    cv03. Returns the stem's centre."""
    p = f.p
    xs = f.X(J_FRAME - 1)
    g.stroke((xs, f.Y(9)), B(xs, f.Y(-2)), B(*f.P(1, -2)), (f.X(1), -p.desc + beak_depth(p, g.sh)))
    return xs


@glyph('uni0237', '\u0237', lambda p: j_body(p), kind='lower')
def dotlessj(g):
    if g.p.mono:                                            # (Arris Mono's j, hooked: see j)
        _hooked_j(g, Frame(g, J_FRAME, 'lower'))
        return
    f = Frame(g, 3, 'asc', top=g.p.asc + g.p.sv)
    _j_strokes(g, f)
    g.clip = (0, -g.p.desc, g.W, g.p.xh)


# cv03, "Hooked j": the j Arris had until 1.017, for whoever wants it back (the owner, 2026-11-12, of the j on the
# l's foot: "you can have the old j using some type of rule that can be turned on, but I like the way it is right
# now"). In Arris Mono, whose j never changed, these are its own.
def _cv03_width(name):
    """The hooked j's body, and in Arris Mono its own j's."""
    return lambda p: REGISTRY[name].width(p) if p.mono else j_width(p)


@glyph('j.cv03', None, _cv03_width('j'), kind='lower')
def j_cv03(g):
    if g.p.mono:
        REGISTRY['j'].fn(g)
        return
    f = Frame(g, J_FRAME, 'asc', top=g.p.asc + g.p.sv)
    _dot(g, f, _hooked_j(g, f))


@glyph('uni0237.cv03', None, _cv03_width('uni0237'), kind='lower')
def dotlessj_cv03(g):
    _hooked_j(g, Frame(g, J_FRAME, 'lower'))
