# Arrows, mathematical operators, technical symbols

334 glyphs in three modules: `glyphs/arrows.py` (94 arrows in U+2190-21FF
and the eight long arrows U+27F5-27FC), `glyphs/operators.py` (161
operators in U+2200-22FF) and `glyphs/technical.py` (71 symbols in
U+2300-23FF). 324 code points are new; the ten arrows Arris already had
(← ↑ → ↓ ↖ ↗ ↘ ↙ ↔ ↕) are redrawn by the new builder under their old names,
so every arrow follows the same rules. − √ ∞ ∆ (an alias of Δ) are kept as
they were. Not drawn: ⎌ (UNDO SYMBOL), whose reference form I could not
pin down.

Proofs: `proofs/arrows-math-arrows.png` (the arrow chart),
`-equations.png`, `-sets-logic.png`, `-media-watch.png`,
`-watch-weights.png`, `-grid.png` (every glyph at Thin, Regular, Black,
Black Italic and Mono).

## One arrow builder

An arrow is drawn in a frame of its own, pointing along +u, then turned to
one of eight directions and centred on the math axis. It is made of three
kinds of part:

* shafts: single, double and triple (stacked as the equal sign's bars),
  dashed (three dashes at every weight, so it varies), wave (one period of
  the tilde's step), squiggle (two 45-degree teeth);
* heads: barbs (a chevron whose two 45-degree strokes meet in a point, the
  shafts ending in its crotch, as < and > are drawn), double barbs, a half
  barb (harpoons), an open triangle, a bar stop;
* tails: a flat end, a bar (maps-to), a feather, a second head, a hook, a
  loop, a double stroke across the shaft, a base.

Arrows that turn (↰ ↱ ↲ ↳ ↴ ↵ ⏎), round arrows (↶ ↷ ↺ ↻), the zigzag ↯,
white arrows (⇦ ⇧ ⇨ ⇩ ⇪) and paired arrows (⇄ ⇅ ⇆ ⇇ ⇈ ⇉ ⇊ ⇋ ⇌ ⇵ ⇶) use
the same heads and measures.

The rules every arrow keeps (they extend DESIGN.md "Symbols keep their
parts apart"):

* **The head.** One chevron whose point the corner rule keeps sharp, its
  barbs cut square to themselves: the Mono ligatures' head (`->`), at 0.35
  of the cap height where theirs is 0.44 (Fira Code's ratio between its
  `→` and its `->`). A barb reaches past the outermost shaft it guards far
  enough to leave half a stem of white between its end and that shaft, if
  that is longer. A head at each end is at most a quarter of the arrow, so
  a shaft shows between them (`↕`, the monospaced `↔`).
* **Free shaft.** Two and a half stems of shaft beyond a head (a stem and a
  half between two heads); the arrow lengthens to keep it, and a negated
  arrow lengthens again so its stroke stays clear of the barbs. In the
  monospaced cell the shaft beyond a single head shortens; the shaft
  between two heads does not.
* **Stacked arrows lighten.** Parts that stack (double and triple shafts,
  patterned shafts, open heads, paired arrows, strokes across a shaft)
  are a tight stack: their strokes ease from the weight's own at SemiBold
  to 0.75 of it at Black (`arrows.stack_k`), so the white between them can
  stay as wide as the equal sign's without the arrow outgrowing the line.
  Circled operators, ∄, ⊻ ⊼ ⊽, ⌘, keys and clocks use the same factor.
* **Paired arrows** stand two barbs apart: a head's barb clears the other
  arrow's shaft by the white rule, and side by side the inner barbs of two
  heads meet in a zigzag whose points are the tips.
* **Monospaced cell.** An arrow fills the figures' body. A head too wide
  for the cell shortens down to the white rule, then the strokes lighten a
  twentieth at a time down to 0.6, then the white under the barbs may
  narrow to 0.3 stems; free shafts shorten to 0.4 of theirs.

## Operators

* The **operator box**: the plus sign's width, as tall as it is wide, on
  the axis. Set signs, tacks and turnstiles fill it; set signs grow with
  the stroke (`growing_width(8, 1, 1.2)`) so their bays stay open; the
  element signs stack three bars in the box and thin them as tight stacks
  do.
* **Stacks** (≡ ≣ ≅ ≈ ≦ ≲ ⊆ ⊴ ≗ ≜ ⊻ ...): components measured from their
  ink and stacked with the equal sign's white, centred on the axis. A stack
  taller than the cap height and two modules thins its horizontals,
  continuously, down to 0.7 of the weight's. A chevron in a stack takes the
  size that makes the stack as tall as ≤.
* **The tilde** is a step on the axis: half way up at 45 degrees, along,
  down, along, half way up again (the five moves `asciitilde`'s docstring
  describes; the existing ~ draws four, see below). Its rise is a quarter
  of its width, or a bar and a third of a stem; its flats never shorter
  than the turns at their ends take from their inner edges. Tilde signs
  grow with the stroke (`growing_width(8, 1, 1.5)`).
* **Negations** are the not-equal sign's 2:1 stroke, long enough to cross
  what they negate; on ∄, ∉, ⊭ and the negated arrows they are placed so
  the pockets they close off stay open at every weight (the variable font
  needs the same contours everywhere).
* **Square and round**: ⊂ ∪ ∩ ⊎ turn their corners as bowls; ⊏ ⊐ ⊓ ⊔ keep
  plain corners with the corner rule's edge break.
* **Circled and squared operators** grow with the stroke
  (`growing_width(8, 1, 2.6)`); their inner parts keep half a stem of white
  from the ring's upright sides and its chamfers.
* **Big operators** (∑ ∏ ∐ ⋀ ⋁ ⋂ ⋃) span the brackets' height; ∫ ∬ ∭ ∮
  run from the descender to the ascender, the f's turn at the top and the
  j's at the foot, each ending in the 2's beak. ∑ joins its bars with a
  chevron at the 7's 2:1.
* ∀ is A turned, ∃ E reversed, ∇ Δ turned; ∂ is a bowl whose right side
  runs on up and turns over it into the 2's beak; ∅ is a regular octagon
  (where O is a tall bowl) with a 45-degree stroke through its corners.

## Technical symbols

* **Keys** (⌘ ⌥ ⌃ ⎋ ⌫ ⌦ ⏏ ⌨, with ⇧ ⇪ among the arrows) share the cap
  height and the arrows' heads.
* **Bracket pieces** (⎛-⎮, ⌠ ⌡) run from the line's descent to its ascent
  (font.Metrics) and an edge break past, so they join line on line and the
  corner rule's cuts fall in the overlap.
* **Media controls** (⏩-⏺, ⏏) are solid shapes of one height on the axis:
  triangles whose sides run at 2:1 (as wide as they are tall, near an
  equilateral's proportions), a square, an octagon, bars. They are drawn
  as polygons, marked `solid` (as the pilcrow's bowl is) and take the
  corner rule. In a narrow cell they scale down together.
* **The watch's pictographs** (⌚ ⏰ ⏱ ⏲ ⌛ ⏳) are drawn in the octagonal
  bowl: a regular octagon's face, hands at twelve and three (lighter than
  the face, as a watch's are), the watch a chamfered case on solid straps
  with a crown, the alarm clock with bells and feet at its chamfers, the
  stopwatch with a crown and a button, the timer with a mark and a hand at
  half past ten; the hourglass's glass runs at 2:1 into an upright neck,
  and ⏳ keeps sand in both bulbs, half a stem inside the glass. Faces
  grow with the stroke so the white about their hands stays open.

## Notes for integration

* `arrows.py` re-registers ← ↑ → ↓ ↖ ↗ ↘ ↙ ↔ ↕ (same names, code points
  and order in the registry); `symbols._arrow`, `arrowboth` and `arrowupdn`
  are now unused and could be deleted. `symbols.arrow_head` is not used
  by the new builder (its rule is `arrows.reach`).
* `asciitilde` (punct.py) draws rise, along, fall, along; its docstring
  says "up at 45 degrees, along, down, along, up". The new tilde operators
  draw the five moves. The lead may want ~ to match ∼.
* Known: in the monospaced cell ∬ and ∭ overflow (three stems and two
  hooks do not fit a figure's cell); at Black a few others overflow by up
  to a fifth of a stem (⇎ ↮ ⎨ ⎬). The radical (√, existing) also
  overflows the cell.
