"""Localised Cyrillic forms (the ``locl`` feature).

* **Bulgarian** (BGR) writes several lowercase letters as the Latin
  lowercase does, with ascenders and descenders where the Russian ones are
  small capitals: в with a loop on an ascender (the B's two bowls on the b),
  д as the g, ж and к with an ascending stem, л as a turned v, и й п т as
  u ŭ n m, ц ш щ with the u's round foot. In the italic, the letters whose
  Russian italic is already cursive (д и й п т ц ш щ) keep it.
* **Serbian and Macedonian** (SRB, MKD) italics write б as δ (a bar on the
  ascender, a 45-degree stroke back down into the bowl), г as ī, п as ū and
  т as m̄. Upright, these are the Russian letters. (Their italic д is the g,
  which Arris's Russian italic already uses.)

Alternates are glyphs named ``uniXXXX.loclBGR`` / ``.loclSRB``; the
monospaced italic keeps the upright forms, as it does for Russian. The
lookups reach the feature file through ``draw.LANGSYS`` and
``draw.FEATURE_CODE`` (gathered by ``features.fea``).
"""
from __future__ import annotations

from ..draw import B, FEATURE_CODE, LANGSYS, REGISTRY, glyph
from .cyrillic import sc
from .cyrillic_ext import _turned, descender, room
from .extra_latin import stamp
from .italic_forms import ital
from .letterframe import Frame, letter_width


def _stamped(name, latin, kind='lower'):
    """An alternate that is a Latin letter's drawing (its italic too)."""
    glyph(name, None, lambda p, n=latin: REGISTRY[n].width(p), kind=kind)(
        lambda g, n=latin: stamp(g, n, width=g.W))


def _italic_as(name, default):
    """In the italic, the alternate keeps the default letter's cursive form."""
    spec = REGISTRY[f'{default}.ital']
    upright = REGISTRY[name]

    def fn(g, spec=spec, upright=upright):
        if g.p.mono:
            return upright.fn(g)
        return spec.fn(g)
    glyph(f'{name}.ital', None, spec.width, kind=upright.kind)(fn)


# --- Bulgarian ---------------------------------------------------------------

def tall_ve(g):
    """The b with a second, narrower bowl on its ascender, closing at the
    x-height: Bulgarian в (and the Greek curled beta)."""
    from .caps import big
    f = Frame(g, 8, 'asc')
    p = g.p
    g.stroke(f.P(1, 0), f.P(1, 13))
    g.stroke(f.P(1, 12), B(*f.P(6, 12)), B(*f.P(6, 8), big(p)), f.P(1, 8), closed=True)
    g.stroke(f.P(1, 8), B(*f.P(7, 8)), B(*f.P(7, 1)), f.P(1, 1), closed=True)


glyph('uni0432.loclBGR', None, letter_width(8, 2), kind='lower')(tall_ve)


@glyph('uni0436.loclBGR', None, lambda p: REGISTRY['uni0436'].width(p), kind='lower')
def zhe_bgr(g):
    """ж whose middle stem rises to the ascender."""
    REGISTRY['uni0436'].fn(g)
    p = g.p
    g.stroke((g.W / 2, p.xh / 2), (g.W / 2, p.asc))


@glyph('uni043A.loclBGR', None, lambda p: REGISTRY['k'].width(p), kind='lower')
def ka_bgr(g):
    """The k, upright in the italic too (the italic's looped k is Latin)."""
    REGISTRY['k'].fn(g)


@glyph('uni043B.loclBGR', None, letter_width(8, 2), kind='lower')
def el_bgr(g):
    """The v, turned: a gable on the x-height."""
    REGISTRY['v'].fn(g)
    _turned(g, g.p.xh)
    g.clip = (0, 0, g.W, g.p.xh)


for _cp, _latin in ((0x0434, 'g'), (0x0438, 'u'), (0x0439, 'ubreve'), (0x043F, 'n'), (0x0442, 'm')):
    _stamped(f'uni{_cp:04X}.loclBGR', _latin)


@glyph('uni0446.loclBGR', None, lambda p: REGISTRY['u'].width(p) + room(p), kind='lower')
def tse_bgr(g):
    """The u with Ц's tail."""
    f = Frame(g, 8, 'lower')
    p = g.p
    xr = g.W - room(p) - p.sv / 2
    g.stroke(f.P(1, 9), B(*f.P(1, 1)), (xr, f.Y(1)))
    g.stroke((xr, p.xh), (xr, f.Y(1)))
    descender(g, f, xr, g.W - p.sv / 2)


def _sha_bgr(g, tail):
    f = Frame(g, 12, 'lower')
    p = g.p
    xr = f.X(11) if not tail else f.X(11) - room(p)
    xm = (f.X(1) + xr) / 2
    if tail:
        g.stroke(f.P(1, 9), B(*f.P(1, 1)), (xr, f.Y(1)))
        g.stroke((xr, p.xh), (xr, f.Y(1)))
        descender(g, f, xr, g.W - p.sv / 2)
    else:
        g.stroke(f.P(1, 9), B(*f.P(1, 1)), B(xr, f.Y(1)), (xr, p.xh))
    g.stroke((xm, p.xh), (xm, f.Y(1)))


glyph('uni0448.loclBGR', None, letter_width(12, 3), kind='lower')(lambda g: _sha_bgr(g, False))
glyph('uni0449.loclBGR', None, lambda p: letter_width(12, 3)(p) + room(p), kind='lower')(
    lambda g: _sha_bgr(g, True))

for _cp in (0x0446, 0x0448, 0x0449):
    _italic_as(f'uni{_cp:04X}.loclBGR', f'uni{_cp:04X}')

BGR = ['uni0432', 'uni0434', 'uni0436', 'uni0438', 'uni0439', 'uni043A', 'uni043B', 'uni043F', 'uni0442',
       'uni0446', 'uni0448', 'uni0449']


# --- Serbian and Macedonian italics ----------------------------------------

SRB = ['uni0431', 'uni0433', 'uni043F', 'uni0442']
for _n in SRB:
    _spec = REGISTRY[_n]
    glyph(f'{_n}.loclSRB', None, _spec.width, kind=_spec.kind)(_spec.fn)


@ital('uni0431.loclSRB', 8, 2)
def be_srb_ital(g):
    """δ's form: the o, and from its top right corner a 45-degree stroke
    rising back to the left into a bar on the ascender."""
    f = Frame(g, 8, 'asc')
    p = g.p
    g.stroke(B(*f.P(1, 1)), B(*f.P(7, 1)), B(*f.P(7, 8)), B(*f.P(1, 8)), closed=True)
    x7, y8, y12 = f.X(7), f.Y(8), f.Y(12)
    a = x7 + y8 - p.leg / 2                                 # x + y: through the bowl's corner chamfer
    y0 = y8 - p.leg / 2
    xt = a - y12
    g.stroke((a - y0, y0), (xt, y12), (x7, y12))


def _macron_over(name, latin):
    """The italic of ``name``: a Latin letter with a macron (ī ū m̄)."""
    def fn(g, latin=latin):
        from .marks import gap, macron
        p = g.p
        sub = stamp(g, latin, width=g.W)
        rings = g.extra[-1]
        top = rings.bounds[3]
        x0, x1 = rings.bounds[0], rings.bounds[2]
        # over the letter's x-height part (an entry flag leans left of it)
        macron(g, (max(x0, 0) + min(x1, g.W)) / 2, top + gap(p), 'lc')
        return sub
    ital(name, 8, 2, width=lambda p, n=latin: REGISTRY[n].width(p))(fn)


_macron_over('uni0433.loclSRB', 'dotlessi')
_macron_over('uni043F.loclSRB', 'u')
_macron_over('uni0442.loclSRB', 'm')


# --- The feature -----------------------------------------------------------

def _subs(names, tag):
    return ''.join(f'        sub {n} by {n}.locl{tag};\n' for n in names)


LANGSYS.extend(['cyrl dflt', 'cyrl BGR', 'cyrl SRB', 'cyrl MKD'])
FEATURE_CODE.append(
    'feature locl {\n'
    '    script cyrl;\n'
    '    language BGR exclude_dflt;\n' + _subs(BGR, 'BGR') +
    '    language SRB exclude_dflt;\n' + _subs(SRB, 'SRB') +
    '    language MKD exclude_dflt;\n' + _subs(SRB, 'SRB') +
    '} locl;\n')
