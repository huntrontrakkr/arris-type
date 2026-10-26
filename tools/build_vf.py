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


def _error(al, exact):
    """Worst difference at the CHECK locations between the font's outline
    and the exact drawing: the mean distance between the outlines, or the
    farthest a point is carried off it over SPIKE, whichever is more."""
    worst = 0.0
    for loc in CHECK:
        try:
            ex = exact(loc)
            got = _shp([r for r in _interpolate(al, loc) if len(set(r)) >= 3])
            err = max(got.symmetric_difference(ex).area / max(ex.boundary.length, 1),
                      got.boundary.hausdorff_distance(ex.boundary) / SPIKE)
        except Exception:  # noqa: BLE001
            err = 1e9
        worst = max(worst, err)
        if worst > 1e8:
            break
    return worst


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
    up = [_place(n, ps[m], record=ITALIC) for m in MASTERS]
    plain = lambda ups: [(u[0], u[2]) for u in ups]
    if not any(u[0] for u in up):
        return n, plain(up), [u[0] for u in up], None, 0.0, 0.0, None
    cache = {}

    def exact(loc):
        if loc not in cache:
            cache[loc] = _shp(_place(n, P(loc), record=ITALIC)[0])
        return cache[loc]

    def candidates(rings, star):
        locs = None if star else LOCS
        try:
            al = align(rings, locs)
            yield 'exact corners', al
            yield 'predicted corners', _predicted(al[:NB])
        except ValueError:
            try:
                yield 'predicted corners', _predicted(align(rings[:NB], None if star else LOCS[:NB]))
            except ValueError:
                return
    best, first = None, None
    for jogs in (True, False):
        if not jogs:
            jog, _geom.JOG = _geom.JOG, 0.0
            try:
                variant = [_place(n, ps[m], record=ITALIC) for m in MASTERS]
            finally:
                _geom.JOG = jog
        else:
            variant = up
        for star in (False, True):
            for corners, al in candidates([u[0] for u in variant], star):
                err = _error(al, exact)
                first = err if first is None else first
                if best is None or err < best[0]:
                    best = (err, al, variant, (jogs, star, corners))
                if best[0] <= LOCAL_TOL:
                    break
            if best is not None and best[0] <= LOCAL_TOL:
                break
        if best is not None and best[0] <= LOCAL_TOL:
            break
    why, choice, err = None, None, first
    if best is None:
        why = 'masters will not align'
    else:
        err, al, up, choice = best
        try:
            rings = al
            if ITALIC:
                # (terminal cells are curved but never slanted: font.place)
                cps = [ps[w].with_(slant=0.0) if REGISTRY[n].cell else ps[w] for w in MASTERS]
                if choice[2] == 'exact corners':
                    rings = ital.aligned_outlines(al, [u[0] for u in up], [u[1] for u in up], cps)
                else:
                    # the corners predicted from the others' italic outlines,
                    # curves and all
                    rings = _predicted(ital.aligned_outlines(al[:NB], [u[0] for u in up[:NB]],
                                                             [u[1] for u in up[:NB]], cps[:NB]))
        except ValueError as e:
            why = str(e)
    if why is not None:
        # cannot vary: every master carries the default outline (reported)
        d = place(n, ps[DEFAULT])[0]
        rings = [d for _ in MASTERS]
    return n, plain(up), rings, choice, first, err, why


from multiprocessing import get_context  # noqa: E402
WORKERS = int(__import__('os').environ.get('ARRIS_VF_WORKERS', '8'))
upright = {m: {} for m in MASTERS}
aligned = {w: {} for w in MASTERS}
frozen, chosen = [], []
with get_context('fork').Pool(WORKERS) as pool:
    for n, up, rings, choice, e0, e1, why in pool.imap_unordered(_glyph, names, chunksize=4):
        if why is not None:
            frozen.append((n, why))
        if choice not in (None, (True, False, 'exact corners')):
            chosen.append((n, 'jogs kept' if not choice[0] else '', 'one reference' if choice[1] else '',
                           choice[2], round(e0, 1), round(e1, 1)))
        for i, m in enumerate(MASTERS):
            upright[m][n] = up[i]                           # (rings, advance)
            aligned[m][n] = (rings[i], up[i][1])
print('placed and aligned', len(names), 'glyphs in', len(MASTERS), 'masters;', len(chosen),
      'took an alternative, interpolating better so:', sorted(chosen, key=lambda c: -c[4])[:12])
print(sum(c[3] == 'predicted corners' for c in chosen), 'glyphs keep predicted corners')
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
FEA = fea()


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


worst = []
with get_context('fork').Pool(min(WORKERS, len(CHECK))) as pool:
    for res in pool.imap_unordered(_check_at, CHECK):
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
