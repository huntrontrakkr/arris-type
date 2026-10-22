"""Build static TTFs: tools/build_fonts.py [weights] [watch] [mono] [italic]

weights: comma-separated (default all nine); 'watch' builds the watch-
proportions family (Arris Watch) instead of the measured optics; 'mono' the
monospaced cut; 'italic' the italics (arris.italic).
"""
import sys

import arris.glyphs  # noqa: F401
from pathlib import Path

from arris.draw import REGISTRY
from arris.font import build
from arris.glyphs.features import fea
from arris.instances import HERITAGE_OPTICS, NAMES, OPTICS, STEMS, params
from arris.italic import italic

FIGS = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine']
weights = [int(w) for w in sys.argv[1].split(',')] if len(sys.argv) > 1 and sys.argv[1] != 'all' else list(STEMS)
watch = 'watch' in sys.argv[2:]
mono = 'mono' in sys.argv[2:]
ital = 'italic' in sys.argv[2:]
family = 'Arris' + (' Mono' if mono else '') + (' Watch' if watch else '')
names = FIGS + [n for n in REGISTRY if n not in FIGS and not n.endswith('.ital')]   # italic drawings replace their uprights (arris.italic)
Path('build').mkdir(exist_ok=True)
for w in weights:
    p = params(w, optics=HERITAGE_OPTICS if watch else OPTICS).with_(mono=mono)
    style = NAMES[w]
    if ital:
        p = italic(p)
        style = 'Italic' if style == 'Regular' else f'{style} Italic'
    path = f"build/{family.replace(' ', '')}-{style.replace(' ', '')}.ttf"
    build(path, names, p, family=family, style=style, weight=w, fea=fea())
    print(path, len(names) + 2, 'glyphs')
