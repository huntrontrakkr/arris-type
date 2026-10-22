import sys
import shapely
from shapely.geometry.polygon import orient
from arris import heritage
from arris.masters import CAPS, LOWER
from arris.spacing import bearings
from arris.proof import render_svg
from PIL import Image
U = 60.0
FIG = {str(i): heritage.zone(str(i)) for i in range(10)}
def rings_of(ch):
    if ch in LOWER: m, base = LOWER[ch], 13       # rows above baseline
    elif ch in CAPS: m, base = CAPS[ch], 12
    else: m, base = FIG[ch], 12
    g = heritage.trace(m)  # y up with row 0 at top: y_up = len(m) - row
    g = shapely.affinity.translate(g, 0, -(len(m) - base))
    g = shapely.affinity.scale(g, U, U, origin=(0, 0))
    out = []
    for poly in getattr(g, 'geoms', [g]):
        poly = orient(poly, 1.0)
        out.append(list(poly.exterior.coords)[:-1])
        out += [list(h.coords)[:-1] for h in poly.interiors]
    return out
LIGHT = 0.27 * (9 * U - 4 * U)   # H sidebearing: 27% of its counter
def place(ch):
    r = rings_of(ch)
    lo, hi = (0, 540) if ch in LOWER else (0, 720)
    l, rr, xmin, xmax = bearings(r, lo, hi, LIGHT, 0.2 * (hi - lo), floor=-15)
    return [[(x - xmin + l, y) for x, y in ring] for ring in r], l + (xmax - xmin) + rr
imgs = []
for line in sys.argv[1].split('|'):
    items = [([], 230) if ch == ' ' else place(ch) for ch in line]
    imgs.append(render_svg(items, gap=0, height=800, baseline=220, scale=float(sys.argv[2]), pad=12))
im = Image.new('L', (max(i.width for i in imgs), sum(i.height for i in imgs)), 255)
y = 0
for i in imgs: im.paste(i, (0, y)); y += i.height
im.save(sys.argv[3]); print(im.size)
