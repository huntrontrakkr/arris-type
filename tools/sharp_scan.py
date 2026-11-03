"""Sharp points: every convex ink corner sharper than ACUTE degrees, glyph by
glyph, as the font carries it (placed; in the italic curved and sheared, then
flattened), at Regular and across the heavy end. A point is measured by its
angle and its arms: how far its two sides run straight (turning less than
STRAIGHT degrees a vertex) before they bend, the shorter of the two in strokes
(the stem's own thickness at that place). An edge shorter than TINY strokes is
part of the corner it stands in, so a tip cut by a hair still reads as a tip.
A glyph's sharpness at a place is the sum over its points of
arm * (ACUTE - angle) / ACUTE. Deliberate points (stars, check marks,
triangles, the lozenge) are in it too: the scan ranks, it does not judge.

usage: sharp_scan.py OUT.json [workers] [names,comma,separated]
       sharp_scan.py --compare NEW.json BASE.json [N]
           (the N sharpest glyph-styles in NEW, with BASE's score beside)
"""
from __future__ import annotations

import json
import math
import sys
import warnings
from multiprocessing import Pool

warnings.filterwarnings('ignore')
import arris.glyphs  # noqa: F401
from arris.draw import REGISTRY
from arris.font import place
from arris.instances import params
from arris.italic import flatten, italic

ACUTE = 80.0       # degrees: a convex ink corner sharper than this is a point
STRAIGHT = 8.0     # degrees: a side runs straight on through vertices that turn less than this
PLACES = [(400, 0, 0), (600, 0, 100), (700, 0, 0), (900, 0, 0), (700, 100, 0), (900, 0, 100), (900, -100, 100), (900, 100, 100)]


def _p(w, g, x, it):
    p = params(w, g, watch=x / 100)
    return italic(p) if it else p


def _area(pl):
    return sum(pl[i][0] * pl[(i + 1) % len(pl)][1] - pl[(i + 1) % len(pl)][0] * pl[i][1] for i in range(len(pl))) / 2


def _clean(pl):
    """Drop repeated points and points on a straight line."""
    out = []
    for q in pl:
        if not out or math.dist(q, out[-1]) > 1e-6:
            out.append(q)
    if len(out) > 1 and math.dist(out[0], out[-1]) <= 1e-6:
        out.pop()
    changed = True
    while changed and len(out) > 3:
        changed = False
        for i in range(len(out)):
            a, b, c = out[i - 1], out[i], out[(i + 1) % len(out)]
            cr = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
            if abs(cr) < 1e-6 * max(1.0, math.dist(a, b) * math.dist(b, c)):
                del out[i]
                changed = True
                break
    return out


def _turn(a, b, c):
    """Signed turn at b, degrees (left positive)."""
    t1 = math.atan2(b[1] - a[1], b[0] - a[0])
    t2 = math.atan2(c[1] - b[1], c[0] - b[0])
    return math.degrees((t2 - t1 + math.pi) % (2 * math.pi) - math.pi)


TINY = 0.15        # strokes: an edge shorter than this is part of the corner it stands in (a 45-degree turn, 7 units,
                   # a right angle: the ҧ's hook at 900 ended in that point); the design's own edge breaks are longer


def _collapse(pl, eps):
    """Merge the ends of every edge shorter than eps into its midpoint, shortest first."""
    pl = list(pl)
    while len(pl) > 3:
        n = len(pl)
        i = min(range(n), key=lambda k: math.dist(pl[k], pl[(k + 1) % n]))
        if math.dist(pl[i], pl[(i + 1) % n]) >= eps:
            break
        a, b = pl[i], pl[(i + 1) % n]
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        if i + 1 < n:
            pl[i:i + 2] = [mid]
        else:
            pl[i] = mid
            del pl[0]
    return pl


def points(rings, sign, eps=0.0):
    """[(x, y, angle, arm)] for a glyph's rings; sign +1 when ink is on the left of travel."""
    out = []
    for pl in rings:
        pl = _clean(_collapse(_clean(pl), eps))
        n = len(pl)
        if n < 3:
            continue
        turns = [sign * _turn(pl[i - 1], pl[i], pl[(i + 1) % n]) for i in range(n)]
        for i in range(n):
            ang = 180.0 - turns[i]
            if turns[i] <= 0 or ang >= ACUTE:
                continue
            arms = []
            for step in (1, -1):
                L, j = 0.0, i
                for _ in range(n):
                    k = (j + step) % n
                    L += math.dist(pl[j], pl[k])
                    j = k
                    if abs(turns[j]) >= STRAIGHT:
                        break
                arms.append(L)
            out.append((round(pl[i][0], 1), round(pl[i][1], 1), round(ang, 1), round(min(arms), 1)))
    return out


def one(args):
    name, it = args
    res = {}
    for pl_ in PLACES:
        try:
            p = _p(*pl_, it)
            rings, _ = place(name, p)
            polys = [[(q[0], q[1]) for q in (flatten(r) if it else r)] for r in rings]
            polys = [q for q in polys if len(q) > 2]
            # ink on the left: the outer rings run counter-clockwise
            big = max(polys, key=lambda q: abs(_area(q))) if polys else None
            sign = 1 if (big and _area(big) > 0) else -1
            pts = points(polys, sign, TINY * p.sv)
            res['/'.join(map(str, pl_))] = {'sv': round(p.sv, 1), 'pts': pts,
                                    'S': round(sum(a / p.sv * (ACUTE - g) / ACUTE for _, _, g, a in pts), 3)}
        except Exception as e:  # noqa: BLE001
            res['/'.join(map(str, pl_))] = {'error': str(e)[:120]}
    return name, it, res


def names():
    out = []
    for n, s in REGISTRY.items():
        if n.endswith('.ital') or s.kind in ('space', 'mark') or (isinstance(s.kind, tuple) and s.kind[0] == 'liga'):
            continue
        if getattr(s, 'cell', False) or getattr(s, 'solid', False):
            continue
        out.append(n)
    return out


def compare(new_path, base_path, n=40):
    with open(new_path) as f:
        a = json.load(f)
    with open(base_path) as f:
        b = json.load(f)

    def worst(r):
        best = (0.0, None)
        for k, v in r.items():
            if v.get('S', 0) > best[0]:
                best = (v['S'], k)
        return best
    rows = []
    for st in ('upright', 'italic'):
        for name, r in a[st].items():
            s, k = worst(r)
            s0, _ = worst(b[st].get(name, {}))
            if k or s0:
                rows.append((s, st, name, k or '-', s0))
    rows.sort(reverse=True)
    print(f'{sum(1 for r in rows if r[0] > 0)} glyph-styles with a point (base {sum(1 for r in rows if r[4] > 0)}); '
          f'{sum(1 for r in rows if r[0] > r[4] + 0.05)} sharper than in base, {sum(1 for r in rows if r[0] < r[4] - 0.05)} blunter')
    for s, st, name, k, s0 in rows[:n]:
        print(f'{s:5.2f} {st:<7} {name:<16} {k:<12} base {s0:.2f}')


if __name__ == '__main__':
    if sys.argv[1] == '--compare':
        compare(sys.argv[2], sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 40)
        sys.exit()
    out_path = sys.argv[1]
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    ns = sys.argv[3].split(',') if len(sys.argv) > 3 else names()
    jobs = [(n, it) for it in (False, True) for n in ns]
    res = {'upright': {}, 'italic': {}}
    with Pool(workers) as pool:
        for i, (n, it, r) in enumerate(pool.imap_unordered(one, jobs, chunksize=4)):
            res['italic' if it else 'upright'][n] = r
            if i % 250 == 0:
                print(i, len(jobs), flush=True)
    with open(out_path, 'w') as f:
        json.dump(res, f)
    print('done', len(jobs))
