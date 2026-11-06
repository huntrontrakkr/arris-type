"""The italic: the same drawings, slanted, with curves where the upright
cuts chamfers.

* **Slant.** Every outline is sheared by ``SLANT_DEG`` about half the
  x-height, so a glyph keeps its place and its advance, and the upright's
  spacing carries over. Stroke weights are set before the shear so every
  stroke comes out as heavy across as its upright self (``geom.Thickness``):
  a shear alone would thin the strokes that lean with it and thicken those
  that lean against it.
* **Curves.** Every chamfer the drawing recorded as one (a bowl's corner,
  an edge break, the steps of the 2's notch and the 4's clip) becomes a
  quadratic curve tangent to the edges it joins, its control point the
  corner it cut. A bowl's corner curves on both its edges or on neither,
  and its inner curve is drawn on shorter legs than the chamfer's, so the
  stroke keeps its own weight round the bend (``_even_bend``).
* **Sharp where the upright is sharp.** Corners the upright never chamfers
  stay sharp: beaks, the 3's and 8's waists, the meeting of two diagonals,
  a diagonal's end. Soft bowls against those points are what keeps the
  italic Arris. A bowl whose inner edge only ends at such a point (the e's
  bowl at its bar, the s's at its spine, the j's hook) curves both edges,
  and the point stays a point.
* **Italic forms.** Where a glyph has an italic drawing (``name.ital``),
  the italic uses it (``draw.draw``): the single-storey a, the descending f.
"""
from __future__ import annotations

import math

from .params import Params

SLANT_DEG = 10.0
SLANT = math.tan(math.radians(SLANT_DEG))

_TOL = 1e-6


def italic(p: Params) -> Params:
    return p.with_(slant=SLANT)


def _axis(v) -> bool:
    n = math.hypot(*v)
    return n > _TOL and (abs(v[0]) <= 1e-4 * n or abs(v[1]) <= 1e-4 * n)


def _diag(v) -> bool:
    n = math.hypot(*v)
    return n > _TOL and abs(abs(v[0]) - abs(v[1])) <= 1e-4 * n


def _cross(a, b) -> float:
    return a[0] * b[1] - a[1] * b[0]


def _meet(p0, p1, q0, q1):
    """Intersection of the lines p0-p1 and q0-q1 (both axis-parallel here)."""
    d1 = (p1[0] - p0[0], p1[1] - p0[1])
    d2 = (q1[0] - q0[0], q1[1] - q0[1])
    den = _cross(d1, d2)
    t = _cross((q0[0] - p0[0], q0[1] - p0[1]), d2) / den
    return (p0[0] + t * d1[0], p0[1] + t * d1[1])


ON = 0.5   # font units: how near a segment must lie to a recorded chamfer


def _owners(a, b, record):
    """The recorded corners the segment a-b may belong to: [(owner, line,
    along)], ('bowl', index) for each of a bowl's two chamfer lines it lies
    on (with how far along the line from where it was recorded the segment
    begins: 0 across the record, negative behind it), ('chord', index) for
    an edge break whose ends it is."""
    out = []
    for idx, r in enumerate(record):
        if r[0] in (SQUARE, HID):
            continue
        if r[0] == 'chord':
            if ((math.dist(a, r[1]) < ON and math.dist(b, r[2]) < ON)
                    or (math.dist(a, r[2]) < ON and math.dist(b, r[1]) < ON)):
                out.append((('chord', idx), 0, 0.0))
        else:
            for k, (q, d) in enumerate(r[1:]):
                if all(abs(_cross((pt[0] - q[0], pt[1] - q[1]), d)) < ON for pt in (a, b)):
                    # where the segment lies along the line from the recorded point
                    u = ((a[0] - q[0]) * d[0] + (a[1] - q[1]) * d[1], (b[0] - q[0]) * d[0] + (b[1] - q[1]) * d[1])
                    dd = math.hypot(*d) or 1.0
                    along = 0.0 if min(u) <= 0 <= max(u) else min(u, key=abs) / dd
                    out.append((('bowl', idx), k, along))
    return out


def _joins_smoothly(v, seg) -> bool:
    """Whether a chamfer meets the edge v as a corner it stands in for: a
    horizontal or vertical edge, or a diagonal running straight on. Any
    other meeting is a point the upright keeps sharp (a waist, a beak's
    tip against a diagonal)."""
    return _axis(v) or (_diag(v) and abs(_cross(v, seg)) <= 1e-4 * math.hypot(*v) * math.hypot(*seg))


SQUARE = 'square'   # a record entry: the glyph's edge breaks against a square diagonal curve (_segments)
HID = 'hid'         # a record entry: a 45-degree edge an overlay covers at one end (geom._hidden_ends)
HID_AT = 1e-3       # font units: how near a ring's point must lie to where a hidden edge now ends
PIECE_MIN = 2.0     # font units: a chamfer showing past an overlay by less is a sliver, its ends one point (_cover); a curve shorter has control legs under the topology check's TINY


def _hidden(record):
    return [r for r in record if r and r[0] == HID]


def _ends(a, b, vin, vout, hid):
    """(a, b, vin, vout, a hidden, b hidden) for the ring's edge a-b: where
    it ends in the letter itself when an overlay (``geom.ink``'s overlay, a
    bar laid over the letter) covers one of its ends, and the edge that went
    on from there; as given otherwise. The chamfer is curved as the letter's
    own, and the overlay keeps covering what it covered (_cover)."""
    ha = hb = False
    for _, at, full, d, which in hid:
        if which == 'end' and math.dist(b, at) < HID_AT:
            # an end on the overlay's edge is the letter's own: its edge, not cut
            b, vout, hb = tuple(full), tuple(d), math.dist(b, full) >= HID_AT
        elif which == 'start' and math.dist(a, at) < HID_AT:
            a, vin, ha = tuple(full), tuple(d), math.dist(a, full) >= HID_AT
    return a, b, vin, vout, ha, hb


def _square(v, seg) -> bool:
    """Whether the edge v is a 45-degree edge square to the chamfer seg: the
    axis edge between them shrunk to nothing (a counter whose side closed
    to a point as the weight grew)."""
    return _diag(v) and abs(v[0] * seg[0] + v[1] * seg[1]) <= 1e-4 * math.hypot(*v) * math.hypot(*seg)


def _corner(a, b, turn_left):
    """The corner a 45-degree chamfer a-b cut: where the horizontal and the
    vertical through its ends meet, outside the ink for a cut (left turns,
    ink on the left), inside it for a fill."""
    c1, c2 = (a[0], b[1]), (b[0], a[1])
    seg = (b[0] - a[0], b[1] - a[1])
    side = _cross(seg, (c1[0] - a[0], c1[1] - a[1]))       # > 0: c1 on the left of a-b
    return c1 if (side > 0) != turn_left else c2


FAR = 1.0    # font units: a bowl's line claims a segment this far from where it was recorded only if no edge break owns it
NEAR = 2.0   # breaks: within this of its record a chamfer is its own however it got there; beyond, only ahead of it and through ink


def _inside(pt, rings_) -> bool:
    """Whether a point is in the ink the rings bound (even-odd)."""
    x, y = pt
    inside = False
    for ring in rings_:
        pts = [tuple(q) for q in ring]
        n = len(pts)
        for i in range(n):
            (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
            if (y0 > y) != (y1 > y) and x0 + (y - y0) * (x1 - x0) / (y1 - y0) > x:
                inside = not inside
    return inside


def _through_ink(q, e, rings_, step) -> bool:
    """Whether the stretch from q to e lies in ink, sampled every step."""
    n = max(2, math.ceil(math.dist(q, e) / step))
    return all(_inside((q[0] + (e[0] - q[0]) * t / n, q[1] + (e[1] - q[1]) * t / n), rings_) for t in range(1, n))


def _segments(rings_, record, p: Params):
    """Every 45-degree recorded chamfer in the rings: (ring, i, owner,
    smooth, turn_left, corner). Each recorded chamfer line is one edge: the
    segment on it nearest where it was recorded. Within NEAR breaks of the
    record any segment is the chamfer's own (polish and stamping move one a
    few units); further, only one ahead of the record along the chamfer
    with ink all the way from the record to it, the rest of a chamfer whose
    start another stroke swallowed (the ρ's bowl at its stem, the æ's, the
    8's waist at its spine), and never an edge break's (the italic y's flag
    at 850, 181 units along its bowl's line). A 45-degree line runs on, and
    another edge can lie on it: an accent's corner on the line of a corner
    of the letter under it, which claimed it and, holding the accent's
    sharp end, held its own curve straight, so á's a was not a's; the Ǒ's
    caron on the O's line at Black, through the O's stroke and the white
    above it; the K's leg behind the Қ's descender corner at 300/-100,
    which claimed and curved it to a corner far off it, a lens cut out of
    the leg."""
    square = any(r and r[0] == SQUARE for r in record)
    square_bowls = any(r and r[0] == SQUARE and r[1:] == ('bowl',) for r in record)
    hid = _hidden(record)
    claims = {}
    pieces = {}                                             # (ring, index): the whole chamfer an overlay cut it from
    for ri, ring in enumerate(rings_):
        pts = [tuple(q) for q in ring]
        n = len(pts)
        for i in range(n):
            a, b = pts[i], pts[(i + 1) % n]
            if not _diag((b[0] - a[0], b[1] - a[1])):
                continue
            if hid:
                a, b, _, _, ha, hb = _ends(a, b, None, None, hid)
                if ha or hb:
                    pieces[(ri, i)] = (a, b)
            for own, k, along in _owners(a, b, record):
                key = (own, k)
                if own[0] == 'chord' or key not in claims or abs(along) < abs(claims[key][0]):
                    claims[key] = (along, ri, i)
    breaks = {(ri, i) for (own, _), (_, ri, i) in claims.items() if own[0] == 'chord'}
    owner = {}
    for (own, k), (along, ri, i) in claims.items():
        if own[0] == 'bowl' and abs(along) > FAR:
            if (ri, i) in breaks:
                continue
            if abs(along) > NEAR * p.c:
                pts = rings_[ri]
                a, b = tuple(pts[i]), tuple(pts[(i + 1) % len(pts)])
                q, d = record[own[1]][1 + k]
                near = min((a, b), key=lambda e: abs((e[0] - q[0]) * d[0] + (e[1] - q[1]) * d[1]))
                if along < 0 or not _through_ink(q, near, rings_, p.c / 2):
                    continue
        owner.setdefault((ri, i), own)
    # an overlay across a chamfer's middle leaves two pieces of it showing (Ø's slash over the O's
    # corners): each is the chamfer's, curved as the whole and cut where the overlay crosses it (_cover)
    for key, whole in pieces.items():
        if key in owner:
            continue
        for other, own in list(owner.items()):
            w2 = pieces.get(other)
            if w2 is not None and all(math.dist(u, v) < HID_AT for u, v in zip(whole, w2)):
                owner[key] = own
                break
    out = []
    for ri, ring in enumerate(rings_):
        pts = [tuple(q) for q in ring]
        n = len(pts)
        for i in range(n):
            a, b = pts[i], pts[(i + 1) % n]
            seg = (b[0] - a[0], b[1] - a[1])
            own = owner.get((ri, i))
            if own is None:
                continue
            prev, nxt = pts[i - 1], pts[(i + 2) % n]
            vin = (a[0] - prev[0], a[1] - prev[1])
            vout = (nxt[0] - b[0], nxt[1] - b[1])
            if hid:
                vin, vout = _ends(a, b, vin, vout, hid)[2:4]
            t1, t2 = _cross(vin, seg), _cross(seg, vout)
            turns = [t for t in (t1, t2) if abs(t) > 1e-6 * math.hypot(*seg)]
            corner = bool(turns) and not (len(turns) == 2 and (turns[0] > 0) != (turns[1] > 0))
            # an S-bend or a straight run is no corner: it cannot curve, and holds its pair straight
            smooth = corner and _joins_smoothly(vin, seg) and _joins_smoothly(vout, seg)
            if square and (own[0] == 'chord' or square_bowls) and corner and not smooth:
                # an edge break against a 45-degree edge square to it stands where an axis edge
                # between them shrank to nothing: curved as it was while that edge was there (the
                # italic k's counter, its side a point at 665 on the heavy grade, curved again at 675).
                # The k's alone (SQUARE in its record): everywhere it changed 511 italic glyphs.
                # ₴'s bowl corners as well (('square', 'bowl')): the right side between its top
                # corner and the spine shrank to nothing from 700 and, the watch's strokes eased past
                # Bold, came back nine units long at Black on the light grade
                smooth = all(_joins_smoothly(v, seg) or _square(v, seg) for v in (vin, vout))
            out.append((ri, i, own, smooth, corner and turns[0] > 0, corner))
    return out


def _ring_pts(ring):
    pts = [tuple(q) for q in ring]
    if len(pts) > 1 and math.dist(pts[0], pts[-1]) < _TOL:
        pts = pts[:-1]
    return pts


def _even_bend(rings_, segs, curved, p: Params, hid=()):
    """{(ring, index): k} for the inner chamfers whose legs shrink to k of
    their own, toward the corner they cut (_cover moves the ends): that
    keeps a curved bowl corner's stroke as heavy round the bend as along
    its chamfer.

    The corner's two edges are 45-degree chamfers with legs Lo (outer) and Li
    (inner), each made a quadratic curve whose control point is the corner
    it cut. A quadratic's apex lies a quarter of its leg from that corner
    along the diagonal, so with both curves on their chamfers' legs the
    stroke is (Lo - Li) / (2 sqrt 2) wider at the bend than the chamfer:
    a fifth with equal strokes, a quarter at Thin (the italic o, c and e
    swelled at their corners). Drawn on legs 2 Li - Lo, the inner curve's
    apex lies exactly a chamfer's width inside the outer's; its control
    point stays at its corner and its ends slide along the edges it joins,
    so the silhouette is unchanged and the counter's corner a little
    tighter. Never under the edge break c (the upright's own inner rule):
    at the heaviest weights the bend keeps part of its swell. Only where
    both edges the inner chamfer joins are horizontal or vertical."""
    pairs: dict = {}
    for ri, i, own, *_ in segs:
        if own[0] == 'bowl' and (ri, i) in curved:
            pairs.setdefault(own, []).append((ri, i))
    out = {}
    for own, edges in pairs.items():
        whole: dict = {}                                    # the pieces of one chamfer (an overlay across it) are one edge
        for ri, i in edges:
            e = _edge(rings_[ri], i, hid)
            key = (round(e[0][0], 3), round(e[0][1], 3), round(e[1][0], 3), round(e[1][1], 3))
            whole.setdefault(key, (e, []))[1].append((ri, i))
        if len(whole) != 2:
            continue
        (e1, k1), (e2, k2) = whole.values()
        legs = [abs(e1[1][0] - e1[0][0]), abs(e2[1][0] - e2[0][0])]
        (lo, _), (li, j) = sorted(zip(legs, range(2)), reverse=True)
        e, keys = (e1, k1) if j == 0 else (e2, k2)
        target = max(p.c, 2 * li - lo)
        if li - target < 0.5:
            continue
        _, _, vin, vout, _, _ = e
        if not (_axis(vin) and _axis(vout)):
            continue
        for key in keys:
            out[key] = target / li
    return out


def _edge(ring, i, hid=()):
    """_ends of the ring's edge from its point i."""
    pts = _ring_pts(ring)
    n = len(pts)
    a, b = pts[i], pts[(i + 1) % n]
    vin = (a[0] - pts[i - 1][0], a[1] - pts[i - 1][1])
    vout = (pts[(i + 2) % n][0] - b[0], pts[(i + 2) % n][1] - b[1])
    return _ends(a, b, vin, vout, hid) if hid else (a, b, vin, vout, False, False)


def _roots01(c0, c1, c2):
    """The roots of c0 + c1 t + c2 t^2 in [0, 1], ascending. Solved in the
    stable form: a 45-degree overlay across a 45-degree chamfer leaves c2 a
    rounding error, and the textbook formula lost the real root to it (Ø's
    slash over the O's corner, in Mono's italic)."""
    scale = abs(c0) + abs(c1) + abs(c2)
    if scale == 0.0:
        return []
    if abs(c2) <= 1e-9 * scale:
        return [] if abs(c1) <= 1e-12 * scale else [t for t in (-c0 / c1,) if -1e-9 <= t <= 1 + 1e-9]
    disc = c1 * c1 - 4 * c2 * c0
    if disc < 0:
        return []
    q = -0.5 * (c1 + math.copysign(math.sqrt(disc), c1))
    ts = [q / c2] + ([c0 / q] if q != 0.0 else [])
    return sorted(t for t in ts if -1e-9 <= t <= 1 + 1e-9)


def _cover(rings_, curved, bend, hid):
    """({(ring, index): moved point}, {(ring, index): control}) for the
    curved chamfers an even bend shortens (bend: their k) or an overlay
    covers in part. The curve is the letter's own, on its full chamfer
    (shortened by k), with the control point at the corner it cut; where an
    overlay covers part of it, the parts it leaves showing: the same curve
    cut where it passes under the overlay's edge (the ring's point there
    moves along that edge to meet it), its control the cut curve's own, so
    the showing part lies exactly on the whole. An even bend stops short of
    taking a covered end out from under the overlay, or a showing end in
    under it, and every piece of one chamfer bends alike (Mono's light ø,
    the slash over its counter's corners, kept each half's end in the open)."""
    def side(q, at, d):
        return _cross(d, (q[0] - at[0], q[1] - at[1]))

    def k_on(C, end, at, d):
        den = side((C[0] + (end[0] - C[0]), C[1] + (end[1] - C[1])), C, d)
        return side(at, C, d) / den if abs(den) > 1e-12 else 1.0

    def bent(C, end, k):
        return (C[0] + (end[0] - C[0]) * k, C[1] + (end[1] - C[1]) * k)
    items, group_k = [], {}
    for (ri, i), left in curved.items():
        pts = _ring_pts(rings_[ri])
        n = len(pts)
        a, b = pts[i], pts[(i + 1) % n]
        A, B, _, _, ha, hb = _edge(rings_[ri], i, hid)
        k = bend.get((ri, i))
        if k is None and not (ha or hb):
            continue
        k = 1.0 if k is None else k
        C = _corner(A, B, left)
        # the overlay's edges the covered ends pass under: through the ring's point, along its next (or last) edge
        lines = []
        if hb:
            lines.append((b, (pts[(i + 2) % n][0] - b[0], pts[(i + 2) % n][1] - b[1]), B, A))
        if ha:
            lines.append((a, (a[0] - pts[i - 1][0], a[1] - pts[i - 1][1]), A, B))
        for at, d, covered, showing in lines:
            if side(covered, at, d) * side(bent(C, covered, k), at, d) <= 0:
                k = max(k, min(1.0, k_on(C, covered, at, d)))
            if len(lines) == 1 and side(showing, at, d) * side(bent(C, showing, k), at, d) <= 0:
                k = max(k, min(1.0, k_on(C, showing, at, d)))
        key = (round(A[0], 3), round(A[1], 3), round(B[0], 3), round(B[1], 3))
        group_k[key] = max(group_k.get(key, 0.0), k)
        items.append((ri, i, n, A, B, C, lines, ha, hb, key))
    moved, controls = {}, {}
    for ri, i, n, A, B, C, lines, ha, hb, key in items:
        k = group_k[key]
        A1, B1 = bent(C, A, k), bent(C, B, k)
        al = A1
        be = (2 * (C[0] - A1[0]), 2 * (C[1] - A1[1]))
        ga = (A1[0] - 2 * C[0] + B1[0], A1[1] - 2 * C[1] + B1[1])
        t0, t1 = 0.0, 1.0
        if hb:
            at, d = lines[0][0], lines[0][1]
            rr = _roots01(_cross(d, (al[0] - at[0], al[1] - at[1])), _cross(d, be), _cross(d, ga))
            t1 = min(rr) if rr else 1.0
        if ha:
            at, d = lines[-1][0], lines[-1][1]
            rr = _roots01(_cross(d, (al[0] - at[0], al[1] - at[1])), _cross(d, be), _cross(d, ga))
            t0 = max(rr) if rr else 0.0
        t0, t1 = max(0.0, min(1.0, t0)), max(0.0, min(1.0, t1))

        def Q(t):
            return ((1 - t) ** 2 * A1[0] + 2 * t * (1 - t) * C[0] + t * t * B1[0],
                    (1 - t) ** 2 * A1[1] + 2 * t * (1 - t) * C[1] + t * t * B1[1])
        q0, q1 = Q(t0), Q(t1)
        if (ha or hb) and math.dist(q0, q1) < PIECE_MIN:
            # the chamfer only just shows past the overlay: a sliver, not a curve; its ends meet where
            # it goes under (₩ ₸ ₥ in the italic at 850 on the light grade)
            q = q1 if hb else q0
            moved[(ri, i)] = moved[(ri, (i + 1) % n)] = q
            controls[(ri, i)] = None
            continue
        moved[(ri, i)] = q0
        moved[(ri, (i + 1) % n)] = q1
        if ha or hb:
            w0, w1, w2 = (1 - t0) * (1 - t1), (1 - t0) * t1 + t0 * (1 - t1), t0 * t1
            controls[(ri, i)] = (w0 * A1[0] + w1 * C[0] + w2 * B1[0], w0 * A1[1] + w1 * C[1] + w2 * B1[1])
    return moved, controls


def _plan_full(rings_, p: Params, record):
    """({(ring, index): turn_left} for the segments that curve, {(ring,
    index): moved point}, {(ring, index): control point} where it is not
    the corner the segment cut) for a drawing (see curve_rings)."""
    segs = _segments(rings_, record, p)
    edges: dict = {}
    for s in segs:
        if s[2][0] == 'bowl':
            edges.setdefault(s[2], []).append(s)
    held = set()
    for own, ss in edges.items():
        outer = [s for s in ss if s[4]]              # the cut: a left turn, ink on the left
        inner = [s for s in ss if not s[4]]
        if any(not s[3] for s in outer) or any(not s[5] for s in inner) or \
                (not outer and any(not s[3] for s in inner)):
            held.add(own)
    curved = {(ri, i): left for ri, i, own, smooth, left, _ in segs
              if (own[0] == 'bowl' and own not in held) or (own[0] != 'bowl' and smooth)}
    hid = _hidden(record)
    moved, controls = _cover(rings_, curved, _even_bend(rings_, segs, curved, p, hid), hid)
    return curved, moved, controls


def _plan(rings_, p: Params, record):
    """({(ring, index): turn_left} for the segments that curve, {(ring,
    index): moved point}) for a drawing (see curve_rings)."""
    return _plan_full(rings_, p, record)[:2]


def curve_rings(rings_, p: Params, record):
    """Rings of points -> contours of (x, y, on_curve), in the upright frame,
    with their corners made curves.

    A bowl's corner is a pair of chamfers, the stroke's outer and inner
    edges, and they are curved together or not at all: a curve on one edge
    against a straight other would swell the stroke (or, bulging across it,
    cross the outline). Its inner curve is drawn on shorter legs, so the
    stroke keeps its weight round the bend (_even_bend). A corner whose
    outer edge meets a sharp point (a waist, a beak's tip, a diagonal
    junction) stays straight on both, so the point stays sharp, and so
    does one whose inner edge is no corner at all (an S-bend). An inner
    edge that only ends at such a point curves with its outer edge: held,
    it straightened the bowl at the weights where the bar or spine reached
    it (the italic e from 400, the s from 250 to 450, the j's hook), and
    curved at the others. Edge breaks curve on their own."""
    curved, moved, controls = _plan_full(rings_, p, record)
    out = []
    for ri, ring in enumerate(rings_):
        pts = _ring_pts(ring)
        n = len(pts)
        c = []
        for i in range(n):
            a, b = pts[i], pts[(i + 1) % n]
            m = moved.get((ri, i), a)
            c.append((m[0], m[1], True))
            if (ri, i) in curved and not ((ri, i) in controls and controls[(ri, i)] is None):
                q = controls.get((ri, i)) or _corner(a, b, curved[(ri, i)])
                c.append((q[0], q[1], False))
        out.append(c)
    return out


def shear(contour, p: Params):
    yc = p.xh / 2
    return [(x + (y - yc) * p.slant, y, on) for x, y, on in contour]


def split_warp(record):
    """(record without warps, the optical correction's warp or None)."""
    warps = [r[1] for r in record if r and r[0] == 'warp']
    return [r for r in record if not (r and r[0] == 'warp')], (warps[0] if warps else None)


def warped(contours, warp):
    if warp is None:
        return contours
    return [[(x, warp(y), on) for x, y, on in c] for c in contours]


def outline(rings, record, p: Params):
    """The italic outline: contours of (x, y, on), sheared, ink on the left
    (as the upright rings). Chamfers are found and curved on the exact
    drawing; the optical corrections (a warp in the record) then move the
    curved outline, and the shear comes last."""
    record, warp = split_warp(record)
    return [shear(c, p) for c in warped(curve_rings(rings, p, record), warp)]


def tt_contours(outline_):
    """Italic contours rounded, with TrueType orientation (outer clockwise)."""
    out = []
    for c in outline_:
        c = [(round(x), round(y), on) for x, y, on in c]
        clean = []
        for q in c:
            if clean and q[:2] == clean[-1][:2]:
                if q[2] and not clean[-1][2]:        # keep the on-curve point
                    clean[-1] = q
                continue
            clean.append(q)
        while len(clean) > 1 and clean[0][:2] == clean[-1][:2]:
            if clean[-1][2] and not clean[0][2]:
                clean[0] = clean[-1]
            clean.pop()
        if len(clean) >= 3:
            out.append(clean[::-1])
    return out


def draw_contours(pen, contours, dx=0.0):
    """Draw (x, y, on) contours on a segment pen: lines and quadratic curves."""
    for c in contours:
        k = next(i for i, q in enumerate(c) if q[2])
        c = c[k:] + c[:k]
        n = len(c)
        pen.moveTo((c[0][0] + dx, c[0][1]))
        i = 1
        while i <= n:
            q = c[i % n]
            if q[2]:
                if i < n:
                    pen.lineTo((q[0] + dx, q[1]))
                i += 1
            else:
                nxt = c[(i + 1) % n]
                pen.qCurveTo((q[0] + dx, q[1]), (nxt[0] + dx, nxt[1]))
                i += 2
        pen.closePath()


def flatten(contour, steps: int = 6):
    """A contour of (x, y, on) as a polyline, curves sampled."""
    n = len(contour)
    out = []
    for i, (x, y, on) in enumerate(contour):
        if on:
            out.append((x, y))
            continue
        a = contour[i - 1]
        b = contour[(i + 1) % n]
        for k in range(1, steps):
            t = k / steps
            out.append(((1 - t) ** 2 * a[0] + 2 * t * (1 - t) * x + t * t * b[0],
                        (1 - t) ** 2 * a[1] + 2 * t * (1 - t) * y + t * t * b[1]))
    return out


def polylines(outline_):
    """The italic outline as polylines, curves sampled (for kerning and
    proofs)."""
    return [flatten(c) for c in outline_]


# --- The variable italic ---------------------------------------------------

def _key(q):
    return (round(q[0], 6), round(q[1], 6))


def _chamfer_map(rings_, record, p: Params):
    """({(a, b): control} for every chamfer segment a-b a drawing curves,
    {a: moved a} for the ends an even bend slides), keyed by the drawing's
    own points."""
    curved, moved, given = _plan_full(rings_, p, record)
    controls, ends = {}, {}
    for (ri, i), left in curved.items():
        pts = _ring_pts(rings_[ri])
        a, b = pts[i], pts[(i + 1) % len(pts)]
        if (ri, i) in given and given[(ri, i)] is None:       # a sliver past an overlay: no curve
            continue
        controls[(_key(a), _key(b))] = given.get((ri, i)) or _corner(a, b, left)
    for (ri, i), m in moved.items():
        ends[_key(_ring_pts(rings_[ri])[i])] = m
    return controls, ends


def prepare_outlines(originals, records, params_):
    """What ``aligned_outlines`` reads of each master, made once: its warp,
    and its chamfer map from the record split from the warp (curved on the
    exact drawing, then moved: outline). The maps do not depend on the
    alignment, so one preparation serves every candidate alignment of a
    glyph."""
    out = []
    for o, r, p in zip(originals, records, params_):
        rec, warp = split_warp(r)
        out.append((warp, _chamfer_map(o, rec, p)))
    return out


def aligned_outlines(aligned, originals, records, params_, prepared=None):
    """Italic outlines for point-compatible upright masters
    (``variable.align``). A segment that is a chamfer in any master carries
    a control point in every master: at the corner it cut where it is a
    chamfer, at its middle (a straight curve) where it is not. So a curve
    grows from a straight edge as the weight moves, and every master has the
    same points with the same flags. ``prepared``: ``prepare_outlines`` of
    the masters, else made here."""
    k = len(aligned)
    if prepared is None:
        prepared = prepare_outlines(originals, records, params_)
    warps = [w for w, _ in prepared[:k]]
    maps = [m for _, m in prepared[:k]]
    out = [[] for _ in range(k)]
    for ci in range(len(aligned[0])):
        n = len(aligned[0][ci])
        curved = [any((_key(aligned[mi][ci][j]), _key(aligned[mi][ci][(j + 1) % n])) in maps[mi][0]
                      for mi in range(k)) for j in range(n)]
        for mi in range(k):
            ring = aligned[mi][ci]
            controls, ends = maps[mi]
            c = []
            for j in range(n):
                a, b = ring[j], ring[(j + 1) % n]
                m = ends.get(_key(a), a)                  # an even bend's end, slid toward its corner
                c.append((m[0], m[1], True))
                if curved[j]:
                    ctrl = controls.get((_key(a), _key(b)), ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2))
                    c.append((ctrl[0], ctrl[1], False))
            out[mi].append(shear(warped([c], warps[mi])[0], params_[mi]))
    return out
