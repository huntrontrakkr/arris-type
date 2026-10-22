"""Number Forms (U+2150-U+218B): vulgar fractions, Roman numerals, the
dozenal digits.

* **Fractions** are set exactly as ½ ¼ ¾ are (``features._fraction``): a
  small numerator on the cap height, the fraction slash raised a fifth of
  the cap height, a small denominator on the baseline; ⅒ takes two
  denominator figures, ⅟ none.
* **Roman numerals** are the letters. A numeral of one letter is the letter
  itself (an alias), except Ⅰ and ⅰ, which keep the plain stem in the
  monospaced cut as the others do. A numeral of several letters is one
  glyph, its letters set tight (``symkit.set_tight``: half a letter's light
  each side, never closer than three quarters of a stem), so Ⅻ reads as one
  number and not as three letters; in a monospaced cell the group is
  condensed to fit.
* The archaic numerals are drawn from the same parts: Ↄ ↄ the C and c
  mirrored; ↀ ↂ ↈ octagonal rings round a stem (one, two, three rings);
  ↁ ↇ the D with a stem inside it, or two D bowls on one stem; ↅ the C
  whose foot drops below the baseline; ↆ a stem ending in an arrowhead.
* ↊ ↋ are the 2 and the 3 turned half round.
"""
from __future__ import annotations

from ..draw import B, REGISTRY, draw, glyph
from ..params import SQRT2
from .features import small
from .letterframe import Frame, growing_width, heft, letter_width
from .symkit import MIRROR, TURN, set_tight, sign, stamp_t, tight

FIGS = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine']

ALIASES = {0x2164: 'V', 0x2169: 'X', 0x216C: 'L', 0x216D: 'C', 0x216E: 'D', 0x216F: 'M',
           0x2174: 'v', 0x2179: 'x', 0x217C: 'l', 0x217D: 'c', 0x217E: 'd', 0x217F: 'm'}


# --- Vulgar fractions ---------------------------------------------------------

def _vulgar(name, ch, num, den):
    """num, den: lists of figure names (den may be empty: ⅟)."""
    def width(p):
        ps = small(p)
        w = len(num) * ps.fig_w + REGISTRY['fraction'].width(p) + 0.3 * p.m
        return w + (len(den) * ps.fig_w + 0.3 * p.m if den else 0.0)

    def fn(g):
        p = g.p
        ps = small(p)
        x = 0.0
        for n in num:
            g.add_glyph(draw(n, ps), x, p.cap - ps.cap)
            x += ps.fig_w
        x += 0.3 * p.m
        sl = draw('fraction', p)
        g.add_glyph(sl, x, 0.2 * p.cap)
        x += sl.W + 0.3 * p.m
        for n in den:
            g.add_glyph(draw(n, ps), x, 0)
            x += ps.fig_w
    sign(name, ch, width, kind=('punct', 0.6))(fn)


for _cp, _nm, _n, _d in ((0x2150, 'uni2150', '1', '7'), (0x2151, 'uni2151', '1', '9'), (0x2152, 'uni2152', '1', '10'),
                         (0x2153, 'onethird', '1', '3'), (0x2154, 'twothirds', '2', '3'),
                         (0x2155, 'uni2155', '1', '5'), (0x2156, 'uni2156', '2', '5'), (0x2157, 'uni2157', '3', '5'),
                         (0x2158, 'uni2158', '4', '5'), (0x2159, 'uni2159', '1', '6'), (0x215A, 'uni215A', '5', '6'),
                         (0x215B, 'oneeighth', '1', '8'), (0x215C, 'threeeighths', '3', '8'),
                         (0x215D, 'fiveeighths', '5', '8'), (0x215E, 'seveneighths', '7', '8'),
                         (0x215F, 'uni215F', '1', ''), (0x2189, 'uni2189', '0', '3')):
    _vulgar(_nm, chr(_cp), [FIGS[int(c)] for c in _n], [FIGS[int(c)] for c in _d])


# --- Roman numerals -------------------------------------------------------------

def _numeral(name, ch, letters, kind):
    def width(p):
        q = p.with_(mono=False)
        z = (0.0, q.cap if kind == 'cap' else q.xh)
        return tight(tuple(letters), q, z)[2]

    def fn(g):
        p = g.p
        set_tight(g, letters, zone=(0.0, p.cap if kind == 'cap' else p.xh))
    glyph(name, ch, width, kind=kind)(fn)


UPPER = {0x2160: 'I', 0x2161: 'II', 0x2162: 'III', 0x2163: 'IV', 0x2165: 'VI', 0x2166: 'VII', 0x2167: 'VIII',
         0x2168: 'IX', 0x216A: 'XI', 0x216B: 'XII'}
for _cp, _s in UPPER.items():
    _numeral(f'uni{_cp:04X}', chr(_cp), list(_s), 'cap')
    _numeral(f'uni{_cp + 0x10:04X}', chr(_cp + 0x10), list(_s.lower()), 'lower')


@glyph('uni2183', 'Ↄ', lambda p: REGISTRY['C'].width(p), kind='cap')
def reversedC(g):
    stamp_t(g, 'C', MIRROR, width=g.W)


@glyph('uni2184', 'ↄ', lambda p: REGISTRY['c'].width(p), kind='lower')
def reversedc(g):
    stamp_t(g, 'c', MIRROR, width=g.W)


def _ring_white(p):
    return max(p.m, 0.55 * p.sv)


def _rings_width(n):
    """n concentric rings round a stem: each side a stroke and its white."""
    return lambda p: max(letter_width(10, 2)(p) + 2 * (n - 1) * (p.sv + _ring_white(p)),
                         (2 * n + 1) * p.sv + 2 * n * _ring_white(p))


def _inner_leg(p, leg, d):
    """A bowl corner's leg for a bowl d inside another: an octagon offset
    inward by d cuts its corners 2 - sqrt2 of d shorter, so the white
    between the two runs at one width round the corner."""
    return max(leg - (2 - SQRT2) * d, p.c)


def _rings(g, n):
    """n concentric octagons and a stem through them all. Their bars thin
    (to 0.7 of the weight's) before the sign outgrows the cap height; where
    even that cannot hold every bar and its white, it grows above and below
    the cap height, about the axis."""
    p, W = g.p, g.W
    w = _ring_white(p)
    bars = 2 * n
    g.sh_k = min(1.0, max(0.7, (p.cap - (bars - 1) * w) / (bars * p.sh)))
    sh = g.sh
    H = max(p.cap, bars * sh + (bars - 1) * w)
    y0 = (p.cap - H) / 2
    for i in range(n):
        dx = i * (p.sv + w)
        dy = i * (sh + w)
        x0, x1 = dx + p.sv / 2, W - dx - p.sv / 2
        ya, yb = y0 + dy + sh / 2, y0 + H - dy - sh / 2
        leg = _inner_leg(p, p.leg, i * (p.sv + w))
        g.stroke(B(x0, ya, leg), B(x1, ya, leg), B(x1, yb, leg), B(x0, yb, leg), closed=True)
    g.stroke((W / 2, y0 + sh / 2), (W / 2, y0 + H - sh / 2))


@glyph('uni2180', 'ↀ', _rings_width(1), kind='cap')
def thousandCD(g):
    _rings(g, 1)


@glyph('uni2182', 'ↂ', _rings_width(2), kind='cap')
def tenthousand(g):
    _rings(g, 2)


@glyph('uni2188', 'ↈ', _rings_width(3), kind='cap')
def hundredthousand(g):
    _rings(g, 3)


@glyph('uni2181', 'ↁ', growing_width(9, 2, 1.5), kind='cap')
def fivethousand(g):
    """D with a stem standing inside it."""
    f = Frame(g, 9)
    p, W = f.p, f.W
    g.stroke(f.P(1, 1), B(*f.P(8, 1), p.leg + p.m), B(*f.P(8, 11), p.leg + p.m), f.P(1, 11), closed=True)
    x = f.X(1) + p.sv + _ring_white(p)
    g.stroke((x, f.Y(1)), (x, f.Y(11)))


@glyph('uni2187', 'ↇ', lambda p: letter_width(9, 2)(p) + p.sv + _ring_white(p) + 1.5 * heft(p), kind='cap')
def fiftythousand(g):
    """Two D bowls, one inside the other, on one stem."""
    f = Frame(g, 9)
    p, W = f.p, f.W
    w = _ring_white(p)
    g.sh_k = min(1.0, max(0.7, (p.cap - 2 * w - 0.6 * p.sv) / (4 * p.sh)))   # four bars, two whites, a counter
    sh = g.sh
    H = max(p.cap, 4 * sh + 2 * w + 0.6 * p.sv)              # outgrowing the cap height, about the axis
    y0 = (p.cap - H) / 2
    xs = p.sv / 2
    g.stroke((xs, y0), (xs, y0 + H))
    g.stroke((xs, y0 + sh / 2), B(W - p.sv / 2, y0 + sh / 2, p.leg + p.m),
             B(W - p.sv / 2, y0 + H - sh / 2, p.leg + p.m), (xs, y0 + H - sh / 2))
    yi0, yi1 = y0 + sh / 2 + sh + w, y0 + H - sh / 2 - sh - w
    g.clip = None
    xi = W - p.sv / 2 - p.sv - w
    leg = _inner_leg(p, p.leg + p.m, p.sv + w)
    g.stroke((xs, yi0), B(xi, yi0, leg), B(xi, yi1, leg), (xs, yi1))


@glyph('uni2185', 'ↅ', letter_width(9, 2), kind='cap')
def sixlate(g):
    """C whose foot runs on below the baseline."""
    from .figures import beak_depth
    f = Frame(g, 9)
    p, H = f.p, f.p.cap
    g.clip = (0, -p.desc, f.W, H)
    g.stroke((f.X(8), H - beak_depth(p)), B(*f.P(8, 11)), B(*f.P(1, 11)), B(*f.P(1, 1)), B(*f.P(8, 1)),
             (f.X(8), -p.desc))


def _arrow_w(p):
    from .symbols import arrow_head
    return p.sv + 2 * arrow_head(p) / SQRT2


@glyph('uni2186', 'ↆ', _arrow_w, kind='cap')
def fiftyearly(g):
    """A stem from the cap height ending on the baseline in an arrowhead."""
    from .symbols import arrow_head
    p, W = g.p, g.W
    head = arrow_head(p)
    tip = (W / 2, p.sd / 2)
    g.stroke((W / 2, p.cap), tip)
    for side in (1, -1):
        g.stroke(tip, (W / 2 + side * head / SQRT2, tip[1] + head / SQRT2))
    g.clip = (0, 0, W, p.cap)


@glyph('uni218A', '↊', 'fig_w')
def turnedtwo(g):
    stamp_t(g, 'two', TURN, width=g.W)


@glyph('uni218B', '↋', 'fig_w')
def turnedthree(g):
    stamp_t(g, 'three', TURN, width=g.W)
