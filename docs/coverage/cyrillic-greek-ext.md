# Cyrillic+ and Greek+

The Cyrillic of Central Asia, the Caucasus, the Volga and Siberia, the
Bulgarian and Serbian/Macedonian local forms, and the Greek symbols and
archaic letters.

Modules: `glyphs/cyrillic_ext.py` (letters, their italics, their accented
forms), `glyphs/cyrillic_locl.py` (`locl` alternates and the feature),
`glyphs/greek_ext.py`.

## What was added

**Cyrillic capitals and small letters** (pairs unless noted):

| | |
|---|---|
| Kazakh, Kyrgyz, Uzbek, Tajik, Tatar, Bashkir, Mongolian, Kalmyk | Ғ ғ Қ қ Ң ң Ө ө Ұ ұ Ү ү Ә ә Ҙ ҙ Ҫ ҫ Ҡ ҡ Җ җ Ҳ ҳ Ҷ ҷ Ӣ ӣ Ӯ ӯ (Һ һ and Ў ў were there) |
| Chuvash, Mari, Udmurt, Altai, Khanty... (composed) | Ӑ ӑ Ӓ ӓ Ӗ ӗ Ӛ ӛ Ӝ ӝ Ӟ ӟ Ӥ ӥ Ӧ ӧ Ӫ ӫ Ӭ ӭ Ӱ ӱ Ӳ ӳ Ӵ ӵ Ӹ ӹ Ӂ ӂ |
| Abkhaz | Ҭ ҭ Ҟ ҟ Ҧ ҧ Ԥ ԥ Ҵ ҵ Ӡ ӡ Ҽ ҽ Ҿ ҿ Ҩ ҩ Ӷ ӷ |
| Yakut, Khakas, Altai, Mari | Ҕ ҕ Ҥ ҥ Ӌ ӌ |
| Chechen, Avar, Ingush, Lezgian... | Ӏ ӏ (palochka: the I) |
| Siberian and Sami | Ӄ ӄ Ӆ ӆ Ӈ ӈ Ӊ ӊ Ӎ ӎ Ҋ ҋ Ҏ ҏ Ԓ ԓ Ԯ ԯ |
| Others | Ҝ ҝ Ҹ ҹ Ҁ ҁ Ӻ ӻ Ӽ ӽ Ӿ ӿ Ԙ ԙ Ԑ ԑ Ӕ ӕ Ԛ ԛ Ԝ ԝ |
| Komi | Ԁ ԁ Ԃ ԃ Ԉ ԉ Ԋ ԋ Ԍ ԍ Ԏ ԏ (not Ԅ Ԇ) |

**Local forms** (`locl`, script `cyrl`): Bulgarian (BGR) в д ж и й к л п т
ц ш щ; Serbian and Macedonian (SRB, MKD) italic б г п т.

**Greek**: ϐ ϑ ϒ ϓ ϔ ϕ ϖ ϰ ϱ ϲ ϳ ϴ ϵ ϶, Ϙ ϙ Ϛ ϛ Ϝ ϝ Ϟ ϟ Ϡ ϡ, the
lunate sigmas Ϲ Ͻ Ͼ Ͽ ͻ ͼ ͽ, Ϳ (yot), Ϸ ϸ (sho), the spacing tonos ΄ and
the numeral signs ʹ ͵ (and U+02B9, which NFC makes of ʹ). The monotonic set
was already complete (all letters, tonos and dialytika, final sigma); only
the spacing tonos was missing.

171 new glyphs (129 Cyrillic letters, 34 of them composed from marks; 16
locl alternates; 26 Greek) and 23 code points mapped to existing glyphs:
178 new code points in all.

## Parts, drawn once

Every added part is a function used by every letter that carries it:

* **Descender** (`descender`): Ц's tail. The foot of the stem it hangs
  from runs on along the baseline to a short stem a module of white
  beyond it, which drops 0.8 of the descender. Қ Ң Ҷ Ҭ Җ Ҳ Ҵ Ԥ Ԯ, and,
  turned to the left of the foot, Ӷ Ӌ.
* **Tail** (`descender(turn=True)`): the same drop turning left at 45
  degrees at its foot, like the comma. "With tail" (Ӆ Ӎ Ӊ Ҋ) is told from
  "with descender" by it.
* **Hook** (`hook`): a stem running on below the baseline and turning back
  left on a bowl corner, as Ђ and Ŋ do (Ӈ Ԓ Ӽ); from mid-stem as Ђ's
  bowl (Ҕ Ҧ Ӄ), and under the foot (Ӻ). On a letter drawn on the
  x-height the hook goes as deep as ŋ's (`hook_y`).
* **Drop** (`drop`): a stem from the middle of a bowl's foot (Ҙ Ҫ Ҿ).
* **Crossing bars**: Đ's and Ħ's (Ғ Ұ Ҟ Ӿ), and short stems through Ҝ's
  arm and Ҹ's bar.
* **Komi hook** (`komi_hook`): a stem's foot running on into a small u.
* **Tick** (Ҏ ҏ): a 45-degree stroke through a bowl's lower corner. It
  shortens at heavy weights so the counter stays open (an `Opening`, as
  the Q's tail).

## Rules introduced

* **Added parts keep their white by growing with the stroke.** A hook's
  side stands a stem and two modules from the stem it leaves
  (`hook_reach`), so the hook's counter grows with the weight; Ҡ's lead-in
  bar is two modules or three quarters of a stem, whichever is more
  (`lead`); a bar across a stem reaches past it as far (`bar_reach`: Ұ ұ),
  and Ӿ's bar runs nearly the body's width, past the diagonals; Ҝ's stem
  stands two modules of white clear of K's stem and half a stem clear of
  the leg. In the monospaced cell a hook takes no
  more than leaves the letter two stems and a module and a half.
* **Lowercase follows the Russian lowercase**: a small capital where the
  Russian letter is one (қ ң ҷ ...), the Latin letter's own drawing where
  it is Latin (ө the o barred, its bars thinned as the e's; ә the e
  turned; ҳ ӽ ӿ on the x; ҫ ҁ on the c; ҏ on the p).
* **Cursive italics follow the Russian italic**: ҋ is the italic й (a u)
  with the cursive ц's tick, ҭ the italic т (an m) with it, ԥ and ҧ the
  italic п (an n) with the tick or the hook. Composed letters (ӣ ӯ ӥ...)
  take their bases' italics.
* **Mouths** (Ә Ҽ Ҿ Ҩ, where a beak faces a bar or a loop) keep three
  quarters of their share of the stem, the beak shortening as the
  figures' do (`MOUTH`); Ҩ, whose height stacks a beak, a mouth and a
  loop, keeps 0.4 and then lowers its loop as far as the loop's own
  counter allows.
* **Crowded cells degrade cleanly**: where a loop, a hook's u or a beak's
  turn has no room (the monospaced cell at Black and grade +100), the
  part is drawn without the turn that would cross itself.

## The feature hook

`draw.py` has two lists, `LANGSYS` and `FEATURE_CODE`, that glyph modules
append to; `features.fea()` writes the language systems after `DFLT` and
`latn` and the feature code before every other feature, so `locl` runs
first. `cyrillic_locl` adds `cyrl dflt/BGR/SRB/MKD` and one `locl`
feature. `tools/hbspec.py` takes `lang=xx` to proof it.

## Known limits

* Ҝ at Black: its short stem crosses the arm where K's arms meet the stem
  closely, and reads as a step on the arm.
* Ҵ ԏ have no cursive italic (their т stays upright-shaped).
* Ҩ ҩ are an Arris reading of the Abkhaz letter: a bowl open at the top
  with a loop in its lower right. In ҩ at Black with a heavy grade or the
  watch balance there is no room for the beak over the loop, and the bowl
  ends flat on its top bar.
* ϰ draws its curls only where they draw as a simple outline
  (`greek_ext._draws`); at Black with grade +100, and in the heavy
  monospaced cells, it falls back to plain flats.
* Serbian and Macedonian д get no alternate: Arris's Russian italic д is
  already the g that they write. Their upright б stays the Russian б.
* Ԅ ԅ Ԇ ԇ (Komi) are not drawn.
* At heavy weights the sampi's lower stroke meets the baseline (Ϡ) or
  runs into the descender (ϡ), and is cut there; the variable font
  follows that cut less closely than elsewhere (about 30 units of mean
  outline difference between masters).
* The kerning (measured for every pair of letters) roughly doubles with
  these letters: about 43,000 pairs at Regular against 20,000 before.
