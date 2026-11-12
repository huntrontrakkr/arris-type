"""Arris Mono's ligatures: what the feature code sets for a string (on a
font of empty glyphs carrying the real Mono feature code), runs whose
pieces meet flush however long, and a sample of the drawings clean."""
from __future__ import annotations

import io

import pytest
from shapely import affinity, union_all

import arris.glyphs  # noqa: F401  (the registry)
from arris.draw import REGISTRY
from arris.font import place
from arris.geom import rings_to_shapely
from arris.glyphs.ligatures import LIGATURES
from arris.instances import mono_weight, params
from arris.italic import italic
from arris.topology import faults

hb = pytest.importorskip('uharfbuzz')


@pytest.fixture(scope='module')
def font():
    from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
    from fontTools.fontBuilder import FontBuilder
    from fontTools.pens.ttGlyphPen import TTGlyphPen

    from arris.glyphs.features import fea
    names = ['.notdef'] + [n for n in REGISTRY if not n.endswith(('.ital', '.ss04'))]
    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder(names)
    fb.setupCharacterMap({s.unicode: n for n, s in REGISTRY.items() if s.unicode and n in names})
    empty = TTGlyphPen(None).glyph()
    fb.setupGlyf({n: empty for n in names})
    fb.setupHorizontalMetrics({n: (600, 0) for n in names})
    fb.setupHorizontalHeader()
    fb.setupNameTable({'familyName': 'Test', 'styleName': 'Regular'})
    fb.setupOS2()
    fb.setupPost()
    addOpenTypeFeaturesFromString(fb.font, fea(mono=True))
    buf = io.BytesIO()
    fb.font.save(buf)
    return hb.Font(hb.Face(buf.getvalue()))


def shape(font, text, **feats):
    b = hb.Buffer()
    b.add_str(text)
    b.guess_segment_properties()
    hb.shape(font, b, feats)
    return [font.glyph_to_string(i.codepoint) for i in b.glyph_infos]


def joined(font, text, **feats):
    """Which characters a ligature or a run took: '^' taken, '.' as typed."""
    return ''.join('^' if g == 'LIG' or '.liga' in g or '.seq.' in g or g.split('.')[-1] in feats else '.'
                   for g in shape(font, text, **feats))


@pytest.mark.parametrize('text, want', [
    ('->', '^^'), ('<==>', '^^^^'), ('--', '^^'), ('[|', '^^'), ('#!', '^^'), ('www', '^^^'),
    ('/*', '^^'), ('<*>', '^^^'), ('..<', '^^^'), ('#_(', '^^^'), (']#', '^^'),
    ('---', '^^^'), ('<--->', '^^^^^'), ('|---|', '^^^^^'), ('====', '^^^^'), ('>=>', '^^^'),
    ('=!=', '^^^'), ('--|--', '^^^^^'), ('<<--', '^^^^'), ('####', '^^^^'), ('____', '^^^^'), ('_|_', '^^^'),
    ('#!/bin', '^^....'),                           # a shebang: the slash after does not stop it
    ('www.example', '^^^........'),                 # www before a dot
    ('wwww', '....'), ('[|]', '...'),                # not inside longer runs of their own
    ('<<<--', '.....'), ('-->>>', '.....'),          # a cap that starts a longer run of its own character
    ('x>-1', '....'), ('|-', '..'),                  # one character and one cap: not a run
    ('a-b', '...'), ('=', '.'), ('-', '.'),
])
def test_what_joins(font, text, want):
    assert joined(font, text) == want


def test_a_run_is_pieces_start_middle_end(font):
    assert shape(font, '<---->') == ['hyphen.seq.s.head'] + ['hyphen.seq.m'] * 4 + ['hyphen.seq.e.head']
    assert shape(font, '==>>') == ['equal.seq.s', 'equal.seq.m', 'LIG', 'equal.seq.e.head2']


@pytest.mark.parametrize('feat, text, want', [
    ('ss07', '=~', ['LIG', 'equal_asciitilde.ss07']),
    ('ss08', '!=', ['LIG', 'exclam_equal.ss08']),
    ('ss09', '|=', ['equal.seq.s.bar', 'equal.seq.e']),
    ('ss09', '>>=', ['LIG', 'equal.seq.s.tail2', 'equal.seq.e']),
    ('ss10', 'fi', ['LIG', 'f_i.ss10']),
    ('cv20', '<=', ['LIG', 'less_equal.cv20']),
    ('cv21', '=<', ['LIG', 'equal_less.cv21']),
    ('cv22', '=<', ['LIG', 'equal_less.cv22']),
    ('cv27', '[]', ['LIG', 'bracketleft_bracketright.cv27']),
    ('cv28', '{.', ['LIG', 'braceleft_period.cv28']),
    ('cv32', '.=', ['LIG', 'period_equal.cv32']),
])
def test_the_optional_sets_are_off_until_asked(font, feat, text, want):
    assert shape(font, text, **{feat: True}) == want
    assert shape(font, text) != want


def _line(names, p):
    """The ink of pieces set side by side, a cell apart, as the font sets them."""
    inks, x = [], 0.0
    for n in names:
        if n != 'LIG':
            rings, _ = place(n, p)
            inks.append(affinity.translate(rings_to_shapely(rings), x, 0.0))
        x += p.fig_adv
    return union_all(inks)


@pytest.mark.parametrize('w', [300, 700])
@pytest.mark.parametrize('kind, lines', [('hyphen', 1), ('equal', 2), ('underscore', 1)])
def test_a_run_is_one_line_however_long(kind, lines, w):
    p = params(mono_weight(w)).with_(mono=True)
    ink = _line([f'{kind}.seq.s'] + [f'{kind}.seq.m'] * 3 + [f'{kind}.seq.e'], p)
    assert len(getattr(ink, 'geoms', [ink])) == lines


@pytest.mark.parametrize('name, pieces', [('w_w_w.liga', 1), ('ampersand_ampersand.liga', 1),
                                          ('question_question.liga', 3), ('numbersign_question.liga', 2)])
@pytest.mark.parametrize('w, it', [(300, False), (700, False), (400, True)])
def test_the_joins_are_one_shape(name, pieces, w, it):
    """Fira Code's joins (one contour in its font) are joined here too: the
    w's of `www`, the &'s of `&&`, the ?'s of `??` and `#?` (their dots apart)."""
    p = params(mono_weight(w)).with_(mono=True)
    if it:
        p = italic(p).with_(cursive=True)
    ink = rings_to_shapely(place(name, p)[0])
    assert len(getattr(ink, 'geoms', [ink])) == pieces


@pytest.mark.parametrize('w, it', [(300, False), (700, False), (400, True)])
def test_the_ligatures_and_run_pieces_are_clean(w, it):
    p = params(mono_weight(w)).with_(mono=True)
    if it:
        p = italic(p).with_(cursive=True)
    names = [n for n, _ in LIGATURES] + [n for n in REGISTRY if '.seq.' in n][::3]
    bad = []
    for n in names[::2 if it else 1]:
        rings, _ = place(n, p)
        if faults(rings, p.c, italic=it):
            bad.append(n)
    assert bad == []
