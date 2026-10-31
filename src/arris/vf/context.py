"""What every stage's workers share: the settings, the font's glyphs, the
census planes and the masters' parameters, forked into each process."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

from arris.params import Params

from .settings import Settings
from .space import Place, master_params, params

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Context:
    settings: Settings
    names: frozenset[str]                               # the font's glyphs (a composite's components must be among them)
    planes: dict[str, list[Place]] = field(default_factory=dict)    # per glyph, where its drawing jumps
    ps: dict[Place, Params] = field(default_factory=dict)           # the masters' parameters

    @classmethod
    def make(cls, settings: Settings, names: list[str]) -> Context:
        return cls(settings, frozenset(names), load_planes(settings), master_params(settings.italic))

    @property
    def italic(self) -> bool:
        return self.settings.italic

    def p(self, loc: Place) -> Params:
        """The parameters at a place (a master's as made once)."""
        return self.ps[loc] if loc in self.ps else params(loc, self.settings.italic)


def load_planes(settings: Settings) -> dict[str, list[Place]]:
    """Where a glyph's exact drawing jumps between one weight and the next
    (tools/vf_planes.py, from a census of the drawings): per glyph, (wght,
    GRAD, WTCH) places just before and just after each jump. The check looks
    there too, and a finer grid can take a plane at either, so a change the
    drawing makes in ten units of weight stays within those ten units in the
    font instead of being drawn out between two masters fifty or a hundred
    apart (a slit filling, a bar fusing, a stub going)."""
    path = settings.planes
    if path is None or not path.is_file():
        return {}
    with open(path, encoding='utf-8') as f:
        planes = {k: [(q[0], q[1], q[2]) for q in v] for k, v in json.load(f).items()}
    log.info('census planes for %d glyphs, from %s', len(planes), path)
    return planes
