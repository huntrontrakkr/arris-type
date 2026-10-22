"""Parameters as functions of the design axes.

Axes:
  wght  100-900  stem weight; SemiBold (600) is the watch's heritage weight
  GRAD  -50-150  grade: thicker or thinner strokes in the same widths and
                 spacing, for light-on-dark text (see docs/DESIGN.md)

Everything optical (stroke ratios by direction, edge breaks, overshoots) is
derived here from the stem and the correction constants in ``OPTICS``, which
docs/research/ explains.
"""
from __future__ import annotations

from dataclasses import dataclass

from .params import SQRT2, Params

# Vertical stem (font units, 1000 UPM, cap height 720) at the named weights.
# Stem / cap: Regular 0.125, SemiBold 0.167 (the watch's figures), Bold 0.194,
# Black 0.243; measured neutral sans faces run 0.128 Regular and 0.227 Bold,
# chamfered ones 0.122 and 0.197 (docs/research/reference-fonts.md).
STEMS = {100: 24, 200: 44, 300: 66, 400: 90, 500: 105, 600: 120, 700: 140, 800: 158, 900: 175}
NAMES = {100: 'Thin', 200: 'ExtraLight', 300: 'Light', 400: 'Regular', 500: 'Medium',
         600: 'SemiBold', 700: 'Bold', 800: 'ExtraBold', 900: 'Black'}


@dataclass(frozen=True)
class Optics:
    h_light: float = 1.0       # horizontal / vertical stroke at Thin ...
    h_heavy: float = 1.0       # ... and at Black
    d_light: float = 1 / SQRT2  # 45-degree stroke (perpendicular) / vertical, Thin ...
    d_heavy: float = 1 / SQRT2  # ... and Black
    s_light: float = 2 / 5 ** 0.5  # 2:1 stroke (perpendicular) / vertical, Thin ...
    s_heavy: float = 2 / 5 ** 0.5  # ... and Black
    c_ratio: float = 0.25      # edge break leg / vertical stem
    leg: float = 90.0          # bowl centreline chamfer leg (1.5 modules)

    @staticmethod
    def _t(sv):
        return min(max((sv - STEMS[100]) / (STEMS[900] - STEMS[100]), 0.0), 1.0)

    def h_ratio(self, sv: float) -> float:
        return self.h_light + (self.h_heavy - self.h_light) * self._t(sv)

    def d_ratio(self, sv: float) -> float:
        return self.d_light + (self.d_heavy - self.d_light) * self._t(sv)

    def s_ratio(self, sv: float) -> float:
        return self.s_light + (self.s_heavy - self.s_light) * self._t(sv)


# The watch's pixel logic: every diagonal as wide across as a stem.
HERITAGE_OPTICS = Optics()
# Horizontals thin from 0.90 of the stem at Thin to 0.85 at Black (measured:
# 0.87-0.90 Regular, 0.85-0.87 Bold). 45-degree strokes, diagonals and bowl
# corners alike, run 0.94 at light weights (measured diagonals 0.94-0.97,
# chamfer corners close to the mean of side and top) and thin to 0.84 at
# Black, as heavy faces do, so tight figures like the 4 keep their counters.
OPTICS = Optics(h_light=0.90, h_heavy=0.85, d_light=0.94, d_heavy=0.84, s_light=0.96, s_heavy=0.88)


def stem(wght: float) -> float:
    ks = sorted(STEMS)
    if wght <= ks[0]:
        return STEMS[ks[0]]
    for a, b in zip(ks, ks[1:]):
        if wght <= b:
            t = (wght - a) / (b - a)
            return STEMS[a] + (STEMS[b] - STEMS[a]) * t
    return STEMS[ks[-1]]


FIG_GROWTH = 1.5  # figure width gained per unit of stem
GRAD_UNIT = 0.25   # stem units per GRAD unit (GRAD 100 adds 25 units)


def params(wght: float = 600, grad: float = 0, optics: Optics = OPTICS, base: Params = Params()) -> Params:
    sv = stem(wght) + grad * GRAD_UNIT
    # Figures stay tabular within a weight but widen with it, so heavier
    # strokes do not eat the counters whole; the watch weight keeps 540.
    d = stem(wght) - 120.0
    fig_w = base.fig_w + (FIG_GROWTH if d > 0 else FIG_GROWTH / 2) * d
    return base.with_(fig_w=fig_w, fig_adv=fig_w + (base.fig_adv - base.fig_w), sv=sv, sh=sv * optics.h_ratio(sv), sd=sv * optics.d_ratio(sv),
                      ss=sv * optics.s_ratio(sv), c=sv * optics.c_ratio, leg=optics.leg)
