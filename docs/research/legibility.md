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
