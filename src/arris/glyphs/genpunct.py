"""General Punctuation (U+2010-U+205E): the rest of the block, and its spaces.

Built from what punctuation already does: dots are the period's chamfered
squares, primes the 2:1 minute stroke, ties and the close-up sign the
chamfered tray of a bowl's corner, the reversed marks mirrors of the
upright ones (``symkit.stamp_t``), the doubled marks two of the single ones
set close. Where parts hold white between them (the two bars of a double
vertical line, the dots between the arms of a reference mark, a row of
primes) the white grows with the stroke, never less than half to three
quarters of a stem, so heavy weights keep them apart.

Spaces are empty glyphs of their own width (``kind='space'``): the em and
its fractions are fixed in the em; the figure space is a tabular figure's
advance, the punctuation space a period's. In the monospaced cut every
space is a cell. The zero-width characters are empty and advance nothing.
"""
from __future__ import annotations

from shapely.geometry import Polygon

from ..draw import B, REGISTRY, draw, glyph
from ..params import SQRT2
from .letterframe import STEEP, Frame, growing_width, letter_width
from .punct import _bracket, axis, dot, dot_w, punct, stem_w
from .symkit import MIRROR, sign, stamp_t

ALIASES = {0x2015: 'emdash', 0x2024: 'period', 0x2027: 'periodcentered'}


def white(p, mod=1.0, stem=0.75):
    """White between two parts of a sign: ``mod`` modules, or ``stem``
    stems where that is more, so it grows with the stroke."""
    return max(mod * p.m, stem * p.sv)


def solid(g, pts):
    g.extra.append(Polygon(pts))


def dash_y(p):
    """The centre of the hyphen and the dashes (x-height zone, row 5)."""
    sh = p.sh
    return sh / 2 + 4 / 7 * (p.xh - sh)


# --- Dashes and lines ---------------------------------------------------------

@glyph('figuredash', '‒', 'fig_w')
def figuredash(g):
    """A dash a tabular figure wide, at the height of the case dashes, so it
    sits on the figures' middle between them (555‒0199)."""
    p = g.p
    y = dash_y(p) + (p.cap - p.xh) / 2
    g.stroke((0, y), (g.W, y))


def _double_gap(p):
    return max(1.5 * p.m, 0.75 * p.sv)


@sign('uni2016', '‖', lambda p: 2 * p.sv + _double_gap(p))
def dblverticalbar(g):
    """Two bars, never closer than three quarters of a stem."""
    p = g.p
    top, bot = p.cap + 0.5 * p.m, -p.desc + 0.5 * p.m
    for x in (p.sv / 2, g.W - p.sv / 2):
        g.stroke((x, bot), (x, top))
    g.clip = (0, bot, g.W, top)


@sign('underscoredbl', '‗', letter_width(9, 0))
def underscoredbl(g):
    """Two low lines: the lower where the underscore is, the upper a stroke
    above it; at heavy weights they thin (to 0.7) before they rise far."""
    p = g.p
    g.stack(2, p.desc + 0.5 * p.m, ratio=0.9)
    g.sh_k = max(g.sh_k, 0.7)
    sh = g.sh
    y1 = -p.desc + sh / 2
    y2 = y1 + sh + max(0.9 * sh, 0.5 * p.m)
    for y in (y1, y2):
        g.stroke((0, y), (g.W, y))


@sign('uni203E', '‾', letter_width(9, 0))
def overline(g):
    p = g.p
    y = p.asc - g.sh / 2
    g.stroke((0, y), (g.W, y))


# --- Reversed quotes and marks ------------------------------------------------

def _mirrored(name, ch, base, solid_=False):
    def fn(g, base=base):
        stamp_t(g, base, MIRROR, width=g.W)
    glyph(name, ch, lambda p, b=base: REGISTRY[b].width(p), kind=REGISTRY[base].kind, solid=solid_)(fn)


_mirrored('quotereversed', '‛', 'quoteright')
_mirrored('uni201F', '‟', 'quotedblright')
_mirrored('uni204B', '⁋', 'paragraph', solid_=True)
_mirrored('uni204F', '⁏', 'semicolon')


# --- Primes -------------------------------------------------------------------

def _prime_w(p):
    return p.ss / STEEP[1]


def _prime_pitch(p):
    """From one prime to the next (the double prime's), its white growing
    with the stroke."""
    w = _prime_w(p)
    return max(2.2 * p.m + w / 2, w + white(p, 0.5, 0.6))


def _primes_width(n):
    return lambda p: (n - 1) * _prime_pitch(p) + 2 * p.m + _prime_w(p)


def _primes(g, n, mirror=False):
    """n minute strokes at the double prime's pitch."""
    p = g.p
    w = _prime_w(p)
    pitch, run = _prime_pitch(p), 2 * p.m
    for i in range(n):
        x0 = w / 2 + i * pitch
        pts = [(x0, p.cap - 2 * run), (x0 + run, p.cap)]
        if mirror:
            pts = [(g.W - x, y) for x, y in pts]
        g.stroke(*pts, start='h', end='h')


for _nm, _ch, _n, _mir in (('uni2034', '\u2034', 3, False), ('uni2057', '\u2057', 4, False),
                           ('uni2035', '\u2035', 1, True), ('uni2036', '\u2036', 2, True),
                           ('uni2037', '\u2037', 3, True)):
    sign(_nm, _ch, _primes_width(_n))(lambda g, n=_n, m=_mir: _primes(g, n, m))


# --- Dots ---------------------------------------------------------------------

@sign('twodotenleader', '‥', dot_w(1 + 1.2))
def twodotenleader(g):
    p = g.p
    for i in range(2):
        dot(g, p.dot() / 2 + i * 2.2 * p.dot(), 0)


def _dot_pitch(p):
    """Centre to centre of dots set in a figure (the three-, four- and
    five-dot marks): a dot, and white across the diagonal between two
    neighbours never less than half a stem."""
    return p.dot() + max(0.5 * p.m, 0.55 * p.sv)


def _dots(g, pts):
    """Square dots centred on the given points."""
    s = g.p.dot()
    for x, y in pts:
        dot(g, x, y - s / 2)


def _dots_y(p, t):
    """The centre of a figure of dots t apart: the x-height's middle, or
    higher where heavy dots would hang below the baseline."""
    return max(p.xh / 2, t + p.dot() / 2)


def _grid_w(n):
    return lambda p: p.dot() + n * _dot_pitch(p)


@sign('uni2056', '\u2056', _grid_w(1))
def threedot(g):
    """One dot on the left at the middle, two on the right, top and bottom."""
    p, t, s = g.p, _dot_pitch(g.p), g.p.dot()
    yc = _dots_y(p, t)
    _dots(g, [(s / 2, yc), (s / 2 + t, yc - t), (s / 2 + t, yc + t)])


@sign('uni2058', '\u2058', _grid_w(2))
def fourdotpunct(g):
    """Four dots in a diamond about the x-height's middle."""
    p, t, s = g.p, _dot_pitch(g.p), g.p.dot()
    x, yc = s / 2 + t, _dots_y(p, t)
    _dots(g, [(x - t, yc), (x + t, yc), (x, yc - t), (x, yc + t)])


@sign('uni2059', '\u2059', _grid_w(2))
def fivedot(g):
    """Four dots in a square and one in the middle (a quincunx)."""
    p, t, s = g.p, _dot_pitch(g.p), g.p.dot()
    x, yc = s / 2 + t, _dots_y(p, t)
    _dots(g, [(x, yc)] + [(x + i * t, yc + j * t) for i in (-1, 1) for j in (-1, 1)])


@sign('uni205A', '\u205a', dot_w())
def twodotpunct(g):
    p, t, s = g.p, _dot_pitch(g.p), g.p.dot()
    yc = _dots_y(p, t)
    _dots(g, [(s / 2, yc - t), (s / 2, yc + t)])


def _mark_t(p):
    """The four dot mark's spread: half as large again as the four-dot
    punctuation's, but within the cap height."""
    return min(1.5 * _dot_pitch(p), (p.cap - p.dot()) / 2)


@sign('uni205B', '\u205b', lambda p: p.dot() + 2 * _mark_t(p))
def fourdotmark(g):
    """The four dots in a larger diamond about the axis."""
    p, t, s = g.p, _mark_t(g.p), g.p.dot()
    x, yc = s / 2 + t, axis(p)
    _dots(g, [(x - t, yc), (x + t, yc), (x, yc - t), (x, yc + t)])


@sign('uni205D', '⁝', dot_w())
def tricolon(g):
    p, s = g.p, g.p.dot()
    for i in range(3):
        dot(g, s / 2, i * (p.cap - s) / 2)


@sign('uni205E', '⁞', dot_w())
def verticalfourdots(g):
    p, s = g.p, g.p.dot()
    for i in range(4):
        dot(g, s / 2, i * (p.cap - s) / 3)


def _wedge_reach(p, s, arm):
    """How far from the centre a dot of size s sits in the wedge between two
    arms at right angles (``arm``: 'x' for diagonal arms, '+' for upright
    ones) so the white between them is at least half a stem."""
    w_min = 0.5 * p.sv
    if arm == 'x':                       # dot on the horizontal, arms at 45 degrees
        return s + SQRT2 * (p.sd / 2 + w_min)
    return s / 2 + p.sv / 2 + w_min      # dot on the diagonal, arms upright


def _refmark_dot(p):
    """The reference mark's dots: a period's at Regular and lighter,
    shrinking to 0.6 of it at Black, so four of them fit between the arms."""
    from .letterframe import heft
    return p.dot() * (1 - 0.4 * min(1.0, heft(p) / (175 - 1.5 * 60) * 60 / p.m))


def _refmark_half(p):
    s = _refmark_dot(p)
    return max(4.0 * p.m, _wedge_reach(p, s, 'x') + s / 2 + 0.5 * p.m)


@sign('uni203B', '※', lambda p: 2 * _refmark_half(p))
def referencemark(g):
    """The multiplication sign's two diagonals with a dot in each of their
    four openings, held clear of the arms by half a stem."""
    p, W = g.p, g.W
    a, h = axis(p), W / 2
    s = _refmark_dot(p)
    g.stroke((0, a - h), (W, a + h), start='v', end='v')
    g.stroke((0, a + h), (W, a - h), start='v', end='v')
    d = max(_wedge_reach(p, s, 'x'), 0.55 * h)
    for x, y in ((W / 2 - d, a), (W / 2 + d, a), (W / 2, a - d), (W / 2, a + d)):
        g.stroke((x, y - s / 2, s), (x, y + s / 2))
    g.clip = (0, a - h, W, a + h)


def _dottedcross_half(p):
    s = p.dot()
    return max(3.5 * p.m, _wedge_reach(p, s, '+') + s / 2 + 0.75 * p.m)


@sign('uni205C', '⁜', lambda p: 2 * _dottedcross_half(p))
def dottedcross(g):
    """A plus with a dot in each quarter."""
    p, W = g.p, g.W
    a, h, s = axis(p), W / 2, p.dot()
    g.stroke((0, a), (W, a))
    g.stroke((h, a - h), (h, a + h))
    d = _wedge_reach(p, s, '+')
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = h + sx * d, a + sy * d
            g.stroke((x, y - s / 2, s), (x, y + s / 2))
    g.clip = (0, a - h, W, a + h)


@sign('uni2052', '⁒', lambda p: p.ss / STEEP[1] + p.cap / 2)
def commercialminus(g):
    """The percent sign with dots for rings: a dot in the top left, the 2:1
    slash, a dot in the bottom right."""
    p, W, H = g.p, g.W, g.p.cap
    w = p.ss / STEEP[1]
    s = p.dot()
    g.stroke((w / 2, 0), (w / 2 + H / 2, H), start='h', end='h')
    dot(g, s / 2, H - s)
    dot(g, W - s / 2, 0)
    g.clip = (0, 0, W, H)


# --- Bullets ------------------------------------------------------------------

def _tri_h(p):
    return min(3.0 * p.sv, 0.8 * p.xh)


@sign('uni2023', '‣', lambda p: _tri_h(p) / 2, kind=('punct', 1.0), solid=True)
def trianglebullet(g):
    """A solid triangle pointing right: an upright side and two 45-degree
    sides meeting in a sharp point, on the x-height's middle."""
    p = g.p
    h = _tri_h(p)
    yc = p.xh / 2
    solid(g, [(0, yc - h / 2), (h / 2, yc), (0, yc + h / 2)])


@sign('uni2043', '\u2043', lambda p: max(3 * p.m, 2.4 * p.sv))
def hyphenbullet(g):
    p = g.p
    y = p.xh / 2
    g.stroke((0, y), (g.W, y))


def _half_bullet(g, left):
    """A solid octagon cut by a slot: the filled half on one side, a thin
    crescent of the outline on the other (the black left- and rightwards
    bullets)."""
    p, S = g.p, g.W
    yc = p.xh / 2
    y0, y1 = yc - S / 2, yc + S / 2
    L = 0.3 * S
    slot = max(0.6 * p.sv, 0.4 * p.m)
    rim = max(1.3 * L, p.sv * 0.75)
    x_slot = S - rim - slot                                  # the solid half ends here
    a = [(0, y0 + L), (L, y0), (x_slot, y0), (x_slot, y1), (L, y1), (0, y1 - L)]
    b = [(S - rim, y0), (S - L, y0), (S, y0 + L), (S, y1 - L), (S - L, y1), (S - rim, y1)]
    for pts in (a, b):
        if not left:
            pts = [(S - x, y) for x, y in pts][::-1]
        solid(g, pts)


def _half_w(p):
    return max(4.5 * p.m, 2.4 * p.sv + 1.2 * p.m)


@sign('uni204C', '⁌', _half_w, kind=('punct', 1.0), solid=True)
def blackleftbullet(g):
    _half_bullet(g, True)


@sign('uni204D', '⁍', _half_w, kind=('punct', 1.0), solid=True)
def blackrightbullet(g):
    _half_bullet(g, False)


# --- Asterisks ----------------------------------------------------------------

def _star_p(p):
    """A small asterisk's parameters: the small figures'."""
    from .features import small
    return small(p)


@sign('uni204E', '⁎', lambda p: REGISTRY['asterisk'].width(p))
def lowasterisk(g):
    """The asterisk lowered to stand on the baseline."""
    p = g.p
    sub = draw('asterisk', p)
    h = sub.W / 2 - p.sv / 4
    g.add_glyph(sub, 0, 2 * h - p.cap)


def _small_star(p):
    sp = _star_p(p)
    W = REGISTRY['asterisk'].width(sp)
    h = W / 2 - sp.sv / 4
    return sp, W, 2 * h


def _stars_gap(p):
    return white(p, 0.75, 0.6)


@sign('uni2051', '⁑', lambda p: _small_star(p)[1])
def twoasterisks(g):
    """Two small asterisks, one above the other, from the cap height down."""
    p = g.p
    sp, W, H = _small_star(p)
    for i in range(2):
        g.add_glyph(draw('asterisk', sp), 0, p.cap - sp.cap - i * (H + _stars_gap(p)))


@sign('uni2042', '⁂', lambda p: 2 * _small_star(p)[1] + _stars_gap(p))
def asterism(g):
    """Three small asterisks in a triangle, the top one between the two."""
    p = g.p
    sp, W, H = _small_star(p)
    gap = _stars_gap(p)
    dy = p.cap - sp.cap
    g.add_glyph(draw('asterisk', sp), (W + gap) / 2, dy)
    for x in (0, W + gap):
        g.add_glyph(draw('asterisk', sp), x, dy - H - 0.5 * gap)


@sign('uni2055', '\u2055', growing_width(9, 1, 3.0))
def flower(g):
    """Eight spokes: the asterisk's six and a level one, about the axis."""
    p, W = g.p, g.W
    h = W / 2 - p.sv / 4
    yc, xc = axis(p), W / 2
    g.stroke((xc, yc - h), (xc, yc + h))
    g.stroke((xc - h, yc), (xc + h, yc))
    d = h / SQRT2
    g.stroke((xc - d, yc - d), (xc + d, yc + d))
    g.stroke((xc - d, yc + d), (xc + d, yc - d))
    g.clip = (0, yc - h, W, yc + h)


# --- Exclamations and questions -----------------------------------------------

def _pair_gap(p):
    return white(p, 1.25, 0.75)


def _pair(a, b):
    return lambda p: REGISTRY[a].width(p) + REGISTRY[b].width(p) + _pair_gap(p)


def _pair_fn(a, b):
    def fn(g):
        p = g.p
        sub = draw(a, p)
        g.add_glyph(sub)
        g.add_glyph(draw(b, p), sub.W + _pair_gap(p))
    return fn


for _nm, _ch, _a, _b in (('exclamdbl', '‼', 'exclam', 'exclam'), ('uni2047', '⁇', 'question', 'question'),
                         ('uni2048', '⁈', 'question', 'exclam'), ('uni2049', '⁉', 'exclam', 'question')):
    sign(_nm, _ch, _pair(_a, _b))(_pair_fn(_a, _b))


@sign('uni203D', '‽', letter_width(9, 2))
def interrobang(g):
    """The question mark with the exclamation's stroke down its middle: the
    stem runs on up to the top bar."""
    REGISTRY['question'].fn(g)
    f = Frame(g, 9, 'cap')
    xs = f.X(4)
    g.stroke((xs, g.p.cap), (xs, f.Y(6)))


# --- Carets -------------------------------------------------------------------

def _caret(g, W, foot):
    """A 45-degree gable W wide, its feet at ``foot`` (the circumflex's)."""
    p = g.p
    h = W / 2
    g.stroke((0, foot), (W / 2, foot + h), (W, foot), start='v', end='v')
    return h


@sign('uni2038', '‸', letter_width(6, 1))
def caret(g):
    """The caret: a gable hanging below the baseline, its point just above."""
    p = g.p
    k = p.sd / SQRT2
    foot = -0.5 * p.desc
    h = _caret(g, g.W, foot)
    g.clip = (0, foot - p.sv, g.W, foot + h + k)


@sign('uni2041', '⁁', letter_width(7, 1))
def caretinsertion(g):
    """A long 45-degree stroke rising to the right, a short one leaving its
    middle down to the baseline: the caret with one arm drawn on."""
    p, W = g.p, g.W
    bot = -0.5 * p.desc
    g.stroke((0, bot), (W, bot + W), start='h', end='h')
    g.stroke((W / 2, bot + W / 2), (W, bot), start='flat', end='h')
    g.clip = (0, bot, W, bot + W)


# --- Brackets with quills -------------------------------------------------------

def _quill(g, mirror):
    p, W = g.p, g.W
    _bracket(g, mirror)
    mid = (p.cap + 0.5 * p.m + (-p.desc + 0.5 * p.m)) / 2
    x0, x1 = p.sv / 2, 0.65 * W
    if mirror:
        x0, x1 = W - x0, W - x1
    g.stroke((x0, mid), (x1, mid))


@sign('uni2045', '⁅', letter_width(5, 1))
def bracketleftquill(g):
    _quill(g, False)


@sign('uni2046', '⁆', letter_width(5, 1))
def bracketrightquill(g):
    _quill(g, True)


# --- Ties and the close-up sign -------------------------------------------------

def _tray(g, y_bar, up, x0=None, x1=None):
    """A shallow chamfered tray (half of a bowl): its bar at y_bar, its sides
    two modules up (``up``) or down from it."""
    p = g.p
    x0 = p.sv / 2 if x0 is None else x0
    x1 = g.W - p.sv / 2 if x1 is None else x1
    d = (1.5 * p.m + g.sh / 2) * (1 if up else -1)
    leg = 0.75 * p.m
    g.stroke((x0, y_bar + d), B(x0, y_bar, leg), B(x1, y_bar, leg), (x1, y_bar + d))


@sign('uni203F', '‿', letter_width(10, 2))
def undertie(g):
    p = g.p
    _tray(g, -p.desc + g.sh / 2, True)


@sign('uni2040', '⁀', letter_width(10, 2))
def chartie(g):
    p = g.p
    _tray(g, p.asc - g.sh / 2, False)


@sign('uni2054', '⁔', letter_width(10, 2))
def invertedundertie(g):
    p = g.p
    _tray(g, -p.desc + 1.5 * p.m + g.sh / 2, False)


@sign('uni2050', '⁐', letter_width(8, 2))
def closeup(g):
    """A tray turned down on the cap height over one turned up on the
    baseline."""
    p = g.p
    _tray(g, p.cap - g.sh / 2, False)
    _tray(g, g.sh / 2, True)


# --- Swung dash, Tironian et ------------------------------------------------------

@sign('uni2053', '⁓', letter_width(12, 1))
def swungdash(g):
    """The tilde's step drawn long: up at 45 degrees, along, down, along, up."""
    p, W = g.p, g.W
    y = dash_y(p)
    r = max(1.5 * p.m, 0.75 * p.sv)
    f = (W - 3 * r) / 2
    lo, hi = y - r / 2, y + r / 2
    g.stroke((0, lo), (r, hi), (r + f, hi), (2 * r + f, lo), (2 * r + 2 * f, lo), (W, hi), start='v', end='v')


@glyph('uni204A', '⁊', letter_width(7, 1), kind='lower')
def tironianet(g):
    """A bar on the x-height and a stem down from near its right end: the
    seven drawn upright."""
    f = Frame(g, 7, 'lower')
    g.stroke(f.P(0, 8), f.P(7, 8))
    g.stroke(f.P(5, 8), f.P(5, 0))


# --- Per ten thousand -----------------------------------------------------------

def _ring_gap(p):
    return white(p, 1.0, 0.6)


def _ring_w(p):
    return 4.5 * p.m + p.sv


@sign('uni2031', '‱', lambda p: REGISTRY['percent'].width(p) + 2 * (_ring_w(p) + _ring_gap(p)),
       kind=('punct', 1.0))
def pertenthousand(g):
    """The per mille sign with one more ring."""
    from .punct import _ring
    p = g.p
    sub = draw('percent', p)
    w = sub.W
    g.add_glyph(sub)
    s, rw, rh = p.sv, _ring_w(p), 5.0 * p.m + p.sv
    for i in range(2):
        x0 = w + _ring_gap(p) + i * (rw + _ring_gap(p))
        _ring(g, x0 + s / 2, g.sh / 2, x0 + rw - s / 2, rh - g.sh / 2)


# --- Spaces -------------------------------------------------------------------------

EM = 1000.0


def _space(name, ch, width):
    glyph(name, ch, width, kind='space')(lambda g: None)


for _cp, _w in ((0x2000, EM / 2), (0x2001, EM), (0x2002, EM / 2), (0x2003, EM), (0x2004, EM / 3),
                (0x2005, EM / 4), (0x2006, EM / 6), (0x2009, EM / 5), (0x200A, EM / 10), (0x202F, EM / 5),
                (0x205F, 4 * EM / 18), (0x200B, 0.0), (0x200C, 0.0), (0x200D, 0.0), (0x2060, 0.0)):
    _space(f'uni{_cp:04X}', chr(_cp), lambda p, w=_w: w)

_space('uni2007', ' ', lambda p: p.fig_adv)


def _period_advance(p):
    from ..font import place
    return place('period', p.with_(mono=False))[1]


_space('uni2008', ' ', _period_advance)


# --- Case forms ---------------------------------------------------------------------

# Raised for capitals as the features module raises the dashes, bullets and
# brackets (features._case_shift): bullets and dashes to the capitals'
# middle, brackets by half the descender.
CASE = {'uni2023': 'mid', 'uni2043': 'mid', 'uni2053': 'mid', 'uni2045': 'bracket', 'uni2046': 'bracket'}


def _case(name, how):
    spec = REGISTRY[name]

    def fn(g):
        p = g.p
        dy = p.desc / 2 - 0.25 * p.m if how == 'bracket' else (p.cap - p.xh) / 2
        g.add_glyph(draw(name, p), 0, dy)
    glyph(f'{name}.case', None, spec.width, kind=spec.kind, solid=spec.solid)(fn)


def register_case():
    """The case forms, and their rules in the ``case`` feature (called once
    the features module, which holds the rules, is loaded)."""
    from .features import MORE
    for n, how in CASE.items():
        _case(n, how)
        MORE.setdefault('case', []).append((n, f'{n}.case'))
