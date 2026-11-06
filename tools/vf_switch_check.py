"""The form switches of a built variable font (vf.forms, vf.assemble): they
sit under rlig, and HarfBuzz swaps each second form in one unit of weight
past its threshold and not one unit before, in every band of the other axes.

usage: vf_switch_check.py FONT.ttf [FONT.ttf ...]   (exit 1 on a fault)
"""
from __future__ import annotations

import sys

import uharfbuzz as hb
from fontTools.ttLib import TTFont

from arris.vf.assemble import FEATURE_VARS_TAG


def _denorm(axis, v):
    """A normalized coordinate in user units (no avar: the default mapping)."""
    lo, df, hi = axis.minValue, axis.defaultValue, axis.maxValue
    return df + v * ((hi - df) if v >= 0 else (df - lo))


def check(path: str) -> list[str]:
    tt = TTFont(path)
    axes = tt['fvar'].axes
    order = tt.getGlyphOrder()
    cmap = {g: c for c, g in tt.getBestCmap().items()}
    gsub = tt['GSUB'].table
    fv = getattr(gsub, 'FeatureVariations', None)
    faults = []
    if fv is None:
        return ['no feature variations']
    if 'avar' in tt:
        faults.append('an avar table: thresholds here are read through the default mapping')
    data = open(path, 'rb').read()
    face = hb.Face(data)
    font = hb.Font(face)

    def shaped(ch, loc):
        font.set_variations(loc)
        buf = hb.Buffer()
        buf.add_str(ch)
        buf.guess_segment_properties()
        hb.shape(font, buf)
        return order[buf.glyph_infos[0].codepoint]
    ax = {x.axisTag: x for x in axes}

    def norm(axis, v):
        lo, df, hi = axis.minValue, axis.defaultValue, axis.maxValue
        return (v - df) / (hi - df) if v >= df else (v - df) / (df - lo)

    def swapped(glyph, loc):
        """What the table says: the first record whose conditions hold swaps it."""
        for rec in fv.FeatureVariationRecord:
            if all(c.FilterRangeMinValue - 1e-4 <= norm(axes[c.AxisIndex], loc[axes[c.AxisIndex].axisTag])
                   <= c.FilterRangeMaxValue + 1e-4 for c in rec.ConditionSet.ConditionTable):
                for sr in rec.FeatureTableSubstitution.SubstitutionRecord:
                    for li in sr.Feature.LookupListIndex:
                        for st in gsub.LookupList.Lookup[li].SubTable:
                            if glyph in getattr(st, 'mapping', {}):
                                return st.mapping[glyph]
                return glyph
        return glyph
    n = 0
    for rec in fv.FeatureVariationRecord:
        ranges = {axes[c.AxisIndex].axisTag: (c.FilterRangeMinValue, c.FilterRangeMaxValue)
                  for c in rec.ConditionSet.ConditionTable}
        for sr in rec.FeatureTableSubstitution.SubstitutionRecord:
            tag = gsub.FeatureList.FeatureRecord[sr.FeatureIndex].FeatureTag
            if tag != FEATURE_VARS_TAG:
                faults.append(f'a switch under {tag}, not {FEATURE_VARS_TAG}')
            for li in sr.Feature.LookupListIndex:
                for st in gsub.LookupList.Lookup[li].SubTable:
                    for a, b in getattr(st, 'mapping', {}).items():
                        if a not in cmap:
                            continue
                        mid = {t: _denorm(ax[t], (lo + hi) / 2) for t, (lo, hi) in ranges.items() if t != 'wght'}
                        mid = {**{t: x.defaultValue for t, x in ax.items()}, **mid}
                        w0 = _denorm(ax['wght'], ranges['wght'][0])
                        for w in (w0 - 1, w0 + 1):
                            if not (ax['wght'].minValue <= w <= ax['wght'].maxValue):
                                continue
                            loc = {**mid, 'wght': w}
                            want = swapped(a, loc)
                            got = shaped(chr(cmap[a]), loc)
                            n += 1
                            if got != want:
                                faults.append(f'{a} at {loc}: {got}, the table says {want}')
                        if swapped(a, {**mid, 'wght': w0 + 1}) != b:
                            faults.append(f'{a} at {mid}: not swapped just past its threshold {w0:.0f}')
    print(f'{path}: {n} shapes, {len(faults)} faults')
    return faults


if __name__ == '__main__':
    bad = []
    for p in sys.argv[1:]:
        bad += check(p)
    for f in bad:
        print(' ', f)
    sys.exit(1 if bad else 0)
