"""The optical audit along the weight (arris.audit): overshoot, contact at the
x-height, counters, the v's point, and the Mono's white per cell.

usage: uv run python tools/optics_report.py [WEIGHT ...]   (default 100 to 900 by 100)
"""
from __future__ import annotations

import sys

from arris import audit
from arris.instances import MONO_WEIGHTS, params

weights = [float(w) for w in sys.argv[1:]] or [100.0 * k for k in range(1, 10)]


def row(label, cells, w=9):
    print(f'{label:<10}' + ''.join(f'{c:>{w}}' for c in cells))


print('Overshoot past the line (top / bottom), font units')
row('', [f'{w:.0f}' for w in weights], 13)
for n in ('c', 'e', 'o', 's', 'a', 'O', 'C', 'S', 'zero'):
    row(n, [f'{t:+.1f}/{b:+.1f}' for t, b in (audit.overshoot(n, params(w)) for w in weights)], 13)
for n in ('v', 'w', 'V', 'A'):
    row(n + ' point', [f'{audit.overshoot(n, params(w))[0 if n == "A" else 1]:+.1f}' for w in weights], 13)

print('\nContact along the x-height (units of ink within 8 of the top)')
row('', [f'{w:.0f}' for w in weights])
for n in 'asgceonmu':
    row(n, [f'{audit.contact(n, params(w)):.0f}' for w in weights])

print('\nCounter width (widest hole), font units')
row('', [f'{w:.0f}' for w in weights])
for n in 'aoegO':
    row(n, [f'{audit.counter(n, params(w)):.0f}' for w in weights])

print('\nArris Mono: white per cell (mean over #24\'s letters), and the tightest letter')
for w in MONO_WEIGHTS:
    white, (n, share) = audit.mono_white(w)
    print(f'  {w:>4}  {white * 100:5.1f}%   {n} fills {share * 100:.1f}% of its cell')
