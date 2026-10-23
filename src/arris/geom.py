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

    def __init__(self, v: float, h: float, d: float, s: float | None = None, slant: float = 0.0,
                 floor: float = 0.0):
        self.v, self.h, self.d = v, h, d
        self.s = s if s is not None else d + (v - d) * (STEEP_DEG - 45) / 45
        self.slant = slant
        self.floor = floor          # no stroke thinner (instances.STROKE_FLOOR)

    def __call__(self, direction) -> float:
        phi = math.degrees(math.atan2(abs(direction[1]), abs(direction[0])))  # 0 = horizontal
        if phi <= 45:
            w = self.h + (self.d - self.h) * phi / 45
        elif phi <= STEEP_DEG:
            w = self.d + (self.s - self.d) * (phi - 45) / (STEEP_DEG - 45)
        else:
            w = self.s + (self.v - self.s) * (phi - STEEP_DEG) / (90 - STEEP_DEG)
        w = max(w, self.floor)
        if self.slant:
            # The italic shears the finished outline, x += y * slant. A strip of
            # width w along unit direction d comes out w / |S d| wide, so it is
            # drawn |S d| cos(slant) wider: every stroke ends as heavy across as
            # its upright self, times cos(slant) (as a vertical stem does).
            dx, dy = direction
            n = math.hypot(dx, dy) or 1.0
            dx, dy = dx / n, dy / n
            w *= math.hypot(dx + self.slant * dy, dy) / math.sqrt(1 + self.slant ** 2)
        return w


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
            vin, vout = _sub(p, (prev.x, prev.y)), _sub((nxt.x, nxt.y), p)
            din, dout = _unit(vin), _unit(vout)
            # A chamfer can be no longer than the straights it cuts into
            # (half of one shared with another bowl).
            share = lambda j: 0.5 if (nodes[j % n].bowl > 0 and (stroke.closed or 0 < j % n < n - 1)) else 0.95
            leg = min(nd.bowl, _len(vin) * share(i - 1), _len(vout) * share(i + 1))
            a = _sub(p, _mul(din, leg))
            b = _add(p, _mul(dout, leg))
            bowls.append(len(pts))
            pts.extend([a, b])
            widths.extend([None, nd.w])
        else:
            pts.append(p)
            widths.append(nd.w)
    # Two chamfers that use a whole straight between them meet in one point.
    keep = [i for i in range(len(pts))
            if _len(_sub(pts[i], pts[i - 1 if (stroke.closed or i > 0) else i])) > 1e-9 or (i == 0 and not stroke.closed)]
    if len(keep) < len(pts):
        remap = {}
        for new_i, old_i in enumerate(keep):
            remap[old_i] = new_i
        # a bowl's chamfer starts at its first point; if that point was merged
        # into the previous one, the chamfer now starts there
        bowls = [remap.get(b, remap.get(b - 1, 0)) for b in bowls]
        pts = [pts[i] for i in keep]
        widths = [widths[i] for i in keep]
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


def stroke_polygon(stroke: Stroke, thick: Thickness, c: float, rec: list | None = None) -> Polygon:
    """The ink of one stroke. If a stroke's bowl chamfers do not fit inside it
    (very heavy weights), the bowls shrink until they do. ``rec`` collects
    the lines the bowls' chamfer edges lie on (see ``ink``)."""
    try:
        return _stroke_polygon(stroke, thick, c, rec=rec)
    except ValueError:
        if not any(n.bowl for n in stroke.nodes):
            # a stroke thicker than it is long (a short diagonal at the very
            # heaviest settings): repair it and log it
            REPAIRED.append(stroke)
            return _stroke_polygon(stroke, thick, c, repair=True, rec=rec)
    lo, hi = 0.0, 1.0
    for _ in range(30):
        mid = (lo + hi) / 2
        try:
            _stroke_polygon(_scale_bowls(stroke, mid), thick, c)
            lo = mid
        except ValueError:
            hi = mid
    try:
        return _stroke_polygon(_scale_bowls(stroke, lo * 0.98), thick, c, rec=rec)
    except ValueError:
        # Last resort: repair the outline and log the stroke for review, so a
        # crowded extreme (a ligature squeezed into a monospaced cell at Black)
        # degrades instead of failing the build.
        REPAIRED.append(stroke)
        return _stroke_polygon(stroke, thick, c, repair=True, rec=rec)


REPAIRED: list = []


def _scale_bowls(stroke: Stroke, k: float) -> Stroke:
    return Stroke(tuple(Node(n.x, n.y, n.bowl * k, n.w) for n in stroke.nodes), stroke.closed, stroke.start, stroke.end)


def _stroke_polygon(stroke: Stroke, thick: Thickness, c: float, repair: bool = False,
                    rec: list | None = None) -> Polygon:
    pts, bowls, widths = _expand(stroke)
    closed = stroke.closed
    m = len(pts)
    nseg = m if closed else m - 1
    segs = []
    for i in range(nseg):
        a, b = pts[i], pts[(i + 1) % m]
        d = _unit(_sub(b, a))
        w = max(widths[i], thick.floor) if widths[i] is not None else thick(d)
        segs.append((a, d, w / 2))

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
        if repair:
            fixed = shapely.make_valid(poly)
            parts = [g for g in getattr(fixed, 'geoms', [fixed]) if isinstance(g, Polygon)]
            if not parts:
                raise ValueError(f'stroke cannot be drawn: {explain_validity(poly)}')
            poly = max(parts, key=lambda g: g.area)
        else:
            raise ValueError(f'stroke outline is not simple: {explain_validity(poly)}')
    if rec is not None:
        for k in bowls:                                     # a bowl's two chamfer edges, as one corner
            rec.append(('bowl', llines[k], rlines[k]))
    return poly


def _dir_class(u) -> str:
    ax, ay = abs(u[0]), abs(u[1])
    if ax < 1e-6 or ay < 1e-6:
        return 'axis'
    if abs(ax - ay) < 1e-6:
        return 'diag'
    return 'steep'


def _on_butt(a, b, butt) -> bool:
    """Whether the edge a-b lies on one of the butt lines (see ``ink``)."""
    for axis, v in butt:
        k = 0 if axis == 'x' else 1
        if abs(a[k] - v) < BUTT_TOL and abs(b[k] - v) < BUTT_TOL:
            return True
    return False


BUTT_TOL = 1e-6


def _ring_rule(coords, c, convex_sign, rec: list | None = None, butt=()):
    """The corner rule on one ring (ink on the left of travel), as the watch's
    pixel rule behaves:

    * a right angle between a horizontal and a vertical edge: a 45-degree chord
      of leg c, cutting it if convex and filling it if concave;
    * a right angle between two 45-degree edges: left sharp (beaks, waists);
    * a 45-degree angle between an axis edge and a 45-degree edge, convex (a
      diagonal's capped end) or concave (a crotch): a chord square to the
      diagonal, reaching c*sqrt2 along it and 2c along the axis edge;
    * a convex corner where a 2:1 edge meets a cap: a chord of leg c;
    * anything else (135-degree turns, the bends of gables): left alone;
    * a corner on a butt line (``butt``, see ``ink``): left square.
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
        if butt and (_on_butt(a, b, butt) or _on_butt(b, q, butt)):
            kind = None                                     # ink cut square where it meets a butt line
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
            if rec is not None and k == 'right':
                rec.append(('chord', out[-2], out[-1]))
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


def ink(strokes, thick: Thickness, c: float, extra=(), clip=None, rec: list | None = None, butt=()):
    """Union the strokes (and any extra polygons), intersect with ``clip``
    (a polygon, if given) and apply the corner rule.

    ``butt``: lines, ('x', value) or ('y', value), where the ink must meet
    its neighbour flush (a terminal cell's edges): a corner with an edge on
    one of them is left square, so a line or a block joins the next cell's
    without a notch.

    Returns a list of rings (lists of points); exteriors counter-clockwise,
    holes clockwise, ink always on the left of travel. ``rec``, if given,
    collects where the outline's chamfers came from: ('line', point,
    direction) for the lines a bowl's chamfer edges lie on, ('chord', a, b)
    for the corner rule's edge breaks on right angles. The italic curves
    exactly these (``arris.italic``)."""
    polys = [stroke_polygon(s, thick, c, rec) for s in strokes] + list(extra)
    if not polys:
        return []
    u = shapely.union_all(polys)
    if clip is not None:
        u = u.intersection(clip)
    u = shapely.make_valid(u)
    if not butt:
        u = _fill_slits(u, SLIT * c)
    u = MultiPolygon([g for g in getattr(u, 'geoms', [u]) if isinstance(g, Polygon) and g.area > 1e-9]) \
        if not isinstance(u, Polygon) else u
    if isinstance(u, Polygon):
        u = MultiPolygon([u])
    rings = []
    min_hole = (MIN_COUNTER * thick.v) ** 2
    moved: dict = {}
    for poly in u.geoms:
        poly = orient(poly, sign=1.0)
        rings.append(_polish(_ring_rule(list(poly.exterior.coords), c, +1, rec, butt), POLISH * c, moved))
        for hole in poly.interiors:
            if Polygon(hole).area < min_hole:                # a counter too small to see is ink
                continue
            rings.append(_polish(_ring_rule(list(hole.coords), c, +1, rec, butt), POLISH * c, moved))
    if rec is not None and moved:
        _follow(rec, moved)
    return rings


MIN_COUNTER = 0.2   # pinholes (under a fifth of a stem, squared) fill in
POLISH = 0.25       # edges shorter than this share of the chamfer leg are slivers: two lines missing each other by a few units
SLIT = 0.35         # white narrower than twice this share of the chamfer leg, and long, is a slit


def _fill_slits(u, eps):
    """Slits of white out of the union: where two strokes run past each
    other a few units apart (a cedilla's foot under a c's foot at Black)
    the white between is a hairline, invisible at text sizes and sloppy at
    large ones. Closing the ink by ``eps`` finds the white narrower than
    twice it; the long thin pieces (not the small triangles a closing fills
    in every inside corner) open to the outside become ink, unless filling
    one would seal a counter's mouth or join two parts that are drawn apart
    (a tonos and its capital): the topology stays what it is, at every
    weight, for the variable font."""
    if eps <= 0 or u.is_empty:
        return u
    closed = u.buffer(eps, join_style='mitre').buffer(-eps, join_style='mitre')
    gaps = closed.difference(u)
    # a counter (white enclosed by ink) is never filled here: its topology
    # must be the same at every weight, for the variable font
    filled = shapely.union_all([Polygon(g.exterior) for g in getattr(u, 'geoms', [u]) if isinstance(g, Polygon)])
    holes = filled.difference(u)
    fill = []
    for part in getattr(gaps, 'geoms', [gaps]):
        if part.is_empty or part.area < 1e-6:
            continue
        if not holes.is_empty and part.difference(holes).area < 0.5 * part.area:
            continue
        r = part.minimum_rotated_rectangle
        xs, ys = r.exterior.coords.xy
        long = max(math.hypot(xs[i + 1] - xs[i], ys[i + 1] - ys[i]) for i in range(2))
        if long > 3 * eps and part.area < long * eps:
            fill.append(part)
    if not fill:
        return u

    def topology(v):
        polys = [g for g in getattr(v, 'geoms', [v]) if isinstance(g, Polygon)]
        return len(polys), sum(len(g.interiors) for g in polys)
    t0 = topology(u)
    for part in fill:     # never seal an open counter's mouth, never join two separate parts
        v = shapely.make_valid(shapely.union_all([u, part]))
        if topology(v) == t0:
            u = v
    return u


def _polish(pts, eps, moved):
    """Slivers out of a finished ring: what stroke unions and clips leave
    behind, much shorter than any cut the design makes (a chamfer is at
    least 1.4 legs, a pixel step a module), and visible only as sloppiness
    at large sizes.

    * a short edge between two edges running the same way (a jog: two
      strokes that should share a line miss it by a few units; a clipped
      stroke's leftover cap): its vertex on the shorter side goes, so the
      longer edge keeps its line;
    * a short edge where the edges either side turn a corner (a micro-flat
      in place of a point): the two edges meet at their intersection.

    A spike (edges either side running back on each other) is left as it
    is. ``moved`` collects old point -> new point for the chamfer record.

    Every choice is made by geometry, never by which way the ring runs, so
    a symmetric drawing stays symmetric: the short edges go in an order a
    mirror image shares (length, then height, then distance from the ring's
    middle), and a jog whose two sides are the same length closes on its
    midpoint."""
    pts = list(pts)
    skip = set()
    cx = (min(p[0] for p in pts) + max(p[0] for p in pts)) / 2 if pts else 0.0
    while len(pts) > 3:
        n = len(pts)
        best = None
        for i in range(n):
            a, b = pts[i], pts[(i + 1) % n]
            L = _len(_sub(b, a))
            if L < eps and (a, b) not in skip:
                key = (round(L, 6), round((a[1] + b[1]) / 2, 6), round(abs((a[0] + b[0]) / 2 - cx), 6))
                if best is None or key < best[0]:
                    best = (key, i)
        if best is None:
            break
        _, i = best
        j, k, h = (i + 1) % n, (i + 2) % n, (i - 1) % n
        prev, a, b, nxt = pts[h], pts[i], pts[j], pts[k]
        e_in, e_out = _sub(a, prev), _sub(nxt, b)
        if _len(e_in) < 1e-9 or _len(e_out) < 1e-9:
            skip.add((a, b))
            continue
        u_in, u_out = _unit(e_in), _unit(e_out)
        turn = abs(math.degrees(math.atan2(_cross(u_in, u_out), _dot(u_in, u_out))))
        if turn < 15:                                         # a jog or a kink
            l_in, l_out = _len(e_in), _len(e_out)
            if abs(l_in - l_out) <= 1e-6 * max(l_in, l_out):  # no shorter side: meet halfway
                q = _mul(_add(a, b), 0.5)
                moved[a] = q
                moved[b] = q
                pts[i] = q
                del pts[j]
            elif l_in < l_out:
                moved[a] = b
                del pts[i]
            else:
                moved[b] = a
                del pts[j]
        elif turn < 165:                                      # a micro-flat at a corner
            q = _meet_pts(prev, a, b, nxt)
            if q is None or _len(_sub(q, _mul(_add(a, b), 0.5))) > 2 * eps:
                skip.add((a, b))
                continue
            moved[a] = q
            moved[b] = q
            pts[i] = q
            del pts[j]
        else:
            skip.add((a, b))
    return pts


def _meet_pts(p0, p1, q0, q1):
    """Where the line through p0, p1 meets the line through q0, q1."""
    d1, d2 = _sub(p1, p0), _sub(q1, q0)
    den = _cross(d1, d2)
    if abs(den) < 1e-12:
        return None
    t = _cross(_sub(q0, p0), d2) / den
    return _add(p0, _mul(d1, t))


def _follow(rec, moved):
    """Chamfer record entries whose points the polish moved, moved too."""
    def near(pt):
        for old, new in moved.items():
            if abs(old[0] - pt[0]) < 1e-6 and abs(old[1] - pt[1]) < 1e-6:
                return new
        return pt
    for i, r in enumerate(rec):
        if r and r[0] == 'chord':
            rec[i] = ('chord', near(r[1]), near(r[2]))


def rings_to_shapely(rings):
    """Rebuild the ink from rings, even-odd: a ring toggles ink inside it, so
    a dot inside a counter inside a bowl comes out right."""
    out = Polygon()
    for r in rings:
        if len(r) < 3:
            continue
        poly = shapely.make_valid(Polygon(r))
        out = out.symmetric_difference(poly)
    return out


def _signed_area(r):
    s = 0.0
    for i in range(len(r)):
        x1, y1 = r[i - 1]
        x2, y2 = r[i]
        s += x1 * y2 - x2 * y1
    return s / 2
