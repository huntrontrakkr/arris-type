"""One glyph, start to end: drawn at every master of the grid, aligned
(``arris.variable.align``), measured against its exact drawings between
the masters, given a finer grid where it is still off, and encoded.

Per glyph, the masters are drawn (upright: the italic is made from them),
aligned, and the alignment is checked: interpolated as the font will
(fontTools' VariationModel, on the font's own masters) at the CHECK
locations between the masters, and compared with the exact drawing there.
Where that is off by more than LOCAL_TOL, the alternatives are tried, and
whichever interpolates best is kept:

* the masters aligned each against one, the one with the most points,
  instead of each against its neighbours in the design space (the default;
  arris.variable): one master's points can pair better with the others'
  through the thin master than through a chain of neighbours;
* the masters drawn again without the jog closing (geom._close_jogs):
  cleaned of jogs, neighbouring weights can differ in structure where a
  step closes at one and not the next.

A glyph that still interpolates off its drawings somewhere gets a finer
grid: the worst place's value on an axis its grid lacks, every master of
that plane drawn (a variable font's variations are stored glyph by glyph:
masters one glyph needs cost the others nothing; gvar, written after the
build: encode.variations). Then every glyph drops the masters its drawings
do not need (encode.prune: certified within the prune tolerance
everywhere).

Glyphs are independent: ``glyph`` runs on a pool of processes, each given
the build's Context by ``use``.
"""
from __future__ import annotations

import logging
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
from itertools import product
from typing import NamedTuple

from shapely.geometry.base import BaseGeometry

from arris import geom
from arris import italic as ital
from arris.draw import REGISTRY
from arris.font import _place, place
from arris.geom import rings_to_shapely
from arris.variable import align

from . import composites
from .composites import Composite
from .context import Context
from .encode import Own, gvar_bytes, prune, tuples
from .measure import LOCAL_TOL, Rings, errors, folds, predicted
from .space import (
    CHECK,
    DEFAULT,
    GRID_AXES,
    MASTERS,
    MODEL,
    MODEL_BASE,
    NB,
    NODES,
    REFINE,
    Place,
    location,
    normal,
)

log = logging.getLogger(__name__)

NODES_MAX = 132                 # masters a glyph's grid may grow to
NM = len(MASTERS)
LEADS = ((len(NODES), None), (NM, MODEL), (NB, MODEL_BASE))     # masters that may lead, and the model that predicts the rest
_LEAD_MODELS = {NM: MODEL, NB: MODEL_BASE}


class Drawn(NamedTuple):
    """A glyph as placed at one master: its upright rings, the chamfer
    record, the advance, and its edges' names (geom.ink)."""
    rings: Rings
    record: list
    advance: float
    edges: list[str]


class Choice(NamedTuple):
    """How a glyph's masters were made to agree."""
    jogs: bool          # drawn with the jog closing (False: cleaned of jogs)
    how: str            # 'named', 'tree' or 'star': how the masters were aligned
    kind: str           # 'sparse', 'grid', 'predicted grid', 'finer grid' or 'composite'
    lead: int           # how many masters lead (the rest predicted from them)
    axes: Sequence[Sequence[float]] | None      # its grid's values on each axis


class Best(NamedTuple):
    """The candidate alignment kept so far."""
    error: float
    aligned: list[Rings]
    drawn: list[Drawn]
    choice: Choice
    nodes: list[Place]


class Finished(NamedTuple):
    """A glyph as the font carries it."""
    rings: list[Rings]              # per master of the font
    drawn: list[Drawn]              # the drawings there
    choice: Choice | None
    error: float | None
    own: Own | None                 # its own grid, or None
    why: str | None                 # why it cannot vary, or None


class Alt(NamedTuple):
    """The glyph without its finer grid: what the grid gains and costs."""
    rings: list[Rings]
    own: Own | None
    gain: float                     # the error the finer grid takes off the check's and the refinement's places
    extra: int                      # the bytes its variations add


@dataclass(slots=True)
class GlyphResult:
    """One glyph's outcome. Only plain outlines go back to the main
    process (the drawings' records hold functions)."""
    name: str
    upright: list[tuple[Rings, float]]          # per master of the font: upright rings and advance (for the kerning)
    rings: list[Rings]                          # per master of the font: its outline as the font carries it
    choice: Choice | None = None                # the alternative taken, or None
    first: float = 0.0                          # the error before ...
    error: float = 0.0                          # ... and after
    why: str | None = None                      # why it cannot vary, or None
    own: Own | None = None                      # its grid: the masters gvar interpolates it between, and its outlines at those the font has not
    shown: dict[Place, Rings] = field(default_factory=dict)   # the exact outlines drawn at the check's places
    composite: Composite | None = None
    alt: Alt | None = None


_CTX: Context | None = None


def use(ctx: Context) -> None:
    """The pool's initializer: the Context every glyph is made in."""
    global _CTX
    _CTX = ctx


def _drawn(ctx: Context, n: str, m: Place, jogs: bool = True) -> Drawn:
    if not jogs:
        jog, geom.JOG = geom.JOG, 0.0
    try:
        edges: list[str] = []
        rings, rec, adv = _place(n, ctx.p(m), record=ctx.italic, tags=edges)
        return Drawn(rings, rec, adv, edges)
    finally:
        if not jogs:
            geom.JOG = jog


class Exact:
    """A glyph's exact drawings at the places the font is checked at, made
    once each: as shapes to measure against, and as the final check sees
    them (the italic curved and flattened, font.place)."""

    def __init__(self, ctx: Context, n: str) -> None:
        self.ctx, self.n = ctx, n
        self.drawn: dict[Place, tuple] = {}
        self.shapes: dict[Place, BaseGeometry] = {}

    def __call__(self, loc: Place) -> BaseGeometry:
        if loc not in self.shapes:
            self.drawn[loc] = _place(self.n, self.ctx.p(loc), record=self.ctx.italic)
            self.shapes[loc] = rings_to_shapely(self.drawn[loc][0])
        return self.shapes[loc]

    def seen(self, loc: Place) -> Rings:
        rings, rec, _ = self.drawn[loc]
        if not self.ctx.italic:
            return rings
        q = self.ctx.p(loc)
        if REGISTRY[self.n].cell:
            q = q.with_(slant=0.0)
        return ital.polylines(ital.outline(rings, rec, q))

    def shown(self, places: Sequence[Place]) -> dict[Place, Rings]:
        """The outlines drawn here already, for the final check: it need
        not draw them again."""
        return {loc: [[tuple(q[:2]) for q in r] for r in self.seen(loc)] for loc in places if loc in self.drawn}


def _total(es: dict[Place, float]) -> float:
    return sum(min(e, 100) for e in es.values())


def _candidates(n: str, variant: list[Drawn], how: str,
                nodes: list[Place]) -> Iterator[tuple[str, int, list[Rings], list[Place]]]:
    """(kind, how many masters lead, aligned outlines, the masters they
    are at): the whole grid aligned; then, for the font's masters and
    for BASE, the rest predicted from them, as aligned with the whole
    grid and as aligned by themselves; and the font's masters alone,
    without the grid, as 1.001 had them (sparse: aligned through a tree
    over many more masters, a pair of neighbours can pair worse, ⇖
    between the grade's ends at Regular, and where the sparse layout
    adds up well the grid's cells can do worse, G at (850, 75, 75))."""
    rings = [u.rings for u in variant]
    names = [u.edges for u in variant] if how == 'named' else None

    def aligned(k: int) -> list[Rings]:
        return align(rings[:k], None if how == 'star' else [normal(m) for m in nodes[:k]],
                     names=None if names is None else names[:k])
    # the sparse layout first: where it holds everywhere (the dense
    # check: nothing past its masters, no crossing, DENSE_TOL), a glyph
    # carries 28 masters' variations, not a grid's 60 and more (the
    # variable fonts would be twice 1.001's size, past fontbakery's 9 MB)
    lead: list[Rings] | None
    try:
        lead = aligned(NM)
        yield 'sparse', NM, lead, nodes[:NM]
    except ValueError as e:
        lead = None
        log.debug('  %s %s sparse: %s', n, how, e)
    full: list[Rings] | None
    try:
        full = aligned(len(nodes))
        yield 'grid', len(nodes), full, nodes
    except ValueError as e:
        full = None
        log.debug('  %s %s grid: %s', n, how, e)
    for k, vmodel in LEADS[1:]:
        assert vmodel is not None
        if full is not None:
            yield 'predicted grid', k, predicted(full[:k], nodes, vmodel), nodes
        try:
            sub = lead if k == NM else aligned(k)
        except ValueError:
            continue
        if sub is not None:
            yield 'predicted grid', k, predicted(sub, nodes, vmodel), nodes


def _merge(a: dict[Place, float], b: dict[Place, float]) -> dict[Place, float]:
    out = dict(a)
    for k, v in b.items():
        out[k] = max(out.get(k, 0.0), v)
    return out


class _Curved:
    """The italic outlines a candidate alignment gives the font, and their
    folds (measure.folds): the choice must hold for the curved outlines the
    font carries, whose corners an alignment's zigzag opens into a loop the
    straight rings barely show (the e at 800/-100/0: 78 units). The masters'
    preparation (italic.prepare_outlines) is made once per set of drawings."""

    def __init__(self, ctx: Context, n: str) -> None:
        self.ctx, self.n = ctx, n
        self.prepared: dict[int, tuple[list, list]] = {}

    def _prep(self, variant: Sequence[Drawn], nodes_: Sequence[Place]) -> tuple[list, list]:
        key = id(variant)
        if key not in self.prepared:
            cps = [self.ctx.p(m).with_(slant=0.0) if REGISTRY[self.n].cell else self.ctx.p(m) for m in nodes_]
            self.prepared[key] = (cps, ital.prepare_outlines([u.rings for u in variant], [u.record for u in variant], cps))
        return self.prepared[key]

    def folds(self, al: Sequence[Rings], ns: Sequence[Place], kind: str, k: int, variant: Sequence[Drawn],
              nodes_: Sequence[Place], where: Sequence[Place]) -> dict[Place, float]:
        if not self.ctx.italic:
            return {}
        try:
            cps, prep = self._prep(variant, nodes_)
            if kind != 'predicted grid':
                outs = ital.aligned_outlines(al, None, None, cps[:len(al)], prepared=prep)
            else:
                outs = predicted(ital.aligned_outlines(al[:k], None, None, cps[:k], prepared=prep), ns, _LEAD_MODELS[k])
            return folds(outs, ns, where)
        except Exception as e:  # noqa: BLE001  (outlines that cannot be curved are as bad as it gets)
            log.debug('  %s italic outlines: %s', self.n, e)
            return {DEFAULT: 1e9}


def _choose(ctx: Context, n: str, up: list[Drawn], exact: Exact,
            nodes: list[Place]) -> tuple[Best | None, float | None]:
    """Candidates, in order, until one interpolates within LOCAL_TOL (else
    the best): the grid's masters aligned each against its neighbours,
    named edges first; the grid's masters past the font's (and past BASE)
    predicted from those, as the sparse layout would have them; the
    masters aligned against the one with the most points; and each of
    those again with the masters drawn without the jog closing. With the
    first candidate's error."""
    best, first = None, None
    curved = _Curved(ctx, n)
    for jogs in (True, False):
        variant = up if jogs else [_drawn(ctx, n, m, False) for m in nodes]
        for how in ('named', 'tree', 'star'):
            for kind, k, al, ns in _candidates(n, variant, how, nodes):
                # (the sparse layout also at the grid's other masters: a
                # model over any of the grid's nodes is multilinear within
                # its cells, so where it matches the drawings at every node
                # it is as good as the grid everywhere between)
                where = CHECK + [m for m in nodes if m not in ns]
                es = _merge(errors(al, exact, ns, where), curved.folds(al, ns, kind, k, variant, nodes, where))
                err = max(es.values())
                log.debug('  %s %s %s %s %d: %.1f at %s', n, 'jogs' if jogs else 'no jogs', how, kind, k, err,
                          max(es, key=es.__getitem__))
                first = err if first is None else first
                if best is None or err < best.error:
                    best = Best(err, al, variant, Choice(jogs, how, kind, k, GRID_AXES), ns)
                if best.error <= LOCAL_TOL:
                    break
            if best is not None and best.error <= LOCAL_TOL:
                break
        if best is not None and best.error <= LOCAL_TOL:
            break
    return best, first


def _refine(ctx: Context, n: str, best: Best, exact: Exact, nodes: list[Place],
            places: list[Place]) -> tuple[Best, dict[Place, float] | None]:
    """A finer grid, from the chosen way's alignment with every master
    drawn, a plane at a time while it helps: kept if it does better than
    the best candidate (not only better than the grid it started from: a
    predicted one may be best), or as well with the glyph nearer its
    drawings overall. With the errors over ``places`` as the grid stands."""
    jogs, how = best.choice.jogs, best.choice.how
    axes, ns, var = [list(a) for a in GRID_AXES], list(nodes), list(best.drawn)
    curved = _Curved(ctx, n)

    def realign(var: list[Drawn], ns: list[Place]) -> list[Rings]:
        return align([u.rings for u in var], None if how == 'star' else [normal(m) for m in ns],
                     names=[u.edges for u in var] if how == 'named' else None)

    def measure(al_: list[Rings], ns_: list[Place], var_: list[Drawn]) -> dict[Place, float]:
        return _merge(errors(al_, exact, ns_, places), curved.folds(al_, ns_, 'finer grid', len(ns_), var_, ns_, places))
    errs: dict[Place, float] | None
    try:
        al = realign(var, ns)
        errs = measure(al, ns, var)
    except ValueError:
        errs = None
    tried: set[Place] = set()
    start = (max(errs.values()), _total(errs)) if errs else None
    while errs and len(tried) < ctx.settings.refine_steps:
        # the worst place not yet tried, its value on each axis the grid
        # lacks tried in turn (a plane that does not help, or will not
        # align, is passed over)
        todo = [(e, loc) for loc, e in errs.items()
                if e > LOCAL_TOL and loc not in tried and any(v not in a for v, a in zip(loc, axes))]
        if not todo:
            break
        _, spot = max(todo)
        tried.add(spot)
        step = None
        for i in range(3):
            if spot[i] in axes[i]:
                continue
            ax2 = [sorted(a + [spot[i]]) if j == i else a for j, a in enumerate(axes)]
            have = set(ns)
            new: list[Place] = [(w, g, t) for w, g, t in product(*ax2) if (w, g, t) not in have]
            if len(ns) + len(new) > NODES_MAX:
                continue
            var2 = var + [_drawn(ctx, n, m, jogs) for m in new]
            try:
                al2 = realign(var2, ns + new)
            except ValueError:
                continue
            errs2 = measure(al2, ns + new, var2)
            if step is None or _total(errs2) < _total(step[0]):
                step = (errs2, ax2, ns + new, var2, al2)
        # kept if the glyph comes nearer its drawings overall (the worst
        # place is now on the grid; the next may be as bad)
        if step is not None and _total(step[0]) < 0.98 * _total(errs):
            errs, axes, ns, var, al = step
        log.debug('  %s finer grid, tried %s: %.1f, axes %s', n, spot, max(errs.values()), axes)
    if errs is not None and start is not None and len(ns) > len(nodes) and (
            max(errs.values()) < best.error or (max(errs.values()) <= best.error and _total(errs) < start[1])):
        best = Best(max(errs.values()), al, var, Choice(jogs, how, 'finer grid', len(ns), axes), ns)
    return best, errs


def _finish(ctx: Context, n: str, best: Best | None, first: float | None, up: list[Drawn]) -> Finished:
    """The glyph as the font carries it: its outlines per master of the
    font (the italic's curved from the aligned upright masters), its own
    grid pruned to the masters it needs; or why it cannot vary."""
    why, choice, err, own = None, None, first, None
    rings, ups = None, up[:NM]
    if best is None:
        why = 'masters will not align'
    else:
        err, al, up_all, choice, nodes_ = best
        kind, k = choice.kind, choice.lead
        try:
            rings = al
            if ctx.italic:
                # (terminal cells are curved but never slanted: font.place)
                cps = [ctx.p(m).with_(slant=0.0) if REGISTRY[n].cell else ctx.p(m) for m in nodes_]
                if kind != 'predicted grid':
                    rings = ital.aligned_outlines(al, [u.rings for u in up_all[:len(nodes_)]],
                                                  [u.record for u in up_all[:len(nodes_)]], cps)
                else:
                    # the rest predicted from the leading masters' italic
                    # outlines, curves and all
                    rings = predicted(ital.aligned_outlines(al[:k], [u.rings for u in up_all[:k]],
                                                            [u.record for u in up_all[:k]], cps[:k]),
                                      nodes_, _LEAD_MODELS[k])
            # every master's advance as the font has it (the font's masters'
            # interpolated: HVAR and the kerning come from those)
            base_adv = [u.advance for u in up_all[:NM]]
            advs = base_adv + [MODEL.interpolateFromMasters(location(m), base_adv) for m in nodes_[NM:]]
            if kind != 'sparse':                        # (sparse: the font's masters alone)
                keep = set(prune(nodes_, rings, advs, ctx.settings.prune))
                own = ([m for m in nodes_ if m in keep],
                       {m: rings[i] for i, m in enumerate(nodes_) if m in keep and i >= NM})
            rings = rings[:NM]
            ups = up_all[:NM]
        except ValueError as e:
            why = str(e)
    if why is not None or rings is None:
        # cannot vary: every master carries the default outline (reported)
        d = place(n, ctx.ps[DEFAULT])[0]
        rings = [d for _ in MASTERS]
        own = None
    return Finished(rings, ups, choice, err, own, why)


def _cost(res: Finished) -> int:
    """The bytes its variations would take."""
    rings, ups, _, _, own, why = res
    if why is not None:
        return 0
    mlocs, extra = own if own else (MASTERS, {})
    outlines = [rings[MASTERS.index(m)] if m in MASTERS else extra[m] for m in mlocs]
    base_adv = [u.advance for u in ups]
    advances = [base_adv[MASTERS.index(m)] if m in MASTERS else
                MODEL.interpolateFromMasters(location(m), base_adv) for m in mlocs]
    return gvar_bytes(tuples(mlocs, outlines, advances))


JUMP = 1.0   # units of weight: how close the two planes about a drawing's jump are brought


def _structure(ctx: Context, n: str, m: Place) -> str:
    return ','.join(str(len(r)) for r in _drawn(ctx, n, m).rings)


def _narrowed(ctx: Context, n: str, planes: Sequence[Place]) -> list[Place]:
    """The census's planes about each jump of the drawing (ten units of
    weight apart, the census's step) brought to JUMP apart by bisection on
    the drawing's structure (the rings' point counts, as the census reads
    it). Between the two planes the font interpolates across the jump, and
    a structure that changes folds as it goes (the ♧'s counter, between its
    planes at 400 and 410, by 45 units at 406): a jump confined to a unit
    of weight is a jump, not a wedge a reader can land on."""
    out: list[Place] = []
    planes = sorted(planes)
    i = 0
    while i < len(planes):
        a = planes[i]
        b = planes[i + 1] if i + 1 < len(planes) else None
        if b is None or a[1:] != b[1:] or not 0 < b[0] - a[0] <= 10:
            out.append(a)
            i += 1
            continue
        try:
            sa, sb = _structure(ctx, n, a), _structure(ctx, n, b)
            if sa != sb:
                lo, hi = a, b
                while hi[0] - lo[0] > JUMP:
                    mid: Place = (round((lo[0] + hi[0]) / 2, 2), a[1], a[2])
                    if _structure(ctx, n, mid) == sa:
                        lo = mid
                    else:
                        hi = mid
                a, b = lo, hi
        except Exception as e:  # noqa: BLE001  (a drawing that fails between the planes: the planes stay as they are)
            log.debug('  %s narrowing %s-%s: %s', n, a, b, e)
        out += [a, b]
        i += 2
    return out


def glyph(n: str) -> GlyphResult:
    """One glyph, start to end, in the Context ``use`` gave this process."""
    ctx = _CTX
    assert ctx is not None, 'glyph.use(ctx) first'
    nodes = list(NODES)
    up = [_drawn(ctx, n, m) for m in nodes]

    def plain(ups: Sequence[Drawn]) -> list[tuple[Rings, float]]:
        return [(u.rings, u.advance) for u in ups[:NM]]
    if not any(u.rings for u in up):
        return GlyphResult(n, plain(up), [u.rings for u in up[:NM]])
    exact = Exact(ctx, n)
    comp = composites.composite(n, ctx)
    if comp is not None:
        # carried as a composite: its outlines (for anchors and kerning) as
        # drawn, the exact ones at the check's places for the final check
        for loc in CHECK:
            exact(loc)
        rings = [composites.contours_at(n, m, ctx) for m in MASTERS] if ctx.italic else [u.rings for u in up[:NM]]
        return GlyphResult(n, plain(up), rings, Choice(True, 'composite', 'composite', 0, None),
                           shown=exact.shown(CHECK), composite=comp)
    best, first = _choose(ctx, n, up, exact, nodes)
    best0, errs = best, None
    # the places the census found this glyph's drawing jumping at: the
    # refinement measures there too, and a plane there confines the jump
    jumps = [q for q in _narrowed(ctx, n, ctx.planes.get(n, [])) if q not in CHECK and q not in REFINE]
    places = CHECK + REFINE + jumps
    if jumps and best is not None and best.error <= LOCAL_TOL:
        at_jumps = max(errors(best.aligned, exact, best.nodes, jumps).values())
        if at_jumps > LOCAL_TOL:
            best = best._replace(error=at_jumps)
    if best is not None and best.error > LOCAL_TOL:
        best, errs = _refine(ctx, n, best, exact, nodes, places)
    res = _finish(ctx, n, best, first, up)
    # a finer grid: the glyph without it too, what it gains (the error over
    # the check's and the refinement's places) and what it costs (bytes), so
    # the font can keep the finer grids that buy most while it fits TARGET
    alt = None
    if best is not best0 and best0 is not None and errs is not None and res.why is None:
        res0 = _finish(ctx, n, best0, first, up)
        if res0.why is None:
            gain = _total(errors(best0.aligned, exact, best0.nodes, places)) - _total(errs)
            alt = Alt(res0.rings, res0.own, gain, _cost(res) - _cost(res0))
    return GlyphResult(n, plain(res.drawn), res.rings, res.choice, first or 0.0, res.error or 0.0, res.why, res.own,
                       exact.shown(CHECK), None, alt)
