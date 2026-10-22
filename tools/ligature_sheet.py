"""Every Arris Mono ligature, set from the built fonts by HarfBuzz, at
Thin, Regular, Black and Black Italic; with 'fira PATH' a Fira Code row
above each, for comparison.

usage: ligature_sheet.py out.png [px] [fira PATH]
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from hbspec import line  # noqa: E402

import arris.glyphs  # noqa: E402,F401
from arris.draw import REGISTRY  # noqa: E402
from arris.glyphs.ligatures import LIGATURES  # noqa: E402

FONTS = ['build/ArrisMono-Thin.ttf', 'build/ArrisMono-Regular.ttf', 'build/ArrisMono-Black.ttf',
         'build/ArrisMono-BlackItalic.ttf']
PER_ROW = 11

if __name__ == '__main__':
    args = sys.argv[1:]
    out = args[0]
    px = int(args[1]) if len(args) > 1 and args[1].isdigit() else 48
    fira = args[args.index('fira') + 1] if 'fira' in args else None
    chars = {n: chr(s.unicode) for n, s in REGISTRY.items() if s.unicode}
    seqs = [''.join(chars[c] for c in comps) for _, comps in LIGATURES]
    rows = []
    for i in range(0, len(seqs), PER_ROW):
        text = '   '.join(seqs[i:i + PER_ROW])
        for path in ([fira] if fira else []) + FONTS:
            rows.append(line(path, text, px, []))
        rows.append(Image.new('L', (1, px // 2), 255))
    page = Image.new('L', (max(r.width for r in rows), sum(r.height for r in rows)), 255)
    y = 0
    for r in rows:
        page.paste(r, (0, y))
        y += r.height
    page.save(out)
    print(page.size, len(seqs), 'ligatures')
