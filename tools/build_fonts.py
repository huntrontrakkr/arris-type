"""Build static TTFs: tools/build_fonts.py [weights] (default: all nine)."""
import sys

import arris.glyphs  # noqa: F401
from pathlib import Path

from arris.draw import REGISTRY
from arris.font import build
from arris.glyphs.features import fea
from arris.instances import NAMES, STEMS, params

FIGS = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine']
weights = [int(w) for w in sys.argv[1].split(',')] if len(sys.argv) > 1 else list(STEMS)
names = FIGS + [n for n in REGISTRY if n not in FIGS]
Path('build').mkdir(exist_ok=True)
for w in weights:
    p = params(w)
    path = f'build/Arris-{NAMES[w]}.ttf'
    build(path, names, p, style=NAMES[w], weight=w, fea=fea())
    print(path, len(names) + 2, 'glyphs')
