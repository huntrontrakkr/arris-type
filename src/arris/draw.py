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

    def outline(self, record: bool = True):
        """(rings, chamfer record): see ``geom.ink``. Stamped glyphs bring
        their own records (``add_glyph``)."""
        p = self.p
        box = None
        if self.clip is not None:
            from shapely.geometry import box as _box
            box = _box(*self.clip)
        rec = [] if record else None
        rings = ink(self.strokes, _thickness(p, self.sh), p.c, self.extra, box, rec, self.butt)
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
        self.extra_chamfers += [_moved(r, dx, dy) for r in rec]

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
        return ('warp', (lambda y, f=f, dy=dy: f(y - dy) + dy)) if dy else r
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

    def f(y):
        if y <= knots[0][0]:
            return y - ob
        if y >= knots[-1][0]:
            return y + ot
        for (x0, y0), (x1, y1) in zip(knots, knots[1:]):
            if y <= x1:
                return y0 + (y - x0) * (y1 - y0) / (x1 - x0)
        return y
    g.warp = f


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
    hull: white at least half a stroke wide (opened by a quarter stroke)."""
    from shapely.geometry import MultiPoint
    from .geom import rings_to_shapely
    if not rings:
        return 0
    ink = rings_to_shapely(rings)
    hull = MultiPoint([q[:2] for r in rings for q in r]).convex_hull
    r = WHITE_OPEN * max(p.sv, p.sh, p.sd, p.ss)
    white = hull.difference(ink).buffer(-r, join_style='mitre').buffer(r, join_style='mitre')
    return sum(1 for q in getattr(white, 'geoms', [white]) if not q.is_empty and q.area > 0.5 * (2 * r) ** 2)


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
    """(reference, count) of the glyph's watched white at Regular, drawn with
    `over` (a free variable at a trial value: a form is held to its own
    Regular, so a pair of bars made one is not missed as two)."""
    from .instances import params
    from .vision import READS
    over = over or {}
    key = (spec.name, p.mono, kinds, tuple(sorted(over.items())))
    if key not in _SQUINT:
        reg = _build(spec, params(400).with_(mono=p.mono), 0.0, 0.0, dict(over))
        d = _squint_pieces(reg, kinds)
        _SQUINT[key] = (min(READS, min(d, default=1.0)) - SQUINT_SLACK, len(d))
    return _SQUINT[key]


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
        from .vision import READS
        kinds = ('hole', 'slot')
        a, b = overrides.get(sq.free, g.defaults[sq.free]), sq.limit(p)
        want, n = _squint_regular(spec, p, kinds, {sq.free: a})
        if sq.absolute:
            want = READS - SQUINT_SLACK
        now = _squint(g, count=n)
        if now >= want:
            continue
        far = _build(spec, p, ot, ob, {**overrides, sq.free: b}, width)
        want_b, n_b = _squint_regular(spec, p, kinds, {sq.free: b})
        if sq.absolute:
            want_b = READS - SQUINT_SLACK
        s_far = _squint(far, count=n_b)
        if s_far >= want_b:
            for _ in range(10):  # bisection: a fuses, b reads
                mid = (a + b) / 2
                if _squint(_build(spec, p, ot, ob, {**overrides, sq.free: mid}, width), count=n_b) >= want_b:
                    b = mid
                else:
                    a = mid
        elif s_far < now - SQUINT_SLACK:
            # the limit reads worse, past what the raster can tell: leave it
            # be (within that, the rule's way, less ink, is taken: ₹'s
            # thinner bars leave its leg room)
            continue
        overrides[sq.free] = b
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
    if OPTICAL is not None and p.optical and spec.name.removesuffix('.ital') in OPTICAL['names']:
        _optical(g, spec, p)
    return g
