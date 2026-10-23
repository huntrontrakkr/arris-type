"""Diacritics, and every accented letter composed from its decomposition.

Marks are drawn in the same language: acute and grave are 45-degree strokes
cut flat top and bottom; circumflex and caron are small gables; dieresis
and dot are stem-square dots; the tilde steps at 45 degrees; breve and ring
are small chamfered bowls; cedilla and ogonek turn on a chamfered corner.

Placement is measured, not tabulated: a mark above sits a fixed gap above
the base's own highest ink (so it clears an ascender or a capital without a
per-letter list); a mark below hangs from the baseline. Capitals take a
flatter mark size, so accented capitals stay inside the line.
"""
from __future__ import annotations

import unicodedata

from fontTools import agl

from ..draw import B, REGISTRY, Glyph, glyph
from ..params import SQRT2


def gap(p):
    """White between a base and a mark above it (the i's dot gap)."""
    return max(p.m, 0.4 * p.sv)


def size(p, case):
    """Height of a stroke mark (acute, circumflex...)."""
    return (2.0 if case == 'lc' else 1.5) * p.m + 0.5 * p.sv


def _dot(g, x, y):
    s = g.p.dot()
    g.stroke((x, y, s), (x, y + s))


def acute(g, x, y, case, sign=1):
    p = g.p
    a = size(p, case)
    k = p.sd / SQRT2
    # centreline rises a over a; flat cuts at y and y + a
    g.stroke((x - sign * a / 2, y), (x + sign * a / 2, y + a), start='h', end='h')


def grave(g, x, y, case):
    acute(g, x, y, case, sign=-1)


def circumflex(g, x, y, case, flip=False):
    """A small gable, its point cut flat an edge break each side (as the A's)."""
    p = g.p
    w = size(p, case)                                       # 45 degrees: as tall as each side is wide
    f = p.c
    if not flip:
        pts = [(x - w, y), (x - f, y + w - f), (x + f, y + w - f), (x + w, y)]
    else:
        pts = [(x - w, y + w), (x - f, y + f), (x + f, y + f), (x + w, y + w)]
    g.stroke(*pts, start='h', end='h')


def caron(g, x, y, case):
    circumflex(g, x, y, case, flip=True)


def dieresis(g, x, y, case):
    p = g.p
    d = p.dot() + max(1.2 * p.m, 0.8 * p.dot())
    _dot(g, x - d / 2, y)
    _dot(g, x + d / 2, y)


def dotaccent(g, x, y, case):
    _dot(g, x, y)


def macron(g, x, y, case):
    p = g.p
    w = size(p, case)
    g.stroke((x - w, y + g.sh / 2), (x + w, y + g.sh / 2))


def tilde(g, x, y, case):
    """Up at 45 degrees, along, down, along, up: the tilde as a step."""
    p = g.p
    w = size(p, case)
    h = w / 2.5
    a = (2 * w - 3 * h) / 2
    x0 = x - w
    y = y + p.sd / SQRT2                                    # the centreline sits half a stroke up
    pts = [(x0, y), (x0 + h, y + h), (x0 + h + a, y + h), (x0 + 2 * h + a, y), (x0 + 2 * h + 2 * a, y),
           (x0 + 3 * h + 2 * a, y + h)]
    g.stroke(*pts, start='v', end='v')


def breve(g, x, y, case):
    """A small chamfered cup. Its sides thin at heavy weights, as accents do,
    so the cup stays open: twice the marks' gap across, room for its inner
    corners' fills and a gap between them."""
    p = g.p
    w = size(p, case)
    h = 0.75 * w
    t = min(p.sv, w - gap(p))                               # side thickness
    xl, xr = x - w + t / 2, x + w - t / 2
    g.stroke((xl, y + h + g.sh / 2, t), B(xl, y + g.sh / 2, p.m / 2),
             B(xr, y + g.sh / 2, p.m / 2, t), (xr, y + h + g.sh / 2))


def ring(g, x, y, case):
    """A small chamfered square ring. Its counter is fixed in modules, but
    never narrower than its stroke (at heavy weights a module-wide counter
    in a two-module ring is a pinhole); its stroke follows the weight's up
    to the watch's two modules and no further, as accents lighten at heavy
    weights, so a heavy Å stays inside the line."""
    p = g.p
    t = min(p.sv, 2 * p.m)                                  # the stroke
    inner = max((2.0 if case == 'lc' else 1.6) * p.m, t)    # the counter, across
    r = (inner + t) / 2                                     # centreline half-size
    leg = p.m / 2
    yc = y + r + t / 2
    g.stroke(B(x - r, yc - r, leg, t), B(x + r, yc - r, leg, t), B(x + r, yc + r, leg, t), B(x - r, yc + r, leg, t),
             closed=True)


def hungarumlaut(g, x, y, case):
    p = g.p
    d = 2 * p.sd / SQRT2 + max(0.6 * p.m, 0.4 * p.sv)     # clear of each other at every weight
    acute(g, x - d / 2, y, case)
    acute(g, x + d / 2, y, case)


def commabelow(g, x, y, case):
    """The comma, hung a gap below the baseline and kept within the
    descender (a little past it, as far as a descender's chamfer): its stub
    shortens first, down to a third of its thickness, then the whole comma
    lightens, as heavy faces draw their accents."""
    from .punct import _comma
    p = g.p
    room = 1.15 * p.desc - gap(p)
    s = min(p.sv, room / (1 / 3 + 0.75))
    stub = min(1.5 * s, room - 0.75 * s)
    _comma(g, None, x + 0.25 * s, -gap(p), stub=stub, s=s)


def commaabove(g, x, y, case):
    """The turned comma that stands for a cedilla over g."""
    p = g.p
    s = p.sv
    yb = y + 0.5 * gap(p)
    yt = yb + 1.5 * s
    g.stroke((x, yb), (x, yt), (x + 0.75 * s, yt + 0.75 * s), end='h')


def cedilla(g, x, y, case):
    p = g.p
    s = p.sv
    yb = -p.desc + g.sh / 2 + 0.25 * p.m
    g.stroke((x, g.sh / 2), (x, yb + 0.0), (x - 1.5 * p.m - s / 2, yb))


def ogonek(g, x, y, case):
    """Hangs from the base's rightmost ink on the baseline (a stem's foot or
    a bar's end, whichever the letter has), turning right underneath."""
    p = g.p
    yb = -p.desc + g.sh / 2 + 0.25 * p.m
    from shapely.geometry import LineString
    base = g.extra[0]
    cut = base.intersection(LineString([(-1e4, 0.3 * g.sh), (1e4, 0.3 * g.sh)]))
    xs = [c[0] for gg in getattr(cut, 'geoms', [cut]) for c in getattr(gg, 'coords', [])]
    x = (max(xs) - 0.75 * p.sv) if xs else x
    g.stroke((x, g.sh / 2), B(x, yb, p.m / 2), (x + 1.5 * p.m + p.sv / 2, yb))


ABOVE = {'̀': grave, '́': acute, '̂': circumflex, '̃': tilde, '̄': macron,
         '̆': breve, '̇': dotaccent, '̈': dieresis, '̊': ring, '̋': hungarumlaut,
         '̌': caron}
BELOW = {'̦': commabelow, '̧': cedilla, '̨': ogonek}
# Marks joined to the base itself (the Vietnamese horn): fn(g, x, case),
# reading the base's ink (g.extra[0]). A monospaced cell narrows the base
# by as much as such a mark reaches past the cell's edge.
ATTACHED: dict = {}
# Pairs of marks above where the second stands beside the first, at its
# upper right, instead of on top of it (Vietnamese tone marks on the
# circumflex).
BESIDE: set = set()

# Letters whose cedilla is written as a comma: Latvian's, and the T and t,
# whose cedilla Romanian writes as a comma (and which, hung from the T's
# stem, would turn the letter into a J).
CEDILLA_AS_COMMA = set('KkLlNnRrGgTt')

STACK_GAP = 0.6     # white between stacked marks, of the marks' gap
LIGHTEST = 0.5      # the furthest a stack of marks lightens and shrinks to stay inside the line


def line_top(p):
    """The top of the line: the font's Windows ascent (``font.Metrics``),
    above which a renderer may clip."""
    from ..font import Metrics
    m = Metrics()
    return (m.win_asc - 2) * p.cap / m.cap


def accent_params(p, k):
    """Marks drawn lighter and smaller by k: strokes, module and edge breaks
    together, so a mark keeps its proportions as it shrinks."""
    if k == 1.0:
        return p
    return p.with_(m=p.m * k, sv=p.sv * k, sh=p.sh * k, sd=p.sd * k, ss=p.ss * k, c=p.c * k, leg=p.leg * k)


def mark_ink(g, n0=0):
    """The finished ink (corner rule and all) of a glyph's strokes from the n0-th on."""
    from ..draw import _thickness
    from ..geom import ink, rings_to_shapely
    return rings_to_shapely(ink(g.strokes[n0:], _thickness(g.p, g.sh), g.p.c))


def raw_ink(g, n0=0):
    """The ink of a glyph's strokes from the n0-th on before the corner rule:
    what the glyph's union sees, so parts apart here stay apart."""
    import shapely
    from ..draw import _thickness
    from ..geom import stroke_polygon
    th = _thickness(g.p, g.sh)
    return shapely.union_all([stroke_polygon(s, th, g.p.c) for s in g.strokes[n0:]])


RAW_CLEAR = 1.0     # font units: marks whose raw strokes come nearer would fuse in the union


def _nearest_clear(scratch, n0, draw_at, others, sg, reach):
    """The least t in [0, reach] for which the mark drawn by draw_at(t)
    stands ``sg`` clear of ``others`` (finished ink) and does not touch
    them before the corner rule (raw ink)."""
    fin, raw = others

    def clear(t):
        del scratch.strokes[n0:]
        draw_at(t)
        return ((not sg or mark_ink(scratch, n0).distance(fin) >= sg - 1e-6)
                and raw_ink(scratch, n0).distance(raw) >= RAW_CLEAR)
    if clear(0.0):
        del scratch.strokes[n0:]
        return 0.0
    lo, hi = 0.0, reach
    for _ in range(20):
        mid = (lo + hi) / 2
        if clear(mid):
            hi = mid
        else:
            lo = mid
    del scratch.strokes[n0:]
    return hi


def stack_above(p, marks, x, top, case, W, room=None, avoid=None):
    """Where the marks above a base go: ([(mark, x, y)], the stack's top).

    The first stands a gap above the base's highest ink; each next one a
    stack gap above the ink of those before it (measured, so a dieresis
    carries a macron lower than an acute would). A pair in ``BESIDE`` puts
    the second mark at the first's upper right instead: drawn where the
    first is, then moved out at 45 degrees, square to the circumflex's
    right arm, until it stands a stack gap clear. Marks never come so near
    that their strokes would fuse. ``avoid`` (finished, raw ink): what the
    stack keeps a stack gap from, moving left if it must (a horn).
    ``room`` (x0, x1): the whole stack shifts sideways, if it must, to stay
    inside it (a monospaced cell)."""
    from ..draw import Glyph
    scratch = Glyph(p, W=W)
    places = []
    y = top + gap(p)
    sg = STACK_GAP * gap(p)
    reach = 4 * size(p, case) + 2 * p.sv
    prev = None
    for m in marks:
        n0 = len(scratch.strokes)
        before = (mark_ink(scratch), raw_ink(scratch)) if n0 else None
        if (prev, m) in BESIDE and places:
            x0, y0 = places[-1][1:]
            t = _nearest_clear(scratch, n0, lambda t: ABOVE[m](scratch, x0 + t, y0 + t, case), before, sg, reach)
            xm, ym = x0 + t, y0 + t
        else:
            xm, ym = x, y
            if before is not None:                          # stacked: never fused to what is below
                t = _nearest_clear(scratch, n0, lambda t: ABOVE[m](scratch, x, y + t, case), before, 0.0, reach)
                ym = y + t
        ABOVE[m](scratch, xm, ym, case)
        places.append((m, xm, ym))
        y = mark_ink(scratch).bounds[3] + sg
        prev = m
    if not places:
        return places, top
    if avoid is not None:
        t = _nearest_clear(scratch, 0, lambda t: [ABOVE[m](scratch, xm - t, ym, case) for m, xm, ym in places],
                           avoid, sg, reach)
        places = [(m, xm - t, ym) for m, xm, ym in places]
        del scratch.strokes[:]
        for m, xm, ym in places:
            ABOVE[m](scratch, xm, ym, case)
    if room is not None:
        x0, _, x1, _ = mark_ink(scratch).bounds
        shift = min(0.0, room[1] - x1) or max(0.0, room[0] - x0)
        places = [(m, xm + shift, ym) for m, xm, ym in places]
    return places, mark_ink(scratch).bounds[3]


def clear_below(base_ink, p, fn, x, case, W):
    """Where a mark below goes: under the body's centre, or, where the
    base's ink below the baseline (a descender's hook) would crowd it, to
    the right, as far as it must go to keep a gap clear."""
    from shapely.geometry import box

    from ..draw import Glyph
    scratch = Glyph(p, W=W)
    hook = base_ink.intersection(box(-1e4, -1e4, 1e4, -1e-3))  # (a cedilla is meant to touch the base)
    if hook.is_empty:
        return x

    def clearance(xm):
        del scratch.strokes[:]
        fn(scratch, xm, 0, case)
        return mark_ink(scratch).distance(hook)
    want = gap(p)
    if clearance(x) >= 0.9 * want:
        return x
    step = 0.1 * p.m
    xm = x
    while clearance(xm) < want and xm < x + 2 * W:
        xm += step
    return xm


def _name(ch):
    return agl.UV2AGL.get(ord(ch), f'uni{ord(ch):04X}')


def compose(chars, base_names):
    """Register a glyph for every char in ``chars`` that decomposes into a
    known base and known marks. ``base_names`` maps base chars to glyph names."""
    made = []
    for ch in chars:
        d = unicodedata.normalize('NFD', ch)
        if len(d) < 2:
            continue
        base, marks = d[0], d[1:]
        if not all(m in ABOVE or m in BELOW or m in ATTACHED for m in marks):
            continue
        bname = base_names.get(base)
        if any(m in ABOVE for m in marks) and bname in ('i', 'j'):
            bname = {'i': 'dotlessi', 'j': 'uni0237'}[bname]
        if bname is None or bname not in REGISTRY:
            continue
        name = _name(ch)
        if name in REGISTRY or any(sp.unicode == ord(ch) for sp in REGISTRY.values()):
            continue
        _register(name, ch, bname, base, marks)
        made.append(name)
    return made


def _register(name, ch, bname, base, marks):
    spec = REGISTRY[bname]
    case = 'uc' if base.isupper() else 'lc'

    def fn(g, bname=bname, marks=marks, base=base, case=case):
        from ..draw import Glyph, draw
        # The base, finished (openings solved, clipped and cut), then the marks.
        p = g.p
        # a monospaced cell gives the marks that stand beside or under the
        # base (a horn, d's and l's apostrophe, a dot under y's tail) the room
        # they need inside the cell: the base is drawn narrower by as much as
        # they would run out of it, its strokes as they are (ogoneks and
        # slashes keep to half the margin by their own drawing)
        room = 0.0
        if p.mono and any(m in ATTACHED or m in BELOW or (m == '\u030c' and base in 'dlLt') for m in marks):
            import shapely
            edge = (g.W + p.fig_adv) / 2                    # the cell's right edge, from the body's origin
            for _ in range(4):
                trial = Glyph(p, W=g.W)
                compose(trial, room)
                parts = list(trial.extra) + ([mark_ink(trial)] if trial.strokes else [])
                over = shapely.union_all(parts).bounds[2] - edge
                if over < 0.5:
                    break
                room += over
            # never so narrow that the base's counter closes (d at Black):
            # past that the mark may reach into the cell's margin
            from .letterframe import least_white
            room = max(0.0, min(room, g.W - 2 * p.sv - least_white(p)))
        g.extra, g.clip = [], None
        compose(g, room)
        if room:
            _into_cell(g)

    def compose(g, room, bname=bname, marks=marks, base=base, case=case):
        from ..draw import draw
        p = g.p
        base_glyph = draw(bname, p, g.ot, g.ob, width=(g.W - room) if room else None)
        rings = base_glyph.rings()
        top = max(y for r in rings for _, y in r)
        g.add_glyph(base_glyph)
        x = (g.W - room) / 2
        above = []
        for m in marks:
            if m in ABOVE:
                if m == '\u030c' and base in 'dlLt':
                    _caron_apostrophe(g, base)
                    continue
                above.append(m)
            elif m in ATTACHED:
                ATTACHED[m](g, x, case)
            elif m == '\u0327' and base in CEDILLA_AS_COMMA:
                if base == 'g':
                    commaabove(g, x, top + gap(p), case)
                else:
                    commabelow(g, x, 0, case)
            elif m == '\u0328':
                ogonek(g, _ogonek_x(g, base), 0, case)
            else:
                BELOW[m](g, clear_below(g.extra[0], p, BELOW[m], x, case, g.W), 0, case)
        if not above:
            return
        cell = (-(p.fig_adv - g.W) / 2, g.W + (p.fig_adv - g.W) / 2) if p.mono else None
        # marks joined to the base (a horn) are kept clear of
        avoid = (mark_ink(g), raw_ink(g)) if g.strokes and any(m in ATTACHED for m in marks) else None
        draw_above(g, above, x, top, case, cell, avoid)

    glyph(name, ch, spec.width, kind=spec.kind)(fn)


def _into_cell(g):
    """In the monospaced cell, a glyph whose ink still runs out of the cell
    on one side moves into the room the other side has (the body is centred
    in the cell, not the ink)."""
    import shapely
    from .symkit import shift
    p = g.p
    parts = list(g.extra) + ([mark_ink(g)] if g.strokes else [])
    a, _, b, _ = shapely.union_all(parts).bounds
    lo, hi = -(p.fig_adv - g.W) / 2, g.W + (p.fig_adv - g.W) / 2
    dx = 0.0
    if b > hi:
        dx = -min(b - hi, max(0.0, a - lo))
    elif a < lo:
        dx = min(lo - a, max(0.0, hi - b))
    if dx:
        shift(g, dx, 0.0)


def draw_above(g, above, x, top, case, cell=None, avoid=None):
    """Draw marks above into g, stacked (``stack_above``) over ink reaching
    ``top``. A stack that would rise past the line's top lightens and
    shrinks, as heavy faces draw their accents, as far as it must (never
    past LIGHTEST)."""
    from ..draw import Glyph
    p = g.p
    k, q = 1.0, p
    places, hi = stack_above(q, above, x, top, case, g.W, cell, avoid)
    if hi > line_top(p):
        lo, k = LIGHTEST, 1.0
        for _ in range(16):
            mid = (lo + k) / 2
            if stack_above(accent_params(p, mid), above, x, top, case, g.W, cell, avoid)[1] <= line_top(p):
                lo = mid
            else:
                k = mid
        k = lo
        q = accent_params(p, k)
        places, hi = stack_above(q, above, x, top, case, g.W, cell, avoid)
    target = g if k == 1.0 else Glyph(q, W=g.W)
    for m, xm, ym in places:
        ABOVE[m](target, xm, ym, case)
    if target is not g:
        g.add_glyph(target)


def _ogonek_x(g, base):
    p = g.p
    return g.W - p.sv / 2 if base in 'aeiouAEIOUy' else g.W / 2


def _caron_apostrophe(g, base):
    """The caron on d, l, L and t is written as an apostrophe beside the stem.

    It stands right of the stem, its top on the ascender (cap height on a
    capital), its tail clear of the stem by a gap. Where ink lies under it
    (the t's crossbar) its stub shortens so the tail stays clear above that
    ink, down to a third of a stem, as heavy faces draw it."""
    from shapely.geometry import box

    from .punct import _comma
    from ..draw import Glyph
    from .figures import heaviness
    p0 = g.p
    ink = g.extra[0]
    # in the monospaced cell the apostrophe is drawn lighter toward Black (as
    # a stack of marks lightens), so a d keeps its counter beside it
    p = accent_params(p0, 1 - 0.5 * heaviness(p0)) if p0.mono else p0
    top = p.cap if base.isupper() else p.asc
    gap = max(p.m, 0.6 * p.sv)
    # the stem: the base's ink above the x-height and its bars
    stem = ink.intersection(box(-1e4, p.xh + g.sh, 1e4, top + 1))
    right = stem.bounds[2] if not stem.is_empty else p.sv
    reach = 0.75 * p.sv + p.sd / SQRT2                      # the tail's far edge, left of the stub's centre
    x = right + gap + reach
    below = ink.intersection(box(x - reach, -1e4, x + p.sv / 2, top - 1e-3))
    floor = below.bounds[3] if not below.is_empty else -1e4
    clear = max(p.c, 0.5 * p.m)
    stub = min(1.5 * p.sv, max(top - floor - clear - 0.75 * p.sv, p.sv / 3))
    if p is p0:
        _comma(g, None, x, top, stub=stub)
    else:
        target = Glyph(p, W=g.W)
        _comma(target, None, x, top, stub=stub)
        g.add_glyph(target)
