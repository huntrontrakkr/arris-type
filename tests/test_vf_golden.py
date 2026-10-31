"""The variable-font build against a golden build: a trial of a few glyphs
(forms, composites, finer grids and the italic among them) built by the
package must come out identical, outline for outline and delta for delta,
to one built before a change (characterization).

    uv run python tests/test_vf_golden.py build/golden/upright    # fingerprint a build (writes fingerprint.json beside it)

Skipped where build/golden/<style>/fingerprint.json is not there: make the
golden with the builder as it stands, then change it.

    ARRIS_VF_ONLY=$GOLDEN_GLYPHS ARRIS_VF_OUT=build/golden/upright uv run python -m arris.vf
    ARRIS_VF_ONLY=$GOLDEN_GLYPHS ARRIS_VF_OUT=build/golden/italic uv run python -m arris.vf italic
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / 'build' / 'golden'
# figures, a capital and a composite of it, forms ($), the fixed ⏭, Ю (a slit
# that closes), glyphs that take a finer grid or an alternative alignment,
# marks and punctuation, a fraction, a symbol
GLYPHS = ('zero,A,a,Aacute,dollar,uni23ED,uni042E,question,g,uni229D,Uogonek,uni21BB,ampersand,period,f,onehalf,'
          'uni0416,at,eacute')
FONTS = {'upright': ('Arris[GRAD,WTCH,wght].ttf', 'vf_check.json', []),
         'italic': ('Arris-Italic[GRAD,WTCH,wght].ttf', 'vf_check_italic.json', ['italic'])}


def fingerprint(font: Path, report: Path | None = None) -> dict:
    """What the build decides, glyph by glyph: every outline and component,
    every variation, the advances; the other tables by a hash of their
    bytes (head apart: its timestamps); and the check's report."""
    f = TTFont(font)
    glyf, gvar, hmtx = f['glyf'], f['gvar'], f['hmtx']
    glyphs = {}
    for n in f.getGlyphOrder():
        g = glyf[n]
        if g.isComposite():
            shape = {'components': [(c.glyphName, c.x, c.y) for c in g.components]}
        else:
            coords, ends, flags = g.getCoordinates(glyf)
            shape = {'coords': [tuple(q) for q in coords], 'ends': list(ends), 'flags': [int(x) for x in flags]}
        glyphs[n] = {**shape, 'hmtx': list(hmtx[n]),
                     'gvar': [(sorted(tv.axes.items()), [list(c) if c is not None else None for c in tv.coordinates])
                              for tv in gvar.variations.get(n, [])]}
    tables = {tag: hashlib.sha1(f.getTableData(tag)).hexdigest()
              for tag in sorted(f.keys()) if tag not in ('GlyphOrder', 'head', 'glyf', 'gvar', 'loca', 'hmtx')}
    out = {'order': f.getGlyphOrder(), 'glyphs': glyphs, 'tables': tables}
    if report is not None and report.exists():
        out['check'] = json.loads(report.read_text())
    return json.loads(json.dumps(out))                     # (as the golden reads back: lists for tuples)


def _differences(got: dict, expect: dict) -> list[str]:
    out = []
    if got['order'] != expect['order']:
        out.append(f'glyph order: {got["order"]} != {expect["order"]}')
    for n, e in expect['glyphs'].items():
        g = got['glyphs'].get(n)
        if g != e:
            keys = [k for k in e if g is None or g.get(k) != e[k]]
            out.append(f'{n}: {", ".join(keys)} differ')
    for tag, h in expect['tables'].items():
        if got['tables'].get(tag) != h:
            out.append(f'table {tag} differs')
    if got.get('check') != expect.get('check'):
        out.append('the check\'s report differs')
    return out


@pytest.mark.parametrize('style', list(FONTS))
def test_against_golden(style: str, tmp_path: Path) -> None:
    gold = GOLDEN / style / 'fingerprint.json'
    if not gold.exists():
        pytest.skip(f'no golden build at {gold}')
    font, report, args = FONTS[style]
    env = {**os.environ, 'ARRIS_VF_ONLY': GLYPHS, 'ARRIS_VF_OUT': str(tmp_path),
           'ARRIS_VF_WORKERS': str(os.cpu_count() or 2)}
    subprocess.run([sys.executable, '-m', 'arris.vf', *args], cwd=ROOT, env=env, check=True)
    got = fingerprint(tmp_path / font, tmp_path / report)
    expect = json.loads(gold.read_text())
    assert not _differences(got, expect)


if __name__ == '__main__':
    for d in sys.argv[1:]:
        p = Path(d)
        style = 'italic' if 'italic' in p.name else 'upright'
        font, report, _ = FONTS[style]
        (p / 'fingerprint.json').write_text(json.dumps(fingerprint(p / font, p / report)))
        print('wrote', p / 'fingerprint.json')
