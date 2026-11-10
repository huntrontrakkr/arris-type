"""Stroke thicknesses by role in hand-drawn sans faces, as shares of the H's stem."""
import sys, math
sys.path.insert(0, '/tmp/claude-0/-home-user/ecf24825-f4d4-5f2b-8341-ec7661a2b47b/scratchpad')
from calib import shape
from fontTools.ttLib import TTFont
from shapely.geometry import LineString

def runs(poly, a, b):
    cut = poly.intersection(LineString([a, b]))
    out = []
    for g in getattr(cut, 'geoms', [cut]):
        if g.is_empty: continue
        (x0, y0), (x1, y1) = g.coords[0], g.coords[-1]
        out.append(((x0, y0), (x1, y1), math.hypot(x1 - x0, y1 - y0)))
    return sorted(out)
def hs(poly, y):
    x0, _, x1, _ = poly.bounds; return runs(poly, (x0 - 5, y), (x1 + 5, y))
def vs(poly, x):
    _, y0, _, y1 = poly.bounds; return sorted(runs(poly, (x, y0 - 5), (x, y1 + 5)), key=lambda r: r[0][1])
def diag(poly, y, i, dy=8):
    """Perpendicular thickness of the i-th run across height y of a straight slanted stroke."""
    a, b = hs(poly, y)[i], hs(poly, y + dy)[i]
    slope = (b[0][0] - a[0][0]) / dy                # dx/dy of the edge
    return a[2] / math.sqrt(1 + slope * slope)

for path in sys.argv[1:]:
    font = TTFont(path); G = lambda c: shape(font, c)[0]
    H = G('H'); cap = H.bounds[3]; xh = G('x').bounds[3]
    stem = hs(H, cap * 0.25)[0][2]
    r = {}
    r['H bar'] = vs(H, (H.bounds[0] + H.bounds[2]) / 2)[0][2]
    E = G('E'); x = E.bounds[0] + 0.7 * (E.bounds[2] - E.bounds[0]); e3 = vs(E, x)
    r['E arms'] = (e3[0][2] + e3[-1][2]) / 2; r['E middle'] = e3[1][2] if len(e3) == 3 else float('nan')
    O = G('O'); r['O side'] = hs(O, cap / 2)[0][2]; r['O top'] = vs(O, (O.bounds[0] + O.bounds[2]) / 2)[-1][2]
    r['V'] = diag(G('V'), cap * 0.6, 0); r['A bar'] = vs(G('A'), (G('A').bounds[0] + G('A').bounds[2]) / 2)[0][2]
    K = G('K'); r['K arm'] = diag(K, cap * 0.85, 1); r['K leg'] = diag(K, cap * 0.12, 1)
    X = G('X'); r['X'] = diag(X, cap * 0.85, 0)
    Z = G('Z'); r['Z diagonal'] = diag(Z, cap * 0.5, 0); r['Z bars'] = vs(Z, (Z.bounds[0] + Z.bounds[2]) / 2)[0][2]
    N = G('N'); r['N diagonal'] = diag(N, cap * 0.5, 1); r['N stems'] = hs(N, cap * 0.5)[0][2]
    M = G('M'); r['M stems'] = hs(M, cap * 0.15)[0][2]; r['M inner'] = diag(M, cap * 0.6, 1)
    W = G('W'); r['W outer'] = diag(W, cap * 0.6, 0); r['W inner'] = diag(W, cap * 0.35, 1)
    n = G('n'); ns = hs(n, xh * 0.25); r['n stem'] = ns[0][2]; r['n right stem'] = ns[-1][2]; r['n arch top'] = vs(n, ns[-1][0][0] - 0.25 * (ns[-1][0][0] - ns[0][1][0]))[-1][2]
    o = G('o'); r['o side'] = hs(o, xh / 2)[0][2]; r['o top'] = vs(o, (o.bounds[0] + o.bounds[2]) / 2)[-1][2]
    e = G('e'); ev = vs(e, (e.bounds[0] + e.bounds[2]) / 2); r['e bar'] = ev[1][2] if len(ev) == 3 else float('nan'); r['e top'] = ev[-1][2]
    a = G('a'); av = vs(a, (a.bounds[0] + a.bounds[2]) * 0.5); r['a bars'] = '/'.join(f'{q[2] / stem:.2f}' for q in av)
    v = G('v'); r['v'] = diag(v, xh * 0.6, 0); y = G('y'); r['y arm'] = diag(y, xh * 0.6, 0); r['y stroke'] = diag(y, xh * 0.6, 1)
    k = G('k'); r['k arm'] = diag(k, xh * 0.8, 1); r['k leg'] = diag(k, xh * 0.15, 1)
    x_ = G('x'); r['x'] = diag(x_, xh * 0.85, 0); z = G('z'); r['z diagonal'] = diag(z, xh * 0.5, 0); r['z bars'] = vs(z, (z.bounds[0] + z.bounds[2]) / 2)[0][2]
    t = G('t'); f = G('f'); r['f bar'] = vs(f, f.bounds[2] - 0.15 * (f.bounds[2] - f.bounds[0]))[0][2] if vs(f, f.bounds[2] - 0.15 * (f.bounds[2] - f.bounds[0])) else float('nan')
    print(path.split('/')[-1], f'stem {stem:.0f} = {stem / cap:.3f} cap')
    print('   ' + '  '.join(f'{k_} {v_ if isinstance(v_, str) else format(v_ / stem, ".2f")}' for k_, v_ in r.items()))
