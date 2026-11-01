"""A glyph's variations as the font stores them: the masters of its grid it
needs (``prune``), and the tuple variations over those (``tuples``), the
points interpolation can infer left out."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from itertools import product

import numpy as np
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables.TupleVariation import TupleVariation
from fontTools.varLib.iup import iup_delta, iup_delta_optimize
from fontTools.varLib.models import VariationModel, supportScalar

from .composites import Composite
from .measure import Rings, fold
from .space import AXIS_TAGS, DEFAULT, MASTERS, MODEL, NODES, Place, location, model

type Own = tuple[list[Place], dict[Place, Rings]]   # a glyph's own masters, and its outlines at those past the font's
type Aligned = Mapping[Place, Mapping[str, tuple[Rings, float]]]   # per master of the font, per glyph: outline, advance

IUP_TOLS = (2.0, 1.0, 0.5)  # font units: IUP tolerances tried, coarsest first ...
IUP_TOL = 2.0               # ... the coarsest that keeps every master of the grid within this


def prune(nodes: Sequence[Place], rings: Sequence[Rings], advs: Sequence[float], tol: float) -> list[Place]:
    """The masters of the glyph's grid it needs: one at a time, those the
    rest reproduce best first (a corner before an edge, an edge before the
    weight axis), each dropped while the masters left reproduce every one
    dropped (each point, and the advance) within ``tol`` units, and within
    ``tol`` of the box the masters left span. Every region of a model over
    any of the grid's nodes starts and ends at grid values, so the model is
    multilinear within each of the grid's cells, as the full grid's is:
    what holds at the dropped masters holds everywhere between them (and
    where the grade's and the watch's changes are linear in the weight, as
    for most glyphs, the masters left are 1.001's sparse layout or
    fewer)."""
    vals = np.array([[q[:2] for r in rings[i] for q in r] + [(advs[i], 0.0)] for i in range(len(nodes))], dtype=float)
    loc = [location(m) for m in nodes]
    lens = [len(r) for r in rings[0]]

    def folded(pts: np.ndarray) -> float:
        rs, k = [], 0
        for ln in lens:
            rs.append([tuple(q) for q in pts[k:k + ln]])
            k += ln
        return fold(rs)

    def off(keep: list[int], at: list[int]) -> float:
        """The farthest the model over keep is from the masters at, or
        they from the box the masters kept span (the font's own masters
        must span every point's range: tools/vf_spikes.py reads a point
        past them as carried off), or the fold the model makes there
        (measure.fold: a master dropped must not leave a wedge where it
        stood)."""
        vmodel = VariationModel([loc[i] for i in keep], axisOrder=AXIS_TAGS)
        deltas = np.array(vmodel.getDeltas(list(vals[keep])))
        lo, hi = vals[keep].min(axis=0), vals[keep].max(axis=0)
        worst = 0.0
        for j in at:
            got = np.tensordot(vmodel.getScalars(loc[j]), deltas, 1)
            worst = max(worst, float(np.abs(got - vals[j]).max()), float(np.maximum(lo - vals[j], vals[j] - hi).max()),
                        folded(got[:-1]))
        return worst
    every = list(range(len(nodes)))
    default = list(nodes).index(DEFAULT)
    alone = {i: off([j for j in every if j != i], [i]) for i in every if i != default}
    order = sorted(alone, key=lambda i: (-sum(1 for v in nodes[i][1:] if v), alone[i]))
    keep, gone = every, []
    for i in order:
        if alone[i] > tol:
            continue
        trial = [j for j in keep if j != i]
        if off(trial, gone + [i]) <= tol:
            keep, gone = trial, gone + [i]
    return [nodes[i] for i in keep]


def tuples(mlocs: Sequence[Place], outlines: Sequence[Rings], advances: Sequence[float],
           coords0: Sequence[tuple] | None = None, ends: Sequence[int] | None = None) -> list[TupleVariation]:
    """A glyph's variations (TupleVariations) over its masters ``mlocs``,
    from its outlines there (rings, put in the master fonts' order: each
    contour reversed, rounded) and advances: the deltas of one model over
    them, the grade never moving the advance (the phantom points), the
    points interpolation can infer left out (IUP) to the coarsest tolerance
    that keeps every node of the glyph's grid within IUP_TOL units. (Each
    delta's IUP error, summed at a node by the model's scalars, is the
    error there; every region starts and ends at grid values, so it is
    multilinear within the grid's cells and the nodes bound it between.)
    ``coords0``, ``ends``: the default glyph's points and contour ends as
    the font has them (else from the default outline)."""
    def pts(rings: Rings) -> list[tuple[int, int]]:
        return [(round(q[0]), round(q[1])) for r in rings for q in r[::-1]]
    vals = [np.array(pts(o) + [(0, 0), (round(a), 0), (0, 0), (0, 0)], dtype=float) for o, a in zip(outlines, advances)]
    if coords0 is None or ends is None:
        d0 = list(mlocs).index(DEFAULT)
        coords0 = [tuple(v) for v in vals[d0]]
        ends = [int(e) for e in np.cumsum([len(r) for r in outlines[d0]]) - 1]
    vmodel = model(mlocs)
    raw: list[tuple[dict, list[tuple[int, int]]]] = []
    for d, sup in zip(vmodel.getDeltas(vals), vmodel.supports):
        if not sup:
            continue
        coords = [(int(round(x)), int(round(y))) for x, y in d]    # noqa: RUF046  (numpy floats)
        if any(tag == 'GRAD' and peak for tag, (lo, peak, hi) in sup.items()):
            # grade never moves an advance: rounding the interpolated
            # advances must not make it do so by a unit
            coords[-4:] = [(0, 0)] * 4
        if any(c != (0, 0) for c in coords):
            raw.append((sup, coords))

    def size(tv: TupleVariation) -> int:
        return sum(map(len, tv.compile(AXIS_TAGS)))
    # the grid the masters are nodes of: every value each axis has
    vals_by_axis = [sorted({m[i] for m in list(mlocs) + NODES}) for i in range(3)]
    grid = [location((w, g, t)) for w, g, t in product(*vals_by_axis)]
    scal = np.array([[supportScalar(g, sup) for sup, _ in raw] for g in grid]) if raw else None
    tvs: list[TupleVariation] = []
    for tol in IUP_TOLS:
        tvs, errs = [], []
        for sup, coords in raw:
            tv = TupleVariation(dict(sup), coords)
            err = np.zeros((len(coords), 2))
            opt = iup_delta_optimize(coords, coords0, ends, tolerance=tol)  # ty: ignore[invalid-argument-type]  (numbers.Real)
            if None in opt:
                small = TupleVariation(dict(sup), opt)
                if size(small) < size(tv):
                    tv = small
                    err = np.array(iup_delta(opt, coords0, ends), dtype=float) - np.array(coords, dtype=float)  # ty: ignore[invalid-argument-type]
            tvs.append(tv)
            errs.append(err)
        if not raw or tol == IUP_TOLS[-1]:
            break
        if scal is not None and np.abs(np.tensordot(scal, np.array(errs), 1)).max() <= IUP_TOL:
            break
    return tvs


def gvar_bytes(tvs: Sequence[TupleVariation]) -> int:
    return sum(sum(map(len, tv.compile(AXIS_TAGS))) for tv in tvs)


def variations(vf: TTFont, names: Sequence[str], aligned: Aligned, own: Mapping[str, Own],
               composites: Mapping[str, Composite]) -> None:
    """Every glyph's variations as its masters have them (``tuples``: its
    own grid's, or the font's masters'); the composites' apart
    (``composite_variations``)."""
    gvar, glyf, hmtx = vf['gvar'], vf['glyf'], vf['hmtx'].metrics
    index = {m: i for i, m in enumerate(MASTERS)}
    for n in names:
        if n in composites or glyf[n].numberOfContours <= 0:     # (composites apart; empty glyphs vary nothing)
            continue
        mlocs = own[n][0] if n in own else MASTERS
        base_adv = [aligned[m][n][1] for m in MASTERS]
        outlines = [aligned[m][n][0] if m in index else own[n][1][m] for m in mlocs]
        advances = [base_adv[index[m]] if m in index else
                    MODEL.interpolateFromMasters(location(m), base_adv) for m in mlocs]
        coords0, ctrl = glyf._getCoordinatesAndControls(n, hmtx, None)
        gvar.variations[n] = tuples(mlocs, outlines, advances, coords0, ctrl.endPts)


def composite_variations(vf: TTFont, composites: Mapping[str, Composite], aligned: Aligned, tol: float) -> None:
    """A composite's variations: where its components stand, over the
    grid's masters it needs (its offsets pruned like an outline's points,
    ``prune``), the advance as the font's masters have it."""
    gvar, glyf = vf['gvar'], vf['glyf']
    index = {m: i for i, m in enumerate(MASTERS)}
    for n, (cs, offs) in composites.items():
        base_adv = [aligned[m][n][1] for m in MASTERS]
        advs = [base_adv[index[m]] if m in index else MODEL.interpolateFromMasters(location(m), base_adv)
                for m in NODES]
        keep = prune(NODES, [[offs[m]] for m in NODES], advs, tol)
        default = [(c.x, c.y) for c in glyf[n].components]   # (as the font has them, rounded)
        vals = []
        for m in keep:
            pts = default if m == DEFAULT else offs[m]
            a = base_adv[index[m]] if m in index else MODEL.interpolateFromMasters(location(m), base_adv)
            vals.append(np.array(list(pts) + [(0, 0), (a if m != DEFAULT else round(a), 0), (0, 0), (0, 0)], dtype=float))
        vmodel = model(keep)
        tvs = []
        for d, sup in zip(vmodel.getDeltas(vals, round=np.round), vmodel.supports):
            if not sup:
                continue
            coords = [(int(x), int(y)) for x, y in d]
            if any(tag == 'GRAD' and peak for tag, (lo, peak, hi) in sup.items()):
                coords[-4:] = [(0, 0)] * 4
            if any(c != (0, 0) for c in coords):
                tvs.append(TupleVariation(dict(sup), coords))
        gvar.variations[n] = tvs
