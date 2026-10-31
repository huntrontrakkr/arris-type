"""The variable fonts: Arris[GRAD,WTCH,wght].ttf and the italic's, made
point-compatible by ``arris.variable.align`` and checked against exact
drawings at places between the masters.

Axes:
  wght  100-900  weight
  GRAD  -100-100 grade: strokes thinner or thicker, every width and space kept
  WTCH  0-100    the watch's own proportions (diagonals as wide across as a
                 stem, horizontals as heavy as verticals) instead of the
                 measured optics

    python -m arris.vf [italic]

('italic' builds Arris-Italic[GRAD,WTCH,wght].ttf: the upright masters are
aligned, then curved and sheared, ``arris.italic``.) The build runs in
stages, a module each: ``settings`` (what the environment asks for),
``space`` (the axes, the masters, the grid and the check's places),
``forms`` (a glyph with two drawings, one glyph each), ``glyph`` (one
glyph drawn at every master, aligned, measured and refined, ``measure``
and ``dense`` measuring), ``composites`` (a glyph that is others moved),
``kerning``, ``encode`` (a glyph's variations, pruned), ``assemble`` (the
master fonts and the variable font, within its size budget), ``check``
(the font against the drawings), and ``build`` running them in order.
``census`` takes the census of the drawings that ``tools/vf_planes.py``
reads the jump places from.
"""
