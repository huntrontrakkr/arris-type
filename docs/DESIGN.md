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
| straight 2:1 stroke | 7 | N, the italic v and w, slashes, fraction slash |
| the 1's foot | 1 | J's top bar |
| the 1's notched flag, turned | 1 | the shoulders of n, m, h and r, the l's top |
| the t's foot | t | the l's tail |

The proofs in `proofs/caps-masters.png` and `proofs/lower-masters.png` show
the pixels, and the rule's outlines beneath them.

**One family of shoulders.** The r's shoulder leaves its stem at 45 degrees,
two modules below the arch, and leaves a notch under it: the 1's flag,
turned. The n, m and h spring from their stems the same way, so the arches
lean forward, the lowercase reads as one family, and the 1's flag runs
through every line of text. From 1.017 every bowl meets its stem through
a shoulder of its own rule, half as deep (`lower.bowl_join`,
`lower.BOWL_DROP`): under the ascender on b and d, over the descender on
p, q and g, at the foot on a, u and y. At the arches' two modules, at the
light weights, a bowl stood a long way off its stem and read as a stroke
of its own.
Where the stems stand too close for the
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

In 1.017 the upright v and w went back to the gable, high walls over
45-degree points, at the owner's word (the italic keeps the 2:1 arms).
In eight modules that v measured 0.38 from the u. Its walls now bend
where the w's do, which makes it as wide as its two arms, nine tenths of
the n, and v/u is 0.46 at Regular by the same measure.

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

**Accents take half.** Up to its cut's Regular a mark is drawn with its
letter's strokes. Past it, its strokes take half of what the letter's gain
(`marks.MARK_GAIN`), its corner breaks stay the Regular's, and so do its
whites: the white between a dieresis's dots, between a double acute's
strokes, between the mark and its letter. That is what fifty-nine other
families do at their heaviest weights (an accent's stroke 0.62 to 0.71 of
the stem, half of the stem's gain from Regular); with the letter's whole
gain Arris's accents were bloated at Black, and held at the Regular's
weight they were hairlines. A letter's own dot grows with its letter.

**Under the letter.** The cedilla is a flat tab, after Tomorrow's: a short
stroke leaning two down for one across, cut level underneath, two modules
deep and as wide as the letter's stem at every weight. The ogonek is a
small hook from the letter's right foot, turning right, on a third of the
letter's gain (`marks.HANG_GAIN`), six tenths of a stem in the italic. The
horn takes the same third. The ring is a regular octagon inside and out,
eight sides of one thickness, also after Tomorrow's.

## 4. From pixels to every weight

The watch has one weight. Arris has nine, Thin to Black, and two stroke
balances.

**The weights.** The watch's stem is two modules, a sixth of the figure
height: a SemiBold. The other weights were drawn around it, 24 units at
Thin, 90 at Regular, 175 at Black (`instances.WATCH_STEMS`), and Arris
Watch keeps them, its SemiBold the watch's figures. Arris and Arris Mono
share them to the Regular. Past it Arris has the stem that gives a line of
its lowercase the colour other families' weight of that name has
(`instances.STEMS`): 110, 133, 155, 178 and 200 units from Medium to Black,
read on sixty grotesque, geometric and squared families at every weight
they have (the ink of a line of lowercase in the band of its x-height:
0.39, 0.45, 0.50, 0.55 and 0.60 for their 0.39, 0.45, 0.50, 0.55 and 0.61).
Black is heavier than any weight of the watch's, and what let it be drawn
is the corner: past the Regular a bowl's outside cut holds the Regular's
size and its inside goes square, where the watch's cut grew with the stem
and a counter two thirds of a stem wide was a diamond. Arris Mono keeps a
lighter ladder (`instances.MONO_STEMS`: 102, 114, 130, 144 and 158, four
fifths of what the watch's adds past the Regular): in a 600 cell its Bold
already has Fira Code Bold's colour, and a third stem of 155 has no room in
the m. A rule of the engine that names a weight (the measured optics' ends,
the weight a cut's forms are chosen at, the weights a heavier one is held
against) names the watch's, whose stem the font's weight has
(`instances.drawn`). Along the watch axis the variable font goes from
Arris's stem to the watch's.

**Strokes, not pixels** (`arris.geom`). A glyph is drawn as centrelines. Each
segment is offset by half its thickness, and the thickness depends only on
direction: horizontal, vertical, 45° and 2:1 each have their own. A *bowl*
node chamfers the centreline. The union of the strokes then gets the corner
rule above. At the watch's parameters this reproduces the pixel figures
exactly. At other parameters it is the same drawing at a different weight.

**Outside corners grow, inside corners do not** (`draw.fill_leg`). The
pixel rule has one chord for a corner that sticks out and a corner that
points in. In Arris the chord that cuts an outside corner is a quarter of
the weight's stem, and the chord that fills an inside one is the weight's
own up to the Regular and the Regular's from there to Black. A cut takes
ink off the outside of a letter; a fill puts it into a counter or a join,
where the white is already shrinking as the stems grow, and on one leg the
insides of the heavy weights clogged: the widest spot at a join stood at
1.38 stems at every weight, where the families measured for it tighten
theirs from 1.18 at Regular to 1.10 at Black. A bowl's inside chamfer is
what its strokes leave of it, down to the same leg. A crotch, where a
diagonal meets a stem, is filled one leg along the stem (the pixel rule's
two put twice a right angle's ink where the strokes already overlap), in
the italic as in the upright; and a shoulder's diagonal starts deeper in
its stem by what the fill is short, so the join keeps its thickness and
only its corner is smaller (`lower.shoulder_enter`). The watch's own
drawing keeps the pixel rule whole.

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
stem; white widens a little at light weights, and past the Regular it
gives way to the stems at the rate the white of other families' letters
does (`instances.white_given`, measured with `tools/width_survey.py`): a
lowercase letter's faster than a capital's, so at the watch's Black, the
boldness the families were read at, the n's counter is 0.62 of the
Regular's and the H's 0.71, and a line sets a twentieth longer, not a
ninth (at Arris's own Black 0.70 and 0.77, the line a twenty-fifth). A letter with one stem, and the y, give the share of
their body the n or the H gives, the cursive's j, l, r and k among them;
the f, the t and the j give no more than their crossbar and hook can
spare, and the cursive f, a stem and a crossbar, gives nothing. A sign
of bars (a dash, the underscore, the plus, the equals and every operator
in the plus's body) has no white between stems to give: its modules are
the length of its bars, and at every weight it keeps the share of the
H's body it has at the Regular (`letterframe.kept_width`), as the dashes
and the operators of other families keep theirs. The N, whose 2:1
diagonal would make it a quarter wider than the H at Black, keeps its
Regular's share too and deepens its joins (`caps.n_width`). The
watch's own drawing keeps its
modules and Arris Mono its cell. Figures are spaced as
the letters are, each by its own white; their tabular twins (`tnum`)
share one cell within a weight, and it widens with the weight.

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

**A feature weight would swallow adapts.** The openings rule is one case
of a general one. Toward Black a stroke's growth reaches the whites around
it, and where a white is part of what the letter is (the slot under the
t's crossbar that holds the ŧ's bar, the white between a g's hook and its
bowl), the drawing gives way by the least that keeps the feature,
in this order: the stroke moves toward the open side; it thins, down to
the stack minimum of a bar (0.7 of the weight's own); its neighbourhood
grows (a hook deepens into the font's descent, by up to 70 units); and
only where no white can remain does the feature close whole, in one piece
without a sliver, leaving a bump to say it was there (the ŧ's bar runs on
past the t's right edge). A hook does not thin: every descender of a
weight stands on one line, set for the g's hook at its full weight under
its bowl (a horizontal and the least white over it: three modules to
SemiBold, 250 units, the font's descent, at Black;
`params.descender_line`), and the y's tail and the p's, q's and j's
descenders stand on it too. Until 1.017 the hook thinned first (three
quarters of the bowl's strokes at Regular) and went deeper alone from
Bold: a stroke out of weight in a letter, and two descender lines in a
line of text. Each move is measured on the drawing itself, the
white read off the ink along the feature, so it follows every axis, not
the weight alone; and a fill the corner rule adds at a stroke's end is
kept half a break clear of a parallel chamfer, or the two leave a step
between them (a hairline, and a bowl line the italic cannot curve). A bar
placed by rule can still land an edge a unit from a jog of the letter it
crosses, so a bar is settled: drawn, read with the topology check
(`arris.topology`), and stepped a few units off such a coincidence
(`Glyph.settle`). The ŧ's bar, the ₽'s bar and foot and the ℘'s hook are
drawn this way. Where the ŧ's slot will not hold the bar at its stack
minimum with a module of white either side, the white gives way first,
down to a break, then the bar, to half its own, and only then does the slot
fill. A part that meets a neighbour's chamfer just where the outline's
jog cleanup or the italic's curving decides differently from one weight
to the next settles too, of its steps the one that leaves the most
corners curved (ϖ's bar, Ѫ's arch), or stands where the decision holds
one way at every weight (₼'s arch, a few units lower from Bold).

**An added stroke keeps the Regular's weight and is laid over the
letter.** Every stroke added to a letter or sign (a bar, a slash: Đ Ħ ŧ Ł
Ø ð ℏ ǥ Ѣ Ғ Ұ Ҟ Ӿ and their lower cases; the bars and strokes of € ¥ $ ¢ £
₦ ₩ ₳ ₸ ₱ ₽ ₣ ₭ ₤ ₴ ₵ ₲ ₡ ₿ ₫ ⃀ ₺ ₮ ₥, a pair of bars by the pair's own
formula at the Regular, no longer thinned further by the squint) is as
thick at every heavier
weight as at the Regular (`draw.EXTRA_HOLD`, `hold_weight`: in Arris Mono
Narrow its own Regular, drawn at 350), one rule for all of them (the
owner, 2026-11-06). It is laid over the finished letter, not unioned with
its strokes (`Glyph.lay`, `draw.lay_bar`, `geom.ink`'s overlay): finished
alone, its ends broken on the Regular's chamfer, and joined to the letter
as it stands. No corner rule runs over the junction, so nothing fills in
round it as the letter grows on, and the letter under it is the letter
(the g in ǥ is the g). A bar across a stem runs out further the thinner it
is than the letter's own (ǥ Ѣ ѣ Ӿ ӿ Ҟ ҟ). Ҟ's bar sits in the V between
stem and arm, which the K's own growth closes from below; it rises with
the weight as far as it must to keep white half a module square on its
edge at both ends (`bar_white`), to the top of the stem at Black. In the
italic, a chamfer a stroke covers at one end (ǥ's hook bend under the bar)
is curved as the letter's own and cut where it passes under the stroke's
edge, so the curve is the g's at every weight, the variable italic
included; a chamfer crossed in its middle (the O's corners under Ø's
slash) stays straight, as it always has.

**Ends that stay ends.** A tail, a hook or a beak shorter than the corner
it turns on ends in that corner's chamfer, a point, and from Bold up the
chamfer grows faster than the tail. So a tail runs at least as far as its
corner needs for a flat to its end, and where the letter has no room for
that the corner's chamfer is the smaller (ҧ's and ԓ's hooks, drawn as Ҧ's
is: the hook stands a reach that grows with the stroke beyond the stem). A
beak is the full one or none: ∂'s arm turns down into the 2's beak while
that leaves a stem's white above the bowl, and ends square from the
weight where it cannot; a beak cut shorter crossed its corner's chamfer
(a tooth under the arm in the italic at 500, a wedge over the cap from
600). The white between a tail and the bowl above it (ϱ ℊ ₰) closes whole
from where it is narrower than the slits the outline fills, not partly and
differently at each weight.
The skeleton check (`arris.skeleton`) holds that no feature flickers along
any axis, and the topology check that nothing on the way folds, spikes or
pinches.

**Symbols keep their parts apart.** A symbol's white between its parts
(the notch under an arrow's barb, the gap between a pilcrow's stems, the
spaces between an asterisk's spokes) is drawn to grow with its strokes
rather than fixed in modules, so heavy strokes cannot eat it: an
arrowhead's barbs are at least √2 stems and a diagonal stroke long, so the
white between a barb's end and the shaft never drops below half a stem,
and the arrow widens to keep a shaft beyond its head; a pilcrow's stems
keep three quarters of a stem between them; the bars of # stay a stroke
apart; a dagger's bar crosses in the upper third at every weight, eight
tenths of a stem of stem over it at least (`punct.dagger_bar`), and its
body grows 1.2 units for every unit of stem; small figures' strokes ease
from 0.8 to 0.68 of the figures' as the weight rises. Behind these sits a rule for every symbol: the white
features it has at Regular (white at least half its heaviest stroke wide,
inside its hull) it keeps at every weight, its strokes lightening as far
as needed, never below 0.8 (`draw.LIGHTEN_MIN`; `tools/white_scan.py`
lists what each weight loses). The heaviest stroke is the drawing's own:
a sign made of diagonals alone (‹ « ^) is measured by its diagonal, not by
a stem it has none of. Lightening and the counter thinning are monotone
in the weight: a weight keeps at least what the next lighter named weight
of its cut decided, so neither comes and goes along the weight axis.
A choice of form keeps the lighter weight's too: once the ¢ or the $
takes stubs for its stem, every heavier weight does. The second form is a
glyph of its own (`draw._second_spec`), as the variable font carries it:
every rule here measures it against its own Regular, not the first
form's, so the $ with stubs, which is the S and has the S's counters, is
drawn in its weight's strokes. Between the watch
axis's ends a glyph's lightening is the blend of what it takes at either
end: the variable font draws that axis from its ends, so a lightening
that came and went between them (some sixty glyphs, the italic @ among
them) left the font's outline off the drawing there.

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

Past Bold the watch balance eases off: from 750 it takes a falling share
of the watch's ratios, three quarters of them at Black
(`instances.WATCH_TAPER`; the watch's weights, which Arris Watch has). Whole, it makes every horizontal as thick as a
stem, where the measured optics thin it to 0.85, and past Bold the drawings
have no room for that: where bars stack against a bowl (э є ӭ ԙ ℡ ҕ ҙ) the
white between them closed and the letter pooled into a blob at Black. Its
horizontals still thicken with the weight, only more slowly. Eased to half,
the ŧ cleared too, but some thirty drawings turned back toward the measured
optics' own: a corner the watch's balance holds from Light up (the italic
s's) curved again at 850, a feature lost and regained along the weight.
The watch itself, SemiBold, and every weight up to 750 keep the balance
whole, and Arris Watch takes the same balance as the variable font at WTCH 100.

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
included. Arris runs from 0.90 at Thin to 0.85 at the watch's Black (0.86 at its own). Measured
illusions explain the direction and about half the size: verticals look
6–7% longer than horizontals of the same length, and horizontal bars 3–5%
thicker. The rest is practice, rightly taken from the fonts. In tight stacks
(the a, e and s carry three bars in an x-height), horizontals thin further
so that each counter stays at least ¾ of a bar.

**Diagonals and bowl corners.** The measured faces set diagonals at
0.94–0.97 of the stem, and chamfered faces make a bowl's 45° corner about
the mean of its side and top. That is where the watch's 71% sits furthest
from practice, and where its light corners come from. Arris uses 0.94 at
light weights, thinning to 0.84 at the watch's Black as heavy faces do, so that tight
figures like the 4 keep their counters. The oblique effect (the eye's
poorer acuity for 45° lines) is real only near threshold and at fine
detail, so it is no reason to change a diagonal's weight at text or watch
size; the ratio is practice, which offsets the darkening where diagonals
meet other strokes.

**One bar for a height, and one middle.** Past the Regular a letter's
horizontals give for its own whites (below), and left to that each letter
stood on a bar of its own: at Black the O on 170 units, the S on 154, the 5
on 147. A height has one bar. Every letter of the lowercase stands on the
bar the a's and the e's hooks hang from (`lower.hook_ref`), every capital
and figure on the 5's (`draw._cap_bar`), upright and italic, and what a
letter still thins for itself is its inner bar (the a's, the e's, the s's
spine, the 3's waist). The hooks of c, a, e and s hang from that bar and
end on one line, and a beak is measured from the bar its letter draws. The
middle bar of H E B S 8 3 e a s stands on the centre of its height: 37
families measured put it 1.3% over at Regular and 1.0% at Bold, Arris had
2.5%, and with halves of one width its ink's centre of mass is on the
centre as theirs is (`draw.OPTICAL['counters']`, which is every letter's
alike and fades out from Bold if it is set again).

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
every weight. Since 1.017 a height has one overshoot: every letter and
figure that stands over its line stands over it by the o's on the x-height
and the O's on the cap height (`draw._zone_over`: 1.3 units at Regular, 0.4
at Black), where each had taken what its own outline asked.

**Optical centre.** People bisect a vertical line about 1% high, and type
sets its middles higher than that: measured crossbars sit at 0.50–0.51 of
the cap height in chamfered faces and 0.51–0.53 in neutral ones. Since
1.017 Arris's middles stand on the centre (above: one bar for a height,
and one middle); what follows is the correction as it was until then, and
as it works if a rise is set again. Arris
raised the middle of its letters and figures (`draw.OPTICAL`) until the top
counter of a three-bar letter (B, E, 8) was 0.86 of the bottom one,
calibrated so that at Regular the middle rose 2.5% of the cap height
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
at Black it adds nothing, so the heaviest stroke a cut draws is its own
Black's (200 units in Arris, 175 in Arris Watch, 158 in Arris Mono). Past the watch's Black
the drawings had no room. With a fifth more, some
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
monospaced italic keeps the upright's, its cells having no room for tails,
but for three, cursive by default in Mono Italic: the descending f, the
looped k and the y that is a u running on into its descender (and the
letters built on them, ǩ ḟ ķ ₖ ⅎ ý ÿ ŷ ỳ ...), each drawn as in the
proportional italic, narrowed until its ink fits the 600 cell with a
quarter-module to spare, and centred in it, so a line keeps its grid with
them or without (`italic_forms.MONO_CURSIVE`); `ss04` ("Plain italic f k
y") gives back the slanted upright's three. The f's tail lies on the
underscore's line, so an underscore before it runs on, at its own height
and weight, past its cell's edge and under the tail: `is_fresh` reads as
one line into the f (`italic_forms.JOIN`; `ss05`, "Underscore apart",
keeps it as it is, and a plain f takes no join). Where the tail is the
heavier (Regular), its chamfer shows as a step up into it.

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

* `pnum` (default) and `tnum` figures: proportional in text, spaced and
  kerned as letters; `tnum` gives the watch's, the same drawings on one
  cell (the default until 1.017: on its cell the 1 stood two stems' white
  from its neighbours and the others a third of one apart). In Arris Mono
  every figure is on the cell.
* `locl`, `ccmp`, `mark`, `mkmk`: local forms and mark positioning (section 10).
* `calt`: a colon between figures becomes the time colon, its dots
  centred on the figures; between tabular figures the watch's, in a
  tighter slot.
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
character touches the sequence on either side, so `<=<`, `>>=`, `//=` and
`||=` stay as their characters while `|->`, `!==` and `...`, which are
ligatures themselves, still form. A few look past that as Fira Code's do:
`#!` forms before the slash of `#!/bin/sh`, `www` before a dot but not in
`wwww`, `[|` not in `[|]`, `#_` not before another underscore
(`ligatures.GUARDS`).

Arris Mono sets every ligature Fira Code sets by default. Fira Code's are
good because each is one gesture, not characters pushed together; Arris's
make the same gestures in its own strokes. A ligature keeps every
character where it stands and as it is drawn alone, so an N-character
ligature is N cells wide and set as the characters would be: the < of
`</span>` is the < of `<span>`, the bars of `==` are the bars of =. A join
only runs a character's own strokes on, in their own direction, until they
meet the next one (`tools/ligature_pairs.py` proves each against its
characters on the cell grid):

* **Tags and pipes**: in `</` `/>` `</>` the chevron's arm runs on along
  its 2:1 until it meets the slash, square to it (a 2:1 arm is
  perpendicular to the 2:1 slash); `|>` `<|` `<|>` `||>` `<||` `|||>`
  `<|||` are simple triangles, the chevron's arms run back to the pipe's
  place and closed there by an upright as tall as they reach (the plain
  chevron's point and angle), the other pipes uprights as tall; in `<>` the
  two chevrons' arms meet.
* **`<$>`** (`<$` `$>`): the chevron's arm runs on until it lands on the
  dollar S's bar, which gives up its beak there; one stroke turns through
  both points, the dollar's stem crossing it.
* **`#` and its neighbours**: in `#[` `#(` `#{` `]#` the bars of # run on at
  their full weight to the bracket's spine (# centres on the brace's point,
  so the point sits between its bars); in `#_` the left stem of # runs down
  into the underscore, and in `#_(` on under the paren and up it, one
  stroke from the # to the top of the (; in `#?` the top bar of # runs on
  into the ?'s bowl, and in `??` the second ?'s beak leaves the first one's
  side the same way. `#=` sets the bars of = level with the bars of #, `#:`
  the colon's dots on them, brought in; `#!` brings the ! in (# stays at
  the start of the line). Fira Code slants the : and ! to its slanted #;
  Arris's # stands upright, so they keep their own drawing.
* **Brackets and a pipe**: in `[|` `|]` `{|` `|}` the bracket's arms run on
  to just short of the pipe, the white of `:=`: one sign, the pipe still
  its own (closed, `[|` and `|]` would both be a rectangle).
* **The tilde**: `~~` is one stroke of two steps; in `-~` the hyphen turns
  up into the tilde's first stroke where it crosses the axis, in `~-` the
  tilde's downstroke turns along it; `~>` `~~>` `<~` `<~~` `<~>` run the
  tilde's wave into the arrows' heads; in `~@` the tilde's rise becomes the
  @'s ring, nothing hanging below the join.
* **Equality**: `==` `===` run the bars of = through, at ='s own white;
  `!=` `/=` `!==` `=/=` strike them; `:=` `=:` `::=` raise the colon onto
  the bars; in `^=` the caret's arm runs down onto the top bar.
* **`/\` `\/`**: the two slashes meet in a point.
* **`www`** is one zigzag, each next w begun on the last one's right
  upright, which they share; the shared uprights stand full height, each
  w's short middle between, so the three still read as three. **`&&`**
  stands on one line: the first one's floor runs on under its leg into the
  second's. (These and `#?` are the sequences Fira Code joins into one
  shape rather than sets closer.)

Where a sequence becomes a new sign, it is drawn across its cells: the
arrows (`->` `-->` `<-` `<->` `=>` `==>` `<=>` `|->` `<-|` `|=>` `->>`
`<<-` `<!--`), one 45-degree head 0.88 of the cap height whose point stays
sharp, the shaft ending inside it, a double shaft's bars ending on its
arms; and `<=` `>=`, a full-size ≤ and ≥ on the 2:1 chevron. `--` stays
two dashes, each run out to fill its cell; `++` `+++` run the plus signs'
bars through.

**Characters together.** What Fira Code draws only closer is set the same
way: `!!` `%%` `**` `***` `..` `...` `::` `:::` `;;` `//` `///` `||`
`|||` `<<` `<<<` `>>` `>>>`, and `/*` `*/` `*>` `<*` `<*>` `<+` `+>`
`<+>` `?.` `.?` `?=` `!!.` `..<` `..=` (Fira Code sets these as its
characters closer, separate shapes, as here). Each character is itself,
the run centred on its cells, each next one half a cell on (as Fira's), or
as far as leaves a stroke and a half of white between them at Regular
(square to their strokes), whichever is further, and never further than
typed. The places are Regular's at every weight, the white thinning as
the strokes grow, never under three quarters of a stroke
(`ligatures.STEP`, `WHITE`, `WHITE_MIN`, `_run`).

**Runs of any length** (`glyphs/sequences.py`): a run of hyphens, equal
signs, underscores or number signs is set as pieces, one to a cell, each
drawing its cell's share of the run's lines; a line runs a quarter module
past its cell into the next piece and meets it flush (the corner rule
leaves the cut square: `Glyph.butt`), so a run is one line however long:
`---` `---->` `<====>` `|---|` `####` `____`. Its caps are the ligatures'
own: the arrowhead of `->`, the double head of `->>` (`<<--` `==>>`), the
pipe and the slash as themselves (`|==|` `/==` `==//`), `||` `>>` `//` as
their repeats set them, the chevron as a tail with its point on the line
(`>->` `<=<`); inside a run, a pipe across it (`--|--` `_|_`), a head on
it (`-->--`), the struck bars of `=/=` (`=/==`), the `!` and `:` of `=!=`
`=:=` with `:=`'s white either side. The fixed ligatures are matched
first, and a run takes what is longer or what they leave. It forms with
three hyphens, four equal signs, two underscores or number signs when it
has no cap (`--` `==` `===` are ligatures of their own), two with one cap,
one between two caps (`|-|` `>=>`), and not when a cap starts a longer
run of its own character (`-->>>`, `<<<--`) or when it is one character
and one cap (`x>-1`, `|-`). In Mono Italic the last of a run of
underscores runs into the cursive f as a single underscore does (`__f`).

**Optional sets**, off by default as in Fira Code, under Fira Code's own
tags (Arris has its own characters, so Fira's character variants are not
taken; cv19, cv23 and cv24, a level bar on ≤ ≥ and `/=` as ≠, are how
Arris draws those already):

| Tag | Sets |
|---|---|
| `ss07` | `=~` `!~` as ≈ ≉, the tildes' flats sharing the two cells |
| `ss08` | `==` `===` `!=` `!==` gapped: each = its own, `!=` `!==` struck through the middle |
| `ss09` | `>>=` `<<=` `\|\|=` `\|=` into the bars of =, with the runs' tail, double head and pipes |
| `ss10` | `Fl` `Tl` `fi` `fj` `fl` `ft`: the f's bar (the F's and T's top) run on into the next letter |
| `cv20` | `<=` as ⇐ |
| `cv21` | `=<` as ⩽, the bar parallel to the chevron's lower arm, the equal sign's white square to it |
| `cv22` | `=<` as ≤, the bar level (as `<=` is) |
| `cv25` `cv26` `cv32` | `.-` `:-` `.=`: the dot raised to the axis (the colon's to the bars), the line run back to it |
| `cv27` | `[]` as a box, the arms run on until they meet |
| `cv28` | `{.` `.}` with the dot raised to the brace's point |

**Alignment** (`calt` too, after the ligatures, after Fira Code's;
`glyphs/alignment.py`): in Mono the hyphen, plus and asterisk sit on the
capitals' middle, the axis the arrows and = < > share. Touching a
lowercase letter (`kebab-case`, `a+b`, `x*y`) they drop to the lowercase
middle; the colon rises to the capitals' middle (the time colon) touching a
capital or beside a chevron (`A:B`, `HH:MM`, `<:`); an x between figures or
in `0x` before a hex digit is a times sign (`1920x1080`, `0xFF`). Between a
capital and a lowercase letter nothing moves (`A-b`), and a sign doubled is
left alone (`Foo::Bar`; `--` and `++` are ligatures), so a run never has
one sign high and the next low.

The signs underneath agree with each other: < and > are 2:1 chevrons
filling the operator box, as tall as + (and ≤ ≥ ≮ ≶ ≺ build on the same
chevron); the bars of = stand 1.6 bars apart to the Regular, the white
every stacked sign keeps, and past it that white gives a third of what the
stem gains (`punct.eq_white`: 126 units at Regular, 89 at Black, as some
seventy families' does by their boldness), so = ≡ ≈ ≅ ≋ stand in the
capitals' height at every weight. A tilde in a stack rises six tenths of
its stroke and two of them stand a bar and that white apart, one in the
other's bays (`operators.stack`); a sign of dots (÷ ∶ ∷ ∴ ∵) is as tall as
the plus, its dots' outer edges where the plus's arms end
(`operators.dot_reach`); the radical's tick starts at 0.45 of its height,
at the steep 2:1 as its rise (`symbols.radical_tick`); past the Regular
the small signs hold near the share of the line they have there (a
quotation mark's dot and the bullet take half of what the weight's would
gain, `punct.quote_dot`; a bracket's and a brace's arms stand out a little
over half a stem, and the brace's point is cut flat where it would stand
out past the Regular's); the brace is told from ( by a square bracket's ends (flat arms,
square corners, as long as the bracket's) and from [ by a point at its
waist, a stem deep on the shallow 2:1, where ( has only its 45° ends. In
the monospaced cut, dots (. , : ; and the tittles) are half
as big again as the stem at Regular, easing to a fifth more at Black: a dot
looks lighter than a stroke of its width, and code turns on them.

Arris Mono ships in Fira Code's six weights, Light (300), Regular, Retina
(450, a Regular a little heavier for light text on dense screens), Medium,
SemiBold and Bold, each with its italic (`instances.MONO_WEIGHTS`,
`MONO_NAMES`). It keeps one cell, ten modules (600 units), at every weight
the engine draws, so every weight shares a grid in an editor or a terminal
(the cell
had followed the figures, which widen with the weight: 528 at Thin, 682 at
Black). A glyph is drawn in the body the proportional figures have at its
weight, held between nine modules and nine and a half (`params.MONO_CELL`,
`MONO_BODY`): a module of margin to SemiBold, half a module from Bold on.

A cell crowds what the proportional cut spreads out, so every Mono glyph,
as the font will carry it (placed in its cell, in whole units, curved in
the italic), is checked for the faults the topology check names: a contour
that crosses itself or another, a fold, white or ink pinched narrower than
a break. One that has any lightens its strokes together, as little as
clears it and at most to the topology lock's limit (`draw._flawed`, the
outline lock): the fractions at SemiBold and Bold, ↂ, ∛ ∜, ‰ ‱. A sign set
from letters (₷ ⅷ ₧) uses Mono's own letters in the italic, the upright's
slanted (`Params.plain`), not the cursive forms whose tails closed in the
cell; a wave or zigzag arrow settles on the first clean run between its
pattern and its head (⇜ ⇝ at Light). Crossings under a unit, which no size
shows, are let be (the italic α's foot). No two characters of the printable
set touch side by side at any weight: the narrowest white between
neighbours is the slashed Ø's, 15 units at Bold.

In the monospaced cut the hyphen sits on the math axis, in line with
`+ = < >` and the arrows it grows into. `ss03` turns `<=` `>=` back into their characters (for languages where
they are arrows); `cv01` is the single-storey a (both cuts), `cv02` the
plain zero. `cv03` is the hooked j: Arris's j is the l run down under the
line, a stem and the l's foot turned to the left on the descender line;
until 1.017 it turned into a hook that ended in a beak, the g's in little,
and `cv03` gives that one back (j, ȷ, ĵ, ǰ). Arris Mono's j and the
italic's are the hooked one, and `cv03` changes nothing there.

## 9. Metrics

| | units | modules |
|---|---|---|
| em | 1000 | 16.7 |
| cap height, figures | 720 | 12 |
| x-height | 540 | 9 |
| ascender | 780 | 13 |
| descender | -180 | -3 |
| hhea / typo ascender / descender | 950 / -250 | |
| stem at Regular / Bold / Black | 90 / 155 / 200 | 1.5 / 2.6 / 3.3 |
| Arris Mono: stem at Regular / Bold | 90 / 130 | 1.5 / 2.2 |
| Arris Watch: stem at SemiBold (the watch's) / Black | 120 / 175 | 2 / 2.9 |

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
  its ink will not fit; bars may hang past its body but keep a letter's
  quarter module from the cell's edge (`draw.CELL_GAP`), and a letter
  drawn narrower to give them room is condensed only as far as it needs
  to stay as open, for its width, as it is in its own cell. Every other
  symbol whose ink would run out of its cell (‰ ™ ∭ @ …) is condensed, or
  drawn smaller, to fit (`symkit.mono_fitted`): drawn smaller, it is
  drawn smaller whole, the body it is drawn in with it (©'s ring with its
  letter), and centred where it stands once raised. Its ink is measured as
  the font carries it, slanted in the italic. A letter's sign is fitted
  as it is drawn, upright; in the italic it is drawn narrower in its cell
  as a letter is, and condensed for the slant only if, as narrow as a
  letter goes, its slanted ink would still not fit (№ ℘ ₠, drawn to their
  own proportions; ₦ ℂ, a letter filling the body, narrow with it). A
  sign is measured as its glyph draws it, horizontals thinned as they
  will be (`symkit._look`), and a sign laid out by its own strokes and
  gaps is clipped on that frame, never on a narrower body it is given
  (₪ ℞ ∛ ∜ lost a stem, a stroke, a rise to the cell that way). The em
  dash just spans the cell.
* **The Mono cell, both ways** (1.015): nothing in Arris Mono is cut by
  its cell. A letter whose ink would pass the 600-unit cell (a horn, the
  apostrophe of ď ľ ť Ľ, an ogonek, Ø's slash, a tone mark beside a
  circumflex, a tonos) is moved as little as brings its ink a quarter
  module inside (`draw.CELL_GAP`), and if it is wider than that leaves room
  for, drawn narrower until it is not, then centred (`draw._cell_fit`):
  the letter gives up width, not the mark, down to its floor (0.6 of its
  body, and never so narrow that a counter between two stems closes:
  `draw.cell_floor`); past it the mark gives way (ď's apostrophe at Bold,
  the horn of Ư Ơ at Bold Italic: `latin_plus.horn_give`), measured
  against its letter drawn at that floor (`marks.at_floor`). Signs keep
  the same quarter module. Every measure is of the ink as the font
  carries it, as far as its curves reach (`draw._ink_x`, `draw._curve_x`:
  not their off-curve points, which stand outside a rounded corner), and
  in the italic slanted, with the overshoot it will be given (vertical,
  but leaned by the slant): the
  slant leans a capital's top 127 units past its foot, so every letter of
  Mono Italic is drawn narrower than its upright, as narrow as its own
  slanted ink needs (a d, whose stem rises on the right, narrower than a
  b), and the figures, drawn on the body they are given
  (`figures.frame`), with them; a letter drawn inside another (Ŧ's T,
  ŀ's l, the cursive y under ỵ's dot) gives up what its body does. Where
  even the letter at its floor and the
  mark at `LIGHTEST` run out of the cell, the mark goes on shrinking, to
  `CELL_LIGHTEST` (ď at Bold Italic, where the slant takes 134 of the
  cell's 570 units). A letter that fits is not clipped at all:
  the cell's clip cuts raw ink, before the corner rule breaks a stroke's
  tips, and cut the tonos of Ά Έ Ό flat. Up and down the cell is the line
  box (975 above, 250 below), a terminal's cell: a stack of marks fits
  under it (`marks.line_top`), its gaps closing up first (to `TIGHTEST`)
  and then its marks lightening and shrinking (to `LIGHTEST`), where it
  will stand after the base's optical correction lifts it; the owner's
  choice (2026-11-06) was the line over the accents' size. Only Ǻ at the
  heaviest weights stands a little over (29 units at Bold). The inferiors
  stand as low as keeps the small p's descender inside the line
  (`features.inferior_dy`), together. `tools/mono_cell_check.py` gates the
  release on it.
* **Cells** (`terminal.md`): box drawing, blocks, shades and Braille fill
  a Mono cell from descender to ascender in every family, meet the cell
  edge square (`Glyph.butt`), and stay upright in the italic so that rows
  and columns join.
