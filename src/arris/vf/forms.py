"""Forms: a glyph whose drawing chooses between two (a Squint rule with
form=True: ¢ $ stem or stubs) cannot interpolate from one to the other.
Each form becomes a glyph of its own, drawn in that form at every master,
and a designspace rule (GSUB feature variations, rvrn) swaps the second in
where the engine draws it: from the weight where it first does, in each
band of grade and watch (the choice is monotone in the weight: draw)."""
from __future__ import annotations

import dataclasses
from collections.abc import Callable
from typing import NamedTuple

from arris.draw import REGISTRY, Glyph, draw

from .space import DEFAULT, Place, params

GRAD_BANDS = [(-100, -75, -100), (-75, -25, -50), (-25, 25, 0), (25, 75, 50), (75, 100, 100)]
WTCH_BANDS = [(0, 25, 0), (25, 75, 50), (75, 100, 100)]


class Region(NamedTuple):
    """Where the second form is drawn: from this weight up, in a band of grade and watch."""
    wght: float
    grad_lo: float
    grad_hi: float
    wtch_lo: float
    wtch_hi: float


class Form(NamedTuple):
    alt: str                    # the second form's glyph
    regions: list[Region]


def _second(n: str, free: str, d: float, lim: float, loc: Place, italic: bool) -> bool:
    g = draw(n, params(loc, italic))
    v = g.overrides.get(free, d)
    return (v - (d + lim) / 2) * (lim - d) > 0


def _pinned(fn: Callable[[Glyph], object], free: str, v: float) -> Callable[[Glyph], object]:
    """The drawing with its free variable held at v."""
    def f(g: Glyph) -> object:
        g.overrides[free] = v
        return fn(g)
    f.__module__, f.__name__ = fn.__module__, getattr(fn, '__name__', f.__name__)
    return f


def install(names: list[str], italic: bool = False) -> tuple[list[str], dict[str, Form]]:
    """Every form among ``names`` as a glyph of its own: REGISTRY is
    changed in place (each form's drawing pinned to its form, the base
    glyph's to the first), and the second forms' names are added to the
    glyphs. (glyph -> its Form) says where the second form is drawn."""
    forms: dict[str, Form] = {}
    names = list(names)
    for n in list(names):
        spec = REGISTRY[n]
        for sq in spec.squint:
            if not sq.form:
                continue
            g0 = draw(n, params(DEFAULT, italic))
            d, lim = g0.defaults.get(sq.free), sq.limit(params(DEFAULT, italic))
            if d is None:
                continue
            regions = []
            for glo, ghi, gs in GRAD_BANDS:
                for tlo, thi, ts in WTCH_BANDS:
                    if not _second(n, sq.free, d, lim, (900, gs, ts), italic):
                        continue
                    lo, hi = 100.0, 900.0
                    if not _second(n, sq.free, d, lim, (lo, gs, ts), italic):
                        for _ in range(9):
                            mid = (lo + hi) / 2
                            lo, hi = (lo, mid) if _second(n, sq.free, d, lim, (mid, gs, ts), italic) else (mid, hi)
                        lo = hi
                    regions.append(Region(round(lo, 1), glo, ghi, tlo, thi))
            alt = f'{n}.{sq.free}'
            keep = tuple(q for q in spec.squint if q is not sq)
            for base in (n, f'{n}.ital'):
                if base in REGISTRY:
                    b = REGISTRY[base]
                    REGISTRY[base] = dataclasses.replace(b, fn=_pinned(b.fn, sq.free, d), squint=keep)
                    REGISTRY[base.replace(n, alt, 1)] = dataclasses.replace(
                        b, name=base.replace(n, alt, 1), unicode=None, fn=_pinned(b.fn, sq.free, lim), squint=keep)
            names.append(alt)
            forms[n] = Form(alt, regions)
    return names, forms
