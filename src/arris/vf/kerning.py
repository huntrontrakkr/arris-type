"""Kerning for the variable font: the same pairs in every master, each
master's own values (``arris.kerning``), the grade keeping every advance
and so every pair."""
from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence

from arris import italic as ital
from arris.draw import REGISTRY
from arris.font import KERN_PUNCT, light, place
from arris.kerning import kerns
from arris.params import Params

from .measure import Rings
from .settings import Settings
from .space import MASTERS, Place

log = logging.getLogger(__name__)

type Pairs = dict[tuple[str, str], float]
type Upright = Mapping[Place, Mapping[str, tuple[Rings, float]]]

_names: list[str] = []
_upright: Upright = {}
_ps: Mapping[Place, Params] = {}
_italic = False


def _use(names: list[str], upright: Upright, ps: Mapping[Place, Params], italic: bool) -> None:
    global _names, _upright, _ps, _italic
    _names, _upright, _ps, _italic = names, upright, ps, italic


def _outline(w: Place, n: str) -> Rings:
    if _italic:
        return ital.polylines(place(n, _ps[w])[0])
    return _upright[w][n][0]


def _master(w: Place) -> tuple[Place, Pairs]:
    return w, kerns({n: (_outline(w, n), round(_upright[w][n][1])) for n in _names}, _ps[w], light(_ps[w]))


def kern(names: Sequence[str], upright: Upright, ps: Mapping[Place, Params],
         settings: Settings) -> tuple[dict[Place, Pairs], set[tuple[str, str]]]:
    """(each master's pairs, every pair kerned in any master): the letters
    and the punctuation that kerns, each ungraded master's kerning made in
    a process of its own, the graded masters taking the ungraded's."""
    kernable = [n for n in names if REGISTRY[n].kind in ('cap', 'lower') or n in KERN_PUNCT]
    plain = [w for w in MASTERS if w[1] == 0]
    with settings.pool(len(plain), _use, (kernable, upright, ps, settings.italic)) as pool:
        pairs_by = dict(pool.imap_unordered(_master, plain))
    for w in MASTERS:                       # grade keeps every advance, kerning included
        if w[1] != 0:
            pairs_by[w] = pairs_by[(w[0], 0, w[2])]
    all_pairs: set[tuple[str, str]] = set().union(*pairs_by.values())
    log.info('%d kerning pairs', len(all_pairs))
    return pairs_by, all_pairs
