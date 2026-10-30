"""Parameters as functions of the design axes.

Axes:
  wght  100-900  stem weight; SemiBold (600) is the watch's heritage weight
  GRAD  -100-100 grade: strokes up to a fifth thinner or thicker in the same
                 widths and spacing, for light-on-dark text (docs/DESIGN.md);
                 a positive grade fades out toward Black (GRAD_TAPER)

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
GRAD_SHARE = 0.002  # grade: GRAD 100 thickens strokes by a fifth, -100 thins them by a fifth
# A positive grade fades out from SemiBold to Black: at Black it adds nothing,
# so the heaviest stroke the font draws is Black's own. Past Black's stroke the
# drawings had no room: with a fifth more, some three hundred glyphs (? ‡ $ €
# among them) fused, kinked or lost a terminal between 750 and 900, and the
# variable font smeared each change across the weights between its masters.
GRAD_TAPER = (600.0, 900.0)


def grade_k(wght: float, grad: float) -> float:
    """What a grade scales the strokes by, at a weight."""
    if grad > 0:
        a, b = GRAD_TAPER
        grad *= min(1.0, max(0.0, (b - wght) / (b - a)))
    return 1 + grad * GRAD_SHARE


def params(wght: float = 600, grad: float = 0, optics: Optics = OPTICS, base: Params = Params(),
           watch: float = 0.0) -> Params:
    """Parameters for a weight, a grade, and a balance between the measured
    optics (watch = 0) and the watch's own proportions (watch = 1)."""
    if watch:
        a, b = optics, HERITAGE_OPTICS
        mix = lambda x, y: x + (y - x) * watch
        optics = Optics(h_light=mix(a.h_light, b.h_light), h_heavy=mix(a.h_heavy, b.h_heavy),
                        d_light=mix(a.d_light, b.d_light), d_heavy=mix(a.d_heavy, b.d_heavy),
                        s_light=mix(a.s_light, b.s_light), s_heavy=mix(a.s_heavy, b.s_heavy),
                        c_ratio=mix(a.c_ratio, b.c_ratio), leg=mix(a.leg, b.leg))
    p = _params(wght, optics, base)
    if grad:
        k = grade_k(wght, grad)
        p = p.with_(sv=p.sv * k, sh=p.sh * k, sd=p.sd * k, ss=p.ss * k, c=p.c * k, grade_k=k, grad=grad)
    optical = 0.0 if optics == HERITAGE_OPTICS else 1.0 - watch
    return p.with_(floor=stroke_floor(base), optical=optical)


def _params(wght, optics, base):
    sv = stem(wght)
    # Figures stay tabular within a weight but widen with it, so heavier
    # strokes do not eat the counters whole; the watch weight keeps 540.
    d = stem(wght) - 120.0
    fig_w = base.fig_w + (FIG_GROWTH if d > 0 else FIG_GROWTH / 2) * d
    return base.with_(fig_w=fig_w, fig_adv=fig_w + (base.fig_adv - base.fig_w), sv=sv, sh=sv * optics.h_ratio(sv), sd=sv * optics.d_ratio(sv),
                      ss=sv * optics.s_ratio(sv), c=sv * optics.c_ratio, leg=optics.leg)



_FLOOR: dict = {}


def stroke_floor(base: Params = Params()) -> float:
    """The thinnest stroke the font draws, in font units: the Thin's own
    thinnest (its horizontal), with the measured optics. Nothing is drawn
    thinner, however it was derived (small figures, marks, the letters
    inside a ring, a negative grade, the watch's light diagonals): below it
    a stroke stops reading as the same pen (see geom.Thickness)."""
    key = id(base)
    if key not in _FLOOR:
        p = _params(100, OPTICS, base)
        _FLOOR[key] = min(p.sv, p.sh, p.sd, p.ss)
    return _FLOOR[key]
