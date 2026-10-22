"""Geometric shapes (U+25A0-U+25FF).

Arris has no curves, so a circle is an octagon: regular, cut 0.29 of its
width deep at each corner (the 0's own corners are 0.28 of its width), and
in the italic its chamfers become curves like every bowl's. Triangles take
the 7's 2:1 slope (base as wide as the triangle is tall), diamonds 45
degrees, the lozenge 2:1, so every shape's edges run in the figures' own
directions. Corners where an edge meets a horizontal or vertical one get
the corner rule's edge break; the points of diamonds stay sharp.

Every shape sits centred on the math axis (half the cap height), in four
sizes: large (0.62 of the cap height, growing with the stem past Regular,
so white inside a shape grows with its strokes), medium (0.8), medium small
(0.64) and small (0.48). Black shapes are solid; white ones are drawn with
their outer edge on the black one's outline, in a pen no heavier than the
weight's stem and light enough that a shape's counter keeps half its
inradius (small and pointed shapes draw lighter, as small figures do).
Shapes with parts inside them (the hatched squares, the bullseye) keep
three fifths or more. Fills inside a shape (hatching, half-black circles)
are strokes clipped to its counter.
"""
from __future__ import annotations

import math

import shapely
from shapely.geometry import Polygon, box

from ..draw import B, REGISTRY, Glyph, _thickness, glyph
from ..geom import stroke_polygon
from ..params import SQRT2
from .letterframe import heft
from .punct import axis
from .terminal import gname

OCT = 1 - 1 / SQRT2           # a regular octagon's corner, along each axis, as a share of its width


def large(p):
    """The large shape's width (the black square's)."""
    return 0.62 * p.cap + 1.5 * heft(p)


SIZES = {'L': 1.0, 'M': 0.8, 'MS': 0.64, 'S': 0.48}


def fit(p, w):
    """A body width, never wider than the figures' in the monospaced cut."""
    return min(w, p.fig_w) if p.mono else w


def size_of(p, sz):
    return fit(p, SIZES[sz] * large(p)) if isinstance(sz, str) else sz(p)


def shape(char, sz='L', solid=False, sides=1.0):
    """Register a shape (named by AGL, else uniXXXX) whose body is its size:
    a size class, or a function of the parameters."""
    name = gname(ord(char))
    assert name not in REGISTRY, name
    return glyph(name, char, lambda p, sz=sz: size_of(p, sz), kind=('punct', sides), solid=solid)


# --- Pens --------------------------------------------------------------------

def inradius(pts) -> float:
    return shapely.maximum_inscribed_circle(Polygon(pts), tolerance=0.5).length


def pen(g, pts, keep=0.5):
    """Set the glyph's pen for the outline of ``pts``: the weight's own, or
    lighter where its counter would keep less than ``keep`` of the shape's
    inradius. Every direction and the edge break scale together."""
    p = g.p
    t = min(p.sv, (1 - keep) * inradius(pts))
    k = max(t, p.floor) / p.sv
    if k < 1:
        g.p = p.with_(sv=p.sv * k, sh=p.sh * k, sd=p.sd * k, ss=p.ss * k, c=p.c * k)
    return g.p


def widths(g):
    """(vertical, horizontal, 45-degree) thickness of the glyph's pen."""
    p = g.p
    return max(p.sv, p.floor), g.sh, max(p.sd, p.floor)


def _ccw(pts):
    a = sum(pts[i - 1][0] * pts[i][1] - pts[i][0] * pts[i - 1][1] for i in range(len(pts)))
    return pts if a > 0 else pts[::-1]


def outline(g, pts):
    """A closed stroke whose outer edge is the polygon ``pts``: each side set
    in by half its own thickness (by its direction, the glyph's pen)."""
    th = _thickness(g.p, g.sh)
    pts = _ccw(list(pts))
    n = len(pts)
    lines = []
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        d = (dx / L, dy / L)
        w = th(d)
        lines.append(((a[0] - d[1] * w / 2, a[1] + d[0] * w / 2), d, w))
    nodes = []
    for i in range(n):
        (p1, d1, _), (p2, d2, w) = lines[i - 1], lines[i]
        den = d1[0] * d2[1] - d1[1] * d2[0]
        t = ((p2[0] - p1[0]) * d2[1] - (p2[1] - p1[1]) * d2[0]) / den
        nodes.append((p1[0] + d1[0] * t, p1[1] + d1[1] * t, w))
    centre = Polygon([q[:2] for q in nodes])
    if centre.is_valid and _ccw([q[:2] for q in nodes]) == [q[:2] for q in nodes]:
        try:
            from ..geom import Node, Stroke, _stroke_polygon
            _stroke_polygon(Stroke(tuple(Node(q[0], q[1], 0.0, q[2]) for q in nodes), True), th, g.p.c)
            g.stroke(*nodes, closed=True)
            return
        except ValueError:
            pass
    # a feature narrower than the pen (a heart's notch at a tiny size): the
    # outline is the shape less the shape set in by the stem, all round
    shp = Polygon(pts)
    solid(g, shp.difference(shp.buffer(-max(g.p.sv, g.p.floor), join_style='mitre')))


def solid(g, poly, chords=()):
    """A solid region (a polygon or shapely geometry). ``chords``: its 45-degree
    edges that stand for an octagon's corners, curved in the italic."""
    poly = poly if not isinstance(poly, (list, tuple)) else Polygon(poly)
    assert poly.is_valid, "a solid must be a valid region"
    g.extra.append(poly)
    g.extra_chamfers += [('chord', a, b) for a, b in chords]


def ink_of(g, strokes):
    """The ink of some strokes in the glyph's pen, before the corner rule
    (to be clipped to a region): strokes as point lists, (x, y[, w])."""
    sub = Glyph(g.p, W=g.W)
    for pts in strokes:
        sub.stroke(*pts)
    th = _thickness(sub.p, sub.sh)
    return shapely.union_all([stroke_polygon(s, th, g.p.c) for s in sub.strokes])


# --- Octagons ------------------------------------------------------------------

def oct_pts(cx, cy, S, H=None):
    """A regular octagon S wide (and H tall, its corners still S's)."""
    H = S if H is None else H
    rx, ry, a = S / 2, H / 2, OCT * min(S, H)
    return [(cx - rx + a, cy - ry), (cx + rx - a, cy - ry), (cx + rx, cy - ry + a), (cx + rx, cy + ry - a),
            (cx + rx - a, cy + ry), (cx - rx + a, cy + ry), (cx - rx, cy + ry - a), (cx - rx, cy - ry + a)]


def oct_chords(pts):
    return [(pts[i], pts[(i + 1) % 8]) for i in (1, 3, 5, 7)]


def disc(g, cx, cy, S):
    """A black circle: a solid octagon."""
    pts = oct_pts(cx, cy, S)
    solid(g, pts, oct_chords(pts))


def ring(g, cx, cy, S, H=None):
    """A white circle: an octagonal ring in the glyph's pen, its outer edge
    on the octagon, its corners bowls (curved in the italic)."""
    H = S if H is None else H
    tv, th, td = widths(g)
    lo = OCT * min(S, H)                                    # the outer corner's leg
    leg = lo - (tv + th) / 2 + td / SQRT2                   # on the centreline (params.outer_leg)
    rx, ry = S / 2 - tv / 2, H / 2 - th / 2
    g.stroke(B(cx - rx, cy - ry, leg, th), B(cx + rx, cy - ry, leg, tv), B(cx + rx, cy + ry, leg, th),
             B(cx - rx, cy + ry, leg, tv), closed=True)


def counter_oct(g, cx, cy, S):
    """The octagon a ring's fills overlap: its centreline (fills reach half
    into the ring, so they join it)."""
    tv = widths(g)[0]
    return Polygon(oct_pts(cx, cy, S - tv))


# --- Squares and rectangles ------------------------------------------------------

def sq_pts(cx, cy, w, h=None):
    h = w if h is None else h
    return [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2), (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)]


def block(g, cx, cy, w, h=None):
    """A black square or rectangle: one stroke as wide as the shape."""
    h = w if h is None else h
    g.stroke((cx, cy - h / 2, w), (cx, cy + h / 2))


def _centre(g):
    return g.W / 2, axis(g.p)


def _black_square(sz, k=1.0):
    def fn(g):
        cx, cy = _centre(g)
        block(g, cx, cy, g.W, k * g.W)
    return fn


def _white_square(sz, k=1.0):
    def fn(g):
        cx, cy = _centre(g)
        pts = sq_pts(cx, cy, g.W, k * g.W)
        pen(g, pts)
        outline(g, pts)
    return fn


for ch, sz in (('■', 'L'), ('◼', 'M'), ('◾', 'MS'), ('▪', 'S')):
    shape(ch, sz, solid=True)(_black_square(sz))
for ch, sz in (('□', 'L'), ('◻', 'M'), ('◽', 'MS'), ('▫', 'S')):
    shape(ch, sz)(_white_square(sz))

shape('▬', 'L', solid=True)(_black_square('L', 0.5))
shape('▭', 'L')(_white_square('L', 0.5))


@shape('▮', lambda p: 0.5 * size_of(p, 'L'), solid=True)
def black_vrect(g):
    cx, cy = _centre(g)
    block(g, cx, cy, g.W, 2 * g.W)


@shape('▯', lambda p: 0.5 * size_of(p, 'L'))
def white_vrect(g):
    cx, cy = _centre(g)
    pts = sq_pts(cx, cy, g.W, 2 * g.W)
    pen(g, pts)
    outline(g, pts)


@shape('▢', 'L')
def white_square_rounded(g):
    """The square with its corners a bowl's: chamfered, curved in the italic."""
    cx, cy = _centre(g)
    S = g.W
    pen(g, sq_pts(cx, cy, S))
    tv, th, td = widths(g)
    lo = 0.18 * S
    leg = lo - (tv + th) / 2 + td / SQRT2
    r, ry = S / 2 - tv / 2, S / 2 - th / 2
    g.stroke(B(cx - r, cy - ry, leg, th), B(cx + r, cy - ry, leg, tv), B(cx + r, cy + ry, leg, th),
             B(cx - r, cy + ry, leg, tv), closed=True)


def _boxed(g, keep=0.6):
    """A white square with room inside: (centre, size, counter box)."""
    cx, cy = _centre(g)
    S = g.W
    pts = sq_pts(cx, cy, S)
    pen(g, pts, keep)
    outline(g, pts)
    tv, th, _ = widths(g)
    return cx, cy, S, (cx - S / 2 + tv, cy - S / 2 + th, cx + S / 2 - tv, cy + S / 2 - th)


@shape('▣', 'L', solid=True)
def square_in_square(g):
    """A black square inside a white one, the white between them as wide as
    the pen at least."""
    cx, cy, S, (x0, y0, x1, y1) = _boxed(g)
    gap = max(widths(g)[0], 0.12 * S)
    inner = (x1 - x0) - 2 * gap
    block(g, cx, cy, inner)


def _hatch(g, horizontal=False, vertical=False, down=False, up=False, n=3):
    """A white square filled with lines as wide as the white between them
    (no heavier than the pen): n each way, or at the same pitch on the
    diagonals. The glyph's edge break is the hatch lines' own (a quarter of
    their width, as a stem's), so the fine counters between them stay
    square."""
    cx, cy, S, (x0, y0, x1, y1) = _boxed(g)
    tv, th, _ = widths(g)
    inner = x1 - x0
    t = min(th, inner / (2 * n + 1))
    g.p = g.p.with_(c=min(g.p.c, 0.25 * t))
    pitch = (inner + t) / (n + 1)
    region = box(x0 - tv / 2, y0 - th / 2, x1 + tv / 2, y1 + th / 2)    # reaching half into the outline
    lines = []
    for i in range(1, n + 1):
        u = x0 - t / 2 + i * pitch                                       # (the white bands are even)
        v = y0 - t / 2 + i * pitch
        if horizontal:
            lines.append([(x0 - S, v, t), (x1 + S, v)])
        if vertical:
            lines.append([(u, y0 - S, t), (u, y1 + S)])
    # diagonals: 2n + 1 lines, the outermost through the counter's corners
    # (where they meet the outline), so no sliver of white is left in a corner
    m = n - 1 if (down and up) else n                                     # (a crosshatch: fewer, larger cells)
    k = inner / m                                                        # along x, from line to line
    td = min(t, k / SQRT2 / 2)                                           # (as heavy as the white between)
    for i in range(-m, m + 1):
        c = i * k
        if down:                                                         # upper left to lower right
            lines.append([(cx + c - S, cy + S, td), (cx + c + S, cy - S)])
        if up:
            lines.append([(cx + c - S, cy - S, td), (cx + c + S, cy + S)])
    solid(g, ink_of(g, lines).intersection(region))


@shape('▤', 'L')
def sq_hfill(g):
    _hatch(g, horizontal=True)


@shape('▥', 'L')
def sq_vfill(g):
    _hatch(g, vertical=True)


@shape('▦', 'L')
def sq_crosshatch(g):
    _hatch(g, horizontal=True, vertical=True)


@shape('▧', 'L')
def sq_down_fill(g):
    _hatch(g, down=True)


@shape('▨', 'L')
def sq_up_fill(g):
    _hatch(g, up=True)


@shape('▩', 'L')
def sq_diag_crosshatch(g):
    _hatch(g, down=True, up=True)


def _half_box(g, region):
    """A white square, the part of its counter in ``region`` black."""
    cx, cy, S, (x0, y0, x1, y1) = _boxed(g, keep=0.4)
    tv, th, _ = widths(g)
    inside = box(x0 - tv / 2, y0 - th / 2, x1 + tv / 2, y1 + th / 2)
    solid(g, inside.intersection(region(cx, cy, S)))


@shape('◧', 'L', solid=True)
def sq_left_black(g):
    _half_box(g, lambda cx, cy, S: box(cx - S, cy - S, cx, cy + S))


@shape('◨', 'L', solid=True)
def sq_right_black(g):
    _half_box(g, lambda cx, cy, S: box(cx, cy - S, cx + S, cy + S))


@shape('◩', 'L', solid=True)
def sq_ul_black(g):
    _half_box(g, lambda cx, cy, S: Polygon([(cx - S, cy - S), (cx + S, cy + S), (cx - S, cy + S)]))


@shape('◪', 'L', solid=True)
def sq_lr_black(g):
    _half_box(g, lambda cx, cy, S: Polygon([(cx - S, cy - S), (cx + S, cy - S), (cx + S, cy + S)]))


@shape('◫', 'L')
def sq_bisected(g):
    cx, cy, S, (x0, y0, x1, y1) = _boxed(g, keep=0.6)
    tv = widths(g)[0]
    g.stroke((cx, y0 - tv / 2, tv), (cx, y1 + tv / 2))


def _quadrant_box(sx, sy):
    def fn(g):
        cx, cy, S, (x0, y0, x1, y1) = _boxed(g, keep=0.6)
        tv, th, _ = widths(g)
        ye = y1 + th / 2 if sy > 0 else y0 - th / 2
        xe = x1 + tv / 2 if sx > 0 else x0 - tv / 2
        g.stroke((cx, ye, tv), (cx, cy - sy * th / 2))
        g.stroke((xe, cy, th), (cx - sx * tv / 2, cy))
    return fn


for cp, (sx, sy) in {0x25F0: (-1, 1), 0x25F1: (-1, -1), 0x25F2: (1, -1), 0x25F3: (1, 1)}.items():
    shape(chr(cp), 'L')(_quadrant_box(sx, sy))


# --- Parallelograms ----------------------------------------------------------

def _para_pts(g):
    cx, cy = _centre(g)
    S = g.W
    h = 0.5 * S
    x0 = cx - S / 2
    return [(x0, cy - h / 2), (x0 + S - h / 2, cy - h / 2), (x0 + S, cy + h / 2), (x0 + h / 2, cy + h / 2)]


@shape('▰', 'L', solid=True)
def black_para(g):
    solid(g, _para_pts(g))


@shape('▱', 'L')
def white_para(g):
    pts = _para_pts(g)
    pen(g, pts)
    outline(g, pts)


# --- Triangles -------------------------------------------------------------------

def tri_pts(cx, cy, S, d):
    """A triangle S wide and tall pointing d ('u', 'd', 'l', 'r'): its sides
    on the 2:1 slope."""
    h = S / 2
    pts = {'u': [(cx - h, cy - h), (cx + h, cy - h), (cx, cy + h)],
           'd': [(cx - h, cy + h), (cx, cy - h), (cx + h, cy + h)],
           'r': [(cx - h, cy - h), (cx + h, cy), (cx - h, cy + h)],
           'l': [(cx + h, cy - h), (cx + h, cy + h), (cx - h, cy)]}
    return pts[d]


def _triangle(d, black):
    def fn(g):
        cx, cy = _centre(g)
        pts = tri_pts(cx, cy, g.W, d)
        if black:
            solid(g, pts)
        else:
            pen(g, pts)
            outline(g, pts)
    return fn


TRIANGLES = {  # cp: (direction, size, black)
    0x25B2: ('u', 'L', 1), 0x25B3: ('u', 'L', 0), 0x25B4: ('u', 'S', 1), 0x25B5: ('u', 'S', 0),
    0x25B6: ('r', 'L', 1), 0x25B7: ('r', 'L', 0), 0x25B8: ('r', 'S', 1), 0x25B9: ('r', 'S', 0),
    0x25BA: ('r', 'M', 1), 0x25BB: ('r', 'M', 0),
    0x25BC: ('d', 'L', 1), 0x25BD: ('d', 'L', 0), 0x25BE: ('d', 'S', 1), 0x25BF: ('d', 'S', 0),
    0x25C0: ('l', 'L', 1), 0x25C1: ('l', 'L', 0), 0x25C2: ('l', 'S', 1), 0x25C3: ('l', 'S', 0),
    0x25C4: ('l', 'M', 1), 0x25C5: ('l', 'M', 0),
}
for cp, (d, sz, black) in TRIANGLES.items():
    shape(chr(cp), sz, solid=bool(black))(_triangle(d, black))


@shape('◬', 'L')
def tri_dot(g):
    cx, cy = _centre(g)
    S = g.W
    pts = tri_pts(cx, cy, S, 'u')
    s0 = g.p.dot()
    pen(g, pts, keep=0.6)
    outline(g, pts)
    tv, th, _ = widths(g)
    s = min(s0, 0.6 * (inradius(pts) - tv))                 # a dot that keeps white round it
    yc = cy - S / 2 + th + (inradius(pts) - th) * 0.9
    block(g, cx, yc, s)


def _tri_half(side):
    def fn(g):
        cx, cy = _centre(g)
        S = g.W
        pts = tri_pts(cx, cy, S, 'u')
        pen(g, pts)
        outline(g, pts)
        region = box(cx - S, cy - S, cx, cy + S) if side < 0 else box(cx, cy - S, cx + S, cy + S)
        solid(g, Polygon(pts).intersection(region))
    return fn


shape('◭', 'L', solid=True)(_tri_half(-1))
shape('◮', 'L', solid=True)(_tri_half(1))


def corner_tri_pts(cx, cy, S, corner):
    """A right triangle in an S square, its right angle at ``corner``
    ('ul', 'ur', 'll', 'lr'), its hypotenuse at 45 degrees."""
    x0, x1, y0, y1 = cx - S / 2, cx + S / 2, cy - S / 2, cy + S / 2
    return {'ul': [(x0, y1), (x0, y0), (x1, y1)], 'ur': [(x1, y1), (x0, y1), (x1, y0)],
            'll': [(x0, y0), (x1, y0), (x0, y1)], 'lr': [(x1, y0), (x1, y1), (x0, y0)]}[corner]


def _corner_tri(corner):
    def fn(g):
        cx, cy = _centre(g)
        pts = corner_tri_pts(cx, cy, g.W, corner)
        pen(g, pts)
        outline(g, pts)
    return fn


for cp, corner in {0x25F8: 'ul', 0x25F9: 'ur', 0x25FA: 'll', 0x25FF: 'lr'}.items():
    shape(chr(cp), 'L')(_corner_tri(corner))


# --- Diamonds and the lozenge ---------------------------------------------------

def diamond_pts(cx, cy, w, h=None):
    h = w if h is None else h
    return [(cx, cy - h / 2), (cx + w / 2, cy), (cx, cy + h / 2), (cx - w / 2, cy)]


@shape('◆', 'L', solid=True)
def black_diamond(g):
    cx, cy = _centre(g)
    solid(g, diamond_pts(cx, cy, g.W))


@shape('◇', 'L')
def white_diamond(g):
    cx, cy = _centre(g)
    pts = diamond_pts(cx, cy, g.W)
    pen(g, pts)
    outline(g, pts)


@shape('◈', 'L')
def diamond_in_diamond(g):
    cx, cy = _centre(g)
    S = g.W
    pts = diamond_pts(cx, cy, S)
    sv = g.p.sv
    pen(g, pts, keep=0.6)
    outline(g, pts)
    t = widths(g)[2]
    gap = max(t, 0.1 * S, 0.6 * sv)                         # (white: three fifths of the weight's stem)
    inner = S - 2 * SQRT2 * (t + gap)                       # (45-degree sides: across is sqrt2 along)
    solid(g, diamond_pts(cx, cy, inner))


@shape('◊', lambda p: 0.5 * size_of(p, 'L'))
def lozenge(g):
    """Twice as tall as wide: sides on the 2:1 slope."""
    cx, cy = _centre(g)
    pts = diamond_pts(cx, cy, g.W, 2 * g.W)
    pen(g, pts)
    outline(g, pts)


# --- Circles -------------------------------------------------------------------------

def xl(p):
    """The large circle's and the large squares' width: the cap height."""
    return fit(p, p.cap + 1.5 * heft(p))


@shape('●', 'L', solid=True)
def black_circle(g):
    cx, cy = _centre(g)
    disc(g, cx, cy, g.W)


@shape('○', 'L')
def white_circle(g):
    cx, cy = _centre(g)
    pen(g, oct_pts(cx, cy, g.W))
    ring(g, cx, cy, g.W)


@shape('◯', xl)
def large_circle(g):
    cx, cy = _centre(g)
    pen(g, oct_pts(cx, cy, g.W))
    ring(g, cx, cy, g.W)


@shape('◌', 'L')
def dotted_circle(g):
    """Eight dots round an octagon, at its sides' middles."""
    cx, cy = _centre(g)
    s = min(g.p.dot(), 0.18 * g.W)                         # (dots stay apart at Black)
    r = g.W / 2 - s / 2
    for k in range(8):
        a = math.radians(45 * k)
        q = r if k % 2 == 0 else r * 0.92                     # the diagonal sides sit in a little
        block(g, cx + q * math.cos(a), cy + q * math.sin(a), s)


@shape('◎', 'L')
def bullseye(g):
    cx, cy = _centre(g)
    S = g.W
    pen(g, oct_pts(cx, cy, S), keep=0.7)
    tv = widths(g)[0]
    ring(g, cx, cy, S)
    gap = max(tv, 0.1 * S)
    ring(g, cx, cy, S - 2 * (tv + gap))


@shape('◉', 'L', solid=True)
def fisheye(g):
    cx, cy = _centre(g)
    S = g.W
    pen(g, oct_pts(cx, cy, S), keep=0.6)
    tv = widths(g)[0]
    ring(g, cx, cy, S)
    gap = max(tv, 0.12 * S)
    disc(g, cx, cy, S - 2 * (tv + gap))


@shape('◍', 'L')
def circle_vfill(g):
    cx, cy = _centre(g)
    S = g.W
    pen(g, oct_pts(cx, cy, S), keep=0.6)
    tv, th, _ = widths(g)
    ring(g, cx, cy, S)
    inner = S - 2 * tv
    n = 3
    t = min(tv, inner / (2 * n + 1))
    pitch = (inner + t) / (n + 1)
    lines = [[(cx - inner / 2 - t / 2 + i * pitch, cy - S, t), (cx - inner / 2 - t / 2 + i * pitch, cy + S)]
             for i in range(1, n + 1)]
    solid(g, ink_of(g, lines).intersection(counter_oct(g, cx, cy, S)))


def _half_circle(region):
    def fn(g):
        cx, cy = _centre(g)
        S = g.W
        pen(g, oct_pts(cx, cy, S))
        ring(g, cx, cy, S)
        solid(g, counter_oct(g, cx, cy, S).intersection(region(cx, cy, S)))
    return fn


HALVES = {
    0x25D0: lambda cx, cy, S: box(cx - S, cy - S, cx, cy + S),
    0x25D1: lambda cx, cy, S: box(cx, cy - S, cx + S, cy + S),
    0x25D2: lambda cx, cy, S: box(cx - S, cy - S, cx + S, cy),
    0x25D3: lambda cx, cy, S: box(cx - S, cy, cx + S, cy + S),
    0x25D4: lambda cx, cy, S: box(cx, cy, cx + S, cy + S),
    0x25D5: lambda cx, cy, S: box(cx - S, cy - S, cx + S, cy + S).difference(box(cx - S, cy, cx, cy + S)),
}
for cp, region in HALVES.items():
    shape(chr(cp), 'L', solid=True)(_half_circle(region))


def _half_disc(side):
    def fn(g):
        S = 2 * g.W
        cy = axis(g.p)
        cx = g.W if side < 0 else 0.0
        pts = oct_pts(cx, cy, S)
        keep = box(cx - S, cy - S, cx, cy + S) if side < 0 else box(cx, cy - S, cx + S, cy + S)
        chords = [c for c in oct_chords(pts) if (c[0][0] - cx) * side > 0]
        solid(g, Polygon(pts).intersection(keep), chords)
    return fn


shape('◖', lambda p: 0.5 * size_of(p, 'L'), solid=True)(_half_disc(-1))
shape('◗', lambda p: 0.5 * size_of(p, 'L'), solid=True)(_half_disc(1))


@shape('◘', 'L', solid=True)
def inverse_bullet(g):
    """A black square with a white octagon in it, the bullet's size."""
    cx, cy = _centre(g)
    S = g.W
    hole = oct_pts(cx, cy, 0.42 * S)
    solid(g, Polygon(sq_pts(cx, cy, S)).difference(Polygon(hole)), oct_chords(hole))


def _inverse_ring(g):
    """A black square with a white ring cut in it: the ring and the disc in
    it in proportion to the square, the ring at least three fifths of the
    stem wide, so neither closes at Black."""
    cx, cy = _centre(g)
    S = g.W
    b = 0.12 * S                                            # black outside the ring
    w = max(0.15 * S, 0.6 * g.p.sv)                         # the white ring
    o = oct_pts(cx, cy, S - 2 * b)
    i = oct_pts(cx, cy, S - 2 * b - 2 * w)
    ink = Polygon(sq_pts(cx, cy, S)).difference(Polygon(o)).union(Polygon(i))
    return cx, cy, S, ink, oct_chords(o) + oct_chords(i)


@shape('◙', 'L', solid=True)
def inverse_circle(g):
    cx, cy, S, ink, chords = _inverse_ring(g)
    solid(g, ink, chords)


@shape('◚', 'L', solid=True)
def inverse_circle_upper(g):
    cx, cy, S, ink, chords = _inverse_ring(g)
    solid(g, ink.intersection(box(cx - S, cy, cx + S, cy + S)), [c for c in chords if c[0][1] > cy])


@shape('◛', 'L', solid=True)
def inverse_circle_lower(g):
    cx, cy, S, ink, chords = _inverse_ring(g)
    solid(g, ink.intersection(box(cx - S, cy - S, cx + S, cy)), [c for c in chords if c[0][1] < cy])


def _arc(corners):
    """Part of the circle's ring: from the middle of one side round the
    given corners to the middle of another."""
    def fn(g):
        cx, cy = _centre(g)
        S = g.W
        pen(g, oct_pts(cx, cy, S))
        tv, th, td = widths(g)
        lo = OCT * S
        leg = lo - (tv + th) / 2 + td / SQRT2
        rx, ry = S / 2 - tv / 2, S / 2 - th / 2
        C = {'ll': (cx - rx, cy - ry), 'lr': (cx + rx, cy - ry), 'ur': (cx + rx, cy + ry), 'ul': (cx - rx, cy + ry)}
        order = ['ll', 'lr', 'ur', 'ul']
        i0 = order.index(corners[0])
        seq = [order[(i0 + k) % 4] for k in range(len(corners))]
        a, b = C[seq[0]], C[seq[-1]]
        prev = C[order[(i0 - 1) % 4]]
        nxt = C[order[(i0 + len(corners)) % 4]]
        start = ((a[0] + prev[0]) / 2, (a[1] + prev[1]) / 2)
        end = ((b[0] + nxt[0]) / 2, (b[1] + nxt[1]) / 2)
        nodes = [start] + [B(*C[c], leg) for c in seq] + [end]
        g.stroke(*nodes)
    return fn


for cp, corners in {0x25DC: ['ul'], 0x25DD: ['ur'], 0x25DE: ['lr'], 0x25DF: ['ll'],
                    0x25E0: ['ur', 'ul'], 0x25E1: ['ll', 'lr']}.items():   # (corners counter-clockwise)
    shape(chr(cp), 'L')(_arc(corners))


def _quadrant_circle(sx, sy):
    def fn(g):
        cx, cy = _centre(g)
        S = g.W
        pen(g, oct_pts(cx, cy, S), keep=0.6)
        tv, th, _ = widths(g)
        ring(g, cx, cy, S)
        g.stroke((cx, cy + sy * (S / 2 - th / 2), tv), (cx, cy - sy * th / 2))
        g.stroke((cx + sx * (S / 2 - tv / 2), cy, th), (cx - sx * tv / 2, cy))
    return fn


for cp, (sx, sy) in {0x25F4: (-1, 1), 0x25F5: (-1, -1), 0x25F6: (1, -1), 0x25F7: (1, 1)}.items():
    shape(chr(cp), 'L')(_quadrant_circle(sx, sy))


def bullet_size(p):
    """The white bullet: a little larger than the bullet (2.4 stems), linear
    in the stem so the variable font draws it exactly between masters."""
    return 1.6 * p.sv + 1.5 * p.m


@shape('◦', bullet_size, sides=0.8)
def white_bullet(g):
    """A ring the bullet's size, on the x-height's centre."""
    p = g.p
    cx, cy = g.W / 2, p.xh / 2
    pen(g, oct_pts(cx, cy, g.W))
    ring(g, cx, cy, g.W)
