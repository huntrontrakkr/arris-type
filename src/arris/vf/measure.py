"""How far the font's interpolation is from the drawings: aligned masters
interpolated as the font will interpolate them, at the check's places
against the exact drawing there, and between those places against
themselves (``dense``)."""
from __future__ import annotations

import logging
from collections.abc import Callable, Sequence

import numpy as np
from fontTools.varLib.models import VariationModel
from shapely.geometry.base import BaseGeometry

from arris.geom import rings_to_shapely
from arris.topology import faults

from . import dense
from .space import CHECK, DENSE, MASTERS, MODEL, Place, location, model, normal

log = logging.getLogger(__name__)

type Ring = list[tuple]                       # a contour's points: (x, y) or (x, y, on)
type Rings = list[Ring]                       # a glyph's outline

LOCAL_TOL = 3.0     # font units: a mean outline difference a glyph's alignment is held to
SPIKE = 20.0        # a point carried off the outline counts its distance over this (a spike has little area)
# Between the check's places: the interpolation looked at on a grid over the
# whole design space (dense), against no drawing: a point carried outside the
# box its masters span, or the outline crossing itself deeper than the
# masters do (by how far a point would have to move back to undo it),
# DENSE_TOL of either as bad as LOCAL_TOL (tools/vf_spikes.py's tolerance),
# so the alignment that keeps the font clean everywhere wins, and a glyph's
# finer grid goes where it is not. (A crossing counted as a fixed cost, ten
# times LOCAL_TOL, made a glyph take a 116-unit spike over a twist 2 units
# deep.)
DENSE_TOL = 20.0    # font units: a point this far past its masters, or a crossing this deep, is as bad as LOCAL_TOL


def fold(rings: Rings) -> float:
    """The largest piece a contour of the outline folds wrong, in font units
    (arris.topology: a contour that crosses itself, sized by the area it
    winds backwards or not at all). A fold is an error of its own size: a
    three-unit sliver is as bad as a LOCAL_TOL mean difference, where the
    crossing's depth (dense.deepest) saw a long thin wedge as shallow."""
    return max((f.size for f in faults(rings, 0.0, False, every=False) if f.kind == 'cross'), default=0.0)


def interpolate(al: Sequence[Rings], loc: Place, vmodel: VariationModel = MODEL) -> Rings:
    """The masters' outlines (aligned) at loc, as the variable font has
    them; a point's further fields (an italic point's on-curve flag) are
    the first master's."""
    flat = [np.array([c for r in m for q in r for c in q[:2]], dtype=float) for m in al]
    v = vmodel.interpolateFromMasters(location(loc), flat)
    out: Rings = []
    i = 0
    for r in al[0]:
        out.append([(v[i + 2 * j], v[i + 2 * j + 1]) + tuple(q[2:]) for j, q in enumerate(r)])
        i += 2 * len(r)
    return out


def predicted(lead: Sequence[Rings], nodes: Sequence[Place], vmodel: VariationModel) -> list[Rings]:
    """Every node's outline: the leading masters' (aligned), the rest
    predicted from them by their model."""
    return list(lead) + [interpolate(lead, m, vmodel) for m in nodes[len(lead):]]


def errors(al: Sequence[Rings], exact: Callable[[Place], BaseGeometry], mlocs: Sequence[Place] | None = None,
           where: Sequence[Place] | None = None) -> dict[Place, float]:
    """The difference at each CHECK location (or ``where``) between the
    font's outline and the exact drawing: the mean distance between the
    outlines, or the farthest a point is carried off it over SPIKE,
    whichever is more."""
    vmodel = model(mlocs or MASTERS)
    out: dict[Place, float] = {}
    try:
        out.update(dense_errors(al, mlocs or MASTERS))
    except Exception as e:  # noqa: BLE001  (a measure that fails says nothing against the alignment)
        log.debug('dense measure: %s', e)
    for loc in (where or CHECK):
        try:
            ex = exact(loc)
            rings = [r for r in interpolate(al, loc, vmodel) if len(set(r)) >= 3]
            got = rings_to_shapely(rings)
            err = max(got.symmetric_difference(ex).area / max(ex.boundary.length, 1),
                      got.boundary.hausdorff_distance(ex.boundary) / SPIKE, fold(rings))
        except Exception:  # noqa: BLE001  (an outline that cannot be made is as bad as it gets)
            err = 1e9
        out[loc] = err
        if err > 1e8:
            break
    return out


def error(al: Sequence[Rings], exact: Callable[[Place], BaseGeometry], mlocs: Sequence[Place] | None = None) -> float:
    return max(errors(al, exact, mlocs).values())


def dense_errors(al: Sequence[Rings], mlocs: Sequence[Place]) -> dict[Place, float]:
    """The places of DENSE where the interpolation overshoots its masters,
    crosses itself deeper than they do, or folds (``fold``, by its size),
    by the equivalent of a mean outline difference (over LOCAL_TOL alone)."""
    vmodel = model(mlocs)
    base, D, R, nxt = dense.from_masters(al, [normal(m) for m in mlocs], vmodel)
    masters_pts = np.array([[q[:2] for r in m for q in r] for m in al], dtype=float)
    locs = np.array([normal(m) for m in DENSE])
    lo, hi = masters_pts.min(axis=0), masters_pts.max(axis=0)
    mask = dense.pair_mask(nxt)
    d0 = float(dense.deepest(np, masters_pts, nxt, mask).max())
    P = dense.outlines(np, locs, base, D, R)
    d = dense.overshoot(np, P, lo, hi)
    x = dense.deepest(np, P, nxt, mask)
    lens = [len(r) for r in al[0]]
    out: dict[Place, float] = {}
    for i, loc in enumerate(DENSE):
        e = max(d[i], x[i] - d0 if x[i] >= dense.DEPTH else 0.0) * LOCAL_TOL / DENSE_TOL
        rings, k = [], 0
        for ln in lens:
            rings.append([tuple(q) for q in P[i, k:k + ln]])
            k += ln
        e = max(e, fold(rings))
        if e > LOCAL_TOL:
            out[loc] = e
    return out
