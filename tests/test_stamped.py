"""A glyph stamped into another is itself: its finished ink is kept as it
was finished wherever it stands apart, under a clip that leaves it whole as
much as with none (geom.ink). Mono clips every glyph at its cell, and ø
clips its slash: until 1.014 both sent the stamped letter round the corner
rule again, so Mono's ǿ was not ø, and at Bold the second finish of ø's
slash junction turned on the last bits of a float."""
from __future__ import annotations

import pytest
from shapely.geometry import Polygon, box

import arris.glyphs  # noqa: F401  (the registry)
from arris import draw as D
from arris.geom import Thickness, ink
from arris.instances import mono_weight, params


def _rings(g):
    return sorted(tuple(sorted((round(x, 6), round(y, 6)) for x, y in r)) for r in g.rings())


def test_finished_ink_a_clip_leaves_whole_is_kept_as_it_was():
    # a notch the corner rule would take in a second finish, under a clip far
    # from it: the ring comes back as it went in
    notched = Polygon([(0, 0), (300, 0), (300, 300), (160, 300), (150, 290), (140, 300), (0, 300)])
    out = ink([], Thickness(100.0, 100.0, 100.0, 100.0), 30.0, extra=[notched],
              clip=box(-100, -100, 400, 400), finished=[notched])
    assert len(out) == 1
    assert Polygon(out[0]).symmetric_difference(notched).area < 1e-6


@pytest.mark.parametrize('w', [400, 700])
def test_mono_accented_letter_keeps_its_letter(w):
    p = params(mono_weight(w)).with_(mono=True)
    base, accented = _rings(D.draw('oslash', p)), _rings(D.draw('oslashacute', p))
    assert all(r in accented for r in base)


def test_mono_bold_oslashacute_does_not_turn_on_a_float():
    # the stamped ø moved by a hair: the same outline, point for point
    p = params(mono_weight(700)).with_(mono=True)
    orig = D.Glyph.add_glyph
    outs = []
    try:
        for eps in (0.0, 1e-13, -1e-13, 1e-10):
            D.Glyph.add_glyph = lambda self, sub, dx=0.0, dy=0.0, e=eps: orig(self, sub, dx + e, dy + e)
            outs.append(D.draw('oslashacute', p).rings())
    finally:
        D.Glyph.add_glyph = orig
    for o in outs[1:]:
        assert [len(r) for r in o] == [len(r) for r in outs[0]]
        assert max(abs(a - b) for r0, r in zip(outs[0], o) for q0, q in zip(r0, r) for a, b in zip(q0, q)) < 1e-6
