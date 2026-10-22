"""Build the variable font, made point-compatible by ``arris.variable.align``
and checked against exact drawings at locations between the masters.

Axes:
  wght  100-900  weight
  GRAD  -100-100 grade: strokes thinner or thicker, every width and space kept
  WTCH  0-100    the watch's own proportions (diagonals as wide across as a
                 stem, horizontals as heavy as verticals) instead of the
                 measured optics
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
from arris.font import KERN_PUNCT, build, light, place
from arris.glyphs.features import fea
from arris.instances import NAMES, params
from arris.kerning import kerns
from arris.variable import align

# (wght, GRAD, WTCH)
MASTERS = [(w, 0, 0) for w in (100, 200, 400, 600, 750, 900)] + \
    [(w, g, 0) for w in (100, 400, 900) for g in (-100, 100)] + \
    [(w, 0, 100) for w in (100, 400, 600, 900)]
DEFAULT = (400, 0, 0)
CHECK = [(150, 0, 0), (300, 0, 0), (500, 0, 0), (700, 0, 0), (800, 0, 0),
         (400, 50, 0), (700, -50, 0), (600, 0, 50), (300, 0, 100), (800, 50, 100)]

family = 'Arris'
FIGS = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine']
names = FIGS + [n for n in REGISTRY if n not in FIGS]


def P(loc):
    w, g, t = loc
    return params(w, g, watch=t / 100)


ps = {m: P(m) for m in MASTERS}
placed = {m: {n: place(n, ps[m]) for n in names} for m in MASTERS}
print('placed', len(MASTERS), 'masters')

aligned = {w: {} for w in MASTERS}
frozen = []
for n in names:
    try:
        rings = align([placed[w][n][0] for w in MASTERS])
    except ValueError as e:
        # cannot vary: every master carries the default outline (reported)
        frozen.append((n, str(e)))
        d = placed[DEFAULT][n][0]
        rings = [d for _ in MASTERS]
    for i, w in enumerate(MASTERS):
        aligned[w][n] = (rings[i], placed[w][n][1])
print('aligned;', len(frozen), 'glyphs could not vary:', frozen[:10])

# kerning: the same pairs in every master, each master's own values
kernable = [n for n in names if REGISTRY[n].kind in ('cap', 'lower') or n in KERN_PUNCT]
pairs_by = {w: kerns({n: (placed[w][n][0], round(placed[w][n][1])) for n in kernable}, ps[w], light(ps[w]))
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
    build(str(path), names, ps[m], family=family, style=NAMES.get(m[0], f'W{m[0]}'), weight=m[0], fea=fea(),
          placed=aligned[m], kern_pairs=pairs)
    src = SourceDescriptor()
    src.path, src.location = str(path), {'Weight': m[0], 'Grade': m[1], 'Watch': m[2]}
    doc.addSource(src)
for w, nm in NAMES.items():
    inst = InstanceDescriptor()
    inst.familyName, inst.styleName, inst.location = family, nm, {'Weight': w, 'Grade': 0, 'Watch': 0}
    doc.addInstance(inst)
vf, _, _ = varlib_build(doc)
from fontTools.otlLib.builder import buildStatTable
buildStatTable(vf, [
    {'tag': 'wght', 'name': 'Weight',
     'values': [{'value': w, 'name': nm, 'flags': 0x2 if w == 400 else 0} for w, nm in NAMES.items()]},
    {'tag': 'GRAD', 'name': 'Grade', 'values': [{'value': 0, 'name': 'Normal', 'flags': 0x2}]},
    {'tag': 'WTCH', 'name': 'Watch', 'values': [{'value': 0, 'name': 'Measured', 'flags': 0x2},
                                                {'value': 100, 'name': 'Watch'}]},
])
vf['name'].names = [nm for nm in vf['name'].names if nm.platformID != 1]   # Windows names only
out = Path('build') / 'Arris[GRAD,WTCH,wght].ttf'
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
        exact = Polygon()
        from arris.geom import rings_to_shapely
        exact = rings_to_shapely(rings)
        g = glyf[n]
        coords, ends, _ = g.getCoordinates(glyf)
        pts, start = list(coords), 0
        got = []
        for e in ends:
            got.append([tuple(q) for q in pts[start:e + 1]][::-1])
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
