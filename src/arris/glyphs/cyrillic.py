"""Cyrillic.

Shared forms are the Latin glyphs under more code points (``ALIASES``).
New capitals are drawn on the capital grid with the same moves: the 3 with
the 2's beak (Ze), gable bends (El, De), the mirrored R (Ya), beaked bowls
round a bar (E, Ukrainian Ye), K's junction twice (Zhe), the figures' bowls
on stems (Be, Che, soft and hard signs, Yeru).

Most lowercase Cyrillic is a small capital: the capital's construction
redrawn on the x-height, with the same stems and corners (``smallcap``).
The rest is drawn: be (the 6, taller), ef, and the Serbian dje and tshe.
"""
from __future__ import annotations

from shapely import affinity

from ..draw import AUTO_MIN, Opening, Squint, B, REGISTRY, draw, glyph
from ..geom import rings_to_shapely
from .caps import big
from .figures import beak_depth, jog
from .letterframe import Frame, k_arms, letter_width

ALIASES = {
    0x0410: 'A', 0x0412: 'B', 0x0415: 'E', 0x041A: 'K', 0x041C: 'M', 0x041D: 'H', 0x041E: 'O', 0x0420: 'P',
    0x0421: 'C', 0x0422: 'T', 0x0425: 'X', 0x0405: 'S', 0x0406: 'I', 0x0408: 'J',
    0x0430: 'a', 0x0435: 'e', 0x043E: 'o', 0x0440: 'p', 0x0441: 'c', 0x0443: 'y', 0x0445: 'x',
    0x0455: 's', 0x0456: 'i', 0x0458: 'j', 0x04BB: 'h',
}


def ccap(name, ch, wm, stems, width=None, squint=(), openings=()):
    return glyph(name, ch, width or letter_width(wm, stems), kind='cap', squint=squint, openings=openings)


# The soft sign's bowl sits in the lower half of the capital. Drawn small (the
# lowercase is the capital at the x-height) and heavy, its counter closes to a
# pinhole: there its top rises, as far as row 7.5, until the counter reads.
BOWL = (Squint('bowl', lambda p: 7.5),)


def mirror(g):
    """Mirror the drawn strokes left to right within the body."""
    W = g.W
    g.strokes = [type(s)(tuple(type(n)(W - n.x, n.y, n.bowl, n.w) for n in s.nodes), s.closed, s.start, s.end)
                 for s in g.strokes]


# --- Capitals ----------------------------------------------------------------

@ccap('uni0411', 'Б', 9, 2)
def Be(g):
    f = Frame(g, 9)
    g.stroke(f.P(8, 11), f.P(1, 11), f.P(1, 0))
    g.stroke(f.P(1, 6), B(*f.P(8, 6)), B(*f.P(8, 1)), f.P(1, 1), closed=True)


@ccap('uni0413', 'Г', 7, 1)
def Ge(g):
    f = Frame(g, 7)
    g.stroke(f.P(1, 0), f.P(1, 11), f.P(7, 11))


@ccap('uni0490', 'Ґ', 7, 1)
def Gheup(g):
    f = Frame(g, 7)
    p = f.p
    g.clip = (0, 0, f.W, p.cap + 2.5 * p.m)
    g.stroke(f.P(1, 0), f.P(1, 11), f.P(6, 11), (f.X(6), p.cap + 2.5 * p.m))


def _bent_leg(f, g, x_top, y_top, x_foot):
    """A stem from (x_top, y_top) that bends out at 45 degrees to land at
    x_foot on the baseline bar's centre line (the gable's bend, turned)."""
    yb = f.Y(1)
    y_bend = yb + (x_top - x_foot)
    return [(x_top, y_top), (x_top, y_bend), (x_foot, yb)]


@ccap('uni041B', '\u041b', 9, 2)
def El(g):
    f = Frame(g, 9)
    g.stroke(f.P(8, 0), f.P(8, 11), f.P(2.5, 11))
    _el_leg(g, f)


def _el_leg(g, f):
    """A stem down from the bar that bends out at 45 degrees to the baseline."""
    x0, x1 = f.X(2.5), f.X(0.5)
    y_bend = x0 - x1
    g.stroke((x0, f.Y(11)), (x0, y_bend), (x1, 0), end='h')


@ccap('uni0414', 'Д', 10, 2)
def De(g):
    f = Frame(g, 10)
    p, W = f.p, f.W
    g.clip = (0, -0.8 * p.desc, W, p.cap)
    g.stroke(f.P(2.5, 11), f.P(8, 11), f.P(8, 1))
    g.stroke(*_bent_leg(f, g, f.X(2.5), f.Y(11), f.X(1)))
    g.stroke((0, f.Y(1)), (W, f.Y(1)))
    for x in (p.sv / 2, W - p.sv / 2):
        g.stroke((x, f.Y(1)), (x, -0.8 * p.desc))


@ccap('uni0416', '\u0416', 13, 3)
def Zhe(g):
    """K's arm and leg, back to back on one stem."""
    f = Frame(g, 13)
    p, W, H = f.p, f.W, f.p.cap
    xm = W / 2
    g.stroke((xm, 0), (xm, H))
    half = W - xm + p.sv / 2                                # the K's body: stem's left edge to the right
    ox = xm - p.sv / 2
    for pts, a, b in k_arms(g, p.sv / 2, half, H, branch=True):    # two junctions would make a block
        for sign in (1, -1):
            g.stroke(*[(xm + sign * (x + ox - xm), y) for x, y in pts], start=a, end=b)


# З's, Э's and Є's bowls are open: the counter rule (closed counters) never
# lightens them, and at Black their small capitals з э є kept only slits
# between the beaks and the middle arm (solid at the heaviest grade). Their
# horizontals thin under the squint instead, as far as the counter rule's,
# a white gone altogether counting as unread (Squint.whites).
OPEN_BOWLS = (Squint('sh_auto', lambda p: AUTO_MIN, whites=True),)


@ccap('uni0417', 'З', 9, 2, squint=OPEN_BOWLS)
def Ze(g):
    """The 3 with the 2's beak on top."""
    ze_shape(g)


def ze_shape(g, foot_leg=None):
    """З. ``foot_leg``: the leg of the lower bowl's foot corners (the default:
    the parameter leg); Ҙ's drop hangs between them (cyrillic_ext.drop_leg)."""
    f = Frame(g, 9)
    p, H, d = f.p, f.p.cap, beak_depth(f.p)
    g.stroke((f.X(1), H - d), B(*f.P(1, 11)), B(*f.P(8, 11)), B(*f.P(8, 6), big(p)), f.P(3, 6))
    g.stroke(f.P(3, 6), B(*f.P(8, 6)), B(*f.P(8, 1), foot_leg), B(*f.P(1, 1), foot_leg), (f.X(1), d))


@ccap('uni0418', 'И', 10, 2, width=lambda p: REGISTRY['N'].width(p))
def Ii(g):
    REGISTRY['N'].fn(g)
    mirror(g)


@ccap('uni041F', 'П', 9, 2)
def Pe(g):
    f = Frame(g, 9)
    g.stroke(f.P(1, 0), f.P(1, 11), f.P(8, 11), f.P(8, 0))


@ccap('uni0423', 'У', 9, 2)
def U_(g):
    f = Frame(g, 9)
    p, k = f.p, f.k
    xl, xr = f.X(1), f.X(8)
    a = (xr - p.sv / 2) + f.Y(4) + p.c - k                  # x + y: the arm meets the stem at a third
    g.stroke((xl, p.cap), (xl, a - xl), (xr, a - xr))
    g.stroke(f.P(8, 12), B(*f.P(8, 1)), f.P(2, 1))


@ccap('uni0424', 'Ф', 11, 3)
def Ef(g):
    f = Frame(g, 11)
    g.stroke(B(*f.P(1, 3)), B(*f.P(10, 3)), B(*f.P(10, 9)), B(*f.P(1, 9)), closed=True)
    g.stroke((f.W / 2, 0), (f.W / 2, f.p.cap))


def _tse_foot(g, f, *stem):
    """Ц's foot: the left stem's line on along the baseline to the body's
    edge, and the descender dropped from its end. In the italic one stroke
    through a small bowl corner into the drop (the cursive ц's tick), which
    it curves; the upright's two strokes meet in an L."""
    p, W = g.p, f.W
    if p.slant:
        g.stroke(*stem, B(W - p.sv / 2, f.Y(1), p.m / 2), (W - p.sv / 2, -0.8 * p.desc))
        return
    g.stroke(*stem, (W, f.Y(1)))
    g.stroke((W - p.sv / 2, f.Y(1)), (W - p.sv / 2, -0.8 * p.desc))


@ccap('uni0426', 'Ц', 10, 2)
def Tse(g):
    f = Frame(g, 10)
    p, W = f.p, f.W
    g.clip = (0, -0.8 * p.desc, W, p.cap)
    _tse_foot(g, f, f.P(1, 12), f.P(1, 1))
    g.stroke(f.P(8, 12), f.P(8, 1))


@ccap('uni0427', 'Ч', 9, 2)
def Che(g):
    f = Frame(g, 9)
    g.stroke(f.P(1, 12), B(*f.P(1, 5)), f.P(8, 5))
    g.stroke(f.P(8, 0), f.P(8, 12))


@ccap('uni0428', 'Ш', 12, 3)
def Sha(g):
    f = Frame(g, 12)
    g.stroke(f.P(1, 12), f.P(1, 1), f.P(11, 1), f.P(11, 12))
    g.stroke((f.W / 2, f.Y(1)), (f.W / 2, f.p.cap))


@ccap('uni0429', 'Щ', 13, 3)
def Shcha(g):
    f = Frame(g, 13)
    p, W = f.p, f.W
    g.clip = (0, -0.8 * p.desc, W, p.cap)
    x3 = f.X(11)
    _tse_foot(g, f, f.P(1, 12), f.P(1, 1))
    g.stroke((x3, f.Y(1)), (x3, p.cap))
    g.stroke((f.X(6), f.Y(1)), (f.X(6), p.cap))


def _sign(g, f, x0, x1):
    """A stem at x0 carrying the lower bowl of a B out to x1 (its top at the
    free row 'bowl', BOWL)."""
    top = f.Y(g.free('bowl', 6.0))
    g.stroke((x0, 0), (x0, f.p.cap))
    g.stroke((x0, top), B(x1, top), B(x1, f.Y(1)), (x0, f.Y(1)), closed=True)


@ccap('uni042C', 'Ь', 9, 2, squint=BOWL)
def Softsign(g):
    f = Frame(g, 9)
    _sign(g, f, f.X(1), f.X(8))


@ccap('uni042A', 'Ъ', 11, 2, squint=BOWL)
def Hardsign(g):
    f = Frame(g, 11)
    g.stroke((0, f.Y(11)), (f.X(3), f.Y(11)))
    _sign(g, f, f.X(3), f.X(10))


@ccap('uni042B', '\u042b', 12, 3, squint=BOWL)
def Yeru(g):
    from ..font import light
    from .symkit import fit_inner

    def bowl(q, W):
        """Where the soft sign's bowl ends, its stem's centre at q.sv / 2:
        the separate stem stands as far from it as a letter from its
        neighbour in a word (two sidebearings), never nearer."""
        return min(q.sv / 2 + 0.7 * (W - q.sv), W - 1.5 * q.sv - 2 * light(q))
    # Mono's cell leaves the soft sign little room beside the stem
    fit_inner(g, 'uni042C', lambda q: bowl(q, g.W) + q.sv / 2)
    f = Frame(g, 12)
    p = f.p
    xs = f.X(11)
    _sign(g, f, f.X(1), bowl(p, g.W))
    g.stroke((xs, 0), (xs, p.cap))


def yat_arm(p):
    """How far yat's bar reaches each side of its stem, centre to end:
    the arm's white beside the stem stays as the stroke grows."""
    return 1.5 * p.m + p.ungraded().sv


@ccap('uni0462', 'Ѣ', 11, 2)
def Yat(g):
    """Yat: the soft sign's stem crossed by a bar in its upper half."""
    f = Frame(g, 11)
    _sign(g, f, f.X(3), f.X(10))
    arm = yat_arm(g.p)
    g.stroke((f.X(3) - arm, f.Y(9)), (f.X(3) + arm, f.Y(9)))


@ccap('uni046A', 'Ѫ', 12, 3)
def Yusbig(g):
    """Big yus: a triangle hanging point down from the top bar, its sides at
    45 degrees, its point on an arch whose legs stand on the baseline, and a
    stem from the point down the middle."""
    f = Frame(g, 12)
    g.stroke(f.P(1, 11), f.P(11, 11), f.P(6, 6), closed=True)
    g.stroke(f.P(1, 0), B(*f.P(1, 6)), B(*f.P(11, 6)), f.P(11, 0))
    g.stroke(f.P(6, 6), f.P(6, 0))


@ccap('uni042D', 'Э', 9, 2, squint=OPEN_BOWLS)
def Ereversed(g):
    f = Frame(g, 9)
    p, H, d = f.p, f.p.cap, beak_depth(f.p)
    g.stroke((f.X(1), H - d), B(*f.P(1, 11)), B(*f.P(8, 11)), B(*f.P(8, 1)), B(*f.P(1, 1)), (f.X(1), d))
    g.stroke(f.P(3, 6), f.P(8, 6))


@ccap('uni0404', 'Є', 9, 2, squint=OPEN_BOWLS)
def Eukr(g):
    REGISTRY['C'].fn(g)
    f = Frame(g, 9)
    g.stroke(f.P(1, 6), f.P(6, 6))


def _yu_gap(g):
    """The white between Ю's stem and its bowl, either side of the bar."""
    return g.defaults_used['gap']


@ccap('uni042E', 'Ю', 14, 3, openings=[Opening(_yu_gap, 'bowl', lambda p: 3 * p.m)])
def Yu(g):
    """The stem, a bar from it, and the O on the bar. The white between the
    stem and the bowl's side keeps its share of the stem (an opening: at the
    heavy weights it was a slit, filled at one weight and open at the next,
    and the variable font smeared a hairline across the weights between);
    where it would close, the bowl's left side moves in, so the O narrows a
    little rather than touch the stem."""
    f = Frame(g, 14)
    p = g.p
    xb = f.X(4) + g.free('bowl', 0.0)
    g.stroke(f.P(1, 0), f.P(1, 12))
    g.stroke(f.P(1, 6), (xb, f.Y(6)))
    g.stroke(B(xb, f.Y(1)), B(*f.P(13, 1)), B(*f.P(13, 11)), B(xb, f.Y(11)), closed=True)
    g.defaults_used['gap'] = xb - f.X(1) - p.sv


@ccap('uni042F', 'Я', 9, 2)
def Ya(g):
    """R, mirrored: the bowl on the left, the leg landing at the left."""
    REGISTRY['R'].fn(g)
    mirror(g)


@ccap('uni0402', 'Ђ', 11, 2)
def Dje(g):
    f = Frame(g, 11)
    p = f.p
    from .italic_forms import tail_run
    g.clip = (0, -p.desc, f.W, p.cap)
    g.stroke((0, f.Y(11)), (f.X(7), f.Y(11)))
    g.stroke(f.P(3, 0), f.P(3, 11))
    g.stroke(f.P(3, 6.5), B(*f.P(10, 6.5)), B(*f.P(10, -2)), (f.X(10) - tail_run(p, f.X(10) - f.X(6)), f.Y(-2)))


@ccap('uni040B', 'Ћ', 11, 2)
def Tshe(g):
    f = Frame(g, 11)
    g.stroke((0, f.Y(11)), (f.X(7), f.Y(11)))
    g.stroke(f.P(3, 0), f.P(3, 11))
    g.stroke(f.P(3, 6.5), B(*f.P(10, 6.5)), f.P(10, 0))


@ccap('uni0409', 'Љ', 14, 3, squint=BOWL)
def Lje(g):
    f = Frame(g, 14)
    p = f.p
    g.stroke(f.P(8, 0), f.P(8, 11), f.P(2.5, 11))
    _el_leg(g, f)
    row = g.free('bowl', 6.0)
    g.stroke(f.P(8, row), B(*f.P(13, row)), B(*f.P(13, 1)), f.P(8, 1), closed=True)


@ccap('uni040A', 'Њ', 14, 3, squint=BOWL)
def Nje(g):
    f = Frame(g, 14)
    g.stroke(f.P(1, 0), f.P(1, 12))
    g.stroke(f.P(1, g.free('bowl', 6.0)), f.P(8, g.free('bowl', 6.0)))   # the bar meets the bowl's top
    _sign(g, f, f.X(8), f.X(13))


@ccap('uni040F', 'Џ', 9, 2)
def Dzhe(g):
    f = Frame(g, 9)
    p = f.p
    g.clip = (0, -0.8 * p.desc, f.W, p.cap)
    g.stroke(f.P(1, 12), f.P(1, 1), f.P(8, 1), f.P(8, 12))
    g.stroke((f.W / 2, f.Y(1)), (f.W / 2, -0.8 * p.desc))


# --- Small capitals as lowercase ---------------------------------------------

SMALLCAP = {0x0431: None, 0x0432: 'B', 0x0433: 'uni0413', 0x0434: 'uni0414', 0x0436: 'uni0416',
            0x0437: 'uni0417', 0x0438: 'uni0418', 0x043A: 'K', 0x043B: 'uni041B', 0x043C: 'M', 0x043D: 'H',
            0x043F: 'uni041F', 0x0442: 'T', 0x0446: 'uni0426', 0x0447: 'uni0427', 0x0448: 'uni0428',
            0x0449: 'uni0429', 0x044A: 'uni042A', 0x044B: 'uni042B', 0x044C: 'uni042C', 0x044D: 'uni042D',
            0x044E: 'uni042E', 0x044F: 'uni042F', 0x0454: 'uni0404', 0x0491: 'uni0490', 0x0459: 'uni0409',
            0x045A: 'uni040A', 0x045F: 'uni040F', 0x046B: 'uni046A'}


def sc(p):
    """Parameters that draw a capital construction as a small capital: the
    x-height for the cap height, and the white scaled so the small H has the
    n's white (four modules for five), which puts the Cyrillic lowercase in
    the Latin lowercase's rhythm."""
    return p.with_(cap=p.xh, m=p.m * 0.8)


def smallcap(name, ch, cap_name):
    def fn(g, cap_name=cap_name):
        sub = draw(cap_name, sc(g.p), width=g.W if g.p.mono else None)
        g.add_glyph(sub)
    glyph(name, ch, lambda p, c=cap_name: REGISTRY[c].width(sc(p)), kind='lower')(fn)


for cp, cap_name in SMALLCAP.items():
    if cap_name:
        smallcap(f'uni{cp:04X}', chr(cp), cap_name)


@glyph('uni0463', 'ѣ', letter_width(11, 2), kind='lower')
def yat(g):
    """Yat: a stem rising to the ascender, crossed by a bar at the x-height,
    the soft sign's bowl below it."""
    f = Frame(g, 11, 'asc')
    x = f.X(3)
    g.stroke((x, 0), (x, f.Y(13)))
    g.stroke((x, f.Y(5)), B(f.X(10), f.Y(5)), B(f.X(10), f.Y(1)), (x, f.Y(1)), closed=True)
    arm = yat_arm(g.p)
    g.stroke((x - arm, f.Y(8)), (x + arm, f.Y(8)))


@glyph('uni0431', 'б', letter_width(8, 2), kind='lower')
def be(g):
    """The 6, its arm lifted to the ascender."""
    f = Frame(g, 8, 'asc')
    g.stroke(f.P(7, 12), B(*f.P(1, 12)), f.P(1, 5))
    g.stroke(f.P(1, 5), B(*f.P(7, 5)), B(*f.P(7, 1)), B(*f.P(1, 1)), closed=True)


@glyph('uni0444', 'ф', letter_width(11, 3), kind='lower')
def ef(g):
    f = Frame(g, 11, 'lower')
    p = f.p
    g.clip = (0, -p.desc, f.W, p.asc)
    g.stroke(B(*f.P(1, 1)), B(*f.P(10, 1)), B(*f.P(10, 8)), B(*f.P(1, 8)), closed=True)
    g.stroke((f.W / 2, -p.desc), (f.W / 2, p.asc))


@glyph('uni045B', 'ћ', lambda p: REGISTRY['hbar'].width(p), kind='lower')
def tshe(g):
    REGISTRY['hbar'].fn(g)


@glyph('uni0452', 'ђ', lambda p: REGISTRY['hbar'].width(p), kind='lower')
def dje(g):
    """tshe, its right stem running down into a hook."""
    from .extra_latin import stamp
    p = g.p
    w = stamp(g, 'eng', p.m, width=g.W - p.m)
    g.stroke((0, (p.xh + p.asc) / 2 + p.m / 2), (p.m + p.sv + 2 * p.m, (p.xh + p.asc) / 2 + p.m / 2))
    g.stroke((p.m + p.sv / 2, p.xh - g.sh), (p.m + p.sv / 2, p.asc))   # overlapping the stem below


@ccap('uni04BA', '\u04ba', 9, 2)
def Shha(g):
    """Capital shha: the h at capital height."""
    f = Frame(g, 9)
    g.stroke(f.P(1, 0), f.P(1, 12))
    g.stroke(f.P(1, 6.5), B(*f.P(8, 6.5)), f.P(8, 0))
