"""Latin beyond Extended-A: Vietnamese, pinyin, Latin Extended-B and
Additional, and the combining marks.

New marks, in the marks' language (``marks``):

* **dot below**: the dot, hung a gap under the baseline; like the comma
  below it keeps inside the descender, lightening at heavy weights;
* **hook above**: the 7 in small, a bar and a diagonal back to the middle
  (the watch's 7 is the one figure with a straight diagonal);
* **horn**: a stroke leaving the letter's top-right corner square to its
  chamfer, at 45 degrees, then rising: the 1's flag turned outward;
* ring below, macron below, dieresis below, double grave and inverted
  breve: the ring, macron, dieresis, grave and breve, hung below or turned.

Vietnamese stacks a tone mark on the circumflex beside it, at its upper
right; the breve carries it on top (``marks.BESIDE``). Accented letters
are composed by ``marks.compose``; a stack that would rise past the line
lightens and shrinks as heavy faces draw their accents.

New letters: the schwa (the e turned), the turned E, the florin (the
italic f's descending stem, upright), the ezh (the sharp s's top bar and
return without its stem), G with stroke, the click letters, the
compatibility digraphs (DŽ, LJ, NJ, DZ) and the dong sign.

Combining marks are glyphs of their own, of no advance, placed on their
base by mark positioning (``arris.anchors``); capitals take flatter
``.case`` forms.
"""
from __future__ import annotations

import math

from ..draw import B, REGISTRY, Glyph, glyph
from ..params import SQRT2
from . import marks
from .cyrillic import mirror
from .extra_latin import stamp, width_of
from .figures import beak_depth
from .letterframe import Frame, growing_width, letter_width, white_scale
from .marks import ABOVE, ATTACHED, BELOW, BESIDE, gap, size

# --- Marks below --------------------------------------------------------------


def room_below(p):
    """The depth a mark below may take: from a gap under the baseline to a
    little past the descender (as far as its chamfer), as the comma below."""
    return 1.15 * p.desc - gap(p)


def below_dot(p):
    """A dot below: the dot, smaller only where the descender has no room."""
    return min(p.dot(), room_below(p))


def dotbelow(g, x, y, case):
    p = g.p
    s = below_dot(p)
    g.stroke((x, -gap(p) - s, s), (x, -gap(p)))


def dieresisbelow(g, x, y, case):
    p = g.p
    s = below_dot(p)
    d = s + max(1.2 * p.m, 0.8 * s)
    for xd in (x - d / 2, x + d / 2):
        g.stroke((xd, -gap(p) - s, s), (xd, -gap(p)))


def macronbelow(g, x, y, case):
    p = g.p
    w = size(p, case)
    t = min(g.sh, room_below(p))
    g.stroke((x - w, -gap(p) - t / 2, t), (x + w, -gap(p) - t / 2))


def ringbelow(g, x, y, case):
    """A small chamfered ring under the baseline; it keeps within the
    descender by lightening (its counter about a stroke and a fifth)."""
    p = g.p
    t0 = min(p.sv, 1.5 * p.m)
    H = min(room_below(p), 1.2 * p.m + 2 * t0)
    t = min(t0, H / 3.2)
    r = (H - t) / 2                                         # centreline half-size
    yc = -gap(p) - H / 2
    leg = min(p.m / 2, r / 2)
    g.stroke(B(x - r, yc - r, leg, t), B(x + r, yc - r, leg, t), B(x + r, yc + r, leg, t),
             B(x - r, yc + r, leg, t), closed=True)


# --- Marks above --------------------------------------------------------------


def hookabove(g, x, y, case):
    """The hook above: the 7 in small. A bar, and from its right end a
    diagonal at the 7's 2:1 back down to the middle, cut flat. Its strokes
    lighten at heavy weights as the breve's sides do, so the angle between
    bar and diagonal stays open."""
    p = g.p
    h = size(p, case)
    t = min(p.sv, max(h - gap(p), p.floor) * 0.8)
    sh = min(g.sh, t)
    yt = y + h - sh / 2                                     # the bar's centreline
    run = (yt - y) / 2                                      # 2:1: across half the drop
    xr = x + run
    xl = x - run - t / 2                                    # the bar as far left as the diagonal reaches right
    g.stroke((xl, yt, sh), (xr, yt, t * p.ss / p.sv), (x, y), end='h')


def doublegrave(g, x, y, case):
    p = g.p
    d = 2 * p.sd / SQRT2 + max(0.6 * p.m, 0.4 * p.sv)
    marks.grave(g, x - d / 2, y, case)
    marks.grave(g, x + d / 2, y, case)


def invertedbreve(g, x, y, case):
    """The breve turned over: a small chamfered arch, its sides thin as the
    breve's."""
    p = g.p
    w = size(p, case)
    h = 0.75 * w
    t = min(p.sv, w - gap(p))
    xl, xr = x - w + t / 2, x + w - t / 2
    g.stroke((xl, y, t), B(xl, y + h, p.m / 2), B(xr, y + h, p.m / 2, t), (xr, y))


# --- The horn ------------------------------------------------------------------


def horn_anchor(ink):
    """Where a horn leaves a letter: its top-right extreme along the
    diagonal (the middle of the chamfer of an O's corner, the cut corner of
    a U's stem)."""
    pts = [q for poly in getattr(ink, 'geoms', [ink]) for q in poly.exterior.coords]
    best = max(x + y for x, y in pts)
    near = [(x, y) for x, y in pts if x + y > best - 0.5]
    return (sum(x for x, _ in near) / len(near), sum(y for _, y in near) / len(near))


def horn_rise(p, case):
    """How far the horn's top stands above where it leaves the letter."""
    return (2.25 if case == 'lc' else 2.0) * p.m + 0.75 * p.sv


def horn_reach(p):
    """How far the horn runs out along its diagonal before it rises."""
    return 1.0 * p.m * white_scale(p) + p.sv / 2


def horn_at(g, ax, ay, case):
    """A horn leaving (ax, ay): a 45-degree stroke square to the corner's
    chamfer, starting inside the letter, then rising, cut flat on top."""
    p = g.p
    k = p.sd / 2                                            # half the diagonal, across
    u = 1 / SQRT2
    x0, y0 = ax - k * u, ay - k * u                         # buried in the letter's corner
    reach = horn_reach(p)
    x1, y1 = ax + reach * u, ay + reach * u
    top = ay + horn_rise(p, case)
    g.stroke((x0, y0), (x1, y1), (x1, max(top, y1 + p.c)), end='h')


def horn(g, x, case):
    horn_at(g, *horn_anchor(g.extra[0]), case)


def horn_room(p):
    """How far a horn reaches right of the letter it leaves."""
    return horn_reach(p) / SQRT2 + p.sv / 2 + p.c


horn.room = horn_room

ABOVE.update({'̉': hookabove, '̏': doublegrave, '̑': invertedbreve})
BELOW.update({'̣': dotbelow, '̤': dieresisbelow, '̥': ringbelow, '̱': macronbelow})
ATTACHED['̛'] = horn
# Vietnamese: acute, grave and hook stand at the circumflex's upper right
BESIDE.update(('̂', m) for m in ('́', '̀', '̉'))


# --- New letters ---------------------------------------------------------------


def turn(g, H):
    """Turn the drawn strokes half round within the body (W wide, H tall)."""
    W = g.W
    g.strokes = [type(s)(tuple(type(n)(W - n.x, H - n.y, n.bowl, n.w) for n in s.nodes), s.closed, s.start, s.end)
                 for s in g.strokes]


@glyph('uni0259', 'ə', lambda p: REGISTRY['e'].width(p), kind='lower',
       openings=REGISTRY['e'].openings)
def schwa(g):
    """The e turned: its eye below, its mouth at the top left."""
    REGISTRY['e'].fn(g)
    turn(g, g.p.xh)


@glyph('uni01DD', 'ǝ', lambda p: REGISTRY['e'].width(p), kind='lower',
       openings=REGISTRY['e'].openings)
def turned_e(g):
    schwa(g)


def _Schwa_gap(g):
    return g.defaults_used['arm'] - g.defaults_used['bar'] - g.sh


@glyph('uni018F', 'Ə', letter_width(9, 2), kind='cap')
def Schwa(g):
    """The capital schwa: the turned e on the capital grid, its bar a
    little above the middle."""
    f = Frame(g, 9)
    yb = f.Y(6.5)
    g.stroke((f.X(8), yb), (f.X(1), yb), B(*f.P(1, 1)), B(*f.P(8, 1)), closed=True)
    g.stroke((f.X(8), yb), B(*f.P(8, 11)), f.P(1, 11))


@glyph('uni018E', 'Ǝ', letter_width(8, 1), kind='cap')
def Eturned(g):
    """The turned E: the E mirrored."""
    REGISTRY['E'].fn(g)
    mirror(g)


@glyph('florin', 'ƒ', letter_width(7, 1), kind='lower')
def florin(g):
    """The italic f's stem, upright: a hook at the top, the stem running
    on below the baseline and turning back."""
    if g.p.mono:
        f = Frame(g, 9, 'asc')
        g.stroke(f.P(9, 12), B(*f.P(4.5, 12)), B(*f.P(4.5, -2)), f.P(0, -2))
        g.stroke(f.P(1, 8), f.P(8, 8))
        return
    f = Frame(g, 7, 'asc')
    g.stroke(f.P(7, 12), B(*f.P(3.5, 12)), B(*f.P(3.5, -2)), f.P(0, -2))
    g.stroke(f.P(0.5, 8), f.P(6.5, 8))


@glyph('uni01B7', 'Ʒ', letter_width(9, 2), kind='cap')
def Ezh(g):
    """The sharp s's top bar and 45-degree return without its stem: a bar,
    a diagonal back to the middle, the 3's lower bowl ending on a beak."""
    f = Frame(g, 9)
    p = f.p
    x8 = f.X(8)
    y_mid = f.Y(11) - (x8 - f.X(4.5))
    g.stroke(f.P(1, 11), (x8, f.Y(11)))
    g.stroke((x8, f.Y(11)), (f.X(4.5), y_mid))
    g.stroke((f.X(4.5), y_mid), B(x8, y_mid), B(*f.P(8, 1)), B(*f.P(1, 1)), (f.X(1), beak_depth(p)))


@glyph('uni0292', 'ʒ', letter_width(8, 2), kind='lower')
def ezh(g):
    """The ezh on the x-height, its bowl hanging into the descender."""
    f = Frame(g, 8, 'lower')
    p = f.p
    x7 = f.X(7)
    y_mid = f.Y(8) - (x7 - f.X(4))
    g.stroke(f.P(1, 8), (x7, f.Y(8)))
    g.stroke((x7, f.Y(8)), (f.X(4), y_mid))
    g.stroke((f.X(4), y_mid), B(x7, y_mid), B(*f.P(7, -2)), B(*f.P(1, -2)), (f.X(1), -p.desc + beak_depth(p)))


@glyph('uni01E4', 'Ǥ', width_of('G', 1.5), kind='cap')
def Gstroke(g):
    """G with a bar across its right side, below its own bar."""
    p = g.p
    w = stamp(g, 'G', width=g.W - 1.5 * p.m)
    xs = w - p.sv / 2
    g.stroke((xs - 1.5 * p.m - p.sv / 2, 0.27 * p.cap), (xs + 1.5 * p.m + p.sv / 2, 0.27 * p.cap))


@glyph('uni01E5', 'ǥ', width_of('g', 1.5), kind='lower')
def gstroke(g):
    """g with a bar across its descender's stem."""
    p = g.p
    w = stamp(g, 'g', width=g.W - 1.5 * p.m)
    xs = w - p.sv / 2
    y = -0.4 * p.desc + g.sh / 2
    g.stroke((xs - 1.5 * p.m - p.sv / 2, y), (xs + 1.5 * p.m + p.sv / 2, y))
    g.clip = None


# --- Click letters ------------------------------------------------------------

def _click_span(p):
    return -p.desc + 0.5 * p.m, p.cap + 0.5 * p.m           # the bar's (|)


@glyph('uni01C0', 'ǀ', lambda p: p.sv, kind='lower')
def click_dental(g):
    p = g.p
    bot, top = _click_span(p)
    g.stroke((g.W / 2, bot), (g.W / 2, top))


@glyph('uni01C1', 'ǁ', growing_width(6, 2, 1.0), kind='lower')
def click_lateral(g):
    p = g.p
    bot, top = _click_span(p)
    for x in (p.sv / 2, g.W - p.sv / 2) if not p.mono else (g.W / 2 - 1.5 * p.m, g.W / 2 + 1.5 * p.m):
        g.stroke((x, bot), (x, top))


@glyph('uni01C2', 'ǂ', growing_width(8, 1, 1.0), kind='lower')
def click_alveolar(g):
    """The dental click crossed by two bars, as the equals sign's."""
    p = g.p
    bot, top = _click_span(p)
    g.stroke((g.W / 2, bot), (g.W / 2, top))
    a = (bot + top) / 2
    off = (g.sh + max(0.8 * g.sh, p.m)) / 2
    for y in (a - off, a + off):
        g.stroke((0, y), (g.W, y))


@glyph('uni01C3', 'ǃ', lambda p: p.dot(), kind='cap')
def click_retroflex(g):
    REGISTRY['exclam'].fn(g)


# --- Digraphs (compatibility letters) -------------------------------------------

def _digraph(name, ch, a, b, kind):
    def width(p, a=a, b=b):
        return REGISTRY[a].width(p) + REGISTRY[b].width(p) + 2.5 * p.m

    def fn(g, a=a, b=b):
        p = g.p
        gp = (0.75 if p.mono else 2.5) * p.m
        wa = (g.W - gp) / 2 if p.mono else None
        w = stamp(g, a, width=wa)
        stamp(g, b, w + gp, width=(g.W - w - gp) if p.mono else None, clear=True)
    glyph(name, ch, width, kind=kind)(fn)


for _cp, _a, _b, _k in ((0x01C4, 'D', 'Zcaron', 'cap'), (0x01C5, 'D', 'zcaron', 'cap'),
                        (0x01C6, 'd', 'zcaron', 'lower'), (0x01C7, 'L', 'J', 'cap'), (0x01C8, 'L', 'j', 'cap'),
                        (0x01C9, 'l', 'j', 'lower'), (0x01CA, 'N', 'J', 'cap'), (0x01CB, 'N', 'j', 'cap'),
                        (0x01CC, 'n', 'j', 'lower'), (0x01F1, 'D', 'Z', 'cap'), (0x01F2, 'D', 'z', 'cap'),
                        (0x01F3, 'd', 'z', 'lower')):
    _digraph(f'uni{_cp:04X}', chr(_cp), _a, _b, _k)


@glyph('dong', '₫', lambda p: REGISTRY['dcroat'].width(p), kind='lower')
def dong(g):
    """The dong: the barred d, underlined a gap below the baseline."""
    p = g.p
    w = stamp(g, 'dcroat', width=g.W)
    t = min(g.sh, room_below(p))
    y = -gap(p) - t / 2
    g.stroke((0, y, t), (w, y))


# --- Accented letters ---------------------------------------------------------------

CHARS = [chr(c) for c in (
    # Vietnamese: the horn letters and every vowel with its tone marks
    [0x01A0, 0x01A1, 0x01AF, 0x01B0] + list(range(0x1EA0, 0x1EFA))
    # pinyin: the caron vowels and u with dieresis and a tone; n with grave, m with acute
    + list(range(0x01CD, 0x01DD)) + [0x01F8, 0x01F9, 0x1E3E, 0x1E3F]
    # Latin Extended-B: Livonian, Skolt Sami, Azerbaijani, Danish, Macedonian transliteration
    + list(range(0x01DE, 0x01F1)) + [0x01F4, 0x01F5] + list(range(0x01FA, 0x0218)) + list(range(0x0226, 0x0234))
    # Latin Extended Additional: Irish dotted letters, Welsh w and y, transliteration's dots below
    + [0x1E02, 0x1E03, 0x1E0A, 0x1E0B, 0x1E1E, 0x1E1F, 0x1E40, 0x1E41, 0x1E56, 0x1E57, 0x1E60, 0x1E61,
       0x1E6A, 0x1E6B, 0x1E80, 0x1E81, 0x1E82, 0x1E83, 0x1E84, 0x1E85, 0x1E44, 0x1E45, 0x1E92, 0x1E93,
       0x1E24, 0x1E25, 0x1E62, 0x1E63, 0x1E6C, 0x1E6D, 0x1E0C, 0x1E0D])]

BASES = {chr(spec.unicode): name for name, spec in REGISTRY.items() if spec.unicode}
ACCENTED = marks.compose(CHARS, BASES)


# --- Combining marks -----------------------------------------------------------------

# code point -> (glyph name, where it goes: 'top', 'bottom', 'ogonek', 'horn')
COMBINING = {}
for _cp in (0x0300, 0x0301, 0x0302, 0x0303, 0x0304, 0x0306, 0x0307, 0x0308, 0x0309, 0x030A, 0x030B, 0x030C,
            0x030F, 0x0311, 0x031B, 0x0323, 0x0324, 0x0325, 0x0326, 0x0327, 0x0328, 0x0331):
    _m = chr(_cp)
    _where = 'top' if _m in ABOVE else 'horn' if _m in ATTACHED else 'ogonek' if _cp == 0x0328 else 'bottom'
    COMBINING[_cp] = (marks._name(_m), _where)


def mark_width(p):
    return 2 * size(p, 'lc') + 1.5 * p.sv


def ogonek_mark(g, x):
    """The ogonek alone: from a foot at x on the baseline, turning right underneath."""
    p = g.p
    yb = -p.desc + g.sh / 2 + 0.25 * p.m
    g.stroke((x, g.sh / 2), B(x, yb, p.m / 2), (x + 1.5 * p.m + p.sv / 2, yb))


def horn_origin(p, case):
    """Where the combining horn's drawing leaves its base, in its body."""
    return (0.0, p.cap if case == 'uc' else p.xh)


def _combining(name, cp, seq, where, case):
    """A combining mark's glyph: ``seq`` the marks it draws (two for the
    Vietnamese pairs, which stand beside each other as in the composed
    letters), over the x-height or, ``.case``, the cap height."""
    def fn(g, seq=seq, where=where, case=case):
        p = g.p
        x = g.W / 2
        if where == 'top':
            top = p.cap if case == 'uc' else p.xh
            for m, xm, ym in marks.stack_above(p, seq, x, top, case, g.W)[0]:
                ABOVE[m](g, xm, ym, case)
        elif where == 'horn':
            ax, ay = horn_origin(p, case)
            horn_at(g, x + ax, ay, case)
        elif where == 'ogonek':
            ogonek_mark(g, x)
        else:
            BELOW[seq[0]](g, x, 0, case)
    glyph(name, chr(cp) if cp else None, mark_width, kind='mark')(fn)
    MARKS[name] = (where, case, seq)


# every mark glyph: name -> (where, case, the marks it draws)
MARKS: dict = {}
for _cp, (_name, _where) in COMBINING.items():
    _combining(_name, _cp, (chr(_cp),), _where, 'lc')
    if _where == 'top':
        _combining(f'{_name}.case', None, (chr(_cp),), _where, 'uc')

# The Vietnamese pairs, for a circumflex and a tone mark that meet as
# combining marks (``ccmp`` joins them): beside each other, as composed.
PAIRS = {}
for _a, _b in sorted(BESIDE):
    _name = f'uni{ord(_a):04X}{ord(_b):04X}'
    PAIRS[(COMBINING[ord(_a)][0], COMBINING[ord(_b)][0])] = _name
    _combining(_name, None, (_a, _b), 'top', 'lc')
    _combining(f'{_name}.case', None, (_a, _b), 'top', 'uc')


@glyph('uni25CC', '\u25cc', lambda p: p.xh, kind=('punct', 1.0))
def dottedcircle(g):
    """The dotted circle, on which marks are shown alone: twelve dots on a
    circle an x-height across; the dots three quarters of the stem's
    square, but never more than half the distance between them, so the
    white between them stays as wide as they are."""
    p = g.p
    n = 12
    chord = 2 * math.sin(math.pi / n)                       # between neighbours, of the radius
    R0 = p.xh / 2
    s = min(max(0.75 * p.dot(), 2 * p.floor), 0.5 * chord * R0)
    R = (min(g.W, p.xh) - s) / 2
    xc, yc = g.W / 2, p.xh / 2
    for i in range(n):
        a = i * 2 * math.pi / n
        x, y = xc + R * math.cos(a), yc + R * math.sin(a)
        g.stroke((x, y - s / 2, s), (x, y + s / 2))
    g.clip = None
