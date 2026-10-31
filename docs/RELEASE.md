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

## Licence and metadata

SIL Open Font License 1.1 (`OFL.txt`), copyright The Arris Project Authors
(`AUTHORS.txt`); no Reserved Font Name. Every font carries the copyright
(name 0), the licence and its URL (13, 14), embedding installable (fsType
0). The vendor ID is `NONE` (unregistered): register one with Microsoft
before a commercial distribution if wanted.

## 1.006 (unreleased)

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
