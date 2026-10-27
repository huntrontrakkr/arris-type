# To do

Open work, most pressing first. `tools/squint_scan.py`, `tools/stroke_scan.py`,
`tools/mono_scan.py`, `tools/jog_scan.py` and `tools/white_scan.py` find most
of it. Before committing a change to the engine or to drawings, run
`tools/sweep.py diff <last release>`: every glyph in every cut, against
the release (fixes kept breaking things elsewhere that only this shows).

## From the barred-sign and small-counter pass (2026-10-22)

- **Mono ₦ ₩ ¥** (done 2026-10-25): one bar in Mono (`symbols.BARS_OR_ONE`),
  where the cell cannot keep a pair's white at Black. The form is chosen
  once for the whole cut, at Black (`draw._cut_form`), so the Mono weights
  agree. Only signs that are written with one bar too take it: € ₳ ₱ ₴ ₤
  keep their pairs, thinned.
- **Squint scan review** (2026-10-25: 215 flags at Black among letters and
  figures, most of them designed notches or rare letterlike symbols).
  Done: Q, љ њ ъ ы ь (the soft-sign bowl's top rises), ⌀ (0.14 to 0.5, as
  ø), ¢ (stubs at Bold and Black, as $), and the squint is read at the
  font's cap for small capitals (it was too kind to them). Left:
  - в at Black (0.49): B's two bowls at the x-height; thinner bars help
    only so far;
  - Ħ (0.49), § (0.49), ® ℗ (0.46): Ħ's bar, §'s loops, the letter in the
    ring;
  - accents at Black: the white between a mark and its letter (Ť Ž š:
    0.41-0.5) is marks.gap, 0.4 of a stem; more would raise the accents and
    the line;
  - operators and arrows with small closed white: ⊚, ∮, ∡, ≜, ⊉ ∉ ∌
    (slash through a closed form), ⇎, ↂ, ◍; letterlike ℚ ℕ ℊ ↈ;
  - the hatched squares ▤–▩ are dense by design; decide whether they
    thin at heavy weights.
  - The ring below (U+0325) cannot read under the squint at any weight:
    it is as small as the room below the line allows.
- **Stacked operators at heavy weights**: ≡ and `===` grow to the cap height
  and two modules (operators.TALL) with the equal sign's 1.6 bars of white;
  struck stacks (≢ `!==` `!=`) are a module and a half shorter at each end
  so the slash can run past them. Review the look at Black.
- **The squint rule, general**: letters with closed counters now thin their
  horizontals under it above Regular (holes only, never the designed
  slots); symbols still use the lightening rule's feature count.

- **Mono at Bold and Black, left over** (2026-10-25, after the
  `fit_inner` pass): ₻ closes its loop at Black (the proportional nearly
  does too); ԙ crowds at Black; the Roman numerals ↁ ↇ ↈ lose counters at
  Bold and Black; ⏰ is drawn small in its cell. `tools/mono_scan.py`
  finds these (every Mono glyph against its proportional self: closed
  counters lost, and the likeness of the two inks stretched to one box);
  run it after any change to Mono.
- **Squint rules ease in at one step** (2026-10-26): a rule's value is
  now never less for a heavier weight than for a lighter one
  (`draw._squint_monotone`; ¥'s bars 78 72 78 81 83 from Medium to Black,
  were 78 72 112 88 119), but where thinning first starts it starts at
  once: Mono ₦'s bars 104 at SemiBold, 78 at Bold. Easing it in over the
  weight before would spread the step.

- **Contours touching or crossing themselves**: the upright static fonts
  split them into their simple loops (`font._untangled`, 2026-10-26: α,
  the superior and fraction 1s, Ȩ ş). Left: the italic statics (curved:
  m т ç ş ∂ ₾ ℅ at Black, sub-unit loops) and the variable fonts' masters
  (every point kept). `tools/stroke_scan.py` reads the engine's outlines,
  before the split, and still lists them.

- **Build speed** (2026-10-27): a full `tools/rebuild.sh` takes about an
  hour on 24 cores with the drawing cache warm (static fonts under a
  minute, variable fonts 25, checks 37: fontbakery on the variable fonts
  is most of it, then the GPU check).

## For Google Fonts (if the family goes there)

Done 2026-10-25: West African Latin (Ɛ ɛ Ɔ ɔ Ɲ ɲ Ɓ ɓ Ɗ ɗ Ƙ ƙ Ƴ ƴ, U+0329),
yat (Ѣ ѣ), big yus (Ѫ ѫ), the dotless superior i under marks, marks centred on their
origin (a mark the shaper left where it was drawn read as unattached),
math on one advance, no soft hyphen, a meta table, no colinear points.
Left of `check-googlefonts`' warnings:
- **alt_caron** (ď ľ Ľ ť "decomposed"): the check reads components, and
  Arris's glyphs are outlines; their carons are the apostrophe form it asks
  for.
- **contour_count**: designed differences (the 4 open at the top, % with
  its rings joined to the slash, ⊕).
- **vendor_id**: `NONE` until an ID is registered with Microsoft.
- **article, unreachable_subsetting**: the Google Fonts repository's
  business (a family article; subsets for the terminal and symbol blocks).
- **math_signs_width at heavy weights**: the core signs share the plus's
  advance, but the set and membership signs (⊂ ⊃ ∈ ∋ ⊆) are drawn wider and
  keep their own; one width for all would mean condensing them.
- **opentype/monospace, numberOfHMetrics** (Mono): the spec's 3 assumes no
  zero-width glyphs between the cells; Mono's marks are zero-width.
- **file_size**: the exact flat kerning (≈ 200k pairs at Black); class
  kerning would save about 2.5x (see the kerning notes).

## Carried over

- **Variable-font interpolation** (2026-10-27): a glyph keeps the font's
  28 masters where they match its drawings at every node of the full grid
  (about 800 glyphs), else it is interpolated on the grid, finer where
  still off, pruned node by node with a 1-unit certificate (`tools/
  build_vf.py`). At the held-out VALID places (`tools/vf_compare.py`,
  against the tagged 1.001 VFs) a point more than 60 units off at 88 glyph
  places upright (1.001: 160) and 144 italic (275); a mean difference over
  3 units at 553 (1,434) and 785 (2,118); 51 and 81 glyphs better, 21 and
  14 worse. The GPU check (`tools/vf_spikes.py`) lists 13 upright and 44
  italic glyphs past their masters (1.001: 675, 844); looked at, these are
  drawings that themselves reach past the 28 masters between them (Ŏ's
  breve at (850, 100, 0)), the font 15 to 55 units from them at most.
  Crossings deeper than 20 units: 19 upright, 45 italic (1.001: 156, 197);
  the italic e at Thin and the lightest grade crosses in its master (the
  italic's curved chamfers at a hairline). Left, worse than 1.001 at some
  place: « » (the white rule, below), ‽ ℵ ϱ ҧ ♧ ⇭, italic y ¼ ψ: their
  drawings change form between the grid's planes (ӻ's slots close at
  Black between grade 0 and 50; ⇖ loses two chamfer points between 790
  and 800), or the aligner pairs a plane's masters poorly. A glyph whose
  drawing changes form between planes could be split into forms as ¢ $
  are.
- **Variable-font size** (2026-10-27): 7.85 MB upright, 8.88 MB italic
  (fontbakery's 9 MB), by kerning only within a script, composites,
  pruning and IUP certified within 2 units, and the finer grids that buy
  most per byte (`build_vf.TARGET`): all 477 in the upright, 124 of 508 in
  the italic, which so gives up some accuracy (a mean difference over 3
  units at 1,136 held-out places, 785 with every finer grid; 1.001 had
  3,725 against today's drawings).
  Accented letters with an attached mark (ogonek, cedilla, horn) are still
  outlines: their mark joins the base in one contour. ę at Black, grade
  -100, italic, has a 25-unit pinhole where its ogonek joins the e.
  The stroke scan lists two more since: ȩ crosses itself at italic Black
  (by its cedilla), ◍ swells to 61 at italic Thin (its hatching's chamfers
  now curve as each line's own).
- **The white rule's count is fragile** (2026-10-27): whites are now
  counted where a disk can move (eroded components), so a pinch no longer
  merges two (∭ was lightened from Bold to Heavy and not at Black). But a
  white that splits in two still counts as more: » at heavy weights loses
  the notch inside its first chevron at watch 75 (lightened), and at watch
  100 the gap between the chevrons splits, so the count is back and the
  lightening lets go. Keep the Regular's features by identity, not count.
- **Variable-font extremes past the Windows box** (1180/-390): ǻ reaches
  1199 at (650, 100, 0) (its exact stacked accents at a heavy grade), ≑
  dips to -396 at the heavy corner. Raise the VF's box, or keep stacked
  accents lower at heavy grades.
- **Heavy-grade topology the lock cannot restore** (2026-10-26): ≰ at
  the heaviest grade, ԙ at Mono Black, would need more lightening than
  LOCK_MIN; ⌦ ⌫ ⏰ in Mono at Black, lightened, now have contours that
  touch (stroke_scan). Accents touching their letter in Mono (ά at
  SemiBold) need the mark's gap, not lightening (composites are exempt).

- **19 italic drawings change point count between 750 and 900** (m n k f
  e y …): fix those constructions (as the italic tail's floor did) or add
  masters where the check says so.

- **`tools/typeart.glyph_grids` fills the counters, not the ink**: it fills
  each ring by the sign of its area as if outer contours ran
  anticlockwise, but TrueType's run clockwise. The garden slide's ASCII
  glitch layer was shape-matched against these inverted templates (it looks
  right by accident). A nonzero-winding fill fixes it (tried 2026-10-22)
  but changes which characters that layer picks: re-check the garden
  slide with the user when fixing.
  Tried again 2026-10-23 with the tone gain at 0.85 and 1.3: neither
  gives back the approved look (bands of `@ $`), so it stays as is until
  the user decides.

- **Sloppiness pass**: `tools/jog_scan.py` for the remaining near-miss
  steps at Black (keep designed steps; fix the ones a few units apart).
- **Presentation**: regenerate after every full rebuild (42 slides).

## Exploring

- **A Text optical size (shelved 2026-10-23).** Trials on one paragraph at
  11 pt (proofs/text-opsz-trial.png): exit tails and entry flags on the stem
  letters and curved chamfers made it flow but read like an accessibility
  face (OpenDyslexic, Lexend), not Arris; drop them. Longer extenders and a
  520 x-height read naturally. Earlier trial proofs were drawn without
  anti-aliasing, which made the weight look uneven: proof text anti-aliased.
  Next, if resumed: measure Arris against established reading sans (x-height,
  extenders, widths, spacing, word space) and change only where it is an
  outlier; then an opsz axis.

- **Japanese and Chinese**: scoping notes in `docs/research/cjk.md`
  (kana first, a 100-kanji pilot from pixel masters and from components,
  separate CJK families).
