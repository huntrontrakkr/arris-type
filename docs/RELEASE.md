# Releasing Arris

## Cutting a release

1. Set `VERSION` in `src/arris/version.py` (the fonts' version string,
   `head.fontRevision` and the unique ID all follow it; outside the drawing
   cache's key, so it redraws nothing).
2. Rebuild everything: `tools/rebuild.sh` (every static weight in a
   process of its own, then both variable fonts with their interpolation
   check, then pytest and fontbakery side by side, and the zip;
   `tools/rebuild.sh extras` also remakes the proofs, the specimen's
   WOFF2s and the presentation). A timing line per phase goes to
   `build/scripts/logs/time.log`.
3. Read `build/scripts/logs/post.log`: pytest passes, fontbakery reports
   no FAIL and no ERROR for the static, variable and Mono sets.
4. Package: `uv run python tools/package.py` writes
   `build/release/Arris-<version>.zip` (static, variable, web, OFL.txt,
   AUTHORS.txt, README.md). It refuses fonts that do not carry the release
   version, the licence URL and installable embedding.
5. Tag the commit `v<version>`; attach the zip to the GitHub release.

Or let GitHub do steps 2 to 5: write the release's section below, set
`VERSION`, merge to `main`, and push the tag (`git tag v<version> &&
git push origin v<version>`). The Release workflow
(`.github/workflows/release.yml`) builds each static family and each
variable font on a runner of its own, keeping each job's drawing cache
between runs, then runs pytest and fontbakery (any FAIL or ERROR stops
it), packages the zip, and publishes the release with the zip and this
file's section for the version. Run it by hand (Actions, Release, Run
workflow) to build and check without publishing: the zip is the run's
artifact; run it on main with "publish" ticked to release that commit
without pushing a tag (it tags `v<version>` itself, and refuses a version
already tagged). The runners have no GPU, so the workflow skips
`tools/vf_spikes.py`; run it on a GPU machine before tagging when the
variable fonts' masters or interpolation change.

After the GitHub release is public, the Release workflow dispatches
`npm.yml` on the release tag and waits for it to publish `@arristype/arris`.
npm authorizes `npm.yml` in `huntrontrakkr/arris-type` as a trusted
publisher. To retry, run the npm workflow with the font version.

## Licence and metadata

The fonts and the glyph drawings (`src/arris/glyphs/`): SIL Open Font
License 1.1 (`OFL.txt`); the engine, tools, tests and documentation: MIT
(`LICENSE`). Copyright The Arris Project Authors (`AUTHORS.txt`); no
Reserved Font Name. Every font carries the copyright
(name 0), the licence and its URL (13, 14), embedding installable (fsType
0). The vendor ID is `NONE` (unregistered): register one with Microsoft
before a commercial distribution if wanted.

## 1.017

How the letters stand together. Six causes, each measured, and five
letters redrawn.

- Past the Regular the letters give white to their stems, as the letters
  of other families do. Arris got bolder outward: almost every unit a stem
  gained went onto the letter's width. Read at one boldness and one
  x-height against 60 grotesque, geometric and squared families
  (`tools/width_survey.py`), its n's counter was 20% narrower at Black
  than at Regular where theirs is 38%, and a line of lowercase 6% longer
  at Bold and 11% at Black for their 2.4% and 3.9% (the owner: "this gets
  far too bold widthwise"). At Regular it sets as they do (a letter of a
  line 0.92 of the x-height, their median 0.92), so nothing changes there
  or below. Past it a lowercase letter's white now gives 0.59 of a module
  for each watch stem its stem gains, a capital's, a figure's and a
  sign's 0.45 (`instances.white_given`, `letterframe.white_scale`): at
  Black the n's counter is 38% narrower and the H's 29%, a line of
  lowercase 4.5% longer and at Bold 2.5%, a line of capitals 3.7% and
  2.2% (theirs 4.4% and 2.5%). Tabular figures widen three
  quarters of a unit for each unit of stem (a unit and a half before:
  `instances.FIG_GIVEN`; the zero's counter 31% narrower at Black for
  19%). The italic gives as the upright does. The watch's own drawing
  (WTCH 100) keeps its modules and Arris Mono its cell: neither changes.
  The mathematical operators, the arrows and the technical signs keep
  their widths (`draw.white_of`): bars a set white apart and strokes at
  45 degrees have no counter to give, and narrowed with the letters ⊦ lost
  its stem to a wedge at Black, ⊫ its two stems to a slab, and the feet of
  ≎ ran out past its bars. Punctuation and currency give as the capitals
  do.

  What a narrower body could not hold as it was is kept by rule. A
  one-stem letter (E F K L T Z, k z) gives the share of its body the H or
  the n gives of its own, not the white of its modules
  (`letterframe.narrowed`): its open side holds an arm or a diagonal, and
  with all of it giving the k and the z stood at 0.90 of their share at
  Black. The y, whose foot is measured on the m's arch, is measured in the
  bodies before they gave and gives as the n does. The f and the t give
  on the arm's side only, and no more than leaves the arm 1.1 stems past
  the stem (`lower.narrow_frame`, `lower.narrow_width`; their crossing is
  the next point). The j keeps a break of white in its hook. The kink where an arch or a bowl leaves its
  stem is what it was, to ExtraBold (the owner: "preserving the kink ...
  at later weights to a small degree so that it matches what we had"):
  where no step is drawn under a shoulder its diagonal lies inside the
  arch and needs none of the counter's room (`lower.shoulder`), and
  without that the n was square from 725. The Q's tail is held to the
  bowl's own width where that is less than its share of the stem, and the
  cursive e's eye to as much less as its counter has given
  (`Opening.across`): held to whites the narrower letters cannot have,
  the Q's bars thinned to 0.7 of the O's at Black and the e's top and bar
  to 0.70 (now none, and 0.82; the e's were 0.92). The florin and the ϰ
  keep their bodies (`letterframe.ungiving`): the florin's crossbar and
  hook ran into a wedge at Black as the f's did, and the ϰ lost its curls.
  Every glyph was compared with its drawing before the narrowing, at
  eighteen places of the family (the Regular and lighter, Arris Mono and
  the watch's own drawing unchanged, to the last point).
- The f and the t keep the crossing they have at 650, to Black. The
  crossbar's stub left of the stem is a quarter of the letter's white,
  about 70 units at every weight, while the cuts on it double from Regular
  to Black: at SemiBold its end still has a face between its two cuts, at
  Bold they met in a point, and from ExtraBold the stub was one plane with
  the cut of the t's top and the f's hook, a wedge on the stem's side (the
  owner: "it just turns into this gnarled, ugly thing when it comes to the
  way that everything joins ... especially for smaller ones, it just looks
  like a big old knot"). And the crossbar ended half a stem short of the
  arm, 45 units at Regular and 88 at Black ("they don't keep track of the
  same length"). Shown the stub going into the stem between SemiBold and
  Bold with the crossbar coming out to the arm's end as it went, the owner
  chose the letter half way: "Look at how it is currently at weight 650
  and make it the exact same shape throughout all the way to 900. It needs
  to not move one bit. It needs to be exactly the same for both the
  stems." To SemiBold the two letters are as they were. From 650 the stub
  is a break and a seventeenth deep (two legs of its crotch's fill, at
  Black), a face between two cuts that take its whole depth, the same
  points on the f and on the t, at every weight (`lower.stub`,
  `lower.narrow_stub`). The crossbar ends level with the arm and the foot
  from 650 (`lower.bar_short`): at 650 it stood an edge break short of
  them, and held so to Black it read as short ("they don't seem to be
  sticking out in level with either the foot or the ascender,
  respectively, with the cross"). The stem stands that much nearer the body's left
  edge and the body is as much narrower: 356 units at 650 for 381 at
  SemiBold, 413 at Black. The rule reads the font's weight past its
  Regular (`Params.past`), so the watch's own drawing keeps its f and t.
- The l lands as the k's leg does. Its cut ended upright, an edge break
  of face over its own break; the k's leg, at the same angle and the same
  thickness, ends in a flat on the baseline and one break up to a point
  (the owner: "the L kind of descends and it lands ... the K has descender
  at the same angle, but the way that it hits it is kind of different, the
  way that the chamfering looks. The L should follow the form that K
  sets"). The l's end is now the leg's at every weight, Thin to Black: the
  same flat on the line, to a tenth of a unit, and the same point. Its
  body is what it was; the cut stands a break lower on the stem.
- The r grows against the n as it gets bolder. At six ninths of the H's
  width for every weight (below) its arm shrank as the stem grew, and
  from Bold nothing of it was left but the end of the shoulder's diagonal
  on the stem's corner (the owner: "a little tiny clown nose"). Other
  families' r gains on their n with weight: its advance 0.65 of the n's
  at Regular and 0.69 at Black across the 60. Shown the r at eight
  ninths, seven, six growing to eight, six growing to seven and six, the
  owner chose six to the Regular growing to seven at Black
  (`lower.r_width`): its advance 0.75 of the n's at Regular, 0.78 at Bold
  and 0.80 at Black. It grows by the font's weight past its Regular
  (`Params.past`): the watch's own drawing keeps six ninths.
- Inside corners stop growing at the Regular. One chord cut every corner
  that sticks out and filled every corner that points in, a quarter of
  the stem long. A cut takes ink off the outside of a letter; a fill puts
  it into a counter or a join, and on one leg the fills grew as fast as
  the stems while the whites they stand in shrank: from Bold the insides
  of the letters clogged (the owner: "the interior ... is getting really
  fat because we chamfer the bits at a certain level and it just doesn't
  look right"). Other families tighten their joins as they get bolder:
  across 37 measured, the widest spot at a join is 1.18 stems at Regular
  and 1.10 at Black, where Arris stood at 1.38 at every weight. A fill
  now has the weight's own leg up to the Regular and the Regular's from
  there to Black (`draw.fill_leg`, 22.5 units where Black's cut is 44);
  the cuts grow as they did. A bowl's inside chamfer is what its strokes
  leave of it, down to the same leg: from ExtraBold it was held at an edge
  break (the O's 44 units for 32 at Black), the stroke thicker round the
  corner than along its sides. Nothing changes at Regular or lighter in
  the upright. At Black the widest spot in the upright's b d g p q y goes
  from 1.32 stems to 1.23, the a's and the e's from 1.28 to 1.18. The
  watch's own drawing (WTCH 100) keeps one leg for every corner.
- The italic fills a crotch one leg, as the upright does. Where a
  diagonal meets a stem the italic kept the pixel rule's fill, two legs
  along the stem: twice the upright's ink where a diagonal already lies
  on a stem, 88 units up each side of the cursive e's eye at Black, whose
  sides are 178. This one changes the italic at every weight, a little:
  the notches over its branches (n h m r), its k, v, w, y and z and the
  e's eye end in a smaller cut.
- A shoulder keeps its neck. An arch's or an arm's diagonal started an
  edge break into its stem, and the fill in the crotch over it was the
  rest of the join: with a smaller fill the neck, where the stroke is
  thinnest, would have lost that ink (the cursive r's arm at Black, 0.54
  of a stem across where it leaves the stem, went to 0.37 in the making).
  The diagonal starts deeper by what the fill is short
  (`lower.shoulder_enter`): the notch stands on the stem where it always
  did, and ends in the small cut. The cursive r's neck is 0.71 of a stem
  at Regular (0.60) and 0.73 at Black (0.54); where a shoulder goes
  square, and at which weight, is as it was, and the step under an arch
  keeps a flat the outline holds (`lower.STEP_KEPT`: the cursive m's
  arches, which rise half as far as the n's, would have lost theirs).
- The cursive e gives only its top and its bar for its eye. Its eye was
  kept open by thinning every horizontal of the letter, the foot with the
  top, and then the bar: from SemiBold the foot was 0.70 of every other
  letter's (104 units beside the a's and the o's 149 at Black), the top
  fell from 98 units at 550 to 73 at 600 and the bar from 121 at Bold to
  88 at Black, and the exit, a reach that shrinks with the white, stood
  28 units over the foot at Black for 59 at Regular (the owner: "there's
  definitely something weird going on with the thicknesses towards the
  black ... the little bit at the bottom ... isn't nearly as thick").
  The back and the foot are now the alphabet's strokes at every weight,
  the exit stands a break and a half over the foot at least, and the top
  and the bar give way together, for the eye alone: full to Bold, 0.97 of
  their own at ExtraBold and 0.92 at Black (137 and 135 units beside the
  foot's 149), never thinner than at the weight before
  (`italic_forms._e_strokes`; the æ's e alike). The eye is held from
  where it first falls short of half a stem, shrinking as the stem grows.
- A step never closes past the end of the edge it slides along
  (`geom._close_jogs`): under the ç at Black, where the c's corner, a
  flat of 33 units and the fill into the cedilla's stem stand over a
  stem side of 25, the fill slid 33 down it and the outline crossed
  itself by four units.
- Every descender stands on one line. The g's and the y's hooks went
  deeper than the p, q and j from Bold (to make room under the bowl: 34
  units at Bold, 70 at Black), so a line of text stood on two descender
  lines. A weight now has one: three modules to SemiBold, then what the
  g's hook needs under its bowl (a horizontal and the least white over
  it), 205 units at Bold, 230 at ExtraBold, 250 at Black, the font's
  descent (`params.descender_line`). Brackets, signs and marks keep their
  own depth (`Params.under`).
- The hooks of g and y are as heavy as the letters' other strokes. They
  were thinner from Light up (57 units to the bowl's 79 at Regular, about
  three quarters), and it read as a mistake: a reader on r/typography
  circled it. The hook measured its white past the inner leg of its own
  corner, not from bar to bar, and thinned before it made room. On the
  weight's descender line it keeps its weight at every weight.
- The hooks of g and y end in a beak. They ran left and stopped flat. A
  hook now turns up at its end through a cut corner into a short
  terminal, as the c's arms end, so the swoop is cut at both ends as the
  top of the 8 is (the owner: "a nice kind of bracketed curve to it").
  The terminal's tip, a short end and not a bar, keeps three quarters of
  the least white under what stands over it (`lower.BEAK_WHITE`). The
  italic's hooks are as they were.
- A letter with one stem keeps its share of the line. Stems alone added
  width, so from Regular to Black the H grew a fifth and the E, K, L, T,
  Z, f, k, t and z not at all: each lost a fifth of its share (0.80 to
  0.84 of what it had; in hand-drawn faces 0.93 to 1.08,
  `tools/letter_shares.py`). Their arms, thicker in a body no wider, were
  stubs, and the K's and k's diagonals rooted in one block along the stem.
  Past Regular such a letter now widens by what its stem has grown
  (`letterframe.letter_width`); Regular and lighter are as they were. The
  r takes a share of the H's width instead: it had been a third wider
  than the n at Thin and a tenth at Regular, its arm long for the letter
  (six ninths to the Regular, below, growing to seven at Black, above).
- Open sides are spaced as hand-spaced faces space them. The spacing
  counts the white beside a letter to a depth, and counted it a fifth of
  the zone deep: twice what ten hand-spaced sans faces count (fitted to
  their side bearings, `tools/spacing_depth.py`: 0.07 to 0.17 of the
  x-height, the same for capitals and lowercase). Every open side (C K L
  T E F, c r f t k) took most of its light from inside the letter and
  stood against its neighbour: in DOCK the C stood 79 units from the K and
  141 from the O, and the word read DO CK. The depth is now an eighth of
  the x-height; those gaps are 125 and 148, and the D, with the O's
  corners, stands 147 from the O.
- The lowercase's horizontals thin a little more than the capitals'
  toward Black (0.92 of them at Bold, 0.87 at Black; upright only), and
  where three bars stack in the x-height (a e s) the inner one gives first
  and the bar at the open end keeps its weight, as in hand-drawn faces
  (`tools/stroke_roles.py`). Until now all three thinned alike.
- Every corner takes one break's leg on its horizontal or vertical edge.
  The corner rule broke a right angle by a chord with a leg on each side,
  outside (cut) and inside (filled), and it filled the crotch a diagonal
  makes with a stem by a chord as long: two legs along the stem, twice the
  ink of any other corner, added where two strokes already overlap. The
  joins of K, k, M, R, Q and the 1 were the thickest in the alphabet for
  it (the largest disk that fits them 1.5 to 1.6 strokes across; a T is
  1.45: `tools/stroke_audit.py`). A crotch is now filled one leg along the
  stem; right angles are broken as before, and nothing is left sharp.
  Those joins measure 1.41 to 1.5 at every weight and grade. The watch's
  own drawing and the italic keep the pixel rule's chord.
- The K is the k's drawing at every weight: the arm into the stem, the leg
  off the arm, the crotch a point. From Bold, and in Arris Mono, it had
  changed to the pixel master's form, arm and leg meeting in a block
  beside the stem.
- Every bowl meets its stem through a notch. Each was a closed octagon
  laid square against its stem. A bowl now joins as the n's arch leaves
  its own, at 45 degrees with a notch, at one of its two joins: under
  the ascender on b and d, where the h has its own; over the descender
  on p, q and g; at the foot on a, u and y (`lower.bowl_join`). The other
  join stays square, and as in the n the notch closes by Black. It is a
  rule of its own, half as deep as the arches': a module under the line
  for their two (`lower.BOWL_DROP`). The n, h, m and r are as they were.
  (The owner: "add a little notch into both the u and the lower part of
  the a, like if you took the letter n and flipped it upside down", then
  "if we're going to do it on the a and the u, then we need to do it on
  all the bowls". At the arches' depth, at the light weights, a bowl
  stood a long way off its stem and the line was noisy; shown it at two
  modules, one and 0.6 he chose one, and of the arches: "those remain
  the same. It's just a different rule set.") In the italic the q, the
  g and the y take the notch too, at the foot ("a little teeny weeny
  notch"); its own a, b, d, p and u branch as they always have, and its
  hooks end flat as they always have ("the descender should remain
  flat"). Letters that draw a bowl of their own (þ, the Cyrillic and
  Greek ones) still close square.
- Redrawn, after the chamfered faces (Chakra Petch first), with Arris's
  corners:
  - a: an arch over a bowl. The arm starts in the c's beak and comes into
    the stem through a bowl's corner; the open storey is seven eighths of
    the bowl (it was two thirds, under a bare bar).
  - e and s: their open ends turn through a cut corner into the same
    beak, so a, c, e and s end alike; the e's bar stands above the middle.
  - v: high walls over a 45-degree point, the capital's drawing in the
    x-height (the owner: "it needs to have the 45 degrees with the high
    walls"), and as wide as its two arms: nine tenths of the n. Its arms
    were at 2:1, the 7's slope, in eight modules; the italic's still are.
  - w: the capital's build in the x-height too, high walls, 45-degree
    valleys and its middle stroke a stem standing on the peak ("if we're
    going to modify the v and the y then we should definitely do the w").
    Its arms were at 2:1, and the italic's still are; the `www` ligature
    follows.
  - v, w and y bend at one height: their walls turn into their arms as
    far above the point as the w's valleys are deep ("where the crook
    occurs needs to be consistent"). That is what narrows the v; of the
    ways to it he was shown (a flat foot on the v, longer arms on the w,
    two heights) this is the one that keeps the v pointed, and it reads
    further from the u than the eight-module v did: v/u 0.46 at Regular
    by `tools/letter_confusion.py` at 11 arcminutes (0.77 with the 2:1
    arms, 0.38 with 45-degree arms in eight modules; other families 0.58
    to 0.88).
  - y: the v's left arm, a wall and 45 degrees, come into a stem as a
    bowl comes into its own, with the bowls' notch at its foot, and the
    stem run on down into the g's hook ("make a g like it is today and
    ... take a v and then join it such that it has a little bit of a
    notch to it like the bowls"). Its foot, the flat between arm and
    join, is as long as the flat on top of the m's arch ("measuring the
    top of the m and making the flat part that long"), which sets its
    width: 0.87 of the n's advance at Thin, 0.96 at Regular, 1.05 at
    Bold. It had been a bowl open at the top, its left corner cut all
    the way across to a flat a module short of the stem. The italic
    keeps its own.
  - x: the X's drawing in the x-height. Both step at the crossing at the
    light weights and lose the step as they grow; the x had crossed plain.
  - 1: a stem whose top left corner is cut and run out into a flag that
    ends plumb, no foot (Arris Mono keeps the foot its cell needs). It
    was the watch's 1 on a foot six modules wide; the watch's cut takes
    the new figure too.
  - D: the O's corners. They were a module larger.
  - J: one stroke, an arm along the cap height that turns down into the
    stem and the stem into the U's hook. It wore the 1's foot on top, a
    bar three modules either side of the stem: two short ends, each
    broken at both corners and filled into the stem, at Black a six-sided
    lump. The arm stands to one side and is never shorter than a stem
    past the stem; the hook's white is seven tenths of the U's at every
    weight (0.57 at Black before).
- An arch's shoulder (n h m) is never drawn smaller than an edge break.
  Its room was measured to the outside of the arch's far corner, so from
  Medium the shoulder's edge ran into that corner's cut and the counter
  came to a point under the arch: at Black a spike 39 units tall beside a
  flat of 106, with the arch a third thicker over the flat than its bar.
  The room is now the arch's own underside, which keeps a flat past the
  shoulder; a step under the shoulder shorter than a break is not drawn
  (the counter's top is then the arch's alone), nor a notch over it
  shallower than a break. So the shoulder goes as the X's step does: the
  n keeps both to Bold, the notch alone at ExtraBold, and is square at
  Black, as the m is from SemiBold. The m's middle stem stands up to its
  second arch (the first arch's corner had bitten a wedge out of it at
  the heavy weights, and that counter's corner was all but sharp).
- Six letters stand where faces of this kind put them. Measured on six
  (Chakra Petch, Oxanium, Rajdhani, Exo 2, Tomorrow, Share Tech: each
  letter's ink and advance against the n's or the H's), the masters'
  module widths left the m cramped and five letters in too much white.
  The m's counters are seven eighths of the n's (three quarters before:
  its advance 1.36 of the n's, now 1.47; those faces 1.44 to 1.59). The w
  is a tenth narrower (1.46 of the n to 1.33; 1.24 to 1.42), the M eleven
  modules for twelve (1.29 of the H to 1.19; 1.15 to 1.31), the W thirteen
  for fourteen (1.37 to 1.28), the T the E's eight for ten (0.98 to 0.79;
  0.79 to 0.84), and the r two thirds of the H for eight ninths, to the
  Regular (its advance was 0.94 of the n's, where every one of those
  faces has it under 0.72; it keeps its notch and its arm). In Arris Mono every letter fills
  the cell as before.
- The j is narrower. Against the n it stood wider than any of those six
  faces sets it, its advance 0.65 of the n's (theirs 0.41 to 0.49): its
  hook is three modules of white across for four, the room its two
  corners need (0.54). Arris Mono's and the italic's are as they were.
- The l ends in one cut. Its foot was a corner and three modules of
  tail. The tail is now nothing: the stem turns through the corner's one
  cut and runs on to the baseline (the owner: "only one single notch", no
  flat foot; it ended upright there, two edge breaks tall, until it took
  the k's leg's end, above). It is its stem and
  its cut at every weight (0.46 to 0.49 of the n's advance; it was 0.65,
  in those faces 0.40 to 0.51).
- The f and the t are a module narrower, six for their masters' seven:
  hook, foot and crossbar each a module shorter (0.61 and 0.69 of the n's
  advance at Regular; they were 0.72 and 0.79, in those faces 0.48 to
  0.69), and a line with several of them (little, filter) keeps the
  rhythm its stems set. They keep their hooks: the l's cut was tried on
  the f's top and the t's foot, and the owner kept it for the l alone
  ("keep the hooks for the f and the t, and the l stays without a
  hook"). The ſ follows the f. Arris Mono's and the italic's own f and l
  are as they were.
- The l has no flag. It carried the 1's at the top, a module to the left
  of the stem. Over the x-height spacing lets a part hang into its
  neighbour's room (it is meant for a j's hook under the line): the
  flag's tip stood 12 units from the body's edge at Regular, where a stem
  stands 88, and 21 outside it at Black, and whatever stood before an l
  with ink that high was crowded: F E T K and the l 0.3 of the white
  between two stems (0.55 to 0.85 in those faces), i d H and the l a
  third at Black (0.84 to 1.0), "illicit" a comb. No longer than it was
  thick, it read as a bump on the stem.
- The percent sign is three pieces. Its rings were four and a half
  modules of counter in the full stem, in a body their two widths did not
  fit: each ran into the slash at every weight (50% read as 5096), and at
  Black the sign was one mass, its counters two thirds of a stem. Drawn in
  the small figures' strokes (0.8 of the weight's, 0.68 at Black), its
  rings half the cap height and five modules across, each stands the
  least white clear of the slash (`punct.pct`), as those faces draw it
  (0.2 to 0.8 of a stem between ring and slash). ‰ and ‱ carry the same
  rings. In Arris Mono's cell the sign is as it was.
- The number sign's ends are longer than its strokes. Only the square
  between its bars was kept, at the full strokes: at Black the ends stood
  two thirds of a stroke past the bars, a cross with a hole in it. Its
  ends are a stroke and a half at least, and where its height does not
  hold that its strokes thin together (0.91 of the weight's at Bold, 0.72
  at Black; those faces 0.8 to 0.9 at Bold).
- The straight quotes are a third of the cap height (two dots from Bold,
  where that is more): they were two dots at every weight, a quarter of
  it at Regular (0.31 to 0.36 in those faces). The double quote's ticks
  stand a module and a half of white apart for two, so the pair no longer
  reads as two apostrophes.
- Figures are proportional by default. The default was the watch's
  tabular set, every figure centred on a ten-module cell: the figures
  stood a third of the white between two stems apart (0.34; 0.63 to 0.88
  in those faces), the 1 two whole ones from its neighbours (1.8 to 2.4;
  0.6 to 0.9), and nothing was kerned against them: 1,110 and 7/11 fell
  apart in a line of text. The same drawings are now spaced as the
  letters are, each by its own white (the 0 against the 0 0.84, the 1
  against the 1 0.68), and kerned with the letters and the marks (a
  period after a 7 1.6 for 2.0). `tnum` gives the tabular set, unkerned,
  on its cell (`pnum` undoes it), and every feature that takes a figure
  takes either: `zero` `ss01` `ss02` `sups` `subs` `numr` `dnom` `frac`
  `ordn` `ss20`. Between proportional figures the time colon keeps a
  colon's sides; between tabular ones it is the watch's. Arris Mono is
  unchanged: every figure on the cell. **Anyone who set a clock, a table
  or a counter in Arris and relied on the default now needs
  `font-variant-numeric: tabular-nums` (`tnum`).**
- The ring is three tenths of the cap height. It was drawn in the full
  stem up to two modules, round a counter of two: 0.38 of the cap height
  at Regular and half of it from Bold, twice any other accent, and Å
  stood 1.47 to 1.60 cap heights tall (1.34 to 1.40 in those faces), into
  the descenders of the line above. Its stroke is 0.7 of the stem up to a
  module and a quarter, its counter a module and a half (0.30 of the cap
  height, 0.33 from Bold; theirs 0.26 to 0.36).
- A comma stands where a period does. Its side was measured from the tip
  of its tail, so after any letter its head stood half a dot further off
  than a period's dot: a quarter of the white between two stems at
  Regular, 0.7 of it at Black (T and a comma 2.3 gaps apart for a
  period's 1.7). Its head now stands on the period's dot and its tail
  hangs into the white before it; the semicolon and the low quotes with
  it.
- No two inks nearer than the collision floor, in any direction. Only
  gaps on a shared row were counted, and a j's hook under an l's, a t's
  or an L's foot shares none: 0.18 to 0.20 of a gap at Regular (0.43 to
  0.97 in those faces), now 0.35.
- The w's middle peak is a peak at every weight. Its middle stroke ran
  from the peak to the sixth module, and where the peak is lower than
  that it stood over it: a post 65 units tall at Thin, a stub at Light,
  and at Regular a spearhead with a barb of 11 units each side. The
  stroke now stands in the peak, never over it.
- Arris Mono's r ends its arm on a whole face at Bold. In the cell the
  arm is short, and the shoulder's diagonal ran into its end, leaving it
  a face of 7 units; the shoulder now rises no further than leaves the
  arm's underside an edge break of flat.
- An arm keeps six tenths of a gap from a side. The capitals whose arms
  stand upright for half their height (A V W Y) take the bearing their
  open half earns, and beside a bowl or another arm that left two upright
  edges all but touching at the heavy weights: R and Y 0.38 of a gap at
  Black, P and A 0.47, two Ys 0.23 (0.63 to 0.74 and 0.62 to 0.85 in
  those faces). They open to 0.6: 7 pairs at Regular, 33 at Black. Bars'
  ends still close to the floor.
- A crotch with a step in it is broken as any crotch. Where a diagonal
  lands on a short edge square to the bar it runs into (the Z's foot),
  the corner was filled as a right angle, no further than that short
  edge: 35 units at Bold, 9 at Black. The chord now keeps its leg on the
  bar and runs square to the diagonal until it meets it
  (`geom._stepped_crotches`): 23 glyphs move at Regular, 147 at Black, by a
  few units each, none in the italic.
- Letters that interlock are kerned as hand kerning leaves them. A pair
  closed only when its narrowest gap passed a standard gap (the white
  between two H's) and a quarter, and then by four fifths of the excess,
  so every such pair was left 1.3 to 1.45 gaps apart: L and Y 240 units
  for the H's 177, L and T 230, T and A 239, and the capitals read loose
  wherever an L, a T or a Y stood. Measured in seven kerned faces of this
  kind (Chakra Petch, Oxanium, Exo 2, Tomorrow; Regular and heavy), the
  facing ends of such pairs stand one standard gap apart (LY 1.06, LT
  0.96, TA 1.02, TJ 1.03), and where the approach is on a slant the inks
  come to three quarters of one or a little more (LV 0.86, LW 0.74, To
  0.87, Ta 0.78, Tr 0.75). Two letters now close to a standard gap and
  never nearer than three quarters of one in any direction: at Regular LY
  -130 (it was -70), LT -75 (-25), LV -120 (-65), LW -45 (0), TA -105
  (-55), To -115 (-60). A pair with a mark of punctuation in it keeps the
  air it had, and a period or a comma is pulled in by no more than 0.45
  of a gap, which is what those faces do after any letter that overhangs
  it (P. 0.47, T. 0.46, Y. 0.47, r. 0.38): it had gone under the P's bowl
  by 255 units at Regular and 280 at Black. Still open: at the heavy
  weights a bowl stands nearer an arm than in those faces (R and Y, P and
  A, V and a); `kerning.py` has the measurements.
- No letter keeps a crumb. Scanned at fifteen weights from Thin to Black
  for edges shorter than half an edge break, twenty-two of the sixty-two
  letters and figures had one somewhere, of three kinds. A counter a
  little taller than its two corners' cuts kept a wall of a few units
  between them as it closed with the weight (a e s B G 3 5 6 8 9: the
  a's bowl 13 units at SemiBold, the G's pocket 20 at Black): such a wall
  under half a break now closes, the cuts running on to meet in a point
  (`geom._polish`, `FACET`). Under the stub of a bar across a stem (f t l,
  the 4) the end's break and the fill into the stem are two chords of one
  length with a flat between, 10 units at Medium and none at Bold: a flat
  under half a break closes, and the two are one plane
  (`geom._close_jogs`). And the X's step left a flat of 6 units in its
  crotches at Regular, which goes with the first. The italic and the
  watch's drawing are finished as they were. At the named weights no edge
  of a letter is now under 0.45 of a break (the v's flank at Black, 0.48).
- The points of v and w hang an edge break under the baseline and are
  cut flat there, a break and a half wide (22 units down at Regular, 44
  at Black). They had run 38 and 73 units under the line to a flat under
  a break wide, the sharpest end in the alphabet; the drop is theirs and
  stays, the needle goes. The w's middle peak ends as the corner rule
  ends any point (cut at the x-height first, it kept two crumbs at
  ExtraBold).
- Ends at Black. The f's top corner is cut down to the t's, so bar and
  corner make one plane; the Q's tail gives as the bowl grows; the 4 keeps
  a module of white beside its stem and the G's bar a least white over
  its foot; the beaks
  of c and j are measured by the lowercase's own bar (they had kept the
  capitals', and the j's beak a 19-unit step).
- The italic keeps its own letters: its a, e, f, k, r, s, t, y and z are
  drawn as they were (the r is the same outline at every weight); it takes
  the descender line, the capitals' widths, the K, the D, the x and the 1.

## 1.016

- Grade changes no width, in every glyph. The grade axis thickens or thins
  the strokes and keeps every advance, so text does not reflow with it;
  in the variable fonts 42 glyphs upright and 52 italic broke that. ⁜ was
  140 units narrower at Black with the grade at 100 (‴ ⁗ in the italic 91
  and 125), ⇿ 85 wider at SemiBold with the grade at -100, and the letters
  and signs with a bar or a slash across them (ł Ł Ø ø ŧ Ħ Đ ₱ ₦ ₩ ₹ ₺ €
  ≠ ≱ ⊈ ∄ and the rest) moved by 2 to 25. A graded glyph is spaced as its
  ungraded self, and that self was not always the plain master. Its
  strokes were the graded ones divided by the grade's factor again, which
  is the number they started as only to its last bit: nothing that asks
  whose parameters these are knew them for a weight of the font, so an
  added stroke (held at the Regular's weight from 1.014) was drawn at
  another's and the glyph was spaced round that; and a drawing that turns
  on a threshold at a named weight (⇿ at SemiBold) fell on its other
  side. And a grade that scales nothing, a positive one at Black, was not
  taken for a grade at all, though the lighter weights its added strokes
  are held from are graded. Now a grade carries the strokes it was made
  from, and its ungraded self is the plain master exactly.
  The static fonts are ungraded and do not change.
- `tools/grade_advance_check.py`: each variable font is checked as it is
  built; a glyph whose advance moves with the grade fails the release.

## 1.015

- Arris Mono's cell, both ways: nothing is cut by it any more. Mono drew
  each letter's body into the 600-unit cell and cut whatever ran past
  the cell's edge, so a mark beside or under a letter was sliced flat
  there: the horns of Ơ Ư and the Vietnamese letters made from them, the
  apostrophe of ď ľ, the ogoneks of ą ę ų Ą Ę, Ø ø's slash, the tone
  marks beside a circumflex (ấ ế ố), the tonos of Ά Έ Ή Ί Ό Ύ Ώ, ŀ's
  dot, ҏ ҽ ƙ ǅ ǆ ĳ ỵ (84 characters in all, in some weight of Mono or
  Mono Narrow). Now a letter that would run out of its cell is moved, and
  if it must be drawn narrower, until its ink stands a quarter of a
  module inside; past the narrowest that keeps its counter open, the
  mark gives way (ď's apostrophe at Bold). Signs keep the same quarter
  module (they kept a unit, and № ℘ ⌃ ⌄ touched their neighbours; at Bold
  № ₠ ℘ ∫ ∮ and the currency signs' bars kept half of it, their margin
  measured from the figures' body, which is wider at Bold).
  The cell's clip had also cut stroke tips flat where they met its edge
  before the corner rule broke them (the tonos, ¢ ¥ ₫'s arms and bars):
  a glyph that fits is no longer clipped.
- Arris Mono Italic and Mono Narrow Italic keep to their cells too. Their
  letters were fitted as they are drawn, upright, and the italic's slant
  (10°) then leaned them out: more than half the glyphs of every Mono
  Italic ran past the cell, by 31 units at the median in Bold Italic and
  103 at worst (the cell check had looked only up and down in the
  italic). Now the fit measures the ink as the font carries it, slanted,
  as far as its curves reach (not their off-curve points, which stand a
  few units outside a rounded corner), with the overshoot it will be
  given, and every italic letter is drawn as much narrower as its slant
  needs: the slant leans a capital's top 127 units past its foot, so at
  Bold Italic an O is about six sevenths of its upright, and a d, whose
  stem rises on the right, is narrower than a b. The figures could not be
  drawn narrower (they were drawn on the figures' body, whatever body
  they were given), and now are; nor could Ŧ, ŀ and ỵ, whose T, l and
  cursive y kept their own width. Signs are fitted the same way: a sign
  drawn smaller is drawn smaller whole (©'s ring stayed the cell's width
  while its C shrank, and in the italic the sign was drawn as small as it
  goes and still leaned out), and a letter's sign is narrowed in the
  italic as a letter is, condensed only where that is not enough (№ ℘ ₠).
  The horns of Ư Ơ ư ơ and their Vietnamese letters give way at Bold
  Italic as ď's apostrophe does, and the apostrophe, beside a d as narrow
  as its bowl allows, goes on shrinking past an accent's smallest, as far
  as the cell needs.
- Signs laid out by their own strokes and gaps but clipped at the body
  they were given lost what ran past it in Mono's narrower cell, and the
  sign's fit, measuring what was left, saw it fit: ₪ had no right-hand
  stem in any weight of Mono (its four stems and three gaps are wider
  than the cell), ℞'s crossing stroke was cut short (and in Mono Italic
  cut away with the leg's foot), and ∛ ∜ lost the top of the radical's
  rise. Each is now cut on its own frame, so the fit sees all of it and
  condenses it to fit.
- Up and down, Mono's cell is its line box (975 above the baseline, 250
  below), which a terminal's cell is: the stacks of accents over
  capitals (Ǻ Ỗ Ẵ Ǜ Å Ȭ Ấ and the rest) and over ĥ ĺ ǩ ḟ stood up to 200
  units above it and were cut there. The owner's choice: the line stays
  and the accents give way. A stack closes up its gaps first, to half,
  and then its marks lighten and shrink, as far as it needs to stand
  under the line (it had fitted under the Windows box, 1180). Only Ǻ's
  ring and acute stand a little over at the heaviest weights (29 units
  at Bold). The proportional fonts' stacks keep to their line (the
  Windows box) the same way, gaps first: where they meet it (Ǻ ǻ from
  Regular, the Vietnamese and pinyin stacks Ấ Ẫ Ắ Ẵ Ế Ễ Ố Ỗ Ǘ Ǚ Ǜ Ȭ from
  Bold) their marks are a little larger and their gaps closer than in
  1.014, which shrank the marks first. The inferiors (₀–₉ ₊ ₋ ₌ ₍ ₎ ₐ–ₜ) stand 22 units higher in
  Mono, together, so ₚ's descender stays inside the line.
- `tools/mono_cell_check.py`: every Mono static font is checked as it is
  built; a glyph cut by its cell or past the line box fails the release.

## 1.014

- Every stroke added to a letter or sign keeps the Regular's weight and
  is laid over it. A bar, a slash, a stroke through a letter (the bars of
  Đ đ Ħ ħ Ŧ ŧ Ғ ғ Ұ ұ Ӻ ӻ Ѣ ѣ Ҟ ҟ Ӿ ӿ ǥ ð ℏ, the slashes of Ł ł Ø ø Ǿ ǿ,
  the bars and strokes of € ¥ $ ¢ £ ₦ ₩ ₳ ₸ ₱ ₽ ₣ ₭ ₤ ₴ ₵ ₲ ₡ ₿ ₫ ⃀ ₺ ₮ ₥,
  the negations ≠ ≢ ≁ ≄ ≇ ≉ ≮ ≯ ≰ ≱ ≨ ≩ ⊄ ⊅ ⊈ ⊉ ∉ ∌ ⊬ ⊭ ∤ ∦ ∄, the struck
  arrows ↚ ↛ ↮ ⇍ ⇎ ⇏) is as thick at every heavier weight as at the
  Regular (1.007 to 1.013 held them from 600, and many not at all), and
  is finished on its own and joined to the finished letter: no corner
  rule runs over the junction, so nothing fills in round it as the
  letter grows, and the letter under it is the letter (the g in ǥ is
  the g). At Black the bars read as bars: Ѣ's clear of its bowl, Ӿ's and
  ӿ's past their diagonals, € ¥ ₦ ₩ ₴'s pairs apart, ≢ ≇'s bars beside
  the slash. Ҟ's bar sits in the V between stem and arm, which the K's
  own growth closes from below: it rises with the weight to stay in the
  open, to the top of the stem at Black. The squint rule no longer thins
  a pair of bars under the Regular's.
- In the italic, a letter's corner an added stroke covers in part is
  curved as the letter's own and cut where the stroke passes over it:
  ǥ's hook bend is the g's curve under the bar at every weight (it had
  stayed straight and snapped round at 648), and Ø's O keeps four round
  corners under the slash. The variable italic does the same.
- A letter stamped into another glyph is the letter, in Arris Mono too.
  Its finished ink is kept as it was finished wherever it stands apart;
  until now any clip sent it round the corner rule a second time, and
  every Mono glyph has a clip (its cell), as has ø (its slash's). So in
  Mono ǿ's ø was not ø, đ's d not d, ¢'s c not c (60 to 75 glyphs a
  font: Ø ø Ǿ ǿ Đ đ Ð ǥ ħ ŧ ł ľ ŉ IJ ij ẁ ẃ ẅ ŵ, the Greek letters with
  tonos, the fractions, ¢ ¥ ₫ ₥ ℃ ℅ ℏ and their kin; in the italic ĝ ğ
  ġ ģ ǧ ǵ Ŕ Ŗ Ř too), and in Arris Ø ø Ǿ ǿ's O and o were not O and o
  from Thin to ExtraBold.
  The second finish was not only wrong but unsteady: at Mono Bold ǿ's
  slash junction came out one way or the other on the last bits of a
  float, and two builds of the same code differed.
- ≨ ≩ ⊊ ⊋: a stacked sign measures a stroke laid over one of its parts
  as that part's ink, so the chevron or the set sign stands the equal
  sign's white above the slash's top. ≨ ≩ have ≤'s chevron (1.013 had
  counted the slash twice and shrunk the chevron by it); ⊊ ⊋ had left
  only 15 to 60 units between the slash and the ⊂, and keep ⊆'s white
  now. The slash reaches past the bar as at the Regular, so the signs
  are no taller than 1.013's.
- Italic R: its leg stands back so the bowl keeps its round to Black.
- The cedilla keeps its hook to Black (Ç ç Ş ş Ţ ţ and the rest): the
  notch under the letter is a white gap and two corner breaks wide.
- ð keeps its bar to Black, clear of the bowl.
- Arris Mono Narrow is recognised as its own cut by every rule that reads
  the cut. Its ligatures had spaced each heavy weight as its own Regular
  and spread to a cell a character from SemiBold (<<< 119 units wider at
  Bold, ..= 92, ::: 83); they space as Arris Mono's do now. Its added
  strokes hold, and its white rules compare with its lighter weights.
- A sign the white rule or the topology lock lightens keeps its added
  strokes' hold (⇎'s strike had jumped from 89 units to 116 at 601).
- Variable fonts: the switches between the two forms of $ and ¢
  compile under `rlig`, not `rvrn` (run before every other feature,
  and mishandled by some Adobe apps). `tools/vf_switch_check.py` shapes
  every switched glyph one unit either side of every threshold.
- Release checks: OTS on every font, a gate; fontTools'
  `varLib.interpolatable`, shaperglot and Fontspector as reports.
- Licences: the code (engine, tools, tests, documentation) is MIT; the
  fonts and the glyph drawings stay OFL. skia-pathops, never imported,
  is no longer a dependency.

## 1.013

- The rest of the math pieces, 22 new glyphs. ⎰ ⎱, two-line braces: each
  end runs on the brace's 45 degrees to its line's edge, so stacked they
  close into the point where the lines meet, and turned half round each
  serves its other use. ⎲ ⎳, the two-line summation: ∑ split where its
  lines meet. ⎸ ⎹ ⏐ ⎯ ⎷ ⎺ ⎻ ⎼ ⎽, terminal cells: the box lines at the
  cell's edges, the vertical extension where | stands, the horizontal
  extension on the operators' axis (it meets an arrow's shaft), the
  radical's foot with its upright at the right edge where ⎹ carries it
  on, the VT100's scan lines. ⏜ ⏝ ⏞ ⏟ ⏠ ⏡ ⎴ ⎵ ⎶: the parenthesis, brace,
  tortoise shell and square bracket turned on their sides, as long as the
  upright brackets are tall, in the line's margin above the cap height or
  below the baseline, where math fonts set them. Upright in the italic,
  as the other pieces are.
- The bracket and integral pieces (⎛ to ⎭, ⌠ ⎮ ⌡) run exactly to the
  line and are cut square there, as box drawing's lines are. They ran a
  break past it and were cut there, the next line's piece meant to cover
  the chamfers: drawn and smoothed one by one, the two chamfers left a
  nick at every join, wider with the weight, and with any more room
  between lines than the font's own (an editor's 1.2) the pieces stood
  apart, each end chamfered, and in the italic rounded. Now the next piece
  continues the stem with no notch, and ⎪ meets the line where │ does.
  Only their free ends (a paren's turn, a brace's point, an integral's
  hooks) are cut as Arris cuts.
- Nothing else changes. Every static font against 1.012's, glyph by
  glyph, upright and italic at all nine weights: the 22 bracket and
  integral pieces move, the 22 new pieces are added, and no other glyph
  moves by as much as a unit.

## 1.012

- Arris Mono Narrow, a new family beside Arris Mono, in the same six
  weights, each with its italic. The same 600-unit cell, so columns and
  line lengths are the same as Arris Mono's, and the same strokes; its
  letters and figures are drawn in a body of 7.8 modules instead of 9 to
  9.5, so about a fifth of every cell is white at every weight (Arris Mono
  leaves a tenth at Regular and a twentieth at Bold; Fira Code a quarter),
  and two lowercase letters side by side keep twice Arris Mono's white
  between them. No two letters or figures come near touching at any
  weight, upright or italic: two-thirds of a module apart at the closest.
  The letters wide by nature (m w M W, æ œ, Ж Ш Ю, ω and the rest drawn 11
  modules wide or more at the Regular) are drawn as wide as Arris Mono
  draws them, so their counters stay open. The arch letters n h r u are a
  little wider than the body, 8.4 modules, so the shoulder keeps Arris
  Mono's notch where it leaves the stem and the r its arm; what is made
  from them (ñ ŕ ĥ ü ǖ ɲ, the Bulgarian п и й, their italics) goes with
  them. Each weight from Regular up is drawn 50 lighter than its name
  (the Regular at 350, the Bold at 650; the Light as it is), so in a
  terminal, light on dark, its Regular puts as much ink in a cell as Fira
  Code's Regular; the weight classes are its names'. Every ligature, run
  and optional set of Arris Mono is in it (`uv run python
  tools/build_fonts.py all mono narrow`, with `italic` for the italics;
  `params.MONO_NARROW`, `draw.ARCH_MODULES`, `instances.narrow_weight`).
- Arris Mono, Arris, Arris Watch and the variable fonts are unchanged.

## 1.011

- Arris Mono sets every ligature Fira Code sets by default, 105 in all,
  each one gesture in Arris's own strokes: a character keeps its place and
  its drawing, and its strokes run on until they meet the next (`[|` `]#`
  `#_(` `#?` `~@` `^=` `</>` …). `www`, `??` and `&&` are joined, as Fira
  joins them; what Fira only sets closer (`!! :: // || << >> /* */ <*> ?.
  ..<` …) is brought together, in the same places at every weight.
- Runs of any length: hyphens, equal signs, underscores and number signs
  are set as one piece to a cell, meeting flush, with the ligatures' own
  heads, tails, pipes and slashes as caps (`---->` `<====>` `|---|` `>=>`
  `<<--` `--|--` `=!==` `####` `____` `_|_`).
- Fira Code's optional sets under its own tags, off by default: `ss07`
  (`=~` `!~` as ≈ ≉), `ss08` (gapped `==` `===` `!=` `!==`), `ss09` (`>>=`
  `<<=` `||=` `|=` as arrows), `ss10` (`Fl Tl fi fj fl ft`), `cv20` (`<=`
  as ⇐), `cv21` and `cv22` (`=<` as ⩽ and as ≤), `cv25` `cv26` `cv32`
  (`.-` `:-` `.=`), `cv27` (`[]` as a box), `cv28` (`{.` `.}`).
- Mono Italic now draws its cursive f, k and y by default (1.010's ss04
  was the f and k, off by default), the underscore running into the f, also
  from the end of a run of underscores (`__f`). `ss04`, "Plain italic f k
  y", gives back the slanted upright's letters; `ss05`, "Underscore apart",
  the underscore as it is.
- The watch's stroke balance eases off past Bold, to three quarters of
  the watch's at Black (`instances.WATCH_TAPER`); SemiBold and everything
  to 750 are unchanged. ŧ ҧ ∂ ϱ ℊ ₰ ϖ Ѫ ₼ ₴ ¢ $ hold steadier along the
  weight.

## 1.010

- Arris Mono in Fira Code's six weights, each with its italic: Light,
  Regular, Retina (450), Medium, SemiBold and Bold (`instances.MONO_WEIGHTS`).
  Every weight keeps one cell, ten modules (600 units), so a Bold word keeps
  a Regular line's grid in an editor or a terminal (the cell had followed
  the figures' width, 578 at Regular, 630 at Bold).
- Mono's outline lock: a Mono glyph whose outline would cross, fold or
  pinch in the cell lightens its strokes as little as clears it (the
  fractions at SemiBold and Bold, ↂ, ∛ ∜, ‰ ‱, ₯ Ɲ Ҋ ↭). In Mono Italic a
  sign set from letters (₷ ⅷ ₧) uses the font's own letters; the wave and
  zigzag arrows settle on a clean lead. No two printable characters touch
  side by side at any weight.
- Mono alignment, after Fira Code (`calt`, on by default): `- + *`
  touching a lowercase letter drop to the lowercase middle (`kebab-case`,
  `x*y`); `:` rises beside a capital or a chevron (`A:B`, `<:`); `x` between
  figures or in `0x` is a times sign (`1920×1080`, `0×FF`).
- Mono Italic: `ss04`, "Cursive italic", the descending f and the looped k
  drawn into the cell; with it `ss05`, "Underscore into the cursive f"
  (`is_fresh` as one line into the f). Both off by default.
- Strokes added to a letter (the bars and slashes of Đ Ħ Ŧ ŧ Ł Ø Ғ Ҟ Ұ ℏ)
  stop gaining weight at SemiBold and are re-placed in the white the
  heavier letter leaves, so they stay visible to Black (`draw.EXTRA_HOLD`).

## 1.009

- Back to 1.007's drawings for every glyph but the italic k. 1.008 held
  the counters of the italic e, æ, ø, Q, the slashed letters, the Cyrillic
  tick and ∅, and the closed-counter thinning, at their area from the
  weight their rule first acted, shrinking with the stem; where a counter
  is small when its rule first acts (the italic e's eye) it shrank to a
  sliver by Black and the letter clogged. The hold stays on the italic
  k's loop alone, with its notch fill: the italic k is 1.008's.
- 1.008's curve at a counter side closed to a point (an edge break
  against a 45-degree edge square to it) is the italic k's alone, marked
  in its chamfer record (`italic.SQUARE`): everywhere, it changed the
  curves of 511 other italic glyphs.
- The italic e's and æ's bar ends are 1.007's again (`Stroke.keep` and
  `geom._kept` removed, with the partial jog closing that was off): the
  lower-left corner turns straight from 825 on the heavy grade, as in
  1.007.
- Checked: all 2,212 glyphs drawn from 1.007's code and from 1.009's at
  19 places (six weights by three grades, and Black at watch 100). The
  upright is 1.007's throughout; the italic is 1.007's but for the k and
  the three built from it (ķ ǩ ₖ), which are 1.008's.
- The drawing cache's key is new (`cache.KEY` v3), so the release draws
  every glyph afresh: in a cache shared with other versions' runs, a row
  that was not 1.009's drawing passed its stamp and stood for the italic
  $ at 600 to 900 on grade 100, watch 25. A trial build of the golden
  glyphs and the k from an empty cache is 1.007's but for the k.
- The nesting check (`arris.steady`) and the two-hour fontbakery jobs stay.

## 1.008

- White that only shrinks. Stack a glyph's weights as slices and its
  white should only taper: a counter at a heavier weight lies inside the
  same counter at a lighter one, so it never grows, never moves outward
  (no notch, flag or slot appearing), and closes but never opens. The
  nesting check, `python -m arris.steady` (`arris.steady`), tests it on a
  built variable font: each counter followed along the weight every ten
  units at five grade-and-watch lines, moved onto the lighter one by the
  translation that leaves least of it outside, and faulted where any part
  lies more than three units outside (or where it opens); `--drawings`
  reads the engine's drawings of named glyphs instead. On 1.007: 109
  italic glyphs and 83 upright (the italic k 19.5 units at 750, Q, ø,
  ε έ, β, $, Д, ⅇ, and the circled and boxed operators and the clocks).
  The release's check job runs it on both variable fonts (an artifact
  beside the topology report). `tests/test_steady.py`.
- The rules that keep white held it to a share of the stem, which grows
  with the stem, so they made a counter larger at every heavier weight:
  the italic k's loop dropped and its counter grew from Bold to 875 on the
  heavy grade, then fell to a diamond at Black where the loop ran out. An
  opening on a counter (`Opening.hold`: the k's loop, the italic e and æ,
  ø and the slashed letters, Q, the Cyrillic tick, ∅) and the
  closed-counter thinning now hold: from the weight of the cut where the
  drawing first falls short of its share, the counter keeps its area there
  times that weight's stem over the current one's (read on the cut's own
  drawings, and in the italic on the curved outline the reader sees).
  Against 1.007's drawings: k 10% growth to 2%, e 8 to 3, æ 10 to 6,
  ъ 17 to 5, љ and њ jumps of 18 to 19% to 7 and 6, б 8 to 3.
- The italic k at the heavy end. Its arm leaves the stem as the n's
  shoulder does, the notch under it a step at the loop's top left, kept as
  it was to about Medium. As the weight grows the arm's diagonal shortens
  and the notch's floor rises to the arch, where the stroke folded and the
  notch opened into a slot in the arch (the flag at 800, the notch at
  775); at Black the arm's level start came out of the stem's back (a nub
  of three points 14 to 17 units apart). Now a 45-degree fill grows across
  the notch from 2.5 breaks under the arch and closes it by half a break,
  and from there the arm starts at the stem's centre
  (`lower.shoulder(notch=False)`): the counter keeps one shape to Black.
- A stroke's end that hides inside another is cut where the other's
  outline runs (`Stroke.keep`, `geom._kept`). The italic e's and æ's bars
  end square, parallel to the bowl's lower-left corner cut, drawn to lie
  on it; drifting with the weight they came out past it by up to eight
  units at Black, a step the cleanup closed at some weights and not at
  others, and the italic curved that corner or cut it straight with it
  (straight from 825 on the heavy grade, 725 at watch 100). The corner is
  curved at every weight now.
- The italic curves an edge break against a 45-degree edge square to it,
  as it did while the axis edge between them was there: a counter whose
  side closed to a point (the k's at 665 on the heavy grade) straightened
  its corner there and curved it again where the side reopened.
- The release's fontbakery jobs have two hours (1.007's upright variable
  font took 59 of its 60 minutes).
- Not yet: the rules capped by nesting (`draw._Nesting`, `ARRIS_NEST=1`),
  proved on a test set (the Q keeps its tail to Black) but off: the
  drawings still spill where geometry, not a rule, moves a counter out
  (ø's bowl corner turns plain at 900, Ҩ's form switches at 860); the
  italic ε έ fold between masters; the symbols' white rule holds white to
  a share of the stroke as the others did.

## 1.007

- The skeleton check, `python -m arris.skeleton` (`arris.skeleton`): a
  glyph's strokes are the letter's intent, and weight an offset of them.
  The check reads the features off the strokes (ink along each segment's
  centreline, white beside it clear of its corners and the strokes it
  meets, each bowl corner present and in the italic curved, each free end
  free, the counters and the pieces of ink counted) and tests each at every
  weight from 100 to 900 at grades −100, 0 and +100 and watch 0 and 100, in
  both styles. A feature may be lost toward Black, once; one lost and
  regained, a counter that appears or a piece of ink that merges with
  weight is a fault, and a feature lost under 500 is listed. Run on 1.005's
  italic it names every flip 1.006 fixed; `tests/test_skeleton.py` keeps a
  core sample passing. The JSON (`--json`) holds every feature's survival,
  for diffing one build against another.
- The topology check, `python -m arris.topology` (`arris.topology`): what
  an Arris outline never does, tested along the axes. Each contour is one
  simple ring that meets no other; no turn is sharper than 150 degrees (a
  fold or a spike); no edge is shorter than a unit; no two parts of a
  contour come nearer than a third of a break without meeting (a pinch, a
  cluster of points). Run on the built variable fonts, every simple glyph
  is read at its own masters, halfway between them on each axis, and along
  the weight every ten units at five grades and three watches, straight
  from the font's variations; `--drawings` reads the engine's drawings at
  the heavy corners of the design space. A crossing is sized by the piece
  it folds wrong (wound backwards, a spike of ink; not at all, a sliver of
  white), so a notch a reader sees ranks above a hairline. On 1.006's
  upright variable font: 680 of 1,787 glyphs cross themselves somewhere
  between their masters, 91 of them by ten units or more (℉ ₘ ҽ ҿ ♧ ₪ Ҏ ð
  ? æ ӡ $ ų ŧ …), 91 at the default grade and watch; the drawings do not.
  The cause is the alignment that makes the masters point-compatible: a
  point it adds sits a fraction of a unit off the outline at a master and
  opens into a wedge between two, and the build's own measure of a
  crossing (its depth, `vf.dense`) sees a long thin wedge as shallow.
  `tests/test_topology.py` holds the check to synthetic folds and a sample
  of drawings. A vertex within two breaks of an edge along its own
  contour is the corner the two make (a notch's flanks, the end chamfers
  of a thin stroke), not a pinch.
- Drawings that adapt where weight closed a feature (docs/DESIGN.md, "A
  feature weight would swallow adapts"). The ŧ's bar reads the t's slot
  and keeps a module of white above and below it, moving and thinning (to
  0.7 of the stroke) as the slot narrows; the fill under its nub left of
  the stem stays half a break clear of the hook's chamfer (landing on it,
  the fill bent the bowl's line, and the italic held the hook's corner
  straight at 600 and curved it again at 800 with the watch's strokes);
  where no white can remain it fills the slot whole, in one piece, and
  runs on past the t's right edge as a bump; and it reads its own outline
  with the topology check, stepping a few units off a coincidence with the
  t's jogs (a hairline fold at 900). 1.006's ŧ was a blob with a hairpin
  fold at 900/+100/100. The hooks of g, y and the italic y thin their
  horizontal to the stack minimum, then deepen into the font's descent (up
  to 70 units) before the slot under the body closes, which at Black it
  did. The ₽'s bar keeps the least white of a sign under the bowl and two
  and a half breaks of foot below it (the fill under the bar and the
  foot's chamfer are parallel diagonals, and a shorter step between them
  the corner rule closes into one line: the chevron of Mono at 700),
  thinning to the stack minimum and then growing the foot down past the
  baseline, 32 units at Black. The ℘'s hook, the j's by intent, was 30
  units wide at Regular and shut at 600: it now stands a stem and the
  least white left of the stem, and far enough out that its two outer
  corners keep a break of flat between them (meeting in a point they held
  the italic's curves straight to 500), the sign growing to the left by as
  much, and it deepens like the g's where its corner would reach the
  bowl's fill. A bar placed by rule can still land on a jog of the letter
  it crosses: `Glyph.settle` draws the first of a few positions, two to
  twelve units apart, that the topology check finds clean.
- The variable fonts' folds (`arris.vf`). 1.006's fonts fold by 40 to 190
  units at their own masters and between them: the build measured a
  self-crossing by its depth, which sees a long thin wedge as shallow; the
  grid nodes it predicts rather than draws were never compared with a
  drawing; the italic's curves, built on the aligned upright rings, open a
  collapsed corner into a loop; and the census its planes come from was
  taken at grade 0 and +100 alone, so a drawing's jump on the other lines
  was interpolated across a hundred units of weight. Now a fold is an
  error of its own size (`measure.fold`, the topology check's measure)
  wherever an alignment is measured: at the check's places, on the dense
  grid, just off each master (where collapsed points open), when a master
  is pruned, and, for the italic, on the curved outlines the font carries
  (`measure.folds`, `italic.prepare_outlines`); the census's planes about
  a jump are brought from ten units of weight apart to one by bisection
  (`glyph._narrowed`), so a jump is a jump and not a wedge a reader can
  land on; and every build ends by reading its own font with the topology
  check (`build/topology.json`). Measured on 1.007's upright variable font:
  of its 750 simple glyphs, 27 still fold by ten units or more somewhere
  between their masters (1.006: 91) and 162 by three or more; the worst are
  ∄ (62 units, at 200/+100/100), ₘ (24, at 400/−50), ⅓ and ⅕ (19, at
  140/+50/100) and ų (17, at 812/0/100); the drawings fold nowhere. These
  lie between masters that are each clean, and a denser measuring grid does
  not move them (a trial of the 26 worst): the alignment's correspondences
  between neighbouring masters are the next work. The italic's numbers are
  in the release's check job (its topology artifact).
- Italic: which edge a bowl's chamfer line claims (`italic._segments`). A
  45-degree line runs on, and the edge nearest where the chamfer was
  recorded can be another's: the K's leg lay behind the Қ's and Җ's
  descender corner at 300/−100 and, claimed, was curved to that corner, a
  lens cut out of the leg; an accent's corner on the line of a corner of
  the letter under it (ř ǒ õ ά ắ, в at one grade) held that corner
  straight at single weights. Further than two breaks from its record a
  chamfer's line now claims only an edge ahead of the record, with ink all
  the way from the record to it: the rest of a chamfer whose start another
  stroke swallowed (the ρ's bowl at its stem, the æ's, the 8's waist at its
  spine), which is what the first skeleton runs had been losing. Faulting
  glyph-styles in the skeleton check 58 → 44, nothing newly lost.

## 1.006 (2026-11-01)

The build, after 1.005 took nine hours of runners for one release:

- The drawing cache stamps each drawing with the modules it came from
  (`arris.cache`: the glyph's module and those it draws with, found as it
  is drawn, widened by their imports, and the engine's drawing modules),
  and reads a stamp against the code as it is now. A change to one glyph
  module redraws that module's glyphs and keeps the rest; before, any
  change under `src/`, a string in the name table included, redrew all
  2,179 glyphs at every master, ninety-five minutes a variable font.
- Fontbakery runs in five jobs side by side, one a family or a variable
  font (about fifteen minutes, from seventy-six in one job); its ital-axis
  check, which wants each italic and its Roman in one run, is made for the
  pairs in the upright jobs.
- A variable font is uploaded and its cache saved as soon as it is
  written; its interpolation check runs in a job of its own on the
  uploaded font and may fail without failing the release.
- The variable-font build is a package, `arris.vf` (`uv run python -m
  arris.vf [italic]`; `tools/build_vf.py` still runs it): the settings, the
  design space, the glyph stages, composites, kerning, encoding, assembly
  and check each a module, `tools/vfdense.py` and `tools/composites.py`
  moved in, and the census planes beside them. A characterization test
  (`tests/test_vf_golden.py`) holds a trial build of nineteen glyphs to a
  golden one, outline for outline and delta for delta; the package's
  matches 1.005's builder exactly. The census the planes come from is
  `python -m arris.vf.census`. The build's own code is outside the drawing
  cache's stamps: a change to it redraws nothing. A `check` workflow runs
  ruff, ty and pytest on pull requests.
- The web fonts are on npm as `@arristype/arris` (WOFF2 and CSS: Arris
  variable, Arris Mono, Arris Watch, and Arris as static weights), and so
  on jsDelivr and unpkg. A published release goes there by itself
  (`.github/workflows/npm.yml`, `tools/npm_package.py`); 1.005 is 1.5.0.

The italic along the weight. The italic curves the upright's bowl corners,
and holds one straight where the geometry beside it has degenerated (a leg
that ran out, two chamfers abutting, a step the slant exposed). 1.005 held
such corners at some weights and not others: the h's and l's feet ended in
a straight cut from 589 to about 740 and a curve either side, the g's and
y's descenders were sharp from 500 to 700, the Ԧ's hook ended in a point at
Bold and a curve at Black, the Ҙ's descender vanished into a belly from
800. A sweep of every italic letter and figure at 44 places each (weights
100–900 at grades −100, 0 and +100 and watch 0 and 100) counted 1,268
weight-dependent holds; the families, and what each is given:

- Exit tails (h l i m n п т …): the tail keeps a flat clear of the jog
  cleanup past its corner (`italic_forms.tail_end`, `TAIL_FLAT`).
- g y д: the bowl's foot meets the descending stem square, without the
  corner rule's fill (`lower.crotch_butt`).
- Curves keep their weight round the bend: the inner curve is drawn on
  shorter legs than its chamfer's (`italic._even_bend`). Quadratic pairs on
  equal legs swelled the Thin o, c and e by a quarter at every bend. Black
  is unchanged.
- A bowl whose inner edge only ends at a sharp point (the e's at its bar,
  the s's at its spine, the j's hook) curves on both edges; held, the e
  straightened from 400 and the s from 250 to 450 (`italic._plan`). A
  bowl's line claims a far segment only when no edge break owns it (the
  y's flag at 850).
- Hooks (Ԧ Ҧ ҧ Ӈ ӈ Ђ ђ Ŋ ŋ Ҕ ҕ Ӄ Ԓ Ӽ, ζ ς Ϛ ϛ): the tail past the corner
  is at least `italic_forms.run_floor` on both of its edges, and a hook's
  arm at least `arm_floor` (`cyrillic_ext.hook_reach`, which the Ԧ and ҧ
  take their width from); the ҧ is drawn as the Ҧ is.
- Beaks (C S J j 3 5 Э Є Ҫ Ҽ Ә and their composites): the inner flank
  under the corner's chamfer is `TAIL_FLAT` breaks longer than the
  upright's one (`figures._flank`), clear of the cleanup that merged it
  with the end's break, and an opening shortens a beak no further than
  that. A small capital's beaks (э з є) are the lowercase c's, chamfered
  at every weight: two of the longer beaks across its height met from 650.
- Cyrillic descenders (Қ Ң Ҷ Ҭ Җ Ҳ Ԥ Ҵ Ӌ Ӷ, the tails Ӊ Ӎ Ӆ Ҋ, Ц Щ): one
  stroke through a small bowl corner into the drop, the cursive ц's, in
  place of two strokes meeting in an L, which the slant showed as a notch.
  The drop still stands a module from its stem, less than a stroke from
  Regular up, so the corner into it is held from about 200: whether the
  italic keeps that step or drops straight from the stem is the next
  decision, with the skeleton check below.
- Drops (Ҙ Ҫ ҫ Ҿ ҿ): the drop meets the foot square and the foot's corners
  take the leg that leaves a flat before it (`cyrillic_ext.drop_leg`).
- The ogonek (ą ę į ų ǫ, capitals): the italic's own, flush with the
  base's right edge where it runs to the baseline, under the bowl where it
  does not, 0.6 of a stem thick (`marks.OGONEK_ITALIC`), its foot at least
  `run_floor`, square to the base. The cedilla meets the base square too.
- Butt lines may be given ends (`geom.ink`): the join is square under the
  mark alone.

All of it in the italic alone: the upright's 2,229 drawings, hashed at six
places before and after, are identical. Still weight-dependent, from 1.005
and left for now: the waists of B (to 300) and 3 8 З Ɛ Ɓ ξ β ß (at Thin),
where the point opens into a flat and the lower corner curves; the k's
loop, round to 350 and sharp into its leg from 400; the æ's e, narrower
than the e, holding its eye's corner to 550; the m's first arch under its
flag at Thin; the shoulder of ʒ Ӡ Ʒ Ǥ ķ into its diagonal, held from about
350; the ӄ's arm reaching its hook's corner from 850; the Ӽ's hook to 300;
the watch-form s at watch 100 to 200; and in the upright, the ç's outline
folds back on itself by eight units at 550 where `_close_jogs` slides a
vertex past its neighbour. Next is a skeleton-fidelity check: the drawing
is the letter's intent, a set of strokes with typed corners and ends, and
weight an offset of it; a check that every feature of the strokes (ink
along each centreline, white beside it, each corner, each free end, each
counter) survives along every axis line, lost toward Black at most once
and never regained, would have named each of these, and will drive what
remains rather than a sweep of held corners.

## 1.005 (2026-10-30)

The variable font between its masters. Sliding the weight at a heavy grade
jumped and went crooked between the masters, and in a smaller way along
the weight axis alone. The causes, and what changed:

- A positive grade fades out from SemiBold to Black (`instances.GRAD_TAPER`):
  at Black it adds nothing, so the heaviest stroke the fonts draw is Black's
  own. A fifth past Black's stroke the drawings had no room (? lost its
  hook's stub, ‡ its bars, $ its counters, some three hundred glyphs in
  all), and the font smeared each change across the weights between its
  masters. A negative grade keeps its full reach.
- The topology lock and the counter thinning are monotone in the weight: a
  weight keeps at least what the next lighter named weight of its cut
  decided. Decided weight by weight on yes-or-no tests, $ lightened to 0.8
  from Bold to 850 and not at 875, ⁜ and several arrows went 1.0, 0.8,
  0.85, 1.0, and @ & § ¥ thinned their bars back and forth.
- The symbol white rule measures a drawing against its own heaviest stroke,
  not the stem's whether it has one or not: « ‹ were lightened, and shrank
  a fifth, from WTCH 60 up at the heavy weights and not at the ends.
- The optical centre's rise comes in by degrees from Thin to about
  ExtraLight; it arrived whole between weights 100 and 110, a kink the font
  drew as a line from Thin to ExtraLight.
- The variable fonts have masters on the grade's ends at 600 and 800 too
  (36 masters, from 28): the taper bends the grade's change at 600, and
  between 400 and 900 everything at a grade was predicted from the ends.
- Ю keeps the white between its stem and bowl at half a stem (an opening):
  at the heavy weights it was a slit, filled at one weight and open at the
  next.
- The build can take a census of where each glyph's drawing jumps
  (`tools/vf_planes.py`) and give the glyph masters just either side.
- ⏭ ⏮: the triangles join the bar instead of touching it. The front
  triangle's tip sat on the bar's edge, one ring or two by the rounding of
  the weight, and a master drawn in the other state could not be aligned;
  the tip now reaches into the bar.

The build's interpolation check, 1.004 to the trial build of these changes
(before ⏭'s): upright, glyph-weights more than 3 units from the drawing
1173 to 867 and points more than 60 units off 190 to 139 (in 82 glyphs to
44); italic 4024 to 2428 and 790 to 520 (215 glyphs to 137). Most of what
remains was ⏭.

## 1.004 (2026-10-30)

- ↻ ↺ redrawn. The head was a full chevron on the ring's top, pointing
  sideways, its lower barb hanging inside a ring barely wider than it: from
  about 250 its white against the ring's top closed into slivers, and the
  ring grew with the weight to make room. The head is now a diagonal
  arrow's, one barb level and one upright, in the ring's top right corner,
  pointing on round it; the ring runs into it down a cut from the top's
  middle toward the right side's. The level barb keeps half a stem of
  white under the ring's top and the right side starts as far below the
  point; where heavy strokes leave no room for both, the cut comes up and
  the right side shortens to a stub on its corner, so nothing meets at
  any weight. In Mono the head is as small as Mono's ring.
- δ keeps the white under its bar. At 45 degrees its neck took as much
  room across as the bar, and from about 450 heavier strokes filled that
  white. The neck is now an opening the engine keeps (DESIGN.md, "Openings
  stay open"): 45 degrees through Medium, standing up toward the 7's 2:1 as
  far as the white needs (0.91 of its run at 600, 0.54 at 900).

## 1.003 (2026-10-28)

- `ss20`, Watch pixels, now lights the time colon too. Between figures,
  `calt`'s time colon (`colon.tf`) becomes `colon.tf.px`: two dots of 2×2
  pixels on rows 3–4 and 8–9 of the twelve, as the watch's big clock lights
  them, the same squares as the pixel figures, upright in the italic.
  `tests/test_heritage.py` checks it against the watch's colon.
- Design notes: section 5 described overshoot and the optical centre as
  Arris drew them before 23 October. It now describes `draw.OPTICAL` as
  the fonts have it: round sides that end in a bowl's cut corners
  overshoot by what a blur measures (S, C, 8 and o by 3 units at Regular),
  middles rise until a three-bar letter's top counter is 0.86 of its
  bottom one (B's by 20 units at Light, none at Thin, where the rise yields
  to the stroke floor), and both fade out along the watch axis.

## 1.002 (2026-10-27)

- Variable fonts: the GPU check (`tools/vf_spikes.py`, 7,667 places per
  glyph) found 1.001's sparse layout of masters carrying 675 upright glyphs
  (844 italic) more than 20 units past every master, ✵ by 350 at (825,
  100, 100): the grade's and the watch's changes, measured at three
  weights, added up across the bends of the weight axis. A glyph now keeps
  the font's 28 masters only where they match its drawings at every node
  of the full grid (each weight of the font's masters × GRAD -100, 0, 100
  × WTCH 0, 100) and at the check's places; any other glyph is
  interpolated on that grid (the masters past the font's in the glyph's
  own variations), finer where it is still off. A model over any of the
  grid's nodes is multilinear within the grid's cells, so what holds at
  its nodes holds everywhere between them: on the full grid nothing can
  go past its masters, and each glyph then drops the masters it does not
  need, one at a time, while those left reproduce every one dropped
  within 2 units (and span its box). `tools/vf_compare.py` compares a
  build with a release at the places no build chooses masters from: a
  point more than 60 units off at 86 held-out places upright (1.001: 213)
  and 175 italic (351).
- Symbols: a symbol's separate whites are counted as pieces a disk half a
  stroke across can move about in, not as the union of such disks, which
  joined two whites where disks either side of a pinch overlapped. ∭ was
  lightened from Bold to Heavy (its triangles under the hooks counted as
  one with the whites between the stems) and not at Black, so its advance
  jumped 210 units between 875 and 900; ⇎ ↚ ↛ ⌨ ⁜ « » and others are no
  longer thinned where nothing closes. ↫ ↬ and the Mono semicolon now keep
  a white they have at Regular, lightening at Bold and Black.
- `tools/vf_spikes.py` runs in `tools/rebuild.sh`'s checks.
- Variable fonts still under 9 MB (fontbakery's file size) with all that:
  7.9 MB upright and 8.9 MB italic (1.001: 6.5 and 8.3). Kerning pairs across
  scripts (a Latin letter beside a Cyrillic or Greek one, a glyph's scripts
  being all those its characters are in) are no longer written: shapers
  break text into runs of one script before kerning, so they were never
  applied, and they were 39% of the pairs. Accented letters that are their
  base and marks moved, and .case forms that are their glyph raised, are
  TrueType composites in the variable fonts (`arris.vf.composites`; nested
  ones flattened, fontbakery's nested_components): their variations are
  where their components stand. A glyph drops grid masters
  while those left reproduce each dropped one within 2 units, and its
  deltas are IUP-optimised to the coarsest tolerance (2, 1 or 0.5 units)
  that keeps every node of its grid within 2 units: certified, as a model
  over grid nodes is multilinear within the grid's cells. And a glyph's finer grid is kept
  where it buys the most accuracy per byte (the error it takes off the
  check's and the refinement's places), while the font fits: the build
  makes the font without them, then with the best that fit (`TARGET`).
- Accented letters at a grade: the base was drawn at its own graded width
  and not in the body the font gives it (the ungraded one), so Á's A was
  not the font's A (45 units apart at the heavy grades); it now is. An
  accented letter's body is its base's in every cut: in the italic the
  italic base's (й's breve centred over the italic и), and a body given to
  a composite reaches its base (Mono Ҋ's И narrows for its tail, which
  stood in its stem).
- Italic: a recorded chamfer line is one edge, the nearest where it was
  recorded. A 45-degree line runs on, and another corner's edge could lie
  on it far away (an accent's, on the line of the letter's corner under
  it; one arch of m on the other's): claimed by that corner, the sharp end
  held its curve straight, so á's a was not a's, and Ĉ Õ ê § and the Thin
  m had a corner left sharp.
- A glyph stamped into another as drawn at its parameters, and only moved
  (an accented letter's base, IJ's J, a fraction's figures), keeps its ink
  as it was finished where it stands apart from the other's strokes: the
  corner rule, polish and jog closing run again on it are not idempotent,
  and changed Ć's C by a jog where the accent stood near it, flattened ₯'s
  Δ apex.

## 1.001 (2026-10-26)

- Big yus Ѫ ѫ (`cyrillic.Yusbig`; ѫ its small capital).
- Mono: a letter drawn inside another was cut to a cell of its own in
  1.000, so at Thin ₦ lost both stems, ₣ ₭ Ҋ a stem, ₩ its W. A stamped
  letter is cut at the outer glyph's cell, where it stands in it.
- Mono: a glyph made of a letter and something beside it (a hook, a
  swash, a degree sign, a second spine or stem) squeezed the letter into
  what was left of the cell until its strokes met: Ɓ Ɗ Ƙ Ɲ Ƴ ɲ ƴ, ℛ ℳ ℰ ℱ,
  ℉ ℃, ₻, and Ы ы Ӹ (whose bowl closed even at Regular). The whole glyph
  is now condensed as far as its letter needs to keep its own white
  (`symkit.fit_inner`); ℤ's second spine stands on the side with room.
- Mono Ǿ: the slash of a stamped Ø is cut at the cell before its corners
  are cut (a twisted sliver at Black).
- Mono ₦ ₩ ¥ take one bar where the cell cannot keep a pair's white
  (decided once for the cut, at Black); € ₳ ₱ ₴ ₤ keep their pairs.
- ₹ at Bold and Black: its bars thin again, giving its leg back its
  length. The squint rule decides once per cut whether a glyph thins
  (readings within the raster's precision count as no worse), and never
  acts under the Regular's stem. Bars never thin under the stroke floor.
- Variable fonts: masters are aligned against their neighbours in the
  design space, not all against the Thin (`arris.variable`), and a point a
  master lacks is collapsed onto the neighbour the nearest master puts it
  by. Six masters at the grade-watch corners (wght 100, 400, 900 × GRAD
  ±100 × WTCH 100) carry each glyph's exact drawing where it aligns, else
  the outline the other masters predict: the spikes of ℕ ℚ ӽ, and of Δ Ç Ø
  z ₰ ₯ (up to 440 units off the outline at the corners, where the grade's
  and the watch's changes added up), are gone. The build checks every
  glyph between the masters on and off the axes and at the corners,
  counting a point carried off the outline as well as the mean
  difference; it tries the alternatives where the check fails, keeps the
  best, and runs on a pool of processes.

- Heavier than the Regular, a drawing keeps the Regular's contours and
  counters (the topology lock, `draw`): white closing into a hole, parts
  fusing, a counter filling are undone by lightening the drawing's strokes
  together, as little as it takes (at most to LOCK_MIN). About a hundred
  glyphs had done so somewhere: at the heaviest grade S J G 4 з э є ε m,
  at Black ȩ ş, Mono Q's tail, ↺ ↻, ⋰ ⋱ ⊎ ≰, ↁ ↇ ↈ, ₻.
- A squint rule never does less for a heavier weight than for a lighter
  one of the same cut: ¥'s bars run 78 72 78 81 83 units from Medium to
  Black (were 78 72 112 88 119); ¢ and $ keep their stubs from the weight
  that first takes them.
- The static fonts split a contour that crosses or touches itself into
  its simple loops (α, the superior and fraction 1s, Ȩ ş).
- The variable fonts pair their masters' points by what made each point
  (`geom.ink` names every edge: a stroke's side, a cap, a chamfer, a
  stamped glyph's own edge), and a glyph that still interpolates away
  from its drawings gets masters of its own where it does (its variations
  are kept glyph by glyph).
- `tools/sweep.py`, the regression gate: every glyph in every cut against
  the last release, before every change to the engine.

Checked for 1.001: pytest; fontbakery `check-universal` 0 FAIL, 0 ERROR
for the static, variable and Mono sets; `tools/stroke_scan.py` 92 findings
upright and 158 Mono (218 and 309 before the 1.000 work), none new;
`tools/mono_scan.py`; every glyph's ink against 1.000's (only the changes
above); `tools/sweep.py` against 1.001's first build (every change toward
the Regular's topology but Mono ℚ's pinhole); the variable fonts' check
as in TODO, and fontbakery on them again (0 FAIL, 0 ERROR) after grade
was kept from moving advances by a unit.

## 1.000 checklist (2026-10-25)

| Check | State |
|---|---|
| Licence, copyright, version, fsType | done |
| fontbakery `check-universal`, static and Mono families | 0 FAIL, 0 ERROR |
| fontbakery `check-googlefonts` (Regular) | names fixed; West African Latin missing (TODO) |
| Figures against the watch's pixels (pytest) | pass |
| Heavy counters under the squint | main fusions fixed; the rest listed in TODO |
| Mono glyphs inside their cells | yes (upright; the italic leans by its slant) |
| Variable-font interpolation | see the latest `build/vf_check*.json` and TODO |
| Name clash | no other "Arris" typeface on the major stores (a web search, not a trademark search) |
