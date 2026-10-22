"""Render text straight from the glyph engine, upright or italic, without building a font:

usage: engine_proof.py out.png scale "w[,ital][,mono]::text" ...
"""
import sys
import arris.glyphs  # noqa
from arris.draw import REGISTRY
from arris.font import place
from arris.instances import params
from arris.italic import italic, polylines
from arris.proof import render_svg
from arris.glyphs import ALIASES
from PIL import Image
cmap = {chr(s.unicode): n for n, s in REGISTRY.items() if s.unicode}
for u, n in ALIASES.items():
    cmap.setdefault(chr(u), n)
out, scale = sys.argv[1], float(sys.argv[2])
rows = []
for arg in sys.argv[3:]:
    spec, text = arg.split('::', 1)
    w, *flags = spec.split(',')
    p = params(int(w), 0).with_(mono='mono' in flags)
    if 'ital' in flags:
        p = italic(p)
    items = []
    for ch in text:
        if ch == ' ':
            items.append(([], p.fig_adv if p.mono else 0.25 * p.cap)); continue
        r, adv = place(cmap[ch], p)
        items.append((polylines(r) if p.slant else r, adv))
    rows.append(render_svg(items, gap=0, height=900, baseline=260, scale=scale, pad=8))
im = Image.new('L', (max(r.width for r in rows), sum(r.height for r in rows)), 255)
y = 0
for r in rows:
    im.paste(r, (0, y)); y += r.height
im.save(out); print(im.size)
