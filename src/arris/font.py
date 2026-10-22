"""Font assembly: glyph rings to TrueType, static and variable."""
from __future__ import annotations

import math
from dataclasses import dataclass

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.pointPen import SegmentToPointPen  # noqa: F401  (kept for later point pens)

from .draw import REGISTRY, draw
from .params import Params

UPM = 1000


@dataclass
class Metrics:
    asc: int = 950      # hhea/typo ascender: room for accents over capitals
    desc: int = -250
    gap: int = 0
    cap: int = 720
    xh: int = 540


def glyph_contours(name: str, p: Params, tune=None):
    """Integer contours for a glyph, TrueType orientation (outer clockwise)."""
    t = (tune or {}).get(name, {})
    g = draw(name, p, ot=t.get('ot', 0.0), ob=t.get('ob', 0.0))
    out = []
    for ring in g.rings():
        pts = [(round(x), round(y)) for x, y in ring]
        clean = []
        for q in pts:
            if not clean or q != clean[-1]:
                clean.append(q)
        if len(clean) > 1 and clean[0] == clean[-1]:
            clean.pop()
        if len(clean) >= 3:
            out.append(clean[::-1])  # ink-left (CCW shells) -> clockwise shells
    return out


# Optical spacing: the H's sidebearing as a fraction of its counter, and how
# deep into a side's white the eye counts it (fraction of the zone height).
SPACE = 0.27
DEPTH = 0.2


def light(p: Params) -> float:
    """Target mean white per side: the H's sidebearing."""
    h_counter = (9 * p.m + (p.sv - 120)) - 2 * p.sv
    return SPACE * h_counter


def place(name: str, p: Params, tune=None):
    """(rings shifted into place, advance) for a glyph."""
    from .spacing import bearings
    t = (tune or {}).get(name, {})
    g = draw(name, p, ot=t.get('ot', 0.0), ob=t.get('ob', 0.0))
    rings = g.rings()
    spec = REGISTRY[name]
    if spec.kind == 'fig':
        adv = p.fig_adv
        dx = (adv - g.W) / 2
    else:
        zone = (0.0, p.cap)
        lsb, rsb, xmin, xmax = bearings(rings, *zone, light(p), DEPTH * (zone[1] - zone[0]),
                                        floor=-0.25 * p.m)
        dx = lsb - xmin
        adv = lsb + (xmax - xmin) + rsb
    return [[(x + dx, y) for x, y in r] for r in rings], adv


def spacing(name: str, p: Params):
    """(left side bearing, advance) of the glyph body (used by proofs)."""
    rings, adv = place(name, p)
    return 0.0, adv


def _tt_glyph(contours, lsb):
    pen = TTGlyphPen(None)
    for c in contours:
        pen.moveTo((c[0][0] + lsb, c[0][1]))
        for x, y in c[1:]:
            pen.lineTo((x + lsb, y))
        pen.closePath()
    return pen.glyph()


def _notdef(p: Params):
    pen = TTGlyphPen(None)
    w, h, s = 480, 720, 60
    for c in ([(40, 0), (40, h), (40 + w, h), (40 + w, 0)],
              [(40 + s, s), (40 + w - s, s), (40 + w - s, h - s), (40 + s, h - s)]):
        pen.moveTo(c[0])
        for q in c[1:]:
            pen.lineTo(q)
        pen.closePath()
    return pen.glyph(), 560


def build(path, names, p: Params, family='Arris', style='Bold', weight=700, tune=None,
          metrics: Metrics | None = None, version='0.1'):
    m = metrics or Metrics(cap=round(p.cap), xh=round(p.xh))
    order = ['.notdef', 'space'] + list(names)
    fb = FontBuilder(UPM, isTTF=True)
    fb.setupGlyphOrder(order)
    cmap = {0x20: 'space'}
    for n in names:
        if REGISTRY[n].unicode is not None:
            cmap[REGISTRY[n].unicode] = n
    fb.setupCharacterMap(cmap)
    glyphs, hmtx = {}, {}
    glyphs['.notdef'], adv = _notdef(p)
    hmtx['.notdef'] = (adv, 40)
    glyphs['space'] = TTGlyphPen(None).glyph()
    hmtx['space'] = (round(p.fig_adv / 2), 0)
    for n in names:
        lsb, adv = spacing(n, p)
        g = _tt_glyph(glyph_contours(n, p, tune), round(lsb))
        glyphs[n] = g
        hmtx[n] = (round(adv), 0)
    fb.setupGlyf(glyphs)
    # left side bearings come from the glyph bounds
    for n, (adv, _) in hmtx.items():
        g = glyphs[n]
        g.recalcBounds(fb.font['glyf'])
        hmtx[n] = (adv, getattr(g, 'xMin', 0) if g.numberOfContours else 0)
    fb.setupHorizontalMetrics(hmtx)
    fb.setupHorizontalHeader(ascent=m.asc, descent=m.desc, lineGap=m.gap)
    ps = f'{family}-{style}'.replace(' ', '')
    fb.setupNameTable({'familyName': family, 'styleName': style, 'uniqueFontIdentifier': f'{ps};{version}',
                       'fullName': f'{family} {style}', 'psName': ps, 'version': f'Version {version}'})
    fb.setupOS2(sTypoAscender=m.asc, sTypoDescender=m.desc, sTypoLineGap=m.gap,
                usWinAscent=m.asc, usWinDescent=-m.desc, sxHeight=m.xh, sCapHeight=m.cap,
                usWeightClass=weight, fsSelection=0x80 | {'Regular': 0x40, 'Bold': 0x20}.get(style, 0),
                achVendID='NONE', version=4)
    fb.setupPost()
    fb.font.save(path)
    return fb.font
