"""Miscellaneous technical symbols (U+2300-23FF): keys, brackets' pieces,
media controls and the watch's own pictographs.

* **Keys** (⌘ ⌥ ⌃ ⎋ ⌫ ⌦ ⏏, with ⇧ and ⇪ among the arrows) share the
  cap height and the arrows' heads.
* **Bracket pieces** (⎛-⎮, ⌠ ⌡) run from the line's descent to its ascent,
  so they join when stacked line on line.
* **Media controls** (⏩-⏺) are solid shapes, the same height, centred on
  the axis: triangles whose sides run at 2:1 (as wide as they are tall,
  near an equilateral's proportions), a square, an octagon, bars; their
  corners take the corner rule like any stroke's.
* **Clocks** (⌚ ⏰ ⏱ ⏲ ⌛ ⏳) are drawn in the octagonal bowl: a regular
  octagon's face, hands at the axes, the watch a chamfered case on its
  straps. Their parts are a tight stack inside the face, so they lighten
  toward Black as stacked arrows do, and the face grows so its white stays
  open around the hands.
"""
from __future__ import annotations

from shapely.geometry import Polygon

from ..draw import B, REGISTRY, _lightened, glyph
from ..params import SQRT2
from .arrows import chev, kb_of, reach, stack_k, Ctx, Turn
from .figures import beak_depth
from .letterframe import STEEP, growing_width, letter_width
from .operators import OPW, cdot, eq_gap, int_span, integral, kd, u
from .punct import _ring, axis


def _mono(width):
    return lambda p: min(width(p), p.fig_w) if p.mono else width(p)


def tech(name, char, width, sides=1.0, solid=False, kind=None):
    return glyph(name, char, _mono(width), kind=kind or ('punct', sides), solid=solid)


def lighten(g):
    """A compound drawing's strokes: lighter toward Black (arrows.stack_k)."""
    k = stack_k(g.p)
    if k != 1.0:
        g.p = _lightened(g.p, k)


def line_top(p):
    """The line's ascent and descent (font.Metrics), in this drawing's units,
    and an edge break past them: bracket pieces span them so they join line
    on line, the corner rule's cuts falling in the overlap."""
    from ..font import Metrics
    m = Metrics()
    return m.asc * p.m / 60.0 + p.c, m.desc * p.m / 60.0 - p.c


# --- Diameter, house, keys ---------------------------------------------------------

@tech(u(0x2300), '⌀', lambda p: 0.6 * p.cap + p.sv)
def diameter(g):
    """A small regular octagon on the axis, a 45-degree stroke through its
    corners reaching a module past them."""
    p = g.p
    a = axis(p)
    W2 = g.W / 2
    r = min(0.3 * p.cap, W2 - p.sv / 2, (W2 - p.sv / 2 - 1.0 * p.m - p.sd / 2) / 0.707)
    cx = g.W / 2
    _ring(g, cx - r, a - r, cx + r, a + r, leg=0.586 * r)
    t = 0.707 * r + p.sv / 2 + 1.0 * p.m
    g.stroke((cx - t, a - t), (cx + t, a + t), start='h', end='h')


@tech('house', '⌂', letter_width(9, 2))
def house(g):
    """Walls, a floor and a 45-degree gable."""
    p = g.p
    W = g.W
    xl, xr = p.sv / 2, W - p.sv / 2
    yb = g.sh / 2
    k = kd(p)
    apex = 0.8 * p.cap - k
    eave = apex - (W / 2 - xl)
    g.stroke((xl, yb), (xr, yb), (xr, eave), (W / 2, apex), (xl, eave), closed=True)


def keycap_chevron(g, yc, up=True, x0=None, x1=None):
    """The control key's chevron: the arrows' head, its barbs cut level."""
    p = g.p
    x0 = 0.0 if x0 is None else x0
    x1 = g.W if x1 is None else x1
    h = (x1 - x0) / 2
    s = 1 if up else -1
    g.stroke((x0, yc - s * h / 2), ((x0 + x1) / 2, yc + s * h / 2), (x1, yc - s * h / 2), start='h', end='h')
    return h + 2 * kd(p)


def _chev_w(p):
    return OPW(p)


@tech(u(0x2303), '⌃', _chev_w)
def upchevron(g):
    keycap_chevron(g, axis(g.p) + 0.25 * g.p.cap)


@tech(u(0x2304), '⌄', _chev_w)
def downchevron(g):
    keycap_chevron(g, axis(g.p) - 0.0 * g.p.cap, up=False)


def _projective(g, n):
    """⌃ under n bars, the equal sign's white apart, the stack centred a
    little above the axis."""
    lighten(g)
    p = g.p
    gap = eq_gap(g)
    hc = g.W / 2 + 2 * kd(p)                                 # the chevron's height
    total = n * g.sh + n * gap + hc
    top = axis(p) + 0.1 * p.cap + total / 2
    y = top - g.sh / 2
    for i in range(n):
        g.stroke((0, y), (g.W, y))
        y -= g.sh + gap
    tip = y + g.sh / 2                                       # the chevron's ink top
    keycap_chevron(g, tip - kd(p) - g.W / 4)


@tech(u(0x2305), '⌅', _chev_w)
def projective(g):
    _projective(g, 1)


@tech(u(0x2306), '⌆', _chev_w)
def perspective(g):
    _projective(g, 2)


@tech(u(0x2307), '⌇', lambda p: 2 * p.sv + 1.5 * p.m)
def wavyline(g):
    """A wave stood on end, the brackets' height: two periods of the tilde's
    step."""
    p = g.p
    d = g.W - p.sv
    lo, hi, mid = p.sv / 2, g.W - p.sv / 2, g.W / 2
    bot, top = -p.desc + 0.5 * p.m, p.cap + 0.5 * p.m
    n = 2
    f = max(((top - bot) - 2 * n * d) / (2 * n), 0.5 * p.sv)
    y = bot
    pts = [(mid, y)]
    y += d / 2
    pts.append((hi, y))
    for i in range(n):
        y += f
        pts.append((hi, y))
        y += d
        pts.append((lo, y))
        y += f
        pts.append((lo, y))
        if i < n - 1:
            y += d
            pts.append((hi, y))
    y += d / 2
    pts.append((mid, y))
    g.stroke(*pts, start='h', end='h')


def _ceil_floor(g, top, mirror):
    from .punct import _bracket
    p = g.p
    W = g.W
    bot_, top_ = -p.desc + 0.5 * p.m, p.cap + 0.5 * p.m
    y = top_ - g.sh / 2 if top else bot_ + g.sh / 2
    yo = bot_ if top else top_
    pts = [(W, y), (p.sv / 2, y), (p.sv / 2, yo)]
    if mirror:
        pts = [(W - x, yy) for x, yy in pts]
    g.stroke(*pts)


for cp, (top, mirror) in {0x2308: (True, False), 0x2309: (True, True), 0x230A: (False, False),
                          0x230B: (False, True)}.items():
    tech(u(cp), chr(cp), letter_width(4, 1))(lambda g, top=top, mirror=mirror: _ceil_floor(g, top, mirror))


@tech('revlogicalnot', '⌐', OPW)
def revlogicalnot(g):
    p = g.p
    a = axis(p)
    g.stroke((g.W, a), (p.sv / 2, a), (p.sv / 2, a - 2.5 * p.m))


@tech(u(0x2319), '⌙', OPW)
def turnednot(g):
    p = g.p
    a = axis(p) - 2.5 * p.m
    g.stroke((p.sv / 2, a + 2.5 * p.m), (p.sv / 2, a), (g.W, a))


@tech(u(0x2311), '⌑', lambda p: 0.55 * p.cap + 2.5 * p.sv)
def squarelozenge(g):
    """A square whose sides are notched in at 45 degrees: a cushion."""
    lighten(g)
    p = g.p
    a = axis(p)
    r = (g.W - p.sv) / 2
    n = 0.3 * r
    c = g.W / 2
    pts = []
    for (x0, y0), (x1, y1), (nx, ny) in [((-r, r), (r, r), (0, -1)), ((r, r), (r, -r), (-1, 0)),
                                         ((r, -r), (-r, -r), (0, 1)), ((-r, -r), (-r, r), (1, 0))]:
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        dx, dy = (x1 - x0) / (2 * r), (y1 - y0) / (2 * r)
        pts += [(x0, y0), (mx - dx * n, my - dy * n), (mx + nx * n, my + ny * n), (mx + dx * n, my + dy * n)]
    g.stroke(*[(c + x, a + y) for x, y in pts], closed=True)


@tech(u(0x2312), '⌒', OPW)
def arc(g):
    """An arch: half a flat octagon, open below."""
    p = g.p
    a = axis(p)
    h = max(0.3 * g.W, g.sh + 0.75 * p.sv)                  # its bay three quarters of a stem deep
    leg = min(p.leg + 0.5 * p.m, 0.8 * h)
    xl, xr = p.sv / 2, g.W - p.sv / 2
    g.stroke((xl, a - h / 2), B(xl, a + h / 2, leg), B(xr, a + h / 2, leg), (xr, a - h / 2))


def _cmd_s(p):
    """⌘'s loop and square side (centrelines; p its lightened strokes): a
    third of its body, the counters at least seven tenths of a stem."""
    return max((0.95 * p.cap - p.sv) / 3, 1.7 * p.sv, p.sv + p.m)


@tech(u(0x2318), '⌘', lambda p: 3 * _cmd_s(_light(p)) + _light(p).sv)
def placeofinterest(g):
    """The command key: a square with a loop at each corner, the loops'
    outer corners turned as bowls."""
    lighten(g)
    p = g.p
    s = min(_cmd_s(p), (g.W - p.sv) / 3)
    a = axis(p)
    c = g.W / 2
    leg = min(p.leg + 0.5 * p.m, 0.45 * s)
    for sx in (-1, 1):
        for sy in (-1, 1):
            # the loop's corner toward the centre is the square's: plain
            x_in, y_in = c + sx * s / 2, a + sy * s / 2
            x_out, y_out = c + sx * 1.5 * s, a + sy * 1.5 * s
            pts = [(x_in, y_in), B(x_out, y_in, leg), B(x_out, y_out, leg), B(x_in, y_out, leg)]
            g.stroke(*pts, closed=True)
    g.stroke((c - s / 2, a - s / 2), (c + s / 2, a - s / 2), (c + s / 2, a + s / 2), (c - s / 2, a + s / 2),
             closed=True)


@tech(u(0x2325), '⌥', letter_width(11, 1))
def option(g):
    """The option key: a bar, a 2:1 run down to a lower bar, and a bar apart
    at the top right."""
    p = g.p
    a = axis(p)
    h = 0.3 * p.cap
    W = g.W
    w = p.ss / STEEP[1]
    yt, yb = a + h, a - h
    x1 = 0.22 * W
    x2 = x1 + (yt - yb) / 2
    g.stroke((0, yt), (x1, yt), (x2, yb), (W, yb))
    gap = max(0.8 * p.sv, 1.25 * p.m)
    x3 = x1 + w / 2 + gap + g.sh / 2                         # clear of the 2:1 run by a stem's white
    g.stroke((x3, yt), (W, yt))


def _erase(g, right):
    """⌦ (⌫): a key pointing right (left), an x inside."""
    p = g.p
    a = axis(p)
    W = g.W
    k = kd(p)
    h = min(_erase_h(p), (W - k - p.sv / 2) / 2.2)           # half height, centreline (a narrow cell: smaller)
    x_tip = W - k
    x_back = x_tip - h
    x0 = p.sv / 2
    pts = [(x0, a - h), (x_back, a - h), (x_tip, a), (x_back, a + h), (x0, a + h)]
    if not right:
        pts = [(W - x, y) for x, y in pts]
    g.stroke(*pts, closed=True)
    # the x: in the square part, clear of the walls by half a stem
    gap = max(0.5 * p.sv, 0.75 * p.m)
    e = p.sd / (2 * SQRT2)                                   # a diagonal's flat end reaches this far past it
    t = min(h - g.sh / 2 - gap - e, (x_back - x0) / 2 - p.sv / 2 - gap - e)
    cx = (x0 + x_back) / 2
    if not right:
        cx = W - cx
    xw = max(0.8 * p.sd, 1.12 * p.floor)                     # the x a little lighter, a mark inside the key
    g.stroke((cx - t, a - t, xw), (cx + t, a + t), start='flat', end='flat')
    g.stroke((cx - t, a + t, xw), (cx + t, a - t), start='flat', end='flat')


def _erase_h(p):
    """The erase keys' half height: a third of the cap height, or room for
    an x a stem across inside, half a stem of white about it."""
    return max(0.33 * p.cap, p.sh / 2 + max(0.5 * p.sv, 0.75 * p.m) + p.sd / (2 * SQRT2) + p.sv)


def _erase_w(p):
    q = _light(p)
    return 3.2 * _erase_h(q) + q.sv


@tech(u(0x2326), '⌦', _erase_w)
def eraseright(g):
    lighten(g)
    _erase(g, True)


@tech(u(0x232B), '⌫', _erase_w)
def eraseleft(g):
    lighten(g)
    _erase(g, False)


@tech(u(0x2327), '⌧', lambda p: max(0.66 * p.cap, 3.8 * _light(p).sv) + _light(p).sv)
def xinbox(g):
    """A square with a lighter x from corner to corner, the square growing
    with the stroke so its four counters stay open."""
    lighten(g)
    p = g.p
    a = axis(p)
    r = (g.W - p.sv) / 2
    c = g.W / 2
    xw = max(0.75 * p.sd, 1.12 * p.floor)
    g.stroke((c - r, a - r), (c + r, a - r), (c + r, a + r), (c - r, a + r), closed=True)
    g.stroke((c - r, a - r, xw), (c + r, a + r))
    g.stroke((c - r, a + r, xw), (c + r, a - r))


KEYS = 5


def _kbd_w(p):
    """⌨'s body: five keys, half a stem or more of white between them."""
    q = _light(p)
    s = max(q.dot() * 0.8, q.sv)
    gap = max(0.6 * s, 0.75 * q.m)
    return max(letter_width(14, 2)(p), KEYS * s + (KEYS + 1) * gap + 2 * q.sv)


@tech(u(0x2328), '⌨', _kbd_w)
def keyboard(g):
    """A frame with two rows of keys and a space bar."""
    lighten(g)
    p = g.p
    a = axis(p)
    W = g.W
    s = max(p.dot() * 0.8, p.sv)
    gap = max(0.6 * s, 0.75 * p.m)
    # a narrow cell: smaller keys (the frame keeps its stroke)
    k = min(1.0, (W - 2 * p.sv) / (KEYS * s + (KEYS + 1) * gap))
    s, gap = max(k * s, p.floor), k * gap
    rowh = s
    H = 3 * rowh + 4 * gap + g.sh                          # frame height, centreline
    x0, x1 = p.sv / 2, W - p.sv / 2
    y0, y1 = a - H / 2, a + H / 2
    leg = min(p.leg, 0.25 * H)
    g.stroke(B(x0, y0, leg), B(x1, y0, leg), B(x1, y1, leg), B(x0, y1, leg), closed=True)
    inner0, inner1 = x0 + p.sv / 2 + gap, x1 - p.sv / 2 - gap
    n = KEYS                                                # the same at every weight
    step = (inner1 - inner0 - s) / (n - 1)
    ytop = y1 - g.sh / 2 - gap - s / 2
    for row in range(2):
        y = ytop - row * (s + gap)
        for i in range(n):
            cdot(g, inner0 + s / 2 + i * step, y, s)
    yb = ytop - 2 * (s + gap)
    g.stroke((inner0 + step, yb, s), (inner1 - step, yb))


def _benzene_w(p):
    """⌬'s body: three quarters of the cap height, or room for its ring
    (its counter nine tenths of a stem) with half a stem of white about it."""
    q = _light(p)
    return max(0.75 * q.cap, 2 * 2.6 * q.sv) + q.sv


@tech(u(0x232C), '⌬', _benzene_w)
def benzene(g):
    """A hexagon whose slopes run at 2:1, a ring inside it."""
    lighten(g)
    p = g.p
    a = axis(p)
    W = g.W
    w = (W - p.sv) / 2                                      # half width, centreline
    c = W / 2
    hh = w                                                  # a 2:1 slope from the point to the top's end
    g.stroke((c - w, a), (c - w / 2, a + hh), (c + w / 2, a + hh), (c + w, a), (c + w / 2, a - hh),
             (c - w / 2, a - hh), closed=True)
    # the ring: clear of the hexagon's top and of its 2:1 sides (where its
    # upright side ends) by half a stem and more, which the italic's curves need
    gap = max(0.5 * p.sv, 0.75 * p.m) + 0.25 * p.sv
    wss = p.ss / STEEP[1]
    t = max(0.75 * p.sv, 1.12 * p.floor)                    # a lighter ring, as a small one is
    r = min(max(0.45 * w, 0.9 * p.sv), w - g.sh / 2 - gap - t / 2,
            (w - wss / 2 - t / 2 - gap) / 1.207)
    _ring(g, c - r, a - r, c + r, a + r, w=t, leg=0.586 * r)


@tech(u(0x238B), '⎋', lambda p: 0.85 * p.cap + p.sv)
def escape(g):
    """The escape key: an octagon broken at its upper left, an arrow running
    out of the break from its centre."""
    lighten(g)
    p = g.p
    a = axis(p)
    W = g.W
    r = (W - p.sv) / 2
    c = W / 2
    leg = 0.586 * r
    ctx = Ctx(p, g.sh, Turn(0))
    h = reach(ctx, design=False)
    L = h * SQRT2
    t = r - leg / 2 + 0.25 * leg                             # the tip, just past the chamfer's line
    tip = (c - t, a + t)
    # the ring, open across its upper left chamfer, clear of the head's barbs
    white = max(0.75 * p.sv, p.m)
    y_end = min(a + r - leg - 0.6 * leg, tip[1] - L - p.sv / 2 - white)
    x_end = max(c - r + leg + 0.6 * leg, tip[0] + L + p.sv / 2 + white)
    g.stroke((c - r, y_end), B(c - r, a - r, leg), B(c + r, a - r, leg), B(c + r, a + r, leg), (x_end, a + r))
    g.stroke((c + 0.15 * r, a - 0.15 * r), (tip[0] + 0.01, tip[1] - 0.01))
    g.stroke((tip[0] + L, tip[1]), tip, (tip[0], tip[1] - L))


# --- Integral and bracket pieces -------------------------------------------------------

def _int_piece(g, top_hook):
    p = g.p
    asc, desc = line_top(p)
    reach_ = 2.5 * p.m + p.sv / 2
    x = g.W / 2
    d = beak_depth(p)
    if top_hook:
        top = p.cap + 0.5 * p.m + 1.0 * p.m
        yt = top - g.sh / 2
        g.stroke((x + reach_, top - d), B(x + reach_, yt), B(x, yt), (x, desc))
    else:
        bot = -p.desc
        yb = bot + g.sh / 2
        g.stroke((x, asc), B(x, yb), B(x - reach_, yb), (x - reach_, bot + d))


def _int_w(p):
    return 2 * (2.5 * p.m + p.sv / 2) + p.sv


@tech('integraltp', '⌠', _int_w)
def integraltp(g):
    _int_piece(g, True)


@tech('integralbt', '⌡', _int_w)
def integralbt(g):
    _int_piece(g, False)


@tech(u(0x23AE), '⎮', _int_w)
def integralex(g):
    asc, desc = line_top(g.p)
    g.stroke((g.W / 2, desc), (g.W / 2, asc))


def _paren_piece(g, part, mirror):
    """Parenthesis pieces: the paren's 45-degree turn into its stem."""
    p = g.p
    W = g.W
    asc, desc = line_top(p)
    xs = p.sv / 2
    reach_ = W - xs
    top, bot = p.cap + 0.5 * p.m, -p.desc + 0.5 * p.m
    T = (lambda x, y: (W - x, y)) if mirror else (lambda x, y: (x, y))
    if part == 'upper':
        g.stroke(T(xs + reach_, top), T(xs, top - reach_), T(xs, desc), start='h', end='h')
    elif part == 'lower':
        g.stroke(T(xs, asc), T(xs, bot + reach_), T(xs + reach_, bot), start='h', end='h')
    else:
        g.stroke(T(xs, desc), T(xs, asc))
    g.clip = None


def _bracket_piece(g, part, mirror):
    p = g.p
    W = g.W
    asc, desc = line_top(p)
    top, bot = p.cap + 0.5 * p.m, -p.desc + 0.5 * p.m
    T = (lambda x, y: (W - x, y)) if mirror else (lambda x, y: (x, y))
    yt, yb = top - g.sh / 2, bot + g.sh / 2
    if part == 'upper':
        g.stroke(T(W, yt), T(p.sv / 2, yt), T(p.sv / 2, desc))
    elif part == 'lower':
        g.stroke(T(p.sv / 2, asc), T(p.sv / 2, yb), T(W, yb))
    else:
        g.stroke(T(p.sv / 2, desc), T(p.sv / 2, asc))


def _brace_piece(g, part, mirror):
    p = g.p
    W = g.W
    asc, desc = line_top(p)
    top, bot = p.cap + 0.5 * p.m, -p.desc + 0.5 * p.m
    xs = W - p.sv / 2 - p.sv                                # the brace's spine
    reach_ = max(xs - p.sv / 2, p.sd + 0.5 * p.sv)          # never too short for its stroke
    xp = xs - reach_
    mid = (asc + desc) / 2
    T = (lambda x, y: (W - x, y)) if mirror else (lambda x, y: (x, y))
    if part == 'upper':
        g.stroke(T(W, top - g.sh / 2), B(*T(xs, top - g.sh / 2)), T(xs, desc))
    elif part == 'lower':
        g.stroke(T(xs, asc), B(*T(xs, bot + g.sh / 2)), T(W, bot + g.sh / 2))
    elif part == 'middle':
        g.stroke(T(xs, asc), T(xs, mid + reach_), T(xp, mid), T(xs, mid - reach_), T(xs, desc))
    else:
        g.stroke(T(xs, desc), T(xs, asc))


PIECES = [
    (0x239B, _paren_piece, 'upper', False, 4), (0x239C, _paren_piece, 'ext', False, 4),
    (0x239D, _paren_piece, 'lower', False, 4), (0x239E, _paren_piece, 'upper', True, 4),
    (0x239F, _paren_piece, 'ext', True, 4), (0x23A0, _paren_piece, 'lower', True, 4),
    (0x23A1, _bracket_piece, 'upper', False, 4), (0x23A2, _bracket_piece, 'ext', False, 4),
    (0x23A3, _bracket_piece, 'lower', False, 4), (0x23A4, _bracket_piece, 'upper', True, 4),
    (0x23A5, _bracket_piece, 'ext', True, 4), (0x23A6, _bracket_piece, 'lower', True, 4),
    (0x23A7, _brace_piece, 'upper', False, 6), (0x23A8, _brace_piece, 'middle', False, 6),
    (0x23A9, _brace_piece, 'lower', False, 6), (0x23AA, _brace_piece, 'ext', False, 6),
    (0x23AB, _brace_piece, 'upper', True, 6), (0x23AC, _brace_piece, 'middle', True, 6),
    (0x23AD, _brace_piece, 'lower', True, 6),
]
for cp, fn, part, mirror, wm in PIECES:
    tech(u(cp), chr(cp), letter_width(wm, 1))(lambda g, fn=fn, part=part, mirror=mirror: fn(g, part, mirror))


# --- Media controls ---------------------------------------------------------------------

def media_h(p):
    """Half the media controls' height: three tenths of the cap height,
    growing a little with the stroke so they keep the weight's colour."""
    return 0.3 * p.cap + 0.5 * max(0.0, p.sv - 1.5 * p.m)


def solid(g, pts):
    g.extra.append(Polygon(pts))


def bar_w(p):
    """A media bar's width: a third of the controls' half height, or a stem."""
    return max(0.33 * media_h(p), p.sv)


def media_gap(p):
    return max(0.6 * bar_w(p), 0.8 * p.sv, 1.0 * p.m)


class M:
    """A media control's measures, scaled down to fit a narrow cell."""

    def __init__(self, g, width):
        p = g.p
        k = min(1.0, g.W / width(p))
        self.h = k * media_h(p)
        self.bw = k * bar_w(p)
        self.gap = k * media_gap(p)
        self.a = axis(p)


def tri(g, x_back, yc, h, d=1):
    """A solid triangle pointing along +x (d = 1) or -x from its back at
    x_back, its sides at 2:1: as wide as it is tall (2h)."""
    solid(g, [(x_back, yc - h), (x_back + d * 2 * h, yc), (x_back, yc + h)])


def tri_v(g, y_base, xc, h, d=1):
    """The same pointing up (d = 1) or down from its base at y_base."""
    solid(g, [(xc - h, y_base), (xc, y_base + d * 2 * h), (xc + h, y_base)])


def ubar(g, x, yc, h, w):
    """A solid upright bar, centred at (x, yc), 2h tall, w wide."""
    g.stroke((x, yc - h, w), (x, yc + h))


def media(name, char, width):
    def deco(fn):
        tech(name, char, width, solid=True)(lambda g: fn(g, M(g, width)))
        return fn
    return deco


W_TRI = lambda p: 2 * media_h(p)
W_FF = lambda p: 3 * media_h(p)
W_TRACK = lambda p: 3 * media_h(p) + bar_w(p)
W_PP = lambda p: 0.8 * (2 * media_h(p) + 2 * bar_w(p) + media_gap(p)) + media_gap(p)
W_PAUSE = lambda p: 2 * bar_w(p) + 1.25 * media_gap(p)


@media(u(0x23F5), '⏵', W_TRI)
def play(g, m):
    tri(g, 0, m.a, m.h)


@media(u(0x23F4), '⏴', W_TRI)
def playleft(g, m):
    tri(g, g.W, m.a, m.h, d=-1)


@media(u(0x23F6), '⏶', W_TRI)
def playup(g, m):
    tri_v(g, m.a - m.h, g.W / 2, m.h)


@media(u(0x23F7), '⏷', W_TRI)
def playdown(g, m):
    tri_v(g, m.a + m.h, g.W / 2, m.h, d=-1)


@media(u(0x23E9), '⏩', W_FF)
def fastforward(g, m):
    """Two triangles, the second's back at the first's middle."""
    tri(g, 0, m.a, m.h)
    tri(g, m.h, m.a, m.h)


@media(u(0x23EA), '⏪', W_FF)
def rewind(g, m):
    tri(g, g.W, m.a, m.h, d=-1)
    tri(g, g.W - m.h, m.a, m.h, d=-1)


@media(u(0x23EB), '⏫', W_TRI)
def fastup(g, m):
    tri_v(g, m.a - 1.5 * m.h, g.W / 2, m.h)
    tri_v(g, m.a - 0.5 * m.h, g.W / 2, m.h)


@media(u(0x23EC), '⏬', W_TRI)
def fastdown(g, m):
    tri_v(g, m.a + 1.5 * m.h, g.W / 2, m.h, d=-1)
    tri_v(g, m.a + 0.5 * m.h, g.W / 2, m.h, d=-1)


@media(u(0x23ED), '⏭', W_TRACK)
def nexttrack(g, m):
    tri(g, 0, m.a, m.h)
    tri(g, m.h, m.a, m.h)
    ubar(g, g.W - m.bw / 2, m.a, m.h, m.bw)


@media(u(0x23EE), '⏮', W_TRACK)
def prevtrack(g, m):
    tri(g, g.W, m.a, m.h, d=-1)
    tri(g, g.W - m.h, m.a, m.h, d=-1)
    ubar(g, m.bw / 2, m.a, m.h, m.bw)


@media(u(0x23EF), '⏯', W_PP)
def playpause(g, m):
    """Play and pause side by side, each four fifths of its size."""
    h, bw, gap = 0.8 * m.h, 0.8 * m.bw, 0.8 * m.gap
    tri(g, 0, m.a, h)
    x = g.W - bw / 2
    ubar(g, x, m.a, h, bw)
    ubar(g, x - bw - gap, m.a, h, bw)


@media(u(0x23F8), '⏸', W_PAUSE)
def pause(g, m):
    ubar(g, m.bw / 2, m.a, m.h, m.bw)
    ubar(g, g.W - m.bw / 2, m.a, m.h, m.bw)


@media(u(0x23F9), '⏹', lambda p: 1.8 * media_h(p))
def stop(g, m):
    h = 0.9 * m.h
    g.stroke((g.W / 2, m.a - h, 2 * h), (g.W / 2, m.a + h))


@media(u(0x23FA), '⏺', W_TRI)
def record(g, m):
    """A solid regular octagon."""
    r, a, c = m.h, m.a, g.W / 2
    l = 0.414 * r
    solid(g, [(c - l, a - r), (c + l, a - r), (c + r, a - l), (c + r, a + l), (c + l, a + r), (c - l, a + r),
              (c - r, a + l), (c - r, a - l)])


@media(u(0x23CF), '⏏', W_TRI)
def eject(g, m):
    """A solid triangle, its sides at 45 degrees, over a bar."""
    W = g.W
    h = W / 2
    total = h + m.gap + m.bw
    y0 = m.a - total / 2
    g.stroke((W / 2, y0, W), (W / 2, y0 + m.bw))
    yb = y0 + m.bw + m.gap
    solid(g, [(0, yb), (W, yb), (W / 2, yb + h)])


# --- Clocks -------------------------------------------------------------------------------

def face(g, c, a, r):
    """A clock's face: a regular octagon, centreline half-size r."""
    _ring(g, c - r, a - r, c + r, a + r, leg=0.586 * r)


def face_r(p, cap_share=0.38):
    """A face's centreline half-size: a share of the cap height, never so
    small that the white about its hands closes (two stems from centre to
    ring, and white either side)."""
    return max(cap_share * p.cap, 1.5 * p.sv + 2.0 * max(0.6 * p.sv, p.m))


HAND = 0.8   # hands are lighter than the face, as a watch's are


def hand(g, c, a, d, L):
    """A hand from the centre along d (an axis or a diagonal), L long."""
    n = (d[0] ** 2 + d[1] ** 2) ** 0.5
    th = _thickness_of(g, d)
    g.stroke((c, a, max(HAND * th, 1.12 * g.p.floor)), (c + d[0] / n * L, a + d[1] / n * L))


def _thickness_of(g, d):
    from ..draw import _thickness
    return _thickness(g.p, g.sh)(d)


def hands(g, c, a, r, minute=(0, 1), hour=(1, 0), long_=0.8, short=0.55):
    """A minute hand (long) and an hour hand (short) from the centre; they
    meet there in a square corner."""
    inner = r - g.p.sv / 2
    for d, k in ((minute, long_), (hour, short)):
        if d is not None:
            hand(g, c, a, d, k * inner)


def clock_w(share=0.38, extra=0.0):
    return lambda p: 2 * face_r(_light(p), share) + _light(p).sv + extra * p.m


def _light(p):
    k = stack_k(p)
    return _lightened(p, k) if k != 1.0 else p


def _crown(p):
    """The watch's crown: how far it stands out from the case."""
    return 0.5 * p.sv + 0.75 * p.m


@tech(u(0x231A), '⌚', lambda p: 2 * face_r(_light(p), 0.3) + _light(p).sv + _crown(_light(p)), solid=True)
def watch(g):
    """The watch: a chamfered case, a little taller than wide, on its
    straps, a crown at the right, hands at twelve and three."""
    lighten(g)
    p = g.p
    a = axis(p)
    rx = (g.W - p.sv - _crown(p)) / 2
    ry = 1.12 * rx
    c = rx + p.sv / 2
    leg = 0.45 * rx
    g.stroke(B(c - rx, a - ry, leg), B(c + rx, a - ry, leg), B(c + rx, a + ry, leg), B(c - rx, a + ry, leg),
             closed=True)
    # straps: solid, narrower than the case, out to the brackets' height
    sw = 1.1 * rx
    bot, top = -p.desc + 0.5 * p.m, p.cap + 0.5 * p.m
    top, bot = max(top, a + ry + p.sv), min(bot, a - ry - p.sv)
    g.stroke((c, a + ry, sw), (c, top))
    g.stroke((c, bot, sw), (c, a - ry))
    g.stroke((c + rx, a), (c + rx + p.sv / 2 + _crown(p), a))
    hands(g, c, a, min(rx, ry), minute=(0, 1), hour=(1, 0))


def _alarm_reach(p):
    """How far the bells stand out past the face's half size, beyond 0.97 of it."""
    gap = max(0.75 * p.sv, 1.0 * p.m)
    bw = 1.2 * p.sd
    return (p.sd / 2 + gap + bw / 2) / SQRT2 + 0.45 * bw


def _alarm_r(p, W):
    return min(face_r(p, 0.33), (W / 2 - _alarm_reach(p)) / 0.97)


@tech(u(0x23F0), '⏰', lambda p: 2 * (0.97 * face_r(_light(p), 0.33) + _alarm_reach(_light(p))))
def alarmclock(g):
    """An octagon's face with two bells above its upper chamfers and two
    feet below its lower ones."""
    lighten(g)
    p = g.p
    a = axis(p) - 0.04 * p.cap
    gap = max(0.75 * p.sv, 1.0 * p.m)
    r = _alarm_r(p, g.W)
    c = g.W / 2
    face(g, c, a, r)
    hands(g, c, a, r)
    leg = 0.586 * r
    # bells: short 45-degree bars along the upper chamfers, a gap outside them
    for s in (-1, 1):
        mx, my = c + s * (r - leg / 2), a + (r - leg / 2)
        bw = 1.2 * p.sd
        off = (p.sd / 2 + gap + bw / 2) / SQRT2
        bx, by = mx + s * off, my + off
        L = 0.45 * leg
        g.stroke((bx - s * L, by + L, bw), (bx + s * L, by - L))
    # feet: from the lower chamfers, out at 45 degrees
    for s in (-1, 1):
        mx, my = c + s * (r - leg / 2), a - (r - leg / 2)
        L = 0.4 * leg + p.sv / 2
        g.stroke((mx, my), (mx + s * L, my - L), start='flat', end='h')


@tech(u(0x23F1), '⏱', clock_w(0.33))
def stopwatch(g):
    """An octagon's face, a crown on top (a stem and a cap) and a button at
    its upper right, one hand at twelve."""
    lighten(g)
    p = g.p
    a = axis(p) - 0.06 * p.cap
    r = (g.W - p.sv) / 2
    c = g.W / 2
    face(g, c, a, r)
    gap = max(0.5 * p.sv, 0.75 * p.m)
    top = a + r
    stem_top = top + gap + 0.5 * g.sh + p.sv * 0.5
    g.stroke((c, top), (c, stem_top))
    cw = 0.45 * r
    g.stroke((c - cw, stem_top + g.sh / 2), (c + cw, stem_top + g.sh / 2))
    leg = 0.586 * r
    mx, my = c + (r - leg / 2), a + (r - leg / 2)
    L = 0.6 * leg
    g.stroke((mx, my), (mx + L, my + L))
    hands(g, c, a, r, minute=(0, 1), hour=None, long_=0.8)


@tech(u(0x23F2), '⏲', clock_w(0.36), solid=True)
def timerclock(g):
    """An octagon's face with a mark above it and a hand turned back to
    half past ten."""
    lighten(g)
    p = g.p
    a = axis(p) - 0.05 * p.cap
    r = (g.W - p.sv) / 2
    c = g.W / 2
    face(g, c, a, r)
    gap = max(0.5 * p.sv, 0.75 * p.m)
    # the mark: a small solid triangle pointing down at twelve
    t = 0.3 * r
    y = a + r + p.sv / 2 + gap
    solid(g, [(c - t, y + t), (c + t, y + t), (c, y)])
    hand(g, c, a, (-1, 1), 0.7 * (r - p.sv / 2))


def _hg(p):
    """An hourglass's measures: (top, bottom, glass half width at the bars,
    the slope's height, the neck's half white, a 2:1 stroke's width)."""
    bot, top = -p.desc + 0.5 * p.m, p.cap + 0.5 * p.m
    sh = p.sh
    hgt = (top - bot) - sh
    w = p.ss / STEEP[1]
    neck = max(0.5 * p.sv, 0.5 * p.m)
    nl = max(0.4 * p.sv, 0.5 * p.m)                          # half the neck's upright
    dy = hgt / 2 - nl
    half_w = neck + w / 2 + dy / 2
    return top, bot, half_w, dy, neck, w


def _hg_w(p):
    k = stack_k(p)
    pk = _lightened(p, k) if k != 1.0 else p
    return 2 * (_hg(pk)[2] + pk.m) + pk.sv * 0


def _hourglass(g, sand):
    """An hourglass: two bars, and glass whose sides run at 2:1 into an
    upright neck; with sand, a heap on the lower bar and a band left at the
    foot of the upper bulb, each following the glass a half stem inside it."""
    lighten(g)
    p = g.p
    W = g.W
    top, bot, half_w, dy, neck, w = _hg(p)
    if half_w > W / 2 - p.m:                                 # a narrow cell: a steeper, shorter glass
        half_w = W / 2 - p.m
        dy = min(dy, 2 * (half_w - neck - w / 2))
    yt, yb = top - g.sh / 2, bot + g.sh / 2
    g.stroke((0, yt), (W, yt))
    g.stroke((0, yb), (W, yb))
    for s_ in (-1, 1):
        x0 = W / 2 + s_ * half_w
        xn = W / 2 + s_ * (neck + w / 2)
        g.stroke((x0, yt), (xn, yb + (yt - yb) - dy), (xn, yb + dy), (x0, yb), start='h', end='h')
    if not sand:
        return
    gap = max(0.5 * p.sv, 0.75 * p.m)
    gh = gap / STEEP[1]                                      # that white, measured across a 2:1 wall
    yn = yt - dy                                             # the upper bulb's foot
    lower = lambda y: W / 2 - half_w + (y - yb) / 2 + w / 2 + gh
    upper = lambda y: W / 2 - (neck + w / 2) - (y - yn) / 2 + w / 2 + gh
    base = yb + g.sh / 2
    hh = min(0.4 * dy, (W / 2 - lower(base)) * 2 - p.sv)
    solid(g, [(lower(base), base), (W - lower(base), base), (W - lower(base + hh), base + hh),
              (lower(base + hh), base + hh)])
    y1 = yn + 2 * (gh - neck + p.sv / 4)
    y2 = max(min(y1 + 0.35 * dy, yt - g.sh / 2 - gap), y1 + 0.4 * p.sv)
    solid(g, [(upper(y1), y1), (W - upper(y1), y1), (W - upper(y2), y2), (upper(y2), y2)])


@tech(u(0x231B), '⌛', _hg_w)
def hourglass(g):
    _hourglass(g, False)


@tech(u(0x23F3), '⏳', _hg_w, solid=True)
def hourglasssand(g):
    _hourglass(g, True)


# --- Corners -------------------------------------------------------------------------------

def _corner(g, top, left):
    """Quine corners: an L of two three-module arms at the cap height or
    the baseline."""
    p = g.p
    W = g.W
    arm = W
    if top:
        y = p.cap - g.sh / 2
        yo = y - arm
    else:
        y = g.sh / 2
        yo = y + arm
    x = p.sv / 2 if left else W - p.sv / 2
    xo = W if left else 0
    g.stroke((xo, y), (x, y), (x, yo))


for cp, (top, left) in {0x231C: (True, True), 0x231D: (True, False), 0x231E: (False, True),
                        0x231F: (False, False)}.items():
    tech(u(cp), chr(cp), lambda p: 3 * p.m + p.sv)(lambda g, top=top, left=left: _corner(g, top, left))
