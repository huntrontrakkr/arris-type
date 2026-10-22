"""Glyphs whose closed counters shrink below a third of the stem or vanish
at heavy weights, positive grade or the watch balance."""
import shapely
from shapely.geometry import Polygon
import arris.glyphs  # noqa
from arris.draw import REGISTRY, draw
from arris.geom import rings_to_shapely
from arris.instances import params

LOCS = [(400, 0, 0), (700, 0, 0), (900, 0, 0), (900, 100, 0), (900, 0, 100), (900, 100, 100)]

def holes(g):
    poly = rings_to_shapely(g.rings())
    out = []
    for part in getattr(poly, 'geoms', [poly]):
        for h in part.interiors:
            out.append(2 * shapely.maximum_inscribed_circle(Polygon(h), tolerance=1.0).length)
    return sorted(out)

rows = []
for n, spec in REGISTRY.items():
    if spec.kind not in ('cap', 'lower'):
        continue
    res = []
    for w, gr, t in LOCS:
        p = params(w, gr, watch=t / 100)
        g = draw(n, p)
        hs = holes(g)
        res.append((len(hs), (min(hs) / p.sv) if hs else None))
    n0 = res[0][0]
    lost = [LOCS[i] for i, (k, _) in enumerate(res) if k < n0]
    tight = [(LOCS[i], round(m, 2)) for i, (k, m) in enumerate(res) if m is not None and m < 0.35]
    if lost or tight:
        rows.append((n, n0, lost, tight))
for r in rows:
    print(r)
print(len(rows), 'flagged')
