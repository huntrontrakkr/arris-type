"""Mark positioning: anchors measured on the outlines, and the features
that use them.

A combining mark (``glyphs.latin_plus.COMBINING``) lands where
``marks.compose`` would draw it on the same base, so a letter followed by a
combining mark shows as the precomposed letter does. Every base glyph
(letters, figures, the dotted circle) carries four anchors, measured on its
placed outline:

* **top**: over its body's centre, a mark's gap above its highest ink (so
  a mark clears an ascender, a capital or an accent already there);
* **bottom**: under its body's centre on the baseline, or to the right,
  clear of a descender's hook (``marks.clear_below``, as the dot below of
  the composed letters);
* **ogonek**: at its right foot (its rightmost ink just above the
  baseline, less three quarters of a stem), as ``marks.ogonek``;
* **horn**: its top-right extreme along the diagonal
  (``latin_plus.horn_anchor``).

A mark carries the anchor it attaches by (where its drawing assumed its
base) and, for stacking (``mkmk``), one a stack gap beyond its own ink:
above it for marks above, below it for marks below.

Anchors are measured upright. In the italic the outline is unsheared to be
measured and each anchor sheared back, so a mark follows the slant exactly
as the composed letters' marks do.

Features (``fea``): ``ccmp`` drops the dot of i and j (and of the letters
that share their glyphs) before a mark above and decomposes į and ị so
their dots go too; it gives marks above their flatter ``.case`` forms after
a capital or a figure. ``mark`` and ``mkmk`` place them; GDEF classes the
glyphs, and each mkmk lookup sees only the marks of its own side.
"""
from __future__ import annotations

from shapely.geometry import LineString

from .draw import REGISTRY
from .geom import rings_to_shapely
from .params import Params

CLASSES = ('top', 'bottom', 'ogonek', 'horn')
BASE_KINDS = ('cap', 'lower', 'fig')
EXTRA_BASES = ('uni25CC',)


def _upright(name, rings, p: Params):
    """(x offset, body width, upright rings) of a glyph where it was placed:
    as ``font._place`` recorded them, or else from its placed rings (an
    italic outline unsheared, its curves flattened)."""
    from .font import BODIES
    if (name, p) in BODIES:
        return BODIES[name, p]
    if p.slant:
        from .italic import flatten
        yc = p.xh / 2
        pts = [[(x - (y - yc) * p.slant, y) for x, y in flatten(r)] for r in rings]
    else:
        pts = [[(q[0], q[1]) for q in r] for r in rings]
    xs = [x for r in pts for x, _ in r] or [0.0]
    return min(xs), max(xs) - min(xs), pts


def _shear(pt, p: Params):
    x, y = pt
    return (x + (y - p.xh / 2) * p.slant, y) if p.slant else (x, y)


def base_anchors(name, rings, p: Params) -> dict:
    """{class: (x, y)} for a base glyph's placed rings."""
    from .glyphs import latin_plus, marks
    dx, W, pts = _upright(name, rings, p)
    cx = dx + W / 2
    out = {}
    if not any(len(r) >= 3 for r in pts):
        for c in CLASSES:
            out[c] = (cx, 0.0)
        return out
    ink = rings_to_shapely(pts)
    top = max(y for r in pts for _, y in r)
    out['top'] = (cx, top + marks.gap(p))
    xb = marks.clear_below(ink, p, marks.BELOW['̣'], cx, 'lc', W)
    out['bottom'] = (xb, 0.0)
    y_foot = 0.3 * p.sh
    cut = ink.intersection(LineString([(-1e4, y_foot), (1e4, y_foot)]))
    xs = [c[0] for g in getattr(cut, 'geoms', [cut]) for c in getattr(g, 'coords', [])]
    out['ogonek'] = ((max(xs) - 0.75 * p.sv) if xs else cx, 0.0)
    out['horn'] = latin_plus.horn_anchor(ink)
    return {c: _shear(a, p) for c, a in out.items()}


def mark_anchors(name, rings, p: Params):
    """(class, attaching anchor, stacking anchor or None) for a combining mark."""
    from .glyphs import latin_plus, marks
    where, case, _ = latin_plus.MARKS[name]
    uc = case == 'uc'
    dx, W, pts = _upright(name, rings, p)
    cx = dx + W / 2
    ys = [y for r in pts for _, y in r] or [0.0]
    sg = marks.STACK_GAP * marks.gap(p)
    if where == 'top':
        attach = (cx, (p.cap if uc else p.xh) + marks.gap(p))
        stack = (cx, max(ys) + sg)
    elif where == 'bottom':
        attach = (cx, 0.0)
        stack = (cx, min(ys) - sg + marks.gap(p))
    elif where == 'horn':
        ax, ay = latin_plus.horn_origin(p, 'uc' if uc else 'lc')
        attach, stack = (cx + ax, ay), None
    else:
        attach, stack = (cx, 0.0), None
    return where, _shear(attach, p), (_shear(stack, p) if stack else None)


def _a(pt):
    return f'<anchor {round(pt[0])} {round(pt[1])}>'


def fea(names, placed, p: Params) -> str:
    """Feature code for the marks among ``names``: GDEF, ccmp, mark, mkmk.
    ``placed`` maps names to (rings, advance) as the font has them."""
    names = list(names)
    mark_names = [n for n in names if REGISTRY[n].kind == 'mark']
    if not mark_names:
        return ''
    bases = [n for n in names if REGISTRY[n].kind in BASE_KINDS or n in EXTRA_BASES]
    lines = []
    m_info = {n: mark_anchors(n, placed[n][0], p) for n in mark_names}
    by_class = {c: [n for n in mark_names if m_info[n][0] == c] for c in CLASSES}
    for n in mark_names:
        lines.append(f'markClass {n} {_a(m_info[n][1])} @MC_{m_info[n][0]};')
    others = [n for n in names if n not in set(mark_names)]
    lines.append(f'table GDEF {{\n  GlyphClassDef [{" ".join(others)}], , [{" ".join(mark_names)}], ;\n}} GDEF;')
    for c in CLASSES:
        if by_class[c]:
            lines.append(f'@MARKS_{c} = [{" ".join(by_class[c])}];')

    # ccmp: dotless i and j before a mark above; flatter marks over capitals
    top_lc = [n for n in by_class['top'] if not n.endswith('.case')]
    top_uc = [f'{n}.case' for n in top_lc if f'{n}.case' in set(mark_names)]
    top_lc = [n for n in top_lc if f'{n}.case' in set(mark_names)]
    caps = [n for n in names if REGISTRY[n].kind in ('cap', 'fig')]
    have = set(names)
    dotless = [(a, b) for a, b in (('i', 'dotlessi'), ('j', 'uni0237')) if a in have and b in have]
    decomp = [(a, b, c) for a, b, c in (('iogonek', 'dotlessi', 'uni0328'), ('uni1ECB', 'dotlessi', 'dotbelowcomb'))
              if {a, b, c} <= have]
    ccmp = []
    if dotless:
        lines.append('lookup CCMP_DOTLESS_SUB {\n' + ''.join(f'  sub {a} by {b};\n' for a, b in dotless)
                     + '} CCMP_DOTLESS_SUB;')
    if decomp:
        lines.append('lookup CCMP_DECOMPOSE_SUB {\n' + ''.join(f'  sub {a} by {b} {c};\n' for a, b, c in decomp)
                     + '} CCMP_DECOMPOSE_SUB;')
    if top_lc:
        lines.append('lookup CCMP_CASE_SUB {\n' + ''.join(f'  sub {a} by {b};\n' for a, b in zip(top_lc, top_uc))
                     + '} CCMP_CASE_SUB;')
    from .glyphs.latin_plus import PAIRS
    pairs = [(a, b, c) for (a, b), c in PAIRS.items() if {a, b, c} <= have]
    pairs += [(f'{a}.case', f'{b}.case', f'{c}.case') for a, b, c in pairs
              if {f'{a}.case', f'{b}.case', f'{c}.case'} <= have]
    if dotless or decomp:
        rules = ''
        if dotless:
            rules += f'    sub [{" ".join(a for a, _ in dotless)}]\' lookup CCMP_DOTLESS_SUB @MARKS_top;\n'
        if decomp:
            rules += f'    sub [{" ".join(a for a, _, _ in decomp)}]\' lookup CCMP_DECOMPOSE_SUB @MARKS_top;\n'
        ccmp.append('  lookup CCMP_DOTLESS {\n    lookupflag UseMarkFilteringSet @MARKS_top;\n' + rules
                    + '  } CCMP_DOTLESS;')
    if top_lc and caps:
        lines.append(f'@CCMP_CAPS = [{" ".join(caps)}];')
        lines.append(f'@CCMP_TOP_LC = [{" ".join(top_lc)}];')
        lines.append(f'@CCMP_TOP_UC = [{" ".join(top_uc)}];')
        ccmp.append('  lookup CCMP_CASE {\n    lookupflag UseMarkFilteringSet @MARKS_top;\n'
                    "    sub @CCMP_CAPS @CCMP_TOP_LC' lookup CCMP_CASE_SUB;\n"
                    "    sub @CCMP_TOP_UC @CCMP_TOP_LC' lookup CCMP_CASE_SUB;\n"
                    '  } CCMP_CASE;')
    if pairs:                                               # Vietnamese: a tone mark beside the circumflex
        ccmp.append('  lookup CCMP_PAIRS {\n    lookupflag UseMarkFilteringSet @MARKS_top;\n'
                    + ''.join(f'    sub {a} {b} by {c};\n' for a, b, c in pairs) + '  } CCMP_PAIRS;')
    if ccmp:
        lines.append('feature ccmp {\n' + '\n'.join(ccmp) + '\n} ccmp;')

    # mark: every base, every class
    rows = []
    for n in bases:
        a = base_anchors(n, placed[n][0], p)
        rows.append(f'    pos base {n} ' + ' '.join(f'{_a(a[c])} mark @MC_{c}' for c in CLASSES if by_class[c]) + ';')
    lines.append('feature mark {\n  lookup MARK_BASE {\n' + '\n'.join(rows) + '\n  } MARK_BASE;\n} mark;')

    # mkmk: marks above stack on marks above, marks below under marks below
    mk = []
    for c in ('top', 'bottom'):
        rows = [f'    pos mark {n} {_a(m_info[n][2])} mark @MC_{c};' for n in by_class[c] if m_info[n][2]]
        if rows:
            mk.append(f'  lookup MKMK_{c.upper()} {{\n    lookupflag UseMarkFilteringSet @MARKS_{c};\n'
                      + '\n'.join(rows) + f'\n  }} MKMK_{c.upper()};')
    if mk:
        lines.append('feature mkmk {\n' + '\n'.join(mk) + '\n} mkmk;')
    return '\n'.join(lines) + '\n'
