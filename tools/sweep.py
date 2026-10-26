"""The regression gate: every glyph, in every cut, against a baseline.

    uv run python tools/sweep.py snapshot NAME      -> build/sweep/NAME.pkl.gz
    uv run python tools/sweep.py diff BASE [NEW]    (NEW: the code as it is now, kept as 'last')

A snapshot draws every glyph at CONFIGS (weights across the upright,
italic, Mono and Mono italic cuts, and the variable font's grade and watch
extremes) and keeps its outline. A diff lists:

* every glyph whose outline changed, and where (a change no one meant is
  the thing to look at: a fix that breaks something elsewhere shows here);
* checks that got worse, for every glyph, not only the changed ones:
  - a contour crossing itself;
  - topology (contours, counters) that differs from the baseline;
  - topology that steps between neighbouring weights of a cut (what the
    variable font cannot interpolate);
  - a Mono glyph that has fewer counters than its proportional self.

Run it before every commit that touches the engine or a drawing; snapshot
each release. Workers: ARRIS_SWEEP_WORKERS (default 20).
"""
from __future__ import annotations

import gzip
import os
import pickle
import subprocess
import sys
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

import arris.glyphs  # noqa: E402,F401
from arris.draw import REGISTRY  # noqa: E402
from arris.font import place  # noqa: E402
from arris.geom import rings_to_shapely  # noqa: E402
from arris.instances import params  # noqa: E402
from arris.italic import italic, polylines  # noqa: E402

OUT = ROOT / 'build' / 'sweep'
WEIGHTS = (100, 300, 400, 600, 700, 900)
# (wght, GRAD, WTCH, mono, italic)
CONFIGS = [(w, 0, 0, m, i) for m in (0, 1) for i in (0, 1) for w in WEIGHTS] + \
    [(900, g, t, 0, i) for i in (0, 1) for g, t in ((100, 0), (-100, 0), (0, 100), (100, 100))]
CHANGED = 0.5       # font units: an outline moved by more than this has changed


def _params(c):
    w, g, t, m, i = c
    p = params(w, g, watch=t / 100).with_(mono=bool(m))
    return italic(p) if i else p


def _draw(n):
    out = {}
    for c in CONFIGS:
        try:
            rings, adv = place(n, _params(c))
            rr = polylines(rings) if c[4] else [[q[:2] for q in r] for r in rings]
            out[c] = ([[(round(x), round(y)) for x, y in r] for r in rr], round(adv, 1))   # as the font keeps them
        except Exception as e:  # noqa: BLE001
            out[c] = ('error', repr(e)[:200])
    return n, out


def snapshot():
    names = [n for n, s in REGISTRY.items() if not n.endswith('.ital') and s.kind != 'space']
    with Pool(int(os.environ.get('ARRIS_SWEEP_WORKERS', '20'))) as pool:
        res = dict(pool.imap_unordered(_draw, names, chunksize=8))
    rev = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    dirty = bool(subprocess.run(['git', 'status', '--porcelain', '--', 'src', 'tools'], cwd=ROOT,
                                capture_output=True, text=True).stdout.strip())
    return {'rev': rev + ('+' if dirty else ''), 'configs': CONFIGS, 'glyphs': res}


def _save(snap, name):
    OUT.mkdir(parents=True, exist_ok=True)
    with gzip.open(OUT / f'{name}.pkl.gz', 'wb') as f:
        pickle.dump(snap, f)


def _load(name):
    with gzip.open(OUT / f'{name}.pkl.gz', 'rb') as f:
        return pickle.load(f)


LOOP = 4.0          # square units: a contour crossing itself counts if it makes a loop this big
                    # (smaller ones are corners touching, at the snapshot's rounding)


def _crosses(r) -> bool:
    import shapely
    from shapely.geometry import LinearRing, Polygon
    if len(set(r)) < 3 or LinearRing(r).is_simple:
        return False
    v = shapely.make_valid(Polygon(r))
    parts = sorted((g.area for g in getattr(v, 'geoms', [v]) if g.geom_type == 'Polygon'), reverse=True)
    return len(parts) > 1 and parts[1] > LOOP


def _shape(entry):
    """(ink, contours, counters, crosses itself) of a drawn entry."""
    rings, _ = entry
    # as the static fonts keep them (font._contours): a contour crossing or
    # pinching itself as its simple loops, specks rounding leaves dropped
    from arris.font import LOOP as FONT_LOOP, _shoelace, _untangled
    rings = [lp for r in rings if len(r) >= 3 for lp in _untangled(list(r))
             if len(lp) >= 3 and abs(_shoelace(lp)) >= FONT_LOOP]
    ink = rings_to_shapely(rings)
    polys = [g for g in getattr(ink, 'geoms', [ink]) if g.geom_type == 'Polygon']
    holes = sum(len(g.interiors) for g in polys)
    crosses = any(_crosses(r) for r in rings)
    return ink, len(polys) + holes, holes, crosses


def _regular_top(g, c):
    """The topology of the glyph at Regular in c's cut (Mono, italic)."""
    e = g.get((400, 0, 0, c[3], c[4]))
    return None if e is None or e[0] == 'error' else _shape(e)[1:3]


def _compare(job):
    n, old, new = job
    changed, worse = [], []
    for c in new:
        a, b = old.get(c), new[c]
        if b[0] == 'error':
            if a is None or a[0] != 'error':
                worse.append((c, 'error: ' + b[1]))
            continue
        if a is None or a[0] == 'error':
            changed.append((c, 'new'))
            continue
        if a == b:
            continue
        ia, ca, ha, xa = _shape(a)
        ib, cb, hb, xb = _shape(b)
        moved = ia.boundary.hausdorff_distance(ib.boundary) if not (ia.is_empty or ib.is_empty) else 0.0
        if moved > CHANGED or abs(a[1] - b[1]) > CHANGED:
            changed.append((c, f'moved {moved:.0f}' + (f', advance {a[1]:.0f}->{b[1]:.0f}' if abs(a[1] - b[1]) > CHANGED else '')))
        if xb and not xa:
            worse.append((c, 'now crosses itself'))
        if (cb, hb) != (ca, ha):
            ra, rb = _regular_top(old, c), _regular_top(new, c)
            if (ca, ha) == ra and (cb, hb) != rb:
                worse.append((c, f'topology {ca}/{ha} -> {cb}/{hb}, no longer the Regular\'s'))
            elif (cb, hb) == rb and (ca, ha) != ra:
                changed.append((c, f'topology {ca}/{ha} -> {cb}/{hb}, now the Regular\'s'))
            else:
                worse.append((c, f'topology {ca}/{ha} -> {cb}/{hb} (Regular {rb[0]}/{rb[1]})'))
    return n, changed, worse


def _steps(snap, n):
    """Cuts where the topology steps between neighbouring weights."""
    out = set()
    g = snap['glyphs'].get(n, {})
    for m in (0, 1):
        for i in (0, 1):
            seq = []
            for w in WEIGHTS:
                e = g.get((w, 0, 0, m, i))
                if e is None or e[0] == 'error':
                    continue
                _, c, h, _ = _shape(e)
                seq.append((c, h))
            if len(set(seq)) > 1:
                out.add((m, i))
    return out


def _mono_loss(snap, n):
    g = snap['glyphs'].get(n, {})
    out = set()
    for w in WEIGHTS:
        for i in (0, 1):
            a, b = g.get((w, 0, 0, 0, i)), g.get((w, 0, 0, 1, i))
            if a and b and a[0] != 'error' and b[0] != 'error' and _shape(b)[2] < _shape(a)[2]:
                out.add((w, i))
    return out


def _certs(job):
    n, old, new = job
    so = {'glyphs': {n: old}}
    sn = {'glyphs': {n: new}}
    worse = []
    if _steps(sn, n) - _steps(so, n):
        worse.append(('cut', f'topology now steps with the weight in {sorted(_steps(sn, n) - _steps(so, n))} (mono, italic)'))
    if _mono_loss(sn, n) - _mono_loss(so, n):
        worse.append(('mono', f'Mono now has fewer counters than proportional at {sorted(_mono_loss(sn, n) - _mono_loss(so, n))} (weight, italic)'))
    return n, worse


def diff(base, new):
    old = base['glyphs']
    jobs = [(n, old.get(n, {}), g) for n, g in new['glyphs'].items()]
    with Pool(int(os.environ.get('ARRIS_SWEEP_WORKERS', '20'))) as pool:
        cmp = list(pool.imap_unordered(_compare, jobs, chunksize=8))
        touched = {n for n, ch, w in cmp if ch or w}
        certs = dict(pool.imap_unordered(_certs, [j for j in jobs if j[0] in touched], chunksize=4))
    print(f"baseline {base['rev']} -> {new['rev']}: {len(new['glyphs'])} glyphs x {len(new['configs'])} configs")
    gone = sorted(set(old) - set(new['glyphs']))
    added = sorted(set(new['glyphs']) - set(old))
    if gone:
        print('REMOVED', ' '.join(gone))
    if added:
        print('ADDED  ', ' '.join(added))
    nch = 0
    for n, ch, w in sorted(cmp):
        w = w + certs.get(n, [])
        if not ch and not w:
            continue
        nch += bool(ch)
        print(f'{n:22} ' + ('; '.join(f'{_cfg(c)} {what}' for c, what in ch[:6]) + (f' (+{len(ch) - 6})' if len(ch) > 6 else '')))
        for c, what in w:
            print(f'{"":22} WORSE {_cfg(c) if isinstance(c, tuple) else c} {what}')
    nworse = sum(1 for n, ch, w in cmp if w) + sum(1 for n in certs if certs[n])
    print(f'{nch} glyphs changed; {nworse} checks worse')


def _cfg(c):
    w, g, t, m, i = c
    s = f'{w}'
    if g or t:
        s += f'/g{g}/w{t}'
    return s + ('M' if m else '') + ('i' if i else '')


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'snapshot' and len(sys.argv) == 3:
        snap = snapshot()
        _save(snap, sys.argv[2])
        print(f"{sys.argv[2]}: {len(snap['glyphs'])} glyphs at {snap['rev']}")
    elif cmd == 'diff' and len(sys.argv) in (3, 4):
        base = _load(sys.argv[2])
        if len(sys.argv) == 4:
            new = _load(sys.argv[3])
        else:
            new = snapshot()
            _save(new, 'last')                              # (re-judge with: diff BASE last)
        diff(base, new)
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
