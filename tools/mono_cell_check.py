"""Arris Mono's cell, both ways, on the built fonts, upright and italic: no
glyph's ink reaches its cell's edge (x 0 or its advance: a terminal cuts
there, or the next character collides), in the italic as slanted, and none
leaves the line box (the hhea/typo ascent and descent: a terminal's cell,
which clips what passes it). Left out are only the glyphs made to meet
their neighbours: box drawing, blocks, shades, Braille, the Powerline
separators, legacy computing, the maths and bracket pieces, the corner
triangles, and the runs and ligatures (one gesture over several cells).
The horizontal brackets ⏜–⏡ and the Powerline icons stand alone and are
checked like any glyph.

usage: mono_cell_check.py FONT.ttf [FONT.ttf ...]   (exit 1 on a fault)
"""
from __future__ import annotations

import sys

from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

MEET = [(0x2500, 0x259F), (0x2800, 0x28FF), (0xE0B0, 0xE0D7), (0x1FB00, 0x1FBFF), (0x239B, 0x23B3),
        (0x23B7, 0x23BD), (0x23D0, 0x23D0), (0x25E2, 0x25E5), (0x2320, 0x2321)]
# What the owner accepted (2026-11-06): the line stays and the accents give
# way, but Ǻ's ring and acute, closed up and shrunk as far as they go, still
# stand a little over the line at the heaviest weights
OVER_LINE_OK = {0x01FA, 0x01FB}
TOLERANCE = 0.5


def _meets(name: str, cp: int | None) -> bool:
    if cp is not None and any(a <= cp <= b for a, b in MEET):
        return True
    return '.seq' in name or '.liga' in name or ('_' in name and not name.startswith('uni'))


def check(path: str) -> list[str]:
    tt = TTFont(path)
    gs = tt.getGlyphSet()
    hmtx = tt['hmtx']
    asc, desc = tt['hhea'].ascent, tt['hhea'].descent
    names = {n: cp for cp, n in sorted(tt.getBestCmap().items(), reverse=True)}
    faults = []
    for name in tt.getGlyphOrder():
        cp = names.get(name)
        adv = hmtx[name][0]
        if adv == 0 or _meets(name, cp):
            continue
        pen = BoundsPen(gs)
        gs[name].draw(pen)
        if pen.bounds is None:
            continue
        x0, y0, x1, y1 = pen.bounds
        label = f'{chr(cp)} {name}' if cp is not None else name
        if x0 < TOLERANCE or x1 > adv - TOLERANCE:
            faults.append(f'{label}: ink {x0:.0f}..{x1:.0f} reaches the cell (0..{adv})')
        if (y1 > asc + TOLERANCE and cp not in OVER_LINE_OK) or y0 < desc - TOLERANCE:
            faults.append(f'{label}: ink {y0:.0f}..{y1:.0f} leaves the line box ({desc}..{asc})')
    return faults


def main(argv: list[str]) -> int:
    bad = 0
    for path in argv:
        faults = check(path)
        print(f'{path}: {len(faults)} fault{"" if len(faults) == 1 else "s"}')
        for f in faults[:60]:
            print('  ' + f)
        bad += bool(faults)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
