# Arris

A chamfered sans: octagonal and monoline, every outer corner cut at 45
degrees, in nine weights, upright, italic and mono, with three variable
axes. An *arris* is the sharp edge where two faces meet; a chamfer is what
you get when you break it. Its figures are the Chamfer clock figures of the
[Dymaxion watch face](https://github.com/huntrontrakkr/dymaxion-watch-face).

![Weights](proofs/figures-weights.png)

![Italic](proofs/italic.png)

## Families

| Family | What it is |
|---|---|
| **Arris** | Proportional letters, tabular figures. Measured optics. Nine weights. |
| **Arris Watch** | The same with the watch's own stroke balance (diagonals as wide across as a stem). |
| **Arris Italic**, **Arris Mono Italic** | Slanted ten degrees, every chamfer a curve, every point the upright keeps sharp kept sharp; a single-storey a and a descending f. Nine weights each. |
| **Arris Mono** | Every glyph on the figures' 10-module pitch: slabbed I, footed i l r, dotted zero, and programming ligatures (`->` `=>` `!=` `===` `<=` `:=` `|>` `</>` `<$>` `#{` …) that keep every character in its cell. |
| **Arris[GRAD,WTCH,wght]**, **Arris-Italic[GRAD,WTCH,wght]** | Variable: weight 100–900, grade −100–100, watch proportions 0–100; linked as one family on the `ital` axis. |

Coverage, about 2,150 code points (details in `docs/coverage/`):

* **Latin**: Western, Central and Eastern European, Turkish, Baltic,
  Romanian; Vietnamese; pinyin; Latin Extended-B and much of Extended
  Additional (Irish, Welsh, Sami, Livonian, Azerbaijani); combining marks,
  placed by `mark`/`mkmk`.
* **Cyrillic**: Russian, Ukrainian, Belarusian, Bulgarian, Serbian,
  Macedonian, the Central Asian, Caucasian, Siberian and Komi letters;
  Bulgarian forms and Serbian/Macedonian italics through `locl`.
* **Greek**: monotonic, with the symbol, archaic and lunate letters.
* **Symbols**: general punctuation, super- and subscripts, every currency
  sign, letterlike symbols, number forms (Roman numerals, fractions),
  arrows, mathematical operators, technical symbols, geometric shapes,
  dingbats.
* **Terminal**: all box drawing, block elements, shades and Braille, cell
  for cell, and the Powerline glyphs.

Features: `tnum` (default) `pnum` `calt` (the watch's time colon between
figures) `zero` `ss01` `sups` `subs` `sinf` `numr` `dnom` `frac` `ordn`
`case` `locl` `ccmp` `mark` `mkmk` `kern`; in Mono, `calt` ligatures,
`ss03` (no ligatures), `cv01`, `cv02`. And `ss20`, "Watch pixels": the
figures as the watch drew them, one square per pixel of the 9×12 masters
they grew from.

## Building

```
uv sync
uv run python tools/build_fonts.py              # Arris, all weights
uv run python tools/build_fonts.py all watch    # Arris Watch
uv run python tools/build_fonts.py all mono     # Arris Mono
uv run python tools/build_fonts.py all italic   # Arris Italic (add mono for Arris Mono Italic)
uv run python tools/build_vf.py                 # the variable font, with its interpolation check
uv run python tools/build_vf.py italic          # the italic variable font
uv run pytest                                   # the figures against the watch's pixels
uv run python tools/presentation.py             # the presentation: presentation/slides/*.png and arris.pdf
```

The presentation (`presentation/`) is forty-two slides set in the built
fonts: the family, axes, figures and their pixel masters, the italic, text,
languages, Mono in code and in a terminal, and applications from a
departure board to a watch face. Its chrome borrows from the graphic
language of Bungie's *Marathon* (2026): a solid tab, a tag chip for the kind
of slide, a pager, crosshairs, a strip of codes up the right edge, serials
and date stamps. It renders with Playwright's Chromium.

Fonts land in `build/`. Proof tools: `tools/master_sheet.py` (pixel
masters), `tools/overlay.py` (constructions over masters),
`tools/weights_sheet.py`, `tools/hbspec.py` (shaped with HarfBuzz, rendered
with FreeType, features and axes as arguments).

## How it is made

`docs/DESIGN.md` explains what the watch figures do, the corner rule, how
letters were drawn in the same language, how weights keep their openings,
and where the optical corrections come from. In short:

* `heritage/`: the watch's pixel masters, copied verbatim.
* `src/arris/masters.py`: pixel masters for the letters.
* `src/arris/geom.py`: strokes to ink. Centrelines with direction-dependent
  thickness, chamfered bowls, and the watch's corner rule on the union.
* `src/arris/glyphs/`: every glyph as a construction in its master's
  coordinates, with its openings declared.
* `src/arris/vision.py`, `src/arris/spacing.py`, `src/arris/kerning.py`:
  measuring instead of eyeballing.
* `src/arris/variable.py`: making masters point-compatible after the fact.
* `src/arris/italic.py`: the italic, from the upright drawings.
* `tools/confusion.py`, `tools/letter_confusion.py`: which figures and
  letters a reader could mistake for one another, against legibility faces
  (`docs/research/legibility.md`).
* `tools/stroke_scan.py`: every glyph's strokes certified, upright and
  italic: no crossing outlines, nothing below the stroke floor, no swelling.
* `tools/scan_counters.py`: counters that tighten or close at heavy weights.
* `tools/squint_scan.py`: holes and slots a squinting reader loses, weight
  by weight (`arris.vision.narrow_whites`).

## Licence

The watch's Draft lettering in `heritage/` is Apache-2.0 (Dymaxion
contributors). Arris is intended for release under the SIL Open Font Licence
1.1.
