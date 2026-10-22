"""Arris Mono's programming ligatures.

Code is set in a fixed grid, so a ligature here never changes the grid: a
sequence of N characters becomes N - 1 empty spacers (LIG) and one glyph
one cell wide that draws back across the N cells (the scheme Fira Code
made standard). The substitution is contextual (`calt`, on by default and
easy to turn off in editors), longest sequences first, with guards so a
ligature never forms inside a longer run of the same characters (`--->`,
`<=<`, `====`).

A ligature exists only where joining says something the characters set
apart cannot, and is built, like Fira Code's, from a few parts shared by
every sequence (``docs/DESIGN.md``, section 8):

* **Arrows**: one head, a single 45-degree chevron whose point stays sharp
  under the corner rule, 0.88 of the cap height; shafts on the axis that
  end inside it; the font's own `|` where an arrow starts or stops at a
  bar. An arrow keeps the hyphen's margins at both ends.
* **Equality**: the bars of `=` run through; `!=` strikes them.
* **Tags**: the 2:1 slash with 2:1 chevrons the other way, whose arms
  meet it square (`</>`); the pipe closed by a chevron into a triangle
  (`|>`).
* **`#` and brackets**: the bracket exactly as itself (it must match its
  closing partner) and `#` moved up to it, its bars running on at full
  weight until they meet the bracket.
* **Pairs** of narrow signs (`||` `::` `!!` `..`): moved toward each other
  until half a cell of white is left between them. Wide signs (`&&`,
  `??`) are already closer than that and are left as they are.
"""
from __future__ import annotations

from ..draw import REGISTRY, B, glyph
from ..params import SQRT2
from .punct import axis, dot

LIGATURES: list[tuple[str, tuple[str, ...]]] = []   # (glyph name, component glyph names), longest first at build
COMPONENTS: dict[str, tuple[str, ...]] = {}         # glyph name -> component glyph names

HEAD = 0.44          # an arrowhead's half-height, of the cap height (Fira Code's: 0.88 of it in all)
DOUBLE = 0.6         # a double head's second chevron: this share of the head behind the first, plus its stroke
PAIR_WHITE = 0.5     # white left between a pair's signs, of a cell
TAG_CHEVRON = 0.6    # a tag chevron's height, of its slash's
TRIANGLE = 0.55      # a pipe triangle's half-height, of the cap height


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
    """Half the distance between the bars of `=`."""
    return (g.sh + max(0.8 * g.sh, g.p.m)) / 2


def tag_h(p):
    """Half the height of `<` (punct._chevron): the tags' slash."""
    return REGISTRY['less'].width(p) - p.sv / 2


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


# --- Equality and comparison ---------------------------------------------

def _bars(g, n, x0=None, x1=None):
    p, W = g.p, g.W
    a = axis(p)
    off = bars_offset(g)
    m = (p.fig_w - _sub('equal', p).W) / 2                  # `=`'s own margin
    x0 = m if x0 is None else x0
    x1 = W - m if x1 is None else x1
    ys = [a - off, a + off] if n == 2 else [a - 2 * off, a, a + 2 * off]
    for y in ys:
        g.stroke((x0, y), (x1, y))
    return ys


def _strike(g, ys):
    """The 2:1 slash of `!=` across bars at heights ys."""
    lo, hi = min(ys) - 2.2 * g.sh, max(ys) + 2.2 * g.sh
    cx = g.W / 2
    run = (hi - lo) / 2
    g.stroke((cx - run / 2, lo), (cx + run / 2, hi), start='h', end='h')


liga('==')(lambda g: _bars(g, 2))
liga('===')(lambda g: _bars(g, 3))
liga('!=', '/=', '=/=')(lambda g: _strike(g, _bars(g, 2)))
liga('!==')(lambda g: _strike(g, _bars(g, 3)))


def _compare(g, mirror):
    """`<=` and `>=`: the font's own ≤ and ≥, centred in the two cells and
    a little larger."""
    p, W = g.p, g.W
    k = p.sd / SQRT2
    h = min(0.42 * p.cap, 0.85 * (p.fig_w - p.sv / 2))
    gap = max(0.8 * g.sh, 0.6 * p.m)
    a = axis(p) + (g.sh + gap) / 2
    x0, x1 = W / 2 - h / 2, W / 2 + h / 2
    if not mirror:
        g.stroke((x1, a + h), (x0, a), (x1, a - h), start='v', end='v')
    else:
        g.stroke((x0, a + h), (x1, a), (x0, a - h), start='v', end='v')
    yb = a - h - k - gap - g.sh / 2
    g.stroke((x0 - p.sv / 2, yb), (x1 + p.sv / 2, yb))


liga('<=')(lambda g: _compare(g, False))
liga('>=')(lambda g: _compare(g, True))


# --- Pairs: narrow signs drawn closer --------------------------------------

def _pitch(g, name):
    """Centre to centre for a pair of ``name``: half a cell of white
    between them (never more than their cells' own)."""
    p = g.p
    return min(p.fig_adv, _sub(name, p).W + PAIR_WHITE * p.fig_adv)


def _row(g, name, n, xc=None, dy=0.0):
    """n copies of ``name`` at the pair pitch, centred at xc (or in the
    ligature); returns their centres."""
    sub = _sub(name, g.p)
    pitch = _pitch(g, name)
    xc = g.W / 2 if xc is None else xc
    xs = [xc + (i - (n - 1) / 2) * pitch for i in range(n)]
    for x in xs:
        g.add_glyph(sub, x - sub.W / 2, dy)
    return xs


def pair(*seqs):
    for seq in seqs:
        liga(seq)(lambda g: _row(g, COMPONENTS[g.name][0], len(COMPONENTS[g.name])))


pair('||', '|||', '::', ':::', '..', '...', '!!', ';;')


def _raised(g, n, xc):
    """n colons' dots raised to the bars of `=` (`:=` `=:` `::=`), at the
    pair pitch; returns the extreme dots' outer edges (left, right)."""
    p = g.p
    s = p.dot()
    a = axis(p)
    off = bars_offset(g)
    pitch = _pitch(g, 'colon')
    xs = [xc + (i - (n - 1) / 2) * pitch for i in range(n)]
    for x in xs:
        for y in (a - off, a + off):
            dot(g, x, y - s / 2)
    return xs[0] - s / 2, xs[-1] + s / 2


def _gap(p):
    return max(p.m, 0.6 * p.dot())


@liga(':=')
def colon_equal(g):
    """The colon raised so its dots sit on the bars."""
    _, right = _raised(g, 1, cell(g, 0)[1] + 0.15 * g.p.fig_adv)
    _bars(g, 2, x0=right + _gap(g.p))


@liga('=:')
def equal_colon(g):
    left, _ = _raised(g, 1, cell(g, 1)[1] - 0.15 * g.p.fig_adv)
    _bars(g, 2, x1=left - _gap(g.p))


@liga('::=')
def double_colon_equal(g):
    p = g.p
    _, right = _raised(g, 2, cell(g, 1)[0] - 0.05 * p.fig_adv)
    _bars(g, 2, x0=right + _gap(p))


@liga('..<', '..=')
def range_op(g):
    """`..<` `..=`: the pair of dots, then the sign as itself."""
    p = g.p
    last = _sub(COMPONENTS[g.name][-1], p)
    x = _at(g, last, 2)
    g.add_glyph(last, x, 0.0)
    _row(g, 'period', 2, xc=x / 2)


# --- Pipes and triangles -----------------------------------------------------

def _pipe_tri(g, left, right, bars=0):
    """`|>`, `<|`, `<|>`, `||>`, `<||`: the pipe closed into a triangle by a
    chevron at the tags' 2:1, its arms ending on the pipe's ends; `||>` and
    `<||` stand another pipe beside it, at the pair pitch."""
    p, W = g.p, g.W
    a = axis(p)
    h = TRIANGLE * p.cap
    pitch = _pitch(g, 'bar')
    span = 2 * h * (left + right) + bars * pitch
    xb = (W - span) / 2 + (2 * h if left else 0) + (bars * pitch if not left else 0)
    if left and right:
        g.stroke((xb, a + h), (xb + 2 * h, a), (xb, a - h), (xb - 2 * h, a), closed=True)
        g.stroke((xb, a - h), (xb, a + h))
    elif right:
        g.stroke((xb, a + h), (xb + 2 * h, a), (xb, a - h), closed=True)
    else:
        g.stroke((xb, a + h), (xb - 2 * h, a), (xb, a - h), closed=True)
    for i in range(1, bars + 1):
        x = xb - i * pitch if right else xb + i * pitch
        g.stroke((x, a - h), (x, a + h))


liga('|>')(lambda g: _pipe_tri(g, False, True))
liga('<|')(lambda g: _pipe_tri(g, True, False))
liga('<|>')(lambda g: _pipe_tri(g, True, True))
liga('||>')(lambda g: _pipe_tri(g, False, True, bars=1))
liga('<||')(lambda g: _pipe_tri(g, True, False, bars=1))


# --- Tags and comments ---------------------------------------------------------

def _tag(g, path):
    """`</`, `/>`, `</>`: the slash at its 2:1, as tall as `<`, and
    chevrons at the 2:1 the other way, shorter, whose arms run square into
    the slash (a 2:1 arm is perpendicular to the 2:1 slash): `<`'s lower
    arm meets it near its foot, `>`'s upper arm near its top, and the slash
    runs on past both."""
    p, W = g.p, g.W
    a = axis(p)
    hs = tag_h(p)
    hc = TAG_CHEVRON * hs
    left, right = path[0] == '<', path[-1] == '>'
    j1, j2 = -hc / 2, hc / 2                                     # the slash at a - hc and a + hc (its centre at 0)
    lo = min([-hs / 2] + ([j1 - 2 * hc] if left else []))
    hi = max([hs / 2] + ([j2 + 2 * hc] if right else []))
    xm = (W - (hi - lo)) / 2 - lo
    g.stroke((xm - hs / 2, a - hs), (xm + hs / 2, a + hs), start='h', end='h')
    if left:
        x = xm + j1
        g.stroke((x, a + hc), (x - 2 * hc, a), (x, a - hc), start='v')
    if right:
        x = xm + j2
        g.stroke((x, a + hc), (x + 2 * hc, a), (x, a - hc), end='v')


liga('</')(lambda g: _tag(g, '</'))
liga('/>')(lambda g: _tag(g, '/>'))
liga('</>')(lambda g: _tag(g, '</>'))


@liga('<>')
def diamond(g):
    """`<>`: the tags' two chevrons closed into one flat lozenge."""
    p, W = g.p, g.W
    a = axis(p)
    hc = min(TAG_CHEVRON * tag_h(p), (W - 2 * p.sd) / 4)
    x = W / 2
    g.stroke((x, a + hc), (x - 2 * hc, a), (x, a - hc), (x + 2 * hc, a), closed=True)


@liga('<!--')
def html_comment(g):
    """`<!--`: an arrow back to the `!`, then the dashes run together into
    one line."""
    p, W = g.p, g.W
    a = axis(p)
    gap = max(1.5 * p.sv, p.m)
    ex = _sub('exclam', p)
    xe = _at(g, ex, 1)
    g.add_glyph(ex, xe, 0.0)
    tip = _tip(g, -1)
    head(g, (tip, a), -1)
    g.stroke((tip, a), (xe - gap, a))
    g.stroke((xe + ex.W + gap, a), (W - edge(p), a))


@liga('--')
def double_hyphen(g):
    """`--`: two dashes, each grown to fill its cell, a stroke apart: still
    two (one line would read as an em dash)."""
    p, W = g.p, g.W
    a = axis(p)
    gap = max(p.sv, p.m)
    for x0, x1 in ((edge(p), W / 2 - gap / 2), (W / 2 + gap / 2, W - edge(p))):
        g.stroke((x0, a), (x1, a))


@liga('++')
def double_plus(g):
    p, W = g.p, g.W
    a = axis(p)
    h = p.fig_w / 2 - p.sv / 2
    g.stroke((edge(p), a), (W - edge(p), a))
    for i in (0, 1):
        _, c, _ = cell(g, i)
        x = c + (1 - 2 * i) * 0.12 * p.fig_adv
        g.stroke((x, a - h), (x, a + h))


def _slashes(g, n):
    from .punct import slash_width
    p, W = g.p, g.W
    sw = slash_width(p)
    pitch = min(p.fig_adv, sw * 0.75)
    span = sw + (n - 1) * pitch
    x0 = (W - span) / 2
    top, bot = p.cap + 0.5 * p.m, -p.desc + 0.5 * p.m
    run = (top - bot) / 2
    for i in range(n):
        xl = x0 + i * pitch + (sw - run) / 2
        g.stroke((xl, bot), (xl + run, top), start='h', end='h')
    g.clip = (0, bot, W, top)


liga('//')(lambda g: _slashes(g, 2))
liga('///')(lambda g: _slashes(g, 3))


def _chevrons(g, n, sign):
    p, W = g.p, g.W
    r = 0.75 * (p.fig_w - p.sv / 2)
    pitch = min(p.fig_adv * 0.75, r + 1.6 * p.sv)
    span = r + (n - 1) * pitch
    x = (W - span) / 2 + (r if sign > 0 else 0)
    for _ in range(n):
        g.stroke((x - sign * r, axis(p) + r), (x, axis(p)), (x - sign * r, axis(p) - r), start='v', end='v')
        x += pitch


liga('>>')(lambda g: _chevrons(g, 2, 1))
liga('<<')(lambda g: _chevrons(g, 2, -1))
liga('>>>')(lambda g: _chevrons(g, 3, 1))
liga('<<<')(lambda g: _chevrons(g, 3, -1))


@liga('/*', '*/')
def comment(g):
    """The slash as itself, and the font's own asterisk raised to the
    slash's middle: the comment's mark reads as one sign."""
    p = g.p
    opening = COMPONENTS[g.name][0] == 'slash'
    sl, st = _sub('slash', p), _sub('asterisk', p)
    i_slash, i_star = (0, 1) if opening else (1, 0)
    xs = _at(g, sl, i_slash) + (1 if opening else -1) * 0.1 * p.fig_adv
    g.add_glyph(sl, xs, 0.0)
    iss, ist = _ink_of(sl), _ink_of(st)
    dy = (iss.bounds[1] + iss.bounds[3]) / 2 - (ist.bounds[1] + ist.bounds[3]) / 2
    g.add_glyph(st, _at(g, st, i_star) - (1 if opening else -1) * 0.1 * p.fig_adv, dy)


# --- `#` run into a bracket ------------------------------------------------------

def _hash(p):
    """`#` as drawn, its bars as (centre y, thickness) low to high, its
    stems as (left, right), and its ink, all in its own frame. Each bar is
    measured between the right stem and the bar's end, clear of the
    chamfers that cut its end, so it runs on at its full weight."""
    hs = _sub('numbersign', p)
    ink = _ink_of(hs)
    stems = _runs(ink, y=(ink.bounds[1] + ink.bounds[3]) / 2)
    x = (stems[-1][1] + ink.bounds[2]) / 2
    bars = [((lo + hi) / 2, hi - lo) for lo, hi in _runs(ink, x=x)]
    return hs, bars, stems, ink


def _hash_join(g, bracket):
    """`#{` `#[` `#(`: the bracket exactly as itself, where it stands in its
    cell (so it matches the closing one), and `#` moved up to it: its bars
    run on at their full weight until they meet the bracket. The bracket's
    spine stands as far from `#`'s right stem as `#`'s stems stand apart,
    so the bars close one more square; the brace's point keeps that much
    white from the stem instead. `#` is centred on the brace's point, so
    its bars meet the brace alike above and below: on the point's arms where
    the point is taller than the bars stand apart (Thin, Regular), on the
    spine where it is not (Black)."""
    p = g.p
    hs, bars, stems, ink = _hash(p)
    white = stems[1][0] - stems[0][1]                          # between `#`'s stems
    right = stems[-1][1]
    br = _sub(bracket, p)
    xb = _at(g, br, 1)
    ib = _ink_of(br, xb)
    dy = 0.0
    if bracket == 'braceleft':
        top, bot = p.cap + 0.5 * p.m, -p.desc + 0.5 * p.m
        mid = (top + bot) / 2                                   # (punct._brace)
        xs = xb + br.W - p.sv / 2 - p.sv                        # its spine
        xp = xb + p.sv / 2                                      # its point
        reach = xs - xp
        dy = mid - (bars[0][0] + bars[-1][0]) / 2
        dx = (xp - p.sd / SQRT2) - white - right                # the point keeps the stems' white
        ends = [xp + min(abs(y + dy - mid), reach) for y, _ in bars]
    else:
        spine = _runs(ib, y=(bars[0][0] + bars[-1][0]) / 2)[0][0] + p.sv / 2
        dx = spine - p.sv / 2 - white - right
        ends = [spine for _ in bars]
    g.add_glyph(hs, dx, dy)
    g.add_glyph(br, xb, 0.0)
    for (y, th), end in zip(bars, ends):
        g.stroke((dx + right - p.sv / 2, y + dy, th), (end, y + dy))


liga('#{')(lambda g: _hash_join(g, 'braceleft'))
liga('#[')(lambda g: _hash_join(g, 'bracketleft'))
liga('#(')(lambda g: _hash_join(g, 'parenleft'))


@liga('#_')
def hash_underscore(g):
    """`#_`: the left stem of `#` runs down at its full weight into the
    underscore, which starts under it; the corner they make takes the
    corner rule."""
    p = g.p
    hs, bars, stems, ink = _hash(p)
    us = _sub('underscore', p)
    xh, xu = _at(g, hs, 0), _at(g, us, 1)
    g.add_glyph(hs, xh, 0.0)
    g.add_glyph(us, xu, 0.0)
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
