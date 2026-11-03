"""How a variable font pairs a glyph's points between two places: each point
at both, joined, the long joins drawn heavy, the outline halfway between
them under it. A wedge between masters is a point paired with one on
another feature (a stand-in for a point one drawing lacks, copied from a
corner a feature away), and shows here as a long join across the white.

    uv run python tools/vf_pairs.py FONT.ttf GLYPH OUT.png wght/GRAD/WTCH wght/GRAD/WTCH [--long 60]

(blue: the first place, red: the second; orange: a join longer than --long
units). Prints the longest joins.
"""
from __future__ import annotations

import math
import sys

from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from PIL import Image, ImageDraw, ImageFont


def _points(font: str, name: str, loc: tuple[float, ...]):
    inst = instantiateVariableFont(TTFont(font), dict(zip(('wght', 'GRAD', 'WTCH'), loc)))
    coords, ends, _ = inst['glyf'][name].getCoordinates(inst['glyf'])
    return list(coords), list(ends)


def _rings(pts, ends):
    out, start = [], 0
    for e in ends:
        out.append(pts[start:e + 1])
        start = e + 1
    return out


def main(argv: list[str]) -> int:
    args = list(argv)
    long = 60.0
    if '--long' in args:
        i = args.index('--long')
        long = float(args[i + 1])
        del args[i:i + 2]
    font, name, out, a, b = args[:5]
    A, B = (tuple(float(v) for v in s.split('/')) for s in (a, b))
    pa, ends = _points(font, name, A)
    pb, _ = _points(font, name, B)
    pm, _ = _points(font, name, tuple((x + y) / 2 for x, y in zip(A, B)))
    xs = [q[0] for q in pa + pb]
    ys = [q[1] for q in pa + pb]
    x0, y0, x1, y1 = min(xs) - 30, min(ys) - 30, max(xs) + 30, max(ys) + 30
    s = 1000 / (y1 - y0)
    im = Image.new('RGB', (int((x1 - x0) * s), 1000), 'white')
    d = ImageDraw.Draw(im)
    font_ = ImageFont.load_default()

    def at(q):
        return ((q[0] - x0) * s, (y1 - q[1]) * s)
    for r in _rings(pm, ends):
        d.polygon([at(q) for q in r], outline=(150, 150, 150))
    for rings, col in ((_rings(pa, ends), (40, 90, 220)), (_rings(pb, ends), (220, 50, 50))):
        for r in rings:
            for q0, q1 in zip(r, r[1:] + r[:1]):
                d.line([at(q0), at(q1)], fill=col, width=2)
    joins = []
    for i, (qa, qb) in enumerate(zip(pa, pb)):
        length = math.dist(qa, qb)
        joins.append((length, i, qa, qb))
        d.line([at(qa), at(qb)], fill=(255, 140, 0) if length > long else (0, 160, 0), width=3 if length > long else 1)
        for q, col in ((qa, (40, 90, 220)), (qb, (220, 50, 50))):
            x, y = at(q)
            d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=col)
        x, y = at(qa)
        d.text((x + 4, y - 12), str(i), fill=(40, 90, 220), font=font_)
    im.save(out)
    joins.sort(reverse=True)
    print(f'{sum(1 for j in joins if j[0] > long)} of {len(joins)} points joined over {long:g} units')
    for length, i, qa, qb in joins[:12]:
        print(f'  point {i}: {length:.0f} units, {tuple(qa)} -> {tuple(qb)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
