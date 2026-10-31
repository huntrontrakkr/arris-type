"""The variable fonts as Google Fonts takes them, from a release:
Arris[GRAD,wght].ttf and Arris-Italic[GRAD,wght].ttf.

    uv run python tools/google_fonts.py build/release/Arris-<version>.zip [out]

(out: build/google-fonts). The watch axis (WTCH) is not in Google Fonts'
axis registry, and an axis outside it does not work there, so it is left
out: the fonts are instanced at WTCH 0, the default, which keeps every
other variation (within a unit, the instancer's rounding). The instancer
runs without its optimisation: with it, it remaps the GDEF variation
store and leaves a sixth of the kerning's variation indices pointing past
it (34,215 of 192,842 in 1.005), which this refuses. STAT is rebuilt
without the watch axis, and name ID 25 (the PostScript prefix of the
fonts' instances) set as arris.vf sets it. Once the registry has the axis
as MECH (docs/google-fonts/axis-proposal.md), the fonts can carry it.
"""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

from fontTools.otlLib.builder import buildStatTable
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from arris.vf.assemble import name_variations, stat_axes

FONTS = {'Arris[GRAD,WTCH,wght].ttf': ('Arris[GRAD,wght].ttf', False),
         'Arris-Italic[GRAD,WTCH,wght].ttf': ('Arris-Italic[GRAD,wght].ttf', True)}


def dangling(font: TTFont) -> int:
    """Kerning variation indices that point past the GDEF variation store."""
    store = font['GDEF'].table.VarStore
    rows = [len(vd.Item) for vd in store.VarData]
    bad = 0
    for lookup in font['GPOS'].table.LookupList.Lookup:
        for st in lookup.SubTable:
            st = st.ExtSubTable if lookup.LookupType == 9 else st
            pairs = [pv for ps in getattr(st, 'PairSet', None) or [] for pv in ps.PairValueRecord]
            pairs += [c2 for c1 in getattr(st, 'Class1Record', None) or [] for c2 in c1.Class2Record]
            for pv in pairs:
                for v in (getattr(pv, 'Value1', None), getattr(pv, 'Value2', None)):
                    d = getattr(v, 'XAdvDevice', None)
                    if d is None or d.DeltaFormat != 0x8000 or d.StartSize == 0xFFFF:
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
            if bad := dangling(font):
                sys.exit(f'{dest}: {bad} kerning variation indices point past the variation store')
            path = out / 'fonts' / 'variable' / dest
            font.save(path)
            axes = ', '.join(f'{a.axisTag} {a.minValue:g}-{a.maxValue:g}' for a in font['fvar'].axes)
            print(f'{path.relative_to(out)}: {axes}; {path.stat().st_size / 1e6:.2f} MB')
    return 0


if __name__ == '__main__':
    sys.exit(main())
