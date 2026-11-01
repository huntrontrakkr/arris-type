"""Skeleton fidelity: whether the ink keeps the drawing's intent at every weight.

A glyph is drawn as strokes, polylines of typed nodes (geom.Stroke): a bowl
corner turns roundly, a plain corner sharply, an end is free or runs into
another stroke. That skeleton is the letter; weight is an offset of it, and
toward Black the offset grows past the size of a feature and eats it: a
tail shorter than its corner's chamfer, a drop as wide as the foot it hangs
from, two beaks meeting across a small capital. The engine's rules (the
corner rule, the jog cleanup, the italic's curves) each decide locally what
to do then, and 1.005 showed the cost: the h's foot curved at Regular, was
cut straight at Bold and curved again at Black.

This module reads the features off the skeleton and tests each against the
finished ink at every place along an axis line:

* ``body``   ink along each stroke segment's centreline
* ``side``   white beside each segment, clear of its own corners and of
             the other strokes it meets
* ``corner`` each bowl corner present: both its chamfers found on the ink
             and turning as a corner, and in the italic curved, not held
* ``end``    each free end still free, with ink up to it
* ``holes``  the counters, counted
* ``parts``  the pieces of ink, counted

A feature may be lost toward Black, once. Lost and regained along a line is
a fault, whatever the shapes look like at either end; so is a counter that
appears (two strokes meeting) or a piece of ink that vanishes (two merging)
with weight. ``survey`` runs glyphs over the lines; ``report`` names the
faults; the JSON holds every feature's survival for diffing one build
against another.

    python -m arris.skeleton                  every letter and figure, both styles
    python -m arris.skeleton h l uni04A6      a few
    python -m arris.skeleton --italic --quick the italic on the weight axis alone
    python -m arris.skeleton --json out.json
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from itertools import pairwise
from multiprocessing import Pool

import shapely
from shapely.geometry import Point, Polygon, box

from . import italic as IT
from .draw import REGISTRY, _thickness, draw
from .geom import MIN_COUNTER, rings_to_shapely, stroke_polygon
from .instances import params
from .params import Params, outer_leg

MARGIN = 1.5      # corner breaks: how far past a stroke's edge the white beside it is read
JUNCTION = 3.0    # corner breaks: how near another stroke's ink the white beside a segment is not read
EARLY = 500       # a feature lost under this weight is listed: weight should take features toward Black, not before
STEP = 1.0        # corner breaks: the spacing of probes along a segment
MOST = 12         # probes along one segment at most

Place = tuple[int, int, int]        # weight, grade, watch (0 or 100)

# The axis lines a glyph is followed along: the weight at grade 0 and watch 0,
# finely; and at grade -100, grade +100 and watch 100, by hundreds.
LINES: dict[str, list[Place]] = {
    'g0/w0': [(w, 0, 0) for w in range(100, 901, 50)],
    'g-100': [(w, -100, 0) for w in range(100, 901, 100)],
    'g+100': [(w, 100, 0) for w in range(100, 901, 100)],
    'w100': [(w, 0, 100) for w in range(100, 901, 100)],
}
QUICK: dict[str, list[Place]] = {'g0/w0': [(w, 0, 0) for w in range(100, 901, 100)]}


@dataclass(frozen=True)
class Probe:
    """One feature's test: points that must be ink, points that must be white."""
    label: str
    inside: tuple[tuple[float, float], ...] = ()
    outside: tuple[tuple[float, float], ...] = ()


@dataclass
class Survival:
    """A glyph's features along one line: label -> one character a place
    ('1' kept, '0' lost, '-' not readable there), and the counts."""
    features: dict[str, str] = field(default_factory=dict)
    holes: list[int] = field(default_factory=list)
    parts: list[int] = field(default_factory=list)


def _unit(v):
    n = math.hypot(*v)
    return (v[0] / n, v[1] / n) if n > 1e-9 else None


def probes(g, p: Params) -> list[Probe]:
    """The body, side and end probes of a drawn glyph's strokes, in the
    drawing's own frame (before the optical warp and the italic's shear)."""
    th = _thickness(p, g.sh)
    c = p.c
    clip = box(*g.clip) if g.clip is not None else None
    inner_clip = clip.buffer(-c) if clip is not None else None
    raw = [stroke_polygon(s, th, c) for s in g.strokes]
    extra = [e for e in g.extra if not e.is_empty]
    beside = []
    for i in range(len(raw)):
        parts = [q for j, q in enumerate(raw) if j != i] + extra
        beside.append(shapely.union_all(parts).buffer(JUNCTION * c) if parts else None)
    out: list[Probe] = []

    def readable(q):
        return inner_clip is None or inner_clip.covers(Point(q))

    def width(nodes, k):
        n = len(nodes)
        a, b = nodes[k % n], nodes[(k + 1) % n]
        return a.w if a.w is not None else th((b.x - a.x, b.y - a.y))

    for i, s in enumerate(g.strokes):
        nodes = s.nodes
        n = len(nodes)
        segs = list(range(n if s.closed else n - 1))
        for k in segs:
            a, b = nodes[k], nodes[(k + 1) % n]
            d = (b.x - a.x, b.y - a.y)
            u = _unit(d)
            if u is None:
                continue
            L = math.hypot(*d)
            nv = (-u[1], u[0])
            w = width(nodes, k)
            # how far from each end the segment is read: past the neighbouring
            # segment's own ink (half its thickness) and the corner's break, or
            # past a bowl's outer chamfer (its centreline leg and the stroke's
            # share), which the italic's curve inside a bend stays within
            reach = []
            for nd, adj in ((a, k - 1), (b, k + 1)):
                has_adj = s.closed or 0 <= adj < n - 1
                r = (width(nodes, adj) / 2 if has_adj else 0.0) + 2 * c
                if nd.bowl and has_adj:
                    r = max(r, nd.bowl + outer_leg(p) - p.leg + 2 * c)
                reach.append(r)
            s0, s1 = reach[0], L - reach[1]
            if s1 - s0 >= c:
                count = max(3, min(MOST, int((s1 - s0) / (STEP * c)) + 1))
                ts = [s0 + (s1 - s0) * t / (count - 1) for t in range(count)]
                centre = [(a.x + u[0] * t, a.y + u[1] * t) for t in ts]
                body = tuple(q for q in centre if readable(q))
                if body:
                    out.append(Probe(f'body:{i}:{k}', inside=body))
                off = w / 2 + MARGIN * c
                for side, sign in (('L', 1), ('R', -1)):
                    pts = [(q[0] + sign * nv[0] * off, q[1] + sign * nv[1] * off) for q in centre]
                    pts = [q for q in pts if readable(q) and (beside[i] is None or not beside[i].covers(Point(q)))]
                    if pts:
                        out.append(Probe(f'side:{i}:{k}:{side}', outside=tuple(pts)))
        if s.closed or n < 2:
            continue
        for which, e, nxt in (('start', nodes[0], nodes[1]), ('end', nodes[-1], nodes[-2])):
            u = _unit((nxt.x - e.x, nxt.y - e.y))          # into the stroke
            if u is None:
                continue
            tip = (e.x, e.y)
            if beside[i] is not None and beside[i].covers(Point(tip)):
                continue                                    # runs into another stroke: a junction, not an end
            if not readable(tip):
                continue                                    # cut by the body: not an end either
            inside = (tip[0] + u[0] * 2 * c, tip[1] + u[1] * 2 * c)
            outside = (tip[0] - u[0] * MARGIN * c, tip[1] - u[1] * MARGIN * c)
            out.append(Probe(f'end:{i}:{which}', inside=(inside,), outside=(outside,)))
    return out


def _ink(g, p: Params):
    """(the finished ink as a shapely geometry, rings, record) in the
    drawing's frame: the upright's rings before the optical warp, the
    italic's curves before the warp and the shear."""
    g = copy.copy(g)
    g.warp = None
    rings, rec = g.outline(record=True)
    rec, _ = IT.split_warp(rec)
    if p.slant:
        contours = IT.curve_rings(rings, p, rec)
        poly = rings_to_shapely([IT.flatten(ct, 8) for ct in contours])
    else:
        poly = rings_to_shapely(rings)
    return poly, rings, rec


def corners(g, rings, rec, p: Params) -> dict[str, bool]:
    """Each bowl corner, named for its node (``corner:stroke:node``; a
    stamped glyph's, ``stamp:n``): present when its outer chamfer is found
    on the ink turning as a corner, and in the italic curved, not held. (The
    record lists a stroke's bowls in node order, the stamped glyphs' after:
    geom._expand, Glyph.add_glyph.)"""
    own = [(i, k) for i, s in enumerate(g.strokes) for k, nd in enumerate(s.nodes)
           if nd.bowl > 0 and (s.closed or 0 < k < len(s.nodes) - 1)]
    labels = {}
    for n, idx in enumerate(idx for idx, r in enumerate(rec) if r[0] == 'bowl'):
        if n < len(own):
            labels[idx] = f'corner:{own[n][0]}:{own[n][1]}'
        elif p.slant:
            # a stamped glyph's corners: exact in the italic, which curves them;
            # the upright stamps them warped, off the 45 degrees the record
            # names, and they are that glyph's own to check
            labels[idx] = f'stamp:{n - len(own)}'
    segs = IT._segments(rings, rec)
    found: dict[int, list] = {}
    for s in segs:
        if s[2][0] == 'bowl':
            found.setdefault(s[2][1], []).append(s)
    held: set = set()
    if p.slant:
        if hasattr(IT, '_plan'):
            curved, _ = IT._plan(rings, p, rec)
            held = {idx for idx, ss in found.items() if not any((s[0], s[1]) in curved for s in ss)}
        else:                                               # 1.005's rule, for comparing builds
            held = {idx for idx, ss in found.items() if any(not s[3] for s in ss)}
    out = {}
    for idx, lab in labels.items():
        outer = [s for s in found.get(idx, []) if s[4]]
        out[lab] = bool(outer) and all((s[5] if len(s) > 5 else s[3]) for s in outer) and idx not in held
    return out


def read(name: str, place: Place) -> tuple[dict[str, bool], int, int]:
    """One glyph at one place: feature -> kept, the holes, the parts."""
    w, grad, watch = place
    p = params(w, grad, watch=watch / 100)
    if STYLE[0] == 'italic':
        p = IT.italic(p)
    g = draw(name, p)
    poly, rings, rec = _ink(g, p)
    kept: dict[str, bool] = {}
    for pr in probes(g, p):
        ok = all(poly.covers(Point(q)) for q in pr.inside) and not any(poly.covers(Point(q)) for q in pr.outside)
        kept[pr.label] = ok
    kept.update(corners(g, rings, rec, p))
    # counters and pieces of ink, as the engine counts them: a hole smaller
    # than a counter can be is none (geom.MIN_COUNTER), nor is a sliver where
    # two sampled curves touch; a piece smaller than a break's square is none
    least = (MIN_COUNTER * p.sv) ** 2
    geoms = [q for q in getattr(poly, 'geoms', [poly]) if not q.is_empty and q.area > p.c ** 2]
    holes = sum(1 for q in geoms for h in q.interiors if Polygon(h).area >= least)
    return kept, holes, len(geoms)


STYLE = ['upright']     # set in each worker: 'upright' or 'italic'


def _init(style):
    import arris.glyphs  # noqa: F401  (the registry)
    STYLE[0] = style


def _one(args):
    name, lines = args
    out: dict[str, Survival] = {}
    for line, places in lines.items():
        sv = Survival()
        rows = []
        for pl in places:
            try:
                kept, holes, parts = read(name, pl)
            except Exception as e:                           # noqa: BLE001  (a drawing that fails is a finding)
                kept, holes, parts = {'error': False}, -1, -1
                sv.features.setdefault('error', '')
                sv.features['error'] += 'E'
                rows.append({})
                sv.holes.append(holes)
                sv.parts.append(parts)
                sv.features.setdefault('error:' + type(e).__name__, '')
                continue
            rows.append(kept)
            sv.holes.append(holes)
            sv.parts.append(parts)
        labels = sorted({k for r in rows for k in r})
        for lab in labels:
            sv.features[lab] = ''.join('-' if lab not in r else ('1' if r[lab] else '0') for r in rows)
        out[line] = sv
    return name, out


def survey(names: Iterable[str], style: str, lines: dict[str, list[Place]] | None = None,
           procs: int = 4) -> dict[str, dict[str, Survival]]:
    """Every glyph's survival along the lines, in one style."""
    lines = LINES if lines is None else lines
    names = list(names)
    jobs = [(n, lines) for n in names]
    if procs <= 1:
        _init(style)
        return dict(_one(j) for j in jobs)
    with Pool(procs, initializer=_init, initargs=(style,)) as pool:
        return dict(pool.map(_one, jobs, chunksize=4))


def faults(sv: Survival, places: list[Place]) -> list[str]:
    """What is wrong along one line: a feature lost and regained, a counter
    appearing, a piece of ink vanishing, a drawing that failed."""
    out = []
    for lab, s in sv.features.items():
        if lab.startswith('error'):
            out.append(lab)
            continue
        seen_lost = False
        for ch, pl in zip(s, places):
            if ch == '0':
                seen_lost = True
            elif ch == '1' and seen_lost:
                out.append(f'{lab} regained at {pl[0]}: {s}')
                break
    for kind, seq, bad in (('holes', sv.holes, lambda a, b: b > a), ('parts', sv.parts, lambda a, b: b < a)):
        for (a, b), pl in zip(pairwise(seq), places[1:]):
            if a >= 0 and b >= 0 and bad(a, b):
                out.append(f'{kind} {a}->{b} at {pl[0]}')
                break
    return out


def losses(sv: Survival, places: list[Place]) -> list[str]:
    """Features lost along one line (once, toward Black): where."""
    out = []
    for lab, s in sv.features.items():
        if '0' in s and '1' in s and s.index('0') > 0 and s.rfind('1') < s.index('0'):
            out.append(f'{lab} lost from {places[s.index("0")][0]}')
    return out


def report(results: dict[str, dict[str, dict[str, Survival]]], lines: dict[str, list[Place]], out=sys.stdout):
    """results: style -> name -> line -> Survival. Prints the faults per
    glyph and a summary; returns the number of glyphs with faults."""
    bad = 0
    lost_count = early_count = 0
    for style, per in results.items():
        for name in sorted(per):
            fl, early = [], []
            for line, sv in per[name].items():
                fl += [f'{line}: {f}' for f in faults(sv, lines[line])]
                for lo in losses(sv, lines[line]):
                    lost_count += 1
                    if int(lo.rsplit(' ', 1)[1]) < EARLY:
                        early.append(f'{line}: {lo}')
            early_count += len(early)
            if fl or early:
                bad += bool(fl)
                print(f'{name} {style}', file=out)
                for f in fl:
                    print(f'    FAULT {f}', file=out)
                for e in early:
                    print(f'    early {e}', file=out)
    n = sum(len(per) for per in results.values())
    print(f'\n{n} glyph-styles; {bad} with a fault (a feature lost and regained, a counter that appears, '
          f'ink that merges); {lost_count} features lost toward Black, {early_count} of them under {EARLY}',
          file=out)
    return bad


def default_names() -> list[str]:
    """Letters and figures: Latin, Latin extended, Greek, Cyrillic."""
    import arris.glyphs  # noqa: F401
    return [n for n, s in REGISTRY.items() if not n.endswith('.ital') and s.unicode and not s.cell and (
        0x30 <= s.unicode <= 0x39 or 0x41 <= s.unicode <= 0x5A or 0x61 <= s.unicode <= 0x7A
        or 0xC0 <= s.unicode <= 0x24F or 0x391 <= s.unicode <= 0x3C9 or 0x400 <= s.unicode <= 0x4FF)]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('names', nargs='*', help='glyph names (default: every letter and figure)')
    ap.add_argument('--upright', action='store_true', help='the upright only')
    ap.add_argument('--italic', action='store_true', help='the italic only')
    ap.add_argument('--quick', action='store_true', help='the weight axis alone, by hundreds')
    ap.add_argument('--json', help='write every feature\'s survival here')
    ap.add_argument('--procs', type=int, default=4)
    a = ap.parse_args(argv)
    import arris.glyphs  # noqa: F401
    names = a.names or default_names()
    styles = ['upright', 'italic']
    if a.upright != a.italic:
        styles = ['upright'] if a.upright else ['italic']
    lines = QUICK if a.quick else LINES
    results = {st: survey(names, st, lines, a.procs) for st in styles}
    if a.json:
        dump = {st: {n: {ln: {'features': sv.features, 'holes': sv.holes, 'parts': sv.parts}
                         for ln, sv in per[n].items()} for n in per} for st, per in results.items()}
        with open(a.json, 'w') as f:
            json.dump({'lines': {k: v for k, v in lines.items()}, 'results': dump}, f)
    return 1 if report(results, lines) else 0


if __name__ == '__main__':
    sys.exit(main())
