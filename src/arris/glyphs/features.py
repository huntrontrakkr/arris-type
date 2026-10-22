"""Alternate figures, small figures, case forms, and the OpenType features
that reach them.

* Figures are tabular by default (``tnum``); ``pnum`` gives proportional
  ones, the same drawings spaced like letters.
* ``calt`` turns a colon between figures into the watch's time colon: two
  stem-square dots centred on the figures, in a tighter slot.
* ``zero``: a slashed zero, the slash square to the bowl's corners; ``ss01``:
  a dotted zero.
* Small figures (superiors, inferiors, numerators, denominators) are drawn
  at small size, not scaled: a smaller module and cap height with strokes
  only a little lighter, so they keep their colour beside full figures.
* ``case`` raises dashes, guillemets and centred marks to the capitals.
"""
from __future__ import annotations

from shapely import affinity

from ..draw import REGISTRY, draw, glyph
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


# superiors: tops on the cap height; inferiors: hanging below the baseline;
# numerators: tops on the cap height; denominators: on the baseline.
_register_small('sups', SUPS, lambda p: p.cap - small(p).cap)
_register_small('subs', SUBS, lambda p: -0.22 * p.cap)
_register_small('numr', None, lambda p: p.cap - small(p).cap)
_register_small('dnom', None, lambda p: 0.0)


# --- Proportional figures ------------------------------------------------

for n in FIGS:
    spec = REGISTRY[n]
    glyph(f'{n}.pnum', None, spec.width, kind='cap', openings=spec.openings)(spec.fn)


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
        ps = small(p).with_(xh=SMALL * p.xh, asc=SMALL * p.asc, desc=SMALL * p.desc)
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
        return p.desc / 2 - 0.25 * p.m
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
    sm = {s: ' '.join(f'{n}.{s}' for n in FIGS) for s in ('sups', 'subs', 'numr', 'dnom', 'pnum')}
    case = '\n'.join(f'    sub {n} by {n}.case;' for n in CASE)
    from ..draw import FEATURE_CODE, LANGSYS
    langsys = ''.join(f'languagesystem {t};\n' for t in dict.fromkeys(LANGSYS))
    extra = ''.join(FEATURE_CODE)                           # (locl first: its lookups run before the rest)
    text = f"""languagesystem DFLT dflt;
languagesystem latn dflt;
{langsys}
{extra}

@figs = [{figs}];
@pnum = [{sm['pnum']}];
@sups = [{sm['sups']}];
@subs = [{sm['subs']}];
@numr = [{sm['numr']}];
@dnom = [{sm['dnom']}];
@anyfig = [{figs} {sm['pnum']} zero.zero zero.dot five.ss02];

feature tnum {{ sub @pnum by @figs; }} tnum;
feature pnum {{ sub @figs by @pnum; }} pnum;
feature zero {{ sub zero by zero.zero; }} zero;
feature ss01 {{
    featureNames {{ name "Dotted zero"; }};
    sub zero by zero.dot;
}} ss01;
feature ss02 {{
    featureNames {{ name "Open five"; }};
    sub five by five.ss02;
}} ss02;
feature calt {{
    sub @anyfig colon' @anyfig by colon.tf;
}} calt;
feature sups {{ sub @figs by @sups;{_more('sups')} }} sups;
feature subs {{ sub @figs by @subs;{_more('subs')} }} subs;
feature sinf {{ sub @figs by @subs;{_more('sinf')} }} sinf;
feature numr {{ sub @figs by @numr;{_more('numr')} }} numr;
feature dnom {{ sub @figs by @dnom;{_more('dnom')} }} dnom;
feature frac {{
    lookup FRAC_SLASH {{ sub slash by fraction; }} FRAC_SLASH;
    lookup FRAC_NUMR {{ sub @figs by @numr; }} FRAC_NUMR;
    lookup FRAC_DNOM {{ sub [fraction @dnom] @numr' by @dnom; }} FRAC_DNOM;
}} frac;
feature ordn {{
    sub @figs [a o]' by [ordfeminine ordmasculine];
}} ordn;
feature case {{
{case}{_more('case')}
}} case;
"""
    from .ligatures import alternates_fea
    if mono:
        from .ligatures import fea as ligature_fea
        text += ligature_fea()
    text += alternates_fea(mono)        # after the ligatures: ss03 replaces what calt made
    return text
