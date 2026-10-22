"""Contact sheet: every glyph in a font file, in a grid, with its name."""
import sys

import freetype
import numpy as np
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw

path, out = sys.argv[1], sys.argv[2]
names = sys.argv[3].split(',') if len(sys.argv) > 3 and sys.argv[3] else None
cell, px, cols = 64, 40, 24
font = TTFont(path)
order = names or [n for n in font.getGlyphOrder() if n not in ('.notdef', 'space')]
face = freetype.Face(path)
face.set_pixel_sizes(0, px)
rows = (len(order) + cols - 1) // cols
img = Image.new('L', (cols * cell, rows * (cell + 10)), 255)
d = ImageDraw.Draw(img)
gid = {n: i for i, n in enumerate(font.getGlyphOrder())}
for k, n in enumerate(order):
    face.load_glyph(gid[n], freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING)
    bm = face.glyph.bitmap
    x0, y0 = (k % cols) * cell, (k // cols) * (cell + 10)
    if bm.rows:
        a = np.array(bm.buffer, dtype=np.uint8).reshape(bm.rows, bm.pitch)[:, :bm.width]
        g = Image.fromarray(255 - a)
        top = int(cell * 0.75) - face.glyph.bitmap_top
        img.paste(g, (x0 + 8 + face.glyph.bitmap_left, y0 + max(0, top)))
    d.text((x0 + 2, y0 + cell), n[:10], fill=120)
img.save(out)
print(img.size, len(order))
