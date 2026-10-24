"""Design parameters.

Every outline is a function of these numbers. ``HERITAGE`` reproduces the
watch's Chamfer figures in module units (a module is one pixel of the 9x12
zone masters). Font instances use 60 units per module, so the cap height is
720 units of a 1000-unit em and the heritage Bold stem is 120.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, replace

SQRT2 = math.sqrt(2)


@dataclass(frozen=True)
class Params:
    m: float = 60.0            # module
    cap: float = 720.0         # cap and figure height (12 modules)
    xh: float = 540.0          # x-height (9 modules)
    asc: float = 780.0         # ascender of b d h k l (13 modules, a module above the caps)
    desc: float = 180.0        # descender depth of g j p q y (3 modules)
    sv: float = 120.0          # vertical stem
    sh: float = 120.0          # horizontal stroke
    sd: float = 120.0 / SQRT2  # 45-degree stroke, measured perpendicular
    ss: float = 120.0 * 2 / math.sqrt(5)  # 2:1 stroke, measured perpendicular
    leg: float = 90.0          # bowl corner: centreline chamfer leg
    c: float = 30.0            # edge break on every right-angled corner
    fig_w: float = 540.0       # tabular figure body (9 modules)
    fig_adv: float = 600.0     # tabular figure advance (10 modules)
    mono: bool = False         # monospaced: every glyph on the figures' pitch
    grade_k: float = 1.0       # grade: strokes scaled by this, widths and spacing untouched
    slant: float = 0.0         # italic: tan of the slant (outlines are sheared when built)
    floor: float = 0.0         # no stroke drawn thinner (instances.stroke_floor); 0 for the heritage
    raw: tuple | None = None   # (sv, sh, sd, ss) before the floor, where it raised them
    optical: float = 1.0       # share of the optical corrections (draw.OPTICAL): 1 measured optics, 0 the watch's own drawing

    def with_(self, **kw) -> 'Params':
        """These parameters with some changed. Strokes never drop below the
        floor: every derived set (small figures, small capitals, the letters
        inside a ring, a grade) is clamped as it is made, so the geometry
        that places strokes and the strokes themselves agree."""
        strokes = ('sv', 'sh', 'sd', 'ss')
        before = dict(zip(strokes, self.raw)) if self.raw else {f: getattr(self, f) for f in strokes}
        before.update({f: kw[f] for f in strokes if f in kw})
        p = replace(self, **kw, raw=None)
        if p.floor and min(before.values()) < p.floor:
            p = replace(p, raw=tuple(before[f] for f in strokes),
                        **{f: max(before[f], p.floor) for f in strokes})
        else:
            p = replace(p, **before)
        return p

    def dot(self) -> float:
        """A dot's size (a period, a tittle, a dieresis, a comma's head): the
        stem's square, but never less than twice the stroke floor, so dots
        still read at the lightest weights. In the monospaced cut, where code
        turns on . , : ; and their dots sit alone in a cell, they are half as
        big again at Regular, easing to a fifth more at Black (a dot looks
        lighter than a stroke of its width)."""
        s = max(self.sv, 2 * self.floor)
        if self.mono:
            heavy = min(max((self.sv - 120.0) / 55.0, 0.0), 1.0)
            s = max(self.sv * (1.5 - 0.3 * heavy), 2 * self.floor)
        return s

    def scaled(self, k: float) -> 'Params':
        keep = ('mono', 'grade_k', 'slant', 'raw')
        out = Params(**{f: (getattr(self, f) * k if f not in keep else getattr(self, f)) for f in self.__dataclass_fields__})
        return replace(out, raw=tuple(v * k for v in self.raw) if self.raw else None)

    def ungraded(self) -> 'Params':
        k = self.grade_k
        if k == 1.0:
            return self
        sv, sh, sd, ss = self.raw if self.raw else (self.sv, self.sh, self.sd, self.ss)
        return self.with_(sv=sv / k, sh=sh / k, sd=sd / k, ss=ss / k, c=self.c / k, grade_k=1.0)


def outer_leg(p: Params, sv: float | None = None, sh: float | None = None) -> float:
    """Outer chamfer leg of a bowl corner between a vertical and a horizontal."""
    sv = p.sv if sv is None else sv
    sh = p.sh if sh is None else sh
    return p.leg + (sv + sh) / 2 - p.sd / SQRT2


def inner_leg(p: Params, sh: float | None = None) -> float:
    sh = p.sh if sh is None else sh
    return max(p.c, p.leg - (p.sv + sh) / 2 + p.sd / SQRT2)


# The watch figures, in modules: two-module strokes; every diagonal as wide
# across as a stem (so 45-degree strokes are only 1/sqrt2 of it), 1.5-module
# bowl legs, half-module edge breaks.
HERITAGE = Params(m=1, cap=12, xh=9, asc=13, desc=3, sv=2, sh=2, sd=SQRT2,
                  ss=4 / math.sqrt(5), leg=1.5, c=0.5, fig_w=9, fig_adv=10, optical=0.0)
HERITAGE_UNITS = HERITAGE.scaled(60)
