"""Certify every glyph's strokes, upright and italic, at the weights given.

Two checks, both measured, neither tuned per glyph:

* **Outlines**: no contour crosses itself or another. A crossing is what
  shows as a break with a sliver of ink beside it.
* **Thickness**: the ink is rasterised and its distance transform read
  along its skeleton, which gives the stroke's thickness at every point of
  its centreline. Away from junctions (where strokes meet, the ink is
  legitimately wider) and from points (beak tips, apexes and stroke ends
  taper by design), no stroke may be thinner than the font's stroke floor
  (``Params.floor``: the Thin's thinnest stroke), and none may swell past
  CEILING of its weight's thickest. Parts lighter than FLOOR of the
  weight's own strokes are listed too: most are designed so (small
  figures, the letters inside a ring, the notch's one-pixel step, a tight
  stack's horizontals).

usage: stroke_scan.py [wght[,GRAD,WTCH] ...] [italic] [upright] [mono]
       (default: 100 400 900, both upright and italic; on every core,
       ARRIS_SCAN_WORKERS to set how many)
"""
from __future__ import annotations

import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from shapely.geometry import LinearRing
from skimage.morphology import skeletonize

import arris.glyphs  # noqa: F401
from arris.draw import REGISTRY
from arris.font import place
from arris.instances import params
from arris.italic import italic, polylines

FLOOR = 0.75        # of the weight's thinnest stroke: lighter parts are reported, as designed or not
CEILING = 1.75      # of its thickest
SPAN = 16           # raster pixels across the weight's thinnest stroke
PX = 0.4            # raster pixels per font unit (set per weight from SPAN)
TOL = 2.5 / SPAN     # the skeleton may sit a pixel or two off the true centreline


def _area(r):
    return sum(r[i - 1][0] * r[i][1] - r[i][0] * r[i - 1][1] for i in range(len(r))) / 2


def outlines(name, p):
    rings, _ = place(name, p)
    return polylines(rings) if p.slant else [[tuple(q[:2]) for q in r] for r in rings]


def crossings(rings):
    out = []
    lrs = []
    for i, r in enumerate(rings):
        if len(r) < 3:
            continue
        lr = LinearRing(r)
        if not lr.is_simple:
            out.append(f'contour {i} crosses itself')
        lrs.append((i, lr))
    for a in range(len(lrs)):
        for b in range(a + 1, len(lrs)):
            if lrs[a][1].intersects(lrs[b][1]):
                out.append(f'contours {lrs[a][0]} and {lrs[b][0]} meet')
    return out


def raster(rings, pad=6):
    xs = [x for r in rings for x, _ in r]
    ys = [y for r in rings for _, y in r]
    x0, y1 = min(xs), max(ys)
    w = int((max(xs) - x0) * PX) + 2 * pad
    h = int((y1 - min(ys)) * PX) + 2 * pad
    img = Image.new('1', (w, h), 0)
    d = ImageDraw.Draw(img)
    for r in sorted(rings, key=lambda r: -abs(_area(r))):
        pts = [((x - x0) * PX + pad, (y1 - y) * PX + pad) for x, y in r]
        d.polygon(pts, fill=1 if _area(r) > 0 else 0)
    return np.ascontiguousarray(np.array(img.convert('L'), dtype=np.uint8) > 0)


def _points(rings, span):
    """Where the outline turns through more than 135 degrees within ``span``
    of its length: apexes, beak tips, a stroke's end. The design draws
    those to points, so a stroke narrowing into them is not a thin stroke."""
    import math
    out = []
    for r in rings:
        n = len(r)
        if n < 3:
            continue
        seg = [math.dist(r[i], r[(i + 1) % n]) for i in range(n)]
        turn = []
        for i in range(n):
            a, b, c = r[i - 1], r[i], r[(i + 1) % n]
            u = (b[0] - a[0], b[1] - a[1])
            v = (c[0] - b[0], c[1] - b[1])
            turn.append(math.atan2(u[0] * v[1] - u[1] * v[0], u[0] * v[0] + u[1] * v[1]))
        for i in range(n):
            total, length, j = turn[i], 0.0, i
            while length < span and j - i < n:               # forward
                length += seg[j % n]
                j += 1
                total += turn[j % n] if length < span else 0.0
            length, j = 0.0, i
            while length < span and i - j < n:               # backward
                j -= 1
                length += seg[j % n]
                total += turn[j % n] if length < span else 0.0
            if abs(total) > math.radians(135):
                out.append(r[i])
    return out


def thickness(rings, p):
    """(thinnest, thickest) stroke away from junctions and ends, font units."""
    ink = raster(rings)
    if ink.sum() == 0:
        return None
    edt = ndimage.distance_transform_edt(ink)
    skel = skeletonize(ink)
    nb = ndimage.convolve(skel.astype(int), np.ones((3, 3), int), mode='constant') - skel
    junction = skel & (nb >= 3)
    end = skel & (nb <= 1)
    t_max = max(p.sv, p.sh, p.sd, p.ss)
    # how far a junction (a 2:1 diagonal meeting a stem merges over four
    # strokes' length) and a taper (a beak, a stroke's end) reach along a stroke
    reach_j = (2.5 * t_max + 2 * p.c) * PX
    reach_e = (1.2 * t_max + 2 * p.c) * PX
    far_j = ndimage.distance_transform_edt(~junction) > reach_j if junction.any() else np.ones_like(skel)
    far_e = ndimage.distance_transform_edt(~end) > reach_e if end.any() else np.ones_like(skel)
    keep = skel & far_j & far_e
    pts = _points(rings, 2 * t_max)
    if pts:
        xs = [x for r in rings for x, _ in r]
        ys = [y for r in rings for _, y in r]
        mark = np.zeros_like(skel)
        for x, y in pts:
            col, row = int((x - min(xs)) * PX) + 6, int((max(ys) - y) * PX) + 6
            if 0 <= row < mark.shape[0] and 0 <= col < mark.shape[1]:
                mark[row, col] = True
        keep &= ndimage.distance_transform_edt(~mark) > reach_e
    if not keep.any():
        return None
    t = 2 * edt[keep] / PX
    return float(t.min()), float(t.max())


def below_floor(rings, p):
    """Exact, on the vector outline: strokes thinner than the floor. Opening
    the ink (eroding it by just under half the floor, then dilating it back)
    removes exactly the parts narrower than the floor; corners lose small
    slivers, which are ignored, as are the parts at points the design draws
    sharp. Returns the width of the widest offending part's run, or None."""
    from shapely.geometry import Point
    from arris.geom import rings_to_shapely
    r = 0.5 * p.floor * (1 - 0.03)
    ink = rings_to_shapely(rings)
    opened = ink.buffer(-r, join_style='mitre').buffer(r, join_style='mitre')
    lost = ink.difference(opened)
    points = [Point(q) for q in _points(rings, 2 * max(p.sv, p.sh, p.sd, p.ss))]
    reach = 1.2 * max(p.sv, p.sh, p.sd, p.ss) + 2 * p.c
    worst = None
    for part in getattr(lost, 'geoms', [lost]):
        if part.is_empty or part.area < 1e-6:
            continue
        x0, y0, x1, y1 = part.bounds
        run = max(x1 - x0, y1 - y0)
        if run < 3 * p.floor:                               # a corner's sliver
            continue
        if part.area < 0.25 * p.floor * run:                # a numerical sliver along a straight edge
            continue
        if any(part.distance(q) < reach for q in points):   # narrowing into a designed point
            continue
        worst = max(worst or 0.0, run)
    return worst


def scan(p, names, pool=None):
    """Every glyph's issues at p, in order; on ``pool`` in chunks of glyphs."""
    if pool is None:
        return _scan_chunk((p, names))
    chunks = [names[i:i + 24] for i in range(0, len(names), 24)]
    return [x for part in pool.imap(_scan_chunk, [(p, c) for c in chunks]) for x in part]


def _scan_chunk(job):
    global PX
    p, names = job
    t_min = max(min(p.sv, p.sh, p.sd, p.ss), p.floor)
    t_max = max(p.sv, p.sh, p.sd, p.ss)
    PX = SPAN / t_min
    issues = []
    for n in names:
        rings = outlines(n, p)
        if not rings:
            continue
        for msg in crossings(rings):
            issues.append((n, msg))
        th = thickness(rings, p)
        if th is None:
            continue
        lo, hi = th
        run = below_floor(rings, p) if p.floor else None
        if run is not None:
            issues.append((n, f'BELOW THE STROKE FLOOR over {run:.0f} units (floor {p.floor:.0f})'))
        elif lo < FLOOR * t_min:
            issues.append((n, f'lighter than its weight: {lo:.0f} ({FLOOR * t_min:.0f})'))
        ceiling = max(CEILING * t_max, 1.1 * p.dot())        # dots and comma heads are drawn bigger at Thin
        if hi > ceiling and not REGISTRY[n].solid:
            issues.append((n, f'swells to {hi:.0f} (ceiling {ceiling:.0f})'))
    return issues


if __name__ == '__main__':
    args = sys.argv[1:]
    modes = [m for m in ('upright', 'italic') if m in args] or ['upright', 'italic']
    mono = 'mono' in args
    locs = [tuple(int(v) for v in a.split(',')) for a in args if a[0].isdigit()] or [(100,), (400,), (900,)]
    names = [n for n in REGISTRY if not n.endswith('.ital')]
    total = 0
    import os
    from multiprocessing import get_context
    with get_context('fork').Pool(int(os.environ.get('ARRIS_SCAN_WORKERS', os.cpu_count() or 8))) as pool:
        for loc in locs:
            w, g, t = (list(loc) + [0, 0])[:3]
            for mode in modes:
                p = params(w, g, watch=t / 100).with_(mono=mono)
                if mode == 'italic':
                    p = italic(p)
                issues = scan(p, names, pool)
                total += len(issues)
                print(f'## {mode} {w},{g},{t}: {len(issues)} issues', flush=True)
                for n, msg in issues:
                    print(f'  {n:18s} {msg}')
    print('TOTAL', total)
