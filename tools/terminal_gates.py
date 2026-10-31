"""Gates for the terminal and UI glyphs (glyphs.terminal, shapes, dingbats).

usage: terminal_gates.py draw          every glyph at 100 400 900, (900,100,0) and (900,0,100),
                                       upright, italic and mono: no exception
       terminal_gates.py stroke [w..]  stroke_scan's checks, these glyphs only
       terminal_gates.py white [w..]   white_scan's check, these glyphs only (every kind)
       terminal_gates.py tiling        cells: ink reaches every edge it should, exactly
"""
from __future__ import annotations

import sys

import arris.glyphs  # noqa: F401
from arris.draw import REGISTRY
from arris.font import place
from arris.instances import params
from arris.italic import italic

MODULES = ('terminal', 'shapes', 'dingbats')
NAMES = [n for n, s in REGISTRY.items() if s.fn.__module__.rsplit('.', 1)[-1] in MODULES]
LOCS = [(100, 0, 0), (400, 0, 0), (900, 0, 0), (900, 100, 0), (900, 0, 100)]


def gate_draw():
    bad = 0
    for loc in LOCS:
        for mono in (False, True):
            for ital in (False, True):
                p = params(loc[0], loc[1], watch=loc[2] / 100).with_(mono=mono)
                if ital:
                    p = italic(p)
                for n in NAMES:
                    try:
                        rings, adv = place(n, p)
                        assert adv > 0
                    except Exception as e:  # noqa: BLE001
                        bad += 1
                        print('FAIL', loc, 'mono' if mono else '', 'italic' if ital else '', n, type(e).__name__, e)
    print(f'draw: {len(NAMES)} glyphs x {len(LOCS)} locations x upright/italic x proportional/mono: {bad} failures')
    return bad


def gate_stroke(locs):
    sys.path.insert(0, 'tools')
    import stroke_scan
    total = 0
    for w, g_, t in locs:
        for mono in (False, True):
            for ital in (False, True):
                p = params(w, g_, watch=t / 100).with_(mono=mono)
                if ital:
                    p = italic(p)
                issues = stroke_scan.scan(p, NAMES)
                serious = [(n, m) for n, m in issues if 'lighter than its weight' not in m]
                light = len(issues) - len(serious)
                total += len(serious)
                print(f'## {"italic" if ital else "upright"}{" mono" if mono else ""} {w},{g_},{t}: '
                      f'{len(serious)} issues ({light} lighter than their weight, informational)')
                for n, m in serious:
                    print(f'  {n:14s} {chr(REGISTRY[n].unicode) if REGISTRY[n].unicode else ""} {m}')
    print('TOTAL', total)
    return total


def gate_white(locs):
    sys.path.insert(0, 'tools')
    import white_scan
    total = 0
    for mono in (False, True):
        ref = params(400).with_(mono=mono)
        base = {n: white_scan.features(n, ref) for n in NAMES}
        for w, g_, t in locs:
            p = params(w, g_, watch=t / 100).with_(mono=mono)
            lost = [(n, base[n], k) for n in NAMES if (k := white_scan.features(n, p)) < base[n]]
            total += len(lost)
            print(f'## {"mono " if mono else ""}{w},{g_},{t}: {len(lost)} glyphs lose white features')
            if lost:
                print('  ' + ', '.join(f'{n} {chr(REGISTRY[n].unicode)} {a}->{b}' for n, a, b in lost))
    print('TOTAL', total)
    return total


def gate_tiling():
    """Every cell glyph's ink, at every location: where it touches a cell
    edge, it lies flush on it (no ink beyond the line's extent, except a
    diagonal running on through a corner), and a full block is exactly the
    cell."""
    from arris.geom import rings_to_shapely
    from arris.glyphs.terminal import BOTTOM, TOP
    from shapely.geometry import box
    bad = 0
    cells = [n for n in NAMES if REGISTRY[n].cell]
    for loc in LOCS:
        for ital in (False, True):
            p = params(loc[0], loc[1], watch=loc[2] / 100)
            if ital:
                p = italic(p)
            for n in cells:
                rings, adv = place(n, p)
                if p.slant:
                    from arris.italic import polylines
                    rings = polylines(rings)
                if not rings:
                    continue
                ink = rings_to_shapely(rings)
                x0, y0, x1, y1 = ink.bounds
                diag = n in ('uni2571', 'uni2572', 'uni2573')
                if y0 < BOTTOM - 1e-6 or y1 > TOP + 1e-6 or (not diag and (x0 < -1e-6 or x1 > adv + 1e-6)):
                    bad += 1
                    print('OUTSIDE', loc, n, ink.bounds, adv)
            full = rings_to_shapely(place('block', p)[0] if not p.slant else
                                    __import__('arris.italic', fromlist=['polylines']).polylines(place('block', p)[0]))
            if full.symmetric_difference(box(0, BOTTOM, place('block', p)[1], TOP)).area > 1e-6:
                bad += 1
                print('BLOCK not the cell', loc)
    print(f'tiling: {len(cells)} cell glyphs: {bad} problems')
    return bad


def gate_counters():
    """scan_counters.py's check for these glyphs: a closed counter they have
    at Regular that closes at a heavier location, or shrinks below a third
    of the stem."""
    import shapely
    from shapely.geometry import Polygon
    from arris.draw import draw
    from arris.geom import rings_to_shapely
    locs = [(400, 0, 0), (700, 0, 0), (900, 0, 0), (900, 100, 0), (900, 0, 100), (900, 100, 100)]
    bad = 0
    for mono in (False, True):
        for n in NAMES:
            res = []
            for w, gr, t in locs:
                p = params(w, gr, watch=t / 100).with_(mono=mono)
                poly = rings_to_shapely(draw(n, p).rings())
                hs = [2 * shapely.maximum_inscribed_circle(Polygon(h), tolerance=1.0).length
                      for part in getattr(poly, 'geoms', [poly]) for h in part.interiors]
                res.append((len(hs), min(hs) / p.sv if hs else None))
            lost = [locs[i] for i, (k, _) in enumerate(res) if k < res[0][0]]
            tight = [(locs[i], round(m, 2)) for i, (k, m) in enumerate(res) if m is not None and m < 0.35]
            if lost or tight:
                bad += 1
                print('mono' if mono else '    ', n, chr(REGISTRY[n].unicode), res[0][0], lost, tight)
    print(f'counters: {bad} flagged')
    return bad


def gate_vf(path='build/Arris[GRAD,WTCH,wght].ttf'):
    """arris.vf's interpolation check (arris.vf.check), for these glyphs only: the
    variable font against exact drawings between its masters (mean outline
    difference, font units)."""
    from fontTools.ttLib import TTFont
    from fontTools.varLib.instancer import instantiateVariableFont
    from arris.geom import rings_to_shapely
    from arris import italic as ital
    checks = [(150, 0, 0), (300, 0, 0), (500, 0, 0), (700, 0, 0), (800, 0, 0),
              (400, 50, 0), (700, -50, 0), (600, 0, 50), (300, 0, 100), (800, 50, 100)]
    slanted = 'Italic' in path
    worst = []
    for w in checks:
        inst = instantiateVariableFont(TTFont(path), {'wght': w[0], 'GRAD': w[1], 'WTCH': w[2]})
        glyf = inst['glyf']
        p = params(w[0], w[1], watch=w[2] / 100)
        if slanted:
            p = italic(p)
        for n in NAMES:
            rings, _ = place(n, p)
            exact = rings_to_shapely(ital.polylines(rings) if slanted else rings)
            coords, ends, flags = glyf[n].getCoordinates(glyf)
            pts, start, got = list(coords), 0, []
            for e in ends:
                c = [(q[0], q[1], bool(f & 1)) for q, f in zip(pts[start:e + 1], flags[start:e + 1])][::-1]
                got.append(ital.flatten(c) if slanted else [q[:2] for q in c])
                start = e + 1
            interp = rings_to_shapely([r for r in got if len(set(r)) >= 3])
            if exact.is_empty and interp.is_empty:
                err = 0.0
            else:
                err = interp.symmetric_difference(exact).area / max(exact.boundary.length, 1)
            worst.append((err, w, n))
    worst.sort(reverse=True)
    bad = [x for x in worst if x[0] > 3.0]
    print(f'vf: {len(worst)} glyph-locations; worst {worst[0][0]:.1f} units, median '
          f'{sorted(worst)[len(worst) // 2][0]:.2f}; {len(bad)} over 3.0 units')
    from collections import Counter
    print("  over 3 units, by glyph:", ", ".join(f"{chr(REGISTRY[n].unicode)} {k}" for n, k in Counter(n for e, w, n in bad).most_common()))
    for e, w, n in worst[:15]:
        print(f'  {n:12s} {chr(REGISTRY[n].unicode)} at {w}: {e:.1f}')
    return len(bad)


if __name__ == '__main__':
    what = sys.argv[1]
    locs = [tuple((list(int(v) for v in a.split(',')) + [0, 0])[:3]) for a in sys.argv[2:]] or \
        [(100, 0, 0), (400, 0, 0), (900, 0, 0)]
    print(len(NAMES), 'glyphs')
    n = {'draw': gate_draw, 'tiling': gate_tiling, 'counters': gate_counters, 'vf': gate_vf}.get(what)
    if n:
        sys.exit(1 if n() else 0)
    sys.exit(1 if {'stroke': gate_stroke, 'white': gate_white}[what](locs) else 0)
