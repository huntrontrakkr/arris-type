"""The glyph-drawing vocabulary and registry.

A glyph is a function of the parameters that adds strokes to a ``Glyph``.
Coordinates are font units, y up, with the glyph body starting at x = 0;
spacing is added when the font is assembled.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from .geom import Node, Stroke, Thickness, ink
from .params import Params

REGISTRY: dict[str, 'Spec'] = {}

# OpenType code that glyph modules contribute: language systems ('cyrl BGR')
# and feature blocks (a locl). ``glyphs.features.fea`` gathers them.
LANGSYS: list[str] = []
FEATURE_CODE: list[str] = []


@dataclass
class Opening:
    """A gap that must not close as strokes get heavier.

    ``measure`` returns the white across the gap (font units) for a built
    glyph. The glyph reads one free variable, ``free``; if the gap is narrower
    than its share of the stem in the watch's own drawing, the variable moves
    from its default toward ``limit(p)`` until the gap has that share again.
    """
    measure: Callable[['Glyph'], float]
    free: str
    limit: Callable[[Params], float]
    max_ratio: float | None = None   # cap on the watch's share, if it is generous


@dataclass(frozen=True)
class Squint:
    """White that must read when a reader squints: the holes and slots of
    the drawing (``vision.narrow_whites``) within the zones it marks
    (``Glyph.zones``; anywhere if it marks none) keep, under the blur, as
    much as they do at Regular, or ``vision.READS``, whichever is less. If
    they would not, the glyph's free variable ``free`` moves from its
    default toward ``limit(p)`` until they do, or as far as the limit."""
    free: str
    limit: Callable[[Params], float]
    absolute: bool = False      # held to vision.READS itself, not to the Regular (where the Regular reads poorly too)
    whites: bool = False        # a white the Regular has that is gone altogether reads 0 (open bowls: _read)
    form: bool = False          # free chooses between two drawings (¢ $ stem or stubs): a variable font
                                # carries each as a glyph of its own, swapped where the engine swaps them (build_vf)


# Math signs set on one advance (the plus sign's, at least), their ink centred
# in it, so a column of figures and operators lines up: the operators
# (glyphs.operators.op) and the ASCII and Latin-1 signs.
TAB_MATH: set = {'plus', 'minus', 'equal', 'less', 'greater', 'plusminus', 'multiply', 'divide', 'logicalnot'}


@dataclass
class Spec:
    name: str
    unicode: int | None
    fn: Callable
    width: Callable[[Params], float]   # body width
    kind: str = 'fig'                  # spacing class
    openings: tuple = ()
    solid: bool = False                # has a solid part by design (the pilcrow's bowl)
    cell: bool = False                 # a terminal cell's drawing: stays upright in the italic (font.place)
    squint: tuple = ()                 # Squint rules


def glyph(name: str, char: str | None, width, kind='fig', openings=(), solid=False, cell=False, squint=()):
    def deco(fn):
        w = width if callable(width) else (lambda p, w=width: getattr(p, w))
        f = fn
        if isinstance(kind, tuple) and kind[0] == 'punct' and not cell and not getattr(fn, 'mono_fitted', False):
            # a symbol keeps to its cell in the monospaced cut (symkit.mono_fitted)
            from .glyphs.symkit import mono_fitted
            f, w = mono_fitted(name, fn, w, kind)
        REGISTRY[name] = Spec(name, ord(char) if char else None, f, w, kind, tuple(openings), solid, cell,
                              tuple(squint))
        return fn
    return deco


def B(x, y, leg=None, w=None):
    """A bowl corner (leg None = the parameter default; w the thickness of
    the segment that follows, None = by its direction)."""
    return ('bowl', x, y, leg, w)


@dataclass
class Glyph:
    p: Params
    name: str = ''
    strokes: list[Stroke] = field(default_factory=list)
    extra: list = field(default_factory=list)   # pre-made polygons
    ot: float = 0.0   # overshoot above the top line (solved per glyph)
    ob: float = 0.0   # overshoot below the baseline
    W: float = 0.0    # body width
    sh_k: float = 1.0  # horizontal thickness factor (tight stacks of bars)
    sh_auto: float = 1.0  # further thinning that keeps closed counters open (see draw)
    clip: tuple[float, float, float, float] | None = None   # keep ink inside (x0, y0, x1, y1)
    butt: tuple = ()   # lines ('x' or 'y', value) the ink meets flush: no edge breaks there (geom.ink)
    overrides: dict = field(default_factory=dict)
    defaults: dict = field(default_factory=dict)
    parts: dict = field(default_factory=dict)        # name -> stroke indices
    defaults_used: dict = field(default_factory=dict)
    extra_chamfers: list = field(default_factory=list)   # chamfer record of stamped glyphs (see add_glyph)
    zones: list = field(default_factory=list)   # (x0, y0, x1, y1) boxes whose white the Squint rule watches
    cell: tuple[float, float] | None = None     # Mono: the cell (x0, x1) no ink may pass (see _build)
    extra_src: list = field(default_factory=list)   # (ink in extra, stamped glyph, its rings, affine map): names its edges

    def free(self, name: str, default: float) -> float:
        """A free variable of the drawing (see Opening)."""
        self.defaults[name] = default
        return self.overrides.get(name, default)

    def part(self, name: str):
        """The ink of the named strokes, before the union and corner rule."""
        import shapely
        from .geom import stroke_polygon
        th = _thickness(self.p, self.sh)
        return shapely.union_all([stroke_polygon(self.strokes[i], th, self.p.c) for i in self.parts[name]])

    def counter_size(self) -> float:
        """Radius of the largest circle inside any counter: how open the
        tightest-held white of a closed form stays."""
        import shapely
        from shapely.geometry import Polygon
        from .geom import rings_to_shapely
        poly = rings_to_shapely(self.rings())
        best = 0.0
        for part in getattr(poly, 'geoms', [poly]):
            for hole in part.interiors:
                mic = shapely.maximum_inscribed_circle(Polygon(hole), tolerance=1.0)
                best = max(best, mic.length)
        return best

    def white_left(self, y: float, x: float) -> float:
        """Width of the white run leftward from x at height y."""
        from shapely.geometry import LineString
        from .geom import rings_to_shapely
        poly = rings_to_shapely(self.rings())
        cut = poly.intersection(LineString([(x - 1e4, y), (x - 1e-3, y)]))
        xs = [c[0] for gg in getattr(cut, 'geoms', [cut]) for c in getattr(gg, 'coords', [])]
        return (x - max(xs)) if xs else 1e4

    def white_vertical(self, x: float, y: float, up: bool = False) -> float:
        """Height of the white run down (or up) from (x, y)."""
        from shapely.geometry import LineString
        from .geom import rings_to_shapely
        poly = rings_to_shapely(self.rings())
        d = 1.0 if up else -1.0
        cut = poly.intersection(LineString([(x, y + d * 1e-3), (x, y + d * 1e4)]))
        ys = [c[1] for gg in getattr(cut, 'geoms', [cut]) for c in getattr(gg, 'coords', [])]
        if not ys:
            return 1e4
        return (min(ys) - y) if up else (y - max(ys))

    def counters(self) -> list[float]:
        """Diameters of the largest circles inside each closed counter."""
        import shapely
        from shapely.geometry import Polygon
        from .geom import rings_to_shapely
        poly = rings_to_shapely(self.rings())
        return [2 * shapely.maximum_inscribed_circle(Polygon(h), tolerance=1.0).length
                for part in getattr(poly, 'geoms', [poly]) for h in part.interiors]

    def tightest_counter(self) -> float:
        """Diameter of the largest circle inside the tightest closed counter."""
        sizes = self.counters()
        return min(sizes) if sizes else 1e4

    def stroke(self, *pts, closed=False, start='flat', end='flat', part=None):
        if part:
            self.parts.setdefault(part, []).append(len(self.strokes))
        nodes = []
        for q in pts:
            if isinstance(q, tuple) and q and q[0] == 'bowl':
                _, x, y, leg, w = q
                nodes.append(Node(x, y, self.p.leg if leg is None else leg, w))
            else:
                # (x, y) or (x, y, w): w is the thickness of the segment that follows
                nodes.append(Node(q[0], q[1], 0.0, q[2] if len(q) > 2 else None))
        self.strokes.append(Stroke(tuple(nodes), closed, start, end))
        return self

    def rings(self):
        return self.outline(record=False)[0]

    def outline(self, record: bool = True, tags: list | None = None):
        """(rings, chamfer record): see ``geom.ink``. Stamped glyphs bring
        their own records (``add_glyph``). ``tags``, if given, collects the
        name of every edge (``geom.ink``); the warp below keeps every point's
        place in its ring, so the names stay true."""
        p = self.p
        box = None
        if self.clip is not None:
            from shapely.geometry import box as _box
            box = _box(*self.clip)
        rec = [] if record else None
        rings = ink(self.strokes, _thickness(p, self.sh), p.c, self.extra, box, rec, self.butt,
                    tags=tags, extra_edges=self._extra_edges() if tags is not None else ())
        rec = (rec or []) + self.extra_chamfers if record else []
        warp = getattr(self, 'warp', None)
        if warp is not None:
            if p.slant:
                # the italic curves its chamfers on the exact drawing first
                # (italic.outline), then moves the curved outline: the warp
                # travels in the record. Its rings stay exact whether or not a
                # record is asked for, so spacing is measured on one geometry
                # (a grade master spaces from its ungraded self)
                if record:
                    rec = rec + [('warp', warp)]
            else:
                # the optical corrections move the finished outline: every
                # corner the corner rule cut, it cut on the drawing's exact
                # directions
                rings = [[(q[0], warp(q[1])) + tuple(q[2:]) for q in r] for r in rings]
                rec = [_warped(r, warp) for r in rec]
        return rings, rec

    def add_glyph(self, sub: 'Glyph', dx: float = 0.0, dy: float = 0.0):
        """Stamp another drawn glyph into this one, chamfer record and all.
        In Mono, the stamped glyph's strokes are cut at this glyph's cell
        (where it stands in it) before its corner rule, as its own would be:
        cut after, as finished ink, a chamfered end can twist (Ǿ's slash)."""
        import copy
        from shapely import affinity
        from .geom import rings_to_shapely
        if self.cell is not None and _cell_kind(REGISTRY.get(sub.name)):
            sub = copy.copy(sub)
            big = 10 * self.p.cap
            x0, y0, x1, y1 = sub.clip if sub.clip is not None else (-big, -big, big, big)
            sub.clip = (max(x0, self.cell[0] - dx), y0, min(x1, self.cell[1] - dx), y1)
        rings, rec = sub.outline()
        self.extra.append(affinity.translate(rings_to_shapely(rings), dx, dy))
        self.extra_src.append((self.extra[-1], sub, rings, (1.0, 0.0, 0.0, 1.0, dx, dy)))
        self.extra_chamfers += [_moved(r, dx, dy) for r in rec]

    def _extra_edges(self):
        """The edges of the extra ink, named: a stamped glyph's by its own
        names, ('sub', j, name) for the j-th piece of extra ink; other extra
        ink by its place in its polygon."""
        out = []
        for j, e in enumerate(self.extra):
            src = next((s for s in self.extra_src if s[0] is e), None)
            if src is not None:
                _, sub, rings, (a, b, c, d, ox, oy) = src
                names: list = []
                sub.outline(record=False, tags=names)
                T = lambda q: (a * q[0] + b * q[1] + ox, c * q[0] + d * q[1] + oy)
                for r, nm in zip(rings, names):
                    n = len(r)
                    out.extend((T(r[i]), T(r[(i + 1) % n]), ('sub', j, nm[i])) for i in range(n))
                continue
            polys = [g for g in getattr(e, 'geoms', [e]) if g.geom_type == 'Polygon']
            for pi, poly in enumerate(polys):
                for k, ring in enumerate([poly.exterior] + list(poly.interiors)):
                    cs = list(ring.coords)
                    out.extend((cs[i], cs[i + 1], ('x', j, pi, k, i)) for i in range(len(cs) - 1))
        return out

    @property
    def sh(self) -> float:
        return max(self.p.sh * self.sh_k * self.sh_auto, self.p.floor)

    def stack(self, n: int, height: float, ratio: float = 0.9):
        """Thin the horizontals where n bars share ``height`` so that each
        counter between them stays at least ``ratio`` times a bar."""
        fit = height / (n + (n - 1) * ratio)
        self.sh_k = min(1.0, fit / self.p.sh)
        return self.sh


def _thickness(p: Params, sh: float) -> Thickness:
    return Thickness(p.sv, sh, p.sd, p.ss, p.slant, floor=p.floor)


def _warped(r, f):
    """A chamfer record entry with every point's y passed through f (a
    direction is carried by moving a point a unit along it)."""
    if r[0] == 'warp':
        return r
    if r[0] == 'bowl':
        return ('bowl',) + tuple(((q[0], f(q[1])), (d[0], f(q[1] + d[1]) - f(q[1]))) for q, d in r[1:])
    if r[0] == 'line':
        (x, y), (dx, dy) = r[1], r[2]
        y0, y1 = f(y), f(y + dy)
        return ('line', (x, y0), (dx, y1 - y0))
    return ('chord', (r[1][0], f(r[1][1])), (r[2][0], f(r[2][1])))


def _moved(r, dx, dy):
    if r[0] == 'warp':
        f = r[1]
        return ('warp', Shifted(f, dy)) if dy else r
    if r[0] == 'bowl':
        return ('bowl',) + tuple(((q[0] + dx, q[1] + dy), d) for q, d in r[1:])
    return ('chord', (r[1][0] + dx, r[1][1] + dy), (r[2][0] + dx, r[2][1] + dy))


LETTER_KINDS = ('cap', 'lower')


def body_width(spec, p, width=None):
    """A glyph's body: its own width, or in the monospaced cut, every
    letter fills the figures' body."""
    if width is not None:
        return width
    if p.mono and spec.kind in LETTER_KINDS:
        return p.fig_w
    return spec.width(p)


_DEPTH = [0]   # how deep in other glyphs' drawings a drawing is made (a stamped or inset letter is 1 or more)


def _cell_kind(spec) -> bool:
    """Whether a glyph keeps to Mono's cell: not marks, spaces, ligatures."""
    return spec is not None and spec.kind not in ('mark', 'space') and \
        not (isinstance(spec.kind, tuple) and spec.kind[0] == 'liga')


def _build(spec, p, ot, ob, overrides, width=None):
    g = Glyph(p, spec.name, ot=ot, ob=ob, W=body_width(spec, p, width), overrides=dict(overrides))
    g.sh_auto = overrides.get('sh_auto', 1.0)
    g.defaults['sh_auto'] = 1.0
    if p.mono and _DEPTH[0] == 0 and _cell_kind(spec):
        # Mono: no ink past the cell (the body sits centred in it); a stroke
        # that would run on is cut at its edge, and the corner rule chamfers
        # the cut like any other end. The glyph's own cell: a letter drawn
        # inside another (an inset N in ₦) is cut at the outer glyph's cell,
        # where it stands in it, when it is stamped (add_glyph), not at a
        # cell of its own parameters
        g.cell = ((g.W - p.fig_adv) / 2, (g.W + p.fig_adv) / 2)
    _DEPTH[0] += 1
    try:
        spec.fn(g)
    finally:
        _DEPTH[0] -= 1
    if g.cell is not None:
        cx0, cx1 = g.cell
        x0, y0, x1, y1 = g.clip if isinstance(g.clip, tuple) else (cx0, -10 * p.cap, cx1, 10 * p.cap)
        g.clip = (max(x0, cx0), y0, min(x1, cx1), y1)
    return g


# Optical corrections, as type is corrected by eye: the optical centre (a
# letter's middle reads a little above its geometric middle, so middle bars
# rise and top halves shrink: B, E, H, S, 3, 8, the e's bar) and overshoot
# (round letters reach a little past the baseline and the cap or x-height, or
# they look smaller than flat ones). Both move stroke centrelines only, so
# every stroke keeps its thickness. Measured optics only: the share is
# Params.optical (0 in the watch's own drawing, WTCH 100). Drawn on the base
# letters and figures; composites inherit them. None turns them off.
_FIGS = ('zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine')
OPTICAL = {
    'names': set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz') | set(_FIGS),
    # optical centre: the middle rises until the top counter of a three-bar
    # letter (B E 8) is this share of the bottom one; calibrated so that at
    # Regular the middle rises 2.5% of the cap height. As the bars thicken the
    # counters shrink and the rise with them, so heavy top bowls never pinch.
    'counters': 0.8615,
    # overshoot: each glyph's own, measured (vision.overshoot_need: its hull
    # under a blur calibrated on a circle to a 1.5% overshoot), at most this
    # share of the zone height
    'over_max': 0.015,
}


def _bowl_side(rings, y_line, inward, p):
    """Whether every flat edge on the outline's extreme line ``y_line`` ends
    at both ends in a bowl's corner: an edge leaving it at 45 degrees
    toward the inside (``inward``: -1 down from a top, +1 up from a bottom)
    for more than an edge break's reach."""
    import math
    reach = max(1.6 * p.c, 0.35 * p.leg)
    flats = 0
    for r in rings:
        n = len(r)
        for i in range(n):
            a, b = r[i], r[(i + 1) % n]
            if abs(a[1] - y_line) > 1.0 or abs(b[1] - y_line) > 1.0 or abs(a[0] - b[0]) < 1.0:
                continue
            flats += 1
            for end, nb in ((a, r[i - 1]), (b, r[(i + 2) % n])):
                dx, dy = nb[0] - end[0], nb[1] - end[1]
                if dy * inward <= 0 or abs(abs(dx) - abs(dy)) > 0.1 * max(abs(dx), abs(dy)) or abs(dy) < reach:
                    return False
    return flats > 0


def _optical(g, spec, p):
    from .geom import Node, Stroke
    from .vision import overshoot_need
    H = p.xh if spec.kind == 'lower' else p.cap
    r = OPTICAL['counters']
    A = max(H / 2 - 1.5 * g.sh, 0.0)                         # a counter's height with the middle centred
    dc = A * (1 - r) / (1 + r) * p.optical
    rings0 = g.rings()
    top, bot = overshoot_need(rings0, H)
    cap_ = OPTICAL['over_max'] * H
    # a side the drawing already carries past its line (v's point) keeps the
    # overshoot it was drawn with
    ys0 = [q[1] for r in rings0 for q in r]
    if ys0 and max(ys0) > H + 1.0:
        top = 0.0
    if ys0 and min(ys0) < -1.0:
        bot = 0.0
    # only a side that ends in bowls overshoots: every flat on its extreme
    # line turns down (up) into a bowl's 45-degree corner at both ends. A
    # stem's end or a bar (F's foot, T's stem, B's top) ends in edge breaks,
    # and sits on the line as H does
    if ys0 and not _bowl_side(rings0, max(ys0), -1, p):
        top = 0.0
    if ys0 and not _bowl_side(rings0, min(ys0), +1, p):
        bot = 0.0
    ot, ob = min(top, cap_) * p.optical, min(bot, cap_) * p.optical
    # a side where the clip cuts ink (A's flat apex, v's foot: strokes run on
    # past the line and are cut on it) is a cut, and a cut stays on its line;
    # only a side the drawing itself ends on (a bowl) overshoots
    if g.clip is not None and isinstance(g.clip, tuple) and (ot or ob):
        import shapely
        from .geom import stroke_polygon
        th = _thickness(g.p, g.sh)
        raw = shapely.union_all([stroke_polygon(st, th, g.p.c) for st in g.strokes] + list(g.extra))
        _, ry0, _, ry1 = raw.bounds
        if ry1 > g.clip[3] + 1.0:
            ot = 0.0
        if ry0 < g.clip[1] - 1.0:
            ob = 0.0
    # The warp, piecewise linear in y: the bottom bar (and all below it), the
    # middle bar and the top bar (and all above it) each move as one piece,
    # so every bar keeps its thickness; the white between them stretches
    # (below the middle) or gives way (above). The middle rises by dc, a bowl
    # side moves out by its overshoot, a cut side stays on its line.
    m, t = H / 2, g.sh
    # The zone above the middle gives way as the middle rises: everything in it
    # (a bar drawn off the middle, as the a's, the s's waist, a diagonal)
    # shrinks by that zone's scale. No stroke may shrink below the floor, so
    # the rise yields: at Thin, where the strokes are the floor, it is all but
    # gone (tools/stroke_scan.py is the check).
    if p.floor:
        zone = H - t - (m + t / 2)
        k = min(1.0, p.floor / max(min(t, p.sh), 1e-6))
        dc = max(0.0, min(dc, zone * (1 - k) + ot))
    knots = [(t, t - ob), (m - t / 2, m - t / 2 + dc), (m + t / 2, m + t / 2 + dc), (H - t, H - t + ot)]
    if not (dc or ot or ob) or not (t < m - t / 2 and m + t / 2 < H - t):
        return

    g.warp = Warp(tuple(knots), ot, ob)


class Warp:
    """The optical correction's vertical warp: piecewise linear through
    knots, below the first moved by -ob, above the last by +ot. (An object,
    not a closure, so a drawing that carries it can be kept: font's cache.)"""

    def __init__(self, knots, ot, ob):
        self.knots, self.ot, self.ob = knots, ot, ob

    def __call__(self, y):
        knots = self.knots
        if y <= knots[0][0]:
            return y - self.ob
        if y >= knots[-1][0]:
            return y + self.ot
        for (x0, y0), (x1, y1) in zip(knots, knots[1:]):
            if y <= x1:
                return y0 + (y - x0) * (y1 - y0) / (x1 - x0)
        return y


class Shifted:
    """A warp f carried by dy: y -> d * f((y - dy) / d) + dy (d = -1: a
    flip about the axis)."""

    def __init__(self, f, dy, d=1.0):
        self.f, self.dy, self.d = f, dy, d

    def __call__(self, y):
        return self.d * self.f((y - self.dy) / self.d) + self.dy


# Every closed counter keeps at least half its share of the stem in the
# watch's own drawing. Where heavier strokes would close it, the glyph's
# horizontals thin, down to AUTO_MIN of the weight's own: the tight-stack
# rule of the a, e and s, applied wherever it is needed. Glyphs that declare
# their own openings on their horizontals (the figures) and composites (drawn
# from other glyphs, which keep their own counters) are left alone.
AUTO_SHARE = 0.5
AUTO_MIN = 0.7
_AUTO: dict = {}


def _auto_counters(spec):
    """(count, share of the stem of the tightest) of a glyph's closed
    counters in the watch's drawing, or None if the rule does not apply."""
    if spec.name not in _AUTO:
        from .params import HERITAGE
        res = None
        if spec.kind != 'fig' and not any(op.free == 'sh_k' for op in spec.openings):
            g = _build(spec, HERITAGE, 0.0, 0.0, {})
            if g.strokes and not g.extra:
                sizes = g.counters()
                if sizes:
                    res = (len(sizes), min(sizes) / HERITAGE.sv)
        _AUTO[spec.name] = res
    return _AUTO[spec.name]


# Symbols keep their white. A symbol's parts hold white between them (the
# notch under an arrow's barb, a pilcrow's gap between its stems, the
# asterisk's spaces between spokes); as strokes grow, that white closes and
# the parts fuse. Every white feature (white at least half a stroke wide,
# inside its hull) a symbol has it keeps at every weight: where a heavy weight would lose one of the features it has at
# Regular, all its strokes lighten, as far as needed and never below
# LIGHTEN_MIN. Better geometry comes first
# (constructions whose white grows with the stroke); this is the rule that
# catches the rest.
LIGHTEN_MIN = 0.8
WHITE_OPEN = 0.25
_WHITE: dict = {}


def white_features(rings, p) -> int:
    """How many separate pieces of readable white a drawing holds inside its
    hull: white a disk half a stroke across fits in, and a piece is one a
    disk can move about in (the white eroded by the disk's radius: where it
    can be centred). Counted as the union of the disks instead (the white
    opened), two pieces met where disks either side of a pinch overlap,
    with no way through: ∭'s triangles under the hooks joined the whites
    between the stems from Bold to Heavy, so the rule lightened those
    weights, and let go at Black, where the beak's corner turned a degree."""
    from shapely.geometry import MultiPoint
    from .geom import rings_to_shapely
    if not rings:
        return 0
    ink = rings_to_shapely(rings)
    hull = MultiPoint([q[:2] for r in rings for q in r]).convex_hull
    r = WHITE_OPEN * max(p.sv, p.sh, p.sd, p.ss)
    centres = hull.difference(ink).buffer(-r, join_style='mitre')
    return sum(1 for q in getattr(centres, 'geoms', [centres])
               if q.geom_type == 'Polygon' and not q.is_empty and q.buffer(r, join_style='mitre').area > 0.5 * (2 * r) ** 2)


def _is_symbol(spec) -> bool:
    return isinstance(spec.kind, tuple) and spec.kind[0] == 'punct'


def _white_reference(spec, p):
    """The white features of a symbol as drawn at Regular, in the same cut
    (monospaced or not): the weight it was designed at."""
    key = (spec.name, p.mono)
    if key not in _WHITE:
        from .instances import params
        ref = params(400).with_(mono=p.mono)
        g = _build(spec, ref, 0.0, 0.0, {})
        _WHITE[key] = white_features(g.rings(), ref)
    return _WHITE[key]


def _lightened(p: Params, k: float) -> Params:
    return p.with_(sv=p.sv * k, sh=p.sh * k, sd=p.sd * k, ss=p.ss * k)


LOCK_MIN = 0.75     # the most the topology lock lightens a drawing's strokes
LOCK_MARGIN = 0.02  # and how far past the least lightening that works it goes
_TOPO: dict = {}


def _topology(g) -> tuple:
    """(pieces of ink, counters) of a drawing as the font will carry it: in
    whole units, and in an italic, curved and sheared (italic.outline)."""
    from .geom import rings_to_shapely
    if g.p.slant and not (REGISTRY.get(g.name) and REGISTRY[g.name].cell):
        from .italic import outline, polylines
        rings, rec = g.outline(record=True)
        rings = polylines(outline(rings, rec, g.p))
    else:
        rings = g.rings()
    ink = rings_to_shapely([[(round(q[0]), round(q[1])) for q in r] for r in rings])
    polys = [q for q in getattr(ink, 'geoms', [ink]) if q.geom_type == 'Polygon']
    return len(polys), sum(len(q.interiors) for q in polys)


def _topology_reference(spec, p) -> tuple:
    """The drawing's topology at Regular, in the same cut (Mono or not,
    italic or not)."""
    key = (spec.name, p.mono, bool(p.slant))
    if key not in _TOPO:
        from .instances import params
        ref = params(400).with_(mono=p.mono)
        if p.slant:
            from .italic import italic
            ref = italic(ref)
        g = _build(spec, ref, 0.0, 0.0, {})
        if OPTICAL is not None and ref.optical and spec.name.removesuffix('.ital') in OPTICAL['names']:
            _optical(g, spec, ref)
        _TOPO[key] = _topology(g)
    return _TOPO[key]


def _counter_white(g, n):
    """The tightest counter, or 0 if any of the drawing's n counters closed."""
    sizes = g.counters()
    return min(sizes) if len(sizes) >= n else 0.0


_RATIOS: dict = {}


def _heritage_ratio(spec, k):
    """An opening's white as a share of the stem in the watch's drawing."""
    key = (spec.name, k)
    if key not in _RATIOS:
        from .params import HERITAGE
        g = _build(spec, HERITAGE, 0.0, 0.0, {})
        _RATIOS[key] = spec.openings[k].measure(g) / HERITAGE.sv
    return _RATIOS[key]


def _squint_pieces(g, kinds=('hole', 'slot')) -> list:
    """Depths of the holes and slots (of `kinds`) in the glyph's marked zones
    under the squint (see Squint)."""
    from shapely.geometry import box
    from .vision import narrow_whites
    zones = [box(*z) for z in g.zones]
    return [d for q, kind, d in narrow_whites(g.rings(), g.p.sv, g.p.view_cap or g.p.cap)
            if kind in kinds and (not zones or any(q.intersects(z) for z in zones))]


def _squint(g, kinds=('hole', 'slot'), count: int = 0) -> float:
    """How light the faintest hole or slot (of `kinds`) in the glyph's marked
    zones stays under the squint; 1 if it has none. With `count`, the number
    the zones had at Regular: white between a sign's bars that has closed
    altogether reads 0, not 1 (white that opened out, a stem become stubs,
    is not narrow any more and is not missed)."""
    d = _squint_pieces(g, kinds)
    if g.zones and len(d) < count:                 # watched white (a sign's bars) that closed altogether
        return 0.0
    return min(d, default=1.0)


_FORMS: dict = {}


def _cut_form(spec, sq, p):
    """An absolute Squint rule chooses a form (two bars or one) once for the
    whole cut, at its heaviest weight, where the white is least: if the
    default form does not read there (vision.READS) and the other reads
    better, every weight of the cut takes the other. A sign keeps one form
    through its family."""
    from .instances import params
    from .vision import READS
    key = (spec.name, sq.free, p.mono)
    if key not in _FORMS:
        heavy = params(900).with_(mono=p.mono)
        g0 = _build(spec, heavy, 0.0, 0.0, {})
        d0 = g0.defaults.get(sq.free)
        b = sq.limit(heavy)
        choice = d0
        if d0 is not None and b != d0:
            kinds = ('hole', 'slot')
            n0 = _squint_regular(spec, heavy, kinds, {sq.free: d0})[1]
            n1 = _squint_regular(spec, heavy, kinds, {sq.free: b})[1]
            s0 = _squint(g0, count=n0)
            s1 = _squint(_build(spec, heavy, 0.0, 0.0, {sq.free: b}), count=n1)
            if s0 < READS - SQUINT_SLACK and s1 > s0:
                choice = b
        _FORMS[key] = choice
    return _FORMS[key]


_THINS: dict = {}


def _thinning_reads(spec, sq, p) -> bool:
    """Whether a Squint rule thins a glyph at all in its cut: if at Black,
    where the white is least, the limit reads no worse than the raster can
    tell (SQUINT_SLACK), the rule's way, less ink, is taken wherever the
    white falls short, to the limit where even that does not bring it back
    (₹'s thinner bars leave its leg room); if the limit reads worse, the
    glyph is left be at every weight. Decided once for the cut, so the
    weights and grades agree (and the variable font's masters with them):
    decided weight by weight, ¥'s bars went thin, thick, thin, thick."""
    from .instances import params
    key = (spec.name, sq.free, p.mono)
    if key not in _THINS:
        heavy = params(900).with_(mono=p.mono)
        kinds = ('hole', 'slot')
        g0 = _build(spec, heavy, 0.0, 0.0, {})
        b = sq.limit(heavy)
        _, n0, w0 = _squint_regular(spec, heavy, kinds, {sq.free: g0.defaults.get(sq.free)})
        _, n1, w1 = _squint_regular(spec, heavy, kinds, {sq.free: b})
        s0 = _read(g0, n0, w0 if sq.whites else 0)
        s1 = _read(_build(spec, heavy, 0.0, 0.0, {sq.free: b}), n1, w1 if sq.whites else 0)
        _THINS[key] = s1 >= s0 - SQUINT_SLACK
    return _THINS[key]


def _squint_value(spec, sq, p, ot, ob, overrides, width):
    """What a Squint rule sets its free variable to at p, or None: toward
    its limit until the glyph's white reads as at its Regular (bisection),
    to the limit if even that does not bring it back (where the cut thins
    at all, _thinning_reads)."""
    g = _build(spec, p, ot, ob, overrides, width)
    if sq.free not in g.defaults:
        return None
    kinds = ('hole', 'slot')
    a, b = overrides.get(sq.free, g.defaults[sq.free]), sq.limit(p)
    want, n, wa = _squint_regular(spec, p, kinds, {sq.free: a})
    wa = wa if sq.whites else 0
    if _read(g, n, wa) >= want or not _thinning_reads(spec, sq, p):
        return None
    far = _build(spec, p, ot, ob, {**overrides, sq.free: b}, width)
    want_b, n_b, wb = _squint_regular(spec, p, kinds, {sq.free: b})
    wb = wb if sq.whites else 0
    if _read(far, n_b, wb) >= want_b:
        for _ in range(10):  # bisection: a fuses, b reads
            mid = (a + b) / 2
            if _read(_build(spec, p, ot, ob, {**overrides, sq.free: mid}, width), n_b, wb) >= want_b:
                b = mid
            else:
                a = mid
    return b


SQUINT_ANCHORS = 4    # lighter strokes in the same body a Squint rule also decides at
_MONO: dict = {}


def _restroked(p, s):
    """p with its stem at s, every stroke and the edge break with it (as a
    grade: the body, the grid and the spacing stay)."""
    k = s / p.sv
    return p.with_(sv=s, sh=p.sh * k, sd=p.sd * k, ss=p.ss * k, c=p.c * k)


_CANON: dict = {}


def _lighter(p):
    """The parameters of the lighter weights of p's own cut, from the
    Regular's up (every 100), if p is a font's own (a weight, grade and
    watch balance of a cut: instances.params, Mono or not, italic or not);
    else None (a set derived from one: small capitals, small figures)."""
    if p not in _CANON:
        from .instances import GRAD_SHARE, params, stem
        out = None
        grad = round((p.grade_k - 1) / GRAD_SHARE, 6)
        base_sv = p.sv / p.grade_k
        lo, hi = 1.0, 1000.0
        for _ in range(40):                                 # the weight whose stem p has
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if stem(mid) < base_sv else (lo, mid)
        w = round((lo + hi) / 2, 3)

        def at(w_, watch):
            q = params(w_, grad, watch=watch).with_(mono=p.mono)
            if p.slant:
                from .italic import italic
                q = italic(q)
            return q
        # the watch balance: the measured optics' share is 1 - watch (0 at
        # the watch's own proportions)
        for watch in sorted({round(1.0 - p.optical, 6), 1.0}):
            try:
                if at(w, watch) == p:
                    out = [at(w_, watch) for w_ in range(400, int(w), 100) if w_ < w]
                    break
            except Exception:  # noqa: BLE001
                pass
        _CANON[p] = out
    return _CANON[p]


def _squint_monotone(spec, sq, p, ot, ob, overrides, width):
    """A Squint rule's value at p, never short of what it gives the lighter
    weights of the same cut (or, for a derived set, lighter strokes in the
    same body: SQUINT_ANCHORS stems from the Regular's to p's): decided at
    each (_squint_value), the one furthest toward the limit kept. A squint
    reading steps with the weight (raster and layout), and decided at p
    alone a rule thinned one weight, left the next, thinned the one after
    (¥'s bars 78 72 112 88 119 units from Medium to Black); so a heavier
    weight now thins at least as much as a lighter one."""
    key = (spec.name, sq.free, p, ot, ob, tuple(sorted(overrides.items())), width)
    if key not in _MONO:
        reg = _regular_sv(p)
        g0 = _build(spec, p, ot, ob, overrides, width)
        a0 = overrides.get(sq.free, g0.defaults.get(sq.free))
        lim = sq.limit(p)
        best = None
        lighter = _lighter(p)
        if lighter is None:
            anchors = [_restroked(p, reg + (p.sv - reg) * j / SQUINT_ANCHORS) for j in range(1, SQUINT_ANCHORS)]
        else:
            anchors = [q for q in lighter if q.sv >= reg]
        for q in anchors + [p]:
            v = _squint_value(spec, sq, q, ot, ob, overrides, width)
            if v is None:
                continue
            if best is None or abs(v - a0) > abs(best - a0):
                best = v
        if best is not None and (lim - a0) * (best - a0) < 0:   # (only ever toward the limit)
            best = None
        _MONO[key] = best
    return _MONO[key]


_SQUINT: dict = {}
SQUINT_SLACK = 0.02   # what the Regular reference allows for the raster
_REG_SV: dict = {}


def _regular_sv(p) -> float:
    """The Regular's stem in the same cut (the squint rule for counters is
    for weights heavier than it)."""
    from .instances import params
    if p.mono not in _REG_SV:
        _REG_SV[p.mono] = params(400).with_(mono=p.mono).sv
    return _REG_SV[p.mono]


def _squint_reference(spec, p, kinds=('hole', 'slot')) -> float:
    """What a glyph's white keeps under the squint at Regular, in the same
    cut, capped at vision.READS: the least it may keep at any weight."""
    return _squint_regular(spec, p, kinds)[0]


def _squint_count(spec, p, kinds=('hole', 'slot')) -> int:
    """How many holes and slots the glyph's watched white has at Regular."""
    return _squint_regular(spec, p, kinds)[1]


def _squint_regular(spec, p, kinds, over=None):
    """(reference, count, whites) of the glyph's watched white at Regular,
    drawn with `over` (a free variable at a trial value: a form is held to
    its own Regular, so a pair of bars made one is not missed as two);
    whites: its readable white features (white_features)."""
    from .instances import params
    from .vision import READS
    over = over or {}
    key = (spec.name, p.mono, kinds, tuple(sorted(over.items())))
    if key not in _SQUINT:
        ref = params(400).with_(mono=p.mono)
        reg = _build(spec, ref, 0.0, 0.0, dict(over))
        d = _squint_pieces(reg, kinds)
        _SQUINT[key] = (min(READS, min(d, default=1.0)) - SQUINT_SLACK, len(d), white_features(reg.rings(), ref))
    return _SQUINT[key]


def _read(g, count, whites) -> float:
    """How a glyph reads under the squint (_squint), held to its Regular's
    count of watched white and, for a rule that watches whites
    (Squint.whites), of white features: a white the Regular has that is
    gone altogether (closed, or narrower than half a stroke) reads 0, not
    1. The narrow whites the squint watches can vanish by closing: З's open
    bowls, wide at Regular, are slits at Black and solid at the heaviest
    grade, and the squint saw no narrow white there at all. (Not every
    rule: the white features of letters at large shrink under half a stroke
    at Black by design, between a tail and its stem, a mark and its letter.)"""
    if whites and white_features(g.rings(), g.p) < whites:
        return 0.0
    return _squint(g, count=count)


def draw(name: str, p: Params, ot: float = 0.0, ob: float = 0.0, width: float | None = None) -> Glyph:
    spec = REGISTRY[name]
    if p.slant and f'{name}.ital' in REGISTRY:   # an italic drawing replaces the upright one
        spec = REGISTRY[f'{name}.ital']
    overrides: dict = {}
    g = _build(spec, p, ot, ob, overrides, width)
    for k, op in enumerate(spec.openings):
        ratio = _heritage_ratio(spec, k)
        if op.max_ratio is not None:
            ratio = min(ratio, op.max_ratio)
        target = ratio * p.sv
        if op.free not in g.defaults:                       # this drawing does not use it (a cell's upright form)
            continue
        if op.measure(g) >= target - 1e-6:
            continue
        a, b = g.defaults[op.free], op.limit(p)
        for _ in range(24):  # bisection: a is too closed, b assumed open enough
            mid = (a + b) / 2
            trial = _build(spec, p, ot, ob, {**overrides, op.free: mid}, width)
            if op.measure(trial) >= target:
                b = mid
            else:
                a = mid
        overrides[op.free] = b
        g = _build(spec, p, ot, ob, overrides, width)
    auto = _auto_counters(spec)
    if auto is not None:
        n, ratio = auto
        target = min(ratio, AUTO_SHARE) * p.sv
        if _counter_white(g, n) < target - 1e-6:
            a, b = 1.0, AUTO_MIN
            for _ in range(24):
                mid = (a + b) / 2
                trial = _build(spec, p, ot, ob, {**overrides, 'sh_auto': mid}, width)
                if _counter_white(trial, n) >= target:
                    b = mid
                else:
                    a = mid
            overrides['sh_auto'] = b
            g = _build(spec, p, ot, ob, overrides, width)
    if auto is not None and not spec.squint and p.sv > _regular_sv(p) * 1.15:
        # a letter's closed counters also read under the squint, not only by
        # measure: its horizontals thin further, within the same bound, until
        # they do (slots are left alone: the arch notches are designed)
        holes = ('hole',)
        want = _squint_reference(spec, p, holes)
        if _squint(g, holes) < want:
            a, b = overrides.get('sh_auto', 1.0), AUTO_MIN
            far = _build(spec, p, ot, ob, {**overrides, 'sh_auto': b}, width)
            if _squint(far, holes) >= want:
                for _ in range(8):  # bisection: a fuses, b reads
                    mid = (a + b) / 2
                    if _squint(_build(spec, p, ot, ob, {**overrides, 'sh_auto': mid}, width), holes) >= want:
                        b = mid
                    else:
                        a = mid
            trial = _build(spec, p, ot, ob, {**overrides, 'sh_auto': b}, width)
            if len(trial.rings()) == len(g.rings()):         # it thins; it never changes the topology
                overrides['sh_auto'] = b                      # (the variable font's masters must agree)
                g = trial
    for sq in spec.squint:
        if sq.free not in g.defaults:
            continue
        if sq.absolute:                     # a choice of form, made once for the cut (see _cut_form)
            v = _cut_form(spec, sq, p)
            if v != g.defaults[sq.free]:
                overrides[sq.free] = v
                g = _build(spec, p, ot, ob, overrides, width)
            continue
        if p.sv < _regular_sv(p):
            # white fuses as strokes grow: under the Regular's stem a glyph
            # reading short of its Regular is not fusing, and thinner
            # strokes would not open it, only lighten it (₱'s bars at
            # Light). (A small capital, on the Regular's stem, reads less
            # than its Regular capital: there the rule still holds.)
            continue
        v = _squint_monotone(spec, sq, p, ot, ob, overrides, width)
        if v is not None:
            overrides[sq.free] = v
            g = _build(spec, p, ot, ob, overrides, width)
    # (the heritage drawing is never lightened; composites rely on their parts' own rules)
    if _is_symbol(spec) and p.floor and g.strokes and not g.extra:
        want = _white_reference(spec, p)
        if want and white_features(g.rings(), p) < want:
            a, b = 1.0, LIGHTEN_MIN
            lo = _build(spec, _lightened(p, b), ot, ob, overrides, width)
            if white_features(lo.rings(), _lightened(p, b)) >= want:
                for _ in range(16):
                    mid = (a + b) / 2
                    trial = _build(spec, _lightened(p, mid), ot, ob, overrides, width)
                    if white_features(trial.rings(), _lightened(p, mid)) >= want:
                        b = mid
                    else:
                        a = mid
            g = _build(spec, _lightened(p, b), ot, ob, overrides, width)
            g.lightened = b
    # the optical corrections move the settled drawing (openings, counters
    # and the squint are solved on the exact one)
    optical = OPTICAL is not None and p.optical and spec.name.removesuffix('.ital') in OPTICAL['names']

    def settled(k):
        """The drawing with its strokes lightened by k, optics applied."""
        h = g if k == 1.0 else _build(spec, _lightened(p, k), ot, ob, overrides, width)
        if optical:
            _optical(h, spec, p)
        return h
    g = settled(1.0)
    # Topology lock: heavier than the Regular, a drawing keeps the Regular's
    # contours and counters (white that closes into a hole, parts that fuse,
    # a counter that fills: S J G 4 з at the heaviest grade). Its strokes
    # lighten together, as little as brings the topology back (as the font
    # will carry it: after the optics, in whole units, curved in the
    # italic), at most to LOCK_MIN; a change they cannot undo is a form of
    # its own (¢ $ with stubs) and stands. A composite relies on its parts'
    # lock: lightened whole for an accent that touches its letter, it went
    # a weight lighter than its neighbours (ά in Mono SemiBold), and its
    # Regular may carry a part's flaw (ℚ the Q's tail pinhole).
    if p.floor and g.strokes and not g.extra and p.sv > _regular_sv(p) and \
            _topology(g) != _topology_reference(spec, p):
        ref = _topology_reference(spec, p)
        k0 = getattr(g, 'lightened', 1.0)
        if _topology(settled(k0 * LOCK_MIN)) == ref:
            a, b = 1.0, LOCK_MIN
            for _ in range(12):
                mid = (a + b) / 2
                if _topology(settled(k0 * mid)) == ref:
                    b = mid
                else:
                    a = mid
            # a margin past where the parts just part (at the boundary they
            # all but touch, and rounding joins them again)
            if b - LOCK_MARGIN >= LOCK_MIN and _topology(settled(k0 * (b - LOCK_MARGIN))) == ref:
                b -= LOCK_MARGIN
            g = settled(k0 * b)
            g.lightened = k0 * b
    return g
