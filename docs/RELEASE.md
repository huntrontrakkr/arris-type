# Releasing Arris

## Cutting a release

1. Set `VERSION` in `src/arris/font.py` (the fonts' version string,
   `head.fontRevision` and the unique ID all follow it).
2. Rebuild everything: `build/scripts/rebuild.sh` (static families, both
   variable fonts with their interpolation check, tests, fontbakery,
   proofs, the specimen's WOFF2s and the presentation).
3. Read `build/scripts/logs/post.log`: pytest passes, fontbakery reports
   no FAIL and no ERROR for the static, variable and Mono sets.
4. Package: `uv run python tools/package.py` writes
   `build/release/Arris-<version>.zip` (static, variable, web, OFL.txt,
   AUTHORS.txt, README.md). It refuses fonts that do not carry the release
   version, the licence URL and installable embedding.
5. Tag the commit `v<version>`; attach the zip to the GitHub release.

## Licence and metadata

SIL Open Font License 1.1 (`OFL.txt`), copyright The Arris Project Authors
(`AUTHORS.txt`); no Reserved Font Name. Every font carries the copyright
(name 0), the licence and its URL (13, 14), embedding installable (fsType
0). The vendor ID is `NONE` (unregistered): register one with Microsoft
before a commercial distribution if wanted.

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
