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
white widens a little at light weights, and past the Regular it gives way
to the stems as the white of other families' letters does (white_scale).
"""
from __future__ import annotations

import contextlib
import math

from ..params import SQRT2, white_floor, white_own

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


def share_width(wm: float):
    """A body that keeps its master's share of the H's width at every
    weight: ``wm`` ninths of it (the H is nine modules)."""
    return lambda p: wm / 9 * (2 * p.sv + 5 * p.m * white_scale(p))


_ZONE = ['cap']     # whose white is being asked for (zone)


@contextlib.contextmanager
def zone(kind):
    """While a glyph's body is measured or drawn: whether its white is a
    lowercase letter's ('lower'), the watch's own, which gives nothing
    ('own': draw.white_of), or a capital's, a figure's, a sign's (anything
    else) (white_scale)."""
    _ZONE.append(kind if kind in ('lower', 'own') else 'cap')
    try:
        yield
    finally:
        _ZONE.pop()


def white_scale(p, lower: bool | None = None) -> float:
    """How much a letter's white widens (light) or narrows (heavy), against
    its master's modules.

    To the Regular the white widens a little as the stems thin, by the
    watch's own rule (params.white_own). Past it the white gives way to the
    stems as the white of other families' letters does, a lowercase
    letter's faster than a capital's, a figure's or a sign's
    (instances.white_given: what is left of it, carried in the parameters,
    so a set drawn smaller inside a glyph gives as its font does).
    ``lower``: whose white; by default the glyph's being measured or drawn
    (zone)."""
    if lower is None and _ZONE[-1] == 'own':
        return white_own(p.sv / (2 * p.m))
    low = _ZONE[-1] == 'lower' if lower is None else lower
    return white_own(p.sv / (2 * p.m)) * (p.white_low if low else p.white_cap)


def plain_width(wm: float, stems: float):
    """Body width for a master ``wm`` modules wide with ``stems`` stems
    across: its stems and its white."""
    return lambda p: stems * p.sv + (wm - 2 * stems) * p.m * white_scale(p)


def own_width(wm: float, stems: float):
    """The body plain_width gives where no white has given way: by the
    watch's own rule at every weight (params.white_own). What a letter
    that narrows by a share of its body is measured in (letter_width,
    lower.y_width)."""
    return lambda p: stems * p.sv + (wm - 2 * stems) * p.m * white_own(p.sv / (2 * p.m))


ARM = 1.0     # what a one-stem letter's open side widens by, for each unit its stem grows past Regular


def ungiving(wm: float, stems: float, arm: float = ARM):
    """A letter's body that gives no white past the Regular: letter_width
    as it was before the letters gave. For a letter whose drawing has no
    counter to take it from: the florin's crossbar and hook (a wedge at
    Black in the narrower body, as the f's were), the ϰ's two curls."""
    own = own_width(wm, stems)
    if stems != 1 or not arm:
        return own
    return lambda p: own(p) + arm * heft(p)


def narrowed(p) -> float:
    """What is left, past the Regular, of the body of the letter the others
    stand beside: the n's among lowercase letters (eight modules, two
    stems), the H's among the rest (nine). 1 to the Regular, in Arris Mono
    and in the watch's own drawing (white_scale)."""
    white = (4 if _ZONE[-1] == 'lower' else 5) * p.m
    return (2 * p.sv + white * white_scale(p)) / (2 * p.sv + white * white_own(p.sv / (2 * p.m)))


def letter_width(wm: float, stems: float, arm: float = ARM):
    """A letter's body. A letter with one stem (E F K L T Z, f k r t z)
    makes room on its open side as its arms and diagonals thicken: past
    Regular it widens by ``arm`` times what the stem has grown, as a letter
    with two stems widens by its second.

    Until 1.017 it did not: stems alone added width, so from Regular to
    Black the H grew a fifth and the E, the K and the r not at all, and
    each lost a fifth of its share of the line (K 0.82, T 0.80, r 0.80, z
    0.80 of what it had at Regular; in hand-drawn faces every letter keeps
    its share, 0.93 to 1.08: tools/letter_shares.py). Their arms, thicker
    in a body no wider, were stubs (f t r), and the K's and k's diagonals
    rooted in one block along the stem.

    Where the white gives way past the Regular (white_scale) a one-stem
    letter gives the share of its body the n (the H) gives of its own
    (narrowed), not the white of its modules: its open side, six modules of
    the k's eight where the n has four between its stems, holds an arm or a
    diagonal as thick as a stem, and with all six giving the k, the z, the K
    and the Z lost a tenth of their share again (0.90 and 0.93)."""
    if stems != 1:
        return plain_width(wm, stems)
    own = own_width(wm, stems)
    # (with no arm's room, the cursive's one-stem letters: the share all the same)
    return lambda p: (own(p) + arm * heft(p)) * narrowed(p)


def least_white(p) -> float:
    """The least white across a closed counter or between two parts of a
    sign: a module, or 0.6 of a stem toward Black (white narrower than half
    a stroke is no white at all: draw.white_features), in Arris no more
    than at a stem of 158 (params.white_floor)."""
    return white_floor(p.m, p.sv, p.optical)


def heft(p) -> float:
    """How far the stem is past Regular's (a module and a half), in units;
    0 at Regular and lighter."""
    return max(0.0, p.sv - 1.5 * p.m)


def growing_width(wm: float, stems: float, k: float):
    """A symbol's body: a letter's, plus k units for every unit its stem has
    grown past Regular, so the white between its parts grows with its
    strokes instead of being eaten by them."""
    base = plain_width(wm, stems)
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


def k_arms(g, x_stem: float, W: float, top: float, branch: bool = True):
    """K's arm and leg for a stem at x_stem in a body W wide and ``top`` tall.

    Both leave the body's right corners an edge break in. The arm runs on
    into the stem and the leg branches from the arm where they cross (from
    the stem, if they cross inside it), so the crotch between them is a
    point at every weight and the two read as two strokes.

    Until 1.017 the capital changed its drawing along the weight: where the
    body was narrow for its strokes (from Bold, and in Arris Mono) arm and
    leg met in a short vertical beside the stem, as the K's pixel master
    draws it, a block a stem wide with a flat-bottomed crotch, while the k,
    drawn in the x-height, never did. (``branch`` is kept for callers that
    named it.) Returns strokes as (points, start cap, end cap)."""
    p = g.p
    k = p.sd / SQRT2
    a_arm = W - top + p.c - k                               # arm: x - y = a_arm
    a_leg = W + p.c - k                                     # leg: x + y = a_leg
    # the leg leaves the arm where they cross, or the stem if they cross inside it
    xm = max((a_arm + a_leg) / 2, x_stem)
    return [([(top + a_arm, top), (x_stem, x_stem - a_arm)], 'h', 'flat'),
            ([(xm, a_leg - xm), (a_leg, 0)], 'flat', 'h')]


def close_slit(g, x0: float, x1: float, bottom: float, top: float) -> None:
    """Fill the white between two horizontals, x0 to x1, from ``bottom``
    (the lower stroke's top edge) up to ``top`` (the upper one's bottom
    edge), where it is narrower than the slits the outline fills
    (geom.SLIT): whole, not as the outline's fill takes it, partly and
    from weight to weight differently. Under ϱ ℊ ₰'s bowls the white
    became a wedge at one weight, a slit at the next and closed at the
    one after, along the heavy watch; filled whole from where it is that
    narrow, it closes once and stays closed."""
    from ..geom import SLIT
    white = top - bottom
    if 0 < white < 2 * SLIT * g.p.c:
        g.stroke((x0, (top + bottom - 1) / 2, white + 1), (x1, (top + bottom - 1) / 2))
