"""Arris Mono's alignment (``calt``, after Fira Code's): signs that move to
the letters beside them.

In Mono the hyphen, plus and asterisk sit on the capitals' middle, the math
axis, so `->` `+=` `*=` line up with = < > and the arrows they ligate into.
Touching a lowercase letter (`kebab-case`, `a+b`, `x*y`) they drop to the
lowercase middle (NAME.lc). The colon, low for prose, rises to the capitals'
middle (its case form, as between figures) touching a capital (`A:B`,
`HH:MM`) or beside a chevron (`<:` `:>`). An x between figures (`1920x1080`)
or after a zero before a hex digit (`0xFF`) is a times sign (x.multiply).

Between a capital and a lowercase letter nothing moves (`A-b`), and a sign
doubled is left alone (`Foo::Bar`, `x--y`; `--` `++` are ligatures): only a
single sign moves, Fira's rule.
"""
from __future__ import annotations

import unicodedata

from ..draw import REGISTRY, draw, glyph
from .punct import axis

LOWERED = ('hyphen', 'plus', 'asterisk')


def _drop(p):
    """From the capitals' middle to the lowercase middle."""
    return p.xh / 2 - axis(p)


for _n in LOWERED:
    _spec = REGISTRY[_n]

    def _lowered(g, n=_n):
        g.add_glyph(draw(n, g.p), 0.0, _drop(g.p))
    glyph(f'{_n}.lc', None, _spec.width, kind=_spec.kind)(_lowered)


@glyph('x.multiply', None, REGISTRY['multiply'].width, kind=REGISTRY['multiply'].kind)
def x_multiply(g):
    g.add_glyph(draw('multiply', g.p))


def _letters(cat, names):
    """The glyphs among ``names`` that are letters of a case (Lu, Ll), and
    their alternates (a.cv01, f.ss04)."""
    out = []
    for n in names:
        spec = REGISTRY.get(n.split('.')[0])
        if n.endswith('.ital') or spec is None or not spec.unicode:
            continue
        if unicodedata.category(chr(spec.unicode)) == cat:
            out.append(n)
    return out


def fea() -> str:
    """The calt lookups: after the ligatures', so a sign a ligature took is
    no longer there to move. The classes hold every glyph the Mono fonts
    carry (all but the italic's drawings, which replace their uprights)."""
    from .features import FIGS
    names = [n for n in REGISTRY if not n.endswith('.ital')]
    lc, uc = _letters('Ll', names), _letters('Lu', names)
    figs = [n for n in names if n.split('.')[0] in FIGS and not n.endswith(('.sups', '.subs', '.numr', '.dnom'))]
    hexa = figs + [n for n in names if n.split('.')[0] in tuple('ABCDEFabcdef')]
    signs = ' '.join(LOWERED)
    low = ' '.join(f'{n}.lc' for n in LOWERED)
    return f"""@ALIGN_LC = [{' '.join(lc)}];
@ALIGN_UC = [{' '.join(uc)}];
@ALIGN_FIG = [{' '.join(figs)}];
@ALIGN_HEX = [{' '.join(hexa)}];
feature calt {{
lookup ALIGN_LC {{
    ignore sub [{signs}] [{signs}]';
    ignore sub [{signs}]' [{signs}];
    ignore sub @ALIGN_UC [{signs}]' @ALIGN_LC;
    ignore sub @ALIGN_LC [{signs}]' @ALIGN_UC;
    sub @ALIGN_LC [{signs}]' by [{low}];
    sub [{signs}]' @ALIGN_LC by [{low}];
}} ALIGN_LC;
lookup ALIGN_UC {{
    ignore sub colon colon';
    ignore sub colon' colon;
    ignore sub @ALIGN_UC colon' @ALIGN_LC;
    ignore sub @ALIGN_LC colon' @ALIGN_UC;
    sub [@ALIGN_UC less greater] colon' by colon.case;
    sub colon' [@ALIGN_UC less greater] by colon.case;
}} ALIGN_UC;
lookup ALIGN_X {{
    sub @ALIGN_FIG x' @ALIGN_FIG by x.multiply;
    sub zero x' @ALIGN_HEX by x.multiply;
}} ALIGN_X;
}} calt;
"""
