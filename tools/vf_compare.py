"""Two variable fonts against the exact drawings, glyph by glyph: the gate for
a change to the variable-font build, as tools/sweep.py is for the drawings.

    uv run python tools/vf_compare.py OLD.ttf [NEW.ttf] [--all]

(NEW: build/Arris[GRAD,WTCH,wght].ttf, or the italic if OLD is one). Each
font is instantiated at build_vf's VALID places, the ones no build chooses a
master from (--all: and its CHECK places, where a build may have put one),
and every glyph compared with the engine's drawing there as the build's
check does: the mean distance between the outlines and the farthest a
point is off. Prints the totals and the glyphs that got worse.
"""
from __future__ import annotations

import os
import sys
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

import arris.glyphs  # noqa: E402,F401
from arris import italic as ital  # noqa: E402
from arris.draw import REGISTRY  # noqa: E402
from arris.font import place  # noqa: E402
from arris.geom import rings_to_shapely  # noqa: E402
from arris.instances import params  # noqa: E402

# (as tools/build_vf.py has them)
VALID = [(850, 25, 25), (650, -25, 75), (300, 50, 50), (725, 60, 30), (500, -75, 25), (875, 90, 90),
         (200, -50, 50), (575, 25, 0), (775, 0, 75), (450, 75, 100)]
CHECK = [(150, 0, 0), (250, 0, 0), (350, 0, 0), (450, 0, 0), (550, 0, 0), (650, 0, 0), (725, 0, 0),
         (775, 0, 0), (825, 0, 0), (875, 0, 0)] + \
    [(w, g, 0) for w in (100, 400, 900) for g in (-50, 50)] + [(w, 0, 50) for w in (100, 400, 600, 800, 900)] + \
    [(700, -50, 0), (300, 0, 100), (400, 50, 50), (900, 50, 50), (800, 50, 100), (850, 75, 75),
     (900, -50, 50), (650, 75, 75), (250, -50, 50), (900, 100, 50), (900, 50, 100)] + \
    [(w, g, 100) for w in (100, 400, 900) for g in (-100, 100)]
FAR = 60.0      # a point this far off the outline is a spike (build_vf.FAR)
TOL = 3.0       # a mean difference over this is off (build_vf.TOL)


def _outline(font, n, italic):
    glyf = font['glyf']
    coords, ends, flags = glyf[n].getCoordinates(glyf)
    pts, start, out = list(coords), 0, []
    for e in ends:
        c = [(q[0], q[1], bool(f & 1)) for q, f in zip(pts[start:e + 1], flags[start:e + 1])][::-1]
        out.append(ital.flatten(c) if italic else [q[:2] for q in c])
        start = e + 1
    return rings_to_shapely([r for r in out if len(set(r)) >= 3])


def _at(job):
    loc, fonts, italic = job
    from fontTools.ttLib import TTFont
    from fontTools.varLib.instancer import instantiateVariableFont
    insts = [instantiateVariableFont(TTFont(f), dict(zip(('wght', 'GRAD', 'WTCH'), loc))) for f in fonts]
    p = params(loc[0], loc[1], watch=loc[2] / 100)
    if italic:
        p = ital.italic(p)
    names = [n for n in insts[0].getGlyphOrder() if all(n in f['glyf'] for f in insts) and n in REGISTRY]
    out = []
    for n in names:
        rings, _ = place(n, p)                              # (an italic's cells unslanted: place)
        exact = rings_to_shapely(ital.polylines(rings) if italic else rings)
        if exact.is_empty:
            continue
        row = [n, loc]
        for f in insts:
            try:
                got = _outline(f, n, italic)
                row += [got.symmetric_difference(exact).area / max(exact.boundary.length, 1),
                        got.boundary.hausdorff_distance(exact.boundary)]
            except Exception:  # noqa: BLE001
                row += [1e9, 1e9]
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
