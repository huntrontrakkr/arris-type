"""Every outline's topology along the axes: what the design never does.

An Arris outline is a union of strokes, polished (geom): each contour one
simple ring, no two meeting; no turn sharper than the steepest diagonal
against a stem (an outer corner is cut at 45 degrees; the N's 2:1 diagonal
meets its stem at 153 degrees of turn); no edge shorter than a polish sliver;
no two parts of a contour nearer than a break unless they meet. Whatever
breaks one of these is a defect, in a drawing (a jog closed past its
neighbour: the ç at 550) or in the variable font between its masters (a
point the alignment put a fraction of a unit off the outline opens into
a wedge: the ŧ at the heavy corner), and shows as a notch, a sliver of
white or ink, a flicker as the weight moves.

Faults, on a contour as a polyline (the italic's curves sampled):

* ``cross``: the contour crosses itself (its size: the side of a square
  as large as the piece it folds into, in font units); ``meet``: two
  contours of the glyph touch or cross.
* ``hairpin``: a turn sharper than HAIRPIN at a vertex, the path doubling
  back: a fold or a spike.
* ``tiny``: an edge longer than nothing and shorter than TINY: a point the
  variable font's alignment left off its neighbour, or a sliver the
  polish missed.
* ``pinch``: a vertex within PINCH breaks of a part of its contour it is
  not on: ink or white narrower than the design draws anywhere, a
  cluster of points that should be one.

Checked on the built variable fonts (``python -m arris.topology
build/Arris[GRAD,WTCH,wght].ttf ...``), at every glyph's own masters
and halfway between neighbouring ones on each axis (every fault), and
along the weight every ten units at five grades and three watches
(crossings, the fault that flickers), and on the engine's drawings
(``--drawings``) at the heavy corners of the design space. The report
names each glyph's faults with where they are; ``--json`` keeps them all
for diffing builds.
"""
from __future__ import annotations

import json
import math
import sys
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass, field
from itertools import pairwise, product
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from fontTools.ttLib import TTFont
from fontTools.varLib.iup import iup_delta
from fontTools.varLib.models import supportScalar
from shapely.geometry import LinearRing, LineString
from shapely.ops import polygonize, unary_union

from . import italic as IT
from .instances import params
from .params import Params

HAIRPIN = 165.0   # degrees: a turn sharper than this at a vertex is a fold or a spike (the design's sharpest, a 2:1 diagonal into a stem, N's, is 153.4; a fold is 175 and over)
TINY = 1.0        # font units: an edge shorter than this, and not nothing, is a point off its neighbour
SAME = 0.25       # font units: points this near are one (a master's peak in F2Dot14 leaves a scalar of 0.9999)
PINCH = 0.35      # breaks: ink or white narrower than this between parts of one contour that do not meet
LOCAL = 2.0     # breaks: nearer than this along the contour, a vertex and an edge are one corner, not a pinch
SMALL = 4.0       # breaks: a whole contour within this (a counter opening between two masters) is not pinched
AXES = ('wght', 'GRAD', 'WTCH')
RANGE = {'wght': (100.0, 400.0, 900.0), 'GRAD': (-100.0, 0.0, 100.0), 'WTCH': (0.0, 0.0, 100.0)}


@dataclass
class Fault:
    kind: str                 # cross | meet | hairpin | tiny | pinch
    contour: int
    at: int                   # the vertex or edge index (the second contour for meet)
    size: float               # degrees of turn, units of edge or gap
    place: tuple[float, float, float] = (400.0, 0.0, 0.0)


@dataclass
class Report:
    name: str
    faults: list[Fault] = field(default_factory=list)

    def kinds(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for f in self.faults:
            out[f.kind] = out.get(f.kind, 0) + 1
        return out


# --- axes --------------------------------------------------------------------

def normalize(tag: str, v: float) -> float:
    lo, d, hi = RANGE[tag]
    return (v - d) / (d - lo) if v < d else (v - d) / (hi - d) if v > d else 0.0


def denormalize(tag: str, n: float) -> float:
    lo, d, hi = RANGE[tag]
    return d + n * (d - lo) if n < 0 else d + n * (hi - d)


def place_of(loc: dict[str, float]) -> tuple[float, float, float]:
    return tuple(round(denormalize(t, loc.get(t, 0.0)), 2) for t in AXES)  # type: ignore[return-value]


# --- the variable font, a glyph at a time ------------------------------------

class Variable:
    """A glyph of a variable font: its default outline and its variations,
    placeable anywhere in the normalized design space (the font's own
    arithmetic: each tuple's scalar at the place, its deltas IUP-filled
    over the outline)."""

    def __init__(self, font: TTFont, name: str):
        glyf = font['glyf']
        g = glyf[name]
        self.name = name
        self.composite = g.isComposite()
        if self.composite:
            self.coords = np.zeros((0, 2)); self.ends: list[int] = []; self.on: list[bool] = []
            self.vars: list[tuple[dict, np.ndarray]] = []
            return
        coords, ends, flags = g.getCoordinates(glyf)
        self.coords = np.array(coords, float).reshape(-1, 2)
        self.ends = list(ends)
        self.on = [bool(f & 1) for f in flags]
        n = len(coords)
        self.vars = []
        for tv in font['gvar'].variations.get(name, []):
            d = list(tv.coordinates)
            if any(c is None for c in d):
                d = iup_delta(d, [tuple(q) for q in coords] + [(0, 0)] * 4, self.ends)
            d = [c or (0, 0) for c in d]
            self.vars.append((dict(tv.axes), np.array(d[:n], float).reshape(-1, 2)))

    def peaks(self, tag: str) -> list[float]:
        """Where this glyph's variations peak on an axis, the default among them."""
        out = {0.0}
        for axes, _ in self.vars:
            if tag in axes:
                out.add(axes[tag][1])
        return sorted(out)

    def at(self, loc: dict[str, float]) -> list[list[tuple[float, float, bool]]]:
        """The contours at a normalized place, as (x, y, on)."""
        pts = self.coords.copy()
        for axes, d in self.vars:
            s = supportScalar(loc, axes)
            if s:
                pts += s * d
        out, start = [], 0
        for e in self.ends:
            out.append([(float(x), float(y), o) for (x, y), o in zip(pts[start:e + 1], self.on[start:e + 1])])
            start = e + 1
        return out


# --- the faults of one outline ------------------------------------------------

def _polyline(contour, italic: bool, sampled: bool = True) -> list[tuple[float, float]]:
    """A contour as a polyline, consecutive duplicates dropped: the italic's
    curves sampled (`sampled`), or its control polygon, every point as it
    is, which has the corners the curves round off (for the tests that
    read the shape of the drawing: a sampled curve is a run of short
    edges and gentle turns, which would read as pinches)."""
    pts = IT.flatten(contour) if sampled and italic and any(not q[2] for q in contour) else [(q[0], q[1]) for q in contour]
    out: list[tuple[float, float]] = []
    for q in pts:
        if not out or math.dist(q, out[-1]) > SAME:
            out.append(q)
    if len(out) > 1 and math.dist(out[0], out[-1]) <= SAME:
        out.pop()
    return out


def _winding(pts: np.ndarray, q) -> int:
    """The winding number of a polygon about a point."""
    a = pts - np.asarray(q, float)
    b = np.roll(a, -1, axis=0)
    ang = np.arctan2(a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0], (a * b).sum(1))
    return round(ang.sum() / (2 * math.pi))


def _wedge(pts: Sequence[tuple[float, float]]) -> float:
    """How much of a self-crossing contour is wrong, in font units: the
    plane cut up along the contour, every piece not wound once the
    contour's own way is wrong (wound backwards: a spike of ink; not at
    all, inside the body: a sliver of white; twice: a fold), and the size
    is the side of a square of the largest such piece's area (a hairline
    fold along an edge, long and nothing wide, counts for little). A
    crossing at a junction between two lobes leaves both lobes right and
    only the fold wrong."""
    P = np.asarray(pts, float)
    area = 0.5 * float((P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1]).sum())
    own = 1 if area > 0 else -1
    try:
        faces = list(polygonize(unary_union(LineString([*pts, pts[0]]))))
    except Exception:  # noqa: BLE001
        return 0.0
    worst = 0.0
    for face in faces:
        if face.area <= 1e-9:
            continue
        if _winding(P, face.representative_point().coords[0]) == own:
            continue
        worst = max(worst, math.sqrt(face.area))
    return worst


def _merged(pts: Sequence[tuple[float, float]], within: float) -> list[tuple[float, float]]:
    """The polyline with runs of points within `within` of each other merged
    to their first, so a tiny edge does not also count as a hairpin."""
    out: list[tuple[float, float]] = []
    for q in pts:
        if not out or math.dist(q, out[-1]) > within:
            out.append(q)
    while len(out) > 1 and math.dist(out[0], out[-1]) <= within:
        out.pop()
    return out


def _turns(pts: Sequence[tuple[float, float]]) -> list[float]:
    """The turn at each vertex, in degrees: 0 straight on, 180 doubling back."""
    n = len(pts)
    out = []
    for i in range(n):
        a, b, c = pts[i - 1], pts[i], pts[(i + 1) % n]
        u, v = (b[0] - a[0], b[1] - a[1]), (c[0] - b[0], c[1] - b[1])
        lu, lv = math.hypot(*u), math.hypot(*v)
        if lu < 1e-9 or lv < 1e-9:
            out.append(0.0)
            continue
        cos = max(-1.0, min(1.0, (u[0] * v[0] + u[1] * v[1]) / (lu * lv)))
        out.append(math.degrees(math.acos(cos)))
    return out


def _pinches(pts: Sequence[tuple[float, float]], gap: float, local: float = 0.0) -> list[tuple[int, int, float]]:
    """(vertex, edge, distance) for every vertex nearer than `gap` to an edge
    of its contour it is not an end of, nor next to, nor within `local` of
    along the contour: a vertex that near its edge the short way round is
    the corner the two make (a notch's flanks closing to their tip, the end
    chamfers of a stroke barely two breaks thick), not two parts of the
    letter meeting."""
    n = len(pts)
    if n < 4:
        return []
    P = np.asarray(pts, float)
    A = P
    B = np.roll(P, -1, axis=0)
    AB = B - A
    L2 = np.maximum((AB ** 2).sum(1), 1e-12)
    # distance from every vertex to every edge
    PA = P[:, None, :] - A[None, :, :]
    t = np.clip((PA * AB[None, :, :]).sum(2) / L2[None, :], 0.0, 1.0)
    proj = A[None, :, :] + t[:, :, None] * AB[None, :, :]
    D = np.sqrt(((P[:, None, :] - proj) ** 2).sum(2))
    idx = np.arange(n)
    # a vertex is an end of edges i-1 and i (the next edges along stand at
    # least a chamfer's height off it in any drawing: no need to spare them)
    for k in (-1, 0):
        D[idx, (idx + k) % n] = np.inf
    if local:
        cum = np.concatenate([[0.0], np.cumsum(np.sqrt(L2))])
        total = cum[-1]
        fwd = (cum[None, :n] - cum[:n, None]) % total        # along the contour, vertex i forward to vertex j
        walk = np.minimum(fwd, total - fwd)                   # the shorter way round
        D[np.minimum(walk, np.roll(walk, -1, axis=1)) < local] = np.inf   # to edge j: its start or its end
    near = np.argwhere(D < gap)
    return [(int(i), int(j), float(D[i, j])) for i, j in near]


def faults(contours, c: float, italic: bool = False, every: bool = True, tiny: bool = True) -> list[Fault]:
    """The faults of one glyph's contours ((x, y, on) or (x, y)), c the break
    at that place. `every` False tests crossings alone (the dense sweep);
    `tiny` False leaves tiny edges out (a variable font's collapsed points
    open between its masters by design)."""
    out: list[Fault] = []
    polys = [_polyline(k, italic) for k in contours]
    rings = []
    for i, pts in enumerate(polys):
        if len(pts) < 3:
            continue
        lr = LinearRing(pts)
        if not lr.is_simple:
            out.append(Fault('cross', i, 0, round(_wedge(pts), 2)))
        rings.append((i, lr))
    for a in range(len(rings)):
        for b in range(a + 1, len(rings)):
            ra, rb = rings[a][1], rings[b][1]
            ba, bb = ra.bounds, rb.bounds
            if ba[2] < bb[0] or bb[2] < ba[0] or ba[3] < bb[1] or bb[3] < ba[1]:
                continue
            if ra.intersects(rb):
                out.append(Fault('meet', rings[a][0], rings[b][0], 0.0))
    if not every:
        return out
    for i, k in enumerate(contours):
        pts = _polyline(k, italic, sampled=False)
        n = len(pts)
        if n < 3:
            continue
        if tiny:
            for k in range(n):
                d = math.dist(pts[k], pts[(k + 1) % n])
                if d < TINY:
                    out.append(Fault('tiny', i, k, round(d, 3)))
        coarse = _merged(pts, TINY)
        if len(coarse) < 3:
            continue
        for k, turn in enumerate(_turns(coarse)):
            if turn > HAIRPIN:
                out.append(Fault('hairpin', i, k, round(turn, 1)))
        xs, ys = [q[0] for q in coarse], [q[1] for q in coarse]
        if max(max(xs) - min(xs), max(ys) - min(ys)) <= SMALL * c:
            continue                                 # a whole small contour: a counter opening, not a pinch
        for v, e, d in _pinches(coarse, PINCH * c, LOCAL * c):
            out.append(Fault('pinch', i, v, round(d, 2)))
    return out


# --- scanning a variable font -------------------------------------------------

def _mid(values: Sequence[float]) -> list[float]:
    out = list(values)
    out += [(a + b) / 2 for a, b in pairwise(values)]
    return sorted(set(out))


DENSE_WGHT = [round(-1 + k * 0.025, 4) for k in range(81)]          # every ten units of weight
DENSE_GRAD = [-1.0, -0.5, 0.0, 0.5, 1.0]
DENSE_WTCH = [0.0, 0.5, 1.0]

_FONT: TTFont | None = None
_ITALIC = False


def _open(path: str, italic: bool) -> None:
    global _FONT, _ITALIC
    _FONT, _ITALIC = TTFont(path), italic


def _break(loc: dict[str, float], italic: bool) -> float:
    w, g, x = place_of(loc)
    p: Params = params(round(w), round(g), watch=x / 100)
    return (IT.italic(p) if italic else p).c


def _scan_glyph(name: str) -> Report:
    assert _FONT is not None
    v = Variable(_FONT, name)
    rep = Report(name)
    if v.composite or not v.ends:
        return rep
    # every fault at the glyph's masters and halfway between them
    grid = [_mid([max(-1.0, min(1.0, q)) for q in v.peaks(t)] + ([-1.0, 1.0] if t == 'wght' else [1.0] if t == 'WTCH' else [-1.0, 1.0])) for t in AXES]
    seen: set[tuple] = set()
    for w, g, x in product(*grid):
        loc = {'wght': w, 'GRAD': g, 'WTCH': x}
        key = place_of(loc)
        seen.add(key)
        for f in faults(v.at(loc), _break(loc, _ITALIC), _ITALIC, every=True, tiny=False):
            f.place = key
            rep.faults.append(f)
    # crossings along the weight, densely
    for w, g, x in product(DENSE_WGHT, DENSE_GRAD, DENSE_WTCH):
        loc = {'wght': w, 'GRAD': g, 'WTCH': x}
        key = place_of(loc)
        if key in seen:
            continue
        for f in faults(v.at(loc), 0.0, _ITALIC, every=False):
            f.place = key
            rep.faults.append(f)
    return rep


def scan_font(path: str | Path, names: Iterable[str] | None = None, procs: int = 4) -> list[Report]:
    """Every simple glyph of a variable font (composites take their bases'
    outlines), its faults at its masters, between them, and along the weight."""
    path = str(path)
    font = TTFont(path)
    italic = 'italic' in Path(path).name.lower() or bool(font['post'].italicAngle)
    if names is None:
        glyf = font['glyf']
        names = [n for n in font.getGlyphOrder() if not glyf[n].isComposite() and glyf[n].numberOfContours > 0]
    names = list(names)
    if procs <= 1:
        _open(path, italic)
        return [_scan_glyph(n) for n in names]
    with Pool(procs, initializer=_open, initargs=(path, italic)) as pool:
        return pool.map(_scan_glyph, names, chunksize=8)


# --- scanning the drawings -----------------------------------------------------

HEAVY: list[tuple[float, float, float]] = [(w, g, x) for w in (700, 800, 850, 900) for g in (-100, 0, 100) for x in (0, 100)] + \
    [(100, g, x) for g in (-100, 0, 100) for x in (0, 100)]
STYLE = ['upright']


def _init_drawings(style: str) -> None:
    import arris.glyphs  # noqa: F401  (the registry)
    STYLE[0] = style


def _scan_drawing(args) -> Report:
    from .font import place
    name, places = args
    rep = Report(name)
    for w, g, x in places:
        p = params(int(w), int(g), watch=x / 100)
        italic = STYLE[0] == 'italic'
        if italic:
            p = IT.italic(p)
        try:
            rings, _ = place(name, p)
        except Exception:  # noqa: BLE001, S112  (a drawing that fails is a finding of the skeleton check)
            continue
        contours = rings if italic else [[(q[0], q[1], True) for q in r] for r in rings]
        for f in faults(contours, p.c, italic, every=True):
            f.place = (float(w), float(g), float(x))
            rep.faults.append(f)
    return rep


def scan_drawings(names: Iterable[str], style: str, places: Sequence[tuple[float, float, float]] | None = None,
                  procs: int = 4) -> list[Report]:
    """Every drawing at the places (HEAVY by default), in one style."""
    places = HEAVY if places is None else list(places)
    jobs = [(n, places) for n in names]
    if procs <= 1:
        _init_drawings(style)
        return [_scan_drawing(j) for j in jobs]
    with Pool(procs, initializer=_init_drawings, initargs=(style,)) as pool:
        return pool.map(_scan_drawing, jobs, chunksize=4)


# --- the report ------------------------------------------------------------------

def _runs(places: Iterable[tuple[float, float, float]]) -> list[str]:
    """Faulty weights along each (grade, watch) line, as runs: '700-900 at +100/100'."""
    lines: dict[tuple[float, float], list[float]] = {}
    for w, g, x in places:
        lines.setdefault((g, x), []).append(w)
    out = []
    for (g, x), ws in sorted(lines.items()):
        ws = sorted(set(ws))
        runs, start, prev = [], ws[0], ws[0]
        for w in ws[1:]:
            if w - prev > 12.6:
                runs.append((start, prev)); start = w
            prev = w
        runs.append((start, prev))
        span = ', '.join(f'{a:.0f}' if a == b else f'{a:.0f}-{b:.0f}' for a, b in runs)
        out.append(f'{span} at {g:+.0f}/{x:.0f}')
    return out


def report(reports: list[Report], out=sys.stdout, limit: int = 40) -> None:
    bad = [r for r in reports if r.faults]
    kinds: dict[str, int] = {}
    for r in bad:
        for k, n in r.kinds().items():
            kinds[k] = kinds.get(k, 0) + n
    print(f'{len(reports)} glyphs; {len(bad)} with a fault: ' + ', '.join(f'{k} {n}' for k, n in sorted(kinds.items())), file=out)
    wedge = lambda r: max((f.size for f in r.faults if f.kind == 'cross'), default=0.0)
    print(f'crossing wedges: {sum(1 for r in bad if wedge(r) >= 10)} glyphs reach 10 units or more, '
          f'{sum(1 for r in bad if 2 <= wedge(r) < 10)} between 2 and 10, {sum(1 for r in bad if 0 < wedge(r) < 2)} under 2', file=out)
    bad.sort(key=lambda r: (-wedge(r), -len(r.faults)))
    for r in bad[:limit]:
        print(f'{r.name}  (wedge {wedge(r):.1f})', file=out)
        by: dict[str, list[Fault]] = {}
        for f in r.faults:
            by.setdefault(f.kind, []).append(f)
        for k, fs in sorted(by.items()):
            worst = max(fs, key=lambda f: f.size) if k in ('hairpin', 'cross') else min(fs, key=lambda f: f.size)
            print(f'    {k:7s} {len(fs):4d}  ' + '; '.join(_runs(f.place for f in fs))
                  + f'  (contour {worst.contour}, {worst.size} at {worst.place[0]:.0f}/{worst.place[1]:+.0f}/{worst.place[2]:.0f})', file=out)
    if len(bad) > limit:
        print(f'... and {len(bad) - limit} more glyphs', file=out)


def dump(reports: list[Report], path: str | Path) -> None:
    Path(path).write_text(json.dumps({r.name: [asdict(f) for f in r.faults] for r in reports if r.faults}))


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    procs = 4
    if '--procs' in args:
        i = args.index('--procs'); procs = int(args[i + 1]); del args[i:i + 2]
    out_json = None
    if '--json' in args:
        i = args.index('--json'); out_json = args[i + 1]; del args[i:i + 2]
    names = None
    if '--glyphs' in args:
        i = args.index('--glyphs'); names = args[i + 1].split(','); del args[i:i + 2]
    reports: list[Report] = []
    if '--drawings' in args:
        args.remove('--drawings')
        from .skeleton import default_names
        styles = [s for s in ('upright', 'italic') if f'--{s}' in args] or ['upright', 'italic']
        for st in styles:
            print(f'== drawings, {st}, at {len(HEAVY)} places')
            reps = scan_drawings(names or default_names(), st, procs=procs)
            report(reps)
            reports += [Report(f'{r.name} {st}', r.faults) for r in reps]
    for path in [a for a in args if not a.startswith('--')]:
        print(f'== {Path(path).name}')
        reps = scan_font(path, names, procs=procs)
        report(reps)
        reports += [Report(f'{r.name} {Path(path).stem}', r.faults) for r in reps]
    if out_json:
        dump(reports, out_json)
    return 1 if any(r.faults for r in reports) else 0


if __name__ == '__main__':
    sys.exit(main())
