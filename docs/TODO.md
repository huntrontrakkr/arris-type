# To do

Open work, most pressing first. `tools/squint_scan.py`, `tools/stroke_scan.py`,
`tools/jog_scan.py` and `tools/white_scan.py` find most of it.

## From the barred-sign and small-counter pass (2026-10-22)

- **Mono ₦ ₩ at Black.** Their cells keep 0.33–0.38 under the squint
  (the rule's floor is 0.55): the Mono cell leaves little room for a
  letter, two bars and their white. Try thinner bars only in Mono, or a
  narrower inset with the letter condensed further.
- **Letters that hang out of their Mono cell** (`/tmp/monofit.py`-style
  check: placed ink past the advance). At Black: ď 415 units, ľ 226,
  ŀ 218, ỵ 141; Ø ø Ǿ ǿ 30 (the slash); Ҽ ҽ Ҿ ҿ Ҏ ҏ 20–32; Ą ą Ę ę ų 16
  (the ogonek). The caron-apostrophe and the middle dot need to sit inside
  the cell; slashes and ogoneks may hang into half the margin at most.
  Worth a tool of its own (a Mono cell scan) next to the stroke scan.
- **Mono signs condensed to fit are lighter than their weight**: № ‰ ∬ ∭
  (stroke scan reports them). Consider drawing them smaller rather than
  thinner past some condensing, or Mono-specific constructions.
- **₴ at heavy weights**: where no pair of bars fits between its beaks,
  the beaks run into the bars and the bowls close. Review the look against
  the user's eye; an alternative is shallower beaks for this sign only.
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
- **δ reads as 6** in maths (the presentation's "∃δ > 0"): the octagonal
  bowl and hooked top are the 6's. Run it through `tools/letter_confusion.py`
  against 6, ∂ and σ, and give δ a distinct top (a tail or an open loop).
- **Make the squint rule general where it is safe**: today only glyphs
  that declare a free variable use it (barred signs, $). Candidates: the
  symbol lightening rule (holes, not just feature counts), with care not
  to thin designed shapes (the asterisk).

## Carried over

- **Sloppiness pass**: `tools/jog_scan.py` for the remaining near-miss
  steps at Black (keep designed steps; fix the ones a few units apart).
- **Presentation**: regenerate after every full rebuild (37 slides).

## Exploring

- **Japanese and Chinese**: scoping notes in `docs/research/cjk.md`
  (kana first, a 100-kanji pilot from pixel masters and from components,
  separate CJK families).
