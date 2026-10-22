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

    def with_(self, **kw) -> 'Params':
        return replace(self, **kw)

    def scaled(self, k: float) -> 'Params':
        keep = ('mono', 'grade_k', 'slant')
        return Params(**{f: (getattr(self, f) * k if f not in keep else getattr(self, f)) for f in self.__dataclass_fields__})

    def ungraded(self) -> 'Params':
        k = self.grade_k
        if k == 1.0:
            return self
        return self.with_(sv=self.sv / k, sh=self.sh / k, sd=self.sd / k, ss=self.ss / k, c=self.c / k, grade_k=1.0)


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
                  ss=4 / math.sqrt(5), leg=1.5, c=0.5, fig_w=9, fig_adv=10)
HERITAGE_UNITS = HERITAGE.scaled(60)
