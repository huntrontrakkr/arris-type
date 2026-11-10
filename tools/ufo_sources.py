"""UFO sources for Google Fonts, written from a built variable font.

    python tools/ufo_sources.py FONT.ttf OUT_DIR [--only GLYPH ...]

Arris is drawn by code (src/arris); Google Fonts asks for sources a font
editor reads, built by fontmake. These are that: the masters of
Arris[GRAD,wght].ttf (tools/google_fonts.py) written out as UFOs with the
designspace that joins them, so that fontmake builds the same font.

Full masters, one UFO each, stand where the kerning has a master: every
weight the font has one at, ungraded, and five weights at the grade's ends
(arris.vf.space.BASE, the watch left out). A glyph the font carries on a
finer grid than those (its own masters, arris.vf.encode.prune) has the
rest of its grid as sparse layers of the Regular UFO, one layer a place,
each holding only the glyphs with a master there. A glyph's variations in
the font change slope only at the values its tuples start, peak and end
at, so the font's outline is multilinear within the cells of the grid of
those values; with a master at every node of that grid, fontmake's model
is the same function, to the rounding of a unit.

Each master is the font's own outline at its place (points as the font
has them: quadratic, on and off the curve, the same order and start), its
advances, its anchors and its kerning, read from the font instanced there.
"""
from __future__ import annotations

import sys
from itertools import product
from pathlib import Path

import numpy as np
import ufoLib2
from fontTools.designspaceLib import AxisDescriptor, DesignSpaceDocument, SourceDescriptor
from fontTools.ttLib import TTFont
from fontTools.varLib.models import VariationModel, normalizeLocation

WEIGHTS = (100, 200, 300, 400, 500, 600, 700, 750, 800, 850, 900)
GRADED = (100, 400, 600, 800, 900)
FULL = [(w, 0) for w in WEIGHTS] + [(w, g) for w in GRADED for g in (-100, 100)]
DEFAULT = (400, 0)
NAMES = {100: 'Thin', 200: 'ExtraLight', 300: 'Light', 400: 'Regular', 500: 'Medium', 600: 'SemiBold', 700: 'Bold',
         750: 'W750', 800: 'ExtraBold', 850: 'W850', 900: 'Black'}
TOL = 0.5           # units: a glyph keeps to the full masters alone if their model is this near its own grid


def master_name(w: float, g: float) -> str:
    return NAMES[w] + {0: '', -100: 'GradeLow', 100: 'GradeHigh'}[g]


def layer_name(w: float, g: float) -> str:
    return f'wght{w:g} GRAD{g:g}'


def glyph_coords(glyf, hmtx, gvar, name: str, loc: dict[str, float]) -> np.ndarray:
    """A glyph's coordinates with its four phantom points, at a normalised place."""
    from fontTools.varLib.iup import iup_delta
    from fontTools.varLib.models import supportScalar
    coords, ctrl = glyf._getCoordinatesAndControls(name, hmtx, None)
    out = np.array(coords, dtype=float)
    orig = list(coords)
    for tv in gvar.variations.get(name, ()):
        s = supportScalar(loc, tv.axes)
        if not s:
            continue
        d = tv.coordinates
        if None in d:
            d = iup_delta(d, orig, ctrl.endPts)
        out += s * np.array(d, dtype=float)
    return out


def main() -> int:
    args = sys.argv[1:]
    only = None
    if '--only' in args:
        i = args.index('--only')
        only, args = set(args[i + 1:]), args[:i]
    src, out = args[0], Path(args[1])
    tt = TTFont(src)
    italic = 'Italic' in Path(src).name
    family = 'Arris'
    stem = 'Arris-Italic' if italic else 'Arris'
    axes = {a.axisTag: (a.minValue, a.defaultValue, a.maxValue) for a in tt['fvar'].axes}
    glyf, hmtx, gvar = tt['glyf'], tt['hmtx'].metrics, tt['gvar']
    order = [n for n in tt.getGlyphOrder() if only is None or n in only or n == '.notdef']
    cmap = {}
    for cp, n in tt.getBestCmap().items():
        cmap.setdefault(n, []).append(cp)

    def norm(place):
        return normalizeLocation({'wght': place[0], 'GRAD': place[1]}, axes)

    def user(tag, v):
        lo, df, hi = axes[tag]
        return round(df + v * ((df - lo) if v < 0 else (hi - df)), 2)

    def at(name, place):
        return glyph_coords(glyf, hmtx, gvar, name, norm(place))

    # each glyph's own grid, and whether the full masters alone carry it
    full_locs = [norm(p) for p in FULL]
    full_model = VariationModel(full_locs, axisOrder=['wght', 'GRAD'])
    sparse: dict[tuple[float, float], list[str]] = {}
    kept = 0
    for n in order:
        ws, gs = set(WEIGHTS), {-100.0, 0.0, 100.0}
        for tv in gvar.variations.get(n, ()):
            for tag, vals in tv.axes.items():
                (ws if tag == 'wght' else gs).update(user(tag, v) for v in vals)
        grid = [p for p in product(sorted(ws), sorted(gs)) if p not in FULL]
        if not grid or n not in gvar.variations:
            continue
        masters = [at(n, p) for p in FULL]
        deltas = full_model.getDeltas(masters)
        worst = max(float(np.abs(np.tensordot(full_model.getScalars(norm(p)), np.array(deltas), 1) - at(n, p)).max())
                    for p in grid)
        if worst <= TOL:
            continue
        kept += 1
        for p in grid:
            sparse.setdefault(p, []).append(n)
    print(f'{len(order)} glyphs; {kept} carry masters past the full ones, at {len(sparse)} places')

    def write_glyph(layer, name, place, with_meta):
        g = layer.newGlyph(name)
        coords = at(name, place)
        tg = glyf[name]
        g.width = round(coords[-3][0] - coords[-4][0])
        if with_meta and name in cmap:
            g.unicodes = sorted(cmap[name])
        pen = g.getPointPen()
        if tg.isComposite():
            for c, (x, y) in zip(tg.components, coords[:-4]):
                t = getattr(c, 'transform', ((1, 0), (0, 1)))
                pen.addComponent(c.glyphName, (t[0][0], t[0][1], t[1][0], t[1][1], round(x), round(y)))
            return
        if tg.numberOfContours <= 0:
            return
        start = 0
        for end in tg.endPtsOfContours:
            pts = [(round(x), round(y)) for x, y in coords[start:end + 1]]
            flags = tg.flags[start:end + 1]
            pen.beginPath()
            for (x, y), on in zip(pts, flags):
                pen.addPoint((x, y), segmentType='qcurve' if on & 1 else None)
            pen.endPath()
            start = end + 1

    out.mkdir(parents=True, exist_ok=True)
    doc = DesignSpaceDocument()
    for tag, name in (('wght', 'Weight'), ('GRAD', 'Grade')):
        a = AxisDescriptor()
        a.tag, a.name = tag, name
        a.minimum, a.default, a.maximum = axes[tag]
        doc.addAxis(a)
    os2, hhea, head, post = tt['OS/2'], tt['hhea'], tt['head'], tt['post']
    default_ufo = None
    for w, g in FULL:
        ufo = ufoLib2.Font()
        info = ufo.info
        info.familyName, info.styleName = family, master_name(w, g) + (' Italic' if italic else '')
        info.unitsPerEm = head.unitsPerEm
        info.ascender, info.descender = os2.sTypoAscender, os2.sTypoDescender
        info.capHeight, info.xHeight = os2.sCapHeight, os2.sxHeight
        info.italicAngle = post.italicAngle
        info.openTypeOS2TypoAscender, info.openTypeOS2TypoDescender, info.openTypeOS2TypoLineGap = \
            os2.sTypoAscender, os2.sTypoDescender, os2.sTypoLineGap
        info.openTypeOS2WinAscent, info.openTypeOS2WinDescent = os2.usWinAscent, os2.usWinDescent
        info.openTypeHheaAscender, info.openTypeHheaDescender, info.openTypeHheaLineGap = \
            hhea.ascent, hhea.descent, hhea.lineGap
        info.openTypeOS2WeightClass = int(min(max(w, 1), 1000))
        ufo.lib['public.glyphOrder'] = order
        for n in order:
            write_glyph(ufo.layers.defaultLayer, n, (w, g), True)
        if (w, g) == DEFAULT:
            default_ufo = ufo
        s = SourceDescriptor()
        s.filename = f'{stem}-{master_name(w, g)}.ufo'
        s.familyName, s.styleName = family, info.styleName
        s.location = {'Weight': w, 'Grade': g}
        doc.addSource(s)
        ufo.save(out / s.filename, overwrite=True)
    assert default_ufo is not None
    for (w, g), names in sorted(sparse.items()):
        layer = default_ufo.newLayer(layer_name(w, g))
        for n in names:
            write_glyph(layer, n, (w, g), False)
        s = SourceDescriptor()
        s.filename = f'{stem}-{master_name(*DEFAULT)}.ufo'
        s.layerName = layer.name
        s.familyName, s.styleName = family, layer.name
        s.location = {'Weight': w, 'Grade': g}
        doc.addSource(s)
    default_ufo.save(out / f'{stem}-{master_name(*DEFAULT)}.ufo', overwrite=True)
    doc.write(out / f'{stem}.designspace')
    print(f'wrote {len(FULL)} masters and {len(sparse)} sparse layers to {out}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
