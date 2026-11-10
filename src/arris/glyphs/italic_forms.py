"""The italic's own lowercase: cursive forms in Arris's vocabulary.

The italic (``arris.italic``) curves every chamfer and slants the outline.
These drawings give it a hand as well, from moves the upright already makes:

* **Entry**: the 1's flag, a 45-degree lead-in to the top of a stem
  (i j m n p r u y), and on ascenders (b h k l).
* **Exit**: the t's foot, a stem turning right on the baseline
  (a d h i m n u); curved by the italic, it is the exit stroke of a hand.
* **Branching**: arches spring from lower on the stem than the upright's
  notched shoulders, as a pen leaves a stem.
* **Cursive forms**: the single-storey a, the descending f, the looped k,
  the y that is a u running on into its descender, the s whose spine is a
  diagonal with the 2's notch, the e whose bar is a diagonal and which
  leaves on an upstroke.

The monospaced italic keeps the upright forms but for three, the f, the k
and the y (``MONO_CURSIVE``), cursive by default and drawn narrower until
they fit the cell, an underscore running on into the f's tail (``JOIN``);
``ss04`` ("Plain italic f k y") gives back the slanted upright's three, and
``ss05`` ("Underscore apart") the underscore as it is.
"""
from __future__ import annotations

from ..draw import AUTO_SHARE, REGISTRY, B, Opening, _counter_white, glyph
from ..params import SQRT2, inner_leg, outer_leg
from .figures import jog
from .letterframe import Frame, plain_width as letter_width, white_scale
from .lower import _dot, crossbar, crotch_butt, hook, shoulder, shoulder_enter, shoulder_under

TAIL = 1.75      # modules of white an exit tail reaches past its stem
FLAG = 1.5       # modules an entry flag reaches left of its stem (and down)
BRANCH = 3       # modules below the arch where an italic shoulder leaves its stem


# Mono's cursive set: the owner's three, the descending f, the looped k (2026-11-02; the whole italic
# set in the cell was too much) and the y that runs on into its descender (2026-11-03), the default in
# Mono Italic since 2026-11-03 (ss04 the plain ones). Every other letter keeps the slanted upright's form.
MONO_CURSIVE = ('f', 'k', 'y')
CELL_GAP = 0.25   # modules: Mono's cursive set keeps its ink this far inside the cell, so neighbours' tails never touch


def _in_cell(g, fn):
    """Mono's cursive set (ss04): the italic's own drawing, drawn as much
    narrower than the body as its hooks and tails need to stay inside the
    cell, then centred in it, ink and all, so the cell (and the grid) is the
    same. The letter gives up width, not its tail."""
    from ..draw import REGISTRY, Glyph, _ink_x, body_width
    p = g.p
    W0 = g.W
    lo, hi = (W0 - p.fig_adv) / 2 + CELL_GAP * p.m, (W0 + p.fig_adv) / 2 - CELL_GAP * p.m
    # drawn in a body narrower than its own (a composite fitted to the cell,
    # draw._cell_fit: ỵ's dot beside its tail), as much less room
    spec = REGISTRY.get(g.name)
    less = max(0.0, body_width(spec, p) - W0) if spec is not None else 0.0
    lo, hi = lo + less / 2, hi - less / 2
    shrink, h = 0.0, None
    for _ in range(4):
        h = Glyph(p, g.name, ot=g.ot, ob=g.ob, W=W0 - shrink, overrides=dict(g.overrides))
        h.sh_auto = g.sh_auto
        fn(h)
        x0, x1 = _ink_x(h, p)               # as the font carries it: slanted
        over = max(0.0, x1 - x0 - (hi - lo))
        if over <= 0.5:
            break
        shrink += over * (W0 - shrink) / max(x1 - x0, 1.0)
    dx = (lo + hi) / 2 - (x0 + x1) / 2
    g.add_glyph(h, dx, 0.0)
    g.defaults.update(h.defaults)
    g.defaults_used.update({k: (v + dx if k == 'stem' else v) for k, v in h.defaults_used.items()})


def ital(name, wm, stems, width=None, openings=()):
    """An italic drawing of ``name`` (``draw`` uses it wherever p.slant)."""
    def deco(fn):
        def wrapped(g):
            if g.p.mono and (not g.p.cursive or name not in MONO_CURSIVE):   # the cell keeps the upright form,
                return REGISTRY[name].fn(g)                                    # but for ss04's letters
            if g.p.mono:
                return _in_cell(g, fn)
            return fn(g)
        glyph(f'{name}.ital', None, width or letter_width(wm, stems), kind=REGISTRY[name].kind,
              openings=openings)(wrapped)
        if name in MONO_CURSIVE:
            CURSIVE.append(name)
        return fn
    return deco


# --- Mono's cursive set, and ss04 -----------------------------------------------
# Arris Mono Italic is drawn with the cursive set on (Params.cursive): every glyph
# that draws one of its letters (the letter, and what is built on it: ḟ ķ ǩ ý ﬁ
# ...) is the cursive form, and has an alternate, NAME.ss04, the same glyph drawn
# with the slanted upright's form; ss04 swaps them in.

CURSIVE: list = []      # MONO_CURSIVE, as registered


def cursive_set(names, p, workers=4):
    """The glyphs among ``names`` whose drawing, in Mono Italic at p, draws
    one of the cursive letters: found by drawing each with the cursive set on
    and noting what it draws (draw.TRACE). Weight does not change which."""
    from multiprocessing import get_context
    global _P
    _P = p.with_(cursive=True)
    names = [n for n in names if n not in CURSIVE_SKIP and _letter(n)]
    with get_context('fork').Pool(workers) as pool:
        hit = pool.map(_draws_cursive, names, chunksize=16)
    return [n for n, h in zip(names, hit) if h]


# Letters only: a symbol built on a letter (℀, the Roman numerals) keeps its own.
CURSIVE_SKIP: tuple = ()


def _letter(name):
    import unicodedata
    u = REGISTRY[name].unicode
    return u is None or unicodedata.category(chr(u)).startswith('L')


_P = None


def _draws_cursive(name):
    from .. import draw as D
    seen = set()
    D.TRACE.append(seen)
    try:
        D.draw(name, _P)
    except Exception:                                       # noqa: BLE001 (a glyph that cannot be drawn so is left out)
        return False
    finally:
        D.TRACE.remove(seen)
    return bool(seen & set(CURSIVE))


def register_cursive(names):
    """NAME.ss04 for each name: the glyph drawn with the slanted upright's
    letters, the cursive set off."""
    out = []
    for n in names:
        alt = f'{n}.ss04'
        if alt not in REGISTRY:
            spec = REGISTRY[n]

            def fn(g, n=n):
                from ..draw import draw
                g.add_glyph(draw(n, g.p.with_(cursive=False), g.ot, g.ob, width=g.W))
            glyph(alt, None, spec.width, kind=spec.kind)(fn)
        out.append(alt)
    return out


def cursive_fea(names) -> str:
    """ss04, the plain letters; then the underscore's join into the f, on
    by default (calt, after ss04's swaps: a plain f takes no join); then
    ss05, which undoes the join."""
    subs = '\n'.join(f'    sub {n} by {n}.ss04;' for n in names)
    out = f'feature ss04 {{\n    featureNames {{ name "Plain italic f k y"; }};\n{subs}\n}} ss04;\n'
    into = ' '.join(_joined(names))
    if into:
        out += (f"feature calt {{\n    sub {JOIN}' [{into}] by {JOINED};\n    sub {RUN_END}' [{into}] by {RUN_JOINED};\n}} calt;\n"
                f'feature {JOIN_TAG} {{\n    featureNames {{ name "Underscore apart"; }};\n'
                f'    sub {JOINED} by {JOIN};\n    sub {RUN_JOINED} by {RUN_END};\n}} {JOIN_TAG};\n')
    return out


# --- The underscore into the f (the owner's, 2026-11-02; on by default, ss05 off, 2026-11-03) ----------
# The descending f ends in a tail on the underscore's line, a cell's margin short of an underscore before
# it. That underscore (JOINED) runs on into the tail, so `is_fresh` reads as one line into the f; ss05
# keeps it apart, and a plain f (ss04) takes no join.
# It is the underscore as it stands in its cell, its bar run on at its own height and weight past the
# cell's edge until it is under the tail: a one-cell piece that draws past its cell, as a ligature does
# ('liga' kind, so the cell does not cut it). The tail keeps its own end above the bar: where the f's
# tail is the heavier, its chamfer shows as a step up into it.

JOIN = 'underscore'
JOIN_TAG = 'ss05'
JOINED = f'{JOIN}.join'
RUN_END = f'{JOIN}.seq.e'                          # the last of a run of underscores (sequences: `__f`)
RUN_JOINED = f'{JOIN}.seq.join'                    # it, run on into the f


def _joined(names):
    """The cursive glyphs an underscore runs into: the f, and the letters that are an f with a mark."""
    import unicodedata
    out = []
    for n in names:
        u = REGISTRY[n].unicode
        if n == 'f' or (u is not None and unicodedata.normalize('NFD', chr(u))[0] == 'f'):
            out.append(n)
    return out


def _join_underscore(g, run=False):
    """``run``: the last of a run of underscores (``sequences``), its line
    coming in from the cell's left edge, flush with the piece before it."""
    from ..draw import draw
    from ..geom import rings_to_shapely
    from .ligatures import _runs
    p = g.p
    us = draw(JOIN, p)
    f = draw('f', p.with_(cursive=True))
    du = (p.fig_w - us.W) / 2                       # each where it stands in its cell, in this glyph's frame
    df = p.fig_adv + (p.fig_w - f.W) / 2            # (whose x = 0 is its body's left: a 'liga' piece's)
    x0, y0, x1, y1 = rings_to_shapely(us.rings()).bounds
    tail = rings_to_shapely(f.rings())
    # where the tail is the bar's full height (past its end's chamfers), and on by a chamfer and a
    # quarter-module, so the bar's own cut end is hidden in the tail
    runs = [_runs(tail, y=y) for y in (y0 + 0.5, y1 - 0.5)]
    end = du + x1                                   # (an f with no tail there, as a check draws it upright: as is)
    if all(runs):
        end = df + max(min(r[0] for r in rs) for rs in runs) + p.c + 0.25 * p.m
    g.p = us.p                                      # the underscore's own (Mono fits it to the cell: symkit)
    start = du + x0
    if run:
        from .sequences import OV
        start = -(p.fig_adv - p.fig_w) / 2 - OV * p.m
        g.butt = (('x', start),)
    g.clip = (start, y0 - p.cap, end, y1 + p.cap)
    g.stroke((start, (y0 + y1) / 2, y1 - y0), (end, (y0 + y1) / 2))


def register_join(names):
    """JOINED, if the cursive set has a letter for it to run into."""
    if not _joined(names):
        return []
    if JOINED not in REGISTRY:
        glyph(JOINED, None, 'fig_w', kind=('liga', 1))(_join_underscore)
        glyph(RUN_JOINED, None, 'fig_w', kind=('liga', 1))(lambda g: _join_underscore(g, run=True))
    return [JOINED, RUN_JOINED]


def _one_counter(g):
    return _counter_white(g, 1)


def _free(g):
    """Let tails and flags run past the body (the frame clips to it): by a
    cap height either side, whatever the body (an i's is a stem wide)."""
    x0, y0, x1, y1 = g.clip
    g.clip = (x0 - g.p.cap, y0, x1 + g.p.cap, y1)


def _reach(p, modules):
    return modules * p.m * white_scale(p)


def entry(g, f, xs, top=None):
    """The 1's flag at the top of a stem standing at xs: a 45-degree stroke
    whose upper edge continues the stem's cut top-left corner, ending
    square FLAG modules down. The stem keeps its flat top (on the x-height,
    or ``top``)."""
    p = g.p
    if p.mono:                                              # Mono's cursive letters leave their entry flags out
        return
    top = p.xh if top is None else top
    # The flag is the Regular's from there to Black (small_part): as thick,
    # and as far out to the left of the stem's side and down from its cut
    # corner, while the stem it leads into goes on getting heavier. Its
    # upper edge still continues the stem's own cut.
    q = small_part(p) or p
    k = q.sd / SQRT2
    a = xs - p.sv / 2 + p.c - top + k                       # centreline: x - y = a
    yf = top - p.c - (_reach(q, FLAG) + q.sv / 2 - q.c)
    if q is not p:
        from ..draw import _thickness
        x0 = xs - p.sv / 2
        # The flag's square end runs into the stem's side. As the Regular's is placed its
        # lower edge comes down on the end's cut three units short of the stem (the italic's
        # diagonal is set a little off its nominal thickness), a notch of white which the
        # outline filled as a slit in one letter and broke as a crotch in the next, at one
        # weight and not the one after (the b's flag had a fill under it at Regular and Black
        # and none between, the p's came and went four times). Kept, the end is cut where the
        # lower edge is a unit inside the stem: one right angle, filled as any is.
        short = x0 + 1.0 - (yf + a + _thickness(q, q.sh)((1.0, 1.0)) / SQRT2)
        yf += max(0.0, short)
        # Where the frame stands over the stem's top (the i, the j: room for the dot) the
        # flag runs on over it, and its end, at the stem's middle, with the fill under it and
        # the stem's own cut corner made the stem a slanted top: a roof from the flag's upper
        # edge down to the stem's far side, one line because a fill and a cut were one leg.
        # A fill is the Regular's now and the flag is the Regular's: the stem's cut is carried
        # up to the flag's end by a square on its point, a cut's leg each way from the middle
        # of the stem's top (under a frame that ends on the stem's top nothing of it shows).
        g.stroke((xs - p.c / 2, top + p.c / 2, p.c * SQRT2), (xs + p.c / 2, top - p.c / 2))
    # (the flag's end at the stem's middle stays square as the flag is finished alone, as it is inside the stem)
    with g.kept(butt=(('x', xs),)):
        g.stroke((xs, xs - a), (yf + a, yf), start='v', end='h')


def small_part(p):
    """The parameters the italic's small parts are drawn with where they
    are not the weight's own: its cut's Regular, past it (draw.held_at);
    None up to there. An entry flag, an exit tail and the e's flick are
    extensions of a letter, and they are no bigger at Black than at Regular
    while the letter goes on getting heavier (the owner, 2026-11-10:
    "anything that is ... like a small little extension or a cross or a
    little diacritic mark that is on a letter, don't let it get bigger
    than what it is at regular"). Until 1.017 they grew with the stem: at
    Black a flag and a tail were strokes of 147 and 149 units on a stem of
    175, where the Regular's are 81 and 79 on 90."""
    from ..draw import held_at
    q = held_at(p)
    return None if q is p else q


def _tail_reach(p):
    """How far an exit tail reaches past its stem (tail_end)."""
    u = p.ungraded()                                  # (grade moves no stroke)
    return max(_reach(p, TAIL), TAIL_FLOOR * u.sv, inner_leg(u) + (1 + TAIL_FLAT) * u.c)


def _kept_tail(g, x0, xs):
    """The Regular's exit tail past a stem at xs, from x0 inside the ink:
    its thickness, its reach past the stem's side and its end's breaks
    (Glyph.kept). Returns (its thickness, where it ends)."""
    p = g.p
    w = g.held()
    y = _foot_line(g) + w / 2
    x_end = xs + p.sv / 2 + _tail_reach(small_part(p))
    with g.kept():
        g.stroke((x0, y, w), (x_end, y))
    return w, x_end


def _foot_line(g) -> float:
    """Where the underside of the letter's own horizontals lies, over the
    baseline: a horizontal is drawn on the frame's first line, half the
    weight's nominal thickness up, and the italic's is a little thinner
    than that (set for the slant), so its underside stands a unit or so
    over the line. A kept tail stands on the same line: a unit lower, the
    letter's underside ran down to it on a slope no eye sees, and the
    bowl's corner before it, its edge no longer level, was held straight
    from Medium to Bold (a d u)."""
    from ..draw import _thickness
    return g.sh / 2 - _thickness(g.p, g.sh)((1.0, 0.0)) / 2


def tail(g, f, xs, y=None):
    """Points that end a stem on the baseline with the t's foot: a corner
    and a short stroke to the right. Past the Regular the stem turns into a
    tail as thick as the Regular's and the tail itself is the Regular's,
    laid on from inside the turn (small_part, _kept_tail)."""
    p = g.p
    if small_part(p) is None or y is not None:
        yb = f.Y(1) if y is None else y
        return [B(xs, yb), tail_end(g, f, xs, yb)]
    from ..draw import _thickness
    w = g.held()
    # where the turn's cut comes down on the baseline (the turn's own diagonal as the strokes take it:
    # in the italic, set for the slant); the tail starts a break of its own before it, its start's
    # break lying on that cut, so nothing of it shows outside the turn
    x_cut = xs + w / 2 + p.leg - _thickness(p, g.sh)((1.0, -1.0)) / SQRT2
    x_in = x_cut - small_part(p).c
    _, x_end = _kept_tail(g, x_in, xs)
    y = _foot_line(g) + w / 2
    return [B(xs, y, None, w), ((x_in + x_end) / 2, y)]


def exit_past(g, f, xs, foot_from=None):
    """The exit past a stem at xs that stands on a bowl's foot (a d u): the
    foot run on into the t's foot to the Regular; past it the foot ends
    under the stem and the Regular's tail leaves the stem's side
    (_kept_tail). ``foot_from``: the points of the foot's own stroke up to
    the stem (the u's, drawn here to its end); None where the bowl is
    closed and the exit is a stroke of its own."""
    p = g.p
    if small_part(p) is None:
        end = tail_end(g, f, xs)
        g.stroke(*(foot_from or [(xs, f.Y(1))]), end)
        return
    if foot_from:
        g.stroke(*foot_from, (xs + p.sv / 2, f.Y(1)))       # the foot, to the stem's far side
    _kept_tail(g, xs, xs)


TAIL_FLOOR = 0.7   # stems: the least an exit tail reaches, so its end keeps a flat past its chamfer
TAIL_FLAT = 1.25   # corner breaks: the least flat an exit tail's top keeps between its corner and its end


def tail_end(g, f, xs, y=None):
    """Where an exit tail from a stem at xs ends: TAIL modules of white past
    the stem, but never under TAIL_FLOOR stems, so that toward Black (where
    the white narrows as the stem grows) the tail's top keeps a flat beyond
    its end's chamfer: the same construction at every weight, which the
    variable font interpolates without a lump.

    Nor so short that the tail's top keeps less than TAIL_FLAT corner breaks
    of flat between the corner's inner chamfer and the end's (the inner leg,
    the end's break and the flat): a step between parallel edges shorter
    than a corner break is taken for a miss and closed (geom.JOG), which cut
    the end's top off the tail and left the corner an S-bend the italic
    cannot curve. In 1.005 that happened from 589 to about 740, where the
    tail's flat (about one corner break from Medium up) fell under the
    threshold: the h, l, d, n and the rest ended in a straight cut at
    SemiBold and Bold and a curve either side."""
    p = g.p
    return (xs + p.sv / 2 + _tail_reach(p), f.Y(1) if y is None else y)


def run_floor(p, leg=None, across=None):
    """The least a stroke runs from the centre of a stem, past a bowl corner
    there, to its end (a hook's tail, an ogonek's foot): on each of its two
    edges the corner's chamfer, the end's edge break and TAIL_FLAT breaks of
    flat between them, as tail_end keeps for the exit tails. Shorter, the
    chamfer and the break merge (geom.JOG) and the corner, no longer one, is
    held straight at that weight and curved at the next: the Ԧ's hook ended
    in a point from 500 to 750 and in a curve at Black. ``leg`` the corner's
    centreline leg (the parameter default: the chamfer legs follow it),
    ``across`` the thickness of the stem the run leaves (a vertical stem's).
    Measured on the strokes as drawn, grade included: graded heavier, the
    chamfers and the breaks grow with the stroke, and a floor from the
    ungraded stroke left the Ԧ's tail held from 200 to 700 at grade +100."""
    d = (p.leg if leg is None else leg) - p.leg
    outer, inner = outer_leg(p) + d, max(p.c, inner_leg(p) + d)
    half = (p.sv if across is None else across) / 2
    flat = (1 + TAIL_FLAT) * p.c
    return max(half + inner + flat, outer - half + flat)


def arm_floor(p):
    """The least a horizontal arm runs from the centre of a stem to the centre
    of a bowl corner at its end (a hook's arm, cyrillic_ext.hook_reach): on
    each of its edges the crotch's fill at the stem, TAIL_FLAT breaks of flat
    and the corner's chamfer. The ҧ's arm of three modules lost its
    underside's flat at Regular, the crotch's fill met the corner's chamfer,
    and the corner was held straight."""
    flat = (1 + TAIL_FLAT) * p.c
    return max(p.sv + inner_leg(p) + flat, outer_leg(p) + flat)


def tail_run(p, run, leg=None):
    """A hook's tail: ``run`` from the hook's stem, or in the italic at least
    run_floor, so the corner into it curves at every weight. (The upright
    keeps its drawing: a tail shorter than the corner's chamfer ends on it in
    a point, as a beak does.)"""
    return max(run, run_floor(p, leg)) if p.slant else run


# --- Stems, entries and exits ------------------------------------------------

@ital('dotlessi', 2, 1, width=lambda p: p.sv)
def dotlessi_ital(g):
    f = Frame(g, 2, 'lower')
    _free(g)
    g.stroke(f.P(1, 9), *tail(g, f, f.X(1)))
    entry(g, f, f.X(1))


@ital('i', 2, 1, width=lambda p: p.sv)
def i_ital(g):
    f = Frame(g, 2, 'asc', top=g.p.asc + g.p.sv)
    _free(g)
    g.stroke(f.P(1, 9), *tail(g, f, f.X(1)))
    entry(g, f, f.X(1))
    _dot(g, f, f.X(1))


@ital('j', 6, 1)
def j_ital(g):
    from .figures import beak_depth
    f = Frame(g, 6, 'asc', top=g.p.asc + g.p.sv)
    p = f.p
    _free(g)
    g.stroke(f.P(5, 9), B(*f.P(5, -2)), B(*f.P(1, -2)), (f.X(1), -p.desc + beak_depth(p)))
    entry(g, f, f.X(5))
    _dot(g, f, f.X(5))


@ital('l', 6, 1)
def l_ital(g):
    f = Frame(g, 6, 'asc')
    _free(g)
    g.defaults_used['stem'] = f.X(2)
    g.stroke(f.P(2, 13), *tail(g, f, f.X(2)))
    entry(g, f, f.X(2), g.p.asc)


@ital('n', 8, 2)
def n_ital(g):
    f = Frame(g, 8, 'lower')
    _free(g)
    xs, xr = f.X(1), f.X(7)
    g.stroke(f.P(1, 0), f.P(1, 9))
    entry(g, f, xs)
    arch, cut = shoulder(g, f, xs, xr, drop=BRANCH)
    g.stroke(*arch, *tail(g, f, xr), start=cut)


@ital('m', 12, 3)
def m_ital(g):
    f = Frame(g, 12, 'lower')
    _free(g)
    x1, x2, x3 = f.X(1), f.X(6), f.X(11)
    g.stroke(f.P(1, 0), f.P(1, 9))
    entry(g, f, x1)
    arch, cut = shoulder(g, f, x1, x2, drop=BRANCH)
    g.stroke(*arch, (x2, 0), start=cut)
    arch, cut = shoulder(g, f, x2, x3, drop=BRANCH)
    g.stroke(*arch, *tail(g, f, x3), start=cut)


@ital('h', 8, 2)
def h_ital(g):
    f = Frame(g, 8, 'asc')
    _free(g)
    xs, xr = f.X(1), f.X(7)
    g.stroke(f.P(1, 0), f.P(1, 13))
    entry(g, f, xs, g.p.asc)
    arch, cut = shoulder(g, f, xs, xr, drop=BRANCH)
    g.stroke(*arch, *tail(g, f, xr), start=cut)


@ital('r', 8, 1)
def r_ital(g):
    f = Frame(g, 8, 'lower')
    _free(g)
    xs = f.X(1)
    g.stroke(f.P(1, 0), f.P(1, 9))
    entry(g, f, xs)
    p = g.p
    k = p.sd / SQRT2
    y8, y5 = f.Y(8), f.Y(8 - BRANCH)
    x0 = xs + p.sv / 2 + k - shoulder_enter(p)
    u_ = shoulder_under(p)                                  # its cut lower by what the fill under it is short
    g.stroke((x0 - u_, y5 - u_), (x0 + (y8 - y5), y8), f.P(8, 8), start='h')


@ital('u', 8, 2)
def u_ital(g):
    f = Frame(g, 8, 'lower')
    _free(g)
    xl, xr = f.X(1), f.X(7)
    # the bowl's foot runs on under the right stem into the exit, as a hand writes a u
    exit_past(g, f, xr, [f.P(1, 9), B(*f.P(1, 1))])
    entry(g, f, xl)
    g.stroke(f.P(7, 9), f.P(7, 1))


@ital('a', 8, 2)
def a_ital(g):
    """The single-storey a: the d's bowl on a stem that stops at the
    x-height and leaves on the t's foot."""
    f = Frame(g, 8, 'lower')
    _free(g)
    # the bowl's foot runs on past the stem into the exit (a corner on the
    # stem would cut across the bowl)
    g.stroke(f.P(7, 9), f.P(7, 1))
    g.stroke(f.P(7, 8), B(*f.P(1, 8)), B(*f.P(1, 1)), f.P(7, 1), closed=True)
    exit_past(g, f, f.X(7))


@ital('d', 8, 2)
def d_ital(g):
    f = Frame(g, 8, 'asc')
    _free(g)
    g.stroke(f.P(7, 13), f.P(7, 1))
    g.stroke(f.P(7, 8), B(*f.P(1, 8)), B(*f.P(1, 1)), f.P(7, 1), closed=True)
    exit_past(g, f, f.X(7))


@ital('b', 8, 2)
def b_ital(g):
    f = Frame(g, 8, 'asc')
    _free(g)
    g.stroke(f.P(1, 13), f.P(1, 0))
    entry(g, f, f.X(1), g.p.asc)
    g.stroke(f.P(1, 8), B(*f.P(7, 8)), B(*f.P(7, 1)), f.P(1, 1), closed=True)


@ital('p', 8, 2)
def p_ital(g):
    f = Frame(g, 8, 'lower')
    _free(g)
    g.stroke(f.P(1, 9), f.P(1, -3))
    entry(g, f, f.X(1))
    g.stroke(f.P(1, 8), B(*f.P(7, 8)), B(*f.P(7, 1)), f.P(1, 1), closed=True)


@ital('f', 7, 1)
def f_ital(g):
    """The stem runs on below the baseline and turns back, the top's hook
    turned over."""
    f = Frame(g, 7, 'asc')
    g.clip = (-f.W, -g.p.desc, 2 * f.W, g.p.asc)
    g.stroke(f.P(7, 12), B(*f.P(3.5, 12)), B(*f.P(3.5, -2)), f.P(0, -2))
    crossbar(g, f.X(0.5), f.X(6.5), g.p.xh)


# --- Cursive forms ---------------------------------------------------------

K_FILL = (2.5, 0.5)     # breaks: the italic k's notch floor this far under the arch starts to fill, and is full by the second


@ital('k', 8, 1, openings=[Opening(_one_counter, 'loop', lambda p: 3.0, max_ratio=AUTO_SHARE, hold=True)])
def k_ital(g):
    """The looped k: the arm closes into a small bowl on the stem, and the
    leg leaves the bowl's foot at 45 degrees. At heavy weights the loop
    reaches lower so it stays open.

    The arm leaves the stem as the n's shoulder does, with the notch under
    it, which in the loop is a little step at the counter's top left. As
    the weight grows the arm's diagonal shortens and the notch's floor (the
    diagonal's level start) rises toward the arch's underside; reaching it,
    the diagonal is shorter than it is thick and the notch would open into
    a slot in the arch (and, far into the stem, the start comes out of the
    stem's back: a nub at Black). So from K_FILL[0] breaks under the arch a
    45-degree fill grows across the notch from its inner corner, the step
    shrinking steadily, and by K_FILL[1] the arm's underside runs straight
    into the stem, one shape on to Black."""
    f = Frame(g, 8, 'asc')
    _free(g)
    p = g.p
    g.square = True         # its counter's side closes to a point and opens again: curved throughout (italic.SQUARE)
    xs = f.X(1)
    g.stroke(f.P(1, 13), f.P(1, 0))
    entry(g, f, xs, p.asc)
    ylo = f.Y(g.free('loop', 4.0))
    arch, cut = shoulder(g, f, xs, f.X(6.5), drop=BRANCH)
    t = 1.0
    if cut == 'h':
        depth = (arch[1][1] - arch[0][1] - g.sh / 2) / p.c     # the notch's floor under the arch, in breaks
        s = (K_FILL[0] - depth) / (K_FILL[0] - K_FILL[1])
        t = 0.0 if s <= 0 else 1.0 if s >= 1 else s * s * (3 - 2 * s)
    if t >= 1:
        arch, cut = shoulder(g, f, xs, f.X(6.5), drop=BRANCH, notch=False)
    g.stroke(*arch, B(f.X(6.5), ylo), (xs, ylo), start=cut)
    x0 = f.X(3.5)
    g.stroke((x0, ylo), (x0 + ylo, 0), start='h', end='h')
    if 0 < t < 1 and cut == 'h':
        # the fill: a 45-degree stroke from the stem's centre whose underside
        # cuts the notch's inner corner, t of the way across; above the
        # notch's floor it lies inside the arm, its top a quarter break short
        # of the arm's (drawn last, so the other strokes keep their names)
        (xa, ya), k = arch[0], p.sd / SQRT2
        notch = xa + k - (xs + p.sv / 2)                    # the floor's run out from the stem
        if notch > 0:
            w = t * notch / SQRT2 + p.c / 4
            at = xa + k - (1 - t) * notch - w / SQRT2       # the fill's centreline on the floor's line
            g.stroke((xs, ya - (at - xs), w), (at + p.c, ya + p.c), start='v', end='h')


@ital('y', 8, 2)
def y_ital(g):
    """A u whose right stem runs on into the descender, as the g's, and
    whose foot comes into that stem through the bowls' notch (lower.bowl_join;
    the owner, 2026-11-10: "this should be on the y as well"). Until 1.017
    the foot met the stem square."""
    from .lower import BOWL_DROP, turned
    f = Frame(g, 8, 'lower')
    _free(g)
    arch, cut = shoulder(g, f, f.X(1), f.X(7), drop=BOWL_DROP)
    g.stroke(f.P(1, 9), *reversed(turned(f.W, f.p.xh, arch)), end=cut)
    entry(g, f, f.X(1))
    hook(g, f)
    g.butt += crotch_butt(g, f.Y(1))                    # the foot meets the descender square (lower.crotch_butt)


@ital('s', 8, 2)
def s_ital(g):
    """The spine a 45-degree diagonal with the 2's notch, from a corner at
    the top left to one at the bottom right."""
    f = Frame(g, 8, 'lower')
    p = g.p
    xl, xr = f.X(1), f.X(7)
    yt, yb = f.Y(8), f.Y(1)
    J = jog(p)
    run = (xr - xl - J) / 2                                 # each half of the spine, across and down
    ymid = (yt + yb) / 2
    y_hi, y_lo = ymid + run, ymid - run
    x1 = xl + run
    g.stroke((f.X(8), yt), B(xl, yt), (xl, y_hi), (x1, ymid, min(J, g.sh)), (x1 + J, ymid),
             (xr, y_lo), B(xr, yb), (f.X(0), yb))


EYE = 0.6          # the least share of their own thickness the cursive e's top and bar keep, thinned for its eye
EXIT_OVER = 1.5    # edge breaks: the least the cursive e's exit stands over its foot


def _e_strokes(g, f, xl, xr, x_exit):
    """The cursive e on a back at xl: the eye's top and bar, the foot and
    the exit.

    The top, the back and the foot are the alphabet's strokes at every
    weight. The bar across the eye is the letter's cross and the exit its
    flick, and from the Regular both are the Regular's own (small_part):
    the bar as thick, the flick as thick and as far over the foot. With a
    bar that stays the Regular's the eye stays open by itself; should it
    ever fall short of its share of the stem (``eye``, the opening:
    draw._opened), the top and the bar give together, down to EYE of their
    own thickness, and nothing else does.

    Until 1.017 the eye was kept by thinning all the letter's horizontals,
    the foot with the top, and then the bar: from SemiBold the foot was 0.70
    of every other letter's (104 units beside the a's and the o's 149 at
    Black), the top fell from 98 units at 550 to 73 at 600, the bar from 121
    at Bold to 88 at Black, and the exit, a reach that shrinks with the
    white, stood 28 units over the foot at Black for 59 at Regular: all but
    gone. (The owner, 2026-11-10: "there's definitely something weird going
    on with the thicknesses towards the black ... the little bit at the
    bottom ... isn't nearly as thick"; and of the fix, "it's also important
    that we remain uniform in thickness".) With the foot and the top whole
    and the bar at the weight's own thickness the eye was a slit from Bold
    and the join under it the widest spot of the cursive, a stem and a
    half across at Black."""
    p = g.p
    full = max(g.sh0 * g.sh_k, p.floor)                     # the alphabet's horizontal here
    k = g.free('eye', 1.0)
    q = small_part(p)
    # the bar is the letter's cross and the exit its flick: both the
    # Regular's from there to Black (small_part)
    cross = g.held((1.0, 1.0))                              # the flick's stroke
    top, bar = full * k, p.sd * g.held_share((1.0, 1.0)) * k
    yt, yf = p.xh - top / 2, full / 2
    g.stroke((xl, yt - (xr - xl), bar), (xr, yt))
    if q is None:
        L = max(_reach(p, FLAG), full / 2 + EXIT_OVER * p.c)
        g.stroke((xr, yt, top), B(xl, yt), B(xl, yf, None, full), (x_exit, yf), (x_exit + L, yf + L), end='h')
        return
    # the foot ends on the flick's slope and the flick stands over it as far
    # as the Regular's stands over its own; the flick itself is laid on from
    # inside the foot, its end broken as the Regular's is (Glyph.kept)
    over = max(_reach(q, FLAG) - q.sh / 2, EXIT_OVER * q.c)
    L = full / 2 + over
    back = full / 4
    g.stroke((xr, yt, top), B(xl, yt), B(xl, yf, None, full), (x_exit, yf, cross), (x_exit + L / 2, yf + L / 2))
    with g.kept():
        g.stroke((x_exit - back, yf - back, cross), (x_exit + L, yf + L), end='h')


@ital('e', 8, 2, openings=[Opening(_one_counter, 'eye', lambda p: EYE, max_ratio=AUTO_SHARE, hold=True)])
def e_ital(g):
    """The cursive e: its bar a 45-degree stroke rising from the left side
    into the top right corner, the eye the triangle above it; the lower arm
    leaves on a 45-degree upstroke, a hand's exit. The bar and the exit are
    the Regular's from there to Black, and the eye stays open (_e_strokes)."""
    f = Frame(g, 8, 'lower')
    _free(g)
    _e_strokes(g, f, f.X(1), f.X(7), f.X(6))


@ital('ae', 14, 3, width=lambda p: REGISTRY['a.ital'].width(p) + REGISTRY['e.ital'].width(p) - p.sv,
      openings=[Opening(lambda g: _counter_white(g, 2), 'eye', lambda p: EYE, max_ratio=AUTO_SHARE, hold=True)])
def ae_ital(g):
    """The single-storey a and the cursive e on one stem: the a's bowl on
    its left, the e's eye and exit on its right."""
    f = Frame(g, 14, 'lower')
    _free(g)
    g.stroke(f.P(7, 8), B(*f.P(1, 8)), B(*f.P(1, 1)), f.P(7, 1), closed=True)
    _e_strokes(g, f, f.X(7), f.X(13), f.X(12))


# --- Cyrillic italic ---------------------------------------------------------
# Cyrillic italics are cursive in their own way: и is written as a u, п as an
# n, т as an m, д as a g; ш, щ and ц are u's with more stems or a descender.
# (а е р у come through their Latin forms already.)

def _as(name, latin):
    spec = REGISTRY[f'{latin}.ital'] if f'{latin}.ital' in REGISTRY else REGISTRY[latin]
    upright = REGISTRY[name]

    def fn(g, spec=spec, upright=upright):
        if g.p.mono:
            return upright.fn(g)
        return spec.fn(g)
    glyph(f'{name}.ital', None, spec.width, kind=upright.kind)(fn)


for _cy, _lat in (('uni0438', 'u'), ('uni043F', 'n'), ('uni0442', 'm'), ('uni0434', 'g')):
    _as(_cy, _lat)


def _u_stems(g, f, xs, descender):
    """A u of several stems: the first with the 1's flag, each joined to the
    next by a bowl corner on the baseline; the last leaves on the t's foot
    or runs into a descender's tick."""
    if descender:
        # a small corner into the tick, so the foot stays straight past the last stem
        g.stroke(f.P(xs[0], 9), B(*f.P(xs[0], 1)), B(*f.P(xs[-1] + 1.5, 1), g.p.m / 2), f.P(xs[-1] + 1.5, -2))
    else:
        exit_past(g, f, f.X(xs[-1]), [f.P(xs[0], 9), B(*f.P(xs[0], 1))])
    entry(g, f, f.X(xs[0]))
    for x in xs[1:]:
        g.stroke(f.P(x, 9), f.P(x, 1))


@ital('uni0448', 12, 3)
def sha_ital(g):
    f = Frame(g, 12, 'lower')
    _free(g)
    _u_stems(g, f, (1, 6, 11), False)


@ital('uni0449', 12, 3)
def shcha_ital(g):
    f = Frame(g, 12, 'lower')
    _free(g)
    _u_stems(g, f, (1, 6, 11), True)


@ital('uni0446', 8, 2)
def tse_ital(g):
    f = Frame(g, 8, 'lower')
    _free(g)
    _u_stems(g, f, (1, 7), True)
