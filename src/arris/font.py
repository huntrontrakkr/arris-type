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
PUNCT_SIDE = 0.9   # punctuation bearings, as a share of the letters' light


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
    if spec.kind == 'fig' or p.mono:
        adv = p.fig_adv
        dx = (adv - g.W) / 2
    elif isinstance(spec.kind, tuple) and spec.kind[0] == 'punct':
        xs = [x for r in rings for x, _ in r] or [0.0, g.W]
        side = PUNCT_SIDE * light(p) * spec.kind[1]
        dx = side - min(xs)
        adv = side + (max(xs) - min(xs)) + side
    else:
        zone = (0.0, p.xh) if spec.kind == 'lower' else (0.0, p.cap)
        lsb, rsb, xmin, xmax = bearings(rings, *zone, light(p), DEPTH * (zone[1] - zone[0]),
                                        floor=-0.25 * p.m)
        # Parts outside the zone (a j's hook, a descender's tail) may hang
        # into the neighbour's space, but by no more than half its light.
        fx0 = min(x for r in rings for x, _ in r)
        fx1 = max(x for r in rings for x, _ in r)
        reach = 0.5 * light(p)
        lsb = max(lsb, (xmin - fx0) - reach)
        rsb = max(rsb, (fx1 - xmax) - reach)
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


def _contours(rings):
    """Rounded TrueType contours (outer clockwise) from ink-left rings."""
    out = []
    for ring in rings:
        pts = [(round(x), round(y)) for x, y in ring]
        clean = []
        for q in pts:
            if not clean or q != clean[-1]:
                clean.append(q)
        if len(clean) > 1 and clean[0] == clean[-1]:
            clean.pop()
        if len(clean) >= 3:
            out.append(clean[::-1])
    return out


def build(path, names, p: Params, family='Arris', style='SemiBold', weight=600, tune=None,
          metrics: Metrics | None = None, version='0.1', space=None, fea: str | None = None):
    m = metrics or Metrics(cap=round(p.cap), xh=round(p.xh))
    order = ['.notdef', 'space'] + list(names)
    fb = FontBuilder(UPM, isTTF=True)
    fb.setupGlyphOrder(order)
    cmap = {0x20: 'space', 0xA0: 'space'}
    for n in names:
        if REGISTRY[n].unicode is not None:
            cmap[REGISTRY[n].unicode] = n
    fb.setupCharacterMap(cmap)
    glyphs, hmtx = {}, {}
    glyphs['.notdef'], adv = _notdef(p)
    hmtx['.notdef'] = (adv, 40)
    glyphs['space'] = TTGlyphPen(None).glyph()
    hmtx['space'] = (round(space if space is not None else 0.45 * p.xh), 0)
    for n in names:
        rings, adv = place(n, p, tune)
        glyphs[n] = _tt_glyph(_contours(rings), 0)
        hmtx[n] = (round(adv), 0)
    fb.setupGlyf(glyphs)
    ymin, ymax = 0, 0
    for n, (adv, _) in hmtx.items():
        g = glyphs[n]
        g.recalcBounds(fb.font['glyf'])
        if g.numberOfContours:
            ymin, ymax = min(ymin, g.yMin), max(ymax, g.yMax)
        hmtx[n] = (adv, getattr(g, 'xMin', 0) if g.numberOfContours else 0)
    fb.setupHorizontalMetrics(hmtx)
    fb.setupHorizontalHeader(ascent=m.asc, descent=m.desc, lineGap=m.gap)
    ribbi = style in ('Regular', 'Bold')
    fam1 = family if ribbi else f'{family} {style}'
    sub1 = style if ribbi else 'Regular'
    ps = f'{family}-{style}'.replace(' ', '')
    fb.setupNameTable({'familyName': fam1, 'styleName': sub1, 'uniqueFontIdentifier': f'{ps};{version}',
                       'fullName': f'{family} {style}', 'psName': ps, 'version': f'Version {version}',
                       'typographicFamily': family, 'typographicSubfamily': style})
    fb.setupOS2(sTypoAscender=m.asc, sTypoDescender=m.desc, sTypoLineGap=m.gap,
                usWinAscent=max(m.asc, ymax), usWinDescent=max(-m.desc, -ymin), sxHeight=m.xh,
                sCapHeight=m.cap, usWeightClass=weight,
                fsSelection=0x80 | {'Regular': 0x40, 'Bold': 0x20}.get(style, 0),
                achVendID='NONE', version=4)
    fb.setupPost(isFixedPitch=1 if p.mono else 0)
    if p.mono:
        fb.font['OS/2'].panose.bProportion = 9
    if fea:
        from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
        addOpenTypeFeaturesFromString(fb.font, fea)
    fb.font.save(path)
    return fb.font
