"""Find small outline defects: edges far shorter than anything drawn on
purpose, at the end of every stroke union and corner rule.

* **jog**: a short edge between two edges running the same way: two
  strokes that should meet in one line miss each other by a few units;
* **spur**: a short edge between two edges running back on each other: a
  hairline spike;
* **kink**: a short edge with almost no turn at either end: a vertex that
  should not be there.

usage: jog_scan.py [wght[,GRAD,WTCH] ...] [mono] [italic] [max=UNITS]
       (default 100 400 900; max: an edge shorter than this is examined,
       default a quarter of the weight's thinnest stroke)
"""
from __future__ import annotations

import math
import sys

import arris.glyphs  # noqa: F401
from arris.draw import REGISTRY
from arris.font import place
from arris.instances import params
from arris.italic import italic, polylines


def _dir(a, b):
    return math.atan2(b[1] - a[1], b[0] - a[0])


def _diff(a, b):
    d = (b - a + math.pi) % (2 * math.pi) - math.pi
    return abs(math.degrees(d))


def defects(rings, limit):
    out = []
    for r in rings:
        n = len(r)
        if n < 4:
            continue
        for i in range(n):
            a, b = r[i], r[(i + 1) % n]
            L = math.dist(a, b)
            if L >= limit or L < 1e-6:
                continue
            prev, nxt = r[i - 1], r[(i + 2) % n]
            d_in, d_e, d_out = _dir(prev, a), _dir(a, b), _dir(b, nxt)
            turn = _diff(d_in, d_out)                        # the edges either side, compared
            if turn < 15:
                kind = 'kink' if _diff(d_in, d_e) < 15 else 'jog'
            elif turn > 165:
                kind = 'spur'
            else:
                continue                                    # a corner cut (a chamfer) or a real turn
            out.append((kind, round(L, 1), (round(a[0]), round(a[1]))))
    return out


if __name__ == '__main__':
    args = sys.argv[1:]
    mono, ital = 'mono' in args, 'italic' in args
    mx = next((float(a.split('=')[1]) for a in args if a.startswith('max=')), None)
    locs = [tuple(int(v) for v in a.split(',')) for a in args if a[0].isdigit()] or [(100,), (400,), (900,)]
    names = [n for n in REGISTRY if not n.endswith('.ital')]
    total = 0
    for loc in locs:
        w, g, t = (list(loc) + [0, 0])[:3]
        p = params(w, g, watch=t / 100).with_(mono=mono)
        if ital:
            p = italic(p)
        limit = mx if mx is not None else 0.25 * max(min(p.sv, p.sh, p.sd, p.ss), p.floor)
        found = []
        for n in names:
            rings, _ = place(n, p)
            rings = polylines(rings) if ital else [[q[:2] for q in r] for r in rings]
            for d in defects(rings, limit):
                found.append((n, *d))
        total += len(found)
        print(f'## {w},{g},{t}{" mono" if mono else ""}{" italic" if ital else ""}: {len(found)} defects (edges under {limit:.0f})')
        for n, kind, L, at in found:
            print(f'  {n:24s} {kind:5s} {L:6.1f} at {at}')
    print('TOTAL', total)
