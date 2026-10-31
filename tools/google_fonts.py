"""The variable fonts as Google Fonts takes them, from a release:
Arris[GRAD,wght].ttf and Arris-Italic[GRAD,wght].ttf.

    uv run python tools/google_fonts.py build/release/Arris-<version>.zip [out]

(out: build/google-fonts). The watch axis (WTCH) is not in Google Fonts'
axis registry, and an axis outside it does not work there, so it is left
out: the fonts are instanced at WTCH 0, the default, which keeps every
other variation (within a unit, the instancer's rounding). Kerning that
varied only along the watch axis is constant after that, and the instancer
leaves each such pair a device that points at no variation (0xFFFF,
0xFFFF): valid, useless, and fatal to fontbakery 1.1.0's
varfont/duplexed_axis_reflow, which indexes the variation store by it. Those
devices are removed (34,215 of 1.005's 192,842; the fonts are no smaller
for it, the identical tables having been shared), and the build refuses a
font with any kerning index pointing past the store. The instancer's own
optimisation of the outline deltas is left off: it would save 3% of the
size and move points by up to half a unit. STAT is rebuilt without the
watch axis, and name ID 25 (the PostScript prefix of the fonts' instances)
set as arris.vf sets it. Once the registry has the axis as MECH
(docs/google-fonts/axis-proposal.md), the fonts can carry it.
"""
from __future__ import annotations

import sys
import zipfile
from collections.abc import Iterator
from pathlib import Path

from fontTools.otlLib.builder import buildStatTable
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from arris.vf.assemble import name_variations, stat_axes

FONTS = {'Arris[GRAD,WTCH,wght].ttf': ('Arris[GRAD,wght].ttf', False),
         'Arris-Italic[GRAD,WTCH,wght].ttf': ('Arris-Italic[GRAD,wght].ttf', True)}
DEVICES = ('XPlaDevice', 'YPlaDevice', 'XAdvDevice', 'YAdvDevice')
VARIATION_INDEX = 0x8000     # a Device table's DeltaFormat when it indexes a variation store
NO_VARIATION = 0xFFFF        # the index that points at no variation


def pair_values(font: TTFont) -> Iterator:
    """Every value record of the font's pair positioning."""
    for lookup in font['GPOS'].table.LookupList.Lookup:
        for st in lookup.SubTable:
            st = st.ExtSubTable if lookup.LookupType == 9 else st
            if getattr(st, 'PairSet', None):
                records = (pv for ps in st.PairSet for pv in ps.PairValueRecord)
            elif getattr(st, 'Class1Record', None):
                records = (c2 for c1 in st.Class1Record for c2 in c1.Class2Record)
            else:
                continue
            for record in records:
                for value in (getattr(record, 'Value1', None), getattr(record, 'Value2', None)):
                    if value is not None:
                        yield value


def strip_no_variation(font: TTFont) -> int:
    """Remove the kerning's devices that point at no variation; how many."""
    n = 0
    for value in pair_values(font):
        for name in DEVICES:
            d = getattr(value, name, None)
            if d is not None and d.DeltaFormat == VARIATION_INDEX and d.StartSize == NO_VARIATION:
                setattr(value, name, None)
                n += 1
    return n


def dangling(font: TTFont) -> int:
    """Kerning variation indices that point past the GDEF variation store."""
    rows = [len(vd.Item) for vd in font['GDEF'].table.VarStore.VarData]
    bad = 0
    for value in pair_values(font):
        for name in DEVICES:
            d = getattr(value, name, None)
            if d is None or d.DeltaFormat != VARIATION_INDEX:
                continue
            if d.StartSize >= len(rows) or d.EndSize >= rows[d.StartSize]:
                bad += 1
    return bad


def main() -> int:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / 'build' / 'google-fonts'
    (out / 'fonts' / 'variable').mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(src) as z:
        for name, (dest, italic) in FONTS.items():
            member = next(n for n in z.namelist() if n.endswith(f'/variable/{name}'))
            tmp = out / name
            tmp.write_bytes(z.read(member))
            font = instantiateVariableFont(TTFont(tmp), {'WTCH': 0}, optimize=False, updateFontNames=False)
            tmp.unlink()
            del font['STAT']
            buildStatTable(font, stat_axes(italic, watch=False))
            name_variations(font, italic)
            stripped = strip_no_variation(font)
            if bad := dangling(font):
                sys.exit(f'{dest}: {bad} kerning variation indices point past the variation store')
            path = out / 'fonts' / 'variable' / dest
            font.save(path)
            axes = ', '.join(f'{a.axisTag} {a.minValue:g}-{a.maxValue:g}' for a in font['fvar'].axes)
            print(f'{path.relative_to(out)}: {axes}; {stripped} constant kerning devices removed;'
                  f' {path.stat().st_size / 1e6:.2f} MB')
    return 0


if __name__ == '__main__':
    sys.exit(main())
