# Japanese and Chinese: what it would take

Scoping notes, 2026-10-22. Nothing here is built yet.

## How much

| Tier | Characters | What it covers |
|---|---|---|
| Kana and punctuation | ≈ 400 | hiragana, katakana (with small and half-width forms), CJK punctuation 、。「」・ー, full-width ASCII |
| Jōyō kanji | 2,136 | everyday Japanese (with ≈ 860 Jinmeiyō for names) |
| JIS X 0208 | 6,355 kanji | a complete standard Japanese font |
| GB 2312 | 6,763 hanzi | standard Simplified Chinese (Tōngyòng Guīfàn: 8,105) |
| Big5 | 13,053 hanzi | Traditional Chinese (5,401 common) |

Japanese and Chinese share most characters but not their forms: 骨 直 角
令 and hundreds more are drawn differently by region. Fonts either ship
one family per region (Noto Sans JP, SC, TC) or switch forms with `locl`.

## The constraint: density

Arris's em is 1000 units, its module 60, its cap 720. A kanji fills a
face of about 900. A character like 量 stacks about nine horizontal
strokes in that height: about 100 units of pitch for a bar and its white.
With the white at the font's own least white (a module), a bar can be 40
units. The Latin Regular's horizontal is 79; Black's is 149.

So the CJK cannot carry the Latin weights stroke for stroke. Its strokes
have to be about half the Latin's at Regular, and thin with each
character's density: 一 人 口 can be heavy, 鬱 (29 strokes) cannot. Arris
already has the machinery: openings that hold their share of the stem,
tight stacks that thin their bars, symbols that lighten to keep their
white, and the squint rule. For CJK these become the main rule rather
than the exception, with much wider bounds (a dense character at Black
may need strokes at a third of a simple one's).

## Three ways to get the structure

**A. Pixel masters.** Arris's figures came from the watch's pixel masters,
and a 16-pixel CJK font maps one pixel to one module: 16 modules are 960
units, nearly the em. The engine already turns pixel staircases into its
45° and 2:1 diagonals.

- Shinonome 16-dot gothic: JIS X 0208 (kana and 6,355 kanji), public domain.
- GNU Unifont: every BMP ideograph at 16×16, dual GPLv2+FE / OFL 1.1
  (since 13.0.04). Mostly Chinese forms; quality varies.
- Ark Pixel (OFL-1.1/MIT): pan-CJK with regional forms, but still missing
  many characters; 12 px is its main target.

Clean licences, and the structure is already reduced to horizontals,
verticals and steps. But 16 px is a compromise for dense characters
(strokes merged or dropped), and a 2-module stroke pitch cannot hold more
than a light weight, so dense glyphs need their structure relieved, not
just their strokes thinned.

**B. Stroke data.** KanjiVG (≈ 6,700 kanji, stroke order and centrelines)
and Make Me a Hanzi (≈ 9,500 hanzi with stroke medians). Real
calligraphic structure, snapped to Arris's directions. But KanjiVG is CC
BY-SA 3.0 (share-alike) and Make Me a Hanzi's graphics are under the
Arphic Public License; neither fits a font meant for the OFL without a
licensing decision.

**C. Components.** Draw 300–500 components (radicals and common parts,
with their positional forms: 氵 vs 水, 亻 vs 人) as constructions, as every
Arris letter is, and compose characters from Ideographic Description
Sequences (⿰ ⿱ ⿴ …). BabelStone's IDS file covers all 97,680 encoded
ideographs, and its maintainer waives copyright. This is the most Arris
way, but automatic composition needs a correction loop per character:
proportions change with position and neighbours.

A hybrid is likely best: kana and components drawn by hand; each kanji's
layout taken from its IDS, checked against a pixel master; the scans as
gatekeepers.

## Engineering

- **Families.** Separate CJK families (Arris JP, SC, TC) that carry the
  Latin, as Noto does: the Latin fonts stay small. 7,000 glyphs per weight
  of straight-line outlines is several MB per static font; the variable
  font, with 16 masters, more; the web specimen would need subsetting.
- **Build.** Today ≈ 2,150 glyphs per family; CJK triples or quadruples
  that. Drawings would need a disk cache keyed by glyph and parameters,
  and parallel builds per glyph.
- **Metrics.** The ideographic em box (−120 to 880 in 1000) against
  Arris's descender of 180 and ascender of 780; kanji taller than the caps
  (about 1.2×); `BASE` table, `vhea`/`vmtx` for vertical Japanese.
- **Mono.** CJK characters are double width in terminals (East Asian
  Width): two Mono cells, so 2 × the weight's advance.
- **Italic.** CJK has no italic; the italic families keep it upright, as
  they keep terminal cells.
- **Features.** `locl` (ja, zh-Hans, zh-Hant), `vert`/`vrt2` for vertical
  setting, `halt`/`palt` (proportional punctuation), `fwid`/`hwid`.
- **Legibility.** The confusion tools apply as they are: 土/士, 未/末,
  己/已/巳, 日/曰, 人/入/八 under the vision model.

## A first step

1. Kana and CJK punctuation by hand in the engine (a few hundred glyphs,
   the size of the Greek work), at all weights; settle the CJK stroke
   scale and metrics on them.
2. A pilot of about 100 kanji chosen for structure (simple, ⿰, ⿱,
   enclosures, dense, heavy diagonals) by route A from Shinonome, then the
   same set by route C, side by side at Regular and Black.
3. Decide the route, the region (Japanese first?), the weights, and
   whether the CJK families vary.

## Sources

- [KanjiVG](https://kanjivg.tagaini.net/) (CC BY-SA 3.0)
- [Hanzi Writer licence notes on Make Me a Hanzi data](https://hanziwriter.org/license.html) (Arphic Public License)
- [Ark Pixel Font README](https://cdn.jsdelivr.net/gh/takwolf/ark-pixel-font@master/README.md)
- [Shinonome font (public domain)](https://plan9port.googlesource.com/plan9/+/refs/heads/master/font/shinonome/README)
- [GNU Unifont](https://unifoundry.com/unifont/) (GPLv2+FE / OFL 1.1)
- [BabelStone IDS](https://babelstone.co.uk/CJK/IDS.HTML) ([IDS.TXT header](https://babelstone.co.uk/CJK/IDS.TXT): copyright waived)
- [cjkvi-ids](https://github.com/cjkvi/cjkvi-ids) (CHISE-derived; GPLv2 for the rest)
