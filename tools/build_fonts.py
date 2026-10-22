"""Build static TTFs: tools/build_fonts.py [weights] [watch]

weights: comma-separated (default all nine); 'watch' builds the watch-
proportions family (Arris Watch) instead of the measured optics.
"""
import sys

import arris.glyphs  # noqa: F401
from pathlib import Path

from arris.draw import REGISTRY
from arris.font import build
from arris.glyphs.features import fea
from arris.instances import HERITAGE_OPTICS, NAMES, OPTICS, STEMS, params

FIGS = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine']
weights = [int(w) for w in sys.argv[1].split(',')] if len(sys.argv) > 1 and sys.argv[1] != 'all' else list(STEMS)
watch = 'watch' in sys.argv[2:]
family = 'Arris Watch' if watch else 'Arris'
names = FIGS + [n for n in REGISTRY if n not in FIGS]
Path('build').mkdir(exist_ok=True)
for w in weights:
    p = params(w, optics=HERITAGE_OPTICS if watch else OPTICS)
    path = f"build/{family.replace(' ', '')}-{NAMES[w]}.ttf"
    build(path, names, p, family=family, style=NAMES[w], weight=w, fea=fea())
    print(path, len(names) + 2, 'glyphs')
