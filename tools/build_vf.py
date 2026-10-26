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
from pathlib import Path

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
# every 100 on the weight axis up to 700 (the 1's flag, ŉ, the digraphs).
BASE = [(w, 0, 0) for w in (100, 200, 300, 400, 500, 600, 700, 750, 800, 850, 900)] + \
    [(w, g, 0) for w in (100, 400, 900) for g in (-100, 100)] + \
    [(w, 0, 100) for w in (100, 400, 600, 800, 900)]
# Masters where the grade and the watch meet. Without them the font adds
# the grade's change and the watch's there, and a point that slides along
# one edge as the grade moves and along another as the watch does (a
# feature present in both, absent in the plain master) is carried off the
# outline: Ç Ø Δ z ₰ by 100 to 440 units at (900, 100, 100). Per glyph, a
# corner master carries the exact drawing where it aligns with the others
# and interpolates better so, else the outline the other masters predict
# there (no change: ŀ, whose dot meets its l at the heavy corner, 2026-10-25).
CORNERS = [(w, g, 100) for w in (100, 400, 900) for g in (-100, 100)]
MASTERS = BASE + CORNERS
NB = len(BASE)
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
if __import__('os').environ.get('ARRIS_VF_ONLY'):          # a trial build of a few glyphs (writes build/ as usual)
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
print('forms:', {n: (a, r[:2], len(r)) for n, (a, r) in FORMS.items()})

ps = {m: P(m) for m in MASTERS}

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


def _predicted(base):
    """Corner masters predicted from the others (all masters' outlines)."""
    return list(base) + [_interpolate(base, c, MODEL_BASE) for c in CORNERS]


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


# A glyph that still interpolates off its drawing somewhere gets masters of its
# own there, one at a time, worst place first, while each makes it better: a
# variable font's variations are stored glyph by glyph, so a master one glyph
# needs costs the others nothing (gvar, rewritten after the build: _own_masters).
OWN_MAX = 8


def _glyph(n):
    """One glyph, start to end: (name, its upright rings and advance per
    master (for the kerning), its outlines per master as the font carries
    them, the alternative taken or None, the error before and after, why it
    cannot vary or None). Only plain outlines go back to the main process
    (the drawings' records hold functions).

    Candidates, in order, until one interpolates within LOCAL_TOL (else the
    best): all masters aligned each against its neighbours; the corners
    predicted instead; the masters aligned against the one with the most
    points; and each of those again with the masters drawn without the jog
    closing (geom._close_jogs: cleaned of jogs, neighbouring weights can
    differ in structure where a step closes at one and not the next)."""
    def placed(m):
        names = []
        u = _place(n, ps[m] if m in ps else P(m), record=ITALIC, tags=names)
        return u + (names,)
    up = [placed(m) for m in MASTERS]
    plain = lambda ups: [(u[0], u[2]) for u in ups]
    if not any(u[0] for u in up):
        return n, plain(up), [u[0] for u in up], None, 0.0, 0.0, None, []
    cache = {}

    def exact(loc):
        if loc not in cache:
            cache[loc] = _shp(_place(n, P(loc), record=ITALIC)[0])
        return cache[loc]

    def candidates(variant, how):
        rings = [u[0] for u in variant]
        locs = None if how == 'star' else LOCS
        names = [u[3] for u in variant] if how == 'named' else None
        try:
            al = align(rings, locs, names=names)
            yield 'exact corners', al
            yield 'predicted corners', _predicted(al[:NB])
        except ValueError:
            try:
                yield 'predicted corners', _predicted(align(rings[:NB], None if locs is None else LOCS[:NB],
                                                            names=None if names is None else names[:NB]))
            except ValueError:
                return
    best, first = None, None
    for jogs in (True, False):
        if not jogs:
            jog, _geom.JOG = _geom.JOG, 0.0
            try:
                variant = [placed(m) for m in MASTERS]
            finally:
                _geom.JOG = jog
        else:
            variant = up
        for how in ('named', 'tree', 'star'):
            for corners, al in candidates(variant, how):
                err = _error(al, exact)
                first = err if first is None else first
                if best is None or err < best[0]:
                    best = (err, al, variant, (jogs, how, corners))
                if best[0] <= LOCAL_TOL:
                    break
            if best is not None and best[0] <= LOCAL_TOL:
                break
        if best is not None and best[0] <= LOCAL_TOL:
            break
    own = []                                                # (location, outline) of the glyph's own masters
    if best is not None and best[0] > LOCAL_TOL:
        # its own masters: from the chosen way's alignment with every master
        # drawn (corners exact), adding the worst place while it helps
        _, _, variant, (jogs, how, _) = best
        mlocs, var = list(MASTERS), list(variant)

        def realign(var, mlocs):
            return align([u[0] for u in var], None if how == 'star' else [LOC(m) for m in mlocs],
                         names=[u[3] for u in var] if how == 'named' else None)
        try:
            al = realign(var, mlocs)
            errs = _errors(al, exact, mlocs, CHECK + REFINE)
            for _ in range(OWN_MAX):
                loc, e = max(errs.items(), key=lambda kv: kv[1])
                if e <= LOCAL_TOL or loc in mlocs:
                    break
                if not jogs:
                    jog, _geom.JOG = _geom.JOG, 0.0
                try:
                    u = placed(loc)
                finally:
                    if not jogs:
                        _geom.JOG = jog
                al2 = realign(var + [u], mlocs + [loc])
                errs2 = _errors(al2, exact, mlocs + [loc], CHECK + REFINE)
                # kept if the glyph comes nearer its drawings overall (the
                # worst place is now exact; the next may be as bad)
                if sum(min(e, 100) for e in errs2.values()) >= 0.98 * sum(min(e, 100) for e in errs.values()):
                    break
                mlocs, var, al, errs = mlocs + [loc], var + [u], al2, errs2
            if len(mlocs) > len(MASTERS) and max(errs.values()) < best[0]:
                best = (max(errs.values()), al, var, (jogs, how, 'own masters', mlocs[len(MASTERS):]))
        except ValueError:
            pass
    why, choice, err = None, None, first
    if best is None:
        why = 'masters will not align'
    else:
        err, al, up_all, choice = best
        mlocs = MASTERS + (choice[3] if choice[2] == 'own masters' else [])
        try:
            rings = al
            if ITALIC:
                # (terminal cells are curved but never slanted: font.place)
                cps = [P(m).with_(slant=0.0) if REGISTRY[n].cell else P(m) for m in mlocs]
                if choice[2] != 'predicted corners':
                    rings = ital.aligned_outlines(al, [u[0] for u in up_all], [u[1] for u in up_all], cps)
                else:
                    # the corners predicted from the others' italic outlines,
                    # curves and all
                    rings = _predicted(ital.aligned_outlines(al[:NB], [u[0] for u in up_all[:NB]],
                                                             [u[1] for u in up_all[:NB]], cps[:NB]))
            own = [(m, rings[len(MASTERS) + i]) for i, m in enumerate(mlocs[len(MASTERS):])]
            rings = rings[:len(MASTERS)]
            up = up_all[:len(MASTERS)]
        except ValueError as e:
            why = str(e)
    if why is not None:
        # cannot vary: every master carries the default outline (reported)
        d = place(n, ps[DEFAULT])[0]
        rings = [d for _ in MASTERS]
        own = []
    return n, plain(up), rings, choice, first, err, why, own


from multiprocessing import get_context  # noqa: E402
WORKERS = int(__import__('os').environ.get('ARRIS_VF_WORKERS', '8'))
upright = {m: {} for m in MASTERS}
aligned = {w: {} for w in MASTERS}
frozen, chosen = [], []
OWN = {}                                                    # glyph -> [(location, outline)]: its own masters
with get_context('fork').Pool(WORKERS) as pool:
    for n, up, rings, choice, e0, e1, why, own in pool.imap_unordered(_glyph, names, chunksize=4):
        if why is not None:
            frozen.append((n, why))
        if own:
            OWN[n] = own
        if choice not in (None, (True, 'named', 'exact corners')):
            chosen.append((n, 'jogs kept' if not choice[0] else '', choice[1], choice[2], round(e0, 1), round(e1, 1)))
        for i, m in enumerate(MASTERS):
            upright[m][n] = up[i]                           # (rings, advance)
            aligned[m][n] = (rings[i], up[i][1])
print('placed and aligned', len(names), 'glyphs in', len(MASTERS), 'masters;', len(chosen),
      'took an alternative, interpolating better so:', sorted(chosen, key=lambda c: -c[4])[:12])
print(sum(c[3] == 'predicted corners' for c in chosen), 'glyphs keep predicted corners;', len(OWN),
      'have masters of their own,', sum(len(v) for v in OWN.values()), 'in all')
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
print(len(all_pairs), 'kerning pairs')

tmp = Path(tempfile.mkdtemp())
doc = DesignSpaceDocument()
for tag, name, lo, df, hi in AXES:
    ax = AxisDescriptor()
    ax.tag, ax.name, ax.minimum, ax.default, ax.maximum = tag, name, lo, df, hi
    doc.addAxis(ax)
FEA = '' if __import__('os').environ.get('ARRIS_VF_ONLY') else fea()   # (a trial's few glyphs: no features)


def _build_master(i):
    m = MASTERS[i]
    pairs = {pr: pairs_by[m].get(pr, 0) for pr in all_pairs}
    build(str(tmp / f'master-{i}.ttf'), names, ps[m], family=family, style=style_name(m[0]), weight=m[0],
          fea=FEA, placed=aligned[m], kern_pairs=pairs, stat=False)
    return i


with get_context('fork').Pool(WORKERS) as pool:     # the master fonts are independent
    list(pool.imap_unordered(_build_master, range(len(MASTERS))))
for i, m in enumerate(MASTERS):
    path = tmp / f'master-{i}.ttf'
    src = SourceDescriptor()
    src.path, src.location = str(path), {'Weight': m[0], 'Grade': m[1], 'Watch': m[2]}
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


def _own_masters(vf):
    """Rewrite the variations of glyphs that have masters of their own:
    one model over all of the glyph's masters, its deltas as the glyph's
    own regions (gvar keeps them glyph by glyph). Points as the master fonts
    carry them (each contour reversed, rounded); the advance (phantom point
    2) follows the font's masters, interpolated at the glyph's own."""
    import numpy as np
    from fontTools.ttLib.tables.TupleVariation import TupleVariation
    gvar = vf['gvar']

    def pts(rings):
        return [(round(q[0]), round(q[1])) for r in rings for q in r[::-1]]
    advs = lambda n: [aligned[m][n][1] for m in MASTERS]
    for n, own in OWN.items():
        mlocs = MASTERS + [m for m, _ in own]
        base_adv = advs(n)
        vals = []
        for i, m in enumerate(MASTERS):
            vals.append(pts(aligned[m][n][0]) + [(0, 0), (round(base_adv[i]), 0), (0, 0), (0, 0)])
        for m, rings in own:
            a = MODEL.interpolateFromMasters(dict(zip(AXIS_TAGS, LOC(m))), base_adv)
            vals.append(pts(rings) + [(0, 0), (round(a), 0), (0, 0), (0, 0)])
        model = _model(mlocs)
        deltas = model.getDeltas([np.array(v, dtype=float) for v in vals])
        supports = model.supports
        tvs = []
        for d, sup in zip(deltas, supports):
            if not sup:
                continue
            coords = [(int(round(x)), int(round(y))) for x, y in d]
            if any(c != (0, 0) for c in coords):
                tvs.append(TupleVariation(dict(sup), coords))
        gvar.variations[n] = tvs


if OWN:
    _own_masters(vf)
vf['name'].names = [nm for nm in vf['name'].names if nm.platformID != 1]   # Windows names only
from arris.font import add_meta  # noqa: E402
add_meta(vf)
out = Path('build') / ('Arris-Italic[GRAD,WTCH,wght].ttf' if ITALIC else 'Arris[GRAD,WTCH,wght].ttf')
vf.save(out)
print('wrote', out)

# --- check: the variable font against exact drawings between the masters ----
def _check_at(w):
    """Every glyph of the built font at w against its exact drawing."""
    from arris.geom import rings_to_shapely
    inst = instantiateVariableFont(TTFont(out), {'wght': w[0], 'GRAD': w[1], 'WTCH': w[2]})
    glyf = inst['glyf']
    p = P(w)
    res = []
    for n in names:
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
print(f'interpolation check: {len(worst)} glyph-weights; mean outline difference worst {worst[0][0]:.1f} units, '
      f'median {sorted(worst)[len(worst) // 2][0]:.2f}; {len(bad)} over {TOL} units; '
      f'{len(spikes)} with a point over {FAR} units off the outline ({len({x[2] for x in spikes})} glyphs)')
for e, w, n, far in worst[:25]:
    print(f'  {n:16} at {w}: {e:.1f} units')
for e, w, n, far in spikes[:15]:
    print(f'  spike: {n:16} at {w}: {far:.0f} units off')
import json  # noqa: E402
(Path('build') / ('vf_check_italic.json' if ITALIC else 'vf_check.json')).write_text(   # every result, for triage
    json.dumps([[round(e, 2), list(w), n, round(far, 1)] for e, w, n, far in worst]))
