"""Parameters as functions of the design axes.

Axes:
  wght  100-900  stem weight; Bold (700) is the watch's heritage weight
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
STEMS = {100: 24, 200: 40, 300: 58, 400: 80, 500: 96, 600: 108, 700: 120, 800: 140, 900: 160}
NAMES = {100: 'Thin', 200: 'ExtraLight', 300: 'Light', 400: 'Regular', 500: 'Medium',
         600: 'SemiBold', 700: 'Bold', 800: 'ExtraBold', 900: 'Black'}


@dataclass(frozen=True)
class Optics:
    h_ratio: float = 1.0       # horizontal / vertical stroke
    d_ratio: float = 1 / SQRT2  # 45-degree stroke (perpendicular) / vertical
    c_ratio: float = 0.25      # edge break leg / vertical stem
    leg: float = 90.0          # bowl centreline chamfer leg (1.5 modules)


HERITAGE_OPTICS = Optics()
OPTICS = Optics(h_ratio=0.92, d_ratio=0.94)   # provisional; see docs/research


def stem(wght: float) -> float:
    ks = sorted(STEMS)
    if wght <= ks[0]:
        return STEMS[ks[0]]
    for a, b in zip(ks, ks[1:]):
        if wght <= b:
            t = (wght - a) / (b - a)
            return STEMS[a] + (STEMS[b] - STEMS[a]) * t
    return STEMS[ks[-1]]


GRAD_UNIT = 0.25   # stem units per GRAD unit (GRAD 100 adds 25 units)


def params(wght: float = 700, grad: float = 0, optics: Optics = OPTICS, base: Params = Params()) -> Params:
    sv = stem(wght) + grad * GRAD_UNIT
    return base.with_(sv=sv, sh=sv * optics.h_ratio, sd=sv * optics.d_ratio,
                      c=sv * optics.c_ratio, leg=optics.leg)
