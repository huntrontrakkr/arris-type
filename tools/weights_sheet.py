"""All glyphs of a set at the nine weights, one row per weight."""
import sys

import arris.glyphs  # noqa: F401

from PIL import Image

from arris.font import place
from arris.instances import STEMS, params
from arris.proof import render_svg

chars = sys.argv[1]
names = {str(i): n for i, n in enumerate(['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine'])}
scale = float(sys.argv[3]) if len(sys.argv) > 3 else 0.06
rows, errors = [], []
for w in (int(x) for x in (sys.argv[4].split(',') if len(sys.argv) > 4 else STEMS)):
    p = params(w)
    items = []
    for ch in chars:
        if ch == ' ':
            items.append(([], 250)); continue
        try:
            items.append(place(names.get(ch, ch), p))
        except Exception as e:
            errors.append((w, ch, repr(e)[:120])); items.append(([], 500))
    rows.append(render_svg(items, gap=0, height=820, baseline=200, scale=scale, pad=8))
im = Image.new('L', (max(r.width for r in rows), sum(r.height for r in rows)), 255)
y = 0
for r in rows:
    im.paste(r, (0, y)); y += r.height
im.save(sys.argv[2])
for e in errors:
    print(*e)
print(im.size)
