"""The variable font from the glyphs as they stand: a master font at every
master (``arris.font.build``), the designspace over them with the forms'
rules and the named instances, fontTools' varLib build, the STAT table,
and every glyph's variations written over its own masters (``encode``).
The font is kept under its size budget: without any glyph's finer grid
first, then the finer grids that buy most accuracy per byte."""
from __future__ import annotations

import io
import logging
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from fontTools.designspaceLib import (
    AxisDescriptor,
    DesignSpaceDocument,
    InstanceDescriptor,
    RuleDescriptor,
    SourceDescriptor,
)
from fontTools.otlLib.builder import buildStatTable
from fontTools.ttLib import TTFont
from fontTools.varLib import build as varlib_build

from arris.font import add_meta, build
from arris.instances import NAMES
from arris.params import Params

from . import encode
from .composites import Composite
from .forms import Form
from .glyph import Alt
from .kerning import Pairs
from .measure import Rings
from .settings import Settings
from .space import AXES, FAMILY, MASTERS, Place, style_name

log = logging.getLogger(__name__)


@dataclass(slots=True)
class Outlines:
    """Every glyph as the font carries it, gathered from the glyph stage."""
    names: list[str]
    upright: dict[Place, dict[str, tuple[Rings, float]]]        # per master, per glyph: upright rings and advance
    aligned: dict[Place, dict[str, tuple[Rings, float]]]        # per master, per glyph: the outline carried, advance
    own: dict[str, encode.Own] = field(default_factory=dict)    # glyph -> its grid's masters, outlines at those past the font's
    alts: dict[str, Alt] = field(default_factory=dict)          # glyph -> (outlines, own) with its finer grid, gain, bytes
    shown: dict[tuple[str, Place], Rings] = field(default_factory=dict)   # (glyph, place) -> exact outline, for the check
    composites: dict[str, Composite] = field(default_factory=dict)
    frozen: list[tuple[str, str]] = field(default_factory=list)          # glyphs that cannot vary, and why
    chosen: list[tuple] = field(default_factory=list)                    # glyphs that took an alternative


@dataclass(frozen=True, slots=True)
class Masters:
    """What the master fonts are built from, forked into the workers."""
    settings: Settings
    names: list[str]
    ps: Mapping[Place, Params]
    fea: str
    outlines: Outlines
    pairs_by: Mapping[Place, Pairs]
    all_pairs: frozenset[tuple[str, str]]
    tmp: Path


_MASTERS: Masters | None = None


def _use(job: Masters) -> None:
    global _MASTERS
    _MASTERS = job


def _build_master(i: int) -> int:
    job = _MASTERS
    assert job is not None
    m = MASTERS[i]
    pairs = {pr: job.pairs_by[m].get(pr, 0) for pr in job.all_pairs}
    out = job.outlines
    build(str(job.tmp / f'master-{i}.ttf'), job.names, job.ps[m], family=FAMILY,
          style=style_name(m[0], job.settings.italic), weight=m[0], fea=job.fea, placed=out.aligned[m],
          kern_pairs=pairs, stat=False,
          components={n: [(c, dx, dy) for c, (dx, dy) in zip(cs, offs[m])] for n, (cs, offs) in out.composites.items()})
    return i


def make_vf(job: Masters, forms: Mapping[str, Form]) -> TTFont:
    """The variable font from the master fonts as the glyphs now stand."""
    doc = DesignSpaceDocument()
    for tag, name, lo, df, hi in AXES:
        ax = AxisDescriptor()
        ax.tag, ax.name, ax.minimum, ax.default, ax.maximum = tag, name, lo, df, hi
        doc.addAxis(ax)
    with job.settings.pool(len(MASTERS), _use, (job,)) as pool:     # the master fonts are independent
        list(pool.imap_unordered(_build_master, range(len(MASTERS))))
    for i, m in enumerate(MASTERS):
        src = SourceDescriptor()
        src.path, src.location = str(job.tmp / f'master-{i}.ttf'), {'Weight': m[0], 'Grade': m[1], 'Watch': m[2]}
        doc.addSource(src)
    for n, (alt, regions) in forms.items():
        if regions:
            rule = RuleDescriptor()
            rule.name = f'{n} second form'
            rule.conditionSets = [[{'name': 'Weight', 'minimum': w, 'maximum': 900},
                                   {'name': 'Grade', 'minimum': glo, 'maximum': ghi},
                                   {'name': 'Watch', 'minimum': tlo, 'maximum': thi}]
                                  for w, glo, ghi, tlo, thi in regions]
            rule.subs = [(n, alt)]
            doc.addRule(rule)
    for w in NAMES:
        inst = InstanceDescriptor()
        inst.familyName, inst.styleName = FAMILY, style_name(w, job.settings.italic)
        inst.location = {'Weight': w, 'Grade': 0, 'Watch': 0}
        doc.addInstance(inst)
    vf, _, _ = varlib_build(doc)
    buildStatTable(vf, stat_axes(job.settings.italic))
    name_variations(vf, job.settings.italic)
    out = job.outlines
    encode.variations(vf, job.names, out.aligned, out.own, out.composites)
    if out.composites:
        encode.composite_variations(vf, out.composites, out.aligned, job.settings.prune)
    vf['name'].names = [nm for nm in vf['name'].names if nm.platformID != 1]   # Windows names only
    add_meta(vf)
    return vf


def stat_axes(italic: bool, watch: bool = True) -> list[dict]:
    """The STAT table's axes and their named values (buildStatTable's
    form); without the watch axis for a build that leaves it out."""
    axes = [
        {'tag': 'wght', 'name': 'Weight',
         'values': [{'value': w, 'name': nm, 'flags': 0x2 if w == 400 else 0} for w, nm in NAMES.items()]},
        {'tag': 'GRAD', 'name': 'Grade', 'values': [{'value': 0, 'name': 'Normal', 'flags': 0x2}]},
        {'tag': 'WTCH', 'name': 'Watch', 'values': [{'value': 0, 'name': 'Measured', 'flags': 0x2},
                                                    {'value': 100, 'name': 'Watch'}]},
        # the upright and the italic are one family: each names its place on ital
        {'tag': 'ital', 'name': 'Italic',
         'values': [{'value': 1, 'name': 'Italic'}] if italic else
                   [{'value': 0, 'name': 'Roman', 'flags': 0x2, 'linkedValue': 1}]},
    ]
    return axes if watch else [a for a in axes if a['tag'] != 'WTCH']


def name_variations(vf: TTFont, italic: bool) -> None:
    """Name ID 25, the prefix of the PostScript names of the font's
    instances: the family's, and the italic's ending in Italic."""
    vf['name'].setName(FAMILY + ('Italic' if italic else ''), 25, 3, 1, 0x409)


def size(vf: TTFont) -> int:
    b = io.BytesIO()
    vf.save(b)
    return len(b.getvalue())


def assemble(settings: Settings, names: Sequence[str], ps: Mapping[Place, Params], fea: str, outlines: Outlines,
             pairs_by: Mapping[Place, Pairs], all_pairs: set[tuple[str, str]], forms: Mapping[str, Form]) -> TTFont:
    """The variable font, within its size budget: without any glyph's
    finer grid first; then the finer grids that buy most accuracy per byte
    (Outlines.alts: the error they take off the check's and the
    refinement's places, for the bytes their variations add), while the
    font stays under settings.target."""
    job = Masters(settings, list(names), ps, fea, outlines, pairs_by, frozenset(all_pairs), Path(tempfile.mkdtemp()))
    vf = make_vf(job, forms)
    bytes_ = size(vf)
    log.info('the font without finer grids: %.2f MB', bytes_ / 1e6)
    alts, target = outlines.alts, settings.target
    if alts and bytes_ < target:
        room = target - bytes_
        take = []
        for n, alt in sorted(alts.items(), key=lambda kv: (kv[1].extra > 0, -kv[1].gain / max(kv[1].extra, 1))):
            if alt.gain <= 0:
                continue
            if alt.extra <= room:
                take.append(n)
                room -= max(alt.extra, 0)
        for n in take:
            rings, own = alts[n].rings, alts[n].own
            for i, m in enumerate(MASTERS):
                outlines.aligned[m][n] = (rings[i], outlines.aligned[m][n][1])
            outlines.own.pop(n, None)
            if own:
                outlines.own[n] = own
        if take:
            vf = make_vf(job, forms)
            bytes_ = size(vf)
        log.info('%d of %d glyphs keep their finer grid: %.2f MB', len(take), len(alts), bytes_ / 1e6)
    if bytes_ > target:
        log.warning('WARNING: %.2f MB, over the %.1f MB target', bytes_ / 1e6, target / 1e6)
    return vf
