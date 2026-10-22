"""Greek symbols and archaic letters.

* **Symbols**: the curled beta (the b with a loop on its ascender, as
  Bulgarian в), the script theta, the upsilon with hooks (Y whose arms
  turn out and down into beaks), the pi symbol (ω under a bar), the kappa
  symbol (an x whose falling stroke leaves and lands on flats), the tailed
  rho; the lunate forms and the theta symbol are letters Arris has.
* **Archaic and numeral letters**: koppa (an O on a stem), stigma (ς with
  a bar), digamma (F, and its small form in the descender), the numeral
  koppa (the 7's diagonal twice, a lightning stroke), sampi (an arch over
  two parallel diagonals).

Capitals with tonos stand it to the left, as the monotonic capitals do.
"""
from __future__ import annotations

from ..draw import B, REGISTRY, glyph
from ..params import SQRT2
from .cyrillic import mirror
from .cyrillic_ext import room
from .cyrillic_locl import tall_ve
from .figures import beak_depth
from .greek import _tonos_width
from .letterframe import Frame, letter_width

ALIASES = {
    0x03D5: 'uni0444',      # phi symbol: the stroked phi
    0x03DC: 'F',            # digamma
    0x03F2: 'c', 0x03F9: 'C',   # lunate sigma
    0x03F3: 'j', 0x037F: 'J',   # yot
    0x03F4: 'uni04E8',      # capital theta symbol: the O barred wall to wall (Ө)
    0x03F5: 'uni0454',      # lunate epsilon (є)
    0x03F6: 'uni044D',      # reversed lunate epsilon (э)
    0x03F7: 'Thorn', 0x03F8: 'thorn',   # sho
}


def gcap(name, ch, wm, stems, width=None):
    return glyph(name, ch, width or letter_width(wm, stems), kind='cap')


def glow(name, ch, wm, stems, width=None):
    return glyph(name, ch, width or letter_width(wm, stems), kind='lower')


# --- Symbols -----------------------------------------------------------------

glow('uni03D0', 'ϐ', 8, 2)(tall_ve)


@glow('uni03D1', 'ϑ', 10, 3)
def theta_symbol(g):
    """The script theta: a u whose right side rises to the ascender, turns
    back over a loop and leaves across it on a bar to the right."""
    f = Frame(g, 10, 'asc')
    p = g.p
    xl, xr = f.X(1), f.X(8.5)
    xm = min(f.X(4.5), xr - p.sv - room(p))                 # the loop keeps a module of white
    yb = f.Y(6)
    # the u's left arm reaches the bar's height where it stands clear of
    # the loop, and stops half a stem under the bar where it cannot
    top = f.Y(7) if xm - xl - p.sv >= 0.25 * p.sv else yb - g.sh - 0.5 * p.sv
    g.stroke((xl, top), B(xl, f.Y(1)), B(xr, f.Y(1)), B(xr, f.Y(12)), B(xm, f.Y(12)), (xm, yb))
    g.stroke((xm, yb), (g.W, yb))


@gcap('uni03D2', 'ϒ', 10, 2)
def Upsilonhook(g):
    """Y whose arms turn out at the cap height and end in beaks."""
    f = Frame(g, 10)
    p, W, H = f.p, f.W, f.p.cap
    xl, xr = f.X(1), f.X(9)
    d = beak_depth(p)
    yt = f.Y(11)
    xa = xl + 1.25 * p.leg + 0.5 * p.sv                     # where the arm meets the top line
    yj = yt - 2 * (W / 2 - xa)                              # at the 7's 2:1 slope, as the v's arms
    g.stroke((W / 2, 0), (W / 2, yj))
    for s in (1, -1):
        X = lambda x: W / 2 + s * (x - W / 2)
        g.stroke((W / 2, yj), (X(xa), yt), B(X(xl), yt), (X(xl), H - d))


@glyph('uni03D3', 'ϓ', lambda p: REGISTRY['uni03D2'].width(p) + _tonos_width(p), kind='cap')
def Upsilonacutehook(g):
    from .extra_latin import stamp
    from .marks import acute, size
    p = g.p
    a = size(p, 'uc')
    if p.mono:
        stamp(g, 'uni03D2', width=g.W)
        acute(g, a / 2 + p.sv / 2, p.cap + 0.6 * p.m, 'uc')
        return
    t = _tonos_width(p)
    stamp(g, 'uni03D2', t)
    acute(g, t / 2 - 0.1 * p.m, p.cap - a, 'uc')


@glow('uni03D6', 'ϖ', 13, 3)
def pi_symbol(g):
    """ω under a bar that reaches past its sides."""
    f = Frame(g, 13, 'lower')
    g.stroke((0, f.Y(8)), (f.W, f.Y(8)))
    g.stroke(f.P(2, 8), B(*f.P(2, 1)), B(*f.P(11, 1)), f.P(11, 8))
    g.stroke((f.W / 2, f.Y(1)), (f.W / 2, f.Y(5)))


@glow('uni03F0', 'ϰ', 8, 2)
def kappa_symbol(g):
    """An x whose falling stroke leaves on a flat at the top left and lands
    on one at the bottom right (both strokes at the 7's 2:1 slope)."""
    f = Frame(g, 8, 'lower')
    p, W = f.p, f.W
    yt, yb = f.Y(8), f.Y(1)
    run = (yt - yb) / 2
    xa = (W - run) / 2
    g.stroke((0, yt), (xa, yt), (xa + run, yb), (W, yb))
    x0 = W / 2 - p.xh / 4
    g.stroke((x0, 0), (x0 + p.xh / 2, p.xh), start='h', end='h')


@glow('uni03F1', 'ϱ', 8, 2)
def rho_symbol(g):
    """ρ whose stem turns right at its foot, under the bowl."""
    f = Frame(g, 8, 'lower')
    p = f.p
    g.clip = (0, -p.desc, f.W, p.xh)
    g.stroke(B(*f.P(1, 1)), B(*f.P(7, 1)), B(*f.P(7, 8)), B(*f.P(1, 8)), closed=True)
    g.stroke(f.P(1, 4), B(*f.P(1, -2)), f.P(6.5, -2))


# --- Lunate sigmas, reversed and dotted ---------------------------------------

def _dot_in(g, x, y):
    s = g.p.dot()
    g.stroke((x, y - s / 2, s), (x, y + s / 2))


def _lunate(name, ch, base, kind, rev, dot):
    def fn(g, base=base, rev=rev, dot=dot):
        REGISTRY[base].fn(g)
        if rev:
            mirror(g)
        if dot:
            p = g.p
            top = p.cap if kind == 'cap' else p.xh
            _dot_in(g, g.W / 2 + (-0.15 if rev else 0.15) * g.W, top / 2)
    glyph(name, ch, lambda p, b=base: REGISTRY[b].width(p), kind=kind)(fn)


_lunate('uni03FD', 'Ͻ', 'C', 'cap', True, False)
_lunate('uni03FE', 'Ͼ', 'C', 'cap', False, True)
_lunate('uni03FF', 'Ͽ', 'C', 'cap', True, True)
_lunate('uni037B', 'ͻ', 'c', 'lower', True, False)
_lunate('uni037C', 'ͼ', 'c', 'lower', False, True)
_lunate('uni037D', 'ͽ', 'c', 'lower', True, True)


# --- Archaic letters and numerals ---------------------------------------------

@gcap('uni03D8', 'Ϙ', 10, 2)
def Koppaarchaic(g):
    """An O on a stem."""
    f = Frame(g, 10)
    g.stroke(B(*f.P(1, 4.5)), B(*f.P(9, 4.5)), B(*f.P(9, 11)), B(*f.P(1, 11)), closed=True)
    g.stroke((f.W / 2, 0), (f.W / 2, f.Y(4.5)))


@glow('uni03D9', 'ϙ', 8, 2)
def koppaarchaic(g):
    f = Frame(g, 8, 'lower')
    p = g.p
    g.clip = (0, -p.desc, f.W, p.xh)
    g.stroke(B(*f.P(1, 1)), B(*f.P(7, 1)), B(*f.P(7, 8)), B(*f.P(1, 8)), closed=True)
    g.stroke((f.W / 2, f.Y(1)), (f.W / 2, -p.desc))


@gcap('uni03DA', 'Ϛ', 9, 2)
def Stigma(g):
    """The final sigma at capital height."""
    f = Frame(g, 9)
    p, d = f.p, beak_depth(f.p)
    g.clip = (0, -p.desc, f.W, p.cap)
    g.stroke((f.X(8), p.cap - d), B(*f.P(8, 11)), B(*f.P(1, 11)), B(*f.P(1, 4)), B(*f.P(8, 4)),
             B(*f.P(8, -2)), f.P(5, -2))


@glow('uni03DB', 'ϛ', 9, 2)
def stigma(g):
    """ς whose top runs on to the right as a bar (σ's)."""
    f = Frame(g, 9, 'lower')
    p = f.p
    g.clip = (0, -p.desc, f.W, p.xh)
    g.stroke((f.W, f.Y(8)), B(*f.P(1, 8)), B(*f.P(1, 2.5)), B(*f.P(7, 2.5)), B(*f.P(7, -2)), f.P(4, -2))


@glow('uni03DD', 'ϝ', 7, 1)
def digamma(g):
    """The F on the x-height, its stem in the descender."""
    f = Frame(g, 7, 'lower')
    p = g.p
    g.clip = (0, -p.desc, f.W, p.xh)
    g.stroke(f.P(7, 8), f.P(1, 8), (f.X(1), -p.desc))
    g.stroke(f.P(1, 3), f.P(6, 3))


@gcap('uni03DE', 'Ϟ', 9, 1)
def Koppa(g):
    """The numeral koppa: the 7 (a bar and its 2:1 stroke) twice, the
    second hung from a bar at the waist, landing on a foot."""
    f = Frame(g, 9)
    p = g.p
    yt, ym, yb = f.Y(11), f.Y(6), f.Y(1)
    run = (yt - ym) / 2
    xa = f.X(1) + run
    xb = f.X(8)
    g.stroke(f.P(0.5, 11), (xa, yt), (xa - run, ym), (xb, ym), (xb - (ym - yb) / 2, yb), (f.W, yb))


@glow('uni03DF', 'ϟ', 8, 1)
def koppa(g):
    """The small numeral koppa: a stem down to the middle of the x-height,
    a bar, and the 7's 2:1 stroke into the descender, landing on a foot."""
    f = Frame(g, 8, 'lower')
    p = g.p
    g.clip = (0, -p.desc, f.W, p.xh)
    ym, yd = f.Y(4), f.Y(-2)
    xb = f.X(7)
    xl = xb - (ym - yd) / 2
    g.stroke(f.P(1, 9), (f.X(1), ym), (xb, ym), (xl, yd), (min(xl + 2.5 * p.m, f.W), yd))


def _sampi(g, f, xl, xr, top, foot):
    """An arch from a beak at the left over to the right, its right side
    down to ``foot``; two parallel strokes at the shallow 2:1 slope hang
    from the right side, half a stem (a module at light weights) below the
    arch and apart. Where the x-height has no room for them (the small
    sampi at heavy weights) the lower one runs into the descender."""
    p = g.p
    d = beak_depth(p)
    g.stroke((xl, top + g.sh / 2 - d), B(xl, top), B(xr, top), (xr, foot))
    t = p.sh + (p.sd - p.sh) * 26.565 / 45                   # thickness at the shallow slope (geom.Thickness)
    v = t * 5 ** 0.5 / 2                                    # ... measured upright
    white = max(0.5 * p.sv, p.m * 0.8)
    wv = white * 5 ** 0.5 / 2
    x_end = xl + 0.2 * (xr - xl)
    run = xr - x_end
    y1 = top - g.sh / 2 - wv - v / 2
    for y in (y1, y1 - v - wv):
        g.stroke((xr, y), (x_end, y - run / 2))


@gcap('uni03E0', 'Ϡ', 9, 2)
def Sampi(g):
    f = Frame(g, 9)
    _sampi(g, f, f.X(1), f.X(8), f.Y(11), 0)


@glow('uni03E1', 'ϡ', 8, 2)
def sampi(g):
    f = Frame(g, 8, 'lower')
    p = g.p
    g.clip = (0, -p.desc, f.W, p.xh)
    _sampi(g, f, f.X(1), f.X(7), f.Y(8), -p.desc)


# --- Spacing marks -------------------------------------------------------------

@glyph('tonos', '΄', lambda p: 0.4 * p.cap / 2, kind=('punct', 0.4))
def tonos(g):
    from .marks import acute, size
    p = g.p
    acute(g, size(p, 'uc') / 2, p.cap - size(p, 'uc'), 'uc')


@glyph('uni0374', 'ʹ', lambda p: 0.4 * p.cap / 2, kind=('punct', 0.4))
def numeralsign(g):
    """The keraia: an acute standing at the cap height."""
    from .marks import acute, size
    p = g.p
    acute(g, size(p, 'uc') / 2, p.cap - size(p, 'uc'), 'uc')


@glyph('uni0375', '͵', lambda p: 0.4 * p.cap / 2, kind=('punct', 0.4))
def lowernumeralsign(g):
    """The lower keraia: the same stroke, hung below the baseline."""
    from .marks import acute, size
    p = g.p
    acute(g, size(p, 'uc') / 2, -0.8 * p.desc, 'uc')
