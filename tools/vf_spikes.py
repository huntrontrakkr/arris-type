"""Spikes anywhere in a variable font: every glyph interpolated on the GPU at
thousands of places across the design space, without drawing anything.

    uv run --group gpu python tools/vf_spikes.py [font.ttf ...] [--grid 41,17,11] [--tol 20]

(default: both variable fonts in build/; the report beside each font). For each glyph, its outline at
every place of a grid over the axes is its default outline plus the sum of
its variation deltas (gvar, the inferred points filled in) scaled by each
region's support there: one matrix product. Two things are looked for:

* overshoot: a point carried farther than --tol units outside the box its
  own positions span across the glyph's masters (the regions' peaks): the
  additive model pushing it where no master puts it (Δ went 440 units off
  at the heavy grade-watch corner). A drawing that itself reaches past its
  masters between them (an accent highest at 850) is listed too: see how
  far the font is from the drawing there (tools/vf_compare.py, arris.vf's
  check);
* crossings: segments of the outline (its control polygon) crossing where
  they do not at the default, deeper than a twist too small to see
  (arris.vf.dense.crossings): a contour turned inside out or into another.

The build's own check compares with exact drawings at 47 places; this one
has none to compare with, but looks everywhere. Writes build/vf_spikes*.json
and prints the worst glyphs.
"""
from __future__ import annotations

import os

os.environ.setdefault('XLA_PYTHON_CLIENT_ALLOCATOR', 'cuda_async')     # WSL2: 4 GiB single allocations otherwise
os.environ.setdefault('XLA_PYTHON_CLIENT_PREALLOCATE', 'false')
os.environ.setdefault('XLA_FLAGS', '--xla_gpu_enable_command_buffer= --xla_gpu_autotune_level=0')

import json  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import jax  # noqa: E402
import jax.numpy as jnp  # noqa: E402
from fontTools.ttLib import TTFont  # noqa: E402

from arris.vf import dense as vfdense  # noqa: E402

HI = jax.lax.Precision.HIGHEST
BUCKETS = (32, 64, 128, 256, 512, 1024)   # points per glyph, padded (one compiled kernel per size)


def _args():
    a = sys.argv[1:]
    fonts = [x for x in a if x.endswith('.ttf')] or sorted(str(p) for p in Path('build').glob('Arris*[[]*.ttf'))
    grid = (41, 17, 11)
    tol = 20.0
    if '--grid' in a:
        grid = tuple(int(v) for v in a[a.index('--grid') + 1].split(','))
    if '--tol' in a:
        tol = float(a[a.index('--tol') + 1])
    return fonts, grid, tol


def glyph_data(font, name):
    """(default points N x 2, deltas T x N x 2, regions T x A x 3, segment
    ends: index of each point's successor in its contour, contour id per
    point) or None for an empty glyph."""
    glyf, gvar = font['glyf'], font['gvar']
    tags = [a.axisTag for a in font['fvar'].axes]
    g = glyf[name]
    if g.numberOfContours <= 0:
        return None
    coords, ctrl = glyf._getCoordinatesAndControls(name, font['hmtx'].metrics, None)
    n = len(coords) - 4                                     # (the phantom points last)
    base = np.array(coords[:n], dtype=np.float64)
    deltas, regions = [], []
    for tv in gvar.variations.get(name, []):
        if any(c is None for c in tv.coordinates):
            import copy
            tv = copy.deepcopy(tv)
            tv.calcInferredDeltas(coords, ctrl.endPts)
        deltas.append(np.array(tv.coordinates[:n], dtype=np.float64))
        regions.append([tv.axes.get(t, (0.0, 0.0, 0.0)) for t in tags])
    nxt, cid, start = np.zeros(n, dtype=np.int32), np.zeros(n, dtype=np.int32), 0
    for k, e in enumerate(ctrl.endPts):
        idx = np.arange(start, e + 1)
        nxt[idx] = np.roll(idx, -1)
        cid[idx] = k
        start = e + 1
    D = np.stack(deltas) if deltas else np.zeros((0, n, 2))
    R = np.array(regions, dtype=np.float64) if regions else np.zeros((0, len(tags), 3))
    return base, D, R, nxt, cid


def support(locs, R):
    """Each region's scalar at each place (fontTools' supportScalar): L x T."""
    lo, pk, hi = R[None, :, :, 0], R[None, :, :, 1], R[None, :, :, 2]
    v = locs[:, None, :]
    up = jnp.where(v < pk, (v - lo) / jnp.where(pk - lo == 0, 1, pk - lo), (hi - v) / jnp.where(hi - pk == 0, 1, hi - pk))
    s = jnp.where(pk == 0, 1.0, jnp.where(v == pk, 1.0, jnp.where((v <= lo) | (v >= hi), 0.0, up)))
    s = jnp.where((pk != 0) & ((lo > pk) | (pk > hi) | ((lo < 0) & (hi > 0))), 1.0, s)   # (no such regions here)
    return jnp.prod(s, axis=2)


@jax.jit
def _outlines(locs, base, D, R):
    S = support(locs, R)
    return base[None] + jnp.einsum('lt,tnc->lnc', S, D, precision=HI)


@jax.jit
def _overshoot(P, lo, hi, mask):
    """How far each place's farthest point lies outside its box (L)."""
    out = jnp.maximum(jnp.maximum(lo[None] - P, P - hi[None]), 0.0)
    d = jnp.sqrt((out ** 2).sum(-1)) * mask[None]
    return d.max(axis=1), d.argmax(axis=1)


@jax.jit
def _crossings(P, nxt, valid):
    return vfdense.crossings(jnp, P, nxt, valid), vfdense.deepest(jnp, P, nxt, valid)


def check_glyph(base, D, R, nxt, cid, locs, peaks, tol):
    n = base.shape[0]
    N = next(b for b in BUCKETS if b >= n) if n <= BUCKETS[-1] else n
    pad = N - n
    baseP = np.pad(base, ((0, pad), (0, 0)))
    DP = np.pad(D, ((0, 0), (0, pad), (0, 0)))
    nxtP = np.concatenate([nxt, np.arange(n, N)])
    mask = np.concatenate([np.ones(n), np.zeros(pad)])
    valid = vfdense.pair_mask(nxtP, n)          # segment pairs that count
    # positions at the masters (the regions' peaks, and the default): each point's box
    Pm = np.asarray(_outlines(jnp.asarray(peaks), baseP, DP, R))
    lo, hi = Pm.min(axis=0), Pm.max(axis=0)
    zero = np.zeros((1, R.shape[1]))
    c0 = int(np.asarray(_crossings(_outlines(jnp.asarray(zero), baseP, DP, R), nxtP, valid)[0])[0])
    worst, worst_at, n_over, n_cross, cross_at, most, deep = 0.0, None, 0, 0, None, 0, 0.0
    for k in range(0, len(locs), 1024 if N <= 256 else 256):
        L = jnp.asarray(locs[k:k + 1024 if N <= 256 else k + 256])
        P = _outlines(L, baseP, DP, R)
        d, _ = _overshoot(P, lo, hi, mask)
        d = np.asarray(d)
        x, dx = (np.asarray(v) for v in _crossings(P, nxtP, valid))
        n_over += int((d > tol).sum())
        if d.max() > worst:
            worst, worst_at = float(d.max()), k + int(d.argmax())
        extra = x > c0
        n_cross += int(extra.sum())
        if extra.any():
            deep = max(deep, float(dx[extra].max()))
            if x.max() - c0 > most:
                most, cross_at = int(x.max() - c0), k + int(x.argmax())
    return worst, worst_at, n_over, n_cross, cross_at, most, deep


def main():
    fonts, grid, tol = _args()
    for path in fonts:
        t0 = time.time()
        font = TTFont(path)
        axes = font['fvar'].axes
        tags = [a.axisTag for a in axes]
        ranges = [np.linspace(-1.0 if a.minValue < a.defaultValue else 0.0,
                              1.0 if a.maxValue > a.defaultValue else 0.0, gs) for a, gs in zip(axes, grid)]
        locs = np.stack(np.meshgrid(*ranges, indexing='ij'), -1).reshape(-1, len(axes))

        def design(v):
            out = []
            for a, x in zip(axes, v):
                out.append(round(float(a.defaultValue + x * ((a.maxValue - a.defaultValue) if x > 0 else (a.defaultValue - a.minValue))), 1))
            return tuple(out)
        report = {}
        for name in font.getGlyphOrder():
            gd = glyph_data(font, name)
            if gd is None:
                continue
            base, D, R, nxt, cid = gd
            if D.shape[0] == 0:
                continue
            peaks = np.concatenate([np.zeros((1, len(tags))), R[:, :, 1]])
            w, wa, no, nc, ca, most, deep = check_glyph(base, D, R, nxt, cid, locs, peaks, tol)
            if no or nc:
                report[name] = {'overshoot': round(w, 1), 'at': design(locs[wa]) if wa is not None else None,
                                'places_over': no, 'places_crossing': nc, 'most_crossings': most,
                                'deepest_crossing': round(deep, 1),
                                'crossing_at': design(locs[ca]) if ca is not None else None}
        out = Path(path).parent / ('vf_spikes_italic.json' if 'Italic' in path else 'vf_spikes.json')
        out.write_text(json.dumps(report, indent=1, ensure_ascii=False))
        bad = sorted(report.items(), key=lambda kv: -max(kv[1]['overshoot'], kv[1]['deepest_crossing']))
        print(f'{Path(path).name}: {len(locs)} places x {len(font.getGlyphOrder())} glyphs in {time.time() - t0:.0f} s; '
              f'{sum(1 for r in report.values() if r["places_over"])} glyphs overshoot by more than {tol:.0f} units, '
              f'{sum(1 for r in report.values() if r["places_crossing"])} cross themselves somewhere, '
              f'{sum(1 for r in report.values() if r["deepest_crossing"] > tol)} deeper than {tol:.0f} ({out})')
        for n, r in bad[:20]:
            print(f'  {n:18} overshoot {r["overshoot"]:6.1f} at {r["at"]}  ({r["places_over"]} places); '
                  f'+{r["most_crossings"]} crossings at {r["crossing_at"]} ({r["places_crossing"]} places, deepest {r["deepest_crossing"]})')


if __name__ == '__main__':
    main()
