"""Terminal cells: box drawing, block elements, shades, Braille, Powerline.

A terminal sets these one to a cell, rows at the font's line height, and
they must join their neighbours across every cell edge. So each is drawn in
the whole cell: the figures' advance wide (the monospaced pitch, which the
proportional cuts share for these glyphs, as terminal fonts' proportional
siblings do) and from the line's descender to its ascender (``font.Metrics``,
-250 to 950), and

* every line or block that reaches a cell edge reaches it exactly and is
  cut square there: the corner rule does not break corners on the cell's
  edges (``Glyph.butt``), so the next cell's line or block continues it
  without a notch;
* everything inside the cell is Arris: corners where lines meet are cut and
  filled by the corner rule, a rounded corner is a bowl's chamfer, dashes
  end in edge breaks, a quadrant block's exposed corner is cut like a
  pixel of the watch's figures, shades are lattices of chamfered squares;
* in the italic the cells stay upright (a slanted line would leave the cell
  below it a slant's width away); their chamfers still become curves
  (``font.place``).

Weights: a light line is the weight's own stroke (vertical sv, horizontal
sh, never under the stroke floor); heavy is twice that; a double line is two
light lines, three quarters of a light line's white between them (at least
a module), so that at Black the cell keeps white outside them.
"""
from __future__ import annotations

import math
import unicodedata

from shapely.geometry import Polygon, box

from fontTools import agl

from ..draw import B, REGISTRY, glyph
from ..font import Metrics

_MET = Metrics()
TOP, BOTTOM = float(_MET.asc), float(_MET.desc)     # the line's extent: rows touch
HEIGHT = TOP - BOTTOM
MID = (TOP + BOTTOM) / 2                              # the cell's centre line


def cell_width(p):
    """A cell is the figures' advance: the monospaced pitch."""
    return p.fig_adv


def gname(cp: int) -> str:
    """A glyph's name: its AGL name where it has one, else uniXXXX."""
    return agl.UV2AGL.get(cp, f'uni{cp:04X}' if cp <= 0xFFFF else f'u{cp:05X}')


def cell_glyph(char, solid=False):
    name = gname(ord(char))
    assert name not in REGISTRY, name
    return glyph(name, char, cell_width, kind='fig', solid=solid, cell=True)


def cell(g, clip_x=True):
    """Set the glyph up as a whole cell: ink is kept inside it (or inside
    its rows only, for lines that run on through a corner) and meets its
    edges flush. Returns (width, centre x, centre y)."""
    W = g.W
    g.clip = (0.0, BOTTOM, W, TOP) if clip_x else (-W, BOTTOM, 2 * W, TOP)
    g.butt = (('x', 0.0), ('x', W), ('y', BOTTOM), ('y', TOP))
    return W, W / 2, MID


def weights(g):
    """(vertical, horizontal) thickness of a light line."""
    p = g.p
    return max(p.sv, p.floor), max(g.sh, p.floor)


def _thick(g, style, vertical):
    lv, lh = weights(g)
    t = lv if vertical else lh
    return 2 * t if style == 'h' else t


def double_offset(g, vertical):
    """Distance from the cell's centre line to each line of a double."""
    lv, lh = weights(g)
    t = lv if vertical else lh
    gap = max(0.75 * t, g.p.m)                             # (at Black the cell keeps white outside them)
    return (gap + t) / 2


def rect(g, x0, y0, x1, y1):
    """A filled rectangle, as a stroke (a block, a dash, a shade's square)."""
    g.stroke(((x0 + x1) / 2, y0, x1 - x0), ((x0 + x1) / 2, y1))


# --- Box drawing -------------------------------------------------------------

# Arms: left, right, up, down; style 'l' light, 'h' heavy, 'd' double.
DIRS = {'LEFT': 'l', 'RIGHT': 'r', 'UP': 'u', 'DOWN': 'd', 'HORIZONTAL': 'lr', 'VERTICAL': 'ud'}
STYLES = {'LIGHT': 'l', 'SINGLE': 'l', 'HEAVY': 'h', 'DOUBLE': 'd'}


def parse_arms(name: str) -> dict:
    """A box-drawing junction's arms from its Unicode name: 'BOX DRAWINGS
    DOWN LIGHT AND RIGHT HEAVY' -> {'d': 'l', 'r': 'h'}. Groups joined by
    AND name their weight first or last; a group without one takes the
    previous group's ('LIGHT DOWN AND RIGHT')."""
    words = name.replace('BOX DRAWINGS ', '').split(' AND ')
    arms, last = {}, None
    for grp in words:
        toks = grp.split()
        style = None
        if toks[0] in STYLES:
            style = STYLES[toks.pop(0)]
        elif toks[-1] in STYLES:
            style = STYLES[toks.pop()]
        style = style or last
        for t in toks:
            for a in DIRS[t]:
                arms[a] = style
        last = style
    return arms


def _junction(g, arms):
    """Light and heavy arms: each runs from its edge to the centre and on
    past it by half the widest arm across it, so arms of any weights meet in
    a clean corner, tee or cross (and the corner rule cuts and fills it)."""
    W, cx, cy = cell(g)
    over = 2 * W                                            # past the edge; the cell clips
    across_h = max([_thick(g, arms[a], True) for a in 'ud' if a in arms] or [0.0])
    across_v = max([_thick(g, arms[a], False) for a in 'lr' if a in arms] or [0.0])
    straight_h = 'l' in arms and 'r' in arms and arms['l'] == arms['r'] and not across_h
    straight_v = 'u' in arms and 'd' in arms and arms['u'] == arms['d'] and not across_v
    if straight_h:
        g.stroke((-over, cy, _thick(g, arms['l'], False)), (W + over, cy))
    else:
        for a, sgn in (('l', -1), ('r', 1)):
            if a in arms:
                g.stroke((cx - sgn * across_h / 2, cy, _thick(g, arms[a], False)), (cx + sgn * (W + over), cy))
    if straight_v:
        g.stroke((cx, BOTTOM - over, _thick(g, arms['u'], True)), (cx, TOP + over))
    else:
        for a, sgn in (('d', -1), ('u', 1)):
            if a in arms:
                g.stroke((cx, cy - sgn * across_v / 2, _thick(g, arms[a], True)), (cx, cy + sgn * (HEIGHT + over)))


def _double(g, arms):
    """Double lines meeting double lines: every arm is two light lines, and
    the square between the four lines' crossings closes on each side no arm
    leaves from, so outer lines turn round the corner and inner lines meet
    in their own corners (the corner rule cuts and fills each)."""
    W, cx, cy = cell(g)
    lv, lh = weights(g)
    dv, dh = double_offset(g, True), double_offset(g, False)
    over = 2 * W
    for a, sgn in (('l', -1), ('r', 1)):
        if a in arms:
            for s in (-1, 1):
                g.stroke((cx + sgn * (dv - lv / 2), cy + s * dh, lh), (cx + sgn * (W + over), cy + s * dh))
    for a, sgn in (('d', -1), ('u', 1)):
        if a in arms:
            for s in (-1, 1):
                g.stroke((cx + s * dv, cy + sgn * (dh - lh / 2), lv), (cx + s * dv, cy + sgn * (HEIGHT + over)))
    # the junction square's sides where no arm leaves
    for a, sgn in (('d', -1), ('u', 1)):
        if a not in arms:
            g.stroke((cx - dv - lv / 2, cy + sgn * dh, lh), (cx + dv + lv / 2, cy + sgn * dh))
    for a, sgn in (('l', -1), ('r', 1)):
        if a not in arms:
            g.stroke((cx + sgn * dv, cy - dh - lh / 2, lv), (cx + sgn * dv, cy + dh + lh / 2))


def _mixed(g, arms):
    """A double axis met or crossed by a single one. The double's two lines
    run through if both its arms are there, else from the single line's far
    side; the single line runs through if both its arms are there, else to
    the nearer double line where the double runs through (a tee) and to the
    farther one where the double turns (a corner)."""
    W, cx, cy = cell(g)
    lv, lh = weights(g)
    over = 2 * W
    if any(arms.get(a) == 'd' for a in 'lr'):               # the double is horizontal: work in (x, y)
        neg, pos, lo, hi = 'l' in arms, 'r' in arms, 'd' in arms, 'u' in arms
        P = lambda a, b: (a, b)
        (a0, a1), ca, (b0, b1), cb = (0.0, W), cx, (BOTTOM, TOP), cy
        t_d, t_s, off = lh, lv, double_offset(g, False)
    else:                                                   # vertical: work in (y, x)
        neg, pos, lo, hi = 'd' in arms, 'u' in arms, 'l' in arms, 'r' in arms
        P = lambda a, b: (b, a)
        (a0, a1), ca, (b0, b1), cb = (BOTTOM, TOP), cy, (0.0, W), cx
        t_d, t_s, off = lv, lh, double_offset(g, True)
    if neg and pos:
        s0, s1 = a0 - over, a1 + over
    elif pos:
        s0, s1 = ca - t_s / 2, a1 + over
    else:
        s0, s1 = a0 - over, ca + t_s / 2
    for k in (-1, 1):
        g.stroke((*P(s0, cb + k * off), t_d), P(s1, cb + k * off))
    if lo and hi:
        g.stroke((*P(ca, b0 - over), t_s), P(ca, b1 + over))
        return
    through = neg and pos
    for present, sgn, edge in ((hi, 1, b1 + over), (lo, -1, b0 - over)):
        if present:
            stop = cb + sgn * off if through else cb - sgn * off
            g.stroke((*P(ca, stop), t_s), P(ca, edge))


def _dashes(g, n, vertical, style):
    """n dashes to a cell, each centred in its nth: across cells, gaps stay
    even. The gap is a quarter of a dash's share, never under three fifths of a stem."""
    W, cx, cy = cell(g)
    t = _thick(g, style, vertical)
    length = HEIGHT if vertical else W
    share = length / n
    gap = max(share / 4, 0.6 * weights(g)[0])
    for i in range(n):
        a, b = i * share + gap / 2, (i + 1) * share - gap / 2
        if vertical:
            g.stroke((cx, BOTTOM + a, t), (cx, BOTTOM + b))
        else:
            g.stroke((a, cy, t), (b, cy))


def arc_leg(g):
    """The chamfer of a rounded corner, on the centreline: half the way from
    the centre to the cell's side."""
    return 0.5 * g.W / 2


def _arc(g, h, v):
    """A light corner whose turn is a bowl's chamfer (curved in the
    italic). h = +1 right / -1 left, v = +1 up / -1 down."""
    W, cx, cy = cell(g)
    lv, lh = weights(g)
    over = 2 * W
    g.stroke((cx + h * (W / 2 + over), cy, lh), B(cx, cy, arc_leg(g), lv), (cx, cy + v * (HEIGHT + over)))


def _diagonal(g, rising):
    """Corner to corner. Cut flat at the cell's top and bottom but running on
    sideways through the corners, so a diagonal continues into the cells
    diagonally next to it without a waist."""
    W, cx, cy = cell(g, clip_x=False)
    lv, _ = weights(g)
    e = HEIGHT
    k = W / HEIGHT
    if rising:
        a, b = (0 - e * k, BOTTOM - e), (W + e * k, TOP + e)
    else:
        a, b = (0 - e * k, TOP + e), (W + e * k, BOTTOM - e)
    g.stroke(a, b)


BOX = {}


def _register_box():
    for cp in range(0x2500, 0x2580):
        ch = chr(cp)
        nm = unicodedata.name(ch)
        body = nm.replace('BOX DRAWINGS ', '')
        if 'DASH' in body:
            toks = body.split()
            n = {'DOUBLE': 2, 'TRIPLE': 3, 'QUADRUPLE': 4}[toks[1]]
            fn = (lambda g, n=n, v=toks[-1] == 'VERTICAL', s=STYLES[toks[0]]: _dashes(g, n, v, s))
        elif 'ARC' in body:
            h = 1 if 'RIGHT' in body else -1
            v = 1 if 'UP' in body else -1
            fn = (lambda g, h=h, v=v: _arc(g, h, v))
        elif 'DIAGONAL' in body:
            if 'CROSS' in body:
                fn = (lambda g: (_diagonal(g, True), _diagonal(g, False)))
            else:
                fn = (lambda g, r='UPPER RIGHT TO LOWER LEFT' in body: _diagonal(g, r))
        else:
            arms = parse_arms(nm)
            styles = set(arms.values())
            if styles == {'d'}:
                fn = (lambda g, a=arms: _double(g, a))
            elif 'd' in styles:
                fn = (lambda g, a=arms: _mixed(g, a))
            else:
                fn = (lambda g, a=arms: _junction(g, a))
        BOX[gname(cp)] = ch
        cell_glyph(ch, solid='HEAVY' in body)(fn)          # (heavy lines: twice the stroke, by design)


_register_box()


# --- Block elements ------------------------------------------------------------

def _block(*parts):
    """Rectangles given as fractions of the cell (x0, y0, x1, y1), y up."""
    def fn(g):
        W, cx, cy = cell(g)
        for x0, y0, x1, y1 in parts:
            rect(g, x0 * W, BOTTOM + y0 * HEIGHT, x1 * W, BOTTOM + y1 * HEIGHT)
    return fn


BLOCKS = {
    0x2580: [(0, 0.5, 1, 1)],
    0x2588: [(0, 0, 1, 1)],
    0x2590: [(0.5, 0, 1, 1)],
    0x2594: [(0, 7 / 8, 1, 1)],
    0x2595: [(7 / 8, 0, 1, 1)],
}
for k in range(1, 8):
    BLOCKS[0x2580 + k] = [(0, 0, 1, k / 8)]               # lower k eighths
    BLOCKS[0x2590 - k] = [(0, 0, k / 8, 1)]               # left k eighths
QUAD = {'ul': (0, 0.5, 0.5, 1), 'ur': (0.5, 0.5, 1, 1), 'll': (0, 0, 0.5, 0.5), 'lr': (0.5, 0, 1, 0.5)}
for cp, qs in {0x2596: 'll', 0x2597: 'lr', 0x2598: 'ul', 0x2599: 'ul ll lr', 0x259A: 'ul lr',
               0x259B: 'ul ur ll', 0x259C: 'ul ur lr', 0x259D: 'ur', 0x259E: 'ur ll',
               0x259F: 'ur ll lr'}.items():
    BLOCKS[cp] = [QUAD[q] for q in qs.split()]
for cp, parts in BLOCKS.items():
    cell_glyph(chr(cp), solid=True)(_block(*parts))


# Shades: one lattice of chamfered squares, two to a cell across and four
# down, every other place in each row inked (a checkerboard of places). The
# cell's edges pass through squares' centres, so a square cut by an edge is
# completed by the next cell's. A shade is a tone, not a weight: it is drawn
# the same at every weight, with Regular's edge break, and its squares are
# sized so that, corners cut, they cover a quarter, a half (the
# checkerboard, its squares meeting only at their cut corners) and three
# quarters (the quarter's negative) of the cell.
SHADE_COLS, SHADE_ROWS = 4, 8
SHADE_BREAK = 0.25 * 90.0                                   # Regular's edge break (instances.Optics)


def _shade_places(W):
    dx, dy = W / SHADE_COLS, HEIGHT / SHADE_ROWS
    for j in range(SHADE_ROWS + 1):
        for i in range(SHADE_COLS + 1):
            if (i + j) % 2 == 0:
                yield i * dx, BOTTOM + j * dy, dx, dy


def _shade_square(dx, dy, cover):
    """Side of a square that, its four corners cut, covers ``cover`` of its
    two lattice places (its own and a white one)."""
    return math.sqrt(2 * cover * dx * dy + 2 * SHADE_BREAK ** 2)


def _shade(g):
    g.p = g.p.with_(c=SHADE_BREAK)
    return cell(g)[0]


@cell_glyph('░', solid=True)
def shade_light(g):
    W = _shade(g)
    for x, y, dx, dy in _shade_places(W):
        s = _shade_square(dx, dy, 0.25)
        rect(g, x - s / 2, y - s / 2, x + s / 2, y + s / 2)


@cell_glyph('▒', solid=True)
def shade_medium(g):
    W = _shade(g)
    e = 1.0                                                 # (corners never quite touch)
    for x, y, dx, dy in _shade_places(W):
        rect(g, x - dx / 2 + e, y - dy / 2 + e, x + dx / 2 - e, y + dy / 2 - e)


@cell_glyph('▓', solid=True)
def shade_dark(g):
    """The light shade's negative: its squares are holes in a full cell, and
    the corner rule fills their corners as it does a counter's."""
    from shapely import union_all
    W = _shade(g)
    full = box(-W, BOTTOM - HEIGHT, 2 * W, TOP + HEIGHT)
    holes = []
    for x, y, dx, dy in _shade_places(W):
        s = _shade_square(dx, dy, 0.25)                    # (its corners filled, it is the quarter's white)
        holes.append(box(x - s / 2, y - s / 2, x + s / 2, y + s / 2))
    g.extra.append(full.difference(union_all(holes)))


# --- Braille ---------------------------------------------------------------------

# Dots 1-3 and 7 down the left column, 4-6 and 8 down the right, on a grid
# that spaces them evenly across cells and rows alike: a column at a quarter
# and three quarters of the width, rows at the eighths of the line's height.
BRAILLE_DOTS = {1: (0, 0), 2: (0, 1), 3: (0, 2), 4: (1, 0), 5: (1, 1), 6: (1, 2), 7: (0, 3), 8: (1, 3)}


def _braille(bits):
    def fn(g):
        W, cx, cy = cell(g)
        s = min(g.p.dot(), min(W / 2, HEIGHT / 4) - 0.6 * weights(g)[0])   # (white between dots: 3/5 stem)
        for d in range(1, 9):
            if bits & (1 << (d - 1)):
                col, row = BRAILLE_DOTS[d]
                x = (0.25 + 0.5 * col) * W
                y = TOP - (2 * row + 1) * HEIGHT / 8
                rect(g, x - s / 2, y - s / 2, x + s / 2, y + s / 2)
    return fn


for bits in range(256):
    cell_glyph(chr(0x2800 + bits))(_braille(bits))


# --- Powerline -------------------------------------------------------------------

@cell_glyph('\ue0b0', solid=True)
def pl_right_solid(g):
    """The full cell's height narrowing to a point on its right edge."""
    W, cx, cy = cell(g)
    g.extra.append(Polygon([(0, BOTTOM), (W, cy), (0, TOP)]))


@cell_glyph('\ue0b2', solid=True)
def pl_left_solid(g):
    W, cx, cy = cell(g)
    g.extra.append(Polygon([(W, BOTTOM), (W, TOP), (0, cy)]))


def _pl_chevron(g, right):
    """A light chevron from the cell's corners, its outer edges meeting in a
    point on the far edge."""
    W, cx, cy = cell(g)
    lv, _ = weights(g)
    tip = W
    for _ in range(8):                                      # the centreline's point, inside by the miter
        tip = W - (lv / 2) / math.sin(math.atan2(HEIGHT / 2, tip))
    e = 0.5 * W
    slope = (HEIGHT / 2) / tip
    pts = [(-e, TOP + e * slope, lv), (tip, cy, lv), (-e, BOTTOM - e * slope)]
    if not right:
        pts = [(W - q[0], *q[1:]) for q in pts]
    g.stroke(*pts)


@cell_glyph('\ue0b1')
def pl_right_line(g):
    _pl_chevron(g, True)


@cell_glyph('\ue0b3')
def pl_left_line(g):
    _pl_chevron(g, False)


# The geometric shapes' black corner triangles are drawn as terminal fonts
# draw them: the cell's diagonal half, joining blocks and Powerline arrows.
CORNER_TRIANGLES = {0x25E2: ((0, 0), (1, 0), (1, 1)), 0x25E3: ((0, 0), (1, 0), (0, 1)),
                    0x25E4: ((0, 1), (1, 1), (0, 0)), 0x25E5: ((1, 1), (0, 1), (1, 0))}


def _corner_triangle(pts):
    def fn(g):
        W, cx, cy = cell(g)
        g.extra.append(Polygon([(x * W, BOTTOM + y * HEIGHT) for x, y in pts]))
    return fn


for cp, pts in CORNER_TRIANGLES.items():
    cell_glyph(chr(cp), solid=True)(_corner_triangle(pts))
