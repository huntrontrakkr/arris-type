"""Font assembly: glyph rings to TrueType, static and variable."""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.pointPen import SegmentToPointPen  # noqa: F401  (kept for later point pens)

from .draw import REGISTRY, TAB_MATH, draw
from .params import Params

UPM = 1000


@dataclass
class Metrics:
    asc: int = 975      # hhea/typo ascender: room for accents over capitals (the Black À reaches 968)
    desc: int = -250
    gap: int = 0
    cap: int = 720
    xh: int = 540
    # Windows clipping box, one for the whole family (every weight, grade,
    # balance and the italic; Windows spaces lines by the typo metrics,
    # USE_TYPO_METRICS): the tallest drawing is ȭ at the heaviest corner of
    # the variable font (1179), the deepest the stacked operators ≑ ≒ ≓ (-382).
    win_asc: int = 1180
    win_desc: int = 390


def glyph_contours(name: str, p: Params, tune=None):
    """Integer contours for a glyph, TrueType orientation (outer clockwise)."""
    t = (tune or {}).get(name, {})
    g = draw(name, p, ot=t.get('ot', 0.0), ob=t.get('ob', 0.0))
    out = []
    for ring in g.rings():
        pts = [(round(x), round(y)) for x, y in ring]
        clean = []
        for q in pts:
            if not clean or q != clean[-1]:
                clean.append(q)
        if len(clean) > 1 and clean[0] == clean[-1]:
            clean.pop()
        if len(clean) >= 3:
            out.append(clean[::-1])  # ink-left (CCW shells) -> clockwise shells
    return out


# Optical spacing: the H's sidebearing as a fraction of its counter, and how
# deep into a side's white the eye counts it (fraction of the zone height).
SPACE = 0.27
DEPTH = 0.2
PUNCT_SIDE = 0.9   # punctuation bearings, as a share of the letters' light


def light(p: Params) -> float:
    """Target mean white per side: the H's sidebearing."""
    h_counter = (9 * p.m + (p.sv - 120)) - 2 * p.sv
    return SPACE * h_counter


def place(name: str, p: Params, tune=None):
    """(rings shifted into place, advance) for a glyph. In the italic
    (``p.slant``) the rings are italic contours of (x, y, on): spaced as the
    upright drawing, then curved and sheared (``arris.italic``)."""
    if p.slant:
        from . import italic
        rings, record, adv = _place(name, p, tune, record=True)
        if REGISTRY[name].cell:
            # a terminal cell's drawing joins the cells above and below it:
            # curved like the italic, never slanted (see _place)
            p = p.with_(slant=0.0)
        return italic.outline(rings, record, p), adv
    rings, _, adv = _place(name, p, tune)
    return rings, adv


def _shift_record(record, dx):
    from .draw import _moved
    return [_moved(r, dx, 0.0) for r in record]


# --- The drawing cache ---------------------------------------------------------
#
# A drawing is a function of the engine's source, the glyph and its
# parameters: kept on disk (one SQLite file every process shares, and in
# memory), a rebuild, a sweep or a check draws only what it has not drawn
# since the engine last changed. ARRIS_CACHE names the file ('' turns it
# off). The key holds a hash of every file of the engine (src/arris), so any
# change to it starts afresh.

_ENGINE = None
_DB = None
_MEM: dict = {}


def _engine_hash():
    global _ENGINE
    if _ENGINE is None:
        import hashlib
        root = Path(__file__).resolve().parent
        h = hashlib.sha1()
        for f in sorted(root.rglob('*')):
            if f.is_file() and '__pycache__' not in f.parts and f.name != 'version.py':
                h.update(str(f.relative_to(root)).encode())
                h.update(f.read_bytes())
        _ENGINE = h.hexdigest()
    return _ENGINE


def _db():
    """This process's connection (opened afresh in a forked child)."""
    global _DB
    import os
    import sqlite3
    import time
    path = os.environ.get('ARRIS_CACHE', str(Path(__file__).resolve().parents[2] / 'build' / 'cache' / 'draw.sqlite'))
    if not path:
        return None
    if _DB is None or _DB[0] != os.getpid():
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(path, timeout=300, isolation_level=None)
        # a fresh file: workers racing to switch it to WAL get "locked" at
        # once, not after the timeout, so try again until one has (WAL stays
        # with the file, and the switch is then a no-op for the rest)
        for tries in range(200):
            try:
                con.execute('PRAGMA journal_mode=WAL')
                con.execute('CREATE TABLE IF NOT EXISTS draw (k TEXT PRIMARY KEY, e TEXT, v BLOB)')
                con.execute('CREATE TABLE IF NOT EXISTS anchor (k TEXT PRIMARY KEY, e TEXT, v TEXT)')   # draw._anchor
                break
            except sqlite3.OperationalError as e:
                if 'locked' not in str(e) or tries == 199:
                    raise
                time.sleep(0.05)
        con.execute('PRAGMA synchronous=NORMAL')
        _DB = (os.getpid(), con)
    return _DB[1]


def prune_cache():
    """Drop the drawings of every other version of the engine; returns how
    many went."""
    con = _db()
    if con is None:
        return 0
    n = con.execute('DELETE FROM draw WHERE e != ?', (_engine_hash(),)).rowcount
    con.execute('DELETE FROM anchor WHERE e != ?', (_engine_hash(),))
    con.execute('PRAGMA wal_checkpoint(TRUNCATE)')
    return n


def _place(name: str, p: Params, tune=None, record: bool = False, tags: list | None = None):
    """(rings, chamfer record, advance), upright, shifted into place;
    ``tags`` collects the names of the rings' edges (``geom.ink``).
    Remembered (the drawing cache, above)."""
    import hashlib
    import pickle
    import zlib
    from . import geom
    con = _db()
    if con is None:
        return _place_drawn(name, p, tune, record, tags)
    spec = REGISTRY[name]
    key = hashlib.sha1(repr((_engine_hash(), name, p, sorted((tune or {}).get(name, {}).items()), record,
                             tags is not None, geom.JOG, getattr(spec.fn, 'pin', None),
                             tuple(sq.free for sq in spec.squint))).encode()).hexdigest()
    hit = _MEM.get(key)
    if hit is None:
        row = con.execute('SELECT v FROM draw WHERE k = ?', (key,)).fetchone()
        if row is not None:
            hit = pickle.loads(zlib.decompress(row[0]))
        else:
            names = [] if tags is not None else None
            rings, rec, adv = _place_drawn(name, p, tune, record, names)
            hit = (rings, rec, adv, names, BODIES.get((name, p)))
            con.execute('INSERT OR REPLACE INTO draw VALUES (?, ?, ?)',
                        (key, _engine_hash(), zlib.compress(pickle.dumps(hit), 3)))
        _MEM[key] = hit
    rings, rec, adv, names, body = hit
    if body is not None:
        BODIES[name, p] = body
    if tags is not None:
        tags.extend(names)
    return [list(r) for r in rings], list(rec), adv


def _place_drawn(name: str, p: Params, tune=None, record: bool = False, tags: list | None = None):
    """_place, drawn."""
    from .spacing import bearings
    t = (tune or {}).get(name, {})
    if REGISTRY[name].kind == 'space':
        # a space: empty, its own advance; in the monospaced cut a cell
        # (zero-width characters advance nothing in either)
        w = REGISTRY[name].width(p.ungraded())
        return [], [], (p.fig_adv if p.mono and w > 0 else w)
    if p.slant and REGISTRY[name].cell:
        p = p.with_(slant=0.0)          # drawn upright, so no stroke is set for a shear (geom.Thickness)
    if p.grade_k != 1.0:
        # Grade changes strokes only: space the glyph as its ungraded self,
        # then draw the graded strokes in the same body at the same place.
        p0 = p.ungraded()
        g0 = draw(name, p0, ot=t.get('ot', 0.0), ob=t.get('ob', 0.0))
        r0, _, adv = _place(name, p0, tune)
        dx = min(x for r in r0 for x, _ in r) - min(x for r in g0.rings() for x, _ in r) if r0 else 0.0
        # glyphs no wider than a couple of stems (I, i, dots) thicken outward,
        # centred where they were; everything else keeps its body
        W = g0.W
        if W <= 2.5 * p0.sv:
            W = REGISTRY[name].width(p)
            dx += (g0.W - W) / 2
        g = draw(name, p, ot=t.get('ot', 0.0), ob=t.get('ob', 0.0), width=W)
        rings, rec = g.outline(record, tags=tags)
        return _body(name, p, rings, dx, W), _shift_record(rec, dx), adv
    g = draw(name, p, ot=t.get('ot', 0.0), ob=t.get('ob', 0.0))
    rings, rec = g.outline(record, tags=tags)
    spec = REGISTRY[name]
    if isinstance(spec.kind, tuple) and spec.kind[0] == 'liga':
        # a ligature is one cell wide and draws back over the n - 1 spacers
        # before it, its body starting at the first cell's margin
        adv = p.fig_adv
        dx = (p.fig_adv - p.fig_w) / 2 - (spec.kind[1] - 1) * p.fig_adv
    elif spec.kind == 'mark':
        # a combining mark takes no room: it hangs over the glyph before it
        # (where mark positioning, ``anchors``, moves it to its base)
        adv = 0.0
        dx = -g.W / 2 - mark_over(p)
    elif spec.kind == 'fig' or p.mono:
        adv = p.fig_adv
        dx = (adv - g.W) / 2
    elif isinstance(spec.kind, tuple) and spec.kind[0] == 'punct':
        xs = [x for r in rings for x, _ in r] or [0.0, g.W]
        k = spec.kind[1]
        side = k(p) if callable(k) else PUNCT_SIDE * light(p) * k      # a glyph may set its own side
        dx = side - min(xs)
        adv = side + (max(xs) - min(xs)) + side
        if name in TAB_MATH and name != 'plus':                          # math on one advance, at least
            tab = _place('plus', p)[2]
            if adv < tab:
                dx += (tab - adv) / 2
                adv = tab
    else:
        zone = (0.0, p.xh) if spec.kind == 'lower' else (0.0, p.cap)
        lsb, rsb, xmin, xmax = bearings(rings, *zone, light(p), DEPTH * (zone[1] - zone[0]),
                                        floor=-0.25 * p.m)
        # Parts outside the zone (a j's hook, a descender's tail) may hang
        # into the neighbour's space, but by no more than half its light.
        fx0 = min(x for r in rings for x, _ in r)
        fx1 = max(x for r in rings for x, _ in r)
        reach = 0.5 * light(p)
        lsb = max(lsb, (xmin - fx0) - reach)
        rsb = max(rsb, (fx1 - xmax) - reach)
        dx = lsb - xmin
        adv = lsb + (xmax - xmin) + rsb
    return _body(name, p, rings, dx, g.W), _shift_record(rec, dx), adv


# Where each placed glyph's body went, (name, params) -> (x offset, body
# width, upright rings in place): mark positioning (``anchors``) centres
# marks on bodies and measures upright outlines, as the composed accented
# letters do.
BODIES: dict = {}


def _body(name, p, rings, dx, W):
    out = [[(x + dx, y) for x, y in r] for r in rings]
    BODIES[name, p] = (dx, W, out)
    return out


def mark_over(p: Params) -> float:
    """Where a combining mark sits before mark positioning moves it to its
    base (``anchors``): centred on its own origin. Hung over the middle of an
    n, it sat exactly where an n-wide letter's anchor puts it (a y, every
    Mono glyph), unmoved, which checkers read as a mark left unattached."""
    return 0.0


def spacing(name: str, p: Params):
    """(left side bearing, advance) of the glyph body (used by proofs)."""
    rings, adv = place(name, p)
    return 0.0, adv


def _raw_glyph(contours):
    """A glyf glyph with exactly these points: nothing merged or dropped,
    as variable-font masters need. Points are (x, y) on the curve, or
    (x, y, on) for the italic's quadratic outlines."""
    from fontTools.ttLib.tables._g_l_y_f import Glyph, GlyphCoordinates
    g = Glyph()
    pts, ends, flags = [], [], []
    for c in contours:
        pts.extend(q[:2] for q in c)
        flags.extend(1 if (len(q) < 3 or q[2]) else 0 for q in c)
        ends.append(len(pts) - 1)
    g.numberOfContours = len(contours)
    g.coordinates = GlyphCoordinates(pts)
    g.endPtsOfContours = ends
    g.flags = bytearray(flags)
    g.program = __import__('fontTools.ttLib.tables.ttProgram', fromlist=['Program']).Program()
    g.program.fromBytecode(b'')
    return g


def _tt_glyph(contours, lsb):
    pen = TTGlyphPen(None)
    for c in contours:
        pen.moveTo((c[0][0] + lsb, c[0][1]))
        for x, y in c[1:]:
            pen.lineTo((x + lsb, y))
        pen.closePath()
    return pen.glyph()


def _notdef(p: Params):
    """The missing glyph: a chamfered octagon (Arris's O, opened up to a
    box) with the scissors inside, cutting corners where it can. One
    drawing, at Regular, in every weight and master (it does not vary)."""
    from .draw import Glyph, draw
    from .glyphs.shapes import ring
    from .glyphs.symkit import _scaled
    from .instances import params
    q = params(400)
    W, H, lsb = 480, 720, 40
    g = Glyph(q, W=W)
    ring(g, W / 2, H / 2, W, H)
    full = [pt for r in draw('uni2702', q).rings() for pt in r]
    fw = max(x for x, _ in full) - min(x for x, _ in full)
    k = (W - 2.8 * q.sv) / fw                               # the scissors fill the box, 0.4 of a stroke clear of each wall
    sub = draw('uni2702', _scaled(q, k))
    pts = [pt for r in sub.rings() for pt in r]
    x0, x1 = min(x for x, _ in pts), max(x for x, _ in pts)
    y0, y1 = min(y for _, y in pts), max(y for _, y in pts)
    g.add_glyph(sub, W / 2 - (x0 + x1) / 2, H / 2 - (y0 + y1) / 2)
    return _tt_glyph(_contours(g.rings()), lsb), W + 2 * lsb


KERN_PUNCT = {'period', 'comma', 'colon', 'semicolon', 'hyphen', 'endash', 'emdash', 'quotesingle', 'quotedbl',
              'quoteleft', 'quoteright', 'quotedblleft', 'quotedblright', 'quotesinglbase', 'quotedblbase',
              'parenleft', 'parenright', 'bracketleft', 'bracketright', 'braceleft', 'braceright', 'slash',
              'backslash', 'guilsinglleft', 'guilsinglright', 'guillemotleft', 'guillemotright', 'exclam',
              'question', 'ampersand', 'asterisk', 'at', 'ellipsis'}


def _contours(rings, keep=False):
    """Rounded TrueType contours (outer clockwise) from ink-left rings.
    ``keep``: keep every point, duplicates included (variable-font masters)."""
    out = []
    for ring in rings:
        pts = [(round(x), round(y)) for x, y in ring]
        if keep:
            out.append(pts[::-1])
            continue
        clean = []
        for q in pts:
            if not clean or q != clean[-1]:
                clean.append(q)
        if len(clean) > 1 and clean[0] == clean[-1]:
            clean.pop()
        clean = _drop_colinear(clean)
        for loop in _untangled(clean):
            # a speck rounding leaves (two edges a unit apart closing a
            # pinhole, a sliver) is not a contour
            if len(loop) >= 3 and abs(_shoelace(loop)) >= LOOP:
                out.append(loop[::-1])
    return out


def _shoelace(pts):
    return sum(pts[i - 1][0] * pts[i][1] - pts[i][0] * pts[i - 1][1] for i in range(len(pts))) / 2


LOOP = 4.0      # square units: a loop of a contour crossing itself smaller than this is dropped


def _untangled(pts):
    """A contour that crosses or touches itself (a chamfer's leg meeting a
    stroke's end by a unit or two: α's tail at the baseline, the 1's flag
    at Black), as the simple loops it makes, in its own direction; loops
    too small to see go. A simple contour is returned as it is. (Static
    fonts only: a variable font's masters keep every point.)"""
    import shapely
    from shapely.geometry import LinearRing, Polygon
    from shapely.geometry.polygon import orient
    if len(pts) < 4 or LinearRing(pts).is_simple:
        return [pts]
    area = sum(pts[i - 1][0] * pts[i][1] - pts[i][0] * pts[i - 1][1] for i in range(len(pts))) / 2
    sign = 1.0 if area > 0 else -1.0
    v = shapely.make_valid(Polygon(pts))
    out = []
    for poly in getattr(v, 'geoms', [v]):
        if poly.geom_type != 'Polygon' or poly.area < LOOP:
            continue
        poly = orient(poly, sign)
        out.append([(round(x), round(y)) for x, y in list(poly.exterior.coords)[:-1]])
        for hole in poly.interiors:
            if Polygon(hole).area >= LOOP:
                out.append([(round(x), round(y)) for x, y in list(hole.coords)[:-1]])
    return out or [pts]


def _drop_colinear(pts):
    """Without the points that lie on a straight run between their
    neighbours (rounding leaves some): a static outline needs none of them."""
    changed = True
    while changed and len(pts) > 3:
        changed = False
        for i in range(len(pts)):
            a, b, c = pts[i - 1], pts[i], pts[(i + 1) % len(pts)]
            u, v = (b[0] - a[0], b[1] - a[1]), (c[0] - b[0], c[1] - b[1])
            if u[0] * v[1] - u[1] * v[0] == 0 and u[0] * v[0] + u[1] * v[1] > 0:
                del pts[i]
                changed = True
                break
    return pts


SCRIPTS = 'Latn, Cyrl, Grek'


def add_meta(font):
    """The scripts the font is designed for and supports (the 'meta' table)."""
    from fontTools.ttLib import newTable
    meta = newTable('meta')
    meta.data = {'dlng': SCRIPTS, 'slng': SCRIPTS}
    font['meta'] = meta


def _nonhinting(font):
    """No hints, but smart dropout control and a gasp table, so unhinted
    outlines rasterise solidly at small sizes (what gftools fix-nonhinting does)."""
    from fontTools.ttLib import newTable
    from fontTools.ttLib.tables import ttProgram
    prep = newTable('prep')
    prep.program = ttProgram.Program()
    prep.program.fromAssembly(['PUSHW[ ]', '511', 'SCANCTRL[ ]', 'PUSHB[ ]', '4', 'SCANTYPE[ ]'])
    font['prep'] = prep
    gasp = newTable('gasp')
    gasp.version = 1
    gasp.gaspRange = {0xFFFF: 0x000F}
    font['gasp'] = gasp


from .version import VERSION  # noqa: E402
REPO = 'https://github.com/huntrontrakkr/arris-type'
COPYRIGHT = f'Copyright 2026 The Arris Project Authors ({REPO})'
LICENSE = ('This Font Software is licensed under the SIL Open Font License, Version 1.1. '
           'This license is available with a FAQ at: https://openfontlicense.org')
LICENSE_URL = 'https://openfontlicense.org'


def build(path, names, p: Params, family='Arris', style='SemiBold', weight=600, tune=None,
          metrics: Metrics | None = None, version=VERSION, space=None, fea: str | None = None,
          kern: bool = True, placed: dict | None = None, kern_pairs: dict | None = None, stat: bool = True,
          components: dict | None = None):
    """Write a font of ``names`` at p. ``components`` (name -> [(component,
    dx, dy)]): glyphs carried as TrueType composites (their rings in
    ``placed`` still give their anchors and kerning)."""
    m = metrics or Metrics(cap=round(p.cap), xh=round(p.xh))
    order = ['.notdef', 'space'] + list(names)
    fb = FontBuilder(UPM, isTTF=True)
    fb.setupGlyphOrder(order)
    cmap = {0x20: 'space', 0xA0: 'space'}
    for n in names:
        if REGISTRY[n].unicode is not None:
            cmap[REGISTRY[n].unicode] = n
    from .glyphs import ALIASES
    for cp, n in ALIASES.items():
        if n in names and cp not in cmap:
            cmap[cp] = n
    fb.setupCharacterMap(cmap)
    glyphs, hmtx = {}, {}
    glyphs['.notdef'], adv = _notdef(p)
    hmtx['.notdef'] = (adv, 40)
    glyphs['space'] = TTGlyphPen(None).glyph()
    hmtx['space'] = (round(space if space is not None else (p.fig_adv if p.mono else 0.45 * p.xh)), 0)
    keep = placed is not None
    placed = dict(placed or {})
    for n in names:
        if n not in placed:
            placed[n] = place(n, p, tune)
        rings, adv = placed[n]
        if components and n in components:
            pen = TTGlyphPen(set(order))                    # (it checks the components are glyphs)
            for c, dx, dy in components[n]:
                pen.addComponent(c, (1, 0, 0, 1, round(dx), round(dy)))
            glyphs[n] = pen.glyph()
        elif p.slant and keep:
            glyphs[n] = _raw_glyph([[(round(x), round(y), on) for x, y, on in c][::-1] for c in rings])
        elif p.slant:
            from . import italic
            pen = TTGlyphPen(None)
            italic.draw_contours(pen, italic.tt_contours(rings))
            glyphs[n] = pen.glyph()
        else:
            glyphs[n] = _raw_glyph(_contours(rings, keep)) if keep else _tt_glyph(_contours(rings), 0)
        hmtx[n] = (round(adv), 0)
    from .anchors import fea as mark_fea                     # mark positioning: anchors from the outlines
    fea = (fea or '') + mark_fea(names, placed, p)
    if kern_pairs is not None:
        from .kerning import fea as kern_fea
        fea = (fea or '') + kern_fea(kern_pairs)
    elif kern and not p.mono:
        from .kerning import fea as kern_fea, kerns
        kinds = {n: REGISTRY[n].kind for n in names}
        kernable = [n for n in names if kinds[n] in ('cap', 'lower') or
                    (isinstance(kinds[n], tuple) and n in KERN_PUNCT)]
        if p.slant:
            from .italic import polylines
            outlines = {n: (polylines(placed[n][0]), round(placed[n][1])) for n in kernable}
        else:
            outlines = {n: (placed[n][0], round(placed[n][1])) for n in kernable}
        pairs = kerns(outlines, p, light(p))
        fea = (fea or '') + kern_fea(pairs)
        print(f'  {len(pairs)} kerning pairs')
    fb.setupGlyf(glyphs)
    ymin, ymax = 0, 0
    for n, (adv, _) in hmtx.items():
        g = glyphs[n]
        g.recalcBounds(fb.font['glyf'])
        if g.numberOfContours:
            ymin, ymax = min(ymin, g.yMin), max(ymax, g.yMax)
        hmtx[n] = (adv, getattr(g, 'xMin', 0) if g.numberOfContours else 0)
    fb.setupHorizontalMetrics(hmtx)
    fb.setupHorizontalHeader(ascent=m.asc, descent=m.desc, lineGap=m.gap)
    is_italic = style.endswith('Italic')
    base = style[:-len('Italic')].strip() or 'Regular' if is_italic else style
    ribbi = base in ('Regular', 'Bold')
    fam1 = family if ribbi else f'{family} {base}'
    sub1 = style if ribbi else ('Italic' if is_italic else 'Regular')
    ps = f'{family}-{style}'.replace(' ', '')
    strings = {'familyName': fam1, 'styleName': sub1, 'uniqueFontIdentifier': f'{ps};{version}',
               'fullName': f'{family} {style}', 'psName': ps, 'version': f'Version {version}',
               'description': f'{family}, a chamfered sans.', 'copyright': COPYRIGHT,
               'licenseDescription': LICENSE, 'licenseInfoURL': LICENSE_URL}
    if not ribbi:                       # Regular, Bold and their italics need no typographic names (16, 17)
        strings.update(typographicFamily=family, typographicSubfamily=style)
    fb.setupNameTable(strings, mac=False)
    fb.setupOS2(sTypoAscender=m.asc, sTypoDescender=m.desc, sTypoLineGap=m.gap,
                usWinAscent=max(m.win_asc, ymax), usWinDescent=max(m.win_desc, -ymin), sxHeight=m.xh,
                sCapHeight=m.cap, usWeightClass=weight,
                fsSelection=0x80 | (0x20 if base == 'Bold' else 0) | (0x01 if is_italic else 0)
                | (0x40 if not is_italic and base != 'Bold' else 0),
                achVendID='NONE', fsType=0, version=4)                 # installable: the OFL allows embedding
    fb.setupPost(isFixedPitch=1 if p.mono else 0,
                 italicAngle=-math.degrees(math.atan(p.slant)) if p.slant else 0)
    if p.slant:
        fb.font['hhea'].caretSlopeRise = 1000
        fb.font['hhea'].caretSlopeRun = round(1000 * p.slant)
    fb.font['head'].fontRevision = float(version)
    os2 = fb.font['OS/2']
    os2.recalcCodePageRanges(fb.font)
    os2.recalcUnicodeRanges(fb.font)
    _nonhinting(fb.font)
    add_meta(fb.font)
    if p.mono:
        fb.font['OS/2'].panose.bFamilyType = 2
        fb.font['OS/2'].panose.bProportion = 9
    if base == 'Bold':
        fb.font['head'].macStyle |= 1
    if is_italic:
        fb.font['head'].macStyle |= 2
    if fea:
        from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
        addOpenTypeFeaturesFromString(fb.font, fea)
    if stat:
        # where this font sits in the family: its weight, upright or italic
        from fontTools.otlLib.builder import buildStatTable
        buildStatTable(fb.font, [
            {'tag': 'wght', 'name': 'Weight',
             'values': [{'value': weight, 'name': base, 'flags': 0x2 if base == 'Regular' else 0}]},
            {'tag': 'ital', 'name': 'Italic',
             'values': [{'value': 1, 'name': 'Italic'}] if is_italic else
                       [{'value': 0, 'name': 'Roman', 'flags': 0x2, 'linkedValue': 1}]},
        ])
        fb.font['name'].names = [nm for nm in fb.font['name'].names if nm.platformID != 1]
    fb.font.save(path)
    return fb.font
