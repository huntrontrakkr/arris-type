# Arris Mono against Fira Code: every alternate, switch and ligature

An audit, 2026-11-02 (Eastern), of Fira Code 6.2 (read from its font: GSUB
features, glyph names, contextual rules) against Arris Mono on `main`.
The owner's call: add all of it. Each item is drawn in Arris's own
vocabulary (chamfered, the 2:1 and 45-degree strokes, the cell), not
copied from Fira; Fira says *what* to offer, Arris how it looks.

## 1. Alignment that happens on its own (`calt`)

| Fira | What it does | Arris now | To do |
|---|---|---|---|
| `colon.uc` | `:` next to a capital rises to the capitals' middle (`A:B`, `HH:MM`) | **has it** between figures (the watch's time colon) | extend to capitals |
| `hyphen.lc`, `plus.lc`, `asterisk.lc` | `-` `+` `*` between lowercase letters drop to the lowercase middle (`a-b`, `x*y`, `kebab-case`) | no: every operator sits on the capitals' middle (360) | add: lowered forms, used between lowercase |
| `hyphen.case`, `parenleft.case` … | the same raised for capitals | `case` feature only (hyphen, colon) | extend to brackets in capital context |
| `x.multiply` | `x` between figures, and in `0x`, becomes a times sign (`1920×1080`, `0×FF`) | no | add |
| `less.center`, `greater.center`, `colon.center` | `<` `>` `:` centred where they meet other operators | partly (ligatures place them) | check case by case |

Fira's rules, read from its GSUB (6.2): `-` `+` `*` take their lowered forms
when a lowercase letter touches them on either side, except between a
capital and a lowercase letter (`A-b`, `a-B` stay); `:` rises when a
capital touches it on either side, with the same exception. `x` becomes
`×` between figures (`1920x1080`) and after a zero before a hex digit
(`0xFF`). `<` `>` `:` take centred forms beside one another (`<:` `:>`).

## 2. Character variants (`cv01`–`cv32`)

| Fira | What | Arris now | To do |
|---|---|---|---|
| cv01 | single-storey a | **has it** (`cv01`) | — |
| cv02 | g, the other storey | one g | draw the alternate g |
| cv03–cv06 | four i's (plain, tailed, slabbed, …) | Mono: footed i | draw the others (plain, tailed) |
| cv07–cv10 | four l's | Mono: footed l | draw the others (plain, tailed, slabbed both sides) |
| cv11–cv13 | zero: dotted, slashed, plain | **has all three** (default dotted, `zero` slashed, `cv02` plain) | tags only |
| cv14 | 3 with a flat top | Arris's 3 *is* flat-topped (the watch's) | offer the round-topped one as the variant |
| cv15, cv16 | asterisk: unlowered / the maths ∗ | one asterisk, centred | variants once `*` lowers (1) |
| cv17 | tilde, lower | one tilde | draw |
| cv18 | % and ‰ alternates | one each | draw |
| cv19–cv23 | `<=` `=<` `>=` drawn as arrows or as ≤ ≥ (several) | `<=` `>=` as ≤ ≥, `ss03` plain | the arrow forms; `=<` |
| cv24 | `/=` as ≠ or struck | struck (with `!=`) | the ≠ form |
| cv25–cv28, cv32 | ligatures `.-` `:-` `[]` `{.` `.}` `.=` | no | draw |
| cv29 | braces, the other form | one brace | draw |
| cv30 | taller bar | one bar | draw |
| cv31 | parentheses, the other form | one paren | draw |

## 3. Stylistic sets (`ss01`–`ss10`)

| Fira | What | Arris now | To do |
|---|---|---|---|
| ss01 | r, another form | Mono: footed r | draw |
| ss02 | `<=` `>=` as comparisons, not arrows | **has it** (Arris `ss03`) | tags only |
| ss03 | ampersand, another form | one & | draw |
| ss04 | dollar, another form | one $ (the stem through or stubs, by weight) | draw |
| ss05 | at, another form | one @ | draw |
| ss06 | thin backslash in escapes (`\n` `\\`) | no | add (contextual) |
| ss07 | `=~` `!~` ligatures (regex) | no | draw |
| ss08 | `==` `===` `!=` `!==` with gaps | no (bars run through) | draw |
| ss09 | `>>=` `<<=` `\|\|=` `\|=` ligatures | no | draw |
| ss10 | `Fl` `Tl` `fi` `fj` `fl` `ft` ligatures | no | draw (cell-wide pairs) |

## 4. Ligatures

Fira 6.2: 86 fixed ligatures, and 70 pieces it chains into arrows and bars
of any length (`---->`, `<====>`, `|---|`, `#####`, `____`). Arris Mono: 49.
Of Fira's 56 that Arris lacks (docs/research/mono-cell.md §4): about 9 are
joins or new signs, the rest draw the characters closer (`::` `..` `//`
`&&` `||` `**` `<<` `>>` `?.` `??` `<*>` …), which DESIGN.md §8 leaves as
characters; the owner's call is to add them all, so §8 changes. Then the
any-length arrows and bars.

## 5. Feature tags: a decision

Arris already uses `cv01` (single-storey a, as Fira), `cv02` (plain zero;
Fira's cv02 is the g), `ss01` (dotted zero, proportional; Fira's is the r),
`ss02` (the 5), `ss03` (plain comparisons; Fira's is ss02), `ss04` (Mono
Italic's cursive f and k; Fira's is the dollar), `ss20` (pixel figures).
Matching Fira's numbers in Mono would let an editor setting written for Fira
work on Arris, but would move four of Arris's existing switches. **The
owner's call (2026-11-02): keep Arris's tags.** Fira's variants go on free
numbers, and the README carries a table from Fira's tags to Arris's.

## 6. Order of work

1. The cursive f and k (ss04), finished and merged.
2. Alignment (§1): lowered `- + *` in lowercase, `×` in dimensions and `0x`,
   the colon among capitals and beside < >. **Done** on `fira-parity`
   (`glyphs/alignment.py`); a sign doubled stays put, where Fira leaves it
   to its sequences.
3. The ligatures (§4), then the any-length arrows and bars.
4. Character variants and stylistic sets (§2, §3), in batches, each drawn,
   checked (topology, cell, Regular and Bold, upright and italic) and shown.
