"""Each Arris Mono ligature under its plain characters, on the cell grid,
from the engine: a ligature must keep every character where it stands and
as it is drawn alone, joining only by running strokes on.

usage: ligature_pairs.py out.png weight [ital]"""
import sys
from PIL import Image, ImageDraw
import arris.glyphs
from arris.draw import REGISTRY
from arris.font import place
from arris.instances import params
from arris.italic import italic, polylines
from arris.glyphs.ligatures import LIGATURES
out, w = sys.argv[1], int(sys.argv[2])
ital = 'ital' in sys.argv[3:]
p = params(w).with_(mono=True)
if ital: p = italic(p)
S = 0.075
cellw = p.fig_adv * S
def draw_rings(d, rings, ox, oy):
    rings = polylines(rings) if ital else [[c[:2] for c in r] for r in rings]
    for r in sorted(rings, key=lambda r: -abs(sum(r[i-1][0]*r[i][1]-r[i][0]*r[i-1][1] for i in range(len(r))))):
        pts = [(ox + x * S, oy + (950 - y) * S) for x, y in r]
        a = sum(pts[i-1][0]*pts[i][1]-pts[i][0]*pts[i-1][1] for i in range(len(pts)))
        d.polygon(pts, fill=0 if a < 0 else 255)
cols = 7
rowh = int(1200 * S) * 2 + 24
n = len(LIGATURES)
W = int(cols * (3 * cellw + 30)) + 40
H = ((n + cols - 1) // cols) * rowh + 20
img = Image.new('L', (W, H), 255); d = ImageDraw.Draw(img)
for k, (name, comps) in enumerate(LIGATURES):
    cx = 20 + (k % cols) * (3 * cellw + 30); cy = 10 + (k // cols) * rowh
    for j in range(len(comps)):
        for row in (0, 1):
            d.rectangle([cx + j * cellw, cy + row * (1200 * S + 8), cx + (j + 1) * cellw, cy + row * (1200 * S + 8) + 1200 * S], outline=215)
    for j, c in enumerate(comps):
        rings, adv = place(c, p)
        draw_rings(d, rings, cx + j * cellw, cy)
    rings, adv = place(name, p)
    draw_rings(d, rings, cx + (len(comps) - 1) * cellw, cy + 1200 * S + 8)
img.save(out); print(img.size)
