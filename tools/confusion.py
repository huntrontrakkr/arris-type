"""How confusable are the figures? An ideal-observer measure.

Each figure is rendered at a common height, aligned on its baseline and
centred, passed through the eye's contrast-sensitivity filter for a viewing
size (arris.vision), and compared with every other figure. Two figures are
as distinct as the energy of their blurred difference, relative to the
font's mean figure energy: the quantity an ideal template matcher's
accuracy depends on (Pelli and colleagues' letter-identification work). Small
numbers mean the pair is easy to confuse.

usage: confusion.py [arcmin ...]
"""
import itertools
import sys
from pathlib import Path

import freetype
import numpy as np

from arris.vision import View, perceive

PX = 144                       # figure height in raster pixels
CANVAS = (220, 200)            # rows, cols
FONTS = {
    'Arris SemiBold': 'build/Arris-SemiBold.ttf',
    'Arris Regular': 'build/Arris-Regular.ttf',
    'Arris Watch SemiBold': 'build/ArrisWatch-SemiBold.ttf',
    'Arris Mono Regular': 'build/ArrisMono-Regular.ttf',
    'B612 Regular': 'research-fonts/fonts/B612-Regular.ttf',
    'Atkinson Hyperlegible': 'research-fonts/fonts/AtkinsonHyperlegible-Regular.ttf',
    'Barlow Regular': 'research-fonts/fonts/Barlow-Regular.ttf',
    'Chakra Petch Regular': 'research-fonts/fonts/ChakraPetch-Regular.ttf',
    'Oxanium': 'research-fonts/fonts/Oxanium[wght].ttf',
    'JetBrains Mono': 'research-fonts/fonts/JetBrainsMono[wght].ttf',
}


def figures(path):
    face = freetype.Face(path)
    # scale so the 0 is PX pixels tall
    face.set_pixel_sizes(0, 200)
    face.load_char('0', freetype.FT_LOAD_NO_HINTING)
    h0 = face.glyph.metrics.height / 64
    size = 200 * PX / h0
    face.set_char_size(int(size * 64))
    out = []
    for ch in '0123456789':
        face.load_char(ch, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING)
        g = face.glyph
        bm = g.bitmap
        a = np.array(bm.buffer, dtype=np.float64).reshape(bm.rows, bm.pitch)[:, :bm.width] / 255.0
        img = np.zeros(CANVAS)
        adv = g.advance.x / 64
        base = 180
        top = base - g.bitmap_top
        left = int(round(CANVAS[1] / 2 - adv / 2 + g.bitmap_left))
        img[top:top + a.shape[0], left:left + a.shape[1]] = a
        out.append(img)
    return out


def distances(imgs, arcmin):
    view = View(cap_arcmin=arcmin, cap_units=PX, px_per_cap=PX)
    blurred = [perceive(i, view) for i in imgs]
    norm = np.sqrt(np.mean([np.sum(b * b) for b in blurred]))
    return {(a, b): float(np.sqrt(np.sum((blurred[a] - blurred[b]) ** 2)) / norm)
            for a, b in itertools.combinations(range(10), 2)}


if __name__ == '__main__':
    sizes = [float(x) for x in sys.argv[1:]] or [44.0, 11.0, 6.0]
    for arcmin in sizes:
        print(f'\n### Figure height {arcmin:g} arcmin\n')
        print('| Font | closest pairs (distance) | mean |')
        print('|---|---|---|')
        for name, path in FONTS.items():
            if not Path(path).exists():
                continue
            d = distances(figures(path), arcmin)
            worst = sorted(d.items(), key=lambda kv: kv[1])[:5]
            pairs = ', '.join(f'{a}/{b} {v:.2f}' for (a, b), v in worst)
            print(f'| {name} | {pairs} | {np.mean(list(d.values())):.2f} |')
