"""Drawings that flicker: along lines through the heavy end of the design
space, where a glyph's structure (its contours' point counts) changes, and
how often it changes back. A drawing that grows or loses a feature once
along a line is a jump the variable font can confine between two masters;
one that toggles a jog or a chamfer back and forth (₿'s feet at Black, six
changes between grade -100 and 0) gives the font's aligner a different set
of points every few units, and the font a wedge wherever it pairs them.

    uv run python tools/flicker_scan.py [OUT.json] [--procs 4] [--glyphs a,b] [--italic]

Lines: the grade from -100 to 100 by 5 at weights 600, 700, 800, 900 and
watch 0 and 100; the watch from 0 to 100 by 10 at the same weights, grade
0; the weight from 600 to 900 by 10 at grade -100, 0, 100. Prints the
glyphs with the most reversals (a structure seen again after another one)
and the lines they flicker on.
"""
from __future__ import annotations

import json
import sys
from itertools import pairwise
from multiprocessing import Pool

import arris.glyphs  # noqa: F401
from arris.draw import REGISTRY
from arris.font import place
from arris.instances import params
from arris.italic import italic as _italic

WEIGHTS = (600, 700, 800, 900)
LINES: dict[str, list[tuple[float, float, float]]] = {}
for _w in WEIGHTS:
    for _x in (0, 100):
        LINES[f'grade at {_w}/{_x}'] = [(_w, g, _x) for g in range(-100, 101, 5)]
    LINES[f'watch at {_w}/0'] = [(_w, 0, x) for x in range(0, 101, 10)]
for _g in (-100, 0, 100):
    LINES[f'weight at {_g}/0'] = [(w, _g, 0) for w in range(600, 901, 10)]


def _structure(name: str, loc, it: bool) -> str:
    p = params(loc[0], loc[1], watch=loc[2] / 100)
    if it:
        p = _italic(p)
    try:
        rings, _ = place(name, p)
    except Exception as e:  # noqa: BLE001  (a drawing that fails: its own structure)
        return f'error {type(e).__name__}'
    return ','.join(str(len(r)) for r in rings)


def _one(job):
    name, it = job
    out = {}
    for line, places in LINES.items():
        seq = [_structure(name, q, it) for q in places]
        changes = sum(1 for a, b in pairwise(seq) if a != b)
        seen, back, prev = set(), 0, None
        for s in seq:
            if s != prev:
                if s in seen:
                    back += 1
                seen.add(s)
                prev = s
        errors = sum(1 for s in seq if s.startswith('error'))
        if changes or errors:
            out[line] = {'changes': changes, 'reversals': back, 'errors': errors}
    return name, out


def main(argv: list[str]) -> int:
    args = list(argv)

    def opt(flag: str, default: str) -> str:
        if flag in args:
            i = args.index(flag)
            v = args[i + 1]
            del args[i:i + 2]
            return v
        return default
    procs = int(opt('--procs', '4'))
    only = [n for n in opt('--glyphs', '').split(',') if n]
    it = '--italic' in args
    args = [a for a in args if a != '--italic']
    names = only or [n for n, s in REGISTRY.items() if not n.endswith('.ital') and s.unicode
                     and not (isinstance(s.kind, tuple) and s.kind[0] == 'liga') and s.kind != 'space']
    with Pool(procs) as pool:
        res = dict(pool.imap_unordered(_one, [(n, it) for n in names], chunksize=4))
    if args:
        with open(args[0], 'w') as f:
            json.dump(res, f)
    rank = sorted(((sum(v['reversals'] for v in r.values()), sum(v['changes'] for v in r.values()), n)
                   for n, r in res.items()), reverse=True)
    print(f'{len(names)} glyphs: {sum(1 for r in rank if r[0])} flicker (a structure seen again), '
          f'{sum(1 for r in rank if r[1])} change somewhere; '
          f'{sum(1 for r in res.values() if any(v["errors"] for v in r.values()))} fail to draw somewhere')
    for back, changes, n in rank[:40]:
        lines = sorted(res[n].items(), key=lambda kv: -kv[1]['reversals'])[:3]
        print(f'  {n:22s} reversals {back:3d}, changes {changes:3d}: ' +
              '; '.join(f'{k} {v["reversals"]}/{v["changes"]}' for k, v in lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
