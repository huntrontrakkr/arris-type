"""Parameters as functions of the design axes.

Axes:
  wght  100-900  stem weight; the watch's heritage weight is Arris Watch's
                 SemiBold (STEMS, WATCH_STEMS; Arris Mono's: MONO_STEMS)
  GRAD  -100-100 grade: strokes up to a fifth thinner or thicker in the same
                 widths and spacing, for light-on-dark text (docs/DESIGN.md);
                 a positive grade fades out toward Black (GRAD_TAPER)
  WTCH  0-100    the watch's stroke balance (docs/DESIGN.md); past Bold it
                 eases off toward Black (WATCH_TAPER)

Everything optical (stroke ratios by direction, edge breaks, overshoots) is
derived here from the stem and the correction constants in ``OPTICS``, which
docs/research/ explains.
"""
from __future__ import annotations

from dataclasses import dataclass

from .params import SQRT2, Params, descender_line, white_own

# Vertical stem (font units, 1000 UPM, cap height 720) at the named weights (STEMS, WATCH_STEMS below).
# Stem / cap on the watch's ladder: Regular 0.125, SemiBold 0.167 (the watch's figures), Bold 0.194,
# Black 0.243; on Arris's, Bold 0.181 and Black 0.219. Measured neutral sans faces run 0.128 Regular
# and 0.227 Bold, chamfered ones 0.122 and 0.197 (docs/research/reference-fonts.md).
# Arris Mono ships Fira Code's six weights, Light to Bold with Fira's Retina (450, a Regular a little
# heavier for light text on high-density screens), each with its italic (the owner, 2026-11-02). The
# engine still draws Mono at any weight; the build makes these.
MONO_NAMES = {300: 'Light', 400: 'Regular', 450: 'Retina', 500: 'Medium', 600: 'SemiBold', 700: 'Bold'}
MONO_WEIGHTS = tuple(MONO_NAMES)
# Arris Mono Narrow draws each weight from Regular up this much lighter than its name says: in a
# terminal, light on dark, its Regular then puts as much ink in a cell as Fira Code's Regular (0.33 of
# the x-height band against Fira's 0.32; drawn at 400, 0.37). Its Light keeps its own weight: at 14 px
# a lighter m's middle stem and the periods already go grey (the owner, 2026-11-05).
NARROW_LIGHTER = 50


def narrow_weight(wght: float) -> float:
    """The weight Arris Mono Narrow draws a weight at (NARROW_LIGHTER), as
    the engine is asked for it (mono_weight)."""
    return mono_weight(wght if wght <= MONO_WEIGHTS[0] else max(MONO_WEIGHTS[0], wght - NARROW_LIGHTER))


def mono_weight(wght: float) -> float:
    """The weight of Arris that has the stem Arris Mono draws a weight with
    (MONO_STEMS): what the engine is asked for to draw Arris Mono's
    ``wght``. To the Regular the same."""
    return _rung(STEMS, _ladder(MONO_STEMS, wght))


# The watch's own weights: the stems the design was drawn on, its figures' at SemiBold (two modules).
# Arris Watch and the watch's end of the variable font (WTCH 100) keep them, and every rule of the engine
# that names a weight means one of these (``drawn``): the measured optics' ends, the weight a cut's forms
# are chosen at, the weights a heavier one is held against.
WATCH_STEMS = {100: 24, 200: 44, 300: 66, 400: 90, 500: 105, 600: 120, 700: 140, 800: 158, 900: 175}
# Arris. To the Regular the watch's; past it each weight has the stem that gives a line of its lowercase the
# colour other families' weight of that name has. Sixty grotesque, geometric and squared families were read at
# every weight they have (the ink of a line of lowercase in the band of its x-height: 2026-11-11). Their Regular
# stands at 0.33 (the middle half 0.31 to 0.35) and so does Arris's. Their Medium 0.39, SemiBold 0.45, Bold 0.50
# (0.48 to 0.52), ExtraBold 0.55, Black 0.61 (0.57 to 0.65); on the ladder Arris had until then (102 114 130 144
# 158) it stood at 0.37, 0.40, 0.44, 0.47 and 0.51: its Bold their SemiBold, its Black their Bold (the owner: "a
# true bold at the same color as other sets and a true black"). On these stems 0.39, 0.45, 0.50, 0.55, 0.60.
#
# Black is heavier than any weight of the watch's. The watch's Black (175) had failed in Arris's widths with the
# watch's corners: the bowl's outside cut grew with the stem and its inside stayed cut, so a counter two thirds of
# a stem wide was a diamond (see _params: the outside cut holds the Regular's size, as the cut families that have a
# Black do, and the inside goes square).
STEMS = {100: 24, 200: 44, 300: 66, 400: 90, 500: 110, 600: 133, 700: 155, 800: 178, 900: 200}
# Arris Mono and Arris Mono Narrow keep the stems Arris drew until then (to Bold: MONO_WEIGHTS). In a 600 cell
# its Bold already has Fira Code Bold's colour (0.41 for 0.43, read the same way), and a third stem of 155 has
# no room in the m (mono_weight).
MONO_STEMS = {100: 24, 200: 44, 300: 66, 400: 90, 500: 102, 600: 114, 700: 130, 800: 144.4, 900: 158}
# The stems the engine draws, by the weights its rules name: the watch's, and one rung past the watch's Black for
# the stems only Arris has (its ExtraBold and Black). No font carries the name; drawn, watch_weight and draw._cut
# read a stem's place on it.
DRAWN_STEMS = {**WATCH_STEMS, 1000: STEMS[900]}
NAMES = {100: 'Thin', 200: 'ExtraLight', 300: 'Light', 400: 'Regular', 500: 'Medium',
         600: 'SemiBold', 700: 'Bold', 800: 'ExtraBold', 900: 'Black'}


@dataclass(frozen=True)
class Optics:
    h_light: float = 1.0       # horizontal / vertical stroke at Thin ...
    h_heavy: float = 1.0       # ... and at the watch's Black (WATCH_STEMS: the stems the ratios were measured at)
    d_light: float = 1 / SQRT2  # 45-degree stroke (perpendicular) / vertical, Thin ...
    d_heavy: float = 1 / SQRT2  # ... and Black
    s_light: float = 2 / 5 ** 0.5  # 2:1 stroke (perpendicular) / vertical, Thin ...
    s_heavy: float = 2 / 5 ** 0.5  # ... and Black
    c_ratio: float = 0.25      # edge break leg / vertical stem
    leg: float = 90.0          # bowl centreline chamfer leg (1.5 modules)

    @staticmethod
    def _t(sv):
        return min(max((sv - WATCH_STEMS[100]) / (WATCH_STEMS[900] - WATCH_STEMS[100]), 0.0), 1.0)

    def h_ratio(self, sv: float) -> float:
        return self.h_light + (self.h_heavy - self.h_light) * self._t(sv)

    def d_ratio(self, sv: float) -> float:
        return self.d_light + (self.d_heavy - self.d_light) * self._t(sv)

    def s_ratio(self, sv: float) -> float:
        return self.s_light + (self.s_heavy - self.s_light) * self._t(sv)


# The watch's pixel logic: every diagonal as wide across as a stem.
HERITAGE_OPTICS = Optics()
# Horizontals thin from 0.90 of the stem at Thin to 0.85 at Black (measured:
# 0.87-0.90 Regular, 0.85-0.87 Bold). 45-degree strokes, diagonals and bowl
# corners alike, run 0.94 at light weights (measured diagonals 0.94-0.97,
# chamfer corners close to the mean of side and top) and thin to 0.84 at
# Black, as heavy faces do, so tight figures like the 4 keep their counters.
OPTICS = Optics(h_light=0.90, h_heavy=0.85, d_light=0.94, d_heavy=0.84, s_light=0.96, s_heavy=0.88)


def _ladder(table: dict, wght: float) -> float:
    ks = sorted(table)
    if wght <= ks[0]:
        return table[ks[0]]
    for a, b in zip(ks, ks[1:]):
        if wght <= b:
            t = (wght - a) / (b - a)
            # (to a billionth of a unit: a weight asked for by its stem, mono_weight, has the ladder's own number,
            # where 114 came back 114.00000000000001 and an outline began on another of its points)
            return round(table[a] + (table[b] - table[a]) * t, 9)
    return table[ks[-1]]


def _rung(table: dict, sv: float) -> float:
    """The weight whose stem is ``sv`` on a ladder (its ends' past them)."""
    ks = sorted(table)
    if sv <= table[ks[0]]:
        return float(ks[0])
    for a, b in zip(ks, ks[1:]):
        if sv <= table[b]:
            return a + (b - a) * (sv - table[a]) / (table[b] - table[a])
    return float(ks[-1])


def stem(wght: float, watch: float = 0.0) -> float:
    """A weight's stem: Arris's (STEMS), the watch's own at the watch's
    end of the axis (WATCH_STEMS), and between them as the variable font
    carries it, straight from one to the other."""
    own = _ladder(STEMS, wght)
    if not watch:
        return own
    theirs = _ladder(WATCH_STEMS, wght)
    return theirs if watch == 1.0 else own + (theirs - own) * watch


def watch_weight(sv: float) -> float:
    """The watch's weight that draws a stem: the weight the engine's rules
    name (past the watch's Black, DRAWN_STEMS' last rung)."""
    return _rung(DRAWN_STEMS, sv)


def weight_of(sv: float, watch: float = 0.0) -> float:
    """The weight of a cut that draws a stem (stem's inverse): Arris's at
    ``watch`` 0, the watch's at 1."""
    if not watch:
        return _rung(STEMS, sv)
    if watch == 1.0:
        return _rung(WATCH_STEMS, sv)
    lo, hi = 100.0, 900.0
    for _ in range(50):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if stem(mid, watch) < sv else (lo, mid)
    return (lo + hi) / 2


FIG_GROWTH = 1.5  # figure width gained per unit of stem, in the watch's own drawing (and half that below its weight)
# Past the Regular a figure's body gains this much for each unit its stem gains. At the watch's rate, a
# unit and a half past its own weight, the zero's counter was 19% narrower at Black than at Regular and
# the figures' advance 10% wider, where 60 families measured at one boldness (tools/width_survey.py)
# narrow the zero's counter 35% and widen the advance 4.7% (letterframe.white_scale: the letters' white).
# At three quarters the zero's counter is 31% narrower: between theirs and the H's 29%, since Arris's
# figures are as wide as its capitals and theirs are narrower; at 0.65, the families' own rate, the
# figures fell to 0.97 of their share of the H (theirs keep 0.99).
FIG_GIVEN = 0.75
# Past the Regular a letter's white gives way to its stems at the rate the white of other families'
# letters does. Across 60 grotesque, geometric and squared families read at one x-height and one
# boldness (tools/width_survey.py), the n's counter is 38% narrower at Arris Black's boldness than at its
# Regular's, the H's 29%, and a line of lowercase 3.9% longer. These are those two rates, in the white
# of a module a letter loses for each watch stem (two modules) its stem gains past the Regular's: a
# lowercase letter's white gives faster than a capital's, a figure's or a sign's.
#
# Until 1.017 the white gave a quarter of a module for each watch stem past the watch's own weight and
# less before it: the n's counter was 20% narrower at Black than at Regular, almost every unit a stem
# gained went outward, and a line of lowercase grew 6% to Bold and 11% to Black where the families grow
# 2.4% and 3.9% (the owner, 2026-11-10: "this gets far too bold widthwise"). Arris Black set as long as a
# geometric face with the ink of other families' ExtraBold.
REGULAR_R = 0.75    # the Regular's stem, in watch stems
LOWER_GIVEN = 0.59
CAP_GIVEN = 0.45


def white_given(sv: float, m: float, rate: float, optical: float = 1.0) -> float:
    """What is left of a letter's white past the Regular, as a share of the
    white the watch's own rule gives that stem (params.white_own): 1 to the
    Regular. The watch's own drawing keeps its modules (``optical`` 0)."""
    r = sv / (2 * m)
    if r <= REGULAR_R or not optical:
        return 1.0
    return 1.0 + ((white_own(REGULAR_R) - rate * (r - REGULAR_R)) / white_own(r) - 1.0) * optical
GRAD_SHARE = 0.002  # grade: GRAD 100 thickens strokes by a fifth, -100 thins them by a fifth
# A positive grade fades out from SemiBold to Black, a cut's own: at Black it adds nothing,
# so the heaviest stroke a cut draws is its Black's own. Past the watch's Black's stroke the
# drawings had no room: with a fifth more, some three hundred glyphs (? ‡ $ €
# among them) fused, kinked or lost a terminal between 750 and 900, and the
# variable font smeared each change across the weights between its masters.
GRAD_TAPER = (600.0, 900.0)


def grade_k(wght: float, grad: float) -> float:
    """What a grade scales the strokes by, at a weight."""
    if grad > 0:
        a, b = GRAD_TAPER
        grad *= min(1.0, max(0.0, (b - wght) / (b - a)))
    return 1 + grad * GRAD_SHARE


# The watch's stroke balance eases off past Bold: from 750 it takes a falling
# share of the watch's ratios, down to WATCH_FLOOR at Black. At its full share
# every horizontal is as thick as a stem (the measured optics thin them to
# 0.85 at Black) and every diagonal as wide across as one, and past Bold the
# drawings have no room for that: where bars stack against a bowl (э є ӭ ԙ ℡
# ҕ ҙ) the white between them closed into a blob at Black. Eased further, to
# half, the ŧ cleared too, but the drawings turned back toward the measured
# optics' own along the weight: a corner the watch's balance holds from Light
# up (the italic s's) curved again at 850, in some thirty glyphs, a feature
# lost and regained. Three quarters keeps the watch's character at Black;
# the ŧ has a rule of its own. The watch itself, SemiBold, and every weight
# up to 750 keep the full balance.
WATCH_TAPER = (750.0, 900.0)
WATCH_FLOOR = 0.75


def watch_share(wght: float) -> float:
    """The share of the watch's stroke balance one of the watch's weights
    (WATCH_STEMS; a stem's: watch_weight) takes at WTCH 100."""
    a, b = WATCH_TAPER
    t = min(1.0, max(0.0, (wght - a) / (b - a)))
    return 1.0 - (1.0 - WATCH_FLOOR) * t


def params(wght: float = 600, grad: float = 0, optics: Optics = OPTICS, base: Params = Params(),
           watch: float = 0.0) -> Params:
    """Parameters for a weight, a grade, and a balance between the measured
    optics (watch = 0) and the watch's own proportions (watch = 1), eased
    off past Bold (WATCH_TAPER). The watch's optics passed whole are watch = 1
    (Arris Watch). The weight is the font's: Arris's own past the Regular,
    the watch's at watch = 1 (stem)."""
    if optics == HERITAGE_OPTICS:
        optics, watch = OPTICS, 1.0
    sv = stem(wght, watch)
    return _made(sv, wght if watch == 1.0 else watch_weight(sv), grade_k(wght, grad) if grad else 1.0, grad,
                 optics, base, watch)


def drawn(wght: float, grad: float = 0, base: Params = Params(), watch: float = 0.0) -> Params:
    """The parameters of the cut at ``watch`` where its stem is that of
    one of the watch's weights (WATCH_STEMS): what the engine's rules ask
    for when they name a weight (draw._cut), whatever the font calls it. In
    Arris the watch's ExtraBold is its Black; the watch's Black, which no
    weight of Arris draws, is still where a cut's forms are chosen."""
    sv = _ladder(DRAWN_STEMS, wght)
    k = grade_k(wght if watch == 1.0 else weight_of(sv, watch), grad) if grad else 1.0
    return _made(sv, wght, k, grad, OPTICS, base, watch)


def _made(sv, heritage_weight, k, grad, optics, base, watch):
    optical = 1.0 - watch
    share = watch * watch_share(heritage_weight)
    if share >= 1.0:
        optics = HERITAGE_OPTICS
    elif share:
        a, b = optics, HERITAGE_OPTICS
        mix = lambda x, y: x + (y - x) * share
        optics = Optics(h_light=mix(a.h_light, b.h_light), h_heavy=mix(a.h_heavy, b.h_heavy),
                        d_light=mix(a.d_light, b.d_light), d_heavy=mix(a.d_heavy, b.d_heavy),
                        s_light=mix(a.s_light, b.s_light), s_heavy=mix(a.s_heavy, b.s_heavy),
                        c_ratio=mix(a.c_ratio, b.c_ratio), leg=mix(a.leg, b.leg))
    p = _params(sv, optics, base, optical)
    if grad:
        p = p.with_(sv=p.sv * k, sh=p.sh * k, sd=p.sd * k, ss=p.ss * k, c=p.c * k, grade_k=k, grad=grad,
                    pregrade=(p.sv, p.sh, p.sd, p.ss, p.c))
    return p.with_(floor=stroke_floor(base), optical=optical)


# The lowercase's horizontals thin a little more than the capitals' toward
# Black: its bars stand in three quarters of the height, and one thickness
# for both closes the lowercase's counters first. Measured in hand-drawn
# faces (the o's top against the H's bar: tools/stroke_roles.py): 0.97 at
# Regular, 0.80 to 0.93 at Bold, 0.91 at Black. Here the whole of it to
# Regular, easing to LOW_HEAVY at Black (0.92 at Bold).
LOW_HEAVY = 0.87


def low_share(sv: float) -> float:
    """The lowercase's horizontals as a share of the weight's own."""
    t = min(max((sv - WATCH_STEMS[400]) / (WATCH_STEMS[900] - WATCH_STEMS[400]), 0.0), 1.0)
    return 1.0 - (1.0 - LOW_HEAVY) * t


def _params(sv, optics, base, optical=1.0):
    # Figures stay tabular within a weight but widen with it, so heavier
    # strokes do not eat the counters whole; the watch weight keeps 540.
    d = sv - WATCH_STEMS[600]
    fig_w = fig_own = base.fig_w + (FIG_GROWTH if d > 0 else FIG_GROWTH / 2) * d
    if optical and sv > STEMS[400]:
        # (past the Regular, as the measured families' figures widen: FIG_GIVEN; the watch's own drawing its own)
        regular = base.fig_w + FIG_GROWTH / 2 * (STEMS[400] - WATCH_STEMS[600])
        fig_w += (regular + FIG_GIVEN * (sv - STEMS[400]) - fig_w) * optical
    sh = sv * optics.h_ratio(sv)
    low = low_share(sv)
    leg = optics.leg
    if optical and sv > STEMS[400]:
        leg -= (_cut_out(sv, optics) - _cut_out(STEMS[400], optics)) * optical
    return base.with_(fig_w=fig_w, fig_adv=fig_w + (base.fig_adv - base.fig_w), fig_own=fig_own,
                      white_low=white_given(sv, base.m, LOWER_GIVEN, optical),
                      white_cap=white_given(sv, base.m, CAP_GIVEN, optical),
                      past=max(0.0, sv - STEMS[400]) * optical, sv=sv, sh=sh, sd=sv * optics.d_ratio(sv),
                      ss=sv * optics.s_ratio(sv), c=sv * optics.c_ratio, leg=leg, low=low,
                      desc=descender_line(base, sv, sh))


# A bowl's corner is cut on its centreline (Optics.leg, a module and a half), and the stroke round it puts the
# outside cut further out and the inside one further in: at the Regular 117 units outside and 62 inside. With one
# centreline leg at every weight the outside cut grew with the stem (140 units at a stem of 155, 156 at 200) while
# the counter it stood round shrank, and the inside stayed cut: at a stem of 200 the o's counter, 134 units wide,
# gave 50 to each corner and was a diamond, the e's eye and the a's bowl with it. The cut families that have a
# Black (Tektur, Tomorrow) keep the outside cut one size from Regular to Black and their insides are square by
# Bold. Past the Regular Arris's outside cut holds the Regular's size; the inside one is what the strokes leave
# of it, down to the corner rule's fill (draw.fill_leg). The watch's own drawing keeps its leg.
def _cut_out(sv: float, optics: Optics) -> float:
    """How far outside its centreline's a bowl's outer cut stands, at a
    stem (params.outer_leg less the leg)."""
    return (sv + sv * optics.h_ratio(sv)) / 2 - sv * optics.d_ratio(sv) / SQRT2



_FLOOR: dict = {}


def stroke_floor(base: Params = Params()) -> float:
    """The thinnest stroke the font draws, in font units: the Thin's own
    thinnest (its horizontal), with the measured optics. Nothing is drawn
    thinner, however it was derived (small figures, marks, the letters
    inside a ring, a negative grade, the watch's light diagonals): below it
    a stroke stops reading as the same pen (see geom.Thickness)."""
    key = id(base)
    if key not in _FLOOR:
        p = _params(STEMS[100], OPTICS, base)
        _FLOOR[key] = min(p.sv, p.sh, p.sd, p.ss)
    return _FLOOR[key]
