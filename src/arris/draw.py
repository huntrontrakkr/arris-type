"""The glyph-drawing vocabulary and registry.

A glyph is a function of the parameters that adds strokes to a ``Glyph``.
Coordinates are font units, y up, with the glyph body starting at x = 0;
spacing is added when the font is assembled.
"""
from __future__ import annotations

import contextlib
import os

from dataclasses import dataclass, field, replace
from typing import Callable

from . import cache
from .geom import Node, Stroke, Thickness, ink
from .params import MONO_NARROW, Params

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

    A share of the stem grows with the stem: a counter held to one is made
    larger at every heavier weight (the italic k's loop dropped, its counter
    grew from Bold to 875 and fell back to a diamond at Black, where the
    loop ran out). ``hold`` (for a closed counter): the rule acts from the
    weight of the cut where the drawing first falls short of its share,
    and from there it keeps the tightest counter's area at what it was
    there, shrinking as the stem grows (in proportion), so the counter
    only ever gets smaller with the weight. (Its width, held instead, let
    the area grow as the shape changed.) The italic k's alone: 1.008 held
    the e, æ, ø, Q and the closed-counter thinning too, and where a counter
    is small when the rule first acts (the italic e's eye) it shrank to a
    sliver by Black, the letter clogged; 1.009 put them back.
    """
    measure: Callable[['Glyph'], float]
    free: str
    limit: Callable[[Params], float]
    max_ratio: float | None = None   # cap on the watch's share, if it is generous
    hold: bool = False               # past the weight where it first acts, the counter it had there, shrinking (_engaged)
    own: bool = False                # the glyph thins the strokes round this counter itself, by ``free``: the thinning
                                     # of all its horizontals for its closed counters (draw) is off where it draws with it
    across: bool = False             # the gap is as wide as the letter's counter: held to as much less of its share as
                                     # the counter has given across past the Regular (given_across)


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
                                # carries each as a glyph of its own, swapped where the engine swaps them (arris.vf.forms)


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
    base: str | None = None            # the letter it is made from (ñ's n, the Bulgarian п's n): its body in Mono Narrow
    white: str = 'cap'                 # whose white its body and drawing measure (letterframe.zone, white_of)


def glyph(name: str, char: str | None, width, kind='fig', openings=(), solid=False, cell=False, squint=(),
          base: str | None = None):
    def deco(fn):
        w = width if callable(width) else (lambda p, w=width: getattr(p, w))
        f = fn
        if isinstance(kind, tuple) and kind[0] == 'punct' and not cell and not getattr(fn, 'mono_fitted', False):
            # a symbol keeps to its cell in the monospaced cut (symkit.mono_fitted)
            from .glyphs.symkit import mono_fitted
            f, w = mono_fitted(name, fn, w, kind)
        white = white_of(fn, kind)
        REGISTRY[name] = Spec(name, ord(char) if char else None, f, _zoned(w, white), kind, tuple(openings), solid, cell,
                              tuple(squint), base, white)
        return fn
    return deco


def given_across(spec, p) -> float:
    """What is left of the white across a glyph's counters past the
    Regular, as a share of what the watch's own rule gives its weight
    (letterframe.white_scale): the measure an opening that is as wide as
    its letter's counter is held to (Opening.across). Until 1.017's
    narrowing the cursive e's eye was held to half a stem whatever its
    counter: in a counter a quarter narrower at Black the rule took hold a
    weight earlier and thinned the top and the bar to 0.70 of their own for
    it, where they had given 0.92."""
    from .glyphs.letterframe import white_scale, zone
    from .params import white_own
    with zone(spec.white):
        return white_scale(p) / white_own(p.sv / (2 * p.m))


OWN_WHITE = ('operators', 'arrows', 'technical')    # glyph modules whose signs keep the watch's own white (white_of)


def white_of(fn, kind) -> str:
    """Whose white a glyph's body and drawing measure (letterframe.zone):
    a lowercase letter's ('lower'), which gives way to the stems fastest
    past the Regular; a capital's, a figure's or a sign's ('cap'); or the
    watch's own ('own'), for the mathematical operators, the arrows and
    the technical signs: figures of fixed geometry, bars a set white apart
    and strokes at 45 degrees, that have no counter to give. Narrowed with
    the letters, ⊦ lost its stem to a wedge at Black, ⊫ its two stems to a
    slab, and the feet of ≎ ran out past its bars in points."""
    if kind == 'lower':
        return 'lower'
    if (getattr(fn, '__module__', '') or '').rsplit('.', 1)[-1] in OWN_WHITE:
        return 'own'
    return 'cap'


def _zoned(width, white):
    """A glyph's body width, measured in its own white: a lowercase
    letter's gives way to its stems faster than a capital's
    (letterframe.white_scale, zone; white_of)."""
    def measured(p):
        from .glyphs.letterframe import zone
        with zone(white):
            return width(p)
    return measured


def B(x, y, leg=None, w=None):
    """A bowl corner (leg None = the parameter default; w the thickness of
    the segment that follows, None = by its direction)."""
    return ('bowl', x, y, leg, w)


NUDGE = (0, -2, 2, -4, 4, -8, 8, -12, 12)   # units: the steps a settling stroke tries off a coincidence with the drawing it meets (Glyph.settle)
# The strokes added to a letter or sign (the bar of Đ Ħ ŧ, the slash of Ø Ł, a bar across a stem: its
# decorations) keep the Regular's weight: past it they stay as they are at Regular while the letter goes on
# getting heavier, so the white beside them stays open and they read at every weight, one rule for every
# one of them (the owner, 2026-11-06: "We need to be consistent about the bar. If it's added, keep the
# weight at 400"; 1.007 to 1.013 held them from 600, docs/research/mono-cell.md §3). In Arris Mono
# Narrow, its own Regular, drawn at narrow_weight(400) (hold_weight).
EXTRA_HOLD = 400.0


def hold_weight(p) -> float:
    """The weight of p's cut whose added strokes every heavier weight keeps
    (EXTRA_HOLD): the cut's Regular, as drawn."""
    if p.narrow:
        from .instances import narrow_weight
        return narrow_weight(EXTRA_HOLD)
    return EXTRA_HOLD


def crotch_fill(p) -> float:
    """How far along the stem the corner rule fills the crotch a diagonal
    makes with it, in breaks (geom._ring_rule): one in Arris, the leg every
    other corner has on its horizontal or vertical edge; two in the watch's
    own drawing (the pixel rule the figures came with, WTCH 100). The
    italic's were two as well until 1.017, twice the upright's ink where a
    diagonal already lies on a stem: 88 units along each side of the
    cursive e's eye at Black."""
    return 2.0 - p.optical


def fill_leg(p) -> float:
    """The leg of the chord that fills a concave corner (geom._ring_rule):
    the weight's own break up to its cut's Regular, and the Regular's from
    there to Black (held_at), so the insides of the letters stop filling
    as the stems grow. The watch's own drawing (WTCH 100) keeps the pixel
    rule, one leg for every corner.

    The owner, 2026-11-10: "the interior ... is getting really fat because
    we chamfer the bits at a certain level and it just doesn't look
    right"; shown the fills held at the Regular's, the italic's crotches
    filled one break and both, he chose both ("you can try three")."""
    return p.c - (p.c - held_c(p)) * p.optical


def facet_close(p) -> float | None:
    """How short a wall of white between two cuts closes to a point, in
    breaks (geom.FACET, geom._polish): half a break in Arris; in the
    watch's own drawing and the italic, only the slivers every outline
    loses."""
    from .geom import FACET, POLISH
    if p.slant:
        return None
    return POLISH + (FACET - POLISH) * p.optical


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
    zone_k: float = 1.0   # the zone's share of the weight's horizontals: the lowercase's are thinner toward Black (Params.low)
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
    overlay: list = field(default_factory=list)     # (stroke, chamfer leg): laid over the finished ink (lay, geom.ink)

    def held(self, direction=(1.0, 0.0)) -> float:
        """The thickness of a stroke added to the letter, running in
        ``direction``: the glyph's own (its horizontals as it thins them) up
        to the Regular (hold_weight), and from there on the Regular's, in the same cut
        (grade, watch, Mono and slant kept). Never heavier than the glyph's
        own. A set derived from a font's (small capitals, small figures) keeps
        its own."""
        return _thickness(self.p, self.sh)(direction) * self.held_share(direction)

    def held_share(self, direction=(1.0, 0.0)) -> float:
        """Glyph.held as a share of the glyph's own thickness in ``direction``
        (1 up to EXTRA_HOLD), for a drawing that sets a stroke's thickness
        itself."""
        p = self.p
        q = held_at(p)
        if q is p:
            return 1.0
        k = self.sh / max(p.sh, 1e-9)                       # the glyph's own thinning of its horizontals, kept
        own = _thickness(p, self.sh)(direction)
        return min(1.0, _thickness(q, max(q.sh * k, q.floor))(direction) / max(own, 1e-9))

    def free(self, name: str, default: float) -> float:
        """A free variable of the drawing (see Opening)."""
        self.defaults[name] = default
        return self.overrides.get(name, default)

    def part(self, name: str):
        """The ink of the named strokes, before the union and corner rule. A
        glyph fitted to Mono's cell (_cell_fit) is its narrower drawing
        stamped in: its parts are that drawing's, where it stands."""
        import shapely
        from .geom import stroke_polygon
        fit = getattr(self, 'fit_src', None)
        if name not in self.parts and fit is not None:
            from shapely import affinity
            return affinity.translate(fit[0].part(name), fit[1], 0.0)
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

    def lay(self, *pts, c: float, start='flat', end='flat'):
        """A stroke laid over the finished letter (``geom.ink``'s overlay):
        finished alone, its ends broken on the chamfer leg ``c``, and joined
        to the letter as it stands, so no corner rule fills in where it
        meets it. For an added stroke held at the Regular (lay_bar): with
        the Regular's ``c`` it is the same stroke from there to Black."""
        n = len(self.strokes)
        self.stroke(*pts, start=start, end=end)
        self.overlay.append((self.strokes.pop(n), c))
        return self

    def move(self, f):
        """Move what is drawn so far node by node, f(x, y) -> (x, y): the
        strokes and those laid over them (lay) alike. (Moved one by one, a
        drawing turned or shifted left its laid strokes where they were:
        a negation's slash 24 units off ∌'s middle in Mono Bold Italic.)"""
        def moved(st):
            return type(st)(tuple(type(n)(*f(n.x, n.y), n.bowl, n.w) for n in st.nodes), st.closed, st.start, st.end)
        self.strokes = [moved(st) for st in self.strokes]
        self.overlay = [(moved(st), c) for st, c in self.overlay]

    def rings(self):
        return self.outline(record=False)[0]

    def settle(self, cands, curves: bool = False, lay: bool = False) -> bool:
        """Draw the first of the candidate stroke sets (each a list of
        ``stroke`` argument tuples) whose outline the topology check
        (``arris.topology``) finds clean, in the italic too. A bar placed by
        rule can still land an edge a unit from a jog of the letter it
        crosses (the ŧ's at 900: a hairline fold where the crossbar's
        underside met the bar's top), and a step of a few units (NUDGE)
        clears it. None clean: the first stands, for the check to name.
        ``lay``: the strokes are added ones, laid over the letter (Glyph.lay)
        with their ends broken as at the Regular (held_c)."""
        from . import italic as IT
        from .topology import faults
        p = self.p
        n, m = len(self.strokes), len(self.overlay)
        def put(st):                                        # (point, ...) or (point, ..., {stroke's keywords})
            kw = st[-1] if st and isinstance(st[-1], dict) else {}
            pts = st[:-1] if kw else st
            if lay:
                self.lay(*pts, c=held_c(p), **kw)
            else:
                self.stroke(*pts, **kw)
        def clear():
            del self.strokes[n:]
            del self.overlay[m:]
        best = None
        for j, strokes in enumerate(cands):
            clear()
            for st in strokes:
                put(st)
            rings, rec = self.outline(record=bool(p.slant))
            if faults([[(q[0], q[1], True) for q in r] for r in rings], p.c):
                continue
            if p.slant and faults(IT.outline(rings, rec, p), p.c, True):
                continue
            if not (curves and p.slant):
                return True
            # ``curves`` (a diagonal stroke added to a letter, in the italic): a 45-degree edge of the
            # stroke lying on the line of one of the letter's chamfers claims it and holds it straight
            # (italic._segments; the ł's foot at 650 and 670, 2026-11-02): of the clean candidates,
            # the one that leaves the most chamfers curved, the first on a tie. Not for bars: a level
            # stroke lies on no such line, and counting its own edge breaks curves them (the italic
            # ҟ's bar went round-ended at 500)
            k = len(IT._plan(rings, p, IT.split_warp(rec)[0])[0])
            if best is None or k > best[0]:
                best = (k, j)
        if best is not None:
            clear()
            for st in cands[best[1]]:
                put(st)
            return True
        clear()
        for st in cands[0]:
            put(st)
        return False

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
        # glyphs stamped as drawn at this one's parameters, only moved (an
        # accented letter's base): finished. One drawn at other parameters
        # (a small figure in a fraction) or scaled is finished again here.
        # Not a mark drawn with its own (marks.kept: ``finished``): it is the
        # mark it is under a lighter letter. Finished again on a heavier
        # letter's breaks, a corner cut where a steep edge meets a level one
        # (the cedilla's tab) was cut a second time, half as deep again.
        finished = [e for e in self.extra if any(src[0] is e and tuple(src[3][:4]) == (1.0, 0.0, 0.0, 1.0)
                                                 and (src[1].p == p or getattr(src[1], 'finished', False))
                                                 for src in self.extra_src)]
        rings = ink(self.strokes, _thickness(p, self.sh), p.c, self.extra, box, rec, self.butt,
                    tags=tags, extra_edges=self._extra_edges() if tags is not None else (), finished=finished,
                    overlay=self.overlay, crotch=crotch_fill(p), facet=facet_close(p), fill=fill_leg(p))
        rec = (rec or []) + self.extra_chamfers if record else []
        if record and getattr(self, 'square', False):
            # italic.SQUARE: the italic k's edge breaks; 'bowl', a bowl's chamfers too (₴)
            rec = rec + [('square',) if self.square is True else ('square', self.square)]
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
    def sh0(self) -> float:
        """The horizontals of the glyph's zone, before the glyph thins its own."""
        return self.p.sh * self.zone_k

    @property
    def sh(self) -> float:
        return max(self.sh0 * self.sh_k * self.sh_auto, self.p.floor)

    def stack(self, n: int, height: float, ratio: float = 0.9):
        """Thin the horizontals where n bars share ``height`` so that each
        counter between them stays at least ``ratio`` times a bar."""
        fit = height / (n + (n - 1) * ratio)
        self.sh_k = min(1.0, fit / self.sh0)
        return self.sh


def _thickness(p: Params, sh: float) -> Thickness:
    return Thickness(p.sv, sh, p.sd, p.ss, p.slant, floor=p.floor)


def _warped(r, f):
    """A chamfer record entry with every point's y passed through f (a
    direction is carried by moving a point a unit along it)."""
    if r[0] in ('warp', 'square'):
        return r
    if r[0] == 'hid':
        (x, y), (fx, fy), (dx, dy) = r[1], r[2], r[3]
        return ('hid', (x, f(y)), (fx, f(fy)), (dx, f(fy + dy) - f(fy)), r[4])
    if r[0] == 'bowl':
        return ('bowl',) + tuple(((q[0], f(q[1])), (d[0], f(q[1] + d[1]) - f(q[1]))) for q, d in r[1:])
    if r[0] == 'line':
        (x, y), (dx, dy) = r[1], r[2]
        y0, y1 = f(y), f(y + dy)
        return ('line', (x, y0), (dx, y1 - y0))
    return ('chord', (r[1][0], f(r[1][1])), (r[2][0], f(r[2][1])))


def _moved(r, dx, dy):
    if r[0] == 'square':
        return r
    if r[0] == 'warp':
        f = r[1]
        return ('warp', Shifted(f, dy)) if dy else r
    if r[0] == 'bowl':
        return ('bowl',) + tuple(((q[0] + dx, q[1] + dy), d) for q, d in r[1:])
    if r[0] == 'hid':
        return ('hid', (r[1][0] + dx, r[1][1] + dy), (r[2][0] + dx, r[2][1] + dy), r[3], r[4])
    return ('chord', (r[1][0] + dx, r[1][1] + dy), (r[2][0] + dx, r[2][1] + dy))


LETTER_KINDS = ('cap', 'lower')


_WIDE: dict = {}
WIDE_MODULES = 11.0   # Mono Narrow: a letter this many modules wide or more at the Regular is wide by nature
WIDE_ROOTS = ('M',)   # and what is made from these: the M is two stems and a V between them at any width (10.7 modules
                      # since 1.017, among Ђ Ъ Ѣ, which are one stem and a bowl)
# Mono Narrow's arch letters, a little wider than its body: in 7.8 modules the
# shoulder's 45-degree diagonal and the arch's corner left the n, h and r
# almost no flat top, and at Bold the diagonal ran out of room and its notch
# (the 1's flag, turned) all but closed; at 8.4 the shoulder keeps Arris
# Mono's notch and the r its arm. The u, an n turned, goes with them.
ARCH = ('n', 'h', 'r', 'u')
ARCH_MODULES = 8.4


def _root(spec):
    """The letter a glyph is made from, followed back (ǖ to ü to u), its
    italic drawing (n.ital) its upright's name."""
    seen = set()
    while spec.base and spec.base in REGISTRY and spec.name not in seen:
        seen.add(spec.name)
        spec = REGISTRY[spec.base]
    return spec.name.removesuffix('.ital')


def _wide(spec) -> bool:
    """Whether a letter is wide by nature: its own width at the Regular
    (proportional, ungraded) is WIDE_MODULES or more (m and W 12.2, w 11.8;
    the rest are not), or it is made from the M (WIDE_ROOTS). Decided once,
    at the Regular, so a letter is wide at every weight or at none."""
    if spec.name not in _WIDE:
        from .instances import params as _params
        ref = _params(400)
        try:
            _WIDE[spec.name] = spec.width(ref) >= WIDE_MODULES * ref.m or _root(spec) in WIDE_ROOTS
        except Exception:
            _WIDE[spec.name] = False
    return _WIDE[spec.name]


def body_width(spec, p, width=None):
    """A glyph's body: its own width, or in the monospaced cut, every
    letter fills the figures' body. Mono Narrow's wide and arch letters are
    measured from its body, so a set drawn smaller (the small figures'
    parameters scale fig_w) draws them smaller with it."""
    if width is not None:
        return width
    if p.mono and spec.kind in LETTER_KINDS:
        if p.narrow and _wide(spec):
            # Mono Narrow: a letter wider by nature (m w M W) is drawn as wide
            # as Arris Mono draws it at this weight, so its counters stay open
            return p.wide * p.fig_w
        if p.narrow and _root(spec) in ARCH:
            # Mono Narrow's arch letters, and what is made from them
            return ARCH_MODULES / MONO_NARROW * p.fig_w
        return p.fig_w
    return spec.width(p)


_DEPTH = [0]   # how deep in other glyphs' drawings a drawing is made (a stamped or inset letter is 1 or more)


@contextlib.contextmanager
def _as_own():
    """While a reference is drawn that others are measured by and that is
    kept (a height's overshoot from its o, its bar from the 5, the hooks'
    lines from the e, a glyph's Regular, the weight its counters shut at):
    drawn as a glyph of its own, not as a part of whichever glyph asks for
    it first. In Arris Mono a glyph of its own is fitted to its cell and a
    part of another is not (_start), so the reference was one drawing if a
    letter asked first and another if an accented letter's base did, and
    kept either way: after a plain e, s or o the x-height's overshoot in
    Mono Bold Italic was 1.50 units, before one 1.09, and the same font
    came out two ways as its glyphs were shared out among the build's
    workers (about a hundred accented letters and tabular figures)."""
    depth, _DEPTH[0] = _DEPTH[0], 0
    try:
        yield
    finally:
        _DEPTH[0] = depth


def _cell_kind(spec) -> bool:
    """Whether a glyph keeps to Mono's cell: not marks, spaces, ligatures."""
    return spec is not None and spec.kind not in ('mark', 'space') and \
        not (isinstance(spec.kind, tuple) and spec.kind[0] == 'liga')


CELL_GAP = 0.25   # modules: in Mono a letter's ink keeps this far inside its cell, so neighbours never touch
# how a drawing asked for a body narrower than its parts allow fails: a
# counter too small for its bowls, a stroke run to nothing (ℰ's inner E at
# a letter's narrowest in Mono Narrow), a white divided by none
UNDRAWABLE = (ValueError, IndexError, ZeroDivisionError)


def _start(spec, p, ot, ob, overrides, width, cell=True):
    """A glyph's drawing begun: its body, and in Mono its cell."""
    g = Glyph(p, spec.name, ot=ot, ob=ob, W=body_width(spec, p, width), overrides=dict(overrides))
    g.width_arg = width                     # (a body the caller set: a composite's base is drawn in it)
    g.sh_auto = overrides.get('sh_auto', 1.0)
    g.defaults['sh_auto'] = 1.0
    if spec.kind == 'lower' and not p.slant:
        g.zone_k = p.low
        if p.optical and spec.name not in ZONE_SETTERS and not _OWN_BAR[0]:
            # The zone's bar is the one the a's and the e's hooks hang from (lower.hook_ref): where those
            # thin it with their closed end's bar, from ExtraBold, every bar of the lowercase thins with
            # them, and the counters of o, c, b, n and the rest stand on the lines the a's and the e's do
            # (the owner, 2026-11-12, of the c brought onto their lines and the o left on its own, 23 units
            # thicker at Black: "o needs to open up a little bit more. Let's make sure that we're extremely
            # consistent like this across everything").
            from .glyphs.lower import hook_ref
            ref = hook_ref(p)
            if ref is not None:
                g.zone_k = ref[0] / p.sh
    elif spec.kind == 'lower' and p.optical and not _OWN_BAR[0]:
        # The italic's lowercase stands on the upright's bar. It kept the weight's own (it is not thinned
        # for the x-height as the upright is), and from SemiBold a line of it was the darker of the two: by
        # 2.6% at Black, on bars of 170 units beside the upright's 118, with every counter of the cursive the
        # tighter for it.
        from .glyphs.lower import hook_ref
        ref = hook_ref(p.with_(slant=0.0))
        if ref is not None:
            g.zone_k = min(1.0, ref[0] / p.sh)
    elif spec.kind in ('cap', 'fig') and p.optical and spec.name not in CAP_SETTERS and not _OWN_BAR[0]:
        # The capitals and the figures the same: one bar on the cap height, the one the 5, the 6 and the 9
        # keep where their mouths hold them (from ExtraBold: 147 units to Black). Each letter thinned for
        # itself, and at Black the O and the E stood on bars of 170 units, the S on 154, the 5, 6 and 9 on
        # 147 and the Q on 119.
        bar = _cap_bar(p)
        if bar is not None:
            g.zone_k = min(1.0, bar / p.sh)
    if cell and p.mono and _DEPTH[0] == 0 and _cell_kind(spec):
        # Mono: no ink past the cell (the body sits centred in it). A letter
        # is fitted into it (_cell_fit); anything else that would run on is
        # cut at its edge, and the corner rule chamfers the cut like any
        # other end. The glyph's own cell: a letter drawn inside another (an
        # inset N in ₦) is cut at the outer glyph's cell, where it stands in
        # it, when it is stamped (add_glyph), not at a cell of its own
        # parameters
        g.cell = ((g.W - p.fig_adv) / 2, (g.W + p.fig_adv) / 2)
    return g


def _drawn(spec, g):
    from .glyphs.letterframe import zone
    _DEPTH[0] += 1
    try:
        with zone(spec.white):                              # (what the drawing measures in white is its own kind's)
            spec.fn(g)
    finally:
        _DEPTH[0] -= 1
    return g


def _ink_x(g, p=None):
    """(left, right) of a drawing's ink as the font carries it, its own clip
    applied (not the cell's): in the italic curved and slanted
    (italic.outline), as far as its curves reach (_curve_x), which is
    where a renderer draws them and where tools/mono_cell_check.py
    measures. Measured upright, a slanted letter ran out of its cell by its
    slant: 31 units at the median in Mono Bold Italic, 103 at worst, in
    more than half the glyphs. ``p``: the font's parameters, with which it
    curves and slants every glyph (font.place), whatever a drawing was
    drawn with: a sign drawn smaller (symkit) has a lower x-height, about
    half of which the slant turns on, and measured by its own it stood 19
    units from where the font put it (№ in Mono Narrow Italic)."""
    p = p or g.p
    if p.slant:
        from .italic import outline
        rings, rec = g.outline(record=True)
        return _curve_x(outline(rings, rec, p))
    from .geom import rings_to_shapely
    x0, _, x1, _ = rings_to_shapely(g.rings()).bounds
    return x0, x1


def _curve_x(contours):
    """(left, right) of quadratic contours ((x, y, on) points, two off-curve
    points in a row meeting at their midpoint), as far as the curves reach:
    not their off-curve points, which stand outside a rounded corner (a
    heavy dot's by 5 units in the italic, so that a dieresis measured
    within its room by its marks' ink was past it by its corners')."""
    xs = []
    for c in contours:
        n = len(c)
        for i, (x, _, on) in enumerate(c):
            if on:
                xs.append(x)
                continue
            px, _, pon = c[i - 1]
            nx, _, non = c[(i + 1) % n]
            a = px if pon else (px + x) / 2
            b = nx if non else (nx + x) / 2
            xs += [a, b]
            den = a - 2 * x + b
            if abs(den) > 1e-12 and 0.0 < (a - x) / den < 1.0:
                t = (a - x) / den
                xs.append((1 - t) ** 2 * a + 2 * (1 - t) * t * x + t * t * b)
    return (min(xs), max(xs)) if xs else (0.0, 0.0)


def cell_floor(W0, p) -> float:
    """The narrowest a letter is drawn to fit its cell: 0.6 of its body, and
    never so narrow that a counter between two stems closes (two stems and
    the least white, letterframe.least_white). Past it a mark beside the
    letter gives way (marks._caron_apostrophe)."""
    from .glyphs.letterframe import least_white
    return max(0.6 * W0, 2 * p.sv + least_white(p))


def _cell_fit(g, spec, p, ot, ob, overrides, width):
    """Mono: a letter whose ink would run out of its cell (a horn, the
    apostrophe of ď ľ, an ogonek, a slash, a tone mark beside a circumflex)
    is fitted into it, never cut: moved as little as brings its ink
    CELL_GAP inside the cell, and if it is wider than that leaves room
    for, drawn narrower until it is not (as the cursive set is,
    italic_forms._in_cell), then centred. The letter gives up width, not
    the mark. Drawn again without the cell, so nothing in it is cut, and
    stamped into the cell (Glyph.add_glyph), laid strokes and all."""
    gap = CELL_GAP * p.m                    # letters and signs alike (a sign kept a unit: № ℘ ⌃ ⌄ touched their neighbours)
    lo, hi = g.cell[0] + gap, g.cell[1] - gap
    optical = OPTICAL is not None and p.optical and spec.name.removesuffix('.ital') in OPTICAL['names']

    def ink_x(d):
        # with the optical corrections it will carry (_draw: they move the
        # settled drawing, after this): an overshoot is vertical, but in the
        # italic the slant leans it, 2 units each side of a round figure
        if not (optical and p.slant):
            return _ink_x(d, p)
        _optical(d, spec, p)
        try:
            return _ink_x(d, p)
        finally:
            d.warp = None
    x0, x1 = ink_x(g)
    if x0 >= lo - 0.5 and x1 <= hi + 0.5:
        return g
    W0 = g.W
    floor = cell_floor(W0, p) if spec.kind in LETTER_KINDS else 0.6 * W0
    W, h = W0, _drawn(spec, _start(spec, p, ot, ob, overrides, width, cell=False))
    x0, x1 = ink_x(h)
    over = (x1 - x0) - (hi - lo)
    wide, fit = W0, None                    # the narrowest body known too wide; the widest known to fit
    prev = None
    for _ in range(12):
        if over <= 0.5:
            fit = (W, h, x0, x1)
            if over >= -1.0:
                break
        else:
            wide = W
            if W <= floor + 1e-6:
                break
        # the next body: where the last two drawings' ink meets the room
        # (the ink need not narrow as the body does: ľ's stem stands in its
        # middle, and moves half as far), the first step as if it did; kept
        # between the bodies known too wide and known to fit
        if prev is not None and abs(over - prev[1]) < 0.25 and abs(W - prev[0]) > 1.0:
            # its ink did not narrow with its body: a sign drawn to its own
            # proportions does not at all; one drawn in a body of its own
            # (ℤ's in Mono Narrow, under the cell's) only past it. Tried as
            # narrow as it goes, and left if that does not narrow it either
            if W <= floor + 1e-6:
                break
            Wn = floor
        elif prev is not None and abs(over - prev[1]) > 1e-6:
            Wn = W - over * (W - prev[0]) / (over - prev[1])
        else:
            Wn = W - over * W / max(x1 - x0, 1.0)
        bottom = floor if fit is None else fit[0]
        if not bottom < Wn < wide:
            Wn = (bottom + wide) / 2 if fit is not None else max(floor, min(Wn, wide))
        if abs(Wn - W) < 0.05:
            break
        try:
            hn = _drawn(spec, _start(spec, p, ot, ob, overrides, Wn, cell=False))
            xn = ink_x(hn)
        except UNDRAWABLE:
            # it cannot be drawn so narrow (a counter would close): its floor
            # lies above, at most halfway back to the last body drawn
            floor = (Wn + W) / 2
            if floor >= wide - 0.05 or abs(W - Wn) < 1.0:
                break
            continue
        prev = (W, over)
        W, h, (x0, x1) = Wn, hn, xn
        over = (x1 - x0) - (hi - lo)
    if over > 0.5 and fit is not None:
        W, h, x0, x1 = fit
    # where the body would stand (centred in the cell), then as little a move as brings the ink inside
    dx = (W0 - h.W) / 2
    if x1 - x0 > hi - lo:
        dx = (lo + hi) / 2 - (x0 + x1) / 2
    elif x1 + dx > hi:
        dx = hi - x1
    elif x0 + dx < lo:
        dx = lo - x0
    f = _start(spec, p, ot, ob, overrides, width)
    f.p = h.p                               # (a sign drawn condensed or smaller, symkit: curved and slanted as its drawing was measured)
    cell, f.cell = f.cell, None             # (fitted: nothing to cut as it is stamped; the cell's clip stands after)
    f.add_glyph(h, dx, 0.0)
    f.cell = cell
    f.defaults.update(h.defaults)
    f.defaults_used.update({k: (v + dx if k == 'stem' else v) for k, v in h.defaults_used.items()})
    f.fitted = (round(W0 - h.W, 2), round(dx - (W0 - h.W) / 2, 2))   # (how much narrower, how far moved)
    f.fit_src = (h, dx)                     # (its parts, for the openings' measures: Glyph.part)
    return f


def _build(spec, p, ot, ob, overrides, width=None):
    g = _drawn(spec, _start(spec, p, ot, ob, overrides, width))
    if g.cell is not None and not spec.cell:
        g = _cell_fit(g, spec, p, ot, ob, overrides, width)
        x0, x1 = _ink_x(g, p)
        if g.cell[0] - 0.5 <= x0 and x1 <= g.cell[1] + 0.5:
            # fitted: no clip. The cell's clip cuts the raw ink, before the
            # corner rule breaks a stroke's tips, so a tip the rule would take
            # off but that reached the cell's edge was cut flat there (the
            # tonos of Ά Έ Ό at Bold)
            return g
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
# The figures and their alternates that stand in text as letters do, spaced by
# their own white (font._place_drawn) and kerned; each has a tabular twin on
# the figures' cell (name.tnum: glyphs.features). In Arris Mono all share
# the cell.
PROPORTIONAL_FIGS = _FIGS + ('zero.zero', 'zero.dot', 'five.ss02')
OPTICAL = {
    # (j.cv03: the hooked j was the j until 1.017, and is Arris Mono's still)
    'names': set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz') | set(_FIGS) | {'j.cv03'},
    # optical centre: the middle rises until the top counter of a three-bar
    # letter (B E 8) is this share of the bottom one. 1.0: no rise, the middle
    # bar of every letter and figure on the centre of its height. One rule for
    # all of them, and one number: until 1.017 it was 0.8615 (the middle 2.5%
    # of the height over the centre at Regular), and the a and the e alone
    # let it go toward Black. Measured on 37 families the middle bar of H E B
    # S 8 3 e a s stands 1.3% over the centre at Regular and 1.0% at Bold
    # (0.928 here), from none to 5%, and the ink's centre of mass on the
    # centre, for their lower halves are the wider; Arris's halves are one
    # width, and with the bars centred its centre of mass is on the centre
    # too, where 0.8615 held it half a percent over. Centred, the a is the e
    # turned half round, the s and the 8 their own half turn and the c's two
    # hooks one length at every weight (the owner, 2026-11-12: "it doesn't
    # have to be symmetric across the horizontal. It just has to follow the
    # same rules", and of centred against half the rise: "I trust your
    # feeling about this").
    'counters': 1.0,
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


CAP_SETTERS = {'five', 'six', 'nine'}       # the figures the cap height's bar is taken from (_cap_bar)
_CAP_BAR: dict = {}


def _cap_bar(p):
    """The bar of the cap height at ``p``: the 5's, as its mouth leaves it."""
    if p not in _CAP_BAR:
        if len(_CAP_BAR) > 512:
            _CAP_BAR.clear()
        _CAP_BAR[p] = None                                  # (while the 5 is drawn: what it stamps keeps the weight's own)
        with _as_own():
            _CAP_BAR[p] = draw('five', p).sh
    return _CAP_BAR[p]


ZONE_SETTERS = {'a', 'e', 's'}  # the letters the lowercase's bar is taken from, and the s, which shares its own out (_start)
_ZONE_OVER: dict = {}
_OWN_BAR = [0]              # while set, a letter is begun on the weight's own bar (_start, _zone_over)


def _zone_over(p, lower: bool) -> float:
    """What a round letter reaches past its line at ``p``: the o's need
    on the x-height, the O's on the cap height (vision.overshoot_need)."""
    key = (p, lower)
    if key not in _ZONE_OVER:
        from .vision import overshoot_need
        if len(_ZONE_OVER) > 1024:
            _ZONE_OVER.clear()
        _ZONE_OVER[key] = 0.0               # (while the o is drawn: fitted into Mono's cell it asks for its own)
        _OWN_BAR[0] += 1                    # (its outside is all that is measured: on the weight's own bar, so the
        try:                                # letters the height's bar is taken from can ask while they are drawn)
            with _as_own():
                g = _build(drawn_spec('o' if lower else 'O', p), p, 0.0, 0.0, {})
        finally:
            _OWN_BAR[0] -= 1
        _ZONE_OVER[key] = overshoot_need(g.rings(), p.xh if lower else p.cap)[0]
    return _ZONE_OVER[key]


HOOKS_WITH = {'c', 's'}     # letters whose hooks are the a's and the e's (lower.hook_ref): they move with theirs (_optical)
_HOOK_WARPS: dict = {}


def _hook_warps(p):
    """(the a's warp, the e's): what the optical corrections do to the two
    letters the hooks of the x-height are taken from."""
    if p not in _HOOK_WARPS:
        if len(_HOOK_WARPS) > 512:
            _HOOK_WARPS.clear()
        with _as_own():
            _HOOK_WARPS[p] = tuple(getattr(draw(n, p), 'warp', None) for n in 'ae')
    return _HOOK_WARPS[p]


class Joined:
    """Two warps, one under ``m`` and one from it up (either may be None:
    nothing moves there)."""

    def __init__(self, low, high, m):
        self.low, self.high, self.m = low, high, m

    def __call__(self, y):
        f = self.low if y < self.m else self.high
        return y if f is None else f(y)


def _optical(g, spec, p):
    from .geom import Node, Stroke
    from .vision import overshoot_need
    H = p.xh if spec.kind == 'lower' else p.cap
    if spec.name in HOOKS_WITH and not p.slant:
        # The c and the s hang the a's hook over the middle and the e's under it (lower.hook_ref), and are
        # moved as those two are, the upper half as the a and the lower as the e: with a rise of their own
        # (an overshoot was each letter's own) the c's hooks
        # ended 2.5 units off theirs at Black, both of them higher.
        high, low = _hook_warps(p)
        g.warp = Joined(low, high, H / 2) if (low is not None or high is not None) else None
        return
    r = OPTICAL['counters']
    # (the bars on its lines, where the letter draws them thicker than its own: the arm the a's and the e's
    # hooks hang from, the 3's top and foot. They move as one piece too; measured on the letter's own bar they
    # stood half in the white that stretches, and the rise took 3 units off the Black 3's top and gave them to
    # its foot)
    outer = max(g.sh, getattr(g, 'arm', 0.0))
    A = max(H / 2 - outer - g.sh / 2, 0.0)                   # a counter's height with the middle centred
    dc = A * (1 - r) / (1 + r) * p.optical
    if dc:
        # (a rise, where OPTICAL sets one, is every letter's alike, and gone at Black, where there is no room
        # for it: from Bold it fades out. The e's closed counter is over its bar and the a's under it, so a
        # rise makes the e's eye the smaller of the two, at Black 93 units by 107, side by side in a word)
        from .instances import STEMS
        dc *= 1.0 - min(1.0, max(0.0, (p.sv / p.grade_k - STEMS[700]) / (STEMS[900] - STEMS[700])))
    rings0 = g.rings()
    top, bot = overshoot_need(rings0, H)
    if p.optical:
        # One overshoot for a height: the o's on the x-height, the O's on the cap height (the capitals and the
        # figures), whatever the letter. Each had what its own outline asked, and at Regular the C stood 3.3
        # units over the line by the O's 1.3, the figures 3.0, the J's foot 10.8: the bars they carry there
        # stood that far off one another's (the owner, 2026-11-12: "put the overshoot on one value").
        top = bot = _zone_over(p, spec.kind == 'lower')
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
        raw = shapely.union_all([stroke_polygon(st, th, g.p.c) for st in g.strokes] + list(g.extra)
                                + [stroke_polygon(st, th, c) for st, c in g.overlay])
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
    # gone (tools/stroke_scan.py is the check). It comes in by degrees with
    # the stroke, nothing at the floor and whole at twice it (about
    # ExtraLight), a straight line in the weight the variable font can follow
    # between its Thin and ExtraLight masters: yielding only as far as the
    # floor forced it, the whole rise arrived between 100 and 110, and the
    # font, drawing a line from Thin to ExtraLight, had a tenth of it at 110.
    if p.floor:
        zone = H - outer - (m + t / 2)
        k = min(1.0, p.floor / max(min(t, p.sh), 1e-6))
        ramp = min(1.0, max(0.0, (min(t, p.sh) - p.floor) / p.floor))
        dc = max(0.0, min(dc * ramp, zone * (1 - k) + ot))
    knots = [(outer, outer - ob), (m - t / 2, m - t / 2 + dc), (m + t / 2, m + t / 2 + dc), (H - outer, H - outer + ot)]
    if not (dc or ot or ob) or not (outer < m - t / 2 and m + t / 2 < H - outer):
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


def _heaviest_stroke(g, p) -> float:
    """The thickest stroke a drawing has, by the directions its segments run
    in (or a thickness a node sets): a sign made of diagonals alone (‹ « ^)
    is measured by its diagonal, not by a stem it has none of. Measured by
    the stem, « fell short of the white rule from WTCH 60 up at the heavy
    weights, where the watch's diagonals are thinner against the stem, and
    was lightened there and not at the ends, which shrank it by a fifth
    (its reach is drawn from its strokes) between one master and the next."""
    if g is None or not getattr(g, 'strokes', None):
        return max(p.sv, p.sh, p.sd, p.ss)
    th = _thickness(p, g.sh)
    best = 0.0
    for st in g.strokes:
        nodes = st.nodes
        for a, b in zip(nodes, nodes[1:] + (nodes[:1] if st.closed else ())):
            best = max(best, a.w if a.w is not None else th((b.x - a.x, b.y - a.y)))
    return best or max(p.sv, p.sh, p.sd, p.ss)


def white_features(rings, p, g=None) -> int:
    """How many separate pieces of readable white a drawing holds inside its
    hull: white a disk half a stroke across fits in (half the drawing's
    heaviest stroke: _heaviest_stroke), and a piece is one a disk can move
    about in (the white eroded by the disk's radius: where it can be
    centred). Counted as the union of the disks instead (the white opened),
    two pieces met where disks either side of a pinch overlap, with no way
    through: ∭'s triangles under the hooks joined the whites between the
    stems from Bold to Heavy, so the rule lightened those weights, and let
    go at Black, where the beak's corner turned a degree."""
    from shapely.geometry import MultiPoint
    from .geom import rings_to_shapely
    if not rings:
        return 0
    ink = rings_to_shapely(rings)
    hull = MultiPoint([q[:2] for r in rings for q in r]).convex_hull
    if g is not None and g.overlay and (g.strokes or g.extra):
        # A stroke laid over a sign (the slash of ≠, of a negation) runs out past it, and between its ends
        # and the sign's own outline stand wedges of white that are nobody's: they close as the sign's
        # strokes grow, whatever is done. Counted, the ≠ had six whites at the Regular for the two a reader
        # sees, lost four from Medium, and was lightened as far as the rule goes from SemiBold without
        # getting one back: its bars 0.8 of the equals' beside it. A sign's whites are the ones inside the
        # outline of what it is laid over.
        import shapely
        from .geom import stroke_polygon
        th = _thickness(g.p, g.sh)
        own = shapely.union_all([stroke_polygon(st, th, g.p.c) for st in g.strokes] + list(g.extra)).convex_hull
        hull = hull.intersection(own)
    r = WHITE_OPEN * _heaviest_stroke(g, p)
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
        with _as_own():
            g = _build(spec, ref, 0.0, 0.0, {})
        _WHITE[key] = white_features(g.rings(), ref, g)
    return _WHITE[key]


def _lightened(p: Params, k: float) -> Params:
    """p with its strokes lightened by k, remembering it (Params.light), so
    an added stroke still keeps its weight's Regular (held_at)."""
    return p.with_(sv=p.sv * k, sh=p.sh * k, sd=p.sd * k, ss=p.ss * k, light=p.light * k,
                   unlit=_unlightened(p))


def _unlightened(p: Params) -> Params:
    """p as its weight draws it, before any lightening (Params.light): the
    very parameters lightened, kept with them (rebuilt by dividing the
    strokes back, they missed their cut by a rounding at some weights, and
    an added stroke went unheld there: ∄'s slash 70 units, 115 at 778)."""
    if p.light == 1.0:
        return p
    return p.unlit if p.unlit is not None else p


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
        with _as_own():
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
    from .instances import drawn
    from .vision import READS
    key = (spec.name, sq.free, p.mono)
    if key not in _FORMS:
        with _as_own():
            heavy = drawn(900).with_(mono=p.mono)                   # (the watch's Black: the heaviest any cut draws)
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
    from .instances import drawn
    key = (spec.name, sq.free, p.mono)
    if key not in _THINS:
        with _as_own():
            heavy = drawn(900).with_(mono=p.mono)
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


def _cut(p):
    """(p's weight, the parameters of p's cut at any weight) if p is a
    font's own (a weight, grade and watch balance of a cut:
    instances.params, Mono, Mono Narrow or neither, italic or not); else
    None (a set derived from one: small capitals, small figures). Mono
    Narrow's weight is the one it is drawn at (instances.narrow_weight).
    The weights are the watch's (instances.WATCH_STEMS, drawn): the one
    whose stem p has, whatever p's font calls it, so a rule that names a
    weight (the Regular's, every hundred to p's own, the watch's Black)
    reads the same stems in Arris, whose weights past the Regular are
    lighter than their names on the watch's ladder, as in Arris Watch.
    Until 1.014 Narrow was not found here, so no rule that reads the cut
    held for it: its ligatures spaced at Bold as at their own Regular and
    spread a cell a character, its added strokes never stopped gaining."""
    if p not in _CANON:
        from .instances import drawn, watch_weight
        out = None
        grad = p.grad
        w = watch_weight(p.sv / p.grade_k)                  # the watch's weight whose stem p has
        if abs(w - round(w, 3)) < 1e-9:
            w = round(w, 3)

        def make(watch):
            def at(w_):
                q = drawn(w_, grad, watch=watch).with_(mono=p.mono, narrow=p.narrow)
                if p.cursive:
                    q = q.with_(cursive=True)
                if p.slant:
                    from .italic import italic
                    q = italic(q)
                return q
            return at
        # the watch balance: the measured optics' share is 1 - watch (0 at
        # the watch's own proportions)
        for watch in sorted({round(1.0 - p.optical, 6), 1.0}):
            try:
                if make(watch)(w).same(p):
                    out = (w, make(watch))
                    break
            except Exception:  # noqa: BLE001
                pass
        _CANON[p] = out
    return _CANON[p]


def _at_watch(p, watch):
    """p's weight and grade in its own cut at another watch balance, if p is
    a font's own (_cut); else None. The font's weight (instances.weight_of),
    as the variable font carries the watch axis: at one weight, from Arris's
    stem to the watch's."""
    cut = _cut(p)
    if cut is None:
        return None
    from .instances import params, weight_of
    q = params(weight_of(p.sv / p.grade_k, 1.0 - p.optical), p.grad, watch=watch).with_(mono=p.mono)
    if p.cursive:
        q = q.with_(cursive=True)
    if p.slant:
        from .italic import italic
        q = italic(q)
    return q


# A stroke added across a letter or sign (a bar, a slash: lay_bar) keeps the Regular's thickness at every
# heavier weight (EXTRA_HOLD), laid over the letter so nothing fills in round it, and runs out further the
# thinner it is than the letter's own (the owner, 2026-11-06: "the thickening doesn't glop on it at all";
# "if the thickness is a problem, just lengthen it"; "if it's added, keep the weight at 400").
BAR_WHITE = 0.5     # modules: the side of the square of white a bar placed by its white keeps on its edge (bar_white)


def held_at(q):
    """q, or its cut's Regular past it (hold_weight): the parameters an
    added stroke is drawn with. A drawing lightened as a whole (a sign the
    white rule or the topology lock lightens: _lightened) holds its weight's
    Regular, lightened alike: unheld, the strike of ⇎'s italic ran from 89
    units to 116 between 600 and 601, where the rule began to lighten it."""
    if q.light != 1.0:
        if q.unlit is None:                                 # a set derived from lightened parameters: its own
            return q
        base = q.unlit
        h = held_at(base)
        return q if h is base else _lightened(h, q.light)
    cut = _cut(q)
    return cut[1](hold_weight(q)) if cut is not None and cut[0] > hold_weight(q) else q


def bar_held(q, direction=(1.0, 0.0)) -> float:
    """An added stroke's thickness at q, running in ``direction``: the
    weight's own, held from the Regular (held_at)."""
    h = held_at(q)
    return min(_thickness(q, q.sh)(direction), _thickness(h, h.sh)(direction))


def bar_white(g) -> float:
    """How much white the laid bar (g.overlay's first stroke, a level bar)
    keeps beside it where it shows: at each of its ends, above and below,
    the side of the largest square of white that sits on its edge in the
    stretch the letter leaves showing from that end in (0 where the letter
    covers the end); the least of the four, in units, at most two modules.
    A bar reads by its ends: white bounded by the letter on both sides (an
    X's notch over the bar at its crossing) is the letter's own."""
    from shapely.geometry import LineString, box
    from .geom import rings_to_shapely
    st, _ = g.overlay[0]
    (x0, y, t), x1 = (st.nodes[0].x, st.nodes[0].y, st.nodes[0].w), st.nodes[-1].x
    x0, x1 = min(x0, x1), max(x0, x1)
    over, g.overlay = g.overlay, []
    try:
        letter = rings_to_shapely(g.outline(record=False)[0])
    finally:
        g.overlay = over
    cap = 2 * g.p.m
    best = cap
    for sgn in (1.0, -1.0):
        e = y + sgn * t / 2
        free = LineString([(x0, e + sgn * 0.5), (x1, e + sgn * 0.5)]).difference(letter)
        spans = [tuple(sorted((q.coords[0][0], q.coords[-1][0]))) for q in getattr(free, 'geoms', [free])
                 if not q.is_empty and q.length > 1e-6]
        for end in (x0, x1):
            span = next((sp for sp in spans if abs(sp[0] - end) < 1.0 or abs(sp[1] - end) < 1.0), None)
            if span is None:
                return 0.0
            lo, hi = span

            def fits(side, lo=lo, hi=hi, e=e, sgn=sgn):
                if hi - lo < side:
                    return False
                strip = box(lo, min(e, e + sgn * side), hi, max(e, e + sgn * side)).intersection(letter)
                ink = sorted((q.bounds[0], q.bounds[2]) for q in getattr(strip, 'geoms', [strip])
                             if not q.is_empty and q.area > 1e-6)
                x = lo
                for a, b in ink:
                    if a - x >= side:
                        return True
                    x = max(x, b)
                return hi - x >= side
            if fits(cap):
                continue
            a, b = 0.0, cap
            for _ in range(14):
                mid = (a + b) / 2
                a, b = (mid, b) if fits(mid) else (a, mid)
            best = min(best, a)
    return best


def held_c(p) -> float:
    """The chamfer leg an added stroke's ends are broken on: the Regular's
    past it (held_at), so the stroke is the same from there to Black."""
    return min(p.c, held_at(p).c)


def lay_bar(g, ends, direction=(1.0, 0.0), start='flat', end='flat'):
    """A stroke added across the letter (a bar, a slash), laid over it
    (Glyph.lay), the Regular's thickness at every heavier weight
    (Glyph.held), its ends broken as at the Regular. ``ends(t, own)``: its
    two end points at thickness t, the letter's own thickness ``own`` at
    this weight (a drawing runs it further the thinner it is than that)."""
    p = g.p
    own = _thickness(p, g.sh)(direction)
    t = g.held(direction)
    a, b = ends(t, own)
    g.lay((a[0], a[1], t), b, c=held_c(p), start=start, end=end)
    return t


def _lighter(p):
    """The parameters of the lighter weights of p's own cut, from the
    Regular's up (every 100), if p is a font's own; else None (_cut)."""
    cut = _cut(p)
    if cut is None:
        return None
    w, at = cut
    return [at(w_) for w_ in range(400, int(w), 100) if w_ < w]


_ENGAGED: dict = {}
ENGAGE_STEPS = 14     # bisection steps over the weight, from the Regular's to Black (a twentieth of a unit)
HOLD_DECAY = 1.0      # a held counter's area goes as (the stem where the rule engaged / the stem) ** this


def _counter_area(g) -> float:
    """The area of the drawing's smallest closed counter as the reader sees
    it (0 if it has none): in the italic, of its curved outline (its
    corners curve or not as the counter's shape changes, a tenth of the
    counter's area at a step)."""
    if g.p.slant:
        from .italic import flatten, outline
        rings, record = g.outline()[:2]
        signed = []
        for c in outline(rings, record, g.p):              # curved (and warped, sheared: the area is the same)
            pts = flatten(c)
            signed.append(0.5 * sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
                                    for i in range(len(pts))))
        if not signed:
            return 0.0
        outer = max(signed, key=abs)
        holes = [abs(a) for a in signed if a * outer < 0]
        return min(holes) if holes else 0.0
    from shapely.geometry import Polygon
    from .geom import rings_to_shapely
    poly = rings_to_shapely(g.rings())
    areas = [Polygon(h).area for part in getattr(poly, 'geoms', [poly]) for h in part.interiors]
    return min(areas) if areas else 0.0


def _engaged(spec, k, ratio, p, ot, ob, overrides, width) -> float | None:
    """The counter area an opening that holds (Opening.hold) keeps at p:
    the area at the weight of p's cut where the drawing, its free variable
    at its default, first falls short of the opening's share of the stem
    (from the Regular's on; at the Regular if it is short there already),
    times that weight's stem over p's. None if p is not a font's own cut
    (the plain share then), or if p is lighter than that weight (the
    rule's own test decides). Found once a cut."""
    cut = _cut(p)
    if cut is None:
        return None
    w, at = cut
    op = spec.openings[k]
    across = (lambda q: given_across(spec, q)) if op.across else (lambda q: 1.0)
    key = (spec.name, k, ratio, at(400), tuple(sorted(overrides.items())))
    if key not in _ENGAGED:
        # read on the cut's own drawings, each in its own width (a graded weight is drawn in its
        # ungraded body: the reference is the cut's, whatever body p is drawn in)
        def short(w_):
            q = at(w_)
            with _as_own():
                return op.measure(_build(spec, q, ot, ob, overrides, None)) < ratio * q.sv * across(q) - 1e-6
        if short(400.0):
            we = 400.0
        elif not short(900.0):
            we = None
        else:
            lo, hi = 400.0, 900.0
            for _ in range(ENGAGE_STEPS):
                mid = (lo + hi) / 2
                lo, hi = (lo, mid) if short(mid) else (mid, hi)
            we = hi
        if we is None:
            _ENGAGED[key] = None
        else:
            q = at(we)
            with _as_own():
                _ENGAGED[key] = (we, _counter_area(_build(spec, q, ot, ob, overrides, None)), q.sv, across(q))
    found = _ENGAGED[key]
    if found is None or w < found[0]:
        return None
    # (a counter that gives across is as much smaller both ways: the eye over a 45-degree bar)
    return found[1] * (found[2] / p.sv) ** HOLD_DECAY * (across(p) / found[3]) ** 2


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
        with _as_own():
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
        with _as_own():
            reg = _build(spec, ref, 0.0, 0.0, dict(over))
        d = _squint_pieces(reg, kinds)
        _SQUINT[key] = (min(READS, min(d, default=1.0)) - SQUINT_SLACK, len(d), white_features(reg.rings(), ref, reg))
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
    if whites and white_features(g.rings(), g.p, g) < whites:
        return 0.0
    return _squint(g, count=count)


def _opened(spec, p, ot, ob, width, nest=True):
    """(the drawing, its overrides) with the spec's openings applied (draw's
    first step, before the closed-counter thinning). Not remembered: a
    drawing must run its glyph's code to be stamped with it (arris.cache)."""
    overrides: dict = {}
    g = _build(spec, p, ot, ob, overrides, width)
    nesting = _Nesting.at(spec.name, g, p, ot, ob, width) if spec.openings and nest else None
    for k, op in enumerate(spec.openings):
        ratio = _heritage_ratio(spec, k)
        if op.max_ratio is not None:
            ratio = min(ratio, op.max_ratio)
        # (a share of the stem, and in Arris of no more stem than the least white grows with, 158 units:
        # params.white_floor. At a stem of 200 the 3's mouth was held to 150 units, the letters' bays to 57)
        from .params import WHITE_HELD
        target = ratio * (p.sv - max(0.0, p.sv - WHITE_HELD * p.grade_k) * p.optical) * (given_across(spec, p) if op.across else 1.0)
        if op.free not in g.defaults:                       # this drawing does not use it (a cell's upright form)
            continue
        measure = op.measure
        if op.hold:
            held = _engaged(spec, k, ratio, p, ot, ob, overrides, width)
            if held is not None:
                measure, target = _counter_area, held
        if measure(g) >= target - 1e-6:
            continue
        a0 = a = g.defaults[op.free]
        b = op.limit(p)
        for _ in range(24):  # bisection: a is too closed, b assumed open enough
            mid = (a + b) / 2
            trial = _build(spec, p, ot, ob, {**overrides, op.free: mid}, width)
            if measure(trial) >= target:
                b = mid
            else:
                a = mid
        if nesting is not None:
            free = op.free
            b = nesting.clamp(lambda v: _build(spec, p, ot, ob, {**overrides, free: v}, width), a0, b)
        overrides[op.free] = b
        g = _build(spec, p, ot, ob, overrides, width)
    return g, overrides


NEST = os.environ.get('ARRIS_NEST', '0') == '1'   # a white-keeping rule never puts a counter outside its lighter
                                                  # anchor's (_Nesting). Off while it is proved on a test set:
                                                  # ARRIS_NEST=1, with ARRIS_CACHE= (the cache keys on the code,
                                                  # not this), draws with it
NEST_TOL = 0.5        # font units: the white a rule leaves outside the lighter counters, over their length, it may


def _white(rings):
    """The counters of a drawing's rings, as one shape."""
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    from .geom import rings_to_shapely
    poly = rings_to_shapely(rings)
    return unary_union([Polygon(h) for part in getattr(poly, 'geoms', [poly]) for h in part.interiors])


def _raw_rings(g):
    """g's ink before the optical warp (its drawing's own frame)."""
    warp = getattr(g, 'warp', None)
    g.warp = None
    try:
        return g.outline(record=False)[0]
    finally:
        g.warp = warp


_NEST_REF: dict = {}


class _Nesting:
    """The white a rule may leave at p: inside the counters of p's lighter
    anchor (the next lighter named weight of its cut, drawn by the same
    rules, so down to the Regular), moved onto p's drawing by the
    translation that leaves least of the lighter ink outside p's. Stack a
    glyph's weights and its white only tapers: a counter at a heavier
    weight lies inside the one at a lighter weight, never growing, never
    moving outward. A rule that keeps white (an opening's free variable,
    the closed-counter thinning) goes only as far as that allows: 1.007's
    held a counter to a share of a stem that kept growing (the italic k's
    loop dropped and its counter grew from Bold to 875; the Q's tail
    swung out and its counter opened to a P)."""

    def __init__(self, ref_white, shift):
        self.ref = ref_white
        self.shift = shift

    @classmethod
    def at(cls, name, g, p, ot, ob, width):
        if not NEST or not p.floor or p.sv <= _regular_sv(p) or not g.strokes or g.extra:
            return None
        lighter = _lighter(p)
        if not lighter:
            return None
        q = lighter[-1]
        key = (name, q, ot, ob, width)
        if key not in _NEST_REF:
            from .geom import rings_to_shapely
            h = draw(name, q, ot, ob, width)
            rings = _raw_rings(h)
            _NEST_REF[key] = (rings_to_shapely(rings), _white(rings), h.W)
        ink_q, white_q, w_q = _NEST_REF[key]
        if white_q.is_empty:
            return None
        from scipy.optimize import minimize
        from shapely import affinity
        from .geom import rings_to_shapely
        here = rings_to_shapely(_raw_rings(g))

        def outside(t):
            return affinity.translate(ink_q, t[0], t[1]).difference(here).area
        starts = [(0.0, 0.0), ((g.W - w_q) / 2, 0.0), (g.W - w_q, 0.0)]
        best = min(starts, key=outside)
        res = minimize(outside, best, method='Nelder-Mead',
                       options={'xatol': 0.1, 'fatol': 0.5, 'maxiter': 120,
                                'initial_simplex': [best, (best[0] + 3, best[1]), (best[0], best[1] + 3)]})
        t = (float(res.x[0]), float(res.x[1])) if res.fun < outside(best) else best
        return cls(affinity.translate(white_q, t[0], t[1]), t)

    def spill(self, h) -> float:
        """The white of the drawing h outside the lighter counters, over the
        length of its counters (font units)."""
        white = _white(_raw_rings(h))
        if white.is_empty:
            return 0.0
        return white.difference(self.ref).area / max(white.length, 1.0)

    def clamp(self, build, a, b):
        """The furthest a free variable goes from a (the drawing as it is)
        toward b (what the rule asked) without its counters reaching further
        outside the lighter ones than the drawing already does. (Where the
        drawing itself lies a little outside them, the e at Black on the
        heavy grade, a rule that may not act at all left its bar at full
        weight and the bar's end came out past the bowl.)"""
        allow = self.spill(build(a)) + NEST_TOL
        if self.spill(build(b)) <= allow:
            return b
        lo, hi = a, b
        for _ in range(8):                                  # to a 256th of the way
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if self.spill(build(mid)) <= allow else (lo, mid)
        return lo


# Arris Mono past Bold: a glyph whose closed counters would shut in the cell (too many strokes for its
# ten modules at Black: Æ Œ æ œ Ǆ Ф ⅅ ℙ ↀ ⌘ ...) stops getting heavier at the weight where they start to:
# the letter unchanged, drawn as at that weight from there to Black (docs/research/mono-cell.md). It shuts
# where its tightest closed counter falls under 0.6 of the Bold's and under a quarter of the stem, where it
# loses a counter and white with it, or where its counters keep under 0.35 of the Bold's white (Ф's bowls
# merging into a lozenge with two slits); a form that drops strokes by design at Black (₩ ₦ with one bar)
# gains white and is left alone. The weight is found once a cut, so ExtraBold is never heavier than Black.
MONO_HOLD = 700.0
_MONO_HELD: dict = {}


def _counters(g):
    """(count, total area, tightest: the widest circle inside the narrowest) of a drawing's closed counters."""
    import shapely
    from shapely.geometry import Polygon
    from .geom import rings_to_shapely
    ink = rings_to_shapely(g.rings())
    holes = [Polygon(r) for poly in getattr(ink, 'geoms', [ink]) if poly.geom_type == 'Polygon'
             for r in poly.interiors]
    holes = [h for h in holes if h.area >= 1.0]
    tight = min((shapely.maximum_inscribed_circle(h, tolerance=1.0).length for h in holes), default=None)
    return len(holes), sum(h.area for h in holes), tight


def _shuts(c, ref, sv) -> bool:
    n_p, a_p, t_p = c
    n_q, a_q, t_q = ref
    return (t_p is not None and t_q is not None and t_p < 0.6 * t_q and t_p < 0.25 * sv) or (n_p < n_q and a_p < a_q) \
        or (n_p and a_q and a_p < 0.35 * a_q)


def _mono_held(name, p, ot, ob, width):
    """The parameters to draw a Mono glyph at: its own, or those of the weight where its counters start to
    shut in the cell, past it (MONO_HOLD)."""
    if not p.mono:
        return p
    cut = _cut(p)
    if cut is None or cut[0] <= MONO_HOLD:
        return p
    w, at = cut
    key = (name, at(MONO_HOLD), ot, ob, width)
    if key not in _MONO_HELD:
        _MONO_HELD[key] = None                              # while it is found, a drawing that asks again (a rule's
        with _as_own():                                     # reference at Black) is drawn as it is
            ref = _counters(_draw(name, at(MONO_HOLD), ot, ob, width))

            def shut(w_):
                q = at(w_)
                return _shuts(_counters(_draw(name, q, ot, ob, width)), ref, q.sv)
            held = None
            if shut(900.0):
                lo, hi = MONO_HOLD, 900.0
                for _ in range(7):                          # to under 2 of weight
                    mid = (lo + hi) / 2
                    lo, hi = (lo, mid) if shut(mid) else (mid, hi)
                held = lo
        _MONO_HELD[key] = held
    held = _MONO_HELD[key]
    return p if held is None or w <= held else at(held)


TRACE: list = []   # open sets that collect the name of every glyph drawn while they are open (italic_forms.cursive_set)


def draw(name: str, p: Params, ot: float = 0.0, ob: float = 0.0, width: float | None = None) -> Glyph:
    for t in TRACE:
        t.add(name)
    return _draw(name, _mono_held(name, p, ot, ob, width), ot, ob, width)


def drawn_spec(name: str, p: Params) -> Spec:
    """The drawing ``name`` gets at ``p``: where the font slants and has an
    italic drawing of it (n.ital), that one replaces the upright one. A
    second form (second_form) is its glyph's drawing, pinned."""
    if p.slant and not p.plain and f'{name}.ital' in REGISTRY:
        return REGISTRY[f'{name}.ital']
    if name not in REGISTRY:
        base, _, free = name.rpartition('.')
        if base in REGISTRY:
            spec = drawn_spec(base, p)
            for sq in spec.squint:
                if sq.form and sq.free == free:
                    return _second_spec(spec, sq, p)
    return REGISTRY[name]


def pinned(fn: Callable, free: str, v: float) -> Callable:
    """The drawing with its free variable held at v."""
    def f(g):
        g.overrides[free] = v
        return fn(g)
    f.__module__, f.__name__ = fn.__module__, getattr(fn, '__name__', f.__name__)
    return f


def second_form(name: str, free: str) -> str:
    """The name of a glyph's second form (Squint.form) as a glyph of its
    own: dollar.stem, and dollar.stem.ital for an italic drawing."""
    root = name.removesuffix('.ital')
    return f'{root}.{free}' + name[len(root):]


_SECOND: dict = {}


def _second_spec(spec: Spec, sq: Squint, p: Params) -> Spec:
    """A glyph's second form as a glyph of its own: its drawing pinned to
    that form, the rule that chose it gone. A form is measured against its
    own Regular: the closed counters its horizontals thin for, the white a
    symbol keeps, the topology the lock holds, the lightening a heavier
    weight keeps from a lighter. The variable font carries the two forms
    as two glyphs (arris.vf.forms) and always drew them so; the static
    fonts measured the second against the first's Regular, and the dollar,
    which with stubs for a stem is the S and has the S's counters, not the
    four its stem cuts, was lightened as far as the rules go for whites it
    no longer had: bars of 96 units at Black on an S of 160, a fifth
    lighter at 690 than at 680."""
    key = (spec.name, sq.free)
    if key not in _SECOND:
        _SECOND[key] = replace(spec, name=second_form(spec.name, sq.free), unicode=None,
                               fn=pinned(spec.fn, sq.free, sq.limit(p)),
                               squint=tuple(q for q in spec.squint if q is not sq))
    return _SECOND[key]


def _draw(name: str, p: Params, ot: float = 0.0, ob: float = 0.0, width: float | None = None) -> Glyph:
    spec = drawn_spec(name, p)
    g, overrides = _opened(spec, p, ot, ob, width)
    nesting = _Nesting.at(name, g, p, ot, ob, width)
    auto = _auto_counters(spec)
    if any(op.hold for op in spec.openings):
        auto = None             # an opening that holds is the counter's rule (thinning on its own share grew it again)
    if any(op.own and op.free in g.defaults for op in spec.openings):
        auto = None             # the drawing thins what bounds its counter, and only that (the cursive e's top and bar)
    if auto is not None:
        n, ratio = auto
        share = min(ratio, AUTO_SHARE)
        target = share * p.sv

        def measure(h):
            return _counter_white(h, n)
        if measure(g) < target - 1e-6:
            a, b = 1.0, AUTO_MIN
            for _ in range(24):
                mid = (a + b) / 2
                trial = _build(spec, p, ot, ob, {**overrides, 'sh_auto': mid}, width)
                if measure(trial) >= target:
                    b = mid
                else:
                    a = mid
            if nesting is not None:
                b = nesting.clamp(lambda v: _build(spec, p, ot, ob, {**overrides, 'sh_auto': v}, width), 1.0, b)
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
            if nesting is not None:
                b = nesting.clamp(lambda v: _build(spec, p, ot, ob, {**overrides, 'sh_auto': v}, width),
                                  overrides.get('sh_auto', 1.0), b)
            trial = _build(spec, p, ot, ob, {**overrides, 'sh_auto': b}, width)
            if len(trial.rings()) == len(g.rings()):         # it thins; it never changes the topology
                overrides['sh_auto'] = b                      # (the variable font's masters must agree)
                g = trial
    # the horizontals thinned at least as much as at the next lighter named
    # weight of the same cut (as the lock below, and the squint rule), whose
    # own thinning keeps to the one below it, and so down to the Regular:
    # solved weight by weight, the thinning went back and forth in a score of
    # glyphs (@ & § ¥), and the variable font pulsed between its masters
    if auto is not None and p.sv > _regular_sv(p):
        lighter = _lighter(p)
        if lighter:
            k_here = overrides.get('sh_auto', 1.0)
            k_min = min(k_here, _anchor(name, lighter[-1], ot, ob, width)[1].get('sh_auto', 1.0))
            if k_min < k_here - 1e-9:
                trial = _build(spec, p, ot, ob, {**overrides, 'sh_auto': k_min}, width)
                if _topology(trial) in (_topology_reference(spec, p), _topology(g)):
                    overrides['sh_auto'] = k_min
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
        if sq.form:
            # a choice of form keeps the next lighter weight's where that is
            # further toward the limit: the lighter weights are read here with
            # this weight's own openings (the ¢'s slash, thinned more at 850
            # than at 800), and the ¢ took stubs at 800, its stem through at
            # 850 and stubs at 900
            lighter = _lighter(p)
            if lighter:
                a0 = g.defaults[sq.free]
                prev = _anchor(name, lighter[-1], ot, ob, width)[1].get(sq.free)
                if prev is not None and (v is None or abs(prev - a0) > abs(v - a0)):
                    v = prev
            a0, lim = g.defaults[sq.free], sq.limit(p)
            if v is not None and (v - (a0 + lim) / 2) * (lim - a0) > 0:
                # the second form is a drawing of its own, held to its own
                # Regular by every rule (_second_spec), as the variable font
                # carries it
                return _draw(second_form(name, sq.free), p, ot, ob, width)
        if v is not None:
            overrides[sq.free] = v
            g = _build(spec, p, ot, ob, overrides, width)
    # (the heritage drawing is never lightened; composites rely on their parts' own rules)
    if _is_symbol(spec) and p.floor and g.strokes and not g.extra:
        want = _white_reference(spec, p)
        if want and white_features(g.rings(), p, g) < want:
            a, b = 1.0, LIGHTEN_MIN
            lo = _build(spec, _lightened(p, b), ot, ob, overrides, width)
            if white_features(lo.rings(), _lightened(p, b), lo) >= want:
                for _ in range(16):
                    mid = (a + b) / 2
                    trial = _build(spec, _lightened(p, mid), ot, ob, overrides, width)
                    if white_features(trial.rings(), _lightened(p, mid), trial) >= want:
                        b = mid
                    else:
                        a = mid
            if nesting is not None:
                b = nesting.clamp(lambda v: _build(spec, _lightened(p, v), ot, ob, overrides, width), 1.0, b)
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
    # Lightened at least as much as the next lighter named weight of the same
    # cut, whose own lightening keeps to the one below it, and so down to the
    # Regular (the squint rule is monotone the same way: _squint_monotone). The lock
    # decided weight by weight on a yes-or-no test, so $ lightened to 0.8 from
    # Bold to 850 and not at all at 875, where its topology happened to match
    # again, and the variable font pulsed a fifth of a stroke between its
    # masters there. A heavier weight now keeps the lighter weights' lightening
    # unless that would change its topology.
    if p.floor and g.strokes and not g.extra and p.sv > _regular_sv(p):
        lighter = _lighter(p)
        if lighter:
            k_here = getattr(g, 'lightened', 1.0)
            k_min = min(k_here, _anchor(name, lighter[-1], ot, ob, width)[0])
            if k_min < k_here - 1e-9:
                trial = settled(k_min)
                # taken unless it changes the topology for the worse: one
                # the lock could not restore ($ at 875, its counters gone
                # lightened or not) stays as wrong, and continuous. (Not a
                # little lighter still: past the lighter weight's share the
                # lightening differed between the watch's masters and the
                # places between them, which the variable font cannot carry,
                # the italic @ twelve units off at Black on the half watch.)
                if _topology(trial) in (_topology_reference(spec, p), _topology(g)):
                    g = trial
                    g.lightened = k_min
    # Between the watch's ends the lightening is the blend of the ends'.
    # The variable font draws the watch axis from its ends alone (a glyph's
    # finer grid rarely adds a plane on it), so a lightening that came and
    # went between them (the lock or the white rule engaging at WTCH 25 or
    # 50 and not at 0 or 100, in some sixty glyphs) left the font's outline
    # off the drawing there, and the italic @ lost its finer grid to it.
    watch = 1.0 - p.optical
    if 1e-6 < watch < 1.0 - 1e-6 and p.floor and g.strokes and not g.extra:
        ends = [_at_watch(p, w_) for w_ in (0.0, 1.0)]
        if None not in ends:
            k0, k1 = (_anchor(name, q, ot, ob, width)[0] for q in ends)
            k = k0 + (k1 - k0) * watch
            if abs(k - getattr(g, 'lightened', 1.0)) > 1e-4:
                g = settled(k)
                g.lightened = k
    # Mono's outline lock: in the cell a crowded glyph can fold, cross or
    # pinch where its strokes meet, a fault the topology check names that
    # the lock above (parts and counters) does not see: the fractions at
    # SemiBold and Bold, ⅷ, ↂ, ∛, the italic's ₯ Ɲ ↭, ‱ whose rings touch
    # once rounded. As the font carries it, a Mono glyph with such a fault
    # lightens its strokes together, as little as clears it, at most to
    # LOCK_MIN; one it cannot clear stays as drawn, for the check to name.
    # A glyph as a font carries it: not a part drawn inside another (a
    # composite is locked whole), not a terminal cell (never slanted).
    if p.mono and _DEPTH[0] == 0 and _cell_kind(spec) and not spec.cell and _flawed(g, p):
        k0 = getattr(g, 'lightened', 1.0)
        k = 1.0
        while k - FLAW_STEP >= LOCK_MIN - 1e-9:
            k -= FLAW_STEP
            h = settled(k0 * k)
            if not _flawed(h, p):
                g = h
                g.lightened = k0 * k
                break
    return g


FLAW_STEP = 0.02    # the outline lock's step of lightening
FLAW_CROSS = 1.0    # a crossing smaller than this (units) no size shows: the outline lock lets it be


def _flawed(g, p: Params) -> bool:
    """Whether a Mono drawing, as the font will carry it (placed in its
    cell, in whole units, curved and sheared in the italic), has a fault the
    topology check names: a crossing of a unit or more, contours that meet,
    a fold, a pinch. Tiny edges and sub-unit crossings do not count."""
    from .topology import faults
    dx = (p.fig_adv - g.W) / 2
    if p.slant:
        from .italic import outline
        rings, rec = g.outline(record=True)
        contours = [[(round(x + dx), round(y), on) for x, y, on in c] for c in outline(rings, rec, p)]
    else:
        contours = [[(round(q[0] + dx), round(q[1]), True) for q in r] for r in g.rings()]
    return any(f.kind not in ('tiny', 'cross') or f.size >= FLAW_CROSS for f in faults(contours, p.c, bool(p.slant)))


_ANCHOR: dict = {}


def _anchor(name, p, ot, ob, width) -> tuple:
    """(how much a glyph's strokes are lightened, its free variables) as
    drawn at p: what a heavier weight of the same cut keeps to. Remembered
    in this process and in the drawing cache (arris.cache), so the processes
    that build the weights side by side each draw a glyph's lighter weights
    once between them, not each for itself."""
    key = (name, p, ot, ob, width)
    if key not in _ANCHOR:
        import json
        con = cache.db()
        k = cache.key('anchor', key) if con is not None else None
        row = con.execute('SELECT e, v FROM anchor WHERE k = ?', (k,)).fetchone() if con is not None else None
        if row is not None and cache.valid(row[0]):
            light, ov = json.loads(row[1])
        else:
            with cache.using() as mods, _as_own():          # (the lighter weight as a glyph of its own, whoever asks)
                g = draw(name, p, ot, ob, width)
            light, ov = getattr(g, 'lightened', 1.0), dict(getattr(g, 'overrides', {}))
            if con is not None:
                con.execute('INSERT OR REPLACE INTO anchor VALUES (?, ?, ?)', (k, cache.stamp(mods), json.dumps([light, ov])))
        _ANCHOR[key] = (light, ov)
    return _ANCHOR[key]
