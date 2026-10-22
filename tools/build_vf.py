"""Build the variable font: weight axis from masters at Thin, Regular,
SemiBold and Black, made point-compatible by ``arris.variable.align``, then
checked against exact drawings at the weights in between.

usage: build_vf.py [watch]
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
from arris.instances import HERITAGE_OPTICS, NAMES, OPTICS, params
from arris.kerning import kerns
from arris.variable import align

MASTERS = [100, 200, 400, 600, 750, 900]
DEFAULT = 400
CHECK = [150, 300, 500, 700, 800]

watch = 'watch' in sys.argv[1:]
family = 'Arris Watch' if watch else 'Arris'
optics = HERITAGE_OPTICS if watch else OPTICS
FIGS = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine']
names = FIGS + [n for n in REGISTRY if n not in FIGS]

ps = {w: params(w, optics=optics) for w in MASTERS}
placed = {w: {n: place(n, ps[w]) for n in names} for w in MASTERS}
print('placed masters')

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
            for w in MASTERS}
all_pairs = set().union(*pairs_by.values())
print(len(all_pairs), 'kerning pairs')

tmp = Path(tempfile.mkdtemp())
doc = DesignSpaceDocument()
ax = AxisDescriptor()
ax.tag, ax.name, ax.minimum, ax.default, ax.maximum = 'wght', 'Weight', min(MASTERS), DEFAULT, max(MASTERS)
doc.addAxis(ax)
for w in MASTERS:
    path = tmp / f'master-{w}.ttf'
    pairs = {pr: pairs_by[w].get(pr, 0) for pr in all_pairs}
    build(str(path), names, ps[w], family=family, style=NAMES.get(w, f'W{w}'), weight=w, fea=fea(),
          placed=aligned[w], kern_pairs=pairs)
    src = SourceDescriptor()
    src.path, src.location = str(path), {'Weight': w}
    doc.addSource(src)
for w, nm in NAMES.items():
    inst = InstanceDescriptor()
    inst.familyName, inst.styleName, inst.location = family, nm, {'Weight': w}
    doc.addInstance(inst)
vf, _, _ = varlib_build(doc)
out = Path('build') / f"{family.replace(' ', '')}[wght].ttf"
vf.save(out)
print('wrote', out)

# --- check: the variable font against exact drawings between the masters ----
worst = []
for w in CHECK:
    inst = instantiateVariableFont(TTFont(out), {'wght': w})
    glyf = inst['glyf']
    p = params(w, optics=optics)
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
