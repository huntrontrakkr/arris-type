"""Arris Mono's programming ligatures.

Code is set in a fixed grid, so a ligature here never changes the grid: a
sequence of N characters becomes N - 1 empty spacers (LIG) and one glyph
one cell wide that draws back across the N cells (the scheme Fira Code
made standard). The substitution is contextual (`calt`, on by default and
easy to turn off in editors), longest sequences first, with guards so a
ligature never forms inside a longer run of the same characters (`--->`,
`<=<`, `====`).

A ligature keeps every character where it stands and as it is drawn
alone: the < of `</span>` is the < of `<span>`, the bars of `==` are the
bars of =. A join only runs a character's own strokes on, in their own
direction, until they meet the next one (the chevron's arm to the slash in
`</`, to the pipe in `|>`, to the S's bars in `<$>`; the bars of # to the
bracket's spine), so an N-character ligature is N cells wide and set as
the characters would be. Where a sequence becomes a new sign, it is drawn
across its cells: the arrows (one 45-degree head, 0.88 of the cap height,
its point kept sharp, the shaft ending inside it), the struck bars of !=,
the larger <= and >=, the raised colon of :=. Sequences that would only
be drawn closer together (`||` `::` `//` `>>`) are left as their
characters (``docs/DESIGN.md``, section 8).
"""
from __future__ import annotations

from ..draw import REGISTRY, B, glyph
from ..params import SQRT2
from .punct import axis, dot

LIGATURES: list[tuple[str, tuple[str, ...]]] = []   # (glyph name, component glyph names), longest first at build
COMPONENTS: dict[str, tuple[str, ...]] = {}         # glyph name -> component glyph names

HEAD = 0.44          # an arrowhead's half-height, of the cap height (Fira Code's: 0.88 of it in all)
DOUBLE = 0.6         # a double head's second chevron: this share of the head behind the first, plus its stroke
LE_HALF = 0.42       # the chevron of <= and >=: half its height, of the cap height


def _names(seq: str) -> tuple[str, ...]:
    cmap = {chr(s.unicode): n for n, s in REGISTRY.items() if s.unicode}
    return tuple(cmap[ch] for ch in seq)


def _body(n):
    """A ligature's body: the n cells' bodies and the gaps between them."""
    return lambda p: n * p.fig_adv - (p.fig_adv - p.fig_w)


def liga(*seqs):
    """Register a drawing for one or more character sequences of the same
    length (`!=` and `/=` share the struck double bar)."""
    def deco(fn):
        for seq in seqs:
            names = _names(seq)
            name = '_'.join(names) + '.liga'
            if len(name) > 31:                  # legacy limit: the AGL's code-point form
                name = 'uni' + ''.join(f'{ord(ch):04X}' for ch in seq) + '.liga'
            COMPONENTS[name] = names
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


def _wave(g, sign):
    """`~>`, `~~>`, `<~`: the tilde's step (up at 45 degrees, along, down,
    along) at the tilde's own period, leaving and rejoining the axis, into
    the arrows' head."""
    p, W = g.p, g.W
    a = axis(p)
    d = REGISTRY['asciitilde'].width(p) / 4                  # the tilde's step (punct.asciitilde)
    tip, start = _tip(g, 1), edge(p)
    run = tip - head_h(p) - start                            # the shaft's room behind the barbs
    n = max(1, int(run // (4 * d)))
    x0 = start + (run - 4 * d * n) / 2
    pts = [(start, a)] if x0 > start + 1 else []
    for i in range(n):
        x = x0 + 4 * d * i
        pts += [(x, a), (x + d / 2, a + d / 2), (x + 3 * d / 2, a + d / 2),
                (x + 5 * d / 2, a - d / 2), (x + 7 * d / 2, a - d / 2)]
    pts += [(x0 + 4 * d * n, a), (tip, a)]
    if sign < 0:
        pts = [(W - x, y) for x, y in pts]
    g.stroke(*pts)
    head(g, ((W - tip) if sign < 0 else tip, a), sign)


liga('~>', '~~>')(lambda g: _wave(g, 1))
liga('<~')(lambda g: _wave(g, -1))


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

def _bars(g, n, x0=None, x1=None):
    """The bars of = run through the cells, from ='s own margin to its
    own margin; three for ===, the same white between each."""
    from .punct import eq_white
    p, W = g.p, g.W
    a = axis(p)
    m = (p.fig_w - _sub('equal', p).W) / 2
    x0 = m if x0 is None else x0
    x1 = W - m if x1 is None else x1
    step = g.sh + eq_white(g)
    ys = [a + (i - (n - 1) / 2) * step for i in range(n)]
    for y in ys:
        g.stroke((x0, y), (x1, y))
    return ys


def _strike(g, ys):
    """The 2:1 slash of != across bars at heights ys, as ≠ draws it."""
    lo, hi = min(ys) - 2.2 * g.sh, max(ys) + 2.2 * g.sh
    cx = g.W / 2
    run = (hi - lo) / 2
    g.stroke((cx - run / 2, lo), (cx + run / 2, hi), start='h', end='h')


liga('==')(lambda g: _bars(g, 2))
liga('===')(lambda g: _bars(g, 3))
liga('!=', '/=', '=/=')(lambda g: _strike(g, _bars(g, 2)))
liga('!==')(lambda g: _strike(g, _bars(g, 3)))


def _compare(g, mirror):
    """`<=` and `>=`: ≤ and ≥ at full size across the two cells: the <
    chevron's 2:1 at LE_HALF of the cap height, the equal sign's white, and
    a bar as long as the chevron is wide; the pair centred on the axis."""
    import math
    from .punct import SLOPE, eq_white
    from ..draw import _thickness
    p, W = g.p, g.W
    t = _thickness(p, g.sh)((2, 1))
    kv = t / (2 * math.cos(SLOPE))
    x_tip = t / (2 * math.sin(SLOPE))
    h = LE_HALF * p.cap
    white = eq_white(g)
    a = axis(p) + (white + g.sh) / 2
    x0 = (W - 2 * h - x_tip) / 2 + x_tip                       # the point, the whole sign centred
    x1 = x0 + 2 * h
    pts = [(x1, a + h), (x0, a), (x1, a - h)]
    if mirror:
        pts = [(W - x, y) for x, y in pts]
    g.stroke(*pts, start='v', end='v')
    yb = a - h - kv - white - g.sh / 2
    g.stroke((x0 - x_tip, yb), (x1, yb)) if not mirror else g.stroke((W - x1, yb), (W - x0 + x_tip, yb))


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


# --- `<$>`: the chevrons' arms run on to the dollar's S --------------------------

def _dollar_wrap(g, left, right):
    """`<$>`, `<$`, `$>`, joined as Fira Code joins them, every character
    as itself and where it stands: the < chevron's lower arm runs on along
    its 2:1 until it lands on the S's bottom bar, the > chevron's upper arm
    until it lands on the top bar, and the S gives up the beak there. One
    stroke runs through both points; the dollar's stem crosses it."""
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
    g.stroke((xc, -1.5 * p.m), (xc, p.cap + 1.5 * p.m), start='h', end='h')


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


def _hash_join(g, bracket):
    """`#{` `#[` `#(`: # and the bracket each as itself in its cell, the
    bars of # running on at their full weight until they meet the
    bracket's spine. The brace's small beak sits between the bars: # moves
    to centre on it (its bars meet the spine above and below the beak)."""
    p = g.p
    hs, bars, stems = _hash(p)
    br, xb = _stamp(g, bracket, 1)
    ib = _ink_of(br, xb)
    xh = _at(g, hs, 0)
    dy = 0.0
    if bracket == 'braceleft':
        top, bot = p.cap + 0.5 * p.m, -p.desc + 0.5 * p.m
        dy = (top + bot) / 2 - (bars[0][0] + bars[-1][0]) / 2
    g.add_glyph(hs, xh, dy)
    right = xh + hs.W
    for y, th in bars:
        y += dy
        hits = [r for r in _runs(ib, y=y) if r[0] > right - 1]
        if hits:
            g.stroke((xh + stems[-1][1] - p.sv / 2, y, th), (hits[0][0] + 0.5 * min(p.sv, g.sh), y))


liga('#{')(lambda g: _hash_join(g, 'braceleft'))
liga('#[')(lambda g: _hash_join(g, 'bracketleft'))
liga('#(')(lambda g: _hash_join(g, 'parenleft'))


@liga('#_')
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


@glyph('zero.cv02', None, 'fig_w', kind='fig')
def zero_cv02(g):
    """The plain zero, without the monospaced cut's dot."""
    p0 = g.p
    g.p = p0.with_(mono=False)
    REGISTRY['zero'].fn(g)
    g.p = p0


def alternates_fea(mono: bool) -> str:
    def cv(tag, label, sub):
        return (f'feature {tag} {{\n    cvParameters {{\n        FeatUILabelNameID {{ name "{label}"; }};\n'
                f'    }};\n    {sub}\n}} {tag};')
    out = [cv('cv01', 'Single-storey a', 'sub a by a.cv01;'),
           cv('cv02', 'Plain zero', 'sub zero by zero.cv02;')]
    if mono:
        subs = '\n'.join(f'    sub {n}.liga by {n}.ss03;' for n in PLAIN)
        out.append(f'feature ss03 {{\n    featureNames {{ name "Plain comparisons"; }};\n{subs}\n}} ss03;')
    return '\n'.join(out) + '\n'


# --- Feature code ---------------------------------------------------------

OPERATORS = '-<>=!|:.+*/~&?^%#$\\'


def fea() -> str:
    """calt lookups, longest sequences first: each component but the last
    becomes LIG, the last the ligature. A ligature never forms when an
    operator character touches it on either side: longer operators that are
    ligatures are matched first, and the rest (`<=<`, `>>=`, `//=`, `---->`)
    stay as their characters."""
    ops = ' '.join(sorted(set(_names(OPERATORS))))
    out = [f'@LIGA_OPS = [{ops}];']
    for name, comps in sorted(LIGATURES, key=lambda t: -len(t[1])):
        n = len(comps)
        tag = name.replace('.', '_')
        rest = ' '.join(comps[1:])
        lines = [f'lookup {tag} {{',
                 f"    ignore sub @LIGA_OPS {comps[0]}' {rest};",
                 f"    ignore sub {comps[0]}' {rest} @LIGA_OPS;",
                 f"    sub {' '.join(['LIG'] * (n - 1))} {comps[-1]}' by {name};"]
        for k in range(n - 2, -1, -1):
            pre = ' '.join(['LIG'] * k)
            after = ' '.join(comps[k + 1:])
            lines.append(f"    sub {pre + ' ' if pre else ''}{comps[k]}' {after} by LIG;")
        lines.append(f'}} {tag};')
        out.append('\n'.join(lines))
    body = '\n'.join(out[1:])
    return f'{out[0]}\nfeature calt {{\n{body}\n}} calt;\n'
