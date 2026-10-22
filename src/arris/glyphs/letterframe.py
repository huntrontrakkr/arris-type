"""Drawing letters in their pixel masters' coordinates, at any weight.

A master is drawn in modules; a letter's construction names its points in
those same module coordinates, and ``Frame`` maps them to font units for the
weight at hand. The map is piecewise linear through anchors where strokes
sit against the body: x = 1 is the centre of a left stem, Wm - 1 of a right
one, 0 and Wm the body's edges; y likewise for bars at the baseline, x-height,
cap height, ascender and descender. Between anchors the map is linear, so
inner strokes keep their place in proportion. At the watch's own weight the
map is the identity, so a construction can be checked against its master.

Diagonals cannot be mapped point by point (their slope must stay 45 degrees
or 2:1), so constructions place them by an anchored edge instead.

Widths: a letter is its stems plus its white. Stems take the weight's stem;
white widens a little at light weights and narrows a little at heavy ones,
so counters change far less than strokes.
"""
from __future__ import annotations

import math

from ..params import SQRT2

STEEP = (1 / math.sqrt(5), 2 / math.sqrt(5))


def _interp(anchors, t):
    pts = sorted(anchors)
    if t <= pts[0][0]:
        (a, fa), (b, fb) = pts[0], pts[1]
    elif t >= pts[-1][0]:
        (a, fa), (b, fb) = pts[-2], pts[-1]
    else:
        for (a, fa), (b, fb) in zip(pts, pts[1:]):
            if a <= t <= b:
                break
    return fa + (fb - fa) * (t - a) / (b - a) if b != a else fa


def white_scale(p) -> float:
    """How much a letter's white widens (light) or narrows (heavy)."""
    r = p.sv / (2 * p.m)          # stem relative to the watch's two-module stem
    if r >= 1:
        return 1 - 0.25 * (r - 1)
    return 1 + 0.4 * (1 - r)


def letter_width(wm: float, stems: float):
    """Body width for a master ``wm`` modules wide with ``stems`` stems across."""
    return lambda p: stems * p.sv + (wm - 2 * stems) * p.m * white_scale(p)


def heft(p) -> float:
    """How far the stem is past Regular's (a module and a half), in units;
    0 at Regular and lighter."""
    return max(0.0, p.sv - 1.5 * p.m)


def growing_width(wm: float, stems: float, k: float):
    """A symbol's body: a letter's, plus k units for every unit its stem has
    grown past Regular, so the white between its parts grows with its
    strokes instead of being eaten by them."""
    base = letter_width(wm, stems)
    return lambda p: base(p) + k * heft(p)


class Frame:
    def __init__(self, g, wm: float, zone: str = 'cap', top: float | None = None):
        p = g.p
        self.g, self.p, self.wm = g, p, wm
        self.W = W = g.W
        sv, sh = p.sv, g.sh
        self.k = p.sd / SQRT2          # half the across-width of a 45-degree stroke
        self.xa = [(0, 0.0), (1, sv / 2), (wm - 1, W - sv / 2), (wm, W)]
        if wm <= 2:
            self.xa = [(0, 0.0), (1, W / 2), (2, W)]
        if zone == 'cap':
            self.ya = [(0, 0.0), (1, sh / 2), (11, p.cap - sh / 2), (12, p.cap)]
            ztop = p.cap
        else:
            self.ya = [(-3, -p.desc), (-2, -p.desc + sh / 2), (0, 0.0), (1, sh / 2),
                       (8, p.xh - sh / 2), (9, p.xh), (12, p.asc - sh / 2), (13, p.asc)]
            ztop = p.asc if zone == 'asc' else p.xh
        self.top = ztop if top is None else top
        g.clip = (0, 0 if zone == 'cap' else -p.desc, W, self.top)

    def X(self, x):
        return _interp(self.xa, x)

    def Y(self, y):
        return _interp(self.ya, y)

    def P(self, x, y):
        return (self.X(x), self.Y(y))


def k_arms(g, x_stem: float, W: float, top: float, branch: bool = False):
    """K's arm and leg for a stem at x_stem in a body W wide and ``top`` tall.

    Both leave the body's right corners an edge break in. At light weights
    they meet in a short vertical beside the stem, as the K master draws it;
    when heavier strokes would make that junction a lump (their outer edges
    no longer reach the vertical), the arm runs on into the stem and the leg
    branches from the arm, so the crotch between them stays open.
    Returns strokes as (points, start cap, end cap)."""
    p = g.p
    k = p.sd / SQRT2
    a_arm = W - top + p.c - k                               # arm: x - y = a_arm
    a_leg = W + p.c - k                                     # leg: x + y = a_leg
    xj = x_stem + p.sv * 0.999                             # (overlapping the stem by a hair)
    if not branch and 2 * xj + p.sv > a_arm + a_leg + 2 * k + 1e-6:
        y_hi, y_lo = xj - a_arm, a_leg - xj
        mid = [(xj, y_hi), (xj, y_lo)] if y_hi > y_lo + 1e-9 else [(xj, y_hi)]
        return [([(top + a_arm, top), *mid, (a_leg, 0)], 'h', 'h')]
    # the leg leaves the arm where they cross, or the stem if they cross inside it
    xm = max((a_arm + a_leg) / 2, x_stem)
    return [([(top + a_arm, top), (x_stem, x_stem - a_arm)], 'h', 'flat'),
            ([(xm, a_leg - xm), (a_leg, 0)], 'flat', 'h')]
