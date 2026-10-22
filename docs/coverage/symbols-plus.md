# Symbols+: punctuation, super- and subscripts, currency, letterlike symbols, number forms

235 new code points in five blocks, 223 new glyphs (5 of them case forms,
17 of them spaces), the rest aliases of existing glyphs.

| Block | Mapped now | New | Modules |
|---|---|---|---|
| General Punctuation U+2000–206F | 88 | 68 | `glyphs/genpunct.py` |
| Superscripts and Subscripts U+2070–209F | 42 | 25 | `glyphs/supsubs.py` |
| Currency Symbols U+20A0–20CF | 33 (all) | 32 | `glyphs/currency.py` |
| Letterlike Symbols U+2100–214F | 53 | 50 | `glyphs/letterlike.py` |
| Number Forms U+2150–218F | 60 (all) | 60 | `glyphs/numberforms.py` |

Shared moves live in `glyphs/symkit.py`. Proofs: `proofs/symbols-plus-*.png`.

## What was added

* **General Punctuation**: ‒ (a tabular figure wide, on the case dashes'
  height) ‖ ‗ ‛ ‟ ‣ ‥ ‱ ‴ ‵ ‶ ‷ ‸ ※ ‼ ‽ ‾ ‿ ⁀ ⁁ ⁂ ⁃ ⁅ ⁆ ⁇ ⁈ ⁉ ⁊ ⁋ ⁌ ⁍ ⁎ ⁏
  ⁐ ⁑ ⁒ ⁓ ⁔ ⁕ ⁖ ⁗ ⁘ ⁙ ⁚ ⁛ ⁜ ⁝ ⁞; ― ․ ‧ are the em dash, period and middle
  dot. Spaces U+2000–200A, U+202F, U+205F are empty glyphs (em-based widths;
  figure space = the tabular figure advance, punctuation space = the
  period's advance; thin and narrow no-break space a fifth of an em, hair
  space a tenth); U+200B–200D and U+2060 advance nothing. In Mono every
  space is one cell, the zero-width ones none.
* **Superscripts and subscripts**: ⁱ ⁿ ⁺ ⁻ ⁼ ⁽ ⁾ and ₊ ₋ ₌ ₍ ₎ ₐ ₑ ₒ ₓ ₔ ₕ ₖ
  ₗ ₘ ₙ ₚ ₛ ₜ: the full-size drawings with the small figures' parameters
  (`features.small`, heights scaled too), on the baselines of ¹ ² ³ and
  ₁ ₂ ₃. The schwa is the small e turned.
* **Currency**: ₠ ₡ ₢ ₣ ₤ ₥ ₦ ₧ ₨ ₩ ₪ ₫ ₭ ₮ ₯ ₰ ₱ ₲ ₳ ₴ ₵ ₶ ₷ ₸ ₹ ₺ ₻ ₼ ₽
  ₾ ₿ ⃀, spaced as letters like € £ ¥ (the existing currency signs are
  letter-spaced, not tabular).
* **Letterlike**: ℀ ℁ ℂ ℃ ℅ ℆ ℇ ℉ ℊ ℎ ℏ ℓ ℕ ℗ ℘ ℙ ℚ ℛ ℝ ℞ ℠ ℡ ℤ ℧ ℨ ℮ ℯ ℰ ℱ
  Ⅎ ℳ ℴ ℵ ℹ ℻ ⅀ ⅁ ⅂ ⅃ ⅄ ⅅ ⅆ ⅇ ⅈ ⅉ ⅋ ⅍ ⅎ; K (U+212A) and Å (U+212B) are the
  letters (Ω was already the Greek Omega).
* **Number forms**: ⅐–⅟ and ↉; Roman numerals Ⅰ–Ⅿ and ⅰ–ⅿ (one-letter
  numerals other than Ⅰ ⅰ are the letters); ↀ ↁ ↂ Ↄ ↄ ↅ ↆ ↇ ↈ; ↊ ↋.

## Design rules introduced

* **Bars across a letter come in pairs that keep their white** (currency):
  white between the two never under 0.6 of a stem, and toward Black the
  pair thins to 0.7 of the weight's horizontals rather than closing.
  Where a stroke through a letter would close a counter (G under its bar, an
  m's arches, a C's mouth twice), the stroke **stands out of the letter**
  above and below instead (₲ ₥ ₡ ₿). The naira's bars pass behind its
  diagonal on one side each, so each side of the diagonal is one counter
  and not a cell beside a closing triangle.
* **Double-struck** letters are the letter with a lighter inner stroke
  (0.55 of a stem) beside the main stem or diagonal, a slit of white
  between them never under 0.6 of a stem; the letter widens by stroke and
  slit. Parallel jogged diagonals (ℤ) stand far enough apart that the 2's
  jog does not reach across the slit.
* **Script letters** are Arris's own cursive, drawn upright (Arris draws no
  curves upright): capitals take a swash, the top drawn out to the left and
  ending on the 2's beak, and the t's foot as an exit; lowercase take the
  italic's forms (ℯ is the cursive e, ℎ the italic h), the j's hook (ℊ),
  the 1's flag (ℴ, ℘), a loop on the l (ℓ). ℇ is the reversed З.
* **Letters set as one sign** (Roman numerals, ₧ ₨ ₯ ₷ ₶, ℡ ℻):
  `symkit.set_tight` puts each pair at half the light the spacing gives a
  letter's side, measured by area, never closer than 0.55 of a stem.
* **Small letters inside signs** (₠ ₢ ℠ ⅍) keep their stems in proportion
  to their own size, never heavier than 2.6 of their own module
  (`symkit.small_letter`), so a small S or E does not close.
* **Concentric bowls** (ↂ ↈ ↇ) cut their inner corners shorter by
  (2 − √2) of the distance between them, so the white between runs at one
  width round the corner; their bars thin (to 0.7) before the sign
  outgrows the cap height, and then it grows about the axis.
* **Turned and reversed glyphs** are stamped through an orthogonal map
  with their chamfer record (`symkit.stamp_t`), so the italic curves them
  as it curves the originals.
* **Explicit stroke widths on diagonals** are set as `geom.Thickness` sets
  its own (`symkit.across`): never under the floor, and corrected for the
  italic's shear.
* **Mono**: a sign wider than the cell is condensed into it, module,
  strokes and the figures' body alike, measured on its natural width and,
  for non-letters, its ink; a sign tied to the cap height that still does
  not fit (‱) is drawn smaller about the axis (`symkit.sign`).

## Hooks into shared code

* `font._place`: glyphs of `kind='space'` are empty with their own advance
  (a cell in Mono, zero-width ones nothing).
* `variable.align`: a glyph empty in every master passes through.
* `features.py`: `MORE`, single substitutions other modules add to `sups`,
  `subs`, `sinf`, `numr`, `dnom` and `case` (used for + − = ( ) i n and the
  inferior letters, and the case forms of ‣ ⁃ ⁓ ⁅ ⁆); `_fraction` registers
  ½ ¼ ¾ through `symkit.sign` so they fit the Mono cell as ⅓ ⅛ do.
* `glyphs/__init__.py`: one import line and the aliases.

## Known issues

* ₦ at Black and at the grade +100 corner: its two counters stay open but
  tight (a third of a stem).
* Interpolation: the variable font draws every new glyph (0 could not
  vary), but 188 of their 2230 checked locations differ from the exact
  drawing by more than 3 units (existing glyphs: 220 of 5570), worst 31.9
  units at (800, 50, 100), where the max() switches of growing white and
  thinning bar pairs meet three axes.
* Mono condenses wide signs (fractions, ⁇, ※, Roman numerals of three or
  four letters) lighter than the cell's other glyphs.
