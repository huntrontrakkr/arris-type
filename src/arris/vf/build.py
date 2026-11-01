"""The build, stage by stage: the glyphs and their forms, every glyph
aligned and refined on a pool of processes, the composites flattened, the
kerning, the master fonts and the variable font within its budget, and
the check. ``main`` is ``python -m arris.vf [italic]``."""
from __future__ import annotations

import logging
import sys
import time
from collections.abc import Sequence
from pathlib import Path

import arris.glyphs  # noqa: F401  (every glyph registered)
from arris.draw import REGISTRY
from arris.glyphs.features import fea

from . import check, composites, forms, glyph, kerning
from .assemble import Outlines, assemble
from .context import Context
from .glyph import Alt
from .settings import Settings
from .space import MASTERS, NODES

log = logging.getLogger('arris.vf')

FIGS = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine']


class _Minutes(logging.Formatter):
    """Each line with the minutes since the build started."""

    def __init__(self) -> None:
        super().__init__('%(message)s')
        self.t0 = time.monotonic()

    def format(self, record: logging.LogRecord) -> str:
        return f'[{(time.monotonic() - self.t0) / 60:.1f} min] {super().format(record)}'


def setup_logging(debug: bool = False) -> None:
    """The build's lines to stdout, with the minutes elapsed; debug: every
    candidate's error, as tried."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_Minutes())
    log.addHandler(handler)
    log.setLevel(logging.DEBUG if debug else logging.INFO)


def glyph_names(settings: Settings) -> list[str]:
    """The font's glyphs, the figures first: every registered glyph but the
    italic's own forms and the ligatures (or the trial's few)."""
    names = FIGS + [n for n in REGISTRY if n not in FIGS and not n.endswith('.ital')
                    and not (isinstance(REGISTRY[n].kind, tuple) and REGISTRY[n].kind[0] == 'liga')]
    if settings.only:
        names = [n for n in names if n in settings.only]
    return names


def gather(settings: Settings, ctx: Context, names: Sequence[str]) -> Outlines:
    """Every glyph through the glyph stage, on the pool, into one Outlines."""
    out = Outlines(list(names), {m: {} for m in MASTERS}, {m: {} for m in MASTERS})
    with settings.pool(None, glyph.use, (ctx,)) as pool:
        for r in pool.imap_unordered(glyph.glyph, names, chunksize=4):
            n, rings, own = r.name, r.rings, r.own
            if r.composite is not None:
                out.composites[n] = r.composite
            if r.alt is not None:
                # (the font starts without the finer grid: the budget decides)
                out.alts[n] = Alt(rings, own, r.alt.gain, r.alt.extra)
                rings, own = r.alt.rings, r.alt.own
            for loc, shown in r.shown.items():
                out.shown[n, loc] = shown
            if r.why is not None:
                out.frozen.append((n, r.why))
            if own:
                out.own[n] = own
            c = r.choice
            if c is not None and (c.jogs, c.how, c.kind) != (True, 'named', 'grid'):
                out.chosen.append((n, 'jogs kept' if not c.jogs else '', c.how, c.kind, round(r.first, 1), round(r.error, 1)))
            for i, m in enumerate(MASTERS):
                out.upright[m][n] = r.upright[i]                    # (rings, advance)
                out.aligned[m][n] = (rings[i], r.upright[i][1])
    chosen = out.chosen
    log.info('placed and aligned %d glyphs in %d masters; %d took an alternative, interpolating better so: %s',
             len(names), len(MASTERS), len(chosen), sorted(chosen, key=lambda c: -c[4])[:12])
    log.info("%d glyphs keep the font's masters alone; %d masters predicted from the font's; %d took a finer grid; "
             'after pruning, %.1f masters a glyph on average (of %d), %d past the font\'s in all',
             sum(c[3] == 'sparse' for c in chosen), sum(c[3] == 'predicted grid' for c in chosen),
             sum(c[3] == 'finer grid' for c in chosen),
             sum(len(v[0]) for v in out.own.values()) / max(len(out.own), 1), len(NODES),
             sum(len(v[1]) for v in out.own.values()))
    out.composites = {n: composites.flat(out.composites, n) for n in list(out.composites)}
    log.info('%d glyphs carried as composites (their components translated at every master)', len(out.composites))
    log.info('aligned; %d glyphs could not vary: %s', len(out.frozen), out.frozen[:10])
    return out


def run(settings: Settings) -> Path:
    """The variable font settings asks for, written to settings.font."""
    names, forms_ = forms.install(glyph_names(settings), settings.italic)
    log.info('forms: %s', {n: (f.alt, [tuple(r) for r in f.regions[:2]], len(f.regions)) for n, f in forms_.items()})
    ctx = Context.make(settings, names)
    outlines = gather(settings, ctx, names)
    pairs_by, all_pairs = kerning.kern(names, outlines.upright, ctx.ps, settings)
    features = '' if settings.only else fea()           # (a trial's few glyphs: no features)
    vf = assemble(settings, names, ctx.ps, features, outlines, pairs_by, all_pairs, forms_)
    # (a trial's few glyphs go apart: build/trial/, the fonts in build/ untouched)
    settings.out.mkdir(parents=True, exist_ok=True)
    vf.save(settings.font)
    log.info('wrote %s', settings.font)
    if not settings.check:
        # the release workflow checks the font in a job of its own (tools/vf_compare.py --all),
        # after the font and the drawing cache are safe: a check that runs out of memory
        # then costs the check, not the build
        log.info('interpolation check left to tools/vf_compare.py (ARRIS_VF_CHECK=0)')
        return settings.font
    check.check(settings, names, outlines.shown)
    topology_report(settings)
    return settings.font


def topology_report(settings: Settings) -> None:
    """The built font's outlines along the axes (arris.topology): every
    simple glyph at its masters, between them and along the weight; the
    glyphs that fold by three units or more logged, every fault written
    beside the check's report."""
    from arris import topology
    reps = topology.scan_font(settings.font, procs=settings.workers)
    worst = sorted(((max((x.size for x in r.faults if x.kind == 'cross'), default=0.0), r.name) for r in reps), reverse=True)
    bad = [(w, n) for w, n in worst if w >= 3.0]
    log.info('topology: %d of %d glyphs fold by 3 units or more somewhere; worst %s',
             len(bad), len(reps), ', '.join(f'{n} {w:.0f}' for w, n in bad[:12]))
    out = settings.out / ('topology_italic.json' if settings.italic else 'topology.json')
    topology.dump(reps, out)
    log.info('topology faults written to %s', out)


def main(argv: Sequence[str] | None = None) -> int:
    settings = Settings.from_env(sys.argv[1:] if argv is None else argv)
    setup_logging(settings.debug)
    run(settings)
    return 0
