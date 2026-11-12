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


_DRAWN_AFTER = r'''
import json, sys
import arris.glyphs
from arris.font import place
from arris.instances import mono_weight, params
from arris.italic import italic
p = italic(params(mono_weight(int(sys.argv[1]))).with_(mono=True)).with_(cursive=True)
for first in [n for n in sys.argv[3].split(',') if n]:
    place(first, p)
out = {}
for name in sys.argv[2].split(','):
    rings, adv = place(name, p)
    out[name] = [[[round(float(v), 2) for v in q[:2]] for q in r] for r in rings]
print(json.dumps(out))
'''


@pytest.mark.parametrize('w', [400, 700])
def test_a_drawing_does_not_depend_on_what_was_drawn_before_it(w):
    """A reference that others are measured by is drawn once and kept: a
    height's overshoot from its o, its bar from the 5, the hooks' lines from
    the e, a glyph's Regular. It was drawn as a part of whichever glyph
    asked first, and in Arris Mono a part of another glyph is not fitted to
    the cell and a glyph of its own is: in Mono Italic the x-height's
    overshoot was 1.50 units at Bold where a plain letter had been drawn
    first and 1.09 where an accented letter's base had, and the same font
    came out two ways as its glyphs were shared out among the build's
    workers (about a hundred accented letters and the tabular figures in
    Mono Bold Italic). Drawn as a glyph of its own, whoever asks
    (draw._as_own). Each order in a process of its own: what is kept is
    kept for the life of one."""
    import json
    import os
    import subprocess
    import sys
    names = 'uni0451,uni04D1,uni0219,omicrontonos,uni218A,eight.tnum,s,e'
    env = dict(os.environ, ARRIS_CACHE='')

    def drawn(first):
        run = subprocess.run([sys.executable, '-W', 'ignore', '-c', _DRAWN_AFTER, str(w), names, first], env=env,
                             capture_output=True, text=True, check=True)
        return json.loads(run.stdout.strip().splitlines()[-1])
    alone = drawn('')
    for first in ('e', 'a,o,s,x', 'edieresis,uni04D3', 'H,five,O'):
        assert drawn(first) == alone, first
