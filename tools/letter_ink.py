"""Colour by letter beside other faces: each letter's ink and its advance
against the n's (lowercase) or the H's (capitals), in Arris at a weight and
in reference fonts of that weight, and how far Arris stands from their mean.

A letter's colour is its ink over its advance. Ink over the mean says its
drawing is heavy or light; advance over the mean says it stands in too much
or too little room. Match the references to the weight by stem (their H's
stem over their cap height is printed: Arris's is 0.125 at Regular, 0.194 at
Bold, 0.243 at Black); a face far heavier or lighter skews every ratio.

usage: letter_ink.py WEIGHT FONT.ttf [FONT.ttf ...]
"""
from __future__ import annotations

import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

LOWER, CAPS = 'oabdegsuhmwvxzrckt', 'OEBRSDAMWNZKTUGJ'


def reference(path):
    from fontTools.ttLib import TTFont
    from refshape import shape
    from shapely.geometry import LineString
    font = TTFont(path)
    got = {c: shape(font, c) for c in 'nH' + LOWER + CAPS}
    H = got['H'][0]
    cap = H.bounds[3]
    stem = min(g.length for g in getattr(H.intersection(LineString([(-999, cap / 4), (9999, cap / 4)])), 'geoms', []))
    out = {}
    for base, chars in (('n', LOWER), ('H', CAPS)):
        for c in chars:
            out[c] = (got[c][0].area / got[base][0].area, got[c][1] / got[base][1])
    return out, stem / cap


def arris(weight):
    import arris.glyphs  # noqa: F401
    from arris.draw import REGISTRY
    from arris.font import place
    from arris.geom import rings_to_shapely
    from arris.instances import params
    cmap = {chr(s.unicode): n for n, s in REGISTRY.items() if s.unicode}
    p = params(weight)
    got = {}
    for c in 'nH' + LOWER + CAPS:
        rings, adv = place(cmap[c], p)
        got[c] = (rings_to_shapely(rings).area, adv)
    out = {}
    for base, chars in (('n', LOWER), ('H', CAPS)):
        for c in chars:
            out[c] = (got[c][0] / got[base][0], got[c][1] / got[base][1])
    return out, p.sv / p.cap


def main(argv):
    if len(argv) < 2:
        sys.exit(__doc__)
    weight, paths = int(argv[0]), argv[1:]
    mine, stem = arris(weight)
    refs = {}
    print(f'Arris {weight}: stem {stem:.3f} of the cap height')
    for path in paths:
        refs[Path(path).stem], s = reference(path)
        print(f'  {Path(path).stem}: stem {s:.3f}')
    rows = []
    for c in LOWER + CAPS:
        ink = mine[c][0] / st.mean(r[c][0] for r in refs.values()) - 1
        adv = mine[c][1] / st.mean(r[c][1] for r in refs.values()) - 1
        rows.append(((1 + ink) / (1 + adv) - 1, c, ink, adv))
    print('colour against the references (ink, advance):')
    for colour, c, ink, adv in sorted(rows):
        print(f'  {c}  {colour:+5.0%}   ink {ink:+4.0%}  advance {adv:+4.0%}' + ('   <--' if abs(colour) >= 0.08 else ''))


if __name__ == '__main__':
    main(sys.argv[1:])
