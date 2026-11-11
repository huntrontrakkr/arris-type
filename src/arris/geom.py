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
                   edges: list | None = None, fill: float | None = None) -> Polygon:
    """The ink of one stroke. If a stroke's bowl chamfers do not fit inside it
    (very heavy weights), the bowls shrink until they do. ``rec`` collects
    the lines the bowls' chamfer edges lie on (see ``ink``); ``edges`` the
    outline's edges, each named for what made it (see ``ink``'s tags).
    ``fill``: the least leg of a bowl's inside chamfer (the corner rule's
    fill, _ring_rule), where it is not ``c``."""
    try:
        return _stroke_polygon(stroke, thick, c, rec=rec, edges=edges, fill=fill)
    except ValueError:
        if not any(n.bowl for n in stroke.nodes):
            # a stroke thicker than it is long (a short diagonal at the very
            # heaviest settings): repair it and log it
            REPAIRED.append(stroke)
            return _stroke_polygon(stroke, thick, c, repair=True, rec=rec, edges=edges, fill=fill)
    lo, hi = 0.0, 1.0
    for _ in range(30):
        mid = (lo + hi) / 2
        try:
            _stroke_polygon(_scale_bowls(stroke, mid), thick, c, fill=fill)
            lo = mid
        except ValueError:
            hi = mid
    try:
        return _stroke_polygon(_scale_bowls(stroke, lo * 0.98), thick, c, rec=rec, edges=edges, fill=fill)
    except ValueError:
        # Last resort: repair the outline and log the stroke for review, so a
        # crowded extreme (a ligature squeezed into a monospaced cell at Black)
        # degrades instead of failing the build.
        REPAIRED.append(stroke)
        return _stroke_polygon(stroke, thick, c, repair=True, rec=rec, edges=edges, fill=fill)


REPAIRED: list = []


def _scale_bowls(stroke: Stroke, k: float) -> Stroke:
    return Stroke(tuple(Node(n.x, n.y, n.bowl * k, n.w) for n in stroke.nodes), stroke.closed, stroke.start, stroke.end)


def _stroke_polygon(stroke: Stroke, thick: Thickness, c: float, repair: bool = False,
                    rec: list | None = None, edges: list | None = None, fill: float | None = None) -> Polygon:
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
        return verts, lines

    left, llines = side(+1)
    right, rlines = side(-1)

    # Inner side of a bowl: if the offset chamfer is shorter than the corner
    # rule's fill (or inverted), use the plain inner corner; the corner rule
    # then fills it with its chord, so the inner leg never drops below the
    # fill's (``fill``; c where none is given: until 1.017 always c, which
    # from ExtraBold held a bowl's inside chamfer above what its strokes make
    # of it, 44 units for 32 at Black, the stroke thicker round the corner
    # than along its sides).
    # verts[i] sits at pts[i] on both sides (caps included for open strokes);
    # bowl k runs from pts[k] to pts[k+1] along segment k.
    for k in bowls:
        din, dout = segs[(k - 1) % nseg][1], segs[(k + 1) % nseg][1]
        verts, lines = (left, llines) if _cross(din, dout) > 0 else (right, rlines)
        (p1, d1), (p2, d2) = lines[(k - 1) % nseg], lines[(k + 1) % nseg]
        corner = _meet(p1, d1, p2, d2)
        if corner is None:
            continue
        if _dot(_sub(corner, verts[k]), din) < (c if fill is None else min(fill, c)) - EPS:
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


def _ring_rule(coords, c, convex_sign, rec: list | None = None, butt=(), crotch: float = 2.0,
               fill: float | None = None):
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

    ``crotch``: how far along the axis edge the fill of a concave 45-degree
    corner reaches, in breaks. The pixel rule's chord there is as long as a
    right angle's (c*sqrt2), which is 2c along the stem and twice the ink
    of a right angle's fill, added where a diagonal already overlaps a
    stem: the joins of K k M R Q 4 and the 1 were the thickest in the
    alphabet for it (tools/stroke_audit.py). Arris gives every corner one
    leg on its horizontal or vertical edge: c at a right angle, c in a
    crotch (crotch 1: draw.crotch_fill); the watch's own drawing and the
    italic keep the pixel rule's 2.

    A crotch with a step in it (a diagonal that lands on a short edge
    square to the bar it runs into: the Z's foot) is a crotch still: its
    chord keeps its leg on the bar and runs square to the diagonal until
    it meets it (_stepped_crotches). A right angle's fill is no longer than
    its shorter edge, so as the Z grew and its foot's step went from 28
    units at Bold to 10 at Black, the corner's break went from 35 units to
    9, all but sharp, where the same crotch without a step (the z's, the
    2's) is
    broken 44. (Not in the watch's drawing, crotch 2.)

    ``fill``: the leg of the chord that fills a concave corner (a right
    angle's, a crotch's), where it is not the leg ``c`` that cuts a convex
    one. A fill adds ink inside a letter where a cut takes it off outside:
    on one leg, a quarter of the stem, the fills grew as fast as the stems
    while the counters they stand in shrank, and from Bold the insides of
    the letters clogged (the cursive e's eye at Black, 178 units a side,
    gave 132 of them to its fills). Arris holds the fill at the Regular's
    leg from there to Black (draw.fill_leg): outside corners grow with the
    weight, inside corners do not, as every family measured tightens its
    joins toward Black (the widest disk in a join, 1.18 stems at Regular
    and 1.10 at Black across 37 families; Arris's 1.38 at every weight).
    """
    f = c if fill is None else min(fill, c)
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
    turns = []
    for i in range(n):
        a, b, q = pts[i - 1], pts[i], pts[(i + 1) % n]
        u1, u2 = _unit(_sub(b, a)), _unit(_sub(q, b))
        turn = math.degrees(math.atan2(_cross(u1, u2), _dot(u1, u2)))  # + = left = convex
        turns.append(turn)
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
    stepped = _stepped_crotches(pts, kinds, turns, f, crotch) if crotch < 2.0 - 1e-9 else {}
    out = []
    for i in range(n):
        if i in stepped:
            out.append(stepped[i])
            continue
        a, b, q = pts[i - 1], pts[i], pts[(i + 1) % n]
        e_in, e_out = _sub(b, a), _sub(q, b)
        u_in, u_out = _unit(e_in), _unit(e_out)
        k = kinds[i]
        # How much of each adjacent edge this corner may use.
        room_in = _len(e_in) * (0.5 if kinds[i - 1] else 1.0)
        room_out = _len(e_out) * (0.5 if kinds[(i + 1) % n] else 1.0)
        if k in ('right', 'steep'):
            r = min(c if turns[i] > 0 else f, room_in, room_out)
            out += [_sub(b, _mul(u_in, r)), _add(b, _mul(u_out, r))]
            if rec is not None and k == 'right':
                rec.append(('chord', out[-2], out[-1]))
        elif k == 'acute':
            leg = c * math.sqrt(2)
            if _cross(u_in, u_out) < 0:                     # a crotch: its fill, by its leg on the axis edge
                leg = f * math.sqrt(2) * crotch / 2.0
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


def _stepped_crotches(pts, kinds, turns, c, crotch) -> dict:
    """The crotches of a ring that have a step in them (_ring_rule): a
    filled right angle whose other edge is shorter than a break and turns
    again, the same way, into a 45-degree edge. The chord keeps its leg on
    the long edge and runs square to the diagonal until it meets it: the
    two points of each become the chord's ends, {point index: its new
    place}. With no step this is the crotch's own chord, with a step a
    break long the right angle's, and every chord between."""
    n = len(pts)
    out: dict = {}

    def chord(v, room_axis, room_diag):
        """The leg on the axis edge and the reach along the diagonal past
        the step's end, for a step v long; None if there is no room."""
        leg = c * (crotch - (crotch - 1.0) * v / c)          # a crotch's leg with no step, a right angle's at a full one
        leg = min(leg, room_axis, v + room_diag * math.sqrt(2))
        return (leg, (leg - v) / math.sqrt(2)) if leg > v + 1e-6 else None

    for i in range(n):
        if kinds[i] != 'right' or turns[i] > 0 or i in out:
            continue
        h, j = (i - 1) % n, (i + 1) % n
        # the step after the right angle: axis in, step, diagonal out
        if kinds[j] is None and abs(turns[j] + 45) < 1.0 and j not in out:
            jj = (j + 1) % n
            u_in, u_d = _unit(_sub(pts[i], pts[h])), _unit(_sub(pts[jj], pts[j]))
            v = _len(_sub(pts[j], pts[i]))
            if _dir_class(u_d) == 'diag' and v < c - 1e-6:
                got = chord(v, _len(_sub(pts[i], pts[h])) * (0.5 if kinds[h] else 1.0),
                            _len(_sub(pts[jj], pts[j])) * (0.5 if kinds[jj] else 1.0))
                if got:
                    out[i] = _sub(pts[i], _mul(u_in, got[0]))
                    out[j] = _add(pts[j], _mul(u_d, got[1]))
                    continue
        # the step before it: diagonal in, step, axis out
        if kinds[h] is None and abs(turns[h] + 45) < 1.0 and h not in out:
            hh = (h - 1) % n
            u_d, u_out = _unit(_sub(pts[h], pts[hh])), _unit(_sub(pts[j], pts[i]))
            v = _len(_sub(pts[i], pts[h]))
            if _dir_class(u_d) == 'diag' and v < c - 1e-6:
                got = chord(v, _len(_sub(pts[j], pts[i])) * (0.5 if kinds[j] else 1.0),
                            _len(_sub(pts[h], pts[hh])) * (0.5 if kinds[hh] else 1.0))
                if got:
                    out[h] = _sub(pts[h], _mul(u_d, got[1]))
                    out[i] = _add(pts[i], _mul(u_out, got[0]))
    return out


def ink(strokes, thick: Thickness, c: float, extra=(), clip=None, rec: list | None = None, butt=(),
        tags: list | None = None, extra_edges=(), finished=(), overlay=(), crotch: float = 2.0,
        facet: float | None = None, fill: float | None = None):
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
    variable font matches masters' points by these (``variable``).

    ``overlay``: strokes laid over the finished ink, (stroke, c) each. Each
    is finished alone, its ends broken on its own chamfer leg ``c``, and
    joined to the finished ink as it is: no corner rule runs over the
    junction, so the corners where it meets the letter stay as they meet
    (a bar frozen at the weight where its white would close, ``draw.frozen``:
    nothing fills in round it as the letter grows on)."""
    segs = [] if tags is not None else None
    polys = []
    for i, st in enumerate(strokes):
        e = [] if segs is not None else None
        polys.append(stroke_polygon(st, thick, c, rec, edges=e, fill=fill))
        if e:
            segs.extend((a, b, ('s', i) + t) for a, b, t in e)
    polys += list(extra)
    if not polys and not overlay:
        return []
    try:
        u = shapely.union_all(polys) if polys else MultiPolygon()
    except shapely.errors.GEOSException:
        # A stamped outline that folds back on itself: a letter tried in no room at all, before its sign
        # is drawn smaller to fit (symkit._mono_fit). ℃'s C in Arris Mono Narrow's cell is tried 59 units
        # wide; at a stem of 108 its lower beak came out with a spike along its own side, and the union
        # stopped the build on it. The fold taken out, the trial is measured and set aside as before.
        u = shapely.union_all([q if q.is_valid else q.buffer(0) for q in polys])
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
    even = facet * c if facet is not None and facet > POLISH + 1e-9 else None   # Arris's own finish, not the watch's or the italic's
    # finished ink (a stamped glyph) standing apart from the strokes is kept
    # as it was finished: the corner rule, polish and jog closing are not
    # idempotent, and run again they changed a stamped C by a jog where an
    # accent stood near it (Ć's C was not C). So under a clip that leaves it
    # whole (the same polygon): until 1.014 any clip sent it round again, and
    # every Mono glyph has one (its cell), as has ø (its slash's): Mono's ǿ
    # was not ø, and the second finish of ø's slash junction at Bold came out
    # one way or the other as the last bits of a float fell (a stamp moved
    # by 1e-13 of a unit turned it), so two builds of one code differed
    done = [q for f in finished for q in getattr(f, 'geoms', [f]) if isinstance(q, Polygon) and q.area > 1e-9]
    for poly in u.geoms:
        poly = orient(poly, sign=1.0)
        if any(abs(poly.area - f.area) <= 1e-6 * max(f.area, 1.0)
               and poly.symmetric_difference(f).area <= 1e-6 * max(f.area, 1.0) for f in done):
            for r in [poly.exterior] + list(poly.interiors):
                pts = list(r.coords)[:-1]
                if r is poly.exterior or Polygon(r).area >= min_hole:
                    rings.append(pts)
            continue
        rings.append(_close_jogs(_polish(_ring_rule(list(poly.exterior.coords), c, +1, rec, butt, crotch, fill), POLISH * c, moved, facet and facet * c), JOG * c, moved, even))
        for hole in poly.interiors:
            if Polygon(hole).area < min_hole:                # a counter too small to see is ink
                continue
            rings.append(_close_jogs(_polish(_ring_rule(list(hole.coords), c, +1, rec, butt, crotch, fill), POLISH * c, moved, facet and facet * c), JOG * c, moved, even))
    if overlay:
        rings = _lay_over(rings, overlay, thick, c, clip, rec, butt, moved, min_hole, segs, crotch)
    if rec is not None and moved:
        _follow(rec, moved)
    if tags is not None:
        segs.extend(extra_edges)
        if clip is not None:
            b = list(clip.exterior.coords)
            segs.extend((b[k], b[k + 1], ('clip', k)) for k in range(len(b) - 1))
        tags.extend(_name_edges(r, segs) for r in rings)
    return rings


def _lay_over(rings, overlay, thick, c, clip, rec, butt, moved, min_hole, segs, crotch=2.0):
    """``ink``'s overlay: each stroke finished alone on its own chamfer leg
    (cut at the clip first, as any stroke is), then the finished ink and the
    finished overlays joined. Rings as ``ink`` returns them. The join
    loses only the edges of less than JOIN_SLIVER it makes where the bar's
    edge passes a letter's point a fraction of a unit off (_polish on that
    alone), and the white narrower than that (_fill_slits on that alone);
    every edge and white wider stays, so nothing jumps as the weight moves
    (a polish on the chamfer's share took the 10 units of Ѣ's stem between
    its bowl and its bar at 840, and a notch of the stem with it)."""
    pieces = []
    for i, (st, c_ov) in enumerate(overlay):
        e = [] if segs is not None else None
        poly = stroke_polygon(st, thick, c_ov, rec, edges=e)
        if e:
            segs.extend((a, b, ('o', i) + t) for a, b, t in e)
        if clip is not None:
            poly = poly.intersection(clip)
        poly = shapely.make_valid(poly)
        for q in getattr(poly, 'geoms', [poly]):
            if not isinstance(q, Polygon) or q.area <= 1e-9:
                continue
            q = orient(q, sign=1.0)
            out = _close_jogs(_polish(_ring_rule(list(q.exterior.coords), c_ov, +1, rec, butt, crotch),
                                      POLISH * c_ov, moved), JOG * c_ov, moved)
            holes = [_close_jogs(_polish(_ring_rule(list(h.coords), c_ov, +1, rec, butt, crotch), POLISH * c_ov, moved),
                                 JOG * c_ov, moved) for h in q.interiors]
            pieces.append(Polygon(out, holes))
    if not pieces:
        return rings
    if rec is not None:
        rec.extend(_hidden_ends(rings, shapely.union_all(pieces)))
    u = shapely.make_valid(shapely.union_all([rings_to_shapely(rings)] + pieces))
    if not butt:
        # white the join leaves under JOIN_SLIVER across (an overlay's edge passing a letter's corner a
        # fraction of a unit off: ∄'s slash at Thin in the italic) is a hairline, never a design's
        u = _fill_slits(u, JOIN_SLIVER / 2)
    given = {(round(q[0], 6), round(q[1], 6)) for r in rings for q in r}
    given |= {(round(q[0], 6), round(q[1], 6)) for pc in pieces for r in [pc.exterior] + list(pc.interiors)
              for q in r.coords}
    out = []
    for poly in getattr(u, 'geoms', [u]):
        if not isinstance(poly, Polygon) or poly.area <= 1e-9:
            continue
        poly = orient(poly, sign=1.0)
        out.append(_polish(_straight(list(poly.exterior.coords)[:-1], given), JOIN_SLIVER, moved))
        out += [_polish(_straight(list(h.coords)[:-1], given), JOIN_SLIVER, moved)
                for h in poly.interiors if Polygon(h).area >= min_hole]
    return out


def _hidden_ends(rings, over):
    """Record entries for the 45-degree edges of the finished ink that the
    overlay ``over`` covers in part: ('hid', where a piece of the edge now
    ends, where the edge ended, the direction of the edge that went on from
    there, 'end' or 'start'). The italic curves such a chamfer as the
    letter's own and keeps the parts the overlay leaves showing
    (``italic._ends``, ``_cover``): the ǥ's hook, its bend under the bar,
    curved as the g's; the O's corners under Ø's slash, curved as the O's.
    One treatment however the overlay lies on the edge (over one end, across
    its middle, an end just out from under it), so nothing flips as the
    weight moves the edge under the overlay (Ø's italic at 451)."""
    from shapely.geometry import LineString, Point
    out = []
    for r in rings:
        n = len(r)
        for i in range(n):
            a, b = tuple(r[i][:2]), tuple(r[(i + 1) % n][:2])
            d = _sub(b, a)
            if _len(d) < 1e-6 or abs(abs(d[0]) - abs(d[1])) > 1e-4 * _len(d):
                continue
            nxt, prev = tuple(r[(i + 2) % n][:2]), tuple(r[i - 1][:2])
            a_in, b_in = over.contains(Point(a)), over.contains(Point(b))
            cut = LineString([a, b]).intersection(over.boundary)
            pts = [(q.x, q.y) for q in getattr(cut, 'geoms', [cut]) if q.geom_type == 'Point']
            if not a_in and not b_in and len(pts) >= 2:
                # across its middle: a piece shows either side, one hidden at its end, the other at
                # its start (an end within a sliver of the overlay leaves a piece the join's polish takes)
                out.append(('hid', min(pts, key=lambda q: math.dist(q, a)), b, _sub(nxt, b), 'end'))
                out.append(('hid', min(pts, key=lambda q: math.dist(q, b)), a, _sub(a, prev), 'start'))
            elif b_in and not a_in and pts:
                out.append(('hid', min(pts, key=lambda q: math.dist(q, a)), b, _sub(nxt, b), 'end'))
            elif a_in and not b_in and pts:
                out.append(('hid', min(pts, key=lambda q: math.dist(q, b)), a, _sub(a, prev), 'start'))
            elif not a_in and not b_in:
                # an end on the overlay's edge, or a sliver off it (the join's polish takes the sliver
                # and moves the end onto the edge): covered as it comes out from under it, the edge
                # that went on from it is the letter's (ǥ's hook at 648 in the italic)
                da, db = over.distance(Point(a)), over.distance(Point(b))
                if db <= JOIN_SLIVER < da:
                    out.append(('hid', b, b, _sub(nxt, b), 'end'))
                elif da <= JOIN_SLIVER < db:
                    out.append(('hid', a, a, _sub(a, prev), 'start'))
    return out


def _straight(ring, given):
    """A ring without the points the join made on a straight edge (where an
    edge of one piece ran on along an edge of the other): a point of the
    pieces themselves (``given``) stays, as they were finished."""
    pts = list(ring)
    changed = True
    while changed and len(pts) > 3:
        changed = False
        for i in range(len(pts)):
            a, b, q = pts[i - 1], pts[i], pts[(i + 1) % len(pts)]
            if (round(b[0], 6), round(b[1], 6)) in given:
                continue
            u, v = _sub(b, a), _sub(q, b)
            if _len(u) < 1e-9 or _len(v) < 1e-9 or (abs(_cross(u, v)) <= 1e-9 * _len(u) * _len(v) and _dot(u, v) > 0):
                del pts[i]
                changed = True
                break
    return pts


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
FACET = 0.5         # a wall of white between two cuts shorter than this share of the chamfer leg closes to a point (_polish)
SLIT = 0.35         # white narrower than twice this share of the chamfer leg, and long, is a slit
JOIN_SLIVER = 1.5   # font units: an edge shorter than this, where an overlay joins the letter, is a point (_lay_over); over the topology check's TINY with the italic's shear to spare


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


def _line_meet(p1, d1, p2, d2):
    """Where the line through p1 along d1 meets the line through p2 along
    d2 (None if they are parallel)."""
    den = _cross(d1, d2)
    if abs(den) < 1e-9:
        return None
    t = _cross(_sub(p2, p1), d2) / den
    return _add(p1, _mul(d1, t))


def _past(q, far, near) -> bool:
    """Whether q, on the line through ``far`` and ``near``, lies at or beyond
    ``far`` (seen from ``near``): a point slid along the edge near-far has
    run off its end."""
    return _dot(_sub(q, far), _sub(near, far)) <= 1e-9


def _close_jogs(pts, eps, moved, even=None):
    """Steps left where strokes that should share a line miss it, larger
    than _polish's slivers but still far smaller than a drawn step (a pixel
    step is a module; this is at most a corner break): a short edge between
    two edges running the same way. The shorter of those two moves onto the
    longer's line, its far end sliding along its own other neighbour, and
    the step's two vertices go: every edge keeps its direction (a right
    angle stays one, a diagonal stays on its 45 or 2:1), only lengths change.
    A move that would carry a point further than the step is long and a
    module more is not made (the step is a feature, not a miss), nor one
    that would carry it past the far end of the edge it slides along (the
    edge would turn round and the outline cross itself: under the ç at
    Black, where the c's corner, a flat of 33 units and the fill into the
    cedilla's stem stand over a stem side of 25, the fill slid 33 down it).
    A vertex
    bending less than STRAY degrees between two long edges also goes.
    Choices are made by geometry alone, so a symmetric drawing stays
    symmetric.

    ``even``: a step shorter than this between two edges of the same
    length closes too, each edge moving half the step onto the line
    between them. Without it such a step stands (there is no shorter side
    to move), and two cuts of one leg are exactly that: under the stub of a
    bar that crosses a stem (f t l, the 4) its end's break and the fill
    into the stem are both a break's chord, and as the stub shortens with
    the weight the flat between them went 40 units, 10, 8, none: at Medium
    and SemiBold a crumb, where at Bold the two were one plane."""
    pts = list(pts)
    # vertices on a straight line (a stroke's end inside another's edge):
    # no corner there, and they hide the jogs beside them
    i = 0
    while len(pts) > 3 and i < len(pts):
        n = len(pts)
        a, b, c2 = pts[i - 1], pts[i], pts[(i + 1) % n]
        u, v = _sub(b, a), _sub(c2, b)
        if _len(u) > 1e-9 and _len(v) > 1e-9 and abs(_cross(_unit(u), _unit(v))) < 0.005 and _dot(u, v) > 0:
            moved[b] = b
            del pts[i]
            continue
        i += 1
    cx = (min(p[0] for p in pts) + max(p[0] for p in pts)) / 2 if pts else 0.0
    skip = set()
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
        parallel = _dot(u_in, u_out) > math.cos(math.radians(10))
        stepping = abs(_cross(u_in, u_s)) > math.sin(math.radians(30))
        if not (parallel and stepping):
            skip.add((a, b))
            continue
        limit = _len(step) + eps
        if abs(_len(e_in) - _len(e_out)) < 1e-6:           # no shorter side: both move, half the step each (``even``)
            mid = _mul(_add(a, b), 0.5)
            close = even is not None and _len(step) < even
            q1 = _line_meet(pp, _sub(prev, pp), mid, u_in) if close else None
            q2 = _line_meet(nn, _sub(nxt, nn), mid, u_in) if close else None
            if q1 is None or q2 is None or max(_len(_sub(q1, prev)), _len(_sub(q2, nxt))) > limit \
                    or len({hh, h, i, j, k, kk}) < 6 or _past(q1, pp, prev) or _past(q2, nn, nxt):
                skip.add((a, b))
                continue
            moved[prev] = q1
            moved[nxt] = q2
            moved[a] = mid
            moved[b] = mid
            pts[h] = q1
            pts[k] = q2
            for idx in sorted((i, j), reverse=True):
                del pts[idx]
            continue
        if _len(e_in) < _len(e_out):                       # the incoming edge moves onto the outgoing's line
            q = _line_meet(pp, _sub(prev, pp), b, u_out)
            if q is None or _len(_sub(q, prev)) > limit or len({hh, h, i, j}) < 4 or _past(q, pp, prev):
                skip.add((a, b))
                continue
            moved[prev] = q
            moved[a] = q
            moved[b] = q
            pts[h] = q
            for idx in sorted((i, j), reverse=True):
                del pts[idx]
        else:                                               # the outgoing edge moves onto the incoming's line
            q = _line_meet(nn, _sub(nxt, nn), a, u_in)
            if q is None or _len(_sub(q, nxt)) > limit or len({i, j, k, kk}) < 4 or _past(q, nn, nxt):
                skip.add((a, b))
                continue
            moved[nxt] = q
            moved[a] = q
            moved[b] = q
            pts[k] = q
            for idx in sorted((i, j), reverse=True):
                del pts[idx]
    # stray vertices: a barely bent long edge
    long_ = 4 * eps
    changed = True
    while changed and len(pts) > 4:
        changed = False
        n = len(pts)
        for i in range(n):
            a, b, c2 = pts[i - 1], pts[i], pts[(i + 1) % n]
            u, v = _sub(b, a), _sub(c2, b)
            if _len(u) < long_ or _len(v) < long_:
                continue
            t = abs(math.degrees(math.atan2(_cross(_unit(u), _unit(v)), _dot(_unit(u), _unit(v)))))
            if 1e-6 < t < STRAY:
                moved[b] = b
                del pts[i]
                changed = True
                break
    return pts


def _polish(pts, eps, moved, facet=None):
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

    ``facet``: a longer reach for the second kind where both turns are into
    the ink, the facet a wall of white between two cuts (FACET: a counter a
    little taller than its two corners' cuts keeps a wall of a few units
    between them, as it closes with the weight: the a's bowl 13 units at
    SemiBold, its upper storey 17 at Bold, the G's pocket 20 at Black).
    Such a wall under half a break is no wall: the cuts run on and meet in
    a point, in the white's own corner, and the outline's reach is as it
    was.

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
            if (a, b) not in skip and (L < eps or (facet is not None and L < facet
                                                   and _white_facet(pts[i - 1], a, b, pts[(i + 2) % n]))):
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
            if q is None or _len(_sub(q, _mul(_add(a, b), 0.5))) > 2 * max(eps, facet or 0.0):
                skip.add((a, b))
                continue
            moved[a] = q
            moved[b] = q
            pts[i] = q
            del pts[j]
        else:
            skip.add((a, b))
    return pts


def _white_facet(prev, a, b, nxt) -> bool:
    """Whether the edge a-b is a wall of white between two cuts: the ring
    (ink on its left) turns right at both its ends, by 30 to 60 degrees
    each, a quarter turn in all. Not beside a doubled point: that edge,
    the shortest there is, goes first, and this one is asked again (the
    hourglass in Arris Mono Narrow Bold has one, and the build stopped on
    its direction)."""
    e0, e1, e2 = _sub(a, prev), _sub(b, a), _sub(nxt, b)
    if min(_len(e0), _len(e1), _len(e2)) < 1e-9:
        return False
    u0, u1, u2 = _unit(e0), _unit(e1), _unit(e2)
    t1 = math.degrees(math.atan2(_cross(u0, u1), _dot(u0, u1)))
    t2 = math.degrees(math.atan2(_cross(u1, u2), _dot(u1, u2)))
    return -60 < t1 < -30 and -60 < t2 < -30


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
        elif r and r[0] == 'hid':
            rec[i] = ('hid', near(r[1])) + tuple(r[2:])


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
