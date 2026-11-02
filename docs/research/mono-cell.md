# Mono on one cell, and the extra bits that stop gaining weight

A note, 2026-11-02 (Eastern): the plan, the evidence for it, and what the
owner decided. Since done on `mono-grid`: the held strokes (section 3, the
letters' bar and slash helpers) and Mono's one cell (section 2, B). And the
owner's call (2026-11-02): Mono shipped only the two weights the site shows,
Regular and Bold with their italics; then, the same day, Fira Code's six,
Light to Bold with Retina (450), each with its italic
(`instances.MONO_WEIGHTS`); the build, the release workflow, the npm package
and the proofs follow. The engine's hold past Bold (`draw.MONO_HOLD`) stays
for a Mono drawn heavier, which no font ships.

## 1. The problem: Mono's cell follows the weight

Arris Mono takes its cell from the tabular figures (`fig_adv`), and the
figures widen with the weight so heavy strokes do not eat their counters
(`instances._params`). Mono inherited that, so its cell is a different width
at every weight. The italic matches its upright, weight for weight:

| Thin | ExtraLight | Light | Regular | Medium | SemiBold | Bold | ExtraBold | Black |
|---|---|---|---|---|---|---|---|---|
| 528 | 543 | 560 | 578 | 589 | 600 | 630 | 657 | 682 |

A Bold word in a Regular line pushes the rest of the line right by 0.05 em a
character (1.09 cells over a 40-character line in the preview); a terminal
takes the cell from the Regular and squeezes or spills the Bold; the site
fakes Mono Bold by double-striking the Regular for this reason. Coding fonts
keep one width at every weight. `.notdef` is also off the grid (560 in every
Mono font).

## 2. The fix: one cell, 600, at every weight

600 is the 10-module pitch the README already promises. Two ways to fill it
were previewed (scratch scripts that patch `Params.with_` when a set turns
monospaced, nothing in the engine changed):

* **A**: cell 600, body 540 at every weight (a 60-unit margin). The Black m
  chokes into a blob; Bold is crowded.
* **B**: cell 600, body as the proportional figures' but between 540 and 570,
  so heavy weights keep a 30-unit margin. Regular gains room (518 → 540),
  Bold keeps its body (570), Black gives up 52 (622 → 570). **The direction
  to take.**

Both put a Regular line with Bold words in it on the grid (drift 0).

### What B costs: every Mono glyph against today's, at 400, 700 and 900

Each glyph's closed counters and open gaps (the widest circle that fits in
each piece of white inside its box), today's Mono against B's. 77 glyphs are
flagged where a counter is lost, or a counter or gap falls under 0.7 (0.6) of
today's and under 0.3 (0.2) of the stem:

* **Regular (5)**: Ҟ and ₥ lose a pinhole that today's drawing has (the white
  opens into a gap: better); ‰, ↂ and ℞ to look at.
* **Bold (3)**: Ø Ǿ (the slash's gaps 98 → 52), ⌬.
* **Black (72)**:
  * the 20 double-line box-drawing pieces (╔ ╬ …): their two lines closer
    (101 → 59), as they are drawn to fill the cell: expected;
  * letters with something added to them: Đ Ð (131 → 91), Ø Ǿ, ₩ ₥, Ǆ Ǳ
    (a 4-unit pinhole), Ҩ ҩ, Ԙ, ℞, ⌀ ⊚ ⊗ ⋈;
  * wide forms in a narrower body: Æ Ǽ Ǣ Œ æ ǽ ǣ œ (counters 49 → 22),
    Ф ф, Ы Ӹ, Ю, N Ń Ň Ñ Ņ Ǹ Ṅ И Ѝ Й Ӣ Ӥ ℕ (diagonal gaps 120 → 64), ℂ ℅;
  * the double-struck ⅅ ⅆ ⅇ ℚ ℙ ℝ ℕ, ↭ ⟺ ⇔.
* m, w, M and ш stay open but tighter at Black (the m's gaps 57 → 45).

So B holds at Regular and Bold; at Black about 50 glyphs need a rule.

## 3. The rule for the extra bits (the owner's, 2026-11-02)

**Do not change any letterform.** The bits added to a letter (a crossbar
through a stem, the bar of Đ Ħ ŧ ₦ ₩, a slash through Ø, a hook, a tail, a
curl, a caron built into a letter, the extra line of a double-struck capital)
**stop gaining weight** at the weight where they would start to close the
white around them. From there to Black they keep that weight, and as the
letter's own strokes grow they are **re-placed** in the white the heavier
letter leaves, so they stay visible at every weight.

* Hold, do not thin: an extra bit is never lighter than it was at the weight
  it stopped at (the owner turned down thinning crossbars in the 1.010 work:
  "don't thin crossbars, make them longer").
* The letter itself goes on getting heavier as it does now: only the added
  strokes stop.
* It applies to every letter where an extra bit crowds, in Mono and in the
  proportional cuts alike, upright and italic.

### How the engine can do it

The pieces exist:

* `draw.Opening(hold=True)` with `_engaged` already finds, once per cut, the
  weight where a glyph's white first falls short of its share of the stem,
  and holds from there (the italic k's loop, its only user today).
* The crossbar rule already places a bar across a stem so it keeps a module
  of white on both sides (TODO #32), and `cyrillic_ext.cross_bar`,
  `extra_latin` and `currency` draw most bars through shared helpers.

As built (`draw.EXTRA_HOLD`, `Glyph.held`): one weight for every glyph,
600, where the stem is the watch's own two modules. An added stroke takes
the glyph's own thickness up to it and that weight's from there to Black, in
the same cut (grade, watch, Mono, slant); a slash's reach stops growing with
it. A per-glyph weight (where its white first falls short, as `_engaged`
finds it) was the alternative: one weight keeps every bar in a line the same
colour, and is simpler to check. The helpers that use it: `extra_latin._bar`,
`_slashbar`, `_oslash`, the ŧ's bar, `cyrillic_ext.cross_bar` and
`_stem_bar`, ℏ. The currency signs' pairs of bars keep their own rule
(`currency.pair_t`, `BARS_OR_ONE`); hooks and tails are not marked yet.

The wide forms (Æ Œ æ œ, Ф ф, N И) are not extra bits: their strokes are the
letter. They need the body B gives and, where that is not enough, the
existing squint rules; to be decided glyph by glyph after the rule above.

### Checks, before anything is shown

* The cell scan (closed counters and open gaps, every Mono glyph, today's
  against the new, 400 / 700 / 900): no counter lost, no gap under a fifth
  of the stem that today's drawing keeps.
* `skeleton` (every feature survives along each axis, losses monotonic) and
  `topology` (no crossings, slivers or point clusters) on the glyphs touched,
  upright and italic, at every weight.
* `tools/mono_scan.py` (Mono against its proportional self) after the change.

## 4. Ligatures, against Fira Code

Fira Code 6.2 has 86 fixed ligatures, plus 70 pieces it chains into arrows
and bars of any length. Arris Mono has 49: 30 in common, and 19 arrows that
Fira builds from its pieces. Of Fira's 56 that Arris lacks:

* about 9 are joins or new signs under Arris's rule (a character stays as it
  is, where it stands; a join only runs its own strokes on): `|||>` `<|||`
  `~~` `~-` `-~` `<~~` `<~>` `/\` `\/`. Sketched; `/\` `\/` come out at the
  slash's full height (Fira's are small ∧ ∨);
* `[|` `|]` `{|` `|}` joined close into boxes and stop reading as brackets:
  not joined;
* most of the rest (`::` `..` `//` `&&` `||` `**` `<<` `>>` `?.` `??` `<*>` …)
  only draw the characters closer together in Fira. DESIGN.md §8 leaves such
  sequences as their characters; adding them would change that rule;
* `www` is Fira's joke.

## 5. Open

1. Done: B (`params.MONO_CELL`, `MONO_BODY`), and the rule in section 3.
2. Ligatures: set aside by the owner for now.
