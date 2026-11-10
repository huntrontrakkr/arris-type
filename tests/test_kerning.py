"""Pair kerning (1.017): letters that interlock close to where hand kerning
leaves them, a standard gap between the facing ends; a period keeps more
air and is pulled in by no more than half a gap."""
from __future__ import annotations

import numpy as np
import pytest

import arris.glyphs  # noqa: F401  (the registry)
from arris import kerning as K
from arris.draw import REGISTRY
from arris.font import light, place
from arris.instances import params

CMAP = {chr(s.unicode): n for n, s in REGISTRY.items() if s.unicode}
CHARS = 'AHJLOPTVWYFaoryf.'


def _kerned(w):
    p = params(w)
    placed = {CMAP[c]: place(CMAP[c], p) for c in CHARS}
    std = 2 * light(p)
    ys = np.linspace(-p.desc, p.asc + 0.3 * p.cap, K.ROWS)
    prof = {n: K.profiles(r, ys) for n, (r, _) in placed.items()}
    kerns = K.kerns(placed, p, light(p))

    def pair(a, b):
        """(kern, the narrowest gap on rows both ink, the nearest the inks come), in standard gaps."""
        a, b = CMAP[a], CMAP[b]
        k = kerns.get((a, b), 0)
        R, L = placed[a][1] - prof[a][1], prof[b][0]
        row = np.nanmin(R + L) + k
        near = min(float(np.hypot(max(R[i] + L[j] + k, 0.0), ys[j] - ys[i]))
                   for i in np.nonzero(~np.isnan(R))[0] for j in np.nonzero(~np.isnan(L))[0])
        return k / std, row / std, near / std
    return pair


@pytest.mark.parametrize('w', [300, 400, 700, 900])
def test_an_l_and_a_y_stand_a_standard_gap_apart(w):
    """The L's foot and the stem it runs up to: a standard gap, as between
    two H's (hand-kerned faces of this kind: LY 0.88 to 1.18, LT 0.74 to
    1.05, TJ 0.88 to 1.18). Until 1.017, 1.30 to 1.47."""
    pair = _kerned(w)
    for a, b in ('LY', 'LT', 'TJ'):
        k, row, near = pair(a, b)
        assert k < 0 and row == pytest.approx(1.0, abs=0.06), (a + b, round(row, 2))
    assert pair('H', 'H')[0] == 0 and pair('H', 'H')[1] == pytest.approx(1.0, abs=0.06)


@pytest.mark.parametrize('w', [400, 700, 900])
def test_letters_that_close_on_a_slant_keep_three_quarters_of_a_gap(w):
    """Closed, an L and a V, a T and an A, a T and an o come no nearer than
    three quarters of a standard gap in any direction (those faces: 0.74 to
    0.98), and no further than one and a fifth on their facing rows."""
    pair = _kerned(w)
    for a, b in ('LV', 'LW', 'TA', 'AT', 'To', 'Ta', 'Yo'):
        k, row, near = pair(a, b)
        assert k < 0, a + b
        assert near >= 0.72, (a + b, round(near, 2))
        assert row <= 1.2, (a + b, round(row, 2))


@pytest.mark.parametrize('w', [400, 700, 900])
def test_a_period_is_pulled_in_by_half_a_gap_at_most(w):
    """After a letter that overhangs it a period is pulled in, by no more
    than 0.45 of a standard gap (those faces: 0.33 to 0.47). Until 1.017 it
    went under the P's bowl by 1.4 gaps at Regular and 2.2 at Black."""
    pair = _kerned(w)
    for a in 'PFTYr':
        k, row, near = pair(a, '.')
        assert -0.5 <= k <= -0.25, (a, round(k, 2))
        assert near >= 1.15, (a, round(near, 2))
