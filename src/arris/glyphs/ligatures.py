"""Arris Mono's programming ligatures.

Code is set in a fixed grid, so a ligature here never changes the grid: a
sequence of N characters becomes N - 1 empty spacers (LIG) and one glyph
one cell wide that draws back across the N cells (the scheme Fira Code
made standard). The substitution is contextual (`calt`, on by default and
easy to turn off in editors), longest sequences first, with guards so a
ligature never forms inside a longer run of the same characters (`--->`,
`<=<`, `====`).

The drawings are Arris: operators on the math axis, the arrowheads of
`symbols.arrow_head`, the bars of `=`, chevrons at 45 degrees, dots of
`Params.dot`. A ligature reads as the characters it replaces, only joined:
`->` is a hyphen grown into an arrow, `==` one long double bar, `!=` the
double bar struck through, `:=` the colon raised to sit on the bars.
"""
from __future__ import annotations

from ..draw import REGISTRY, glyph
from ..params import SQRT2
from .punct import axis, dot
from .symbols import arrow_head

LIGATURES: list[tuple[str, tuple[str, ...]]] = []   # (glyph name, component glyph names), longest first at build


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
            glyph(name, None, _body(len(seq)), kind=('liga', len(seq)))(fn)
            LIGATURES.append((name, names))
        return fn
    return deco


@glyph('LIG', None, 'fig_w', kind=('liga', 1))
def lig_spacer(g):
    """The empty cell a ligature draws over."""


# --- Geometry shared by the drawings ---------------------------------------

def cell(g, i):
    """(left, centre, right) of the i-th cell's body, in the ligature's frame."""
    p = g.p
    left = i * p.fig_adv
    return left, left + p.fig_w / 2, left + p.fig_w


def bars_offset(g):
    """Half the distance between the bars of `=`."""
    return (g.sh + max(0.8 * g.sh, g.p.m)) / 2


def head(g, tip, sign, size=None):
    """Two barbs from the tip, pointing right (sign 1) or left (-1)."""
    x, y = tip
    L = (size or arrow_head(g.p)) / SQRT2
    for s in (1, -1):
        g.stroke((x, y), (x - sign * L, y + s * L))


def chevron(g, tip, sign, reach):
    """`<` (sign -1) or `>` (sign 1) with its tip at ``tip``."""
    x, y = tip
    g.stroke((x - sign * reach, y + reach), (x, y), (x - sign * reach, y - reach), start='v', end='v')


def reach(g):
    """The reach of `<` and `>` (from punct._chevron)."""
    p = g.p
    return p.fig_w - p.sv / 2


# --- Arrows ---------------------------------------------------------------

def _single(g, left_head=False, right_head=True, bars=1, start_bar=False, end_bar=False, double_head=False):
    p, W = g.p, g.W
    a = axis(p)
    x0, x1 = p.sv / 2, W - p.sv / 2
    off = bars_offset(g)
    L = arrow_head(p)
    if bars == 1:
        g.stroke((x0, a), (x1, a))
    else:
        # the bars stop where they meet the barbs (a barb at height off is off in from the tip)
        R = max(L / SQRT2, off + 1.5 * p.sv)
        bx0 = x0 + (off if left_head else 0.0)
        bx1 = x1 - (off if right_head else 0.0)
        for y in (a - off, a + off):
            g.stroke((bx0, y), (bx1, y))
        L = R * SQRT2
    if right_head:
        head(g, (x1, a), 1, L)
        if double_head:
            head(g, (x1 - 0.6 * L, a), 1, L)
    if left_head:
        head(g, (x0, a), -1, L)
        if double_head:
            head(g, (x0 + 0.6 * L, a), -1, L)
    h = max(L / SQRT2, off + 1.5 * p.sv) if bars > 1 else L / SQRT2
    if start_bar:
        g.stroke((x0, a - h), (x0, a + h))
    if end_bar:
        g.stroke((x1, a - h), (x1, a + h))


liga('->', '-->')(lambda g: _single(g))
liga('<-', '<--')(lambda g: _single(g, left_head=True, right_head=False))
liga('<->', '<-->')(lambda g: _single(g, left_head=True))
liga('=>', '==>')(lambda g: _single(g, bars=2))
liga('<==')(lambda g: _single(g, bars=2, left_head=True, right_head=False))
liga('<=>', '<==>')(lambda g: _single(g, bars=2, left_head=True))
liga('|->')(lambda g: _single(g, start_bar=True))
liga('<-|')(lambda g: _single(g, left_head=True, right_head=False, end_bar=True))
liga('|=>')(lambda g: _single(g, bars=2, start_bar=True))
liga('->>')(lambda g: _single(g, double_head=True))
liga('<<-')(lambda g: _single(g, left_head=True, right_head=False, double_head=True))


@liga('~>', '~~>')
def wave_arrow(g):
    """A wavy shaft (the tilde's 45-degree steps) into a head."""
    p, W = g.p, g.W
    a = axis(p)
    x0, x1 = p.sv / 2, W - p.sv / 2
    L = arrow_head(p)
    amp = max(p.m, 0.6 * p.sv)
    pts, x, up = [(x0, a)], x0, True
    end = x1 - L / SQRT2 * 0.6
    while x + 2 * amp < end:
        x += 2 * amp
        pts.append((x - amp, a + (amp if up else -amp)))
        pts.append((x, a))
        up = not up
    pts.append((x1, a))
    g.stroke(*pts)
    head(g, (x1, a), 1, L)


@liga('<~')
def wave_arrow_left(g):
    p, W = g.p, g.W
    a = axis(p)
    x0, x1 = p.sv / 2, W - p.sv / 2
    L = arrow_head(p)
    amp = max(p.m, 0.6 * p.sv)
    pts, x, up = [(x1, a)], x1, True
    end = x0 + L / SQRT2 * 0.6
    while x - 2 * amp > end:
        x -= 2 * amp
        pts.append((x + amp, a + (amp if up else -amp)))
        pts.append((x, a))
        up = not up
    pts.append((x0, a))
    g.stroke(*pts)
    head(g, (x0, a), -1, L)


# --- Equality and comparison ---------------------------------------------

def _bars(g, n, x0=None, x1=None):
    p, W = g.p, g.W
    a = axis(p)
    off = bars_offset(g)
    x0 = 0.0 if x0 is None else x0
    x1 = W if x1 is None else x1
    ys = [a - off, a + off] if n == 2 else [a - 2 * off, a, a + 2 * off]
    for y in ys:
        g.stroke((x0, y), (x1, y))
    return ys


def _strike(g, ys):
    """The 2:1 slash of `!=` across bars at heights ys."""
    p, W = g.p, g.W
    lo, hi = min(ys) - 2.2 * g.sh, max(ys) + 2.2 * g.sh
    cx = W / 2
    run = (hi - lo) / 2
    g.stroke((cx - run / 2, lo), (cx + run / 2, hi), start='h', end='h')


liga('==')(lambda g: _bars(g, 2))
liga('===')(lambda g: _bars(g, 3))


@liga('!=', '/=')
def not_equal(g):
    _strike(g, _bars(g, 2))


@liga('!==')
def not_identical(g):
    _strike(g, _bars(g, 3))


@liga('=/=')
def not_equal_long(g):
    _strike(g, _bars(g, 2))


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


# --- Colons, dots, pipes ---------------------------------------------------

@liga('::')
def double_colon(g):
    p = g.p
    s = p.dot()
    for i in (0, 1):
        _, c, _ = cell(g, i)
        x = c + (1 - 2 * i) * 0.18 * p.fig_adv              # drawn toward each other
        dot(g, x, 0)
        dot(g, x, p.xh - s)


@liga(':::')
def triple_colon(g):
    p = g.p
    s = p.dot()
    for i in (0, 1, 2):
        _, c, _ = cell(g, i)
        x = c + (1 - i) * 0.18 * p.fig_adv
        dot(g, x, 0)
        dot(g, x, p.xh - s)


@liga(':=')
def colon_equal(g):
    """The colon raised so its dots sit on the bars' axis."""
    p = g.p
    s = p.dot()
    a = axis(p)
    off = bars_offset(g)
    _, c0, r0 = cell(g, 0)
    x = c0 + 0.15 * p.fig_adv
    for y in (a - off, a + off):
        dot(g, x, y - s / 2)
    _bars(g, 2, x0=x + s / 2 + max(p.m, 0.6 * s), x1=g.W)


@liga('=:')
def equal_colon(g):
    p = g.p
    s = p.dot()
    a = axis(p)
    off = bars_offset(g)
    _, c1, _ = cell(g, 1)
    x = c1 - 0.15 * p.fig_adv
    for y in (a - off, a + off):
        dot(g, x, y - s / 2)
    _bars(g, 2, x0=0.0, x1=x - s / 2 - max(p.m, 0.6 * s))


@liga('::=')
def double_colon_equal(g):
    p = g.p
    s = p.dot()
    a = axis(p)
    off = bars_offset(g)
    xs = [cell(g, 0)[1] + 0.2 * p.fig_adv, cell(g, 1)[1] - 0.1 * p.fig_adv]
    for x in xs:
        for y in (a - off, a + off):
            dot(g, x, y - s / 2)
    _bars(g, 2, x0=xs[-1] + s / 2 + max(p.m, 0.6 * s), x1=g.W)


def _dots(g, n):
    p, W = g.p, g.W
    s = p.dot()
    gap = (W - n * s) / (n - 1) if n > 1 else 0
    gap = min(gap, 2.2 * s * 2)
    span = n * s + (n - 1) * gap
    x = (W - span) / 2 + s / 2
    for _ in range(n):
        dot(g, x, 0)
        x += s + gap


liga('..')(lambda g: _dots(g, 2))
liga('...')(lambda g: _dots(g, 3))


@liga('..<')
def range_lt(g):
    p = g.p
    s = p.dot()
    for i in (0, 1):
        dot(g, cell(g, i)[1] + (0.15 - 0.1 * i) * p.fig_adv, 0)
    _, c2, r2 = cell(g, 2)
    chevron(g, (c2 - reach(g) / 2 + p.sv / 2, axis(p)), -1, reach(g) / 2)


@liga('..=')
def range_eq(g):
    p = g.p
    for i in (0, 1):
        dot(g, cell(g, i)[1] + (0.15 - 0.1 * i) * p.fig_adv, 0)
    _bars(g, 2, x0=cell(g, 2)[0], x1=g.W)


@liga('||')
def double_bar(g):
    p = g.p
    top, bot = p.cap + 0.5 * p.m, -p.desc + 0.5 * p.m
    gap = max(1.2 * p.m, 1.2 * p.sv)
    for x in (g.W / 2 - gap / 2 - p.sv / 2, g.W / 2 + gap / 2 + p.sv / 2):
        g.stroke((x, bot), (x, top))
    g.clip = (0, bot, g.W, top)


def _pipe_tri(g, left, right):
    """`|>`, `<|`, `<|>`: a bar with chevrons joined to its ends (a
    triangle, the pipe drawn as an arrow)."""
    p, W = g.p, g.W
    a = axis(p)
    h = min(reach(g), 0.42 * p.cap)
    xb = W / 2
    g.stroke((xb, a - h), (xb, a + h))
    if right:
        g.stroke((xb, a + h), (xb + h, a), (xb, a - h))
    if left:
        g.stroke((xb, a + h), (xb - h, a), (xb, a - h))


liga('|>')(lambda g: _pipe_tri(g, False, True))
liga('<|')(lambda g: _pipe_tri(g, True, False))
liga('<|>')(lambda g: _pipe_tri(g, True, True))


# --- Plus, minus, slashes, chevrons, comments -------------------------------

@liga('--')
def double_hyphen(g):
    g.stroke((g.p.sv / 2, axis(g.p)), (g.W - g.p.sv / 2, axis(g.p)))


@liga('++')
def double_plus(g):
    p, W = g.p, g.W
    a = axis(p)
    h = p.fig_w / 2 - p.sv / 2
    g.stroke((0, a), (W, a))
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
    r = 0.75 * reach(g)
    pitch = min(p.fig_adv * 0.75, r + 1.6 * p.sv)
    span = r + (n - 1) * pitch
    x = (W - span) / 2 + (r if sign > 0 else 0)
    for _ in range(n):
        chevron(g, (x, axis(p)), sign, r)
        x += pitch


liga('>>')(lambda g: _chevrons(g, 2, 1))
liga('<<')(lambda g: _chevrons(g, 2, -1))
liga('>>>')(lambda g: _chevrons(g, 3, 1))
liga('<<<')(lambda g: _chevrons(g, 3, -1))


@liga('/*', '*/')
def comment(g):
    """The slash, and the asterisk raised to the slash's middle: the
    comment's mark reads as one sign."""
    p, W = g.p, g.W
    opening = g.name.startswith('slash')
    top, bot = p.cap + 0.5 * p.m, -p.desc + 0.5 * p.m
    run = (top - bot) / 2
    i_slash, i_star = (0, 1) if opening else (1, 0)
    _, cs, _ = cell(g, i_slash)
    g.stroke((cs - run / 2, bot), (cs + run / 2, top), start='h', end='h')
    _, ca, _ = cell(g, i_star)
    h = p.fig_w / 2 - p.sv / 2
    yc = (top + bot) / 2
    g.stroke((ca, yc - h), (ca, yc + h))
    d = h / SQRT2 * 1.1
    g.stroke((ca - d, yc - d), (ca + d, yc + d))
    g.stroke((ca - d, yc + d), (ca + d, yc - d))
    g.clip = (0, bot, W, top)


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
