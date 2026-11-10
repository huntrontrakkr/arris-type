"""Grade changes no advance, on a built variable font: at every weight and
watch the font has a master at, each glyph's advance as a shaper reads it
(hmtx and HVAR) is the same at the grade's ends as ungraded. Until 1.016
it was not for 42 glyphs upright and 52 italic (⁜ 140 units narrower at
Black, grade 100; ⇿ 85 wider at SemiBold, grade -100; the barred letters and
signs by 2 to 25).

usage: grade_advance_check.py FONT.ttf [FONT.ttf ...]   (exit 1 on a fault)
"""
from __future__ import annotations

import sys

from fontTools.ttLib import TTFont
from fontTools.varLib.models import normalizeLocation
from fontTools.varLib.varStore import VarStoreInstancer

WEIGHTS = (100, 200, 300, 400, 500, 600, 700, 750, 800, 850, 900)
TOLERANCE = 1.0     # units: the rounding of the variations' deltas


def check(path: str) -> list[str]:
    tt = TTFont(path)
    axes = {a.axisTag: (a.minValue, a.defaultValue, a.maxValue) for a in tt['fvar'].axes}
    if 'GRAD' not in axes:
        return []
    hvar, hmtx, order = tt['HVAR'].table, tt['hmtx'].metrics, tt.getGlyphOrder()
    names = {n: chr(c) for c, n in tt.getBestCmap().items()}

    def advances(loc: dict[str, float]) -> list[float]:
        inst = VarStoreInstancer(hvar.VarStore, tt['fvar'].axes, normalizeLocation(loc, axes))
        index = hvar.AdvWidthMap.mapping if hvar.AdvWidthMap else None
        return [hmtx[n][0] + inst[index[n] if index else i] for i, n in enumerate(order)]
    worst: dict[str, tuple[float, dict]] = {}
    for watch in ((0, 100) if 'WTCH' in axes else (0,)):
        for w in WEIGHTS:
            at = {'wght': w, **({'WTCH': watch} if watch else {})}
            plain = advances(at)
            for g in (axes['GRAD'][0], axes['GRAD'][2]):
                for n, a, b in zip(order, plain, advances({**at, 'GRAD': g})):
                    if abs(b - a) > TOLERANCE and abs(b - a) > abs(worst.get(n, (0.0, {}))[0]):
                        worst[n] = (b - a, {**at, 'GRAD': g})
    return [f'{names.get(n, "")} {n}: the grade moves its advance by {d:+.0f} at {loc}'
            for n, (d, loc) in sorted(worst.items(), key=lambda kv: -abs(kv[1][0]))]


def main() -> int:
    bad = 0
    for path in sys.argv[1:]:
        faults = check(path)
        bad += len(faults)
        print(f'{path}: {len(faults)} glyphs whose advance the grade moves')
        for f in faults[:60]:
            print('  ' + f)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
