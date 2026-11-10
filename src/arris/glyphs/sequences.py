"""Arris Mono's runs of any length, after Fira Code's: `---->` `<====>`
`|---|` `>=>` `--|--` `=!==` `####` `____`.

A run of hyphens, equal signs, underscores or number signs, with a cap at
either end or one inside it, is set as pieces, one to a cell. Each piece
draws its cell's share of the run's lines, which run on past the cell's
edge into the next piece's by OV and meet it flush (the corner rule leaves
the cut square there: ``Glyph.butt``), so a run is one line however long.
Its caps are the ligatures' own: the arrowhead of `->`, the double head of
`->>`, the pipe and the slash as themselves, the chevron as a tail (its
point on the line: `>->` `<=<`), `||` `//` `>>` as their repeats set them;
inside a run, a pipe across it, a head on it, the struck bars of `=/=`,
the `!` and `:` of `=!=` `=:=` with the white of `:=` either side.

The fixed ligatures (`->` `<==>` `--` `==` `===` `!=` ...) are matched
first; the runs take what is longer, or what those leave. A run forms when
it has LEAST characters with no cap, two with one cap, or one between two
caps (`|-|` `>=>`), never when the cap is the start of a longer run of its
own character (`<<<--` `-->>>`).
"""
from __future__ import annotations

from ..draw import glyph
from ..params import SQRT2
from .ligatures import (
    DOUBLE,
    _bar_at,
    _body,
    _gap,
    _hash,
    _ink_of,
    _raised,
    _run,
    _slash_line,
    _stamp,
    _strike,
    _sub,
    _tip,
    bars_offset,
    cell,
    head,
    head_h,
)
from .punct import axis

OV = 0.25       # of a module: how far a piece's lines run on past its cell, into the next piece's

KINDS = ('hyphen', 'equal', 'underscore', 'numbersign')
LEAST = {'hyphen': 3, 'equal': 4, 'underscore': 2, 'numbersign': 2}     # a run with no cap, at least
# the caps, as the characters that make them at a run's left and right ends
LEFT = {'head': ('less',), 'head2': ('less', 'less'), 'tail': ('greater',), 'tail2': ('greater', 'greater'),
        'bar': ('bar',), 'bar2': ('bar', 'bar'), 'slash': ('slash',), 'slash2': ('slash', 'slash')}
RIGHT = {'head': ('greater',), 'head2': ('greater', 'greater'), 'tail': ('less',), 'tail2': ('less', 'less'),
         'bar': ('bar',), 'bar2': ('bar', 'bar'), 'slash': ('slash',), 'slash2': ('slash', 'slash')}
MID = {'bar': 'bar', 'right': 'greater', 'left': 'less', 'exclam': 'exclam', 'colon': 'colon', 'slash': 'slash'}
CAPS = {'hyphen': ('head', 'head2', 'tail', 'tail2', 'bar', 'bar2'),
        'equal': ('head', 'head2', 'tail', 'tail2', 'bar', 'bar2', 'slash', 'slash2'),
        'underscore': (), 'numbersign': ()}
MIDS = {'hyphen': ('bar', 'right', 'left'), 'equal': ('bar', 'right', 'left', 'exclam', 'colon', 'slash'),
        'underscore': ('bar',), 'numbersign': ()}


def _lines(g, kind):
    """The run's lines, as (y, thickness or None for the stroke's own)."""
    p = g.p
    a = axis(p)
    if kind == 'hyphen':
        return [(a, None)]
    if kind == 'equal':
        off = bars_offset(g)
        return [(a - off, None), (a + off, None)]
    if kind == 'underscore':
        ink = _ink_of(_sub('underscore', p))
        return [((ink.bounds[1] + ink.bounds[3]) / 2, ink.bounds[3] - ink.bounds[1])]
    return list(_hash(p)[1])


def _cells(g):
    p = g.p
    return round((g.W + p.fig_adv - p.fig_w) / p.fig_adv)


def _chevron_point(sub, x0, g, sign):
    """The point of a < (sign -1) or > (1) set at x0."""
    from .punct import chevron_geometry
    x_tip, _ = chevron_geometry(g, sub.W)
    return x0 + x_tip if sign < 0 else x0 + sub.W - x_tip


def _cap(g, kind, cap, right):
    """Draw the cap at the piece's right end (or its left); return x(y),
    where the run's line at height y leaves it."""
    p = g.p
    s = 1 if right else -1
    out = _cells(g) - 1 if right else 0
    a = axis(p)
    if cap == 'own':                                    # the character's own end
        if kind == 'numbersign':
            _, _, stems = _hash(p)
            _, xh = _stamp(g, 'numbersign', out)
            x = xh + (stems[0][0] + p.sv / 2 if right else stems[-1][1] - p.sv / 2)
        else:
            sub = _sub(kind, p)
            ink = _ink_of(sub, (p.fig_w - sub.W) / 2 + out * p.fig_adv)
            x = ink.bounds[2] if right else ink.bounds[0]
        return lambda y: x
    if cap in ('head', 'head2'):                        # `->`'s head, `->>`'s two
        t = _tip(g, s)
        head(g, (t, a), s)
        if cap == 'head2':
            t2 = t - s * (DOUBLE * head_h(p) + 2 * SQRT2 * p.sd)
            head(g, (t2, a), s)
            if kind != 'hyphen':                        # bars end on the inner head (`->>`'s shaft runs through it)
                return lambda y: t2 - s * abs(y - a)
        return lambda y: t - s * abs(y - a)            # bars end on the head's arms, as `=>`'s
    if cap in ('tail', 'tail2'):                        # the chevron pointing into the run, its point on the line
        name = 'less' if right else 'greater'
        if cap == 'tail':
            sub, x0 = _stamp(g, name, out)
        else:
            placed = _run(g, [name, name])
            sub, x0 = placed[0] if right else placed[-1]
        t = _chevron_point(sub, x0, g, -s)
        return lambda y: t + s * 2 * abs(y - a)        # bars leave its arms
    if cap in ('bar', 'bar2'):
        if cap == 'bar':
            x = _bar_at(g, out)
        else:
            placed = _run(g, ['bar', 'bar'])
            sub, x0 = placed[0] if right else placed[-1]
            x = x0 + sub.W / 2
        return lambda y: x
    if cap == 'slash':
        return _slash_line(g, out)
    from .letterframe import STEEP  # slash2: `//` as its repeat sets it
    placed = _run(g, ['slash', 'slash'])
    _, x0 = placed[0] if right else placed[-1]
    bot, w = -p.under + 0.5 * p.m, p.ss / STEEP[1]
    return lambda y: x0 + w / 2 + (y - bot) / 2


def _mid(g, kind, mid):
    """Draw a cap inside the run; return the spans of white it leaves on the lines."""
    p = g.p
    if mid == 'bar':
        _bar_at(g, 0)
        return []
    if mid in ('right', 'left'):
        s = 1 if mid == 'right' else -1
        head(g, (cell(g, 0)[1] + s * head_h(p) / 2, axis(p)), s)
        return []
    if mid == 'exclam':
        sub, x = _stamp(g, 'exclam', 0)
        ink = _ink_of(sub, x)
        return [(ink.bounds[0] - _gap(p), ink.bounds[2] + _gap(p))]
    if mid == 'colon':
        left, right = _raised(g, 0)
        return [(left - _gap(p), right + _gap(p))]
    return []                                           # slash: struck after the lines


def _piece(g, kind, left, right, mid=None):
    p = g.p
    mg = (p.fig_adv - p.fig_w) / 2
    ov = OV * p.m
    L, R = -mg - ov, g.W + mg + ov
    if kind == 'numbersign' and left is None and right is None:
        _stamp(g, 'numbersign', 0)
    xl = _cap(g, kind, left, False) if left else (lambda y: L)
    xr = _cap(g, kind, right, True) if right else (lambda y: R)
    white = _mid(g, kind, mid) if mid else []
    ys = _lines(g, kind)
    for y, th in ys:
        spans = [(xl(y), xr(y))]
        for w0, w1 in white:
            spans = [q for x0, x1 in spans for q in ((x0, min(x1, w0)), (max(x0, w1), x1)) if q[1] > q[0]]
        for x0, x1 in spans:
            g.stroke((x0, y) if th is None else (x0, y, th), (x1, y))
    if mid == 'slash':
        _strike(g, [y for y, _ in ys])
    g.clip = (L, -10 * p.cap, R, 10 * p.cap)
    g.butt = (('x', L), ('x', R))


def name(kind, tag):
    return f'{kind}.seq.{tag}'


def _register():
    for kind in KINDS:
        def reg(tag, n, left, right, mid=None, kind=kind):
            def fn(g, kind=kind, left=left, right=right, mid=mid):
                _piece(g, kind, left, right, mid)
            glyph(name(kind, tag), None, _body(n), kind=('liga', n))(fn)
        reg('s', 1, 'own', None)
        reg('m', 1, None, None)
        reg('e', 1, None, 'own')
        for cap in CAPS[kind]:
            n = 2 if cap.endswith('2') else 1
            reg(f's.{cap}', n, cap, None)
            reg(f'e.{cap}', n, None, cap)
        for mid in MIDS[kind]:
            reg(f'm.{mid}', 1, None, None, mid)


_register()


# --- Feature code ---------------------------------------------------------

def _lookup(kind):
    e = kind
    opens = [name(kind, 's'), name(kind, 'm')] + [name(kind, f's.{c}') for c in CAPS[kind]] + \
        [name(kind, f'm.{m}') for m in MIDS[kind]]
    OPEN = f'@SEQ_{kind.upper()}'
    ends = sorted({RIGHT[c][0] for c in CAPS[kind]})               # characters that can cap a run's right end
    doubled = sorted({RIGHT[c][0] for c in CAPS[kind] if c.endswith('2')})
    mids = [MID[m] for m in MIDS[kind]]
    END = f'[{" ".join(ends)}]' if ends else None
    rules = []
    # within a run (after a piece open on its right): an element runs on if what follows joins
    for c in doubled:
        rules.append(f"sub {OPEN} {e}' {c} {c} {c} by {name(kind, 'e')};")
    rules.append(f"sub {OPEN} {e}' {e} by {name(kind, 'm')};")
    for c in sorted(set(mids)):
        rules.append(f"sub {OPEN} {e}' {c} {e} by {name(kind, 'm')};")
    if END:
        rules.append(f"sub {OPEN} {e}' {END} by {name(kind, 'm')};")
    rules.append(f"sub {OPEN} {e}' by {name(kind, 'e')};")
    # a cap within or at the end of a run
    for m in MIDS[kind]:
        rules.append(f"sub {OPEN} {MID[m]}' {e} by {name(kind, f'm.{m}')};")
    for cap in CAPS[kind]:
        if cap.endswith('2'):
            c1, c2 = RIGHT[cap]
            rules.append(f"sub {OPEN} {c1}' {c2} by LIG;")
            rules.append(f"sub {OPEN} LIG {c2}' by {name(kind, f'e.{cap}')};")
    for cap in CAPS[kind]:
        if not cap.endswith('2'):
            rules.append(f"sub {OPEN} {RIGHT[cap][0]}' by {name(kind, f'e.{cap}')};")
    # the start of a run
    joins = [f'{e} ' * (LEAST[kind] - 1)]                           # (shorter runs need a cap to join)
    for k in range(1, LEAST[kind] - 1):
        if END:
            joins.append(f'{e} ' * k + f'{END} ')
    for k in range(LEAST[kind] - 1):
        joins += [f'{e} ' * k + f'{c} {e} ' for c in sorted(set(mids))]
    for c in doubled:
        rules.append(f"ignore sub {e}' {e} {c} {c} {c};")
    for j in joins:
        rules.append(f"sub {e}' {j.strip()} by {name(kind, 's')};")
    after = [f'{e} {e}'] + ([f'{e} {END}'] if END else [])          # a capped run: two, or one and a cap
    for cap in CAPS[kind]:
        if cap.endswith('2'):
            c1, c2 = LEFT[cap]
            rules.append(f"ignore sub {c1} {c1}' {c2} {e};")
            for a in after:
                rules.append(f"sub {c1}' {c2} {a} by LIG;")
            rules.append(f"sub LIG {c2}' {e} by {name(kind, f's.{cap}')};")
    for cap in CAPS[kind]:
        if not cap.endswith('2'):
            c = LEFT[cap][0]
            rules.append(f"ignore sub {c} {c}' {e};")
            for a in after:
                rules.append(f"sub {c}' {a} by {name(kind, f's.{cap}')};")
    body = '\n'.join(f'    {r}' for r in rules)
    return f'{OPEN} = [{" ".join(opens)}];\nlookup seq_{kind} {{\n{body}\n}} seq_{kind};'


def fea() -> str:
    """The runs' calt lookups, one to a kind of line, after the fixed
    ligatures'. Each goes left to right, so a rule sees the pieces it has
    already set before it: an element after a piece open on its right is
    a middle (if what follows joins) or the end."""
    out = [_lookup(k) for k in KINDS]
    classes = [o.split('\n', 1)[0] for o in out]
    lookups = [o.split('\n', 1)[1] for o in out]
    return '\n'.join(classes) + '\nfeature calt {\n' + '\n'.join(lookups) + '\n} calt;\n'
