"""The variable font's interpolation, looked at everywhere: a glyph's outline
at many places at once from its masters (or from a font's gvar), and two
measures of it that need no exact drawing to compare with:

* overshoot: how far a point lies outside the box its own positions span
  across the glyph's masters (the additive model carrying it off);
* crossings: how many pairs of the outline's segments cross properly,
  beyond what the masters themselves have (a contour turned inside out).

Written for any array module with numpy's interface (``xp``): build_vf runs
it with numpy on a coarse grid for every candidate alignment, and
tools/vf_spikes.py with jax.numpy on the GPU over thousands of places.
"""
from __future__ import annotations

import numpy as np


def support(xp, locs, R):
    """Each region's scalar at each place (fontTools' supportScalar):
    locs L x A, R (lower, peak, upper) T x A x 3 -> L x T."""
    lo, pk, hi = R[None, :, :, 0], R[None, :, :, 1], R[None, :, :, 2]
    v = locs[:, None, :]
    rise = (v - lo) / xp.where(pk - lo == 0, 1, pk - lo)
    fall = (hi - v) / xp.where(hi - pk == 0, 1, hi - pk)
    s = xp.where(v < pk, rise, fall)
    s = xp.where((v <= lo) | (v >= hi), 0.0, s)
    s = xp.where(v == pk, 1.0, s)
    s = xp.where(pk == 0, 1.0, s)
    return xp.prod(s, axis=2)


def outlines(xp, locs, base, D, R):
    """Points at each place: base N x 2 plus the deltas D (T x N x 2) scaled
    by their regions' support -> L x N x 2."""
    return base[None] + xp.einsum('lt,tnc->lnc', support(xp, locs, R), D)


def segments(ring_lengths):
    """For points laid out ring after ring: each point's successor in its
    ring (a segment runs from a point to it)."""
    nxt, start = [], 0
    for n in ring_lengths:
        nxt += [start + (i + 1) % n for i in range(n)]
        start += n
    return np.array(nxt, dtype=np.int32)


def pair_mask(nxt, n=None):
    """Segment pairs that count as crossings: different, not sharing a
    point; padding (indices from n on) excluded."""
    N = len(nxt)
    n = N if n is None else n
    i = np.arange(N)
    real = i < n
    m = real[:, None] & real[None, :] & (i[:, None] < i[None, :])
    m &= (nxt[:, None] != i[None, :]) & (nxt[None, :] != i[:, None])
    return m


BUDGET = 4e6     # numpy: segment pairs at once (each array of them L x N x N)
DEPTH = 2.0      # font units: a crossing a point need move less than this to undo is a twist too small to see


def _depths(xp, P, nxt, mask, eps):
    """Each pair of segments' crossing depth at each place (0 where they do
    not cross): L x N x N."""
    a, b = P, P[:, nxt]

    def orient(p, q, r):
        return (q[..., 0] - p[..., 0]) * (r[..., 1] - p[..., 1]) - (q[..., 1] - p[..., 1]) * (r[..., 0] - p[..., 0])
    A, B, C, Dd = a[:, :, None], b[:, :, None], a[:, None, :], b[:, None, :]
    o1, o2, o3, o4 = orient(A, B, C), orient(A, B, Dd), orient(C, Dd, A), orient(C, Dd, B)
    cross = (o1 * o2 < -eps) & (o3 * o4 < -eps) & mask[None]
    seg = xp.sqrt(((b - a) ** 2).sum(-1)) + 1e-9            # L x N
    # (|orient(p, q, r)| / |pq| is r's distance from the line through p, q)
    d = xp.minimum(xp.minimum(xp.abs(o1), xp.abs(o2)) / seg[:, :, None],
                   xp.minimum(xp.abs(o3), xp.abs(o4)) / seg[:, None, :])
    return xp.where(cross, d, 0.0)


def _chunked(fn, xp, P, nxt, *args):
    if xp is np and len(P) and len(P) * len(nxt) ** 2 > BUDGET:
        k = max(1, int(BUDGET // len(nxt) ** 2))
        return np.concatenate([fn(xp, P[i:i + k], nxt, *args) for i in range(0, len(P), k)])
    return fn(xp, P, nxt, *args)


def crossings(xp, P, nxt, mask, eps=1e-6, depth=DEPTH):
    """How many pairs of segments cross properly at each place (P L x N x
    2), counting only crossings deeper than ``depth``: the least distance
    an end of either segment lies from the other's line, what one point
    would have to move to undo the crossing. Two points at a vertex that
    swap by a fraction of a unit tie a bow-tie that thin (◌'s dots); a
    point that collapses in one master and opens out in another, a loop a
    unit or two across (⁂'s arm tips); a contour turned inside out crosses
    deep. With numpy, a few places at a time (the pairs make L x N x N
    arrays)."""
    return _chunked(lambda xp, P, nxt: (_depths(xp, P, nxt, mask, eps) >= depth).sum(axis=(1, 2)), xp, P, nxt)


def deepest(xp, P, nxt, mask, eps=1e-6):
    """The deepest crossing at each place (0 where none): how far a point is
    carried past where the outline would let it, in font units, like a
    point carried off it."""
    return _chunked(lambda xp, P, nxt: _depths(xp, P, nxt, mask, eps).max(axis=(1, 2)), xp, P, nxt)


def overshoot(xp, P, lo, hi):
    """How far the farthest point at each place lies outside its box: L."""
    out = xp.maximum(xp.maximum(lo[None] - P, P - hi[None]), 0.0)
    return xp.sqrt((out ** 2).sum(-1)).max(axis=1)


def from_masters(al, mlocs_norm, model):
    """(base, D, R, nxt) of aligned masters (per master, rings of points)
    under a fontTools VariationModel over their normalised places."""
    tags = model.axisOrder
    vals = [np.array([q[:2] for r in m for q in r], dtype=float) for m in al]
    deltas = model.getDeltas(vals)
    sups = model.supports
    base = deltas[0] if not sups[0] else None
    D, R = [], []
    for d, s in zip(deltas, sups):
        if not s:
            base = d
            continue
        D.append(d)
        R.append([s.get(t, (0.0, 0.0, 0.0)) for t in tags])
    n = len(vals[0])
    D = np.array(D) if D else np.zeros((0, n, 2))
    R = np.array(R, dtype=float) if R else np.zeros((0, len(tags), 3))
    return base, D, R, segments([len(r) for r in al[0]])


def measure(xp, base, D, R, nxt, locs, masters_pts):
    """(worst overshoot, its place index, places with crossings beyond the
    masters', the place index with the most) for one glyph."""
    lo = masters_pts.min(axis=0)
    hi = masters_pts.max(axis=0)
    mask = pair_mask(nxt)
    c0 = int(crossings(np, masters_pts, nxt, mask).max()) if len(masters_pts) else 0
    P = outlines(xp, locs, base, D, R)
    d = np.asarray(overshoot(xp, P, lo, hi))
    x = np.asarray(crossings(xp, P, nxt, mask))
    extra = x - c0
    return float(d.max()), int(d.argmax()), int((extra > 0).sum()), int(extra.argmax()) if (extra > 0).any() else None
