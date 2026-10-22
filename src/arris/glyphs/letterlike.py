"""Letterlike Symbols (U+2100-U+214F), the useful ones.

* **Double-struck** letters (ℂ ℕ ℙ ℚ ℝ ℤ ⅅ ⅆ ⅇ ⅈ ⅉ ⅀) are Arris letters
  with an inner parallel stroke: a lighter stroke beside the main stem (or
  the Z's and Σ's diagonals), inside the letter, a slit of white between
  them that never drops below 0.6 of a stem. The letter widens by the
  stroke and its slit, so its counter keeps its size (``ds_*``).
* **Script** letters (ℊ ℓ ℘ ℛ ℰ ℱ ℳ ℯ ℴ) and the Planck constant are written
  in Arris's own hand, the italic's moves drawn upright: the 1's flag as an
  entry into a capital's first stem, the t's foot as an exit, the j's hook,
  the italic's cursive e and h (``italic_forms``), a loop on the l. Arris
  draws no curves upright, so its script is a cursive, not a copperplate.
* **Turned and reversed** letters (⅁ ⅂ ⅃ ⅄ ⅋ ⅎ Ⅎ ℧ ℇ) are the letters
  turned or mirrored whole (``symkit.stamp_t``).
* **Abbreviations** (℀ ℁ ℅ ℆ ⅍, ℃ ℉, ℠ ℡ ℻, ℗) are letters set small,
  as the ordinals and fractions set them, or small capitals set tight.
"""
from __future__ import annotations

from ..draw import B, REGISTRY, draw, glyph
from ..params import SQRT2
from .figures import beak_depth, jog
from .letterframe import STEEP, Frame, heft, letter_width
from .symkit import MIRROR, TURN, across, set_tight, sign, small_all, stamp_t, tight

ALIASES = {0x212A: 'K', 0x212B: 'Aring'}


def stamp(g, name, dx=0.0, dy=0.0, width=None, p=None):
    sub = draw(name, p or g.p, width=width)
    g.add_glyph(sub, dx, dy)
    return sub


class _Body:
    """A stand-in glyph for reading a frame's coordinates at another width."""

    def __init__(self, p, W):
        self.p, self.W, self.sh, self.clip = p, W, p.sh, None


def ink_x(sub):
    xs = [x for r in sub.rings() for x, _ in r]
    return (min(xs), max(xs)) if xs else (0.0, sub.W)


# --- Double-struck -----------------------------------------------------------

def ds_t(p):
    """The inner stroke: lighter than a stem."""
    return max(0.55 * p.sv, p.floor)


def ds_s(p):
    """The slit of white between a stem and its inner stroke."""
    return max(0.75 * p.m, 0.6 * p.sv)


def ds_extra(p):
    return ds_t(p) + ds_s(p)


def ds_x(p, x_stem, side=1):
    """Where the inner stroke stands beside a stem at x_stem (side +1:
    to its right)."""
    return x_stem + side * (p.sv / 2 + ds_s(p) + ds_t(p) / 2)


def _inner(g, x, y0, y1):
    g.stroke((x, y0, ds_t(g.p)), (x, y1))


def _ds_width(name, wider=True):
    return lambda p: REGISTRY[name].width(p) + (ds_extra(p) if wider else 0.0)


def _double(name, ch, base, y_range, side=1, wider=True, kind='cap', dot=False):
    """A double-struck letter: ``base`` drawn wider by the inner stroke and
    its slit, the inner stroke beside its stem from y_range(p, sh)[0] to [1].
    The stem is the left one (x = sv/2) unless side is -1 (the right one)."""
    def fn(g):
        p = g.p
        sub = stamp(g, base, width=g.W)
        xs = p.sv / 2 if side > 0 else g.W - p.sv / 2
        y0, y1 = y_range(p, sub.sh)
        _inner(g, ds_x(p, xs, side), y0, y1)
        if dot:
            from .lower import _dot
            f = Frame(g, 2, 'asc', top=p.asc + p.sv)
            _dot(g, f, (xs + ds_x(p, xs, side)) / 2)
    sign(name, ch, _ds_width(base, wider), kind=kind)(fn)


_double('uni2102', 'ℂ', 'C', lambda p, sh: (sh / 2, p.cap - sh / 2))
_double('uni2119', 'ℙ', 'P', lambda p, sh: (0.0, p.cap - sh / 2))
_double('uni211D', 'ℝ', 'R', lambda p, sh: (0.0, p.cap - sh / 2))
_double('uni211A', 'ℚ', 'Q', lambda p, sh: (sh / 2, p.cap - sh / 2))
_double('uni2145', 'ⅅ', 'D', lambda p, sh: (sh / 2, p.cap - sh / 2))
_double('uni2146', 'ⅆ', 'd', lambda p, sh: (sh / 2, p.asc), side=-1, kind='lower')


@sign('uni2147', '\u2147', lambda p: REGISTRY['e'].width(p) + ds_extra(p), kind='lower')
def dse(g):
    """The upright e (lower.e: three bars in a tight stack, the bar on row
    4), its left side doubled by an inner stroke from the bottom bar to the
    top. Drawn here rather than stamped, so the italic slants this e and not
    its cursive one, and the closed-counter rule keeps the slits open."""
    g.stack(3, g.p.xh, ratio=0.75)
    f = Frame(g, 8, 'lower')
    p = g.p
    yb = f.Y(4)
    g.stroke((f.X(1), yb), (f.X(7), yb), B(*f.P(7, 8)), B(*f.P(1, 8)), closed=True)
    g.stroke((f.X(1), yb), B(*f.P(1, 1)), f.P(7, 1))
    _inner(g, ds_x(p, f.X(1)), f.Y(1), f.Y(8))


@sign('uni2148', 'ⅈ', lambda p: p.sv + ds_extra(p), kind='lower')
def dsi(g):
    """The i's stem and an inner stroke beside it, the dot over both."""
    from .lower import _dot
    p = g.p
    f = Frame(g, 2, 'asc', top=p.asc + p.sv)
    xs = p.sv / 2
    g.stroke((xs, 0), (xs, p.xh))
    xi = ds_x(p, xs)
    _inner(g, xi, 0, p.xh)
    _dot(g, f, (xs + xi) / 2)
    g.clip = None


@sign('uni2149', '\u2149', lambda p: REGISTRY['uni0237'].width(p) + ds_extra(p), kind='lower')
def dsj(g):
    """The j doubled: its stem, and a lighter stroke on its right that turns
    into the j's hook under both; the dot over the two."""
    from .lower import _dot
    p = g.p
    wj = g.W - ds_extra(p)
    f = Frame(g, 6, 'asc', top=p.asc + p.sv)
    fj = Frame(_Body(p, wj), 6, 'lower')
    xs = wj - p.sv / 2
    xi = ds_x(p, xs)
    yb = fj.Y(-2)
    x1 = fj.X(1)
    g.stroke((xi, p.xh, ds_t(p)), B(xi, yb), B(x1, yb), (x1, -p.desc + beak_depth(p)))
    g.stroke((xs, p.xh), (xs, yb))
    _dot(g, f, (xs + xi) / 2)
    g.clip = None


@sign('uni2115', 'ℕ', _ds_width('N', False), kind='cap')
def dsN(g):
    """N with an inner stroke beside its left stem, up to the diagonal."""
    p = g.p
    sub = stamp(g, 'N', width=g.W)
    w = p.ss / STEEP[1]
    x0 = p.sv + w / 2                                       # the diagonal's centre at the top bar (caps.N)
    xi = ds_x(p, p.sv / 2)
    y = (p.cap - sub.sh / 2) - 2 * (xi - x0)                # the diagonal's centre over the inner stroke
    _inner(g, xi, 0, y)


def _z_diag(g, f, W, a_up, x_end, t=None):
    """The Z's spine (caps.Z): from the top bar down at 45 degrees, a jog
    left on a short bar, down again to a vertical at x_end. ``t``: a lighter
    stroke than the weight's (the inner spine of the double-struck Z)."""
    p = g.p
    J = jog(p)
    a_lo = a_up - J
    yj = f.Y(6.5)
    step = min(J, g.sh)
    y0, y1 = f.Y(11), f.Y(1)
    d = across(p, t, (1, 1)) if t else None
    v = t if t else None
    g.stroke((y0 + a_up, y0, d), (yj + a_up, yj, step), (yj + a_lo, yj, d), (x_end, x_end - a_lo, v), (x_end, y1),
             start='h')


def _ds_shift(p):
    """How far apart (across) two parallel 45-degree strokes stand to keep
    the slit between them, where they run and where they step by the 2's
    jog together (a jog's bar must not reach across the slit)."""
    return max(SQRT2 * (p.sd / 2 + ds_t(p) / 2 + ds_s(p)), jog(p) + p.sv / 2 + ds_t(p) / 2 + ds_s(p))


@sign('uni2124', 'ℤ', lambda p: REGISTRY['Z'].width(p) + _ds_shift(p), kind='cap')
def dsZ(g):
    """Z with its spine doubled by a lighter one beside it."""
    f = Frame(g, 9)
    p, W, H, k = f.p, f.W, f.p.cap, f.k
    D = _ds_shift(p)
    g.stroke(f.P(0, 11), f.P(9, 11))
    g.stroke(f.P(0, 1), f.P(9, 1))
    a_up = W - (H - g.sh - p.c) - k
    xl = f.X(1)
    _z_diag(g, f, W, a_up, xl + D)
    _z_diag(g, f, W, a_up - D, xl, ds_t(p))


@sign('uni2140', '⅀', lambda p: REGISTRY['uni03A3'].width(p) + _ds_shift(p), kind=('punct', 1.0))
def dsSigma(g):
    """Σ with its chevron doubled by a lighter one inside it."""
    f = Frame(g, 9)
    p, W = f.p, f.W
    D = _ds_shift(p)
    yt, yb = f.Y(11), f.Y(1)
    half = (yt - yb) / 2
    xl = f.X(1)
    reach = min(half, 0.45 * (W - D))
    g.stroke((W, yt), (xl, yt), (xl + reach, (yt + yb) / 2), (xl, yb), (W, yb))
    t = ds_t(p)
    g.stroke((xl + D, yt, across(p, t, (1, -1))), (xl + D + reach, (yt + yb) / 2, across(p, t, (-1, -1))),
             (xl + D, yb))


# --- Script: the italic's hand, upright -------------------------------------------

def _flag(p):
    from .italic_forms import FLAG, _reach
    return _reach(p, FLAG)


def _tail_reach(p):
    from .italic_forms import TAIL, _reach
    return _reach(p, TAIL)


def _entry(g, xs, top):
    """The 1's flag leading into the top of a stem at xs (italic_forms.entry)."""
    from .italic_forms import entry
    entry(g, None, xs, top)


def _lead(p):
    """How far a script capital's swash reaches left of its first stem: a
    stem and the white between it and the swash's beak."""
    return p.sv + max(1.5 * p.m, 0.75 * p.sv)


def _script(name, ch, base, exit_=None, foot=None):
    """A capital in Arris's cursive: its top drawn out to the left into a
    swash that ends on the 2's beak; ``exit_``: (x, y) of a foot that
    leaves on the t's foot; ``foot``: the first stem turns back left at its
    foot."""
    def tail_w(p):
        return _tail_reach(p) + p.sv / 2 if exit_ else 0.0

    def width(p):
        return REGISTRY[base].width(p) + _lead(p) + tail_w(p)

    def fn(g):
        p = g.p
        dx = _lead(p)
        wb = g.W - dx - tail_w(p)
        sub = stamp(g, base, dx, width=wb)
        xs = dx + p.sv / 2
        y = p.cap - sub.sh / 2
        g.stroke((p.sv / 2, p.cap - beak_depth(p, sub.sh)), B(p.sv / 2, y), (xs, y))
        if exit_:
            x, y0 = exit_(p, wb)
            x += dx
            g.stroke((x - p.sv / 2, y0), (x + p.sv / 2 + _tail_reach(p), y0))
        if foot:
            g.stroke((xs + p.sv / 2, sub.sh / 2), (xs - dx + p.sv, sub.sh / 2))
    sign(name, ch, width, kind='cap')(fn)


_script('uni211B', 'ℛ', 'R', exit_=lambda p, w: (w - 0.5 * p.sd, p.sh / 2))
_script('uni2130', 'ℰ', 'E')
_script('uni2131', 'ℱ', 'F')
_script('uni2133', 'ℳ', 'M', exit_=lambda p, w: (w - p.sv / 2, p.sh / 2))


@sign('uni210E', 'ℎ', lambda p: REGISTRY['h.ital'].width(p), kind='lower')
def planck(g):
    """The italic h (its flag and exit), as the italic writes it."""
    stamp(g, 'h.ital', width=g.W)


@sign('uni212F', 'ℯ', lambda p: REGISTRY['e.ital'].width(p), kind='lower')
def scripte(g):
    """The italic's cursive e: its bar a diagonal into the top corner."""
    stamp(g, 'e.ital', width=g.W)


@sign('uni2134', '\u2134', lambda p: REGISTRY['o'].width(p) + _flag(p), kind='lower')
def scripto(g):
    """An o entered from the left on the 1's flag, as the italic enters its
    stems."""
    p = g.p
    dx = _flag(p)
    f = Frame(g, 8, 'lower')
    X = lambda x: dx + (f.X(x) - dx) * 1.0
    wo = g.W - dx
    fo = Frame(_Body(p, wo), 8, 'lower')
    P = lambda x, y: (dx + fo.X(x), fo.Y(y))
    g.stroke(B(*P(1, 1)), B(*P(7, 1)), B(*P(7, 8)), P(1, 8), closed=True)
    g.clip = None
    _entry(g, dx + p.sv / 2, p.xh)


@sign('uni210A', 'ℊ', letter_width(8, 2), kind='lower')
def scriptg(g):
    """The g whose descender turns up into the j's beak."""
    f = Frame(g, 8, 'lower')
    p = f.p
    g.stroke(f.P(7, 8), B(*f.P(1, 8)), B(*f.P(1, 1)), f.P(7, 1), closed=True)
    top = min(-p.desc + beak_depth(p), -max(p.m, 0.6 * p.sv))     # white under the bowl
    g.stroke(f.P(7, 9), B(*f.P(7, -2)), B(*f.P(1, -2)), (f.X(1), max(top, f.Y(-2) + 0.01)))


def loop_w(p):
    """The script l's loop: across, its centreline."""
    return max(3 * p.m, 1.25 * p.sv + 1.5 * p.m)


def loop_l(g, xs, y_top, side=1):
    """A closed loop on a stem at xs, its top a bar on y_top: a 45-degree
    stroke leaves the stem, rises to the loop's far side, which runs up and
    turns back over the top to the stem (``side`` -1: the loop on the
    stem's left)."""
    p = g.p
    lw = loop_w(p)
    straight = max(1.5 * p.m, 0.75 * p.sv)
    yj = y_top - lw - straight
    xr = xs + side * lw
    g.stroke((xs, yj), (xr, yj + lw), B(xr, y_top), B(xs, y_top), closed=True)
    return yj


@sign('uni2113', 'ℓ', lambda p: p.sv + loop_w(p) + 0.5 * p.m, kind='lower')
def scriptl(g):
    """A stem with a loop at its top and the t's foot."""
    p = g.p
    xs = p.sv / 2
    y_top = p.asc - g.sh / 2
    loop_l(g, xs, y_top)
    g.stroke((xs, y_top), B(xs, g.sh / 2), (g.W, g.sh / 2))


@sign('weierstrass', '℘', letter_width(9, 2), kind='lower')
def weierstrass(g):
    """A p whose stem enters on the 1's flag and whose descender turns back
    up on the j's hook."""
    f = Frame(g, 9, 'lower')
    p = f.p
    xs = f.X(3)
    g.clip = (-g.W, -p.desc, 2 * g.W, p.xh)
    g.stroke((xs, p.xh), B(xs, f.Y(-2)), B(f.X(1), f.Y(-2)), (f.X(1), f.Y(-2) + g.sh / 2 + beak_depth(p)))
    g.stroke((xs, f.Y(8)), B(*f.P(8, 8)), B(*f.P(8, 1)), (xs, f.Y(1)), closed=True)
    _entry(g, xs, p.xh)


# --- Turned and reversed ------------------------------------------------------------

def _turned(name, ch, base, M=TURN, zone='cap', kind=None, solid=False):
    def fn(g):
        p = g.p
        about = p.cap / 2 if zone == 'cap' else p.xh / 2
        stamp_t(g, base, M, width=g.W, about=about)
    sign(name, ch, lambda p: REGISTRY[base].width(p), kind=kind or REGISTRY[base].kind, solid=solid)(fn)


_turned('uni2141', '⅁', 'G')
_turned('uni2142', '⅂', 'L')
_turned('uni2143', '⅃', 'L', MIRROR)
_turned('uni2144', '⅄', 'Y')
_turned('uni214B', '⅋', 'ampersand')
_turned('uni2132', 'Ⅎ', 'F')
_turned('uni214E', 'ⅎ', 'f', zone='lower')
_turned('uni2127', '℧', 'uni03A9')
_turned('uni2107', 'ℇ', 'uni0417', MIRROR)


# --- Letters with marks ---------------------------------------------------------------

@sign('uni210F', 'ℏ', lambda p: REGISTRY['h'].width(p) + 1.5 * p.m, kind='lower')
def hslash(g):
    """h with a 45-degree stroke across its ascender (ħ's bar is level)."""
    p = g.p
    dx = 1.5 * p.m
    stamp(g, 'h', dx, width=g.W - dx)
    x, y = dx + p.sv / 2, (p.xh + p.asc) / 2 + p.m / 2
    e = 1.5 * p.m + p.sv / 2
    g.stroke((x - e, y - e), (x + e, y + e), start='v', end='v')


def _rx(p):
    """℞: (R's width, where its leg is crossed (x, y), the crossing
    stroke's reach): the leg runs on below the baseline and is crossed just
    under it, clear of the bowl above."""
    wr = REGISTRY['R'].width(p)
    k = p.sd / SQRT2
    a = wr + p.c - k                                        # the R's leg: x + y = a (caps.R)
    yc = -p.desc / 3
    e = 1.5 * p.m + p.sv / 2
    return wr, a, yc, e


def _rx_width(p):
    wr, a, yc, e = _rx(p)
    return max(a + 0.9 * p.desc, a - yc + e) + p.sd


@sign('prescription', '\u211e', _rx_width, kind='cap')
def prescription(g):
    """R whose leg runs on below the baseline, crossed there by a short
    stroke square to it."""
    p = g.p
    wr, a, yc, e = _rx(p)
    stamp(g, 'R', width=wr)
    bot = -0.9 * p.desc
    g.stroke((a - p.sv / 2, p.sv / 2), (a - bot, bot), start='flat', end='h')   # (overlapping the leg)
    xc = a - yc
    g.stroke((xc - e, yc - e), (xc + e, yc + e), start='v', end='v')
    g.clip = (0, bot, g.W, p.cap)


@sign('uni2128', 'ℨ', letter_width(9, 2), kind='cap')
def frakturZ(g):
    """The black-letter Z as Arris writes it, an ezh: a top bar, a
    45-degree stroke down to the middle, and the 3's lower bowl falling
    through the baseline to a beak."""
    f = Frame(g, 9)
    p, W = f.p, f.W
    g.clip = (0, -p.desc, W, p.cap)
    k = p.sd / SQRT2
    yt = f.Y(11)
    xr, xl = f.X(8), f.X(1)
    a = W - (p.cap - g.sh - p.c) - k                        # spine: x - y = a, an edge break below the bar's end
    xm = f.X(3.5)
    ym = xm - a
    yb = -p.desc + g.sh / 2
    g.stroke((0, yt), (W, yt))
    g.stroke((yt + a, yt), (xm, ym), start='h', end='flat')
    beak = min(yb + g.sh / 2 + beak_depth(p), ym - g.sh / 2 - max(p.m, 0.6 * p.sv))
    g.stroke((xm - p.sv / 4, ym), B(xr, ym), B(xr, yb), B(xl, yb), (xl, max(beak, yb + 0.01)))


@sign('estimated', '℮', letter_width(10, 2), kind='lower')
def estimated(g):
    """The e-mark: an e taller than the x-height, its bar across, its lower
    arm turning up into a beak."""
    p = g.p
    W = g.W
    H = 0.8 * p.cap
    g.stack(3, H, ratio=0.75)
    sh = g.sh
    xl, xr = p.sv / 2, W - p.sv / 2
    yt, yb = H - sh / 2, sh / 2
    ym = H / 2
    # the beak rises no closer to the bar than a stroke's white
    d = max(min(beak_depth(p, sh), ym - sh / 2 - max(p.m, 0.6 * p.sv)), yb + sh / 2 + 0.01)
    g.stroke((xl, ym), (xr, ym), B(xr, yt), B(xl, yt), closed=True)
    g.stroke((xl, ym), B(xl, yb), B(xr, yb), (xr, d))


@sign('aleph', '\u2135', letter_width(10, 2), kind='cap')
def aleph(g):
    """The X's falling stroke whole, and its rising stroke broken where they
    cross: the upper half meets the falling stroke a jog above the centre,
    the lower half a jog below it."""
    f = Frame(g, 10)
    p, H, W = f.p, f.p.cap, f.W
    xl, xr = f.X(1), f.X(9)
    c0 = (W + H) / 2                                        # the falling stroke: x + y = c0
    g.stroke((xl, H), (xl, c0 - xl), (xr, c0 - xr), (xr, 0))
    J = jog(p)
    xa, ya = W / 2 - J, H / 2 + J                           # the upper arm leaves here, up and right
    g.stroke((xa, ya), (xr, xr - (xa - ya)), (xr, H))
    xb, yb = W / 2 + J, H / 2 - J                           # the lower arm, down and left
    g.stroke((xb, yb), (xl, xl - (xb - yb)), (xl, 0))


@sign('uni2139', 'ℹ', letter_width(8, 1), kind='lower')
def information(g):
    """The monospaced i, its flag and foot, in a proportional body."""
    stamp(g, 'i', width=g.W, p=g.p.with_(mono=True))


# --- Abbreviations ----------------------------------------------------------------

def _over_gap(p):
    """White beside the slash in a letter fraction: the fractions' 0.3
    module, or more where heavy letters would reach it."""
    return max(0.3 * p.m, 0.4 * p.sv - 0.5 * p.m)


def _over(name, ch, num, den, caps=False):
    """Letters as a fraction: the first raised to the cap height, the
    fraction slash, the second on the baseline (as ½ sets its figures)."""
    def pf(p):
        from .features import small
        if not caps:
            return small_all(p)
        from .symkit import small_letter
        from .features import SMALL
        return small_letter(p, SMALL, 0.8 * 0.85)

    def parts(p):
        ps = pf(p)
        return ps, REGISTRY[num].width(ps), REGISTRY['fraction'].width(p), REGISTRY[den].width(ps)

    def width(p):
        ps, a, s, b = parts(p)
        return a + s + b + 2 * _over_gap(p)

    def fn(g):
        p = g.p
        ps, a, s, b = parts(p.with_(mono=False))
        top = ps.cap if caps else ps.xh
        g.add_glyph(draw(num, ps), 0, p.cap - top)
        x = a + _over_gap(p)
        g.add_glyph(draw('fraction', p), x, 0.2 * p.cap)
        g.add_glyph(draw(den, ps), x + s + _over_gap(p), 0)
    sign(name, ch, width, kind=('punct', 0.6))(fn)


_over('uni2100', '℀', 'a', 'c')
_over('uni2101', '℁', 'a', 's')
_over('careof', '℅', 'c', 'o')
_over('uni2106', '℆', 'c', 'u')
_over('uni214D', '⅍', 'A', 'S', caps=True)


def _degree_letter(name, ch, letter):
    gap = lambda p: max(0.5 * p.m, 0.4 * p.sv)

    def fn(g):
        p = g.p
        sub = draw('degree', p)
        g.add_glyph(sub)
        wl = REGISTRY[letter].width(p) if not p.mono else g.W - sub.W - gap(p)
        stamp(g, letter, sub.W + gap(p), width=wl)
    sign(name, ch, lambda p: REGISTRY['degree'].width(p) + gap(p) + REGISTRY[letter].width(p), kind='cap')(fn)


_degree_letter('uni2103', '℃', 'C')
_degree_letter('uni2109', '℉', 'F')


@sign('uni2117', '℗', lambda p: p.cap + 0.0, kind=('punct', 1.0))
def soundcopyright(g):
    from .symbols import _ringed
    _ringed(g, 'P')


@sign('uni2120', '℠', lambda p: 0.55 * (REGISTRY['S'].width(p) + REGISTRY['M'].width(p)) + 0.6 * p.m,
       kind=('punct', 0.8))
def servicemark(g):
    """S and M small on the cap height, as the trade mark sets T and M."""
    from .symbols import stamp as sstamp
    p = g.p
    from .symkit import small_letter
    ps = small_letter(p, 0.55)
    ws = sstamp(g, 'S', ps, dy=p.cap - ps.cap)
    sstamp(g, 'M', ps, dx=ws + 0.6 * p.m, dy=p.cap - ps.cap)


def _smallcaps(name, ch, letters):
    """Small capitals set tight, on the baseline (TEL, FAX)."""
    from .cyrillic import sc

    def width(p):
        q = sc(p).with_(mono=False)
        return tight(tuple(letters), q, (0.0, q.cap))[2]

    def fn(g):
        q = sc(g.p)
        set_tight(g, letters, zone=(0.0, q.cap), p=q)
    glyph(name, ch, width, kind='lower')(fn)


_smallcaps('uni2121', '℡', ['T', 'E', 'L'])
_smallcaps('uni213B', '℻', ['F', 'A', 'X'])
