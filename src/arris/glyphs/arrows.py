"""Arrows: one builder for every arrow.

An arrow is drawn in a frame of its own, pointing along +u with v across
it, then turned to one of eight directions and centred on the math axis
(``axis``). It is made of three kinds of part, each with a few forms:

* **shafts**: single, double and triple (a stack of bars, as = and the
  identity sign), dashed, wave (the tilde's step) and squiggle (a
  45-degree zigzag);
* **heads**: barbs (a chevron whose two 45-degree strokes meet in a point,
  the shafts ending in its crotch, as < and > are drawn), double barbs,
  a half barb (harpoons), an open triangle, a bar stop;
* **tails**: a flat end, a bar (maps-to), a feather (a chevron at the
  tail), a second head, a hook, a loop, a double stroke across the shaft.

Every arrow follows the same rules (DESIGN.md, "Symbols keep their parts
apart"):

* a barb reaches past the outermost shaft it guards far enough to leave at
  least half a stem of white between its end and that shaft
  (``reach``); the module design (3.2 modules and half a stem) holds where
  that is longer;
* barb ends are cut square to the arrow, as < and > are, and the corner
  rule trims their acute corners;
* the shaft keeps two and a half stems of length beyond a head (a stem and
  a half between two heads), and the arrow lengthens to keep it;
* parts that stack (double and triple shafts, paired arrows) are a tight
  stack: their strokes lighten toward Black, down to ``STACK_MIN`` of the
  weight's, so that the white between them can stay as wide as the
  equal sign's without the arrow outgrowing the line;
* in the monospaced cell an arrow fills the figures' body; a head too wide
  for the cell shortens down to the white rule, then lightens.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from functools import lru_cache

from ..draw import B, REGISTRY, _lightened, _thickness, glyph
from ..geom import Node, Stroke, stroke_polygon
from ..params import SQRT2
from .figures import heaviness
from .letterframe import STEEP, letter_width
from .punct import axis

WHITE = 0.5          # white under a barb's end, in stems
SHAFT_FREE = 2.5     # shaft beyond a single head, in stems
SHAFT_BETWEEN = 1.5  # shaft between two heads, in stems
MONO_FREE = 0.4      # in the monospaced cell, free shafts shorten to this share
MONO_MIN = 0.6       # ... strokes may lighten to this share of the weight's
MONO_WHITE = 0.3     # ... and, last, the white under a barb narrow to this many stems
DASHES = 3           # a dashed shaft's dashes (the head's included), at every weight
STACK_MIN = 0.75     # stacked arrows' strokes at Black, of the weight's own


# --- Frames -------------------------------------------------------------------

class Turn:
    """Local (u, v) to glyph directions: a rotation by ``theta`` degrees
    (a multiple of 45)."""

    def __init__(self, theta: float):
        t = math.radians(theta)
        self.theta = theta % 360
        self.c, self.s = round(math.cos(t), 12), round(math.sin(t), 12)

    def vec(self, u, v):
        return (u * self.c - v * self.s, u * self.s + v * self.c)

    @property
    def horizontal(self):
        return self.theta % 180 == 0

    @property
    def vertical(self):
        return self.theta % 180 == 90

    def cap(self, kind):
        """'across' cuts a stroke's end square to the arrow, 'along' parallel
        to it; on a diagonal arrow both are square to the stroke itself."""
        if kind == 'across':
            return 'v' if self.horizontal else 'h' if self.vertical else 'flat'
        if kind == 'along':
            return 'h' if self.horizontal else 'v' if self.vertical else 'flat'
        if kind in ('gh', 'gv'):                            # in glyph terms, whatever the turn
            return kind[1]
        return kind


@dataclass
class Part:
    """A stroke in the arrow's frame: points (u, v), or ('bowl', u, v, leg)."""
    pts: list
    start: str = 'flat'
    end: str = 'flat'
    closed: bool = False
    w: float | None = None          # thickness of every segment (None: by direction)


class Ctx:
    """What a part needs to know: the parameters, the horizontal stroke in
    force and the turn, so thicknesses can be read in the arrow's frame."""

    def __init__(self, p, sh, turn: Turn, white=WHITE):
        self.p, self.sh, self.turn = p, sh, turn
        self.th = _thickness(p, sh)
        self.white = white
        self.free_k = MONO_FREE if p.mono else 1.0

    def free(self, stems):
        """A free run of shaft, in units."""
        return stems * self.free_k * self.p.sv

    def t(self, du, dv):
        """Thickness of a stroke running along local (du, dv)."""
        return self.th(self.turn.vec(du, dv))

    @property
    def ts(self):
        return self.t(1, 0)

    def kb(self):
        """Half a barb's extent measured along v (and along u): its
        thickness over cos 45."""
        return max(self.t(-1, 1), self.t(-1, -1)) / SQRT2


def to_glyph(ctx, parts, ox=0.0, oy=0.0):
    out = []
    for prt in parts:
        nodes = []
        for q in prt.pts:
            if q[0] == 'bowl':
                u, v, leg = q[1], q[2], q[3]
                x, y = ctx.turn.vec(u, v)
                nodes.append(('bowl', x + ox, y + oy, leg, prt.w))
            else:
                x, y = ctx.turn.vec(*q[:2])
                nodes.append((x + ox, y + oy) + ((prt.w,) if prt.w is not None else ()))
        out.append((nodes, prt.closed, ctx.turn.cap(prt.start), ctx.turn.cap(prt.end)))
    return out


def _stroke_obj(ctx, nodes, closed, start, end):
    ns = []
    for q in nodes:
        if q[0] == 'bowl':
            ns.append(Node(q[1], q[2], ctx.p.leg if q[3] is None else q[3], q[4]))
        else:
            ns.append(Node(q[0], q[1], 0.0, q[2] if len(q) > 2 else None))
    return Stroke(tuple(ns), closed, start, end)


def bounds(ctx, strokes):
    """The ink's box (before the corner rule, which only trims it)."""
    x0 = y0 = 1e9
    x1 = y1 = -1e9
    for nodes, closed, start, end in strokes:
        poly = stroke_polygon(_stroke_obj(ctx, nodes, closed, start, end), ctx.th, ctx.p.c)
        a, b, c, d = poly.bounds
        x0, y0, x1, y1 = min(x0, a), min(y0, b), max(x1, c), max(y1, d)
    return x0, y0, x1, y1


def emit(g, strokes):
    for nodes, closed, start, end in strokes:
        pts = []
        for q in nodes:
            pts.append(B(q[1], q[2], q[3], q[4]) if q[0] == 'bowl' else q)
        g.stroke(*pts, closed=closed, start=start, end=end)


# --- Measures -------------------------------------------------------------------

def stack_k(p) -> float:
    """Stroke factor for stacked arrows: 1 up to the watch's weight, easing
    to STACK_MIN at Black."""
    return 1.0 - (1.0 - STACK_MIN) * heaviness(p)


def bar_gap(ctx, t=None) -> float:
    """White between stacked shafts: the equal sign's, a module or four
    fifths of the bar, whichever is more."""
    t = ctx.ts if t is None else t
    return max(0.8 * t, ctx.p.m)


def shaft_offsets(ctx, n: int):
    """Centrelines of n stacked shafts, centred on the arrow."""
    if n == 1:
        return [0.0]
    step = ctx.ts + bar_gap(ctx)
    return [(i - (n - 1) / 2) * step for i in range(n)]


def reach(ctx, off=0.0, design=True) -> float:
    """How far a barb reaches back (and out) from the tip, along u: the
    module design (3.2 modules and half a stem, along the barb), or as much
    as leaves half a stem of white between the barb's end and the outermost
    shaft (at ``off``), whichever is more."""
    p = ctx.p
    need = ctx.kb() + off + ctx.ts / 2 + ctx.white * p.sv
    if not design:
        return need
    return max((3.2 * p.m + 0.5 * p.sv) / SQRT2, need)


# --- Heads (tip vertex at u = 0, pointing +u) -------------------------------------

@dataclass
class Piece:
    parts: list = field(default_factory=list)
    depth: float = 0.0              # how far back from its anchor it reaches (centreline)
    ends: dict = field(default_factory=dict)   # v -> where a shaft at v ends (u)


def chevron(h, u0=0.0, v0=0.0, sides=(1, -1)):
    """A chevron pointing +u with its vertex at (u0, v0), barbs reaching h
    back and out."""
    if len(sides) == 2:
        return Part([(u0 - h, v0 + h), (u0, v0), (u0 - h, v0 - h)], 'across', 'across')
    s = sides[0]
    return Part([(u0, v0), (u0 - h, v0 + s * h)], 'flat', 'across')


def head(ctx, kind, h, offs):
    """A head of ``kind`` at u = 0 over shafts at offsets ``offs``."""
    p = ctx.p
    pc = Piece()
    eps = 0.01 * ctx.ts
    if kind in ('barb', 'bar'):
        pc.parts.append(chevron(h))
        pc.depth = h
        pc.ends = {v: -abs(v) - eps for v in offs}
        if kind == 'bar':                                   # a stop across the tip, the point buried in it
            kb = ctx.kb()
            tb = ctx.t(0, 1)
            pc.parts.append(Part([(kb, -(h + kb)), (kb, h + kb)], 'along', 'along'))
    elif kind == 'dbl':
        step = SQRT2 * (ctx.t(-1, 1) + max(0.8 * p.m, 0.7 * ctx.t(-1, 1)))
        pc.parts += [chevron(h), chevron(h, -step)]
        pc.depth = h + step
        pc.ends = {v: -abs(v) - eps for v in offs}
    elif kind in ('half+', 'half-'):
        s = 1 if kind == 'half+' else -1
        # the shaft runs on into its one barb, a single stroke turning back
        # through 135 degrees: the outer corner is the tip
        lead = h
        pc.parts.append(Part([(-lead, 0.0), (0.0, 0.0), (-h, s * h)], 'flat', 'across'))
        pc.depth = h
        pc.ends = {v: -lead / 2 for v in offs}
    elif kind == 'open':
        hh = open_reach(ctx, h)
        pc.parts.append(Part([(0.0, 0.0), (-hh, hh), (-hh, -hh)], closed=True))
        pc.depth = hh
        pc.ends = {v: -hh for v in offs}
    else:
        raise ValueError(kind)
    return pc


def open_reach(ctx, h):
    """An open triangle's reach: the barbs', or as much as keeps a counter
    of three quarters of a stem inside it (a right isosceles triangle's
    inradius is 0.414 of its reach; its strokes take half their weight
    from it)."""
    t = max(ctx.t(-1, 1), ctx.t(0, 1))
    return max(h, (0.45 * ctx.p.sv + t / 2) / (SQRT2 - 1))


# --- Shafts ---------------------------------------------------------------------

def shaft(ctx, kind, starts, ends, offs, start='flat', back=None):
    """Shafts from where the tail leaves them (``starts``) to where the head
    takes them (``ends``); ``back`` is where the head's barbs end, so a
    patterned shaft (dashes, a wave) lays its pattern clear of them."""
    p = ctx.p
    parts = []
    u_tail = starts[offs[len(offs) // 2]]
    if kind in ('single', 'double', 'triple'):
        for v in offs:
            parts.append(Part([(starts[v], v), (ends[v], v)], start, 'flat'))
    elif kind == 'dashed':
        # n dashes and n - 1 gaps from the tail to the barbs' ends, stretched
        # to fit; the last dash runs on into the head
        dash, gap = dash_measures(ctx)
        run = back - u_tail
        n = DASHES                                          # the same at every weight
        k = (run + gap) / (n * (dash + gap))
        dash, gap = dash * k, gap * k
        u = u_tail
        for i in range(n):
            end = ends[0.0] if i == n - 1 else u + dash
            parts.append(Part([(u, 0.0), (end, 0.0)], start if i == 0 else 'flat', 'flat'))
            u += dash + gap
    elif kind in ('wave', 'squiggle'):
        parts.append(Part(wave_points(ctx, kind, u_tail, back - wave_lead(ctx), ends[0.0]), start, 'flat'))
    else:
        raise ValueError(kind)
    return parts


def dash_measures(ctx):
    """(dash, gap): a dash twice its gap, the gap never under four fifths
    of a stem."""
    p = ctx.p
    if p.mono:                                              # a cell has room for short dashes only
        return max(1.25 * p.m, 1.0 * p.sv), max(0.75 * p.m, 0.6 * p.sv)
    return max(2.0 * p.m, 1.6 * p.sv), max(1.0 * p.m, 0.8 * p.sv)


def wave_amp(ctx):
    """Half a wave's height: crest and trough keep half a stem of white
    between them."""
    p = ctx.p
    return max(1.0 * p.m, (ctx.ts + 0.5 * p.sv) / 2)


def zigzag_amp(ctx):
    """Half a zigzag's height: the white in each tooth (inside two 45-degree
    strokes meeting at a point) at least a third of a stem deep."""
    p = ctx.p
    return max(1.25 * p.m, ctx.t(1, 1) / SQRT2 + 0.35 * p.sv)


def wave_flat(ctx):
    if ctx.p.mono:
        return max(0.5 * ctx.p.m, 0.4 * ctx.p.sv)
    return max(1.0 * ctx.p.m, 0.75 * ctx.p.sv)


def wave_lead(ctx):
    """Straight shaft between a wave and the barbs' ends."""
    return max(0.5 * ctx.p.sv, 0.5 * ctx.p.m)


def pattern_min(ctx, kind):
    """The shortest run a patterned shaft needs: two dashes and a gap, one
    period of the wave, two teeth of the zigzag."""
    if kind == 'dashed':
        dash, gap = dash_measures(ctx)
        return DASHES * dash + (DASHES - 1) * gap
    if kind == 'wave':
        return 4 * wave_amp(ctx) + 2 * wave_flat(ctx) + wave_lead(ctx)
    if kind == 'squiggle':
        return 6 * zigzag_amp(ctx) + wave_lead(ctx)
    return 0.0


def wave_points(ctx, kind, u0, u_w, u1):
    """A wave from u0 to u_w about v = 0, then straight on to u1 (in the
    head). Wave: the tilde's step (up at 45 degrees, along, down, along),
    its flats stretched to fill. Squiggle: a 45-degree zigzag of n teeth,
    its height stretched to fill."""
    room = u_w - u0
    pts = [(u0, 0.0)]
    if kind == 'wave':
        a, f = wave_amp(ctx), wave_flat(ctx)
        n = 1                                               # one period at every weight (so it varies)
        f = (room - n * 4 * a) / (2 * n)
        u = u0 + a
        pts.append((u, a))
        for i in range(n):
            u += f; pts.append((u, a))
            u += 2 * a; pts.append((u, -a))
            u += f; pts.append((u, -a))
            if i < n - 1:
                u += 2 * a; pts.append((u, a))
        u += a; pts.append((u, 0.0))
    else:
        n = 2                                               # two teeth at every weight
        a = room / (4 * n - 2)
        u = u0 + a
        pts.append((u, a))
        for i in range(2 * n - 2):
            u += 2 * a
            pts.append((u, -a if i % 2 == 0 else a))
        u += a; pts.append((u, 0.0))
    pts.append((max(u1, u + 1e-3), 0.0))
    return pts


# --- Tails ---------------------------------------------------------------------

def tail(ctx, kind, u_t, h, offs, spec):
    """(parts, where each shaft starts, the shafts' start cap) for a tail at u_t."""
    kb = ctx.kb()
    eps = 0.01 * ctx.ts
    if kind in ('flat', None):
        return [], {v: u_t for v in offs}, 'flat'
    if kind == 'bar':
        top = max(offs) + h + kb
        return [Part([(u_t, -top), (u_t, top)], 'along', 'along')], {v: u_t for v in offs}, 'flat'
    if kind == 'feather':
        # a chevron at the tail pointing on along the arrow; the shafts start in its crotch
        return [chevron(h, u_t + h)], {v: u_t + h - abs(v) - eps for v in offs}, 'flat'
    if kind == 'head':
        hp = head(ctx, spec.head, h, offs)
        parts = [Part([_shift_u(_mirror_u(q, 0.0), u_t) for q in prt.pts], prt.start, prt.end, prt.closed, prt.w)
                 for prt in hp.parts]
        return parts, {v: u_t - hp.ends[v] for v in offs}, 'flat'
    raise ValueError(kind)


def _mirror_u(q, u0):
    if q[0] == 'bowl':
        return ('bowl', 2 * u0 - q[1], q[2], q[3])
    return (2 * u0 - q[0], q[1])


def _shift_u(q, du, dv=0.0):
    if q[0] == 'bowl':
        return ('bowl', q[1] + du, q[2] + dv, q[3])
    return (q[0] + du, q[1] + dv)


def _flip_v(q):
    if q[0] == 'bowl':
        return ('bowl', q[1], -q[2], q[3])
    return (q[0], -q[1])


# --- Arrows as drawings ------------------------------------------------------------

class Drawing:
    """An arrow drawing: parts in its frame for a length Ls (tip vertex at
    u = 0, tail at u = -Ls) and a barb reach h."""
    theta = 0.0
    stacked = False
    strike = False
    long = False
    two = False                      # a head at each end

    def offs(self, ctx):
        return [0.0]

    def depth(self, ctx, h):
        """How far the heads and tails reach along the shaft (centrelines)."""
        return h

    def free(self):
        return SHAFT_BETWEEN if self.two else SHAFT_FREE

    def natural(self, ctx):
        p = ctx.p
        return letter_width(18 if self.long else 13 if self.two else 11, 1)(p)

    def parts(self, ctx, Ls, h):
        raise NotImplementedError

    def reach_bounds(self, ctx):
        off = max(self.offs(ctx))
        return reach(ctx, off), reach(ctx, off, design=False)

    def tall(self, ctx):
        """A vertical arrow's height: the cap height."""
        return ctx.p.cap

    def build(self, ctx, mono):
        return fit_straight(self, ctx, mono)


@dataclass(frozen=True)
class Spec(Drawing):
    theta: float = 0.0
    shaft: str = 'single'
    head: str = 'barb'
    tail: str = 'flat'
    strike: bool = False
    long: bool = False
    marks: str = ''          # 'dblbar': two strokes across the shaft

    @property
    def n(self):
        return {'double': 2, 'triple': 3}.get(self.shaft, 1)

    @property
    def stacked(self):
        """Drawn as a tight stack, lighter toward Black: several shafts, a
        patterned shaft, an open head, strokes across the shaft or a base."""
        return (self.n > 1 or self.shaft in ('dashed', 'wave', 'squiggle') or self.head == 'open'
                or self.marks in ('dblbar', 'base'))

    @property
    def two(self):
        return self.tail in ('head', 'feather')

    def offs(self, ctx):
        return shaft_offsets(ctx, self.n)

    def depth(self, ctx, h):
        offs = self.offs(ctx)
        d = head(ctx, self.head, h, offs).depth
        if self.tail == 'head':
            d *= 2
        elif self.tail == 'feather':
            d += h
        t = ctx.t(0, 1)
        if self.marks == 'dblbar':                          # two strokes, white about them
            d += 2 * t + max(bar_gap(ctx, t), 0.8 * ctx.p.sv) + 1.5 * ctx.p.sv
        if self.marks == 'base':                            # a base under the tail's head
            d += t + bar_gap(ctx, t)
        if self.strike:                                     # room for the negation, clear of the barbs
            p = ctx.p
            half = max(self.offs(ctx)) + ctx.ts / 2 + max(2.0 * p.m, 1.0 * p.sv)
            d += half + p.ss / STEEP[1] + (0.5 if p.mono else 1.5) * p.sv
        return d + pattern_min(ctx, self.shaft)

    def free(self):
        if self.shaft in ('dashed', 'wave', 'squiggle'):
            return 0.0
        return Drawing.free(self)

    def parts(self, ctx, Ls, h):
        offs = self.offs(ctx)
        hp = head(ctx, self.head, h, offs)
        tparts, starts, cap0 = tail(ctx, self.tail, -Ls, h, offs, self)
        parts = list(hp.parts) + tparts
        back = -hp.depth
        if self.tail == 'head':
            back_t = -Ls + hp.depth
        else:
            back_t = min(starts.values())
        parts += shaft(ctx, self.shaft, {v: back_t if self.tail == 'head' and self.shaft in ('dashed', 'wave', 'squiggle') else starts[v] for v in offs},
                       hp.ends, offs, start=cap0, back=back)
        if self.tail == 'head' and self.shaft in ('dashed', 'wave', 'squiggle'):
            # the pattern starts clear of the tail's head, joined to it by a straight run
            parts.append(Part([(starts[0.0], 0.0), (back_t + 1e-3, 0.0)]))
        if self.marks == 'dblbar':
            # two strokes across the shaft, a bar's white apart, halfway along it
            um = (-Ls - hp.depth) / 2
            t = ctx.t(0, 1)
            gap = max(bar_gap(ctx, t), 0.8 * ctx.p.sv)
            half = 0.8 * (h + ctx.kb())
            for du in (-(gap + t) / 2, (gap + t) / 2):
                parts.append(Part([(um + du, -half), (um + du, half)], 'along', 'along'))
        if self.marks == 'base':
            # a bar under the tail's point, a bar's white below it, as wide as the head
            t = ctx.t(0, 1)
            ub = -Ls - ctx.kb() - bar_gap(ctx, t) - t / 2
            half = h + ctx.kb()
            parts.append(Part([(ub, -half), (ub, half)], 'along', 'along'))
        return parts


def _extent(ctx, strokes, along):
    x0, y0, x1, y1 = bounds(ctx, strokes)
    return (x1 - x0) if along == 'x' else (y1 - y0) if along == 'y' else max(x1 - x0, y1 - y0)


@lru_cache(maxsize=8192)
def layout(dr: Drawing, p, sh):
    """(W, strokes in glyph coordinates, stroke factor) for an arrow
    drawing. Stacked drawings lighten toward Black (``stack_k``). In the
    monospaced cell a drawing too big for the cell first shortens its
    shafts and heads (down to the white rule), then lightens a twentieth at
    a time down to MONO_MIN of the weight's strokes, then lets the white
    under its barbs narrow to MONO_WHITE stems; past that it overflows."""
    k = stack_k(p) if dr.stacked else 1.0
    if not p.mono:
        pk = _lightened(p, k) if k != 1.0 else p
        W, strokes, _ = _layout(dr, pk, sh * k, WHITE)
        return W, strokes, k
    tries = []
    kk = k
    while kk >= MONO_MIN - 1e-9:
        tries.append((kk, WHITE))
        kk -= 0.05
    tries.append((min(k, MONO_MIN), MONO_WHITE))
    best = None
    for kk, white in tries:
        pk = _lightened(p, kk) if kk != 1.0 else p
        W, strokes, fits = _layout(dr, pk, sh * kk, white)
        best = (W, strokes, kk)
        if fits:
            break
    return best


def _layout(dr, p, sh, white):
    ctx = Ctx(p, sh, Turn(dr.theta), white)
    strokes, fits = dr.build(ctx, p.mono)
    W, strokes = centre(ctx, strokes)
    return W, strokes, fits


def fit_straight(dr, ctx, mono):
    """Lay out a drawing along its direction: horizontal arrows take their
    natural length (or the cell), vertical ones the cap height, diagonal
    ones a box 0.85 of it, each lengthening to keep its free shaft."""
    p, turn = ctx.p, ctx.turn
    h_des, h_min = dr.reach_bounds(ctx)
    along = 'x' if turn.horizontal else 'y' if turn.vertical else 'xy'
    cell = p.fig_w

    def make(Ls, h):
        return to_glyph(ctx, dr.parts(ctx, Ls, h))

    def ext_of(Ls, h):
        return _extent(ctx, make(Ls, h), along)

    def solve(target, h):
        """Shaft length giving the target extent (the extent is linear in
        Ls: slope 1 along an axis, 1/sqrt2 on a diagonal)."""
        L0 = dr.depth(ctx, h) + 2 * p.sv
        e0, e1 = ext_of(L0, h), ext_of(L0 + p.m * 10, h)
        slope = (e1 - e0) / (p.m * 10)
        return L0 + (target - e0) / slope

    def min_len(h):
        return dr.depth(ctx, h) + ctx.free(dr.free())

    def across(h):
        x0, y0, x1, y1 = bounds(ctx, make(min_len(h), h))
        return (y1 - y0) if turn.horizontal else (x1 - x0)

    h = h_des
    fits = True
    if turn.horizontal:
        target = max(dr.natural(ctx), ext_of(min_len(h), h))
        if mono and target > cell:
            target = cell
            if ext_of(min_len(h), h) > cell:
                h = _shrink(lambda hh: ext_of(min_len(hh), hh) <= cell, h_min, h_des)
                fits = ext_of(min_len(h), h) <= cell + 1e-6
                target = max(cell, ext_of(min_len(h), h))
    elif turn.vertical:
        if mono and across(h) > cell:
            h = _shrink(lambda hh: across(hh) <= cell, h_min, h_des)
            fits = across(h) <= cell + 1e-6
        target = max(dr.tall(ctx), ext_of(min_len(h), h))
    else:
        target = max(0.85 * p.cap, ext_of(min_len(h), h))
        if mono and target > cell:
            if ext_of(min_len(h), h) > cell:
                h = _shrink(lambda hh: ext_of(min_len(hh), hh) <= cell, h_min, h_des)
                fits = ext_of(min_len(h), h) <= cell + 1e-6
            target = max(cell, ext_of(min_len(h), h))
    Ls = solve(target, h)
    strokes = make(Ls, h)
    if dr.strike:
        strokes += strike(ctx, dr, Ls, h)
    return strokes, fits


def _shrink(ok, lo, hi):
    """The longest reach in [lo, hi] for which ok() holds (lo if none)."""
    if ok(hi):
        return hi
    if not ok(lo):
        return lo
    for _ in range(20):
        mid = (lo + hi) / 2
        if ok(mid):
            lo = mid
        else:
            hi = mid
    return lo


def centre(ctx, strokes, W=None):
    """Shift strokes so the ink sits in a body of its own width (or W),
    centred on the math axis."""
    x0, y0, x1, y1 = bounds(ctx, strokes)
    W = (x1 - x0) if W is None else W
    dx = (W - (x1 - x0)) / 2 - x0
    dy = axis(ctx.p) - (y0 + y1) / 2
    return W, [([_move(q, dx, dy) for q in nodes], c, s, e) for nodes, c, s, e in strokes]


def _move(q, dx, dy):
    if q[0] == 'bowl':
        return ('bowl', q[1] + dx, q[2] + dy, q[3], q[4])
    return (q[0] + dx, q[1] + dy) + tuple(q[2:])


def strike(ctx, spec, Ls, h):
    """The negation: a 2:1 stroke, as the not-equal sign's, across the
    middle of the free shaft (clear of the barbs), reaching two modules or
    a stem past the outer shafts."""
    p = ctx.p
    offs = spec.offs(ctx)
    hd = head(ctx, spec.head, h, offs).depth
    td = hd if spec.tail == 'head' else (h if spec.tail == 'feather' else 0.0)
    um = (-Ls + td - hd) / 2
    xm, ym = ctx.turn.vec(um, 0.0)
    half = max(offs) + ctx.ts / 2 + max(2.0 * p.m, 1.0 * p.sv)
    return [([(xm - half / 2, ym - half), (xm + half / 2, ym + half)], False, 'h', 'h')]


# --- Paired arrows ----------------------------------------------------------------

def pair_sep(ctx):
    """Between the shafts of paired harpoons (their barbs face out): a
    shaft and the equal sign's white, and a quarter more."""
    return ctx.ts + 1.25 * bar_gap(ctx)


@dataclass(frozen=True)
class Pair(Drawing):
    """Two or three arrows side by side, with the shortest heads the white
    rule allows.

    * 'opp' (two arrows pointing opposite ways) and 'same' (arrows pointing
      the same way) stand two barbs apart: a head's barb then clears the
      other arrow's shaft by the white rule, and side by side the inner
      barbs of two heads meet, a zigzag whose points are the tips;
    * 'harpoon' (two harpoons pointing opposite ways): barbs outward, the
      shafts as close as the equal sign's bars allow.

    ``side``: where the arrow pointing along theta lies (+1: left of travel).
    """
    theta: float = 0.0
    mode: str = 'opp'
    side: int = 1
    n: int = 2

    @property
    def stacked(self):
        return True

    @property
    def two(self):
        return self.mode != 'same'

    def offs(self, ctx):
        return [0.0]

    def reach_bounds(self, ctx):
        """Barbs a little shorter than a single arrow's, or as short as the
        white rule allows, whichever is longer."""
        h_min = reach(ctx, design=False)
        return max(h_min, 0.85 * (3.2 * ctx.p.m + 0.5 * ctx.p.sv) / SQRT2), h_min

    def depth(self, ctx, h):
        return h if self.mode == 'same' else 2 * h

    def sep(self, ctx, h):
        if self.mode == 'harpoon':
            return pair_sep(ctx)
        return 2 * h if self.n == 2 else 1.5 * h

    def parts(self, ctx, Ls, h):
        d = self.sep(ctx, h)
        eps = 0.01 * ctx.ts
        if self.mode == 'same':
            vs = [(i - (self.n - 1) / 2) * d for i in range(self.n)][::-1]
            pts = [(-h, vs[0] + h), (0.0, vs[0])]
            for a, b in zip(vs, vs[1:]):
                pts += [(-(a - b) / 2, (a + b) / 2), (0.0, b)]
            pts.append((-h, vs[-1] - h))
            parts = [Part(pts, 'across', 'across')]
            parts += [Part([(-Ls, v), (-eps, v)]) for v in vs]
            return parts
        va, vb = self.side * d / 2, -self.side * d / 2
        if self.mode == 'harpoon':
            s = self.side
            return [Part([(-Ls, va), (0.0, va), (-h, va + s * h)], 'flat', 'across'),
                    Part([(0.0, vb), (-Ls, vb), (-Ls + h, vb - s * h)], 'flat', 'across')]
        return [chevron(h, 0.0, va), Part([(-Ls, va), (-eps, va)]),
                Part([(-Ls + h, vb + h), (-Ls, vb), (-Ls + h, vb - h)], 'across', 'across'),
                Part([(-Ls + eps, vb), (0.0, vb)])]


# --- Arrows drawn in the glyph's own frame ------------------------------------------

def chev(ctx, tip, d, h):
    """A chevron head at ``tip`` pointing along d (a unit axis or diagonal
    direction, in glyph terms), barbs reaching h back and out along the
    arrow (on a diagonal arrow, h sqrt2 along each axis)."""
    dx, dy = d
    if dx == 0 or dy == 0:
        a = (tip[0] - dx * h - dy * h, tip[1] - dy * h + dx * h)
        b = (tip[0] - dx * h + dy * h, tip[1] - dy * h - dx * h)
        cap = 'gv' if dy == 0 else 'gh'
        return Part([a, tip, b], cap, cap)
    L = h * SQRT2
    sx, sy = (1 if dx > 0 else -1), (1 if dy > 0 else -1)
    return Part([(tip[0] - sx * L, tip[1]), tip, (tip[0], tip[1] - sy * L)])


def kb_of(ctx, d):
    """A head's barbs' half-extent across them (see Ctx.kb), for a head
    pointing along d in glyph terms."""
    if d[0] == 0 or d[1] == 0:
        return max(ctx.th((1, 1)), ctx.th((-1, 1))) / SQRT2
    return max(ctx.th((1, 0)), ctx.th((0, 1))) / SQRT2


def mirror_x(parts):
    return [Part([(-q[0], q[1]) if q[0] != 'bowl' else ('bowl', -q[1], q[2], q[3]) for q in prt.pts],
                 prt.start, prt.end, prt.closed, prt.w) for prt in parts]


def flip_y(parts):
    return [Part([(q[0], -q[1]) if q[0] != 'bowl' else ('bowl', q[1], -q[2], q[3]) for q in prt.pts],
                 prt.start, prt.end, prt.closed, prt.w) for prt in parts]


def turn_parts(parts, theta):
    """Parts drawn pointing right, turned by a multiple of 90 degrees (caps
    in glyph terms swap with the turn)."""
    t = Turn(theta)
    swap = {'gh': 'gv', 'gv': 'gh'} if t.vertical else {}
    out = []
    for prt in parts:
        pts = [t.vec(*q) if q[0] != 'bowl' else ('bowl', *t.vec(q[1], q[2]), q[3]) for q in prt.pts]
        out.append(Part(pts, swap.get(prt.start, prt.start), swap.get(prt.end, prt.end), prt.closed, prt.w))
    return out


class Framed(Drawing):
    """A drawing made in glyph terms (theta 0), laid out by its own rule;
    in the monospaced cell its head shortens (down to the white rule) until
    it fits."""
    theta = 0.0

    def build(self, ctx, mono):
        h_des, h_min = self.reach_bounds(ctx)
        h = h_des
        strokes = to_glyph(ctx, self.draw(ctx, h))
        fits = True
        if mono:
            def ok(hh):
                a, _, b, _ = bounds(ctx, to_glyph(ctx, self.draw(ctx, hh)))
                return b - a <= ctx.p.fig_w + 1e-6
            if not ok(h):
                h = _shrink(ok, h_min, h_des)
                strokes = to_glyph(ctx, self.draw(ctx, h))
                fits = ok(h)
        return strokes, fits


@dataclass(frozen=True)
class Hook(Framed):
    """An arrow whose tail turns back in a half octagon (hook), or runs round
    a loop and crosses the shaft (loop). Drawn pointing right with the hook
    above; ``mirror`` points it left."""
    loop: bool = False
    mirror: bool = False

    @property
    def stacked(self):
        return True

    def draw(self, ctx, h):
        p = ctx.p
        kb = kb_of(ctx, (1, 0))
        H = max(h, ctx.ts + 1.25 * bar_gap(ctx) + 0.5 * p.sv)      # the hook's height, centrelines
        leg = min(p.leg, H / 3)
        xl = p.sv / 2
        eps = 0.01 * ctx.ts
        if self.loop:
            xr = xl + H                                         # a square loop
            reach_end = xr + p.sv / 2
        else:
            r = xl + leg + max(1.5 * p.sv, 2 * p.m)
            reach_end = r
        Wn = letter_width(13 if self.loop else 11, 1)(p)
        if p.mono:
            Wn = min(Wn, p.fig_w)
        x_tip = max(Wn - kb, reach_end + ctx.free(SHAFT_BETWEEN) + h)
        parts = [chev(ctx, (x_tip, 0.0), (1, 0), h)]
        if self.loop:
            # up through the shaft, round the loop and back along the shaft
            # (two strokes: a stroke may not cross itself)
            e = ctx.ts / 2 + max(0.75 * p.sv, p.m)
            parts.append(Part([(xr, -e), B(xr, H, leg), B(xl, H, leg), B(xl, 0.0, leg), (xr - p.sv, 0.0)],
                              'flat', 'flat'))
            parts.append(Part([(xr - p.sv - eps, 0.0), (x_tip - eps, 0.0)]))
        else:
            parts.append(Part([(r, H), B(xl, H, leg), B(xl, 0.0, leg), (x_tip - eps, 0.0)], 'gv', 'flat'))
        return mirror_x(parts) if self.mirror else parts


@dataclass(frozen=True)
class LArrow(Framed):
    """An arrow that turns a right angle (↰ ↱ ↲ ↳ ↴ ↵), and the return
    symbol, whose corner is a bowl's. Drawn pointing right, its other leg
    rising (``up``) or falling from the corner, then turned by ``turn``
    (a multiple of 90).

    ``long_leg``: the other leg is long (it fills the cap height, or an
    arrow's length if it lies horizontal) and the shaft short; otherwise
    the shaft is an arrow's length and the leg rises a head and a stem and
    a half."""
    turn: float = 0.0
    up: bool = True
    long_leg: bool = True
    bowl: bool = False

    def draw(self, ctx, h):
        p = ctx.p
        t = Turn(self.turn)
        kb = kb_of(ctx, (1, 0))
        th_shaft = ctx.th(t.vec(1, 0))
        th_leg = ctx.th(t.vec(0, 1))
        leg_vertical = t.horizontal
        cell = p.fig_w if p.mono else 1e9
        if self.long_leg:
            Ls = h + kb + ctx.free(SHAFT_BETWEEN) + th_leg / 2   # corner to tip
            full = p.cap if leg_vertical else min(letter_width(11, 1)(p), cell)
            V = max(full - th_shaft / 2 - (h + kb), h + kb + p.sv)
        else:
            Ls = min(letter_width(11, 1)(p), cell) - kb - th_leg / 2
            V = h + kb + 1.5 * p.sv
        s = 1 if self.up else -1
        eps = 0.01 * ctx.ts
        corner = B(-Ls, 0.0, p.leg + p.m) if self.bowl else (-Ls, 0.0)
        parts = [chev(ctx, (0.0, 0.0), (1, 0), h),
                 Part([(-Ls, s * V), corner, (-eps, 0.0)], 'gh', 'flat')]
        return turn_parts(parts, self.turn)


@dataclass(frozen=True)
class Circle(Framed):
    """An open octagon with a head at its top (↻; ``mirror``: ↺), or an
    arch with a head at its foot (↷; ``mirror``: ↶)."""
    semi: bool = False
    mirror: bool = False

    @property
    def stacked(self):
        return True

    def draw(self, ctx, h):
        p = ctx.p
        kb = kb_of(ctx, (1, 0))
        white = 0.75 * p.sv
        leg = p.leg + 0.5 * p.m
        if not self.semi:
            # from the ring's foot to the head's upper barb: the cap height,
            # unless the ring needs more room for the barb hanging inside it
            R = max((p.cap - ctx.sh / 2 - (h + kb)) / 2, (ctx.sh + h + kb + white) / 2, leg + p.sv)
            if p.mono:
                R = min(R, (p.fig_w - p.sv) / 2)
            x_tip = R - p.sv / 2 - white - kb
            y_s = R - leg - 0.5 * p.sv
            parts = [chev(ctx, (x_tip, R), (1, 0), h),
                     Part([(R, y_s), B(R, -R, leg), B(-R, -R, leg), B(-R, R, leg), (x_tip - 0.01 * ctx.ts, R)],
                          'flat', 'flat')]
        else:
            # an arch: up from its left foot, over, down the right into a head
            kb2 = kb_of(ctx, (0, -1))
            Wa = max(0.55 * letter_width(11, 1)(p), h + kb2 + white + p.sv)    # between the legs, centrelines
            Ha = max(0.5 * p.cap, h + leg + 1.5 * p.sv)                       # top to tip, centrelines
            parts = [chev(ctx, (Wa, 0.0), (0, -1), h),
                     Part([(0.0, h), B(0.0, Ha, leg), B(Wa, Ha, leg), (Wa, 0.01 * ctx.ts)], 'flat', 'flat')]
        return mirror_x(parts) if self.mirror else parts


@dataclass(frozen=True)
class Zigzag(Framed):
    """↯: a bolt down to the left, stepping right once, ending in a head."""

    @property
    def stacked(self):
        return True

    def draw(self, ctx, h):
        p = ctx.p
        k = ctx.th((1, 1)) / SQRT2
        j = max(3 * p.m, SQRT2 * (ctx.th((1, 1)) + 0.6 * p.sv))     # the step: white between the runs
        L = h * SQRT2
        a = max((p.cap - k) / 2, L + p.sv)                       # each diagonal run, across and down
        x0, y0 = 2 * a - j, 2 * a
        pts = [(x0, y0), (x0 - a, y0 - a), (x0 - a + j, y0 - a), (x0 - 2 * a + j, 0.0)]
        return [Part(pts, 'gh', 'flat'), chev(ctx, pts[-1], (-1, -1), h)]


@dataclass(frozen=True)
class White(Drawing):
    """A white arrow (⇦ ⇧ ⇨ ⇩): the whole arrow an outline, one counter in
    its head and shaft. ``bar``: standing on a bar (⇪)."""
    theta: float = 0.0
    bar: bool = False

    @property
    def stacked(self):
        return True

    def reach_bounds(self, ctx):
        p = ctx.p
        t = max(ctx.t(1, 1), ctx.t(0, 1))
        need = (0.4 * p.sv + t / 2) / (SQRT2 - 1)
        return max(1.3 * reach(ctx), need), need

    def half(self, ctx, hh):
        """The shaft's half width (centreline): half the head's, never so
        narrow that its counter closes."""
        return max(0.45 * hh, ctx.ts / 2 + 0.6 * ctx.p.sv)

    def depth(self, ctx, h):
        return h + (bar_gap(ctx) + ctx.t(0, 1) if self.bar else 0.0)

    def free(self):
        return 2.0

    def parts(self, ctx, Ls, hh):
        w = self.half(ctx, hh)
        parts = [Part([(0.0, 0.0), (-hh, hh), (-hh, w), (-Ls, w), (-Ls, -w), (-hh, -w), (-hh, -hh)], closed=True)]
        if self.bar:
            # a bar under the tail, a bar's white below it, most of the head's width
            t = ctx.t(0, 1)
            ub = -Ls - ctx.t(1, 0) / 2 - bar_gap(ctx, t) - t / 2
            half = max(w + ctx.ts / 2, 0.8 * hh)
            parts.append(Part([(ub, -half), (ub, half)], 'along', 'along'))
        return parts


# --- Registration -------------------------------------------------------------------

def arrow_glyph(name, char, spec: Drawing, kind_sides=0.8):
    def width(p, spec=spec):
        return layout(spec, p, p.sh)[0]

    def fn(g, spec=spec):
        W, strokes, kk = layout(spec, g.p, g.sh)
        if kk != 1.0:
            g.p = _lightened(g.p, kk)
        _, strokes = centre(Ctx(g.p, g.sh, Turn(spec.theta)), strokes, g.W)
        emit(g, strokes)
        g.clip = None
    glyph(name, char, width, kind=('punct', kind_sides))(fn)
    return fn


DIR = {'right': 0, 'up': 90, 'left': 180, 'down': 270,
       'upright': 45, 'upleft': 135, 'downleft': 225, 'downright': 315}

# The eight plain arrows and the two two-headed ones, redrawn by the shared
# builder (they were drawn by symbols._arrow before; the names, code points
# and order are kept).
for nm, ch, d in (('arrowleft', '←', 'left'), ('arrowup', '↑', 'up'), ('arrowright', '→', 'right'),
                  ('arrowdown', '↓', 'down'), ('arrowupleft', '↖', 'upleft'), ('arrowupright', '↗', 'upright'),
                  ('arrowdownright', '↘', 'downright'), ('arrowdownleft', '↙', 'downleft')):
    arrow_glyph(nm, ch, Spec(DIR[d]))
arrow_glyph('arrowboth', '↔', Spec(0, tail='head'))
arrow_glyph('arrowupdn', '↕', Spec(90, tail='head'))


def _u(cp):
    return f'uni{cp:04X}'


# Straight arrows: (code point, name or None for uniXXXX, drawing).
R, U, L, D = DIR['right'], DIR['up'], DIR['left'], DIR['down']
STRAIGHT = [
    (0x219A, None, Spec(L, strike=True)), (0x219B, None, Spec(R, strike=True)),
    (0x219C, None, Spec(L, shaft='wave')), (0x219D, None, Spec(R, shaft='wave')),
    (0x219E, None, Spec(L, head='dbl')), (0x219F, None, Spec(U, head='dbl')),
    (0x21A0, None, Spec(R, head='dbl')), (0x21A1, None, Spec(D, head='dbl')),
    (0x21A2, None, Spec(L, tail='feather')), (0x21A3, None, Spec(R, tail='feather')),
    (0x21A4, None, Spec(L, tail='bar')), (0x21A5, None, Spec(U, tail='bar')),
    (0x21A6, None, Spec(R, tail='bar')), (0x21A7, None, Spec(D, tail='bar')),
    (0x21AD, None, Spec(R, shaft='wave', tail='head')), (0x21AE, None, Spec(R, tail='head', strike=True)),
    # harpoons: the barb on +v (left of travel) or -v
    (0x21BC, None, Spec(L, head='half-')), (0x21BD, None, Spec(L, head='half+')),
    (0x21BE, None, Spec(U, head='half-')), (0x21BF, None, Spec(U, head='half+')),
    (0x21C0, None, Spec(R, head='half+')), (0x21C1, None, Spec(R, head='half-')),
    (0x21C2, None, Spec(D, head='half+')), (0x21C3, None, Spec(D, head='half-')),
    (0x21CD, None, Spec(L, 'double', strike=True)), (0x21CE, None, Spec(R, 'double', tail='head', strike=True)),
    (0x21CF, None, Spec(R, 'double', strike=True)),
    (0x21D0, 'arrowdblleft', Spec(L, 'double')), (0x21D1, 'arrowdblup', Spec(U, 'double')),
    (0x21D2, 'arrowdblright', Spec(R, 'double')), (0x21D3, 'arrowdbldown', Spec(D, 'double')),
    (0x21D4, 'arrowdblboth', Spec(R, 'double', tail='head')), (0x21D5, None, Spec(U, 'double', tail='head')),
    (0x21D6, None, Spec(DIR['upleft'], 'double')), (0x21D7, None, Spec(DIR['upright'], 'double')),
    (0x21D8, None, Spec(DIR['downright'], 'double')), (0x21D9, None, Spec(DIR['downleft'], 'double')),
    (0x21DA, None, Spec(L, 'triple')), (0x21DB, None, Spec(R, 'triple')),
    (0x21DC, None, Spec(L, shaft='squiggle')), (0x21DD, None, Spec(R, shaft='squiggle')),
    (0x21DE, None, Spec(U, marks='dblbar')), (0x21DF, None, Spec(D, marks='dblbar')),
    (0x21E0, None, Spec(L, 'dashed')), (0x21E1, None, Spec(U, 'dashed')),
    (0x21E2, None, Spec(R, 'dashed')), (0x21E3, None, Spec(D, 'dashed')),
    (0x21E4, None, Spec(L, head='bar')), (0x21E5, None, Spec(R, head='bar')),
    (0x21FD, None, Spec(L, head='open')), (0x21FE, None, Spec(R, head='open')),
    (0x21FF, None, Spec(R, head='open', tail='head')),
    # long arrows
    (0x27F5, None, Spec(L, long=True)), (0x27F6, None, Spec(R, long=True)),
    (0x27F7, None, Spec(R, tail='head', long=True)),
    (0x27F8, None, Spec(L, 'double', long=True)), (0x27F9, None, Spec(R, 'double', long=True)),
    (0x27FA, None, Spec(R, 'double', tail='head', long=True)),
    (0x27FB, None, Spec(L, tail='bar', long=True)), (0x27FC, None, Spec(R, tail='bar', long=True)),
]
for cp, nm, dr in STRAIGHT:
    arrow_glyph(nm or _u(cp), chr(cp), dr)

# ↨: the up-down arrow on a base
arrow_glyph('arrowupdnbse', '↨', Spec(U, tail='head', marks='base'))
# hooks and loops
arrow_glyph(_u(0x21A9), '↩', Hook(mirror=True))
arrow_glyph(_u(0x21AA), '↪', Hook())
arrow_glyph(_u(0x21AB), '↫', Hook(loop=True, mirror=True))
arrow_glyph(_u(0x21AC), '↬', Hook(loop=True))
arrow_glyph(_u(0x21AF), '↯', Zigzag())
# arrows turning a corner
arrow_glyph(_u(0x21B0), '↰', LArrow(180, up=True))          # up, then left
arrow_glyph(_u(0x21B1), '↱', LArrow(0, up=False))            # up, then right
arrow_glyph(_u(0x21B2), '↲', LArrow(180, up=False))           # down, then left
arrow_glyph(_u(0x21B3), '↳', LArrow(0, up=True))             # down, then right
arrow_glyph(_u(0x21B4), '↴', LArrow(270, up=False))           # right, then down
arrow_glyph('carriagereturn', '↵', LArrow(180, up=False, long_leg=False))
arrow_glyph(_u(0x23CE), '⏎', LArrow(180, up=False, long_leg=False, bowl=True))
# round the clock
arrow_glyph(_u(0x21B6), '↶', Circle(semi=True, mirror=True))
arrow_glyph(_u(0x21B7), '↷', Circle(semi=True))
arrow_glyph(_u(0x21BA), '↺', Circle(mirror=True))
arrow_glyph(_u(0x21BB), '↻', Circle())
# pairs
arrow_glyph(_u(0x21C4), '⇄', Pair(R, 'opp', 1))
arrow_glyph(_u(0x21C5), '⇅', Pair(U, 'opp', 1))
arrow_glyph(_u(0x21C6), '⇆', Pair(R, 'opp', -1))
arrow_glyph(_u(0x21C7), '⇇', Pair(L, 'same'))
arrow_glyph(_u(0x21C8), '⇈', Pair(U, 'same'))
arrow_glyph(_u(0x21C9), '⇉', Pair(R, 'same'))
arrow_glyph(_u(0x21CA), '⇊', Pair(D, 'same'))
arrow_glyph(_u(0x21CB), '⇋', Pair(R, 'harpoon', -1))
arrow_glyph(_u(0x21CC), '⇌', Pair(R, 'harpoon', 1))
arrow_glyph(_u(0x21F5), '⇵', Pair(U, 'opp', -1))
arrow_glyph(_u(0x21F6), '⇶', Pair(R, 'same', n=3))
# white arrows
arrow_glyph(_u(0x21E6), '⇦', White(L))
arrow_glyph(_u(0x21E7), '⇧', White(U))
arrow_glyph(_u(0x21E8), '⇨', White(R))
arrow_glyph(_u(0x21E9), '⇩', White(D))
arrow_glyph(_u(0x21EA), '⇪', White(U, bar=True))
