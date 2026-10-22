"""Proof sheet of pixel masters: the pixels, and the Chamfer rule's outline."""
import sys

import cairosvg

from arris import heritage
from arris.masters import CAPS, LOWER

S = 16  # px per module


def sheet(table, keys, path, per_row=13):
    rows = [keys[i:i + per_row] for i in range(0, len(keys), per_row)]
    H = max(len(table[k]) for k in keys) + 2
    width = max(sum(len(table[k][0]) + 2 for k in r) for r in rows) * S + 2 * S
    height = len(rows) * (2 * H + 2) * S
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">'
           '<rect width="100%" height="100%" fill="white"/>']
    for ri, r in enumerate(rows):
        y0 = ri * (2 * H + 2) * S + S
        x = S
        for k in r:
            m = table[k]
            w = len(m[0])
            for yy, row in enumerate(m):        # pixels
                for xx, ch in enumerate(row):
                    fill = '#222' if ch == '#' else '#eee'
                    out.append(f'<rect x="{x + xx * S}" y="{y0 + yy * S}" width="{S - 1}" height="{S - 1}" fill="{fill}"/>')
            g = heritage.trace(m)                # Chamfer rule, y up
            ty = y0 + (H + 1) * S
            d = []
            for poly in getattr(g, 'geoms', [g]):
                for ring in [poly.exterior, *poly.interiors]:
                    d.append('M' + 'L'.join(f'{x + px * S:.1f},{ty + (len(m) - py) * S:.1f}' for px, py in ring.coords) + 'Z')
            out.append(f'<path fill="black" fill-rule="evenodd" d="{" ".join(d)}"/>')
            x += (w + 2) * S
    out.append('</svg>')
    cairosvg.svg2png(bytestring=''.join(out).encode(), write_to=path)


if __name__ == '__main__':
    which = sys.argv[1]
    table = {'caps': CAPS, 'lower': LOWER}[which]
    sheet(table, sorted(table), sys.argv[2])
