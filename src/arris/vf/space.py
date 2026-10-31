"""The design space: the axes, the masters, the grid they are nodes of, the
places the interpolation is checked at, and the variation model between
them."""
from __future__ import annotations

from collections.abc import Sequence
from functools import cache
from itertools import product
from typing import NamedTuple

from fontTools.varLib.models import VariationModel

from arris import italic as ital
from arris.instances import NAMES
from arris.instances import params as _params
from arris.params import Params

type Place = tuple[float, float, float]      # (wght, GRAD, WTCH), in the axes' own units

FAMILY = 'Arris'


class Axis(NamedTuple):
    tag: str
    name: str
    minimum: float
    default: float
    maximum: float


AXES = (Axis('wght', 'Weight', 100, 400, 900), Axis('GRAD', 'Grade', -100, 0, 100), Axis('WTCH', 'Watch', 0, 0, 100))
AXIS_TAGS = [a.tag for a in AXES]

# Masters where the interpolation check found the drawing bends between them:
# every 100 on the weight axis up to 700 (the 1's flag, ŉ, the digraphs). On
# the grade's ends, SemiBold and ExtraBold too: a positive grade fades out
# from SemiBold to Black (instances.GRAD_TAPER), so the grade's change bends
# at 600, and from three weights the model carried less than half of it
# there; and the heavy grades are where the drawings change most.
BASE: list[Place] = [(w, 0, 0) for w in (100, 200, 300, 400, 500, 600, 700, 750, 800, 850, 900)] + \
    [(w, g, 0) for w in (100, 400, 600, 800, 900) for g in (-100, 100)] + \
    [(w, 0, 100) for w in (100, 400, 600, 800, 900)]
# Masters where the grade and the watch meet. Without them the font adds
# the grade's change and the watch's there, and a point that slides along
# one edge as the grade moves and along another as the watch does (a
# feature present in both, absent in the plain master) is carried off the
# outline: Ç Ø Δ z ₰ by 100 to 440 units at (900, 100, 100). Per glyph, a
# corner master carries the exact drawing where it aligns with the others
# and interpolates better so, else the outline the other masters predict
# there (no change: ŀ, whose dot meets its l at the heavy corner, 2026-10-25).
CORNERS: list[Place] = [(w, g, 100) for w in (100, 400, 600, 800, 900) for g in (-100, 100)]
MASTERS: list[Place] = BASE + CORNERS
NB = len(BASE)
# The masters a glyph is interpolated between: a full grid over the design
# space, every weight of BASE by the grade's ends and default by the watch's
# ends (the font's masters among them, first). On a full grid the variation
# model is multilinear: the outline anywhere is a weighted mean of the
# outlines at its cell's corners and cannot overshoot them. On the font's
# sparse layout the grade's change and the watch's, each measured at three
# weights, add up across the bends of the weight axis: tools/vf_spikes.py
# found 675 glyphs carried more than 20 units past every master (✵ 350 at
# (825, 100, 100), ₩ 170, ð 140) and 929 crossing themselves. The masters
# past the font's are each glyph's own (gvar keeps variations glyph by glyph:
# encode.variations), and each glyph keeps only the planes it needs
# (encode.prune).
GRID_AXES: tuple[list[float], list[float], list[float]] = (
    [w for w, g, t in BASE if not g and not t], [-100, 0, 100], [0, 100])
NODES: list[Place] = MASTERS + sorted(set(product(*GRID_AXES)) - set(MASTERS))
DEFAULT: Place = (400, 0, 0)
# between every two neighbouring masters on each axis, off the axes, and the
# corners themselves (where a predicted corner shows what it adds up to)
CHECK: list[Place] = [(150, 0, 0), (250, 0, 0), (350, 0, 0), (450, 0, 0), (550, 0, 0), (650, 0, 0), (725, 0, 0),
                      (775, 0, 0), (825, 0, 0), (875, 0, 0)] + \
    [(w, g, 0) for w in (100, 400, 900) for g in (-50, 50)] + [(w, 0, 50) for w in (100, 400, 600, 800, 900)] + \
    [(700, -50, 0), (300, 0, 100), (400, 50, 50), (900, 50, 50), (800, 50, 100), (850, 75, 75),
     (900, -50, 50), (650, 75, 75), (250, -50, 50), (900, 100, 50), (900, 50, 100)] + CORNERS
# more places between the masters, off the axes, that a glyph's own masters
# are chosen from (VALID, in the final check, stays apart from both)
REFINE: list[Place] = [(500, -50, 50), (300, -50, 0), (600, 50, 50), (750, -75, 75), (850, 50, 25), (250, 50, 0),
                       (650, -50, 100), (450, -100, 50), (550, 100, 25), (350, 25, 75), (800, -25, 25), (700, 100, 75)]
# the check, and places between it the build never looked at (a glyph's own
# masters come from CHECK: these say whether it holds in between)
VALID: list[Place] = [(850, 25, 25), (650, -25, 75), (300, 50, 50), (725, 60, 30), (500, -75, 25), (875, 90, 90),
                      (200, -50, 50), (575, 25, 0), (775, 0, 75), (450, 75, 100)]
# a coarse grid over the whole design space, for the dense measure (dense)
DENSE: list[Place] = [(w, g, t) for w in range(100, 901, 50) for g in (-100, -50, 0, 50, 100) for t in (0, 25, 50, 75, 100)]


def _normal(v: float, axis: Axis) -> float:
    lo, df, hi = axis.minimum, axis.default, axis.maximum
    return (v - df) / (df - lo) if v < df else (v - df) / (hi - df) if hi > df else 0.0


def normal(place: Place) -> tuple[float, float, float]:
    """A place in the font's normalised design space (-1..1 on each axis, 0
    at the default): what the aligner measures nearness in."""
    w, g, t = place
    return _normal(w, AXES[0]), _normal(g, AXES[1]), _normal(t, AXES[2])


def location(place: Place) -> dict[str, float]:
    """A place as fontTools' models take it: its normalised value by axis tag."""
    return dict(zip(AXIS_TAGS, normal(place)))


LOCS = [normal(m) for m in MASTERS]
MODEL = VariationModel([location(m) for m in MASTERS], axisOrder=AXIS_TAGS)
MODEL_BASE = VariationModel([location(m) for m in BASE], axisOrder=AXIS_TAGS)


@cache
def _model(places: tuple[Place, ...]) -> VariationModel:
    return VariationModel([location(m) for m in places], axisOrder=AXIS_TAGS)


def model(places: Sequence[Place]) -> VariationModel:
    """The variation model over a glyph's masters (the font's, and any of its own)."""
    return _model(tuple(places))


def params(place: Place, italic: bool = False) -> Params:
    """The engine's parameters at a place (the italic's, sheared and curved)."""
    w, g, t = place
    p = _params(w, g, watch=t / 100)
    return ital.italic(p) if italic else p


def master_params(italic: bool = False) -> dict[Place, Params]:
    return {m: params(m, italic) for m in MASTERS}


def style_name(w: float, italic: bool = False) -> str:
    nm = NAMES.get(w, f'W{w}')
    if not italic:
        return nm
    return 'Italic' if nm == 'Regular' else f'{nm} Italic'
