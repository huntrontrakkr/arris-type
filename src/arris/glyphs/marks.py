"""Diacritics, and every accented letter composed from its decomposition.

Marks are drawn in the same language: acute and grave are 45-degree strokes
cut flat top and bottom; circumflex and caron are small gables; dieresis
and dot are stem-square dots; the tilde steps at 45 degrees; the breve is a
small chamfered bowl and the ring an octagon; the cedilla is a flat tab and
the ogonek turns on a chamfered corner.

Placement is measured, not tabulated: a mark above sits a fixed gap above
the base's own highest ink (so it clears an ascender or a capital without a
per-letter list); a mark below hangs from the baseline. Capitals take a
flatter mark size, so accented capitals stay inside the line.
"""
from __future__ import annotations

import unicodedata

from fontTools import agl

from ..draw import B, REGISTRY, Glyph, glyph
from ..params import SQRT2


def gap(p):
    """White between a base and a mark above it (the i's dot gap)."""
    return max(p.m, 0.4 * p.sv)


MARK_GAIN = 0.5     # of what its letter's strokes gain past the Regular, the share an accent's take (mark_params)
HANG_GAIN = 1 / 3   # the same for a mark hanging off its letter: the cedilla, the ogonek, the horn


def mark_params(p, gain=None):
    """The parameters a mark is drawn with: its letter's up to its cut's
    Regular; past it, the Regular's own (draw.held_at: the same cut, grade,
    watch balance and slant) with strokes that take ``gain`` of what the
    letter's gain: MARK_GAIN for an accent, HANG_GAIN for a mark that
    hangs off its letter (the ogonek, the horn). Its breaks stay the
    Regular's, and its whites (kept, whites).

    Drawn with the letter's own strokes at a size that grew with them, an
    accent at Black carried 1.3 to 2.0 times the ink of other families' for
    its letter and stood 1.2 to 1.6 times as tall (the acute 1.48 and 1.35,
    the caron 1.99, the tilde 1.63 and 1.62; forty-two families): the
    owner, 2026-11-12, "all bloated and ugly at black". Held at the
    Regular's size with seven tenths of the letter's gain its dots still
    spread (a dieresis's 134 units apart at Black for the Regular's 72):
    "They are still too far apart". Held at the Regular's weight outright
    ("Can you just make the accents at the regular weight?") an accent was
    a hairline on a Black letter, four tenths of its stem: "It looks
    wrong. Can we look at what other heavy or black weights look like on
    other languages and try to figure out what we can do better?"

    Fifty-nine families, each mark's thickest stroke over its letter's
    stem at Regular and at the heaviest weight: an accent's is 0.76 to
    0.86 of the stem at Regular and 0.62 to 0.71 at the heaviest, and of
    what the stem gains between the two it takes half (0.49 to 0.63 at the
    median, accent by accent); the white between it and its letter closes
    a little (0.12 of the x-height to 0.09) and a dieresis's dots thicken
    without drifting apart. Half the gain and the Regular's whites put
    Arris's accents at 0.62 to 0.66 of the stem at Black. A hook under a
    letter takes about the same in those families and stays small (0.68 to
    0.71 of the stem, 0.45 to 0.48 of its letter's width); Arris's ogonek
    starts at a whole stem at Regular where theirs is 0.84, and at a third
    of the gain stands 0.67 and 0.46 at Black (at two thirds, 0.92 and
    0.64).

    A set derived from a font's (small capitals) has no Regular of its own
    to ask for: its accents take the strokes that stand to its module as
    the Regular's do, a module and a half to the stem (letterframe.heft)."""
    from ..draw import _cut, held_at
    gain = MARK_GAIN if gain is None else gain
    q = held_at(p)
    if q is p and _cut(p) is None:
        r = 1.5 * p.m / p.sv
        if r >= 1.0:
            return p
        q = p.with_(sv=p.sv * r, sh=p.sh * r, sd=p.sd * r, ss=p.ss * r, c=p.c * r)
    if q is p or not gain:
        return q
    # (its breaks stay the Regular's, as the letters' inside corners do past it (draw.fill_leg): on breaks
    # that grew with its strokes a ring's counter filled to a pinhole at Black)
    mix = lambda a, b: a + gain * (b - a)
    return q.with_(sv=mix(q.sv, p.sv), sh=mix(q.sh, p.sh), sd=mix(q.sd, p.sd), ss=mix(q.ss, p.ss))


JOIN_FILL = 4.0     # units across: the least piece that is a join's fill (kept)


def whites(g):
    """The parameters a mark's whites are measured by (between a
    dieresis's dots, a double acute's strokes): the Regular's past it, so
    the dots thicken and do not drift apart (kept, draw_above)."""
    return getattr(g, 'reg', g.p)


def kept(g, fn, *args, joined=False, gain=None, apart=False):
    """Draw a mark into g with its own parameters (mark_params): in g
    itself where they are g's; else in a drawing of its own, stamped into
    g. A mark that hangs from its letter reads the letter's ink and
    parameters off that drawing (``base_ink``, ``own_p``, ``own_sh``), and
    a line it must meet flush is the letter's too (``butt``).

    ``joined``: the corners the mark makes with its letter are filled as
    they are in the letter's own drawing up to the Regular. Stamped in
    alone, an ogonek lost those fills where it became the Regular's (700
    square units of į between weights 400 and 401). The two are finished
    together in a drawing apart, and what that adds where they meet is
    stamped in with the mark. Only that: with the letter's ink stamped in
    a second time under the mark, the italic no longer knew the letter's
    own corners for its own, and the ą's bowl was cut straight at Bold and
    ExtraBold. ``gain``: mark_params'. ``apart``: in a drawing of its own at
    every weight (a mark that is a glyph by itself: a sign's own drawing
    breaks a sharp corner another way than a mark's, and the ¸ changed by
    1,700 square units between weights 400 and 401)."""
    q = mark_params(g.p, gain)
    if q is g.p and not apart:
        return fn(g, *args)

    def drawn(with_letter):
        t = Glyph(q, W=g.W)
        t.finished = True                                   # (the host leaves its corners as they are: Glyph.outline)
        t.reg = mark_params(g.p, 0.0)
        t.base_ink = g.extra[0] if g.extra else None
        t.own_p, t.own_sh = g.p, g.sh
        if with_letter:
            t.extra = [g.extra[0]]
            t.extra_chamfers = list(g.extra_chamfers)
        fn(t, *args)
        return t
    target = drawn(False)
    g.butt += target.butt
    if not (target.strokes or target.overlay or target.extra):
        return
    g.add_glyph(target)
    if joined and len(g.extra) > 1:
        import shapely

        from ..geom import rings_to_shapely
        letter, mark = g.extra[0], g.extra[-1]
        whole = rings_to_shapely(drawn(True).outline()[0])
        more = whole.difference(shapely.union_all([letter, mark]).buffer(0.05))
        # (a fill, not the sliver two outlines leave where they all but agree: under JOIN_FILL across it
        # is no corner's fill, and stamped in it met the letter at a point: the italic ç at Black, grade
        # 100, on the watch's ladder, a unit and a half across; Arris Mono Narrow Bold Italic's ą and Ą, a
        # piece three units by four)
        # (and grown back over the hair it was cut clear of the two by: cut clear, a fill lay beside them and
        # met them at a point, a ring of its own, ę ǫ Ę Ų at every weight and į ą ų Ą Į from Medium)
        # (and at the join: no higher than two breaks over the mark's top. Above it is no fill but the
        # letter finished again on the mark's breaks, a sliver up the stem: the whole of the Į's at 600, a
        # wedge that leaned the Ą's right leg at Bold)
        top = mark.bounds[3] + 2 * q.c
        g.extra += [q_.buffer(0.1, join_style='mitre') for q_ in getattr(more, 'geoms', [more])
                    if q_.area > 1.0 and q_.distance(letter) < 1.0 and q_.distance(mark) < 1.0
                    and not q_.buffer(-JOIN_FILL / 2).is_empty and q_.bounds[3] <= top]


def size(p, case):
    """Height of a stroke mark (acute, circumflex...): two modules and half
    a stem (a module and a half on a capital), the stem no more than the
    Regular's (mark_params)."""
    return (2.0 if case == 'lc' else 1.5) * p.m + 0.5 * min(p.sv, 1.5 * p.m)


def _dot(g, x, y):
    s = g.p.dot()
    g.stroke((x, y, s), (x, y + s))


def acute(g, x, y, case, sign=1):
    p = g.p
    a = size(p, case)
    k = p.sd / SQRT2
    # centreline rises a over a; flat cuts at y and y + a
    g.stroke((x - sign * a / 2, y), (x + sign * a / 2, y + a), start='h', end='h')


def grave(g, x, y, case):
    acute(g, x, y, case, sign=-1)


def circumflex(g, x, y, case, flip=False):
    """A small gable, its point cut flat an edge break each side (as the A's)."""
    p = g.p
    w = size(p, case)                                       # 45 degrees: as tall as each side is wide
    f = p.c
    if not flip:
        pts = [(x - w, y), (x - f, y + w - f), (x + f, y + w - f), (x + w, y)]
    else:
        pts = [(x - w, y + w), (x - f, y + f), (x + f, y + f), (x + w, y + w)]
    g.stroke(*pts, start='h', end='h')


def caron(g, x, y, case):
    """The circumflex turned over. Its point is a stroke's underside, which
    comes down as the stroke thickens: past the Regular it is lifted by as
    much, so the white under it stays the Regular's (43 units over a c; it
    closed to 29 at Black, where other families keep 0.09 of the x-height)."""
    from ..draw import _thickness
    r = whites(g)
    if r is not g.p:
        level = (1.0, 0.0)
        y += (_thickness(g.p, g.sh)(level) - _thickness(r, g.sh * r.sh / g.p.sh)(level)) / 2
    circumflex(g, x, y, case, flip=True)


def dieresis(g, x, y, case):
    p = g.p
    d = p.dot() + max(1.2 * p.m, 0.8 * whites(g).dot())    # (the white between the dots: the Regular's past it)
    _dot(g, x - d / 2, y)
    _dot(g, x + d / 2, y)


def dotaccent(g, x, y, case):
    _dot(g, x, y)


def macron(g, x, y, case):
    p = g.p
    w = size(p, case)
    g.stroke((x - w, y + g.sh / 2), (x + w, y + g.sh / 2))


def tilde(g, x, y, case):
    """Up at 45 degrees, along, down, along, up: the tilde as a step."""
    p = g.p
    w = size(p, case)
    h = w / 2.5
    a = (2 * w - 3 * h) / 2
    x0 = x - w
    y = y + p.sd / SQRT2                                    # the centreline sits half a stroke up
    pts = [(x0, y), (x0 + h, y + h), (x0 + h + a, y + h), (x0 + 2 * h + a, y), (x0 + 2 * h + 2 * a, y),
           (x0 + 3 * h + 2 * a, y + h)]
    g.stroke(*pts, start='v', end='v')


def breve(g, x, y, case):
    """A small chamfered cup. Its sides thin at heavy weights, as accents do,
    so the cup stays open: twice the marks' gap across, room for its inner
    corners' fills and a gap between them."""
    p = g.p
    w = size(p, case)
    h = 0.75 * w
    t = min(p.sv, w - gap(p))                               # side thickness
    xl, xr = x - w + t / 2, x + w - t / 2
    g.stroke((xl, y + h + g.sh / 2, t), B(xl, y + g.sh / 2, p.m / 2),
             B(xr, y + g.sh / 2, p.m / 2, t), (xr, y + h + g.sh / 2))


RING = 1.5          # the ring's counter across, in modules
RING_STROKE = 1.25  # the most its stroke grows to, in modules


def ring(g, x, y, case):
    """A small ring of eight sides, an octagon inside and out, after
    Tomorrow's (the owner, 2026-11-12: "Do Tomorrow because it's better"):
    its stroke 0.7 of the stem, up to a module and a quarter and no further
    (accents lighten at heavy weights), its counter a module and a half
    across. Three tenths of the cap height at Regular and a third from
    Bold, as faces of this kind draw it (Chakra Petch, Oxanium, Exo 2,
    Rajdhani: 0.26 to 0.31 of it, the stroke 0.56 to 0.70 of the stem; at
    their heaviest 0.26 to 0.36 and 0.41 to 0.59).

    It was a square on four bowl corners. A bowl corner's diagonal is as
    thick as the alphabet's diagonals, thicker than the ring's sides: the
    counter came out a diamond and the outside all but square, a block with
    a pinhole at Black. Its eight sides are one thickness.

    Until 1.017 it was drawn in the full stem up to two modules, round a
    counter of two: 0.38 of the cap height at Regular and half of it from
    Bold, twice any other accent, and Å stood 1.47 to 1.60 cap heights tall
    (those faces 1.34 to 1.40), into the line above."""
    p = g.p
    t = min(max(0.7 * p.sv, p.floor), RING_STROKE * p.m)    # the stroke
    inner = max(RING * p.m, t)                              # the counter, across
    r = (inner + t) / 2                                     # centreline half-size
    yc = y + r + t / 2
    a = 2 * r / (2 + SQRT2)                                 # a regular octagon's cut
    pts = [(x - r + a, yc - r), (x + r - a, yc - r), (x + r, yc - r + a), (x + r, yc + r - a),
           (x + r - a, yc + r), (x - r + a, yc + r), (x - r, yc + r - a), (x - r, yc - r + a)]
    g.stroke(*[(px, py, t) for px, py in pts], closed=True)


def hungarumlaut(g, x, y, case):
    p = g.p
    d = 2 * p.sd / SQRT2 + max(0.6 * p.m, 0.4 * whites(g).sv)     # clear of each other at every weight (the Regular's white past it)
    acute(g, x - d / 2, y, case)
    acute(g, x + d / 2, y, case)


def commabelow(g, x, y, case):
    """The comma, hung a gap below the baseline and kept within the
    descender (a little past it, as far as a descender's chamfer): its stub
    shortens first, down to a third of its thickness, then the whole comma
    lightens, as heavy faces draw their accents."""
    from .punct import _comma
    p = g.p
    room = 1.15 * p.under - gap(p)
    s = min(p.sv, room / (1 / 3 + 0.75))
    stub = min(1.5 * s, room - 0.75 * s)
    _comma(g, None, x + 0.25 * s, -gap(p), stub=stub, s=s)


def commaabove(g, x, y, case):
    """The turned comma that stands for a cedilla over g."""
    p = g.p
    s = p.sv
    yb = y + 0.5 * gap(p)
    yt = yb + 1.5 * s
    g.stroke((x, yb), (x, yt), (x + 0.75 * s, yt + 0.75 * s), end='h')


CEDILLA_ROOM = 1.15   # descenders: how far below the baseline the cedilla's foot may hang (commabelow's room)
HOOK_ITALIC = 0.6     # stems: how thick the ogonek under an italic letter is (see hook, ogonek)


def hook(g):
    """The ogonek's measures: (its neck's thickness, its foot's, the foot's
    centreline, how far the foot runs from the neck's centre). A neck down
    from the letter and a foot turning right, with a notch between the
    letter and the foot that must outlast the corner rule, which breaks
    the notch's inside corners at the neck and the foot's end beyond it:
    so the notch is at least a mark's gap tall, and that gap and two
    corner breaks wide; as it would close, the foot hangs lower, as far as
    the comma below may (CEDILLA_ROOM descenders), and past that the hook
    lightens.

    In the italic it is HOOK_ITALIC of a stem. Thicker, it changes the
    letter it hangs from: at seven tenths the Į's stem was drawn another
    way at the Regular, at a whole stem the į's to Medium and the Į's at
    SemiBold and Bold (the ink above the baseline, against the plain
    letter's)."""
    from ..draw import _thickness
    p = g.p
    th = _thickness(p, g.sh)
    wv, wh = th((0.0, 1.0)), th((1.0, 0.0))
    if p.slant:
        wv, wh = HOOK_ITALIC * wv, HOOK_ITALIC * wh
    room = CEDILLA_ROOM * p.under
    tall = gap(p)                                            # the notch's height, at least
    k = min(1.0, (room - tall) / wh)                         # the hook's strokes, lightened only past the room
    wv, wh = k * wv, k * wh
    foot = max(min(-p.under + 0.25 * p.m, -tall - wh), -room)  # the foot's underside: as drawn, or lower
    run = wv / 2 + max(1.5 * p.m, gap(p) + 2 * p.c)          # the notch's width past the neck, both its ends broken
    if p.slant:
        from .italic_forms import run_floor
        run = max(run, run_floor(p, p.m / 2, wh))           # (the ogonek's corner into its foot curves at every weight)
    return wv, wh, foot + wh / 2, run


TAB_DEPTH = 2.0     # modules: how far under the baseline the cedilla's tab hangs


def cedilla(g, x, y, case):
    """A flat tab under the letter, after Tomorrow's (the owner,
    2026-11-12: "the cedilla under the c ... just turns into a little flat
    tab"; of the tab at a third, two thirds and the whole of the letter's
    weight, "F. Definitely": the whole). A short stroke leaning as steeply
    as the alphabet's steep diagonals (two down for one across), its top in
    the letter, cut level underneath, as wide as the letter's own stem at
    every weight, two modules deep. The middle of what shows of it stands
    under x.

    It was a hook: a neck down and a foot turning left, with a notch
    between the letter and the foot that had to outlast the corner rule.
    From Bold that took a foot hung lower and reaching further, and at
    Black the hook stood 0.92 of the stem thick and 0.62 of its letter
    wide where fifty-nine other families' heaviest weights have 0.68 and
    0.48: a second foot under the letter ("It looks wrong")."""
    p = g.p
    own = getattr(g, 'own_p', p)                            # the letter's own parameters (kept)
    depth = TAB_DEPTH * p.m
    top = g.sh / 2
    x0 = x + depth / 4                                      # its centreline on the baseline
    w = own.sv * 2 / 5 ** 0.5                               # across the stroke: its level cuts are a stem wide
    g.stroke((x0 - depth / 2, -depth, w), (x0 + top / 2, top), start='h', end='h')


def ogonek(g, x, y, case):
    """Hangs from the base's rightmost ink on the baseline (a stem's foot or
    a bar's end, whichever the letter has), turning right underneath (hook)."""
    p = g.p
    own = getattr(g, 'own_p', p)                            # the letter's own parameters (kept)
    wv, wh, yb, run = hook(g)
    from shapely.geometry import LineString
    base = getattr(g, 'base_ink', None) or g.extra[0]
    cut = base.intersection(LineString([(-1e4, 0.3 * g.sh), (1e4, 0.3 * g.sh)]))
    xs = [c[0] for gg in getattr(cut, 'geoms', [cut]) for c in getattr(gg, 'coords', [])]
    if p.slant:
        # The italic's hangs flush with the base's right edge where that edge
        # runs down to the baseline (the end of the a's, i's and u's exit
        # tails, the E's bar, an I's stem) and runs it on down; a quarter
        # stem in, the slant showed a step at the join and a nose at 680/+60.
        # It is HOOK_ITALIC of a stem thick: an exit tail is as long as its
        # own corner needs and little more, and a stem-thick ogonek at its end
        # cut into that corner's chamfer and held it straight from 400 to 850.
        # Where the edge ends on a bowl corner (the e's arm, the o's and U's
        # bowls) it hangs under the bowl, clear of the corner. Its foot is at
        # least run_floor long, so the corner into it curves at every weight
        # (shorter, it was a slab at Black); and it meets the base's
        # underside square, as the g's descender meets its foot
        # (lower.crotch_butt): with the corner rule's fill there, the fill
        # and the corner's chamfer merged at Black and the corner held.
        from shapely.geometry import box

        from ..params import outer_leg
        from .italic_forms import TAIL_FLAT
        w = wv
        top = p.cap if case == 'uc' else p.xh
        body = base.intersection(box(-1e4, 0.0, 1e4, top))
        if body.is_empty:
            body = base
        xr = body.bounds[2]
        edge = body.intersection(LineString([(xr - 1.0, -1e4), (xr - 1.0, 1e4)]))
        y_edge = 0.0 if edge.is_empty else edge.bounds[1]
        if y_edge <= g.sh / 2 + 1.0:
            x = xr - w / 2                                  # flush with a stem, a tail's end, a bar's end
        else:
            # a bowl corner at the foot of that edge (the e's arm, the o's and
            # U's bowls): under the bowl, clear of the corner's outer chamfer
            x = xr - outer_leg(own) - TAIL_FLAT * own.c - w / 2
        under = base.intersection(box(x - w / 2, -1e4, x + w / 2, top))
        g.stroke((x, g.sh / 2, w), B(x, yb, p.m / 2, wh), (x + run, yb))
        g.butt += (('y', 0.0 if under.is_empty else under.bounds[1], x - w / 2 - 1.0, x + w / 2 + 1.0),)
        return
    x = (max(xs) - 0.75 * wv) if xs else x
    g.stroke((x, g.sh / 2, wv), B(x, yb, p.m / 2, wh), (x + run, yb))


ABOVE = {'̀': grave, '́': acute, '̂': circumflex, '̃': tilde, '̄': macron,
         '̆': breve, '̇': dotaccent, '̈': dieresis, '̊': ring, '̋': hungarumlaut,
         '̌': caron}
BELOW = {'̦': commabelow, '̧': cedilla, '̨': ogonek}
# Marks joined to the base itself (the Vietnamese horn): fn(g, x, case),
# reading the base's ink (g.extra[0]). A monospaced cell narrows the base
# by as much as such a mark reaches past the cell's edge.
ATTACHED: dict = {}
# Pairs of marks above where the second stands beside the first, at its
# upper right, instead of on top of it (Vietnamese tone marks on the
# circumflex).
BESIDE: set = set()

# Letters whose cedilla is written as a comma: Latvian's, and the T and t,
# whose cedilla Romanian writes as a comma (and which, hung from the T's
# stem, would turn the letter into a J).
CEDILLA_AS_COMMA = set('KkLlNnRrGgTt')

STACK_GAP = 0.6     # white between stacked marks, of the marks' gap
TIGHTEST = 0.5      # the furthest a stack's gaps close up to stay inside the line (or the cell), before its marks shrink
LIGHTEST = 0.5      # the furthest a stack of marks lightens and shrinks to stay inside the line
CELL_LIGHTEST = 0.3     # the furthest a mark beside a letter shrinks to stay inside Mono's cell (_squeeze)
CELL_GIVE = 2.0         # _squeeze's s at CELL_LIGHTEST


def line_top(p):
    """The top of the line, above which a renderer may clip: the font's
    Windows ascent (``font.Metrics``); in Mono, its line box (the typo and
    hhea ascent), which is a terminal's cell (the owner, 2026-11-06: the
    line stays, the accents give way)."""
    from ..font import Metrics
    m = Metrics()
    return ((m.asc if p.mono else m.win_asc) - 2) * p.cap / m.cap


def _scaled(p, k):
    """p lighter and smaller by k: strokes, module and edge breaks together."""
    if k == 1.0:
        return p
    return p.with_(m=p.m * k, sv=p.sv * k, sh=p.sh * k, sd=p.sd * k, ss=p.ss * k, c=p.c * k, leg=p.leg * k)


def accent_params(p, k, gain=None):
    """A mark's parameters (mark_params), drawn lighter and smaller by k:
    strokes, module and edge breaks together, so a mark keeps its
    proportions as it shrinks."""
    return _scaled(mark_params(p, gain), k)


def mark_ink(g, n0=0):
    """The finished ink (corner rule and all) of a glyph's strokes from the n0-th on."""
    from ..draw import _thickness
    from ..geom import ink, rings_to_shapely
    return rings_to_shapely(ink(g.strokes[n0:], _thickness(g.p, g.sh), g.p.c))


def raw_ink(g, n0=0):
    """The ink of a glyph's strokes from the n0-th on before the corner rule:
    what the glyph's union sees, so parts apart here stay apart."""
    import shapely
    from ..draw import _thickness
    from ..geom import stroke_polygon
    th = _thickness(g.p, g.sh)
    return shapely.union_all([stroke_polygon(s, th, g.p.c) for s in g.strokes[n0:]])


RAW_CLEAR = 1.0     # font units: marks whose raw strokes come nearer would fuse in the union


def _nearest_clear(scratch, n0, draw_at, others, sg, reach):
    """The least t in [0, reach] for which the mark drawn by draw_at(t)
    stands ``sg`` clear of ``others`` (finished ink) and does not touch
    them before the corner rule (raw ink)."""
    fin, raw = others

    def clear(t):
        del scratch.strokes[n0:]
        draw_at(t)
        return ((not sg or mark_ink(scratch, n0).distance(fin) >= sg - 1e-6)
                and raw_ink(scratch, n0).distance(raw) >= RAW_CLEAR)
    if clear(0.0):
        del scratch.strokes[n0:]
        return 0.0
    lo, hi = 0.0, reach
    for _ in range(20):
        mid = (lo + hi) / 2
        if clear(mid):
            hi = mid
        else:
            lo = mid
    del scratch.strokes[n0:]
    return hi


def stack_above(p, marks, x, top, case, W, room=None, avoid=None, tight=1.0, reg=None):
    """Where the marks above a base go: ([(mark, x, y)], the stack's top,
    how much wider than ``room`` the stack is).

    The first stands a gap above the base's highest ink; each next one a
    stack gap above the ink of those before it (measured, so a dieresis
    carries a macron lower than an acute would). A pair in ``BESIDE`` puts
    the second mark at the first's upper right instead: drawn where the
    first is, then moved out at 45 degrees, square to the circumflex's
    right arm, until it stands a stack gap clear. Marks never come so near
    that their strokes would fuse. ``avoid`` (finished, raw ink): what the
    stack keeps a stack gap from, moving left if it must (a horn).
    ``room`` (x0, x1): the whole stack shifts sideways, if it must, to stay
    inside it (a monospaced cell). ``tight``: the gaps, the first and the
    stack's, closed up to this share of themselves (draw_above)."""
    from ..draw import Glyph
    scratch = Glyph(p, W=W)
    if reg is not None:
        scratch.reg = reg
    places = []
    y = top + tight * gap(p)
    sg = tight * STACK_GAP * gap(p)
    reach = 4 * size(p, case) + 2 * p.sv
    prev = None
    for m in marks:
        n0 = len(scratch.strokes)
        before = (mark_ink(scratch), raw_ink(scratch)) if n0 else None
        if (prev, m) in BESIDE and places:
            x0, y0 = places[-1][1:]
            t = _nearest_clear(scratch, n0, lambda t: ABOVE[m](scratch, x0 + t, y0 + t, case), before, sg, reach)
            xm, ym = x0 + t, y0 + t
        else:
            xm, ym = x, y
            if before is not None:                          # stacked: never fused to what is below
                t = _nearest_clear(scratch, n0, lambda t: ABOVE[m](scratch, x, y + t, case), before, 0.0, reach)
                ym = y + t
        ABOVE[m](scratch, xm, ym, case)
        places.append((m, xm, ym))
        y = mark_ink(scratch).bounds[3] + sg
        prev = m
    if not places:
        return places, top, 0.0
    if avoid is not None:
        t = _nearest_clear(scratch, 0, lambda t: [ABOVE[m](scratch, xm - t, ym, case) for m, xm, ym in places],
                           avoid, sg, reach)
        places = [(m, xm - t, ym) for m, xm, ym in places]
        del scratch.strokes[:]
        for m, xm, ym in places:
            ABOVE[m](scratch, xm, ym, case)
    over = 0.0
    if room is not None:
        # as the font carries the marks (draw._ink_x): in the italic
        # slanted, where they stand highest and lean furthest, ~110 units at
        # an accent's height, past a cell an upright measure fitted, and
        # curved, as the letter under them is measured
        from ..draw import _ink_x
        x0, x1 = _ink_x(scratch)
        shift = min(0.0, room[1] - x1) or max(0.0, room[0] - x0)
        places = [(m, xm + shift, ym) for m, xm, ym in places]
        over = max(0.0, (x1 - x0) - (room[1] - room[0]))
    return places, mark_ink(scratch).bounds[3], over


def clear_below(base_ink, p, fn, x, case, W):
    """Where a mark below goes: under the body's centre, or, where the
    base's ink below the baseline (a descender's hook) would crowd it, to
    the right, as far as it must go to keep a gap clear."""
    from shapely.geometry import box

    from ..draw import Glyph
    scratch = Glyph(p, W=W)
    hook = base_ink.intersection(box(-1e4, -1e4, 1e4, -1e-3))  # (a cedilla is meant to touch the base)
    if hook.is_empty:
        return x

    def clearance(xm):
        del scratch.strokes[:]
        fn(scratch, xm, 0, case)
        return mark_ink(scratch).distance(hook)
    want = gap(p)
    if clearance(x) >= 0.9 * want:
        return x
    step = 0.1 * p.m
    xm = x
    while clearance(xm) < want and xm < x + 2 * W:
        xm += step
    return xm


def _name(ch):
    return agl.UV2AGL.get(ord(ch), f'uni{ord(ch):04X}')


def compose(chars, base_names):
    """Register a glyph for every char in ``chars`` that decomposes into a
    known base and known marks. ``base_names`` maps base chars to glyph names."""
    made = []
    for ch in chars:
        d = unicodedata.normalize('NFD', ch)
        if len(d) < 2:
            continue
        base, marks = d[0], d[1:]
        if not all(m in ABOVE or m in BELOW or m in ATTACHED for m in marks):
            continue
        bname = base_names.get(base)
        if any(m in ABOVE for m in marks) and bname in ('i', 'j'):
            bname = {'i': 'dotlessi', 'j': 'uni0237'}[bname]
        if bname is None or bname not in REGISTRY:
            continue
        name = _name(ch)
        if name in REGISTRY or any(sp.unicode == ord(ch) for sp in REGISTRY.values()):
            continue
        _register(name, ch, bname, base, marks)
        made.append(name)
    return made


def _register(name, ch, bname, base, marks):
    spec = REGISTRY[bname]
    case = 'uc' if base.isupper() else 'lc'

    def fn(g, bname=bname, marks=marks, base=base, case=case):
        # The base, finished (openings solved, clipped and cut), then the marks.
        # (in the monospaced cell a mark that would run out of it, a horn,
        # d's and l's apostrophe, an ogonek, a tone mark beside the
        # circumflex, is given room by the cell's own fit: draw._cell_fit)
        g.extra, g.clip = [], None
        compose(g, 0.0)

    def compose(g, room, bname=bname, marks=marks, base=base, case=case):
        from ..draw import draw
        p = g.p
        # in the body the composite was given, if any: the base's as the font
        # places it (at a grade, the ungraded body: font._place_drawn; the
        # composite's width is its base's in every cut). Drawn at its own
        # graded width, the base in Á was not the font's A.
        body = getattr(g, 'width_arg', None)
        base_glyph = draw(bname, p, g.ot, g.ob, width=(body - room) if body is not None else ((g.W - room) if room else None))
        # the marks are placed on the exact base; its optical correction
        # (draw._optical) then moves the whole composite, so a cedilla or an
        # ogonek stays joined to the foot it hangs from and an accent keeps
        # its distance from the top
        warp = getattr(base_glyph, 'warp', None)
        base_glyph.warp = None
        rings = base_glyph.rings()
        top = max(y for r in rings for _, y in r)
        g.add_glyph(base_glyph)
        g.warp = warp
        x = (g.W - room) / 2
        above = []
        for m in marks:
            if m in ABOVE:
                if m == '\u030c' and base in 'dlLt':
                    _caron_apostrophe(g, base)
                    continue
                above.append(m)
            elif m in ATTACHED:
                ATTACHED[m](g, x, case)
            elif m == '\u0327' and base in CEDILLA_AS_COMMA:
                if base == 'g':
                    kept(g, commaabove, x, top + gap(mark_params(p)), case)
                else:
                    kept(g, commabelow, x, 0, case)
            elif m == '\u0328':
                kept(g, ogonek, _ogonek_x(g, base), 0, case, joined=True, gain=HANG_GAIN)
            else:
                # (the cedilla hangs off its letter: its breaks a hanging mark's, its join finished with the letter)
                hangs = m == '\u0327'
                q = p if hangs else mark_params(p)
                kept(g, BELOW[m], clear_below(g.extra[0], q, BELOW[m], x, case, g.W), 0, case,
                     joined=hangs, gain=HANG_GAIN if hangs else None, apart=hangs)
        if not above:
            return
        # (in the monospaced cell, the stack keeps the cell's margin: draw.CELL_GAP)
        from ..draw import CELL_GAP
        cell = (-(p.fig_adv - g.W) / 2 + CELL_GAP * p.m, g.W + (p.fig_adv - g.W) / 2 - CELL_GAP * p.m) if p.mono else None
        # marks joined to the base (a horn) are kept clear of; a horn that
        # gave way in Mono's cell is stamped in, drawn lighter (latin_plus.horn_give)
        avoid = None
        if any(m in ATTACHED for m in marks) and (g.strokes or len(g.extra) > 1):
            import shapely
            held = g.extra[1:]
            avoid = (shapely.union_all([mark_ink(g), *held]), shapely.union_all([raw_ink(g), *held]))
        # the base's optical correction lifts what stands above its top (its
        # overshoot: more in Mono Narrow's narrower bowls) after the marks are
        # placed; the stack keeps under the line where it will stand
        lift = (warp(top + 1.0) - (top + 1.0)) if warp is not None else 0.0
        draw_above(g, above, x, top, case, cell, avoid, lift)

    def width(p, bname=bname):
        """The base's body in every cut (its italic drawing's in the italic):
        the composite is its base and marks, stamped in the base's body."""
        sp = REGISTRY.get(f'{bname}.ital') if p.slant else None
        return (sp or REGISTRY[bname]).width(p)
    glyph(name, ch, width, kind=spec.kind, base=bname)(fn)


def _into_cell(g):
    """In the monospaced cell, a glyph whose ink still runs out of the cell
    on one side moves into the room the other side has (the body is centred
    in the cell, not the ink)."""
    import shapely
    from .symkit import shift
    p = g.p
    parts = list(g.extra) + ([mark_ink(g)] if g.strokes else [])
    a, _, b, _ = shapely.union_all(parts).bounds
    lo, hi = -(p.fig_adv - g.W) / 2, g.W + (p.fig_adv - g.W) / 2
    dx = 0.0
    if b > hi:
        dx = -min(b - hi, max(0.0, a - lo))
    elif a < lo:
        dx = min(lo - a, max(0.0, hi - b))
    if dx:
        shift(g, dx, 0.0)


def _squeeze(s):
    """(the gaps' share, the marks' scale) at s in [0, 1]: the gaps close up
    first (to TIGHTEST), then the marks lighten and shrink (to LIGHTEST),
    so the stack changes continuously as s grows. On to s = CELL_GIVE, for
    a mark beside a letter in Mono's cell only (the caron's apostrophe, the
    horn): past LIGHTEST it goes on shrinking, to CELL_LIGHTEST, where the
    letter at its narrowest and the mark at LIGHTEST still run out of the
    cell, which a terminal cuts at (ď at Mono Bold Italic, where the slant
    takes 134 of the cell's 570 units)."""
    if s <= 0.5:
        return 1.0 - (1.0 - TIGHTEST) * 2 * s, 1.0
    if s <= 1.0:
        return TIGHTEST, 1.0 - (1.0 - LIGHTEST) * (2 * s - 1)
    return TIGHTEST, LIGHTEST - (LIGHTEST - CELL_LIGHTEST) * min(s - 1.0, CELL_GIVE - 1.0) / (CELL_GIVE - 1.0)


def draw_above(g, above, x, top, case, cell=None, avoid=None, lift=0.0):
    """Draw marks above into g, stacked (``stack_above``) over ink reaching
    ``top``. A stack that would rise past the line's top (line_top), or be
    wider than its cell, closes up its gaps and then lightens and shrinks,
    as heavy faces draw their accents, as far as it must (never past
    TIGHTEST and LIGHTEST)."""
    from ..draw import Glyph
    p = g.p

    def fits(st):
        return st[1] + lift <= line_top(p) and st[2] <= 0.5

    def at(s):
        t, k = _squeeze(s)
        return stack_above(accent_params(p, k), above, x, top, case, g.W, cell, avoid, tight=t, reg=accent_params(p, k, 0.0))
    s = 0.0
    st = at(0.0)
    if not fits(st):
        lo, hi = 0.0, 1.0
        for _ in range(18):
            mid = (lo + hi) / 2
            if fits(at(mid)):
                hi = mid
            else:
                lo = mid
        s = hi
        st = at(s)
    places = st[0]
    k = _squeeze(s)[1]
    q = accent_params(p, k)
    target = g if q is p else Glyph(q, W=g.W)             # (its own strokes past the Regular: drawn apart, stamped in)
    if target is not g:
        target.finished = True
        target.reg = accent_params(p, k, 0.0)
    for m, xm, ym in places:
        ABOVE[m](target, xm, ym, case)
    if target is not g:
        g.add_glyph(target)


def _ogonek_x(g, base):
    p = g.p
    return g.W - p.sv / 2 if base in 'aeiouAEIOUy' else g.W / 2


def at_floor(g):
    """A composite's base as the cell's fit draws it at its narrowest
    (draw.cell_floor), where the marks beside it must still find room: the
    base as drawn if it is there already, or g is no letter's composite."""
    from ..draw import REGISTRY, body_width, cell_floor, draw
    _, base, _, _ = g.extra_src[0]
    spec = REGISTRY.get(g.name)
    if spec is None or spec.base is None:
        return base
    floor = cell_floor(body_width(spec, g.p), g.p)
    return base if g.W <= floor + 0.5 else draw(spec.base, g.p, g.ot, g.ob, width=floor)


def _caron_apostrophe(g, base):
    """The caron on d, l, L and t is written as an apostrophe beside the stem.

    It stands right of the stem, its top on the ascender (cap height on a
    capital), its tail clear of the stem by a gap. Where ink lies under it
    (the t's crossbar) its stub shortens so the tail stays clear above that
    ink, down to a third of a stem, as heavy faces draw it."""
    from shapely.geometry import box

    from .punct import _comma
    from ..draw import Glyph
    from ..geom import rings_to_shapely
    from .figures import heaviness
    p0 = g.p
    ink = g.extra[0]
    # the Regular's apostrophe from there to Black (mark_params). Not in the
    # monospaced cell: there is no room for white between the two there, the
    # apostrophe is drawn into its letter and the letter's finish joins them
    # (4 to 20 units between them before it, at Regular as at Bold). Stamped
    # in at the Regular's weight it kept that hairline. It stays the
    # letter's own, drawn lighter toward Black (as a stack of marks
    # lightens), so a d keeps its counter beside it
    p = _scaled(p0, 1 - 0.5 * heaviness(p0)) if p0.mono else mark_params(p0)
    tight = 1.0
    if p0.mono:
        # the letter narrows to make room in the cell (draw._cell_fit) down to
        # its floor (draw.cell_floor); where even that leaves too little, the
        # apostrophe gives way as a stack of marks does (_squeeze): its gap
        # closes up, then it lightens and shrinks (ď at Bold). Measured as
        # drawn, against the letter as it stands at its floor (at_floor),
        # as the font carries them (in the italic, slanted)
        from ..draw import CELL_GAP, _ink_x
        bf = at_floor(g)
        x0f, x1f = _ink_x(bf, p0)
        room = x0f + p0.fig_adv - 2 * CELL_GAP * p0.m
        inkf = rings_to_shapely(bf.rings())
        stem0 = inkf.intersection(box(-1e4, p.xh + g.sh, 1e4, (p.cap if base.isupper() else p.asc) + 1))
        right0 = stem0.bounds[2] if not stem0.is_empty else p.sv

        def reach_right(s_):
            t, k = _squeeze(s_)
            q = _scaled(p, k)
            top_ = q.cap if base.isupper() else q.asc
            scratch = Glyph(q, W=g.W)
            scratch.warp = getattr(bf, 'warp', None)        # (the letter's overshoot moves its marks: in the italic, leaned)
            _comma(scratch, None, right0 + t * max(q.m, 0.6 * q.sv) + 0.75 * q.sv + q.sd / SQRT2, top_, stub=1.5 * q.sv)
            return max(_ink_x(scratch, p0)[1], x1f)
        if reach_right(0.0) > room:
            # (past LIGHTEST only if LIGHTEST is not enough: _squeeze)
            lo_, hi_ = (0.0, 1.0) if reach_right(1.0) <= room else (1.0, CELL_GIVE)
            for _ in range(18):
                mid = (lo_ + hi_) / 2
                if reach_right(mid) <= room:
                    hi_ = mid
                else:
                    lo_ = mid
            tight, k = _squeeze(hi_)
            p = _scaled(p, k)
    top = p.cap if base.isupper() else p.asc
    gap = tight * max(p.m, 0.6 * p.sv)
    # the stem: the base's ink above the x-height and its bars (from the bar's top: from a bar's thickness
    # over it, the t's stem stood under the line from 850 and was read as none, then at 890 as a sliver of
    # its top, and the apostrophe jumped 49 units right)
    stem = ink.intersection(box(-1e4, p.xh + g.sh / 2 + 1.0, 1e4, top + 1))
    right = stem.bounds[2] if not stem.is_empty else p.sv
    reach = 0.75 * p.sv + p.sd / SQRT2                      # the tail's far edge, left of the stub's centre
    x = right + gap + reach
    below = ink.intersection(box(x - reach, -1e4, x + p.sv / 2, top - 1e-3))
    floor = below.bounds[3] if not below.is_empty else -1e4
    clear = max(p.c, 0.5 * p.m)
    stub = min(1.5 * p.sv, max(top - floor - clear - 0.75 * p.sv, p.sv / 3))
    if p is p0:
        _comma(g, None, x, top, stub=stub)
    else:
        target = Glyph(p, W=g.W)
        _comma(target, None, x, top, stub=stub)
        g.add_glyph(target)
