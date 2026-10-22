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
others as a duplicate of its neighbour: a feature growing from nothing as
the weight moves.

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
    xs = [x for r in rings for x, _ in r]
    ys = [y for r in rings for _, y in r]
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
    def cost(i, j):
        if fr[i][0] != fo[j][0]:
            return 1e9
        # position and size: a dot centred in a bowl must not pair with the bowl
        return (math.hypot(fr[i][1] - fo[j][1], fr[i][2] - fo[j][2])
                + abs(fr[i][3] - fo[j][3]) + abs(fr[i][4] - fo[j][4]))
    if n <= 7:
        best = min(itertools.permutations(range(n)), key=lambda perm: sum(cost(i, perm[i]) for i in range(n)))
        return list(best) if sum(cost(i, best[i]) for i in range(n)) < 1e8 else None
    order, used = [], set()
    for i in range(n):
        j = min((j for j in range(n) if j not in used), key=lambda j: cost(i, j))
        used.add(j)
        order.append(j)
    return order


def _dp(A, TA, B, TB):
    """Global alignment of A (with its start fixed) against a rotation of B.
    Returns list of (i or None, j or None) pairs."""
    n, m = len(A), len(B)
    best = None
    # candidate rotations: B starts that look like A's start
    starts = sorted(range(m), key=lambda j: math.hypot(A[0][0] - B[j][0], A[0][1] - B[j][1])
                    + (TURN if abs(TA[0] - TB[j]) > 0.3 else 0))[:4]
    for r in starts:
        Br = B[r:] + B[:r]
        Tr = TB[r:] + TB[:r]
        D = np.full((n + 1, m + 1), np.inf)
        P = np.zeros((n + 1, m + 1), dtype=np.int8)
        D[0, 0] = 0.0
        for i in range(n + 1):
            for j in range(m + 1):
                if i == 0 and j == 0:
                    continue
                cands = []
                if i > 0 and j > 0:
                    c = math.hypot(A[i - 1][0] - Br[j - 1][0], A[i - 1][1] - Br[j - 1][1])
                    c += TURN if abs(TA[i - 1] - Tr[j - 1]) > 0.3 else 0.0
                    cands.append((D[i - 1, j - 1] + c, 1))
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
            xs = [x for r in masters[mi] for x, _ in r]
            ys = [y for r in masters[mi] for _, y in r]
            q = (min(xs) + c[0] * (max(xs) - min(xs)), min(ys) + c[1] * (max(ys) - min(ys)))
            extra.append([q] * len(h))
        out.append(list(masters[mi]) + extra)
    return out


def align(masters: list[list[list[tuple]]]):
    """masters: per master, a list of rings (ink-left). Returns the same,
    made compatible (same contour order, same point counts, same order), or
    raises ValueError."""
    k = len(masters)
    masters = _add_missing_counters(masters)
    ref_i = max(range(k), key=lambda i: sum(len(r) for r in masters[i]))
    ref = masters[ref_i]
    nref = _norm(ref)
    orders = []
    for mi in range(k):
        o = _match_contours(ref, masters[mi], nref, _norm(masters[mi]))
        if o is None:
            raise ValueError(f'contours differ: {[len(m) for m in masters]}')
        orders.append(o)
    out = [[None] * len(ref) for _ in range(k)]
    for ci in range(len(ref)):
        # columns: list of per-master point (or None)
        A = [nref(q) for q in ref[ci]]
        TA = _turns(ref[ci])
        cols = [[None] * k for _ in A]
        for idx, q in enumerate(ref[ci]):
            cols[idx][ref_i] = q
        for mi in range(k):
            if mi == ref_i:
                continue
            ring = masters[mi][orders[mi][ci]]
            nm = _norm(masters[mi])
            B = [nm(q) for q in ring]
            TB = _turns(ring)
            r = _rotation_only(A, TA, B, TB) if len(cols) == len(A) else None
            if r is not None and len(B) == len(cols):
                for idx in range(len(cols)):
                    cols[idx][mi] = ring[(idx + r) % len(ring)]
                continue
            # reference coordinates per column (carry the last real one over gaps)
            refpts, reft, last = [], [], None
            for c_i, col in enumerate(cols):
                if col[ref_i] is not None:
                    last = c_i
                src = cols[last][ref_i] if last is not None else next(c[ref_i] for c in cols if c[ref_i] is not None)
                refpts.append(nref(src))
            reft = _turns([c[ref_i] if c[ref_i] is not None else refpts[i] for i, c in enumerate(cols)]) \
                if all(c[ref_i] is not None for c in cols) else [0.0] * len(cols)
            path = _dp(refpts, reft, B, TB)
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
        # fill gaps with the previous real point (cyclically) per master
        for mi in range(k):
            seq = [c[mi] for c in cols]
            if all(q is None for q in seq):
                raise ValueError('a master lost a whole contour')
            first = next(i for i, q in enumerate(seq) if q is not None)
            prev = seq[first]
            for t in range(len(seq)):
                i = (first + t) % len(seq)
                if seq[i] is None:
                    seq[i] = prev
                else:
                    prev = seq[i]
            for c, q in zip(cols, seq):
                c[mi] = q
        for mi in range(k):
            out[mi][ci] = [c[mi] for c in cols]
    return out
