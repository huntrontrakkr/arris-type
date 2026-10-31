"""The Mechanical axis's illustration for Google Fonts' axis registry
(docs/google-fonts/mechanical.svg), drawn from the variable font: "Hx" at
MECH 0 and at MECH 100 (the font's WTCH), each over a slider, in the
registry's layout and colours (1920 x 1080, as its Thin Stroke and Grade
pictures). The strokes the axis moves are marked as the Thin Stroke picture
marks its bar: a band in the stroke's own thickness, drawn on past the
letter, here the H's crossbar (which thickens) and the x's rising diagonal
(which thins).

    uv run python tools/axis_illustration.py [font] [weight]
"""
from __future__ import annotations

import sys
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parents[1]
INK, TRACK, FILL, MARK = '#3C4043', '#D2E3FC', '#1A73E8', '#FF6D7F'
CENTRES = (595, 1325)           # the sliders' middles, as the registry places them
BASELINE, WIDTH = 660, 500      # where the letters stand, and how wide "Hx" is drawn
EXT = 46                        # px: how far a band runs on past its letter
GAP = 170                       # units between the H and the x, so their bands stay apart


def contours(glyf, name):
    coords, ends, _ = glyf[name].getCoordinates(glyf)
    out, start = [], 0
    for e in ends:
        out.append([tuple(map(float, p)) for p in coords[start:e + 1]])
        start = e + 1
    return out


def edges(rings):
    for r in rings:
        yield from zip(r, r[1:] + r[:1])


def bar(rings) -> tuple[float, float]:
    """The H's crossbar: its bottom and top, the horizontal edges between
    the baseline and the cap height."""
    ys = sorted({a[1] for a, b in edges(rings) if a[1] == b[1] and 150 < a[1] < 600})
    return ys[0], ys[-1]


def rising(rings) -> tuple[float, float]:
    """The x's rising diagonal: y - x of its two long edges."""
    cs: dict[float, float] = {}
    for a, b in edges(rings):
        dx, dy = b[0] - a[0], b[1] - a[1]
        if abs(dx) > 40 and abs(abs(dy / dx) - 1) < 0.02 and dy / dx > 0:
            c = round(a[1] - a[0], 1)
            cs[c] = cs.get(c, 0.0) + abs(dx)
    two = sorted(sorted(cs, key=cs.get)[-2:])
    return two[0], two[1]


def sample(font: TTFont, cx: float, scale: float) -> str:
    glyf, hmtx = font['glyf'], font['hmtx'].metrics
    adv = hmtx['H'][0] + GAP + hmtx['x'][0]
    x0 = cx - adv * scale / 2
    X = lambda u, at=0.0: x0 + (at + u) * scale
    Y = lambda u: BASELINE - u * scale
    marks = []
    h = contours(glyf, 'H')
    lo, hi = bar(h)
    xs = [p[0] for r in h for p in r]
    marks.append(f'M{X(min(xs)) - EXT:.1f} {Y(hi):.1f}H{X(max(xs)) + EXT:.1f}V{Y(lo):.1f}H{X(min(xs)) - EXT:.1f}Z')
    x = contours(glyf, 'x')
    c1, c2 = rising(x)
    at = hmtx['H'][0] + GAP
    # the band: the stroke's own strip, square at its ends, from before the x
    # to past it along the stroke (u: up the stroke; n: across it)
    r2 = 2 ** 0.5
    cm, half = (c1 + c2) / 2, (c2 - c1) / r2 / 2
    along = [(px + py - cm) / r2 for r in x for px, py in r]
    s0, s1 = min(along) - EXT / scale, max(along) + EXT / scale
    centre = lambda t: (t / r2, cm + t / r2)
    nx, ny = -1 / r2, 1 / r2
    pts = [(centre(t)[0] + k * nx * half, centre(t)[1] + k * ny * half) for t, k in ((s0, -1), (s1, -1), (s1, 1), (s0, 1))]
    marks.append('M' + 'L'.join(f'{X(px, at):.1f} {Y(py):.1f}' for px, py in pts) + 'Z')
    pen = SVGPathPen(None, ntos=lambda v: f'{v:.1f}')
    gs = font.getGlyphSet()
    for name, dx in (('H', 0), ('x', at)):
        gs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, X(0, dx), BASELINE)))
    return f'<path fill="{MARK}" d="{"".join(marks)}"/><path d="{pen.getCommands()}" fill="{INK}"/>'


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'build' / 'Arris[GRAD,WTCH,wght].ttf'
    wght = float(sys.argv[2]) if len(sys.argv) > 2 else 900
    ends = [instantiateVariableFont(TTFont(path), {'wght': wght, 'GRAD': 0, 'WTCH': t}) for t in (0, 100)]
    scale = WIDTH / max(f['hmtx'].metrics['H'][0] + GAP + f['hmtx'].metrics['x'][0] for f in ends)
    sliders = (f'<rect x="1216" y="813" width="218" height="50" rx="25" fill="{TRACK}"/>'
               f'<rect x="1215" y="813" width="218" height="50" rx="25" fill="{FILL}"/>'
               f'<rect x="486" y="813" width="218" height="50" rx="25" fill="{TRACK}"/>'
               f'<rect x="486" y="813" width="50" height="50" rx="25" fill="{FILL}"/>')
    svg = ('<svg width="1920" height="1080" fill="none" xmlns="http://www.w3.org/2000/svg">' + sliders
           + ''.join(sample(f, cx, scale) for f, cx in zip(ends, CENTRES)) + '</svg>\n')
    out = ROOT / 'docs' / 'google-fonts' / 'mechanical.svg'
    out.write_text(svg)
    for f, t in zip(ends, (0, 100)):
        lo, hi = bar(contours(f['glyf'], 'H'))
        c1, c2 = rising(contours(f['glyf'], 'x'))
        print(f'MECH {t:3}: crossbar {hi - lo:.0f} units, diagonal {(c2 - c1) / 2 ** 0.5:.0f} units across the stroke')
    print(f'{out}: wght {wght:g}, {len(svg) / 1024:.0f} KB')
    return 0


if __name__ == '__main__':
    sys.exit(main())
