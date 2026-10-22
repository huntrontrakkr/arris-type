# Arris: design

Arris grows a typeface out of the Chamfer clock figures of the Dymaxion
watch face. This document records what those figures do, which parts of
that we kept, and how the rest of the alphabet, the weights and the optical
corrections follow from it.

## 1. Where it comes from

The watch's clock figures are the **Draft zone numerals**: ten pixel
drawings, 9 pixels wide and 12 tall, with strokes two pixels thick
(`heritage/draft_lettering.py`, copied from the watch repository). The watch
enlarges them three times and runs one rule over the result:

> Every exposed pixel corner is cut on a 45° line, and every inside step is
> filled on the same diagonal.

Nothing else is drawn. The octagons, the beaks and the notches come out of
that rule meeting the pixel drawing. Arris is built the same way: a drawing
on a module grid, the corner rule, and nothing drawn by hand that the rule
can generate.

## 2. What the Chamfer figures do

Tracing the rule exactly (`arris.heritage.trace`) turns each pixel master
into an outline with no loss. Reading those outlines closely shows the
design.

**Octagonal shells around near-rectangular counters.** A two-step pixel
staircase becomes a single 45° line. So the 0's outer corners are cut 2.5
modules deep, but its counter's corners only half a module. A bowl is an
octagon wrapped around a nearly square hole, which gives it a machined look.
That's where both "chamfer" and "Arris" get their names: an arris is the
sharp edge a chamfer removes.

**One rule, applied with care.** The pixel rule, stated as geometry
(`arris.geom._ring_rule`):

* a right angle between a horizontal and a vertical edge gets a 45° chord,
  half a module long: cut if the corner sticks out, filled if it points in;
* a right angle between two 45° edges stays sharp, which is how the beaks
  and the 3's and 8's waists keep their points;
* a 45° angle between a straight edge and a diagonal (the end of a
  diagonal stroke, or the crotch where one meets a stem) gets a chord
  square to the diagonal;
* 135° turns are left alone.

**Diagonals as wide across as a stem.** A pixel staircase is two pixels
wide in every row, so a 45° stroke is only 1/√2 of a stem measured square to
its direction: 71%. The watch's corners and diagonals are light, and the
figures read crisp and drawn rather than heavy.

**Quirks that are the character.** These are pixel decisions the rule
turns into features. Arris keeps every one of them:

* the **2's notch**: the spine is two 45° strokes offset by a module and
  joined on a short horizontal;
* the **4's clip**: the same offset, joined on a short vertical;
* the **3's waist**: the upper bowl's lower corner is a module larger than
  the lower bowl's upper corner, so the two outer chamfers meet in a sharp
  point;
* the **1's notched flag**: the flag continues the stem's cut corner, and
  the crotch fill under it leaves a notch;
* **beaks**: where an open bowl ends (2, 3, 5), the stub below the corner is
  exactly one edge break long, so the rule turns it into a point;
* flat-topped 3 and 5, a flat arm on the 6, the 6 and 9 as exact 180°
  rotations of each other, the 8's pinched upper bowl;
* the **7**: the zone master's leg is a wobbling staircase, which the watch
  replaced with a straight 2:1 stroke. Arris uses the watch's 7.

**Proportions.** Figures are ¾ as wide as they are tall. Stems are a sixth
of the figure height, which measured fonts would call SemiBold. Tabular
figures sit on a 10-module pitch.

The engine reproduces all of this exactly. At the watch's own weight, all ten
figures rasterize to the watch's shipped pixel masters with no pixel
different, using the watch's own 8×8 sampler (`tests/test_heritage.py`).

## 3. The letters

There was no alphabet at this size, so one was drawn the same way the
figures were: pixel masters, 12 rows to the cap height, 9 to the x-height,
two-pixel strokes, every corner left to the rule (`arris.masters`). Most of
it reuses moves the figures already make:

| Move | Figures | Letters |
|---|---|---|
| bowl corners, octagonal bowls | 0 6 8 9 | B C D G O P Q R S U b d g o p q |
| the 3's sharp waist | 3 8 | B ß |
| the 2's notch | 2 | Z z, and the X's crossing |
| the 4's clip / the 1's notched flag | 4 1 | the comma's tail, r's shoulder |
| beaks | 2 3 5 | C G J S c j ? |
| gables (verticals bending at 45°) | (the Draft 5×7 caps) | A V W X Y M v w x y |
| straight 2:1 stroke | 7 | N, slashes, fraction slash |
| the 1's foot | 1 | J's top bar |

The proofs in `proofs/caps-masters.png` and `proofs/lower-masters.png` show
the pixels, and the rule's outlines beneath them.

## 4. From pixels to every weight

The watch has one weight. Arris has nine, Thin to Black, and two stroke
balances.

**Strokes, not pixels** (`arris.geom`). A glyph is drawn as centrelines. Each
segment is offset by half its thickness, and the thickness depends only on
direction: horizontal, vertical, 45° and 2:1 each have their own. A *bowl*
node chamfers the centreline. The union of the strokes then gets the corner
rule above. At the watch's parameters this reproduces the pixel figures
exactly. At other parameters it is the same drawing at a different weight.

**Coordinates from the masters** (`arris.glyphs.letterframe`). A letter's
construction names points in its master's module coordinates. A frame maps
them to font units for each weight, anchored where strokes sit against the
body (stems at x = 1 and Wm - 1, bars at the baseline, x-height and cap
height). Between anchors the map is linear. At the watch weight it is the
identity, so every construction can be checked against its master
(`tools/overlay.py`). Diagonals are never mapped point by point, so their
slope stays 45° or 2:1. They are placed by an anchored edge instead: the
4's diagonal leaves the crossbar's end one edge break up; K's arm meets the
cap height one edge break in.

**Widths.** A letter is its stems plus its white. Stems take the weight's
stem; white widens a little at light weights and narrows a little at heavy
ones, so counters change far less than strokes. Figures stay tabular
within a weight but widen with it.

**Openings stay open.** Heavier strokes grow inward, and a fixed body would
close the 4's top, the 1's notch, the e's and a's apertures and the Q's
counter. Each glyph declares its openings, and with each one the free
variable a designer would move. When a weight would shrink an opening below
its share of the stem in the watch's own drawing, the construction moves
that variable until the opening is back to size:

* the 4's clip deepens;
* the 1's flag drops;
* the a's bowl lowers;
* the e's bar rises;
* the Q's tail shortens.

The quirks therefore don't just survive heavy weights; at Black the 4's
clip is what keeps the 4 open. At light weights the clip and notch never
shrink below a module, so they stay visible.

**Two balances.** *Watch proportions* keep the pixel logic: diagonals as
wide across as a stem, horizontals as heavy as verticals. *Measured optics*
(the default) follow well-made fonts (section 5). At the watch weight, the
watch balance is the watch.

## 5. Optical corrections

Corrections in Arris are measured, not eyeballed. The numbers come from
two sources. One is measurements of 24 open-licence fonts: neutral sans
faces, chamfered and octagonal faces, and monospaced faces
(`research-fonts/`, `docs/research/reference-fonts.md`). The other is a small
model of vision (`arris.vision`).

**Horizontals thinner than verticals.** A horizontal bar looks heavier than a
vertical stem of the same thickness. The measured faces set horizontals at
0.87–0.90 of the stem at Regular and 0.85–0.87 at Bold, chamfered faces
included. Arris runs from 0.90 at Thin to 0.85 at Black. In tight stacks
(the a, e and s carry three bars in an x-height), horizontals thin further
so that each counter stays at least ¾ of a bar.

**Diagonals and bowl corners.** The measured faces set diagonals at
0.94–0.97 of the stem, and chamfered faces make a bowl's 45° corner about
the mean of its side and top. That is where the watch's 71% sits furthest
from practice, and where its light corners come from. Arris uses 0.94 at
light weights, thinning to 0.84 at Black as heavy faces do, so that tight
figures like the 4 keep their counters.

**No overshoot for chamfered bowls.** Round letters usually rise above and
dip below the flat ones (about 1.3–1.6% in the neutral faces), because a
curve looks shorter than a flat edge of the same height. The vision
model blurs each glyph with a contrast-sensitivity filter at the viewing
size and finds where the blurred edge crosses half a bar's plateau. It
shows that the octagon's flat top, four modules wide, reads as tall as a
square top at text and watch sizes. Only below about 11 arcminutes of cap
height (a 7-pixel label) do pointed ends start to look short. The
chamfered faces agree: their median overshoot is zero. Arris does not
overshoot its bowls.

**Optical centre.** Measured crossbars sit at 0.50–0.51 of the cap height in
chamfered faces (0.51–0.53 in neutral ones). The watch figures put their
waists at the geometric middle, and so do the Arris capitals. Bowls of B
and P follow their masters.

**Small figures drawn small.** Superiors, inferiors and the figures of
fractions are not scaled-down figures. They are the same constructions with
a smaller module and cap height (0.62) and strokes only a little lighter
(0.8). Their colour then matches the full figures beside them.

**Spacing by area.** Each side of each glyph carries the same mean white,
counted to a depth limit (`arris.spacing`). That is the area method, made
exact for any outline: a flat H side sets the target, and octagonal sides
and open mouths take what makes them equal. Parts outside the measured
zone, such as a j's hook, may hang into a neighbour's space by at most half
its white.

**Grade, for light on dark.** Light text on a dark ground looks bolder than
the same text dark on light, and the watch has dark palettes. The grade
axis (GRAD) thickens or thins every stroke by up to a fifth. Each glyph is
spaced as its ungraded self and drawn in the same body, so no advance moves
and a line of text keeps its length. Glyphs as narrow as a stem (I, i, dots)
thicken outward about their centre; everything else thickens inward from
its edges.

*Pending: the literature review on the horizontal–vertical illusion, the
oblique effect and irradiation (`docs/research/perception.md`), which will
set the recommended grade for dark palettes.*

## 6. The variable font

Three axes: weight (100–900), grade (−100–100) and watch (0–100), the
dial between the measured optics and the watch's own stroke balance.

Arris's outlines are unions of strokes cut by the corner rule. That means
the number of points can change between weights: a junction becomes a
lump, a chamfer uses up a straight, an opening's free variable moves. A
variable font needs every master of a glyph to have identical structure,
so `arris.variable.align` makes the masters compatible after the fact:

* Contours are matched by kind (ink or counter), position and size.
* Points are matched by a sequence alignment on normalised position and
  turning direction.
* A point present in only some masters is inserted into the others as a
  duplicate of its neighbour, so the feature grows from nothing.
* A counter that closes at an extreme is given to the other masters as a
  contour collapsed to a point.

Nothing is trusted. `tools/build_vf.py` draws every glyph exactly at
locations between the masters and compares the variable font's
interpolation to it. With sixteen masters, every glyph varies, and the
median outline difference is under half a unit of the 1000-unit em. The
largest differences come where three axes combine, or where an opening is
solved non-linearly.

That check found real design faults, which were then fixed:

* Z and r came apart at Thin.
* Accents touched their letters at Black.
* g-cedilla's comma was being drawn as a hidden cedilla.

## 7. Features

* `tnum` (default) and `pnum` figures.
* `calt`: a colon between figures becomes the watch's time colon, with
  dots centred on the figures in a tighter slot.
* `zero`: a slashed zero, its slash square to the bowl's corners.
* `ss01`: a dotted zero.
* `ss02`: the open five, whose bowl sits one pixel row higher. Blurred, it
  is the figure that separates most from the 6
  (`docs/research/legibility.md`).
* `sups` `subs` `sinf` `numr` `dnom` `frac` `ordn`, plus precomposed ½ ¼ ¾,
  superior ¹ ² ³ and ª º.
* `case`: dashes, guillemets, bullets and brackets raised for capitals.

## 8. Metrics

| | units | modules |
|---|---|---|
| em | 1000 | 16.7 |
| cap height, figures | 720 | 12 |
| x-height | 540 | 9 |
| ascender | 780 | 13 |
| descender | -180 | -3 |
| hhea / typo ascender / descender | 950 / -250 | |
| stem at Regular / SemiBold (watch) / Black | 90 / 120 / 175 | 1.5 / 2 / 2.9 |
