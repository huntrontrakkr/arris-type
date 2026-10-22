"""How confusable are the letters? The ideal-observer measure of
tools/confusion.py, for letters, and for the strings readers mistake for
one another (rn and m, cl and d, I l 1).

Every string is rendered at a common cap height, centred on its advance,
blurred by the eye's contrast-sensitivity filter for a viewing size
(arris.vision), and compared. Distances are relative to the font's mean
string energy, so fonts of different weight compare fairly. Small numbers
are easy to confuse.

usage: letter_confusion.py [arcmin ...]
"""
import itertools
import string
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from arris.vision import View, perceive

PX = 120                        # cap height in raster pixels
CANVAS = (240, 420)             # rows, cols
BASE = 170                      # baseline row
FONTS = {
    'Arris Regular': 'build/Arris-Regular.ttf',
    'Arris SemiBold': 'build/Arris-SemiBold.ttf',
    'Arris Mono Regular': 'build/ArrisMono-Regular.ttf',
    'Atkinson Hyperlegible': 'research-fonts/fonts/AtkinsonHyperlegible-Regular.ttf',
    'B612 Regular': 'research-fonts/fonts/B612-Regular.ttf',
    'Barlow Regular': 'research-fonts/fonts/Barlow-Regular.ttf',
    'Chakra Petch Regular': 'research-fonts/fonts/ChakraPetch-Regular.ttf',
    'JetBrains Mono': 'research-fonts/fonts/JetBrainsMono[wght].ttf',
}
CLASSIC = [('I', 'l'), ('I', '1'), ('l', '1'), ('I', '|'), ('l', '|'), ('O', '0'), ('o', '0'), ('O', 'o'),
           ('S', '5'), ('Z', '2'), ('B', '8'), ('G', '6'), ('g', '9'), ('q', '9'), ('b', '6'), ('D', 'O'),
           ('rn', 'm'), ('cl', 'd'), ('vv', 'w'), ('VV', 'W'), ('ri', 'n'), ('li', 'h'), ('nn', 'm'),
           ('u', 'v'), ('U', 'V'), ('a', 'o'), ('e', 'c'), ('c', 'o'), ('h', 'b'), ('n', 'h'), ('i', 'j'),
           ('t', 'f'), ('y', 'v'), ('C', 'G'), ('E', 'F'), ('P', 'R'), ('K', 'X'), ('M', 'N')]


def renderer(path):
    probe = ImageFont.truetype(path, 400)
    top = probe.getbbox('H', anchor='ls')[1]            # cap height, as a negative offset
    size = 400 * PX / -top
    return ImageFont.truetype(path, size=int(round(size)))


def render(font, s):
    img = Image.new('L', (CANVAS[1], CANVAS[0]), 0)
    adv = font.getlength(s)
    ImageDraw.Draw(img).text((CANVAS[1] / 2 - adv / 2, BASE), s, font=font, fill=255, anchor='ls')
    return np.asarray(img, dtype=np.float64) / 255.0


def distances(path, arcmin, pairs):
    font = renderer(path)
    view = View(cap_arcmin=arcmin, cap_units=PX, px_per_cap=PX)
    strings = sorted({s for p in pairs for s in p})
    blurred = {s: perceive(render(font, s), view) for s in strings}
    norm = np.sqrt(np.mean([np.sum(b * b) for b in blurred.values()]))
    return {(a, b): float(np.sqrt(np.sum((blurred[a] - blurred[b]) ** 2)) / norm) for a, b in pairs}


SETS = {
    'lowercase': list(itertools.combinations(string.ascii_lowercase, 2)),
    'capitals': list(itertools.combinations(string.ascii_uppercase, 2)),
    'classic confusions': CLASSIC,
}

if __name__ == '__main__':
    sizes = [float(x) for x in sys.argv[1:]] or [22.0, 11.0]
    for arcmin in sizes:
        for title, pairs in SETS.items():
            print(f'\n### {title}, cap height {arcmin:g} arcmin\n')
            print('| Font | closest pairs (distance) | mean |')
            print('|---|---|---|')
            for name, path in FONTS.items():
                if not Path(path).exists():
                    continue
                d = distances(path, arcmin, pairs)
                worst = sorted(d.items(), key=lambda kv: kv[1])[:8]
                cells = ', '.join(f'{a}/{b} {v:.2f}' for (a, b), v in worst)
                print(f'| {name} | {cells} | {np.mean(list(d.values())):.2f} |')


# --- From the engine, for trying variants before a font is built -----------

def engine_distances(p, arcmin, pairs, names=None):
    """Distances for strings drawn straight from the glyph engine at params
    ``p``. ``names`` maps a character to a glyph name (a variant under test)."""
    import arris.glyphs  # noqa: F401
    from arris.draw import REGISTRY
    from arris.font import place
    from arris.vision import coverage
    cmap = {chr(s.unicode): n for n, s in REGISTRY.items() if s.unicode}
    cmap.update(names or {})
    cache = {}

    def glyph(ch):
        if ch not in cache:
            r, adv = place(cmap[ch], p)
            if p.slant:                                     # italic contours carry curves
                from arris.italic import polylines
                r = polylines(r)
            cache[ch] = (r, adv)
        return cache[ch]

    view = View(cap_arcmin=arcmin, cap_units=p.cap, px_per_cap=PX)
    strings = sorted({s for pr in pairs for s in pr})
    w, h = CANVAS[1] * p.cap / PX, CANVAS[0] * p.cap / PX
    blurred = {}
    for s in strings:
        rings, x = [], 0.0
        adv = sum(glyph(ch)[1] for ch in s)
        for ch in s:
            r, a = glyph(ch)
            rings += [[(px + x - adv / 2 + w / 2, py) for px, py in ring] for ring in r]
            x += a
        base = (CANVAS[0] - BASE) * p.cap / PX
        cov = coverage(rings, view, 0.0, -base, w, h)
        blurred[s] = perceive(cov, view)
    norm = np.sqrt(np.mean([np.sum(b * b) for b in blurred.values()]))
    return {(a, b): float(np.sqrt(np.sum((blurred[a] - blurred[b]) ** 2)) / norm) for a, b in pairs}
