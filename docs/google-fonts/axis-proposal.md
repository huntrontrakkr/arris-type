# Mechanical (MECH): an axis proposed to Google Fonts

For a pull request to [googlefonts/axisregistry](https://github.com/googlefonts/axisregistry):
`mechanical.textproto` and `mechanical.svg` go in `Lib/axisregistry/data/`.
The illustration is drawn from the variable font by
`tools/axis_illustration.py`.

Arris's own fonts carry this axis as WTCH (Watch). The Google Fonts build
leaves it out until the registry has it, then carries it as MECH.

## The note for the pull request

Arris (a chamfered geometric sans, OFL, variable on weight and grade) has
an axis that moves from its optically corrected drawing to the strict
construction it was built from, the pixel figures of a watch face. At
Regular, horizontals go from 79 to 90 units (the stem), diagonals from 81 to
64 units measured perpendicular to the stroke (as wide as a stem measured
horizontally), and overshoot and the raised optical centre fade out. At
Black, as in the illustration, the crossbar goes from 149 to 176 units and
the diagonal from 147 to 123.

No registered axis covers this. Contrast (CTRS) measures thick against thin
strokes, but this axis thickens horizontals while thinning diagonals, and
also removes overshoot and optical centring. Thin Stroke (YOPQ) is an
absolute, parametric thickness. Geometric Form (GEOM) simplifies shapes and
swaps forms.

Proposed: Mechanical, MECH, 0–100, default 0. The variable fonts are in
production: https://github.com/huntrontrakkr/arris-type
