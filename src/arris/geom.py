"""Stroke geometry: centrelines in, ink polygons out.

A glyph is drawn as strokes: polylines along a centreline. Each segment is
offset by half its thickness, and a segment's thickness depends only on its
direction, so horizontals, verticals and diagonals can carry different weights.
A node may be a *bowl* corner: the centreline is chamfered there by a leg
length, which yields the octagonal bowls. Ends are capped flat (perpendicular),
or cut horizontally or vertically through the end point.

The union of the strokes then gets the one rule inherited from the pixel
figures, applied to the whole outline: every right-angled corner is replaced
by a 45-degree chord of leg ``c``, cutting convex corners and filling concave
ones. Acute corners (a diagonal cut by a horizontal or vertical cap) are
truncated perpendicular to the diagonal by a chord of the same length.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import shapely
from shapely.geometry import Polygon, MultiPolygon
from shapely.geometry.polygon import orient
from shapely.validation import explain_validity

EPS = 1e-7


@dataclass(frozen=True)
class Node:
    x: float
    y: float
    bowl: float = 0.0  # centreline chamfer leg at this node; 0 = plain corner
    w: float | None = None  # thickness of the segment leaving this node (None: by direction)


@dataclass(frozen=True)
class Stroke:
    nodes: tuple[Node, ...]
    closed: bool = False
    start: str = 'flat'  # cap at the first node: 'flat', 'h' or 'v'
    end: str = 'flat'


def _sub(a, b): return (a[0] - b[0], a[1] - b[1])
def _add(a, b): return (a[0] + b[0], a[1] + b[1])
def _mul(a, k): return (a[0] * k, a[1] * k)
def _dot(a, b): return a[0] * b[0] + a[1] * b[1]
def _cross(a, b): return a[0] * b[1] - a[1] * b[0]
def _len(a): return math.hypot(a[0], a[1])
def _unit(a):
    n = _len(a)
    if n < EPS:
        raise ValueError('zero-length segment')
    return (a[0] / n, a[1] / n)


def _meet(p1, d1, p2, d2):
    """Intersection of the lines p1 + t d1 and p2 + s d2 (None if parallel)."""
    den = _cross(d1, d2)
    if abs(den) < EPS:
        return None
    t = _cross(_sub(p2, p1), d2) / den
    return _add(p1, _mul(d1, t))


STEEP_DEG = math.degrees(math.atan2(2, 1))   # the 2:1 slope, 63.43 degrees


class Thickness:
    """Stroke thickness (measured perpendicular) as a function of direction.

    Knots: horizontal ``h``, 45 degrees ``d``, the 2:1 slope ``s`` and vertical
    ``v``, linear in angle between them. In the watch's pixel drawings every
    diagonal is a staircase as wide across as a stem, so there ``d`` is
    v*sin(45) and ``s`` is v*sin(63.4).
    """

    def __init__(self, v: float, h: float, d: float, s: float | None = None):
        self.v, self.h, self.d = v, h, d
        self.s = s if s is not None else d + (v - d) * (STEEP_DEG - 45) / 45

    def __call__(self, direction) -> float:
        phi = math.degrees(math.atan2(abs(direction[1]), abs(direction[0])))  # 0 = horizontal
        if phi <= 45:
            return self.h + (self.d - self.h) * phi / 45
        if phi <= STEEP_DEG:
            return self.d + (self.s - self.d) * (phi - 45) / (STEEP_DEG - 45)
        return self.s + (self.v - self.s) * (phi - STEEP_DEG) / (90 - STEEP_DEG)


def _expand(stroke: Stroke):
    """Replace bowl nodes by their two chamfer points. Returns the point list
    and, per bowl, the index of its chamfer segment."""
    nodes = list(stroke.nodes)
    n = len(nodes)
    pts, bowls, widths = [], [], []   # widths[i]: thickness of the segment from pts[i]
    for i, nd in enumerate(nodes):
        p = (nd.x, nd.y)
        interior = stroke.closed or 0 < i < n - 1
        if nd.bowl > 0 and interior:
            prev = nodes[(i - 1) % n]
            nxt = nodes[(i + 1) % n]
            din = _unit(_sub(p, (prev.x, prev.y)))
            dout = _unit(_sub((nxt.x, nxt.y), p))
            a = _sub(p, _mul(din, nd.bowl))
            b = _add(p, _mul(dout, nd.bowl))
            bowls.append(len(pts))
            pts.extend([a, b])
            widths.extend([None, nd.w])
        else:
            pts.append(p)
            widths.append(nd.w)
    return pts, bowls, widths


def _cap_point(p, d, side_pt, kind):
    """Where a side line (through side_pt, direction d) meets the cap at p."""
    if kind == 'flat':
        return _meet(side_pt, d, p, (-d[1], d[0]))
    if kind == 'h':
        return _meet(side_pt, d, p, (1.0, 0.0))
    if kind == 'v':
        return _meet(side_pt, d, p, (0.0, 1.0))
    raise ValueError(f'unknown cap {kind!r}')


def stroke_polygon(stroke: Stroke, thick: Thickness, c: float) -> Polygon:
    """The ink of one stroke. If a stroke's bowl chamfers do not fit inside it
    (very heavy weights), the bowls shrink until they do."""
    try:
        return _stroke_polygon(stroke, thick, c)
    except ValueError:
        if not any(n.bowl for n in stroke.nodes):
            raise
    lo, hi = 0.0, 1.0
    for _ in range(30):
        mid = (lo + hi) / 2
        try:
            _stroke_polygon(_scale_bowls(stroke, mid), thick, c)
            lo = mid
        except ValueError:
            hi = mid
    return _stroke_polygon(_scale_bowls(stroke, lo * 0.98), thick, c)


def _scale_bowls(stroke: Stroke, k: float) -> Stroke:
    return Stroke(tuple(Node(n.x, n.y, n.bowl * k, n.w) for n in stroke.nodes), stroke.closed, stroke.start, stroke.end)


def _stroke_polygon(stroke: Stroke, thick: Thickness, c: float) -> Polygon:
    pts, bowls, widths = _expand(stroke)
    closed = stroke.closed
    m = len(pts)
    nseg = m if closed else m - 1
    segs = []
    for i in range(nseg):
        a, b = pts[i], pts[(i + 1) % m]
        d = _unit(_sub(b, a))
        segs.append((a, d, (widths[i] if widths[i] is not None else thick(d)) / 2))

    def side(sign):
        lines = [(_add(a, _mul((-d[1], d[0]), sign * h)), d) for a, d, h in segs]
        verts = []
        rng = range(nseg) if closed else range(1, nseg)
        for i in rng:
            p1, d1 = lines[i - 1]
            p2, d2 = lines[i]
            q = _meet(p1, d1, p2, d2)
            if q is None:  # collinear continuation
                q = _add(pts[i], _mul((-d2[1], d2[0]), sign * segs[i][2]))
            verts.append(q)
        if not closed:
            (p0, d0), (pn, dn) = lines[0], lines[-1]
            verts.insert(0, _cap_point(pts[0], d0, p0, stroke.start))
            verts.append(_cap_point(pts[-1], dn, pn, stroke.end))
        return verts, lines

    left, llines = side(+1)
    right, rlines = side(-1)

    # Inner side of a bowl: if the offset chamfer is shorter than the edge
    # break (or inverted), use the plain inner corner; the corner rule then
    # fills it with the edge-break chord, so the inner leg never drops below c.
    # verts[i] sits at pts[i] on both sides (caps included for open strokes);
    # bowl k runs from pts[k] to pts[k+1] along segment k.
    for k in bowls:
        din, dout = segs[(k - 1) % nseg][1], segs[(k + 1) % nseg][1]
        verts, lines = (left, llines) if _cross(din, dout) > 0 else (right, rlines)
        (p1, d1), (p2, d2) = lines[(k - 1) % nseg], lines[(k + 1) % nseg]
        corner = _meet(p1, d1, p2, d2)
        if corner is None:
            continue
        if _dot(_sub(corner, verts[k]), din) < c - EPS:
            verts[k] = corner
            verts[(k + 1) % len(verts)] = corner

    if closed:
        rings = [left, right]
        polys = [Polygon(r) for r in rings]
        outer, inner = sorted(polys, key=lambda p: -abs(p.area))
        if not inner.is_valid or not outer.is_valid:
            raise ValueError('counter too small for its bowls')
        poly = Polygon(outer.exterior.coords, [inner.exterior.coords])
    else:
        poly = Polygon(left + right[::-1])
    if not poly.is_valid:
        raise ValueError(f'stroke outline is not simple: {explain_validity(poly)}')
    return poly


def _dir_class(u) -> str:
    ax, ay = abs(u[0]), abs(u[1])
    if ax < 1e-6 or ay < 1e-6:
        return 'axis'
    if abs(ax - ay) < 1e-6:
        return 'diag'
    return 'steep'


def _ring_rule(coords, c, convex_sign):
    """The corner rule on one ring (ink on the left of travel), as the watch's
    pixel rule behaves:

    * a right angle between a horizontal and a vertical edge: a 45-degree chord
      of leg c, cutting it if convex and filling it if concave;
    * a right angle between two 45-degree edges: left sharp (beaks, waists);
    * a 45-degree angle between an axis edge and a 45-degree edge, convex (a
      diagonal's capped end) or concave (a crotch): a chord square to the
      diagonal, reaching c*sqrt2 along it and 2c along the axis edge;
    * a convex corner where a 2:1 edge meets a cap: a chord of leg c;
    * anything else (135-degree turns, the bends of gables): left alone.
    """
    pts = [tuple(p) for p in coords[:-1]]
    # drop duplicate and collinear points
    changed = True
    while changed and len(pts) > 3:
        changed = False
        for i in range(len(pts)):
            a, b, q = pts[i - 1], pts[i], pts[(i + 1) % len(pts)]
            e1, e2 = _sub(b, a), _sub(q, b)
            if _len(e1) < 1e-6 or (abs(_cross(e1, e2)) < 1e-6 * max(_len(e1), 1) * max(_len(e2), 1) and _dot(e1, e2) > 0):
                del pts[i]
                changed = True
                break
    n = len(pts)
    kinds = []
    for i in range(n):
        a, b, q = pts[i - 1], pts[i], pts[(i + 1) % n]
        u1, u2 = _unit(_sub(b, a)), _unit(_sub(q, b))
        turn = math.degrees(math.atan2(_cross(u1, u2), _dot(u1, u2)))  # + = left = convex
        k1, k2 = _dir_class(u1), _dir_class(u2)
        kind = None
        if k1 == k2 == 'axis' and abs(abs(turn) - 90) < 1.0:
            kind = 'right'
        elif {k1, k2} == {'axis', 'diag'} and abs(abs(turn) - 135) < 1.0:
            kind = 'acute'
        elif 'steep' in (k1, k2) and 'diag' not in (k1, k2) and turn > 45:
            kind = 'steep'
        kinds.append(kind)
    out = []
    for i in range(n):
        a, b, q = pts[i - 1], pts[i], pts[(i + 1) % n]
        e_in, e_out = _sub(b, a), _sub(q, b)
        u_in, u_out = _unit(e_in), _unit(e_out)
        k = kinds[i]
        # How much of each adjacent edge this corner may use.
        room_in = _len(e_in) * (0.5 if kinds[i - 1] else 1.0)
        room_out = _len(e_out) * (0.5 if kinds[(i + 1) % n] else 1.0)
        if k in ('right', 'steep'):
            r = min(c, room_in, room_out)
            out += [_sub(b, _mul(u_in, r)), _add(b, _mul(u_out, r))]
        elif k == 'acute':
            leg = c * math.sqrt(2)
            if _dir_class(u_in) == 'diag':
                bb = min(leg, room_in, room_out / math.sqrt(2))
                out += [_sub(b, _mul(u_in, bb)), _add(b, _mul(u_out, bb * math.sqrt(2)))]
            else:
                bb = min(leg, room_out, room_in / math.sqrt(2))
                out += [_sub(b, _mul(u_in, bb * math.sqrt(2))), _add(b, _mul(u_out, bb))]
        else:
            out.append(b)
    # dedupe coincident neighbours
    clean = []
    for p in out:
        if not clean or _len(_sub(p, clean[-1])) > 1e-6:
            clean.append(p)
    if len(clean) > 1 and _len(_sub(clean[0], clean[-1])) < 1e-6:
        clean.pop()
    return clean


def ink(strokes, thick: Thickness, c: float, extra=(), clip=None):
    """Union the strokes (and any extra polygons), intersect with ``clip``
    (a polygon, if given) and apply the corner rule.

    Returns a list of rings (lists of points); exteriors counter-clockwise,
    holes clockwise, ink always on the left of travel."""
    polys = [stroke_polygon(s, thick, c) for s in strokes] + list(extra)
    if not polys:
        return []
    u = shapely.union_all(polys)
    if clip is not None:
        u = u.intersection(clip)
    u = shapely.make_valid(u)
    u = MultiPolygon([g for g in getattr(u, 'geoms', [u]) if isinstance(g, Polygon) and g.area > 1e-9]) \
        if not isinstance(u, Polygon) else u
    if isinstance(u, Polygon):
        u = MultiPolygon([u])
    rings = []
    for poly in u.geoms:
        poly = orient(poly, sign=1.0)
        rings.append(_ring_rule(list(poly.exterior.coords), c, +1))
        for hole in poly.interiors:
            rings.append(_ring_rule(list(hole.coords), c, +1))
    return rings


def rings_to_shapely(rings):
    """Rebuild a (multi)polygon from rings using even-odd containment."""
    polys = [Polygon(r) for r in rings]
    shells = [p for p, r in zip(polys, rings) if _signed_area(r) > 0]
    holes = [p for p, r in zip(polys, rings) if _signed_area(r) < 0]
    out = []
    for s in shells:
        hs = [h.exterior.coords for h in holes if s.contains(h.representative_point())]
        out.append(Polygon(s.exterior.coords, hs))
    return MultiPolygon(out) if len(out) != 1 else out[0]


def _signed_area(r):
    s = 0.0
    for i in range(len(r)):
        x1, y1 = r[i - 1]
        x2, y2 = r[i]
        s += x1 * y2 - x2 * y1
    return s / 2
