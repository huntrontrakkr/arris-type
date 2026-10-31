"""Two variable fonts against the exact drawings, glyph by glyph: the gate for
a change to the variable-font build, as tools/sweep.py is for the drawings.

    uv run python tools/vf_compare.py OLD.ttf [NEW.ttf] [--all]

(NEW: build/Arris[GRAD,WTCH,wght].ttf, or the italic if OLD is one). Each
font is instantiated at the build's VALID places (arris.vf.space), the ones
no build chooses a master from (--all: and its CHECK places, where a build
may have put one), and every glyph compared with the engine's drawing there
as the build's check does (arris.vf.check): the mean distance between the
outlines and the farthest a point is off. Prints the totals and the glyphs
that got worse.
"""
from __future__ import annotations

import os
import sys
from multiprocessing import Pool
from pathlib import Path

import arris.glyphs  # noqa: F401
from arris import italic as ital
from arris.draw import REGISTRY
from arris.font import place
from arris.geom import rings_to_shapely
from arris.vf.check import FAR, TOL, compare, outline
from arris.vf.space import CHECK, VALID, params

ROOT = Path(__file__).resolve().parents[1]


def _at(job):
    loc, fonts, italic = job
    from fontTools.ttLib import TTFont
    from fontTools.varLib.instancer import instantiateVariableFont
    insts = [instantiateVariableFont(TTFont(f), dict(zip(('wght', 'GRAD', 'WTCH'), loc))) for f in fonts]
    p = params(loc, italic)
    names = [n for n in insts[0].getGlyphOrder() if all(n in f['glyf'] for f in insts) and n in REGISTRY]
    out = []
    for n in names:
        rings, _ = place(n, p)                              # (an italic's cells unslanted: place)
        exact = rings_to_shapely(ital.polylines(rings) if italic else rings)
        if exact.is_empty:
            continue
        row = [n, loc]
        for f in insts:
            row += list(compare(outline(f['glyf'], n, italic), exact))
        out.append(row)
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:
        sys.exit(__doc__)
    old = args[0]
    italic = 'Italic' in Path(old).name
    new = args[1] if len(args) > 1 else str(ROOT / 'build' / ('Arris-Italic[GRAD,WTCH,wght].ttf' if italic else 'Arris[GRAD,WTCH,wght].ttf'))
    places = VALID + (CHECK if '--all' in sys.argv else [])
    with Pool(min(len(places), int(os.environ.get('ARRIS_VF_WORKERS', '12')))) as pool:
        rows = [r for rr in pool.imap_unordered(_at, [(loc, (old, new), italic) for loc in places]) for r in rr]
    print(f'{Path(old).name} vs {Path(new).name}: {len({r[0] for r in rows})} glyphs at {len(places)} places'
          f' ({"VALID and CHECK" if "--all" in sys.argv else "VALID"})')
    for i, label in ((2, 'old'), (4, 'new')):
        far = [r for r in rows if r[i + 1] > FAR]
        off = [r for r in rows if r[i] > TOL]
        print(f'  {label}: {len(far)} glyph-places with a point over {FAR:.0f} units off ({len({r[0] for r in far})} glyphs), '
              f'{len(off)} with a mean difference over {TOL:.0f} ({len({r[0] for r in off})} glyphs)')
    far = {}
    for n, loc, e0, f0, e1, f1 in rows:                     # each glyph's farthest point, either font
        w = far.setdefault(n, [0.0, 0.0, None])
        w[0] = max(w[0], f0)
        if f1 >= w[1]:
            w[1], w[2] = f1, loc
    worse = sorted(((n, *v) for n, v in far.items() if v[1] > max(FAR, v[0] + 20)), key=lambda x: x[1] - x[2])
    better = [n for n, v in far.items() if v[0] > max(FAR, v[1] + 20)]
    print(f'  {len(worse)} glyphs with a spike {FAR:.0f}+ units off now, 20 more than before; {len(better)} the other way')
    for n, f0, f1, loc in worse[:30]:
        print(f'    {n:20} {f0:5.0f} -> {f1:5.0f} at {loc}')


if __name__ == '__main__':
    main()
