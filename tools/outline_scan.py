"""Scan finished outlines for the faults the eye catches at heavy weights.

* **short**: an edge shorter than half a module that is not a chamfer (a
  chamfer turns 45 degrees at both ends): two vertices that should be one;
* **stray**: a vertex where a long edge bends by only a few degrees: a
  point that should not be there, or two edges that should be one line;
* **skew**: a long edge within a few degrees of one of the font's
  directions (0, 90, 45, the 2:1 and 1:2) but not on it.

usage: outline_scan.py [wght ...] [italic] [mono] [top=N] [only=name,name]
       (default 500 550 ... 900). Prints counts per kind and the worst
       glyphs; ``--json`` writes the findings to /tmp/outline_scan.json.
"""
from __future__ import annotations

import json
import math
import sys

import arris.glyphs  # noqa: F401
from arris.draw import REGISTRY
from arris.font import place
from arris.instances import params
from arris.italic import italic, polylines

DIRS = [0.0, 90.0, 45.0, 135.0, math.degrees(math.atan2(2, 1)), math.degrees(math.atan2(1, 2)),
        180 - math.degrees(math.atan2(2, 1)), 180 - math.degrees(math.atan2(1, 2))]
STRAY_TURN = 8.0       # degrees: a vertex bending less than this between long edges
SKEW_MAX = 4.0         # degrees: an edge this close to a font direction should be on it


def _ang(a, b):
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 180.0


def _off(angle):
    return min(min(abs(angle - d), 180 - abs(angle - d)) for d in DIRS)


def _turn(a, b, c):
    u = (b[0] - a[0], b[1] - a[1])
    v = (c[0] - b[0], c[1] - b[1])
    return abs(math.degrees(math.atan2(u[0] * v[1] - u[1] * v[0], u[0] * v[0] + u[1] * v[1])))


def findings(rings, p, curved=False):
    out = []
    short_lim, long_lim = 0.5 * p.m, 1.5 * p.m
    for r in rings:
        n = len(r)
        if n < 3:
            continue
        L = [math.dist(r[i], r[(i + 1) % n]) for i in range(n)]
        for i in range(n):
            a, b, c = r[i - 1], r[i], r[(i + 1) % n]
            lin, lout = L[i - 1], L[i]
            t = _turn(a, b, c)
            # a short edge b->c that is not a chamfer (45 at both ends) nor a curve's chord
            if lout < short_lim and not curved:
                d = r[(i + 2) % n]
                t1, t2 = t, _turn(b, c, d)
                if not (abs(t1 - 45) < 6 and abs(t2 - 45) < 6) and lout > 0.01:
                    out.append(('short', round(lout, 1), b))
            if not curved and lin > long_lim and lout > long_lim and 0.05 < t < STRAY_TURN:
                out.append(('stray', round(t, 1), b))
            if not curved and lout > long_lim:
                o = _off(_ang(b, c))
                if 0.05 < o < SKEW_MAX:
                    out.append(('skew', round(o, 2), b))
    return out


def main():
    args = sys.argv[1:]
    weights = [int(a) for a in args if a.isdigit()] or list(range(500, 901, 50))
    ital = 'italic' in args
    mono = 'mono' in args
    top = next((int(a[4:]) for a in args if a.startswith('top=')), 30)
    only = next((a[5:].split(',') for a in args if a.startswith('only=')), None)
    names = [n for n, s in REGISTRY.items() if not n.endswith('.ital')
             and not (isinstance(s.kind, tuple) and s.kind[0] == 'liga')]
    if only:
        names = only
    totals, per = {'short': 0, 'stray': 0, 'skew': 0}, {}
    for w in weights:
        p = params(w).with_(mono=mono)
        if ital:
            p = italic(p)
        for n in names:
            try:
                rings, _ = place(n, p)
            except Exception as e:  # noqa: BLE001
                print('error', n, w, e)
                continue
            if ital:
                rings = polylines(rings)
            f = findings(rings, p, curved=False)
            for kind, v, q in f:
                totals[kind] += 1
                per.setdefault(n, []).append((w, kind, v, (round(q[0]), round(q[1]))))
    print(f'{len(names)} glyphs x {len(weights)} weights{" italic" if ital else ""}{" mono" if mono else ""}:', totals)
    worst = sorted(per.items(), key=lambda kv: -len(kv[1]))[:top]
    for n, fs in worst:
        ch = chr(REGISTRY[n].unicode) if REGISTRY[n].unicode else ''
        kinds = {k: sum(1 for x in fs if x[1] == k) for k in totals}
        print(f'  {n:18} {ch:2} {kinds}  e.g. {fs[0]}')
    if '--json' in args:
        json.dump(per, open('/tmp/outline_scan.json', 'w'))


if __name__ == '__main__':
    main()
