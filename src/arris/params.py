"""Design parameters.

Every outline is a function of these numbers. ``HERITAGE`` reproduces the
watch's Chamfer figures in module units (a module is one pixel of the 9x12
zone masters). Font instances use 60 units per module, so the cap height is
720 units of a 1000-unit em and the heritage Bold stem is 120.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field, fields, replace

SQRT2 = math.sqrt(2)

# Arris Mono's cell, in modules: ten at every weight, so Regular, Bold and
# Black text keep one grid (the cell had followed the figures, which widen
# with the weight: 528 units at Thin to 682 at Black, and a Bold word pushed
# a Regular line off it). A glyph is drawn in the body: the proportional
# figures' at that weight, kept between nine modules (a module of margin,
# as at the Regular) and nine and a half (half a module, at Bold and up).
MONO_CELL = 10.0
MONO_BODY = (9.0, 9.5)
# Arris Mono Narrow: the same cell, its letters and figures in a body of
# this many modules at every weight, so a fifth of the cell or more is white
# (Arris Mono's leaves a tenth at Regular, a twentieth at Bold; Fira Code a
# quarter); a letter wider by nature (m w M W) keeps its own width, up to
# Arris Mono's widest body, so its counters stay open (draw.body_width)
MONO_NARROW = 7.8


@dataclass(frozen=True)
class Params:
    m: float = 60.0            # module
    cap: float = 720.0         # cap and figure height (12 modules)
    xh: float = 540.0          # x-height (9 modules)
    asc: float = 780.0         # ascender of b d h k l (13 modules, a module above the caps)
    desc: float = 180.0        # descender depth of g j p q y: 3 modules, deeper from Bold (descender_line)
    deep: float = 250.0        # the font's descent (font.Metrics.desc): the deepest a letter draws
    sv: float = 120.0          # vertical stem
    sh: float = 120.0          # horizontal stroke
    sd: float = 120.0 / SQRT2  # 45-degree stroke, measured perpendicular
    ss: float = 120.0 * 2 / math.sqrt(5)  # 2:1 stroke, measured perpendicular
    leg: float = 90.0          # bowl corner: centreline chamfer leg
    c: float = 30.0            # edge break on every right-angled corner
    fig_w: float = 540.0       # tabular figure body (9 modules)
    fig_adv: float = 600.0     # tabular figure advance (10 modules)
    mono: bool = False         # monospaced: every glyph on one cell (MONO_CELL), whatever the weight
    narrow: bool = False       # Arris Mono Narrow: the Mono's cell, its letters in MONO_NARROW modules
    wide: float = 1.0          # Mono Narrow: Arris Mono's body at this weight over the narrow one, a wide letter's (draw.body_width)
    cursive: bool = False      # Mono's italic with ss04's cursive letters (italic_forms.MONO_CURSIVE)
    plain: bool = False        # the italic drawn with the upright's letters, slanted (Mono's, in a sign set from letters)
    grade_k: float = 1.0       # grade: strokes scaled by this, widths and spacing untouched
    light: float = 1.0         # strokes lightened by this (draw._lightened): the weight's own are these over it
    unlit: 'Params | None' = field(default=None, compare=False, repr=False)   # the parameters lightened (draw._lightened)
    grad: float = 0.0          # the grade itself (GRAD), for the lighter weights of the same cut (draw._lighter)
    slant: float = 0.0         # italic: tan of the slant (outlines are sheared when built)
    floor: float = 0.0         # no stroke drawn thinner (instances.stroke_floor); 0 for the heritage
    raw: tuple | None = None   # (sv, sh, sd, ss) before the floor, where it raised them
    pregrade: tuple | None = field(default=None, compare=False, repr=False)   # a grade's strokes and break before it: (sv, sh, sd, ss, c) (ungraded)
    optical: float = 1.0       # share of the optical corrections (draw.OPTICAL): 1 measured optics, 0 the watch's own drawing
    view_cap: float = 0.0      # the cap height text is read at (0: cap); a set drawn smaller keeps its font's

    def with_(self, **kw) -> 'Params':
        """These parameters with some changed. Strokes never drop below the
        floor: every derived set (small figures, small capitals, the letters
        inside a ring, a grade) is clamped as it is made, so the geometry
        that places strokes and the strokes themselves agree."""
        strokes = ('sv', 'sh', 'sd', 'ss')
        kw.setdefault('unlit', None)                      # a set derived from lightened parameters is not their weight's
        if 'pregrade' not in kw and any(f in kw for f in (*strokes, 'c')):
            kw['pregrade'] = None                         # restroked: no longer that grade of those strokes
        if 'cap' in kw and 'view_cap' not in kw:          # a set drawn at another size is still read at the font's
            kw['view_cap'] = self.view_cap or self.cap
        before = dict(zip(strokes, self.raw)) if self.raw else {f: getattr(self, f) for f in strokes}
        before.update({f: kw[f] for f in strokes if f in kw})
        p = replace(self, **kw, raw=None)
        if kw.get('mono') and not self.mono:                # turning monospaced: Mono's one cell (MONO_CELL)
            lo, hi = MONO_BODY
            p = replace(p, fig_adv=MONO_CELL * p.m, fig_w=min(max(p.fig_w, lo * p.m), hi * p.m))
        if p.mono and p.narrow and not (self.mono and self.narrow):   # turning narrow: the narrow body,
            p = replace(p, wide=p.fig_w / (MONO_NARROW * p.m), fig_w=MONO_NARROW * p.m)   # the Mono's for the wide letters
        if p.floor and min(before.values()) < p.floor:
            p = replace(p, raw=tuple(before[f] for f in strokes),
                        **{f: max(before[f], p.floor) for f in strokes})
        else:
            p = replace(p, **before)
        return p

    def same(self, other: 'Params') -> bool:
        """Whether these are the other's parameters, to the last bits of
        the arithmetic: a set scaled and scaled back (a grade's ungraded
        self: strokes times k, over k) is the set it came from. Read exactly,
        it was not (sd one unit in the last place off at SemiBold, grade
        -100), and nothing that asks whose parameters these are (draw._cut)
        knew it for a font's own."""
        for f in fields(self):
            if not f.compare:
                continue
            a, b = getattr(self, f.name), getattr(other, f.name)
            if a == b:
                continue
            xs, ys = (a, b) if isinstance(a, tuple) and isinstance(b, tuple) and len(a) == len(b) else ((a,), (b,))
            if not all(isinstance(x, float) and isinstance(y, (float, int)) and math.isclose(x, y, rel_tol=1e-9, abs_tol=1e-9)
                       for x, y in zip(xs, ys)):
                return False
        return True

    def dot(self) -> float:
        """A dot's size (a period, a tittle, a dieresis, a comma's head): the
        stem's square, but never less than twice the stroke floor, so dots
        still read at the lightest weights. In the monospaced cut, where code
        turns on . , : ; and their dots sit alone in a cell, they are half as
        big again at Regular, easing to a fifth more at Black (a dot looks
        lighter than a stroke of its width)."""
        s = max(self.sv, 2 * self.floor)
        if self.mono:
            heavy = min(max((self.sv - 120.0) / 55.0, 0.0), 1.0)
            s = max(self.sv * (1.5 - 0.3 * heavy), 2 * self.floor)
        return s

    def scaled(self, k: float) -> 'Params':
        keep = ('mono', 'narrow', 'cursive', 'plain', 'grade_k', 'grad', 'slant', 'raw', 'light', 'unlit', 'pregrade')
        out = Params(**{f: (getattr(self, f) * k if f not in keep else getattr(self, f)) for f in self.__dataclass_fields__})
        return replace(out, raw=tuple(v * k for v in self.raw) if self.raw else None,
                       pregrade=tuple(v * k for v in self.pregrade) if self.pregrade else None)

    def ungraded(self) -> 'Params':
        k = self.grade_k
        if self.pregrade:
            # the strokes the grade was made from, themselves: times k and
            # over k again is not the same number (sd one unit in the last
            # place off at SemiBold, grade -100), and a drawing that turns
            # on a threshold there took another width (⇿ 85 units)
            sv, sh, sd, ss, c = self.pregrade
            return self.with_(sv=sv, sh=sh, sd=sd, ss=ss, c=c, grade_k=1.0, grad=0.0, pregrade=None)
        if k == 1.0:
            # a grade that leaves the strokes as they are (a positive grade at
            # Black: instances.GRAD_TAPER) is still a grade: the lighter
            # weights of its cut are graded (draw._lighter reads grad)
            return self.with_(grad=0.0) if self.grad else self
        sv, sh, sd, ss = self.raw if self.raw else (self.sv, self.sh, self.sd, self.ss)
        return self.with_(sv=sv / k, sh=sh / k, sd=sd / k, ss=ss / k, c=self.c / k, grade_k=1.0, grad=0.0)


def white_floor(m: float, sv: float) -> float:
    """The least white between two parts of a letter: a module, or 0.6 of
    a stem toward Black (letterframe.least_white)."""
    return max(m, 0.6 * sv)


def descender_line(base: Params, sv: float, sh: float) -> float:
    """How deep a weight's descenders go, all of them: three modules, or
    what the g's hook needs under its bowl, a horizontal and the least
    white over it, down to the font's descent. One line a weight: the g
    and y had gone deeper alone from Bold (their hooks making room, 205
    units at Bold and 250 at Black) and left p q j at 180, so a line of
    text stood on two descender lines."""
    return min(base.deep, max(base.desc, sh + white_floor(base.m, sv)))


def outer_leg(p: Params, sv: float | None = None, sh: float | None = None) -> float:
    """Outer chamfer leg of a bowl corner between a vertical and a horizontal."""
    sv = p.sv if sv is None else sv
    sh = p.sh if sh is None else sh
    return p.leg + (sv + sh) / 2 - p.sd / SQRT2


def inner_leg(p: Params, sh: float | None = None) -> float:
    sh = p.sh if sh is None else sh
    return max(p.c, p.leg - (p.sv + sh) / 2 + p.sd / SQRT2)


# The watch figures, in modules: two-module strokes; every diagonal as wide
# across as a stem (so 45-degree strokes are only 1/sqrt2 of it), 1.5-module
# bowl legs, half-module edge breaks.
HERITAGE = Params(m=1, cap=12, xh=9, asc=13, desc=3, deep=250 / 60, sv=2, sh=2, sd=SQRT2,
                  ss=4 / math.sqrt(5), leg=1.5, c=0.5, fig_w=9, fig_adv=10, optical=0.0)
HERITAGE_UNITS = HERITAGE.scaled(60)
