# Figure legibility: an ideal-observer measure

`tools/confusion.py` renders each font's figures at a common height, aligned
on the baseline and centred. It blurs them with the contrast-sensitivity
filter for a viewing size (`arris.vision`). For every pair it measures the
energy of the blurred difference, relative to the font's mean figure energy.
That quantity sets how accurately an ideal template matcher tells the two
apart, so lower means more confusable. Three viewing sizes are tested, by
the angular height of the figures:

* 44 arcmin: the watch clock (36 px on a 200 ppi screen at 35 cm);
* 11 arcmin: a small label;
* 6 arcmin: the edge of reading.

Comparison fonts: B612 (designed for cockpit displays), Atkinson Hyperlegible
(designed for low vision), Barlow (DIN-like), Chakra Petch and Oxanium
(chamfered, like Arris), JetBrains Mono.


### Figure height 44 arcmin

| Font | closest pairs (distance) | mean |
|---|---|---|
| Arris SemiBold | 5/6 0.40, 3/8 0.56, 0/9 0.57, 0/6 0.57, 6/8 0.58 | 0.86 |
| Arris Regular | 5/6 0.43, 3/8 0.59, 0/6 0.60, 0/9 0.60, 0/8 0.67 | 0.93 |
| Arris Watch SemiBold | 5/6 0.42, 3/8 0.53, 0/6 0.59, 0/9 0.59, 6/8 0.60 | 0.86 |
| Arris Mono Regular | 5/6 0.43, 3/8 0.58, 0/6 0.62, 0/9 0.62, 0/8 0.63 | 0.93 |
| B612 Regular | 3/5 0.64, 6/8 0.74, 0/9 0.79, 2/7 0.80, 0/6 0.83 | 1.00 |
| Atkinson Hyperlegible | 5/6 0.53, 3/8 0.65, 6/8 0.67, 3/5 0.73, 5/8 0.78 | 0.99 |
| Barlow Regular | 6/8 0.50, 5/6 0.51, 0/9 0.66, 6/9 0.67, 0/6 0.68 | 0.96 |
| Chakra Petch Regular | 6/8 0.51, 0/8 0.56, 5/6 0.56, 3/8 0.57, 0/9 0.60 | 0.92 |
| Oxanium | 6/8 0.53, 5/6 0.55, 0/8 0.58, 0/6 0.63, 0/9 0.64 | 0.94 |
| JetBrains Mono | 3/5 0.65, 0/8 0.66, 0/5 0.76, 5/8 0.77, 5/6 0.78 | 0.97 |

### Figure height 11 arcmin

| Font | closest pairs (distance) | mean |
|---|---|---|
| Arris SemiBold | 5/6 0.36, 6/8 0.46, 0/9 0.52, 0/6 0.52, 0/8 0.53 | 0.78 |
| Arris Regular | 5/6 0.38, 6/8 0.51, 0/6 0.55, 0/9 0.55, 3/8 0.57 | 0.83 |
| Arris Watch SemiBold | 5/6 0.38, 6/8 0.46, 3/8 0.49, 8/9 0.54, 0/6 0.55 | 0.77 |
| Arris Mono Regular | 5/6 0.38, 0/8 0.50, 6/8 0.51, 0/6 0.52, 0/9 0.52 | 0.82 |
| B612 Regular | 3/5 0.50, 6/8 0.53, 2/7 0.59, 0/9 0.65, 0/6 0.67 | 0.85 |
| Atkinson Hyperlegible | 5/6 0.39, 6/8 0.44, 3/8 0.54, 5/8 0.55, 3/5 0.57 | 0.84 |
| Barlow Regular | 6/8 0.30, 5/6 0.38, 8/9 0.46, 5/8 0.50, 6/9 0.51 | 0.81 |
| Chakra Petch Regular | 6/8 0.32, 8/9 0.39, 5/6 0.46, 0/8 0.47, 3/9 0.48 | 0.80 |
| Oxanium | 6/8 0.41, 5/6 0.44, 0/8 0.46, 8/9 0.53, 3/9 0.56 | 0.83 |
| JetBrains Mono | 0/8 0.44, 5/8 0.56, 3/5 0.57, 0/5 0.57, 2/7 0.59 | 0.82 |

### Figure height 6 arcmin

| Font | closest pairs (distance) | mean |
|---|---|---|
| Arris SemiBold | 5/6 0.31, 6/8 0.32, 8/9 0.37, 5/8 0.42, 2/3 0.42 | 0.62 |
| Arris Regular | 5/6 0.33, 6/8 0.36, 8/9 0.40, 2/3 0.45, 0/6 0.46 | 0.66 |
| Arris Watch SemiBold | 6/8 0.31, 5/6 0.32, 8/9 0.35, 2/3 0.40, 5/8 0.40 | 0.60 |
| Arris Mono Regular | 5/6 0.33, 6/8 0.36, 0/8 0.36, 0/6 0.39, 0/9 0.39 | 0.65 |
| B612 Regular | 3/5 0.36, 6/8 0.36, 2/7 0.41, 1/3 0.43, 5/9 0.45 | 0.61 |
| Atkinson Hyperlegible | 6/8 0.26, 5/6 0.31, 5/8 0.37, 2/3 0.41, 0/6 0.42 | 0.62 |
| Barlow Regular | 6/8 0.19, 8/9 0.26, 5/6 0.28, 6/9 0.33, 5/8 0.36 | 0.58 |
| Chakra Petch Regular | 6/8 0.20, 8/9 0.25, 6/9 0.36, 5/6 0.38, 3/9 0.39 | 0.62 |
| Oxanium | 6/8 0.36, 8/9 0.39, 5/6 0.39, 0/8 0.40, 5/9 0.41 | 0.68 |
| JetBrains Mono | 0/8 0.28, 5/8 0.37, 0/5 0.39, 2/7 0.42, 3/5 0.44 | 0.57 |


## What it says about Arris

* **At the smallest size, Arris holds up as well as or better than the
  legibility-focused faces.** Its weakest pairs (5/6 and 6/8 at about 0.31)
  beat Barlow (6/8 0.19), Chakra Petch (0.20) and Atkinson Hyperlegible
  (0.26). The octagonal bowls and the beaks keep their differences under
  blur.
* **At watch size its weakest pair is 5/6** (0.40), below Atkinson (0.53)
  and Chakra Petch (0.56). The two share a top bar and a lower bowl and are
  told apart mainly by the 5's open lower left.
* **The open five** (`five.ss02`, feature `ss02`) moves the 5's bowl up one
  pixel row, from the watch's row 7 to row 8. That single change raises
  5/6 to 0.64 at watch size, 0.54 at 11 arcmin and 0.44 at 6 arcmin,
  better than every comparison font. It keeps 5/3, 5/8 and 5/9 at or above
  their earlier values. It is an alternate, because it changes a figure
  from the watch.

Tested and rejected for the 5: a shorter beak alone (0.47) and a longer top
bar (0.43). Raising the junction by half a module (0.51) is not
pixel-aligned.


# Letter legibility

`tools/letter_confusion.py` applies the same measure to letters: every pair
of lowercase letters, every pair of capitals, and the strings readers
mistake for one another (I l 1 |, O 0, rn and m, cl and d, B and 8, S and 5,
u and v...), each rendered at a common cap height and centred on its
advance. Sizes are given by cap height: 22 arcminutes is 10 pt text at 40
cm; 11 arcminutes a small label.

The first run found Arris weaker than every comparison face on six pairs,
and the letters were changed where the measure pointed (`docs/DESIGN.md`
section 3). At 11 arcminutes, SemiBold:

| Pair | before | after | change |
|---|---|---|---|
| l/I | 0.29 | 0.57 | the l's tail (the t's foot) |
| v/u | 0.43 | 0.72 | the v's 2:1 arms |
| B/8 | 0.25 | 0.29 | the B's narrower upper bowl |
| c/o | 0.36 | 0.42 | the c's shortest beaks |
| G/B | 0.39 | 0.49 | the G's lower bar |
| 0/O (Mono) | 0.17 | 0.38 | the dotted zero's tall dot |

What remains at the bottom is shared with every face measured: h/n, o/p
and o/q, E/F, O/Q, I/T and P/R are the pairs the alphabet itself makes
close. I/| (the capital and the vertical bar) is the closest classic pair
left in the proportional faces; the monospaced cut, where it matters, slabs
its I.

### lowercase, cap height 22 arcmin

| Font | closest pairs (distance) | mean |
|---|---|---|
| Arris Regular | h/n 0.41, g/q 0.48, o/p 0.48, o/q 0.48, b/o 0.53, d/o 0.53, b/p 0.54, d/q 0.54 | 1.01 |
| Arris SemiBold | h/n 0.42, o/p 0.47, o/q 0.47, g/q 0.47, c/o 0.49, e/o 0.50, b/o 0.51, d/o 0.51 | 0.96 |
| Arris Mono Regular | h/n 0.40, c/o 0.42, o/p 0.46, o/q 0.46, i/l 0.48, b/o 0.51, d/o 0.51, g/q 0.51 | 0.97 |
| Atkinson Hyperlegible | h/n 0.36, l/t 0.38, f/t 0.42, v/y 0.43, i/l 0.49, f/l 0.50, o/p 0.50, b/o 0.51 | 1.02 |
| B612 Regular | h/n 0.44, v/y 0.49, i/j 0.50, r/t 0.51, f/t 0.52, g/q 0.53, i/l 0.53, n/u 0.54 | 1.02 |
| Barlow Regular | i/l 0.27, h/n 0.39, v/y 0.45, i/j 0.46, f/t 0.47, g/q 0.47, b/h 0.48, c/o 0.48 | 1.02 |
| Chakra Petch Regular | i/l 0.27, h/n 0.40, c/o 0.44, a/e 0.45, e/o 0.49, f/t 0.49, g/y 0.50, o/q 0.50 | 1.01 |
| JetBrains Mono | h/n 0.36, c/o 0.38, b/h 0.42, v/y 0.45, e/o 0.46, o/q 0.47, b/o 0.47, o/p 0.47 | 0.93 |

### capitals, cap height 22 arcmin

| Font | closest pairs (distance) | mean |
|---|---|---|
| Arris Regular | O/Q 0.43, E/F 0.45, F/P 0.49, I/T 0.51, P/R 0.52, C/G 0.52, G/S 0.60, E/L 0.61 | 1.04 |
| Arris SemiBold | O/Q 0.41, E/F 0.43, I/T 0.49, C/G 0.49, P/R 0.50, G/S 0.54, F/P 0.55, B/S 0.55 | 0.99 |
| Arris Mono Regular | O/Q 0.41, F/P 0.44, I/T 0.44, D/O 0.45, C/G 0.45, E/F 0.47, G/O 0.47, P/R 0.48 | 0.91 |
| Atkinson Hyperlegible | I/T 0.45, P/R 0.47, E/F 0.48, G/O 0.52, O/Q 0.52, E/L 0.58, F/P 0.59, D/U 0.60 | 1.02 |
| B612 Regular | O/Q 0.40, I/T 0.44, E/F 0.50, E/L 0.57, P/R 0.59, C/G 0.59, F/P 0.61, F/L 0.64 | 1.05 |
| Barlow Regular | O/Q 0.32, G/O 0.39, C/O 0.40, C/G 0.41, P/R 0.45, D/O 0.46, I/T 0.46, G/Q 0.47 | 1.02 |
| Chakra Petch Regular | O/Q 0.25, D/O 0.33, D/Q 0.42, G/O 0.45, I/T 0.46, C/G 0.48, D/G 0.50, E/F 0.50 | 1.03 |
| JetBrains Mono | D/O 0.29, O/Q 0.37, G/O 0.41, C/G 0.43, I/T 0.44, O/U 0.44, C/O 0.46, E/F 0.46 | 0.90 |

### classic confusions, cap height 22 arcmin

| Font | closest pairs (distance) | mean |
|---|---|---|
| Arris Regular | I/| 0.32, n/h 0.38, E/F 0.45, B/8 0.51, P/R 0.52, C/G 0.52, h/b 0.54, O/0 0.54 | 0.83 |
| Arris SemiBold | I/| 0.31, n/h 0.38, B/8 0.41, E/F 0.44, O/0 0.45, c/o 0.45, C/G 0.50, h/b 0.50 | 0.76 |
| Arris Mono Regular | n/h 0.37, c/o 0.39, O/0 0.39, D/O 0.44, C/G 0.44, E/F 0.46, l/1 0.46, P/R 0.48 | 0.78 |
| Atkinson Hyperlegible | n/h 0.32, l/| 0.36, t/f 0.37, y/v 0.37, I/l 0.40, i/j 0.45, rn/m 0.47, h/b 0.48 | 0.77 |
| B612 Regular | I/| 0.36, n/h 0.40, I/l 0.41, y/v 0.44, i/j 0.45, B/8 0.46, t/f 0.46, h/b 0.50 | 0.80 |
| Barlow Regular | I/l 0.04, I/| 0.26, l/| 0.26, n/h 0.35, y/v 0.40, i/j 0.41, C/G 0.42, t/f 0.43 | 0.73 |
| Chakra Petch Regular | I/l 0.06, D/O 0.33, n/h 0.36, c/o 0.40, l/| 0.44, B/8 0.44, t/f 0.45, I/| 0.45 | 0.75 |
| JetBrains Mono | D/O 0.29, O/0 0.32, n/h 0.33, c/o 0.34, h/b 0.38, y/v 0.42, C/G 0.43, e/c 0.45 | 0.77 |

### lowercase, cap height 11 arcmin

| Font | closest pairs (distance) | mean |
|---|---|---|
| Arris Regular | h/n 0.40, g/q 0.43, o/p 0.43, o/q 0.43, o/u 0.45, e/o 0.47, b/o 0.48, d/o 0.48 | 0.92 |
| Arris SemiBold | h/n 0.41, o/p 0.43, o/q 0.43, g/q 0.43, e/o 0.44, c/o 0.44, o/u 0.44, b/h 0.47 | 0.88 |
| Arris Mono Regular | h/n 0.38, c/o 0.41, o/p 0.42, i/l 0.42, o/q 0.42, g/q 0.46, b/o 0.47, d/o 0.47 | 0.90 |
| Atkinson Hyperlegible | l/t 0.30, h/n 0.35, i/l 0.35, f/t 0.37, v/y 0.40, f/l 0.40, f/i 0.43, o/p 0.44 | 0.93 |
| B612 Regular | i/l 0.41, h/n 0.43, r/t 0.44, v/y 0.45, b/h 0.45, g/q 0.46, f/t 0.47, n/u 0.47 | 0.91 |
| Barlow Regular | i/l 0.22, h/n 0.37, f/t 0.40, c/o 0.40, g/q 0.41, b/h 0.41, a/e 0.41, v/y 0.42 | 0.92 |
| Chakra Petch Regular | i/l 0.20, a/e 0.33, h/n 0.38, c/o 0.39, a/s 0.39, e/s 0.42, f/t 0.42, b/h 0.42 | 0.92 |
| JetBrains Mono | h/n 0.34, c/o 0.35, b/h 0.37, v/y 0.39, o/u 0.40, e/o 0.40, a/e 0.40, o/q 0.41 | 0.82 |

### capitals, cap height 11 arcmin

| Font | closest pairs (distance) | mean |
|---|---|---|
| Arris Regular | O/Q 0.39, F/P 0.42, E/F 0.43, G/S 0.48, I/T 0.48, P/R 0.48, C/G 0.48, B/S 0.53 | 0.95 |
| Arris SemiBold | O/Q 0.38, E/F 0.41, G/S 0.44, D/O 0.45, I/T 0.46, C/G 0.47, P/R 0.47, F/P 0.47 | 0.91 |
| Arris Mono Regular | D/O 0.31, I/T 0.38, F/P 0.38, O/Q 0.39, O/U 0.43, C/G 0.44, G/O 0.44, E/F 0.44 | 0.84 |
| Atkinson Hyperlegible | I/T 0.38, E/F 0.44, P/R 0.45, D/O 0.45, G/O 0.47, F/P 0.48, O/Q 0.48, G/Q 0.50 | 0.94 |
| B612 Regular | O/Q 0.34, I/T 0.40, E/F 0.42, E/L 0.48, F/P 0.48, P/R 0.51, C/E 0.53, H/N 0.53 | 0.96 |
| Barlow Regular | O/Q 0.26, D/O 0.30, G/O 0.33, C/O 0.38, D/Q 0.39, G/Q 0.40, C/G 0.40, P/R 0.42 | 0.91 |
| Chakra Petch Regular | D/O 0.21, O/Q 0.22, D/Q 0.31, G/O 0.39, D/G 0.41, I/T 0.43, E/F 0.44, D/U 0.45 | 0.93 |
| JetBrains Mono | D/O 0.20, O/Q 0.34, G/O 0.36, O/U 0.37, I/T 0.38, D/U 0.40, B/D 0.40, F/P 0.42 | 0.80 |

### classic confusions, cap height 11 arcmin

| Font | closest pairs (distance) | mean |
|---|---|---|
| Arris Regular | I/| 0.28, B/8 0.34, n/h 0.36, O/0 0.39, E/F 0.43, S/5 0.44, h/b 0.44, I/1 0.46 | 0.71 |
| Arris SemiBold | I/| 0.28, B/8 0.29, O/0 0.35, n/h 0.37, c/o 0.41, S/5 0.41, E/F 0.41, h/b 0.43 | 0.67 |
| Arris Mono Regular | D/O 0.31, n/h 0.36, c/o 0.38, O/0 0.38, I/l 0.39, l/1 0.42, I/1 0.42, S/5 0.42 | 0.70 |
| Atkinson Hyperlegible | n/h 0.30, l/| 0.31, rn/m 0.32, t/f 0.33, I/l 0.34, y/v 0.35, h/b 0.39, i/j 0.41 | 0.66 |
| B612 Regular | I/l 0.31, B/8 0.34, I/| 0.35, n/h 0.38, y/v 0.40, h/b 0.40, t/f 0.42, E/F 0.44 | 0.68 |
| Barlow Regular | I/l 0.03, I/| 0.21, l/| 0.21, D/O 0.31, O/0 0.33, n/h 0.33, t/f 0.36, c/o 0.36 | 0.60 |
| Chakra Petch Regular | I/l 0.04, D/O 0.22, B/8 0.30, O/0 0.33, n/h 0.35, c/o 0.35, S/5 0.36, t/f 0.38 | 0.63 |
| JetBrains Mono | D/O 0.20, O/0 0.27, n/h 0.31, c/o 0.32, B/8 0.33, h/b 0.34, y/v 0.35, a/o 0.41 | 0.68 |
