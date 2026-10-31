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
| straight 2:1 stroke | 7 | N, v, w, slashes, fraction slash |
| the 1's foot | 1 | J's top bar |
| the 1's notched flag, turned | 1 | the shoulders of n, m, h and r, the l's top |
| the t's foot | t | the l's tail |

The proofs in `proofs/caps-masters.png` and `proofs/lower-masters.png` show
the pixels, and the rule's outlines beneath them.

**One family of shoulders.** The r's shoulder leaves its stem at 45 degrees,
two modules below the arch, and leaves a notch under it: the 1's flag,
turned. The n, m and h spring from their stems the same way, so the arches
lean forward, the lowercase reads as one family, and the 1's flag runs
through every line of text. Where the stems stand too close for the
diagonal (the monospaced m, the heaviest weights) the shoulder rises less,
down to a plain square join, so the drawing changes continuously with
weight. The u keeps its plain bowl: notched, it moved toward the v.

**Measured, then drawn.** `tools/letter_confusion.py` puts every pair of
letters, and the strings readers mistake for one another (rn and m, cl and
d, I l 1), through the same ideal-observer model as the figures
(`docs/research/legibility.md`), against B612, Atkinson Hyperlegible and
the chamfered faces. Where Arris was weaker than all of them, the letter
changed:

| Change | Pair | before | after |
|---|---|---|---|
| l: the t's foot as a tail | l/I | 0.29 | 0.57 |
| v, w: 2:1 arms (the 7's slope) instead of 45-degree gables | v/u | 0.43 | 0.72 |
| B: the upper bowl a module narrower (the classic B) | B/8 | 0.25 | 0.29 |
| c: the shortest beaks | c/o | 0.36 | 0.42 |
| G: the bar below the middle and deeper in | G/B | 0.39 | 0.49 |
| the dotted zero's dot three times as tall | 0/O (Mono) | 0.21 | 0.43 |

(SemiBold, cap height 11 arcminutes: a small label.) The capital V keeps its
45-degree gable, from the watch's own capitals: at cap height it has
diagonal enough, and V/U measures 0.52.

**Cyrillic in the Latin rhythm.** Small-capital forms (в, к, н, п, ы, я...)
draw their capitals in the x-height with the white scaled four modules for
five, so the small Н has the n's white. The Ы's separate stem stands from
its bowl as far as a letter from its neighbour (two sidebearings), and the
Љ counts the three verticals it has.

**Marks under stems.** The cedilla of T and t is written as a comma, as
Romanian writes it: hung from the T's stem, a cedilla would make the letter
a J. The comma below keeps inside the descender: its stub shortens, then
the whole comma lightens, as heavy faces draw their accents; the breve's
sides thin the same way so its cup stays open.

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
* the 3's waist bar draws back toward the middle;
* a beak (3, 5, §) shortens, never past its own outer flank, so it keeps
  its point;
* the figures that stack three bars (3 5 6 8 9) thin their horizontals,
  down to 0.7 of the weight's own, as the a, e and s do;
* the open five's bowl comes back down toward the 5's own;
* the a's bowl lowers;
* the e's bar rises;
* the Q's tail shortens;
* the δ's neck stands up, from 45 degrees toward the 7's 2:1.

Every closed counter, in letters and signs alike, keeps at least half its
share of the stem in the watch's drawing. Where heavier strokes would close
it, the glyph's horizontals thin, down to 0.7 of the weight's own: the
tight-stack rule of the a, e and s, applied wherever it is needed rather
than declared letter by letter. A stroke that crosses a bowl (the ø's
slash, the ¢'s bar) thins instead.

**Symbols keep their parts apart.** A symbol's white between its parts
(the notch under an arrow's barb, the gap between a pilcrow's stems, the
spaces between an asterisk's spokes) is drawn to grow with its strokes
rather than fixed in modules, so heavy strokes cannot eat it: an
arrowhead's barbs are at least √2 stems and a diagonal stroke long, so the
white between a barb's end and the shaft never drops below half a stem,
and the arrow widens to keep a shaft beyond its head; a pilcrow's stems
keep three quarters of a stem between them; the bars of # stay a stroke
apart; a dagger's bar moves down so the stem above it stays longer than it
is thick; small figures' strokes ease from 0.8 to 0.68 of the figures' as
the weight rises. Behind these sits a rule for every symbol: the white
features it has at Regular (white at least half its heaviest stroke wide,
inside its hull) it keeps at every weight, its strokes lightening as far
as needed, never below 0.8 (`draw.LIGHTEN_MIN`; `tools/white_scan.py`
lists what each weight loses). The heaviest stroke is the drawing's own:
a sign made of diagonals alone (‹ « ^) is measured by its diagonal, not by
a stem it has none of. Lightening and the counter thinning are monotone
in the weight: a weight keeps at least what the next lighter named weight
of its cut decided, so neither comes and goes along the weight axis.

**A floor under every stroke.** The lightest the font draws is the Thin's
own thinnest stroke (its horizontal, 22 units). Nothing is drawn thinner,
however it was derived: small figures, the letters inside © and ®, a
negative grade at Thin, the watch balance's light diagonals at Thin. The
floor lives in the parameters (`Params.floor`): every derived set of
parameters clamps its strokes to it as it is made, so the geometry that
places a stroke and the stroke itself agree. It binds only at the lightest
settings; from ExtraLight up every stroke is already above it. Dots (the
period, a tittle, a dieresis, a comma's head) have a floor of their own,
twice the stroke floor (`Params.dot`): a stem's square at Thin is a speck,
and Thin faces draw their dots about twice their stems.

Mouths, where a beak faces a bar, keep three quarters of their share;
closed counters and the gaps under the 5's and 6's arms keep half. The 5's
mouth is what tells it from a 6, the pair most easily confused at small
sizes (`docs/research/legibility.md`), so it is held open to the heaviest
corner of the variable font: Black, grade +100, watch balance.

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
model of vision (`arris.vision`). A review of the perception literature
(`docs/research/perception.md`) says which of these corrections the eye
explains and which are typographers' practice.

**Horizontals thinner than verticals.** A horizontal bar looks heavier than a
vertical stem of the same thickness. The measured faces set horizontals at
0.87–0.90 of the stem at Regular and 0.85–0.87 at Bold, chamfered faces
included. Arris runs from 0.90 at Thin to 0.85 at Black. Measured
illusions explain the direction and about half the size: verticals look
6–7% longer than horizontals of the same length, and horizontal bars 3–5%
thicker. The rest is practice, rightly taken from the fonts. In tight stacks
(the a, e and s carry three bars in an x-height), horizontals thin further
so that each counter stays at least ¾ of a bar.

**Diagonals and bowl corners.** The measured faces set diagonals at
0.94–0.97 of the stem, and chamfered faces make a bowl's 45° corner about
the mean of its side and top. That is where the watch's 71% sits furthest
from practice, and where its light corners come from. Arris uses 0.94 at
light weights, thinning to 0.84 at Black as heavy faces do, so that tight
figures like the 4 keep their counters. The oblique effect (the eye's
poorer acuity for 45° lines) is real only near threshold and at fine
detail, so it is no reason to change a diagonal's weight at text or watch
size; the ratio is practice, which offsets the darkening where diagonals
meet other strokes.

**Overshoot, where a bowl turns at a cut corner.** Round letters usually
rise above and dip below the flat ones (about 1.3–1.6% in the neutral
faces), because a curve looks shorter than a flat edge of the same height.
Arris has no curves, but its bowls are octagons: S's top turns down at 45
degrees at both ends, so it holds less ink at the line than H's square-cut
stems and looks short. The vision model says by how much
(`vision.overshoot_need`): it blurs the glyph's convex hull with a sigma of
0.119 of the zone height (the blur at which a circle needs a 1.5%
overshoot), compares it at the half level with the box it fills between
the lines, and the side reaches past its line by the difference, at most
1.5% of the zone (`draw.OPTICAL`). Only a side that ends in bowls
overshoots: every flat on its extreme line must turn down (or up) into a
bowl's 45-degree corner at both ends (`draw._bowl_side`). Stem ends and
bars (H, F's foot, T's stem, B's top) sit on the line, as does a side the
clip cuts (A's apex, v's foot), and a side the drawing already carries past
its line (v's point) keeps what it was drawn with. In 1.002, at Regular, S,
C, 8 and o reach 3 units past their lines at the top and the bottom, O
1; at Thin S 4 and o 5; at Black S 2 and o 1. H and x stay on the line at
every weight.

**Optical centre.** People bisect a vertical line about 1% high, and type
sets its middles higher than that: measured crossbars sit at 0.50–0.51 of
the cap height in chamfered faces and 0.51–0.53 in neutral ones. Arris
raises the middle of its letters and figures (`draw.OPTICAL`) until the top
counter of a three-bar letter (B, E, 8) is 0.86 of the bottom one,
calibrated so that at Regular the middle rises 2.5% of the cap height
(B's: 17.5 units). As the bars thicken the counters shrink, and the rise
with them, so a heavy top bowl never pinches: B's middle is 20 units up at
Light and 10.5 at Black. At Thin, where the strokes are the stroke floor,
the zone above the middle cannot give way without a stroke falling under
the floor, so the rise yields: it comes in by degrees with the stroke,
nothing at the floor and whole at twice it (about ExtraLight), a straight
line in the weight that the variable font follows between its Thin and
ExtraLight masters (`tools/stroke_scan.py` is the check). The correction
is a piecewise-linear warp through the bars:
the bottom bar, the middle bar and the top bar each move as one piece, so
every stroke keeps its thickness and only the white between them stretches
or gives way.

**Measured optics only.** Both corrections are the share `Params.optical`,
which is 1 at the measured optics and falls linearly to 0 along the watch
axis: at WTCH 100, and in Arris Watch, the figures are the watch's own
drawing, pixel-exact (`tests/test_heritage.py`). Composites take their
base's correction whole (a cedilla stays joined).

**Small figures drawn small.** Superiors, inferiors and the figures of
fractions are not scaled-down figures. They are the same constructions with
a smaller module and cap height (0.62) and strokes only a little lighter
(0.8). Their colour then matches the full figures beside them.

**White that reads when you squint.** Two parts of a glyph are only
apart if a reader sees the white between them. The vision model squints:
it blurs the drawing with a Gaussian 5% of the cap height wide and looks
at the white narrower than half a stem, where parts come close
(`vision.narrow_whites`). That white is a hole (closed), a slot (between
two parts, the same width all along: the gap between a sign's bars, the
notch where a bar runs out past a stem), a wedge (where two strokes meet
at an angle, a K's crotch) or a shallow inside corner. Blur fills a wedge's
point in every face at every weight, so wedges and corners are not
counted. A hole or slot reads if its median stays at least 0.55 of the
way from the blurred ink's peak to paper; the e's eye and the a's and s's
counters keep 0.52–0.59 at Bold and Black. A glyph declares the free
variable that opens its white (`draw.Squint`), and the rule moves it only
as far as needed to keep what the glyph keeps at Regular (or 0.55, if that
is less), so nothing that reads already is touched. `tools/squint_scan.py`
lists the holes and slots each weight squeezes shut, and the pinholes and
slivers that never read at all.

**Small counters.** A closed counter narrower than half a stroke is not
white at all, only a speck, so small closed forms keep at least the
least white (`letterframe.least_white`: a module, or 0.6 of a stem) or
their own stroke across. The degree sign's ring, like the ring accent's,
stops thickening at two modules and keeps three quarters of its stroke
inside; ¤ widens to hold its counter; the ring below is drawn wider than
high; the @ stands its four uprights evenly, and thins its four bars as a
tight stack does, where its a would close; small figures, like small
letters, are never heavier than 2.6 of their own modules, so the small
8 keeps both counters. The dollar's stem runs above and below the S at
the weights where, run through, it would split the S's counters into
slivers.

**Barred signs.** ¥ € and the currency signs with two bars (₦ ₩ ₱ ₳ ₤ ₴
₸ ₹) follow one rule. The bars are the weight's horizontals, easing to
0.8 of them at Black; the white between them is at least three quarters
of a stem; they run 0.9 of a stem past the letter, which widens to hold
them. Where the squint would still see the pair fuse, the bars thin
(never below 0.65 of the horizontal) and the white between them stays.
Each sign places its pair where its letter has room: ¥ a stroke's white
under where the arms meet the stem, ₤ centred between base and top with
the white shared evenly, ₴ clear of its beaks, or, at heavy weights where
no pair fits between them, with the beak running into the bar rather than
leaving a sliver.

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

A positive grade fades out from SemiBold to Black (`instances.GRAD_TAPER`):
at Black it adds nothing, so the heaviest stroke the fonts draw is Black's
own. Past Black's stroke the drawings had no room. With a fifth more, some
three hundred glyphs fused, kinked or lost a terminal between 750 and 900
(the ? its hook's stub, the ‡ its bars, the $ its counters), and the
variable font smeared each change across the weights between its masters.
A negative grade thins, which the drawings have room for, and keeps its
full reach.

**Recommended grade.** A light–dark border looks shifted about 0.4
arcminutes toward the dark side (Westheimer), so a light stroke on dark
gains about 0.8 arcminutes. At the watch's 36-pixel figures that is 11% of
the SemiBold stem. Material's guidance for light-on-dark icons is −25;
neither Google nor Apple documents a value for text, and in a 459-person
study grade made no measurable difference to reading speed in dark mode,
so the choice is one of appearance.

| Screen and setting | GRAD |
|---|---|
| dark on light | 0 |
| light on dark, backlit or OLED (the watch's dark palettes) | −50 (strokes −10%, about 0.6 px) |
| light on dark, transflective in daylight | −25 |
| night or glance use | −100, or a weight lighter at −50 |

Never go past −100. The value that would fully match dark-on-light weight
under the border model (−22% at SemiBold) is an upper bound from a single
edge, not a stroke. Settle the final value with proofs on the device: how
the watch blends antialiased edges (in gamma or linear light) thins light
text by up to a third of a pixel per edge on its own.

## 6. The variable font

Three axes: weight (100–900), grade (−100–100) and watch (0–100), the
dial between the measured optics and the watch's own stroke balance.

**Masters.** Every hundred on the weight axis, and every fifty from Bold
up; the grade's ends at 100, 400, 600, 800 and 900 (a positive grade
fades out from SemiBold, so its change bends at 600, and between the ends
at 400 and 900 alone everything at a grade was predicted); the watch's end
at 100, 400, 600, 800 and 900; and the grade's ends on the watch's end at
the same five weights, where the two changes meet. Thirty-six in all
(`arris.vf.space`, `BASE` and `CORNERS`). Each glyph then keeps only the
masters its drawings need, and a glyph the font still draws away from its
drawings somewhere gets masters of its own there, on a finer grid; a census
of where each glyph's drawing jumps from one weight to the next
(`tools/vf_planes.py`) can give it masters just either side of the jump,
so a change the drawing makes in ten units of weight stays within them.

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
* A glyph that is mirror-symmetric in every master (537 of them: 8, A,
  W, *, Ж, ‡, ¥ …) is aligned by its halves: each master is cut on its
  axis into arcs from the axis back to it, the arcs are matched across the
  masters with their ends pinned, and each contour is an arc and its
  mirror. Aligned whole, a point present in some masters only was paired
  with a neighbour on one side and the opposite neighbour on the other,
  and 92 symmetric glyphs leaned between the masters (Ж by 38% of its
  area, the 8 by 1%). Now every instance of them is symmetric. The corner
  rule's polish makes its choices by geometry, never by the direction a
  ring runs, so a symmetric drawing stays exactly symmetric to begin with.

Nothing is trusted. The build (`arris.vf`) draws every glyph exactly at
locations between the masters and compares the variable font's
interpolation to it. With sixteen masters, every glyph varies, and the
median outline difference is under half a unit of the 1000-unit em. The
largest differences come where three axes combine, or where an opening is
solved non-linearly.

That check found real design faults, which were then fixed:

* Z and r came apart at Thin.
* Accents touched their letters at Black.
* g-cedilla's comma was being drawn as a hidden cedilla.

## 7. The italic

The italic is the same drawings, slanted ten degrees, with curves where
the upright cuts chamfers (`arris.italic`).

**Curves for chamfers, points kept.** Every 45-degree chamfer that stands in
for a right angle (a bowl's corner, an edge break, the steps of the 2's
notch and the 4's clip) becomes a quadratic curve, its control point the
corner it cut. The construction records which edges are chamfers as it
draws them, so a diagonal stroke never becomes a curve by looking like one.
A bowl's corner is a pair of chamfers, the stroke's outer and inner edges,
and they curve together or not at all: a curve on one edge against a
straight other swells the stroke into a wedge, or, bulging across it,
crosses the outline. A corner either of whose edges runs into a point (the
3's, 8's and B's waists, a beak's tip at the lightest weights) stays
straight on both, so the point stays sharp. Everything
the upright keeps sharp stays sharp: beaks, the 3's and 8's waists, the
meeting of two diagonals, a diagonal's end, the X's stepped crossing. The
softened bowls against those points are what keep the italic Arris.

**Slant without distortion.** The outline is sheared about half the
x-height, so every glyph keeps its place and its advance and the upright's
spacing carries over; kerning is measured on the slanted shapes. A shear
alone thins the strokes that lean with it and thickens those that lean
against it (each 45-degree diagonal by about 9%), so stroke weights are set
before the shear: every stroke comes out as heavy across as its upright
self, times cos 10 degrees, as a stem does.

**A hand, not a slant.** The italic lowercase is cursive, built from moves
the upright already makes (`arris.glyphs.italic_forms`):

* *Entries*: the 1's flag leads into the tops of i j m n p r u y, and into
  the ascenders of b h k l, its upper edge continuing the stem's cut corner
  so the stem keeps its flat top on the x-height.
* *Exits*: the t's foot ends the stems of a d h i m n u on the baseline;
  curved by the italic, it is a hand's exit stroke, and a's tail meets i's
  flag as a pen would join them.
* *Branching*: arches leave their stems three modules below the arch, a
  module lower than the upright's notched shoulders.
* *Cursive forms*: the single-storey a; the f that runs on below the
  baseline and turns back; the looped k, whose arm closes into a bowl on
  the stem; the y that is a u running on into the g's descender; the s
  whose spine is a 45-degree diagonal with the 2's notch; the e whose bar is
  a 45-degree diagonal rising into the top right corner, the eye the
  triangle above it, leaving on an upstroke. The e's bar thins and the k's
  loop deepens at heavy weights, so their counters keep half a stem.
* *Cyrillic*: и is written as a u, п as an n, т as an m, д as a g; ш, щ
  and ц are u's with three stems or a descender (а е р у come through the
  Latin forms).

Measured with `tools/letter_confusion.py`, the diagonal s is further from
its neighbours than a slanted upright s (closest pair 0.51 against 0.41 at
11 arcminutes), and the cursive e is as far from c as the upright e is
from o. Accented letters and the ordinals take the italic forms; the
monospaced italic keeps the upright's, its cells having no room for tails.

**Variable.** The italic's variable font aligns the upright masters, then
curves them: a segment that is a chamfer in any master carries a control
point in all of them, at its middle where it is straight, so a curve grows
from a straight edge as the weight moves.

**Certified, not eyeballed.** `tools/stroke_scan.py` checks every glyph,
upright and italic, at every weight and at the grade and watch extremes:
no contour crosses itself or another; on the exact outline, no stroke is
thinner than the floor (an opening of the ink by the floor's width removes
nothing but corner slivers and the points the design draws sharp); and,
along each stroke's skeleton away from junctions and points, none swells
past 1.75 times its weight's thickest. Parts lighter than their weight's
strokes are listed, and every one is designed so: small figures, the
letters inside a ring, the notch's one-pixel step, a tight stack's
horizontals.

## 8. Features

* `tnum` (default) and `pnum` figures.
* `locl`, `ccmp`, `mark`, `mkmk`: local forms and mark positioning (section 10).
* `calt`: a colon between figures becomes the watch's time colon, with
  dots centred on the figures in a tighter slot.
* `zero`: a slashed zero, its slash square to the bowl's corners.
* `ss01`: a dotted zero. Clocks should keep the plain 0: a dot or a slash
  moves a zero toward an 8, which is why the German number-plate face
  dropped its slashed zero. The Mono cut dots its zero, for code.
* `ss02`: the open five, whose bowl sits one pixel row higher. Blurred, it
  is the figure that separates most from the 6
  (`docs/research/legibility.md`).
* `sups` `subs` `sinf` `numr` `dnom` `frac` `ordn`, plus precomposed ½ ¼ ¾,
  superior ¹ ² ³ and ª º.
* `case`: dashes, guillemets, bullets and brackets raised for capitals.
* `ss20`, Watch pixels: the figures as the watch drew them, one square
  per lit pixel of their 9×12 masters, and the time colon between them as
  the watch lights it, two dots of 2×2 on rows 3–4 and 8–9 of the twelve
  (`arris.glyphs.origin`). Upright in the italic, as a display's pixels are.

### Programming ligatures (Arris Mono)

Code sits on a fixed grid, so a ligature never changes it: a sequence of N
characters becomes N - 1 empty spacers and one glyph a cell wide that
draws back across all N cells (the scheme Fira Code made standard). The
substitution is contextual (`calt`, on by default; editors can turn it
off), longest sequences first, and it never forms when an operator
character touches the sequence on either side, so `<=<`, `>>=`, `//=`,
`||=` and `---->` stay as their characters while `|->`, `!==` and `...`,
which are ligatures themselves, still form.

A ligature keeps every character where it stands and as it is drawn
alone, so an N-character ligature is N cells wide and set as the
characters would be: the < of `</span>` is the < of `<span>`, the bars of
`==` are the bars of =. A join only runs a character's own strokes on, in
their own direction, until they meet the next one (`tools/ligature_pairs.py`
proves each against its characters on the cell grid):

* **Tags and pipes**: in `</` `/>` `</>` the chevron's arm runs on along
  its 2:1 until it meets the slash, square to it (a 2:1 arm is
  perpendicular to the 2:1 slash); `|>` `<|` `<|>` `||>` `<||` are simple
  triangles, the chevron's arms run back to the pipe's place and closed
  there by an upright as tall as they reach (the plain chevron's point and
  angle); in `<>` the two chevrons' arms meet.
* **`<$>`** (`<$` `$>`): the chevron's arm runs on until it lands on the
  dollar S's bar, which gives up its beak there; one stroke turns through
  both points, the dollar's stem crossing it.
* **`#[` `#(` `#{`**: # and the bracket each in its cell, the bars of #
  running on at their full weight to the bracket's spine; # centres on the
  brace's point, so the point sits between its bars. In `#_` the left
  stem of # runs down into the underscore.
* **Equality**: `==` `===` run the bars of = through, at ='s own white;
  `!=` `/=` `!==` `=/=` strike them; `:=` `=:` `::=` raise the colon onto
  the bars.

Where a sequence becomes a new sign, it is drawn across its cells: the
arrows (`->` `-->` `<-` `<->` `=>` `==>` `<=>` `|->` `<-|` `|=>` `->>`
`<<-` `~>` `~~>` `<~` `<!--`), one 45-degree head 0.88 of the cap height
whose point stays sharp, the shaft ending inside it, a double shaft's bars
ending on its arms; and `<=` `>=`, a full-size ≤ and ≥ on the 2:1 chevron.
`--` stays two dashes, each run out to fill its cell; `++` runs the plus
signs' bars through. Sequences that would only be drawn closer together
(`||` `::` `..` `!!` `//` `>>` `/*` `<*>`) are left as their characters.

The signs underneath agree with each other: < and > are 2:1 chevrons
filling the operator box, as tall as + (and ≤ ≥ ≮ ≶ ≺ build on the same
chevron); the bars of = stand 1.6 bars apart, the white every stacked sign
keeps; the brace is told from ( by a square bracket's ends (flat arms,
square corners, as long as the bracket's) and from [ by a point at its
waist, a stem deep on the shallow 2:1, where ( has only its 45° ends. In
the monospaced cut, dots (. , : ; and the tittles) are half
as big again as the stem at Regular, easing to a fifth more at Black: a dot
looks lighter than a stroke of its width, and code turns on them.

In the monospaced cut the hyphen sits on the math axis, in line with
`+ = < >` and the arrows it grows into. `ss03` turns `<=` `>=` back into their characters (for languages where
they are arrows); `cv01` is the single-storey a (both cuts), `cv02` the
plain zero.

## 9. Metrics

| | units | modules |
|---|---|---|
| em | 1000 | 16.7 |
| cap height, figures | 720 | 12 |
| x-height | 540 | 9 |
| ascender | 780 | 13 |
| descender | -180 | -3 |
| hhea / typo ascender / descender | 950 / -250 | |
| stem at Regular / SemiBold (watch) / Black | 90 / 120 / 175 | 1.5 / 2 / 2.9 |

## 10. Beyond the letters

The wider repertoire (about 2,150 code points) follows the same rules. Each
area has a note in `docs/coverage/`, listing what was drawn and why:

* **Marks** (`latin-plus.md`): combining marks are glyphs with no advance,
  and `mark`/`mkmk` place them on anchors measured from each finished
  outline (`arris.anchors`), so base + marks lands where the precomposed
  letter has them. Stacks keep a gap over the ink below them, and a stack
  that would pass the line lightens and shrinks as one, never below half
  size. `ccmp` drops the i's and j's dots under a mark and picks the flat
  `.case` marks after capitals.
* **Local forms** (`cyrillic-greek-ext.md`): glyph modules add language
  systems and feature code through `draw.LANGSYS` and `draw.FEATURE_CODE`;
  `locl` runs first. Bulgarian gets its own forms, and the Serbian and
  Macedonian italic gets its own cursive.
* **Signs** (`symbols-plus.md`, `arrows-math.md`): currency and letterlike
  signs are Arris letters with bars, strokes and inner lines whose white
  grows with the stem; every arrow comes from one builder (shaft, head,
  tail, eight directions); operators sit on the maths axis. In Mono a
  letter's sign fills the cell as letters do, and is condensed only when
  its ink will not fit; bars hang into half the cell's margin, and a letter
  drawn narrower to give them room is condensed only as far as it needs
  to stay as open, for its width, as it is in its own cell. Every other
  symbol whose ink would run out of its cell (‰ ™ ∭ @ …) is condensed, or
  drawn smaller, to fit (`symkit.mono_fitted`); the em dash just spans
  the cell.
* **Cells** (`terminal.md`): box drawing, blocks, shades and Braille fill
  a Mono cell from descender to ascender in every family, meet the cell
  edge square (`Glyph.butt`), and stay upright in the italic so that rows
  and columns join.
