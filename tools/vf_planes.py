"""The places where glyphs' exact drawings jump, for the variable font
(build_vf.py, ARRIS_VF_PLANES): from structure censuses of the drawings
(one json line per glyph: its steps [wght, structure, moved mean, moved max,
rings, lightened, overrides] at a grade and watch balance), the steps that
move the outline far more than the glyph's usual step, as (wght, GRAD, WTCH)
just before and at the jump.

usage: vf_planes.py out.json census.jsonl:GRAD:WTCH [...]
"""
import json
import statistics
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
        med_mv = statistics.median(s[2] for s in steps[1:]) or 0.5
        med_mx = statistics.median(s[3] for s in steps[1:]) or 2.0
        jumps = []
        for prev, s in zip(steps, steps[1:]):
            w, mv, mx = s[0], s[2], s[3]
            if (mv > 2.5 * med_mv and mv > 2.0) or (mx > 3 * med_mx and mx > 20):
                jumps.append((max(mx, 10 * mv), prev[0], w))
        jumps.sort(reverse=True)
        for _, w0, w1 in jumps[:3]:          # the three biggest: a plane costs the glyph six masters
            planes.setdefault(r['n'], set()).update({(w0, g, t), (w1, g, t)})
json.dump({n: sorted(v) for n, v in planes.items()}, open(out, 'w'))
print(len(planes), 'glyphs,', sum(len(v) for v in planes.values()), 'places')
