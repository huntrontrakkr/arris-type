"""Render text with built TTFs through FreeType (antialiased, unhinted)."""
import sys

import freetype
import numpy as np
from PIL import Image


def line(path, text, px, pad=8):
    face = freetype.Face(path)
    face.set_pixel_sizes(0, px)
    asc = int(face.size.ascender / 64) + pad
    desc = int(-face.size.descender / 64) + pad
    pen, glyphs = 0, []
    for ch in text:
        face.load_char(ch, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING)
        g = face.glyph
        bm = g.bitmap
        arr = np.array(bm.buffer, dtype=np.uint8).reshape(bm.rows, bm.pitch)[:, :bm.width] if bm.rows else None
        glyphs.append((pen + g.bitmap_left, asc - g.bitmap_top, arr))
        pen += g.advance.x / 64
    img = np.zeros((asc + desc, int(pen) + 2 * pad), dtype=np.float32)
    for x, y, arr in glyphs:
        if arr is None:
            continue
        x = int(round(x)) + pad
        h, w = arr.shape
        img[y:y + h, x:x + w] = np.maximum(img[y:y + h, x:x + w], arr / 255.0)
    return Image.fromarray((255 * (1 - img)).astype(np.uint8))


if __name__ == '__main__':
    out, px = sys.argv[1], int(sys.argv[2])
    specs = sys.argv[3:]
    imgs = []
    for spec in specs:
        path, text = spec.split('::', 1)
        imgs.append(line(path, text, px))
    W = max(i.width for i in imgs)
    canvas = Image.new('L', (W, sum(i.height for i in imgs)), 255)
    y = 0
    for i in imgs:
        canvas.paste(i, (0, y)); y += i.height
    canvas.save(out)
    print(canvas.size)
