"""Counters that only shrink: every glyph's white along the weight.

As the weight grows a counter gets smaller and simpler, steadily: it never
grows, and it never jumps from one shape to another between neighbouring
weights. Both happened, and neither the skeleton check (features kept or
lost) nor the topology check (outlines that fold) saw them: the italic
k's counter grew from Bold to 875 on the heavy grade, a rule holding it to
a share of a stem that kept growing, and fell to a diamond at Black; a
step in its notch closed by the jog cleanup snapped a twentieth of it shut
in five units of weight.

Read on a built variable font (``python -m arris.steady
build/Arris[GRAD,WTCH,wght].ttf``), whose every contour is the same
contour at every weight: each counter (a contour wound against its
glyph's outline) is followed along the weight every STEP units at each
grade and watch of LINES, its area (the italic's curves flattened) read
at each. Faults:

* ``grows``: the area grows by more than GROW of itself from one weight to
  the next;
* ``jumps``: it changes by more than JUMP of the largest it has on its line
  between neighbouring weights (a counter that steps from one shape to
  another).

``--json`` keeps every glyph's faults for diffing builds.
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass, field
from multiprocessing import Pool
from pathlib import Path

from fontTools.ttLib import TTFont

STEP = 10                     # units of weight between readings
GROW = 0.01                   # a counter growing by more than this share of itself in a step grows
JUMP = 0.06                   # changing by more than this share of its largest in ten units of weight, it jumps
MIN_AREA = 400.0              # font units squared: a counter smaller than this (a pinhole closing) is not read
LINES = [(-100, 0), (0, 0), (100, 0), (0, 100), (100, 100)]   # (grade, watch)


@dataclass
class Fault:
    kind: str                 # grows | jumps
    contour: int
    grade: float
    watch: float
    weight: float             # the heavier of the two weights
    change: float             # the change as a share (of itself for grows, of its largest for jumps)


@dataclass
class Report:
    name: str
    faults: list[Fault] = field(default_factory=list)


def _area(contour, italic: bool) -> float:
    """The signed area of a contour of (x, y, on) points, curves flattened."""
    from . import italic as IT
    pts = IT.flatten(contour) if italic and any(not q[2] for q in contour) else [(q[0], q[1]) for q in contour]
    n = len(pts)
    return 0.5 * sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n))


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


def scan_glyph(name: str) -> Report:
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
            series.append([_area(c, italic) for c in v.at(loc)])
        if not series or not series[0]:
            continue
        for k in range(len(series[0])):
            a = [row[k] for row in series]
            outer = [max(row, key=abs) for row in series]
            # a counter: wound against the glyph's largest contour, at every weight it is read
            holes = [x * o < 0 for x, o in zip(a, outer)]
            if not any(holes):
                continue
            mag = [abs(x) if h else 0.0 for x, h in zip(a, holes)]
            big = max(mag)
            if big < MIN_AREA:
                continue
            for i in range(1, len(weights)):
                prev, cur = mag[i - 1], mag[i]
                if prev < MIN_AREA or cur < MIN_AREA:
                    continue
                if cur > prev * (1 + GROW):
                    rep.faults.append(Fault('grows', k, grade, watch, weights[i], round(cur / prev - 1, 4)))
                if abs(cur - prev) > JUMP * STEP / 10 * big:
                    rep.faults.append(Fault('jumps', k, grade, watch, weights[i], round((cur - prev) / big, 4)))
    return rep


_STYLE = ['upright']


def _init_drawings(style: str) -> None:
    import arris.glyphs  # noqa: F401  (the registry)
    _STYLE[0] = style


def _holes(rings, italic: bool) -> list[float]:
    signed = [_area(r if italic else [(q[0], q[1], True) for q in r], italic) for r in rings]
    if not signed:
        return []
    outer = max(signed, key=abs)
    return sorted(abs(a) for a in signed if a * outer < 0 and abs(a) >= MIN_AREA)


def scan_drawing(args) -> Report:
    """One glyph's drawings (the engine's, no variable font) along the lines
    between ``lo`` and 900: the smallest counter and all of them together,
    since contours are not the same from one drawing to the next."""
    from .font import place
    from .instances import params
    name, lo = args
    italic = _STYLE[0] == 'italic'
    rep = Report(name)
    weights = list(range(lo, 901, STEP))
    for grade, watch in LINES:
        rows = []
        for w in weights:
            p = params(w, grade, watch=watch / 100)
            if italic:
                from .italic import italic as ital
                p = ital(p)
            try:
                rings, _ = place(name, p)
            except Exception:  # noqa: BLE001  (a drawing that fails is the skeleton check's)
                rows.append(None)
                continue
            rows.append(_holes(rings, italic))
        for k, pick in ((0, min), (1, sum)):
            series = [pick(r) if r else 0.0 for r in rows]
            big = max(series) if series else 0.0
            if big < MIN_AREA:
                continue
            for i in range(1, len(weights)):
                prev, cur = series[i - 1], series[i]
                if prev < MIN_AREA or cur < MIN_AREA or rows[i] is None or rows[i - 1] is None:
                    continue
                if cur > prev * (1 + GROW):
                    rep.faults.append(Fault('grows', k, grade, watch, weights[i], round(cur / prev - 1, 4)))
                if abs(cur - prev) > JUMP * STEP / 10 * big:
                    rep.faults.append(Fault('jumps', k, grade, watch, weights[i], round((cur - prev) / big, 4)))
    return rep


def scan_drawings(names, style: str, lo: int = 500, procs: int = 4) -> list[Report]:
    """The engine's drawings of the names in one style, from ``lo`` to Black
    (``contour`` 0 is the smallest counter, 1 all of them)."""
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
    grows = sum(1 for r in bad if any(f.kind == 'grows' for f in r.faults))
    jumps = sum(1 for r in bad if any(f.kind == 'jumps' for f in r.faults))
    print(f'{len(reports)} glyphs; {len(bad)} with a counter that grows ({grows}) or jumps ({jumps}) along the weight',
          file=out)

    def worst(r):
        return max(abs(f.change) for f in r.faults)
    for r in sorted(bad, key=worst, reverse=True)[:limit]:
        fs = sorted(r.faults, key=lambda f: -abs(f.change))
        desc = ', '.join(f'{f.kind} {f.change:+.0%} at {f.weight:g}/{f.grade:+g}/{f.watch:g}' for f in fs[:3])
        print(f'  {r.name:24s} {desc}', file=out)


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
