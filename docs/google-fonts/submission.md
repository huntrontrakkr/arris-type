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
| Sources in a font editor's format (UFO, .glyphs), built with fontmake | **No: Arris is drawn by code** (`src/arris`), one command builds it. The guide allows an exception on request; the request below asks for it |
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
> **Sources, and an exception I'd like to ask for:** Arris has no drawn
> sources. Every glyph is a short program over one rule set (a module grid,
> stroke weights, the 45-degree corner), and the fonts are built from that
> code in one command, in CI, on every release. There are no UFOs to give
> you that would be sources rather than exports. I'd like to ask whether
> the family can be taken as it is built, or what you would need instead.
>
> **Quality checks run on every release:** fontbakery (universal profile,
> no FAIL), OTS, an interpolation check of the variable fonts against the
> drawings, an outline topology check along every axis, and a test suite.
> The `googlefonts` profile's results on the two fonts above are attached.
>
> I've signed the Google CLA.

## Checks

(fontbakery `check-googlefonts` on the 1.015 fonts: results to be added.)
