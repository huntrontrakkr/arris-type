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


@dataclass
class Spec:
    name: str
    unicode: int | None
    fn: Callable
    width: Callable[[Params], float]   # body width
    kind: str = 'fig'                  # spacing class
    openings: tuple = ()


def glyph(name: str, char: str | None, width, kind='fig', openings=()):
    def deco(fn):
        w = width if callable(width) else (lambda p, w=width: getattr(p, w))
        REGISTRY[name] = Spec(name, ord(char) if char else None, fn, w, kind, tuple(openings))
        return fn
    return deco


def B(x, y, leg=None):
    """A bowl corner (leg None = the parameter default)."""
    return ('bowl', x, y, leg)


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
    clip: tuple[float, float, float, float] | None = None   # keep ink inside (x0, y0, x1, y1)
    overrides: dict = field(default_factory=dict)
    defaults: dict = field(default_factory=dict)
    parts: dict = field(default_factory=dict)        # name -> stroke indices
    defaults_used: dict = field(default_factory=dict)

    def free(self, name: str, default: float) -> float:
        """A free variable of the drawing (see Opening)."""
        self.defaults[name] = default
        return self.overrides.get(name, default)

    def part(self, name: str):
        """The ink of the named strokes, before the union and corner rule."""
        import shapely
        from .geom import stroke_polygon
        th = Thickness(self.p.sv, self.sh, self.p.sd, self.p.ss)
        return shapely.union_all([stroke_polygon(self.strokes[i], th, self.p.c) for i in self.parts[name]])

    def white_left(self, y: float, x: float) -> float:
        """Width of the white run leftward from x at height y."""
        from shapely.geometry import LineString
        from .geom import rings_to_shapely
        poly = rings_to_shapely(self.rings())
        cut = poly.intersection(LineString([(x - 1e4, y), (x - 1e-3, y)]))
        xs = [c[0] for gg in getattr(cut, 'geoms', [cut]) for c in getattr(gg, 'coords', [])]
        return (x - max(xs)) if xs else 1e4

    def stroke(self, *pts, closed=False, start='flat', end='flat', part=None):
        if part:
            self.parts.setdefault(part, []).append(len(self.strokes))
        nodes = []
        for q in pts:
            if isinstance(q, tuple) and q and q[0] == 'bowl':
                _, x, y, leg = q
                nodes.append(Node(x, y, self.p.leg if leg is None else leg))
            else:
                # (x, y) or (x, y, w): w is the thickness of the segment that follows
                nodes.append(Node(q[0], q[1], 0.0, q[2] if len(q) > 2 else None))
        self.strokes.append(Stroke(tuple(nodes), closed, start, end))
        return self

    def rings(self):
        p = self.p
        box = None
        if self.clip is not None:
            from shapely.geometry import box as _box
            box = _box(*self.clip)
        return ink(self.strokes, Thickness(p.sv, self.sh, p.sd, p.ss), p.c, self.extra, box)

    @property
    def sh(self) -> float:
        return self.p.sh * self.sh_k

    def stack(self, n: int, height: float, ratio: float = 0.9):
        """Thin the horizontals where n bars share ``height`` so that each
        counter between them stays at least ``ratio`` times a bar."""
        fit = height / (n + (n - 1) * ratio)
        self.sh_k = min(1.0, fit / self.p.sh)
        return self.sh


def _build(spec, p, ot, ob, overrides):
    g = Glyph(p, spec.name, ot=ot, ob=ob, W=spec.width(p), overrides=dict(overrides))
    spec.fn(g)
    return g


_RATIOS: dict = {}


def _heritage_ratio(spec, k):
    """An opening's white as a share of the stem in the watch's drawing."""
    key = (spec.name, k)
    if key not in _RATIOS:
        from .params import HERITAGE
        g = _build(spec, HERITAGE, 0.0, 0.0, {})
        _RATIOS[key] = spec.openings[k].measure(g) / HERITAGE.sv
    return _RATIOS[key]


def draw(name: str, p: Params, ot: float = 0.0, ob: float = 0.0) -> Glyph:
    spec = REGISTRY[name]
    overrides: dict = {}
    g = _build(spec, p, ot, ob, overrides)
    for k, op in enumerate(spec.openings):
        ratio = _heritage_ratio(spec, k)
        if op.max_ratio is not None:
            ratio = min(ratio, op.max_ratio)
        target = ratio * p.sv
        if op.measure(g) >= target - 1e-6:
            continue
        a, b = g.defaults[op.free], op.limit(p)
        for _ in range(40):  # bisection: a is too closed, b assumed open enough
            mid = (a + b) / 2
            trial = _build(spec, p, ot, ob, {**overrides, op.free: mid})
            if op.measure(trial) >= target:
                b = mid
            else:
                a = mid
        overrides[op.free] = b
        g = _build(spec, p, ot, ob, overrides)
    return g
