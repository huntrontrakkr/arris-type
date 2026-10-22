# Perception: the literature behind Arris's optical corrections

This report collects the perceptual research behind the corrections in
`docs/DESIGN.md` section 5, which were chosen from measurements of 24 fonts
(`docs/research/reference-fonts.md`). Each finding carries a one-line
confidence note. Where a practice is typographers' lore rather than a
measured effect, the report says so.

## 1. Horizontal–vertical illusion

**Lengths.** A vertical line looks longer than a horizontal line of the
same length. Mamassian & de Montalembert [1] split the inverted-T effect
into two parts:

* an orientation anisotropy: verticals look about 6% longer;
* a bisection effect: the line that is divided looks about 16% shorter.

Mikellidou & Thompson [2] re-measured it. They found the anisotropy at
7%. They also found that a line which *abuts* another looks 9% longer,
and one that is *crossed* looks 7% shorter. The illusion is smaller with
one eye [3], and larger inside a horizontally elongated frame [4].

* Anisotropy 6–7%. *Confidence: high. It has been replicated, but always
  on lines several degrees long.*
* Abutting +9%, crossing −7%. *Confidence: medium. One lab, revising the
  earlier 16%.*

**Thickness.** The only direct measurement I found is de Waard, Van der
Burg & Olivers [4]. They randomised the horizontal bar's length so that
length could not cue the answer. Even so, a vertical bar had to be
**5.4%** thicker to match a horizontal one (27 of 28 observers). In a
second experiment it was **2.6%**, and the effect was 2.3 times larger in
a horizontal frame than in a vertical one. Their bars were 0.6–1.1°
thick. An Arris stem at the watch view is 5.5–7.3 arcmin, ten times
thinner.

* Thickness illusion 3–5%. *Confidence: medium. One study; the direction
  is certain, but the size at stroke scale is unmeasured.*

**Does it justify 0.85–0.90?** Only partly. A 3–7% anisotropy predicts
horizontals at 0.93–0.97 of the stem. Fonts use 0.85–0.90, and de Waard
et al. point out that Futura (13%) and Avenir (20%) go well beyond their
effect [4]. The rest is **practice**, with plausible reasons that nobody
has measured:

* the broad-nib heritage of stroke contrast;
* vertical crowding: E, e, a and s stack three bars. At Bold this is
  geometry, not perception, and it explains better than any illusion why
  heavy weights thin their horizontals more;
* darkening where bars meet stems.

The illusion gives the direction and about half the size. The number
itself rightly comes from the fonts.

## 2. Oblique effect

**The classic result.** Campbell, Kulikowski & Levinson [5] found
resolution and contrast sensitivity lower for oblique gratings than for
vertical or horizontal ones, from 1 to 35 c/deg. The deficit survived
laser interference fringes, which bypass the eye's optics, so it is
neural. Mitchell, Freeman & Westheimer found the same [6]. Appelle's
review [7] named it the "oblique effect" and collected it across acuity,
detection and orientation tasks.

**Frequency dependence.** The deficit in contrast sensitivity is confined
to high spatial frequencies and steady presentation:

* it is "greatly diminished" at low frequencies [8];
* it is gone for flickering gratings [9];
* oblique gratings need a larger area to reach full sensitivity [10];
* at large pupils part of it is optical [11].

The one parametric form I know is the oblique-effect filter in Watson &
Ahumada's Standard Spatial Observer [12], fitted to Berkley, Kitterle &
Watkins [13]:

    OEF(f, θ) = 1 − (1 − exp(−(f − γ)/λ)) · sin²(2θ)   for f > γ, else 1
    γ ≈ 3.5 c/deg, λ ≈ 13.6 c/deg

At 45° this leaves 0.96 of full sensitivity at 4 c/deg, 0.72 at 8 c/deg
and 0.40 at 16 c/deg. The 2011 revision of the model dropped the term,
along with other changes, and fitted the data better [14].

* Deficit at high frequency, small below about 4 c/deg. *Confidence:
  high.*
* γ and λ. *Confidence: low to medium. I recalled them from [12], whose
  full text I could not open. Verify them before use.*

**Two cautions.**

* For broadband stimuli like natural images the anisotropy *reverses*:
  horizontal content is seen worst. This is the "horizontal effect" [15],
  and strokes are broadband edges.
* Above threshold, apparent contrast across orientations cannot be
  predicted from thresholds [16].

**Weight of diagonals.** I found no direct measurement. Fonts thin
diagonals by 3–6% (0.94–0.97). That is **practice**, usually explained by
darkening at apexes and crotches.

**For Arris.** Letters are identified through a single channel about 1.6
octaves wide [17, 18]. Its centre is set by the *stroke frequency*, the
strokes crossed per slice divided by the letter width [17]:

    f_channel = 10 c/deg × (f_stroke / 10 c/deg)^(2/3)

An Arris figure at the watch view is 0.55° wide, and a slice crosses
about 2.5 strokes. That gives f_stroke ≈ 4.5 c/deg and f_channel ≈ 6
c/deg, where the filter predicts a *threshold* deficit of about 15% at
45°.

Clock digits are far above threshold, though. There, perceived contrast
follows physical contrast (contrast constancy [19]). Across orientations
it does so less exactly [16], and for edges the sign may even reverse
[15].

So nothing here argues for compensating 45° strokes. The watch's 71%
diagonals look light because they carry 29% less ink. Keep
`View.oblique` near 0 for weight balancing.

* Channel at about 6 c/deg. *Confidence: medium. The formula is
  measured [17]; the 2.5 strokes per slice is my estimate.*

## 3. Overshoot

**Evidence.** I found no psychophysical measurement of how much a round
or pointed letter needs to overshoot. The values are **practice**:

* "perhaps 1% to 3%" for O [20];
* Karow: 3% for O, 5% for A [21];
* the measured neutral faces: 1.3–1.6% of cap height, 1.6–1.8% of
  x-height;
* the chamfered faces: 0.0% (`reference-fonts.md`).

*Confidence: high that fonts do this; nothing measures what the eye
needs.*

**Models.**

1. *The majority argument* (Frere-Jones [22]). Most of an O's top falls
   below full height, so the letter is judged short. This is a designer's
   explanation. It cannot be a full-width average: a circle's top contour,
   averaged across its width, lies 10.7% of the diameter below the apex.
   That would mean overshoots seven times larger than anyone draws.
2. *Centroid localisation.* The perceived position of a shape is the
   centroid of its filtered luminance [23, 24]. This makes the majority
   argument local to the top.
3. *Blur, then threshold.* Filter with the eye's PSF or CSF, and read the
   edge where the result crosses a fixed level. The Müller-Lyer illusion
   is a mislocation of line ends in this sense [25].
   `vision.perceived_top` is this model. Roughly, an apex retreats by a
   distance of order σ, and a curve of radius R ≫ σ by σ²/(2R). Points
   therefore need more overshoot than curves (Karow's 5% against 3%), and
   both need proportionally more at small sizes.

**A consistency check (my calculation).** Suppose the top is judged by
averaging the contour over ±w about the apex. A circle's mean drop is
then w²/(6R), and matching the drawn 1.5% needs w ≈ 0.42R. That is a
window 42% of the letter's width. The Arris 0's flat top is 4 of 9
modules, 44% of its width. Under the same window it needs no overshoot,
which agrees with the blur model and the chamfered faces. *Confidence:
medium; three independent lines agree.*

**Octagonal forms.** There is no literature. The octagonal faces (Chakra
Petch, Tomorrow, Turret Road) use no overshoot. Most round-cornered
square faces use none either; Michroma (2.1%) and Bai Jamjuree (1.1%) are
the exceptions. Arris's sharp points, the waists and beaks, do not bound
the figure, so they need none.

**Pixels.** 1.5% of a 36 px cap is 0.54 px. It either vanishes or
becomes a whole pixel (2.8%). PostScript hinting suppresses overshoot by
default below about 42 px per em (BlueScale 0.039625) [26]. At watch
sizes, overshoot is a rounding decision.

## 4. Optical centre and vertical bisection

**Demonstration.** Luckiesh [27]: the halves of an S or an 8 look equal,
but inverted "the difference is seen to be large". Also: "a perfect
square when viewed vertically appears too high". These are
demonstrations, not measurements.

**Measured.** People bisect vertical lines *above* the true midpoint.
Jeerakathil & Kirk [28] and Toth & Kirk [29] used lines 20–30 cm long.
They separated two biases:

* one towards the upper visual field;
* one towards whichever end is labelled "top", about 2 mm, under 1% of
  the length.

McCourt & Olafson [30] found the subjective midpoint raised with brief,
forced-choice presentations, so part of the bias is perceptual. The
horizontal version (pseudoneglect) reverses for short lines [31, 32], and
a 44-arcmin glyph is a very short line.

* Upward bias of order 1% of length. *Confidence: medium for the
  direction, low for its size at glyph scale.*

**Optical centre of a shape.** "A few percent above the geometric
centre" is design **folklore**. A "3.5%" figure circulates online, but I
could not trace it. The evidence is mixed:

* perceived centres depend on both contour and luminance distribution
  [33];
* centres of dot squares and rectangles were biased *downward* [34].

**Fonts.**

* Crossbars sit at 0.51–0.53 of the cap in neutral faces and 0.50–0.51
  in chamfered ones.
* 8 waists sit at 0.53 and 0.51.
* The upper bowl of the 8 is narrower than the lower (0.89 against 0.98).

A bar at 0.515 is 1.5% above centre, the same order as the bisection
bias. The neutral faces' 0.53 goes beyond anything measured.

**For Arris.** The geometric middle puts Arris with the chamfered faces
and the watch. It costs at most about 1% of cap height: 7 of 720 units,
a third of a pixel at 36 px. The 8's pinched upper bowl already makes
its top smaller. If text capitals look low, raise the bars of H, E and F
to 0.505–0.51, not to 0.53.

## 5. Irradiation, polarity and the grade axis

**Irradiation.** Westheimer [35] measured how far a black–white border
appears to move: about **0.4 arcmin** towards the black side, foveally,
at medium photopic luminance. He modelled it as optical spread followed
by a compressive (Naka–Rushton) response. Pons et al. [36] trace the
asymmetry to saturation in the ON pathway, which dark backgrounds and
optical blur make worse. So irradiation grows with:

* luminance and contrast;
* blur, including the large pupils of dark surroundings;
* smaller strokes: it is fixed in arcmin, so its share of a thin stroke
  is larger.

*Confidence: medium for 0.4 arcmin (one lab, a single border); high for
the directions.*

**Per stroke.** A light stroke on dark gains about 0.8 arcmin; a dark one
on light loses about 0.8. At the watch view (36 px cap at 200 ppi from
35 cm: 44 arcmin cap, 1.25 arcmin per pixel):

| Stem | arcmin | px | To look as drawn (−0.8′) | To match dark-on-light (−1.6′) |
|---|---|---|---|---|
| Regular, 90 u | 5.5 | 4.5 | −15%, GRAD ≈ −73 | −29%, past the axis |
| SemiBold (watch), 120 u | 7.3 | 6.0 | −11%, GRAD ≈ −55 | −22%, just past the axis (−109) |

*Confidence: low to medium. This applies a single-border model to
strokes, so treat it as an upper bound.*

**Legibility evidence.**

* Dark-on-light reads better [37]. Piepenbrock et al. attribute this to
  display luminance and pupil size [38, 39]. The advantage is larger for small characters [38]
  and in dark surroundings [40].
* With Roboto Flex and 459 people, grade had **no significant effect in
  dark mode**, while heavier grades helped in light mode [41]. A
  dark-palette grade is therefore an appearance choice, with no cost in
  reading. *Confidence: high.*
* Digits at threshold distance (Berger [57], via Crook & Baxter [47]):
  * In daylight the optimum stroke is 12.5% of height for black on white
    and **7.7%** for white on black, which is 38% thinner.
  * The optima converge as light falls, to about 15% and 12% at 3
    foot-candles.
  * Each optimum is a broad plateau about 5 points wide.

  Arris Regular (12.5%) sits on the dark-on-light optimum. The watch
  weight (16.7%) is past both, and GRAD −100 only reaches 13.3%.
  *Confidence: medium. Old threshold data, but the direction matches
  irradiation.*
* Signage **practice**: Clearview has a -W series for light on dark and a
  -B series for dark on light. They differ only in stroke width, the -W
  thinner, to counter halation [48, 49].

**Google and Apple.**

* Grade units are "the same as in the Weight axis" [42].
* The Grade axis proposal names dark mode as a use but gives no value
  [43].
* The only published number is for Material Symbols: "To reduce glare
  for a light symbol on a dark background, use a low grade", with **−25**
  as the example [44]. Material's icon pages give 0 for dark-on-light and
  −25 for light-on-dark [45].
* In Roboto Flex at Regular, −25 is about 4% of the stem.
* There is no official dark-mode GRAD for text. "Dark theme GRAD −25" in
  Android code copies the icon rule.
* Apple's HIG relies on "vibrancy and increased contrast" for text on
  dark backgrounds and advises against Ultralight, Thin and Light. It
  documents no change of weight or grade [46].

*Practice.*

**Rendering caveats.**

* Antialiasing in gamma space renders a 50%-coverage pixel at about 21%
  luminance. That thins light-on-dark text by up to about 0.3 px per edge
  and cancels part of the irradiation. Check how the watch blends.
* In print, reversed type is thickened to allow for ink spread. That
  habit does not apply to screens.

**Recommendation.** For light figures on a dark watch screen, at 36 px
cap height on 200 ppi: **GRAD −50**. That thins strokes by 10%, about
0.6 px of the 6 px watch stem. The reasons:

* It is the "look as drawn" correction for the watch weight under
  Westheimer's shift (−11%, GRAD ≈ −55).
* It is twice Google's icon value, which suits a dark surround and
  dilated pupils.
* It is small enough to leave the protected openings alone.

Adjust it for conditions:

* **OLED, or backlight on in the dark:** −50, up to −75 if proofs on the
  device still look heavy.
* **Pebble Time 2 transflective in daylight:** −25, because contrast is
  low and pupils are small (my reasoning; not measured). If the palette follows the ambient-light
  sensor, tie the grade to it.
* **Night or glance use:** −100, or one weight lighter plus −50,
  following Berger.
* **Never beyond −100.** The match-to-dark-on-light target (−22% to
  −29%) is an upper bound.
* **Pixels:** 0.6 px is one 2-bit antialiasing level per edge. On a 1-bit
  display, removing 1 px from the watch stem is GRAD ≈ −83.

## 6. Digit confusability

**Findings.**

* **Crook & Baxter, WADC TR 54-262 [47].** Experiments on back-lit Air
  Force–Navy (AND) dial digits at very low brightness, plus a review of
  Berger [57], Kuntz & Sleight, Soar, Aldrich and Lansdell [50]:
  * the worst pairs were **3–5, 4–6 and 0–6**, then **5–6 and 0–9**;
  * errors were asymmetric: 4 was read as 6 more often than 6 as 4;
  * recognisability, best to worst: **7 9 2 5 3 1 6 4 8 0**. Across
    studies 7 is near the top and 8 near the bottom ("the most
    persistently amorphous"), while 6 and 9 swap places;
  * the open 4 was read as 6 because its rising diagonal mimics the 6's
    "tail sloping up to the right";
  * "an open style, round-topped 3 is more recognizable than a
    flat-topped 3";
  * the 1 "looks dimmer", having the least ink;
  * Lansdell's angular numerals with filled loops beat Mackworth's when
    shown singly, but not in groups.

  *Confidence: medium. Consistent, but near-threshold, low-brightness
  dials.*
* **Seven-segment digits (van Nes & Bouma [51]).**
  * Digits with fewer segments are recognised better.
  * Confusion falls roughly in inverse proportion to the number of
    segments in which two digits differ.
  * Errors drift towards the *simpler* digit. At 16 m, 8 was read as 9
    fourteen times; 9 was read as 8 three times.
  * With tailed 6 and 9, the pairs one segment apart are 8–0, 8–6, 8–9,
    7–1, 9–3, 9–5 and 6–5. 7–1 was as common as 8–0.
  * The left verticals and the middle and lower bars carry most
    information. The authors recommend tail-less 6 and 9.
  * Segmented digits read worse than conventional ones at short
    exposures [52].

  *Confidence: high.*
* **Beier, Bernard & Castet [53]**, crowded strings in peripheral
  vision: a narrow 1 **without a foot**, **open apertures for 3 and 9**, a
  **7 with a straight leg** and no serif, and shorter skeletons
  generally. *Confidence: medium; one study.*
* **Faces designed for legibility** (mostly **practice**):
  * B612 was refined through lab and cockpit tests [54]. Its 1 has a
    foot, its 4 is open, and its 3 is flat-topped with a diagonal.
  * Atkinson Hyperlegible slashes its 0 and gives its 1 no foot.
  * Tiresias aimed at "maximum differentiation" [55].
  * FE-Schrift replaced DIN 1451 on German plates. It dropped its
    slashed zero because it "could be mistaken for an 8", and uses a
    short slash at the upper right instead [56].
  * I found no confusion data for DIN 1451, OCR-B or Clearview's
    figures.

**Arris's figures.**

* **1 with a 45° flag and slab foot.** The foot rules out 1/7 and adds
  ink to the "dim" digit. Beier's result against feet comes from crowded
  peripheral strings, and B612 and most monospaced faces keep a foot.
  *Keep it*, at 55–75% of the advance.
* **Open 4.** The documented 4→6 error needs a 6 with a rising tail, and
  Arris's 6 has a flat arm. *Keep it*, and keep the clip's gap visible at
  the smallest size and the heaviest weight.
* **7 with a straight 2:1 leg.** This is what Beier recommends, and 7
  tops every ranking. *Good.*
* **8 with a pinched upper bowl.** 8 is the hardest digit, and errors
  drift from it to 9, 0 and 6. The pinched top and the sharp waist
  notches separate it from 0. *Keep them, and protect the notch depth at
  Black and at positive grade.*
* **6 and 9 as exact rotations.** Upright, the position of the bowl is a
  coarse cue that survives blur. The pairs that fail in the studies are
  6–8, 9–8, 5–6, 3–9, 0–6 and 0–9, not 6–9.
  * The flat arms act like seven-segment tails, one stroke from 8 (and
    from 5 and 3). Keep each arm-to-bowl aperture at least as tall as the
    3's and 5's openings.
  * The upper-half effect (§4) makes the 9's bowl look a little larger
    than the 6's. A slightly smaller 9 bowl is optional.
  * Rotation is a real risk only if figures are shown turned.
* **3 and 5 with flat tops.** This is the weak point. 3–5 is Crook &
  Baxter's worst pair. Their standard 3 was flat-topped, like Arris's, and
  they found a round-topped open 3 better. Octilinear remedies:
  * cut the 3's top-left corner as a beak, as the 2 already does. This is
    the octilinear "round top";
  * keep the 5's upper-left stem full height;
  * keep the 3's left openings at least a stem wide.

  The flat 3 is a watch quirk, so offer the beaked 3 as a stylistic set,
  or make it the default at small sizes.
* **0 as a tall octagon, with optional dot or slash.** A clock has no
  letters, so 0/O does not arise. A dot or slash only adds ink in the
  centre, which moves 0 towards 8, as FE-Schrift found. *Use the plain 0
  for clocks.* If a marked zero is needed, a short slash clear of the
  centre is better than a dot or a full slash.
* **3 and 8.** They differ in the left verticals, the most informative
  strokes [51]. Keep the 3's beak short so its lower-left opening stays
  open.

## 7. A computational legibility model

This extends `arris.vision` along the lines of Watson & Ahumada's acuity
model [58, 59]: optics, then a neural filter, then noise, then an ideal
decision. The decision stage is Pelli et al.'s ideal observer [60, 61].

1. **Geometry.**
   * θ_cap = 2·atan(h_cap / 2D). For the watch, 4.57 mm at 350 mm gives
     0.748°.
   * ppd = px_per_cap / θ_cap, and f = fftfreq(N) · ppd, as in
     `vision.perceive`.
   * Resolve about 60 c/deg, i.e. ppd ≥ 120, which means px_per_cap ≥ 90
     at the watch view.
2. **Display.**
   * Rasterise at the device resolution: 36 px cap, with the real
     antialiasing and 2-bit levels.
   * Upsample with a box pixel, whose MTF is |sinc(f / f_px)| with
     f_px ≈ 48 px/deg.
   * Convert code values to linear luminance.
3. **Optics.** Use Watson's mean optical MTF [62], with the pupil
   diameter d from the Watson–Yellott formula [63]:

       M(f, d) = D(f, d) · (1 + (f/u1(d))²)^−0.62
       u1(d)   = 21.95 − 5.512 d + 0.3922 d²      (c/deg; d in mm)

   D is the diffraction MTF of the pupil. *Confidence: medium. The
   coefficients are recalled; check them against [62].*
4. **Polarity, for GRAD.**
   * After the optics, apply R = I^n / (I^n + I50^n), as Westheimer did
     [35]. Pons et al. used n > 1, with I50 = 0.1 for ON and 0.5 for OFF
     on normalised luminance [36].
   * Calibrate it so that a single border shifts 0.4 arcmin.
   * Place each stroke edge at the midpoint of R. The GRAD that makes
     light-on-dark and dark-on-light widths equal is the model's answer
     to §5.
5. **Neural CSF.**
   * *Mannos–Sakrison* [64], as now. It has no luminance term:

         A(f) = 2.6 (0.0192 + 0.114 f) · exp(−(0.114 f)^1.1)     peak ≈ 8 c/deg

   * *Barten's simplified formula* [65] responds to luminance and size.
     L is in cd/m², and X0 is the field size in degrees (about 2 θ_cap).
     It already includes the optics, so use it *instead of* step 3:

         S(f) = 5200 exp(−0.0016 f² (1 + 100/L)^0.08)
                / sqrt((1 + 144/X0² + 0.64 f²) · (63/L^0.83 + 1/(1 − exp(−0.02 f²))))

   * The full 1999 model is
     `colour.contrast.contrast_sensitivity_function_Barten1999` [66].
   * For blur measurements, keep the current "held at 1 below the peak"
     low-pass. For identification, use the band-pass.
6. **Ideal observer.**
   * Each template T_k is steps 2–5 applied to one figure in its tabular
     slot.
   * Present T_i plus white Gaussian noise of standard deviation σ. The
     ideal observer picks

         k̂ = argmax_k ( O·T_k − ½‖T_k‖² )

   * A Monte Carlo run (10⁴ trials per digit) gives the confusion matrix.
     Pairwise, d′_ij = ‖T_i − T_j‖ / σ and P(i→j) ≈ Φ(−d′_ij / 2).
   * Fix σ so the reference design scores about 70% at a near-threshold
     size (6–10 arcmin cap). Compare variants, grades and polarities at
     that σ.
   * Also report each figure's perimetric complexity (perimeter² ÷ ink
     area). Human efficiency falls in inverse proportion to it [60].
   * Model and human confusions correlated 0.5–0.8 off the diagonal for
     simple optotypes [59]. Use the model to rank, not to predict error
     rates.
7. **Validate.**
   * On seven-segment digits, the model should reproduce van Nes &
     Bouma's difference-segment rule and their worst pairs [51].
   * On an AND-style set, it should put 8 near the worst and 7 near the
     best [47].
   * Then run Arris at 8–45 arcmin, at GRAD −100 to +50, in both
     polarities. Watch the worst-pair d′, especially 3–5, 3–9, 5–6, 6–8,
     0–8 and 4–6.

## Recommendations for Arris

1. **Horizontals at 0.90 → 0.85: keep.** The anisotropy (3–7%) explains
   the direction and about half the size. The rest is practice, rightly
   taken from fonts (§1).
2. **Diagonals at 0.94: keep, as practice about junctions.** Don't
   compensate for orientation at text or watch sizes, and keep
   `View.oblique` near 0 (§2).
3. **No overshoot on octagonal bowls: keep.** A flat top 44% of the width
   needs none under a local-window or blur model. Revisit only for pointed
   apexes below about 11 arcmin (§3).
4. **Crossbars at 0.50: keep.** If text capitals look low, use 0.505–0.51,
   never 0.53 (§4).
5. **GRAD for dark palettes: −50 at watch size** (strokes −10%, about
   0.6 px) (§5).
   * Transflective screen in daylight: −25.
   * Night or glance use: −100, or one weight lighter plus −50.
   * Settle the final value with the §7 polarity model and proofs on the
     device.
6. **Figures (§6).**
   * Use the plain 0 for clocks. A marked zero should use a short,
     off-centre slash.
   * Add a beaked-top 3 as an alternate, the default at small sizes, to
     break 3–5.
   * Keep the 1's foot at 55–75% of the advance.
   * Keep the 6 and 9 apertures at least as tall as the 3's and 5's.
   * Protect the 8's waist notch.
7. **Build the §7 model.** Validate it on seven-segment digits, then use
   it to rank figure variants and to set GRAD.

## Sources

DOIs checked against Crossref or Europe PMC unless noted.

1. Mamassian & de Montalembert (2010). A simple model of the
   vertical–horizontal illusion. *Vision Research* 50, 956–962.
   https://doi.org/10.1016/j.visres.2010.03.005
2. Mikellidou & Thompson (2013). The vertical-horizontal illusion:
   assessing the contributions of anisotropy, abutting, and crossing.
   *Journal of Vision* 13(8):7. https://doi.org/10.1167/13.8.7
3. Prinzmetal & Gettleman (1993). Vertical-horizontal illusion: one eye is
   better than two. *Perception & Psychophysics* 53, 81–88.
   https://doi.org/10.3758/BF03211717
4. de Waard, Van der Burg & Olivers (2019). A thickness illusion:
   horizontal is perceived as thicker than vertical. *Vision* 3(1):1.
   https://doi.org/10.3390/vision3010001 (open:
   https://pmc.ncbi.nlm.nih.gov/articles/PMC6802759/)
5. Campbell, Kulikowski & Levinson (1966). The effect of orientation on the
   visual resolution of gratings. *J. Physiol.* 187, 427–436.
   https://doi.org/10.1113/jphysiol.1966.sp008100
6. Mitchell, Freeman & Westheimer (1967). Effect of orientation on the
   modulation sensitivity for interference fringes on the retina. *JOSA*
   57, 246. https://doi.org/10.1364/JOSA.57.000246
7. Appelle (1972). Perception and discrimination as a function of stimulus
   orientation: the "oblique effect" in man and animals. *Psychological
   Bulletin* 78, 266–278. https://doi.org/10.1037/h0033117
8. Quinn & Lehmkuhle (1983). An oblique effect of spatial summation.
   *Vision Research* 23, 655–658.
   https://doi.org/10.1016/0042-6989(83)90072-X
9. Camisa, Blake & Lema (1977). The effects of temporal modulation on the
   oblique effect in humans. *Perception* 6, 165–171.
   https://doi.org/10.1068/p060165
10. Tootle & Berkley (1983). Contrast sensitivity for vertically and
    obliquely oriented gratings as a function of grating area. *Vision
    Research* 23, 907–910. https://doi.org/10.1016/0042-6989(83)90060-3
11. Murray, Elliott, Pallikaris, Werner, Choi & Tahir (2010). The oblique
    effect has an optical component. *Journal of Vision* 10(11):10.
    https://doi.org/10.1167/10.11.10
12. Watson & Ahumada (2005). A standard model for foveal detection of
    spatial contrast. *Journal of Vision* 5(9):6, 717–740.
    https://doi.org/10.1167/5.9.6
13. Berkley, Kitterle & Watkins (1975). Grating visibility as a function of
    orientation and retinal eccentricity. *Vision Research* 15, 239–244.
    https://doi.org/10.1016/0042-6989(75)90213-8
14. Ahumada & Watson (2011). Updating the Standard Spatial Observer for
    contrast detection. NASA technical report.
    https://ntrs.nasa.gov/citations/20110015437
15. Essock, DeFord, Hansen & Sinai (2003). Oblique stimuli are seen best
    (not worst!) in naturalistic broad-band stimuli: a horizontal effect.
    *Vision Research* 43, 1329–1335.
    https://doi.org/10.1016/S0042-6989(03)00142-1
16. Bowker & Mandler (1981). Apparent contrast of suprathreshold gratings
    varies with stimulus orientation. *Perception & Psychophysics* 29,
    585–588. https://doi.org/10.3758/BF03207375
17. Majaj, Pelli, Kurshan & Palomares (2002). The role of spatial frequency
    channels in letter identification. *Vision Research* 42, 1165–1184.
    https://doi.org/10.1016/S0042-6989(02)00045-7
18. Solomon & Pelli (1994). The visual filter mediating letter
    identification. *Nature* 369, 395–397. https://doi.org/10.1038/369395a0
19. Georgeson & Sullivan (1975). Contrast constancy: deblurring in human
    vision by spatial frequency channels. *J. Physiol.* 252, 627–656.
    https://doi.org/10.1113/jphysiol.1975.sp011162
20. Evans & Sherin (2013). *The Graphic Design Reference & Specification
    Book*, p. 28, as cited at
    https://en.wikipedia.org/wiki/Overshoot_(typography). Practice.
21. Karow, *Digital Formats for Typefaces* (URW), p. 26, as cited at the
    same page. Practice.
22. Frere-Jones, interviewed in Slate (2015).
    https://slate.com/human-interest/2015/04/tobias-frere-jones-explains-the-optical-illusion-that-tricks-our-brains-into-perceiving-typeface-letters-are-of-equal-height.html
23. Whitaker, McGraw, Pacey & Barrett (1996). Centroid analysis predicts
    visual localization of first- and second-order stimuli. *Vision
    Research* 36, 2957–2970. https://doi.org/10.1016/0042-6989(96)00031-4
24. Vos, Bocheva, Yakimoff & Helsper (1993). Perceived location of
    two-dimensional patterns. *Vision Research* 33, 2157–2169.
    https://doi.org/10.1016/0042-6989(93)90014-N
25. Morgan, Hole & Glennerster (1990). Biases and sensitivities in
    geometrical illusions. *Vision Research* 30, 1793–1810.
    https://doi.org/10.1016/0042-6989(90)90160-M
26. Adobe (1990). *Adobe Type 1 Font Format*, BlueScale (default
    0.039625, i.e. 10 pt at 300 dpi).
    https://adobe-type-tools.github.io/font-tech-notes/pdfs/T1_SPEC.pdf
27. Luckiesh (1922). *Visual Illusions: Their Causes, Characteristics and
    Applications*. Van Nostrand. https://www.gutenberg.org/ebooks/36297
28. Jeerakathil & Kirk (1994). A representational vertical bias.
    *Neurology* 44, 703–706. https://doi.org/10.1212/WNL.44.4.703
29. Toth & Kirk (1996). A normal bias toward a pictorially defined top in
    line bisection. *Can. J. Neurol. Sci.* 23, 110–113.
    https://doi.org/10.1017/S0317167100038816
30. McCourt & Olafson (1997). Cognitive and perceptual influences on visual
    line bisection. *Neuropsychologia* 35, 369–380.
    https://doi.org/10.1016/S0028-3932(96)00143-1
31. McCourt & Jewell (1999). Visuospatial attention in line bisection:
    stimulus modulation of pseudoneglect. *Neuropsychologia* 37, 843–855.
    https://doi.org/10.1016/S0028-3932(98)00140-7
32. Jewell & McCourt (2000). Pseudoneglect: a review and meta-analysis of
    performance factors in line bisection tasks. *Neuropsychologia* 38,
    93–110. https://doi.org/10.1016/S0028-3932(99)00045-7
33. Proffitt, Thomas & O'Brien (1983). The roles of contour and luminance
    distribution in determining perceived centers within shapes.
    *Perception & Psychophysics* 33, 63–71.
    https://doi.org/10.3758/BF03205866
34. Liby & Friedenberg (2010). Visual estimation of three- and four-body
    center of mass. *Perceptual and Motor Skills* 110, 195–212.
    https://doi.org/10.2466/pms.110.1.195-212
35. Westheimer (2007). Irradiation, border location, and the
    shifted-chessboard pattern. *Perception* 36, 483–494.
    https://doi.org/10.1068/p5646
36. Pons, Mazade, Jin, Dul, Zaidi & Alonso (2017). Neuronal mechanisms
    underlying differences in spatial resolution between darks and lights
    in human vision. *Journal of Vision* 17(14):5.
    https://doi.org/10.1167/17.14.5
37. Buchner & Baumgartner (2007). Text–background polarity affects
    performance irrespective of ambient illumination and colour contrast.
    *Ergonomics* 50, 1036–1063. https://doi.org/10.1080/00140130701306413
38. Piepenbrock, Mayr & Buchner (2014). Positive display polarity is
    particularly advantageous for small character sizes. *Human Factors*
    56, 942–951. https://doi.org/10.1177/0018720813515509
39. Piepenbrock, Mayr & Buchner (2014). Smaller pupil size and better
    proofreading performance with positive than with negative polarity
    displays. *Ergonomics* 57, 1670–1677.
    https://doi.org/10.1080/00140139.2014.948496
40. Dobres, Chahine & Reimer (2017). Effects of ambient illumination,
    contrast polarity, and letter size on text legibility under glance-like
    reading. *Applied Ergonomics* 60, 68–73.
    https://doi.org/10.1016/j.apergo.2016.11.001
41. Palmén, Gilbert & Crossland (2023). How bold can we be? The impact of
    adjusting font grade on readability in light and dark polarities.
    *CHI '23*. https://doi.org/10.1145/3544548.3581552. Earlier summary:
    Gilbert, Feldman, Simpson & Al-khazraji (2022), "Adjusting Grade for
    Mode", https://m3.material.io/blog/readability-research
42. Google Fonts axis registry, Grade.
    https://github.com/googlefonts/axisregistry/blob/main/Lib/axisregistry/data/grade.textproto
43. Berlow & Crossland (2020). Grade axis proposal summary.
    https://github.com/TypeNetwork/Opentype-1.8-Axis-Proposal/blob/gh-pages/proposal/Grade/ProposalSummary.md
44. Google Fonts, Material Symbols developer guide (grade section).
    https://developers.google.com/fonts/docs/material_symbols
45. Material Design 3, Icons: applying icons. Script-rendered, so I could
    not fetch the text directly. https://m3.material.io/styles/icons/applying-icons
46. Apple Human Interface Guidelines: Dark Mode and Typography.
    https://developer.apple.com/design/human-interface-guidelines/dark-mode
    and https://developer.apple.com/design/human-interface-guidelines/typography
47. Crook & Baxter (1954). *Design of Digits*. WADC Technical Report
    54-262, Wright Air Development Center. Reviews Berger, Kuntz &
    Sleight, Soar, Brown et al., Lansdell, Aldrich and others.
    https://contrails.library.iit.edu/item/153424
48. Clearview Type System, "Anatomy" (designers' documentation of the
    -W/-B split). Practice. https://www.clearviewhwy.com/home/anatomy/
49. Garvey, Klena, Eie & Meeker (2016). Legibility of the Clearview
    typeface and FHWA Standard Alphabets on negative- and positive-contrast
    signs. *Transportation Research Record* 2555, 28–37.
    https://doi.org/10.3141/2555-04
50. Lansdell (1954). Effect of form on the legibility of numbers.
    *Canadian Journal of Psychology* 8, 77–79.
    https://doi.org/10.1037/h0083603
51. van Nes & Bouma (1980). On the legibility of segmented numerals.
    *Human Factors* 22, 463–474. https://doi.org/10.1177/001872088002200407
    (open: https://pure.tue.nl/ws/files/4403505/734572.pdf)
52. Plath (1970). The readability of segmented and conventional numerals.
    *Human Factors* 12, 493–497. https://doi.org/10.1177/001872087001200510
53. Beier, Bernard & Castet (2018). Numeral legibility and visual
    complexity. *DRS 2018*. https://doi.org/10.21606/drs.2018.246
54. Vinot & Athènes (2012). Legible, are you sure? An experimentation-based
    typographical design in safety-critical context. *CHI '12*, 2287–2296.
    https://doi.org/10.1145/2207676.2208387 (open:
    https://enac.hal.science/hal-01022511)
55. Tiresias (RNIB; Sharville and Gill). Practice.
    https://en.wikipedia.org/wiki/Tiresias_(typeface)
56. FE-Schrift (Hoefer; tests at Giessen 1978–80). Practice.
    https://en.wikipedia.org/wiki/FE-Schrift
57. Berger (1944). Stroke-width, form and horizontal spacing of numerals as
    determinants of the threshold of recognition, I and II. *Journal of
    Applied Psychology* 28, 208–231 and 336–346.
    https://doi.org/10.1037/h0054045 and https://doi.org/10.1037/h0061189
58. Watson & Ahumada (2008). Predicting visual acuity from wavefront
    aberrations. *Journal of Vision* 8(4):17. https://doi.org/10.1167/8.4.17
59. Watson & Ahumada (2012). Modeling acuity for optotypes varying in
    complexity. *Journal of Vision* 12(10):19.
    https://doi.org/10.1167/12.10.19
60. Pelli, Burns, Farell & Moore-Page (2006). Feature detection and letter
    identification. *Vision Research* 46, 4646–4674.
    https://doi.org/10.1016/j.visres.2006.04.023
61. Pelli, Farell & Moore (2003). The remarkable inefficiency of word
    recognition. *Nature* 423, 752–756. https://doi.org/10.1038/nature01516
62. Watson (2013). A formula for the mean human optical modulation transfer
    function as a function of pupil size. *Journal of Vision* 13(6):18.
    https://doi.org/10.1167/13.6.18
63. Watson & Yellott (2012). A unified formula for light-adapted pupil
    size. *Journal of Vision* 12(10):12. https://doi.org/10.1167/12.10.12
64. Mannos & Sakrison (1974). The effects of a visual fidelity criterion on
    the encoding of images. *IEEE Trans. Information Theory* 20, 525–536.
    https://doi.org/10.1109/TIT.1974.1055250
65. Barten (2003). Formula for the contrast sensitivity of the human eye.
    *Proc. SPIE* 5294, 231–238. https://doi.org/10.1117/12.537476
66. colour-science, `contrast_sensitivity_function_Barten1999`
    (implements Barten 1999, https://doi.org/10.1117/3.353254).
    https://colour.readthedocs.io/en/latest/generated/colour.contrast.contrast_sensitivity_function_Barten1999.html
