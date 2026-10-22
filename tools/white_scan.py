"""Which glyphs fuse at heavy weights: white features they lose.

The white a glyph's parts hold between them (inside its convex hull) is
opened by a quarter of the weight's stroke, so only white at least half a
stroke wide counts: white a reader can see. Its separate features (a
counter, the notch under an arrow's barb, the gap between a pilcrow's
stems) are counted at Regular and at the weight under test. A feature the
Regular has and the heavier weight lacks is a fusion.

usage: white_scan.py [wght[,GRAD,WTCH] ...] [italic] [kinds=punct,cap,lower,fig]
"""
from __future__ import annotations

import sys

from shapely.geometry import MultiPoint

import arris.glyphs  # noqa: F401
from arris.draw import REGISTRY
from arris.font import place
from arris.geom import rings_to_shapely
from arris.instances import params
from arris.italic import italic, polylines

OPEN = 0.25          # opening radius, as a share of the weight's stroke
MIN_AREA = 0.5       # a feature counts if at least this many squares of the opening's width


def features(name, p):
    rings, _ = place(name, p)
    if p.slant:
        rings = polylines(rings)
    if not rings:
        return 0
    ink = rings_to_shapely(rings)
    hull = MultiPoint([q[:2] for r in rings for q in r]).convex_hull
    white = hull.difference(ink)
    r = OPEN * max(p.sv, p.sh, p.sd, p.ss)
    readable = white.buffer(-r, join_style='mitre').buffer(r, join_style='mitre')
    parts = [g for g in getattr(readable, 'geoms', [readable]) if not g.is_empty]
    return sum(1 for g in parts if g.area > MIN_AREA * (2 * r) ** 2)


def kind_of(spec):
    return spec.kind[0] if isinstance(spec.kind, tuple) else spec.kind


if __name__ == '__main__':
    args = sys.argv[1:]
    ital = 'italic' in args
    kinds = next((a.split('=')[1].split(',') for a in args if a.startswith('kinds=')), ['punct'])
    locs = [tuple(int(v) for v in a.split(',')) for a in args if a[0].isdigit()] or [(700,), (900,)]
    names = [n for n, s in REGISTRY.items() if not n.endswith('.ital') and kind_of(s) in kinds]
    ref = params(400)
    if ital:
        ref = italic(ref)
    base = {n: features(n, ref) for n in names}
    total = 0
    for loc in locs:
        w, g, t = (list(loc) + [0, 0])[:3]
        p = params(w, g, watch=t / 100)
        if ital:
            p = italic(p)
        lost = []
        for n in names:
            k = features(n, p)
            if k < base[n]:
                lost.append((n, base[n], k))
        total += len(lost)
        print(f'## {"italic" if ital else "upright"} {w},{g},{t}: {len(lost)} glyphs lose white features')
        print('  ' + ', '.join(f'{n} {a}->{b}' for n, a, b in lost))
    print('TOTAL', total)
