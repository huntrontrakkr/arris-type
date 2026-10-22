"""Shape with HarfBuzz (features on) and render with FreeType.

usage: hbspec.py out.png px 'font.ttf::text[::@feat,feat,wght=700]' ...
"""
import sys

import freetype
import numpy as np
import uharfbuzz as hb
from PIL import Image


def line(path, text, px, feats, pad=8):
    blob = hb.Blob.from_file_path(path)
    font = hb.Font(hb.Face(blob))
    axes = {f.split('=')[0]: float(f.split('=')[1]) for f in feats if '=' in f}
    feats = [f for f in feats if '=' not in f]
    if axes:
        font.set_variations(axes)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, {f: True for f in feats if f} | {f[1:]: False for f in feats if f.startswith('-')})
    upem = font.face.upem
    face = freetype.Face(path)
    face.set_pixel_sizes(0, px)
    if axes:
        tags = [a.tag for a in face.get_variation_info().axes]
        face.set_var_design_coords([axes.get(t, a.default) for t, a in zip(tags, face.get_variation_info().axes)])
    scale = px / upem
    pen, raw = 0.0, []
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        face.load_glyph(info.codepoint, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING)
        g = face.glyph
        bm = g.bitmap
        arr = np.array(bm.buffer, dtype=np.uint8).reshape(bm.rows, bm.pitch)[:, :bm.width] if bm.rows else None
        raw.append((pen + pos.x_offset * scale + g.bitmap_left, g.bitmap_top + pos.y_offset * scale, arr))
        pen += pos.x_advance * scale
    tops = [t for _, t, a in raw if a is not None] + [int(face.size.ascender / 64)]
    bots = [a.shape[0] - t for _, t, a in raw if a is not None] + [int(-face.size.descender / 64)]
    asc, desc = int(max(tops)) + pad, int(max(bots)) + pad
    img = np.zeros((asc + desc, int(pen) + 2 * pad), dtype=np.float32)
    for x, t, arr in raw:
        if arr is None:
            continue
        x, y = int(round(x)) + pad, int(round(asc - t))
        h, w = arr.shape
        img[y:y + h, x:x + w] = np.maximum(img[y:y + h, x:x + w], arr / 255.0)
    return Image.fromarray((255 * (1 - img)).astype(np.uint8))


if __name__ == '__main__':
    out, px = sys.argv[1], int(sys.argv[2])
    imgs = []
    for spec in sys.argv[3:]:
        parts = spec.split('::')
        path = parts[0]
        if len(parts) > 2 and parts[-1].startswith('@'):   # features and axes after '::@'
            feats, parts = parts[-1][1:].split(','), parts[:-1]
        else:
            feats = []
        text = '::'.join(parts[1:])                         # the text may contain '::' itself
        imgs.append(line(path, text, px, feats))
    canvas = Image.new('L', (max(i.width for i in imgs), sum(i.height for i in imgs)), 255)
    y = 0
    for i in imgs:
        canvas.paste(i, (0, y)); y += i.height
    canvas.save(out)
    print(canvas.size)
