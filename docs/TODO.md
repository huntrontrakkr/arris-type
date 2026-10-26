# To do

Open work, most pressing first. `tools/squint_scan.py`, `tools/stroke_scan.py`,
`tools/mono_scan.py`, `tools/jog_scan.py` and `tools/white_scan.py` find most
of it.

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
- **Squint readings step with the weight**: a glyph's reading under the
  squint is not smooth in the weight (raster and layout steps), so the
  rule's per-weight answer is not either: ¥'s bars are 78 72 112 88 119
  units from Medium to Black (thinned where the white falls short, full
  where it reads). Decide the thinning at Black, once per cut, and ease it
  in from the Regular by the stem, so the weights and the variable font's
  masters change smoothly (cent's stem switch is the exception: a form).

- **Contours touching or crossing themselves, by a unit or two**
  (`tools/stroke_scan.py`, 2026-10-25; all there before 1.000): α at every
  weight (its tail meets its bowl at the baseline corner), at Black the
  superior and fraction 1's flag joint (a 2-unit bow-tie), Ȩ ş, and in
  the italic at Black m т ç ş ∂ ₾ ℅ (a sub-unit loop where the shear
  meets a corner). Invisible at text sizes; untangle them in the outline
  step (for the static fonts, where points need not match across masters).

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

- **Variable-font interpolation** (2026-10-26, 1.001, 28 masters with the
  grade-watch corners): the build's check (82,688 glyph-locations between
  the masters, on and off the axes and at the corners) finds 3,442 upright
  and 5,040 italic over 3 units of mean outline difference, worst 58–60
  (∭ ∬ underscoredbl, as before), and a point more than 60 units off the
  outline at 622 upright locations (168 glyphs) and 1,251 italic (337
  glyphs). The worst: ₪ along the grade at Black (250 units), ₹ and ¢ at
  the heavy corner, ℚ's predicted corner in the italic (522), ↺ in the
  italic at (400, ±100, 100). `build/vf_check*.json` lists every
  location with both measures. The build keeps a glyph's predicted corner
  where its exact one does not align or interpolates worse (242 glyphs);
  those keep 1.000's additive corner. Next: align a corner master against
  its own neighbours only (it need not move the others' points), and look
  at ₪'s grade pairing.
- **Variable-font extremes past the Windows box** (1180/-390) at the far
  corners: Ǖ and Ȫ reach 1200 at (900, 100, 100) (their exact drawings,
  now carried by the corner masters), ų dips to -418 at (650, -100, 100),
  and the italic ℚ's spike to -508. Raise the VF's box, or keep the
  stacked accents lower at the heaviest grade.
- **Heavy grade small capitals**: at (900, 100, *) з э є stay dark even
  thinned to the squint rule's limit (three horizontals in the small
  capital's height leave little white); в as well. A lower limit for open
  bowls, or a narrower stroke at the heaviest grade, if it matters.

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
