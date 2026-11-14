# Handoff (2026-11-14)

Branch `letters-together`, last commit 675a81d. Release run 66 (no publish) built every font and
passed every gate (fontbakery, OTS, Fontspector, interpolation, topology, nesting, pytest). Nothing is
released or published; that waits on the owner's word.

Done in this stretch (docs/RELEASE.md has the detail): ⌬ as the textbook benzene ring, one drawing
everywhere; ₢'s r one drawing in one place, its stem standing on the C's bar; ∤ ∦ ≰ ≱ strikes; ⇿;
⌛ ⏳ in the cells; ‰ ‱ in the cells; ₮ ₺ pairs; ℚ in Mono; ď ľ ť Ľ apostrophes.

Open, small, at the heavy end only:
- ⇧ ⇩ ⇪ step at weight 709: the squint rule in draw._draw thins their horizontals to AUTO_MIN (0.7) at
  once where their counter first counts as a hole, though thinning does not help it read. A general
  fix (decide once per cut, fade in from the Regular) moved 71 symbols and made ≗ ⊴ ⊵ worse; dropped.
  Needs a fix for these three alone.
- ° ✂ ⌀ & ⊫ ⊭ ⊛: each thins its horizontals to 0.7 at one weight. Same pinning in the counter-measure
  branch of draw._draw (bisection keeps AUTO_MIN when no value passes).
