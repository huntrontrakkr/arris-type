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
# every 100 on the weight axis up to 700 (the 1's flag, ŉ, the digraphs). (A
# master at the heavy grade-watch corner was tried, 2026-10-25: there the ŀ's
# dot meets its l, and the masters' contours stop agreeing.)
MASTERS = [(w, 0, 0) for w in (100, 200, 300, 400, 500, 600, 700, 750, 800, 850, 900)] + \
    [(w, g, 0) for w in (100, 400, 900) for g in (-100, 100)] + \
    [(w, 0, 100) for w in (100, 400, 600, 800, 900)]
DEFAULT = (400, 0, 0)
CHECK = [(150, 0, 0), (250, 0, 0), (350, 0, 0), (450, 0, 0), (550, 0, 0), (650, 0, 0), (725, 0, 0),
         (775, 0, 0), (825, 0, 0), (875, 0, 0),
         (400, 50, 0), (700, -50, 0), (600, 0, 50), (300, 0, 100), (800, 50, 100), (850, 75, 75)]

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
# upright drawings (rings, chamfer record, advance); the italic is made from them
upright = {m: {n: _place(n, ps[m], record=ITALIC) for n in names} for m in MASTERS}
print('placed', len(MASTERS), 'masters')

# Per glyph: masters cleaned of jogs (geom._close_jogs) can differ in
# structure between neighbouring weights where a step closes at one and not
# the next; most still interpolate well, some do not. Each glyph is aligned,
# interpolated between its neighbouring weight masters and compared with the
# exact drawing at the midpoints; where that is off by more than the build's
# tolerance, the glyph's masters are drawn again without the jog closing,
# and whichever interpolates better is kept.
from arris import geom as _geom
from arris.geom import rings_to_shapely as _shp
WM = sorted(w for (w, g, t) in MASTERS if g == 0 and t == 0)
MIDS = [((a + b) / 2, WM.index(a), WM.index(b)) for a, b in zip(WM, WM[1:])]
_exact = {}


def _exact_at(n, w):
    if (n, w) not in _exact:
        _exact[(n, w)] = _shp(_place(n, P((w, 0, 0)), record=ITALIC)[0])
    return _exact[(n, w)]


def _local_error(n, rings_by_master):
    try:
        al = align(rings_by_master)
    except ValueError:
        return 1e9, None
    idx = [MASTERS.index((w, 0, 0)) for w in WM]
    worst = 0.0
    for wm, i0, i1 in MIDS:
        r0, r1 = al[idx[i0]], al[idx[i1]]
        mid = [[((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2) for p0, p1 in zip(a_, b_)] for a_, b_ in zip(r0, r1)]
        try:
            ex = _exact_at(n, wm)
            got = _shp([r for r in mid if len(set(r)) >= 3])
            err = got.symmetric_difference(ex).area / max(ex.boundary.length, 1)
        except Exception:  # noqa: BLE001
            err = 1e9
        worst = max(worst, err)
    return worst, al


LOCAL_TOL = 3.0
replaced = []
for n in names:
    rings_a = [upright[w][n][0] for w in MASTERS]
    if not any(rings_a):
        continue
    ea, _ = _local_error(n, rings_a)
    if ea <= LOCAL_TOL:
        continue
    jog, _geom.JOG = _geom.JOG, 0.0
    try:
        alt = {w: _place(n, ps[w], record=ITALIC) for w in MASTERS}
    finally:
        _geom.JOG = jog
    eb, _ = _local_error(n, [alt[w][0] for w in MASTERS])
    if eb < ea:
        for w in MASTERS:
            upright[w][n] = alt[w]
        replaced.append((n, round(ea, 1), round(eb, 1)))
print(len(replaced), 'glyphs keep their jogs in the variable font, interpolating better so:', replaced[:12])

aligned = {w: {} for w in MASTERS}
frozen = []
for n in names:
    try:
        rings = align([upright[w][n][0] for w in MASTERS])
        if ITALIC:
            # (terminal cells are curved but never slanted: font.place)
            rings = ital.aligned_outlines(rings, [upright[w][n][0] for w in MASTERS],
                                          [upright[w][n][1] for w in MASTERS],
                                          [ps[w].with_(slant=0.0) if REGISTRY[n].cell else ps[w] for w in MASTERS])
    except ValueError as e:
        # cannot vary: every master carries the default outline (reported)
        frozen.append((n, str(e)))
        d = place(n, ps[DEFAULT])[0]
        rings = [d for _ in MASTERS]
    for i, w in enumerate(MASTERS):
        aligned[w][n] = (rings[i], upright[w][n][2])
print('aligned;', len(frozen), 'glyphs could not vary:', frozen[:10])


def kern_outline(w, n):
    if ITALIC:
        return ital.polylines(place(n, ps[w])[0])
    return upright[w][n][0]


# kerning: the same pairs in every master, each master's own values
kernable = [n for n in names if REGISTRY[n].kind in ('cap', 'lower') or n in KERN_PUNCT]
pairs_by = {w: kerns({n: (kern_outline(w, n), round(upright[w][n][2])) for n in kernable}, ps[w], light(ps[w]))
            for w in MASTERS if w[1] == 0}
for w in MASTERS:                       # grade keeps every advance, kerning included
    if w[1] != 0:
        pairs_by[w] = pairs_by[(w[0], 0, w[2])]
all_pairs = set().union(*pairs_by.values())
print(len(all_pairs), 'kerning pairs')

tmp = Path(tempfile.mkdtemp())
doc = DesignSpaceDocument()
for tag, name, lo, df, hi in (('wght', 'Weight', 100, 400, 900), ('GRAD', 'Grade', -100, 0, 100),
                              ('WTCH', 'Watch', 0, 0, 100)):
    ax = AxisDescriptor()
    ax.tag, ax.name, ax.minimum, ax.default, ax.maximum = tag, name, lo, df, hi
    doc.addAxis(ax)
for i, m in enumerate(MASTERS):
    path = tmp / f'master-{i}.ttf'
    pairs = {pr: pairs_by[m].get(pr, 0) for pr in all_pairs}
    build(str(path), names, ps[m], family=family, style=style_name(m[0]), weight=m[0], fea=fea(),
          placed=aligned[m], kern_pairs=pairs, stat=False)
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
worst = []
for w in CHECK:
    inst = instantiateVariableFont(TTFont(out), {'wght': w[0], 'GRAD': w[1], 'WTCH': w[2]})
    glyf = inst['glyf']
    p = P(w)
    for n in names:
        rings, adv = place(n, p)
        from arris.geom import rings_to_shapely
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
            # area between them over the exact outline's length
            err = interp.symmetric_difference(exact).area / max(exact.boundary.length, 1)
        except Exception as ex:  # noqa: BLE001
            err = 1e9
        worst.append((err, w, n))
worst.sort(reverse=True)
TOL = 3.0   # font units: a mean outline difference under 0.3% of the em passes
bad = [x for x in worst if x[0] > TOL]
print(f'interpolation check: {len(worst)} glyph-weights; mean outline difference worst {worst[0][0]:.1f} units, '
      f'median {sorted(worst)[len(worst) // 2][0]:.2f}; {len(bad)} over {TOL} units')
for e, w, n in worst[:25]:
    print(f'  {n:16} at {w}: {e:.1f} units')
import json  # noqa: E402
(Path('build') / ('vf_check_italic.json' if ITALIC else 'vf_check.json')).write_text(   # every result, for triage
    json.dumps([[round(e, 2), list(w), n] for e, w, n in worst]))
