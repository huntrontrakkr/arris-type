"""The places where glyphs' exact drawings jump, for the variable font
(build_vf.py, ARRIS_VF_PLANES): from structure censuses of the drawings
(one json line per glyph: its steps [wght, structure, moved mean, moved max,
rings, lightened, overrides] at a grade and watch balance), the steps that
move the outline far more than the glyph's usual step, as (wght, GRAD, WTCH)
just before and at the jump.

usage: vf_planes.py out.json census.jsonl:GRAD:WTCH [...]
(build_vf.py reads tools/vf_planes.json, or vf_planes_italic.json for the italic, if it is there, or ARRIS_VF_PLANES)
"""
import json
import sys

out = sys.argv[1]
planes: dict = {}
for arg in sys.argv[2:]:
    path, g, t = arg.rsplit(':', 2)
    g, t = int(g), int(t)
    for line in open(path):
        r = json.loads(line)
        if 'error' in r or len(r.get('steps', [])) < 3:
            continue
        steps = r['steps']
        jumps = []
        for i, (prev, s) in enumerate(zip(steps, steps[1:])):
            w, mv, mx = s[0], s[2], s[3]
            # a jump: a step that moves the outline far more than the steps
            # either side of it (a steady growth, however fast, is not one)
            near = [q for q in (steps[i - 1] if i >= 1 else None, steps[i + 2] if i + 2 < len(steps) else None) if q]
            n_mv = max((q[2] for q in near), default=0.0); n_mx = max((q[3] for q in near), default=0.0)
            if not ((mv > 2.5 * n_mv and mv > 2.0) or (mx > 3 * n_mx and mx > 20)):
                continue
            # a jump that the drawing undoes within three steps (a rule that
            # fires at one weight and lets go at the next: ⁜'s lightening) is
            # no place for a master: the font's masters sit outside it, and
            # masters inside would carry the flicker into the font
            same = lambda a, b: a[1] == b[1] and abs(a[5] - b[5]) < 0.02 and a[6] == b[6]   # structure, lightening, free variables
            if any(same(steps[j], prev) for j in range(i + 2, min(i + 5, len(steps)))) or \
                    any(same(s, steps[j]) for j in range(max(0, i - 3), i)):     # (or is itself the undoing)
                continue
            jumps.append((max(mx, 10 * mv), prev[0], w))
        jumps.sort(reverse=True)
        for _, w0, w1 in jumps[:3]:          # the three biggest: a plane costs the glyph six masters
            planes.setdefault(r['n'], set()).update({(w0, g, t), (w1, g, t)})
json.dump({n: sorted(v) for n, v in planes.items()}, open(out, 'w'))
print(len(planes), 'glyphs,', sum(len(v) for v in planes.values()), 'places')
