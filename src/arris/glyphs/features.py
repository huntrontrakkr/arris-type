"""Alternate figures, small figures, case forms, and the OpenType features
that reach them.

* Figures are proportional in Arris, spaced by their own white as the
  letters are and kerned (``draw.PROPORTIONAL_FIGS``); ``tnum`` gives the
  watch's tabular ones, the same drawings on one cell (``pnum`` back).
  Until 1.017 the tabular set was the default: on its ten-module cell the
  figures stood a third of the white between two stems apart and the 1
  two whole ones from its neighbours (1,110). In Arris Mono every figure
  is on the cell either way.
* ``calt`` turns a colon between figures into the time colon: two
  stem-square dots centred on the figures; between tabular figures the
  watch's, in a tighter slot.
* ``zero``: a slashed zero, the slash square to the bowl's corners; ``ss01``:
  a dotted zero.
* Small figures (superiors, inferiors, numerators, denominators) are drawn
  at small size, not scaled: a smaller module and cap height with strokes
  only a little lighter, so they keep their colour beside full figures.
* ``case`` raises dashes, guillemets and centred marks to the capitals.
"""
from __future__ import annotations

from shapely import affinity

from ..draw import PROPORTIONAL_FIGS, REGISTRY, draw, glyph
from ..geom import rings_to_shapely
from ..params import SQRT2
from .letterframe import STEEP

FIGS = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine']
SUPS = '⁰¹²³⁴⁵⁶⁷⁸⁹'
SUBS = ''.join(chr(0x2080 + i) for i in range(10))
SMALL = 0.62       # small figures' size, of the cap height
SMALL_STROKE = 0.8  # their strokes, of the full stems


def small(p):
    from .figures import heaviness
    from .symkit import SMALL_HEFT
    # strokes a little lighter than the figures' (0.8); toward Black, lighter
    # still (0.68), so a small figure's strokes stay in proportion to its
    # size; and, as small letters' (symkit.small_letter), never heavier than
    # SMALL_HEFT of its own module, or the 8's counters close to pinholes
    k = SMALL
    s = min(SMALL_STROKE - 0.12 * heaviness(p), SMALL_HEFT * k * p.m / p.sv)
    return p.with_(m=k * p.m, cap=k * p.cap, fig_w=k * p.fig_w, fig_adv=k * p.fig_adv, leg=k * p.leg,
                   sv=s * p.sv, sh=s * p.sh, sd=s * p.sd, ss=s * p.ss, c=s * p.c)


def _stamp_small(g, name, dy):
    ps = small(g.p)
    sub = draw(name, ps)
    g.add_glyph(sub, 0, dy)


def _register_small(suffix, chars, dy_of):
    for i, n in enumerate(FIGS):
        ch = chars[i] if chars else None

        def fn(g, n=n):
            _stamp_small(g, n, dy_of(g.p))
        glyph(f'{n}.{suffix}', ch, lambda p: small(p).fig_w, kind=('punct', 0.55))(fn)


_INFERIOR_FLOOR: dict = {}


def inferior_dy(p):
    """The inferiors' baseline (the figures' and supsubs' letters and
    signs, one line for all, so H₂O and xₚ set together): hanging 0.22 of
    the cap height below the baseline; in Mono no lower than keeps the
    deepest of them, the small p's descender (ₚ), inside the line box, a
    terminal's cell (font.Metrics' descent, two units in, as
    marks.line_top keeps the top)."""
    dy = -0.22 * p.cap
    if p.mono:
        from ..font import Metrics
        from .symkit import small_all
        if p not in _INFERIOR_FLOOR:
            ys = [y for r in draw('p', small_all(p)).rings() for _, y in r]
            m = Metrics()
            _INFERIOR_FLOOR[p] = (m.desc + 2) * p.cap / m.cap - min(ys)
        dy = max(dy, _INFERIOR_FLOOR[p])
    return dy


# superiors: tops on the cap height; inferiors: hanging below the baseline;
# numerators: tops on the cap height; denominators: on the baseline.
_register_small('sups', SUPS, lambda p: p.cap - small(p).cap)
_register_small('subs', SUBS, inferior_dy)
_register_small('numr', None, lambda p: p.cap - small(p).cap)
_register_small('dnom', None, lambda p: 0.0)


# --- Zeros ---------------------------------------------------------------

@glyph('zero.zero', None, 'fig_w')
def zero_slash(g):
    p0 = g.p
    g.p = p0.with_(mono=False)
    REGISTRY['zero'].fn(g)
    g.p = p0
    p, W, H = g.p, g.W, g.p.cap
    # a 45-degree slash across the counter, wall to wall
    a = (W - 2 * p.sv) / 2 + p.sv / 2
    g.stroke((W / 2 - a, H / 2 - a), (W / 2 + a, H / 2 + a), start='v', end='v')


@glyph('zero.dot', None, 'fig_w')
def zero_dot(g):
    REGISTRY['zero'].fn(g)
    p, W, H = g.p, g.W, g.p.cap
    if not p.mono:                                          # (Mono's zero is dotted already)
        from .figures import zero_dot
        zero_dot(g)


# --- Tabular figures -----------------------------------------------------

def _tabular(n):
    """n.tnum: the figure n as it is drawn, on the figures' cell."""
    def fn(g, n=n):
        g.add_glyph(draw(n, g.p, width=g.W))
    glyph(f'{n}.tnum', None, REGISTRY[n].width)(fn)


for n in PROPORTIONAL_FIGS:
    _tabular(n)


# --- The time colon ------------------------------------------------------

def _figure_side(p):
    return (p.fig_adv - p.fig_w) / 2


@glyph('colon.tf', None, lambda p: p.dot(), kind=('punct', _figure_side))
def colon_tf(g):
    """The watch clock's colon: dots centred a sixth of a module above the
    figures' middle, their centres five modules apart, with a figure's
    sidebearing each side, so the white beside the dots is the white
    between two figures (on the watch, 3 pixels each side of the colon
    and between the figures alike)."""
    p = g.p
    s = p.dot()
    yc = p.cap / 2 + p.cap / 72
    half = 2.5 * p.cap / 12
    for y in (yc - half, yc + half):
        g.stroke((s / 2, y - s / 2, s), (s / 2, y + s / 2))


# --- Fraction slash and precomposed fractions ------------------------------

def _fraction_width(p):
    return p.ss / STEEP[1] + 0.3 * p.cap


@glyph('fraction', '\u2044', _fraction_width, kind=('punct', 0.2))
def fraction(g):
    """The fraction slash: the 2:1 slash, the height of a numerator and a half."""
    p = g.p
    w = p.ss / STEEP[1]
    g.stroke((w / 2, 0), (w / 2 + 0.3 * p.cap, 0.6 * p.cap), start='h', end='h')


def _fraction(name, ch, num, den):
    def fn(g):
        p = g.p
        ps = small(p)
        x = 0.0
        a = draw(f'{num}', ps)
        g.add_glyph(a, x, p.cap - ps.cap)
        x += ps.fig_w + 0.3 * p.m
        sl = draw('fraction', p)
        g.add_glyph(sl, x, 0.2 * p.cap)
        x += sl.W + 0.3 * p.m
        b = draw(f'{den}', ps)
        g.add_glyph(b, x, 0)

    def width(p):
        ps = small(p)
        return 2 * ps.fig_w + REGISTRY['fraction'].width(p) + 0.6 * p.m
    from .symkit import sign                # (condensed into the monospaced cell, as ⅓ ⅛ are)
    sign(name, ch, width, kind=('punct', 0.6))(fn)


_fraction('onehalf', '½', 'one', 'two')
_fraction('onequarter', '¼', 'one', 'four')
_fraction('threequarters', '¾', 'three', 'four')


# --- Ordinals ------------------------------------------------------------

def _ordinal(name, ch, letter):
    def fn(g):
        p = g.p
        ps = small(p).with_(xh=SMALL * p.xh, asc=SMALL * p.asc, desc=SMALL * p.under, under=SMALL * p.under, deep=SMALL * p.deep)
        sub = draw(letter, ps)
        dy = p.cap - ps.xh
        g.add_glyph(sub, 0, dy)
        gap = max(0.6 * p.m, 0.75 * ps.sv)                  # white over the rule: never under the small stroke's
        y = dy - gap - ps.sh / 2
        g.stroke((0, y), (sub.W, y))
        g.sh_k = SMALL_STROKE
    glyph(name, ch, lambda p: REGISTRY[letter].width(small(p).with_(xh=SMALL * p.xh)), kind=('punct', 0.6))(fn)


_ordinal('ordfeminine', 'ª', 'a')
_ordinal('ordmasculine', 'º', 'o')


# --- Case forms ----------------------------------------------------------

CASE = ['hyphen', 'endash', 'emdash', 'guilsinglleft', 'guilsinglright', 'guillemotleft', 'guillemotright',
        'bullet', 'periodcentered', 'parenleft', 'parenright', 'bracketleft', 'bracketright', 'braceleft',
        'braceright', 'colon']


def _case_shift(p, name):
    if name.startswith(('paren', 'bracket', 'brace')):
        return p.under / 2 - 0.25 * p.m
    if name == 'colon':
        return 0.0
    return (p.cap - p.xh) / 2


for n in CASE:
    spec = REGISTRY[n]

    def fn(g, n=n):
        sub = draw(n, g.p)
        if n == 'colon':
            REGISTRY['colon.tf'].fn(g)
            return
        g.add_glyph(sub, 0, _case_shift(g.p, n))
    glyph(f'{n}.case', None, spec.width, kind=spec.kind)(fn)


# Single substitutions other glyph modules add to these features (sups,
# subs, sinf, numr, dnom, case): {feature tag: [(glyph, replacement)]}.
MORE: dict = {}


def _more(tag):
    return ''.join(f' sub {a} by {b};' for a, b in MORE.get(tag, []))


def fea(mono: bool = False) -> str:
    """The feature file (the monospaced cut adds its programming ligatures)."""
    figs = ' '.join(FIGS)
    px = ' '.join(f'{n}.px' for n in FIGS)
    sm = {s: ' '.join(f'{n}.{s}' for n in FIGS) for s in ('sups', 'subs', 'numr', 'dnom', 'tnum')}
    alts = ' '.join(n for n in PROPORTIONAL_FIGS if n not in FIGS)          # zero.zero zero.dot five.ss02
    alts_t = ' '.join(f'{n}.tnum' for n in PROPORTIONAL_FIGS if n not in FIGS)
    case = '\n'.join(f'    sub {n} by {n}.case;' for n in CASE)
    from ..draw import FEATURE_CODE, LANGSYS
    langsys = ''.join(f'languagesystem {t};\n' for t in dict.fromkeys(LANGSYS))
    extra = ''.join(FEATURE_CODE)                           # (locl first: its lookups run before the rest)
    text = f"""languagesystem DFLT dflt;
languagesystem latn dflt;
{langsys}
{extra}

@figs = [{figs}];
@tnum = [{sm['tnum']}];
@sups = [{sm['sups']}];
@subs = [{sm['subs']}];
@numr = [{sm['numr']}];
@dnom = [{sm['dnom']}];
@px = [{px}];
@pfig = [{figs} {alts}];
@tfig = [{sm['tnum']} {alts_t}];

feature tnum {{ sub @pfig by @tfig; }} tnum;
feature pnum {{ sub @tfig by @pfig; }} pnum;
feature zero {{ sub zero by zero.zero; sub zero.tnum by zero.zero.tnum; }} zero;
feature ss01 {{
    featureNames {{ name "Dotted zero"; }};
    sub zero by zero.dot;
    sub zero.tnum by zero.dot.tnum;
}} ss01;
feature ss02 {{
    featureNames {{ name "Open five"; }};
    sub five by five.ss02;
    sub five.tnum by five.ss02.tnum;
}} ss02;
feature calt {{
    sub @pfig colon' @pfig by colon.case;
    sub [@tfig @px] colon' [@tfig @px] by colon.tf;
}} calt;
feature ss20 {{
    featureNames {{ name "Watch pixels"; }};
    sub @figs by @px;
    sub @tnum by @px;
    sub [zero.zero zero.dot zero.zero.tnum zero.dot.tnum] by zero.px;
    sub [five.ss02 five.ss02.tnum] by five.px;
    sub [colon.tf colon.case] by colon.tf.px;
}} ss20;
feature sups {{ sub @figs by @sups; sub @tnum by @sups;{_more('sups')} }} sups;
feature subs {{ sub @figs by @subs; sub @tnum by @subs;{_more('subs')} }} subs;
feature sinf {{ sub @figs by @subs; sub @tnum by @subs;{_more('sinf')} }} sinf;
feature numr {{ sub @figs by @numr; sub @tnum by @numr;{_more('numr')} }} numr;
feature dnom {{ sub @figs by @dnom; sub @tnum by @dnom;{_more('dnom')} }} dnom;
feature frac {{
    lookup FRAC_SLASH {{ sub slash by fraction; }} FRAC_SLASH;
    lookup FRAC_NUMR {{ sub @figs by @numr; sub @tnum by @numr; }} FRAC_NUMR;
    lookup FRAC_DNOM {{ sub [fraction @dnom] @numr' by @dnom; }} FRAC_DNOM;
}} frac;
feature ordn {{
    sub [@figs @tnum] [a o]' by [ordfeminine ordmasculine];
}} ordn;
feature case {{
{case}{_more('case')}
}} case;
"""
    from .ligatures import alternates_fea
    if mono:
        from .ligatures import fea as ligature_fea
        from .sequences import fea as sequence_fea
        text += ligature_fea() + sequence_fea()     # the fixed ligatures first: runs take what they leave
    text += alternates_fea(mono)        # after the ligatures: ss03 replaces what calt made
    if mono:
        from .alignment import fea as alignment_fea
        text += alignment_fea()         # after the ligatures: a sign one took is not there to move
    return text
