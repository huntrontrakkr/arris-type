"""Ink widths against the H's (capitals) and the n's (lowercase), light to heavy: which letters keep their share of width as weight is added."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
CAPS = 'ABCDEFGKLMNOPRSTUVWXYZ'; LOW = 'abcdefgkoprstuvwxyz'
def table(get, label):
    out = {}
    for chars, ref in ((CAPS, 'H'), (LOW, 'n')):
        r = get(ref)
        for c in chars: out[c] = get(c) / r
    return out
def ref(path):
    from refshape import shape
    from fontTools.ttLib import TTFont
    font = TTFont(path)
    def get(c):
        b = shape(font, c)[0].bounds; return b[2] - b[0]
    return table(get, path)
def arris(w):
    import arris.glyphs
    from arris.draw import REGISTRY
    from arris.font import place
    from arris.instances import params
    cmap = {chr(s.unicode): n for n, s in REGISTRY.items() if s.unicode}
    p = params(w)
    def get(c):
        xs = [q[0] for r in place(cmap[c], p)[0] for q in r]; return max(xs) - min(xs)
    return table(get, w)
pairs = [('Inter', ref('/usr/share/fonts/opentype/inter/Inter-Regular.otf'), ref('/usr/share/fonts/opentype/inter/Inter-Black.otf')),
         ('Liberation', ref('/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'), ref('/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf')),
         ('DejaVu', ref('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'), ref('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')),
         ('Arris 400-700', arris(400), arris(700)), ('Arris 400-900', arris(400), arris(900))]
print('change in each letter\'s width against H or n, light to heavy (1.00 = keeps its share)')
print('      ' + ''.join(f'{c:>6}' for c in CAPS + LOW))
for name, a, b in pairs:
    print(f'{name:14}' + ''.join(f'{b[c] / a[c]:6.2f}' for c in CAPS + LOW))
