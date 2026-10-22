"""Overlay: a set's pixel-master traces (grey) under the constructions at the
watch's weight (red), with the area that differs per glyph."""
import sys

import cairosvg
import shapely

import arris.glyphs.figures  # noqa: F401
import arris.glyphs.caps  # noqa: F401
import arris.glyphs.lower  # noqa: F401
from arris import heritage
from arris.draw import draw
from arris.geom import rings_to_shapely
from arris.masters import CAPS, LOWER
from arris.params import HERITAGE


def master(table, ch):
    m = table[ch]
    base = 13 if table is LOWER else 12
    g = heritage.trace(m)
    return shapely.affinity.translate(g, 0, -(len(m) - base))


def overlay(table, names, path, S=24, per_row=9):
    rows = [names[i:i + per_row] for i in range(0, len(names), per_row)]
    Hh = 17 if table is LOWER else 13
    width = (max(sum(len(table[k][0]) + 2 for k in r) for r in rows) + 2) * S
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{len(rows) * (Hh + 2) * S}">'
           '<rect width="100%" height="100%" fill="white"/>']
    report = []
    for ri, r in enumerate(rows):
        x = S
        base_y = ri * (Hh + 2) * S + (Hh - (3 if table is LOWER else 0)) * S + S
        for k in r:
            old = master(table, k)
            new = rings_to_shapely(draw(k, HERITAGE).rings())
            report.append((k, new.symmetric_difference(old).area, old.area))

            def path_of(geom):
                d = []
                for poly in getattr(geom, 'geoms', [geom]):
                    for ring in [poly.exterior, *poly.interiors]:
                        d.append('M' + 'L'.join(f'{x + px * S:.1f},{base_y - py * S:.1f}' for px, py in ring.coords) + 'Z')
                return ' '.join(d)
            out.append(f'<path fill="#bbb" fill-rule="evenodd" d="{path_of(old)}"/>')
            out.append(f'<path fill="none" stroke="red" stroke-width="1.5" d="{path_of(new)}"/>')
            x += (len(table[k][0]) + 2) * S
    out.append('</svg>')
    cairosvg.svg2png(bytestring=''.join(out).encode(), write_to=path)
    return report


if __name__ == '__main__':
    table = {'caps': CAPS, 'lower': LOWER}[sys.argv[1]]
    for k, d, a in overlay(table, sorted(table), sys.argv[2]):
        print(f'{k}: differs by {d:6.2f} of {a:6.2f} ({100 * d / a:5.1f}%)')
