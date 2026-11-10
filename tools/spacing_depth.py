"""How deep into a side's white hand-spaced fonts count it: fit the area model's depth limit to their side bearings."""
import sys, glob
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union

class Flat(BasePen):
    def __init__(self, gs): super().__init__(gs); self.rings = []; self.cur = None
    def _moveTo(self, p): self.cur = [p]
    def _lineTo(self, p): self.cur.append(p)
    def _curveToOne(self, a, b, c):
        p0 = self.cur[-1]
        for t in np.linspace(0, 1, 9)[1:]:
            self.cur.append(tuple((1-t)**3*np.array(p0) + 3*(1-t)**2*t*np.array(a) + 3*(1-t)*t*t*np.array(b) + t**3*np.array(c)))
    def _qCurveToOne(self, a, b):
        p0 = self.cur[-1]
        for t in np.linspace(0, 1, 9)[1:]:
            self.cur.append(tuple((1-t)**2*np.array(p0) + 2*(1-t)*t*np.array(a) + t*t*np.array(b)))
    def _closePath(self):
        if self.cur and len(self.cur) > 2: self.rings.append(self.cur)
        self.cur = None
    _endPath = _closePath

def shape(font, ch):
    gs = font.getGlyphSet(); name = font.getBestCmap()[ord(ch)]
    pen = Flat(gs); gs[name].draw(pen)
    poly = None
    for r in pen.rings:
        q = Polygon(r).buffer(0)
        poly = q if poly is None else poly.symmetric_difference(q)
    return poly, gs[name].width

def sides(poly, adv, y0, y1, n=120):
    ys = y0 + (np.arange(n) + 0.5) * (y1 - y0) / n
    minx, _, maxx, _ = poly.bounds
    L = np.full(n, np.nan); R = np.full(n, np.nan)
    for i, y in enumerate(ys):
        cut = poly.intersection(LineString([(minx - 10, y), (maxx + 10, y)]))
        if cut.is_empty: continue
        xs = [c[0] for g in getattr(cut, 'geoms', [cut]) for c in g.coords]
        L[i], R[i] = min(xs), max(xs)
    xmin, xmax = np.nanmin(L), np.nanmax(R)
    return L - xmin, xmax - R, xmin, adv - xmax      # white depths per row on each side; actual lsb, rsb

CAPS = 'ABCDEFGHJKLMNOPQRSTUVWXYZ'; LOW = 'abcdefghknopqrstuvxz'
def fit(path):
    font = TTFont(path, fontNumber=0)
    cap = shape(font, 'H')[0].bounds[3]; xh = shape(font, 'x')[0].bounds[3]
    out = {}
    for zone, chars, ref in (('cap', CAPS, 'H'), ('low', LOW, 'n')):
        top = cap if zone == 'cap' else xh
        data = {c: sides(*shape(font, c), 0, top) for c in chars}
        light = data[ref][2]                                  # the straight stem's bearing
        best = None; rows = {}
        for d in np.arange(0.04, 0.42, 0.01):
            lim = d * top; err = []
            for c, (wl, wr, lsb, rsb) in data.items():
                for w, sb in ((wl, lsb), (wr, rsb)):
                    pred = light - float(np.where(np.isnan(w), lim, np.minimum(w, lim)).mean())
                    err.append((pred - sb) / light)
            e = float(np.sqrt(np.mean(np.square(err))))
            rows[round(float(d), 2)] = e
            if best is None or e < best[1]: best = (round(float(d), 2), e)
        out[zone] = (best, rows, light, top, data)
    return out
if __name__ == '__main__':
    import os
    for path in sys.argv[1:]:
        r = fit(path)
        if os.environ.get('RESID'):
            dx = float(os.environ['RESID'])
            for z in ('cap', 'low'):
                best, rows, light, top, data = r[z]; lim = dx * r['low'][3]; line = []
                for c, (wl, wr, lsb, rsb) in data.items():
                    pl = light - float(np.where(np.isnan(wl), lim, np.minimum(wl, lim)).mean()); pr = light - float(np.where(np.isnan(wr), lim, np.minimum(wr, lim)).mean())
                    line.append(f'{c} {lsb/light:.2f}/{pl/light:.2f} {rsb/light:.2f}/{pr/light:.2f}')
                print('   ', z, 'actual/model, as shares of the stem bearing:', ' | '.join(line))
        print(path.split('/')[-1], '  '.join(f"{z}: depth {r[z][0][0]:.2f} of the zone ({r[z][0][0]*r[z][3]/r['low'][3]:.2f} x-heights), rms {r[z][0][1]:.2f}; at 0.20: {r[z][1][0.2]:.2f}" for z in ('cap', 'low')))
