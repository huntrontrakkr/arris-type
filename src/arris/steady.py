"""The white only ever shrinks: every glyph's counters nested along the weight.

Stack a glyph's weights as slices, the weight the third axis: the white is
a solid that only tapers. Every counter at a heavier weight fits inside the
same counter at a lighter one (the body aligned: it widens with the
weight), so the ink only ever grows. From that: a counter's area never
grows; no part of it moves outward (a notch, a flag, a slot that appears
out of nowhere, a corner that opens); a counter closes but never opens or
opens again. The italic k broke it three ways in 1.007: its counter grew
from Bold to 875 on the heavy grade (a rule holding it to a share of a
stem that kept growing), the notch under its arm opened into a slot at
775, and a step in it snapped shut at 824 on the light grade.

Read on a built variable font (``python -m arris.steady
build/Arris[GRAD,WTCH,wght].ttf``), whose every contour is the same
contour at every weight: each counter (a contour wound against its glyph's
outline) is followed along the weight every STEP units at each grade and
watch of LINES (the italic's curves flattened). Between neighbouring
weights the heavier counter is moved onto the lighter one, by the
translation that leaves least of it outside (_fit), and faulted:

* ``spills``: some part of it lies more than SPILL units outside the
  lighter counter (its size: how far, the furthest point);
* ``opens``: it is a counter where the lighter weight has none (a pinhole
  under MIN_AREA does not count).

``--drawings`` reads the engine's drawings of named glyphs instead, their
counters matched from one weight to the next by place. ``--json`` keeps
every glyph's faults for diffing builds.
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass, field
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from fontTools.ttLib import TTFont
from shapely import affinity
from shapely.geometry import Point, Polygon

STEP = 10                     # units of weight between readings
SPILL = 3.0                   # font units: a heavier counter further than this outside the lighter one spills
MIN_AREA = 400.0              # font units squared: a counter smaller than this (a pinhole closing) is not read
DENSE = 4.0                   # font units: the heavier counter's edges read every this far for the furthest point
LINES = [(-100, 0), (0, 0), (100, 0), (0, 100), (100, 100)]   # (grade, watch)


@dataclass
class Fault:
    kind: str                 # spills | opens
    contour: int
    grade: float
    watch: float
    weight: float             # the heavier of the two weights
    size: float               # units outside (spills), or the counter's area (opens)


@dataclass
class Report:
    name: str
    faults: list[Fault] = field(default_factory=list)


def _pts(contour, italic: bool) -> list[tuple[float, float]]:
    """A contour of (x, y, on) points as a polygon, the italic's curves flattened."""
    from . import italic as IT
    if italic and any(not q[2] for q in contour):
        return [(float(x), float(y)) for x, y in IT.flatten(contour)]
    return [(float(q[0]), float(q[1])) for q in contour]


def _signed(pts) -> float:
    n = len(pts)
    return 0.5 * sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n))


def _poly(pts) -> Polygon:
    import shapely
    poly = Polygon(pts)
    return poly if poly.is_valid else shapely.make_valid(poly).buffer(0)


def _outside(light: Polygon, heavy: Polygon) -> float:
    """How far the heavy counter reaches outside the light one: the furthest
    point of its boundary (read every DENSE units) from the light counter."""
    import shapely
    if heavy.is_empty or light.is_empty:
        return 0.0
    pts = shapely.get_coordinates(shapely.segmentize(heavy.boundary, DENSE))
    edge = light.boundary
    best = 0.0
    for x, y in pts:
        q = Point(x, y)
        if not light.covers(q):
            best = max(best, edge.distance(q))
    return best


def _fit(light: Polygon, heavy: Polygon) -> tuple[float, tuple[float, float]]:
    """(units outside, translation) for the heavy counter moved onto the light
    one so that least of it lies outside: tried in place and centred, the
    better then searched (Nelder-Mead on the area outside)."""
    from scipy.optimize import minimize
    cl, ch = light.centroid, heavy.centroid
    starts = [(0.0, 0.0), (cl.x - ch.x, cl.y - ch.y)]

    def spill_area(t):
        return affinity.translate(heavy, t[0], t[1]).difference(light).area
    best = min(starts, key=spill_area)
    out = _outside(light, affinity.translate(heavy, *best))
    if out <= SPILL:
        return out, best
    res = minimize(spill_area, np.array(best), method='Nelder-Mead',
                   options={'xatol': 0.25, 'fatol': 1.0, 'maxiter': 80, 'initial_simplex':
                            np.array([best, (best[0] + 4, best[1]), (best[0], best[1] + 4)])})
    t = (float(res.x[0]), float(res.x[1]))
    out2 = _outside(light, affinity.translate(heavy, *t))
    return (out2, t) if out2 < out else (out, best)


_FONT: list = []


def _open(path: str) -> None:
    font = TTFont(path)
    italic = bool(font['post'].italicAngle) or 'Italic' in Path(path).name
    _FONT[:] = [font, italic]


def _norm(font, tag: str, v: float) -> float:
    for a in font['fvar'].axes:
        if a.axisTag == tag:
            lo, d, hi = a.minValue, a.defaultValue, a.maxValue
            v = min(max(v, lo), hi)
            return (v - d) / (hi - d) if v >= d else (v - d) / (d - lo) if d > lo else 0.0
    return 0.0


def _faults_along(series, weights, grade, watch, contour_of=None) -> list[Fault]:
    """Faults along one line: series[i] the counters at weights[i], each
    (key, polygon); counters of neighbouring weights paired by key."""
    out = []
    for i in range(1, len(weights)):
        light = dict(series[i - 1])
        for key, heavy in series[i]:
            if heavy.area < MIN_AREA:
                continue
            lt = light.get(key)
            if lt is None or lt.area < MIN_AREA:
                out.append(Fault('opens', key if contour_of is None else contour_of(key), grade, watch,
                                 weights[i], round(heavy.area)))
                continue
            try:
                far, _ = _fit(lt, heavy)
            except Exception:  # noqa: BLE001, S112  (a contour folded past reading: the topology check's)
                continue
            if far > SPILL:
                out.append(Fault('spills', key if contour_of is None else contour_of(key), grade, watch,
                                 weights[i], round(far, 1)))
    return out


def scan_glyph(name: str) -> Report:
    """One glyph of the open variable font (its contours the same at every weight)."""
    from .topology import Variable
    font, italic = _FONT
    rep = Report(name)
    v = Variable(font, name)
    if v.composite or not len(v.coords):
        return rep
    weights = list(range(100, 901, STEP))
    for grade, watch in LINES:
        series = []
        for w in weights:
            loc = {'wght': _norm(font, 'wght', w), 'GRAD': _norm(font, 'GRAD', grade), 'WTCH': _norm(font, 'WTCH', watch)}
            pts = [_pts(c, italic) for c in v.at(loc)]
            signed = [_signed(q) if len(q) > 2 else 0.0 for q in pts]
            if not signed:
                series.append([])
                continue
            outer = max(signed, key=abs)
            series.append([(k, _poly(q)) for k, (q, a) in enumerate(zip(pts, signed)) if a * outer < 0])
        rep.faults += _faults_along(series, weights, grade, watch)
    return rep


_STYLE = ['upright']


def _init_drawings(style: str) -> None:
    import arris.glyphs  # noqa: F401  (the registry)
    _STYLE[0] = style


def _drawn_holes(name, p, italic):
    from .font import place
    rings, _ = place(name, p)
    pts = [_pts(r if italic else [(q[0], q[1], True) for q in r], italic) for r in rings]
    signed = [_signed(q) if len(q) > 2 else 0.0 for q in pts]
    if not signed:
        return []
    outer = max(signed, key=abs)
    return [_poly(q) for q, a in zip(pts, signed) if a * outer < 0 and abs(a) >= MIN_AREA]


def _matched(prev, holes):
    """Keys for this drawing's counters: each the key of the lighter
    drawing's counter nearest it (by centroid), a new key where none is."""
    if not prev:
        return list(enumerate(holes))
    out, used = [], set()
    nxt = max(k for k, _ in prev) + 1
    for h in sorted(holes, key=lambda h: -h.area):
        c = h.centroid
        cands = [(Point(c).distance(ph.centroid), k) for k, ph in prev if k not in used]
        if cands:
            d, k = min(cands)
            if d < max(60.0, dict(prev)[k].area ** 0.5):
                used.add(k)
                out.append((k, h))
                continue
        out.append((nxt, h))
        nxt += 1
    return out


def scan_drawing(args) -> Report:
    """One glyph's drawings (the engine's, no variable font) along the lines
    from ``lo`` to 900."""
    from .instances import params
    name, lo = args
    italic = _STYLE[0] == 'italic'
    rep = Report(name)
    weights = list(range(lo, 901, STEP))
    for grade, watch in LINES:
        series, prev = [], []
        for w in weights:
            p = params(w, grade, watch=watch / 100)
            if italic:
                from .italic import italic as ital
                p = ital(p)
            try:
                holes = _drawn_holes(name, p, italic)
            except Exception:  # noqa: BLE001  (a drawing that fails is the skeleton check's)
                holes = []
            prev = _matched(prev, holes)
            series.append(prev)
        rep.faults += _faults_along(series, weights, grade, watch)
    return rep


def scan_drawings(names, style: str, lo: int = 500, procs: int = 4) -> list[Report]:
    """The engine's drawings of the names in one style, from ``lo`` to Black."""
    jobs = [(n, lo) for n in names]
    if procs <= 1:
        _init_drawings(style)
        return [scan_drawing(j) for j in jobs]
    with Pool(procs, initializer=_init_drawings, initargs=(style,)) as pool:
        return pool.map(scan_drawing, jobs, chunksize=1)


def scan(path: str | Path, names=None, procs: int = 4) -> list[Report]:
    font = TTFont(str(path))
    names = list(names) if names else font.getGlyphOrder()
    if procs <= 1:
        _open(str(path))
        return [scan_glyph(n) for n in names]
    with Pool(procs, initializer=_open, initargs=(str(path),)) as pool:
        return pool.map(scan_glyph, names, chunksize=8)


def report(reports: list[Report], out=sys.stdout, limit: int = 40) -> None:
    bad = [r for r in reports if r.faults]
    spills = sum(1 for r in bad if any(f.kind == 'spills' for f in r.faults))
    opens = sum(1 for r in bad if any(f.kind == 'opens' for f in r.faults))
    print(f'{len(reports)} glyphs; {len(bad)} whose white is not nested along the weight: '
          f'{spills} with a counter that spills outward, {opens} with one that opens', file=out)

    def worst(r):
        return max((f.size for f in r.faults if f.kind == 'spills'), default=0.0)
    for r in sorted(bad, key=worst, reverse=True)[:limit]:
        fs = sorted(r.faults, key=lambda f: (f.kind != 'spills', -f.size))
        desc = ', '.join((f'spills {f.size:g} at {f.weight:g}/{f.grade:+g}/{f.watch:g}' if f.kind == 'spills'
                          else f'opens at {f.weight:g}/{f.grade:+g}/{f.watch:g}') for f in fs[:3])
        n = len(r.faults)
        print(f'  {r.name:24s} {desc}{f"  (+{n - 3})" if n > 3 else ""}', file=out)


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('font', help='a variable font, or "upright" / "italic" with --drawings')
    ap.add_argument('names', nargs='*')
    ap.add_argument('--drawings', action='store_true', help="read the engine's drawings of the names (from --from to Black)")
    ap.add_argument('--from', dest='lo', type=int, default=500)
    ap.add_argument('--json')
    ap.add_argument('--procs', type=int, default=4)
    ap.add_argument('--limit', type=int, default=40)
    a = ap.parse_args(argv)
    if a.drawings:
        reps = scan_drawings(a.names, a.font, a.lo, a.procs)
    else:
        reps = scan(a.font, a.names or None, a.procs)
    report(reps, limit=a.limit)
    if a.json:
        Path(a.json).write_text(json.dumps({r.name: [asdict(f) for f in r.faults] for r in reps if r.faults}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
