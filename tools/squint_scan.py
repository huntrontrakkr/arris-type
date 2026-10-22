"""Which glyphs hold white a squinting reader loses: holes and slots that the
squint fills in (``arris.vision.narrow_whites``).

A hole (closed white) or a slot (white running between two parts) is at
fault when, blurred, it keeps less than ``vision.READS`` and less than the
same glyph keeps at Regular: white the weight has squeezed shut. A hole
that keeps less than READS even at Regular is listed too: a pinhole, or a
sliver of a counter, that is never a feature. Wedges (where strokes meet at
an angle) and shallow inside corners are not white between parts and are
not counted.

usage: squint_scan.py [wght[,GRAD,WTCH] ...] [mono] [italic] [kinds=punct,cap,lower,fig,...] [names=a,b]
"""
from __future__ import annotations

import sys

import arris.glyphs  # noqa: F401
from arris.draw import REGISTRY, draw
from arris.instances import params
from arris.italic import italic
from arris.vision import READS, narrow_whites


def faint(name, p):
    """[(kind, depth, (x, y))] of the glyph's holes and slots, faintest first."""
    g = draw(name, p)
    out = []
    for q, kind, d in narrow_whites(g.rings(), g.p.sv, g.p.cap):
        if kind in ('hole', 'slot'):
            c = q.representative_point()
            out.append((kind, d, (round(c.x), round(c.y))))
    return sorted(out, key=lambda t: t[1])


def kind_of(spec):
    return spec.kind[0] if isinstance(spec.kind, tuple) else spec.kind


if __name__ == '__main__':
    args = sys.argv[1:]
    mono = 'mono' in args
    ital = 'italic' in args
    kinds = next((a.split('=')[1].split(',') for a in args if a.startswith('kinds=')), None)
    only = next((a.split('=')[1].split(',') for a in args if a.startswith('names=')), None)
    locs = [tuple(int(v) for v in a.split(',')) for a in args if a[0].isdigit()] or [(700,), (900,)]

    def at(w, gr=0, t=0):
        p = params(w, gr, watch=t / 100).with_(mono=mono)
        return italic(p) if ital else p

    names = [n for n, s in REGISTRY.items() if not n.endswith('.ital')
             and (only is None or n in only) and (kinds is None or kind_of(s) in kinds)]
    ref = at(400)
    base = {}
    total = 0
    for loc in locs:
        p = at(*loc)
        bad = []
        for n in names:
            try:
                got = faint(n, p)
            except Exception as e:  # a glyph that does not draw is another tool's business
                print(f'  {n}: {type(e).__name__}')
                continue
            if not got or got[0][1] >= READS:
                continue
            if n not in base:
                b = faint(n, ref)
                base[n] = b[0][1] if b else 1.0
            worst = [f for f in got if f[1] < READS and (f[0] == 'hole' or f[1] < base[n] - 0.02)]
            if worst:
                bad.append((n, worst))
        total += len(bad)
        print(f'{loc}: {len(bad)} glyphs')
        for n, worst in bad:
            print(f'  {n}: ' + ', '.join(f'{k} {d:.2f} at {xy}' for k, d, xy in worst[:3]))
    print(f'{total} in all')
