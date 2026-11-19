"""Stroke consistency, measured: where a glyph's ink is thicker than its
strokes, and which strokes are drawn off their weight.

A letter is strokes of known thickness. Where they meet, the ink is thicker
than any one of them: the largest disk that fits in the ink (its inscribed
circle) is wider than the heaviest stroke. How much wider is the join's
bloat: 1.0 along a plain stroke, 1.12 in a bowl's cut corner, 1.25 where a
bar ends on a stem (a T), 1.41 where two strokes cross at right angles (an
X). Past that the join is a lump: strokes rooted in one another, read as a
mass and not as strokes (the K's arm and leg in a block beside the stem at
Black until 1.017: 1.9).

For every glyph, at every place asked for (weight, grade, watch, upright or
italic), this reports the bloat and where it is, and lists every stroke
drawn thinner than its direction's rule allows (a horizontal under the stack
minimum of the weight's own, any stroke under the floor).

usage: stroke_audit.py [--limit 1.45] [--set latin|all] [--json OUT] [--sheet OUT.png] PLACE [PLACE ...]
       a PLACE is wght[,GRAD[,WTCH]] with an optional i for the italic: 900  900,100,100  700i
exit 1 if any glyph passes the limit.
"""
from __future__ import annotations

import argparse
import json
import sys
from multiprocessing import Pool

LATIN = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
LIMIT = 1.45      # a crossing of two strokes at right angles, and a little


def place_params(place: str):
    from arris.instances import params
    from arris.italic import italic
    it = place.endswith('i')
    parts = [float(v) for v in place.rstrip('i').split(',')]
    w, grad, watch = (parts + [0.0, 0.0])[:3]
    p = params(w, grad=grad, watch=watch / 100.0)
    return italic(p) if it else p


def heaviest(g):
    """The heaviest stroke of a drawing, its stamped letters' strokes among
    them: an accented letter is measured by its letter's stem, not by its
    accent's strokes (which made every accented K, R and A read as a lump
    two or three accents thick)."""
    from arris.draw import _heaviest_stroke
    own = [_heaviest_stroke(g, g.p)] if g.strokes else []
    subs = [abs(m[0]) * heaviest(sub) for _, sub, _, m in g.extra_src]
    return max(own + subs) if own or subs else _heaviest_stroke(g, g.p)


def measure(args):
    name, place = args
    import arris.glyphs  # noqa: F401
    from shapely import maximum_inscribed_circle

    from arris.draw import _heaviest_stroke, _thickness, draw
    from arris.geom import rings_to_shapely
    from arris.glyphs.figures import STACK_MIN
    p = place_params(place)
    upright = p.with_(slant=0.0) if p.slant else p         # the drawing, before the italic's shear
    try:
        g = draw(name, upright)
        ink = rings_to_shapely(g.rings())
    except Exception as e:                                  # noqa: BLE001  (a drawing that fails is a finding)
        return name, place, {'error': repr(e)[:80]}
    if ink.is_empty:
        return name, place, None
    heavy = heaviest(g)
    best = (0.0, 0.0, 0.0)
    for part in getattr(ink, 'geoms', [ink]):
        if part.area < 1:
            continue
        r = maximum_inscribed_circle(part, tolerance=0.5)
        (cx, cy), (ex, ey) = r.coords[0], r.coords[-1]
        d = 2 * ((cx - ex) ** 2 + (cy - ey) ** 2) ** 0.5
        if d > best[0]:
            best = (d, cx, cy)
    # strokes off their weight: thinner than the rule for their direction allows
    th = _thickness(upright, g.sh)
    thin = []
    for st in g.strokes:
        nodes = st.nodes
        for a, b in zip(nodes, nodes[1:] + (nodes[:1] if st.closed else ())):
            dx, dy = b.x - a.x, b.y - a.y
            if abs(dx) + abs(dy) < 1:
                continue
            own = a.w if a.w is not None else th((dx, dy))
            rule = _thickness(upright, upright.sh)((dx, dy))
            if (dx * dx + dy * dy) ** 0.5 < 1.2 * own:        # a step in a stroke (the 2's notch), not a stroke
                continue
            floor = STACK_MIN * g.zone_k * rule if abs(dy) < 1e-6 else rule
            if own < 0.97 * floor:
                thin.append((round(own / rule, 2), round(a.x), round(a.y)))
    return name, place, {'bloat': round(best[0] / heavy, 3), 'at': (round(best[1]), round(best[2])),
                         'disk': round(best[0], 1), 'stroke': round(heavy, 1), 'thin': thin}


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('places', nargs='+')
    ap.add_argument('--limit', type=float, default=LIMIT)
    ap.add_argument('--set', default='latin')
    ap.add_argument('--json')
    ap.add_argument('--top', type=int, default=40)
    a = ap.parse_args(argv)
    import arris.glyphs  # noqa: F401
    from arris.draw import REGISTRY
    if a.set == 'latin':
        cmap = {chr(s.unicode): n for n, s in REGISTRY.items() if s.unicode}
        names = [cmap[c] for c in LATIN]
    else:
        names = [n for n, s in REGISTRY.items() if s.kind in ('cap', 'lower', 'fig') and not n.endswith('.ital')]
    jobs = [(n, pl) for pl in a.places for n in names]
    with Pool(4) as pool:
        res = pool.map(measure, jobs, chunksize=16)
    out, over, thin, errors = {}, [], [], []
    for name, place, r in res:
        if r is None:
            continue
        out.setdefault(place, {})[name] = r
        if 'error' in r:
            errors.append((name, place, r['error']))
            continue
        if r['bloat'] > a.limit:
            over.append((r['bloat'], name, place, r['at']))
        for t in r['thin']:
            thin.append((t[0], name, place, t[1:]))
    for place in a.places:
        vals = sorted((r['bloat'], n) for n, r in out.get(place, {}).items() if 'bloat' in r)
        if vals:
            med = vals[len(vals) // 2][0]
            print(f'{place:>14}: {len(vals)} glyphs, median bloat {med:.2f}, worst ' +
                  ' '.join(f'{n} {b:.2f}' for b, n in vals[-8:][::-1]))
    print(f'\nover {a.limit}: {len(over)}')
    for b, n, pl, at in sorted(over, reverse=True)[:a.top]:
        print(f'  {b:5.2f}  {n:<14} {pl:<12} at {at}')
    print(f'strokes under their rule: {len(thin)}')
    for k, n, pl, at in sorted(thin)[:a.top]:
        print(f'  {k:5.2f}  {n:<14} {pl:<12} at {at}')
    if errors:
        print(f'drawings that failed: {len(errors)}', errors[:10])
    if a.json:
        json.dump(out, open(a.json, 'w'))
    return 1 if over or errors else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
