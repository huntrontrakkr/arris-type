"""Mathematical operators (U+2200-22FF), on the math axis.

Every operator is built from a few parts that the existing signs already
use (+ - = < <= in ``punct``), so they align in an equation:

* the **operator box**: the plus sign's width (8 modules), as tall as it
  is wide, centred on the axis (half the cap height); set signs (subset,
  union, element), tacks and turnstiles fill it;
* **bars** a module or four fifths of a bar apart (the equal sign's
  white), stacked as tight stacks are: where a stack would outgrow the
  line its horizontals thin, down to 0.7 of the weight's own;
* the **tilde**: the asciitilde's step (up at 45 degrees, along, down,
  along), its rise never less than a bar and half a stem, so its bays
  stay open;
* the **chevron** of < and <= (45-degree arms meeting in a point); the
  stacked relations shrink it so the stack is as tall as <=;
* **bowls**: set signs turn their corners as the letters' bowls do; the
  square set signs keep plain corners (an edge break);
* **rings**: octagons (the degree sign's, larger for the circled
  operators, whose body grows with the stroke so their counters stay
  open);
* the **negation**: the not-equal sign's 2:1 stroke, long enough to cross
  whatever it negates;
* **dots**: the period's square dot, centred.

Big operators (n-ary sum, product, union..., the integral) span the
brackets' height, the descender to above the caps.
"""
from __future__ import annotations

from ..draw import B, REGISTRY, draw, glyph
from ..params import SQRT2
from .figures import beak_depth, heaviness
from .letterframe import STEEP, growing_width, letter_width
from .punct import _ring, axis, dot

ALIASES = {}


def _mono(width):
    """A body that never outgrows the monospaced cell."""
    return lambda p: min(width(p), p.fig_w) if p.mono else width(p)


def op(name, char, width=None, sides=1.0, solid=False):
    w = _mono(width or letter_width(8, 1))
    return glyph(name, char, w, kind=('punct', sides), solid=solid)


def u(cp):
    return f'uni{cp:04X}'


OPW = letter_width(8, 1)                       # the plus sign's body
RINGW = growing_width(8, 1, 2.6)               # circled and squared operators: counters grow with the stroke


def eq_gap(g):
    """White between stacked bars: the equal sign's (punct.eq_white)."""
    from .punct import eq_white
    return eq_white(g)


def kv(g):
    """Half a 2:1 stroke's extent up and down past its centreline: a
    chevron's arms reach this far beyond their ends."""
    import math
    from ..draw import _thickness
    from .punct import SLOPE
    return _thickness(g.p, g.sh)((2, 1)) / (2 * math.cos(SLOPE))


def kd(p):
    """Half a 45-degree stroke's extent along an axis."""
    return p.sd / SQRT2


def span(p):
    """The brackets' height: big operators span it."""
    return -p.desc + 0.5 * p.m, p.cap + 0.5 * p.m


# --- Components: a height and a drawing centred at yc ---------------------------

class Bar:
    def __init__(self, x0=None, x1=None):
        self.x0, self.x1 = x0, x1

    def height(self, g):
        return g.sh

    def draw(self, g, yc):
        g.stroke((0 if self.x0 is None else self.x0, yc), (g.W if self.x1 is None else self.x1, yc))


class Bars:
    def __init__(self, n, x0=None, x1=None):
        self.n, self.x0, self.x1 = n, x0, x1

    def height(self, g):
        return self.n * g.sh + (self.n - 1) * eq_gap(g)

    def draw(self, g, yc):
        step = g.sh + eq_gap(g)
        for i in range(self.n):
            y = yc + (i - (self.n - 1) / 2) * step
            g.stroke((0 if self.x0 is None else self.x0, y), (g.W if self.x1 is None else self.x1, y))


TILDEW = growing_width(8, 1, 1.5)               # tilde signs: room for the step's bays at heavy weights


def tilde_rise(g):
    """The tilde's rise: a quarter of its width, or a bar and a third of a
    stem, so the bays above and below its flats stay open; but never so
    much that the flats' inner edges vanish (a graded Black keeps its
    body)."""
    from ..draw import _thickness
    p = g.p
    th = _thickness(p, g.sh)                                 # (the italic's own thicknesses)
    sd, sh = max(th((1, 1)), th((-1, 1))), th((1, 0))
    # a flat's inner edge loses sqrt2 sd - sh to the turns at its ends
    flat = max(0.5 * sh, SQRT2 * sd - sh) + 0.25 * p.sv
    return min(max(g.W / 4, g.sh + 0.35 * p.sv), (g.W - 2 * flat) / 2)


class Tilde:
    """A step on the axis: half way up at 45 degrees, along, down, along,
    half way up again (a half turn of itself, as a tilde is)."""

    def __init__(self, mirror=False, x0=0.0, x1=None):
        self.mirror, self.x0, self.x1 = mirror, x0, x1

    def height(self, g):
        return tilde_rise(g) + g.sh

    def draw(self, g, yc):
        x0, x1 = self.x0, (g.W if self.x1 is None else self.x1)
        d = tilde_rise(g)
        f = max((x1 - x0 - 2 * d) / 2, 0.25 * d)          # the flats share what the diagonals leave
        lo, hi = yc - d / 2, yc + d / 2
        pts = [(x0, yc), (x0 + d / 2, hi), (x0 + d / 2 + f, hi), (x0 + 1.5 * d + f, lo),
               (x0 + 1.5 * d + 2 * f, lo), (x0 + 2 * d + 2 * f, yc)]
        if self.mirror:
            pts = [(x0 + x1 - x, y) for x, y in pts][::-1]
        # its ends cut upright, unless a half rise is too short for that
        # under its stroke (the italic Black at the heaviest grade): then square
        from ..draw import _thickness
        th = _thickness(g.p, g.sh)
        sd = max(th((1, 1)), th((-1, 1)))
        cap = 'v' if d / 2 > (SQRT2 * sd - th((1, 0))) / 2 + 0.05 * g.p.sv else 'flat'
        g.stroke(*pts, start=cap, end=cap)


class Chevron:
    """The < chevron (punct._chevron), pointing left (or right): 2:1 arms
    reaching 2h across and h up and down; ``h`` None: the < itself, or as
    large as the stack lets it be. It stands at the right of the body
    (left, pointing right), as <='s does; ``x1`` moves its open end."""

    def __init__(self, right=False, h=None, x1=None):
        self.right, self.h, self.x1 = right, h, x1

    def height(self, g):
        return 2 * self.size(g) + 2 * kv(g)

    def size(self, g):
        if self.h is not None:
            return self.h
        from .punct import chevron_geometry
        return chevron_geometry(g)[1] / 2

    def draw(self, g, yc):
        W = g.W if self.x1 is None else self.x1
        h = self.size(g)
        pts = [(W, yc + h), (W - 2 * h, yc), (W, yc - h)]
        if self.right:
            pts = [(g.W - x, y) for x, y in pts]
        g.stroke(*pts, start='v', end='v')


class Curly(Chevron):
    """The precedes sign's chevron: the < chevron's 2:1 arms, running out
    level for the last quarter of its reach."""

    def size(self, g):
        """Its half height: at most what leaves the level run a quarter of
        the reach (2:1 arms need twice their height across)."""
        from .punct import chevron_geometry
        reach = chevron_geometry(g)[1]
        h = 0.38 * reach if self.h is None else self.h
        return min(h, 0.385 * reach)

    def draw(self, g, yc):
        from .punct import chevron_geometry
        W = g.W
        h = self.size(g)
        A = chevron_geometry(g)[1]
        pts = [(W, yc + h), (W - A + 2 * h, yc + h), (W - A, yc), (W - A + 2 * h, yc - h), (W, yc - h)]
        if self.right:
            pts = [(W - x, y) for x, y in pts]
        g.stroke(*pts, start='v', end='v')


class Shape:
    """Any drawing of a known height, centred at yc: fn(g, yc)."""

    def __init__(self, h, fn):
        self.h, self.fn = h, fn

    def height(self, g):
        return self.h(g) if callable(self.h) else self.h

    def draw(self, g, yc):
        self.fn(g, yc)


TALL = lambda p: p.cap + 2 * p.m               # the tallest a stacked relation grows (about <='s)
STRUCK = lambda p: TALL(p) - 3 * p.m            # a stack a negation crosses: room for it to run past the bars


def stack(g, comps, centre=None, flex=None, gap=None, tall=None):
    """Stack components top to bottom, the white between them the equal
    sign's, centred on the axis. A stack taller than TALL thins its
    horizontals (down to 0.7 of the weight's, the tight-stack rule); a
    flexible component (a Chevron with no size) takes the height that
    makes the stack as tall as <=."""
    p = g.p
    centre = axis(p) if centre is None else centre
    gapf = (lambda: eq_gap(g)) if gap is None else (lambda: gap(g))
    limit = (tall or TALL)(p)
    flex = [c for c in comps if isinstance(c, Chevron) and c.h is None]

    def fit(k):
        g.sh_k = k
        if flex:
            fixed = sum(c.height(g) for c in comps if c not in flex) + gapf() * (len(comps) - 1)
            room = le_height(g) - fixed
            each = (room / len(flex) - 2 * kv(g)) / 2
            for c in flex:
                c.h_fit = max(each, 0.75 * p.sv)
        ext = [_extent(c, g) for c in comps]
        return ext, sum(y1 - y0 for y0, y1 in ext) + gapf() * (len(comps) - 1)

    # thin the horizontals just as far as the limit needs (continuously, so
    # the variable font interpolates it), never below 0.7
    ext, total = fit(1.0)
    if total > limit:
        lo, hi = 0.7, 1.0
        if fit(lo)[1] <= limit:
            for _ in range(14):
                mid = (lo + hi) / 2
                if fit(mid)[1] <= limit:
                    lo = mid
                else:
                    hi = mid
        ext, total = fit(lo)
    y = centre + total / 2
    for c, (y0, y1) in zip(comps, ext):
        _draw(c, g, y - y1)
        y -= (y1 - y0) + gapf()


def _extent(c, g):
    """(bottom, top) of a component's ink drawn at 0: measured, so the
    white between stacked parts is exactly the stack's."""
    from ..draw import Glyph, _thickness
    from ..geom import stroke_polygon
    tmp = Glyph(g.p, W=g.W, sh_k=g.sh_k, sh_auto=g.sh_auto)
    _draw(c, tmp, 0.0)
    th = _thickness(tmp.p, tmp.sh)
    polys = [stroke_polygon(s, th, tmp.p.c) for s in tmp.strokes] + list(tmp.extra)
    return min(q.bounds[1] for q in polys), max(q.bounds[3] for q in polys)


def _h(c, g):
    if isinstance(c, Chevron) and c.h is None and hasattr(c, 'h_fit'):
        return Chevron(c.right, c.h_fit).height(g)
    return c.height(g)


def _draw(c, g, yc):
    if isinstance(c, Chevron) and c.h is None and hasattr(c, 'h_fit'):
        type(c)(c.right, c.h_fit, c.x1).draw(g, yc)
    else:
        c.draw(g, yc)


def le_height(g):
    """The less-than-or-equal sign's height: its chevron (the < itself),
    the equal sign's white and the bar."""
    return Chevron().height(g) + eq_gap(g) + g.sh


def negate(g, half=None, x=None, y=None):
    """The not-equal sign's 2:1 stroke, crossing at (x, y) and reaching
    ``half`` up and down (default: the not-equal sign's four modules)."""
    p = g.p
    x = g.W / 2 if x is None else x
    y = axis(p) if y is None else y
    half = 4 * p.m if half is None else half
    g.stroke((x - half / 2, y - half), (x + half / 2, y + half), start='h', end='h')


def cdot(g, x, y, s=None):
    """A square dot centred at (x, y)."""
    s = g.p.dot() if s is None else s
    g.stroke((x, y - s / 2, s), (x, y + s / 2))


def dot_space(g):
    """White between a dot and a bar."""
    return max(0.8 * g.sh, 0.75 * g.p.m)


# --- Bars and tildes ---------------------------------------------------------------

@op('equivalence', '≡')
def equivalence(g):
    stack(g, [Bars(3)])


@op(u(0x2262), '≢')
def notidentical(g):
    stack(g, [Bars(3)], tall=STRUCK)
    negate(g, half=_neg_half(g))


@op(u(0x2263), '≣')
def strictly(g):
    stack(g, [Bars(4)])


def _neg_half(g):
    """A negation long enough to cross the drawing: its half height plus
    three quarters of a module, never shorter than the not-equal sign's."""
    from shapely.geometry import box
    rings = g.rings()
    ys = [y for r in rings for _, y in r]
    a = axis(g.p)
    return max(4 * g.p.m, max(max(ys) - a, a - min(ys)) + 0.75 * g.p.m)


@op('similar', '∼', width=TILDEW)
def similar(g):
    stack(g, [Tilde()])


@op(u(0x223D), '∽', width=TILDEW)
def reversedtilde(g):
    stack(g, [Tilde(mirror=True)])


@op(u(0x2241), '≁', width=TILDEW)
def nottilde(g):
    stack(g, [Tilde()])
    negate(g, half=_neg_half(g))


@op(u(0x2242), '≂', width=TILDEW)
def minustilde(g):
    stack(g, [Bar(), Tilde()])


@op(u(0x2243), '≃', width=TILDEW)
def asymptequal(g):
    stack(g, [Tilde(), Bar()])


@op(u(0x2244), '≄', width=TILDEW)
def notasymptequal(g):
    stack(g, [Tilde(), Bar()])
    negate(g, half=_neg_half(g))


@op('congruent', '≅', width=TILDEW)
def congruent(g):
    stack(g, [Tilde(), Bars(2)])


@op(u(0x2247), '≇', width=TILDEW)
def notcongruent(g):
    stack(g, [Tilde(), Bars(2)])
    negate(g, half=_neg_half(g))


@op('approxequal', '≈', width=TILDEW)
def approxequal(g):
    stack(g, [Tilde(), Tilde()])


@op(u(0x2249), '≉', width=TILDEW)
def notapprox(g):
    stack(g, [Tilde(), Tilde()])
    negate(g, half=_neg_half(g))


@op(u(0x224A), '≊', width=TILDEW)
def approxorequal(g):
    stack(g, [Tilde(), Tilde(), Bar()])


@op(u(0x224B), '≋', width=TILDEW)
def tripletilde(g):
    stack(g, [Tilde(), Tilde(), Tilde()])


@op(u(0x2240), '≀', width=lambda p: 2 * p.sv + 1.5 * p.m)
def wreath(g):
    """The tilde stood on end, the box's height."""
    p = g.p
    a = axis(p)
    d = g.W - p.sv
    lo, hi, mid = p.sv / 2, g.W - p.sv / 2, g.W / 2
    H = box_r(g) + g.sh / 2 + 0.5 * p.m
    f = max(H - d, 0.5 * p.sv)
    y0 = a - (d + f)
    g.stroke((mid, y0), (hi, y0 + d / 2), (hi, y0 + d / 2 + f), (lo, y0 + 1.5 * d + f), (lo, y0 + 1.5 * d + 2 * f),
             (mid, y0 + 2 * d + 2 * f), start='h', end='h')


def bump_h(g):
    """A bump's rise above its bar (centrelines): its white a third of a
    stem deep, at least a module and a half."""
    return max(1.5 * g.p.m, g.sh + 0.35 * g.p.sv)


def _bump_bar(g, y, up=True):
    """A bar with a bump in its middle, a small octagon's half (≏ ≎)."""
    p = g.p
    d = bump_h(g) * (1 if up else -1)
    hw = max(1.75 * p.m, p.sv / 2 + 0.4 * p.sv) + p.sv / 2      # half the bump, centrelines
    leg = min(0.6 * abs(d), hw - p.sv / 2)
    b0, b1 = g.W / 2 - hw, g.W / 2 + hw
    g.stroke((0, y), (b0, y), B(b0, y + d, leg), B(b1, y + d, leg), (b1, y), (g.W, y))


def _bump_height(g):
    return bump_h(g) + g.sh


@op(u(0x224E), '≎', width=TILDEW)
def geomequiv(g):
    stack(g, [Shape(_bump_height, lambda g, y: _bump_bar(g, y - (_bump_height(g) - g.sh) / 2, True)),
              Shape(_bump_height, lambda g, y: _bump_bar(g, y + (_bump_height(g) - g.sh) / 2, False))])


@op(u(0x224F), '≏', width=TILDEW)
def difference(g):
    stack(g, [Shape(_bump_height, lambda g, y: _bump_bar(g, y - (_bump_height(g) - g.sh) / 2, True)), Bar()])


@op(u(0x224D), '≍', width=TILDEW)
def equivalent(g):
    """A smile over a frown: bars whose ends turn away from each other at
    45 degrees."""
    def bent(g, y, up):
        d = bent_h(g) * (1 if up else -1)
        W = g.W
        g.stroke((0, y + d), (abs(d), y), (W - abs(d), y), (W, y + d), start='v', end='v')
    bent_h = lambda g: max(1.25 * g.p.m, 0.5 * g.sh + 0.35 * g.p.sv)
    hb = lambda g: bent_h(g) + g.sh
    stack(g, [Shape(hb, lambda g, y: bent(g, y - (hb(g) - g.sh) / 2, True)),
              Shape(hb, lambda g, y: bent(g, y + (hb(g) - g.sh) / 2, False))])


# --- Equals with marks --------------------------------------------------------------

def _eq_with(g, above=None, below=None, left=None, right=None):
    """The equal sign with dots (or another mark) above and below, or
    either side diagonally."""
    p = g.p
    a = axis(p)
    s = p.dot()
    off = (g.sh + eq_gap(g)) / 2
    for y in (a - off, a + off):
        g.stroke((0, y), (g.W, y))
    top = a + off + g.sh / 2 + dot_space(g) + s / 2
    bot = a - off - g.sh / 2 - dot_space(g) - s / 2
    if above is not None:
        cdot(g, above, top)
    if below is not None:
        cdot(g, below, bot)


@op(u(0x2250), '≐')
def approaches(g):
    _eq_with(g, above=g.W / 2)


@op(u(0x2251), '≑')
def geomequal(g):
    _eq_with(g, above=g.W / 2, below=g.W / 2)


@op(u(0x2252), '≒')
def imageof(g):
    s = g.p.dot()
    _eq_with(g, above=s / 2, below=g.W - s / 2)


@op(u(0x2253), '≓')
def origof(g):
    s = g.p.dot()
    _eq_with(g, above=g.W - s / 2, below=s / 2)


def _colon_eq(g, colon_left):
    """:= and =: the colon's dots on the axis, a stem's white from the bars."""
    p = g.p
    a = axis(p)
    s = p.dot()
    off = (g.sh + eq_gap(g)) / 2
    gap = max(0.8 * p.sv, p.m)
    xd = s / 2 if colon_left else g.W - s / 2
    x0, x1 = (s + gap, g.W) if colon_left else (0, g.W - s - gap)
    for y in (a - off, a + off):
        g.stroke((x0, y), (x1, y))
    dy = max(off + g.sh / 2 - s / 2, s / 2 + 0.5 * dot_space(g))
    cdot(g, xd, a + dy)
    cdot(g, xd, a - dy)


@op(u(0x2254), '≔', width=lambda p: OPW(p) + p.dot() + max(0.8 * p.sv, p.m))
def colonequals(g):
    _colon_eq(g, True)


@op(u(0x2255), '≕', width=lambda p: OPW(p) + p.dot() + max(0.8 * p.sv, p.m))
def equalscolon(g):
    _colon_eq(g, False)


def _small_ring_box(g, cx, cy, r):
    """A small octagon ring of centreline half-size r at (cx, cy)."""
    p = g.p
    w = max(0.85 * p.sv, 1.12 * p.floor)
    _ring(g, cx - r, cy - r, cx + r, cy + r, w=w, leg=0.6 * r)


def small_ring_r(g):
    """A small ring's centreline half-size: its counter at least half a stem."""
    return small_ring_r_p(g.p)


@op(u(0x2256), '≖', width=growing_width(8, 1, 2.0))
def ringinequal(g):
    """The equal sign with a ring between its bars: the ring's top and foot
    run in the bars, its sides close a small octagon between them."""
    p = g.p
    a = axis(p)
    off = (g.sh + eq_gap(g)) / 2
    for y in (a - off, a + off):
        g.stroke((0, y), (g.W, y))
    r = off
    rx = max(r, small_ring_r(g))
    g.stroke(B(g.W / 2 - rx, a - r, 0.6 * r), B(g.W / 2 + rx, a - r, 0.6 * r), B(g.W / 2 + rx, a + r, 0.6 * r),
             B(g.W / 2 - rx, a + r, 0.6 * r), closed=True)


@op(u(0x2257), '≗')
def ringequal(g):
    r = small_ring_r(g)
    stack(g, [Shape(lambda g: 2 * r + 0.85 * g.p.sv, lambda g, y: _small_ring_box(g, g.W / 2, y, r)), Bars(2)])


@op(u(0x225C), '≜')
def deltaequal(g):
    def tri(g, yc):
        p = g.p
        h = tri_h(g)
        k = kd(p)
        # a small 45-degree delta on a bar
        x0, x1 = g.W / 2 - h, g.W / 2 + h
        yb = yc - (h + k + g.sh / 2) / 2 + g.sh / 2
        g.stroke((x0, yb), (g.W / 2, yb + h), (x1, yb), closed=True)
    # its counter (inradius 0.414 of its reach, less half its strokes) a
    # quarter of a stem at least
    tri_h = lambda g: max(2.2 * g.p.m, (0.25 * g.p.sv + 0.5 * max(g.p.sd, g.sh)) / (SQRT2 - 1))
    stack(g, [Shape(lambda g: tri_h(g) + kd(g.p) + g.sh / 2, tri), Bars(2)])


@op(u(0x225F), '≟')
def questionequal(g):
    p = g.p
    k, t = 0.55, 0.45                                        # strokes in proportion to its size
    ps = p.with_(cap=k * p.cap, m=k * p.m, sv=t * p.sv, sh=t * p.sh, sd=t * p.sd, ss=t * p.ss, c=t * p.c)
    sub = draw('question', ps)
    hq = ps.cap
    def q(g, yc):
        g.add_glyph(sub, (g.W - sub.W) / 2, yc - hq / 2)
    stack(g, [Shape(hq, q), Bars(2)])


# --- Less, greater and their kin ------------------------------------------------------

def _less_full(g, right=False):
    REGISTRY['greater' if right else 'less'].fn(g)


@op(u(0x226E), '≮')
def notless(g):
    _less_full(g)
    negate(g, half=_neg_half(g))


@op(u(0x226F), '≯')
def notgreater(g):
    _less_full(g, True)
    negate(g, half=_neg_half(g))


@op(u(0x2270), '≰')
def notlessequal(g):
    REGISTRY['lessequal'].fn(g)
    _le_strike(g)


@op(u(0x2271), '≱')
def notgreaterequal(g):
    REGISTRY['greaterequal'].fn(g)
    _le_strike(g)


def _le_strike(g):
    """The negation of <= and >=: the not-equal sign's stroke from below the
    bar to above the chevron, crossing both, as tall as the sign needs."""
    negate(g, half=_neg_half(g))


@op(u(0x2266), '≦')
def lessoverequal(g):
    stack(g, [Chevron(), Bars(2)])


@op(u(0x2267), '≧')
def greateroverequal(g):
    stack(g, [Chevron(right=True), Bars(2)])


def _bar_with_stroke(g):
    """A bar crossed by a short 2:1 stroke: the 'not equal' under a relation."""
    def fn(g, yc):
        g.stroke((0, yc), (g.W, yc))
        h = g.sh / 2 + max(1.75 * g.p.m, 1.0 * g.p.sv)
        g.stroke((g.W / 2 - h / 2, yc - h), (g.W / 2 + h / 2, yc + h), start='h', end='h')
    return Shape(lambda g: g.sh, fn)


@op(u(0x2268), '≨')
def lessnotequal(g):
    stack(g, [Chevron(), _bar_with_stroke(g)], gap=lambda g: eq_gap(g) + max(1.75 * g.p.m, 1.0 * g.p.sv) - g.sh / 2)


@op(u(0x2269), '≩')
def greaternotequal(g):
    stack(g, [Chevron(right=True), _bar_with_stroke(g)], gap=lambda g: eq_gap(g) + max(1.75 * g.p.m, 1.0 * g.p.sv) - g.sh / 2)


def _guil_step(p):
    return SQRT2 * (p.sd + max(0.8 * p.m, 0.7 * p.sd))


@op(u(0x226A), '≪', width=lambda p: OPW(p) + _guil_step(p))
def muchless(g):
    p, W = g.p, g.W
    a = axis(p)
    step = _guil_step(p)
    h = max(min(0.85 * (OPW(p) - p.sv / 2), W - step - kd(p)), 1.5 * kd(p))
    for x in (W - step, W):
        g.stroke((x, a + h), (x - h, a), (x, a - h), start='v', end='v')


@op(u(0x226B), '≫', width=lambda p: OPW(p) + _guil_step(p))
def muchgreater(g):
    p, W = g.p, g.W
    a = axis(p)
    step = _guil_step(p)
    h = max(min(0.85 * (OPW(p) - p.sv / 2), W - step - kd(p)), 1.5 * kd(p))
    for x in (0, step):
        g.stroke((x, a + h), (x + h, a), (x, a - h), start='v', end='v')


@op(u(0x2272), '≲', width=TILDEW)
def lessequiv(g):
    stack(g, [Chevron(), Tilde()])


@op(u(0x2273), '≳', width=TILDEW)
def greaterequiv(g):
    stack(g, [Chevron(right=True), Tilde()])


def _lg(g, first_right):
    """< over > (or > over <), centred on the body, together as tall as <=."""
    p = g.p
    h = max((le_height(g) - eq_gap(g) - 4 * kv(g)) / 4, 1.5 * kv(g))
    xr = (g.W + 2 * h) / 2
    stack(g, [Chevron(first_right, h, x1=xr), Chevron(not first_right, h, x1=xr)])


@op(u(0x2276), '≶')
def lessgreater(g):
    _lg(g, False)


@op(u(0x2277), '≷')
def greaterless(g):
    _lg(g, True)


@op(u(0x227A), '≺')
def precedes(g):
    stack(g, [Curly()])


@op(u(0x227B), '≻')
def succeeds(g):
    stack(g, [Curly(right=True)])


@op(u(0x227C), '≼')
def precedeseq(g):
    stack(g, [Curly(), Bar()])


@op(u(0x227D), '≽')
def succeedseq(g):
    stack(g, [Curly(right=True), Bar()])


@op(u(0x226C), '≬', width=lambda p: 2 * p.sv + 3 * p.m)
def between(g):
    """Two brackets back to back, )(, as tall as <: bowls turned toward
    each other, a stem's white apart."""
    p, W = g.p, g.W
    a = axis(p)
    h = 0.85 * (OPW(p) - p.sv / 2)
    gap = max(0.75 * p.sv, p.m)
    xm = W / 2
    xi_l, xi_r = xm - gap / 2 - p.sv / 2, xm + gap / 2 + p.sv / 2
    leg = min(p.leg + p.m, h / 2)
    g.stroke((0, a + h), B(xi_l, a + h, leg), B(xi_l, a - h, leg), (0, a - h), start='v', end='v')
    g.stroke((W, a + h), B(xi_r, a + h, leg), B(xi_r, a - h, leg), (W, a - h), start='v', end='v')


# --- Sets ----------------------------------------------------------------------------

def box_r(g, W=None):
    """The operator box's centreline half-height: the box is as tall as the
    plus sign is wide (or as the body W, for the set signs)."""
    return (OPW(g.p) if W is None else W) / 2 - g.sh / 2


SETW = growing_width(8, 1, 1.2)                # set signs: their bays grow with the stroke


def set_leg(g, r):
    return min(g.p.leg + 0.5 * g.p.m, 0.8 * r)


def subset(g, yc, r, right=False, square=False, x1=None, bar=False):
    """⊂ (or ⊃) of centreline half-height r centred at yc; ``square``: ⊏."""
    p = g.p
    W = g.W if x1 is None else x1
    xl = p.sv / 2
    leg = set_leg(g, r)
    c = (lambda x, y: (x, y)) if square else (lambda x, y: B(x, y, leg))
    pts = [(W, yc + r), c(xl, yc + r), c(xl, yc - r), (W, yc - r)]
    if right:
        pts = [(g.W - q[0], q[1]) if q[0] != 'bowl' else B(g.W - q[1], q[2], q[3]) for q in pts]
    g.stroke(*pts)
    if bar:
        xb0, xb1 = (xl, W - 0.5 * p.m) if not right else (g.W - (W - 0.5 * p.m), g.W - xl)
        g.stroke((xb0, yc), (xb1, yc))


def cup(g, yc, r, down=False, square=False, x0=None, x1=None):
    """∪ (or ∩) of centreline half-height r at yc."""
    p = g.p
    xl = p.sv / 2 if x0 is None else x0
    xr = g.W - p.sv / 2 if x1 is None else x1
    leg = set_leg(g, min(r, (xr - xl) / 2))
    c = (lambda x, y: (x, y)) if square else (lambda x, y: B(x, y, leg))
    s = -1 if down else 1
    g.stroke((xl, yc + s * r), c(xl, yc - s * r), c(xr, yc - s * r), (xr, yc + s * r))


def SetShape(fn):
    return Shape(lambda g: 2 * box_r(g) + g.sh, fn)


def _set(g, fn, below=None, neg=False, bars=2, right=False):
    """A set sign in its box (as tall as it is wide), alone or over a bar
    (or a bar with a stroke); with a negation across. The element signs
    stack three bars in the box, and thin them as tight stacks do."""
    if bars == 3:
        g.stack(3, g.W, ratio=0.8)
        g.sh_k = max(g.sh_k, 0.7)
    if below is None:
        fn(g, axis(g.p), box_r(g, g.W))
    else:
        # over a bar: the sign shrinks so the pair is as tall as <=
        H = le_height(g)
        hb = below.height(g)
        r = (H - hb - eq_gap(g) - g.sh) / 2
        r = min(r, box_r(g, g.W))
        top = axis(g.p) + (2 * r + g.sh + eq_gap(g) + hb) / 2
        fn(g, top - g.sh / 2 - r, r)
        below.draw(g, top - 2 * r - g.sh - eq_gap(g) - hb / 2)
    if neg:
        # (the element signs: crossing their bays where each keeps a pocket
        # half a stem wide, between the stem and the stroke)
        x = None
        if bars == 3:
            p = g.p
            w = p.ss / STEEP[1]
            r = box_r(g, g.W)
            x = max(g.W / 2, 1.5 * p.sv + r / 4 + w / 2)
            if right:
                x = g.W - x
        negate(g, half=_neg_half(g), x=x)


SETS = [
    (0x2282, 'propersubset', lambda g, y, r: subset(g, y, r), None, False),
    (0x2283, 'propersuperset', lambda g, y, r: subset(g, y, r, right=True), None, False),
    (0x2284, 'notsubset', lambda g, y, r: subset(g, y, r), None, True),
    (0x2285, u(0x2285), lambda g, y, r: subset(g, y, r, right=True), None, True),
    (0x2286, 'reflexsubset', lambda g, y, r: subset(g, y, r), 'bar', False),
    (0x2287, 'reflexsuperset', lambda g, y, r: subset(g, y, r, right=True), 'bar', False),
    (0x2288, u(0x2288), lambda g, y, r: subset(g, y, r), 'bar', True),
    (0x2289, u(0x2289), lambda g, y, r: subset(g, y, r, right=True), 'bar', True),
    (0x228A, u(0x228A), lambda g, y, r: subset(g, y, r), 'nbar', False),
    (0x228B, u(0x228B), lambda g, y, r: subset(g, y, r, right=True), 'nbar', False),
    (0x228F, u(0x228F), lambda g, y, r: subset(g, y, r, square=True), None, False),
    (0x2290, u(0x2290), lambda g, y, r: subset(g, y, r, right=True, square=True), None, False),
    (0x2291, u(0x2291), lambda g, y, r: subset(g, y, r, square=True), 'bar', False),
    (0x2292, u(0x2292), lambda g, y, r: subset(g, y, r, right=True, square=True), 'bar', False),
    (0x2229, 'intersection', lambda g, y, r: cup(g, y, r, down=True), None, False),
    (0x222A, 'union', lambda g, y, r: cup(g, y, r), None, False),
    (0x2293, u(0x2293), lambda g, y, r: cup(g, y, r, down=True, square=True), None, False),
    (0x2294, u(0x2294), lambda g, y, r: cup(g, y, r, square=True), None, False),
    (0x2208, 'element', lambda g, y, r: subset(g, y, r, bar=True), None, False),
    (0x2209, 'notelement', lambda g, y, r: subset(g, y, r, bar=True), None, True),
    (0x220B, 'suchthat', lambda g, y, r: subset(g, y, r, right=True, bar=True), None, False),
    (0x220C, u(0x220C), lambda g, y, r: subset(g, y, r, right=True, bar=True), None, True),
]
ELEMENTS = {0x2208, 0x2209, 0x220B, 0x220C}
for cp, nm, fn, below, neg in SETS:
    def make(g, fn=fn, below=below, neg=neg, cp=cp):
        b = {None: None, 'bar': Bar(), 'nbar': _bar_with_stroke(g)}[below]
        _set(g, fn, b, neg, bars=3 if cp in ELEMENTS else 2, right=cp in (0x220B, 0x220C))
    op(nm, chr(cp), width=SETW)(make)


def _small_set(g, right):
    """The small element signs: the element sign three quarters the size,
    its bars a tight stack."""
    p = g.p
    g.stack(3, g.W, ratio=0.8)
    g.sh_k = max(g.sh_k, 0.7)
    subset(g, axis(p), box_r(g, g.W), right=right, bar=True)


SMALLSETW = lambda p: 0.78 * SETW(p)


@op(u(0x220A), '∊', width=SMALLSETW)
def smallelement(g):
    _small_set(g, False)


@op(u(0x220D), '∍', width=SMALLSETW)
def smallcontains(g):
    _small_set(g, True)


@op(u(0x228E), '⊎', width=growing_width(9, 1, 3.5))
def multisetunion(g):
    """The union with a plus inside its cup."""
    p = g.p
    a = axis(p)
    r = box_r(g)
    cup(g, a, r)
    clear = max(0.5 * p.sv, 0.75 * p.m)
    arm = min((g.W - 2 * p.sv) / 2 - clear - g.sh / 2, 0.75 * r)
    yc = a - r + g.sh / 2 + clear + arm
    g.stroke((g.W / 2 - arm, yc), (g.W / 2 + arm, yc))
    g.stroke((g.W / 2, yc - arm), (g.W / 2, yc + arm))


# --- Logic -----------------------------------------------------------------------------

def gable(g, yc, r, down=False, x0=None, x1=None):
    """∧ (or ∨): two 2:1 strokes meeting in a point, the box's width wide."""
    p = g.p
    x0 = 0.0 if x0 is None else x0
    x1 = g.W if x1 is None else x1
    w = p.ss / STEEP[1]                                      # a 2:1 stroke's width across
    half = (x1 - x0 - w) / 2
    hgt = 2 * half
    s = -1 if down else 1
    yb, yt = yc - s * hgt / 2, yc + s * hgt / 2
    lift = (p.ss / 2) * 5 ** 0.5 / 2
    g.stroke((x0 + w / 2, yb), ((x0 + x1) / 2, yt), (x1 - w / 2, yb), start='h', end='h')
    return hgt


def _gable_h(g):
    w = g.p.ss / STEEP[1]
    return g.W - w


@op('logicaland', '∧')
def logicaland(g):
    gable(g, axis(g.p), 0)


@op('logicalor', '∨')
def logicalor(g):
    gable(g, axis(g.p), 0, down=True)


def _light(g):
    """A stack of parts: lighter toward Black (arrows.stack_k)."""
    from .arrows import stack_k
    from ..draw import _lightened
    k = stack_k(g.p)
    if k != 1.0:
        g.p = _lightened(g.p, k)


@op(u(0x22BB), '⊻')
def xor(g):
    _light(g)
    stack(g, [Shape(_gable_h, lambda g, y: gable(g, y, 0, down=True)), Bar()])


@op(u(0x22BC), '⊼')
def nand(g):
    _light(g)
    stack(g, [Bar(), Shape(_gable_h, lambda g, y: gable(g, y, 0))])


@op(u(0x22BD), '⊽')
def nor(g):
    _light(g)
    stack(g, [Bar(), Shape(_gable_h, lambda g, y: gable(g, y, 0, down=True))])


def tack(g, kind, n_v=1, n_h=1, short=False):
    """Turnstiles and tacks in the operator box. kind 'right' (⊢), 'left'
    (⊣), 'down' (⊤), 'up' (⊥); n_v verticals, n_h horizontals; ``short``:
    the vertical half the box (⊦ ⊧)."""
    p = g.p
    a = axis(p)
    r = box_r(g) + g.sh / 2                                  # ink half-height
    gapv = max(0.75 * p.sv, 1.25 * p.m)                      # between verticals (the pilcrow's)
    if kind in ('right', 'left'):
        rs = max(0.6 * r, (g.sh + eq_gap(g)) / 2 * (n_h - 1) + g.sh / 2 + 0.75 * p.sv)   # a short stem, its bays open
        top, bot = (a + r, a - r) if not short else (a + rs, a - rs)
        xs = [p.sv / 2 + i * (p.sv + gapv) for i in range(n_v)]
        x_end = xs[-1] + p.sv / 2
        for x in xs:
            g.stroke((x, bot), (x, top))
        off = (g.sh + eq_gap(g)) / 2
        ys = [a] if n_h == 1 else [a - off, a + off]
        for y in ys:
            g.stroke((xs[0], y), (g.W, y))
        if kind == 'left':
            g.strokes = [type(s_)(tuple(type(nd)(g.W - nd.x, nd.y, nd.bowl, nd.w) for nd in s_.nodes),
                                  s_.closed, s_.start, s_.end) for s_ in g.strokes]
    else:
        yb = a - r + g.sh / 2 if kind == 'up' else a + r - g.sh / 2
        g.stroke((0, yb), (g.W, yb))
        g.stroke((g.W / 2, a - r), (g.W / 2, a + r))


@op(u(0x22A2), '⊢')
def righttack(g):
    tack(g, 'right')


@op(u(0x22A3), '⊣')
def lefttack(g):
    tack(g, 'left')


@op(u(0x22A4), '⊤')
def downtack(g):
    tack(g, 'down')


@op('perpendicular', '⊥')
def uptack(g):
    tack(g, 'up')


@op(u(0x22A6), '⊦')
def assertion(g):
    tack(g, 'right', short=True)


@op(u(0x22A7), '⊧')
def models(g):
    tack(g, 'right', n_h=2, short=True)


@op(u(0x22A8), '⊨')
def true_(g):
    tack(g, 'right', n_h=2)


def _tack_w(n):
    return lambda p: OPW(p) + (n - 1) * (p.sv + max(0.75 * p.sv, 1.25 * p.m))


@op(u(0x22A9), '⊩', width=_tack_w(2))
def forces(g):
    tack(g, 'right', n_v=2)


@op(u(0x22AA), '⊪', width=_tack_w(3))
def triplevert(g):
    tack(g, 'right', n_v=3)


@op(u(0x22AB), '⊫', width=_tack_w(2))
def dblvertdbl(g):
    tack(g, 'right', n_v=2, n_h=2)


def _tack_strike(g, half):
    """A negation across a turnstile's bars, half way from the stem to their
    ends, the turnstile widened so it keeps clear of the stem."""
    p = g.p
    negate(g, half=half, x=(p.sv + g.W) / 2)


NOTW = growing_width(9, 1, 2.5)


@op(u(0x22AC), '⊬', width=NOTW)
def notproves(g):
    tack(g, 'right')
    _tack_strike(g, g.sh / 2 + max(1.5 * g.p.m, 0.75 * g.p.sv))


@op(u(0x22AD), '⊭', width=NOTW)
def nottrue(g):
    tack(g, 'right', n_h=2)
    _tack_strike(g, (g.sh + eq_gap(g)) / 2 + g.sh / 2 + max(1.5 * g.p.m, 0.75 * g.p.sv))


# --- Triangles and the bowtie ------------------------------------------------------------

def triangle(g, x_tip, yc, h, right=False):
    """A triangle pointing left (right), its sides at 2:1 (the media
    controls' triangle, as wide as it is tall), its point at x_tip, its
    upright side 2h back from it, reaching h up and down."""
    s = 1 if right else -1
    x_back = x_tip - s * 2 * h
    g.stroke((x_tip, yc), (x_back, yc + h), (x_back, yc - h), closed=True)


def _tip(p):
    """How far a 2:1 triangle's point reaches past its vertex: its sides'
    stroke over sin 26.6 degrees, less the corner rule's cut."""
    t = p.sh + (p.sd - p.sh) * 26.565 / 45
    return 1.118 * t


def tri_reach_p(p, W=None):
    """A triangle's reach (half its height): the box filled, or as much as
    keeps its counter half a stem across (the inradius of a 2:1 triangle
    is 0.618 of its reach; its strokes take half their weight from it)."""
    W = OPW(p) if W is None else W
    return max((W - p.sv / 2 - _tip(p)) / 2, (0.25 * p.sv + max(p.sv, p.sd) / 2) / 0.618)


def tri_reach(g):
    return tri_reach_p(g.p)


def tri_w(p):
    return 2 * tri_reach_p(p) + _tip(p) + p.sv / 2


@op(u(0x22B2), '⊲', width=tri_w)
def normalsub(g):
    triangle(g, _tip(g.p), axis(g.p), tri_reach(g))


@op(u(0x22B3), '⊳', width=tri_w)
def contnormalsub(g):
    triangle(g, g.W - _tip(g.p), axis(g.p), tri_reach(g), right=True)


@op(u(0x22B4), '⊴')
def normalsubeq(g):
    def t(g, yc):
        h = tri_reach(g)
        triangle(g, _tip(g.p) + (g.W - tri_w(g.p)) / 2, yc, h)
    stack(g, [Shape(lambda g: 2 * tri_reach(g) + 2 * kd(g.p), t), Bar()])


@op(u(0x22B5), '⊵')
def contnormalsubeq(g):
    def t(g, yc):
        h = tri_reach(g)
        triangle(g, g.W - _tip(g.p) - (g.W - tri_w(g.p)) / 2, yc, h, right=True)
    stack(g, [Shape(lambda g: 2 * tri_reach(g) + 2 * kd(g.p), t), Bar()])


@op(u(0x22C8), '⋈', width=growing_width(10, 2, 2.0))
def bowtie(g):
    """Two triangles meeting point to point."""
    p = g.p
    a = axis(p)
    h = (g.W - p.sv) / 2
    xm = g.W / 2
    g.stroke((xm, a), (p.sv / 2, a + h), (p.sv / 2, a - h), closed=True)
    g.stroke((xm, a), (g.W - p.sv / 2, a + h), (g.W - p.sv / 2, a - h), closed=True)


@op(u(0x22C4), '⋄', width=lambda p: 2 * (1.6 * p.m + p.sv))
def diamondop(g):
    p = g.p
    a = axis(p)
    h = g.W / 2 - kd(p)
    xm = g.W / 2
    g.stroke((xm, a + h), (xm + h, a), (xm, a - h), (xm - h, a), closed=True)


@op(u(0x22C6), '⋆', width=lambda p: 2 * (2.2 * p.m + 0.6 * p.sv), solid=True)
def starop(g):
    """A solid four-pointed star, its edges at 2:1."""
    from shapely.geometry import Polygon
    p = g.p
    a = axis(p)
    R = g.W / 2
    q = R / 3
    xm = g.W / 2
    pts = [(xm, a + R), (xm + q, a + q), (xm + R, a), (xm + q, a - q), (xm, a - R), (xm - q, a - q),
           (xm - R, a), (xm - q, a + q)]
    g.extra.append(Polygon(pts))


@op(u(0x22B8), '⊸', width=lambda p: OPW(p) + 1.5 * p.m)
def multimap(g):
    """A bar running into a small ring."""
    p = g.p
    a = axis(p)
    r = small_ring_r(g) + 0.25 * p.m
    w = max(0.85 * p.sv, 1.12 * p.floor)
    cx = g.W - r - w / 2
    g.stroke((0, a), (cx - r, a))
    _small_ring_box(g, cx, a, r)


# --- Circled and squared operators --------------------------------------------------------

def circle_box(g):
    """(cx, cy, r, leg): the circled operators' octagon, the box's height."""
    p = g.p
    r = g.W / 2 - p.sv / 2
    leg = min(p.leg + p.m, 0.55 * r)
    return g.W / 2, axis(p), r, leg


def _circled(g, inner, square=False):
    """A ring (or a square) round an operator. Its parts are a tight stack
    across the ring: they lighten toward Black as stacked arrows do."""
    from .arrows import stack_k
    from ..draw import _lightened
    k = stack_k(g.p)
    if k != 1.0:
        g.p = _lightened(g.p, k)
    p = g.p
    cx, cy, r, leg = circle_box(g)
    if square:
        g.stroke((cx - r, cy - r), (cx + r, cy - r), (cx + r, cy + r), (cx - r, cy + r), closed=True)
    else:
        _ring(g, cx - r, cy - r, cx + r, cy + r, leg=leg)
    inner(g, cx, cy, r, leg)


def _free(g, r, y=0.0, L=None):
    """How far a bar inside a ring reaches (its centreline), at y from the
    centre, when it keeps clear of the ring's inside (its upright side, or
    its chamfer) by half a stem, or three quarters of a module, of white."""
    p = g.p
    L = 0.586 * r if L is None else L
    k = p.sd / SQRT2
    inner = min(r - p.sv / 2, 2 * r - L - k - (abs(y) + g.sh / 2))
    return inner - max(0.5 * p.sv, 0.75 * p.m) - g.sh / 2


CIRCLED = {
    0x2295: ('circleplus', lambda g, x, y, r, L: (g.stroke((x - r, y), (x + r, y)), g.stroke((x, y - r), (x, y + r)))),
    0x2296: (u(0x2296), lambda g, x, y, r, L: g.stroke((x - r, y), (x + r, y))),
    0x2297: ('circlemultiply', lambda g, x, y, r, L: (g.stroke((x - (r - L / 2), y - (r - L / 2)), (x + r - L / 2, y + r - L / 2)),
                                                    g.stroke((x - (r - L / 2), y + r - L / 2), (x + r - L / 2, y - (r - L / 2))))),
    0x2298: (u(0x2298), lambda g, x, y, r, L: g.stroke((x - (r - L / 2), y - (r - L / 2)), (x + r - L / 2, y + r - L / 2))),
    0x2299: (u(0x2299), lambda g, x, y, r, L: cdot(g, x, y)),
    0x229A: (u(0x229A), lambda g, x, y, r, L: _inner_ring(g, x, y, r)),
    0x229B: (u(0x229B), lambda g, x, y, r, L: _inner_asterisk(g, x, y, _free(g, r, L=L) + g.sh / 2)),
    0x229C: (u(0x229C), lambda g, x, y, r, L: _inner_bars(g, x, y, _free(g, r, (g.sh + eq_gap(g)) / 2, L) + g.sh / 2, 2, r)),
    0x229D: (u(0x229D), lambda g, x, y, r, L: _inner_bars(g, x, y, _free(g, r, 0.0, L) + g.sh / 2, 1)),
}
SQUARED = {
    0x229E: (u(0x229E), CIRCLED[0x2295][1]),
    0x229F: (u(0x229F), CIRCLED[0x2296][1]),
    0x22A0: (u(0x22A0), lambda g, x, y, r, L: (g.stroke((x - r, y - r), (x + r, y + r)), g.stroke((x - r, y + r), (x + r, y - r)))),
    0x22A1: (u(0x22A1), CIRCLED[0x2299][1]),
}


def _inner_ring(g, x, y, r):
    """A ring inside the ring, half a stem of white between them."""
    p = g.p
    w = max(0.6 * p.sv, 1.12 * p.floor)                     # a lighter ring, as a small one is
    ri = r - p.sv / 2 - max(0.45 * p.sv, 0.6 * p.m) - w / 2
    _ring(g, x - ri, y - ri, x + ri, y + ri, w=w, leg=0.45 * ri)


def _inner_bars(g, x, y, half, n, r=None):
    """One bar, or the equal sign's two, inside a ring of centreline half
    size r: two bars that would not fit with half a stem of white above
    and below thin, and close up, as a tight stack does."""
    p = g.p
    t, gap = g.sh, eq_gap(g)
    if n == 2 and r is not None:
        room = r - g.sh / 2 - max(0.5 * p.sv, 0.75 * p.m)     # from the centre to the white's edge
        if t + gap / 2 > room:
            t = max(room / 1.4, 1.12 * p.floor)
            gap = max(0.8 * t, 2 * (room - t))
    off = (t + gap) / 2
    ys = [y] if n == 1 else [y - off, y + off]
    for yy in ys:
        g.stroke((x - half, yy, t), (x + half, yy))


def _inner_asterisk(g, x, y, half):
    """Six spokes, the asterisk's: the vertical and the shallow 2:1 slopes."""
    import math
    from .punct import SPOKE
    c, s = half * math.cos(SPOKE), half * math.sin(SPOKE)
    g.stroke((x, y - half), (x, y + half))
    g.stroke((x - c, y - s), (x + c, y + s))
    g.stroke((x - c, y + s), (x + c, y - s))


for cp, (nm, inner) in CIRCLED.items():
    op(nm, chr(cp), width=RINGW)(lambda g, inner=inner: _circled(g, inner))
for cp, (nm, inner) in SQUARED.items():
    op(nm, chr(cp), width=RINGW)(lambda g, inner=inner: _circled(g, inner, square=True))


# --- Dots -------------------------------------------------------------------------------

@op('dotmath', '⋅', width=lambda p: p.dot())
def dotmath(g):
    cdot(g, g.W / 2, axis(g.p))


@op(u(0x2219), '∙', width=lambda p: 1.5 * p.dot())
def bulletop(g):
    cdot(g, g.W / 2, axis(g.p), 1.5 * g.p.dot())


def dot_step(p):
    """From one dot to the next in a column or row (the ellipsis's)."""
    return 2.2 * p.dot()


@op(u(0x2236), '∶', width=lambda p: p.dot())
def ratio(g):
    p = g.p
    for s in (-1, 1):
        cdot(g, g.W / 2, axis(p) + s * dot_step(p) / 2 * 1.4)


def _dd(g):
    """Half the step between a pair of dots: the ellipsis's, or as much as
    the body holds."""
    return min(0.7 * dot_step(g.p), (g.W - g.p.dot()) / 2)


@op(u(0x2237), '∷', width=lambda p: p.dot() + 1.4 * dot_step(p))
def proportion(g):
    p = g.p
    d = _dd(g)
    for sx in (-1, 1):
        for sy in (-1, 1):
            cdot(g, g.W / 2 + sx * d, axis(p) + sy * 0.7 * dot_step(p))


@op('therefore', '∴', width=lambda p: p.dot() + 1.4 * dot_step(p))
def therefore(g):
    p = g.p
    d = _dd(g)
    cdot(g, g.W / 2, axis(p) + d)
    cdot(g, g.W / 2 - d, axis(p) - d)
    cdot(g, g.W / 2 + d, axis(p) - d)


@op(u(0x2235), '∵', width=lambda p: p.dot() + 1.4 * dot_step(p))
def because(g):
    p = g.p
    d = _dd(g)
    cdot(g, g.W / 2, axis(p) - d)
    cdot(g, g.W / 2 - d, axis(p) + d)
    cdot(g, g.W / 2 + d, axis(p) + d)


@op(u(0x2238), '∸')
def dotminus(g):
    p = g.p
    a = axis(p)
    g.stroke((0, a), (g.W, a))
    cdot(g, g.W / 2, a + g.sh / 2 + dot_space(g) + p.dot() / 2)


@op(u(0x2239), '∹', width=lambda p: OPW(p) + p.dot() + max(0.8 * p.sv, p.m))
def excess(g):
    """A minus and a colon."""
    p = g.p
    a = axis(p)
    s = p.dot()
    g.stroke((0, a), (g.W - s - max(0.8 * p.sv, p.m), a))
    for sy in (-1, 1):
        cdot(g, g.W - s / 2, a + sy * 0.7 * dot_step(p))


@op(u(0x223A), '∺', width=lambda p: OPW(p))
def geomprop(g):
    """A minus with a dot at each corner."""
    p = g.p
    a = axis(p)
    s = p.dot()
    g.stroke((0, a), (g.W, a))
    dy = g.sh / 2 + dot_space(g) + s / 2
    for sx in (-1, 1):
        for sy in (-1, 1):
            cdot(g, g.W / 2 + sx * (g.W / 2 - s / 2), a + sy * dy)


@op(u(0x223B), '∻', width=TILDEW)
def homothetic(g):
    """The tilde with a dot above and below."""
    p = g.p
    a = axis(p)
    s = p.dot()
    Tilde().draw(g, a)
    dy = (tilde_rise(g) + g.sh) / 2 + dot_space(g) + s / 2
    cdot(g, g.W / 2, a + dy)
    cdot(g, g.W / 2, a - dy)


@op(u(0x2214), '∔')
def dotplus(g):
    p = g.p
    a = axis(p)
    s = p.dot()
    h = g.W / 2 - 0.5 * (s + dot_space(g))
    a2 = a - 0.5 * (s + dot_space(g))
    g.stroke((0, a2), (g.W, a2))
    g.stroke((g.W / 2, a2 - h), (g.W / 2, a2 + h))
    cdot(g, g.W / 2, a2 + h + dot_space(g) + s / 2)


@op(u(0x22EE), '⋮', width=lambda p: p.dot())
def vellipsis(g):
    p = g.p
    for i in (-1, 0, 1):
        cdot(g, g.W / 2, axis(p) + i * dot_step(p))


@op(u(0x22EF), '⋯', width=lambda p: p.dot() + 2 * dot_step(p))
def cellipsis(g):
    p = g.p
    step = min(dot_step(p), (g.W - p.dot()) / 2)
    for i in range(3):
        cdot(g, p.dot() / 2 + i * step, axis(p))


@op(u(0x22F0), '⋰', width=lambda p: p.dot() + 2 * dot_step(p) / SQRT2)
def upellipsis(g):
    p = g.p
    d = min(dot_step(p) / SQRT2, (g.W - p.dot()) / 2)
    for i in (-1, 0, 1):
        cdot(g, g.W / 2 + i * d, axis(p) + i * d)


@op(u(0x22F1), '⋱', width=lambda p: p.dot() + 2 * dot_step(p) / SQRT2)
def downellipsis(g):
    p = g.p
    d = min(dot_step(p) / SQRT2, (g.W - p.dot()) / 2)
    for i in (-1, 0, 1):
        cdot(g, g.W / 2 + i * d, axis(p) - i * d)


# --- Arithmetic --------------------------------------------------------------------------

@op(u(0x2213), '∓')
def minusplus(g):
    """The plus-minus sign turned: the bar above, the plus below."""
    REGISTRY['plusminus'].fn(g)
    p = g.p
    c = axis(p) * 2 + 0.0
    ys = [nd.y for s_ in g.strokes for nd in s_.nodes]
    mid = (max(ys) + min(ys)) / 2
    g.strokes = [type(s_)(tuple(type(nd)(nd.x, 2 * mid - nd.y, nd.bowl, nd.w) for nd in s_.nodes),
                          s_.closed, s_.start, s_.end) for s_ in g.strokes]


@op(u(0x2215), '∕', width=lambda p: p.ss / STEEP[1] + 0.5 * OPW(p) * 1.2)
def divslash(g):
    """The fraction slash's 2:1, on the axis, the box's height."""
    p = g.p
    a = axis(p)
    w = p.ss / STEEP[1]
    h = (g.W - w)
    g.stroke((w / 2, a - h), (g.W - w / 2, a + h), start='h', end='h')


@op(u(0x2216), '∖', width=lambda p: p.ss / STEEP[1] + 0.5 * OPW(p) * 1.2)
def setminus(g):
    p = g.p
    a = axis(p)
    w = p.ss / STEEP[1]
    h = (g.W - w)
    g.stroke((w / 2, a + h), (g.W - w / 2, a - h), start='h', end='h')


@op('asteriskmath', '∗', width=lambda p: REGISTRY['asterisk'].width(p))
def asteriskmath(g):
    """The asterisk, centred on the axis."""
    REGISTRY['asterisk'].fn(g)
    p = g.p
    ys = [nd.y for s_ in g.strokes for nd in s_.nodes]
    dy = axis(p) - (max(ys) + min(ys)) / 2
    g.strokes = [type(s_)(tuple(type(nd)(nd.x, nd.y + dy, nd.bowl, nd.w) for nd in s_.nodes),
                          s_.closed, s_.start, s_.end) for s_ in g.strokes]
    if g.clip:
        x0, y0, x1, y1 = g.clip
        g.clip = (x0, y0 + dy, x1, y1 + dy)


@op(u(0x2218), '∘', width=lambda p: 2 * (small_ring_r_p(p) + 0.425 * p.sv))
def ringop(g):
    r = small_ring_r(g)
    _small_ring_box(g, g.W / 2, axis(g.p), r)


def small_ring_r_p(p):
    """A small ring's centreline half-size: its counter at least a stem
    across, or a module and a half."""
    return max(1.5 * p.m, 0.85 * p.sv / 2 + 0.5 * p.sv)


# --- Divides and parallels ------------------------------------------------------------------

def _vbar_half(p):
    return OPW(p) / 2 + 1.0 * p.m


@op(u(0x2223), '∣', width=lambda p: p.sv)
def divides(g):
    a = axis(g.p)
    h = _vbar_half(g.p)
    g.stroke((g.W / 2, a - h), (g.W / 2, a + h))


@op(u(0x2224), '∤', width=lambda p: p.sv + 4 * p.m)
def notdivides(g):
    a = axis(g.p)
    h = _vbar_half(g.p)
    g.stroke((g.W / 2, a - h), (g.W / 2, a + h))
    negate(g, half=max(3.5 * g.p.m, 1.4 * g.p.sv), x=g.W / 2)


def _par_gap(p):
    """Between parallel bars: the pilcrow's, three quarters of a stem, or two modules."""
    return max(0.75 * p.sv, 2 * p.m)


@op(u(0x2225), '∥', width=lambda p: 2 * p.sv + _par_gap(p))
def parallel(g):
    p = g.p
    a = axis(p)
    h = _vbar_half(p)
    for x in (p.sv / 2, g.W - p.sv / 2):
        g.stroke((x, a - h), (x, a + h))


@op(u(0x2226), '∦', width=lambda p: 2 * p.sv + _par_gap(p) + 2 * p.m)
def notparallel(g):
    p = g.p
    a = axis(p)
    h = _vbar_half(p)
    for x in (p.m + p.sv / 2, g.W - p.m - p.sv / 2):
        g.stroke((x, a - h), (x, a + h))
    negate(g, half=max(3 * p.m, 1.2 * p.sv))


# --- Angles ----------------------------------------------------------------------------------

@op('orthogonal', '∟')
def rightangle(g):
    p = g.p
    a = axis(p)
    r = box_r(g)
    g.stroke((p.sv / 2, a + r + g.sh / 2), (p.sv / 2, a - r), (g.W, a - r))


def _angle(g):
    """∠: a bar and a 45-degree stroke rising from its left end."""
    p = g.p
    a = axis(p)
    r = box_r(g)
    yb = a - r
    k = kd(p)
    g.stroke((0, yb), (g.W, yb))
    L = g.W - 2 * k                                          # its end at the body's edge
    g.stroke((k, yb), (k + L, yb + L), start='h', end='h')
    return yb


@op('angle', '∠', width=growing_width(8, 1, 1.5))
def angle(g):
    _angle(g)


@op(u(0x2221), '∡', width=growing_width(8, 1, 1.5))
def measuredangle(g):
    """The angle with an arc across it: up from the bar, then square to the
    diagonal (an octagon's eighth)."""
    p = g.p
    yb = _angle(g)
    rr = 0.62 * g.W
    k = kd(p)
    x = k + rr
    t = rr * 0.414                                           # tan 22.5
    e = max(0.75 * p.m, 0.5 * p.sv)
    g.stroke((x, yb - e), (x, yb + t), (k + rr / SQRT2 - e / SQRT2, yb + rr / SQRT2 + e / SQRT2),
             start='h', end='flat')


@op(u(0x2222), '∢')
def sphericalangle(g):
    """A < with a short upright crossing both arms."""
    p = g.p
    a = axis(p)
    W = g.W
    h = W - kd(p)                                            # across the body, as < is
    g.stroke((W, a + h), (W - h, a), (W, a - h), start='v', end='v')
    x = W - h + 0.45 * h
    e = max(0.75 * p.m, 0.5 * p.sv)
    g.stroke((x, a - 0.45 * h - e), (x, a + 0.45 * h + e))


def _prop_loop(p):
    """∝'s loop, centreline width: its counter at least three quarters of a
    stem, or three modules."""
    return p.sv + max(3.0 * p.m, 0.75 * p.sv)


@op('proportional', '∝', width=lambda p: p.sv / 2 + _prop_loop(p) + max(4.5 * p.m, 2.5 * p.sv))
def proportional(g):
    """The infinity sign with its right loop open."""
    p, W = g.p, g.W
    a = axis(p)
    s = p.sv
    h = max(2.2 * p.m + 0.5 * s, g.sh / 2 + 0.75 * s / 2 + s / 2)
    xm = s / 2 + _prop_loop(p)
    leg = min(1.2 * p.m + 0.3 * s, 0.45 * h)
    _ring(g, s / 2, a - h, xm, a + h, leg=leg)
    g.stroke((W, a + h), B(xm, a + h, leg), B(xm, a - h, leg), (W, a - h))


# --- Letterlike operators ----------------------------------------------------------------------

def _flip_strokes(g, fx=None, fy=None):
    """Mirror the drawing so far: x -> fx - x, y -> fy - y."""
    def m(nd):
        return type(nd)(fx - nd.x if fx is not None else nd.x, fy - nd.y if fy is not None else nd.y, nd.bowl, nd.w)
    g.strokes = [type(s_)(tuple(m(nd) for nd in s_.nodes), s_.closed, s_.start, s_.end) for s_ in g.strokes]


@glyph('universal', '∀', REGISTRY['A'].width, kind='cap')
def universal(g):
    REGISTRY['A'].fn(g)
    _flip_strokes(g, fy=g.p.cap)


@glyph('existential', '∃', REGISTRY['E'].width, kind='cap')
def existential(g):
    REGISTRY['E'].fn(g)
    _flip_strokes(g, fx=g.W)


@glyph(u(0x2204), '∄', lambda p: p.fig_w if p.mono else REGISTRY['E'].width(p), kind=('punct', 1.0))
def notexists(g):
    """∃ struck through, the stroke crossing its bars well to the left of
    its stem, so the pockets it closes off against the stem stay open; its
    three bars a tight stack, lighter toward Black."""
    _light(g)
    REGISTRY['E'].fn(g)
    _flip_strokes(g, fx=g.W)
    p = g.p
    g.clip = None
    x0 = 0.3 * g.W
    half = p.cap / 2 + 1.0 * p.m
    if p.mono:                                               # the cell: the stroke ends at the body
        half = min(half, 2 * (x0 - p.ss / STEEP[1] / 2))
    negate(g, half=half, x=x0)


@glyph(u(0x2201), '∁', letter_width(8, 1), kind='cap')
def complement(g):
    """The C without its beaks: a bowl open to the right."""
    p = g.p
    W = g.W
    from .caps import big
    yt, yb = p.cap - g.sh / 2, g.sh / 2
    g.stroke((W, yt), B(p.sv / 2, yt, big(p)), B(p.sv / 2, yb, big(p)), (W, yb))


@glyph('gradient', '∇', REGISTRY['uni0394'].width, kind='cap')
def gradient(g):
    REGISTRY['uni0394'].fn(g)
    _flip_strokes(g, fy=g.p.cap)


@glyph('partialdiff', '∂', letter_width(8, 2), kind='cap')
def partialdiff(g):
    """A bowl whose right side runs on up and turns back over it, ending in
    the 2's beak."""
    p = g.p
    W = g.W
    xl, xr = p.sv / 2, W - p.sv / 2
    yb, yt = g.sh / 2, p.cap - g.sh / 2
    ybt = 0.58 * p.cap - g.sh / 2
    # the beak: the 2's, never nearer the bowl than a stem's white
    d = min(beak_depth(p), yt - (ybt + g.sh + max(p.sv, 1.25 * p.m)))
    g.stroke(B(xl, yb), B(xr, yb), B(xr, ybt), B(xl, ybt), closed=True)
    # the right side runs on up from the bowl's straight side, so the two are one at every weight
    g.stroke((xr, (yb + ybt) / 2), B(xr, yt), B(xl, yt), (xl, yt + g.sh / 2 - d))


@glyph('emptyset', '∅', lambda p: 0.85 * p.cap + 0.5 * p.sv, kind='cap')
def emptyset(g):
    """A regular octagon (a circle, where the O is a tall bowl) and a
    45-degree stroke through it, reaching a module past its corners."""
    p = g.p
    W = g.W
    r = (W - p.sv) / 2
    cy = p.cap / 2
    ry = (p.cap - g.sh) / 2
    leg = 0.29 * 2 * min(r, ry)
    cx = W / 2
    _ring(g, cx - r, cy - ry, cx + r, cy + ry, leg=leg)
    t = min(r, ry) - leg / 2 + p.sv / 2 + 1.0 * p.m
    if p.mono:                                               # the cell: the stroke ends inside it
        t = min(t, W / 2 - p.sd)
    g.stroke((cx - t, cy - t), (cx + t, cy + t), start='h', end='h')
    g.clip = None


@glyph(u(0x220E), '∎', lambda p: 0.55 * p.cap, kind=('punct', 1.0), solid=True)
def endofproof(g):
    """A solid block, as tall as a capital is wide."""
    p = g.p
    h = 0.75 * p.cap
    g.stroke((g.W / 2, 0, g.W), (g.W / 2, h))


# --- Big operators ------------------------------------------------------------------------------

BIGW = letter_width(10, 2)


@op('summation', '∑', width=letter_width(10, 1))
def summation(g):
    """Two bars joined by a chevron at the 7's 2:1, pointing into the
    counter."""
    p, W = g.p, g.W
    bot, top = span(p)
    yt, yb = top - g.sh / 2, bot + g.sh / 2
    w = p.ss / STEEP[1]
    xl = w / 2
    mid = (yt + yb) / 2
    g.stroke((W, yt), (xl, yt), (xl + (yt - mid) / 2, mid), (xl, yb), (W, yb))
    g.clip = (0, bot, W, top)


@op('product', '∏', width=BIGW)
def product(g):
    p, W = g.p, g.W
    bot, top = span(p)
    yt = top - g.sh / 2
    g.stroke((0, yt), (W, yt))
    for x in (p.m + p.sv / 2, W - p.m - p.sv / 2):
        g.stroke((x, bot), (x, yt))


@op(u(0x2210), '∐', width=BIGW)
def coproduct(g):
    p, W = g.p, g.W
    bot, top = span(p)
    yb = bot + g.sh / 2
    g.stroke((0, yb), (W, yb))
    for x in (p.m + p.sv / 2, W - p.m - p.sv / 2):
        g.stroke((x, yb), (x, top))


@op(u(0x22C0), '⋀', width=BIGW)
def naryand(g):
    bot, top = span(g.p)
    w = g.p.ss / STEEP[1]
    hgt = top - bot
    x0 = g.W / 2 - hgt / 4 - w / 2
    g.W = g.W
    g.stroke((g.W / 2 - hgt / 4, bot), (g.W / 2, top), (g.W / 2 + hgt / 4, bot), start='h', end='h')
    g.clip = (0, bot, g.W, top)


@op(u(0x22C1), '⋁', width=BIGW)
def naryor(g):
    bot, top = span(g.p)
    hgt = top - bot
    g.stroke((g.W / 2 - hgt / 4, top), (g.W / 2, bot), (g.W / 2 + hgt / 4, top), start='h', end='h')
    g.clip = (0, bot, g.W, top)


@op(u(0x22C2), '⋂', width=BIGW)
def naryintersection(g):
    bot, top = span(g.p)
    r = (top - bot - g.sh) / 2
    cup(g, (top + bot) / 2, r, down=True)


@op(u(0x22C3), '⋃', width=BIGW)
def naryunion(g):
    bot, top = span(g.p)
    r = (top - bot - g.sh) / 2
    cup(g, (top + bot) / 2, r)


def integral(g, x, bot, top):
    """∫ on a stem at x: the f's turn at the top, the j's at the foot, each
    ending in a beak, a half turn of each other."""
    p = g.p
    reach = 2.5 * p.m + p.sv / 2
    d = beak_depth(p)
    yt, yb = top - g.sh / 2, bot + g.sh / 2
    g.stroke((x + reach, top - d), B(x + reach, yt), B(x, yt), B(x, yb), B(x - reach, yb), (x - reach, bot + d))


def int_w(n=1):
    return lambda p: 2 * (2.5 * p.m + p.sv / 2) + p.sv + (n - 1) * int_step(p)


def int_step(p):
    """From one integral to the next: its hook's reach and a stem's white."""
    return 2.5 * p.m + p.sv + max(0.75 * p.sv, p.m)


def int_span(p):
    return -p.desc, p.asc


@op('integral', '∫', width=int_w())
def integral1(g):
    p = g.p
    integral(g, g.W / 2, *int_span(p))


@op(u(0x222C), '∬', width=int_w(2))
def integral2(g):
    p = g.p
    x0 = 2.5 * p.m + p.sv
    for i in range(2):
        integral(g, x0 + i * int_step(p), *int_span(p))


@op(u(0x222D), '∭', width=int_w(3))
def integral3(g):
    p = g.p
    x0 = 2.5 * p.m + p.sv
    for i in range(3):
        integral(g, x0 + i * int_step(p), *int_span(p))


def _cint_r(p):
    """∮'s ring: round the stem with white inside it, half a stem at least."""
    return max(small_ring_r_p(p) + 1.0 * p.m, 1.4 * p.sv)


@op(u(0x222E), '∮', width=lambda p: max(int_w()(p), 2 * _cint_r(p) + p.sv))
def contourintegral(g):
    p = g.p
    bot, top = int_span(p)
    integral(g, g.W / 2, bot, top)
    r = _cint_r(p)
    # an octagon wider than tall where the hooks' beaks would come near it
    w = max(0.85 * p.sv, 1.12 * p.floor)
    white = max(0.75 * p.sv, p.m)
    ry = min(r, (top - bot) / 2 - beak_depth(p) - white - w / 2)
    c, mid = g.W / 2, (bot + top) / 2
    _ring(g, c - r, mid - ry, c + r, mid + ry, w=w, leg=0.6 * min(r, ry))


# --- Roots ---------------------------------------------------------------------------------------

ROOT_K = 0.42                                  # the index's size, of the figures'


def _root_params(p):
    s = 0.5 - 0.08 * heaviness(p)                            # strokes in proportion to the index's size
    k = ROOT_K
    return p.with_(m=k * p.m, cap=k * p.cap, fig_w=k * p.fig_w, fig_adv=k * p.fig_adv, leg=k * p.leg,
                   sv=s * p.sv, sh=s * p.sh, sd=s * p.sd, ss=s * p.ss, c=s * p.c)


def _root_layout(p):
    """(index width, index foot, the radical's shift, its bar's length):
    the index stands above the radical's tick, a stem's white clear of it
    and of the 2:1 rise; the radical moves right only as far as that needs.
    In the monospaced cell the bar shortens to a module."""
    t = _tick(p)
    top = p.cap + 0.5 * p.m
    gap = max(0.5 * p.sv, 0.75 * p.m)
    wi = _root_params(p).fig_w
    w = p.ss / STEEP[1]
    yb = t + 0.5 * p.sv + gap
    dx = max(0.0, wi + gap - t - yb / 2 + w / 2)
    bar = 1.0 * p.m if p.mono else 3.5 * p.m
    return wi, yb, dx, bar


def _tick(p):
    """The radical's tick: √'s two modules, or longer than its stroke is
    wide across (the heaviest grade)."""
    return max(2.0 * p.m, 1.3 * p.sd / SQRT2)


def _root_w(p):
    wi, yb, dx, bar = _root_layout(p)
    return dx + _tick(p) + (p.cap + 0.5 * p.m) / 2 + bar


def _root(g, n):
    """The radical (its tick, its 2:1 rise and its bar, as √ draws them)
    with a small index in its crook."""
    p = g.p
    wi, yb, dx, bar = _root_layout(p)
    top = p.cap + 0.5 * p.m
    t = _tick(p)
    g.stroke((dx, t), (dx + t, 0), start='v', end='h')
    g.stroke((dx + t, 0), (dx + t + top / 2, top), start='h', end='h')
    g.stroke((dx + t + top / 2 - p.sv / 2, top - g.sh / 2), (g.W, top - g.sh / 2))
    g.clip = (0, 0, g.W, top)
    sub = draw(n, _root_params(p))
    g.add_glyph(sub, 0, yb)


@op(u(0x221B), '∛', width=_root_w, sides=0.6)
def cuberoot(g):
    _root(g, 'three')


@op(u(0x221C), '∜', width=_root_w, sides=0.6)
def fourthroot(g):
    _root(g, 'four')
