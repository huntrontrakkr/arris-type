"""Cyrillic widths against other families': each basic letter's advance and ink as shares of the Н's (the н's
for a small letter), in the reference families that have Cyrillic and in Arris, and where Arris stands outside
their range.

Two steps, because the reference fonts are downloads (read them with ``python -I``, from a directory of their
own, and keep this file out of it):

    python -I tools/cyrillic_shares.py refs OUT.json DIR [DIR ...]     # every <Family>-400.ttf and -700.ttf in DIR
    PYTHONPATH=src python tools/cyrillic_shares.py compare OUT.json

Eighteen families were read for 1.017 (Exo 2, Fira Sans, IBM Plex Sans, Inter, Jost, Libre Franklin, Manrope,
Montserrat, Mulish, Noto Sans, Onest, Overpass, Raleway, Roboto, Rubik, Source Sans 3, Tektur, Unbounded): see
glyphs/cyrillic.py, EL_BODY and the bodies beside it."""
import json
import statistics as st
import sys

LOW = [chr(c) for c in range(0x430, 0x450)] + ['ё']
CAP = [chr(c) for c in range(0x410, 0x430)] + ['Ё']
WEIGHTS = (400, 700)


def refs(out, dirs):
    import glob
    import os

    from fontTools.pens.areaPen import AreaPen
    from fontTools.ttLib import TTFont

    def measure(glyphs, cmap, ch):
        g = glyphs[cmap[ord(ch)]]
        pen = AreaPen(glyphs)
        g.draw(pen)
        return g.width, abs(pen.value)
    found = {}
    for d in dirs:
        for w in WEIGHTS:
            for path in sorted(glob.glob(os.path.join(d, f'*-{w}.ttf'))):
                family = os.path.basename(path).rsplit('-', 1)[0]
                font = TTFont(path)
                cmap = font.getBestCmap()
                if any(ord(ch) not in cmap for ch in LOW + CAP):
                    continue
                glyphs = font.getGlyphSet()
                row = {}
                for letters, ref in ((LOW, 'н'), (CAP, 'Н')):
                    a0, i0 = measure(glyphs, cmap, ref)
                    for ch in letters:
                        a, i = measure(glyphs, cmap, ch)
                        row[ch] = (round(a / a0, 4), round(i / i0, 4))
                found.setdefault(str(w), {})[family] = row
    with open(out, 'w') as f:
        json.dump(found, f, ensure_ascii=False)
    print({w: len(v) for w, v in found.items()}, 'families')


def compare(path):
    import arris.glyphs  # noqa: F401
    from arris.draw import REGISTRY
    from arris.font import place
    from arris.geom import rings_to_shapely
    from arris.glyphs import ALIASES
    from arris.instances import params
    with open(path) as f:
        found = json.load(f)
    cmap = {chr(s.unicode): n for n, s in REGISTRY.items() if s.unicode}
    cmap.update({chr(cp): n for cp, n in ALIASES.items()})

    def outside(v, xs):                                     # how far past the families' range, as a share of their median
        return (v - xs[-1]) / st.median(xs) if v > xs[-1] else (v - xs[0]) / st.median(xs) if v < xs[0] else 0.0

    def measure(ch, p):
        rings, advance = place(cmap[ch], p)
        return advance, rings_to_shapely(rings).area
    for w in WEIGHTS:
        p = params(w)
        families = found[str(w)]
        print(f'{w}: {len(families)} families. Letter, Arris\'s width (their least, median, most), its ink the same')
        inside = total = 0
        for letters, ref in ((LOW, 'н'), (CAP, 'Н')):
            a0, i0 = measure(ref, p)
            for ch in letters:
                a, i = measure(ch, p)
                widths = sorted(f[ch][0] for f in families.values())
                inks = sorted(f[ch][1] for f in families.values())
                ow, oi = outside(a / a0, widths), outside(i / i0, inks)
                total += 1
                if abs(ow) <= 0.02 and abs(oi) <= 0.03:
                    inside += 1
                    continue
                print(f'  {ch}  width {a / a0:.2f} ({widths[0]:.2f} {st.median(widths):.2f} {widths[-1]:.2f}) {ow:+.0%}'
                      f'   ink {i / i0:.2f} ({inks[0]:.2f} {st.median(inks):.2f} {inks[-1]:.2f}) {oi:+.0%}')
        print(f'  inside their range on both: {inside} of {total}')


if __name__ == '__main__':
    if len(sys.argv) >= 4 and sys.argv[1] == 'refs':
        refs(sys.argv[2], sys.argv[3:])
    elif len(sys.argv) == 3 and sys.argv[1] == 'compare':
        compare(sys.argv[2])
    else:
        sys.exit(__doc__)
