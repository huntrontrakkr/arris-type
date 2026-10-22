"""Build static TTFs: tools/build_fonts.py [weights] (default: all nine)."""
import sys
from pathlib import Path

import arris.glyphs.figures  # noqa: F401
import arris.glyphs.caps  # noqa: F401
import arris.glyphs.lower  # noqa: F401
import arris.glyphs.punct  # noqa: F401
from arris.draw import REGISTRY
from arris.font import build
from arris.instances import NAMES, STEMS, params

FIGS = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine']
weights = [int(w) for w in sys.argv[1].split(',')] if len(sys.argv) > 1 else list(STEMS)
names = FIGS + sorted(n for n, s in REGISTRY.items() if s.kind == 'cap') + \
    sorted(n for n, s in REGISTRY.items() if s.kind == 'lower') + \
    sorted(n for n, s in REGISTRY.items() if isinstance(s.kind, tuple))
Path('build').mkdir(exist_ok=True)
for w in weights:
    p = params(w)
    path = f'build/Arris-{NAMES[w]}.ttf'
    build(path, names, p, style=NAMES[w], weight=w)
    print(path, len(names) + 2, 'glyphs')
