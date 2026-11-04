"""The optical audit's rules along the weight (arris.audit): a bowl's
overshoot grows with the weight and stays under its cap, flat sides stay on
their lines; and the Mono's white per cell, which waits on the width
decision (#24). (v's and w's points sink below the baseline as the stroke
grows, by design: the audit reports them, no rule holds them.)"""
from __future__ import annotations

from itertools import pairwise

import pytest

from arris import audit
from arris.draw import OPTICAL
from arris.instances import params

WEIGHTS = (100, 400, 700, 900)


@pytest.mark.parametrize('name', ['c', 'o', 'O', 'zero'])
def test_overshoot_grows_with_the_weight(name):
    """Every side of a bowl overshoots, more at each heavier weight (the
    measure alone gave Black a fifth of Thin's: #26), and never past the cap."""
    seen = [audit.overshoot(name, params(w)) for w in WEIGHTS]
    H = params(400).cap if name in ('O', 'zero') else params(400).xh
    for side in (0, 1):
        vals = [s[side] for s in seen]
        assert all(b >= a - 0.05 for a, b in pairwise(vals)), (name, side, vals)
        assert vals[0] > 0 and vals[-1] <= OPTICAL['over_max'] * H + 0.05, (name, side, vals)


def test_flat_lines_stay_on_their_lines():
    """A stem's end and a bar sit on their lines: no overshoot (H, n's foot, x)."""
    for w in WEIGHTS:
        for name in ('H', 'n', 'x'):
            _, bottom = audit.overshoot(name, params(w))
            assert abs(bottom) < 0.5, (name, w, bottom)


@pytest.mark.xfail(strict=True, reason='#24: the Mono width pass waits on the counter decision')
def test_mono_keeps_its_white_at_every_weight():
    """Arris Mono keeps a fifth of its cell white or more, Light to Bold (Fira
    Code keeps a quarter at Regular)."""
    for w in (300, 400, 700):
        white, _ = audit.mono_white(w)
        assert white >= 0.20, (w, white)
