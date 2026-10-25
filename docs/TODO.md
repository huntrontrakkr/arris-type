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
- **Squint scan review** (≈370 glyphs flagged at Black, most of them the
  arch notches of n h m and their relatives, which are designed). Go
  through the rest by family and fix the real fusions:
  - closed counters: Q (0.41), љ њ (0.42), в (0.46), ъ ы ь (0.49–0.53),
    Ħ, ӹ, ⅇ, ® ℗ (0.26), § (0.49), ¢ (its stem through the c: stubs as $?);
  - operators and arrows with small closed white: ⌀ (0.14), ⊚, ∮, ∡, ≜,
    ⊉ ∉ ∌ (slash through a closed form), ⇎, ↂ, ◍;
  - the hatched squares ▤–▩ are dense by design; decide whether they
    thin at heavy weights.
  - The ring below (U+0325) cannot read under the squint at any weight:
    it is as small as the room below the line allows.
- **Stacked operators at heavy weights**: ≡ and `===` grow to the cap height
  and two modules (operators.TALL) with the equal sign's 1.6 bars of white;
  struck stacks (≢ `!==` `!=`) are a module and a half shorter at each end
  so the slash can run past them. Review the look at Black.
- **Make the squint rule general where it is safe**: today only glyphs
  that declare a free variable use it (barred signs, $). Candidates: the
  symbol lightening rule (holes, not just feature counts), with care not
  to thin designed shapes (the asterisk).

## Carried over

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
- **ď in Mono Bold** reaches 44 units past its cell (Regular and Black
  fit): the base narrows only as far as its counter allows and the
  apostrophe lightens toward Black; at Bold neither is quite enough.

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
