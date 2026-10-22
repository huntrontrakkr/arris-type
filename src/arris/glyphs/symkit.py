"""Shared moves for the symbol blocks (general punctuation, super- and
subscripts, currency, letterlike symbols, number forms).

* ``stamp_t``: stamp a drawn glyph turned or mirrored. Only the maps that
  keep Arris's directions (half turns, mirrors, quarter turns) are used, so
  a turned 2 or a reversed C is the same drawing, chamfer record and all,
  and the italic curves it as it curves the original.
* ``set_tight``: letters set as one sign (Roman numerals, TEL, Pts, Rs):
  each pair as close as half the light the spacing gives a letter's side,
  measured by area as ``arris.spacing`` measures it, and never closer than
  three quarters of a stem (the pilcrow's rule), so the white between them
  holds at Black. In a monospaced cell the whole group is condensed, module
  and strokes alike, until it fits.
* ``small_all``: the small figures' parameters (``features.small``) with
  the x-height, ascender and descender scaled too, for small letters and
  signs that hang below or reach above their zone (parentheses, i, n).
"""
from __future__ import annotations

from functools import lru_cache

from shapely import affinity

from ..draw import REGISTRY, draw
from ..geom import rings_to_shapely

# Directions-keeping linear maps (a, b, c, d): x' = a x + b y, y' = c x + d y.
MIRROR = (-1, 0, 0, 1)     # left to right
FLIP = (1, 0, 0, -1)       # top to bottom
TURN = (-1, 0, 0, -1)      # half a turn


def _xform_rec(r, M, dx, dy):
    a, b, c, d = M

    def pt(q):
        return (a * q[0] + b * q[1] + dx, c * q[0] + d * q[1] + dy)

    def vec(v):
        return (a * v[0] + b * v[1], c * v[0] + d * v[1])
    if r[0] == 'bowl':
        return ('bowl',) + tuple((pt(q), vec(v)) for q, v in r[1:])
    return ('chord', pt(r[1]), pt(r[2]))


def add_t(g, sub, M=(1, 0, 0, 1), dx=0.0, dy=0.0):
    """Stamp a drawn glyph ``sub`` into g through x' = a x + b y + dx,
    y' = c x + d y + dy (an orthogonal map), with its chamfer record."""
    rings, rec = sub.outline()
    a, b, c, d = M
    g.extra.append(affinity.affine_transform(rings_to_shapely(rings), [a, b, c, d, dx, dy]))
    g.extra_chamfers += [_xform_rec(r, M, dx, dy) for r in rec]


def stamp_t(g, name, M=(1, 0, 0, 1), p=None, width=None, about=None):
    """Draw ``name`` and stamp it through M about the centre of its body box
    (x in [0, W], y about ``about``, default the middle of 0..cap), so a
    half turn keeps it in its own body. Returns the sub-glyph."""
    p = p or g.p
    sub = draw(name, p, width=width)
    W = sub.W
    yc = p.cap / 2 if about is None else about
    a, b, c, d = M
    # keep the centre (W/2, yc) fixed
    dx = W / 2 - (a * W / 2 + b * yc)
    dy = yc - (c * W / 2 + d * yc)
    add_t(g, sub, M, dx, dy)
    return sub


def ink_x(sub):
    xs = [x for r in sub.rings() for x, _ in r]
    return (min(xs), max(xs)) if xs else (0.0, sub.W)


# --- Letters set as one sign --------------------------------------------------

TIGHT = 0.5         # of a letter side's light, each side
TIGHT_MIN = 0.75    # of a stem: the least white between two letters of one sign


def _condensed(p, k):
    return p.with_(m=k * p.m, sv=k * p.sv, sh=k * p.sh, sd=k * p.sd, ss=k * p.ss, leg=k * p.leg, c=k * p.c)


def _layout(names, p, zone):
    """[(name, params, x offset)], total width: letters side by side, tight."""
    from ..font import light
    from ..spacing import bearings
    from ..font import DEPTH
    y0, y1 = zone
    lt = TIGHT * light(p)
    out, x, prev = [], 0.0, None
    for n in names:
        sub = draw(n, p)
        rings = sub.rings()
        lsb, rsb, xmin, xmax = bearings(rings, y0, y1, lt, DEPTH * (y1 - y0), floor=0.0)
        if prev is None:
            dx = -xmin
        else:
            prings, pdx, prsb = prev
            dx = x + prsb + lsb - xmin
            # never closer than TIGHT_MIN stems
            a = rings_to_shapely([[(qx + pdx, qy) for qx, qy in r] for r in prings])
            for _ in range(3):
                b = rings_to_shapely([[(qx + dx, qy) for qx, qy in r] for r in rings])
                short = TIGHT_MIN * p.sv - a.distance(b)
                if short <= 1e-6:
                    break
                dx += short
        out.append((n, dx))
        x = dx + xmax
        prev = (rings, dx, rsb)
    return out, x


@lru_cache(maxsize=None)
def tight(names: tuple, p, zone: tuple, cell: float | None = None):
    """(params, [(name, x)], width) for letters set as one sign; with a
    ``cell`` (the monospaced body), condensed until they fit it."""
    lay, w = _layout(names, p, zone)
    if cell is None or w <= cell:
        return p, lay, w
    lo, hi = 0.2, 1.0
    for _ in range(14):
        k = (lo + hi) / 2
        if _layout(names, _condensed(p, k), zone)[1] <= cell:
            lo = k
        else:
            hi = k
    pk = _condensed(p, lo)
    lay, w = _layout(names, pk, zone)
    return pk, lay, w


def set_tight(g, names, zone=None, mono_cell=True, p=None):
    """Stamp ``names`` side by side as one sign, centred in g's body.
    Letters keep their proportional forms in the monospaced cut (a slab I
    beside a slab I would touch); there the group is condensed to the cell."""
    p0 = p or g.p
    pp = p0.with_(mono=False)
    zone = zone or (0.0, p0.cap)
    cell = g.W if (p0.mono and mono_cell) else None
    pk, lay, w = tight(tuple(names), pp, tuple(zone), cell)
    off = (g.W - w) / 2 if cell is not None else 0.0
    for n, x in lay:
        g.add_glyph(draw(n, pk), x + off, 0.0)
    return w


def tight_width(names, zone=None, case='cap'):
    """Width function for a sign of tight letters (its proportional body)."""
    def width(p):
        z = zone or ((0.0, p.cap) if case == 'cap' else (0.0, p.xh))
        return tight(tuple(names), p.with_(mono=False), tuple(z))[2]
    return width


# --- Small letters and signs --------------------------------------------------

def small_all(p):
    """Small figures' parameters with every vertical metric scaled."""
    from .features import SMALL, small
    return small(p).with_(xh=SMALL * p.xh, asc=SMALL * p.asc, desc=SMALL * p.desc)


def width_of(name, pf=None, extra=0.0):
    """A glyph's body width (under derived parameters pf(p)), plus ``extra``
    modules."""
    return lambda p: REGISTRY[name].width(pf(p) if pf else p) + extra * p.m


# --- Signs in the monospaced cell ---------------------------------------------

K_MIN = 0.35        # the most a sign is condensed before it is drawn smaller instead


def _scaled(p, s):
    """Every dimension of the drawing (heights too) times s: a smaller sign."""
    return _condensed(p, s).with_(cap=s * p.cap, xh=s * p.xh, asc=s * p.asc, desc=s * p.desc)


def _ink_x(fn, width, p):
    from ..draw import Glyph
    g = Glyph(p, W=min(width(p), p.fig_w) if p.mono else width(p))
    fn(g)
    xs = [x for r in g.rings() for x, _ in r]
    return (min(xs), max(xs)) if xs else (0.0, g.W)


_FIT: dict = {}


def _mono_fit(key, fn, width, p):
    """(k, s, dx, dy) for a sign in the monospaced cell: condensed by k
    (module and strokes) until its ink fits; if even K_MIN does not do it
    (a sign whose long strokes are tied to the cap height, ‱), drawn
    smaller by s about the axis; then centred on its ink."""
    if (key, p) in _FIT:
        return _FIT[(key, p)]
    cell = min(width(p), p.fig_w)
    x0, x1 = _ink_x(fn, width, p)
    k, s = 1.0, 1.0
    if max(x1 - x0, width(p)) > p.fig_w + 1e-6:
        def fits(q):                    # its ink, and its body (ink a clip box may hide)
            a, b = _ink_x(fn, width, q)
            return max(b - a, width(q)) <= p.fig_w

        if fits(_condensed(p, K_MIN)):
            lo, hi = K_MIN, 1.0
            for _ in range(14):
                mid = (lo + hi) / 2
                lo, hi = (mid, hi) if fits(_condensed(p, mid)) else (lo, mid)
            k = lo
        else:
            k = K_MIN
            lo, hi = 0.2, 1.0
            for _ in range(14):
                mid = (lo + hi) / 2
                lo, hi = (mid, hi) if fits(_scaled(_condensed(p, K_MIN), mid)) else (lo, mid)
            s = lo
    q = _condensed(p, k) if k < 1 else p
    q = _scaled(q, s) if s < 1 else q
    dx, dy = 0.0, (1 - s) * p.cap / 2
    if k < 1 or s < 1:
        a, b = _ink_x(fn, width, q)
        dx = (cell - (a + b)) / 2
    _FIT[(key, p)] = (k, s, dx, dy)
    return _FIT[(key, p)]


def shift(g, dx, dy):
    """Move everything drawn in g by (dx, dy)."""
    from ..draw import _moved
    from ..geom import Node, Stroke
    g.strokes = [Stroke(tuple(Node(n.x + dx, n.y + dy, n.bowl, n.w) for n in st.nodes), st.closed, st.start, st.end)
                 for st in g.strokes]
    g.extra = [affinity.translate(e, dx, dy) for e in g.extra]
    g.extra_chamfers = [_moved(r, dx, dy) for r in g.extra_chamfers]
    if g.clip is not None:
        x0, y0, x1, y1 = g.clip
        g.clip = (x0 + dx, y0 + dy, x1 + dx, y1 + dy)


def sign(name, ch, width, kind=('punct', 1.0), solid=False, openings=()):
    """Register a sign. ``width``: its body (a function of the parameters,
    or a number of modules for a body of one stem). In the monospaced cut a
    sign whose ink is wider than the cell is condensed into it
    (``_mono_fit``), so nothing hangs into the neighbouring cells."""
    from ..draw import glyph
    from .letterframe import letter_width
    if not callable(width):
        width = letter_width(width, 1)

    def body(p):
        n = width(p)
        return min(n, p.fig_w) if p.mono else n

    def deco(fn):
        def wrapped(g):
            if not g.p.mono:
                return fn(g)
            k, s, dx, dy = _mono_fit(name, fn, width, g.p)
            p = g.p
            if k < 1.0:
                g.p = _condensed(g.p, k)
            if s < 1.0:
                g.p = _scaled(g.p, s)
            fn(g)
            if dx or dy:
                shift(g, dx, dy)
            g.p = p if (k < 1 or s < 1) and False else g.p
        wrapped.__module__ = fn.__module__
        wrapped.__name__ = fn.__name__
        glyph(name, ch, body, kind=kind, solid=solid, openings=openings)(wrapped)
        return fn
    return deco
