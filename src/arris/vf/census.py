"""A census of the drawings: how each glyph's exact drawing changes from
one weight to the next at a grade and watch, one json line per glyph,
for tools/vf_planes.py to read the jump places from (context.load_planes).

    python -m arris.vf.census OUT.jsonl [italic] [--grad G] [--watch T] [--step 10]

A glyph's line: {"n": name, "steps": [[wght, structure, moved mean, moved
max, rings, lightened, overrides], ...], "changes": how many steps change
the structure}; a glyph whose drawing fails, {"n": name, "error": why}.
The structure is the rings' point counts as text, so two drawings of one
structure read alike; moved is how far the outline is from the step
before (the mean distance: the area between them over the earlier
outline's length; and the farthest a point is off it); lightened how far
the drawing's strokes were lightened (draw), overrides its free variables
as json. (The planes 1.005 was built with came from a census in this
shape, taken by a script that was not kept.)
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from collections.abc import Sequence
from itertools import pairwise

import arris.glyphs  # noqa: F401  (every glyph registered)
from arris.draw import draw
from arris.geom import rings_to_shapely

from .build import glyph_names, setup_logging
from .settings import Settings
from .space import params

log = logging.getLogger(__name__)

_ARGS: tuple[float, float, bool, int] = (0, 0, False, 10)


def _use(grad: float, wtch: float, italic: bool, step: int) -> None:
    global _ARGS
    _ARGS = (grad, wtch, italic, step)


def steps(n: str, grad: float, wtch: float, italic: bool = False, step: int = 10) -> dict:
    """One glyph's line of the census."""
    grad_, out, prev = grad, [], None
    for w in range(100, 901, step):
        g = draw(n, params((w, grad_, wtch), italic))
        rings = g.rings()
        shape = rings_to_shapely(rings)
        mv = mx = 0.0
        if prev is not None:
            mv = shape.symmetric_difference(prev).area / max(prev.boundary.length, 1)
            mx = shape.boundary.hausdorff_distance(prev.boundary)
        out.append([w, ','.join(str(len(r)) for r in rings), round(mv, 2), round(mx, 1), len(rings),
                    round(getattr(g, 'lightened', 1.0), 3), json.dumps(dict(sorted(g.overrides.items())))])
        prev = shape
    return {'n': n, 'steps': out, 'changes': sum(1 for a, b in pairwise(out) if a[1] != b[1])}


def _line(n: str) -> str:
    try:
        return json.dumps(steps(n, *_ARGS))
    except Exception as e:  # noqa: BLE001  (a drawing that fails is a line of its own)
        return json.dumps({'n': n, 'error': str(e)})


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0], usage=__doc__.split('\n\n')[1].strip())
    ap.add_argument('out')
    ap.add_argument('italic', nargs='?', choices=['italic'])
    ap.add_argument('--grad', type=float, default=0)
    ap.add_argument('--watch', type=float, default=0)
    ap.add_argument('--step', type=int, default=10)
    a = ap.parse_args(sys.argv[1:] if argv is None else argv)
    settings = Settings.from_env(['italic'] if a.italic else [])
    setup_logging()
    names = glyph_names(settings)
    with open(a.out, 'w', encoding='utf-8') as f, \
            settings.pool(None, _use, (a.grad, a.watch, settings.italic, a.step)) as pool:
        for i, line in enumerate(pool.imap_unordered(_line, names, chunksize=4), 1):
            f.write(line + '\n')
            if i % 200 == 0:
                log.info('%d of %d glyphs', i, len(names))
    log.info('census of %d glyphs at grade %g, watch %g: %s', len(names), a.grad, a.watch, a.out)
    return 0


if __name__ == '__main__':
    sys.exit(main())
