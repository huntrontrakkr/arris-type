"""The variable font's alignment step alone, for the terminal and UI glyphs:
every glyph's masters made point-compatible (build_vf.py's MASTERS), so no
glyph is left unable to vary. Fast; the full build_vf.py also checks the
interpolation. usage: terminal_gates_align.py [italic]"""
import sys

import arris.glyphs  # noqa: F401
from arris import italic as ital
from arris.draw import REGISTRY
from arris.font import _place
from arris.instances import params
from arris.variable import align

sys.path.insert(0, 'tools')
from terminal_gates import NAMES  # noqa: E402

MASTERS = [(w, 0, 0) for w in (100, 200, 400, 600, 750, 900)] + \
    [(w, g, 0) for w in (100, 400, 900) for g in (-100, 100)] + \
    [(w, 0, 100) for w in (100, 400, 600, 900)]
LOCS = [((w - 400) / (300 if w < 400 else 500), g / 100, t / 100) for w, g, t in MASTERS]   # build_vf.LOC
ITALIC = 'italic' in sys.argv[1:]
ps = {m: params(m[0], m[1], watch=m[2] / 100) for m in MASTERS}
if ITALIC:
    ps = {m: ital.italic(p) for m, p in ps.items()}
frozen = []
for n in NAMES:
    up = [_place(n, ps[m], record=ITALIC) for m in MASTERS]
    try:
        rings = align([u[0] for u in up], LOCS)
        if ITALIC:
            ital.aligned_outlines(rings, [u[0] for u in up], [u[1] for u in up],
                                  [ps[m].with_(slant=0.0) if REGISTRY[n].cell else ps[m] for m in MASTERS])
    except ValueError as e:
        frozen.append((n, str(e)))
print(f'{len(NAMES)} glyphs, {"italic" if ITALIC else "upright"}: {len(frozen)} could not vary', frozen)
