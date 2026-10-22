"""Superscripts and subscripts (U+2070-U+209C) beyond the figures.

The signs and letters are the full-size drawings under the small figures'
parameters (``features.small``: a smaller module and cap height, strokes a
little lighter), with the x-height, ascender and descender scaled the same
way (``symkit.small_all``), and placed as the small figures are:
superiors on the baseline of ¹ ² ³ (their figures' tops on the cap
height), inferiors on the baseline of ₁ ₂ ₃. So x⁻¹, H₂O and xⁿ⁺¹ set on
one line, and ``sups``/``subs``/``sinf`` reach them from + − = ( ) and the
letters.

The subscript schwa is the small e turned half round.
"""
from __future__ import annotations

from ..draw import REGISTRY, draw, glyph
from .features import MORE, small
from .symkit import TURN, add_t, small_all

SUP_SIGNS = {'uni207A': ('⁺', 'plus'), 'uni207B': ('⁻', 'minus'), 'uni207C': ('⁼', 'equal'),
             'uni207D': ('⁽', 'parenleft'), 'uni207E': ('⁾', 'parenright')}
SUP_LETTERS = {'uni2071': ('ⁱ', 'i'), 'uni207F': ('ⁿ', 'n')}
SUB_SIGNS = {'uni208A': ('₊', 'plus'), 'uni208B': ('₋', 'minus'), 'uni208C': ('₌', 'equal'),
             'uni208D': ('₍', 'parenleft'), 'uni208E': ('₎', 'parenright')}
SUB_LETTERS = {'uni2090': ('ₐ', 'a'), 'uni2091': ('ₑ', 'e'), 'uni2092': ('ₒ', 'o'),
               'uni2093': ('ₓ', 'x'), 'uni2094': ('ₔ', None), 'uni2095': ('ₕ', 'h'),
               'uni2096': ('ₖ', 'k'), 'uni2097': ('ₗ', 'l'), 'uni2098': ('ₘ', 'm'),
               'uni2099': ('ₙ', 'n'), 'uni209A': ('ₚ', 'p'), 'uni209B': ('ₛ', 's'),
               'uni209C': ('ₜ', 't')}


def sup_dy(p):
    """Superiors' baseline: the small figures' (their tops on the cap height)."""
    return p.cap - small(p).cap


def sub_dy(p):
    """Inferiors' baseline: the small figures' (hanging below the baseline)."""
    return -0.22 * p.cap


def _small_width(base, letter):
    def width(p):
        ps = small_all(p)
        if letter and p.mono:                               # a small letter fills a small cell
            return ps.fig_w
        return REGISTRY[base].width(ps)
    return width


def _register(table, dy, letter):
    for name, (ch, base) in table.items():
        if base is None:
            continue

        def fn(g, base=base):
            g.add_glyph(draw(base, small_all(g.p)), 0, dy(g.p))
        glyph(name, ch, _small_width(base, letter), kind=('punct', 0.55))(fn)


_register(SUP_SIGNS, sup_dy, False)
_register(SUP_LETTERS, sup_dy, True)
_register(SUB_SIGNS, sub_dy, False)
_register(SUB_LETTERS, sub_dy, True)


@glyph('uni2094', 'ₔ', _small_width('e', True), kind=('punct', 0.55))
def schwainferior(g):
    """The small e turned half round about the middle of its x-height."""
    ps = small_all(g.p)
    sub = draw('e', ps)
    add_t(g, sub, TURN, sub.W, ps.xh + sub_dy(g.p))


# --- Features: + − = ( ) and the letters reach their small forms ----------------

_SIGN_SRC = {'plus': 'plus', 'minus': 'minus', 'equal': 'equal', 'parenleft': 'parenleft',
             'parenright': 'parenright'}
for _tag, _signs, _letters in (('sups', SUP_SIGNS, SUP_LETTERS), ('subs', SUB_SIGNS, SUB_LETTERS),
                               ('sinf', SUB_SIGNS, SUB_LETTERS)):
    rules = MORE.setdefault(_tag, [])
    for _name, (_ch, _base) in list(_signs.items()) + list(_letters.items()):
        if _base:
            rules.append((_base, _name))
        if _base == 'minus':
            rules.append(('hyphen', _name))
