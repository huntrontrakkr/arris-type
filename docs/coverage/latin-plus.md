# Latin+: Vietnamese, pinyin, Latin Extended-B and Additional, combining marks

Code: `src/arris/glyphs/latin_plus.py` (marks, letters, the composed set,
the combining marks), `src/arris/anchors.py` (mark positioning), and small
changes to `marks.compose` and `font.py` (below).

## What was added (278 glyphs)

* **Vietnamese**, complete: Ơ ơ Ư ư and U+1EA0–U+1EF9 (every vowel with
  dot below, hook above, tilde, acute and grave, alone and with circumflex,
  breve and horn), with the dong sign ₫.
* **Pinyin**: Ǎ–ǜ (U+01CD–U+01DC), Ǹ ǹ, Ḿ ḿ; ê̄ and ê̌ through mark
  positioning.
* **Latin Extended-B**: Ə ə (Azerbaijani), Ǝ ǝ, ƒ, Ʒ ʒ Ǯ ǯ and Ǥ ǥ (Skolt
  Sami), Ǟ–ǭ (Livonian and Sami: Ǟ ǟ Ǡ ǡ Ǣ ǣ Ǧ ǧ Ǩ ǩ Ǫ ǫ Ǭ ǭ), ǰ, Ǵ ǵ,
  Ǻ–ǿ, Ȁ–ȗ (double grave and inverted breve), Ȧ–ȳ, the digraphs Ǆ–ǌ and
  Ǳ–ǳ, the click letters ǀ ǁ ǂ ǃ.
* **Latin Extended Additional**: the Irish dotted letters Ḃ ḃ Ḋ ḋ Ḟ ḟ Ṁ ṁ
  Ṗ ṗ Ṡ ṡ Ṫ ṫ, Welsh Ẁ ẁ Ẃ ẃ Ẅ ẅ Ỳ ỳ, and Ṅ ṅ Ẓ ẓ Ḥ ḥ Ṣ ṣ Ṭ ṭ Ḍ ḍ.
* **Combining marks** U+0300–0304, 0306–030C, 030F, 0311, 031B,
  0323–0328, 0331 (22), with flatter `.case` forms of the marks above
  (14), the three Vietnamese pairs (circumflex with acute, grave, hook) as
  single marks and their `.case` forms (6), and the dotted circle ◌.

## New marks

Drawn in the marks' language (`marks.py`), each a function `fn(g, x, y,
case)` registered in `marks.ABOVE`, `marks.BELOW` or `marks.ATTACHED`:

* **dot below**: the dot, hung a gap under the baseline. Like the comma
  below it keeps inside the descender (to 1.15 of it): where the stem's
  square would not fit, the dot is smaller (from Black up).
* **hook above**: the 7 in small. A bar, and from its right end a diagonal
  at the 7's 2:1 back down to the middle, cut flat; the bar reaches as far
  left as the diagonal reaches right, so the hook is centred. Its strokes
  lighten at heavy weights as the breve's sides do.
* **horn**: leaves the letter's top-right extreme along the diagonal (the
  middle of an O's corner chamfer, the cut corner of a U's stem), square to
  that chamfer at 45 degrees, then rises and is cut flat: the 1's flag turned
  outward. The same point is the combining horn's anchor.
* **ring below, macron below, dieresis below**: the ring, macron and
  dieresis hung below, inside the same depth as the dot below (they lighten
  to fit, the ring's counter about a stroke and a fifth).
* **double grave, inverted breve**: two graves (as the double acute), the
  breve turned over.

## Rules introduced

* **Marks stack by measure** (`marks.stack_above`). The first mark above
  stands a gap over the base's highest ink, each next one a stack gap (0.6
  of the gap) over the finished ink of those before it, so a dieresis
  carries a macron lower than an acute would. (This also lowers the tonos
  of Greek ΐ ΰ onto its dialytika: the only existing glyphs that change.)
* **Vietnamese tone marks beside the circumflex** (`marks.BESIDE`): acute,
  grave and hook are drawn where the circumflex is, then moved out at 45
  degrees, square to its right arm, until they stand a stack gap clear. A
  breve carries its tone mark on top; a circumflex carries a tilde on top.
* **Marks never fuse.** A stacked or beside mark also keeps its raw strokes
  (before the corner rule) apart from those of the marks before it, or the
  union would join them (the watch balance's sharp stroke ends reach
  further than the finished ink shows); and the stack keeps a stack gap
  from a horn, moving left if it must (ỡ at Black).
* **A stack stays inside the line** (`marks.line_top`, `LIGHTEST`). Where
  the marks above would rise past the font's Windows ascent (1160), all of
  them lighten and shrink together (strokes, module and edge breaks scaled
  by one factor, never below 0.5), as heavy faces draw their accents. It
  binds only on stacks: Ǻ from Regular, Ẫ Ẵ Ễ Ỗ ǻ from SemiBold, the other
  capital stacks from ExtraBold (Ǘ Ǚ Ǜ at Black), lowercase stacks only at
  Black with positive grade. Every new glyph stays inside 1160 at Black,
  grade +100, watch 100.
* **Marks below clear a descender** (`marks.clear_below`): a mark below
  goes under the body's centre unless the base's ink below the baseline
  would crowd it; then it moves right until it stands a gap clear. ỵ gets
  its dot beside the descender, under the right arm, as Arial, Segoe UI,
  Bahnschrift, Consolas and Cascadia place it.
* **Joined marks get room in a cell**: in Mono, where a mark joined to its
  base (the horn) would reach past the cell's edge, the base is drawn that
  much narrower.
* **The schwa's arm stops short.** ə is the e turned, but its arm stops a
  module and a half short of the left side, so the mouth is wider than the
  e's: Arris's a is the turned e with a stem, and a/ə measured 0.21 with
  the arm run on (Chakra Petch and Barlow: 0.21); 0.27 short
  (`tools/letter_confusion.py`, Regular, 11 arcminutes).
* **Digraphs are spaced as their letters**: the first letter's right
  bearing and the second's left, but never closer than half a sidebearing
  between the inks (the L's foot and the J's hook). In Mono both letters
  are drawn small enough to fit the cell at their own widths (a Z's diagonal
  cannot be squeezed into half a cell).

## Mark positioning (`src/arris/anchors.py`)

Anchors are measured on each glyph's placed outline, so a letter followed
by a combining mark shows as the composed letter does:

* bases (letters, figures, ◌): **top** over the body's centre, a gap above
  the highest ink; **bottom** under the centre on the baseline, or beside a
  descender as `clear_below` puts the dot below; **ogonek** at the right
  foot; **horn** at the top-right extreme along the diagonal;
* marks: the anchor they attach by (where their drawing assumed the base),
  and for stacking one a stack gap beyond their ink.

Italic anchors are measured on the upright drawing and sheared, so marks
follow the slant. Checked against the composed letters (base plus marks,
positioned by these anchors, against the composed glyph; mean outline
difference): at Regular every composed letter of the generic design lands
within 1.3 units upright and 4 in the italic, the largest being marks that
touch their base (cedilla, ogonek, horn), whose junction the composed
letter fills and two overlapping glyphs cannot; at Black within 5 upright
and 6 in the italic. The
rest differ by design: the caron as an apostrophe (ď ľ Ľ ť), the cedilla
as a comma (ģ ķ ļ ņ ŗ ţ), the Greek capitals' tonos, the stacks the line
rule lightens (which mark positioning, stacking separate glyphs, does not),
and ỡ at heavy weights, whose tilde steps left of the horn.

Features:

* `ccmp`: i and j lose their dot before a mark above (and į ị decompose
  so theirs goes too); marks above take their `.case` forms after a capital
  or a figure; a circumflex followed by an acute, grave or hook becomes the
  Vietnamese pair.
* `mark`, `mkmk` (marks above stack on marks above, marks below under marks
  below, each lookup filtered to its own side), and GDEF glyph classes.

## Shared code touched

* `glyphs/__init__.py`: one import line, `latin_plus`, before `marks`.
* `glyphs/marks.py`: `compose` handles any sequence of marks (stacking by
  measure, `BESIDE`, the line rule, `ATTACHED`, `clear_below`).
  Every existing composed glyph is unchanged except Greek ΐ ΰ.
* `font.py`: `_place` gives `kind='mark'` glyphs no advance (hung over the
  glyph before, `mark_over`) and records each glyph's body and upright
  rings (`BODIES`); `build` appends `anchors.fea(names, placed, p)` to the
  feature code, before kerning.

## Known issues

* Kerning is flat pairs (`kerning.py`), so its size grows with the square
  of the letters: Regular's kerning went from 20,450 pairs to 40,945 and
  the file from 116 to 227 KB; the variable font's pairs from 54,520 to
  131,944, its GPOS from 358 to 886 KB and the file from 1.0 to 1.9 MB.
  Kerning composed letters by their base's classes would undo most of that.
* Mono: the marks' zero advance, in the middle of the glyph order, keeps
  `hhea.numberOfHMetrics` at 567 (it was 2; fontbakery warned about it
  before too).
* The compatibility digraphs in Mono are small letters (about half size).
* Variable font: the digraphs interpolate less well than the rest (Ǉ ǈ ǉ
  up to 12 units at 300, where the inks' minimum distance starts to bind),
  as do the combining comma and dot below where their depth limit starts
  to bind (8 units), as their composed letters' marks already do.
