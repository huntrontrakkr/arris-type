# Terminal and UI glyphs

Arris Mono as a terminal font: box drawing, block elements, shades,
Braille, the Powerline glyphs, geometric shapes and a set of dingbats. The
proportional families carry the same glyphs. 594 glyphs in three modules:

| Module | Block | Code points | Glyphs |
|---|---|---|---|
| `glyphs/terminal.py` | Box drawing | U+2500–257F | 128 |
| | Block elements (with the shades ░▒▓) | U+2580–259F | 32 |
| | Braille patterns | U+2800–28FF | 256 |
| | Powerline separators | U+E0B0–E0B3 | 4 |
| | Black corner triangles ◢◣◤◥ | U+25E2–25E5 | 4 |
| `glyphs/shapes.py` | Geometric shapes (the rest) | U+25A0–25FF | 92 |
| `glyphs/dingbats.py` | Dingbats and symbols | ✂ ✓ ✔ ✕ ✖ ✗ ✘ ✚ ✛ ✜ ✢ ✣ ✤ ✥ ✦ ✧ ✱ ✲ ✳ ✴ ✵ ✶ ✷ ✸ ✹ ❌ ❎ ❓ ❔ ❕ ❗ ➔ ➜ ➤ ★ ☆ ☐ ☑ ☒ ☰–☷ ☺ ☹ ♠ ♣ ♥ ♦ ♤ ♧ ♡ ♢ ♩ ♪ ♫ ♬ ⚠ ⚡ ⚙ ⚐ ⚑ ⚫ ⚪ ⬆ ⬇ ⬅ ➡ ⬛ ⬜ ⬤ | 75 |
| | Powerline icons (branch, line number, lock) | U+E0A0–E0A2 | 3 |

Names are AGL names where they exist (`SF100000`, `block`, `ltshade`,
`filledbox`, `circle`, `spade`...), else `uniXXXX`.

## Cells

A terminal sets these glyphs one to a cell, rows at the line height, and
they must join across every cell edge. A cell is the figures' advance wide
(`fig_adv`, the monospaced pitch) and the line's full height, from the
hhea/typo descender to the ascender (-250 to 950, `font.Metrics`), so rows
touch. The proportional families use the same cell for the cell glyphs
(box drawing, blocks, shades, Braille, Powerline separators, corner
triangles), as terminal fonts' proportional siblings do: a box drawn in
Arris lines up as in Arris Mono. Shapes and dingbats are spaced as
punctuation in the proportional cuts and centred in the cell in Mono.

**Flush edges.** The corner rule breaks every right-angled corner, which
would notch a line where it leaves its cell. Glyphs now carry *butt
lines* (`Glyph.butt`, passed to `geom.ink`): a corner with an edge lying on
one of them is left square. Cell glyphs set their cell's four edges as butt
lines and clip to the cell, so lines and blocks are cut square exactly on
the edges and continue into the next cell, while every corner inside the
cell keeps the rule (a junction's outer corner is cut, its crotch filled).

**Upright in the italic.** A slanted vertical would leave the cell below
it a slant's width away, so cell glyphs (`Spec.cell`) are drawn upright in
the italics; their chamfers still become curves (the rounded corners ╭╮╯╰
are curved, not slanted). `font.place`/`_place` draw them without the
shear; `tools/build_vf.py` passes them unsheared to the italic masters.

## Box drawing

* **Weights.** A light line is the weight's own stroke: vertical `sv`,
  horizontal `sh`, never under the stroke floor. Heavy is twice that. A
  double line is two light lines with three quarters of a light line's
  white between them (at least a module), so at Black the cell keeps white
  outside a double.
* **Junctions** are parsed from the Unicode names (`parse_arms`): each arm
  runs from its edge to the centre and on past it by half the widest arm
  across it, so arms of any weights meet in a clean corner, tee or cross,
  and the corner rule cuts and fills the junction. Mixed heavy and light
  arms step with a cut corner. Doubles meeting doubles close the square
  between their four lines on each side no arm leaves from; a double met by
  a single runs through or stops at the single's far side, and the single
  stops at the nearer double line at a tee and the farther one at a corner.
* **Dashes**: n dashes to a cell, each centred in its nth, so gaps stay even
  across cells; the gap is a quarter of a dash's share, never under three
  fifths of a stem.
* **Rounded corners** ╭╮╯╰ are a bowl's chamfer (leg a quarter of the cell
  width on the centreline); the italic curves them.
* **Diagonals** ╱╲╳ run corner to corner (the slope is the cell's, near
  the 2:1). They are cut flat at the cell's top and bottom but run on
  sideways through the corners by half their width, so a diagonal continues
  into the cells diagonally next to it without a waist (a line clipped to
  the cell would pinch to nothing at every corner).

## Blocks and shades

Blocks fill the cell exactly (eighths of the height or width, halves,
quadrants), every edge on a cell edge square. A quadrant's one exposed
corner, at the cell's centre, is cut and an inside step filled: the watch's
pixel rule, applied to half-cell pixels.

Shades are tones, not weights: drawn the same at every weight with
Regular's edge break, on one lattice of chamfered squares (four places
across, eight down, every other place inked). The cell's edges pass
through squares' centres, so a square cut by an edge is completed by the
next cell. ░ covers exactly a quarter (squares sized for their cut
corners), ▒ is the checkerboard (46%, its squares meeting only at their cut
corners), ▓ is ░'s negative (75%: its squares are holes, their corners
filled as a counter's).

## Braille

Dots are `p.dot()` squares on a 2×4 grid that spaces them evenly across
cells and rows alike: columns at a quarter and three quarters of the cell
width, rows at the odd eighths of the line height, so a field of Braille
graphics is a uniform dot matrix. U+2800 is an empty cell
(`variable.align` passes empty glyphs through).

## Powerline

The solid arrows fill the cell's full height and narrow to a point on the
far edge; the thin ones run from the cell's corners, their outer edges
meeting in a point on the far edge. They join blocks and coloured cells
seamlessly. The branch (a stem, a 45-degree branch, square nodes), the
line-number LN (small L over small N) and the padlock (chamfered shackle,
solid body, keyhole cut) are icons in the text's height.

## Geometric shapes

A circle in Arris is an octagon: regular, cut 0.29 of its width deep (the
0's corners are 0.28), curved by the italic. Triangles take the 7's 2:1
slope (as wide as tall), diamonds 45 degrees, the lozenge 2:1, so every
edge runs in the figures' directions. Shapes sit on the math axis in four
sizes: large (0.62 of the cap height, growing 1.5 units per unit of stem
past Regular, so the white inside grows with the stroke), medium 0.8,
medium small 0.64, small 0.48; ◯ ⬛ ⬜ ⬤ are the cap height (in Mono, never
wider than the figures).

White shapes are outlines whose outer edge is the black shape's: each side
set in by half its thickness by direction (`shapes.outline`). Their pen is
the weight's stroke, but light enough that the counter keeps half the
shape's inradius (small and pointed shapes draw lighter, as small figures
do); shapes with parts inside (▣ ◈ ◉ ◎ the hatched squares) keep three
fifths. Hatching is strokes as wide as the white between them, clipped to
the counter, with the hatch lines' own edge break; diagonal hatching runs
its outer lines through the counter's corners so no sliver of white is
left. Black shapes are solids; their octagonal corners are recorded as
chamfers so the italic curves them like the white ones.

## Dingbats

Built from the same vocabulary: the check mark is the radical's 45-degree
tick and 2:1 rise; crosses and Xs are strokes; the four-pointed stars
keep the 2:1 (inner corners a third of the way out); the six-pointed star
is two 2:1 triangles; the rectilinear eight-pointed star is a square and
its 45-degree turn; the pinwheel's blades lie on radii and on 45 degrees;
the heavy asterisk spreads six spokes on the vertical and the shallow 2:1s,
53 to 63 degrees apart; the lightning bolt is two 2:1 bands joined by the
2's notch; the gear sets a tooth on each of an octagon's eight sides; the
heart's lobes are octagon corners, its point 45 degrees; flags have a
45-degree swallowtail; the scissors are two octagonal finger rings a
stroke apart (in a pen that keeps their holes) and two blades on the 2:1
laid down, crossing at the pivot. Three stars truly need their own angles and use
them: ★ ☆ (the pentagram), ✴ (eight sharp points) and ✹ (twelve).

**Heavy forms** draw 1.6 times the weight's stroke, but never heavier than
a share of their own size (a quarter, a quarter more for heavy forms), so
at Black their parts stay apart and the heavy forms stay heavier than the
light ones. The ornament marks ❓❗ are Arris's own ? and ! drawn heavy
(up to a fifth of the cap height); ❔❕ are their outlines (walls a
fifth of the stroke, at least the floor). At Black the black ornaments are
the weight's own marks.

## Checking

* `tools/terminal_gates.py draw | stroke | white | counters | tiling | vf`
  runs the brief's gates on these glyphs alone; `tools/terminal_gates_align.py
  [italic]` is the variable font's alignment step for them (seconds, not
  minutes).
* `tools/cell_proof.py` sets text as a terminal does: rows at the font's
  line height, glyphs at their advances, all ink of one colour filled as one
  path (so a seam shows only where ink has a gap), from a built font or the
  engine, with terminal colours for Powerline prompts.
* `tools/terminal_proofs.py` makes the sheets `proofs/terminal-*.png`.
