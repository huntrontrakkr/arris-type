"""Arris Mono's programming ligatures.

Code is set in a fixed grid, so a ligature here never changes the grid: a
sequence of N characters becomes N - 1 empty spacers (LIG) and one glyph
one cell wide that draws back across the N cells (the scheme Fira Code
made standard). The substitution is contextual (`calt`, on by default and
easy to turn off in editors), longest sequences first, with guards so a
ligature never forms inside a longer run of operators (`<=<`, `>>=`).

A ligature keeps every character where it stands and as it is drawn
alone: the < of `</span>` is the < of `<span>`, the bars of `==` are the
bars of =. A join only runs a character's own strokes on, in their own
direction, until they meet the next one (the chevron's arm to the slash in
`</`, to the pipe in `|>`, to the S's bars in `<$>`; the bars of # to the
bracket's spine), so an N-character ligature is N cells wide and set as
the characters would be. Where a sequence becomes a new sign, it is drawn
across its cells: the arrows (one 45-degree head, 0.88 of the cap height,
its point kept sharp, the shaft ending inside it), the struck bars of !=,
the larger <= and >=, the raised colon of :=. What Fira Code only draws
closer (`||` `::` `//` `>>` `/*` `<*>`) is set as its characters brought
together, each as itself (``_run``); what it joins into one shape (`www`
`&&` `??` `#?`) is joined. Runs of any length (`---->`)
are ``sequences``; Fira Code's optional sets are here too, under its tags
(OPTIONAL). ``docs/DESIGN.md``, section 8.
"""
from __future__ import annotations

from ..draw import REGISTRY, B, glyph
from ..params import SQRT2
from .punct import axis, dot

LIGATURES: list[tuple[str, tuple[str, ...]]] = []   # (glyph name, component glyph names), longest first at build
COMPONENTS: dict[str, tuple[str, ...]] = {}         # glyph name -> component glyph names
GUARDS: dict[str, tuple[str, str]] = {}             # glyph name -> (characters before, after) that keep it from forming

HEAD = 0.44          # an arrowhead's half-height, of the cap height (Fira Code's: 0.88 of it in all)
DOUBLE = 0.6         # a double head's second chevron: this share of the head behind the first, plus its stroke
OPERATORS = '-<>=!|:.+*/~&?^%#$\\'
LE_HALF = 0.42       # the chevron of <= and >=: half its height, of the cap height


def _names(seq: str) -> tuple[str, ...]:
    cmap = {chr(s.unicode): n for n, s in REGISTRY.items() if s.unicode}
    return tuple(cmap[ch] for ch in seq)


def _body(n):
    """A ligature's body: the n cells' bodies and the gaps between them."""
    return lambda p: n * p.fig_adv - (p.fig_adv - p.fig_w)


def liga(*seqs, before=None, after=None):
    """Register a drawing for one or more character sequences of the same
    length (`!=` and `/=` share the struck double bar). ``before`` and
    ``after``: the characters that keep it from forming when they touch it
    (the operators, OPERATORS, unless given)."""
    def deco(fn):
        for seq in seqs:
            names = _names(seq)
            name = '_'.join(names) + '.liga'
            if len(name) > 31:                  # legacy limit: the AGL's code-point form
                name = 'uni' + ''.join(f'{ord(ch):04X}' for ch in seq) + '.liga'
            COMPONENTS[name] = names
            if before is not None or after is not None:
                GUARDS[name] = (OPERATORS if before is None else before, OPERATORS if after is None else after)
            glyph(name, None, _body(len(seq)), kind=('liga', len(seq)))(fn)
            LIGATURES.append((name, names))
        return fn
    return deco


@glyph('LIG', None, 'fig_w', kind=('liga', 1))
def lig_spacer(g):
    """The empty cell a ligature draws over."""


# --- Shared geometry ----------------------------------------------------------
# A ligature's frame runs from its first cell's body (x = 0) to its last
# cell's (x = W); cell i's body is [i * fig_adv, i * fig_adv + fig_w].

def cell(g, i):
    """(left, centre, right) of the i-th cell's body, in the ligature's frame."""
    p = g.p
    left = i * p.fig_adv
    return left, left + p.fig_w / 2, left + p.fig_w


def _sub(name, p):
    from ..draw import draw
    return draw(name, p)


def _at(g, sub, i):
    """x where ``sub`` sits when set in cell i as itself."""
    return i * g.p.fig_adv + (g.p.fig_w - sub.W) / 2


def edge(p):
    """The margin an arrow or a run of bars keeps at the ligature's ends:
    the hyphen's own, so `->` starts where `-` starts."""
    return (p.fig_w - _sub('hyphen', p).W) / 2


def bars_offset(g):
    """Half the distance between the bars of `=` (punct.eq_offset)."""
    from .punct import eq_offset
    return eq_offset(g)


def _ink_of(sub, dx=0.0, dy=0.0):
    from shapely import affinity
    from ..geom import rings_to_shapely
    return affinity.translate(rings_to_shapely(sub.rings()), dx, dy)


def _runs(ink, x=None, y=None):
    """The ink's runs across the vertical line at x, as (low, high) in y;
    or across the horizontal line at y, as (left, right) in x."""
    from shapely.geometry import LineString
    x0, y0, x1, y1 = ink.bounds
    line = LineString([(x, y0 - 1), (x, y1 + 1)]) if x is not None else LineString([(x0 - 1, y), (x1 + 1, y)])
    k = 1 if x is not None else 0
    out = []
    cut = ink.intersection(line)
    for seg in getattr(cut, 'geoms', [cut]):
        cs = list(getattr(seg, 'coords', []))
        if len(cs) >= 2:
            out.append((min(c[k] for c in cs), max(c[k] for c in cs)))
    return sorted(out)


# --- Arrows -----------------------------------------------------------------

def head_h(p):
    return HEAD * p.cap


def head(g, tip, sign):
    """An arrowhead: one 45-degree chevron with its point at ``tip``,
    pointing right (sign 1) or left (-1). Drawn as a single stroke, its
    point is a right angle between two diagonals, which the corner rule
    keeps sharp; the barbs end square to themselves."""
    x, y = tip
    h = head_h(g.p)
    g.stroke((x - sign * h, y + h), (x, y), (x - sign * h, y - h))


def _tip(g, sign):
    """The centreline point of a head at the ligature's right (sign 1) or
    left (-1) end, so the head's ink ends at the hyphen's margin."""
    p = g.p
    inset = edge(p) + p.sd / SQRT2                              # the point's ink lies sd/sqrt2 past its centreline
    return g.W - inset if sign > 0 else inset


def _bar_at(g, i):
    """The font's `|`, as itself in cell i; returns its centre x."""
    bar = _sub('bar', g.p)
    x = _at(g, bar, i)
    g.add_glyph(bar, x, 0.0)
    return x + bar.W / 2


def _arrow(g, bars=1, right=True, left=False, double=False, start_bar=False, end_bar=False):
    """Every straight arrow: a shaft of one or two bars on the axis, a head
    at either end or both, a second chevron behind a head (`->>`), a bar at
    the start or the end (`|->`, `<-|`). A single shaft runs to the point,
    inside the head; a double shaft's bars end on the head's arms, as `=`
    meets `>` in `=>`."""
    p, W = g.p, g.W
    a = axis(p)
    h = head_h(p)
    x0, x1 = edge(p), W - edge(p)
    if start_bar:
        x0 = _bar_at(g, 0)
    if end_bar:
        x1 = _bar_at(g, len(COMPONENTS[g.name]) - 1)
    back = DOUBLE * h + 2 * SQRT2 * p.sd                       # the second chevron: the white between grows with the stroke
    tips = []
    if right:
        tips.append((_tip(g, 1), 1))
    if left:
        tips.append((_tip(g, -1), -1))
    for t, s in tips:
        head(g, (t, a), s)
        if double:
            head(g, (t - s * back, a), s)
        if s > 0:
            x1 = t
        else:
            x0 = t
    if bars == 1:
        g.stroke((x0, a), (x1, a))
    else:
        off = bars_offset(g)
        for y in (a - off, a + off):
            g.stroke((x0 + (off if left else 0.0), y), (x1 - (off if right else 0.0), y))


liga('->', '-->')(lambda g: _arrow(g))
liga('<-', '<--')(lambda g: _arrow(g, right=False, left=True))
liga('<->', '<-->')(lambda g: _arrow(g, left=True))
liga('=>', '==>')(lambda g: _arrow(g, bars=2))
liga('<==')(lambda g: _arrow(g, bars=2, right=False, left=True))
liga('<=>', '<==>')(lambda g: _arrow(g, bars=2, left=True))
liga('|->')(lambda g: _arrow(g, start_bar=True))
liga('<-|')(lambda g: _arrow(g, right=False, left=True, end_bar=True))
liga('|=>')(lambda g: _arrow(g, bars=2, start_bar=True))
liga('->>')(lambda g: _arrow(g, double=True))
liga('<<-')(lambda g: _arrow(g, right=False, left=True, double=True))


def _wave_pts(p, x_from, x_to, end=None):
    """The tilde's step (up at 45 degrees, along, down, along) at the
    tilde's own period, as many whole periods as fit between x_from and
    x_to, centred there, leaving and rejoining the axis; on along the axis
    to x_from and to ``end`` (x_to if not given)."""
    a = axis(p)
    d = REGISTRY['asciitilde'].width(p) / 4                  # the tilde's step (punct.asciitilde)
    run = x_to - x_from
    n = max(1, int(run // (4 * d)))
    x0 = x_from + (run - 4 * d * n) / 2
    pts = [(x_from, a)] if x0 > x_from + 1 else []
    for i in range(n):
        x = x0 + 4 * d * i
        pts += [(x, a), (x + d / 2, a + d / 2), (x + 3 * d / 2, a + d / 2),
                (x + 5 * d / 2, a - d / 2), (x + 7 * d / 2, a - d / 2)]
    return pts + [(x0 + 4 * d * n, a), (x_to if end is None else end, a)]


def _wave(g, sign, both=False):
    """`~>`, `~~>`, `<~`, `<~~`, `<~>`: the tilde's wave into the arrows'
    head (or heads)."""
    p, W = g.p, g.W
    a = axis(p)
    tip, start = _tip(g, 1), edge(p)
    if both:
        lt = W - tip
        pts = _wave_pts(p, lt + head_h(p), tip - head_h(p), end=tip)
        g.stroke((lt, a), *pts)
        head(g, (tip, a), 1)
        head(g, (lt, a), -1)
        return
    pts = _wave_pts(p, start, tip - head_h(p), end=tip)      # the shaft's room behind the barbs
    if sign < 0:
        pts = [(W - x, y) for x, y in pts]
    g.stroke(*pts)
    head(g, ((W - tip) if sign < 0 else tip, a), sign)


liga('~>', '~~>')(lambda g: _wave(g, 1))
liga('<~', '<~~')(lambda g: _wave(g, -1))
# `<~>`: both heads on the wave, as `<->` has both on its shaft (`<~` and `~>`
# take the arrows' head; the < and > themselves, as Fira draws it, open at 2:1
# too slowly for the wave: it could begin only far from their points)
liga('<~>')(lambda g: _wave(g, 1, both=True))


def _tilde_d(p):
    return REGISTRY['asciitilde'].width(p) / 4               # the tilde's step (punct.asciitilde)


@liga('~~')
def double_tilde(g):
    """`~~`: the two tildes as one stroke, the second's step begun where
    the first's ends (at the foot of its step), one even wave of two steps
    centred on the cells, its ends the tilde's own."""
    p = g.p
    a, d = axis(p), _tilde_d(p)
    lo, hi = a - d / 2, a + d / 2
    x = g.W / 2 - 4 * d
    pts = []
    for k in (0, 4):
        pts += [(x + k * d, lo), (x + (k + 1) * d, hi), (x + (k + 2) * d, hi), (x + (k + 3) * d, lo)]
    g.stroke(*pts, (x + 8 * d, lo), start='v', end='v')


@liga('-~')
def hyphen_tilde(g):
    """`-~`: the hyphen along the axis, turning up into the tilde's first
    stroke where that crosses the axis: one stroke into the wave."""
    p = g.p
    a, d = axis(p), _tilde_d(p)
    lo, hi = a - d / 2, a + d / 2
    x = _at(g, _sub('asciitilde', p), 1)
    g.stroke((edge(p), a), (x + d / 2, a), (x + d, hi), (x + 2 * d, hi), (x + 3 * d, lo), (x + 4 * d, lo),
             end='v')


@liga('~-')
def tilde_hyphen(g):
    """`~-`: the tilde, its downstroke turning along the axis where it
    crosses it and running on as the hyphen (`-~` turned about)."""
    p, W = g.p, g.W
    a, d = axis(p), _tilde_d(p)
    lo, hi = a - d / 2, a + d / 2
    x = _at(g, _sub('asciitilde', p), 0)
    g.stroke((x, lo), (x + d, hi), (x + 2 * d, hi), (x + 5 * d / 2, a), (W - edge(p), a), start='v')


@liga('~@')
def tilde_at(g):
    """`~@`: the tilde as itself, and from the foot of its step its wave's
    next step, rising at the steep 2:1 into the @: it becomes the ring, one
    line from the wave over the top of the @ and down into its a, with
    nothing hanging below where it comes in (punct.at's lead-in; as Fira
    Code's tilde becomes its @'s outer stroke)."""
    from ..draw import Glyph
    p = g.p
    a = axis(p)
    t, at = _sub('asciitilde', p), _sub('at', p)
    d = t.W / 4
    x0, xa = _at(g, t, 0), _at(g, at, 1)
    lo, hi = a - d / 2, a + d / 2
    h = Glyph(p, 'at', W=at.W)
    h.sh_auto = getattr(at, 'sh_auto', h.sh_auto)
    h.lead = [(x0 + k * d - xa, y) for k, y in ((0, lo), (1, hi), (2, hi), (3, lo), (4, lo))]
    REGISTRY['at'].fn(h)
    if h.clip is not None:                                  # the @ keeps to its box: the box opened to the left
        cx0, cy0, cx1, cy1 = h.clip                         # for the wave
        h.clip = (min(cx0, x0 - xa - p.sv), min(cy0, lo - p.sv), cx1, cy1)
    g.add_glyph(h, xa, 0.0)


@liga('^=')
def caret_equal(g):
    """`^=`: the caret and the = as themselves, the caret's right arm run
    on down at 45 degrees and the ='s top bar on to the left until they
    meet."""
    p = g.p
    c, xc = _stamp(g, 'asciicircum', 0)
    e, xe = _stamp(g, 'equal', 1)
    k = p.sd / SQRT2
    ya = p.cap + p.c - k                                     # the caret's point (punct.asciicircum)
    xp = xc + c.W / 2
    yb = axis(p) + bars_offset(g)                           # the top bar's centreline
    xm = xp + (ya - yb)                                     # where the arm, run on, crosses it
    y_in = p.cap - 2 * p.c                                  # from inside the arm (the caret is cut at the cap)
    g.stroke((xp + (ya - y_in), y_in), (xm, yb), (xe + p.c, yb), start='flat', end='flat')


def _slashes_meet(g, down):
    """`/\\` (∧) and `\\/` (∨): one sign, as Arris's ∧ ∨ are drawn
    (operators.gable: two 2:1 strokes meeting in a point), from the
    baseline to the cap height across the two cells."""
    from .letterframe import STEEP
    from .operators import gable
    p = g.p
    w = p.ss / STEEP[1]                                     # a 2:1 stroke's width across (gable)
    H = p.cap
    xc = g.W / 2
    gable(g, H / 2, 0, down=down, x0=xc - H / 2 - w / 2, x1=xc + H / 2 + w / 2)


liga('/\\')(lambda g: _slashes_meet(g, False))
liga('\\/')(lambda g: _slashes_meet(g, True))


# --- Characters as themselves ------------------------------------------------------

def _stamp(g, name, i, dy=0.0):
    """The character as itself in cell i; returns (glyph, x)."""
    sub = _sub(name, g.p)
    x = _at(g, sub, i)
    g.add_glyph(sub, x, dy)
    return sub, x


def _chev(g, i, sign):
    """The < (sign -1) or > (sign 1) of cell i, as punct._chevron draws it:
    (point x, arm-end x, half height)."""
    from .punct import chevron_geometry
    p = g.p
    sub = _sub('less', p)
    x0 = _at(g, sub, i)
    x_tip, reach = chevron_geometry(g, sub.W)
    if sign < 0:
        return x0 + x_tip, x0 + sub.W, reach / 2
    return x0 + sub.W - x_tip, x0, reach / 2


def _chevron_to(g, i, sign, upper=None, lower=None):
    """The chevron of cell i, its upper and/or lower arm run on along its
    own 2:1 to the given run (half-height) where it meets its neighbour;
    an arm not given ends as the chevron's own, cut upright."""
    tip, end, v = _chev(g, i, sign)
    a = axis(g.p)
    dx = 1 if sign < 0 else -1                                 # arms run away from the point
    tu = v if upper is None else upper
    tl = v if lower is None else lower
    g.stroke((tip + dx * 2 * tu, a + tu), (tip, a), (tip + dx * 2 * tl, a - tl),
             start='v' if upper is None else 'flat', end='v' if lower is None else 'flat')
    return tip


def _slash_line(g, i):
    """The slash of cell i as itself; returns x(y) along its centreline."""
    from .letterframe import STEEP
    p = g.p
    sub, x0 = _stamp(g, 'slash', i)
    bot = -p.desc + 0.5 * p.m
    w = p.ss / STEEP[1]
    return lambda y: x0 + w / 2 + (y - bot) / 2


def _meet_slash(tip, a, line, sign, up):
    """The run t at which a chevron arm from ``tip`` (pointing ``sign``)
    going up (``up``) or down meets the slash centreline x(y)."""
    dx = 1 if sign < 0 else -1
    dy = 1 if up else -1
    # tip + dx 2t = line(a + dy t), line(y) = c + y / 2
    c = line(0.0)
    return (c + a / 2 - tip) / (2 * dx - dy / 2)


# --- Equality and comparison ---------------------------------------------

def _bars(g, n, x0=None, x1=None, struck=False):
    """The bars of = run through the cells, from ='s own margin to its
    own margin; three for ===, the same white between each. A stack taller
    than ≡ may grow (operators.TALL; STRUCK if a slash will cross it, as ≢)
    thins its bars as ≡ does (the tight-stack rule, never below 0.7)."""
    from .operators import STRUCK
    from .operators import TALL as TALL_
    from .punct import eq_white
    TALL = STRUCK if struck else TALL_
    p, W = g.p, g.W
    a = axis(p)
    m = (p.fig_w - _sub('equal', p).W) / 2
    x0 = m if x0 is None else x0
    x1 = W - m if x1 is None else x1
    tall = lambda: n * g.sh + (n - 1) * eq_white(g)
    if tall() > TALL(p):
        lo, hi = 0.7, 1.0
        for _ in range(14):
            g.sh_k = (lo + hi) / 2
            lo, hi = (g.sh_k, hi) if tall() <= TALL(p) else (lo, g.sh_k)
        g.sh_k = lo
    step = g.sh + eq_white(g)
    ys = [a + (i - (n - 1) / 2) * step for i in range(n)]
    for y in ys:
        g.stroke((x0, y), (x1, y))
    return ys


def _strike(g, ys):
    """The 2:1 slash of != across bars at heights ys, as ≠ draws it; never
    past where ≢'s negation reaches (three quarters of a module beyond the
    tallest stack, operators.TALL)."""
    from .operators import TALL
    p = g.p
    reach = TALL(p) / 2 + 0.75 * p.m
    lo = max(min(ys) - 2.2 * g.sh, axis(p) - reach)
    hi = min(max(ys) + 2.2 * g.sh, axis(p) + reach)
    cx = g.W / 2
    run = (hi - lo) / 2
    g.stroke((cx - run / 2, lo), (cx + run / 2, hi), start='h', end='h')


liga('==')(lambda g: _bars(g, 2))
liga('===')(lambda g: _bars(g, 3))
liga('!=', '/=', '=/=')(lambda g: _strike(g, _bars(g, 2, struck=True)))
liga('!==')(lambda g: _strike(g, _bars(g, 3, struck=True)))


def _compare(g, mirror, slant=False):
    """`<=` and `>=`: ≤ and ≥ at full size across the two cells: the <
    chevron's 2:1 at LE_HALF of the cap height, the equal sign's white, and
    a bar as long as the chevron is wide; the pair centred on the axis.
    ``slant``: the bar instead parallel to the chevron's lower arm, the
    equal sign's white square to it, cut upright as the arm is (⩽, Fira
    Code's cv21)."""
    import math

    from ..draw import _thickness
    from .punct import SLOPE, eq_white
    p, W = g.p, g.W
    t = _thickness(p, g.sh)((2, 1))
    kv = t / (2 * math.cos(SLOPE))
    x_tip = t / (2 * math.sin(SLOPE))
    h = LE_HALF * p.cap
    white = eq_white(g)
    d = (t + white) / math.cos(SLOPE)                          # the slanted bar below the arm, in y
    a = axis(p) + (d / 2 if slant else (white + g.sh) / 2)
    x0 = (W - 2 * h - x_tip) / 2 + x_tip                       # the point, the whole sign centred
    x1 = x0 + 2 * h
    T = (lambda x: W - x) if mirror else (lambda x: x)
    g.stroke((T(x1), a + h), (T(x0), a), (T(x1), a - h), start='v', end='v')
    if slant:
        xs = x0 - x_tip
        g.stroke((T(xs), a - d - (xs - x0) / 2), (T(x1), a - d - h), start='v', end='v')
        return
    yb = a - h - kv - white - g.sh / 2
    g.stroke((T(x0 - x_tip), yb), (T(x1), yb)) if not mirror else g.stroke((T(x1), yb), (T(x0 - x_tip), yb))


liga('<=')(lambda g: _compare(g, False))
liga('>=')(lambda g: _compare(g, True))


def _raised(g, i, x1=None):
    """The colon of cell i, its dots raised to the bars of =; returns its
    dots' (left, right) edges."""
    p = g.p
    s = p.dot()
    a = axis(p)
    off = bars_offset(g)
    x = cell(g, i)[1]
    for y in (a - off, a + off):
        dot(g, x, y - s / 2)
    return x - s / 2, x + s / 2


def _gap(p):
    return max(p.m, 0.6 * p.dot())


@liga(':=')
def colon_equal(g):
    """The colon raised so its dots sit on the bars; the bars run on from
    the = to just short of it."""
    _, right = _raised(g, 0)
    _bars(g, 2, x0=right + _gap(g.p))


@liga('=:')
def equal_colon(g):
    left, _ = _raised(g, 1)
    _bars(g, 2, x1=left - _gap(g.p))


@liga('::=')
def double_colon_equal(g):
    _raised(g, 0)
    _, right = _raised(g, 1)
    _bars(g, 2, x0=right + _gap(g.p))


# --- Pipes and triangles: simple triangles --------------------------------------

def _pipe_x(g, i):
    """The centre of the pipe of cell i, as it stands alone."""
    sub = _sub('bar', g.p)
    return _at(g, sub, i) + sub.W / 2


def _triangle(g, i, sign, xp):
    """A simple triangle: the chevron of cell i (its point and its 2:1, as
    the plain < or > has them), its arms run back to the pipe's place at xp
    and closed by an upright there, as tall as the arms reach."""
    tip, _, _ = _chev(g, i, sign)
    a = axis(g.p)
    t = abs(tip - xp) / 2
    g.stroke((xp, a + t), (tip, a), (xp, a - t), closed=True)
    return t


@liga('|>')
def pipe_right(g):
    _triangle(g, 1, 1, _pipe_x(g, 0))


@liga('<|')
def pipe_left(g):
    _triangle(g, 0, -1, _pipe_x(g, 1))


@liga('<|>')
def pipe_both(g):
    """Both triangles as one lozenge with the upright through it."""
    xp, a = _pipe_x(g, 1), axis(g.p)
    tl, _, _ = _chev(g, 0, -1)
    tr, _, _ = _chev(g, 2, 1)
    t = min(xp - tl, tr - xp) / 2
    g.stroke((xp, a + t), (tr, a), (xp, a - t), (tl, a), closed=True)
    g.stroke((xp, a - t), (xp, a + t))


@liga('||>')
def pipes_right(g):
    """The triangle, and the other pipe an upright as tall as its side."""
    t = _triangle(g, 2, 1, _pipe_x(g, 1))
    x, a = _pipe_x(g, 0), axis(g.p)
    g.stroke((x, a - t), (x, a + t))


@liga('<||')
def pipes_left(g):
    t = _triangle(g, 0, -1, _pipe_x(g, 1))
    x, a = _pipe_x(g, 2), axis(g.p)
    g.stroke((x, a - t), (x, a + t))


@liga('|||>')
def pipes3_right(g):
    """The triangle, and the other pipes uprights as tall as its side."""
    t = _triangle(g, 3, 1, _pipe_x(g, 2))
    a = axis(g.p)
    for i in (0, 1):
        x = _pipe_x(g, i)
        g.stroke((x, a - t), (x, a + t))


@liga('<|||')
def pipes3_left(g):
    t = _triangle(g, 0, -1, _pipe_x(g, 1))
    a = axis(g.p)
    for i in (2, 3):
        x = _pipe_x(g, i)
        g.stroke((x, a - t), (x, a + t))


# --- Tags: the chevron's arm runs on to the slash -----------------------------------

@liga('</')
def tag_open(g):
    a = axis(g.p)
    line = _slash_line(g, 1)
    tip, _, _ = _chev(g, 0, -1)
    _chevron_to(g, 0, -1, lower=_meet_slash(tip, a, line, -1, up=False))


@liga('/>')
def tag_close(g):
    a = axis(g.p)
    line = _slash_line(g, 0)
    tip, _, _ = _chev(g, 1, 1)
    _chevron_to(g, 1, 1, upper=_meet_slash(tip, a, line, 1, up=True))


@liga('</>')
def tag_empty(g):
    a = axis(g.p)
    line = _slash_line(g, 1)
    tl, _, _ = _chev(g, 0, -1)
    tr, _, _ = _chev(g, 2, 1)
    _chevron_to(g, 0, -1, lower=_meet_slash(tl, a, line, -1, up=False))
    _chevron_to(g, 2, 1, upper=_meet_slash(tr, a, line, 1, up=True))


@liga('<>')
def diamond(g):
    """`<>`: the two chevrons as themselves, their arms run on until they
    meet: one lozenge."""
    tl, el, _ = _chev(g, 0, -1)
    tr, er, _ = _chev(g, 1, 1)
    xm = (el + er) / 2
    _chevron_to(g, 0, -1, upper=(xm - tl) / 2, lower=(xm - tl) / 2)
    _chevron_to(g, 1, 1, upper=(tr - xm) / 2, lower=(tr - xm) / 2)


@liga('<!--')
def html_comment(g):
    """`<!--`: an arrow back to the `!`, then the dashes run together into
    one line (it closes with the arrow `-->`)."""
    p, W = g.p, g.W
    a = axis(p)
    gap = max(1.5 * p.sv, p.m)
    ex, xe = _stamp(g, 'exclam', 1)
    tip = _tip(g, -1)
    head(g, (tip, a), -1)
    g.stroke((tip, a), (xe - gap, a))
    g.stroke((xe + ex.W + gap, a), (W - edge(p), a))


@liga('--')
def double_hyphen(g):
    """`--`: two dashes, each run out to fill its cell, a stroke apart: still
    two (one line would read as an em dash)."""
    p, W = g.p, g.W
    a = axis(p)
    gap = max(p.sv, p.m)
    for x0, x1 in ((edge(p), W / 2 - gap / 2), (W / 2 + gap / 2, W - edge(p))):
        g.stroke((x0, a), (x1, a))


@liga('++')
def double_plus(g):
    """`++`: both plus signs as themselves, their bars run through."""
    p, W = g.p, g.W
    a = axis(p)
    s0, x0 = _stamp(g, 'plus', 0)
    s1, x1 = _stamp(g, 'plus', 1)
    g.stroke((x0 + s0.W / 2, a), (x1 + s1.W / 2, a))


@liga('+++')
def triple_plus(g):
    """`+++`: the three plus signs as themselves, their bars run through."""
    p = g.p
    a = axis(p)
    s0, x0 = _stamp(g, 'plus', 0)
    _stamp(g, 'plus', 1)
    s2, x2 = _stamp(g, 'plus', 2)
    g.stroke((x0 + s0.W / 2, a), (x2 + s2.W / 2, a))


# --- Repeats: the copies drawn together ----------------------------------------
# Fira Code draws a character repeated (`!!` `::` `//` `||` `<<` `&&` ...) as its
# copies brought together, so the run reads as one operator. Here each copy is
# the character as it is drawn alone, the run centred on its cells: the copies
# half a cell apart (STEP), as Fira's are, but with WHITE at least between them
# at Regular, square to their strokes (a wide % or & comes in only as far as
# that; nested chevrons, whose arms are long and shallow, as far as a stroke
# and a half square to the arms); never further apart than set alone. As Fira's,
# the copies stand as far apart at every weight as at Regular, the white
# thinning as the strokes grow, down to WHITE_MIN (where Bold's chevrons part a
# little more).

STEP = 0.5      # of a cell: how far apart a repeat's copies stand
WHITE = 1.5     # strokes (the weight's stem, at least a module): the least white between them at Regular, square to
                # their strokes (measured across instead, << nested into a ≪)
WHITE_MIN = 0.75    # strokes: the least at any weight (each weight its own white instead, Light's << nested into a ≪
                    # and Bold's stood apart as typed)


def _close_pair(a, b, gap):
    """How far apart (in x, ink centre to ink centre) ``a`` and then ``b``
    stand for ``gap`` of white between them, by bisection on the distance."""
    from shapely import affinity
    ca = (a.bounds[0] + a.bounds[2]) / 2
    cb = (b.bounds[0] + b.bounds[2]) / 2
    lo, hi = 0.0, (a.bounds[2] - a.bounds[0] + b.bounds[2] - b.bounds[0]) / 2 + gap
    for _ in range(40):
        mid = (lo + hi) / 2
        if a.distance(affinity.translate(b, ca + mid - cb, 0.0)) < gap:
            lo = mid
        else:
            hi = mid
    return hi


def _run(g, names, dys=None, draw=True):
    """The characters ``names`` together, as a repeat's copies are (STEP,
    WHITE, WHITE_MIN), each as itself (moved up or down by ``dys``), the
    run centred on its cells: each next character as far from the last
    (ink centre to ink centre) as half a cell, or as WHITE between them at
    Regular, or as WHITE_MIN here, whichever is furthest; never further than
    set alone. Returns each one's (glyph, x); ``draw`` False only places them."""
    from ..draw import _cut
    p, W = g.p, g.W
    dys = dys or [0.0] * len(names)
    cut = _cut(p)
    reg = cut[1](400) if cut is not None else p                 # the same cut at Regular

    def inks(q):
        out = []
        for name, dy in zip(names, dys):
            sub = _sub(name, q)
            out.append((sub, _ink_of(sub, 0.0, dy * (q.cap / p.cap))))
        return out
    here, there = inks(p), inks(reg)
    mids = [(i.bounds[0] + i.bounds[2]) / 2 for _, i in here]
    xs = [0.0]                                                  # ink centres, the first at 0
    for k in range(1, len(names)):
        a, b = here[k - 1][1], here[k][1]
        alone = p.fig_adv
        step = max(STEP * p.fig_adv, _close_pair(there[k - 1][1], there[k][1], WHITE * max(reg.sv, reg.m)),
                   _close_pair(a, b, WHITE_MIN * max(p.sv, p.m)))
        xs.append(xs[-1] + min(alone, step))
    lo = min(x + i.bounds[0] - m for x, (_, i), m in zip(xs, here, mids))
    hi = max(x + i.bounds[2] - m for x, (_, i), m in zip(xs, here, mids))
    shift = W / 2 - (lo + hi) / 2
    out = []
    for x, (sub, _), m, dy in zip(xs, here, mids, dys):
        if draw:
            g.add_glyph(sub, shift + x - m, dy)
        out.append((sub, shift + x - m))
    return out


def _together(g, name, n):
    """n copies of ``name`` together (STEP, WHITE), centred on the n cells."""
    _run(g, [name] * n)


def _register_repeats():
    for ch, n in (('!', 2), ('%', 2), ('*', 2), ('*', 3), ('.', 2), ('.', 3), (':', 2), (':', 3),
                  (';', 2), ('/', 2), ('/', 3), ('|', 2), ('|', 3), ('<', 2), ('<', 3), ('>', 2), ('>', 3)):
        name = _names(ch)[0]

        def fn(g, name=name, n=n):
            _together(g, name, n)
        fn.__doc__ = f'`{ch * n}`: {n} copies of {name} together.'
        liga(ch * n)(fn)


_register_repeats()


# Characters brought together the same way, as Fira Code brings them: comments
# (`/*` `*/`), the applicative and plus operators (`<*>` `<+>`, their halves),
# Kotlin's and Swift's (`?.` `.?` `?=` `!!.`), ranges (`..<` `..=`).
def _register_runs():
    for seq in ('/*', '*/', '*>', '<*', '<*>', '<+', '+>', '<+>', '?.', '.?', '?=', '!!.', '..<', '..='):
        names = list(_names(seq))

        def fn(g, names=names):
            _run(g, names)
        fn.__doc__ = f'`{seq}`: its characters together.'
        liga(seq)(fn)


_register_runs()


# Three Fira Code joins, not only brings together (each is one shape in Fira's
# font): `www`, `??`, `&&`. In Arris's strokes:

@liga('www', before='w', after='w')                 # `www.` yes, `wwww` no
def www(g):
    """`www`: the three w's as one zigzag, each next w begun on the last
    one's right upright, which they share: the shared uprights full height
    as a w's own sides are, each w's short middle upright between, so the
    three still read as three. The w's own drawing (lower.w), centred on
    the cells."""
    from ..draw import Glyph
    from .letterframe import Frame
    from .lower import _vee
    p = g.p
    ws = _sub('w', p)
    f = Frame(Glyph(p, 'w', W=ws.W), 14, 'lower')
    xl, xm, xr = f.X(1), ws.W / 2, f.X(13)
    q1, q3 = (xl + xm) / 2, (xm + xr) / 2
    ya = _vee(f)
    yt = min(ya + 2 * (q1 - xl), p.xh)                      # the w's 2:1
    step = xr - xl
    o = g.W / 2 - (xl + 1.5 * step)
    pts = [(o + xl, p.xh), (o + xl, yt)]
    for k in range(3):
        b = o + k * step
        pts += [(b + q1, ya), (b + xm, yt), (b + q3, ya), (b + xr, yt)]
        g.stroke((b + xm, yt), (b + xm, f.Y(6)))           # the w's middle
    g.stroke(*pts, (o + xl + 3 * step, p.xh))
    for k in (1, 2):
        g.stroke((o + xl + k * step, yt), (o + xl + k * step, p.xh))


@liga('??')
def question_question(g):
    """`??`: the two ? where the repeats rule sets them, the second's beak
    leaving from the first one's right side, as the ? of `#?` leaves the
    bar of #: one stroke from the first ? into the second."""
    from ..draw import Glyph
    from .figures import beak_depth
    from .letterframe import Frame
    p = g.p
    (q1, x1), (q2, x2) = _run(g, ['question', 'question'], draw=False)
    g.add_glyph(q1, x1, 0.0)
    side = x1 + Frame(Glyph(p, 'question', W=q1.W), 9, 'cap').X(8)
    g.add_glyph(_led(g, 'question', q2, [(side - x2, p.cap - beak_depth(p))]), x2, 0.0)


@liga('&&')
def ampersand_ampersand(g):
    """`&&`: the two & where the repeats rule sets them, standing on one
    line: the foot of the first (its bowl's floor, under its leg) runs on
    at its weight into the floor of the second."""
    p = g.p
    (a1, x1), (a2, x2) = _run(g, ['ampersand', 'ampersand'], draw=True)
    i1, i2 = _ink_of(a1, x1), _ink_of(a2, x2)
    lo, hi = _runs(i2, x=(i2.bounds[0] + i2.bounds[2]) / 2)[0]       # the floor, across the second's middle
    y = (lo + hi) / 2
    start = max(r[1] for r in _runs(i1, y=y)) - p.c - 0.25 * p.sv
    end = min(r[0] for r in _runs(i2, y=y)) + p.c + 0.25 * p.sv
    g.stroke((start, y, hi - lo), (end, y))


# --- `<$>`: the chevrons' arms run on to the dollar's S --------------------------

def _dollar_wrap(g, left, right):
    """`<$>`, `<$`, `$>`, joined as Fira Code joins them, every character
    as itself and where it stands: the < chevron's lower arm runs on along
    its 2:1 until it lands on the S's bottom bar, the > chevron's upper arm
    until it lands on the top bar, and the S gives up the beak there. One
    stroke runs through both points; the dollar's stem crosses it as it
    crosses the dollar's own S (punct.dollar_stem)."""
    from .figures import beak_depth
    p = g.p
    a = axis(p)
    i = 1 if left else 0
    d_sub = _sub('dollar', p)
    s0 = _at(g, d_sub, i)
    ws = d_sub.W
    x1, x8 = s0 + p.sv / 2, s0 + ws - p.sv / 2                 # caps.S's frame: X(1), X(8)
    y1, y6, y11 = g.sh / 2, p.cap / 2, p.cap - g.sh / 2        # Y(1), Y(6), Y(11)
    d = beak_depth(p)
    pts = []
    if left:
        tip, _, v = _chev(g, 0, -1)
        t = a - y1                                             # the lower arm, down to the bottom bar
        pts += [(tip + 2 * v, a + v), (tip, a), (tip + 2 * t, y1)]
    else:
        pts += [(x1, d), B(x1, y1)]
    pts += [B(x8, y1), B(x8, y6), B(x1, y6), B(x1, y11)]
    if right:
        tip, _, v = _chev(g, i + 1, 1)
        t = y11 - a                                            # the upper arm, up to the top bar
        pts += [(tip - 2 * t, y11), (tip, a), (tip - 2 * v, a - v)]
    else:
        pts += [B(x8, y11), (x8, p.cap - d)]
    g.stroke(*pts, start='v' if left else 'flat', end='v' if right else 'flat')
    xc = s0 + ws / 2
    from .punct import dollar_stem
    through = d_sub.overrides.get('stem', 1.0) >= 0.5          # as the dollar's own stem runs
    for y0, y1 in dollar_stem(p, g.sh, through):
        g.stroke((xc, y0), (xc, y1), start='h' if y0 < 0 else 'flat', end='h' if y1 > p.cap else 'flat')


liga('<$>')(lambda g: _dollar_wrap(g, True, True))
liga('<$')(lambda g: _dollar_wrap(g, True, False))
liga('$>')(lambda g: _dollar_wrap(g, False, True))


# --- `#` run into a bracket ------------------------------------------------------

def _hash(p):
    """`#` as drawn, its bars as (centre y, thickness) low to high, its
    stems as (left, right), all in its own frame. Each bar is measured
    between the right stem and the bar's end, clear of the chamfers that
    cut its end, so it runs on at its full weight."""
    hs = _sub('numbersign', p)
    ink = _ink_of(hs)
    stems = _runs(ink, y=(ink.bounds[1] + ink.bounds[3]) / 2)
    x = (stems[-1][1] + ink.bounds[2]) / 2
    bars = [((lo + hi) / 2, hi - lo) for lo, hi in _runs(ink, x=x)]
    return hs, bars, stems


def _hash_join(g, bracket, after=False):
    """`#{` `#[` `#(`: # and the bracket each as itself in its cell, the
    bars of # running on at their full weight until they meet the
    bracket's spine. The brace's small beak sits between the bars: # moves
    to centre on it (its bars meet the spine above and below the beak).
    ``after``: the bracket first and # after it (`]#`), the bars run back
    to the spine."""
    p = g.p
    hs, bars, stems = _hash(p)
    br, xb = _stamp(g, bracket, 0 if after else 1)
    ib = _ink_of(br, xb)
    xh = _at(g, hs, 1 if after else 0)
    dy = 0.0
    if bracket == 'braceleft':
        top, bot = p.cap + 0.5 * p.m, -p.desc + 0.5 * p.m
        dy = (top + bot) / 2 - (bars[0][0] + bars[-1][0]) / 2
    g.add_glyph(hs, xh, dy)
    tuck = 0.5 * min(p.sv, g.sh)
    for y, th in bars:
        y += dy
        if after:
            hits = [r for r in _runs(ib, y=y) if r[1] < xh + 1]
            if hits:
                g.stroke((xh + stems[0][0] + p.sv / 2, y, th), (hits[-1][1] - tuck, y))
        else:
            hits = [r for r in _runs(ib, y=y) if r[0] > xh + hs.W - 1]
            if hits:
                g.stroke((xh + stems[-1][1] - p.sv / 2, y, th), (hits[0][0] + tuck, y))


liga('#{')(lambda g: _hash_join(g, 'braceleft'))
liga('#[')(lambda g: _hash_join(g, 'bracketleft'))
liga('#(')(lambda g: _hash_join(g, 'parenleft'))
liga(']#')(lambda g: _hash_join(g, 'bracketright', after=True))


@liga('#_', after=OPERATORS + '_')                  # `#__` is a run of underscores
def hash_underscore(g):
    """`#_`: the left stem of `#` runs down at its full weight into the
    underscore, which runs back under it; the corner they make takes the
    corner rule."""
    p = g.p
    hs, bars, stems = _hash(p)
    _, xh = _stamp(g, 'numbersign', 0)
    us, xu = _stamp(g, 'underscore', 1)
    iu = _ink_of(us, xu)
    x0, x1 = stems[0]
    xc, w = xh + (x0 + x1) / 2, x1 - x0
    yu, t = (iu.bounds[1] + iu.bounds[3]) / 2, iu.bounds[3] - iu.bounds[1]
    g.stroke((xc, bars[0][0], w), (xc, yu, t), (iu.bounds[0] + p.sv, yu))


@liga('#_(', after=OPERATORS + '_(')
def hash_underscore_paren(g):
    """`#_(`: one stroke from the # to the top of the (: the left stem
    of # runs down into the underscore, the underscore runs on under the
    paren until it meets the paren's lower diagonal run on down to it, and
    the paren goes on as itself, up its spine to its top. The turns take
    the corner rule."""
    p = g.p
    _, bars, stems = _hash(p)
    _, xh = _stamp(g, 'numbersign', 0)
    us = _sub('underscore', p)
    iu = _ink_of(us, _at(g, us, 1))
    pr = _sub('parenleft', p)
    xp = _at(g, pr, 2)
    x0, x1 = stems[0]
    xc, w = xh + (x0 + x1) / 2, x1 - x0
    yu, t = (iu.bounds[1] + iu.bounds[3]) / 2, iu.bounds[3] - iu.bounds[1]
    top, bot = p.cap + 0.5 * p.m, -p.desc + 0.5 * p.m       # punct._paren
    xs = xp + p.sv / 2
    reach = pr.W - p.sv / 2
    xj = xs + (bot + reach - yu)                            # the paren's lower diagonal, down to the underscore's line
    g.stroke((xc, bars[0][0], w), (xc, yu, t), (xj, yu), (xs, bot + reach), (xs, top - reach),
             (xs + reach, top), end='h')
    g.clip = (-10 * p.cap, -10 * p.cap, 10 * p.cap, top)


# --- `#` with the next character -------------------------------------------------
# Fira Code slants the : ! of `#:` `#!` to its slanted #, and runs the #'s top
# bar into the ? of `#?`. Arris's # stands upright, so the : and ! keep their
# own drawing; what carries over is where they stand and how they meet: the
# character after # brought in toward it (# stays where it stands, at the start
# of `#!/bin/sh`), as far as a repeat's copies come together (WHITE at
# Regular, the same place at every weight, never less than WHITE_MIN), the
# colon's dots on the bars of #, the bars of = level with them, the top bar
# of # run on into the ?.

def _bring(g, build):
    """x of the second of two characters, brought in toward the first:
    ``build(p)`` gives (the first's ink where it stands, the second's ink
    at x = 0, the second's x where it stands)."""
    from shapely import affinity

    from ..draw import _cut
    p = g.p

    def least(q, gap):
        a, b, alone = build(q)
        if a.distance(affinity.translate(b, alone, 0.0)) <= gap:
            return alone
        lo, hi = a.bounds[2] - b.bounds[2], alone
        for _ in range(40):
            mid = (lo + hi) / 2
            if a.distance(affinity.translate(b, mid, 0.0)) < gap:
                lo = mid
            else:
                hi = mid
        return hi
    cut = _cut(p)
    reg = cut[1](400) if cut is not None else p
    alone = build(p)[2]
    return min(alone, max(least(reg, WHITE * max(reg.sv, reg.m)), least(p, WHITE_MIN * max(p.sv, p.m))))


def _led(g, name, sub, lead):
    """``name`` drawn as ``sub`` is, its stroke led in from ``lead`` (points
    in its own frame, left of it: punct.question, punct.at), its clip
    widened to take the lead in."""
    from ..draw import Glyph
    h = Glyph(g.p, name, W=sub.W)
    h.sh_auto = getattr(sub, 'sh_auto', h.sh_auto)
    h.lead = lead
    REGISTRY[name].fn(h)
    if h.clip is not None:
        x0, y0, x1, y1 = h.clip
        h.clip = (min(x0, min(q[0] for q in lead) - g.p.sv), y0, x1, y1)
    return h


def _hash_then(g, name):
    """# as itself in cell 0, ``name`` as itself brought in toward it."""
    def build(q):
        hs, sub = _sub('numbersign', q), _sub(name, q)
        return _ink_of(hs, _at(g, hs, 0)), _ink_of(sub), _at(g, sub, 1)
    _stamp(g, 'numbersign', 0)
    g.add_glyph(_sub(name, g.p), _bring(g, build), 0.0)


liga('#!', after=OPERATORS.replace('/', ''))(lambda g: _hash_then(g, 'exclam'))     # `#!/bin/sh`


@liga('#:')
def hash_colon(g):
    """`#:`: the colon's dots centred on the bars of #, brought in."""
    from shapely.geometry import box
    from shapely.ops import unary_union

    from .punct import dot as dot_

    def build(q):
        hs = _sub('numbersign', q)
        _, bars, _ = _hash(q)
        s = q.dot()
        dots = unary_union([box(-s / 2, y - s / 2, s / 2, y + s / 2) for y, _ in bars])
        return _ink_of(hs, _at(g, hs, 0)), dots, cell(g, 1)[1]
    _stamp(g, 'numbersign', 0)
    x = _bring(g, build)
    s = g.p.dot()
    for y, _ in _hash(g.p)[1]:
        dot_(g, x, y - s / 2)


@liga('#=')
def hash_equal(g):
    """`#=`: the bars of = level with the bars of #, at their weight, run
    on from just past # (the white of `:=`) to the ='s own margin."""
    p = g.p
    _, bars, _ = _hash(p)
    hs, xh = _stamp(g, 'numbersign', 0)
    right = _ink_of(hs, xh).bounds[2]
    eq = _sub('equal', p)
    x1 = _at(g, eq, 1) + eq.W
    for y, th in bars:
        g.stroke((right + _gap(p), y, th), (x1, y))


@liga('#?')
def hash_question(g):
    """`#?`: the top bar of # runs on at its weight into the ?, which
    leaves it upright into its bowl: one stroke from # into the ?."""
    p = g.p
    _, bars, stems = _hash(p)
    _, xh = _stamp(g, 'numbersign', 0)
    q = _sub('question', p)
    xq = _at(g, q, 1)
    y, th = bars[-1]
    g.add_glyph(_led(g, 'question', q, [(xh + stems[-1][1] - p.sv / 2 - xq, y, th)]), xq, 0.0)


# --- Brackets closed by a pipe ----------------------------------------------------

def _closed(g, bracket, ib, ip):
    """`[|` `|]` `{|` `|}`: the bracket (or brace) of cell ib and the pipe
    of cell ip each as themselves, the bracket's arms run on at their own
    weight to just short of the pipe (the white of `:=`), as Fira Code
    runs them: one sign, the pipe still standing on its own (closed into a
    box, `[|` and `|]` would both read as a rectangle)."""
    p = g.p
    br, xb = _stamp(g, bracket, ib)
    xp = _bar_at(g, ip)
    ink = _ink_of(br, xb)
    x0, _, x1, _ = ink.bounds
    right = xp > x1
    x = x1 - p.c - 0.25 * p.sv if right else x0 + p.c + 0.25 * p.sv     # the arm, clear of its end's chamfers
    end = xp - p.sv / 2 - _gap(p) if right else xp + p.sv / 2 + _gap(p)
    rs = _runs(ink, x=x)
    for lo, hi in (rs[0], rs[-1]):
        g.stroke((x, (lo + hi) / 2, hi - lo), (end, (lo + hi) / 2))


_BR = OPERATORS + '[]{}'                # not in `[|]` `{||}`, as Fira Code's
liga('[|', before=_BR, after=_BR)(lambda g: _closed(g, 'bracketleft', 0, 1))
liga('|]', before=_BR, after=_BR)(lambda g: _closed(g, 'bracketright', 1, 0))
liga('{|', before=_BR, after=_BR)(lambda g: _closed(g, 'braceleft', 0, 1))
liga('|}', before=_BR, after=_BR)(lambda g: _closed(g, 'braceright', 1, 0))


# --- Alternates: plain comparisons (ss03) and character variants -----------

def _plain(g):
    """The components as themselves, in their own cells."""
    p = g.p
    comps = g.name.split('.')[0].split('_')
    for i, comp in enumerate(comps):
        sub = _sub(comp, p)
        g.add_glyph(sub, _at(g, sub, i), 0.0)


PLAIN = ('less_equal', 'greater_equal')
for _n in PLAIN:
    glyph(f'{_n}.ss03', None, _body(2), kind=('liga', 2))(_plain)


@glyph('a.cv01', None, lambda p: REGISTRY['a'].width(p), kind='lower')
def a_cv01(g):
    """The single-storey a (the italic's), upright."""
    from .letterframe import Frame
    f = Frame(g, 8, 'lower')
    g.stroke(f.P(7, 0), f.P(7, 9))
    g.stroke(f.P(7, 8), B(*f.P(1, 8)), B(*f.P(1, 1)), f.P(7, 1), closed=True)


# ss06, the code alternates (Mono only; arristype issue #25): letters told
# apart at text sizes in a terminal, where the default's even feet ask the
# reader to know l from i and 1 by their tops alone, and rn from m.
@glyph('l.ss06', None, lambda p: REGISTRY['l'].width(p), kind='lower')
def l_ss06(g):
    """The l with a tail, as the proportional Arris draws it (the 1's flag
    at the top, the t's foot at the bottom), in the Mono's cell: its stem
    where the Mono's t stands, its tail running out to where the t's does."""
    from .letterframe import Frame
    f = Frame(g, 9, 'asc')
    u = g.W / 9
    x = 3.5 * u
    g.stroke((x - 3 * u, f.Y(12)), (x, f.Y(12)), B(x, f.Y(1)), (8.5 * u, f.Y(1)))


@glyph('r.ss06', None, lambda p: REGISTRY['r'].width(p), kind='lower')
def r_ss06(g):
    """The r whose arm turns down at its end: the default's flat arm reads
    long, a cantilever with a void under it, and beside an n the pair reads
    as an m; the arm's drop closes that void (its shape, not its reach, as
    Fira Code's r is drawn). Otherwise the Mono's r: its stem two and a half
    modules in, on a foot."""
    from .letterframe import Frame
    f = Frame(g, 8, 'lower')
    p = g.p
    u = g.W / 9
    xs = f.X(1) + 2.5 * u
    g.stroke((xs, 0), (xs, p.xh))
    k = p.sd / 2 ** 0.5
    y8, y6 = f.Y(8), f.Y(6)
    x6 = xs + p.sv / 2 + k - p.c
    # the drop: a module and a fifth below the arm's lower edge at every weight
    # (on the grid, a heavy arm's own thickness took the whole of it)
    g.stroke((x6, y6), (x6 + (y8 - y6), y8), B(*f.P(8, 8)), (f.X(8), p.xh - g.sh - 1.2 * p.m), start='h')
    g.stroke((xs - 2.5 * u, f.Y(1)), (xs + 2.5 * u, f.Y(1)))


@glyph('zero.cv02', None, 'fig_w', kind='fig')
def zero_cv02(g):
    """The plain zero, without the monospaced cut's dot."""
    p0 = g.p
    g.p = p0.with_(mono=False)
    REGISTRY['zero'].fn(g)
    g.p = p0


def _cls(chars):
    """A class of the characters' glyphs (None for none: no guard)."""
    return '[' + ' '.join(sorted(set(_names(chars)))) + ']' if chars else None


def _chain(name, comps, pre='@LIGA_OPS', post='@LIGA_OPS'):
    """The rules that set ``comps`` as N - 1 LIG and the glyph ``name``,
    unless one of ``pre`` or ``post`` touches them."""
    n = len(comps)
    rest = ' '.join(comps[1:])
    lines = ([f"ignore sub {pre} {comps[0]}' {rest};"] if pre else []) + \
        ([f"ignore sub {comps[0]}' {rest} {post};"] if post else []) + \
        [f"sub {' '.join(['LIG'] * (n - 1))} {comps[-1]}' by {name};"]
    for k in range(n - 2, -1, -1):
        lig = ' '.join(['LIG'] * k)
        lines.append(f"sub {lig + ' ' if lig else ''}{comps[k]}' {' '.join(comps[k + 1:])} by LIG;")
    return lines


# --- Fira Code's optional sets, under Fira's own tags ---------------------------
# Off by default, as in Fira Code, and drawn as the default ligatures are. Fira's
# cv19 and cv23 (`<=` `>=` with a level bar) and cv24 (`/=` as ≠) are how Arris
# draws those by default; cv21 and cv22 are `=<` as ⩽ (the bar slanted) and as ≤
# (level), as Fira's are. Its character variants are not taken (Arris has its
# own characters).

OPTIONAL: dict[str, tuple[str, list[str]]] = {}     # tag -> (label, feature-code lines)


def _optional(tag, label, *lines):
    OPTIONAL.setdefault(tag, (label, []))[1].extend(lines)


def _alt(seq, suffix, fn, tag=None, label=None, **guard):
    """A glyph for ``seq`` (NAMES.suffix, across its cells), set by ``tag``
    where the calt rules would set a ligature (the same guards)."""
    names = _names(seq)
    name = '_'.join(names) + '.' + suffix
    glyph(name, None, _body(len(names)), kind=('liga', len(names)))(fn)
    if tag:
        pre, post = (_cls(guard.get('before', OPERATORS)), _cls(guard.get('after', OPERATORS)))
        if not guard:
            pre = post = '@LIGA_OPS'
        _optional(tag, label, f'lookup {name.replace(".", "_")} {{',
                  *(f'    {r}' for r in _chain(name, list(names), pre, post)), f'}} {name.replace(".", "_")};')
    return name


def _approx(g, struck):
    """`=~` `!~` (ss07): ≈ across the cells, its tildes' flats sharing the
    width as ≈'s do; ≉ struck as ≠ is."""
    from .operators import Tilde, _neg_half, negate, stack
    m = (g.p.fig_w - _sub('equal', g.p).W) / 2
    stack(g, [Tilde(x0=m, x1=g.W - m), Tilde(x0=m, x1=g.W - m)])
    if struck:
        negate(g, half=_neg_half(g))


_alt('=~', 'ss07', lambda g: _approx(g, False), 'ss07', 'Regex matches as ≈ ≉')
_alt('!~', 'ss07', lambda g: _approx(g, True), 'ss07', 'Regex matches as ≈ ≉')


def _gapped(g, n, struck):
    """ss08: the equals of `==` `===` as themselves (each its own); `!=` and
    `!==` struck through the middle, as ≠ is."""
    _run(g, ['equal'] * n)
    if struck:
        off = bars_offset(g)
        _strike(g, [axis(g.p) - off, axis(g.p) + off])


for _seq, _n, _s in (('==', 2, False), ('===', 3, False), ('!=', 2, True), ('!==', 3, True)):
    _g = _alt(_seq, 'ss08', lambda g, n=_n, s=_s: _gapped(g, n, s))
    _optional('ss08', 'Equality gapped', f'sub {_g.replace(".ss08", ".liga")} by {_g};')


def _ss09():
    """`>>=` `<<=` `||=` `|=` (ss09): the runs' own pieces (``sequences``), a
    tail, a double head, the pipes, each into the bars of =."""
    out = ['lookup ss09_runs {']
    for seq, cap in ((('greater', 'greater'), 'tail2'), (('less', 'less'), 'head2'), (('bar', 'bar'), 'bar2'),
                     (('bar',), 'bar')):
        piece = f'equal.seq.s.{cap}'
        c = ' '.join(seq)
        out += [f"    ignore sub @LIGA_OPS {seq[0]}' {' '.join(seq[1:] + ('equal',))};",
                f"    ignore sub {seq[0]}' {' '.join(seq[1:] + ('equal',))} @LIGA_OPS;"]
        if len(seq) == 2:
            out += [f"    sub {seq[0]}' {seq[1]} equal by LIG;", f"    sub LIG {seq[1]}' equal by {piece};"]
        else:
            out += [f"    sub {c}' equal by {piece};"]
        out += [f"    sub {piece} equal' by equal.seq.e;"]
    out.append('} ss09_runs;')
    _optional('ss09', 'Shifts and pipes into =', *out)


_ss09()


def _bar_on(g, a, b, y):
    """ss10: ``a`` and ``b`` as themselves, a's bar nearest the height y
    run on at its own weight until it meets b (the f's into the i's flag,
    the t's bar, the l's stem; the F's and T's top into the l)."""
    p = g.p
    sa, xa = _stamp(g, a, 0)
    sb, xb = _stamp(g, b, 1)
    ia, ib = _ink_of(sa, xa), _ink_of(sb, xb)
    end = max(r[1] for r in _runs(ia, y=y))
    x = end - p.c - 0.25 * p.sv                                 # the bar, clear of its end's chamfers
    lo, hi = min(_runs(ia, x=x), key=lambda r: abs((r[0] + r[1]) / 2 - y))
    yc = (lo + hi) / 2
    hits = [r for r in _runs(ib, y=yc) if r[0] > end - 1]
    if hits:
        g.stroke((x, yc, hi - lo), (hits[0][0] + 0.5 * min(p.sv, g.sh), yc))


for _seq in ('Fl', 'Tl', 'fi', 'fj', 'fl', 'ft'):
    _a, _b = _names(_seq)
    _alt(_seq, 'ss10', lambda g, a=_a, b=_b: _bar_on(g, a, b, (g.p.cap if a.isupper() else g.p.xh) - g.sh / 2),
         'ss10', 'Text ligatures (Fl Tl fi fj fl ft)', before='', after='')
_alt('<=', 'cv20', lambda g: _arrow(g, bars=2, right=False, left=True))
_optional('cv20', '<= as an arrow', 'sub less_equal.liga by less_equal.cv20;')
_alt('=<', 'cv21', lambda g: _compare(g, False, slant=True), 'cv21', '=< as ≤, its bar slanted')
_alt('=<', 'cv22', lambda g: _compare(g, False), 'cv22', '=< as ≤, its bar level')


def _dot_then(g, after, colon=False):
    """`.-` `:-` `.=` (cv25 cv26 cv32): the period raised to the axis (the
    colon's dots to the bars of =, as `:=` raises them), the hyphen's line
    (or the bars of =) run back to just short of it, as `:=`'s are."""
    p = g.p
    if colon:
        _, right = _raised(g, 0)
    else:
        s = p.dot()
        x = cell(g, 0)[1]
        dot(g, x, axis(p) - s / 2)
        right = x + s / 2
    if after == 'hyphen':
        g.stroke((right + _gap(p), axis(p)), (g.W - edge(p), axis(p)))
    else:
        _bars(g, 2, x0=right + _gap(p))


_alt('.-', 'cv25', lambda g: _dot_then(g, 'hyphen'), 'cv25', '.- joined')
_alt(':-', 'cv26', lambda g: _dot_then(g, 'hyphen', colon=True), 'cv26', ':- joined')
_alt('.=', 'cv32', lambda g: _dot_then(g, 'equal'), 'cv32', '.= joined')


@lambda fn: _alt('[]', 'cv27', fn, 'cv27', '[] as a box', before=OPERATORS + '[]', after=OPERATORS + '[]')
def _box(g):
    """`[]` (cv27): the brackets as themselves, their arms run on until they
    meet: a box."""
    p = g.p
    b0, x0 = _stamp(g, 'bracketleft', 0)
    b1, x1 = _stamp(g, 'bracketright', 1)
    i0, i1 = _ink_of(b0, x0), _ink_of(b1, x1)
    x = i0.bounds[2] - p.c - 0.25 * p.sv
    xe = i1.bounds[0] + p.c + 0.25 * p.sv
    rs = _runs(i0, x=x)
    for lo, hi in (rs[0], rs[-1]):
        g.stroke((x, (lo + hi) / 2, hi - lo), (xe, (lo + hi) / 2))


def _brace_dot(g, right):
    """`{.` `.}` (cv28): the brace as itself, the period raised to its
    point, where it stands."""
    p = g.p
    _stamp(g, 'braceright' if right else 'braceleft', 1 if right else 0)
    s = p.dot()
    mid = (p.cap + 0.5 * p.m - p.desc + 0.5 * p.m) / 2      # punct._brace
    dot(g, cell(g, 0 if right else 1)[1], mid - s / 2)


_alt('{.', 'cv28', lambda g: _brace_dot(g, False), 'cv28', '{. .} with a raised dot')
_alt('.}', 'cv28', lambda g: _brace_dot(g, True), 'cv28', '{. .} with a raised dot')


SS06 = ('l', 'r')     # the code alternates' letters (their .ss06 glyphs, the Mono's only)


def alternates_fea(mono: bool) -> str:
    def cv(tag, label, sub):
        return (f'feature {tag} {{\n    cvParameters {{\n        FeatUILabelNameID {{ name "{label}"; }};\n'
                f'    }};\n    {sub}\n}} {tag};')
    out = [cv('cv01', 'Single-storey a', 'sub a by a.cv01;'),
           cv('cv02', 'Plain zero', 'sub zero by zero.cv02;')]
    if mono:
        subs = '\n'.join(f'    sub {n}.liga by {n}.ss03;' for n in PLAIN)
        out.append(f'feature ss03 {{\n    featureNames {{ name "Plain comparisons"; }};\n{subs}\n}} ss03;')
        out.append('feature ss06 {\n    featureNames { name "Code alternates: tailed l, r with a dropped arm"; };\n'
                   + '\n'.join(f'    sub {n} by {n}.ss06;' for n in SS06) + '\n} ss06;')
        for tag in sorted(OPTIONAL):
            label, lines = OPTIONAL[tag]
            body = '\n'.join(f'    {ln}' for ln in lines)
            if tag.startswith('ss'):
                out.append(f'feature {tag} {{\n    featureNames {{ name "{label}"; }};\n{body}\n}} {tag};')
            else:
                out.append(f'feature {tag} {{\n    cvParameters {{\n        FeatUILabelNameID {{ name "{label}"; }};\n'
                           f'    }};\n{body}\n}} {tag};')
    return '\n'.join(out) + '\n'


# --- Feature code ---------------------------------------------------------



def fea() -> str:
    """calt lookups, longest sequences first: each component but the last
    becomes LIG, the last the ligature. A ligature never forms when an
    operator character touches it on either side (or those its GUARDS
    name): longer operators that are ligatures are matched first, and the
    rest (`<=<`, `>>=`, `//=`) stay as their characters, or make a run of
    any length (``sequences``)."""
    out = [f'@LIGA_OPS = {_cls(OPERATORS)};']
    for name, comps in sorted(LIGATURES, key=lambda t: -len(t[1])):
        tag = name.replace('.', '_')
        guard = () if name not in GUARDS else tuple(_cls(c) for c in GUARDS[name])
        body = '\n'.join(f'    {r}' for r in _chain(name, comps, *guard))
        out.append(f'lookup {tag} {{\n{body}\n}} {tag};')
    body = '\n'.join(out[1:])
    return f'{out[0]}\nfeature calt {{\n{body}\n}} calt;\n'
