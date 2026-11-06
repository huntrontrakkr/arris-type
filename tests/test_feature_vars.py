"""The form switches (vf.forms, vf.assemble) compile under rlig, and
HarfBuzz swaps the second form in either side of the threshold: a two-master
font built as the variable font is (a designspace rule, the lib key)."""
from __future__ import annotations

import uharfbuzz as hb
from fontTools.designspaceLib import AxisDescriptor, DesignSpaceDocument, RuleDescriptor, SourceDescriptor
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.varLib import build as varlib_build

from arris.vf.assemble import FEATURE_VARS_TAG, FEATURE_VARS_TAG_KEY


def _box(w):
    pen = TTGlyphPen(None)
    pen.moveTo((0, 0))
    pen.lineTo((0, 700))
    pen.lineTo((w, 700))
    pen.lineTo((w, 0))
    pen.closePath()
    return pen.glyph()


def _master(path, w):
    fb = FontBuilder(1000, isTTF=True)
    order = ['.notdef', 'dollar', 'dollar.stem']
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap({ord('$'): 'dollar'})
    fb.setupGlyf({'.notdef': _box(100), 'dollar': _box(w), 'dollar.stem': _box(w + 10)})
    fb.setupHorizontalMetrics({n: (600, 0) for n in order})
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    fb.setupNameTable({'familyName': 'T', 'styleName': 'R'})
    fb.setupOS2()
    fb.setupPost()
    fb.save(path)


def _shape(font_bytes, wght):
    face = hb.Face(font_bytes)
    font = hb.Font(face)
    font.set_variations({'wght': wght})
    buf = hb.Buffer()
    buf.add_str('$')
    buf.guess_segment_properties()
    hb.shape(font, buf)
    return buf.glyph_infos[0].codepoint


def test_switch_under_rlig(tmp_path):
    _master(str(tmp_path / 'a.ttf'), 100)
    _master(str(tmp_path / 'b.ttf'), 300)
    doc = DesignSpaceDocument()
    ax = AxisDescriptor()
    ax.tag, ax.name, ax.minimum, ax.default, ax.maximum = 'wght', 'Weight', 100, 400, 900
    doc.addAxis(ax)
    for path, w in (('a.ttf', 400), ('b.ttf', 900)):            # the default master, and the heavy one
        src = SourceDescriptor()
        src.path, src.location = str(tmp_path / path), {'Weight': w}
        doc.addSource(src)
    doc.lib[FEATURE_VARS_TAG_KEY] = FEATURE_VARS_TAG
    rule = RuleDescriptor()
    rule.name = 'dollar second form'
    rule.conditionSets = [[{'name': 'Weight', 'minimum': 650, 'maximum': 900}]]
    rule.subs = [('dollar', 'dollar.stem')]
    doc.addRule(rule)
    vf, _, _ = varlib_build(doc)
    fv = vf['GSUB'].table.FeatureVariations
    tags = {vf['GSUB'].table.FeatureList.FeatureRecord[r.FeatureIndex].FeatureTag
            for rec in fv.FeatureVariationRecord for r in rec.FeatureTableSubstitution.SubstitutionRecord}
    assert tags == {'rlig'}
    path = tmp_path / 'vf.ttf'
    vf.save(path)
    data = path.read_bytes()
    order = vf.getGlyphOrder()
    assert order[_shape(data, 649)] == 'dollar'
    assert order[_shape(data, 651)] == 'dollar.stem'
