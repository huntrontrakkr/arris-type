"""UFO sources for Google Fonts, written from a built variable font.

    python tools/ufo_sources.py FONT.ttf OUT_DIR [--features FILE.fea] [--only GLYPH ...]

(FILE.fea: the font's substitutions as arris.glyphs.features.fea() writes them.)

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
from fontTools.designspaceLib import (
    AxisDescriptor,
    AxisLabelDescriptor,
    DesignSpaceDocument,
    InstanceDescriptor,
    RuleDescriptor,
    SourceDescriptor,
)
from fontTools.ttLib import TTFont
from fontTools.varLib.models import VariationModel, normalizeLocation

WEIGHTS = (100, 200, 300, 400, 500, 600, 700, 750, 800, 850, 900)
GRADED = (100, 400, 600, 800, 900)
FULL = [(w, 0) for w in WEIGHTS] + [(w, g) for w in GRADED for g in (-100, 100)]
DEFAULT = (400, 0)
NAMES = {100: 'Thin', 200: 'ExtraLight', 300: 'Light', 400: 'Regular', 500: 'Medium', 600: 'SemiBold', 700: 'Bold',
         750: 'W750', 800: 'ExtraBold', 850: 'W850', 900: 'Black'}
LETTERS = 'ABCDEFGHIJKLMNOP'
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


def layout_reader(tt: TTFont, loc: dict[str, float]):
    """value(base, device): a GPOS value at a normalised place."""
    from fontTools.varLib.varStore import VarStoreInstancer
    inst = VarStoreInstancer(tt['GDEF'].table.VarStore, tt['fvar'].axes, loc)

    def value(base, device) -> int:
        if device is not None and device.DeltaFormat == 0x8000 and (device.StartSize, device.EndSize) != (0xFFFF, 0xFFFF):
            return round((base or 0) + inst[(device.StartSize << 16) + device.EndSize])
        return base or 0
    return value


def _anchor(a, value) -> tuple[int, int]:
    return (value(a.XCoordinate, getattr(a, 'XDeviceTable', None)), value(a.YCoordinate, getattr(a, 'YDeviceTable', None)))


KNOWN_MARKS = {'gravecomb': 'top', 'dotbelowcomb': 'bottom', 'uni0328': 'ogonek', 'uni031B': 'horn'}


def anchors(tt: TTFont, loc: dict[str, float]) -> dict[str, list[tuple[str, int, int]]]:
    """Each glyph's anchors at a place, read from the font's mark
    positioning: a mark's '_top', a letter's 'top' (and a mark's own
    'top', for the mark that stacks on it). A class is named by a mark it
    is known by (KNOWN_MARKS: the grave's is 'top'), else by a letter
    ('markE'; not a number, which ufo2ft reads at a name's end as a
    ligature's component)."""
    value = layout_reader(tt, loc)
    out: dict[str, dict[str, tuple[int, int]]] = {}
    for lookup in tt['GPOS'].table.LookupList.Lookup:
        for st in lookup.SubTable:
            st = st.ExtSubTable if lookup.LookupType == 9 else st
            kind = type(st).__name__
            if kind == 'MarkBasePos':
                marks, bases = (st.MarkCoverage, st.MarkArray.MarkRecord), \
                    (st.BaseCoverage, [r.BaseAnchor for r in st.BaseArray.BaseRecord])
            elif kind == 'MarkMarkPos':
                marks, bases = (st.Mark1Coverage, st.Mark1Array.MarkRecord), \
                    (st.Mark2Coverage, [r.Mark2Anchor for r in st.Mark2Array.Mark2Record])
            else:
                continue
            names = {rec.Class: KNOWN_MARKS[g] for g, rec in zip(marks[0].glyphs, marks[1]) if g in KNOWN_MARKS}
            for g, rec in zip(marks[0].glyphs, marks[1]):
                name, at = '_' + names.get(rec.Class, f'mark{LETTERS[rec.Class]}'), _anchor(rec.MarkAnchor, value)
                assert out.setdefault(g, {}).setdefault(name, at) == at, (g, name)   # one anchor, both lookups
            for g, row in zip(bases[0].glyphs, bases[1]):
                for c, a in enumerate(row):
                    if a is not None:
                        out.setdefault(g, {})[names.get(c, f'mark{LETTERS[c]}')] = _anchor(a, value)
    return {g: [(n, x, y) for n, (x, y) in d.items()] for g, d in out.items()}


def kerning(tt: TTFont, loc: dict[str, float]) -> dict[tuple[str, str], int]:
    """The font's pair kerning at a place: flat pairs, glyph to glyph."""
    value = layout_reader(tt, loc)
    pairs: dict[tuple[str, str], int] = {}
    for lookup in tt['GPOS'].table.LookupList.Lookup:
        for st in lookup.SubTable:
            st = st.ExtSubTable if lookup.LookupType == 9 else st
            if type(st).__name__ != 'PairPos':
                continue
            assert st.Format == 1, 'the font kerns glyph to glyph'
            for left, ps in zip(st.Coverage.glyphs, st.PairSet):
                for pv in ps.PairValueRecord:
                    v = pv.Value1
                    pairs.setdefault((left, pv.SecondGlyph), value(v.XAdvance, getattr(v, 'XAdvDevice', None)))
    return pairs


def grouped(by_master: list[dict[tuple[str, str], int]]) -> tuple[dict[str, list[str]], list[dict[tuple[str, str], int]]]:
    """The masters' flat kerning as groups and group pairs, nothing lost:
    glyphs that kern alike against every glyph in every master (an accented
    letter and its base, mostly) share a group."""
    every = sorted(set().union(*by_master))
    row: dict[str, list] = {}
    col: dict[str, list] = {}
    for a, b in every:
        vals = tuple(m.get((a, b), 0) for m in by_master)
        row.setdefault(a, []).append((b, vals))
        col.setdefault(b, []).append((a, vals))
    groups: dict[str, list[str]] = {}

    def classes(side: dict[str, list], prefix: str) -> dict[str, str]:
        same: dict[tuple, list[str]] = {}
        for g, items in side.items():
            same.setdefault(tuple(items), []).append(g)
        name = {}
        for members in same.values():
            if len(members) > 1:
                groups[f'{prefix}{members[0]}'] = members
            for g in members:
                name[g] = f'{prefix}{members[0]}' if len(members) > 1 else g
        return name
    left = classes(row, 'public.kern1.')
    # the right side grouped on what is left of the pairs once the left is
    col2: dict[str, list] = {}
    for a, b in every:
        if left[a] in (a, f'public.kern1.{a}'):
            col2.setdefault(b, []).append((left[a], tuple(m.get((a, b), 0) for m in by_master)))
    right = classes(col2, 'public.kern2.')
    out = []
    for m in by_master:
        d: dict[tuple[str, str], int] = {}
        for (a, b), v in m.items():
            d[left[a], right.get(b, b)] = v
        out.append(d)
    return groups, out


def rules(tt: TTFont, axes) -> list[tuple[list[dict], dict[str, str]]]:
    """The font's form switches (GSUB feature variations): where, and
    which glyphs swap."""
    fv = getattr(tt['GSUB'].table, 'FeatureVariations', None)
    if fv is None:
        return []
    tags = [a.axisTag for a in tt['fvar'].axes]
    names = {'wght': 'Weight', 'GRAD': 'Grade'}
    lookups = tt['GSUB'].table.LookupList.Lookup
    feats = tt['GSUB'].table.FeatureList.FeatureRecord

    def user(tag, v):
        lo, df, hi = axes[tag]
        return round(df + v * ((df - lo) if v < 0 else (hi - df)), 1)
    out = []
    for rec in fv.FeatureVariationRecord:
        cond = [{'name': names[tags[c.AxisIndex]], 'minimum': user(tags[c.AxisIndex], c.FilterRangeMinValue),
                 'maximum': user(tags[c.AxisIndex], c.FilterRangeMaxValue)} for c in rec.ConditionSet.ConditionTable]
        subs: dict[str, str] = {}
        for sr in rec.FeatureTableSubstitution.SubstitutionRecord:
            before = set(feats[sr.FeatureIndex].Feature.LookupListIndex)
            for i in sr.Feature.LookupListIndex:
                if i not in before:
                    for st in lookups[i].SubTable:
                        st = st.ExtSubTable if lookups[i].LookupType == 7 else st
                        subs.update(st.mapping)
        out.append((cond, subs))
    return out



def main() -> int:
    args = sys.argv[1:]
    only = None
    if '--only' in args:
        i = args.index('--only')
        only, args = set(args[i + 1:]), args[:i]
    fea_path = None
    if '--features' in args:
        i = args.index('--features')
        fea_path = args[i + 1]
        del args[i:i + 2]
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

    from fontTools.varLib.varStore import VarStoreInstancer
    hvar = tt['HVAR'].table
    adv_at: dict[tuple[float, float], VarStoreInstancer] = {}

    def advance(name, place):
        """The glyph's advance at a place as a shaper reads it: hmtx and HVAR."""
        inst = adv_at.get(place)
        if inst is None:
            inst = adv_at[place] = VarStoreInstancer(hvar.VarStore, tt['fvar'].axes, norm(place))
        idx = hvar.AdvWidthMap.mapping[name] if hvar.AdvWidthMap else tt.getGlyphID(name)
        return round(hmtx[name][0] + inst[idx])

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

    def write_glyph(layer, name, place, anchors_=None):
        g = layer.newGlyph(name)
        coords = at(name, place)
        tg = glyf[name]
        g.width = advance(name, place)
        if anchors_ is not None:
            if name in cmap:
                g.unicodes = sorted(cmap[name])
            for an, x, y in anchors_.get(name, ()):
                g.appendAnchor({'name': an, 'x': x, 'y': y})
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
    weight_names = {100: 'Thin', 200: 'ExtraLight', 300: 'Light', 400: 'Regular', 500: 'Medium', 600: 'SemiBold',
                    700: 'Bold', 800: 'ExtraBold', 900: 'Black'}
    for tag, name in (('wght', 'Weight'), ('GRAD', 'Grade')):
        a = AxisDescriptor()
        a.tag, a.name = tag, name
        a.minimum, a.default, a.maximum = axes[tag]
        if tag == 'wght':
            a.axisLabels = [AxisLabelDescriptor(name=nm, userValue=w, elidable=w == 400,
                                                linkedUserValue=700 if w == 400 else None)
                            for w, nm in weight_names.items()]
        else:
            a.axisLabels = [AxisLabelDescriptor(name='Normal', userValue=0, elidable=True)]
        doc.addAxis(a)
    # the form switches compile under rlig, as in the font (arris.vf.assemble)
    doc.lib['com.github.fonttools.varLib.featureVarsFeatureTag'] = 'rlig'
    for i, (cond, subs) in enumerate(rules(tt, axes)):
        r = RuleDescriptor()
        r.name = f'second forms {i + 1}'
        r.conditionSets = [cond]
        r.subs = sorted(subs.items())
        doc.addRule(r)
    os2, hhea, head, post, name_t = tt['OS/2'], tt['hhea'], tt['head'], tt['post'], tt['name']
    gdef = tt['GDEF'].table.GlyphClassDef.classDefs
    categories = {n: {1: 'base', 2: 'ligature', 3: 'mark', 4: 'component'}[gdef[n]] for n in order if n in gdef}
    features = Path(fea_path).read_text() if fea_path else ''
    kern_by = [kerning(tt, norm((w, 0))) for w in WEIGHTS]
    groups, kern_by = grouped(kern_by)
    kern_at = dict(zip(WEIGHTS, kern_by))

    def nm(i):
        return name_t.getDebugName(i)
    version = nm(5).split(';')[0].replace('Version ', '')
    default_ufo = None
    for w, g in FULL:
        ufo = ufoLib2.Font()
        info = ufo.info
        info.familyName, info.styleName = family, master_name(w, g) + (' Italic' if italic else '')
        info.unitsPerEm = head.unitsPerEm
        info.versionMajor, info.versionMinor = int(version.split('.')[0]), int(version.split('.')[1])
        info.copyright, info.openTypeNameLicense, info.openTypeNameLicenseURL = nm(0), nm(13), nm(14)
        info.openTypeNameDesigner, info.openTypeNameDesignerURL = nm(9), nm(12)
        info.openTypeNameManufacturer, info.openTypeNameManufacturerURL = nm(8), nm(11)
        info.openTypeNameDescription = nm(10)
        info.openTypeOS2VendorID = os2.achVendID
        info.openTypeOS2Type = []
        info.openTypeOS2Selection = [7]         # the line metrics are the typographic ones
        info.ascender, info.descender = os2.sTypoAscender, os2.sTypoDescender
        info.capHeight, info.xHeight = os2.sCapHeight, os2.sxHeight
        info.italicAngle = post.italicAngle
        info.postscriptUnderlinePosition, info.postscriptUnderlineThickness = post.underlinePosition, post.underlineThickness
        info.openTypeOS2TypoAscender, info.openTypeOS2TypoDescender, info.openTypeOS2TypoLineGap = \
            os2.sTypoAscender, os2.sTypoDescender, os2.sTypoLineGap
        info.openTypeOS2WinAscent, info.openTypeOS2WinDescent = os2.usWinAscent, os2.usWinDescent
        info.openTypeHheaAscender, info.openTypeHheaDescender, info.openTypeHheaLineGap = \
            hhea.ascent, hhea.descent, hhea.lineGap
        info.openTypeHheaCaretSlopeRise, info.openTypeHheaCaretSlopeRun = hhea.caretSlopeRise, hhea.caretSlopeRun
        info.openTypeOS2WeightClass = int(w)
        ufo.lib['public.glyphOrder'] = order
        ufo.lib['public.openTypeCategories'] = categories
        ufo.lib['com.github.googlei18n.ufo2ft.useProductionNames'] = False   # the glyphs' names are the font's
        ufo.features.text = features
        ufo.groups.update(groups)
        ufo.kerning.update({pr: v for pr, v in kern_at[w].items() if v})
        anchors_ = anchors(tt, norm((w, g)))
        for n in order:
            write_glyph(ufo.layers.defaultLayer, n, (w, g), anchors_)
        if (w, g) == DEFAULT:
            default_ufo = ufo
        s = SourceDescriptor()
        s.filename = f'{stem}-{master_name(w, g)}.ufo'
        s.familyName, s.styleName = family, info.styleName
        s.location = {'Weight': w, 'Grade': g}
        doc.addSource(s)
        ufo.save(out / s.filename, overwrite=True)
    for w, wn in weight_names.items():
        inst = InstanceDescriptor()
        inst.familyName = family
        inst.styleName = (wn + ' Italic' if italic and w != 400 else 'Italic' if italic else wn)
        inst.location = {'Weight': w, 'Grade': 0}
        doc.addInstance(inst)
    assert default_ufo is not None
    for (w, g), names in sorted(sparse.items()):
        layer = default_ufo.newLayer(layer_name(w, g))
        for n in names:
            write_glyph(layer, n, (w, g))
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
