"""A reference font's glyph as a shape: its outline flattened (curves in
eight chords) and its contours combined even-odd, with its advance. The
measuring tools that read other faces share it (letter_shares, stroke_roles,
letter_ink); the fonts themselves are given by path and are not in the
repository."""
from __future__ import annotations

from fontTools.pens.basePen import BasePen
from shapely.geometry import Polygon


class Flat(BasePen):
    def __init__(self, glyphs):
        super().__init__(glyphs)
        self.rings = []
        self.cur = None

    def _moveTo(self, p):
        self.cur = [p]

    def _lineTo(self, p):
        self.cur.append(p)

    def _curveToOne(self, a, b, c):
        p0 = self.cur[-1]
        for i in range(1, 9):
            t = i / 8
            m = 1 - t
            self.cur.append((m ** 3 * p0[0] + 3 * m * m * t * a[0] + 3 * m * t * t * b[0] + t ** 3 * c[0],
                             m ** 3 * p0[1] + 3 * m * m * t * a[1] + 3 * m * t * t * b[1] + t ** 3 * c[1]))

    def _qCurveToOne(self, a, b):
        p0 = self.cur[-1]
        for i in range(1, 9):
            t = i / 8
            m = 1 - t
            self.cur.append((m * m * p0[0] + 2 * m * t * a[0] + t * t * b[0], m * m * p0[1] + 2 * m * t * a[1] + t * t * b[1]))

    def _closePath(self):
        if self.cur and len(self.cur) > 2:
            self.rings.append(self.cur)
        self.cur = None

    _endPath = _closePath


def shape(font, ch):
    """(shape, advance) of a character in a fontTools TTFont."""
    glyphs = font.getGlyphSet()
    name = font.getBestCmap()[ord(ch)]
    pen = Flat(glyphs)
    glyphs[name].draw(pen)
    poly = None
    for ring in pen.rings:
        q = Polygon(ring).buffer(0)
        poly = q if poly is None else poly.symmetric_difference(q)
    return poly, glyphs[name].width
