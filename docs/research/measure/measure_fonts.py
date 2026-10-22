#!/usr/bin/env python
"""Measure optical corrections in reference fonts by slicing outlines.

  cd research-fonts
  uv run --no-project --with fonttools --with skia-pathops --with numpy \
      python measure_fonts.py            # -> results.json, tables.md

Method (see geom.py): each glyph is decomposed, overlap-removed with
skia-pathops and flattened to <=0.01 u chord error; measurements are ink
intervals along horizontal, vertical or arbitrary lines.  Stroke thickness
of a diagonal is the length of the cut perpendicular to the stroke's fitted
centre line, taken through the stroke's midpoint.  Every number is a median
over several slice positions; the spread across positions is kept and turned
into a flag when it exceeds a threshold (contrast, taper, curvature).
"""

from __future__ import annotations

import json
import math
import statistics
import sys
import traceback

import numpy as np

from fontset import FACES, ROBOTO_FLEX, instance
from geom import Outline, dist_to_poly, interval_at

EPS = 0.37          # offset (font units) so a slice never runs exactly along an edge
SQ2 = math.sqrt(2)
DIGITS = "0123456789"


def lin(lo, hi, fs):
    return [lo + (hi - lo) * f for f in fs]


def med(v):
    v = [x for x in v if x is not None]
    return statistics.median(v) if v else None


def spread(v):
    v = [x for x in v if x is not None]
    if len(v) < 2:
        return 0.0
    return (max(v) - min(v)) / statistics.mean(v)


def ln(iv):
    return iv[1] - iv[0]


def ctr(iv):
    return 0.5 * (iv[0] + iv[1])


class Glyphs:
    """Lazy cache of Outline objects for one font."""

    def __init__(self, font):
        self.font = font
        self.gs = font.getGlyphSet()
        self.cmap = font.getBestCmap()
        self._c = {}

    def name(self, key):
        return self.cmap[ord(key)] if len(key) == 1 else key

    def __call__(self, key):
        n = self.name(key)
        if n not in self._c:
            self._c[n] = Outline.from_glyphset(self.gs, n)
        return self._c[n]

    def has(self, key):
        return (ord(key) in self.cmap) if len(key) == 1 else key in self.gs


# --------------------------------------------------------------------------
# reference heights and vertical metrics
# --------------------------------------------------------------------------

def m_metrics(font, G):
    os2, hhea, head = font["OS/2"], font["hhea"], font["head"]
    asc = max(G(c).bounds[3] for c in "bdhkl")
    return dict(
        upm=head.unitsPerEm,
        cap=G("H").bounds[3],
        xh=G("x").bounds[3],
        asc=asc,
        desc=G("p").bounds[1],
        fig=G("7").bounds[3],
        os2_cap=getattr(os2, "sCapHeight", None),
        os2_x=getattr(os2, "sxHeight", None),
        typo_asc=os2.sTypoAscender, typo_desc=os2.sTypoDescender, typo_gap=os2.sTypoLineGap,
        win_asc=os2.usWinAscent, win_desc=os2.usWinDescent,
        hhea_asc=hhea.ascent, hhea_desc=hhea.descent, hhea_gap=hhea.lineGap,
        use_typo=bool(os2.fsSelection & (1 << 7)),
        head_ymax=head.yMax, head_ymin=head.yMin,
    )


# --------------------------------------------------------------------------
# 1. stems and horizontal strokes
# --------------------------------------------------------------------------

def m_stems(G, M, flags):
    cap, xh, fig = M["cap"], M["xh"], M["fig"]
    out = {}
    H = G("H")
    ws = []
    for y in lin(0, cap, [0.15, 0.22, 0.30, 0.70, 0.78, 0.85]):
        iv = H.hslice(y + EPS)
        if len(iv) == 2:
            ws += [ln(iv[0]), ln(iv[1])]
    out["H_stem"] = med(ws)
    if spread(ws) > 0.03:
        flags.append(f"H stems vary {spread(ws):.0%} over height")

    l_ = G("l")
    top = l_.bounds[3]
    ws = [ln(iv[0]) for y in lin(0, top, [0.4, 0.5, 0.6, 0.7])
          if len(iv := l_.hslice(y + EPS)) == 1]
    out["l_stem"] = med(ws)

    n = G("n")
    wl, wr = [], []
    for y in lin(0, xh, [0.2, 0.28, 0.36, 0.44]):
        iv = n.hslice(y + EPS)
        if len(iv) == 2:
            wl.append(ln(iv[0]))
            wr.append(ln(iv[1]))
    out["n_stem"] = med(wl)
    out["n_stem_r"] = med(wr)

    one = G("1")
    ws = [ln(iv[0]) for y in lin(0, fig, [0.3, 0.4, 0.5])
          if len(iv := one.hslice(y + EPS)) == 1]
    out["one_stem"] = med(ws)
    return out


def m_horizontals(G, M, flags):
    cap = M["cap"]
    out = {}
    # H crossbar
    H = G("H")
    iv = H.hslice(0.25 * cap + EPS)
    gx0, gx1 = iv[0][1], iv[1][0]
    ts, cs = [], []
    for x in lin(gx0, gx1, [0.15, 0.3, 0.5, 0.7, 0.85]):
        bars = [s for s in H.vslice(x) if ln(s) < 0.5 * cap]
        if len(bars) == 1:
            ts.append(ln(bars[0]))
            cs.append(ctr(bars[0]))
    out["H_bar"] = med(ts)
    out["H_bar_spread"] = spread(ts)
    out["H_bar_centre"] = med(cs)
    if spread(ts) > 0.03:
        flags.append(f"H crossbar thickness varies {spread(ts):.0%} along its length "
                     f"(min {min(ts):.0f}, max {max(ts):.0f})")

    # E arms
    E = G("E")
    x0, _, x1, _ = E.bounds
    sb = E.hslice(0.25 * cap + EPS)[0][1]
    xs = np.linspace(sb + 0.5, x1 - 0.5, 240)
    three = [x for x in xs if len(E.vslice(x)) == 3]
    arms = {"bot": [], "mid": [], "top": []}
    mids = []
    if three:
        xe = max(three)
        for x in lin(sb, xe, [0.3, 0.45, 0.6]):
            iv = E.vslice(x)
            if len(iv) == 3:
                arms["bot"].append(ln(iv[0]))
                arms["mid"].append(ln(iv[1]))
                arms["top"].append(ln(iv[2]))
                mids.append(ctr(iv[1]))
    for k, v in arms.items():
        if spread(v) > 0.03:
            flags.append(f"E {k} arm thickness varies {spread(v):.0%} near the stem")
    out["E_top"] = med(arms["top"])
    out["E_mid"] = med(arms["mid"])
    out["E_bot"] = med(arms["bot"])
    out["E_mid_centre"] = med(mids)

    # T bar (left half, clear of the stem)
    T = G("T")
    tx0 = T.bounds[0]
    st = T.hslice(0.5 * cap + EPS)
    st = min(st, key=lambda s: abs(ctr(s) - ctr(T.bounds[0::2])))
    ts = [ln(T.vslice(x)[-1]) for x in lin(tx0, st[0], [0.2, 0.4, 0.6])]
    out["T_bar"] = med(ts)
    if spread(ts) > 0.04:
        flags.append(f"T bar tapers {spread(ts):.0%}")

    # 7 bar: topmost interval, left part
    S7 = G("7")
    a, b, c, d = S7.bounds
    ts = []
    for x in lin(a, c, np.linspace(0.1, 0.6, 11)):
        iv = S7.vslice(x)
        if iv and iv[-1][1] > d - 0.02 * cap:
            ts.append(ln(iv[-1]))
    # minimum: a beak (dropped left end) or the leg junction only lengthen the cut
    out["7_bar"] = min(ts)
    if spread(ts) > 0.05:
        flags.append(f"7 bar: vertical cut ranges {min(ts):.0f}-{max(ts):.0f} u along the bar "
                     f"(beak/terminal or leg junction); thinnest cut used")

    # 2 base: bottommost interval, right part
    S2 = G("2")
    a, b, c, d = S2.bounds
    ts = []
    for x in lin(a, c, np.linspace(0.45, 0.85, 9)):
        iv = S2.vslice(x)
        if iv and iv[0][0] < b + 1:
            ts.append(ln(iv[0]))
    out["2_base"] = min(ts)
    if spread(ts) > 0.05:
        flags.append(f"2 base: vertical cut ranges {min(ts):.0f}-{max(ts):.0f} u along the base; "
                     f"thinnest cut used")
    return out


# --------------------------------------------------------------------------
# 2. diagonals
# --------------------------------------------------------------------------

def stroke_fit(o, ys, pick):
    """Fit both edges of a straight stroke from horizontal slices, then cut
    perpendicular to the mean edge direction through each slice midpoint."""
    pts = []
    for y in ys:
        s = pick(o.hslice(y + EPS))
        if s:
            pts.append((y + EPS, s[0], s[1]))
    if len(pts) < 3:
        return None
    Y = np.array([p[0] for p in pts])
    A = np.array([p[1] for p in pts])
    B = np.array([p[2] for p in pts])
    ma, ca = np.polyfit(Y, A, 1)
    mb, cb = np.polyfit(Y, B, 1)
    resid = max(np.abs(np.polyval([ma, ca], Y) - A).max(),
                np.abs(np.polyval([mb, cb], Y) - B).max())
    m = 0.5 * (ma + mb)
    nperp = np.array([1.0, -m]) / math.hypot(1, m)
    ts = []
    for y, a, b in pts:
        P = np.array([0.5 * (a + b), y])
        s = interval_at(o.slice(P, nperp), 0.0)
        if s:
            ts.append(ln(s))
    return dict(t=med(ts), t_spread=spread(ts), t_first=ts[0] if ts else None,
                t_last=ts[-1] if ts else None, y_first=pts[0][0], y_last=pts[-1][0],
                angle=math.degrees(math.atan(m)),          # from vertical, + leans right
                edge_div=math.degrees(math.atan(mb) - math.atan(ma)),
                resid=float(resid), hcut=float(np.median(B - A)), n=len(ts))


def m_diagonals(G, M, flags):
    cap, fig = M["cap"], M["fig"]
    out = {}
    two = lambda i: (lambda iv: iv[i] if len(iv) == 2 else None)
    one = lambda iv: iv[0] if len(iv) == 1 else None
    V = G("V")
    out["V_l"] = stroke_fit(V, lin(0, cap, [0.3, 0.38, 0.46, 0.54, 0.62, 0.7]), two(0))
    out["V_r"] = stroke_fit(V, lin(0, cap, [0.3, 0.38, 0.46, 0.54, 0.62, 0.7]), two(1))
    X = G("X")
    lo = lin(0, cap, [0.08, 0.14, 0.2, 0.26, 0.32])
    hi = lin(0, cap, [0.68, 0.74, 0.8, 0.86, 0.92])
    out["X_sl_lo"] = stroke_fit(X, lo, two(0))     # '/' lower-left
    out["X_bs_lo"] = stroke_fit(X, lo, two(1))     # '\' lower-right
    out["X_bs_hi"] = stroke_fit(X, hi, two(0))     # '\' upper-left
    out["X_sl_hi"] = stroke_fit(X, hi, two(1))     # '/' upper-right
    out["7_leg"] = stroke_fit(G("7"), lin(0, fig, [0.08, 0.17, 0.26, 0.35, 0.44, 0.53]), one)
    out["Z_diag"] = stroke_fit(G("Z"), lin(0, cap, [0.3, 0.38, 0.46, 0.54, 0.62, 0.7]), one)
    out["N_diag"] = stroke_fit(G("N"), lin(0, cap, np.linspace(0.25, 0.75, 11)),
                               lambda iv: iv[1] if len(iv) == 3 else None)
    for k, v in out.items():
        if v is None:
            flags.append(f"{k}: could not isolate the stroke")
            continue
        if v["resid"] > 0.01 * cap:
            flags.append(f"{k} is curved or kinked (edge fit residual {v['resid']:.0f} u)")
        if abs(v["edge_div"]) > 1.5:
            flags.append(f"{k} tapers (edges diverge {v['edge_div']:+.1f} deg)")
    return out


# --------------------------------------------------------------------------
# 3. bowls: side / top thickness, 45-degree corner, chamfer legs
# --------------------------------------------------------------------------

def _chamfer(lines, cx, cy, sx, sy):
    """Longest straight non-axial line in quadrant (sx, sy) that cuts the
    corner (i.e. runs from the top/bottom flat to the side); among several,
    the one furthest out along the corner normal."""
    best = None
    for p0, p1 in lines:
        if not all(sx * (p[0] - cx) > 0 and sy * (p[1] - cy) > 0 for p in (p0, p1)):
            continue
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        L = math.hypot(dx, dy)
        if L < 1:
            continue
        ang = math.degrees(math.atan2(abs(dy), abs(dx)))
        if not 15 < ang < 75 or dx * dy * sx * sy >= 0:
            continue
        mid = np.array([(p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2])
        nrm = np.array([-dy, dx]) / L
        if nrm @ np.array([sx, sy]) < 0:
            nrm = -nrm
        proj = mid @ np.array([sx, sy])
        key = (proj, L)
        if best is None or key > best[0]:
            best = (key, dict(len=L, dx=abs(dx), dy=abs(dy), angle=ang, mid=mid, nrm=nrm))
    return best[1] if best else None


def _extent(lines, pts, sx, sy):
    """Corner extent: distance from the contour's x/y extremes to the end of
    the straight top (bottom) flat and the straight side flat."""
    X0, Y0 = pts.min(0)
    X1, Y1 = pts.max(0)
    xe = X1 if sx > 0 else X0
    ye = Y1 if sy > 0 else Y0
    hx = vy = None
    for p0, p1 in lines:
        if abs(p0[1] - ye) < 1 and abs(p1[1] - ye) < 1 and abs(p1[0] - p0[0]) > 1:
            e = max(sx * p0[0], sx * p1[0])
            hx = min(hx, sx * xe - e) if hx is not None else sx * xe - e
        if abs(p0[0] - xe) < 1 and abs(p1[0] - xe) < 1 and abs(p1[1] - p0[1]) > 1:
            e = max(sy * p0[1], sy * p1[1])
            vy = min(vy, sy * ye - e) if vy is not None else sy * ye - e
    return hx, vy


def m_bowl(G, ch, M, flags):
    o = G(ch)
    outer, holes, islands = o.classify_contours()
    if not holes:
        flags.append(f"{ch}: no counter found")
        return None
    P = o.polys[outer]
    X0, Y0 = P.min(0)
    X1, Y1 = P.max(0)
    cx, cy = (X0 + X1) / 2, (Y0 + Y1) / 2
    hv = o.hslice(cy + EPS)
    vv = o.vslice(cx + EPS)
    side = 0.5 * (ln(hv[0]) + ln(hv[-1]))
    topt, bott = ln(vv[-1]), ln(vv[0])
    out = dict(side=side, top=topt, bottom=bott, width=X1 - X0, height=Y1 - Y0)
    HP = np.concatenate([o.polys[i] for i in holes])
    hx0, hy0 = HP.min(0)
    hx1, hy1 = HP.max(0)
    hcx, hcy = (hx0 + hx1) / 2, (hy0 + hy1) / 2
    olines = o.contour_lines(outer)
    ilines = [l for i in holes for l in o.contour_lines(i)]
    corners = {}
    QN = {(1, 1): "NE", (-1, 1): "NW", (-1, -1): "SW", (1, -1): "SE"}
    for q in QN:
        sx, sy = q
        oc = _chamfer(olines, cx, cy, sx, sy)
        ic = _chamfer(ilines, hcx, hcy, sx, sy)
        if oc is not None:
            nrm, anchor = oc["nrm"], oc["mid"]
        else:
            nrm = np.array([sx, sy]) / SQ2
            pts, _ = o.support([outer], nrm, tol=0.05)
            anchor = pts.mean(0)
        iv = o.slice(anchor + 2 * nrm, -nrm)
        t_slice = ln(iv[0]) if iv else None
        if t_slice is not None and t_slice > 1.5 * side:
            t_slice = None          # cut ran into a slash/dot: not a clean corner
        # inner anchor: the counter's own chamfer midpoint, else its 45-degree
        # support point; corner thickness = its distance to the outer contour
        if ic is not None:
            ianchor = ic["mid"]
        else:
            ipts, _ = o.support(holes, -np.array([-sx, -sy]) / SQ2, tol=0.05)
            ianchor = ipts.mean(0)
        t_in = dist_to_poly(ianchor, P)
        t_lines = None
        if oc is not None and ic is not None and abs(oc["angle"] - ic["angle"]) < 3:
            # both contours chamfered and parallel: perpendicular distance
            # between the outer and inner chamfer lines
            t_lines = abs((oc["mid"] - ic["mid"]) @ oc["nrm"])
        if t_slice is None:
            t = None
        elif t_lines is not None:
            t = t_lines
            if abs(t_in - t_lines) > 0.03 * t_lines:
                flags.append(f"{ch} {QN[q]}: inner and outer chamfers are offset; chamfer-line "
                             f"distance {t_lines:.0f} u used, nearest outer point to the inner "
                             f"chamfer is {t_in:.0f} u away")
        else:
            t = t_in
        ohx, ovy = _extent(olines, P, sx, sy)
        ihx, ivy = _extent(ilines, HP, sx, sy)
        corners[QN[q]] = dict(t=t, t_slice=t_slice, t_in=t_in, t_lines=t_lines, outer=oc, inner=ic, outer_ext=(ohx, ovy), inner_ext=(ihx, ivy))
    good = [c for c in corners.values() if c["t"] is not None]
    out["corner_t"] = med([c["t"] for c in good])
    out["corners"] = corners
    nch = sum(1 for c in corners.values() if c["outer"] is not None)
    out["chamfered"] = nch
    if nch:
        cs = [c for c in corners.values() if c["outer"] is not None]
        out["ch_angle"] = med([c["outer"]["angle"] for c in cs])
        out["ch_out_dx"] = med([c["outer"]["dx"] for c in cs])
        out["ch_out_dy"] = med([c["outer"]["dy"] for c in cs])
        ci = [c for c in cs if c["inner"] is not None]
        out["ch_in_dx"] = med([c["inner"]["dx"] for c in ci]) if ci else None
        out["ch_in_dy"] = med([c["inner"]["dy"] for c in ci]) if ci else None
    oe = [c["outer_ext"] for c in corners.values() if None not in c["outer_ext"]]
    ie = [c["inner_ext"] for c in corners.values() if None not in c["inner_ext"]]
    out["ext_out"] = (med([e[0] for e in oe]), med([e[1] for e in oe])) if oe else None
    out["ext_in"] = (med([e[0] for e in ie]), med([e[1] for e in ie])) if ie else None
    out["n_holes"], out["n_islands"] = len(holes), len(islands)
    return out


# --------------------------------------------------------------------------
# 4. overshoot
# --------------------------------------------------------------------------

def m_overshoot(G, M):
    cap, xh, fig = M["cap"], M["xh"], M["fig"]
    out = {}
    for ch in "O0S8C3":
        x0, y0, x1, y1 = G(ch).bounds
        ref = fig if ch in DIGITS else cap
        out[ch] = dict(top=y1 - ref, bot=-y0, top_vs_cap=y1 - cap)
    x0, y0, x1, y1 = G("o").bounds
    out["o"] = dict(top=y1 - xh, bot=-y0)
    for ch in "HEZ":
        out[ch + "_flat_bot"] = G(ch).bounds[1]
    return out


# --------------------------------------------------------------------------
# 5. optical centre and bowl widths
# --------------------------------------------------------------------------

def _middle_interval(o, xs):
    """Middle interval from the first vertical slice that has exactly three."""
    for x in xs:
        iv = o.vslice(x + EPS)
        if len(iv) == 3:
            return iv[1], x
    return None, None


def _bowl_widths(o, split, lo, hi):
    def ext(y0, y1):
        best = 0
        for y in np.linspace(y0, y1, 60):
            iv = o.hslice(y + EPS)
            if iv:
                best = max(best, iv[-1][1] - iv[0][0])
        return best
    up, dn = ext(split, hi - 1), ext(lo + 1, split)
    return up, dn


def m_centres(G, M, H_bar_centre, E_mid_centre, hbar, flags):
    cap = M["cap"]
    out = dict(H=H_bar_centre, E=E_mid_centre)
    A = G("A")
    a, b, c, d = A.bounds
    bars = [s for s in A.vslice((a + c) / 2 + EPS) if s[1] < 0.9 * cap and s[0] > 0.02 * cap]
    out["A"] = ctr(bars[0]) if bars else None
    out["A_bar"] = ln(bars[0]) if bars else None
    res = {}
    for ch, fr in [("8", [0.5, 0.45, 0.55, 0.4, 0.6]),
                   ("S", [0.5, 0.45, 0.55, 0.4, 0.6])]:
        o = G(ch)
        a, b, c, d = o.bounds
        iv, x = _middle_interval(o, lin(a, c, fr))
        res[ch] = iv
        out[ch] = ctr(iv) if iv else None
        out[ch + "_t"] = ln(iv) if iv else None
        if iv is None:
            flags.append(f"{ch}: no 3-interval vertical slice for the junction")
    # 3: junction = centre of the middle stroke in vertical slices that cut
    # the 3 exactly three times (bottom stroke, junction, top stroke); median
    # over x in 20-85 % of the width.  Right of a round 3's tongue the slice
    # cuts four times (the two bowls part) and is ignored; for a flat-topped
    # (Z-type) 3 the three-cut zone is where the diagonal lands on the lower
    # bowl.  Cuts thinner than 0.7 x the H crossbar are grazes of a rounded
    # tongue tip and are ignored.
    o = G("3")
    a, b, c, d = o.bounds
    cands = []
    for x in lin(a, c, np.linspace(0.2, 0.85, 66)):
        iv = o.vslice(x + EPS)
        if len(iv) == 3 and ln(iv[1]) >= 0.7 * hbar:
            cands.append(iv[1])
    iv = None
    if cands:
        cm = med([ctr(s_) for s_ in cands])
        iv = (cm - 0.5 * med([ln(s_) for s_ in cands]), cm + 0.5 * med([ln(s_) for s_ in cands]))
    res["3"] = iv
    out["3"] = ctr(iv) if iv else None
    out["3_t"] = ln(iv) if iv else None
    if iv is None:
        flags.append("3: no three-cut vertical slice for the junction")
    # top form: a diagonal from the top bar into the lower bowl ("Z-type",
    # flat-topped 3) or an upper bowl with a vertical-ish right side
    rs = stroke_fit(o, lin(0, d, [0.62, 0.66, 0.70, 0.74, 0.78]),
                    lambda iv: iv[-1] if iv else None)
    out["3_top"] = "diagonal" if rs and abs(rs["angle"]) > 20 else "bowl"
    B = G("B")
    a, b, c, d = B.bounds
    sb = B.hslice(0.25 * cap + EPS)[0][1]
    iv, x = _middle_interval(B, lin(sb, c, [0.3, 0.2, 0.4, 0.5]))
    res["B"] = iv
    out["B"] = ctr(iv) if iv else None
    widths = {}
    for ch in "8B3S":
        o = G(ch)
        iv = res[ch]
        if iv is None:
            continue
        up, dn = _bowl_widths(o, ctr(iv), o.bounds[1], o.bounds[3])
        widths[ch] = dict(upper=up, lower=dn, ratio=up / dn)
    out["widths"] = widths
    return out


# --------------------------------------------------------------------------
# 6. figures
# --------------------------------------------------------------------------

def gsub_map(font, tag):
    if "GSUB" not in font:
        return {}
    t = font["GSUB"].table
    m = {}
    if not t.FeatureList:
        return m
    for fr in t.FeatureList.FeatureRecord:
        if fr.FeatureTag != tag:
            continue
        for li in fr.Feature.LookupListIndex:
            lk = t.LookupList.Lookup[li]
            for st in lk.SubTable:
                if lk.LookupType == 7:
                    st = st.ExtSubTable
                if hasattr(st, "mapping"):
                    m.update(st.mapping)
                elif hasattr(st, "alternates"):
                    m.update({k: v[0] for k, v in st.alternates.items()})
    return m


def classify_zero(o):
    outer, holes, islands = o.classify_contours()
    if len(holes) >= 2:
        return "slashed (connected)"
    if not islands:
        return "plain"
    kinds = []
    for i in islands:
        p = o.polys[i]
        c = p - p.mean(0)
        w, v = np.linalg.eigh(np.cov(c.T))
        elong = math.sqrt(w[1] / max(w[0], 1e-9))
        ang = math.degrees(math.atan2(v[1, 1], v[0, 1])) % 180
        if elong < 2:
            kinds.append("dotted")
        elif 80 < ang < 100:
            kinds.append("barred (vertical)")
        else:
            kinds.append(f"slashed (floating, {ang:.0f} deg)")
    return ", ".join(kinds)


def m_figures(font, G, M, flags):
    cap, fig = M["cap"], M["fig"]
    out = {}
    names = [G.name(c) for c in DIGITS]
    adv = [G.gs[n].width for n in names]
    out["default_tabular"] = len(set(adv)) == 1
    tnum = gsub_map(font, "tnum")
    pnum = gsub_map(font, "pnum")
    if out["default_tabular"]:
        out["tab_adv"] = adv[0]
        out["has_pnum"] = any(n in pnum for n in names)
        tab_names = names
    else:
        tab_names = [tnum.get(n, n) for n in names]
        tadv = {G.gs[n].width for n in tab_names}
        out["tab_adv"] = tadv.pop() if len(tadv) == 1 else None
        out["has_tnum"] = any(n in tnum for n in names)
        out["prop_adv"] = (min(adv), max(adv))
    out["fig_h"] = fig
    out["fig_h_5"] = G("5").bounds[3]

    # 1: stem, flag, foot (default glyph)
    one = G("1")
    stem = [s for s in one.hslice(0.45 * fig + EPS)]
    stem = stem[0] if len(stem) == 1 else None
    if stem:
        sw = ln(stem)
        left = []
        for y in np.linspace(0.5 * fig, fig - 1, 80):
            iv = one.hslice(y)
            if iv:
                left.append((iv[0][0], y))
        lx, ly = min(left)
        flag_len = stem[0] - lx
        out["1_flag"] = flag_len > 0.03 * cap
        out["1_flag_len"] = flag_len
        out["1_flag_tip_h"] = ly
        bot = one.hslice(0.02 * fig)
        foot = (bot[-1][1] - bot[0][0]) if bot else 0
        out["1_foot"] = foot > 1.8 * sw
        out["1_foot_w"] = foot
        out["1_stem_w"] = sw
    # 4: closed counter?
    four = G("4")
    _, holes, _ = four.classify_contours()
    out["4_closed"] = bool(holes)
    # 7: crossed?
    s7 = G("7")
    legw = [ln(iv[0]) for y in lin(0, fig, [0.15, 0.25]) if len(iv := s7.hslice(y + EPS)) == 1]
    # a crossbar runs through the leg: one interval much wider than the leg
    wmax = max(max(ln(s) for s in iv) for y in np.linspace(0.3 * fig, 0.6 * fig, 40)
               if (iv := s7.hslice(y)))
    out["7_crossed"] = bool(legw) and wmax > 2.0 * med(legw)
    # beak: the bar's left end drops below the bar as a separate stroke
    out["7_beak"] = any(len(s7.hslice(y)) >= 2 and s7.hslice(y)[0][1] < ctr(s7.bounds[0::2])
                        for y in np.linspace(0.62 * fig, 0.75 * fig, 6))
    # 0
    out["0_default"] = classify_zero(G("0"))
    zmap = gsub_map(font, "zero")
    zn = G.name("0")
    if zn in zmap:
        out["0_zero_feature"] = classify_zero(Outline.from_glyphset(G.gs, zmap[zn]))
    else:
        out["0_zero_feature"] = None
    alts = [n for n in G.gs.keys() if n.lower().startswith(("zero.", "zero_")) and "." in n]
    out["0_alts"] = sorted(alts)[:6]
    return out


# --------------------------------------------------------------------------
# driver
# --------------------------------------------------------------------------

def measure_face(face):
    font = instance(face.file, dict(face.loc))
    G = Glyphs(font)
    flags = []
    R = dict(family=face.family, style=face.style, group=face.group, file=face.file,
             loc=dict(face.loc), flags=flags)
    M = m_metrics(font, G)
    R["metrics"] = M
    for key, fn in [("stems", lambda: m_stems(G, M, flags)),
                    ("horiz", lambda: m_horizontals(G, M, flags)),
                    ("diag", lambda: m_diagonals(G, M, flags)),
                    ("O", lambda: m_bowl(G, "O", M, flags)),
                    ("zero", lambda: m_bowl(G, "0", M, flags)),
                    ("o", lambda: m_bowl(G, "o", M, flags)),
                    ("overshoot", lambda: m_overshoot(G, M)),
                    ("figures", lambda: m_figures(font, G, M, flags))]:
        try:
            R[key] = fn()
        except Exception as e:  # keep going; record the failure
            R[key] = None
            flags.append(f"{key}: measurement failed ({e!r})")
            traceback.print_exc()
    try:
        R["centres"] = m_centres(G, M, R["horiz"]["H_bar_centre"], R["horiz"]["E_mid_centre"],
                                 R["horiz"]["H_bar"], flags)
    except Exception as e:
        R["centres"] = None
        flags.append(f"centres: measurement failed ({e!r})")
        traceback.print_exc()
    R["monospaced"] = len({G.gs[G.name(c)].width for c in "HOil1mM0W.,"}) == 1
    return R


# --------------------------------------------------------------------------
# Roboto Flex GRAD
# --------------------------------------------------------------------------

def grad_study():
    from fontTools.ttLib import TTFont
    vf = TTFont(f"fonts/{ROBOTO_FLEX}")
    axes = {a.axisTag: (a.minValue, a.defaultValue, a.maxValue) for a in vf["fvar"].axes}
    gmin, gdef, gmax = axes["GRAD"]
    grads = sorted({gmin, gmin / 2, 0.0, gmax / 2, gmax})
    out = dict(axes=axes, grads=grads, by_wght={})
    for w in (400, 700):
        rows = []
        hmtx = {}
        for g in grads:
            f = instance(ROBOTO_FLEX, {"wght": w, "GRAD": g})
            G = Glyphs(f)
            M = m_metrics(f, G)
            fl = []
            st = m_stems(G, M, fl)
            hz = m_horizontals(G, M, fl)
            O = m_bowl(G, "O", M, fl)
            o = m_bowl(G, "o", M, fl)
            Hb = G("H").bounds
            rows.append(dict(GRAD=g, H_stem=st["H_stem"], n_stem=st["n_stem"], l_stem=st["l_stem"],
                             H_bar=hz["H_bar"], E_mid=hz["E_mid"], O_side=O["side"], O_top=O["top"],
                             o_side=o["side"], o_top=o["top"], cap=M["cap"], xh=M["xh"],
                             H_xmin=Hb[0], H_xmax=Hb[2]))
            hmtx[g] = dict(f["hmtx"].metrics)
        base = hmtx[0.0]
        changed = {g: sorted(n for n in base if hmtx[g][n][0] != base[n][0]) for g in grads}
        lsb_changed = {g: sum(1 for n in base if hmtx[g][n][1] != base[n][1]) for g in grads}
        slopes = {}
        for k in ["H_stem", "n_stem", "l_stem", "H_bar", "E_mid", "O_side", "O_top", "o_side", "o_top",
                  "cap", "xh", "H_xmin"]:
            xs = np.array([r["GRAD"] for r in rows])
            ys = np.array([r[k] for r in rows], dtype=float)
            s, c0 = np.polyfit(xs, ys, 1)
            res = float(np.abs(np.polyval([s, c0], xs) - ys).max())
            # piecewise: negative and positive sides separately
            neg = [(r["GRAD"], r[k]) for r in rows if r["GRAD"] <= 0]
            pos = [(r["GRAD"], r[k]) for r in rows if r["GRAD"] >= 0]
            sn = np.polyfit(*zip(*neg), 1)[0] if len(neg) > 1 else None
            sp = np.polyfit(*zip(*pos), 1)[0] if len(pos) > 1 else None
            slopes[k] = dict(slope=float(s), resid=res, slope_neg=float(sn), slope_pos=float(sp))
        out["by_wght"][w] = dict(rows=rows, slopes=slopes,
                                 adv_changed={str(g): len(v) for g, v in changed.items()},
                                 adv_changed_examples={str(g): v[:8] for g, v in changed.items()},
                                 lsb_changed={str(g): v for g, v in lsb_changed.items()},
                                 n_glyphs=len(base))
    hv = vf["HVAR"] if "HVAR" in vf else None
    out["has_HVAR"] = hv is not None
    return out


def main():
    only = sys.argv[1:]
    results = []
    for face in FACES:
        if only and not any(o.lower() in face.label.lower() for o in only):
            continue
        print("measuring", face.label, file=sys.stderr)
        results.append(measure_face(face))
    payload = dict(faces=results)
    if not only:
        print("Roboto Flex GRAD study", file=sys.stderr)
        payload["roboto_flex"] = grad_study()
    out = "results.json" if not only else "results_partial.json"
    with open(out, "w") as fh:
        json.dump(payload, fh, indent=1, default=_json_default)
    print("wrote", out, file=sys.stderr)


def _json_default(o):
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    if isinstance(o, tuple):
        return list(o)
    raise TypeError(type(o))


if __name__ == "__main__":
    main()
