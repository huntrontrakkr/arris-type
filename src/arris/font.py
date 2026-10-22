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
    if p.grade_k != 1.0:
        # Grade changes strokes only: space the glyph as its ungraded self,
        # then draw the graded strokes in the same body at the same place.
        p0 = p.ungraded()
        g0 = draw(name, p0, ot=t.get('ot', 0.0), ob=t.get('ob', 0.0))
        r0, adv = place(name, p0, tune)
        dx = min(x for r in r0 for x, _ in r) - min(x for r in g0.rings() for x, _ in r) if r0 else 0.0
        # glyphs no wider than a couple of stems (I, i, dots) thicken outward,
        # centred where they were; everything else keeps its body
        W = g0.W
        if W <= 2.5 * p0.sv:
            W = REGISTRY[name].width(p)
            dx += (g0.W - W) / 2
        g = draw(name, p, ot=t.get('ot', 0.0), ob=t.get('ob', 0.0), width=W)
        return [[(x + dx, y) for x, y in r] for r in g.rings()], adv
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


def _raw_glyph(contours):
    """A glyf glyph with exactly these points: nothing merged or dropped,
    as variable-font masters need."""
    from fontTools.ttLib.tables._g_l_y_f import Glyph, GlyphCoordinates
    g = Glyph()
    pts, ends = [], []
    for c in contours:
        pts.extend(c)
        ends.append(len(pts) - 1)
    g.numberOfContours = len(contours)
    g.coordinates = GlyphCoordinates(pts)
    g.endPtsOfContours = ends
    g.flags = bytearray([1] * len(pts))
    g.program = __import__('fontTools.ttLib.tables.ttProgram', fromlist=['Program']).Program()
    g.program.fromBytecode(b'')
    return g


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


KERN_PUNCT = {'period', 'comma', 'colon', 'semicolon', 'hyphen', 'endash', 'emdash', 'quotesingle', 'quotedbl',
              'quoteleft', 'quoteright', 'quotedblleft', 'quotedblright', 'quotesinglbase', 'quotedblbase',
              'parenleft', 'parenright', 'bracketleft', 'bracketright', 'braceleft', 'braceright', 'slash',
              'backslash', 'guilsinglleft', 'guilsinglright', 'guillemotleft', 'guillemotright', 'exclam',
              'question', 'ampersand', 'asterisk', 'at', 'ellipsis'}


def _contours(rings, keep=False):
    """Rounded TrueType contours (outer clockwise) from ink-left rings.
    ``keep``: keep every point, duplicates included (variable-font masters)."""
    out = []
    for ring in rings:
        pts = [(round(x), round(y)) for x, y in ring]
        if keep:
            out.append(pts[::-1])
            continue
        clean = []
        for q in pts:
            if not clean or q != clean[-1]:
                clean.append(q)
        if len(clean) > 1 and clean[0] == clean[-1]:
            clean.pop()
        if len(clean) >= 3:
            out.append(clean[::-1])
    return out


def _nonhinting(font):
    """No hints, but smart dropout control and a gasp table, so unhinted
    outlines rasterise solidly at small sizes (what gftools fix-nonhinting does)."""
    from fontTools.ttLib import newTable
    from fontTools.ttLib.tables import ttProgram
    prep = newTable('prep')
    prep.program = ttProgram.Program()
    prep.program.fromAssembly(['PUSHW[ ]', '511', 'SCANCTRL[ ]', 'PUSHB[ ]', '4', 'SCANTYPE[ ]'])
    font['prep'] = prep
    gasp = newTable('gasp')
    gasp.version = 1
    gasp.gaspRange = {0xFFFF: 0x000F}
    font['gasp'] = gasp


def build(path, names, p: Params, family='Arris', style='SemiBold', weight=600, tune=None,
          metrics: Metrics | None = None, version='0.100', space=None, fea: str | None = None,
          kern: bool = True, placed: dict | None = None, kern_pairs: dict | None = None):
    m = metrics or Metrics(cap=round(p.cap), xh=round(p.xh))
    order = ['.notdef', 'space'] + list(names)
    fb = FontBuilder(UPM, isTTF=True)
    fb.setupGlyphOrder(order)
    cmap = {0x20: 'space', 0xA0: 'space'}
    for n in names:
        if REGISTRY[n].unicode is not None:
            cmap[REGISTRY[n].unicode] = n
    from .glyphs import ALIASES
    for cp, n in ALIASES.items():
        if n in names and cp not in cmap:
            cmap[cp] = n
    fb.setupCharacterMap(cmap)
    glyphs, hmtx = {}, {}
    glyphs['.notdef'], adv = _notdef(p)
    hmtx['.notdef'] = (adv, 40)
    glyphs['space'] = TTGlyphPen(None).glyph()
    hmtx['space'] = (round(space if space is not None else 0.45 * p.xh), 0)
    keep = placed is not None
    placed = dict(placed or {})
    for n in names:
        if n not in placed:
            placed[n] = place(n, p, tune)
        rings, adv = placed[n]
        glyphs[n] = _raw_glyph(_contours(rings, keep)) if keep else _tt_glyph(_contours(rings), 0)
        hmtx[n] = (round(adv), 0)
    if kern_pairs is not None:
        from .kerning import fea as kern_fea
        fea = (fea or '') + kern_fea(kern_pairs)
    elif kern and not p.mono:
        from .kerning import fea as kern_fea, kerns
        kinds = {n: REGISTRY[n].kind for n in names}
        kernable = [n for n in names if kinds[n] in ('cap', 'lower') or
                    (isinstance(kinds[n], tuple) and n in KERN_PUNCT)]
        pairs = kerns({n: (placed[n][0], round(placed[n][1])) for n in kernable}, p, light(p))
        fea = (fea or '') + kern_fea(pairs)
        print(f'  {len(pairs)} kerning pairs')
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
                       'typographicFamily': family, 'typographicSubfamily': style}, mac=False)
    fb.setupOS2(sTypoAscender=m.asc, sTypoDescender=m.desc, sTypoLineGap=m.gap,
                usWinAscent=max(m.asc, ymax), usWinDescent=max(-m.desc, -ymin), sxHeight=m.xh,
                sCapHeight=m.cap, usWeightClass=weight,
                fsSelection=0x80 | {'Regular': 0x40, 'Bold': 0x20}.get(style, 0),
                achVendID='NONE', version=4)
    fb.setupPost(isFixedPitch=1 if p.mono else 0)
    fb.font['head'].fontRevision = float(version)
    os2 = fb.font['OS/2']
    os2.recalcCodePageRanges(fb.font)
    os2.recalcUnicodeRanges(fb.font)
    _nonhinting(fb.font)
    if p.mono:
        fb.font['OS/2'].panose.bProportion = 9
    if fea:
        from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
        addOpenTypeFeaturesFromString(fb.font, fea)
    fb.font.save(path)
    return fb.font
