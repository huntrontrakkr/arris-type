"""Every stroke end that comes to a point, in every glyph of every cut.

A stroke ends in a cut, a face and a cut (``geom._share``); an end whose
two cuts meet, or leave a face too short to see, is an arrowhead on a
bar, and the design has none (``topology.stroke_ends``: ``point``,
``thin``). The hooks' beaks are counted beside them, as drawn.

usage: end_scan.py [cut,cut...] [procs=N] [json=FILE]
       cuts: up it watch mono monoit narrow narrowit (default all), each at
       its ladder of weights. Exits 1 if any end is a point or thin.
"""
from __future__ import annotations

import json
import sys
from multiprocessing import Pool

# Read as an end and not one, or one still to redraw: named here, listed apart, and not counted.
KNOWN: dict[str, str] = {}    # (2.0: none; the six it named once, ҏ's tick and ⊜ ⊎ ⎋ ⌦ ⌫ in the monospaced cuts, redrawn)
LADDER = (100, 200, 300, 400, 500, 600, 700, 800, 850, 900)
MONO = (300, 400, 450, 500, 600, 700)


def cuts():
    from arris.instances import mono_weight, narrow_weight, params
    from arris.italic import italic
    return {
        'up': (lambda w: params(w), LADDER),
        'it': (lambda w: italic(params(w)), LADDER),
        'watch': (lambda w: params(w, watch=1.0), (400, 700, 900)),
        'mono': (lambda w: params(mono_weight(w)).with_(mono=True), MONO),
        'monoit': (lambda w: italic(params(mono_weight(w)).with_(mono=True)).with_(cursive=True), MONO),
        'narrow': (lambda w: params(narrow_weight(w)).with_(mono=True, narrow=True), MONO),
        'narrowit': (lambda w: italic(params(narrow_weight(w)).with_(mono=True, narrow=True)).with_(cursive=True), MONO),
    }


def scan(job):
    cut, w = job
    import arris.glyphs  # noqa: F401  (the registry)
    from arris.draw import REGISTRY, draw
    from arris.topology import stroke_ends
    p = cuts()[cut][0](w)
    found = {}
    for name in REGISTRY:
        try:
            ends = stroke_ends(draw(name, p).rings(), p.c)
        except Exception as e:  # noqa: BLE001  (a drawing that fails is another check's finding)
            ends = [('error', 0.0, 0.0, 0.0, type(e).__name__)]
        if ends:
            found[name] = [(e[0], round(e[1]), round(e[2]), round(e[3], 2)) for e in ends]
    return cut, w, found


def main(argv) -> int:
    opts = dict(a.split('=', 1) for a in argv if '=' in a)
    want = [c for a in argv if '=' not in a for c in a.split(',')] or list(cuts())
    jobs = [(cut, w) for cut in want for w in cuts()[cut][1]]
    out, bad = {}, 0
    with Pool(int(opts.get('procs', 3))) as pool:
        for cut, w, found in pool.imap_unordered(scan, jobs):
            out[f'{cut}/{w}'] = found
            count = {k: sum(1 for n, v in found.items() if n not in KNOWN and any(e[0] == k for e in v))
                     for k in ('point', 'thin', 'beak', 'error')}
            bad += count['point'] + count['thin']
            print(f"{cut:9s}{w:4d}  glyphs with a point {count['point']}, a thin face {count['thin']}; "
                  f"with a beak {count['beak']}; not drawn {count['error']}", flush=True)
            for name, v in found.items():
                for e in v:
                    if e[0] in ('point', 'thin'):
                        print(f"    {name}: {e[0]} at ({e[1]}, {e[2]}), {e[3]}{' (known: ' + KNOWN[name] + ')' if name in KNOWN else ''}",
                              flush=True)
            if 'json' in opts:
                with open(opts['json'], 'w') as f:
                    json.dump(out, f)
    print('ends that are points or thin:', bad)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
