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
    labels = []                       # what made each point: ('n', node) or ('b', node, 0 or 1)
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
            labels.extend([('b', i, 0), ('b', i, 1)])
        else:
            pts.append(p)
            widths.append(nd.w)
            labels.append(('n', i))
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
        labels = [labels[i] for i in keep]
    return pts, bowls, widths, labels


def _cap_point(p, d, side_pt, kind):
    """Where a side line (through side_pt, direction d) meets the cap at p."""
    if kind == 'flat':
        return _meet(side_pt, d, p, (-d[1], d[0]))
    if kind == 'h':
        return _meet(side_pt, d, p, (1.0, 0.0))
    if kind == 'v':
        return _meet(side_pt, d, p, (0.0, 1.0))
    raise ValueError(f'unknown cap {kind!r}')


def stroke_polygon(stroke: Stroke, thick: Thickness, c: float, rec: list | None = None,
                   edges: list | None = None) -> Polygon:
    """The ink of one stroke. If a stroke's bowl chamfers do not fit inside it
    (very heavy weights), the bowls shrink until they do. ``rec`` collects
    the lines the bowls' chamfer edges lie on (see ``ink``); ``edges`` the
    outline's edges, each named for what made it (see ``ink``'s tags)."""
    try:
        return _stroke_polygon(stroke, thick, c, rec=rec, edges=edges)
    except ValueError:
        if not any(n.bowl for n in stroke.nodes):
            # a stroke thicker than it is long (a short diagonal at the very
            # heaviest settings): repair it and log it
            REPAIRED.append(stroke)
            return _stroke_polygon(stroke, thick, c, repair=True, rec=rec, edges=edges)
    lo, hi = 0.0, 1.0
    for _ in range(30):
        mid = (lo + hi) / 2
        try:
            _stroke_polygon(_scale_bowls(stroke, mid), thick, c)
            lo = mid
        except ValueError:
            hi = mid
    try:
        return _stroke_polygon(_scale_bowls(stroke, lo * 0.98), thick, c, rec=rec, edges=edges)
    except ValueError:
        # Last resort: repair the outline and log the stroke for review, so a
        # crowded extreme (a ligature squeezed into a monospaced cell at Black)
        # degrades instead of failing the build.
        REPAIRED.append(stroke)
        return _stroke_polygon(stroke, thick, c, repair=True, rec=rec, edges=edges)


REPAIRED: list = []


def _scale_bowls(stroke: Stroke, k: float) -> Stroke:
    return Stroke(tuple(Node(n.x, n.y, n.bowl * k, n.w) for n in stroke.nodes), stroke.closed, stroke.start, stroke.end)


def _stroke_polygon(stroke: Stroke, thick: Thickness, c: float, repair: bool = False,
                    rec: list | None = None, edges: list | None = None) -> Polygon:
    pts, bowls, widths, labels = _expand(stroke)
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
        # Continuity: a segment shorter than an edge break between two that
        # turn (a flat between two chamfers, all but used up) is offset in
        # proportion to its length. Offset in full, a flat of 0.03 units cut
        # its corner as one of a break would, and the same corner with no
        # flat came to a point: ∭'s hooks jumped 12 units between 272 and
        # 273. Its two outline corners move toward where its neighbours'
        # offsets meet, wholly at no length, not at all from a break up.
        nv = len(verts)
        for j in (range(nseg) if closed else range(1, nseg - 1)):
            L = _len(_sub(pts[(j + 1) % m], pts[j]))
            if L >= c or L <= 0:
                continue
            (pa, da), (pb, db) = lines[j - 1], lines[(j + 1) % nseg]
            turn = math.degrees(math.acos(max(-1.0, min(1.0, _dot(da, db)))))
            k = (1.0 - ease(L, c, 0.0)) * ease(turn, 30.0, 10.0)
            q = _meet(pa, da, pb, db) if k > 0 else None
            if q is None:
                continue
            a_, b_ = j % nv, (j + 1) % nv
            verts[a_] = _add(verts[a_], _mul(_sub(q, verts[a_]), k))
            verts[b_] = _add(verts[b_], _mul(_sub(q, verts[b_]), k))
            # on the inside of the turn the short segment's offset folds back
            # on itself (its two corners crossed): there it is no edge, and
            # its corners are the neighbours' meeting point, where an edge
            # folding back has none of its own length left. (Left folded, the
            # outline was not simple and the stroke's bowls were shrunk until
            # it was, cutting the corner by their 2% margin.)
            if _dot(_sub(verts[b_], verts[a_]), segs[j][1]) < 0:
                verts[a_] = verts[b_] = q
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
    if edges is not None:
        # each side's edge j lies on segment j's offset line: named by the
        # segment's two ends (what made them) and the side; the caps by end
        seg = [(labels[j], labels[(j + 1) % m]) for j in range(nseg)]
        nv = len(left)
        for j in range(nseg if closed else nv - 1):
            edges.append((left[j], left[(j + 1) % nv], ('L',) + seg[j]))
            edges.append((right[j], right[(j + 1) % nv], ('R',) + seg[j]))
        if not closed:
            edges.append((left[0], right[0], ('cap', 0)))
            edges.append((left[-1], right[-1], ('cap', 1)))
    return poly


def _dir_class(u) -> str:
    ax, ay = abs(u[0]), abs(u[1])
    if ax < 1e-6 or ay < 1e-6:
        return 'axis'
    if abs(ax - ay) < 1e-6:
        return 'diag'
    return 'steep'


def _on_butt(a, b, butt, corner=None) -> bool:
    """Whether the edge a-b lies on one of the butt lines (see ``ink``). A
    line given with ends, ('y', value, lo, hi), holds only where ``corner``
    (the vertex in question) lies between them: a mark meets its base square
    under itself, and the base keeps its edge breaks elsewhere on the line."""
    for line in butt:
        axis, v = line[0], line[1]
        k = 0 if axis == 'x' else 1
        on = abs(a[k] - v) < BUTT_TOL and abs(b[k] - v) < BUTT_TOL
        if on and (len(line) < 4 or corner is None or line[2] <= corner[1 - k] <= line[3]):
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
        if butt and (_on_butt(a, b, butt, b) or _on_butt(b, q, butt, b)):
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


def ink(strokes, thick: Thickness, c: float, extra=(), clip=None, rec: list | None = None, butt=(),
        tags: list | None = None, extra_edges=(), finished=()):
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
    exactly these (``arris.italic``).

    ``tags``, if given, collects per ring the name of each edge (from its
    point i to i + 1): the line it lies on, named for what made it (a
    stroke's side along a segment, a cap, a stamped glyph's own edge
    (``extra_edges``), the clip box), or a corner-rule chord between two
    named edges. The same edge in another master has the same name: the
    variable font matches masters' points by these (``variable``)."""
    segs = [] if tags is not None else None
    polys = []
    for i, st in enumerate(strokes):
        e = [] if segs is not None else None
        polys.append(stroke_polygon(st, thick, c, rec, edges=e))
        if e:
            segs.extend((a, b, ('s', i) + t) for a, b, t in e)
    polys += list(extra)
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
    # finished ink (a stamped glyph) standing apart from the strokes is kept
    # as it was finished: the corner rule, polish and jog closing are not
    # idempotent, and run again they changed a stamped C by a jog where an
    # accent stood near it (Ć's C was not C)
    done = [q for f in finished for q in getattr(f, 'geoms', [f]) if isinstance(q, Polygon) and q.area > 1e-9]
    for poly in u.geoms:
        poly = orient(poly, sign=1.0)
        if clip is None and any(abs(poly.area - f.area) <= 1e-6 * max(f.area, 1.0)
                                and poly.symmetric_difference(f).area <= 1e-6 * max(f.area, 1.0) for f in done):
            for r in [poly.exterior] + list(poly.interiors):
                pts = list(r.coords)[:-1]
                if r is poly.exterior or Polygon(r).area >= min_hole:
                    rings.append(pts)
            continue
        rings.append(_close_jogs(_polish(_ring_rule(list(poly.exterior.coords), c, +1, rec, butt), POLISH * c, moved), JOG * c, moved))
        for hole in poly.interiors:
            if Polygon(hole).area < min_hole:                # a counter too small to see is ink
                continue
            rings.append(_close_jogs(_polish(_ring_rule(list(hole.coords), c, +1, rec, butt), POLISH * c, moved), JOG * c, moved))
    if rec is not None and moved:
        _follow(rec, moved)
    if tags is not None:
        segs.extend(extra_edges)
        if clip is not None:
            b = list(clip.exterior.coords)
            segs.extend((b[k], b[k + 1], ('clip', k)) for k in range(len(b) - 1))
        tags.extend(_name_edges(r, segs) for r in rings)
    return rings


def _name_edges(ring, segs, tol=1e-3):
    """The name of each edge of a ring (point i to i + 1): the named input
    edge it lies along, overlapping it most (``ink``'s tags); an edge that
    lies along none (a corner-rule chord) is named by the named edges
    before and after it."""
    n = len(ring)
    pre = []
    for (p, q, t) in segs:
        e = _sub(q, p)
        le = _len(e)
        if le > 1e-9:
            pre.append((p, _mul(e, 1 / le), le, t))
    names = []
    for i in range(n):
        a, b = ring[i][:2], ring[(i + 1) % n][:2]
        d = _sub(b, a)
        ld = _len(d)
        best = None
        if ld > 1e-9:
            u = _mul(d, 1 / ld)
            for p, v, le, t in pre:
                if abs(_cross(u, v)) > 1e-6 or abs(_cross(_sub(a, p), v)) > tol:
                    continue
                ta, tb = sorted((_dot(_sub(a, p), v), _dot(_sub(b, p), v)))
                ov = min(tb, le) - max(ta, 0.0)
                if ov < -tol:
                    continue
                if best is None or ov > best[0] + 1e-6 or (abs(ov - best[0]) <= 1e-6 and repr(t) < repr(best[1])):
                    best = (ov, t)
        names.append(best[1] if best else None)
    if all(t is None for t in names):
        return [('?', i) for i in range(n)]
    out = list(names)
    for i in range(n):
        if names[i] is None:
            prev = next(names[(i - k) % n] for k in range(1, n + 1) if names[(i - k) % n] is not None)
            nxt = next(names[(i + k) % n] for k in range(1, n + 1) if names[(i + k) % n] is not None)
            out[i] = ('chord', prev, nxt)
    return out


MIN_COUNTER = 0.2   # pinholes (under a fifth of a stem, squared) fill in
JOG = 1.0           # a step between parallel edges shorter than this share of the chamfer leg is closed (_close_jogs)
STRAY = 3.0         # degrees: a vertex bending less than this between two long edges goes (_close_jogs)
POLISH = 0.25       # edges shorter than this share of the chamfer leg are slivers: two lines missing each other by a few units
SLIT = 0.35         # white narrower than twice this share of the chamfer leg, and long, is a slit
HAIR = 1e-3         # units: white narrower than twice this is no white (_fill_slits)
SLIT_RAMP = 0.5     # a slit's limits (three eps long, one eps across) ease in over this share of eps about them
# Continuity (the owner, 2026-11-05): the outline is a continuous function of
# the weight. A clean-up that acts on a feature past a limit (a step shorter
# than a break, a sliver, a slit) acts in proportion as the feature nears
# the limit, over its last RAMP share, wholly only beyond: closed at once
# at the limit, a feature jumped by the limit's size from one weight to the
# next, and a variable font animating its weight flickered there
# (tools/continuity_scan.py).
RAMP = 0.4
SNAP = 1.0     # units: a feature eased in so far that less than this of it is left closes whole (no edge
               # that short: the italic read a 0.2-unit edge as a corner of its own and curved ∭ 49 units off)


def ease(x, full, none):
    """How far a rule acts on what measures ``x``: 1 at ``full`` or beyond
    it, 0 at ``none`` or beyond it, in proportion between (either may be
    the larger). Continuity: a rule that would switch at a limit eases in
    over a span ending there instead, and the drawing changes as smoothly
    as the measure (a clean-up here; a drawing's own choice, as the @'s
    even spacing, in the glyphs)."""
    if none == full:
        return 1.0 if x == full else 0.0
    return min(max((none - x) / (none - full), 0.0), 1.0)


_ease = ease


def _folds(chain) -> bool:
    """Whether an open polyline crosses itself (a stretch of a ring
    around a move: _unfolded)."""
    from shapely.geometry import LineString
    pts = [q for i, q in enumerate(chain) if i == 0 or _len(_sub(q, chain[i - 1])) > 1e-9]
    return len(pts) > 3 and not LineString(pts).is_simple


def _unfolded(make, chain_of):
    """The largest share f (at most 1) of a move for which the stretch of
    the ring around it does not fold: ``make(f)`` the moved points,
    ``chain_of(moved)`` the stretch. A partial clean-up that would fold the
    outline (the ŧ's bar at 900, a step half closed across its neighbour)
    goes as far as it can without; found by halving, so it follows the
    geometry continuously."""
    if not _folds(chain_of(make(1.0))):
        return 1.0
    lo, hi = 0.0, 1.0
    for _ in range(12):
        mid = (lo + hi) / 2
        if _folds(chain_of(make(mid))):
            hi = mid
        else:
            lo = mid
    return lo


def _fill_slits(u, eps):
    """Slits of white out of the union: where two strokes run past each
    other a few units apart (a cedilla's foot under a c's foot at Black)
    the white between is a hairline, invisible at text sizes and sloppy at
    large ones. Closing the ink by ``eps`` finds the white narrower than
    twice it; the long thin pieces (not the small triangles a closing fills
    in every inside corner) open to the outside become ink, unless filling
    one would seal a counter's mouth or join two parts that are drawn apart
    (a tonos and its capital): the topology stays what it is, at every
    weight, for the variable font.

    Continuity: a slit is long (over three times ``eps``) and thin (under
    ``eps`` across on average), and each eases in over a span about its
    limit (SLIT_RAMP): a gap part way in is filled only where it is
    narrower than twice that share of ``eps``, from its narrowest outward.
    Filled whole or not at all, a cedilla's gap under ç that sat on both
    limits at once was filled at 890 and open at 880 and 900."""
    if eps <= 0 or u.is_empty:
        return u
    closed = u.buffer(eps, join_style='mitre').buffer(-eps, join_style='mitre')
    # the closing leaves hairlines of no width along edges that meet at a shallow angle: opened away
    # (HAIR), so an inside corner's small triangle is not joined by one to a long reach of nothing and
    # filled as a slit (the turned brace's notch under its point, kept at 421 and filled at 422)
    raw = closed.difference(u)
    gaps = raw.buffer(-HAIR, join_style='mitre').buffer(HAIR, join_style='mitre')    # measured opened, filled as found
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
        k = (_ease(long, (3 + SLIT_RAMP) * eps, (3 - SLIT_RAMP) * eps)
             * _ease(part.area / max(long, 1e-9), (1 - SLIT_RAMP / 2) * eps, (1 + SLIT_RAMP / 2) * eps))
        if k >= 1 - 1e-9:
            fill.append(raw.intersection(part.buffer(2 * HAIR, join_style='mitre')))
        elif k > 0:                                         # part way: the gap's white narrower than 2 k eps
            r = k * eps
            piece = u.buffer(r, join_style='mitre').buffer(-r, join_style='mitre').difference(u).intersection(part)
            if not piece.is_empty and piece.area > 1e-6:
                fill.append(piece)
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


def _drawn(v) -> bool:
    """Whether an edge runs on one of the drawing's own directions: level,
    upright, 45 degrees or a 2:1 slope either way (to a ten-thousandth, as
    the italic reads them: italic._axis, italic._diag)."""
    n = _len(v)
    if n <= 1e-9:
        return False
    x, y = abs(v[0]) / n, abs(v[1]) / n
    return min(x, y) <= 1e-4 or abs(x - y) <= 1e-4 or abs(x - 2 * y) <= 1e-4 or abs(y - 2 * x) <= 1e-4


def _line_meet(p1, d1, p2, d2):
    """Where the line through p1 along d1 meets the line through p2 along
    d2 (None if they are parallel)."""
    den = _cross(d1, d2)
    if abs(den) < 1e-9:
        return None
    t = _cross(_sub(p2, p1), d2) / den
    return _add(p1, _mul(d1, t))


def _keep_drawn(pts, i, r, reach, moved, ease=False):
    """Straighten the vertex pts[i] between two nearly straight edges by
    share ``r``, keeping an edge that runs on a drawn direction (_drawn) on
    it: the other edge turns onto its line, its far end sliding along its
    own other neighbour (as a jog's edges do), and once on it the vertex
    goes. Removed or straightened onto the chord between them instead, the
    drawn edge tilted by hundredths of a unit and the italic, which curves
    a corner only between edges that run on the drawn directions, left it
    straight. None if neither edge or both run on one (the caller's own
    way then); else the share it went, 0 where the end would move further
    than ``reach`` (with ``ease``, fading out from 0.8 of it), 1 where the
    vertex went."""
    n = len(pts)
    if n < 5:
        return None
    a, b, c2 = pts[i - 1], pts[i], pts[(i + 1) % n]
    u, v = _sub(b, a), _sub(c2, b)
    du, dv = _drawn(u), _drawn(v)
    if du == dv:
        return None
    far, nb, keep = ((i + 1) % n, (i + 2) % n, u) if du else ((i - 1) % n, (i - 2) % n, v)
    q = _line_meet(pts[nb], _sub(pts[far], pts[nb]), b, keep)
    if q is None:
        return 0.0
    d = _len(_sub(q, pts[far]))
    r = r * _ease(d, 0.8 * reach, reach) if ease else (r if d <= reach else 0.0)
    if r <= 0:
        return 0.0
    f2 = _add(pts[far], _mul(_sub(q, pts[far]), r))
    moved[pts[far]] = f2
    pts[far] = f2
    if r >= 1 - 1e-9:
        moved[b] = b
        del pts[i]
        return 1.0
    return r


def _close_jogs(pts, eps, moved):
    """Steps left where strokes that should share a line miss it, larger
    than _polish's slivers but still far smaller than a drawn step (a pixel
    step is a module; this is at most a corner break): a short edge between
    two edges running the same way. The shorter of those two moves onto the
    longer's line, its far end sliding along its own other neighbour, and
    the step's two vertices go: every edge keeps its direction (a right
    angle stays one, a diagonal stays on its 45 or 2:1), only lengths change.
    A move that would carry a point further than the step is long and a
    module more is not made (the step is a feature, not a miss). A vertex
    bending less than STRAY degrees between two long edges also goes.
    Choices are made by geometry alone, so a symmetric drawing stays
    symmetric.

    Continuity: every one of those tests eases in (_ease) rather than
    switching, so the outline is a continuous function of the weight. A
    step closes wholly below 1 - RAMP of the limit and in proportion
    above it (the two edges move toward each other's line by that share,
    the step shortening); edges that are nearly parallel, a step that is
    nearly steep enough, a move nearly too far, act in proportion too; and
    where the two edges are nearly the same length both move, the shorter
    the more, so the side that moves does not change at once."""
    pts = list(pts)
    # vertices on a straight line (a stroke's end inside another's edge):
    # no corner there, and they hide the jogs beside them
    i = 0
    while len(pts) > 3 and i < len(pts):
        n = len(pts)
        a, b, c2 = pts[i - 1], pts[i], pts[(i + 1) % n]
        u, v = _sub(b, a), _sub(c2, b)
        if _len(u) > 1e-9 and _len(v) > 1e-9 and abs(_cross(_unit(u), _unit(v))) < 0.005 and _dot(u, v) > 0:
            went = _keep_drawn(pts, i, 1.0, eps, moved)          # a drawn edge keeps its direction
            if went is None:
                moved[b] = b
                del pts[i]
            elif went < 1:
                i += 1
                continue
            i = max(i - 2, 0)    # the slid end, or the vertex's neighbours, may be on a straight line now
            continue
        i += 1
    cx = (min(p[0] for p in pts) + max(p[0] for p in pts)) / 2 if pts else 0.0
    skip = set()
    cos_full, cos_none = math.cos(math.radians(5)), math.cos(math.radians(10))
    sin_full, sin_none = math.sin(math.radians(40)), math.sin(math.radians(30))
    while len(pts) > 5:
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
        hh, h, j, k, kk = (i - 2) % n, (i - 1) % n, (i + 1) % n, (i + 2) % n, (i + 3) % n
        pp, prev, a, b, nxt, nn = pts[hh], pts[h], pts[i], pts[j], pts[k], pts[kk]
        e_in, step, e_out = _sub(a, prev), _sub(b, a), _sub(nxt, b)
        if min(_len(e_in), _len(e_out), _len(step)) < 1e-9:
            skip.add((a, b))
            continue
        u_in, u_out, u_s = _unit(e_in), _unit(e_out), _unit(step)
        l_in, l_out, L = _len(e_in), _len(e_out), _len(step)
        if abs(l_in - l_out) < 1e-6:                         # no shorter side (a symmetric drawing's own steps)
            skip.add((a, b))
            continue
        act = (_ease(L, (1 - RAMP) * eps, eps)
               * _ease(_dot(u_in, u_out), cos_full, cos_none)          # the two edges run the same way
               * _ease(abs(_cross(u_in, u_s)), sin_full, sin_none))     # and the step steps across them
        alpha = _ease((l_out - l_in) / (l_out + l_in), 0.2, -0.2)      # 1: the incoming edge is the shorter, it moves
        limit = L + eps
        q_in = _line_meet(pp, _sub(prev, pp), b, u_out)                # where each edge's far end goes, moved wholly
        q_out = _line_meet(nn, _sub(nxt, nn), a, u_in)
        ok_in = _ease(_len(_sub(q_in, prev)), 0.8 * limit, limit) if q_in is not None else 0.0
        ok_out = _ease(_len(_sub(q_out, nxt)), 0.8 * limit, limit) if q_out is not None else 0.0
        b_in, b_out = act * alpha * ok_in, act * (1 - alpha) * ok_out
        if b_in + b_out <= 1e-9:
            skip.add((a, b))
            continue
        if (1 - b_in - b_out) * L < SNAP:                               # under a unit left: closed (SNAP)
            scale = 1.0 / (b_in + b_out)
            b_in, b_out = b_in * scale, b_out * scale

        def moved_pts(f, b_in=b_in, b_out=b_out):
            bi, bo = b_in * f, b_out * f
            a2 = _add(a, _mul(step, bi))                               # the step's ends move toward each other
            b2 = _sub(b, _mul(step, bo))
            d_in = _unit(_add(_mul(u_in, 1 - bi), _mul(u_out, bi)))     # each edge turns onto the other's line as it moves
            d_out = _unit(_add(_mul(u_out, 1 - bo), _mul(u_in, bo)))
            prev2 = _line_meet(pp, _sub(prev, pp), a2, d_in) if bi > 0 else prev
            nxt2 = _line_meet(nn, _sub(nxt, nn), b2, d_out) if bo > 0 else nxt
            return prev2, a2, b2, nxt2
        if any(q is None for q in moved_pts(1.0)):
            skip.add((a, b))
            continue
        f = 1.0 if b_in + b_out >= 1 - 1e-9 else _unfolded(
            moved_pts, lambda m4: [pts[(i - 4) % n], pp] + list(m4) + [nn, pts[(i + 4) % n]])
        b_in, b_out = b_in * f, b_out * f
        if b_in + b_out <= 1e-9:
            skip.add((a, b))
            continue
        prev2, a2, b2, nxt2 = moved_pts(1.0, b_in, b_out)
        moved[prev], moved[nxt] = prev2, nxt2
        pts[h], pts[k] = prev2, nxt2
        if b_in + b_out >= 1 - 1e-9:                                   # closed: the step's two vertices go
            moved[a] = moved[b] = a2
            for idx in sorted((i, j), reverse=True):
                del pts[idx]
        else:
            moved[a], moved[b] = a2, b2
            pts[i], pts[j] = a2, b2
            skip.add((a2, b2))
    # stray vertices: a barely bent long edge straightens, wholly below half
    # of STRAY, in proportion above it and as its edges near the long limit.
    # Where one of the two edges runs on a drawn direction (_drawn) it keeps
    # it, as a jog's edges do: the other turns onto its line, the far end
    # sliding along its own other neighbour. Straightened onto the chord
    # between them, a level edge tilted by hundredths of a unit, and the
    # italic, reading it as no corner's edge, left its corner straight (the
    # italic p's bowl at its stem, where the bowl's top sits under the
    # x-height by the slant's thinning and the stem's top runs up to it).
    long_ = 4 * eps
    done = set()
    changed = True
    while changed and len(pts) > 4:
        changed = False
        n = len(pts)
        for i in range(n):
            a, b, c2 = pts[i - 1], pts[i], pts[(i + 1) % n]
            if b in done:
                continue
            u, v = _sub(b, a), _sub(c2, b)
            if _len(u) < 0.75 * long_ or _len(v) < 0.75 * long_:
                continue
            t = abs(math.degrees(math.atan2(_cross(_unit(u), _unit(v)), _dot(_unit(u), _unit(v)))))
            if not 1e-6 < t < STRAY:
                continue
            r = _ease(t, STRAY / 2, STRAY) * _ease(min(_len(u), _len(v)), long_, 0.75 * long_)
            if r <= 0:
                continue
            if _drawn(u) and _drawn(v):
                continue
            went = _keep_drawn(pts, i, r, eps, moved, ease=True)   # never further than a break
            if went is not None:
                if went <= 0:
                    continue
                if went < 1:
                    done.add(b)
            elif r >= 1 - 1e-9:
                moved[b] = b
                del pts[i]
            else:
                ch = _sub(c2, a)
                foot = _add(a, _mul(ch, _dot(_sub(b, a), ch) / _dot(ch, ch)))
                b2 = _add(b, _mul(_sub(foot, b), r))
                moved[b] = b2
                pts[i] = b2
                done.add(b2)
            changed = True
            break
    return pts


def _polish(pts, eps, moved):
    """Slivers out of a finished ring: what stroke unions and clips leave
    behind, much shorter than any cut the design makes (a chamfer is at
    least 1.4 legs, a pixel step a module), and visible only as sloppiness
    at large sizes.

    * a short edge between two edges running the same way (a jog: two
      strokes that should share a line miss it by a few units; a clipped
      stroke's leftover cap): its vertex on the shorter side goes, so the
      longer edge keeps its line; where it steps across two parallel
      edges, it is left to _close_jogs, which keeps both edges'
      directions;
    * a short edge where the edges either side turn a corner (a micro-flat
      in place of a point): the two edges meet at their intersection.

    A spike (edges either side running back on each other) is left as it
    is. ``moved`` collects old point -> new point for the chamfer record.

    Every choice is made by geometry, never by which way the ring runs, so
    a symmetric drawing stays symmetric: the short edges go in an order a
    mirror image shares (length, then height, then distance from the ring's
    middle), and a jog whose two sides are the same length closes on its
    midpoint.

    Continuity: each fix eases in (_ease). A short edge is taken out
    wholly below 1 - RAMP of the limit, in proportion above it (its ends
    move that share of the way); the jog's fix and the corner's blend over
    turns of 10 to 20 degrees, and fade out toward a spike's 165 and a
    corner too far away; and a jog whose sides are nearly the same length
    closes between its ends, nearer the longer side's line the more it
    is the longer."""
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
        l_in, l_out, L = _len(e_in), _len(e_out), _len(_sub(b, a))
        # the jog's fix: the vertex on the shorter side onto the other (both to the middle when even)
        if abs(l_in - l_out) <= 1e-6 * max(l_in, l_out):
            alpha = 0.5
        else:
            alpha = _ease((l_out - l_in) / (l_out + l_in), 0.2, -0.2)
        jog = _add(a, _mul(_sub(b, a), alpha))
        # the corner's fix: both onto the corner the edges either side make
        mix = _ease(turn, 20.0, 10.0)
        q = _meet_pts(prev, a, b, nxt) if mix > 0 else None
        if mix > 0 and q is None:
            mix = 0.0
        flat = _ease(_len(_sub(q, _mul(_add(a, b), 0.5))), 1.5 * eps, 2 * eps) if q is not None else 0.0
        # a step across two edges running the same way is _close_jogs' to close: the shorter
        # edge onto the longer's line, both keeping their directions. Merged here into one
        # point, it tilted the edges either side by its height (both, where they were nearly
        # the same length): a level edge off level, which the italic reads as no corner's edge
        hand = 0.0 if abs(l_in - l_out) < 1e-6 or n <= 5 or L < 1e-9 else (
            _ease(_dot(u_in, u_out), math.cos(math.radians(5)), math.cos(math.radians(10)))
            * _ease(abs(_cross(u_in, _unit(_sub(b, a)))), math.sin(math.radians(40)), math.sin(math.radians(30))))
        s = _ease(L, (1 - RAMP) * eps, eps) * ((1 - mix) + mix * flat) * _ease(turn, 155.0, 165.0) * (1 - hand)
        if s <= 0:
            skip.add((a, b))
            continue
        target = _add(_mul(jog, 1 - mix), _mul(q, mix)) if mix > 0 else jog
        if s >= 1 - 1e-9 or (1 - s) * L < SNAP:
            moved[a] = moved[b] = target
            pts[i] = target
            del pts[j]
        else:
            def moved_pts(f, s=s, target=target):
                return _add(a, _mul(_sub(target, a), s * f)), _add(b, _mul(_sub(target, b), s * f))
            f = _unfolded(moved_pts, lambda m2: [pts[(i - 2) % n], prev] + list(m2) + [nxt, pts[(i + 3) % n]])
            if f <= 0:
                skip.add((a, b))
                continue
            a2, b2 = moved_pts(f)
            moved[a], moved[b] = a2, b2
            pts[i], pts[j] = a2, b2
            skip.add((a2, b2))
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
    a dot inside a counter inside a bowl comes out right. Ink is area only: a
    ring collapsed to a point or a line (a counter not yet open, in a
    variable font's master) toggles nothing."""
    out = Polygon()
    for r in rings:
        if len(set(r)) < 3:
            continue
        poly = shapely.make_valid(Polygon(r))
        if poly.geom_type not in ('Polygon', 'MultiPolygon'):
            poly = shapely.union_all([q for q in getattr(poly, 'geoms', [poly])
                                      if q.geom_type in ('Polygon', 'MultiPolygon')])
        if poly.is_empty:
            continue
        out = _area(out.symmetric_difference(poly))
    return out


def _area(g):
    """The polygons of a geometry: rings that share an edge exactly (a
    counter collapsed onto its outline in one of a variable font's masters)
    leave that edge behind as a line in their symmetric difference."""
    if g.geom_type in ('Polygon', 'MultiPolygon'):
        return g
    parts = [q for q in getattr(g, 'geoms', [g]) if q.geom_type in ('Polygon', 'MultiPolygon') and not q.is_empty]
    return shapely.union_all(parts) if parts else Polygon()


def _signed_area(r):
    s = 0.0
    for i in range(len(r)):
        x1, y1 = r[i - 1]
        x2, y2 = r[i]
        s += x1 * y2 - x2 * y1
    return s / 2
