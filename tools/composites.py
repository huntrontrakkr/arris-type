"""Glyphs that are other glyphs of the font, translated: composites.

An accented letter is its base and its marks (``glyphs.marks.compose``), a
.case form its plain glyph raised, a stamped glyph the glyphs it stamps
(``Glyph.add_glyph``). Where the drawing is exactly those glyphs moved (no
union joining them, no part redrawn), the font can carry it as a TrueType
composite: references to the components and where they stand. A variable
font then varies only those offsets, a few numbers per master, where an
outline varies every point (the accented letters were a quarter of the
variable fonts' outline variations).

``decompose(contours, name, comps)`` finds the components and their
offsets in one drawing, or None; the caller checks every place it needs
(build_vf: every master of the grid, and the check's places).
"""
from __future__ import annotations

import unicodedata

import numpy as np

EXACT = 0.01        # font units: a component's points match the glyph's within this, translated


def _cmap():
    import arris.glyphs  # noqa: F401
    from arris.draw import REGISTRY
    from arris.glyphs import ALIASES
    cmap = {}
    for n, s in REGISTRY.items():
        if s.unicode is not None and not n.endswith('.ital'):
            cmap.setdefault(s.unicode, n)
    for cp, n in ALIASES.items():
        cmap.setdefault(cp, n)
    return cmap


_CMAP: dict = {}


def candidates(name, stamped=()):
    """Glyphs ``name`` may be made of, likeliest first: its canonical
    decomposition's base and marks (a capital's marks in their .case form
    first), and what its drawing stamps."""
    from arris.draw import REGISTRY
    if not _CMAP:
        _CMAP.update(_cmap())
    spec = REGISTRY[name]
    out = []
    if spec.unicode is not None:
        d = unicodedata.normalize('NFD', chr(spec.unicode))
        if len(d) > 1:
            base = _CMAP.get(ord(d[0]))
            if base in ('i', 'j'):
                out.append({'i': 'dotlessi', 'j': 'uni0237'}[base])
            if base:
                out.append(base)
            for m in d[1:]:
                mn = _CMAP.get(ord(m))
                if mn:
                    out += [mn + '.case', mn] if d[0].isupper() else [mn, mn + '.case']
    if '.' in name:                                         # a form: its plain glyph (bullet.case)
        out.append(name.split('.')[0])
    out += list(stamped)
    seen = []
    for x in out:
        if x in REGISTRY and x != name and x not in seen:
            seen.append(x)
    return seen


def _bare(c):
    """A contour without the points that do not change its shape: one on a
    point before it, an on-curve point midway between two off-curve ones
    (implied in TrueType), one on the straight line between its on-curve
    neighbours. Two drawings of one shape can differ in those (the italic's
    curving of a stamped base kept one its own drawing did not)."""
    pts = [tuple(q) for q in c]
    on = (lambda q: len(q) < 3 or q[2] > 0.5)
    changed = True
    while changed and len(pts) > 3:
        changed = False
        for i in range(len(pts)):
            a, q, b = pts[i - 1], pts[i], pts[(i + 1) % len(pts)]
            if abs(q[0] - a[0]) <= EXACT and abs(q[1] - a[1]) <= EXACT and on(q) == on(a):
                drop = True
            elif not on(q):
                drop = False
            elif not on(a) and not on(b):
                drop = abs(q[0] - (a[0] + b[0]) / 2) <= EXACT and abs(q[1] - (a[1] + b[1]) / 2) <= EXACT
            elif on(a) and on(b):
                cross = (q[0] - a[0]) * (b[1] - a[1]) - (q[1] - a[1]) * (b[0] - a[0])
                L = max(np.hypot(b[0] - a[0], b[1] - a[1]), 1e-9)
                dot = (q[0] - a[0]) * (b[0] - a[0]) + (q[1] - a[1]) * (b[1] - a[1])
                drop = abs(cross) / L <= EXACT and 0 <= dot <= L * L
            else:
                drop = False
            if drop:
                del pts[i]
                changed = True
                break
    return np.array(pts, float)


def _canon(c):
    """A contour (N x 2 or 3), its shape's own points only (_bare), from its
    least point, so two copies of it start alike wherever they stand."""
    c = _bare(c)
    k = int(np.lexsort((c[:, 1].round(3), c[:, 0].round(3)))[0])
    return np.roll(c, -k, axis=0)


def decompose(contours, name, comps):
    """[(component, dx, dy)]: components whose contours, translated, are
    exactly ``name``'s, every contour accounted for; else None.
    ``contours(n)`` gives a glyph's contours as arrays of points (x, y[, on])."""
    G = [_canon(np.asarray(c, float)) for c in contours(name) if len(c) >= 3]
    used = [False] * len(G)
    out = []
    for cn in comps:
        C = [_canon(np.asarray(c, float)) for c in contours(cn) if len(c) >= 3]
        if not C:
            continue
        found = None
        for i, g in enumerate(G):
            if used[i] or g.shape != C[0].shape:
                continue
            off = g[0] - C[0][0]
            off[2:] = 0.0                                    # (an on-curve flag is not moved)
            if np.abs(g - C[0] - off).max() > EXACT:
                continue
            match = []
            for c in C:
                j = next((j for j, h in enumerate(G) if not used[j] and j not in match and h.shape == c.shape
                          and np.abs(h - c - off).max() <= EXACT), None)
                if j is None:
                    break
                match.append(j)
            else:
                found = (match, off)
                break
        if found:
            for j in found[0]:
                used[j] = True
            out.append((cn, float(found[1][0]), float(found[1][1])))
    return out if out and all(used) else None
