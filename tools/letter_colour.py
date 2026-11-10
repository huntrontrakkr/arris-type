"""Colour by letter: the share of its own cell each letter inks (advance x the zone it stands in), by weight, against the median of its class."""
import sys, statistics as st
import arris.glyphs
from arris.draw import REGISTRY
from arris.font import place
from arris.instances import params
from arris.geom import rings_to_shapely
from shapely.geometry import box
cmap = {chr(s.unicode): n for n, s in REGISTRY.items() if s.unicode}
ws = [int(w) for w in sys.argv[1].split(',')]
def ink(ch, p, y0, y1):
    rings, adv = place(cmap[ch], p)
    poly = rings_to_shapely(rings)
    return poly.intersection(box(-500, y0, adv + 500, y1)).area / (adv * (y1 - y0)), poly.area, adv
for label, chars, zone in (('lower', 'abcdeghnopqsuvxyzkrtfmw', 'xh'), ('caps', 'ABCDEFGHKMNOPRSTUVWXYZ', 'cap'), ('figures', '0123456789', 'cap')):
    print(label)
    for w in ws:
        p = params(w); top = getattr(p, zone)
        d = {c: ink(c, p, 0, top)[0] for c in chars}
        med = st.median(d.values())
        print(f'  {w}: median {med:.3f}  ' + ' '.join(f'{c}{d[c] / med - 1:+.0%}' for c in sorted(d, key=d.get)))
