"""Images set in type, for the presentation: pictures drawn with Arris Mono's
own glyphs.

* ``shapes``: ASCII art by shape. Every printable ASCII glyph is rasterised
  from the built font into a small grid of sub-cells; each cell of the
  picture takes the glyph whose ink best matches that patch of the image
  (least squares), so edges come out as / \\ | _ ( ) and tone as density.
* ``braille``: a picture dithered (Floyd-Steinberg) onto the Braille dot
  lattice, two by four dots a cell. In Arris Mono the dots stand on an even
  lattice (290 and 300 units) at a line height of 1.2, so the dither is
  even too.
* ``gradient``: a colour for a tone, from stops (gradient mapping).
"""
from __future__ import annotations

import numpy as np
from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw

ASCENT, DESCENT = 950, 250          # Arris Mono's cell, font units (block elements fill it)


class _Rings(BasePen):
    def __init__(self, gs):
        super().__init__(gs)
        self.rings, self.cur = [], []

    def _moveTo(self, pt):
        self.cur = [pt]

    def _lineTo(self, pt):
        self.cur.append(pt)

    def _qCurveToOne(self, a, b):
        p0 = self.cur[-1]
        for i in range(1, 7):
            t = i / 6
            self.cur.append(((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * a[0] + t * t * b[0],
                             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * a[1] + t * t * b[1]))

    def _curveToOne(self, a, b, c):
        self.cur.append(c)

    def _closePath(self):
        self.rings.append(self.cur)
        self.cur = []


def glyph_grids(font_path, chars, sub=(6, 12), ss=8):
    """{char: array (sub_h, sub_w) of ink coverage 0..1} over the Mono cell."""
    font = TTFont(font_path)
    gs, cmap = font.getGlyphSet(), font.getBestCmap()
    out = {}
    for ch in chars:
        name = cmap.get(ord(ch))
        if name is None:
            continue
        adv = font['hmtx'][name][0]
        W, H = sub[0] * ss, sub[1] * ss
        img = Image.new('L', (W, H), 0)
        pen = _Rings(gs)
        gs[name].draw(pen)
        d = ImageDraw.Draw(img)
        for r in pen.rings:
            area = sum(r[i - 1][0] * r[i][1] - r[i][0] * r[i - 1][1] for i in range(len(r)))
            pts = [(x / adv * W, (ASCENT - y) / (ASCENT + DESCENT) * H) for x, y in r]
            if len(pts) > 2:
                d.polygon(pts, fill=255 if area > 0 else 0)
        a = np.asarray(img, dtype=np.float32) / 255.0
        out[ch] = a.reshape(sub[1], ss, sub[0], ss).mean(axis=(1, 3))
    return out


def shapes(tone, glyphs):
    """tone: array (rows * sub_h, cols * sub_w), 0..1 (1 = full ink). Returns
    rows of chars: each cell the glyph with the least squared difference."""
    chars = list(glyphs)
    G = np.stack([glyphs[c] for c in chars])                # (k, sh, sw)
    k, sh, sw = G.shape
    rows, cols = tone.shape[0] // sh, tone.shape[1] // sw
    P = tone[:rows * sh, :cols * sw].reshape(rows, sh, cols, sw).transpose(0, 2, 1, 3).reshape(rows * cols, sh * sw)
    Gf = G.reshape(k, sh * sw)
    err = (P ** 2).sum(1)[:, None] - 2 * P @ Gf.T + (Gf ** 2).sum(1)[None, :]
    best = err.argmin(1).reshape(rows, cols)
    return [''.join(chars[i] for i in row) for row in best]


def braille(tone, gamma=1.0):
    """tone: array (rows * 4, cols * 2), 0..1 (1 = dot). Floyd-Steinberg onto
    the dot lattice; returns rows of Braille characters."""
    a = np.clip(tone, 0, 1).astype(np.float64) ** gamma
    h, w = a.shape
    on = np.zeros_like(a, dtype=bool)
    for y in range(h):
        for x in range(w):
            old = a[y, x]
            new = 1.0 if old >= 0.5 else 0.0
            on[y, x] = new > 0
            e = old - new
            if x + 1 < w:
                a[y, x + 1] += e * 7 / 16
            if y + 1 < h:
                if x > 0:
                    a[y + 1, x - 1] += e * 3 / 16
                a[y + 1, x] += e * 5 / 16
                if x + 1 < w:
                    a[y + 1, x + 1] += e * 1 / 16
    bits = [(0, 0, 0x01), (0, 1, 0x02), (0, 2, 0x04), (1, 0, 0x08), (1, 1, 0x10), (1, 2, 0x20), (0, 3, 0x40), (1, 3, 0x80)]
    rows, cols = h // 4, w // 2
    out = []
    for r in range(rows):
        line = []
        for c in range(cols):
            code = 0
            for dx, dy, b in bits:
                if on[r * 4 + dy, c * 2 + dx]:
                    code |= b
            line.append(chr(0x2800 + code))
        out.append(''.join(line))
    return out


def gradient(stops, t):
    """Colour (r, g, b) at t from [(t, (r, g, b)), ...] stops."""
    t = float(np.clip(t, 0, 1))
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        if t <= t1:
            u = (t - t0) / ((t1 - t0) or 1)
            return tuple(c0[i] + (c1[i] - c0[i]) * u for i in range(3))
    return stops[-1][1]


def hexc(c):
    return '#%02x%02x%02x' % tuple(int(np.clip(v, 0, 255)) for v in c)


def cells_html(chars, colours, esc):
    """Rows of characters and rows of colours (None: blank) as spans."""
    out = []
    for line, cols in zip(chars, colours):
        runs, cur, buf = [], None, ''
        for ch, col in zip(line, cols):
            col = col or 'transparent'
            if col != cur and buf:
                runs.append(f'<span style="color:{cur}">{esc(buf)}</span>')
                buf = ''
            cur = col
            buf += ch
        runs.append(f'<span style="color:{cur}">{esc(buf)}</span>')
        out.append(''.join(runs))
    return '\n'.join(out)
