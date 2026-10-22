"""The italic's own lowercase: cursive forms in Arris's vocabulary.

The italic (``arris.italic``) curves every chamfer and slants the outline.
These drawings give it a hand as well, from moves the upright already makes:

* **Entry**: the 1's flag, a 45-degree lead-in to the top of a stem
  (i j m n p r u y), and on ascenders (b h k l).
* **Exit**: the t's foot, a stem turning right on the baseline
  (a d h i m n u); curved by the italic, it is the exit stroke of a hand.
* **Branching**: arches spring from lower on the stem than the upright's
  notched shoulders, as a pen leaves a stem.
* **Cursive forms**: the single-storey a, the descending f, the looped k,
  the y that is a u running on into its descender, the s whose spine is a
  diagonal with the 2's notch, the e whose bar is a diagonal and which
  leaves on an upstroke.

The monospaced italic keeps the upright forms: a cell has no room for a
tail.
"""
from __future__ import annotations

from ..draw import AUTO_SHARE, REGISTRY, B, Opening, _counter_white, glyph
from ..params import SQRT2
from .figures import jog
from .letterframe import Frame, letter_width, white_scale
from .lower import _dot, shoulder

TAIL = 1.75      # modules of white an exit tail reaches past its stem
FLAG = 1.5       # modules an entry flag reaches left of its stem (and down)
BRANCH = 3       # modules below the arch where an italic shoulder leaves its stem


def ital(name, wm, stems, width=None, openings=()):
    """An italic drawing of ``name`` (``draw`` uses it wherever p.slant)."""
    def deco(fn):
        def wrapped(g):
            if g.p.mono:                                    # the cell keeps the upright form
                return REGISTRY[name].fn(g)
            return fn(g)
        glyph(f'{name}.ital', None, width or letter_width(wm, stems), kind=REGISTRY[name].kind,
              openings=openings)(wrapped)
        return fn
    return deco


def _one_counter(g):
    return _counter_white(g, 1)


def _free(g):
    """Let tails and flags run past the body (the frame clips to it): by a
    cap height either side, whatever the body (an i's is a stem wide)."""
    x0, y0, x1, y1 = g.clip
    g.clip = (x0 - g.p.cap, y0, x1 + g.p.cap, y1)


def _reach(p, modules):
    return modules * p.m * white_scale(p)


def entry(g, f, xs, top=None):
    """The 1's flag at the top of a stem standing at xs: a 45-degree stroke
    whose upper edge continues the stem's cut top-left corner, ending
    square FLAG modules down. The stem keeps its flat top (on the x-height,
    or ``top``)."""
    p = g.p
    top = p.xh if top is None else top
    k = p.sd / SQRT2
    a = xs - p.sv / 2 + p.c - top + k                       # centreline: x - y = a
    yf = top - _reach(p, FLAG) - p.sv / 2
    g.stroke((xs, xs - a), (yf + a, yf), start='v', end='h')


def tail(g, f, xs, y=None):
    """Points that end a stem on the baseline with the t's foot: a corner
    and a short stroke to the right."""
    p = g.p
    yb = f.Y(1) if y is None else y
    return [B(xs, yb), tail_end(g, f, xs, yb)]


def tail_end(g, f, xs, y=None):
    """Where an exit tail from a stem at xs ends."""
    p = g.p
    return (xs + p.sv / 2 + _reach(p, TAIL), f.Y(1) if y is None else y)


# --- Stems, entries and exits ------------------------------------------------

@ital('dotlessi', 2, 1, width=lambda p: p.sv)
def dotlessi_ital(g):
    f = Frame(g, 2, 'lower')
    _free(g)
    g.stroke(f.P(1, 9), *tail(g, f, f.X(1)))
    entry(g, f, f.X(1))


@ital('i', 2, 1, width=lambda p: p.sv)
def i_ital(g):
    f = Frame(g, 2, 'asc', top=g.p.asc + g.p.sv)
    _free(g)
    g.stroke(f.P(1, 9), *tail(g, f, f.X(1)))
    entry(g, f, f.X(1))
    _dot(g, f, f.X(1))


@ital('j', 6, 1)
def j_ital(g):
    from .figures import beak_depth
    f = Frame(g, 6, 'asc', top=g.p.asc + g.p.sv)
    p = f.p
    _free(g)
    g.stroke(f.P(5, 9), B(*f.P(5, -2)), B(*f.P(1, -2)), (f.X(1), -p.desc + beak_depth(p)))
    entry(g, f, f.X(5))
    _dot(g, f, f.X(5))


@ital('l', 6, 1)
def l_ital(g):
    f = Frame(g, 6, 'asc')
    _free(g)
    g.defaults_used['stem'] = f.X(2)
    g.stroke(f.P(2, 13), *tail(g, f, f.X(2)))
    entry(g, f, f.X(2), g.p.asc)


@ital('n', 8, 2)
def n_ital(g):
    f = Frame(g, 8, 'lower')
    _free(g)
    xs, xr = f.X(1), f.X(7)
    g.stroke(f.P(1, 0), f.P(1, 9))
    entry(g, f, xs)
    arch, cut = shoulder(g, f, xs, xr, drop=BRANCH)
    g.stroke(*arch, *tail(g, f, xr), start=cut)


@ital('m', 12, 3)
def m_ital(g):
    f = Frame(g, 12, 'lower')
    _free(g)
    x1, x2, x3 = f.X(1), f.X(6), f.X(11)
    g.stroke(f.P(1, 0), f.P(1, 9))
    entry(g, f, x1)
    arch, cut = shoulder(g, f, x1, x2, drop=BRANCH)
    g.stroke(*arch, (x2, 0), start=cut)
    arch, cut = shoulder(g, f, x2, x3, drop=BRANCH)
    g.stroke(*arch, *tail(g, f, x3), start=cut)


@ital('h', 8, 2)
def h_ital(g):
    f = Frame(g, 8, 'asc')
    _free(g)
    xs, xr = f.X(1), f.X(7)
    g.stroke(f.P(1, 0), f.P(1, 13))
    entry(g, f, xs, g.p.asc)
    arch, cut = shoulder(g, f, xs, xr, drop=BRANCH)
    g.stroke(*arch, *tail(g, f, xr), start=cut)


@ital('r', 8, 1)
def r_ital(g):
    f = Frame(g, 8, 'lower')
    _free(g)
    xs = f.X(1)
    g.stroke(f.P(1, 0), f.P(1, 9))
    entry(g, f, xs)
    p = g.p
    k = p.sd / SQRT2
    y8, y5 = f.Y(8), f.Y(8 - BRANCH)
    x0 = xs + p.sv / 2 + k - p.c
    g.stroke((x0, y5), (x0 + (y8 - y5), y8), f.P(8, 8), start='h')


@ital('u', 8, 2)
def u_ital(g):
    f = Frame(g, 8, 'lower')
    _free(g)
    xl, xr = f.X(1), f.X(7)
    # the bowl's foot runs on under the right stem into the exit, as a hand writes a u
    g.stroke(f.P(1, 9), B(*f.P(1, 1)), tail_end(g, f, xr))
    entry(g, f, xl)
    g.stroke(f.P(7, 9), f.P(7, 1))


@ital('a', 8, 2)
def a_ital(g):
    """The single-storey a: the d's bowl on a stem that stops at the
    x-height and leaves on the t's foot."""
    f = Frame(g, 8, 'lower')
    _free(g)
    g.stroke(f.P(7, 9), *tail(g, f, f.X(7)))
    g.stroke(f.P(7, 8), B(*f.P(1, 8)), B(*f.P(1, 1)), f.P(7, 1), closed=True)


@ital('d', 8, 2)
def d_ital(g):
    f = Frame(g, 8, 'asc')
    _free(g)
    g.stroke(f.P(7, 13), *tail(g, f, f.X(7)))
    g.stroke(f.P(7, 8), B(*f.P(1, 8)), B(*f.P(1, 1)), f.P(7, 1), closed=True)


@ital('b', 8, 2)
def b_ital(g):
    f = Frame(g, 8, 'asc')
    _free(g)
    g.stroke(f.P(1, 13), f.P(1, 0))
    entry(g, f, f.X(1), g.p.asc)
    g.stroke(f.P(1, 8), B(*f.P(7, 8)), B(*f.P(7, 1)), f.P(1, 1), closed=True)


@ital('p', 8, 2)
def p_ital(g):
    f = Frame(g, 8, 'lower')
    _free(g)
    g.stroke(f.P(1, 9), f.P(1, -3))
    entry(g, f, f.X(1))
    g.stroke(f.P(1, 8), B(*f.P(7, 8)), B(*f.P(7, 1)), f.P(1, 1), closed=True)


@ital('f', 7, 1)
def f_ital(g):
    """The stem runs on below the baseline and turns back, the top's hook
    turned over."""
    f = Frame(g, 7, 'asc')
    g.clip = (-f.W, -g.p.desc, 2 * f.W, g.p.asc)
    g.stroke(f.P(7, 12), B(*f.P(3.5, 12)), B(*f.P(3.5, -2)), f.P(0, -2))
    g.stroke(f.P(0.5, 8), f.P(6.5, 8))


# --- Cursive forms ---------------------------------------------------------

@ital('k', 8, 1, openings=[Opening(_one_counter, 'loop', lambda p: 3.0, max_ratio=AUTO_SHARE)])
def k_ital(g):
    """The looped k: the arm closes into a small bowl on the stem, and the
    leg leaves the bowl's foot at 45 degrees. At heavy weights the loop
    reaches lower so it stays open."""
    f = Frame(g, 8, 'asc')
    _free(g)
    p = g.p
    xs = f.X(1)
    g.stroke(f.P(1, 13), f.P(1, 0))
    entry(g, f, xs, p.asc)
    ylo = f.Y(g.free('loop', 4.0))
    arch, cut = shoulder(g, f, xs, f.X(6.5), drop=BRANCH)
    g.stroke(*arch, B(f.X(6.5), ylo), (xs, ylo), start=cut)
    x0 = f.X(3.5)
    g.stroke((x0, ylo), (x0 + ylo, 0), start='h', end='h')


@ital('y', 8, 2)
def y_ital(g):
    """A u whose right stem runs on into the descender, as the g's."""
    f = Frame(g, 8, 'lower')
    _free(g)
    g.stroke(f.P(1, 9), B(*f.P(1, 1)), f.P(7, 1))
    entry(g, f, f.X(1))
    g.stroke(f.P(7, 9), B(*f.P(7, -2)), f.P(1, -2))


@ital('s', 8, 2)
def s_ital(g):
    """The spine a 45-degree diagonal with the 2's notch, from a corner at
    the top left to one at the bottom right."""
    f = Frame(g, 8, 'lower')
    p = g.p
    xl, xr = f.X(1), f.X(7)
    yt, yb = f.Y(8), f.Y(1)
    J = jog(p)
    run = (xr - xl - J) / 2                                 # each half of the spine, across and down
    ymid = (yt + yb) / 2
    y_hi, y_lo = ymid + run, ymid - run
    x1 = xl + run
    g.stroke((f.X(8), yt), B(xl, yt), (xl, y_hi), (x1, ymid, min(J, g.sh)), (x1 + J, ymid),
             (xr, y_lo), B(xr, yb), (f.X(0), yb))


@ital('e', 8, 2, openings=[Opening(_one_counter, 'bar', lambda p: 0.6, max_ratio=AUTO_SHARE)])
def e_ital(g):
    """The cursive e: its bar a 45-degree stroke rising from the left side
    into the top right corner, the eye the triangle above it; the lower arm
    leaves on a 45-degree upstroke, a hand's exit. At heavy weights the bar
    thins so the eye stays open."""
    f = Frame(g, 8, 'lower')
    _free(g)
    p = g.p
    xl, xr = f.X(1), f.X(7)
    yt = f.Y(8)
    g.stroke((xl, yt - (xr - xl), p.sd * g.free('bar', 1.0)), (xr, yt))
    L = _reach(p, FLAG)
    g.stroke((xr, yt), B(xl, yt), B(xl, f.Y(1)), (f.X(6), f.Y(1)), (f.X(6) + L, f.Y(1) + L), end='h')


@ital('ae', 14, 3, width=lambda p: REGISTRY['a.ital'].width(p) + REGISTRY['e.ital'].width(p) - p.sv,
      openings=[Opening(lambda g: _counter_white(g, 2), 'bar', lambda p: 0.6, max_ratio=AUTO_SHARE)])
def ae_ital(g):
    """The single-storey a and the cursive e on one stem: the a's bowl on
    its left, the e's eye and exit on its right."""
    f = Frame(g, 14, 'lower')
    _free(g)
    p = g.p
    xl, xm, xr = f.X(1), f.X(7), f.X(13)
    yt = f.Y(8)
    g.stroke(f.P(7, 8), B(*f.P(1, 8)), B(*f.P(1, 1)), f.P(7, 1), closed=True)
    g.stroke((xm, yt - (xr - xm), p.sd * g.free('bar', 1.0)), (xr, yt))
    L = _reach(p, FLAG)
    g.stroke((xr, yt), B(xm, yt), B(xm, f.Y(1)), (f.X(12), f.Y(1)), (f.X(12) + L, f.Y(1) + L), end='h')


# --- Cyrillic italic ---------------------------------------------------------
# Cyrillic italics are cursive in their own way: и is written as a u, п as an
# n, т as an m, д as a g; ш, щ and ц are u's with more stems or a descender.
# (а е р у come through their Latin forms already.)

def _as(name, latin):
    spec = REGISTRY[f'{latin}.ital'] if f'{latin}.ital' in REGISTRY else REGISTRY[latin]
    upright = REGISTRY[name]

    def fn(g, spec=spec, upright=upright):
        if g.p.mono:
            return upright.fn(g)
        return spec.fn(g)
    glyph(f'{name}.ital', None, spec.width, kind=upright.kind)(fn)


for _cy, _lat in (('uni0438', 'u'), ('uni043F', 'n'), ('uni0442', 'm'), ('uni0434', 'g')):
    _as(_cy, _lat)


def _u_stems(g, f, xs, descender):
    """A u of several stems: the first with the 1's flag, each joined to the
    next by a bowl corner on the baseline; the last leaves on the t's foot
    or runs into a descender's tick."""
    if descender:
        # a small corner into the tick, so the foot stays straight past the last stem
        g.stroke(f.P(xs[0], 9), B(*f.P(xs[0], 1)), B(*f.P(xs[-1] + 1.5, 1), g.p.m / 2), f.P(xs[-1] + 1.5, -2))
    else:
        g.stroke(f.P(xs[0], 9), B(*f.P(xs[0], 1)), tail_end(g, f, f.X(xs[-1])))
    entry(g, f, f.X(xs[0]))
    for x in xs[1:]:
        g.stroke(f.P(x, 9), f.P(x, 1))


@ital('uni0448', 12, 3)
def sha_ital(g):
    f = Frame(g, 12, 'lower')
    _free(g)
    _u_stems(g, f, (1, 6, 11), False)


@ital('uni0449', 12, 3)
def shcha_ital(g):
    f = Frame(g, 12, 'lower')
    _free(g)
    _u_stems(g, f, (1, 6, 11), True)


@ital('uni0446', 8, 2)
def tse_ital(g):
    f = Frame(g, 8, 'lower')
    _free(g)
    _u_stems(g, f, (1, 7), True)
