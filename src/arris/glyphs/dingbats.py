"""Dingbats and miscellaneous symbols for interfaces, and the Powerline icons.

Built from the shapes' vocabulary (``shapes``): octagons for circles, the
2:1 slope and 45 degrees for every diagonal, solids with the corner rule's
breaks, white forms as outlines in a pen that keeps their counters. Where
Arris already has the form, the dingbat grows from it: the check mark is
the radical's tick and rise, the arrows' heads are the arrows' 45 degrees,
the lightning bolt is two bands joined by the 2's notch, the gear sits its
teeth on an octagon's eight sides, the ornament question and exclamation
marks are Arris's own drawn heavy (and hollowed for the white ones).

Three stars truly need angles of their own: the five-pointed star (36 and
72 degrees), the eight-pointed star with sharp points and the
twelve-pointed one. The rectilinear eight-pointed star, the pinwheel, the
four-pointed and the six-pointed stars keep to 45 degrees and the 2:1.

"Heavy" forms (the heavy check, the heavy crosses and asterisk) draw their
strokes 1.6 times the weight's.
"""
from __future__ import annotations

import math

from shapely.geometry import Polygon, box

from ..draw import B, REGISTRY, draw
from ..params import SQRT2
from .letterframe import heft
from .punct import axis
from .shapes import (OCT, block, disc, fit, ink_of, oct_chords, oct_pts, outline, pen, ring, slanted,
                     shape, size_of, solid, sq_pts, tri_pts, widths, xl)

HEAVY = 1.6


def heavy(g, S, k=HEAVY, share=0.25):
    """Set the glyph's pen for a form S wide: k times the weight's stroke
    (HEAVY for the heavy forms), but no heavier than ``share`` of the form
    (a quarter more for the heavy ones), so that at Black its parts stay apart
    and the heavy forms stay heavier than the light. Every direction and
    the edge break scale together."""
    p = g.p
    t = min(k * p.sv, share * (1.25 if k > 1 else 1.0) * S)
    f = max(t, p.floor) / p.sv
    g.p = p.with_(sv=p.sv * f, sh=p.sh * f, sd=p.sd * f, ss=p.ss * f, c=p.c * f)
    return g.p


def _c(g):
    return g.W / 2, axis(g.p)


def rot(pts, cx, cy, quarter):
    """Points turned by quarter * 90 degrees about (cx, cy), exactly."""
    out = []
    for x, y in pts:
        dx, dy = x - cx, y - cy
        for _ in range(quarter % 4):
            dx, dy = -dy, dx
        out.append((cx + dx, cy + dy))
    return out


# --- Check marks and crosses -----------------------------------------------------

def _check_width(p):
    return fit(p, 0.68 * p.cap + 1.0 * heft(p))


def _check(g, box_=None):
    """The radical's tick and rise: a short 45-degree stroke down to the
    foot, a long 2:1 stroke up; the foot cut flat on the baseline."""
    if box_ is None:
        x0, y0, W = 0.0, 0.0, g.W
    else:
        x0, y0, W = box_
    p = g.p
    H = W / 0.8
    a = 0.3 * H                                              # the tick's height
    xb = x0 + a + p.sd / 2
    g.stroke((xb - a, y0 + a), (xb, y0), (xb + H / 2, y0 + H), start='flat', end='h')
    return (x0, y0, x0 + W, y0 + H)


@shape('✓', _check_width)
def check(g):
    heavy(g, g.W, 1.0)
    g.clip = _check(g)


@shape('✔', _check_width)
def check_heavy(g):
    heavy(g, g.W)
    g.clip = _check(g)


def _x(g, S, steep=False):
    """An X in an S square centred on the axis, its strokes cut square to
    the box's sides. ``steep``: the ballot X, one stroke at the 2:1."""
    cx, cy = _c(g)
    h = S / 2
    if steep:
        g.stroke((cx - h / 2, cy - h), (cx + h / 2, cy + h), start='h', end='h')
    else:
        g.stroke((cx - h, cy - h), (cx + h, cy + h), start='v', end='v')
    g.stroke((cx - h, cy + h), (cx + h, cy - h), start='v', end='v')
    g.clip = (cx - h, cy - h, cx + h, cy + h)


for ch, k, steep in (('✕', 1.0, False), ('✖', HEAVY, False), ('✗', 1.0, True), ('✘', HEAVY, True)):
    def fn(g, k=k, steep=steep):
        heavy(g, g.W, k)
        _x(g, g.W, steep)
    shape(ch, 'L')(fn)


@shape('❌', 'L', solid=True)                                 # (twice the stroke, by design)
def cross_mark(g):
    heavy(g, g.W, 2.0)
    _x(g, g.W)


@shape('❎', 'L', solid=True)
def neg_squared_x(g):
    """A black square, a white X cut through it."""
    cx, cy = _c(g)
    S = g.W
    k = 0.62 * S / 2
    white = ink_of(g, [[(cx - k, cy - k), (cx + k, cy + k)], [(cx - k, cy + k), (cx + k, cy - k)]])
    solid(g, Polygon(sq_pts(cx, cy, S)).difference(white))


def _cross(g, k=1.0, gap=0.0):
    """A cross of four equal arms in the box, ``gap`` (a share of the pen
    or of the box, whichever is more) white at its centre."""
    heavy(g, g.W, k)
    cx, cy = _c(g)
    h = g.W / 2
    t, th = max(g.p.sv, g.p.floor), g.sh
    if gap:
        gap = max(gap * t, 0.1 * g.W)
        for s in (-1, 1):
            g.stroke((cx + s * gap, cy, th), (cx + s * h, cy))
            g.stroke((cx, cy + s * gap, t), (cx, cy + s * h))
    else:
        g.stroke((cx - h, cy, th), (cx + h, cy))
        g.stroke((cx, cy - h, t), (cx, cy + h))


@shape('✚', 'L')
def greek_cross_heavy(g):
    _cross(g, HEAVY)


@shape('✛', 'L')
def cross_open(g):
    _cross(g, 1.0, gap=0.6)


@shape('✜', 'L')
def cross_open_heavy(g):
    _cross(g, HEAVY, gap=0.6)


# --- Asterisks and spoked forms ---------------------------------------------------

def _spokes(g, n, r0, r1, k=1.0):
    """n spokes (4: the axes, 8: axes and diagonals, 6: Arris's asterisk,
    vertical and the two diagonals) from radius r0 to r1."""
    cx, cy = _c(g)
    dirs = {4: (0, 90, 180, 270), 8: tuple(range(0, 360, 45)), 6: (45, 90, 135, 225, 270, 315)}[n]
    for a in dirs:
        u = (math.cos(math.radians(a)), math.sin(math.radians(a)))
        u = (round(u[0], 12), round(u[1], 12))
        w = k * (g.p.sv if abs(u[0]) < 1e-9 else (g.sh if abs(u[1]) < 1e-9 else g.p.sd))
        start = (cx + u[0] * r0, cy + u[1] * r0) if r0 else (cx, cy)
        g.stroke((*start, slanted(g, w, u)), (cx + u[0] * r1, cy + u[1] * r1))


HEX = (90, 270, math.degrees(math.atan2(1, 2)), 180 - math.degrees(math.atan2(1, 2)),
       180 + math.degrees(math.atan2(1, 2)), 360 - math.degrees(math.atan2(1, 2)))


@shape('✱', 'L')
def asterisk_heavy(g):
    """Six spokes, near sixty degrees apart in the figures' own directions:
    the vertical and the four shallow 2:1 slopes. Heavy, as far as the white
    between spokes (53 degrees at the narrowest) keeps half its width."""
    cx, cy = _c(g)
    R = g.W / 2
    t = min(HEAVY * g.p.sv, 0.5 * R * math.sin(math.radians(53.13)))
    k = t / g.p.sv
    for a in HEX:
        u = (math.cos(math.radians(a)), math.sin(math.radians(a)))
        r = R - t / 4 if abs(u[0]) < 1e-9 else R
        w = k * (g.p.sv if abs(u[0]) < 1e-9 else g.p.ss)
        g.stroke((cx, cy, slanted(g, w, u)), (cx + u[0] * r, cy + u[1] * r), end='flat' if abs(u[0]) < 1e-9 else 'v')
    g.clip = (cx - R, cy - R, cx + R, cy + R)


@shape('✲', 'L')
def asterisk_open(g):
    """Eight spokes from a small octagonal ring at the centre (the ring
    holds them together at every weight)."""
    cx, cy = _c(g)
    R = g.W / 2
    heavy(g, g.W, 1.0, share=0.13)
    h = max(2.2 * g.p.sv, 0.3 * g.W)                         # the ring's width
    pen(g, oct_pts(cx, cy, h), keep=0.4)
    ring(g, cx, cy, h)
    for a in range(0, 360, 45):
        u = (round(math.cos(math.radians(a)), 12), round(math.sin(math.radians(a)), 12))
        axial = abs(u[0]) < 1e-9 or abs(u[1]) < 1e-9
        r0 = h / 2 - widths(g)[0] / 2
        r1 = R - (g.p.sv / 4 if axial else 0)
        g.stroke((cx + u[0] * r0, cy + u[1] * r0), (cx + u[0] * r1, cy + u[1] * r1))
    g.clip = (cx - R, cy - R, cx + R, cy + R)


@shape('✳', 'L')
def asterisk_eight(g):
    """Eight spokes through the centre, in a pen light enough that they part
    within the inner half."""
    heavy(g, g.W, 1.0, share=0.13)
    _spokes(g, 8, 0, g.W / 2 - g.p.sv / 4)
    g.clip = (0, axis(g.p) - g.W / 2, g.W, axis(g.p) + g.W / 2)


def _teardrop(cx, cy, R, w):
    """An upward spoke: a point at the centre, widening on the 2:1 to
    half-width w, its end a chamfered flat."""
    a = OCT * 2 * w * 0.5
    y1 = cy + R
    yw = cy + 2 * w                                           # the 2:1 reaches full width here
    return [(cx, cy), (cx + w, yw), (cx + w, y1 - a), (cx + w - a, y1), (cx - w + a, y1), (cx - w, y1 - a), (cx - w, yw)]


@shape('✢', 'L', solid=True)
def teardrop_asterisk(g):
    cx, cy = _c(g)
    R = g.W / 2
    w = min(max(0.16 * R, 0.6 * g.p.sv), 0.3 * R)            # (the drop widens within its length)
    for q in range(4):
        pts = rot(_teardrop(cx, cy + 0.06 * R, R * 0.94, w), cx, cy, q)
        solid(g, pts)


def _balloons(g, filled, k):
    cx, cy = _c(g)
    R = g.W / 2
    d = 0.42 * R + 0.5 * heft(g.p)                           # a balloon's width
    pen(g, oct_pts(cx, cy, d), keep=0.4)
    for q in range(4):
        u = [(0, 1), (-1, 0), (0, -1), (1, 0)][q]
        bx, by = cx + u[0] * (R - d / 2), cy + u[1] * (R - d / 2)
        w = k * (g.p.sv if u[0] == 0 else g.sh)
        g.stroke((cx, cy, w), (bx, by))
        if filled:
            disc(g, bx, by, d)
        else:
            ring(g, bx, by, d)


@shape('✣', 'L')
def balloon_asterisk(g):
    _balloons(g, False, 1.0)


@shape('✤', 'L', solid=True)
def balloon_asterisk_heavy(g):
    _balloons(g, True, 1.6)


def club_pts(cx, cy, d, quarter=0):
    """Three discs in a trefoil, d wide each, centred on (cx, cy), its top
    turned ``quarter`` right angles (the discs' centres turn; an octagon is
    its own quarter turn)."""
    import shapely
    off = 0.5 * d
    cs = rot([(cx, cy + off * 0.75), (cx - off, cy - off * 0.35), (cx + off, cy - off * 0.35)], cx, cy, quarter)
    return shapely.union_all([Polygon(oct_pts(x, y, d)) for x, y in cs])


@shape('✥', 'L', solid=True)
def club_asterisk(g):
    """Four light spokes, each ending in a club's trefoil."""
    cx, cy = _c(g)
    R = g.W / 2
    heavy(g, g.W, 1.0, share=0.12)
    d = 0.28 * R
    for q in range(4):
        u = [(0, 1), (-1, 0), (0, -1), (1, 0)][q]
        bx, by = cx + u[0] * (R - 0.8 * d), cy + u[1] * (R - 0.8 * d)
        g.stroke((cx, cy, g.p.sv if u[0] == 0 else g.sh), (bx, by))
        tre = club_pts(bx, by, d, q)
        solid(g, tre)


# --- Stars --------------------------------------------------------------------------

def star4_pts(cx, cy, R):
    """Four points on the axes, their sides on the 2:1 (inner corners a
    third of the way out)."""
    r = R / 3
    return [(cx, cy + R), (cx + r, cy + r), (cx + R, cy), (cx + r, cy - r), (cx, cy - R), (cx - r, cy - r),
            (cx - R, cy), (cx - r, cy + r)]


@shape('✦', 'L', solid=True)
def star4_black(g):
    cx, cy = _c(g)
    solid(g, star4_pts(cx, cy, g.W / 2))


@shape('✧', 'L')
def star4_white(g):
    cx, cy = _c(g)
    pts = star4_pts(cx, cy, g.W / 2)
    pen(g, pts, keep=0.5)
    outline(g, pts)


def star_pts(cx, cy, R, n, r):
    """A regular n-pointed star, outer radius R, inner r, a point up."""
    pts = []
    for i in range(2 * n):
        a = math.pi / 2 + i * math.pi / n
        q = R if i % 2 == 0 else r
        pts.append((cx + q * math.cos(a), cy + q * math.sin(a)))
    return pts


def _star5(g):
    cx, cy = _c(g)
    R = g.W / 2 / math.sin(math.radians(72))
    h = R * (1 + math.cos(math.radians(36)))                # its height: centre it on the axis
    yc = cy - h / 2 + R
    r = R * math.sin(math.radians(18)) / math.sin(math.radians(126))   # the pentagram's own
    return star_pts(cx, yc, R, 5, r)


@shape('★', 'L', solid=True)
def star_black(g):
    solid(g, _star5(g))


@shape('☆', 'L')
def star_white(g):
    pts = _star5(g)
    pen(g, pts, keep=0.35)
    outline(g, pts)


@shape('✴', 'L', solid=True)
def star8_black(g):
    cx, cy = _c(g)
    R = g.W / 2
    solid(g, star_pts(cx, cy, R, 8, 0.5 * R))


@shape('✹', 'L', solid=True)
def star12_black(g):
    cx, cy = _c(g)
    R = g.W / 2
    solid(g, star_pts(cx, cy, R, 12, 0.66 * R))


@shape('✵', 'L', solid=True)
def pinwheel(g):
    """Eight blades, each with one side on a radius and the other on 45
    degrees or the axis: inner corners at 1/sqrt2 of the radius."""
    cx, cy = _c(g)
    R = g.W / 2
    pts = []
    for k in range(8):
        a, b = math.radians(45 * k), math.radians(45 * (k + 1))
        pts.append((cx + R * math.cos(a), cy + R * math.sin(a)))
        r = R / SQRT2
        pts.append((cx + r * math.cos(b), cy + r * math.sin(b)))
    solid(g, pts)


@shape('✶', lambda p: 2 / 3 * size_of(p, 'L'), solid=True)
def star6_black(g):
    """Two 2:1 triangles, one up and one down, overlapping by half their
    height: as tall as the large shapes."""
    import shapely
    cx, cy = _c(g)
    H = g.W                                                 # each triangle as tall as wide
    up = Polygon([(cx - H / 2, cy - H / 4), (cx + H / 2, cy - H / 4), (cx, cy + 3 * H / 4)])
    dn = Polygon([(cx - H / 2, cy + H / 4), (cx, cy - 3 * H / 4), (cx + H / 2, cy + H / 4)])
    solid(g, shapely.union_all([up, dn]))


def _rect_star(cx, cy, S):
    import shapely
    sq = Polygon(sq_pts(cx, cy, S / SQRT2))
    di = Polygon([(cx, cy - S / 2), (cx + S / 2, cy), (cx, cy + S / 2), (cx - S / 2, cy)])
    return shapely.union_all([sq, di])


@shape('✷', 'M', solid=True)
def star8_rect(g):
    """A square and the same square turned 45 degrees."""
    cx, cy = _c(g)
    solid(g, _rect_star(cx, cy, g.W))


@shape('✸', 'L', solid=True)
def star8_rect_heavy(g):
    """The rectilinear star, larger."""
    cx, cy = _c(g)
    solid(g, _rect_star(cx, cy, g.W))


# --- Ornament question and exclamation marks ----------------------------------------

def ornament_pen(p):
    """(stroke, wall) of the ornament marks: Arris's mark drawn 1.6 times
    the weight's stroke, but no heavier than a fifth of the cap height where
    that is more than the weight's own (the question mark's mouth stays open), and
    never so light that the white ornament's walls (a quarter of the stroke,
    at least the floor) leave less than the floor of white inside."""
    T = min(HEAVY * p.sv, max(p.sv, 0.2 * p.cap))
    wall = max(1.12 * p.floor, 0.22 * T)                    # (the italic's shear thins a wall by up to a tenth)
    return max(T, 2 * wall + p.floor), wall


def _ornament(g, name, hollow):
    """Arris's own mark drawn heavy (its dot and gap scale with it); the
    white ornament is its outline: the heavy mark less its inside."""
    p = g.p
    T, wall = ornament_pen(p)
    k = T / p.sv
    ph = p.with_(sv=p.sv * k, sh=p.sh * k, sd=p.sd * k, ss=p.ss * k, c=p.c * k)
    sub = draw(name, ph, width=g.W)
    if not hollow:
        g.add_glyph(sub)
        return
    from ..geom import rings_to_shapely
    ink = rings_to_shapely(sub.rings())
    inside = ink.buffer(-wall, join_style='mitre')
    solid(g, ink.difference(inside))


def _q_width(p):
    T = ornament_pen(p)[0]
    return fit(p, REGISTRY['question'].width(p.with_(sv=T)))


def _ex_width(p):
    T = ornament_pen(p)[0]
    return max(T, 2 * p.floor)


@shape('❓', _q_width, solid=True)
def q_black(g):
    _ornament(g, 'question', False)


@shape('❔', _q_width)
def q_white(g):
    _ornament(g, 'question', True)


@shape('❗', _ex_width, solid=True)
def ex_black(g):
    _ornament(g, 'exclam', False)


@shape('❕', _ex_width)
def ex_white(g):
    _ornament(g, 'exclam', True)


# --- Arrows ---------------------------------------------------------------------------

def _black_arrow(g, d, head_k=1.0, shaft_k=1.0):
    """A solid arrow pointing d (0 right, 1 up, 2 left, 3 down): a shaft and
    a head whose sides run at 45 degrees to a right-angled point."""
    cx, cy = _c(g)
    L = g.W if d % 2 == 0 else (g.p.cap * 0.9 + heft(g.p))
    hh = head_k * 0.5 * min(L, size_of(g.p, 'L')) * 0.9     # half the head's height
    s = shaft_k * min(max(1.6 * g.p.sv, 0.5 * hh), 0.7 * hh) / 2   # half the shaft: a quarter to a third of the head
    s = min(s, 0.42 * hh)
    x0, x1 = cx - L / 2, cx + L / 2
    xh = x1 - hh
    pts = [(x0, cy - s), (xh, cy - s), (xh, cy - hh), (x1, cy), (xh, cy + hh), (xh, cy + s), (x0, cy + s)]
    solid(g, rot(pts, cx, cy, d))


def _arrow_width(d, head_k=1.0):
    def w(p):
        if d % 2 == 0:
            return size_of(p, 'L')
        return fit(p, head_k * 0.9 * size_of(p, 'L'))
    return w


for ch, d in (('➡', 0), ('⬆', 1), ('⬅', 2), ('⬇', 3)):
    shape(ch, _arrow_width(d), solid=True)(lambda g, d=d: _black_arrow(g, d))


@shape('➔', 'L', solid=True)
def arrow_wide(g):
    _black_arrow(g, 0, head_k=1.15, shaft_k=1.3)


@shape('➜', 'L')
def arrow_round_tip(g):
    """Heavy strokes; the head's point a bowl's chamfer (round, as
    Arris rounds: curved in the italic)."""
    heavy(g, 0.8 * g.W)
    cx, cy = _c(g)
    L = g.W
    x1 = cx + L / 2 - g.p.sv / 2
    hh = 0.36 * L
    g.stroke((cx - L / 2, cy), (x1 - g.p.sv / 2, cy))
    g.stroke((x1 - hh, cy + hh), B(x1, cy, 0.5 * g.p.sv), (x1 - hh, cy - hh), start='flat', end='flat')


@shape('➤', 'L', solid=True)
def arrowhead(g):
    """A dart: the right-pointing triangle's 2:1 sides, its back notched at
    45 degrees."""
    cx, cy = _c(g)
    S = g.W
    h = S / 2
    notch = 0.4 * h
    solid(g, [(cx - h, cy - h), (cx + h, cy), (cx - h, cy + h), (cx - h + notch, cy)])


# --- Squares, circles, boxes --------------------------------------------------------------

@shape('⬛', xl, solid=True)
def black_large_square(g):
    cx, cy = _c(g)
    block(g, cx, cy, g.W)


@shape('⬜', xl)
def white_large_square(g):
    cx, cy = _c(g)
    pts = sq_pts(cx, cy, g.W)
    pen(g, pts)
    outline(g, pts)


@shape('⬤', xl, solid=True)
def black_large_circle(g):
    cx, cy = _c(g)
    disc(g, cx, cy, g.W)


@shape('⚫', 'M', solid=True)
def medium_black_circle(g):
    cx, cy = _c(g)
    disc(g, cx, cy, g.W)


@shape('⚪', 'M')
def medium_white_circle(g):
    cx, cy = _c(g)
    pen(g, oct_pts(cx, cy, g.W))
    ring(g, cx, cy, g.W)


def _ballot_size(p):
    return fit(p, 0.86 * p.cap + 1.5 * heft(p))


def _ballot(g):
    cx, cy = _c(g)
    S = g.W
    pts = sq_pts(cx, cy, S)
    pen(g, pts, keep=0.6)
    outline(g, pts)
    tv, th, _ = widths(g)
    return cx, cy, S, tv


@shape('☐', _ballot_size)
def ballot_box(g):
    _ballot(g)


@shape('☑', _ballot_size)
def ballot_check(g):
    """The box, and a check mark inside it in a pen of its own size, its foot
    cut flat on its own line (drawn apart, so the box keeps its edges)."""
    from ..draw import Glyph
    cx, cy, S, tv = _ballot(g)
    gap = max(0.6 * tv, 0.08 * S)
    H = S - 2 * tv - 2 * gap
    sub = Glyph(g.p, W=g.W)
    heavy(sub, 0.8 * H, 1.0)
    sub.clip = _check(sub, (cx - 0.4 * H, cy - H / 2, 0.8 * H))
    g.add_glyph(sub)


@shape('☒', _ballot_size)
def ballot_x_box(g):
    from ..draw import Glyph
    cx, cy, S, tv = _ballot(g)
    gap = max(0.6 * tv, 0.08 * S)
    h = (S - 2 * tv) / 2 - gap
    sub = Glyph(g.p, W=g.W)
    heavy(sub, 2 * h, 1.0)
    sub.stroke((cx - h, cy - h), (cx + h, cy + h), start='v', end='v')
    sub.stroke((cx - h, cy + h), (cx + h, cy - h), start='v', end='v')
    sub.clip = (cx - h, cy - h, cx + h, cy + h)
    g.add_glyph(sub)


# --- Trigrams ---------------------------------------------------------------------------

def _trigram(bits):
    """Three bars, top to bottom; a broken bar (yin) for each set bit."""
    def fn(g):
        cx, cy = _c(g)
        S = g.W
        b = g.sh
        gap = max(1.1 * b, 0.13 * S)
        brk = max(1.2 * g.p.sv, 0.16 * S)
        for i in range(3):
            y = cy + (1 - i) * (b + gap)
            if bits & (1 << i):
                g.stroke((cx - S / 2, y, b), (cx - brk / 2, y))
                g.stroke((cx + brk / 2, y, b), (cx + S / 2, y))
            else:
                g.stroke((cx - S / 2, y, b), (cx + S / 2, y))
    return fn


for i in range(8):
    shape(chr(0x2630 + i), 'L')(_trigram(i))


# --- Faces --------------------------------------------------------------------------------

def _face(smile):
    def fn(g):
        cx, cy = _c(g)
        S = g.W
        pen(g, oct_pts(cx, cy, S), keep=0.7)
        tv, th, _ = widths(g)
        ring(g, cx, cy, S)
        e = max(g.p.dot(), 0.1 * S) * 0.9
        for sx in (-1, 1):
            block(g, cx + sx * 0.17 * S, cy + 0.1 * S, min(e, 0.14 * S))
        w = 0.22 * S
        y0, y1 = (cy - 0.22 * S, cy - 0.04 * S) if smile else (cy - 0.2 * S, cy - 0.06 * S)   # (clear of ring and eyes)
        leg = 0.08 * S
        if smile:
            g.stroke((cx - w, y1), B(cx - w, y0, leg), B(cx + w, y0, leg), (cx + w, y1))
        else:
            g.stroke((cx - w, y0), B(cx - w, y1, leg), B(cx + w, y1, leg), (cx + w, y0))
    return fn


shape('☺', 'L')(_face(True))
shape('☹', 'L')(_face(False))


# --- Card suits -----------------------------------------------------------------------------

def heart_pts(cx, cy, S):
    """Two octagonal lobes meeting in a 45-degree notch, sides falling at 45
    degrees to a right-angled point. (points, lobe chamfers)"""
    H = 0.9 * S
    y0, yt = cy - H / 2, cy + H / 2
    x0, x1 = cx - S / 2, cx + S / 2
    a = OCT * S / 2                                          # a lobe's corner (its own octagon's)
    n = 0.24 * S / 2                                         # the notch's depth
    pts = [(cx, y0), (x1, y0 + S / 2), (x1, yt - a), (x1 - a, yt), (cx + n, yt), (cx, yt - n),
           (cx - n, yt), (x0 + a, yt), (x0, yt - a), (x0, y0 + S / 2)]
    return pts, [(pts[2], pts[3]), (pts[7], pts[8])]


@shape('♥', 'L', solid=True)
def heart_black(g):
    cx, cy = _c(g)
    pts, ch = heart_pts(cx, cy, g.W)
    solid(g, pts, ch)


@shape('♡', 'L')
def heart_white(g):
    cx, cy = _c(g)
    pts, _ = heart_pts(cx, cy, g.W)
    pen(g, pts)
    outline(g, pts)


def _suit_diamond(g):
    cx, cy = _c(g)
    return [(cx, cy - g.W), (cx + g.W / 2, cy), (cx, cy + g.W), (cx - g.W / 2, cy)]


@shape('♦', lambda p: 0.5 * 1.25 * size_of(p, 'L'), solid=True)
def diamond_black(g):
    solid(g, _suit_diamond(g))


@shape('♢', lambda p: 0.5 * 1.25 * size_of(p, 'L'))
def diamond_white(g):
    pts = _suit_diamond(g)
    pen(g, pts)
    outline(g, pts)


def _stem_foot(g, cx, y_top, y0, S):
    """A suit's stem and its foot: a short trapezoid on the 2:1, flaring a
    tenth of the suit and two fifths of the stem each side (light at Thin)."""
    sw = max(g.p.sv, g.p.floor)
    f = 0.1 * S + 0.4 * sw
    solid(g, [(cx - f, y0), (cx + f, y0), (cx + sw / 2, y0 + 2 * (f - sw / 2)), (cx + sw / 2, y_top),
              (cx - sw / 2, y_top), (cx - sw / 2, y0 + 2 * (f - sw / 2))])


def _spade(g, black):
    cx, cy = _c(g)
    S = g.W
    body_c = cy + 0.12 * S
    pts, ch = heart_pts(cx, body_c, S * 0.92)
    pts = [(2 * cx - x, 2 * body_c - y) for x, y in pts]     # turned half round: point up
    ch = [((2 * cx - a[0], 2 * body_c - a[1]), (2 * cx - b[0], 2 * body_c - b[1])) for a, b in ch]
    y_bot = min(y for _, y in pts)
    if black:
        solid(g, pts, ch)
    else:
        pen(g, pts)
        outline(g, pts)
    notch = 2 * body_c - (body_c + 0.9 * 0.92 * S / 2 - 0.12 * 0.92 * S)   # the turned notch's point
    _stem_foot(g, cx, max(y_bot + 0.05 * S, notch + max(g.p.sv, g.p.floor)), cy - 0.6 * S, S)          # (the foot clear of the lobes)


@shape('♠', 'L', solid=True)
def spade_black(g):
    _spade(g, True)


@shape('♤', 'L', solid=True)                                  # (a solid foot)
def spade_white(g):
    _spade(g, False)


def _club(g, black):
    cx, cy = _c(g)
    S = g.W
    d = 0.48 * S
    tre = club_pts(cx, cy + 0.14 * S, d)
    if black:
        solid(g, tre)
    else:
        t = max(min(g.p.sv, 0.2 * d), g.p.floor)
        solid(g, tre.difference(tre.buffer(-t, join_style='mitre')))
    _stem_foot(g, cx, cy + 0.0 * S, cy - 0.6 * S, S)


@shape('♣', 'L', solid=True)
def club_black(g):
    _club(g, True)


@shape('♧', 'L', solid=True)                                  # (a solid foot)
def club_white(g):
    _club(g, False)


# --- Notes ---------------------------------------------------------------------------------

def _note_head(g, x, y, w):
    """A note head: a solid octagon half again as wide as it is tall."""
    pts = oct_pts(x, y, w, w / 1.35)
    solid(g, pts, oct_chords(pts))


def flag_reach(p):
    """How far a quaver's flag reaches right of its stem: far enough that
    the white under it stays wider than the stem."""
    return max(0.15 * p.cap, 1.6 * max(p.sv, p.floor))


def _notes(g, n, beams, flag=False):
    """Note heads (solid octagons, wider than tall) with stems on their right;
    a flag, or beams joining two stems' tops (each as heavy as a bar and a
    third, the white between them as wide as a beam)."""
    p = g.p
    W = g.W
    w = note_head(p) if n == 1 else min(note_head(p), 0.42 * W)   # two heads keep white between them
    hy = w / 2.7
    top = p.cap
    sv = max(p.sv, p.floor)
    xs = [w / 2] if n == 1 else [w / 2, W - w / 2]
    stems = []
    for x in xs:
        _note_head(g, x, hy, w)
        stems.append(x + w / 2 - sv / 2)
    bh = max(g.sh * 1.3, 0.09 * top)                         # a beam
    for xs_ in stems:
        g.stroke((xs_, hy, sv), (xs_, top))
    if beams:
        for i in range(beams):
            y = top - bh / 2 - i * (bh + max(0.8 * bh, 0.6 * p.m))
            g.stroke((stems[0] - sv / 2, y, bh), (stems[-1] + sv / 2, y))
    if flag:
        x = stems[0]
        f = flag_reach(p)
        g.stroke((x, top), (x + f, top - f), (x + f, top - f - 0.12 * top), end='h')


def note_head(p):
    """A note head's width (it is 1.35 times as wide as tall)."""
    return 0.55 * size_of(p, 'L') + 0.5 * heft(p)


def _note_w(n, flag=False):
    def w(p):
        head = note_head(p)
        if n == 1:
            return fit(p, head + (flag_reach(p) + max(p.sv, p.floor) / 2 if flag else 0))
        return fit(p, 2 * head + 0.25 * p.cap)
    return w


shape('♩', _note_w(1), solid=True)(lambda g: _notes(g, 1, 0))
shape('♪', _note_w(1, flag=True), solid=True)(lambda g: _notes(g, 1, 0, flag=True))
shape('♫', _note_w(2), solid=True)(lambda g: _notes(g, 2, 1))
shape('♬', _note_w(2), solid=True)(lambda g: _notes(g, 2, 2))


# --- Signs -------------------------------------------------------------------------------------

@shape('⚠', xl)
def warning(g):
    """The triangle, an exclamation mark in it."""
    cx, cy = _c(g)
    S = g.W
    pts = tri_pts(cx, cy, S, 'u')
    pen(g, pts, keep=0.55)
    outline(g, pts)
    tv, th, _ = widths(g)
    p = g.p
    y0 = cy - S / 2 + th
    s = min(max(p.sv, p.floor), 0.11 * S)
    gap = max(0.8 * s, 0.05 * S)
    yd = y0 + max(0.9 * s, 0.06 * S)
    block(g, cx, yd + s / 2, s)
    top = cy + S / 2 - 0.42 * S
    g.stroke((cx, yd + s + gap, s), (cx, top))


@shape('⚡', 'L', solid=True)
def high_voltage(g):
    """Two bands on the 2:1 joined by a step (the 2's notch), the lower one
    closing to a point on 45 degrees."""
    cx, cy = _c(g)
    u = g.W / 9
    x0, y0 = cx - 4.5 * u, cy - 6 * u
    pts = [(7, 12), (3, 12), (0, 6), (4, 6), (1, 0), (9, 8), (5, 8)]
    solid(g, [(x0 + x * u, y0 + y * u) for x, y in pts])


@shape('⚙', 'L')
def gear(g):
    """An octagonal wheel with a tooth on each of its eight sides."""
    import shapely
    cx, cy = _c(g)
    S = g.W
    tl = 0.13 * S
    Sb = S - 2 * tl
    wall = min(0.32 * Sb, max(0.18 * Sb, 1.2 * g.p.sv))
    body = Polygon(oct_pts(cx, cy, Sb))
    hole = oct_pts(cx, cy, Sb - 2 * wall)
    tw = 0.24 * Sb
    teeth = []
    for k in range(8):
        a = math.radians(45 * k)
        u = (math.cos(a), math.sin(a))
        r0, r1 = Sb / 2 - tl, Sb / 2 + tl
        teeth.append([(cx + u[0] * r0, cy + u[1] * r0, tw), (cx + u[0] * r1, cy + u[1] * r1)])
    ink = shapely.union_all([body, ink_of(g, teeth)]).difference(Polygon(hole))
    solid(g, ink, oct_chords(hole))


def _flag(g, black):
    """A pole and a flag, its fly end cut in a 45-degree swallowtail."""
    p = g.p
    sv = max(p.sv, p.floor)
    g.stroke((sv / 2, 0, sv), (sv / 2, p.cap))
    fw, fh = g.W - sv / 2, 0.42 * p.cap
    yb, yt = p.cap - fh, p.cap
    pts = [(sv / 2, yb), (fw, yb), (fw - fh / 2, (yb + yt) / 2), (fw, yt), (sv / 2, yt)]
    if black:
        solid(g, pts)
    else:
        pen(g, pts, keep=0.5)
        outline(g, pts)


def _flag_w(p):
    return fit(p, 0.6 * p.cap + max(p.sv, p.floor))


shape('⚐', _flag_w)(lambda g: _flag(g, False))
shape('⚑', _flag_w, solid=True)(lambda g: _flag(g, True))


# --- Powerline icons ------------------------------------------------------------------------------

@shape('\ue0a0', lambda p: fit(p, 0.62 * p.cap + 0.5 * heft(p)))
def pl_branch(g):
    """Version-control branch: a stem, and a branch that leaves it at 45
    degrees and rises; a square node at each end. Its pen is the weight's,
    up to a seventh of its width, so the branch stays apart from the stem."""
    p = g.p
    heavy(g, g.W, 1.0, share=0.14)
    sv = max(g.p.sv, g.p.floor)
    d = min(max(2.0 * sv, 3 * p.floor), 0.28 * g.W)
    x1, x2 = d / 2, g.W - d / 2
    top, bot = p.cap - d / 2, d / 2
    yj = 0.3 * p.cap
    yb = yj + (x2 - x1)
    g.stroke((x1, bot, sv), (x1, top))
    g.stroke((x1, yj), (x2, yb), (x2, top))
    for x, y in ((x1, bot), (x1, top), (x2, top)):
        block(g, x, y, d)


@shape('\ue0a1', lambda p: fit(p, 0.62 * p.cap + max(p.sv, p.floor)))
def pl_line_number(g):
    """'LN': a small L over a small N, stepped."""
    p = g.p
    k = 0.48
    ps = p.with_(cap=k * p.cap, m=k * p.m, sv=0.8 * p.sv, sh=0.8 * p.sh, sd=0.8 * p.sd, ss=0.8 * p.ss,
                 c=0.8 * p.c)
    wl = REGISTRY['L'].width(ps)
    wn = REGISTRY['N'].width(ps)
    sub = draw('L', ps, width=wl)
    g.add_glyph(sub, 0, p.cap - ps.cap)
    sub = draw('N', ps, width=wn)
    g.add_glyph(sub, g.W - wn, 0)


@shape('\ue0a2', lambda p: fit(p, 0.62 * p.cap + 0.5 * heft(p)), solid=True)
def pl_lock(g):
    """A padlock: a shackle with chamfered shoulders, narrower than the body,
    over a solid body with a keyhole cut in it. The shackle's pen is the
    weight's, up to a seventh of the width, so its counter stays open."""
    p = g.p
    W = g.W
    body_top = 0.52 * p.cap
    sv0 = p.sv
    heavy(g, W, 1.0, share=0.14)
    t = max(g.p.sv, g.p.floor)
    m = 0.14 * W
    g.stroke((m + t / 2, body_top), B(m + t / 2, p.cap - g.sh / 2, 0.3 * (W - 2 * m)),
             B(W - m - t / 2, p.cap - g.sh / 2, 0.3 * (W - 2 * m)), (W - m - t / 2, body_top))
    kw = max(0.9 * t, 0.12 * W, 0.6 * sv0, 2 * p.floor)        # (a keyhole three fifths of a stem wide at least)
    key = box(W / 2 - kw / 2, 0.14 * p.cap, W / 2 + kw / 2, 0.36 * p.cap)
    solid(g, box(0, 0, W, body_top).difference(key))
