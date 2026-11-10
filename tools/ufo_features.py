"""The feature file of the UFO sources (tools/ufo_sources.py): the font's
substitutions as the build writes them, and the marks' own (ccmp: the
dotless i and j under a mark, the flatter marks over capitals, the
Vietnamese pairs). Mark and kerning positions are not here: the UFOs carry
them as anchors and kerning, and fontmake writes those features.

    uv run python tools/ufo_features.py FONT.ttf OUT.fea
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from fontTools.ttLib import TTFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import arris.glyphs  # noqa: F401  (every glyph registered)
from arris import italic as ital
from arris.anchors import fea as mark_fea
from arris.draw import REGISTRY
from arris.font import place
from arris.glyphs.features import fea
from arris.instances import params


def main() -> int:
    font, out = sys.argv[1], Path(sys.argv[2])
    italic = 'Italic' in Path(font).name
    p = params(400)
    if italic:
        p = ital.italic(p)
    names = [n for n in TTFont(font).getGlyphOrder() if n in REGISTRY]
    marks = mark_fea(names, {n: place(n, p) for n in names}, p)
    # the classes and lookups ccmp needs, without the positions
    keep = [m.group(0) for m in re.finditer(r'^@(?:MARKS|CCMP)_\w+ = \[[^\]]*\];$', marks, re.MULTILINE)]
    keep += [m.group(0) for m in re.finditer(r'^lookup (CCMP_\w+) \{\n.*?\} \1;$', marks, re.MULTILINE | re.DOTALL)]
    keep += [m.group(0) for m in re.finditer(r'^feature ccmp \{\n.*?\n\} ccmp;$', marks, re.MULTILINE | re.DOTALL)]
    order = sorted(keep, key=marks.index)
    # fontmake's kerning goes script by script, and makes a Greek script of
    # its own for the Greek letters' pairs; every other feature must be
    # there too, or Greek text loses its marks (the build's own font has no
    # Greek script, and Greek falls to the default)
    text = fea().replace('languagesystem latn dflt;\n', 'languagesystem latn dflt;\nlanguagesystem grek dflt;\n', 1)
    assert 'languagesystem grek dflt;' in text
    out.write_text(text + '\n'.join(order) + '\n')
    print(f'{out}: {len(order)} blocks for ccmp')
    return 0


if __name__ == '__main__':
    sys.exit(main())
