"""The variable font against exact drawings between the masters: every
glyph, instantiated at the check's places and at places the build never
chose a master from (VALID), compared with the engine's drawing there."""
from __future__ import annotations

import json
import logging
from collections.abc import Mapping, Sequence
from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

from arris import italic as ital
from arris.font import place
from arris.geom import rings_to_shapely

from .measure import Rings
from .settings import Settings
from .space import CHECK, VALID, Place, params

log = logging.getLogger(__name__)

TOL = 3.0       # font units: a mean outline difference under 0.3% of the em passes
FAR = 60.0      # font units: a point carried farther than this off the outline is a spike

type Result = tuple[float, Place, str, float]       # (mean difference, place, glyph, farthest point off)


def outline(glyf, n: str, italic: bool) -> list[list[tuple]]:
    """A built glyph's contours as the drawings are compared with: reversed
    to the engine's direction, the italic's curves flattened."""
    coords, ends, flags = glyf[n].getCoordinates(glyf)
    pts, start = list(coords), 0
    got = []
    for e in ends:
        c = [(q[0], q[1], bool(f & 1)) for q, f in zip(pts[start:e + 1], flags[start:e + 1])][::-1]
        got.append(ital.flatten(c) if italic else [q[:2] for q in c])
        start = e + 1
    return got


def compare(got: list[list[tuple]], exact) -> tuple[float, float]:
    """(the mean distance between the two outlines, in font units: the area
    between them over the exact outline's length; the farthest a point is
    off the exact outline: a spike)."""
    try:
        interp = rings_to_shapely([r for r in got if len(set(r)) >= 3])
        return (interp.symmetric_difference(exact).area / max(exact.boundary.length, 1),
                interp.boundary.hausdorff_distance(exact.boundary))
    except Exception:  # noqa: BLE001  (an outline that cannot be made is as bad as it gets)
        return 1e9, 1e9


_FONT: Path | None = None
_NAMES: Sequence[str] = ()
_SHOWN: Mapping[tuple[str, Place], Rings] = {}
_ITALIC = False


def _use(font: Path, names: Sequence[str], shown: Mapping[tuple[str, Place], Rings], italic: bool) -> None:
    global _FONT, _NAMES, _SHOWN, _ITALIC
    _FONT, _NAMES, _SHOWN, _ITALIC = font, names, shown, italic


def _at(w: Place) -> list[Result]:
    """Every glyph of the built font at w against its exact drawing."""
    assert _FONT is not None
    inst = instantiateVariableFont(TTFont(_FONT), {'wght': w[0], 'GRAD': w[1], 'WTCH': w[2]})
    glyf = inst['glyf']
    p = params(w, _ITALIC)
    res = []
    for n in _NAMES:
        if (n, tuple(w)) in _SHOWN:                         # drawn while aligning
            exact = rings_to_shapely(_SHOWN[n, tuple(w)])
        else:
            rings, _ = place(n, p)
            exact = rings_to_shapely(ital.polylines(rings) if _ITALIC else rings)
        err, far = compare(outline(glyf, n, _ITALIC), exact)
        res.append((err, w, n, far))
    return res


def check(settings: Settings, names: Sequence[str], shown: Mapping[tuple[str, Place], Rings]) -> list[Result]:
    """The font settings.font against the drawings at CHECK and VALID:
    the report logged (the worst glyphs, the spikes), every result written
    to settings.report for triage."""
    places = CHECK + VALID
    worst: list[Result] = []
    with settings.pool(len(places), _use, (settings.font, names, shown, settings.italic)) as pool:
        for res in pool.imap_unordered(_at, places):
            worst += res
    worst.sort(reverse=True)
    bad = [x for x in worst if x[0] > TOL]
    spikes = sorted((x for x in worst if x[3] > FAR), key=lambda x: -x[3])
    log.info('interpolation check: %d glyph-weights; mean outline difference worst %.1f units, median %.2f; '
             '%d over %s units; %d with a point over %s units off the outline (%d glyphs)',
             len(worst), worst[0][0], sorted(worst)[len(worst) // 2][0], len(bad), TOL, len(spikes), FAR,
             len({x[2] for x in spikes}))
    for e, w, n, far in worst[:25]:
        log.info('  %-16s at %s: %.1f units', n, w, e)
    for e, w, n, far in spikes[:15]:
        log.info('  spike: %-16s at %s: %.0f units off', n, w, far)
    settings.report.write_text(json.dumps([[round(e, 2), list(w), n, round(far, 1)] for e, w, n, far in worst]))
    return worst
