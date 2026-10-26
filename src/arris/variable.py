"""The variable font: masters made point-compatible after the fact.

Every outline is a union of strokes cut by the corner rule, so the number
of points can differ between weights: a junction becomes a lump, a chamfer
uses up the straight beside it, an opening's free variable moves. A variable
font needs every master of a glyph to have the same contours with the same
points in the same order.

``align`` makes them so. Contours are matched across masters by kind (ink or
counter) and position. Within a matched contour, points are matched by a
sequence alignment on their normalised positions and turning directions.
A point that exists in one master but not another is inserted into the
others as a duplicate of the neighbour it is nearer to (where it exists):
a feature growing from nothing, or shrinking into a corner, as the weight
moves.

Masters are aligned one at a time, each against the master already aligned
that lies nearest it in the design space (``locs``): the outline it will be
interpolated with, so the two differ least. Aligned all against one master
(the thinnest, which has the most points), a heavy master whose strokes have
fused has several equally good-looking starts on the thin outline, and two
heavy neighbours could take different ones: their instances between turned
inside out (ℕ at the heavy grade-watch corner, 2026-10-25).

A glyph that is mirror-symmetric in every master (8, A, *) is aligned by
its left half, cut on its axis, and mirrored: aligned whole, a point
present in some masters only can be paired with a neighbour on one side
and the opposite neighbour on the other, and the instances between the
masters lean.

The result is checked rather than trusted. ``check`` draws the glyphs
exactly at weights between the masters and compares them with the variable
font's interpolation; the build reports the worst offenders.
"""
from __future__ import annotations

import itertools
import math

import numpy as np

GAP = 0.6           # alignment cost of a missing point, in normalised units (a match is preferred)
TURN = 0.5          # cost of matching points that turn differently
NAMED = 1.0         # cost of matching points whose names differ (half if they share a line; see vertex_names)


def _area(r):
    return sum(r[i - 1][0] * r[i][1] - r[i][0] * r[i - 1][1] for i in range(len(r))) / 2


def _turns(r):
    out = []
    n = len(r)
    for i in range(n):
        a, b, c = r[i - 1], r[i], r[(i + 1) % n]
        u = (b[0] - a[0], b[1] - a[1])
        v = (c[0] - b[0], c[1] - b[1])
        out.append(math.atan2(u[0] * v[1] - u[1] * v[0], u[0] * v[0] + u[1] * v[1]))
    return out


def _norm(rings):
    xs = [q[0] for r in rings for q in r]
    ys = [q[1] for r in rings for q in r]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    s = max(x1 - x0, y1 - y0, 1e-9)                         # one scale: keep the aspect
    return lambda q: ((q[0] - x0) / s, (q[1] - y0) / s)


def _match_contours(ref, other, nref, noth):
    """Permutation of other's contours matching ref's (None if impossible)."""
    if len(ref) != len(other):
        return None
    def feat(r, nf):
        pts = [nf(q) for q in r]
        xs, ys = [x for x, _ in pts], [y for _, y in pts]
        cx, cy = sum(xs) / len(pts), sum(ys) / len(pts)
        # a collapsed counter counts as a counter
        return (1 if _area(r) > 0 else -1, cx, cy, max(xs) - min(xs), max(ys) - min(ys))
    fr = [feat(r, nref) for r in ref]
    fo = [feat(r, noth) for r in other]
    n = len(ref)
    lines = lambda r: {x for q in r if len(q) > 2 for x in q[2]}
    lr, lo = [lines(r) for r in ref], [lines(r) for r in other]
    def cost(i, j):
        if fr[i][0] != fo[j][0]:
            return 1e9
        # position and size: a dot centred in a bowl must not pair with the bowl
        c = (math.hypot(fr[i][1] - fo[j][1], fr[i][2] - fo[j][2])
             + abs(fr[i][3] - fo[j][3]) + abs(fr[i][4] - fo[j][4]))
        if lr[i] and lo[j]:                                 # what made them: the share of lines they do not share
            c += 1.0 - len(lr[i] & lo[j]) / len(lr[i] | lo[j])
        return c
    if n <= 7:
        best = min(itertools.permutations(range(n)), key=lambda perm: sum(cost(i, perm[i]) for i in range(n)))
        return list(best) if sum(cost(i, best[i]) for i in range(n)) < 1e8 else None
    order, used = [], set()
    for i in range(n):
        j = min((j for j in range(n) if j not in used), key=lambda j: cost(i, j))
        used.add(j)
        order.append(j)
    return order


def vertex_names(edge_names):
    """The names of a ring's points from the names of its edges (geom.ink's
    tags, edge i from point i to i + 1): point i is where edge i - 1 meets
    edge i, named by the two lines, a corner-rule chord by the two lines it
    cuts between. So a chamfer growing out of a corner shares a line with
    the corner on each side, and a point whose edge shrinks away shares one
    with the point it shrinks into."""
    n = len(edge_names)
    return [(edge_names[i - 1], edge_names[i]) for i in range(n)]


def _name_cost(a, b):
    """0 for the same name, half for a shared line, 1 otherwise (or for a
    point with no name)."""
    if a is None or b is None:
        return 0.5
    if a == b:
        return 0.0
    if a[0] in b or a[1] in b:
        return 0.5
    return 1.0


def _dp(A, TA, B, TB, rotate=True, turn=TURN, NB=None):
    """Global alignment of A (with its start fixed) against a rotation of B
    (or B as it is: ``rotate`` False, for open paths).
    Returns list of (i or None, j or None) pairs.

    A, TA may also be several guides at once: A a list of (weight, points,
    turns[, names]), the cost of a match their weighted mean (TA unused).
    NB: B's point names; with the guides' names, a match costs NAMED for
    names that differ (vertex_names)."""
    guides = A if TA is None else [(1.0, A, TA)]
    n, m = len(guides[0][1]), len(B)
    wsum = sum(g[0] for g in guides)
    Bx, By, Bt = np.array([q[0] for q in B]), np.array([q[1] for q in B]), np.array(TB)
    C = np.zeros((n, m))
    for g in guides:
        w, Ag, Tg = g[:3]
        ax, ay, at = np.array([q[0] for q in Ag]), np.array([q[1] for q in Ag]), np.array(Tg)
        C += w / wsum * (np.hypot(ax[:, None] - Bx[None, :], ay[:, None] - By[None, :])
                         + turn * (np.abs(at[:, None] - Bt[None, :]) > 0.3))
        if NB is not None and len(g) > 3 and g[3] is not None:
            C += w / wsum * NAMED * np.array([[_name_cost(a, b) for b in NB] for a in g[3]])
    best = None
    # candidate rotations: B starts that look like A's start
    starts = sorted(range(m), key=lambda j: C[0, j])[:4] if rotate else [0]
    for r in starts:
        Cr = np.roll(C, -r, axis=1).tolist()
        D = np.full((n + 1, m + 1), np.inf)
        P = np.zeros((n + 1, m + 1), dtype=np.int8)
        D[0, 0] = 0.0
        for i in range(n + 1):
            for j in range(m + 1):
                if i == 0 and j == 0:
                    continue
                cands = []
                if i > 0 and j > 0:
                    cands.append((D[i - 1, j - 1] + Cr[i - 1][j - 1], 1))
                if i > 0:
                    cands.append((D[i - 1, j] + GAP, 2))
                if j > 0:
                    cands.append((D[i, j - 1] + GAP, 3))
                D[i, j], P[i, j] = min(cands)
        if best is None or D[n, m] < best[0]:
            path, i, j = [], n, m
            while i > 0 or j > 0:
                k = P[i, j]
                if k == 1:
                    path.append((i - 1, (j - 1 + r) % m)); i -= 1; j -= 1
                elif k == 2:
                    path.append((i - 1, None)); i -= 1
                else:
                    path.append((None, (j - 1 + r) % m)); j -= 1
            best = (D[n, m], path[::-1])
    return best[1]


def _rotation_only(A, TA, B, TB):
    """If B is A with another start (same turns throughout), the rotation."""
    n = len(A)
    if n != len(B):
        return None
    best = None
    for r in range(n):
        if all(abs(TA[i] - TB[(i + r) % n]) < 0.3 for i in range(n)):
            d = sum(math.hypot(A[i][0] - B[(i + r) % n][0], A[i][1] - B[(i + r) % n][1]) for i in range(n))
            if best is None or d < best[0]:
                best = (d, r)
    return None if best is None or best[0] / n > 0.6 else best[1]


def _add_missing_counters(masters):
    """A counter that exists only in some masters (closed at an extreme) is
    given to the others as a contour collapsed to a point where it would be,
    so that it grows from nothing."""
    k = len(masters)
    holes = [[r for r in m if _area(r) < 0] for m in masters]
    shells = [[r for r in m if _area(r) > 0] for m in masters]
    if len({len(s) for s in shells}) != 1:
        return masters                                   # a stroke separates: a design fault, reported later
    nmax = max(len(h) for h in holes)
    if all(len(h) == nmax for h in holes):
        return masters
    ref = max(range(k), key=lambda i: len(holes[i]))
    nref = _norm(masters[ref])
    cen = lambda r, nf: (sum(nf(q)[0] for q in r) / len(r), sum(nf(q)[1] for q in r) / len(r))
    out = []
    for mi in range(k):
        if len(holes[mi]) == nmax:
            out.append(masters[mi])
            continue
        nm = _norm(masters[mi])
        have = [cen(h, nm) for h in holes[mi]]
        extra = []
        for h in holes[ref]:
            c = cen(h, nref)
            if have and min(math.hypot(c[0] - a[0], c[1] - a[1]) for a in have) < 0.08:
                continue
            # place the collapsed counter at the same normalised spot in this master
            xs = [q[0] for r in masters[mi] for q in r]
            ys = [q[1] for r in masters[mi] for q in r]
            q = (min(xs) + c[0] * (max(xs) - min(xs)), min(ys) + c[1] * (max(ys) - min(ys)))
            extra.append([(q[0], q[1]) + tuple(hq[2:]) for hq in h])
        out.append(list(masters[mi]) + extra)
    return out


SYM = 1e-6          # a master is symmetric if its mirror misses less than this share of its ink
SNAP = 0.01         # units: a mirrored point this close to a drawn one takes the drawn one's place
ON_AXIS = 0.01      # units: a point this close to the axis is on it


def _axis(rings):
    """x of the vertical axis a master is mirror-symmetric about, or None."""
    from shapely import affinity
    from .geom import rings_to_shapely
    ink = rings_to_shapely(rings)
    if ink.is_empty:
        return None
    x0, _, x1, _ = ink.bounds
    c = (x0 + x1) / 2
    mirror = affinity.scale(ink, -1, 1, origin=(c, 0))
    return c if ink.symmetric_difference(mirror).area <= SYM * ink.area else None


def _half(rings, c):
    """The left half of a master's ink, cut on x = c, as rings (ink-left)."""
    from shapely.geometry import box
    from shapely.geometry.polygon import orient
    from .geom import rings_to_shapely
    ink = rings_to_shapely(rings)
    x0, y0, x1, y1 = ink.bounds
    left = ink.intersection(box(x0 - 10, y0 - 10, c, y1 + 10))
    out = []
    for poly in getattr(left, 'geoms', [left]):
        if poly.geom_type != 'Polygon' or poly.area < 1e-6:
            continue
        poly = orient(poly, 1.0)
        for ring in [poly.exterior] + list(poly.interiors):
            pts = [(x if abs(x - c) > ON_AXIS else c, y) for x, y in list(ring.coords)[:-1]]
            out.append(pts)
    return out


def _straight(a, p, b):
    """Whether p lies on the straight line from a to b."""
    return abs((p[0] - a[0]) * (b[1] - a[1]) - (p[1] - a[1]) * (b[0] - a[0])) <= 1e-6 * max(
        1.0, math.hypot(b[0] - a[0], b[1] - a[1])) ** 2


def _arcs(half, c):
    """A master's left half split where it was cut on the axis: (arcs,
    side rings). An arc runs from the axis along the ink's edge back to it;
    a side ring lies off the axis (a dot beside it)."""
    arcs, sides = [], []
    for r in half:
        n = len(r)
        on = [abs(q[0] - c) <= ON_AXIS for q in r]
        if not any(on):
            sides.append(r)
            continue
        cuts = [j for j in range(n) if on[j] and on[(j + 1) % n]]
        if not cuts:
            return None                                     # a half that only touches the axis
        for t, j in enumerate(cuts):
            start, end = (j + 1) % n, cuts[(t + 1) % len(cuts)]
            idx = [start]
            while idx[-1] != end:
                idx.append((idx[-1] + 1) % n)
            if len(idx) >= 2:
                arcs.append([r[i] for i in idx])
    return arcs, sides


def _whole(arc, c):
    """The contour an arc and its mirror make."""
    return list(arc) + [(2 * c - x, y) for x, y in reversed(arc[1:-1])]


def _fill_gaps(cols, norms, locs, ends=None):
    """Fill each master's gaps (None in its column) with a duplicate of the
    real point on either side of the gap that the missing point is nearer
    to, judged by where it lies in the master nearest in the design space
    that has it (the first that has it, without locs): a feature collapsing
    in some masters (a step shrinking to a corner) collapses onto the point
    it shrinks into, not onto whichever point happens to precede it, nor
    onto the one a far master puts it near. Collapsed onto the far end of
    an edge, it slides along the edge between the masters, unseen, but two
    such slides add up off the outline where two axes meet (Δ's step at
    the heavy grade-watch corner, 440 units out). ``ends``: per master, the
    ends of an open path (the axis points of a half), which a gap at the
    head or the tail collapses onto."""
    k = len(cols[0]) if cols else 0
    n = len(cols)
    real = [[q is not None for q in c] for c in cols]
    for mi in range(k):
        seq = [c[mi] for c in cols]
        if ends is None and all(q is None for q in seq):
            raise ValueError('a master lost a whole contour')
        fill = list(seq)
        for i in range(n):
            if seq[i] is not None:
                continue
            have = [m for m in range(k) if real[i][m]]
            src = min(have, key=lambda m: (math.dist(locs[m], locs[mi]), m)) if locs else have[0]
            r = norms[src](cols[i][src])
            if ends is None:
                ip = next((i - t) % n for t in range(1, n + 1) if seq[(i - t) % n] is not None)
                inx = next((i + t) % n for t in range(1, n + 1) if seq[(i + t) % n] is not None)
                cands = [seq[ip], seq[inx]]
            else:
                cands = [next((seq[j] for j in range(i - 1, -1, -1) if seq[j] is not None), ends[mi][0]),
                         next((seq[j] for j in range(i + 1, n) if seq[j] is not None), ends[mi][1])]
            fill[i] = min(cands, key=lambda q: math.dist(norms[mi](q), r))
        for c, q in zip(cols, fill):
            c[mi] = q
    return cols


def _align_open(paths, norms, locs=None, turn=TURN):
    """Open paths, one per master, both ends on the axis: the ends pinned to
    each other, the points between matched, a missing point filled with the
    previous one (the start, at the head of the path)."""
    k = len(paths)
    inner = [p[1:-1] for p in paths]
    ref_i = max(range(k), key=lambda i: len(inner[i]))
    ref = inner[ref_i]
    cols = [[None] * k for _ in ref]
    for idx, q in enumerate(ref):
        cols[idx][ref_i] = q
    # a master with no points between its ends guides nothing: grow the
    # tree over the others only
    have = [mi for mi in range(k) if inner[mi]]
    sub = _tree(have.index(ref_i), len(have), [locs[mi] for mi in have] if locs else None) if ref else []
    for a, guides in sub:
        mi = have[a]
        B = [norms[mi](q) for q in inner[mi]]
        gs = [(w, *_guide(cols, have[b], norms[have[b]])[:2]) for w, b in guides]
        path = _dp(gs, None, B, _turns(inner[mi]) if len(B) > 2 else [0.0] * len(B), rotate=False, turn=turn)
        new = []
        for a, b in path:
            col = cols[a] if a is not None else [None] * k
            col[mi] = inner[mi][b] if b is not None else None
            new.append(col)
        cols = new
    _fill_gaps(cols, norms, locs, ends=[(pa[0], pa[-1]) for pa in paths])
    return [[paths[mi][0]] + [col[mi] for col in cols] + [paths[mi][-1]] for mi in range(k)]


def _mirror_align(masters, locs=None, turn=TURN):
    """A glyph symmetric in every master, aligned by its left half and
    mirrored, so every instance between the masters is symmetric too; or
    None, if it is not symmetric or its halves will not align.

    Each master's left half is split into arcs from the axis back to it
    before anything is matched, so the points on the axis stay on it in
    every master; the arcs are matched across the masters as whole
    contours, then point by point with their ends pinned."""
    axes = [_axis(m) for m in masters]
    if any(c is None for c in axes):
        return None
    parts = [_arcs(_half(m, c), c) for m, c in zip(masters, axes)]
    if any(pt is None for pt in parts):
        return None
    k = len(masters)
    wholes = [[_whole(a, c) for a in arcs] for (arcs, _), c in zip(parts, axes)]
    sides = [sd for _, sd in parts]
    norms = [_norm(w + sd) if (w or sd) else None for w, sd in zip(wholes, sides)]
    if any(nm is None for nm in norms) or len({len(w) for w in wholes}) != 1 or len({len(sd) for sd in sides}) != 1:
        return None
    ref_i = max(range(k), key=lambda i: sum(len(r) for r in wholes[i]))
    out = [[] for _ in range(k)]
    if wholes[0]:
        orders = [_match_contours(wholes[ref_i], wholes[mi], norms[ref_i], norms[mi]) for mi in range(k)]
        if any(o is None for o in orders):
            return None
        for ai in range(len(wholes[ref_i])):
            group = [parts[mi][0][orders[mi][ai]] for mi in range(k)]
            al = _align_open(group, norms, locs, turn)
            if al is None:
                return None
            for mi in range(k):
                out[mi].append(_whole(al[mi], axes[mi]))
    if sides[0]:
        try:
            al = _align(sides, locs, turn)
        except ValueError:
            return None
        for mi in range(k):
            c = axes[mi]
            for r in al[mi]:
                out[mi].append(list(r))
                out[mi].append([(2 * c - x, y) for x, y in reversed(r)])
    # mirrored points take the drawn points' exact places (the italic finds
    # its chamfers by position)
    for mi in range(k):
        drawn = [q for r in masters[mi] for q in r]
        for ci, r in enumerate(out[mi]):
            out[mi][ci] = [min(drawn, key=lambda d: (d[0] - q[0]) ** 2 + (d[1] - q[1]) ** 2)
                           if any(abs(d[0] - q[0]) <= SNAP and abs(d[1] - q[1]) <= SNAP for d in drawn) else q
                           for q in r]
    # drop an axis point that is the middle of a straight edge in every master
    for ci in range(len(out[0])):
        n = len(out[0][ci])
        keep = [not all(abs(out[mi][ci][j][0] - axes[mi]) <= ON_AXIS
                        and _straight(out[mi][ci][j - 1], out[mi][ci][j], out[mi][ci][(j + 1) % n])
                        for mi in range(k)) for j in range(n)]
        if sum(keep) < 3:
            continue
        for mi in range(k):
            out[mi][ci] = [q for q, kp in zip(out[mi][ci], keep) if kp]
    if len({tuple(len(r) for r in m) for m in out}) != 1:
        return None
    return out


def align(masters: list[list[list[tuple]]], locs=None, turn=TURN, names=None):
    """masters: per master, a list of rings (ink-left). Returns the same,
    made compatible (same contour order, same point counts, same order), or
    raises ValueError. A glyph symmetric in every master is aligned by its
    halves (``_mirror_align``), so its instances stay symmetric.

    locs: each master's place in the design space, axes scaled alike (a
    master is aligned against the nearest one already aligned); without
    them, every master is aligned against the one with the most points.
    turn: the cost of pairing points that turn differently (0: by position
    alone, which pairs a fused heavy master with a thin one better in some
    glyphs and worse in others: 2026-10-26, best for about 6% of glyphs).

    names: per master, per ring, the name of each edge (geom.ink's tags):
    points are then paired by what made them (vertex_names) before where
    they lie, and a glyph symmetric in every master is aligned whole."""
    if names is not None:
        named = [[[(q[0], q[1], nm) for q, nm in zip(r, vertex_names(en))] for r, en in zip(m, mn)]
                 for m, mn in zip(masters, names)]
        return [[[q[:2] for q in r] for r in m] for m in _align(named, locs, turn)]
    if any(masters):
        res = _mirror_align(masters, locs, turn)
        if res is not None:
            return res
    return _align(masters, locs, turn)


def _tree(ref_i, k, locs):
    """The order to align masters in, each with the masters to align it
    against, weighted: grown from ref_i, every step taking the master
    nearest to one already aligned (a shortest spanning tree, Prim's); it
    is aligned against that one and against its nearest aligned neighbour
    each way along each axis (the masters it is interpolated with), the
    nearer weighing more."""
    if locs is None:
        return [(mi, [(1.0, ref_i)]) for mi in range(k) if mi != ref_i]
    d = lambda a, b: math.dist(locs[a], locs[b])
    done, out = [ref_i], []
    while len(done) < k:
        mi, pa = min(((m, q) for m in range(k) if m not in done for q in done),
                     key=lambda mq: (d(*mq), mq))
        guides = {pa}
        for ax in range(len(locs[mi])):
            for side in (-1, 1):
                line = [q for q in done if all(abs(locs[q][b] - locs[mi][b]) < 1e-9 for b in range(len(locs[mi])) if b != ax)
                        and (locs[q][ax] - locs[mi][ax]) * side > 1e-9]
                if line:
                    guides.add(min(line, key=lambda q: (d(mi, q), q)))
        done.append(mi)
        out.append((mi, [(1.0 / max(d(mi, q), 1e-9), q) for q in sorted(guides)]))
    return out


def _guide(cols, pa, norm):
    """Master pa's points along the columns, normalised, with their turns:
    a column pa has no point in carries the last point it has (the next, at
    the head), turning nowhere; and their names (None where pa has none,
    or the points carry no names)."""
    real = [i for i, c in enumerate(cols) if c[pa] is not None]
    t = dict(zip(real, _turns([cols[i][pa] for i in real]) if len(real) > 2 else [0.0] * len(real)))
    pts, last = [], None
    for i, c in enumerate(cols):
        if c[pa] is not None:
            last = i
        pts.append(norm(cols[last if last is not None else real[0]][pa]))
    names = [c[pa][2] if c[pa] is not None and len(c[pa]) > 2 else None for c in cols]
    return pts, [t.get(i, 0.0) for i in range(len(cols))], len(real) == len(cols), names


def _align(masters, locs=None, turn=TURN):
    k = len(masters)
    if not any(masters):
        return masters                                      # an empty glyph (a blank Braille cell) varies trivially
    masters = _add_missing_counters(masters)
    ref_i = max(range(k), key=lambda i: sum(len(r) for r in masters[i]))
    ref = masters[ref_i]
    nref = _norm(ref)
    norms = [_norm(m) for m in masters]
    tree = _tree(ref_i, k, locs)
    orders = []
    for mi in range(k):
        o = _match_contours(ref, masters[mi], nref, _norm(masters[mi]))
        if o is None:
            raise ValueError(f'contours differ: {[len(m) for m in masters]}')
        orders.append(o)
    out = [[None] * len(ref) for _ in range(k)]
    for ci in range(len(ref)):
        # columns: list of per-master point (or None)
        cols = [[None] * k for _ in ref[ci]]
        for idx, q in enumerate(ref[ci]):
            cols[idx][ref_i] = q
        for mi, guides in tree:
            ring = masters[mi][orders[mi][ci]]
            B = [norms[mi](q) for q in ring]
            TB = _turns(ring)
            gs = [(w, *_guide(cols, q, norms[q])) for w, q in guides]
            NB = [q[2] for q in ring] if ring and len(ring[0]) > 2 else None
            if len(gs) == 1 and gs[0][3]:
                r = _rotation_only(gs[0][1], gs[0][2], B, TB)
                if r is not None and (NB is None or all(
                        gs[0][4][idx] == NB[(idx + r) % len(ring)] for idx in range(len(cols)))):
                    for idx in range(len(cols)):
                        cols[idx][mi] = ring[(idx + r) % len(ring)]
                    continue
            path = _dp([(g[0], g[1], g[2], g[4]) for g in gs], None, B, TB, turn=turn, NB=NB)
            new_cols = []
            for a, b in path:
                if a is not None:
                    col = cols[a]
                    col[mi] = ring[b] if b is not None else None
                    new_cols.append(col)
                else:
                    col = [None] * k
                    col[mi] = ring[b]
                    new_cols.append(col)
            cols = new_cols
        _fill_gaps(cols, norms, locs)
        for mi in range(k):
            out[mi][ci] = [c[mi] for c in cols]
    return out
