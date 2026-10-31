"""What a build is asked for: the environment's ARRIS_VF_* variables and
the command line, read once into a Settings."""
from __future__ import annotations

import os
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from multiprocessing import get_context
from multiprocessing.pool import Pool
from pathlib import Path

PLANES_DIR = Path(__file__).resolve().parent             # planes.json, planes_italic.json: tools/vf_planes.py


@dataclass(frozen=True, slots=True)
class Settings:
    italic: bool = False                    # the italic variable font
    only: frozenset[str] | None = None      # a trial build of these glyphs alone (into build/trial/)
    out: Path = Path('build')               # where the font goes
    workers: int = 8                        # processes (glyphs are independent)
    debug: bool = False                     # every candidate's error, as tried
    refine_steps: int = 12                  # places tried for a finer grid
    prune: float = 2.0                      # font units: what a dropped master may move
    target: float = 8.9e6                   # bytes: the font, under fontbakery's 9 MB
    planes: Path | None = None              # where the drawings jump (tools/vf_planes.py), or none
    check: bool = True                      # the interpolation check at the end (else tools/vf_compare.py)

    @classmethod
    def from_env(cls, argv: Sequence[str] = (), env: Mapping[str, str] | None = None) -> Settings:
        """ARRIS_VF_ONLY, _OUT, _WORKERS, _DEBUG, _REFINE, _PRUNE, _TARGET,
        _PLANES (empty: none), _CHECK (0: none); 'italic' on the command line."""
        e = os.environ if env is None else env
        italic = 'italic' in argv
        only = frozenset(e['ARRIS_VF_ONLY'].split(',')) if e.get('ARRIS_VF_ONLY') else None
        planes = e.get('ARRIS_VF_PLANES', str(PLANES_DIR / ('planes_italic.json' if italic else 'planes.json')))
        return cls(
            italic=italic, only=only,
            out=Path(e.get('ARRIS_VF_OUT') or Path('build') / ('trial' if only else '')),
            workers=int(e.get('ARRIS_VF_WORKERS', '8')),
            debug=bool(e.get('ARRIS_VF_DEBUG')),
            refine_steps=int(e.get('ARRIS_VF_REFINE', '12')),
            prune=float(e.get('ARRIS_VF_PRUNE', '2.0')),
            target=float(e.get('ARRIS_VF_TARGET', '8.9e6')),
            planes=Path(planes) if planes else None,
            check=e.get('ARRIS_VF_CHECK', '1') != '0')

    @property
    def font(self) -> Path:
        return self.out / ('Arris-Italic[GRAD,WTCH,wght].ttf' if self.italic else 'Arris[GRAD,WTCH,wght].ttf')

    @property
    def report(self) -> Path:
        """Every result of the check, for triage."""
        return self.out / ('vf_check_italic.json' if self.italic else 'vf_check.json')

    def pool(self, jobs: int | None = None, initializer: Callable[..., object] | None = None,
             initargs: tuple = ()) -> Pool:
        """A pool of worker processes, forked (they take the glyphs' state
        as it stands: the forms installed, the drawings in memory), at most
        one a job."""
        n = self.workers if jobs is None else min(self.workers, jobs)
        return get_context('fork').Pool(max(n, 1), initializer, initargs)
