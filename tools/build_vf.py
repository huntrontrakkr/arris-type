"""Build the variable font, made point-compatible by ``arris.variable.align``
and checked against exact drawings at locations between the masters.

Axes:
  wght  100-900  weight
  GRAD  -100-100 grade: strokes thinner or thicker, every width and space kept
  WTCH  0-100    the watch's own proportions (diagonals as wide across as a
                 stem, horizontals as heavy as verticals) instead of the
                 measured optics

usage: build_vf.py [italic]   ('italic' builds Arris-Italic[GRAD,WTCH,wght].ttf:
the upright masters are aligned, then curved and sheared, arris.italic)
"""
import sys
import tempfile
import time
from itertools import product
from pathlib import Path

_T0 = time.time()


def _took():
    """Minutes since the build started, for each phase's line."""
    return f'[{(time.time() - _T0) / 60:.1f} min]'

from fontTools.designspaceLib import AxisDescriptor, DesignSpaceDocument, InstanceDescriptor, SourceDescriptor
from fontTools.ttLib import TTFont
from fontTools.varLib import build as varlib_build
from fontTools.varLib.instancer import instantiateVariableFont
from shapely.geometry import Polygon

import arris.glyphs  # noqa: F401
from arris.draw import REGISTRY
from arris.font import KERN_PUNCT, _place, build, light, place
from arris import italic as ital
from arris.glyphs.features import fea
from arris.instances import NAMES, params
from arris.kerning import kerns
from arris.variable import align

# (wght, GRAD, WTCH)
# Masters where the interpolation check found the drawing bends between them:
# every 100 on the weight axis up to 700 (the 1's flag, ŉ, the digraphs). On
# the grade's ends, SemiBold and ExtraBold too: a positive grade fades out
# from SemiBold to Black (instances.GRAD_TAPER), so the grade's change bends
# at 600, and from three weights the model carried less than half of it
# there; and the heavy grades are where the drawings change most.
BASE = [(w, 0, 0) for w in (100, 200, 300, 400, 500, 600, 700, 750, 800, 850, 900)] + \
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
CORNERS = [(w, g, 100) for w in (100, 400, 600, 800, 900) for g in (-100, 100)]
MASTERS = BASE + CORNERS
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
# _own_masters), and each glyph keeps only the planes it needs (_prune).
GRID_AXES = ([w for w, g, t in BASE if not g and not t], [-100, 0, 100], [0, 100])
NODES = MASTERS + sorted(set(product(*GRID_AXES)) - set(MASTERS))
DEFAULT = (400, 0, 0)
AXES = (('wght', 'Weight', 100, 400, 900), ('GRAD', 'Grade', -100, 0, 100), ('WTCH', 'Watch', 0, 0, 100))
# between every two neighbouring masters on each axis, off the axes, and the
# corners themselves (where a predicted corner shows what it adds up to)
CHECK = [(150, 0, 0), (250, 0, 0), (350, 0, 0), (450, 0, 0), (550, 0, 0), (650, 0, 0), (725, 0, 0),
         (775, 0, 0), (825, 0, 0), (875, 0, 0)] + \
    [(w, g, 0) for w in (100, 400, 900) for g in (-50, 50)] + [(w, 0, 50) for w in (100, 400, 600, 800, 900)] + \
    [(700, -50, 0), (300, 0, 100), (400, 50, 50), (900, 50, 50), (800, 50, 100), (850, 75, 75),
     (900, -50, 50), (650, 75, 75), (250, -50, 50), (900, 100, 50), (900, 50, 100)] + CORNERS


def LOC(m):
    """A master's place in the font's normalised design space (-1..1 on
    each axis, 0 at the default): what the aligner measures nearness in."""
    return tuple((v - df) / (df - lo) if v < df else (v - df) / (hi - df) if hi > df else 0.0
                 for v, (_, _, lo, df, hi) in zip(m, AXES))


LOCS = [LOC(m) for m in MASTERS]

family = 'Arris'
FIGS = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine']
names = FIGS + [n for n in REGISTRY if n not in FIGS and not n.endswith('.ital')
                and not (isinstance(REGISTRY[n].kind, tuple) and REGISTRY[n].kind[0] == 'liga')]
if __import__('os').environ.get('ARRIS_VF_ONLY'):          # a trial build of a few glyphs (into build/trial/)
    names = [n for n in names if n in __import__('os').environ['ARRIS_VF_ONLY'].split(',')]


ITALIC = 'italic' in sys.argv[1:]


def P(loc):
    w, g, t = loc
    p = params(w, g, watch=t / 100)
    return ital.italic(p) if ITALIC else p


def style_name(w):
    nm = NAMES.get(w, f'W{w}')
    if not ITALIC:
        return nm
    return 'Italic' if nm == 'Regular' else f'{nm} Italic'


# Forms: a glyph whose drawing chooses between two (a Squint rule with
# form=True: ¢ $ stem or stubs) cannot interpolate from one to the other.
# Each form becomes a glyph of its own, drawn in that form at every master,
# and a designspace rule (GSUB feature variations, rvrn) swaps the second in
# where the engine draws it: from the weight where it first does, in each
# band of grade and watch (the choice is monotone in the weight: draw).
import dataclasses  # noqa: E402
from fontTools.designspaceLib import RuleDescriptor  # noqa: E402
from arris.draw import draw as _draw_glyph  # noqa: E402

GRAD_BANDS = [(-100, -75, -100), (-75, -25, -50), (-25, 25, 0), (25, 75, 50), (75, 100, 100)]
WTCH_BANDS = [(0, 25, 0), (25, 75, 50), (75, 100, 100)]
FORMS = {}                                                   # glyph -> (its second form's name, regions)


def _second(n, free, d, lim, loc):
    g = _draw_glyph(n, P(loc))
    v = g.overrides.get(free, d)
    return (v - (d + lim) / 2) * (lim - d) > 0


for n in list(names):
    spec = REGISTRY[n]
    for sq in spec.squint:
        if not sq.form:
            continue
        g0 = _draw_glyph(n, P(DEFAULT))
        d, lim = g0.defaults.get(sq.free), sq.limit(P(DEFAULT))
        if d is None:
            continue
        regions = []
        for glo, ghi, gs in GRAD_BANDS:
            for tlo, thi, ts in WTCH_BANDS:
                if not _second(n, sq.free, d, lim, (900, gs, ts)):
                    continue
                lo, hi = 100.0, 900.0
                if not _second(n, sq.free, d, lim, (lo, gs, ts)):
                    for _ in range(9):
                        mid = (lo + hi) / 2
                        lo, hi = (lo, mid) if _second(n, sq.free, d, lim, (mid, gs, ts)) else (mid, hi)
                    lo = hi
                regions.append((round(lo, 1), glo, ghi, tlo, thi))
        alt = f'{n}.{sq.free}'

        def pinned(fn, free=sq.free, v=None):
            def f(g):
                g.overrides[free] = v
                return fn(g)
            f.__module__, f.__name__ = fn.__module__, fn.__name__
            return f
        keep = tuple(q for q in spec.squint if q is not sq)
        for base in (n, f'{n}.ital'):
            if base in REGISTRY:
                b = REGISTRY[base]
                REGISTRY[base] = dataclasses.replace(b, fn=pinned(b.fn, v=d), squint=keep)
                REGISTRY[base.replace(n, alt, 1)] = dataclasses.replace(b, name=base.replace(n, alt, 1), unicode=None,
                                                                        fn=pinned(b.fn, v=lim), squint=keep)
        names.append(alt)
        FORMS[n] = (alt, regions)
print(_took(), 'forms:', {n: (a, r[:2], len(r)) for n, (a, r) in FORMS.items()})

ps = {m: P(m) for m in MASTERS}
NAMESET = set(names)                                    # (a composite's components must be in the font)

# Per glyph, the masters are drawn (upright: the italic is made from them),
# aligned, and the alignment is checked: interpolated as the font will
# (fontTools' VariationModel, on the font's own masters) at the CHECK
# locations between the masters, and compared with the exact drawing there.
# Where that is off by more than LOCAL_TOL, the alternatives are tried, and
# whichever interpolates best is kept:
# * the masters aligned each against one, the one with the most points,
#   instead of each against its neighbours in the design space (the default;
#   arris.variable): one master's points can pair better with the others'
#   through the thin master than through a chain of neighbours;
# * the masters drawn again without the jog closing (geom._close_jogs):
#   cleaned of jogs, neighbouring weights can differ in structure where a
#   step closes at one and not the next.
# Glyphs are independent: the work runs on a pool of processes.
from fontTools.varLib.models import VariationModel  # noqa: E402
from arris import geom as _geom  # noqa: E402
from arris.geom import rings_to_shapely as _shp  # noqa: E402

AXIS_TAGS = [a[0] for a in AXES]
MODEL = VariationModel([dict(zip(AXIS_TAGS, loc)) for loc in LOCS], axisOrder=AXIS_TAGS)
MODEL_BASE = VariationModel([dict(zip(AXIS_TAGS, loc)) for loc in LOCS[:NB]], axisOrder=AXIS_TAGS)
LOCAL_TOL = 3.0
SPIKE = 20.0    # a point carried off the outline counts its distance over this (a spike has little area)


def _interpolate(al, loc, model=MODEL):
    """The masters' outlines (aligned) at loc, as the variable font has
    them; a point's further fields (an italic point's on-curve flag) are
    the first master's."""
    import numpy as np
    flat = [np.array([c for r in m for q in r for c in q[:2]], dtype=float) for m in al]
    v = model.interpolateFromMasters(dict(zip(AXIS_TAGS, LOC(loc))), flat)
    out, i = [], 0
    for r in al[0]:
        out.append([(v[i + 2 * j], v[i + 2 * j + 1]) + tuple(q[2:]) for j, q in enumerate(r)])
        i += 2 * len(r)
    return out


def _predicted(lead, nodes, model):
    """Every node's outline: the leading masters' (aligned), the rest
    predicted from them by their model."""
    return list(lead) + [_interpolate(lead, m, model) for m in nodes[len(lead):]]


_MODELS: dict = {}


def _model(mlocs):
    """The variation model over a glyph's masters (the font's, and any of its own)."""
    key = tuple(mlocs)
    if key not in _MODELS:
        _MODELS[key] = VariationModel([dict(zip(AXIS_TAGS, LOC(m))) for m in mlocs], axisOrder=AXIS_TAGS)
    return _MODELS[key]


# more places between the masters, off the axes, that a glyph's own masters
# are chosen from (VALID, in the final check, stays apart from both)
REFINE = [(500, -50, 50), (300, -50, 0), (600, 50, 50), (750, -75, 75), (850, 50, 25), (250, 50, 0),
          (650, -50, 100), (450, -100, 50), (550, 100, 25), (350, 25, 75), (800, -25, 25), (700, 100, 75)]


def _errors(al, exact, mlocs=None, where=None):
    """The difference at each CHECK location (or ``where``) between the
    font's outline and the exact drawing: the mean distance between the
    outlines, or the farthest a point is carried off it over SPIKE,
    whichever is more."""
    model = _model(mlocs or MASTERS)
    out = {}
    try:
        out.update(_dense_errors(al, mlocs or MASTERS))
    except Exception:  # noqa: BLE001
        pass
    for loc in (where or CHECK):
        try:
            ex = exact(loc)
            got = _shp([r for r in _interpolate(al, loc, model) if len(set(r)) >= 3])
            err = max(got.symmetric_difference(ex).area / max(ex.boundary.length, 1),
                      got.boundary.hausdorff_distance(ex.boundary) / SPIKE)
        except Exception:  # noqa: BLE001
            err = 1e9
        out[loc] = err
        if err > 1e8:
            break
    return out


def _error(al, exact, mlocs=None):
    return max(_errors(al, exact, mlocs).values())


# Between the check's places: the interpolation looked at on a grid over the
# whole design space (tools/vfdense.py), against no drawing: a point carried
# outside the box its masters span, or the outline crossing itself deeper
# than the masters do (by how far a point would have to move back to undo
# it), DENSE_TOL of either as bad as LOCAL_TOL (tools/vf_spikes.py's
# tolerance), so the alignment that keeps the font clean everywhere wins,
# and a glyph's finer grid goes where it is not. (A crossing counted as a
# fixed cost, ten times LOCAL_TOL, made a glyph take a 116-unit spike over a
# twist 2 units deep.)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import vfdense  # noqa: E402
DENSE = [(w, g, t) for w in range(100, 901, 50) for g in (-100, -50, 0, 50, 100) for t in (0, 25, 50, 75, 100)]
DENSE_TOL = 20.0    # font units: a point this far past its masters, or a crossing this deep, is as bad as LOCAL_TOL


def _dense_errors(al, mlocs):
    import numpy as np
    model = _model(mlocs)
    base, D, R, nxt = vfdense.from_masters(al, [LOC(m) for m in mlocs], model)
    masters_pts = np.array([[q[:2] for r in m for q in r] for m in al], dtype=float)
    locs = np.array([LOC(m) for m in DENSE])
    lo, hi = masters_pts.min(axis=0), masters_pts.max(axis=0)
    mask = vfdense.pair_mask(nxt)
    d0 = float(vfdense.deepest(np, masters_pts, nxt, mask).max())
    P = vfdense.outlines(np, locs, base, D, R)
    d = vfdense.overshoot(np, P, lo, hi)
    x = vfdense.deepest(np, P, nxt, mask)
    out = {}
    for i, loc in enumerate(DENSE):
        e = max(d[i], x[i] - d0 if x[i] >= vfdense.DEPTH else 0.0) * LOCAL_TOL / DENSE_TOL
        if e > LOCAL_TOL:
            out[loc] = e
    return out


# A glyph that still interpolates off its drawings somewhere gets a finer grid:
# the worst place's value on an axis its grid lacks, every master of that
# plane drawn (a variable font's variations are stored glyph by glyph: masters
# one glyph needs cost the others nothing; gvar, rewritten after the build:
# _own_masters). Then every glyph drops the masters its drawings do not need
# (_prune: certified within PRUNE units everywhere).
NODES_MAX = 132
DEBUG = bool(__import__('os').environ.get('ARRIS_VF_DEBUG'))     # every candidate's error, as tried
# Where a glyph's exact drawing jumps between one weight and the next
# (tools/vf_planes.py, from a census of the drawings): per glyph, (wght,
# GRAD, WTCH) places just before and just after each jump. The check looks
# there too, and a finer grid can take a plane at either, so a change the
# drawing makes in ten units of weight stays within those ten units in the
# font instead of being drawn out between two masters fifty or a hundred
# apart (a slit filling, a bar fusing, a stub going).
PLANES: dict = {}
_planes_path = __import__('os').environ.get(
    'ARRIS_VF_PLANES', str(Path(__file__).resolve().parent / ('vf_planes_italic.json' if ITALIC else 'vf_planes.json')))
if _planes_path and Path(_planes_path).is_file():
    import json as _json
    PLANES = {k: [tuple(q) for q in v] for k, v in _json.load(open(_planes_path)).items()}
    print(_took(), 'census planes for', len(PLANES), 'glyphs, from', _planes_path)
REFINE_STEPS = int(__import__('os').environ.get('ARRIS_VF_REFINE', '12'))   # places tried for a finer grid
PRUNE = float(__import__('os').environ.get('ARRIS_VF_PRUNE', '2.0'))   # font units: what a dropped master may move


def _prune(nodes, rings, advs):
    """The masters of the glyph's grid it needs: one at a time, those the
    rest reproduce best first (a corner before an edge, an edge before the
    weight axis), each dropped while the masters left reproduce every one
    dropped (each point, and the advance) within PRUNE units, and within
    PRUNE of the box the masters left span. Every region
    of a model over any of the grid's nodes starts and ends at grid values,
    so the model is multilinear within each of the grid's cells, as the
    full grid's is: what holds at the dropped masters holds everywhere
    between them (and where the grade's and the watch's changes are linear
    in the weight, as for most glyphs, the masters left are 1.001's sparse
    layout or fewer)."""
    import numpy as np
    vals = np.array([[q[:2] for r in rings[i] for q in r] + [(advs[i], 0.0)] for i in range(len(nodes))], dtype=float)
    loc = [dict(zip(AXIS_TAGS, LOC(m))) for m in nodes]

    def off(keep, at):
        """The farthest the model over keep is from the masters at, or
        they from the box the masters kept span (the font's own masters
        must span every point's range: tools/vf_spikes.py reads a point
        past them as carried off)."""
        model = VariationModel([loc[i] for i in keep], axisOrder=AXIS_TAGS)
        deltas = np.array(model.getDeltas(list(vals[keep])))
        lo, hi = vals[keep].min(axis=0), vals[keep].max(axis=0)
        return max(max(float(np.abs(np.tensordot(model.getScalars(loc[j]), deltas, 1) - vals[j]).max()),
                       float(np.maximum(lo - vals[j], vals[j] - hi).max())) for j in at)
    every = list(range(len(nodes)))
    default = nodes.index(DEFAULT)
    alone = {i: off([j for j in every if j != i], [i]) for i in every if i != default}
    order = sorted(alone, key=lambda i: (-sum(1 for v in nodes[i][1:] if v), alone[i]))
    keep, gone = every, []
    for i in order:
        if alone[i] > PRUNE:
            continue
        trial = [j for j in keep if j != i]
        if off(trial, gone + [i]) <= PRUNE:
            keep, gone = trial, gone + [i]
    return [nodes[i] for i in keep]


IUP_TOLS = (2.0, 1.0, 0.5)  # font units: IUP tolerances tried, coarsest first ...
IUP_TOL = 2.0               # ... the coarsest that keeps every master of the grid within this
TARGET = float(__import__('os').environ.get('ARRIS_VF_TARGET', '8.9e6'))   # bytes: the font, under fontbakery's 9 MB


def _tuples(mlocs, outlines, advances, coords0=None, ends=None):
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
    import numpy as np
    from fontTools.ttLib.tables.TupleVariation import TupleVariation
    from fontTools.varLib.iup import iup_delta, iup_delta_optimize
    from fontTools.varLib.models import supportScalar
    pts = lambda rings: [(round(q[0]), round(q[1])) for r in rings for q in r[::-1]]
    vals = [np.array(pts(o) + [(0, 0), (round(a), 0), (0, 0), (0, 0)], dtype=float) for o, a in zip(outlines, advances)]
    if coords0 is None:
        d0 = mlocs.index(DEFAULT)
        coords0 = [tuple(v) for v in vals[d0]]
        ends = [int(e) for e in np.cumsum([len(r) for r in outlines[d0]]) - 1]
    model = _model(mlocs)
    raw = []
    for d, sup in zip(model.getDeltas(vals), model.supports):
        if not sup:
            continue
        coords = [(int(round(x)), int(round(y))) for x, y in d]
        if any(tag == 'GRAD' and peak for tag, (lo, peak, hi) in sup.items()):
            # grade never moves an advance: rounding the interpolated
            # advances must not make it do so by a unit
            coords[-4:] = [(0, 0)] * 4
        if any(c != (0, 0) for c in coords):
            raw.append((sup, coords))
    size = lambda tv: sum(map(len, tv.compile(AXIS_TAGS)))
    # the grid the masters are nodes of: every value each axis has
    vals_by_axis = [sorted({m[i] for m in list(mlocs) + NODES}) for i in range(3)]
    grid = [dict(zip(AXIS_TAGS, LOC(m))) for m in product(*vals_by_axis)]
    scal = np.array([[supportScalar(g, sup) for sup, _ in raw] for g in grid]) if raw else None
    for tol in IUP_TOLS:
        tvs, errs = [], []
        for sup, coords in raw:
            tv = TupleVariation(dict(sup), coords)
            err = np.zeros((len(coords), 2))
            opt = iup_delta_optimize(coords, coords0, ends, tolerance=tol)
            if None in opt:
                small = TupleVariation(dict(sup), opt)
                if size(small) < size(tv):
                    tv = small
                    err = np.array(iup_delta(opt, coords0, ends), dtype=float) - np.array(coords, dtype=float)
            tvs.append(tv)
            errs.append(err)
        if not raw or tol == IUP_TOLS[-1]:
            break
        if np.abs(np.tensordot(scal, np.array(errs), 1)).max() <= IUP_TOL:
            break
    return tvs


def _gvar_bytes(tvs):
    return sum(sum(map(len, tv.compile(AXIS_TAGS))) for tv in tvs)


# Composites (tools/composites.py): a glyph that is other glyphs of the font,
# translated, at every master of the grid and every check place (an accented
# letter, a .case form) is carried as a TrueType composite: no alignment of
# its own, its variations only where its components stand.
import composites  # noqa: E402
COMPOSITES = {}                                         # glyph -> (components, {place: [(dx, dy)]})


def _contours_at(n, loc):
    """n's contours at loc as the font carries them (the italic curved, its
    points (x, y, on))."""
    rings, rec, _ = _place(n, ps[loc] if loc in ps else P(loc), record=ITALIC)
    if not ITALIC:
        return [[q[:2] for q in r] for r in rings]
    q = P(loc)
    if REGISTRY[n].cell:
        q = q.with_(slant=0.0)
    return [[(x, y, float(on)) for x, y, on in c] for c in ital.outline(rings, rec, q)]


def _composite(n):
    """(its components, {place: their offsets}) if n is exactly its
    components translated at every master of the grid and every check
    place; else None."""
    try:
        stamped = [s[1].name for s in getattr(_draw_glyph(n, P(DEFAULT)), 'extra_src', [])]
    except Exception:  # noqa: BLE001
        stamped = []
    comps = [c for c in composites.candidates(n, stamped) if c in NAMESET]
    if not comps:
        return None
    kept, offs = None, {}
    for loc in NODES + [c for c in CHECK if c not in NODES]:
        d = composites.decompose(lambda x: _contours_at(x, loc), n, comps)
        if d is None or (kept is not None and [c for c, _, _ in d] != kept):
            return None
        kept = [c for c, _, _ in d]
        offs[loc] = [(dx, dy) for _, dx, dy in d]
    return kept, offs


def _glyph(n):
    """One glyph, start to end: (name, its upright rings and advance per
    master of the font (for the kerning), its outlines per master as the
    font carries them, the alternative taken or None, the error before and
    after, why it cannot vary or None, its grid (the masters gvar
    interpolates it between, and its outlines at those the font has not),
    the exact outlines drawn at the check's places). Only plain outlines go
    back to the main process (the drawings' records hold functions).

    Candidates, in order, until one interpolates within LOCAL_TOL (else the
    best): the grid's masters aligned each against its neighbours, named
    edges first; the grid's masters past the font's (and past BASE)
    predicted from those, as the sparse layout would have them; the masters
    aligned against the one with the most points; and each of those again
    with the masters drawn without the jog closing (geom._close_jogs:
    cleaned of jogs, neighbouring weights can differ in structure where a
    step closes at one and not the next)."""
    def placed(m, jogs=True):
        if not jogs:
            jog, _geom.JOG = _geom.JOG, 0.0
        try:
            names = []
            u = _place(n, ps[m] if m in ps else P(m), record=ITALIC, tags=names)
            return u + (names,)
        finally:
            if not jogs:
                _geom.JOG = jog
    nodes, nm = list(NODES), len(MASTERS)
    up = [placed(m) for m in nodes]
    plain = lambda ups: [(u[0], u[2]) for u in ups[:nm]]
    if not any(u[0] for u in up):
        return n, plain(up), [u[0] for u in up[:nm]], None, 0.0, 0.0, None, None, {}, None, None
    cache, drawn = {}, {}

    def exact(loc):
        if loc not in cache:
            drawn[loc] = _place(n, P(loc), record=ITALIC)
            cache[loc] = _shp(drawn[loc][0])
        return cache[loc]

    def seen(loc):
        """The outline the final check compares the font with at loc, from
        the drawing made here (the italic curved and flattened, font.place)."""
        rings, rec, _ = drawn[loc]
        if not ITALIC:
            return rings
        q = P(loc)
        if REGISTRY[n].cell:
            q = q.with_(slant=0.0)
        return ital.polylines(ital.outline(rings, rec, q))

    comp = _composite(n)
    if comp is not None:
        # carried as a composite: its outlines (for anchors and kerning) as
        # drawn, the exact ones at the check's places for the final check
        for loc in CHECK:
            exact(loc)
        if ITALIC:
            rings = [_contours_at(n, m) for m in MASTERS]
        else:
            rings = [u[0] for u in up[:nm]]
        shown = {loc: [[tuple(q[:2]) for q in r] for r in seen(loc)] for loc in CHECK}
        return n, plain(up), rings, (True, 'composite', 'composite', 0, None), 0.0, 0.0, None, None, shown, comp, None

    LEADS = ((len(nodes), None), (nm, MODEL), (NB, MODEL_BASE))

    def candidates(variant, how):
        """(kind, how many masters lead, aligned outlines, the masters they
        are at): the whole grid aligned; then, for the font's masters and
        for BASE, the rest predicted from them, as aligned with the whole
        grid and as aligned by themselves; and the font's masters alone,
        without the grid, as 1.001 had them (sparse: aligned through a tree
        over many more masters, a pair of neighbours can pair worse, ⇖
        between the grade's ends at Regular, and where the sparse layout
        adds up well the grid's cells can do worse, G at (850, 75, 75))."""
        rings = [u[0] for u in variant]
        names = [u[3] for u in variant] if how == 'named' else None

        def aligned(k):
            return align(rings[:k], None if how == 'star' else [LOC(m) for m in nodes[:k]],
                         names=None if names is None else names[:k])
        # the sparse layout first: where it holds everywhere (the dense
        # check: nothing past its masters, no crossing, DENSE_TOL), a glyph
        # carries 28 masters' variations, not a grid's 60 and more (the
        # variable fonts would be twice 1.001's size, past fontbakery's 9 MB)
        try:
            lead = aligned(nm)
            yield 'sparse', nm, lead, nodes[:nm]
        except ValueError:
            lead = None
        try:
            full = aligned(len(nodes))
            yield 'grid', len(nodes), full, nodes
        except ValueError:
            full = None
        for k, model in LEADS[1:]:
            if full is not None:
                yield 'predicted grid', k, _predicted(full[:k], nodes, model), nodes
            try:
                sub = lead if k == nm else aligned(k)
            except ValueError:
                continue
            if sub is not None:
                yield 'predicted grid', k, _predicted(sub, nodes, model), nodes
    total = lambda es: sum(min(e, 100) for e in es.values())
    best, first = None, None
    for jogs in (True, False):
        variant = up if jogs else [placed(m, False) for m in nodes]
        for how in ('named', 'tree', 'star'):
            for kind, k, al, ns in candidates(variant, how):
                # (the sparse layout also at the grid's other masters: a
                # model over any of the grid's nodes is multilinear within
                # its cells, so where it matches the drawings at every node
                # it is as good as the grid everywhere between)
                where = CHECK + [m for m in nodes if m not in ns]
                err = max(_errors(al, exact, ns, where).values())
                if DEBUG:
                    es = _errors(al, exact, ns, where)
                    print(f'  {n} {"jogs" if jogs else "no jogs"} {how} {kind} {k}: {err:.1f} at {max(es, key=es.get)}', flush=True)
                first = err if first is None else first
                if best is None or err < best[0]:
                    best = (err, al, variant, (jogs, how, kind, k, GRID_AXES), ns)
                if best[0] <= LOCAL_TOL:
                    break
            if best is not None and best[0] <= LOCAL_TOL:
                break
        if best is not None and best[0] <= LOCAL_TOL:
            break
    best0, errs = best, None
    # the places the census found this glyph's drawing jumping at (PLANES):
    # the refinement measures there too, and a plane there confines the jump
    jumps = [q for q in PLANES.get(n, []) if q not in CHECK and q not in REFINE]
    if jumps and best is not None and best[0] <= LOCAL_TOL:
        _, al_b, _, _, ns_b = best
        if max(_errors(al_b, exact, ns_b, jumps).values()) > LOCAL_TOL:
            best = (max(_errors(al_b, exact, ns_b, jumps).values()),) + tuple(best[1:])
    if best is not None and best[0] > LOCAL_TOL:
        # a finer grid (above), from the chosen way's alignment with every
        # master drawn, a plane at a time while it helps
        _, _, variant, (jogs, how, _, _, _), _ = best
        axes, ns, var = [list(a) for a in GRID_AXES], list(nodes), list(variant)
        places = CHECK + REFINE + jumps

        def realign(var, ns):
            return align([u[0] for u in var], None if how == 'star' else [LOC(m) for m in ns],
                         names=[u[3] for u in var] if how == 'named' else None)
        try:
            al = realign(var, ns)
            errs = _errors(al, exact, ns, places)
        except ValueError:
            errs = None
        tried = set()
        start = (max(errs.values()), total(errs)) if errs else None
        while errs and len(tried) < REFINE_STEPS:
            # the worst place not yet tried, its value on each axis the grid
            # lacks tried in turn (a plane that does not help, or will not
            # align, is passed over)
            todo = [(e, loc) for loc, e in errs.items()
                    if e > LOCAL_TOL and loc not in tried and any(v not in a for v, a in zip(loc, axes))]
            if not todo:
                break
            e, place = max(todo)
            tried.add(place)
            step = None
            for i in range(3):
                if place[i] in axes[i]:
                    continue
                ax2 = [sorted(a + [place[i]]) if j == i else a for j, a in enumerate(axes)]
                have = set(ns)
                new = [m for m in product(*ax2) if m not in have]
                if len(ns) + len(new) > NODES_MAX:
                    continue
                var2 = var + [placed(m, jogs) for m in new]
                try:
                    al2 = realign(var2, ns + new)
                except ValueError:
                    continue
                errs2 = _errors(al2, exact, ns + new, places)
                if step is None or total(errs2) < total(step[0]):
                    step = (errs2, ax2, ns + new, var2, al2)
            # kept if the glyph comes nearer its drawings overall (the worst
            # place is now on the grid; the next may be as bad)
            if step is not None and total(step[0]) < 0.98 * total(errs):
                errs, axes, ns, var, al = step
            if DEBUG:
                print(f'  {n} finer grid, tried {place}: {max(errs.values()):.1f}, axes {axes}', flush=True)
        # kept if it does better than the best candidate (not only better
        # than the grid it started from: a predicted one may be best), or
        # as well with the glyph nearer its drawings overall
        if errs is not None and len(ns) > len(nodes) and (
                max(errs.values()) < best[0] or (max(errs.values()) <= best[0] and total(errs) < start[1])):
            best = (max(errs.values()), al, var, (jogs, how, 'finer grid', len(ns), axes), ns)
    def finish(best):
        """(outlines per master of the font, the drawings there, the choice,
        its error, its own grid or None, why it cannot vary or None)."""
        why, choice, err, own = None, None, first, None
        rings, ups = None, up[:nm]
        if best is None:
            why = 'masters will not align'
        else:
            err, al, up_all, choice, nodes_ = best
            _, _, kind, k, axes = choice
            try:
                rings = al
                if ITALIC:
                    # (terminal cells are curved but never slanted: font.place)
                    cps = [P(m).with_(slant=0.0) if REGISTRY[n].cell else P(m) for m in nodes_]
                    if kind != 'predicted grid':
                        rings = ital.aligned_outlines(al, [u[0] for u in up_all[:len(nodes_)]],
                                                      [u[1] for u in up_all[:len(nodes_)]], cps)
                    else:
                        # the rest predicted from the leading masters' italic
                        # outlines, curves and all
                        rings = _predicted(ital.aligned_outlines(al[:k], [u[0] for u in up_all[:k]],
                                                                 [u[1] for u in up_all[:k]], cps[:k]),
                                           nodes_, dict((a, b) for a, b in LEADS)[k])
                # every master's advance as the font has it (the font's masters'
                # interpolated: HVAR and the kerning come from those)
                base_adv = [u[2] for u in up_all[:nm]]
                advs = base_adv + [MODEL.interpolateFromMasters(dict(zip(AXIS_TAGS, LOC(m))), base_adv)
                                   for m in nodes_[nm:]]
                if kind != 'sparse':                        # (sparse: the font's masters alone)
                    keep = set(_prune(nodes_, rings, advs))
                    own = ([m for m in nodes_ if m in keep],
                           {m: rings[i] for i, m in enumerate(nodes_) if m in keep and i >= nm})
                rings = rings[:nm]
                ups = up_all[:nm]
            except ValueError as e:
                why = str(e)
        if why is not None:
            # cannot vary: every master carries the default outline (reported)
            d = place(n, ps[DEFAULT])[0]
            rings = [d for _ in MASTERS]
            own = None
        return rings, ups, choice, err, own, why

    def cost(res):
        """The bytes its variations would take."""
        rings, ups, _, _, own, why = res
        if why is not None:
            return 0
        mlocs = own[0] if own else MASTERS
        outlines = [rings[MASTERS.index(m)] if m in MASTERS else own[1][m] for m in mlocs]
        base_adv = [u[2] for u in ups]
        advances = [base_adv[MASTERS.index(m)] if m in MASTERS else
                    MODEL.interpolateFromMasters(dict(zip(AXIS_TAGS, LOC(m))), base_adv) for m in mlocs]
        return _gvar_bytes(_tuples(mlocs, outlines, advances))

    res = finish(best)
    rings, up_m, choice, err, own, why = res
    # a finer grid: the glyph without it too, what it gains (the error over
    # the check's and the refinement's places) and what it costs (bytes), so
    # the font can keep the finer grids that buy most while it fits TARGET
    alt = None
    if best is not best0 and best0 is not None and errs is not None and why is None:
        res0 = finish(best0)
        if res0[5] is None:
            _, al0, _, _, ns0 = best0
            gain = total(_errors(al0, exact, ns0, places)) - total(errs)
            alt = (res0[0], res0[4], gain, cost(res) - cost(res0))
    # the exact outlines at the check's places, drawn here already: the final
    # check need not draw them again
    shown = {loc: [[tuple(q[:2]) for q in r] for r in seen(loc)] for loc in CHECK if loc in drawn}
    up = up_m
    return n, plain(up), rings, choice, first, err, why, own, shown, None, alt


from multiprocessing import get_context  # noqa: E402
WORKERS = int(__import__('os').environ.get('ARRIS_VF_WORKERS', '8'))
upright = {m: {} for m in MASTERS}
aligned = {w: {} for w in MASTERS}
frozen, chosen = [], []
OWN = {}                                                    # glyph -> (its grid's masters, outlines at those past the font's)
ALTS = {}                                                   # glyph -> (outlines, own) with its finer grid, gain, bytes
SHOWN = {}                                                  # (glyph, location) -> exact outline, for the check
with get_context('fork').Pool(WORKERS) as pool:
    for n, up, rings, choice, e0, e1, why, own, shown, comp, alt in pool.imap_unordered(_glyph, names, chunksize=4):
        if comp is not None:
            COMPOSITES[n] = comp
        if alt is not None:
            # (the font starts without the finer grid: TARGET decides)
            ALTS[n] = (rings, own, alt[2], alt[3])
            rings, own = alt[0], alt[1]
        for loc, r in shown.items():
            SHOWN[n, loc] = r
        if why is not None:
            frozen.append((n, why))
        if own:
            OWN[n] = own
        if choice is not None and choice[:3] != (True, 'named', 'grid'):
            chosen.append((n, 'jogs kept' if not choice[0] else '', choice[1], choice[2], round(e0, 1), round(e1, 1)))
        for i, m in enumerate(MASTERS):
            upright[m][n] = up[i]                           # (rings, advance)
            aligned[m][n] = (rings[i], up[i][1])
print(_took(), 'placed and aligned', len(names), 'glyphs in', len(MASTERS), 'masters;', len(chosen),
      'took an alternative, interpolating better so:', sorted(chosen, key=lambda c: -c[4])[:12])
print(sum(c[3] == 'sparse' for c in chosen), 'glyphs keep the font\'s masters alone;', sum(c[3] == 'predicted grid' for c in chosen), 'masters predicted from the font\'s;',
      sum(c[3] == 'finer grid' for c in chosen), 'took a finer grid; after pruning,',
      f'{sum(len(v[0]) for v in OWN.values()) / max(len(OWN), 1):.1f} masters a glyph on average (of {len(NODES)}),',
      sum(len(v[1]) for v in OWN.values()), 'past the font\'s in all')


def _flat(n, seen=()):
    """A composite's components down to glyphs that are none (nested
    components render badly in some variable-font implementations:
    fontbakery's nested_components), their offsets added up at every place."""
    cs, offs = COMPOSITES[n]
    flat, out = [], {loc: [] for loc in offs}
    for k, c in enumerate(cs):
        if c in COMPOSITES and c not in seen:
            ccs, coffs = _flat(c, seen + (n,))
            flat += ccs
            for loc in offs:
                dx, dy = offs[loc][k]
                out[loc] += [(dx + a, dy + b) for a, b in coffs[loc]]
        else:
            flat.append(c)
            for loc in offs:
                out[loc].append(offs[loc][k])
    return flat, out


COMPOSITES.update({n: _flat(n) for n in list(COMPOSITES)})
print(len(COMPOSITES), 'glyphs carried as composites (their components translated at every master)')
print('aligned;', len(frozen), 'glyphs could not vary:', frozen[:10])


def kern_outline(w, n):
    if ITALIC:
        return ital.polylines(place(n, ps[w])[0])
    return upright[w][n][0]


# kerning: the same pairs in every master, each master's own values
kernable = [n for n in names if REGISTRY[n].kind in ('cap', 'lower') or n in KERN_PUNCT]


def _kern_master(w):
    return w, kerns({n: (kern_outline(w, n), round(upright[w][n][1])) for n in kernable}, ps[w], light(ps[w]))


with get_context('fork').Pool(WORKERS) as pool:     # each master's kerning is its own
    pairs_by = dict(pool.imap_unordered(_kern_master, [w for w in MASTERS if w[1] == 0]))
for w in MASTERS:                       # grade keeps every advance, kerning included
    if w[1] != 0:
        pairs_by[w] = pairs_by[(w[0], 0, w[2])]
all_pairs = set().union(*pairs_by.values())
print(_took(), len(all_pairs), 'kerning pairs')

def _composite_masters(vf):
    """A composite's variations: where its components stand, over the
    grid's masters it needs (its offsets pruned like an outline's points,
    _prune), the advance as the font's masters have it."""
    import numpy as np
    from fontTools.ttLib.tables.TupleVariation import TupleVariation
    gvar, glyf = vf['gvar'], vf['glyf']
    index = {m: i for i, m in enumerate(MASTERS)}
    for n, (cs, offs) in COMPOSITES.items():
        base_adv = [aligned[m][n][1] for m in MASTERS]
        advs = [base_adv[index[m]] if m in index else MODEL.interpolateFromMasters(dict(zip(AXIS_TAGS, LOC(m))), base_adv)
                for m in NODES]
        keep = _prune(NODES, [[offs[m]] for m in NODES], advs)
        default = [(c.x, c.y) for c in glyf[n].components]   # (as the font has them, rounded)
        vals = []
        for m in keep:
            pts = default if m == DEFAULT else offs[m]
            a = base_adv[index[m]] if m in index else MODEL.interpolateFromMasters(dict(zip(AXIS_TAGS, LOC(m))), base_adv)
            vals.append(np.array(list(pts) + [(0, 0), (a if m != DEFAULT else round(a), 0), (0, 0), (0, 0)], dtype=float))
        model = _model(keep)
        tvs = []
        for d, sup in zip(model.getDeltas(vals, round=np.round), model.supports):
            if not sup:
                continue
            coords = [(int(x), int(y)) for x, y in d]
            if any(tag == 'GRAD' and peak for tag, (lo, peak, hi) in sup.items()):
                coords[-4:] = [(0, 0)] * 4
            if any(c != (0, 0) for c in coords):
                tvs.append(TupleVariation(dict(sup), coords))
        gvar.variations[n] = tvs


FEA = '' if __import__('os').environ.get('ARRIS_VF_ONLY') else fea()   # (a trial's few glyphs: no features)
tmp = Path(tempfile.mkdtemp())


def _build_master(i):
    m = MASTERS[i]
    pairs = {pr: pairs_by[m].get(pr, 0) for pr in all_pairs}
    build(str(tmp / f'master-{i}.ttf'), names, ps[m], family=family, style=style_name(m[0]), weight=m[0],
          fea=FEA, placed=aligned[m], kern_pairs=pairs, stat=False,
          components={n: [(c, dx, dy) for c, (dx, dy) in zip(cs, offs[m])] for n, (cs, offs) in COMPOSITES.items()})
    return i


def _variations(vf):
    """Every glyph's variations as its masters have them (_tuples: its own
    grid's, or the font's masters'), every composite's (_composite_masters)."""
    gvar, glyf, hmtx = vf['gvar'], vf['glyf'], vf['hmtx'].metrics
    index = {m: i for i, m in enumerate(MASTERS)}
    for n in names:
        if n in COMPOSITES or glyf[n].numberOfContours <= 0:     # (composites below; empty glyphs vary nothing)
            continue
        mlocs = OWN[n][0] if n in OWN else MASTERS
        base_adv = [aligned[m][n][1] for m in MASTERS]
        outlines = [aligned[m][n][0] if m in index else OWN[n][1][m] for m in mlocs]
        advances = [base_adv[index[m]] if m in index else
                    MODEL.interpolateFromMasters(dict(zip(AXIS_TAGS, LOC(m))), base_adv) for m in mlocs]
        coords0, ctrl = glyf._getCoordinatesAndControls(n, hmtx, None)
        gvar.variations[n] = _tuples(mlocs, outlines, advances, coords0, ctrl.endPts)


def make_vf():
    """The variable font from the master fonts as the glyphs now stand."""
    doc = DesignSpaceDocument()
    for tag, name, lo, df, hi in AXES:
        ax = AxisDescriptor()
        ax.tag, ax.name, ax.minimum, ax.default, ax.maximum = tag, name, lo, df, hi
        doc.addAxis(ax)
    with get_context('fork').Pool(WORKERS) as pool:     # the master fonts are independent
        list(pool.imap_unordered(_build_master, range(len(MASTERS))))
    for i, m in enumerate(MASTERS):
        src = SourceDescriptor()
        src.path, src.location = str(tmp / f'master-{i}.ttf'), {'Weight': m[0], 'Grade': m[1], 'Watch': m[2]}
        doc.addSource(src)
    for n, (alt, regions) in FORMS.items():
        if regions:
            rule = RuleDescriptor()
            rule.name = f'{n} second form'
            rule.conditionSets = [[{'name': 'Weight', 'minimum': w, 'maximum': 900},
                                   {'name': 'Grade', 'minimum': glo, 'maximum': ghi},
                                   {'name': 'Watch', 'minimum': tlo, 'maximum': thi}]
                                  for w, glo, ghi, tlo, thi in regions]
            rule.subs = [(n, alt)]
            doc.addRule(rule)
    for w, nm in NAMES.items():
        inst = InstanceDescriptor()
        inst.familyName, inst.styleName, inst.location = family, style_name(w), {'Weight': w, 'Grade': 0, 'Watch': 0}
        doc.addInstance(inst)
    vf, _, _ = varlib_build(doc)
    from fontTools.otlLib.builder import buildStatTable
    buildStatTable(vf, [
        {'tag': 'wght', 'name': 'Weight',
         'values': [{'value': w, 'name': nm, 'flags': 0x2 if w == 400 else 0} for w, nm in NAMES.items()]},
        {'tag': 'GRAD', 'name': 'Grade', 'values': [{'value': 0, 'name': 'Normal', 'flags': 0x2}]},
        {'tag': 'WTCH', 'name': 'Watch', 'values': [{'value': 0, 'name': 'Measured', 'flags': 0x2},
                                                    {'value': 100, 'name': 'Watch'}]},
        # the upright and the italic are one family: each names its place on ital
        {'tag': 'ital', 'name': 'Italic',
         'values': [{'value': 1, 'name': 'Italic'}] if ITALIC else
                   [{'value': 0, 'name': 'Roman', 'flags': 0x2, 'linkedValue': 1}]},
    ])
    _variations(vf)
    if COMPOSITES:
        _composite_masters(vf)
    vf['name'].names = [nm for nm in vf['name'].names if nm.platformID != 1]   # Windows names only
    from arris.font import add_meta
    add_meta(vf)
    return vf


def _size(vf):
    import io
    b = io.BytesIO()
    vf.save(b)
    return len(b.getvalue())


# The font without any glyph's finer grid first; then the finer grids that
# buy most accuracy per byte (ALTS: the error they take off the check's and
# the refinement's places, for the bytes their variations add), while the
# font stays under TARGET.
vf = make_vf()
size = _size(vf)
print(_took(), f'the font without finer grids: {size / 1e6:.2f} MB')
if ALTS and size < TARGET:
    room = TARGET - size
    take = []
    for n, (rings, own, gain, extra) in sorted(ALTS.items(), key=lambda kv: (kv[1][3] > 0, -kv[1][2] / max(kv[1][3], 1))):
        if gain <= 0:
            continue
        if extra <= room:
            take.append(n)
            room -= max(extra, 0)
    for n in take:
        rings, own = ALTS[n][0], ALTS[n][1]
        for i, m in enumerate(MASTERS):
            aligned[m][n] = (rings[i], aligned[m][n][1])
        OWN.pop(n, None)
        if own:
            OWN[n] = own
    if take:
        vf = make_vf()
        size = _size(vf)
    print(_took(), f'{len(take)} of {len(ALTS)} glyphs keep their finer grid: {size / 1e6:.2f} MB')
if size > TARGET:
    print(f'WARNING: {size / 1e6:.2f} MB, over the {TARGET / 1e6:.1f} MB target')
# (a trial's few glyphs go apart: build/trial/, the fonts in build/ untouched)
OUT = Path(__import__('os').environ.get('ARRIS_VF_OUT') or Path('build') / ('trial' if __import__('os').environ.get('ARRIS_VF_ONLY') else ''))
OUT.mkdir(parents=True, exist_ok=True)
out = OUT / ('Arris-Italic[GRAD,WTCH,wght].ttf' if ITALIC else 'Arris[GRAD,WTCH,wght].ttf')
vf.save(out)
print(_took(), 'wrote', out)

# --- check: the variable font against exact drawings between the masters ----
def _check_at(w):
    """Every glyph of the built font at w against its exact drawing."""
    from arris.geom import rings_to_shapely
    inst = instantiateVariableFont(TTFont(out), {'wght': w[0], 'GRAD': w[1], 'WTCH': w[2]})
    glyf = inst['glyf']
    p = P(w)
    res = []
    for n in names:
        if (n, tuple(w)) in SHOWN:                          # drawn while aligning
            exact = rings_to_shapely(SHOWN[n, tuple(w)])
        else:
            rings, adv = place(n, p)
            exact = rings_to_shapely(ital.polylines(rings) if ITALIC else rings)
        g = glyf[n]
        coords, ends, flags = g.getCoordinates(glyf)
        pts, start = list(coords), 0
        got = []
        for e in ends:
            c = [(q[0], q[1], bool(f & 1)) for q, f in zip(pts[start:e + 1], flags[start:e + 1])][::-1]
            got.append(ital.flatten(c) if ITALIC else [q[:2] for q in c])
            start = e + 1
        try:
            interp = rings_to_shapely([r for r in got if len(set(r)) >= 3])
            # mean distance between the two outlines, in font units: the
            # area between them over the exact outline's length; and the
            # farthest a point is off the exact outline (a spike)
            err = interp.symmetric_difference(exact).area / max(exact.boundary.length, 1)
            far = interp.boundary.hausdorff_distance(exact.boundary)
        except Exception:  # noqa: BLE001
            err, far = 1e9, 1e9
        res.append((err, w, n, far))
    return res


# the check, and places between it the build never looked at (a glyph's own
# masters come from CHECK: these say whether it holds in between)
VALID = [(850, 25, 25), (650, -25, 75), (300, 50, 50), (725, 60, 30), (500, -75, 25), (950 - 75, 90, 90),
         (200, -50, 50), (575, 25, 0), (775, 0, 75), (450, 75, 100)]
worst = []
with get_context('fork').Pool(min(WORKERS, len(CHECK) + len(VALID))) as pool:
    for res in pool.imap_unordered(_check_at, CHECK + VALID):
        worst += res
worst.sort(reverse=True)
TOL = 3.0       # font units: a mean outline difference under 0.3% of the em passes
FAR = 60.0      # font units: a point carried farther than this off the outline is a spike
bad = [x for x in worst if x[0] > TOL]
spikes = sorted((x for x in worst if x[3] > FAR), key=lambda x: -x[3])
print(_took(), f'interpolation check: {len(worst)} glyph-weights; mean outline difference worst {worst[0][0]:.1f} units, '
      f'median {sorted(worst)[len(worst) // 2][0]:.2f}; {len(bad)} over {TOL} units; '
      f'{len(spikes)} with a point over {FAR} units off the outline ({len({x[2] for x in spikes})} glyphs)')
for e, w, n, far in worst[:25]:
    print(f'  {n:16} at {w}: {e:.1f} units')
for e, w, n, far in spikes[:15]:
    print(f'  spike: {n:16} at {w}: {far:.0f} units off')
import json  # noqa: E402
(OUT / ('vf_check_italic.json' if ITALIC else 'vf_check.json')).write_text(   # every result, for triage
    json.dumps([[round(e, 2), list(w), n, round(far, 1)] for e, w, n, far in worst]))
