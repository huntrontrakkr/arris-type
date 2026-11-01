"""Greek.

Capitals shared with Latin and Cyrillic are aliases. New capitals use the
same moves: the gable (Lambda, Delta), the octagon (Theta, and Omega opened
at the bottom on outward feet), bars (Xi), a 45-degree chevron between two
bars (Sigma), a cup on a stem (Psi).

Lowercase is drawn: most forms grow from the Latin ones (eta from n, mu from
u, rho from p, final sigma from c, epsilon as a mirrored small Ze, beta from
the sharp s with a descending stem).
"""
from __future__ import annotations

from ..draw import B, REGISTRY, Opening, glyph
from ..params import SQRT2
from .caps import big
from .cyrillic import mirror, sc
from .figures import beak_depth, jog
from .letterframe import STEEP, Frame, k_arms, letter_width

ALIASES = {
    0x037E: 'semicolon', 0x0387: 'periodcentered',
    0x0391: 'A', 0x0392: 'B', 0x0395: 'E', 0x0396: 'Z', 0x0397: 'H', 0x0399: 'I', 0x039A: 'K', 0x039C: 'M',
    0x039D: 'N', 0x039F: 'O', 0x03A1: 'P', 0x03A4: 'T', 0x03A5: 'Y', 0x03A7: 'X',
    0x0393: 'uni0413', 0x03A0: 'uni041F', 0x03A6: 'uni0424',
    0x03BF: 'o', 0x03BD: 'v', 0x03BA: 'uni043A', 0x03C6: 'uni0444',
}


def gcap(name, ch, wm, stems, width=None):
    return glyph(name, ch, width or letter_width(wm, stems), kind='cap')


def glow(name, ch, wm, stems, width=None, openings=()):
    return glyph(name, ch, width or letter_width(wm, stems), kind='lower', openings=openings)


# --- Capitals ----------------------------------------------------------------

def _steep_gable(g, f, wm):
    """A gable at the 7's 2:1 slope, standing on short verticals: without a
    crossbar a 45-degree gable reads as an arch, a steeper one as a point."""
    p, W, H = f.p, f.W, f.p.cap
    xl, xr = f.X(1), f.X(wm - 1)
    lift = (p.ss / 2) * 5 ** 0.5                            # outer edge above the centreline, vertically
    ya = H + 2 * p.c - lift                                 # outer point 2c above the cap: cut flat by the body
    yt = ya - 2 * (W / 2 - xl)
    g.stroke((xl, 0), (xl, yt), (W / 2, ya), (xr, yt), (xr, 0))
    return xl, xr


@gcap('uni039B', '\u039b', 10, 2)
def Lambda(g):
    _steep_gable(g, Frame(g, 10), 10)


@gcap('uni0394', '\u0394', 10, 2)
def Delta(g):
    f = Frame(g, 10)
    _steep_gable(g, f, 10)
    g.stroke((0, f.Y(1)), (f.W, f.Y(1)))


@gcap('uni0398', 'Θ', 10, 2)
def Theta(g):
    REGISTRY['O'].fn(g)
    f = Frame(g, 10)
    g.stroke(f.P(3.5, 6), f.P(6.5, 6))


@gcap('uni039E', 'Ξ', 9, 0)
def Xi(g):
    f = Frame(g, 9)
    g.stroke((0, f.Y(11)), (f.W, f.Y(11)))
    g.stroke(f.P(1.5, 6), f.P(7.5, 6))
    g.stroke((0, f.Y(1)), (f.W, f.Y(1)))


@gcap('uni03A3', 'Σ', 9, 1)
def Sigma(g):
    """Two bars joined by a 45-degree chevron pointing into the counter."""
    f = Frame(g, 9)
    p, W, H = f.p, f.W, f.p.cap
    yt, yb = f.Y(11), f.Y(1)
    half = (yt - yb) / 2
    xl = f.X(1)
    g.stroke((W, yt), (xl, yt), (xl + min(half, 0.45 * W), (yt + yb) / 2), (xl, yb), (W, yb))


@gcap('uni03A8', 'Ψ', 11, 3)
def Psi(g):
    f = Frame(g, 11)
    p, W = f.p, f.W
    g.stroke(f.P(1, 12), B(*f.P(1, 5)), B(*f.P(10, 5)), f.P(10, 12))
    g.stroke((W / 2, 0), (W / 2, p.cap))


@gcap('uni03A9', 'Ω', 10, 2)
def Omega(g):
    """An octagon opened at the foot, its sides chamfered in and turned out."""
    f = Frame(g, 10)
    p, W = f.p, f.W
    xl, xr = f.X(1), f.X(9)
    xf, xg = f.X(3), f.X(7)
    y_in = f.Y(1) + p.sv                                    # where the sides finish turning in
    ys = y_in + (xf - xl)                                   # where they start
    g.stroke((0, f.Y(1)), (xf, f.Y(1)), (xf, y_in), (xl, ys), B(xl, f.Y(11)), B(xr, f.Y(11)), (xr, ys),
             (xg, y_in), (xg, f.Y(1)), (W, f.Y(1)))


# --- Lowercase ---------------------------------------------------------------

@glow('uni03B1', 'α', 8, 2)
def alpha(g):
    f = Frame(g, 8, 'lower')
    g.stroke(f.P(7, 8), B(*f.P(1, 8)), B(*f.P(1, 1)), f.P(7, 1), closed=True)
    g.stroke(f.P(7, 9), f.P(7, 1), f.P(8, 0))


@glow('uni03B2', 'β', 8, 2)
def beta(g):
    f = Frame(g, 8, 'asc')
    p = f.p
    g.clip = (0, -p.desc, f.W, p.asc)
    g.stroke(f.P(1, -3), B(*f.P(1, 12)), B(*f.P(7, 12)), B(*f.P(7, 7.5), big(p)), f.P(3.5, 7.5))
    g.stroke(f.P(3.5, 7.5), B(*f.P(7, 7.5)), B(*f.P(7, 1)), f.P(1, 1))


@glow('uni03B3', 'γ', 8, 2)
def gamma(g):
    f = Frame(g, 8, 'lower')
    p, W, k = f.p, f.W, f.k
    xl, xr = f.X(1), f.X(7)
    ya = f.Y(1)
    yt = ya + (W / 2 - xl)
    g.clip = (0, -p.desc, W, p.xh)
    g.stroke((xl, p.xh), (xl, yt), (W / 2, ya), (xr, yt), (xr, p.xh))
    g.stroke((W / 2, ya), (W / 2, -p.desc))


def _delta_hook(g):
    """The white under δ's bar beside its neck, halfway up the neck."""
    return g.defaults_used['hook']


@glow('uni03B4', 'δ', 8, 2, openings=[Opening(_delta_hook, 'neck', lambda p: 0.5)])
def delta(g):
    """An o under a hooked ascender: from the bowl's top a stroke up to the
    left, turning at the ascender into a short top bar to the right. Not
    the 6 (whose stem stands on the bowl's left side), nor the soft sign's
    be (б), whose flag it used to borrow. The neck is 45 degrees; heavier
    strokes would fill the white under the bar, so as they grow it stands
    up, toward the 7's 2:1, as far as it needs to keep that white open
    (``neck``: its run across for its rise)."""
    f = Frame(g, 8, 'asc')
    p = f.p
    g.clip = (0, -p.desc, f.W, p.asc)
    g.stroke(B(*f.P(1, 1)), B(*f.P(7, 1)), B(*f.P(7, 8)), B(*f.P(1, 8)), closed=True)
    xl, yt, yb = f.X(1), f.Y(12), f.Y(8)
    s = g.free('neck', 1.0)
    g.stroke((xl + s * (yt - yb), yb), B(xl, yt), f.P(6, 12), start='h')
    g.defaults_used['hook'] = f.X(6) - (xl + s * (yt - yb) / 2 + p.sd * (1 + s * s) ** 0.5 / 2)


@glow('uni03B5', 'ε', 8, 2)
def epsilon(g):
    """A small Ze, mirrored: beaks at the right, the waist's point at the left."""
    f = Frame(g, 8, 'lower')
    p, d = f.p, beak_depth(f.p)
    g.stroke((f.X(7), p.xh - d), B(*f.P(7, 8)), B(*f.P(1, 8)), B(*f.P(1, 4.5), big(p)), f.P(5, 4.5))
    g.stroke(f.P(5, 4.5), B(*f.P(1, 4.5)), B(*f.P(1, 1)), B(*f.P(7, 1)), (f.X(7), d))


@glow('uni03B6', 'ζ', 8, 1)
def zeta(g):
    f = Frame(g, 8, 'asc')
    p, k = f.p, f.k
    g.clip = (0, -p.desc, f.W, p.asc)
    xl, xr = f.X(1), f.X(7)
    y_top = f.Y(12)
    y_l = y_top - (xr - xl)
    from .italic_forms import tail_run
    g.stroke((f.X(1.5), y_top), (xr, y_top), (xl, y_l), B(xl, f.Y(1)), B(xr, f.Y(1)), (xr, f.Y(-2)),
             (xr - tail_run(p, xr - f.X(5)), f.Y(-2)))


@glow('uni03B7', 'η', 8, 2)
def eta(g):
    f = Frame(g, 8, 'lower')
    p = f.p
    g.clip = (0, -p.desc, f.W, p.xh)
    g.stroke(f.P(1, 0), f.P(1, 9))
    g.stroke(f.P(1, 8), B(*f.P(7, 8)), f.P(7, -3))


@glow('uni03B8', 'θ', 8, 2)
def theta(g):
    f = Frame(g, 8, 'asc')
    g.stroke(B(*f.P(1, 1)), B(*f.P(7, 1)), B(*f.P(7, 12)), B(*f.P(1, 12)), closed=True)
    g.stroke(f.P(1, 6.5), f.P(7, 6.5))


@glow('uni03B9', 'ι', 5, 1)
def iota(g):
    f = Frame(g, 5, 'lower')
    g.stroke(f.P(1, 9), B(*f.P(1, 1)), f.P(5, 1))


@glow('uni03BB', 'λ', 8, 1)
def lambda_(g):
    """A long 2:1 stroke from the ascender to the right foot, a 45-degree leg
    from its middle to the left."""
    f = Frame(g, 8, 'asc')
    p, W = f.p, f.W
    w = p.ss / STEEP[1]
    x_at = lambda y: W - w / 2 - y / 2                      # the long stroke lands at the right
    g.stroke((x_at(p.asc), p.asc), (x_at(0), 0), start='h', end='h')
    ym = p.xh * 0.55
    xm = x_at(ym)
    g.stroke((xm, ym), (xm - ym, 0), start='flat', end='h')


@glow('uni03BC', 'μ', 8, 2)
def mu(g):
    f = Frame(g, 8, 'lower')
    p = f.p
    g.clip = (0, -p.desc, f.W, p.xh)
    g.stroke(f.P(1, -3), f.P(1, 9))
    g.stroke(f.P(1, 1), B(*f.P(7, 1)), f.P(7, 9))


@glow('uni03BE', 'ξ', 8, 1)
def xi(g):
    f = Frame(g, 8, 'asc')
    p = f.p
    g.clip = (0, -p.desc, f.W, p.asc)
    g.stroke(f.P(7, 12), B(*f.P(1.5, 12)), B(*f.P(1.5, 7)), f.P(6, 7))
    g.stroke(f.P(6, 7), B(*f.P(1, 7)), B(*f.P(1, 1)), B(*f.P(7, 1)), f.P(7, -2.5))


@glow('uni03C0', 'π', 9, 2)
def pi(g):
    f = Frame(g, 9, 'lower')
    g.stroke((0, f.Y(8)), (f.W, f.Y(8)))
    g.stroke(f.P(2, 8), f.P(2, 0))
    g.stroke(f.P(7, 8), B(*f.P(7, 1)), f.P(9, 1))


@glow('uni03C1', 'ρ', 8, 2)
def rho(g):
    f = Frame(g, 8, 'lower')
    p = f.p
    g.clip = (0, -p.desc, f.W, p.xh)
    g.stroke(B(*f.P(1, 1)), B(*f.P(7, 1)), B(*f.P(7, 8)), B(*f.P(1, 8)), closed=True)
    g.stroke(f.P(1, -3), f.P(1, 4))


@glow('uni03C3', 'σ', 9.5, 2)
def sigma(g):
    f = Frame(g, 9.5, 'lower')
    W = f.W
    xr = W - 1.5 * f.p.m - f.p.sv / 2
    g.stroke(B(*f.P(1, 1)), B(xr, f.Y(1)), B(xr, f.Y(8)), f.P(1, 8), closed=True)
    g.stroke(f.P(4, 8), (W, f.Y(8)))


@glow('uni03C2', 'ς', 8, 2)
def finalsigma(g):
    f = Frame(g, 8, 'lower')
    p, d = f.p, beak_depth(f.p)
    g.clip = (0, -p.desc, f.W, p.xh)
    from .italic_forms import tail_run
    g.stroke((f.X(7), p.xh - d), B(*f.P(7, 8)), B(*f.P(1, 8)), B(*f.P(1, 2.5)), B(*f.P(7, 2.5)),
             B(*f.P(7, -2)), (f.X(7) - tail_run(p, f.X(7) - f.X(4)), f.Y(-2)))


@glow('uni03C4', 'τ', 8, 1)
def tau(g):
    f = Frame(g, 8, 'lower')
    g.stroke((0, f.Y(8)), (f.W, f.Y(8)))
    g.stroke(f.P(3.5, 8), B(*f.P(3.5, 1)), f.P(7, 1))


@glow('uni03C5', 'υ', 8, 2)
def upsilon(g):
    f = Frame(g, 8, 'lower')
    g.stroke(f.P(1, 9), B(*f.P(1, 1)), B(*f.P(7, 1)), f.P(7, 9))


@glow('uni03C7', 'χ', 8, 2)
def chi(g):
    f = Frame(g, 8, 'lower')
    p = f.p
    g.clip = (0, -p.desc, f.W, p.xh)
    xl, xr = f.X(1), f.X(7)
    top, bot = p.xh, -p.desc
    half = (xr - xl) / 2
    yc = (top + bot) / 2
    g.stroke((xl, top), (xl, yc + half), (xr, yc - half), (xr, bot))
    g.stroke((xr, top), (xr, yc + half), (xl, yc - half), (xl, bot))


@glow('uni03C8', 'ψ', 10, 3)
def psi(g):
    f = Frame(g, 10, 'lower')
    p, W = f.p, f.W
    g.clip = (0, -p.desc, W, p.asc)
    g.stroke(f.P(1, 9), B(*f.P(1, 1)), B(*f.P(9, 1)), f.P(9, 9))
    g.stroke((W / 2, -p.desc), (W / 2, p.asc))


@glow('uni03C9', 'ω', 12, 3)
def omega(g):
    f = Frame(g, 12, 'lower')
    g.stroke(f.P(1, 9), B(*f.P(1, 1)), B(*f.P(11, 1)), f.P(11, 9))
    g.stroke((f.W / 2, f.Y(1)), (f.W / 2, f.Y(5.5)))


# --- Capitals with tonos: the accent stands to the left, at the cap height ----

TONOS = {0x0386: 'A', 0x0388: 'E', 0x0389: 'H', 0x038A: 'I', 0x038C: 'O', 0x038E: 'Y', 0x038F: 'uni03A9'}


def _tonos_width(p):
    from .marks import size
    return size(p, 'uc') + 0.6 * p.sv + 0.5 * p.m


for cp, base in TONOS.items():
    def fn(g, base=base):
        from .extra_latin import stamp
        from .marks import acute, size
        p = g.p
        a = size(p, 'uc')
        if p.mono:                                          # no room beside it: above, to the left
            stamp(g, base, width=g.W)
            acute(g, a / 2 + p.sv / 2, p.cap + 0.6 * p.m, 'uc')
            return
        t = _tonos_width(p)
        stamp(g, base, t)
        acute(g, t / 2 - 0.1 * p.m, p.cap - a, 'uc')
    glyph(f'uni{cp:04X}', chr(cp), lambda p, b=base: REGISTRY[b].width(p) + _tonos_width(p), kind='cap')(fn)
