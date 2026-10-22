"""Render lines of text as a terminal does: rows stacked at the font's line
height (hhea ascender - descender, no gap), glyphs at their advances, so
box drawing, blocks and shades can be checked for seams between cells and
rows.

usage: cell_proof.py out.png px SOURCE::text [SOURCE::text ...]

SOURCE is a built font (path ending .ttf, e.g. build/ArrisMono-Regular.ttf)
or the engine: 'w[,ital][,mono]' (drawn without building a font). px is
the line height in pixels. A text '\\n' starts a new row in the same
block; consecutive arguments are separate blocks with a little paper
between them. A label after a second '::' is written to the left. A SOURCE
ending in '+grid' draws each cell's box in grey behind the ink (and puts a
cell of paper between glyphs, '+grid+gap'). In a text, '{25A0-25FF/16}'
stands for those code points in rows of 16, and '{E0B0}' for one.
"""
from __future__ import annotations

import io
import re
import sys


def expand(text):
    def rng(m):
        a = int(m.group(1), 16)
        b = int(m.group(2), 16) if m.group(2) else a
        n = int(m.group(3)) if m.group(3) else b - a + 1
        cps = list(range(a, b + 1))
        return '\\n'.join(''.join(chr(c) for c in cps[i:i + n]) for i in range(0, len(cps), n))
    return re.sub(r'\{([0-9A-Fa-f]{4,5})(?:-([0-9A-Fa-f]{4,5}))?(?:/(\d+))?\}', rng, text)

import cairosvg
from PIL import Image, ImageDraw


def _engine(spec):
    import arris.glyphs  # noqa: F401
    from arris.draw import REGISTRY
    from arris.font import Metrics, place
    from arris.glyphs import ALIASES
    from arris.instances import params
    from arris.italic import italic, polylines
    w, *flags = spec.split(',')
    p = params(int(w), 0).with_(mono='mono' in flags)
    if 'ital' in flags:
        p = italic(p)
    cmap = {chr(s.unicode): n for n, s in REGISTRY.items() if s.unicode}
    for u, n in ALIASES.items():
        cmap.setdefault(chr(u), n)
    m = Metrics()
    cache = {}

    def glyph(ch):
        if ch == ' ':
            return [], (p.fig_adv if p.mono else 0.45 * p.xh)
        if ch not in cache:
            r, adv = place(cmap[ch], p)
            cache[ch] = (polylines(r) if p.slant else [[q[:2] for q in ring] for ring in r], adv)
        return cache[ch]
    return glyph, m.asc, m.desc, 'paths'


def _font(path):
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.ttLib import TTFont
    f = TTFont(path)
    gs = f.getGlyphSet()
    cmap = f.getBestCmap()
    hmtx = f['hmtx']
    asc, desc = f['hhea'].ascent, f['hhea'].descent

    def glyph(ch, x, base, k):
        from fontTools.pens.transformPen import TransformPen
        n = cmap.get(ord(ch), '.notdef')
        pen = SVGPathPen(gs)
        gs[n].draw(TransformPen(pen, (k, 0, 0, -k, x * k, base * k)))
        return pen.getCommands(), hmtx[n][0]
    return glyph, asc, desc, 'svg'


def block_svg(source, text, px):
    grid, spaced = '+grid' in source, '+gap' in source
    source = source.replace('+grid', '').replace('+gap', '')
    glyph, asc, desc, kind = _font(source) if source.endswith('.ttf') else _engine(source)
    k = px / (asc - desc)
    rows = expand(text).split('\\n')
    if spaced:                                               # a row of paper between rows, too
        rows = [r for row in rows for r in (row, '')][:-1]
    paths, boxes, width = [], [], 0.0
    for r, line in enumerate(rows):
        x = 0.0
        base = r * (asc - desc) + asc
        for i, ch in enumerate(line):
            if spaced and i:
                x += glyph(' ')[1] if kind != 'svg' else glyph(' ', 0, 0, k)[1]
            if grid:
                adv0 = glyph(ch)[1] if kind != 'svg' else glyph(ch, 0, 0, k)[1]
                boxes.append(f'<rect x="{x * k:.3f}" y="{r * px:.3f}" width="{adv0 * k:.3f}" height="{px}" '
                             f'fill="none" stroke="#bbb" stroke-width="1"/>')
            if kind == 'svg':
                d, adv = glyph(ch, x, base, k)
            else:
                g, adv = glyph(ch)
                d = ''.join('M' + 'L'.join(f'{(x + q[0]) * k:.3f},{(base - q[1]) * k:.3f}' for q in ring) + 'Z'
                            for ring in g if len(ring) >= 3)
            paths.append(d)
            x += adv
        width = max(width, x)
    W, H = width * k, len(rows) * px
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{H:.0f}">'
           f'<rect width="100%" height="100%" fill="#fff"/>' + ''.join(boxes) +
           # one path for the whole block: abutting glyphs are filled as one
           # shape, so a seam shows only where the ink really has a gap
           f'<path fill="#000" fill-rule="nonzero" d="{" ".join(paths)}"/></svg>')
    return Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode()))).convert('L')


if __name__ == '__main__':
    out, px = sys.argv[1], int(sys.argv[2])
    blocks = []
    for arg in sys.argv[3:]:
        parts = arg.split('::')
        src, text = parts[0], parts[1]
        label = parts[2] if len(parts) > 2 else ''
        blocks.append((label, block_svg(src, text, px)))
    lw = 8 * max((len(lb) for lb, _ in blocks), default=0) + (16 if any(lb for lb, _ in blocks) else 0)
    gap = max(px // 3, 6)
    Wt = lw + max(im.width for _, im in blocks) + 2 * gap
    Ht = sum(im.height for _, im in blocks) + gap * (len(blocks) + 1)
    page = Image.new('L', (Wt, Ht), 255)
    d = ImageDraw.Draw(page)
    y = gap
    for lb, im in blocks:
        if lb:
            d.text((gap, y + 2), lb, fill=0)
        page.paste(im, (lw + gap, y))
        y += im.height + gap
    page.save(out)
    print(page.size)
