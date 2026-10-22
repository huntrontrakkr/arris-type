"""Latin letters that do not decompose: barred and slashed letters, ligatures
and the sharp s, built from existing parts where they are composites.

``stamp`` draws a finished glyph (openings solved, clipped and cut) into
another at an offset, the general way to make a composite.
"""
from __future__ import annotations

from shapely import affinity

from ..draw import B, REGISTRY, draw, glyph
from ..geom import rings_to_shapely
from ..params import SQRT2
from .caps import big
from .figures import beak_depth
from .letterframe import Frame, k_arms, letter_width


def stamp(g, name, dx=0.0, dy=0.0, width=None):
    sub = draw(name, g.p, width=width)
    poly = rings_to_shapely(sub.rings())
    g.extra.append(affinity.translate(poly, dx, dy))
    return sub.W


def width_of(name, extra=0.0, scale=1.0):
    return lambda p: REGISTRY[name].width(p) * scale + extra * p.m + (0 if extra >= 0 else 0)


def plus_width(*names, gap=0.0):
    return lambda p: sum(REGISTRY[n].width(p) for n in names) + gap * p.m


def _bar(g, x0, x1, y):
    g.stroke((x0, y), (x1, y))


# --- Bars and slashes over existing letters ----------------------------------

def _slashbar(g, x, y, e):
    """A short 45-degree stroke through a stem (the Polish l's stroke)."""
    g.stroke((x - e, y - e), (x + e, y + e), start='v', end='v')


@glyph('Lslash', 'Ł', width_of('L', 1.5), kind='cap')
def Lslash(g):
    p = g.p
    dx = 1.5 * p.m
    stamp(g, 'L', dx, width=g.W - dx)
    _slashbar(g, dx + p.sv / 2, 0.45 * p.cap, 1.5 * p.m + p.sv / 2)


@glyph('lslash', 'ł', width_of('l', 1.5), kind='lower')
def lslash(g):
    p = g.p
    w = stamp(g, 'l', width=g.W - 1.5 * p.m if p.mono else None)
    xs = (w - p.sv / 2) if not p.mono else g.W / 2
    _slashbar(g, xs, 0.55 * p.xh + p.m, 1.5 * p.m + p.sv / 2)


def _oslash(g, name, top):
    p = g.p
    w = stamp(g, name)
    k = p.sd / SQRT2
    # along the main diagonal, square to the lower-left and upper-right chamfers
    a = w / 2 - top / 2                                     # x - y = a
    lo, hi = -0.75 * p.m, top + 0.75 * p.m
    g.stroke((lo + a, lo), (hi + a, hi), start='h', end='h')
    g.clip = (-p.m, lo, w + p.m, hi)


@glyph('Oslash', 'Ø', width_of('O'), kind='cap')
def Oslash(g):
    _oslash(g, 'O', g.p.cap)


@glyph('oslash', 'ø', width_of('o'), kind='lower')
def oslash(g):
    _oslash(g, 'o', g.p.xh)


@glyph('Dcroat', 'Đ', width_of('D', 1.5), kind='cap')
def Dcroat(g):
    p = g.p
    dx = 1.5 * p.m
    stamp(g, 'D', dx, width=g.W - dx)
    _bar(g, 0, dx + p.sv + 2.5 * p.m, p.cap / 2)


@glyph('Eth', 'Ð', width_of('D', 1.5), kind='cap')
def Eth(g):
    Dcroat(g)


@glyph('dcroat', 'đ', width_of('d', 1.5), kind='lower')
def dcroat(g):
    p = g.p
    w = stamp(g, 'd', width=g.W - 1.5 * p.m)
    xs = w - p.sv / 2
    _bar(g, xs - 2.5 * p.m, xs + 1.5 * p.m + p.sv / 2, (p.xh + p.asc) / 2 + p.m / 2)


@glyph('Hbar', 'Ħ', width_of('H', 2.0), kind='cap')
def Hbar(g):
    p = g.p
    w = stamp(g, 'H', p.m, width=g.W - 2 * p.m)
    _bar(g, 0, w + 2 * p.m, 0.75 * p.cap + g.sh / 4)


@glyph('hbar', 'ħ', width_of('h', 1.0), kind='lower')
def hbar(g):
    p = g.p
    w = stamp(g, 'h', p.m, width=g.W - p.m)
    _bar(g, 0, p.m + p.sv + 2 * p.m, (p.xh + p.asc) / 2 + p.m / 2)


@glyph('Tbar', 'Ŧ', width_of('T'), kind='cap')
def Tbar(g):
    p = g.p
    w = stamp(g, 'T')
    _bar(g, w / 2 - 2 * p.m, w / 2 + 2 * p.m, p.cap / 2)


@glyph('tbar', 'ŧ', width_of('t'), kind='lower')
def tbar(g):
    p = g.p
    w = stamp(g, 't')
    _bar(g, 0, REGISTRY['t'].width(p) - p.m, p.xh * 0.45)


@glyph('Ldot', 'Ŀ', width_of('L', 1.0), kind='cap')
def Ldot(g):
    p = g.p
    stamp(g, 'L', width=g.W)
    x = p.sv + 1.0 * p.m + p.sv / 2
    g.stroke((x, p.cap / 2 - p.sv / 2), (x, p.cap / 2 + p.sv / 2))


@glyph('ldot', 'ŀ', width_of('l', 2.0), kind='lower')
def ldot(g):
    p = g.p
    w = stamp(g, 'l', width=(g.W - 2 * p.m) if p.mono else None)
    x = w + 1.0 * p.m + p.sv / 2
    g.stroke((x, p.xh / 2 - p.sv / 2), (x, p.xh / 2 + p.sv / 2))


# --- Pairs -------------------------------------------------------------------

@glyph('IJ', 'Ĳ', plus_width('I', 'J', gap=1.5), kind='cap')
def IJ(g):
    p = g.p
    gap = (0.75 if p.mono else 1.5) * p.m
    w = stamp(g, 'I', width=p.sv)
    stamp(g, 'J', w + gap, width=g.W - w - gap)


@glyph('ij', 'ĳ', plus_width('i', 'j', gap=1.0), kind='lower')
def ij(g):
    p = g.p
    w = stamp(g, 'dotlessi', width=p.sv)
    from .lower import _dot
    _dot(g, None, p.sv / 2)
    gap = (0.5 if p.mono else 1.0) * p.m
    stamp(g, 'j', w + gap, width=g.W - w - gap)


@glyph('napostrophe', 'ŉ', plus_width('quoteright', 'n', gap=0.5), kind='lower')
def napostrophe(g):
    p = g.p
    w = stamp(g, 'quoteright')
    stamp(g, 'n', w + 0.5 * p.m, width=g.W - w - 0.5 * p.m)


# --- Redrawn -----------------------------------------------------------------

@glyph('kgreenlandic', 'ĸ', letter_width(8, 1), kind='lower')
def kgreenlandic(g):
    f = Frame(g, 8, 'lower')
    g.stroke(f.P(1, 0), f.P(1, 9))
    for pts, a, b in k_arms(g, f.X(1), f.W, f.p.xh):
        g.stroke(*pts, start=a, end=b)


@glyph('longs', 'ſ', letter_width(7, 1), kind='lower')
def longs(g):
    f = Frame(g, 7, 'asc')
    g.stroke(f.P(2, 0), B(*f.P(2, 12)), f.P(7, 12))


@glyph('eng', 'ŋ', letter_width(8, 2), kind='lower')
def eng(g):
    f = Frame(g, 8, 'lower')
    p = f.p
    g.stroke(f.P(1, 0), f.P(1, 9))
    g.stroke(f.P(1, 8), B(*f.P(7, 8)), B(*f.P(7, -2)), f.P(3, -2))


@glyph('Eng', 'Ŋ', letter_width(9, 2), kind='cap')
def Eng(g):
    f = Frame(g, 9)
    p = f.p
    g.clip = (0, -p.desc, f.W, p.cap)
    g.stroke(f.P(1, 0), f.P(1, 12))
    g.stroke(f.P(1, 11), B(*f.P(8, 11)), B(*f.P(8, -2)), f.P(4, -2))


@glyph('Thorn', 'Þ', letter_width(9, 2), kind='cap')
def Thorn(g):
    f = Frame(g, 9)
    g.stroke(f.P(1, 0), f.P(1, 12))
    g.stroke(f.P(1, 9), B(*f.P(8, 9)), B(*f.P(8, 3)), f.P(1, 3))


@glyph('thorn', 'þ', letter_width(8, 2), kind='lower')
def thorn(g):
    f = Frame(g, 8, 'asc')
    p = f.p
    g.clip = (0, -p.desc, f.W, p.asc)
    g.stroke(f.P(1, -3), f.P(1, 13))
    g.stroke(f.P(1, 8), B(*f.P(7, 8)), B(*f.P(7, 1)), f.P(1, 1), closed=True)


@glyph('eth', '\u00f0', letter_width(8, 2), kind='lower')
def eth(g):
    """An o whose right side rises and bends back over it at 45 degrees,
    crossed level partway up (the barred d's bar)."""
    p = g.p
    f = Frame(g, 8, 'asc')
    W8 = letter_width(8, 2)(p)
    xr = W8 - p.sv / 2
    xl = p.sv / 2
    g.stroke(B(xl, g.sh / 2), B(xr, g.sh / 2), B(xr, p.xh - g.sh / 2), B(xl, p.xh - g.sh / 2), closed=True)
    y_bend = p.xh - g.sh / 2
    reach = p.asc - y_bend
    g.stroke((xr, p.xh / 2), (xr, y_bend), (xr - reach, p.asc), end='h')
    yb = p.xh + 0.45 * (p.asc - p.xh)
    xc = xr - (yb - y_bend)                                  # the diagonal's centre at the bar
    g.stroke((xc - 1.6 * p.m, yb), (xc + 1.6 * p.m, yb))
    g.clip = (0, 0, g.W, p.asc)


@glyph('germandbls', 'ß', letter_width(8, 2), kind='lower')
def germandbls(g):
    """A stem carrying the 3's right side: the waist's point, the flat end."""
    f = Frame(g, 8, 'asc')
    p = f.p
    g.stroke(f.P(1, 0), B(*f.P(1, 12)), B(*f.P(7, 12)), B(*f.P(7, 7.5), big(p)), f.P(3.5, 7.5))
    g.stroke(f.P(3.5, 7.5), B(*f.P(7, 7.5)), B(*f.P(7, 1)), f.P(3.5, 1))


@glyph('uni1E9E', 'ẞ', letter_width(9, 2), kind='cap')
def Germandbls(g):
    """Capital sharp s: a stem, a top bar, a 45-degree return, the 3's lower bowl."""
    f = Frame(g, 9)
    p = f.p
    x8 = f.X(8)
    y_mid = f.Y(11) - (x8 - f.X(4.5))
    g.stroke(f.P(1, 0), B(*f.P(1, 11)), (x8, f.Y(11)))
    g.stroke((x8, f.Y(11)), (f.X(4.5), y_mid))
    g.stroke((f.X(4.5), y_mid), B(x8, y_mid), B(*f.P(8, 1)), f.P(3, 1))


@glyph('AE', 'Æ', letter_width(13, 2), kind='cap')
def AE(g):
    f = Frame(g, 13)
    p, W, H, k = f.p, f.W, f.p.cap, f.k
    xs = f.X(7)
    xl = f.X(1)
    # the A's left leg, bending at 45 degrees into the top bar
    y_bend = f.Y(11) - (f.X(5) - xl)
    g.stroke((xl, 0), (xl, y_bend), (f.X(5), f.Y(11)), (W, f.Y(11)))
    g.stroke((xs, f.Y(11)), (xs, f.Y(1)), (W, f.Y(1)))
    g.stroke((xl, f.Y(6)), (f.X(12), f.Y(6)))


@glyph('ae', 'æ', lambda p: REGISTRY['a'].width(p) + REGISTRY['e'].width(p) - p.sv, kind='lower')
def ae(g):  # width: a + e sharing a stem
    p = g.p
    half = (g.W + p.sv) / 2
    wa = stamp(g, 'a', width=half)
    stamp(g, 'e', wa - p.sv, width=g.W - wa + p.sv)


@glyph('OE', 'Œ', letter_width(13, 2), kind='cap')
def OE(g):
    f = Frame(g, 13)
    p, W = f.p, f.W
    xs = f.X(7)
    g.stroke((xs, f.Y(1)), B(*f.P(1, 1)), B(*f.P(1, 11)), (xs, f.Y(11)), closed=True)
    g.stroke((W, f.Y(11)), (xs, f.Y(11)), (xs, f.Y(1)), (W, f.Y(1)))
    g.stroke((xs, f.Y(6)), (f.X(12), f.Y(6)))


@glyph('oe', 'œ', lambda p: REGISTRY['o'].width(p) + REGISTRY['e'].width(p) - p.sv, kind='lower')
def oe(g):
    p = g.p
    half = (g.W + p.sv) / 2
    wo = stamp(g, 'o', width=half)
    stamp(g, 'e', wo - p.sv, width=g.W - wo + p.sv)
