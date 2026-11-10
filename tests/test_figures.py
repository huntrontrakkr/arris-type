"""The figures in a line of text (1.017): proportional by default, spaced
by their own white and kerned as the letters are; the watch's tabular set
behind ``tnum``, the same drawings on one cell."""
from __future__ import annotations

import numpy as np
import pytest
from shapely import affinity

import arris.glyphs  # noqa: F401  (the registry)
from arris import kerning as K
from arris.draw import PROPORTIONAL_FIGS
from arris.font import light, place
from arris.geom import rings_to_shapely
from arris.glyphs.features import FIGS, fea
from arris.instances import params

NAMES = list(FIGS) + ['H', 'period', 'comma', 'parenleft']


def _set(w):
    p = params(w)
    placed = {n: place(n, p) for n in NAMES}
    std = 2 * light(p)
    ys = np.linspace(-p.desc, p.asc + 0.3 * p.cap, K.ROWS)
    prof = {n: K.profiles(r, ys) for n, (r, _) in placed.items()}
    kerns = K.kerns(placed, p, light(p))

    def near(a, b):
        """The nearest the inks of a and b come, kerned, in standard gaps."""
        k = kerns.get((a, b), 0)
        R, L = placed[a][1] - prof[a][1], prof[b][0]
        return min(float(np.hypot(max(R[i] + L[j] + k, 0.0), ys[j] - ys[i]))
                   for i in np.nonzero(~np.isnan(R))[0] for j in np.nonzero(~np.isnan(L))[0]) / std
    return near, kerns


@pytest.mark.parametrize('w', [300, 400, 700, 900])
def test_figures_stand_as_far_apart_as_letters(w):
    """Faces of this kind set a 0 by a 0 0.63 to 0.88 of the white between
    two stems apart and a 1 by a 1 0.62 to 0.93 (Chakra Petch, Oxanium,
    Exo 2, Rajdhani, Tomorrow). On the watch's cell, the default until
    1.017, the 0s stood 0.34 apart and the 1s 1.8 to 2.4."""
    near, _ = _set(w)
    assert 0.6 <= near('zero', 'zero') <= 0.95
    assert 0.5 <= near('one', 'one') <= 0.95
    assert near('one', 'zero') <= 1.0 and near('zero', 'one') <= 1.0
    for a in FIGS:                                          # (those faces: every pair 0.14 to 1.26, the tightest 44 and 77)
        for b in FIGS:
            assert 0.3 <= near(a, b) <= 1.1, (a, b, round(near(a, b), 2))


@pytest.mark.parametrize('w', [400, 700, 900])
def test_figures_are_kerned_with_the_marks(w):
    """A period after a 7 and a 1 after a parenthesis close as they do after
    letters (those faces: 7 and period 1.3 to 1.8 gaps, parenthesis and 1
    0.6 to 0.96; unkerned they stood 2.0 to 2.2 and 1.6 to 2.1)."""
    near, kerns = _set(w)
    assert kerns.get(('seven', 'period'), 0) < 0
    assert near('seven', 'period') <= 1.8
    assert near('parenleft', 'one') <= 1.35


@pytest.mark.parametrize('w', [400, 900])
def test_the_tabular_twins_are_the_same_figures_on_one_cell(w):
    p = params(w)
    for n in PROPORTIONAL_FIGS:
        rings, _ = place(n, p)
        twin, cell = place(n + '.tnum', p)
        assert cell == pytest.approx(p.fig_adv)
        a, b = rings_to_shapely(rings), rings_to_shapely(twin)
        b = affinity.translate(b, a.bounds[0] - b.bounds[0], 0)
        assert a.symmetric_difference(b).area <= 0.002 * a.area, n          # the same drawing, to a unit's rounding
        x0, _, x1, _ = rings_to_shapely(twin).bounds
        assert x0 == pytest.approx(cell - x1, abs=0.35 * p.fig_w) and x0 >= 0 and x1 <= cell      # in its cell
    assert place('one', p)[1] < 0.75 * place('zero', p)[1]         # the 1 takes a 1's room
    assert place('one', p.with_(mono=True))[1] == place('zero', p.with_(mono=True))[1]      # in Mono all share the cell


def test_every_figure_feature_takes_either_set():
    text = fea(False)
    assert 'feature tnum { sub @pfig by @tfig; } tnum;' in text
    assert 'feature pnum { sub @tfig by @pfig; } pnum;' in text
    for tag in ('sups', 'subs', 'sinf', 'numr', 'dnom'):
        line = next(l for l in text.splitlines() if l.startswith(f'feature {tag} '))
        assert 'sub @figs by' in line and 'sub @tnum by' in line
    assert 'sub zero.tnum by zero.zero.tnum;' in text and 'sub five.tnum by five.ss02.tnum;' in text
    assert "sub @pfig colon' @pfig by colon.case;" in text
