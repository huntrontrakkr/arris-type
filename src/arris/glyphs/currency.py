"""Currency Symbols (U+20A0-U+20C0).

Every sign is drawn from Arris letters, as the euro is from the C and the
yen from the Y (``symbols``): a letter with bars across it (₦ ₩ ₱ ₳ ₤ ₸ ₹),
with strokes through it (₵ ₲ ₮ ₺ ₥) or standing out of it (₡ ₿), or
letters set as one sign (₧ Pts, ₨ Rs, ₯ Δρ, ₶ lt, ₠ CE). They are spaced
as letters, like € £ ¥.

Bars across a letter come in pairs that keep their white (``bar_pair``):
the bars are the weight's horizontals, easing to 0.8 of them at Black; the
white between them is at least three quarters of a stem; they run out past the letter
by 0.9 of a stem (in Mono, a module and half the cell's margin). Where a
squinting reader would still see the pair fuse, with itself or with the
letter (``draw.Squint``), the bars thin further, down to 0.65 of the
horizontals. Strokes through a bowl leave each part of
the counter at least 0.6 of a stem: the sign widens with the stroke where
it must (``growing_width``).
"""
from __future__ import annotations

from types import SimpleNamespace

from ..draw import B, REGISTRY, draw, glyph, white_features
from ..params import SQRT2
from .caps import big
from .figures import beak_depth, heaviness, jog
from .letterframe import STEEP, Frame, growing_width, letter_width
from .symkit import _condensed, across, set_tight, sign, tight_width


def cur(name, ch, width, kind='cap', squint=()):
    return sign(name, ch, width, kind=kind, squint=squint)


def stamp(g, name, dx=0.0, dy=0.0, width=None, p=None):
    sub = draw(name, p or g.p, width=width)
    g.add_glyph(sub, dx, dy)
    return sub


_INSET: dict = {}


def _white_share(g, p):
    """The readable white inside a letter's hull (opened by a quarter of
    its stroke, as draw.white_features counts it) per unit of its width."""
    from shapely.geometry import MultiPoint
    from ..draw import WHITE_OPEN
    from ..geom import rings_to_shapely
    rings = g.rings()
    ink = rings_to_shapely(rings)
    hull = MultiPoint([q[:2] for r in rings for q in r]).convex_hull
    r = WHITE_OPEN * max(p.sv, p.sh, p.sd, p.ss)
    white = hull.difference(ink).buffer(-r, join_style='mitre').buffer(r, join_style='mitre')
    return white.area / max(1.0, g.W)


def inset_letter(g, name, dx, w):
    """Stamp the letter a sign's bars cross, ``w`` wide at dx. In Mono a
    letter fills its cell; one drawn narrower, to leave its bars room to run
    out, is condensed (module and strokes, symkit._condensed) as far as it
    must be to keep the white it has in its own cell (as much of it for its
    width), and no further."""
    p = g.p
    if not p.mono or w >= p.fig_w - 0.5:
        return stamp(g, name, dx, width=w)
    key = (name, p, round(w, 3))
    if key not in _INSET:
        own = draw(name, p)
        want = _white_share(own, p)

        def keeps(k):           # as open, for its width, as in its own cell
            q = _condensed(p, k)
            return _white_share(draw(name, q, width=w), q) >= want - 1e-3
        lo = 1.0
        if not keeps(1.0):
            lo, hi = 0.5, 1.0
            for _ in range(12):
                mid = (lo + hi) / 2
                lo, hi = (mid, hi) if keeps(mid) else (lo, mid)
        _INSET[key] = lo
    k = _INSET[key]
    return stamp(g, name, dx, width=w, p=_condensed(p, k) if k < 1 else None)


def frame(p, W, wm, zone='cap'):
    """A letter's frame for a body W wide, for reading its coordinates
    (where its stems and bars lie) without drawing it."""
    return Frame(SimpleNamespace(p=p, W=W, sh=p.sh, clip=None), wm, zone)


def wmin(p):
    """The least white between two parts of a sign."""
    return max(p.m, 0.6 * p.sv)


PAIR_T = 0.8         # a pair's bars at Black, as a share of the horizontal
PAIR_T_MIN = 0.65    # as thin as the squint rule takes them


def pair_t(p):
    """Thickness of a pair of bars as drawn: the weight's horizontal, easing
    toward Black to PAIR_T of it."""
    return p.sh * (1 - (1 - PAIR_T) * heaviness(p))


def pair_gap(p):
    """White between a pair of bars: a module and a quarter, or three
    quarters of a stem, whichever is more (the ungraded stem: grade changes
    strokes, never where they lie)."""
    return max(1.25 * p.m, 0.75 * p.ungraded().sv)


def pair(g):
    """(thickness, white) of the glyph's pair of bars: as drawn, unless the
    squint rule has thinned them (the free variable 'bars', the share of
    pair_t they keep). The white between them stays: what the bars give up
    goes to the white between them and the letter."""
    return pair_t(g.p) * g.free('bars', 1.0), pair_gap(g.p)


def mark_bars(g, x0, x1, y_lo, y_hi):
    """Mark a pair of bars, centred at y_lo and y_hi from x0 to x1, for the
    squint rule: it watches the white that touches them (between them,
    where they run out past the letter, between them and the letter's
    other strokes), not the letter's own."""
    t, _ = pair(g)
    e = 2.0
    for y in (y_lo, y_hi):
        g.zones.append((min(x0, x1) - e, y - t / 2 - e, max(x0, x1) + e, y + t / 2 + e))


from .symbols import BARS, BARS_OR_ONE  # noqa: E402,F401  (the rules of every barred sign, € ¥ too)


def one_bar(g) -> bool:
    """Whether the squint rule has made the glyph's pair of bars one."""
    return g.free('one', 0.0) >= 0.5


def bar_out(p):
    """How far a bar runs out past the letter it crosses: a module, or 0.9
    of a stem toward Black, so it reads as a bar and not as a nub on the
    letter's side. In Mono the cell is fixed and the letter can give up
    only a module of it; the bars make up some of the rest by hanging into
    the cell's margin (bar_hang)."""
    if p.mono:
        return p.m + bar_hang(p)
    return max(p.m, 0.9 * p.ungraded().sv)                  # (grade moves strokes, not layout)


def bar_hang(p):
    """How far bars hang past the body: half of Mono's cell margin, nothing
    in the proportional cuts (where the body grows instead)."""
    return (p.fig_adv - p.fig_w) / 4 if p.mono else 0.0


def bar_inset(p):
    """How far the letter stands in from the body's side the bars cross."""
    return bar_out(p) - bar_hang(p)


def bar_pair(g, yc, x0, x1):
    """Two bars from x0 to x1 about yc (see pair). Returns their centres."""
    t, gap = pair(g)
    if one_bar(g):
        g.stroke((x0, yc, pair_t(g.p)), (x1, yc))
        mark_bars(g, x0, x1, yc, yc)
        return yc, yc
    off = (t + gap) / 2
    for y in (yc - off, yc + off):
        g.stroke((x0, y, t), (x1, y))
    mark_bars(g, x0, x1, yc - off, yc + off)
    return yc - off, yc + off


def fit_pair(g, lo, hi, x0, x1):
    """A pair of bars in the room between two of the letter's strokes (the
    white from lo to hi), centred in it. Where the room is short of the
    pair and a pair's white either side, the three whites (under, between,
    over) share it evenly."""
    t, gap = pair(g)
    gap = min(gap, (hi - lo - 2 * t) / 3)
    off = (t + gap) / 2
    yc = (lo + hi) / 2
    for y in (yc - off, yc + off):
        g.stroke((x0, y, t), (x1, y))
    mark_bars(g, x0, x1, yc - off, yc + off)


def pair_band(g):
    """Height of the glyph's pair of bars, white included."""
    t, gap = pair(g)
    return 2 * t + gap


# --- C, and what crosses it ------------------------------------------------------

def _c_width(extra=0.0):
    return lambda p: letter_width(9, 2)(p) + extra * p.m


@cur('uni20B5', '₵', growing_width(9, 2, 1.5))
def cedi(g):
    """C with a stroke through it, right of the middle so the counter's
    closed part stays open."""
    p = g.p
    REGISTRY['C'].fn(g)
    x = 0.5 * g.W + 0.25 * p.sv
    g.stroke((x, -1.5 * p.m), (x, p.cap + 1.5 * p.m))
    g.clip = (0, -1.5 * p.m, g.W, p.cap + 1.5 * p.m)


def _stubs(g, xs, top, bot, h):
    """Strokes standing out of a letter's top and bottom bars."""
    p = g.p
    for x in xs:
        g.stroke((x, top - g.sh / 2), (x, top + h))
        g.stroke((x, bot + g.sh / 2), (x, bot - h))


def _stub_xs(p, xc):
    d = (p.sv + max(1.25 * p.m, 0.75 * p.sv)) / 2
    return (xc - d, xc + d)


@cur('colonmonetary', '₡', growing_width(9, 2, 1.0))
def colon_sign(g):
    """C with two strokes standing out of its top and bottom (the colón's
    two lines, shown where they leave the letter)."""
    p = g.p
    REGISTRY['C'].fn(g)
    h = 1.5 * p.m
    _stubs(g, _stub_xs(p, 0.5 * g.W), p.cap, 0.0, h)
    g.clip = (0, -h, g.W, p.cap + h)


@cur('uni20BF', '₿', growing_width(9, 2, 1.0))
def bitcoin(g):
    """B with two strokes standing out of its top and bottom."""
    p = g.p
    REGISTRY['B'].fn(g)
    f = Frame(g, 9)
    h = 1.5 * p.m
    _stubs(g, _stub_xs(p, (f.X(1) + f.X(7)) / 2), p.cap, 0.0, h)
    g.clip = (0, -h, g.W, p.cap + h)


@cur('uni20B2', '₲', letter_width(9, 2))
def guarani(g):
    """G with a stroke standing out of its top and bottom: drawn through it,
    the stroke would close the white under the G's bar."""
    p = g.p
    REGISTRY['G'].fn(g)
    h = 1.5 * p.m
    _stubs(g, [0.5 * g.W], p.cap, 0.0, h)
    g.clip = (0, -h, g.W, p.cap + h)


def _small_letter(p, k=0.55, stroke=0.85):
    """A letter's parameters at a smaller size (symkit.small_letter), its
    x-height its cap height (a small capital or a small r standing in a C)."""
    from .symkit import small_letter
    q = small_letter(p, k, stroke)
    return q.with_(xh=q.cap)


@cur('uni20A2', '₢', _c_width(1.0))
def cruzeiro(g):
    """C holding a small r: its stem stands on the C's bottom bar, its arm
    reaches out through the mouth."""
    p = g.p
    wc = g.W - p.m
    stamp(g, 'C', width=wc)
    # the r as tall as leaves a stroke's white under the C's upper beak
    k = min(0.62, max(0.45, (p.cap - beak_depth(p) - wmin(p)) / p.cap))
    pr = _small_letter(p, k, 0.7).with_(mono=False)        # a letter inside a sign: the plain r, not Mono's footed one
    wr = REGISTRY['r'].width(pr)
    stamp(g, 'r', dx=g.W - wr - 0.25 * p.m, p=pr)


def _ce_layout(p):
    """₠: a raised C and an E on the baseline, both at 0.7, the E as close
    as a stroke's white allows."""
    from shapely import affinity
    from ..geom import rings_to_shapely
    ps = _small_letter(p, 0.7)
    c = draw('C', ps)
    e = draw('E', ps)
    dy = p.cap - ps.cap
    a = affinity.translate(rings_to_shapely(c.rings()), 0, dy)
    b0 = rings_to_shapely(e.rings())
    lo, hi = 0.0, c.W + 2 * p.sv
    for _ in range(18):
        mid = (lo + hi) / 2
        if a.distance(affinity.translate(b0, mid, 0)) >= wmin(p):
            hi = mid
        else:
            lo = mid
    return ps, dy, hi, hi + e.W


@cur('uni20A0', '₠', lambda p: _ce_layout(p)[3])
def euroecu(g):
    p = g.p
    ps, dy, dx, _ = _ce_layout(p.with_(mono=False))
    stamp(g, 'C', 0, dy, p=ps)
    stamp(g, 'E', dx, 0, p=ps)


def _under_bar(g, name, width=None):
    """A letter over a bar on the descender's floor, raised where heavy
    strokes leave too little white between them."""
    p = g.p
    t = g.sh
    lift = max(0.0, t + wmin(p) - p.desc)
    sub = stamp(g, name, 0, lift, width=width)
    xs = [x for r in sub.rings() for x, _ in r]
    y = -p.desc + t / 2
    g.stroke((min(xs), y), (max(xs), y))


@cur('dong', '₫', lambda p: REGISTRY['dcroat'].width(p), kind='lower')
def dong(g):
    _under_bar(g, 'dcroat', g.W)


@cur('uni20C0', '⃀', lambda p: REGISTRY['C'].width(p))
def som(g):
    _under_bar(g, 'C', g.W)


# --- Letters with bars -----------------------------------------------------------

@cur('uni20A6', '₦', lambda p: REGISTRY['N'].width(p) + 2 * bar_inset(p), squint=BARS_OR_ONE)
def naira(g):
    """N with two bars across, centred between the points where the
    diagonal meets the stems, so the white either side of it matches."""
    p = g.p
    o, hang = bar_inset(p), bar_hang(p)
    wn = g.W - 2 * o
    from .caps import n_diagonal
    sub = inset_letter(g, 'N', o, wn)                       # the N as drawn (condensed, in Mono)
    q = sub.p
    f = frame(q, wn, 10)
    cx = n_diagonal(sub, f.X(1) + q.sv / 2, f.X(9) - q.sv / 2, q.cap)   # its diagonal (caps.N)
    t, gap = pair(g)
    yc = q.cap / 2                                          # the joins lie alike about the middle
    yu, yl = yc + (t + gap) / 2, yc - (t + gap) / 2
    at = lambda y: o + cx(y)[0]                              # the diagonal's centre at height y
    xs_l, xs_r = o + q.sv / 2, g.W - o - q.sv / 2            # the stems' centres
    if one_bar(g):                                          # one bar, run out from the stems only, so it
        g.stroke((-hang, yc, pair_t(p)), (xs_l, yc))        # cuts no sliver against the diagonal
        g.stroke((xs_r, yc, pair_t(p)), (g.W + hang, yc))
        mark_bars(g, -hang, g.W + hang, yc, yc)
        return
    # each bar passes behind the diagonal on one side: the upper is cut
    # between the left stem and the diagonal, the lower between the
    # diagonal and the right stem, so the white each side of the diagonal is
    # one counter, not a cell and a sliver of a triangle
    g.stroke((-hang, yu, t), (xs_l, yu))
    g.stroke((at(yu), yu, t), (g.W + hang, yu))
    g.stroke((-hang, yl, t), (at(yl), yl))
    g.stroke((xs_r, yl, t), (g.W + hang, yl))
    mark_bars(g, -hang, g.W + hang, yl, yu)


@cur('uni20A9', '₩', lambda p: REGISTRY['W'].width(p) + 2 * bar_inset(p), squint=BARS_OR_ONE)
def won(g):
    """W with two bars, the lower one where the middle stem ends."""
    p = g.p
    o, hang = bar_inset(p), bar_hang(p)
    w = g.W - 2 * o
    inset_letter(g, 'W', o, w)
    f = frame(p, w, 14)
    y_lo = f.Y(7)
    off = sum(pair(g))
    bar_pair(g, y_lo + off / 2, -hang, g.W + hang)


@cur('uni20B3', '\u20b3', lambda p: REGISTRY['A'].width(p) + 2 * bar_inset(p), squint=BARS)
def austral(g):
    """A whose crossbar is doubled and drawn out past its legs."""
    p = g.p
    o, hang = bar_inset(p), bar_hang(p)
    w = g.W - 2 * o
    f = frame(p, w, 10)
    k = p.sd / SQRT2
    xl, xr = f.X(1) + o, f.X(9) + o
    ya = p.cap + p.c - k                                    # the A's gable (caps.A)
    yt = ya - (w / 2 - f.X(1))
    g.stroke((xl, 0), (xl, yt), (o + w / 2, ya), (xr, yt), (xr, 0))
    g.clip = (-hang, 0, g.W + hang, p.cap)
    bar_pair(g, f.Y(4), -hang, g.W + hang)


@cur('uni20B8', '₸', letter_width(10, 1), squint=BARS)
def tenge(g):
    """T with a second bar above its own: the stem hangs from the lower."""
    p = g.p
    f = Frame(g, 10)
    t, gap = pair(g)
    y1 = p.cap - t / 2
    y2 = y1 - t - gap
    g.stroke((0, y1, t), (g.W, y1))
    g.stroke((0, y2, t), (g.W, y2))
    g.stroke((g.W / 2, y2), (g.W / 2, 0))
    mark_bars(g, 0, g.W, y2, y1)


@cur('uni20B1', '₱', lambda p: letter_width(10.5, 2)(p) + max(0.0, bar_inset(p) - 1.5 * p.m), squint=BARS)
def peso(g):
    """P whose bowl's top bar and a second bar through the bowl run out to
    the left past the stem."""
    p = g.p
    W = g.W
    hang = bar_hang(p)
    xs = max(1.5 * p.m, bar_inset(p)) + p.sv / 2
    xr = W - p.sv / 2
    top = p.cap
    t, gap = pair(g)
    y1 = top - t / 2
    y2 = y1 - t - gap
    y3 = y2 - t - gap
    g.stroke((xs, 0), (xs, top))
    g.stroke((-hang, y1, t), B(xr, y1), B(xr, y3, None, t), (xs, y3))
    g.stroke((-hang, y2, t), (xr, y2))
    g.clip = (-hang, 0, W, top)
    mark_bars(g, -hang, xr, y3, y1)


@cur('uni20BD', '₽', lambda p: REGISTRY['P'].width(p) + bar_inset(p))
def ruble(g):
    """P with a bar across its stem below the bowl."""
    p = g.p
    dx, hang = bar_inset(p), bar_hang(p)
    inset_letter(g, 'P', dx, g.W - dx)
    f = frame(p, g.W - dx, 9)
    y = min(f.Y(3), f.Y(6) - g.sh - wmin(p))
    g.stroke((-hang, y), (dx + p.sv + bar_out(p) + 1.5 * p.m, y))


@cur('franc', '₣', lambda p: REGISTRY['F'].width(p) + bar_inset(p))
def franc(g):
    """F with a bar across its stem below its arm."""
    p = g.p
    dx, hang = bar_inset(p), bar_hang(p)
    inset_letter(g, 'F', dx, g.W - dx)
    f = frame(p, g.W - dx, 8)
    y = min(f.Y(3), f.Y(6) - g.sh - wmin(p))
    g.stroke((-hang, y), (dx + p.sv + bar_out(p) + p.m, y))


@cur('uni20AD', '₭', lambda p: REGISTRY['K'].width(p) + bar_inset(p))
def kip(g):
    """K with a bar across its stem at the middle."""
    p = g.p
    dx, hang = bar_inset(p), bar_hang(p)
    inset_letter(g, 'K', dx, g.W - dx)
    g.stroke((-hang, p.cap / 2), (dx + p.sv + 1.5 * p.m, p.cap / 2))


@cur('lira', '₤', letter_width(8, 1), squint=BARS)
def lira(g):
    """The pound sign with two bars, centred between its base and its top,
    the white below, between and above them shared evenly where the room
    is short (fit_pair)."""
    f = Frame(g, 8)
    p = f.p
    g.stroke(f.P(8, 11), B(*f.P(2.5, 11)), f.P(2.5, 1))
    g.stroke((0, f.Y(1)), (f.W, f.Y(1)))
    fit_pair(g, f.Y(1) + g.sh / 2, f.Y(11) - g.sh / 2, f.X(0.5), f.X(6))


@cur('uni20B9', '₹', letter_width(9, 2), squint=BARS)
def rupee(g):
    """Two bars on top, a bowl hanging from the first, and a 45-degree leg
    from the bowl's foot to the baseline."""
    f = Frame(g, 9)
    p, W = f.p, f.W
    t, gap = pair(g)
    y1 = p.cap - t / 2
    y2 = y1 - t - gap
    yb = min(f.Y(6), y2 - t - gap)
    xr = f.X(7.5)
    xe = min(W, xr + p.sv / 2)                              # the bars end flush with the bowl's side
    g.stroke((0, y1, t), (xe, y1))
    g.stroke((0, y2, t), (xe, y2))
    mark_bars(g, 0, xe, y2, y1)
    g.stroke((f.X(3), y1, t), B(xr, y1), B(xr, yb, None, t), (f.X(1), yb))
    k = p.sd / SQRT2
    a = f.X(1) - p.sv / 2 + yb + g.sh / 2 + k - p.c        # leg: x + y = a, leaving the bowl's foot
    g.stroke((a - yb, yb), (a, 0), start='h', end='h')
    g.clip = (0, 0, W, p.cap)


@cur('uni20B4', '₴', lambda p: letter_width(9, 2)(p) + 2 * bar_inset(p), squint=BARS)
def hryvnia(g):
    """The reversed S of the hryvnia, open: a top hook (beak, bowl, a
    45-degree spine) that ends on the upper bar, and a bottom hook that
    leaves the lower bar the same way; between the bars nothing, so the
    white there is whole at every weight. A beak shortens to keep a
    stroke's white from its bar rather than run into it."""
    f = Frame(g, 9)
    p, W, H = f.p, f.W, f.p.cap
    d = beak_depth(p)
    o, hang = bar_inset(p), bar_hang(p)
    xl, xr = f.X(1) + o, f.X(8) - o                          # the body, the bars running out past it
    yt, yb = f.Y(11), f.Y(1)
    run = (xr - xl) / 2                                      # the spine: one 45-degree run, corner to corner
    ym = (yt + yb) / 2
    y_hi, y_lo = ym + run, ym - run
    # the pair between the hooks' strokes. Where the room holds the pair
    # with a stroke's white (wmin) in each hook and between, as drawn; where
    # it does not (toward Black), bars and whites share it in five equal
    # parts, so the sign stays open stripes and never closes into slabs
    room = yt - yb - g.sh
    t, gap = pair(g)
    if room - 2 * t - 2 * wmin(p) < gap:
        t = gap = min(t, room / 5)
    gap = min(gap, (room - 2 * t) / 3)
    yu, yl = ym + (t + gap) / 2, ym - (t + gap) / 2
    x_at = lambda y: xl + (y - y_lo)                         # on the spine
    # each beak keeps a stroke's white from its bar; where even a module of
    # beak cannot, there is none, and the hook ends in its corner
    hi_beak = max(H - d, yu + t / 2 + wmin(p))
    lo_beak = min(d, yl - t / 2 - wmin(p))
    beak_hi = hi_beak <= yt - g.sh / 2 - p.m
    beak_lo = lo_beak >= yb + g.sh / 2 + p.m
    top = [(xl, hi_beak), B(xl, yt)] if beak_hi else [(xl, yt)]
    foot = [B(xr, yb), (xr, lo_beak)] if beak_lo else [(xr, yb)]
    g.stroke(*top, B(xr, yt), (xr, y_hi), (x_at(yu), yu), start='flat' if beak_hi else 'v', end='h')
    g.stroke((x_at(yl), yl), (xl, y_lo), B(xl, yb), *foot, start='h', end='flat' if beak_lo else 'v')
    for y in (yl, yu):
        g.stroke((-hang, y, t), (W + hang, y))
    mark_bars(g, -hang, W + hang, yl, yu)


def _cross_pair(p):
    """Two parallel 45-degree strokes across a stem: their thickness (the
    diagonal's, thinning toward Black to 0.6 of it, as a pair must), the
    vertical step between them (white across of half a stem, or a module),
    and how far each reaches either side of the stem's centre (never less
    than the stem's half and a module and a quarter, so they read as
    strokes and not as bumps on the stem)."""
    t = p.sd * (1 - 0.4 * heaviness(p))
    dy = SQRT2 * (t + max(p.m, 0.5 * p.sv))
    e = 1.4 * p.m + p.sv / 2
    return t, dy, e


def _free_arm(p):
    """How far a crossing stroke's arm reaches where nothing is in its way:
    long enough past the stem to read as a stroke, not a bump on it."""
    return 2.0 * p.m + 0.75 * p.sv


def _cross(g, xs, y_lo, y_hi, t, arms):
    """The pair across a stem at xs, centred at y_lo and y_hi; ``arms``:
    (lower left, lower right, upper left, upper right) reaches."""
    a = arms
    for y, el, er in ((y_lo, a[0], a[1]), (y_hi, a[2], a[3])):
        g.stroke((xs - el, y - el, across(g.p, t, (1, 1))), (xs + er, y + er), start='v', end='v')


@cur('uni20BA', '\u20ba', growing_width(9, 2, 1.0))
def turkishlira(g):
    """A stem whose foot turns along the baseline and up the right side, two
    45-degree strokes across the stem."""
    f = Frame(g, 9)
    p = f.p
    xs = f.X(3)
    g.stroke((xs, p.cap), B(xs, f.Y(1)), B(*f.P(8, 1)), f.P(8, 6))
    t, dy, e = _cross_pair(p)
    # the pair over the bowl: the lower stroke's right arm stays a stroke's
    # white clear of the bowl's right side, so it rises as the stem thickens
    yc = max(f.Y(6.5), f.Y(1) + g.sh / 2 + wmin(p) + 0.71 * t + dy / 2 + max(0.0, e - (f.X(8) - xs - p.sv)))
    ef = _free_arm(p)
    _cross(g, xs, yc - dy / 2, yc + dy / 2, t, (ef, e, ef, ef))   # only the lower stroke's right arm is over the bowl


@cur('uni20AE', '\u20ae', letter_width(10, 1))
def tugrik(g):
    """T with two 45-degree strokes across its stem. The upper stroke stays
    a stroke's white under the bar; at heavy weights the lower one may run
    out through the baseline, cut flat by it, rather than crowd the stem."""
    f = Frame(g, 10)
    p = f.p
    g.stroke(f.P(0, 11), f.P(10, 11))
    xs = f.X(5)
    g.stroke((xs, f.Y(11)), (xs, 0))
    t, dy, e = _cross_pair(p)
    top = f.Y(11) - g.sh / 2 - wmin(p) - 0.71 * t           # the upper stroke's highest centre point
    y_hi = min(0.42 * p.cap + dy / 2, top - e)
    ef = _free_arm(p)
    _cross(g, xs, y_hi - dy, y_hi, t, (e, ef, ef, e))           # the arms toward the bar and the baseline kept short
    g.clip = (0, 0, f.W, p.cap)


@cur('uni20A5', '₥', letter_width(12, 3), kind='lower')
def mill(g):
    """m with a 2:1 stroke through its middle stem, shown where it stands out
    of it, below the baseline and over the x-height (drawn across the
    arches, it would close their white)."""
    p = g.p
    sub = stamp(g, 'm', width=g.W)
    f = Frame(g, 12, 'lower')
    xc = f.X(6)
    h = 1.5 * p.m + p.ss / 2
    sh = sub.sh
    g.stroke((xc, sh), (xc - h / 2, -h), start='flat', end='h')
    y0 = p.xh - sh - p.leg - p.m                            # (from below the stem's chamfered top)
    g.stroke((xc, y0), (xc + (p.xh + h - y0) / 2, p.xh + h), start='flat', end='h')
    g.clip = None


@cur('uni20BC', '₼', letter_width(10, 2))
def manat(g):
    """An arch on two legs with a stem through its top up to the cap height."""
    f = Frame(g, 10)
    p, W = f.p, f.W
    ya = f.Y(8)
    g.stroke(f.P(1, 0), B(f.X(1), ya), B(f.X(9), ya), f.P(9, 0))
    g.stroke((W / 2, f.Y(3.5)), (W / 2, p.cap))


@cur('uni20BE', '₾', letter_width(10, 2))
def lari(g):
    """An arch whose left leg turns along the baseline into a bar, its right
    leg ending in a beak; two short stems rise out of its top."""
    f = Frame(g, 10)
    p, W = f.p, f.W
    ya = f.Y(8)
    d = beak_depth(p)
    g.stroke((W, f.Y(1)), B(f.X(1), f.Y(1)), B(f.X(1), ya), B(f.X(9), ya), (f.X(9), f.Y(1) + g.sh / 2 + d))
    for x in _stub_xs(p, W / 2):
        g.stroke((x, ya), (x, p.cap))


@cur('uni20AA', '₪', lambda p: 4 * p.sv + 3 * max(1.5 * p.m, 0.75 * p.sv))
def sheqel(g):
    """Two hooks interlocked: a stem rising and turning down on the right,
    and inside it a stem falling and turning up on the right."""
    p, W, H = g.p, g.W, g.p.cap
    gap = max(1.5 * p.m, 0.75 * p.sv)
    xs = [p.sv / 2 + i * (p.sv + gap) for i in range(4)]
    yt, yb = H - g.sh / 2, g.sh / 2
    g.stroke((xs[0], 0), B(xs[0], yt), B(xs[2], yt), (xs[2], g.sh + gap))
    g.stroke((xs[1], H - g.sh - gap), B(xs[1], yb), B(xs[3], yb), (xs[3], H))
    g.clip = (0, 0, W, H)


# --- Letters set as one sign -------------------------------------------------------

def _letters(name, ch, names, kind='cap'):
    """Letters set as one sign, spaced on the x-height zone (capitals and
    lowercase alike)."""
    def fn(g):
        set_tight(g, names, zone=(0.0, g.p.xh))
    glyph(name, ch, lambda p: tight_width(names, (0.0, p.xh))(p), kind=kind)(fn)


_letters('peseta', '₧', ['P', 't', 's'])
_letters('uni20A8', '₨', ['R', 's'])
_letters('uni20AF', '₯', ['uni0394', 'uni03C1'])


@cur('uni20B6', '₶', tight_width(['l', 't'], (0.0, 540.0)), kind='lower')
def livretournois(g):
    """l and t, the t's crossbar drawn back through the l."""
    p = g.p
    set_tight(g, ['l', 't'], zone=(0.0, p.xh))
    y = p.xh - g.sh / 2
    g.stroke((0, y), (g.W - 1.5 * p.m, y))


_letters('uni20B7', '\u20b7', ['S', 'm'])


@cur('uni20B0', '₰', letter_width(8, 2), kind='lower')
def pfennig(g):
    """A bowl on the x-height whose right side rises to the ascender and
    turns back over it to a beak, and runs on below the baseline and turns
    back (the italic f's descender)."""
    f = Frame(g, 8, 'asc')
    p = f.p
    g.clip = (0, -p.desc, f.W, p.asc)
    g.stroke(B(*f.P(1, 1)), B(*f.P(7, 1)), B(*f.P(7, 8)), B(*f.P(1, 8)), closed=True)
    beak = max(f.Y(12) - beak_depth(p) + g.sh / 2, p.xh + max(p.m, 0.6 * p.sv))   # clear of the bowl
    g.stroke((f.X(2), min(beak, f.Y(12) - 0.01)), B(*f.P(2, 12)), B(*f.P(7, 12)), B(*f.P(7, -2)), f.P(2, -2))


@cur('uni20BB', '\u20bb', lambda p: REGISTRY['m'].width(p) + _loop_w(p), kind='lower')
def nordicmark(g):
    """An m whose first stem rises into the script l's loop, turned to the
    left."""
    from .letterlike import loop_l
    p = g.p
    dx = _loop_w(p)
    sub = stamp(g, 'm', dx, width=g.W - dx)
    xs = dx + p.sv / 2
    y_top = p.asc - sub.sh / 2
    g.stroke((xs, p.xh - sub.sh / 2), (xs, y_top))
    loop_l(g, xs, y_top, side=-1)


def _loop_w(p):
    from .letterlike import loop_w
    return loop_w(p) + p.sv / 2
