"""Parameters as functions of the design axes.

Axes:
  wght  100-900  stem weight; SemiBold (600) is the watch's heritage weight
  GRAD  -100-100 grade: strokes up to a fifth thinner or thicker in the same
                 widths and spacing, for light-on-dark text (docs/DESIGN.md);
                 a positive grade fades out toward Black (GRAD_TAPER)
  WTCH  0-100    the watch's stroke balance (docs/DESIGN.md); past Bold it
                 eases off toward Black (WATCH_TAPER)

Everything optical (stroke ratios by direction, edge breaks, overshoots) is
derived here from the stem and the correction constants in ``OPTICS``, which
docs/research/ explains.
"""
from __future__ import annotations

from dataclasses import dataclass

from .params import SQRT2, Params, descender_line

# Vertical stem (font units, 1000 UPM, cap height 720) at the named weights.
# Stem / cap: Regular 0.125, SemiBold 0.167 (the watch's figures), Bold 0.194,
# Black 0.243; measured neutral sans faces run 0.128 Regular and 0.227 Bold,
# chamfered ones 0.122 and 0.197 (docs/research/reference-fonts.md).
# Arris Mono ships Fira Code's six weights, Light to Bold with Fira's Retina (450, a Regular a little
# heavier for light text on high-density screens), each with its italic (the owner, 2026-11-02). The
# engine still draws Mono at any weight; the build makes these.
MONO_NAMES = {300: 'Light', 400: 'Regular', 450: 'Retina', 500: 'Medium', 600: 'SemiBold', 700: 'Bold'}
MONO_WEIGHTS = tuple(MONO_NAMES)
# Arris Mono Narrow draws each weight from Regular up this much lighter than its name says: in a
# terminal, light on dark, its Regular then puts as much ink in a cell as Fira Code's Regular (0.33 of
# the x-height band against Fira's 0.32; drawn at 400, 0.37). Its Light keeps its own weight: at 14 px
# a lighter m's middle stem and the periods already go grey (the owner, 2026-11-05).
NARROW_LIGHTER = 50


def narrow_weight(wght: float) -> float:
    """The weight Arris Mono Narrow draws a weight at (NARROW_LIGHTER)."""
    return wght if wght <= MONO_WEIGHTS[0] else max(MONO_WEIGHTS[0], wght - NARROW_LIGHTER)
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


# The watch's stroke balance eases off past Bold: from 750 it takes a falling
# share of the watch's ratios, down to WATCH_FLOOR at Black. At its full share
# every horizontal is as thick as a stem (the measured optics thin them to
# 0.85 at Black) and every diagonal as wide across as one, and past Bold the
# drawings have no room for that: where bars stack against a bowl (э є ӭ ԙ ℡
# ҕ ҙ) the white between them closed into a blob at Black. Eased further, to
# half, the ŧ cleared too, but the drawings turned back toward the measured
# optics' own along the weight: a corner the watch's balance holds from Light
# up (the italic s's) curved again at 850, in some thirty glyphs, a feature
# lost and regained. Three quarters keeps the watch's character at Black;
# the ŧ has a rule of its own. The watch itself, SemiBold, and every weight
# up to 750 keep the full balance.
WATCH_TAPER = (750.0, 900.0)
WATCH_FLOOR = 0.75


def watch_share(wght: float) -> float:
    """The share of the watch's stroke balance a weight takes at WTCH 100."""
    a, b = WATCH_TAPER
    t = min(1.0, max(0.0, (wght - a) / (b - a)))
    return 1.0 - (1.0 - WATCH_FLOOR) * t


def params(wght: float = 600, grad: float = 0, optics: Optics = OPTICS, base: Params = Params(),
           watch: float = 0.0) -> Params:
    """Parameters for a weight, a grade, and a balance between the measured
    optics (watch = 0) and the watch's own proportions (watch = 1), eased
    off past Bold (WATCH_TAPER). The watch's optics passed whole are watch = 1
    (Arris Watch)."""
    if optics == HERITAGE_OPTICS:
        optics, watch = OPTICS, 1.0
    optical = 1.0 - watch
    share = watch * watch_share(wght)
    if share >= 1.0:
        optics = HERITAGE_OPTICS
    elif share:
        a, b = optics, HERITAGE_OPTICS
        mix = lambda x, y: x + (y - x) * share
        optics = Optics(h_light=mix(a.h_light, b.h_light), h_heavy=mix(a.h_heavy, b.h_heavy),
                        d_light=mix(a.d_light, b.d_light), d_heavy=mix(a.d_heavy, b.d_heavy),
                        s_light=mix(a.s_light, b.s_light), s_heavy=mix(a.s_heavy, b.s_heavy),
                        c_ratio=mix(a.c_ratio, b.c_ratio), leg=mix(a.leg, b.leg))
    p = _params(wght, optics, base)
    if grad:
        k = grade_k(wght, grad)
        p = p.with_(sv=p.sv * k, sh=p.sh * k, sd=p.sd * k, ss=p.ss * k, c=p.c * k, grade_k=k, grad=grad,
                    pregrade=(p.sv, p.sh, p.sd, p.ss, p.c))
    return p.with_(floor=stroke_floor(base), optical=optical)


# The lowercase's horizontals thin a little more than the capitals' toward
# Black: its bars stand in three quarters of the height, and one thickness
# for both closes the lowercase's counters first. Measured in hand-drawn
# faces (the o's top against the H's bar: tools/stroke_roles.py): 0.97 at
# Regular, 0.80 to 0.93 at Bold, 0.91 at Black. Here the whole of it to
# Regular, easing to LOW_HEAVY at Black (0.92 at Bold).
LOW_HEAVY = 0.87


def low_share(sv: float) -> float:
    """The lowercase's horizontals as a share of the weight's own."""
    t = min(max((sv - STEMS[400]) / (STEMS[900] - STEMS[400]), 0.0), 1.0)
    return 1.0 - (1.0 - LOW_HEAVY) * t


def _params(wght, optics, base):
    sv = stem(wght)
    # Figures stay tabular within a weight but widen with it, so heavier
    # strokes do not eat the counters whole; the watch weight keeps 540.
    d = stem(wght) - 120.0
    fig_w = base.fig_w + (FIG_GROWTH if d > 0 else FIG_GROWTH / 2) * d
    sh = sv * optics.h_ratio(sv)
    low = low_share(sv)
    return base.with_(fig_w=fig_w, fig_adv=fig_w + (base.fig_adv - base.fig_w), sv=sv, sh=sh, sd=sv * optics.d_ratio(sv),
                      ss=sv * optics.s_ratio(sv), c=sv * optics.c_ratio, leg=optics.leg, low=low,
                      desc=descender_line(base, sv, sh))



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
