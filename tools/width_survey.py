"""How wide a family sets as it gets bolder, against others, at one x-height and one boldness.

    python tools/width_survey.py SUBJECT FONT.ttf ...

Font files are named Family-weight.ttf (Arris-400.ttf, Inter-900.ttf: static
instances, one per weight); SUBJECT is the family measured against the rest.
Each font is rasterised unhinted at 1000 px to the em and measured in those
units; every length is then taken by the font's own x-height (capitals and
figures by its cap height), and a family is read along its weights at the
subject's boldness (the n's stem by the x-height), so a face with a large
x-height or with other weight names is compared like for like.

Prints, for the subject's Regular and each heavier weight: the length of a
line of lowercase, of capitals and of figures against the subject's Regular,
beside the other families' median and quartiles; and what the white inside
the n, the o, the H and the zero does. letterframe.white_scale and
instances.FIG_GIVEN take their rates from this table (1.017: 60 grotesque,
geometric and squared families from Google Fonts).
"""
from __future__ import annotations

import statistics as st
import sys
from itertools import pairwise
from pathlib import Path

import freetype
import numpy as np

PP = 1000
LOWER = 'the quick brown fox jumps over the lazy dog and typography is the craft of endowing human language with a durable visual form'
UPPER = 'HAMBURGEFONSTIV QUICK WALTZ JUDGE NYMPH BOX'


def bitmap(face, ch):
    face.load_char(ch, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING | freetype.FT_LOAD_TARGET_MONO)
    g = face.glyph
    b = g.bitmap
    if b.rows == 0:
        return np.zeros((0, 0), bool), 0, g.advance.x / 64
    rows = np.unpackbits(np.array(b.buffer, dtype=np.uint8).reshape(b.rows, b.pitch), axis=1)[:, :b.width]
    return rows.astype(bool), g.bitmap_top, g.advance.x / 64


def spans(line):
    out, start = [], None
    for i, v in enumerate([*line, False]):
        if v and start is None:
            start = i
        if not v and start is not None:
            out.append((start, i))
            start = None
    return out


def white(row):
    """The white between the first and the last run of ink on a row."""
    sp = spans(row)
    return sp[-1][0] - sp[0][1] if len(sp) > 1 else 0


def measure(path):
    face = freetype.Face(str(path))
    face.set_pixel_sizes(0, PP)
    if not all(face.get_char_index(c) for c in 'xnoHr0'):
        return None
    xh, cap = bitmap(face, 'x')[1], bitmap(face, 'H')[1]
    n, ntop, n_adv = bitmap(face, 'n')
    row = spans(n[ntop - xh // 3])
    o, _, _ = bitmap(face, 'o')
    H, _, _ = bitmap(face, 'H')
    z, _, _ = bitmap(face, '0')
    r_adv = bitmap(face, 'r')[2]
    text = lambda s: sum(bitmap(face, c)[2] for c in s) / len(s)
    return {'bold': (row[0][1] - row[0][0]) / xh, 'lower': text(LOWER) / xh, 'upper': text(UPPER) / cap,
            'figures': text('0123456789') / cap, 'n counter': white(n[ntop - xh // 3]) / xh,
            'o counter': white(o[o.shape[0] // 2]) / xh, 'H counter': white(H[H.shape[0] * 3 // 4]) / cap,
            'zero counter': white(z[z.shape[0] // 3]) / cap, 'r to n': r_adv / n_adv}


def at(weights, bold, key):
    """A family's measure at a boldness, along its weights (None outside them)."""
    pts = sorted((m['bold'], m[key]) for m in weights.values())
    if not pts or bold < pts[0][0] - 1e-9 or bold > pts[-1][0] + 1e-9:
        return None
    for (b0, v0), (b1, v1) in pairwise(pts):
        if b0 <= bold <= b1:
            return v0 + (v1 - v0) * (bold - b0) / max(b1 - b0, 1e-9)
    return pts[-1][1]


def main(subject, paths):
    fams: dict = {}
    for path in map(Path, paths):
        fam, _, w = path.stem.rpartition('-')
        m = measure(path) if w.isdigit() else None
        if m:
            fams.setdefault(fam, {})[int(w)] = m
    own = fams.pop(subject)
    regular = own[400]
    print(f'{subject} against {len(fams)} families, each read at {subject}\'s boldness and by its own x-height')
    print(f'Regular (stem {regular["bold"]:.3f} of the x-height):')
    for key in ('lower', 'upper', 'figures', 'r to n'):
        vs = [v for v in (at(ws, regular['bold'], key) for ws in fams.values()) if v is not None]
        q = st.quantiles(vs, n=4)
        print(f'  {key:13s} {regular[key]:.3f}   families: median {st.median(vs):.3f}, quartiles {q[0]:.3f} to {q[2]:.3f}')
    for w in sorted(k for k in own if k > 400):
        print(f'{w} (stem {own[w]["bold"]:.3f}), against the Regular:')
        for key in ('lower', 'upper', 'figures', 'n counter', 'o counter', 'H counter', 'zero counter', 'r to n'):
            vs = []
            for ws in fams.values():
                v0, v1 = at(ws, regular['bold'], key), at(ws, own[w]['bold'], key)
                if v0 and v1:
                    vs.append(v1 / v0 - 1)
            if len(vs) < 4:
                continue
            q = st.quantiles(vs, n=4)
            print(f'  {key:13s} {(own[w][key] / regular[key] - 1) * 100:+6.1f}%   {len(vs)} families: median {st.median(vs) * 100:+5.1f}%, '
                  f'quartiles {q[0] * 100:+5.1f}% to {q[2] * 100:+5.1f}%')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2:])
