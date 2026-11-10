# Submitting Arris to Google Fonts

What Google Fonts asks of a new family (its guide, "Onboarding" and
"Upstream repo", read 2026-11-09), where Arris stands on each, and the text
of the request. The request is an issue on
[google/fonts](https://github.com/google/fonts/issues/new/choose), "Add a
new font", filed by the copyright holder.

## The fonts offered

`Arris[GRAD,wght].ttf` and `Arris-Italic[GRAD,wght].ttf`, weight 100–900 and
grade −100 to 100, written from a release zip by `tools/google_fonts.py`.
The watch axis (WTCH) is left out: it is not in Google Fonts' axis registry,
and the fonts are instanced at its default, 0, which is the family as it is
normally set. Arris Mono and Mono Narrow are static families and would
follow as requests of their own.

## Where Arris stands

| Google Fonts asks | Arris |
|---|---|
| An original design of good quality (the Google Design team decides) | Original; theirs to judge |
| Wholly OFL 1.1, every style of the family | Yes: `OFL.txt`; the code is MIT, which the OFL allows of build scripts |
| No Reserved Font Name | None |
| Copyright holders have signed Google's Contributor Licence Agreement | **To do, by the owner**: https://cla.developers.google.com |
| A plain, unique family name | "Arris"; fontbakery's name check to confirm |
| Developed in public on GitHub, releases tagged | Yes |
| Sources in a font editor's format (UFO, .glyphs), built with fontmake; for any other source, a script that converts it to UFO, the UFOs committed | Arris is drawn by code (`src/arris`). `tools/ufo_sources.py` writes the fonts' masters as UFOs with their designspace, and fontmake builds the same fonts from them: see "UFO sources" |
| TTF binaries | Yes |
| GF Latin Core | Yes, and Vietnamese, Cyrillic, Greek |
| Passes fontbakery's `googlefonts` profile | See "Checks" |
| Repository layout: `fonts/`, `sources/`, `documentation/`, `AUTHORS.txt`, `CONTRIBUTORS.txt`, `OFL.txt` | `OFL.txt` and `AUTHORS.txt` are there; fonts are release assets, not committed; the rest is to add if the request is taken up |

## The request

Title: **Add Arris**

> **Family:** Arris, a chamfered geometric sans: monoline, every outer
> corner cut at 45 degrees, with a cursive italic. Its figures began as the
> pixel numerals of a watch face; the alphabet was developed from them.
>
> **Repository:** https://github.com/huntrontrakkr/arris-type
> **Specimen:** https://arristype.com
> **Licence:** SIL OFL 1.1, no Reserved Font Name.
>
> **Fonts:** two variable fonts, `Arris[GRAD,wght].ttf` and
> `Arris-Italic[GRAD,wght].ttf`: weight 100–900, grade −100 to 100 (grade
> changes no advance width). 2,192 characters: Latin including Vietnamese
> and West African, Cyrillic, Greek, arrows, mathematics, box drawing.
>
> **Sources:** Arris is drawn by code: every glyph is a short program over
> one rule set (a module grid, stroke weights, the 45-degree corner). For
> Google Fonts the masters are also written out as UFOs with a
> designspace (21 full masters, and sparse layers for the glyphs that
> need masters between them), and fontmake builds the fonts from those.
> The fontmake build is checked against the project's own: outlines within
> two units everywhere, shaping identical.
>
> **Quality checks run on every release:** fontbakery (universal profile,
> no FAIL), OTS, an interpolation check of the variable fonts against the
> drawings, an outline topology check along every axis, and a test suite.
> The `googlefonts` profile's results on the two fonts above are attached.
>
> I've signed the Google CLA.

## UFO sources

    uv run python tools/google_fonts.py build/release/Arris-<version>.zip build/google-fonts
    uv run python tools/ufo_features.py "build/google-fonts/fonts/variable/Arris[GRAD,wght].ttf" build/arris.fea
    python tools/ufo_sources.py "build/google-fonts/fonts/variable/Arris[GRAD,wght].ttf" sources --features build/arris.fea
    fontmake -m sources/Arris.designspace -o variable --keep-direction

(and the same for `Arris-Italic`). Measured on 1.015, the fontmake build
against the release's two-axis font, at 95 places across both axes:

| | Upright | Italic |
|---|---|---|
| Glyphs | 2,207 | 2,207 |
| Farthest any point stands from the release's | 2.1 units | 2.0 units |
| Marks on letters, 19,800 sequences at 11 places | identical | identical |
| Features, every character under every feature | identical | identical |
| Form switches ($ ¢), 729 places | identical | identical |
| Kerned pairs, 36,000 at 11 places | 27 differ, by 2 units, at one place between masters | 28, likewise |
| Size of the sources | 194 MB, 82,000 files | 246 MB, 87,000 files |

Still to do before the request is filed:

- **Where the UFOs live.** 440 MB and 169,000 files is a lot for this
  repository; a repository of their own, written by the release workflow,
  may suit better. The owner's decision.
- **The repository's layout** as the guide has it (`sources/` with a
  one-command build, `fonts/`, `documentation/`, `CONTRIBUTORS.txt`).
- **The fontmake build through Google's own pipeline** (gftools-builder),
  and fontbakery on what it makes: names, STAT and the instances have not
  been compared with the release's yet.

Found on the way, in the release itself: for 14 glyphs, at the heaviest
weights and grades, the advance a shaper reads (HVAR) is not the advance
the glyph's own outline data was made for (⁜ by 140 units at Black, grade
100; ⊚ 25, ⊈ ≱ 15, ₹ ₱ ₺ about 10). HVAR is made from the font's 28
masters, the outlines from each glyph's own. To fix in `arris.vf`.

## Checks

fontbakery `check-googlefonts` on the 1.015 two-axis fonts (2026-11-10):
no ERROR, no FAIL, 24 warnings (12 kinds, each on both fonts), 239 passes.
The warnings: `alt_caron`, `contour_count`-style design notes and
`math_signs_width` (see docs/TODO.md); `file_size`; `interpolation_issues`
and `overlapping_path_segments` (reports); `mandatory_avar_table` (no avar:
the weight axis is linear); `unreachable_glyphs` (the form switches'
glyphs); `soft_dotted`; `shape_languages`; `vendor_id` (none registered);
and two that are the Google Fonts repository's own (`article`,
`unreachable_subsetting`).
