"""Find Mono glyphs that broke in the cell: every glyph's Mono drawing
against its proportional self, at the weights given.

Two measures, neither tuned per glyph:

* **Counters lost**: closed white the proportional drawing has and the Mono
  one does not (a bowl squeezed shut, a letter blocked solid). Some are
  designed (₦ ₩ with one bar in Mono).
* **Likeness**: the proportional ink stretched onto the Mono ink's box, and
  the share of the two that agrees (intersection over union). Mono's own
  forms score low by design (the slab i l r, a capital beside its tonos),
  but a glyph whose strokes merged or vanished in the cell (2026-10-25: Ƙ
  Ɲ ℛ ℳ ℤ ℉) is among the lowest.

usage: mono_scan.py [wght,...] [workers]     (default: 400,900 8)
"""
from __future__ import annotations

import sys
from multiprocessing import Pool

from shapely import affinity

import arris.glyphs  # noqa: F401
from arris.draw import REGISTRY
from arris.font import place
from arris.geom import rings_to_shapely
from arris.instances import params

WEIGHTS = [int(w) for w in sys.argv[1].split(',')] if len(sys.argv) > 1 else [400, 900]
WORKERS = int(sys.argv[2]) if len(sys.argv) > 2 else 8
LIKENESS = 0.3      # list glyphs whose likeness is under this


def _counters(ink) -> int:
    return sum(len(g.interiors) for g in getattr(ink, 'geoms', [ink]) if g.geom_type == 'Polygon')


def scan(n):
    out = []
    for w in WEIGHTS:
        a = rings_to_shapely(place(n, params(w))[0])
        b = rings_to_shapely(place(n, params(w).with_(mono=True))[0])
        if a.is_empty or b.is_empty:
            continue
        if _counters(b) < _counters(a):
            out.append((w, f'loses counters: {_counters(a)} -> {_counters(b)}'))
        ax0, ay0, ax1, ay1 = a.bounds
        bx0, by0, bx1, by1 = b.bounds
        s = affinity.scale(a, (bx1 - bx0) / max(ax1 - ax0, 1), (by1 - by0) / max(ay1 - ay0, 1), origin=(ax0, ay0))
        s = affinity.translate(s, bx0 - ax0, by0 - ay0)
        like = s.intersection(b).area / max(s.union(b).area, 1)
        if like < LIKENESS:
            out.append((w, f'likeness {like:.2f}'))
    return n, out


def main():
    names = [n for n, s in REGISTRY.items() if not n.endswith('.ital') and s.kind not in ('space', 'mark')
             and not (isinstance(s.kind, tuple) and s.kind[0] == 'liga')]
    with Pool(WORKERS) as pool:
        found = sorted((n, r) for n, r in pool.imap_unordered(scan, names, chunksize=8) if r)
    for n, r in found:
        for w, what in r:
            print(f'  {n:18} {w}: {what}')
    print(f'{len(names)} glyphs at {WEIGHTS}: {len(found)} to look at')


if __name__ == '__main__':
    main()
