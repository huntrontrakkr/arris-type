# To do

Open work, most pressing first. `tools/squint_scan.py`, `tools/stroke_scan.py`,
`tools/jog_scan.py` and `tools/white_scan.py` find most of it.

## From the barred-sign and small-counter pass (2026-10-22)

- **Mono ₦ ₩ ¥ at heavy weights.** Their cells keep 0.33–0.38 under the
  squint (the rule's floor is 0.55): the Mono cell leaves little room for a
  letter, two bars and their white. The squint rule cannot help: Mono's own
  Regular already reads 0.38, the reference the heavy weights are held to,
  and in ¥ at Bold and Black the bars fuse with the Y outright (no white
  left; the rule now notices that, but thinner bars do not reopen it).
  Needs a Mono drawing: one bar where two cannot keep their white (a
  one-bar trial, 2026-10-25, was blocked by the white count the rule now
  keeps: one bar has fewer whites by design), or a narrower inset.
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

## For Google Fonts (if the family goes there)

Done 2026-10-25: West African Latin (Ɛ ɛ Ɔ ɔ Ɲ ɲ Ɓ ɓ Ɗ ɗ Ƙ ƙ Ƴ ƴ, U+0329),
yat (Ѣ ѣ), the dotless superior i under marks, marks centred on their
origin (a mark the shaper left where it was drawn read as unattached),
math on one advance, no soft hyphen, a meta table, no colinear points.
Left of `check-googlefonts`' warnings:
- **big yus Ѫ ѫ** (auxiliary for Russian and Bulgarian): not drawn; its
  traditional form wants checking against a reference first.
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

- **Variable-font spikes at the heavy grade-watch corner** (wght 900, GRAD
  100, WTCH 100, where the grade's and the watch's deltas add): ℕ reaches
  1344 units (720 drawn), ӽ and ℚ dip to -465 and -438. Their masters
  agree in contours but not in points, and the aligner's duplicates pair
  differently in the two directions. The rest of the font stays inside
  1180/-390 there. A corner master would pin it but joins ŀ's dot to its l
  (tried 2026-10-25); fix the three alignments instead.

- **Variable-font interpolation**: the build's check (exact drawings against
  the VF between masters) still finds ≈1,150 upright and ≈1,500 italic
  glyph-locations over 3 units of mean outline difference, worst 40–57
  (underscoredbl, ∭ ∬, and the GRAD/WTCH corner at (800, 50, 100)). Masters
  at 800 and 850 and the aligner's nearer-neighbour gap fill (2026-10-23)
  fixed the 3 and the italic h; 19 italic drawings still change point count
  between 750 and 900 (m n k f e y …). Fix those constructions (as the
  italic tail's floor did) or add masters where the check says so.

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
