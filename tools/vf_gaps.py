"""Where a variable font parts from its drawings between the masters, by the
farthest a point of either outline is from the other (not the mean over the
whole outline, which a wedge 40 units deep on one corner of a long outline
passes: ₿ at Black, grade -50, a mean of 1.4 units).

    uv run python tools/vf_gaps.py FONT.ttf [OUT.json] [--visible 10] [--procs 4] [--glyphs a,b]

Each glyph is instantiated at places off the build's masters, most of them
at the heavy end and on the grade and the watch, where the drawings change
most between masters (arris.vf.space.GAPS), and compared with the engine's
drawing there as the build's check compares (arris.vf.check.compare). Run it
against the engine the font was built from (a font of a release against that
release's code): a drawing changed since reads as a gap. Prints how many
glyphs have a point more than --visible units off somewhere, the worst of
them and where, and writes every result to OUT.json.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from multiprocessing import Pool

import arris.glyphs  # noqa: F401
from arris import italic as ital
from arris.draw import REGISTRY
from arris.font import place
from arris.geom import rings_to_shapely
from arris.vf.check import compare, outline
from arris.vf.space import GAPS, params


def _at(job):
    loc, font, italic, names = job
    from fontTools.ttLib import TTFont
    from fontTools.varLib.instancer import instantiateVariableFont
    inst = instantiateVariableFont(TTFont(font), dict(zip(('wght', 'GRAD', 'WTCH'), loc)))
    p = params(loc, italic)
    out = []
    for n in inst.getGlyphOrder():
        if n not in REGISTRY or n not in inst['glyf'] or (names and n not in names):
            continue
        try:
            rings, _ = place(n, p)
            exact = rings_to_shapely(ital.polylines(rings) if italic else rings)
            if exact.is_empty:
                continue
            mean, far = compare(outline(inst['glyf'], n, italic), exact)
        except Exception:  # noqa: BLE001  (a drawing that fails: reported as such)
            mean, far = -1.0, -1.0
        out.append((n, list(loc), round(mean, 2), round(far, 1)))
    return out


def main(argv: list[str]) -> int:
    args = list(argv)

    def opt(name: str, default: str) -> str:
        if name in args:
            i = args.index(name)
            v = args[i + 1]
            del args[i:i + 2]
            return v
        return default
    visible = float(opt('--visible', '10'))
    procs = int(opt('--procs', '4'))
    names = set(opt('--glyphs', '').split(',')) - {''}
    font, out = args[0], (args[1] if len(args) > 1 else None)
    italic = 'Italic' in font
    with Pool(procs) as pool:
        rows = [r for part in pool.imap_unordered(_at, [(loc, font, italic, names) for loc in GAPS]) for r in part]
    if out:
        with open(out, 'w') as f:
            json.dump(rows, f)
    per = defaultdict(list)
    for n, loc, mean, far in rows:
        per[n].append((far, mean, tuple(loc)))
    worst = sorted(((max(v), n) for n, v in per.items()), reverse=True)
    failed = sorted(n for n, v in per.items() if any(far < 0 for far, _, _ in v))
    over = [x for x in worst if x[0][0] > visible]
    print(f'{len(per)} glyphs at {len(GAPS)} places: {len(over)} with a point over {visible:g} units off '
          f'somewhere, {sum(1 for x in worst if x[0][0] > 3 * visible)} over {3 * visible:g}; '
          f'{len(failed)} that would not draw')
    for (far, mean, loc), n in over[:40]:
        print(f'  {n:22s} {far:6.1f} units off at {loc} (mean {mean:.2f})')
    if failed:
        print('  would not draw:', ' '.join(failed[:20]))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
