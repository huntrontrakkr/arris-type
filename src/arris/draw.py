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
class Spec:
    name: str
    unicode: int | None
    fn: Callable
    width: Callable[[Params], float]   # body width
    kind: str = 'fig'                  # spacing class


def glyph(name: str, char: str | None, width, kind='fig'):
    def deco(fn):
        w = width if callable(width) else (lambda p, w=width: getattr(p, w))
        REGISTRY[name] = Spec(name, ord(char) if char else None, fn, w, kind)
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
    clip: tuple[float, float, float, float] | None = None   # keep ink inside (x0, y0, x1, y1)

    def stroke(self, *pts, closed=False, start='flat', end='flat'):
        nodes = []
        for q in pts:
            if isinstance(q, tuple) and q and q[0] == 'bowl':
                _, x, y, leg = q
                nodes.append(Node(x, y, self.p.leg if leg is None else leg))
            else:
                nodes.append(Node(q[0], q[1]))
        self.strokes.append(Stroke(tuple(nodes), closed, start, end))
        return self

    def rings(self):
        p = self.p
        box = None
        if self.clip is not None:
            from shapely.geometry import box as _box
            box = _box(*self.clip)
        return ink(self.strokes, Thickness(p.sv, p.sh, p.sd), p.c, self.extra, box)


def draw(name: str, p: Params, ot: float = 0.0, ob: float = 0.0) -> Glyph:
    spec = REGISTRY[name]
    g = Glyph(p, name, ot=ot, ob=ob, W=spec.width(p))
    spec.fn(g)
    return g
