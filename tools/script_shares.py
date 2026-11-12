"""A script's widths against other families': each basic letter's advance and ink as shares of a reference
letter's, in the families that have the script and in Arris, and where Arris stands outside their range.
Cyrillic is read against its own Н and н; Greek against the Latin H and n, which every Greek font carries
and which say how its Greek stands beside its Latin.

Two steps, because the reference fonts are downloads (read them with ``python -I``, from a directory of their
own, and keep this file out of it):

    python -I tools/script_shares.py refs cyrillic|greek OUT.json DIR [DIR ...]   # every <Family>-400.ttf and -700.ttf in DIR
    PYTHONPATH=src python tools/script_shares.py compare cyrillic|greek OUT.json

For 1.017 the Cyrillic was read in eighteen families (Exo 2, Fira Sans, IBM Plex Sans, Inter, Jost, Libre
Franklin, Manrope, Montserrat, Mulish, Noto Sans, Onest, Overpass, Raleway, Roboto, Rubik, Source Sans 3,
Tektur, Unbounded: see glyphs/cyrillic.py, EL_BODY and the bodies beside it) and the Greek in twenty-one
(Advent Pro, Alegreya Sans, Arimo, Comfortaa, Commissioner, Didact Gothic, Fira Sans, Geologica, IBM Plex
Sans, Inter, Jura, M PLUS 1p, Manrope, Noto Sans, Open Sans, Play, Roboto, Sofia Sans, Source Sans 3, Tektur,
Ubuntu: see glyphs/greek.py, the Ξ)."""
import json
import statistics as st
import sys

# script: (small letters, their reference, capitals, theirs)
SCRIPTS = {
    'cyrillic': ([chr(c) for c in range(0x430, 0x450)] + ['ё'], 'н', [chr(c) for c in range(0x410, 0x430)] + ['Ё'], 'Н'),
    'greek': ([chr(c) for c in range(0x3B1, 0x3CA)], 'n', [chr(c) for c in range(0x391, 0x3AA) if c != 0x3A2], 'H'),
}
WEIGHTS = (400, 700)


def refs(script, out, dirs):
    low, low_ref, cap, cap_ref = SCRIPTS[script]
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
                if any(ord(ch) not in cmap for ch in low + cap + [low_ref, cap_ref]):
                    continue
                glyphs = font.getGlyphSet()
                row = {}
                for letters, ref in ((low, low_ref), (cap, cap_ref)):
                    a0, i0 = measure(glyphs, cmap, ref)
                    for ch in letters:
                        a, i = measure(glyphs, cmap, ch)
                        row[ch] = (round(a / a0, 4), round(i / i0, 4))
                found.setdefault(str(w), {})[family] = row
    with open(out, 'w') as f:
        json.dump(found, f, ensure_ascii=False)
    print({w: len(v) for w, v in found.items()}, 'families')


def compare(script, path):
    low, low_ref, cap, cap_ref = SCRIPTS[script]
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
        for letters, ref in ((low, low_ref), (cap, cap_ref)):
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
    if len(sys.argv) >= 5 and sys.argv[1] == 'refs' and sys.argv[2] in SCRIPTS:
        refs(sys.argv[2], sys.argv[3], sys.argv[4:])
    elif len(sys.argv) == 4 and sys.argv[1] == 'compare' and sys.argv[2] in SCRIPTS:
        compare(sys.argv[2], sys.argv[3])
    else:
        sys.exit(__doc__)
