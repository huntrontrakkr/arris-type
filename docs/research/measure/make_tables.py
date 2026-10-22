#!/usr/bin/env python
"""Turn results.json (from measure_fonts.py) into markdown tables.

  uv run --no-project --with numpy python make_tables.py > tables.md
"""

from __future__ import annotations

import json
import math
import statistics


R = json.load(open("results.json"))
FACES = R["faces"]
SQ2 = math.sqrt(2)


def f(v, d=2):
    return "–" if v is None else f"{v:.{d}f}"


def pct(v, ref, d=1):
    return "–" if v is None or not ref else f"{100 * v / ref:.{d}f}"


def rat(v, ref, d=2):
    return "–" if v is None or not ref else f"{v / ref:.{d}f}"


def name(r, short=False):
    s = "R" if r["style"] == "Regular" else "B"
    return f"{r['family']} {s}"


def table(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "|".join("---" for _ in head) + "|"]
    out += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join(out) + "\n"


def bad(r, key):
    """Diagonal flagged as curved/kinked?"""
    return any(fl.startswith(key + " is curved") for fl in r["flags"])


def corner_kind(b):
    if b is None:
        return "–"
    if b.get("chamfered") == 4:
        return f"chamfer {b['ch_angle']:.0f}°"
    if b.get("ext_out"):
        return "round corner"
    return "curved"


GROUPS = {
    "neutral": ["Roboto", "Inter", "Jost", "Montserrat", "Barlow", "Atkinson Hyperlegible", "B612"],
    "chamfer": ["Chakra Petch", "Oxanium", "Orbitron", "Aldrich", "Michroma", "Share Tech Mono",
                "Tomorrow", "Saira", "Rajdhani", "Turret Road", "Bai Jamjuree"],
    "true chamfer (45°/53° cuts)": ["Chakra Petch", "Tomorrow", "Turret Road"],
    "mono": ["B612 Mono", "JetBrains Mono", "IBM Plex Mono", "Roboto Mono", "Space Mono",
             "Red Hat Mono"],
}


# ---------------------------------------------------------------------------
def t_metrics():
    rows, rows2 = [], []
    for r in FACES:
        if r["style"] != "Regular":
            continue
        M = r["metrics"]
        cap, upm = M["cap"], M["upm"]
        rows.append([r["family"], upm, f"{M['cap']:.0f} ({M['os2_cap']})", f"{M['xh']:.0f} ({M['os2_x']})",
                     f"{M['asc']:.0f}", f"{M['desc']:.0f}",
                     f"{M['typo_asc']} / {M['typo_desc']} / {M['typo_gap']}",
                     f"{M['hhea_asc']} / {M['hhea_desc']} / {M['hhea_gap']}",
                     f"{M['win_asc']} / {M['win_desc']}", "yes" if M["use_typo"] else "no"])
        hh = M["hhea_asc"] - M["hhea_desc"] + M["hhea_gap"]
        ty = M["typo_asc"] - M["typo_desc"] + M["typo_gap"]
        rows2.append([r["family"], rat(cap, upm, 3), rat(M["xh"], cap, 3), rat(M["asc"], cap, 3),
                      rat(-M["desc"], cap, 3), rat(M["fig"], cap, 3),
                      rat(hh, upm, 3), rat(ty, upm, 3), rat(M["win_asc"] + M["win_desc"], upm, 3),
                      rat(M["hhea_asc"], cap, 3), rat(-M["hhea_desc"], cap, 3)])
    a = table(["Font", "UPM", "cap measured (OS/2)", "x-height measured (OS/2)", "ascender (bdhkl)",
               "descender (p)", "typo asc / desc / gap", "hhea asc / desc / gap", "win asc / desc",
               "USE_TYPO"], rows)
    b = table(["Font", "cap/UPM", "x/cap", "asc/cap", "desc/cap", "figures/cap", "hhea line/UPM",
               "typo line/UPM", "win total/UPM", "hhea asc/cap", "hhea desc/cap"], rows2)
    return a, b


def t_stems():
    rows = []
    for r in FACES:
        s, h, M = r["stems"], r["horiz"], r["metrics"]
        hs = s["H_stem"]
        hor = [h[k] for k in ("H_bar", "E_top", "E_mid", "E_bot", "T_bar")]
        ver = [s[k] for k in ("H_stem", "l_stem", "n_stem")]
        rows.append([name(r), f"{hs:.0f}", pct(hs, M["cap"]), rat(s["l_stem"], hs), rat(s["n_stem"], hs),
                     rat(s["one_stem"], hs), rat(h["H_bar"], hs), rat(h["E_top"], hs), rat(h["E_mid"], hs),
                     rat(h["E_bot"], hs), rat(h["T_bar"], hs), rat(h["7_bar"], hs), rat(h["2_base"], hs),
                     f"{statistics.mean(hor) / statistics.mean(ver):.2f}"])
    return table(["Face", "H stem (u)", "H stem % cap", "l", "n", "1", "H bar (= H/V)", "E top", "E mid",
                  "E bot", "T bar", "7 bar", "2 base", "mean horiz / mean vert"], rows)


def t_diag():
    rows = []
    for r in FACES:
        d, hs = r["diag"], r["stems"]["H_stem"]

        def cell(key, keys=None):
            vs = [d[k] for k in (keys or [key]) if d.get(k)]
            if not vs:
                return "–"
            t = statistics.mean(v["t"] for v in vs)
            ang = statistics.mean(abs(v["angle"]) for v in vs)
            mark = "†" if any(bad(r, k) for k in (keys or [key])) else ""
            return f"{t / hs:.2f} @{ang:.0f}°{mark}"

        allv = [d[k]["t"] / hs for k in ("V_l", "V_r", "X_sl_lo", "X_bs_lo", "X_bs_hi", "X_sl_hi", "7_leg")
                if d.get(k) and not bad(r, k)]
        m = statistics.mean(allv)
        verdict = "thinner" if m < 0.97 else ("thicker" if m > 1.03 else "equal")
        vt = [d[k] for k in ("V_l", "V_r") if d.get(k)]
        # V taper: thickness at lowest sample (near the vertex) vs highest
        taper = statistics.mean(v["t_first"] / v["t_last"] for v in vt) if vt else None
        interp = 0.5 * (1 + r["horiz"]["H_bar"] / hs)
        rows.append([name(r), cell("V", ["V_l", "V_r"]), cell("X/", ["X_sl_lo", "X_sl_hi"]),
                     cell("X\\", ["X_bs_lo", "X_bs_hi"]), cell("7_leg"), cell("Z_diag"), cell("N_diag"),
                     f"{m:.2f} {verdict}", f"{interp:.2f}", f(taper)])
    return table(["Face", "V", "X /", "X \\", "7 leg", "Z", "N", "mean V,X,7 → verdict",
                  "(stem + H bar)/2 ÷ stem", "V thickness at 30% ÷ at 70% cap"], rows)


def t_bowls():
    rows = []
    for r in FACES:
        hs = r["stems"]["H_stem"]
        O, Z, o = r["O"], r["zero"], r["o"]

        def mean_st(b):
            return 0.5 * (b["side"] + b["top"])

        rows.append([name(r), corner_kind(O), rat(O["side"], hs), rat(O["top"], O["side"]),
                     rat(O["corner_t"], O["side"]), rat(O["corner_t"], mean_st(O)),
                     rat(Z["corner_t"], Z["side"]) if Z else "–",
                     rat(Z["corner_t"], mean_st(Z)) if Z else "–",
                     rat(o["corner_t"], o["side"]), rat(o["top"], o["side"]),
                     rat(o["corner_t"], mean_st(o))])
    return table(["Face", "O corner", "O side / H stem", "O top / O side", "O corner / side",
                  "O corner / mean(side,top)", "0 corner / side", "0 corner / mean", "o corner / side",
                  "o top / side", "o corner / mean"], rows)


def t_chamfer():
    rows = []
    for r in FACES:
        if r["family"] not in GROUPS["chamfer"]:
            continue
        cap = r["metrics"]["cap"]
        for g, b in (("O", r["O"]), ("0", r["zero"]), ("o", r["o"])):
            if b is None:
                continue
            kind = corner_kind(b)
            if b.get("chamfered") == 4:
                lo, li = b["ch_out_dx"], b["ch_in_dx"]
                lov, liv = b["ch_out_dy"], b["ch_in_dy"]
                tv, th = b["side"], b["top"]
                neutral = lo - (1 - 1 / SQ2) * (tv + th) if abs(b["ch_angle"] - 45) < 2 else None
                legs_o = f"{lo:.0f}" if abs(lo - lov) < 2 else f"{lo:.0f}×{lov:.0f}"
                legs_i = f"{li:.0f}" if li is not None and abs(li - liv) < 2 else f"{f(li, 0)}×{f(liv, 0)}"
                rows.append([name(r), g, kind, legs_o, pct(lo, cap), legs_i, pct(li, cap), rat(li, lo),
                             f(neutral, 0), f"{b['corner_t']:.0f}", rat(b["corner_t"], b["side"]),
                             rat(b["corner_t"], 0.5 * (tv + th))])
            elif b.get("ext_out"):
                (ho, vo), ei = b["ext_out"], b["ext_in"]
                hi, vi = ei if ei else (None, None)
                legs_o = f"{ho:.0f}" if abs(ho - vo) < 2 else f"{ho:.0f}×{vo:.0f}"
                legs_i = "–" if hi is None else (f"{hi:.0f}" if abs(hi - vi) < 2 else f"{hi:.0f}×{vi:.0f}")
                rows.append([name(r), g, kind, legs_o, pct(ho, cap), legs_i, pct(hi, cap), rat(hi, ho),
                             "–", f"{b['corner_t']:.0f}", rat(b["corner_t"], b["side"]),
                             rat(b["corner_t"], 0.5 * (b["side"] + b["top"]))])
            else:
                rows.append([name(r), g, kind, "–", "–", "–", "–", "–", "–", f"{b['corner_t']:.0f}",
                             rat(b["corner_t"], b["side"]),
                             rat(b["corner_t"], 0.5 * (b["side"] + b["top"]))])
    return table(["Face", "glyph", "corner", "outer leg (u)", "outer % cap", "inner leg (u)", "inner % cap",
                  "inner/outer", "inner leg giving corner = mean(side,top)", "corner t (u)", "corner / side",
                  "corner / mean(side,top)"], rows)


def t_overshoot():
    rows = []
    for r in FACES:
        M, os_ = r["metrics"], r["overshoot"]
        cap, xh = M["cap"], M["xh"]

        def tb(ch, ref):
            return f"{100 * os_[ch]['top'] / ref:.1f} / {100 * os_[ch]['bot'] / ref:.1f}"

        rows.append([name(r), corner_kind(r["O"]), tb("O", cap), tb("C", cap), tb("S", cap), tb("0", cap),
                     tb("8", cap), tb("3", cap), tb("o", xh)])
    return table(["Face", "bowl", "O", "C", "S", "0*", "8*", "3*", "o (% x-height)"], rows)


def t_centres():
    rows = []
    for r in FACES:
        c, cap = r["centres"], r["metrics"]["cap"]
        fig = r["metrics"]["fig"]
        w = c["widths"]
        rows.append([name(r), rat(c["H"], cap, 3), rat(c["E"], cap, 3), rat(c["A"], cap, 3),
                     rat(c["8"], fig, 3), f"{rat(c['3'], fig, 3)} {'Z' if c['3_top'] == 'diagonal' else ''}",
                     rat(c["B"], cap, 3), rat(c["S"], cap, 3),
                     f(w["8"]["ratio"]), f(w["B"]["ratio"]), f(w["S"]["ratio"]), f(w["3"]["ratio"])])
    return table(["Face", "H bar", "E mid", "A bar", "8 waist", "3 junction", "B middle", "S spine",
                  "8 up/low", "B up/low", "S up/low", "3 up/low"], rows)


def t_figures():
    rows = []
    for r in FACES:
        F, M = r["figures"], r["metrics"]
        cap, fig = M["cap"], M["fig"]
        if F["default_tabular"]:
            tab = "default"
        elif F.get("has_tnum") and F.get("tab_adv"):
            tab = "tnum"
        else:
            tab = "none"
        adv = F.get("tab_adv")
        one = []
        if F.get("1_flag"):
            one.append(f"flag {100 * F['1_flag_len'] / cap:.0f}% cap, tip at {100 * F['1_flag_tip_h'] / fig:.0f}%")
        else:
            one.append("no flag")
        if F.get("1_foot"):
            ref = adv or F["prop_adv"][1]
            one.append(f"foot {100 * F['1_foot_w'] / ref:.0f}% adv")
        else:
            one.append("no foot")
        seven = ("crossed" if F["7_crossed"] else "plain") + (", beak" if F.get("7_beak") else "")
        zero = F["0_default"]
        alt = F["0_zero_feature"] or "–"
        three = "flat top + diagonal" if r["centres"]["3_top"] == "diagonal" else "round/bowl top"
        rows.append([name(r), tab, rat(adv, cap, 3) if adv else "–",
                     "–" if F["default_tabular"] else f"{F['prop_adv'][0]}–{F['prop_adv'][1]}",
                     rat(fig, cap, 3), "; ".join(one), "closed" if F["4_closed"] else "open", seven,
                     three, zero, alt, rat(r["zero"]["width"], r["O"]["width"])])
    return table(["Face", "tabular figs", "tab adv / cap", "default (prop.) adv range (u)",
                  "figure h / cap", "1", "4", "7", "3", "0 default", "0 with `zero`",
                  "0 width / O width"], rows)


def t_grad():
    G = R["roboto_flex"]
    lo, de, hi = G["axes"]["GRAD"]
    out = [f"GRAD axis: min {lo:g}, default {de:g}, max {hi:g}.  Other axes pinned at defaults "
           f"(opsz {G['axes']['opsz'][1]:g}, wdth {G['axes']['wdth'][1]:g}; parametric axes at default). "
           f"UPM 2048.\n"]
    for w, v in G["by_wght"].items():
        rows = []
        for row in v["rows"]:
            rows.append([f"{row['GRAD']:g}", f"{row['H_stem']:.1f}", f"{row['n_stem']:.0f}",
                         f"{row['H_bar']:.0f}", f"{row['O_side']:.1f}", f"{row['O_top']:.0f}",
                         f"{row['o_side']:.0f}", f"{row['o_top']:.0f}", f"{row['H_xmin']:.0f}"])
        out.append(f"\n**wght {w}**\n\n" + table(["GRAD", "H stem", "n stem", "H bar", "O side", "O top",
                                                  "o side", "o top", "H left side bearing"], rows))
        sl = v["slopes"]
        base = {row["GRAD"]: row for row in v["rows"]}
        srow = []
        for k in ("H_stem", "n_stem", "H_bar", "O_side", "O_top", "o_side", "o_top"):
            z = base[0.0][k]
            dlo, dhi = base[lo][k] - z, base[hi][k] - z
            srow.append([k, f"{z:.1f}", f"{dlo:+.1f} ({100 * dlo / z:+.0f}%)", f"{dhi:+.1f} ({100 * dhi / z:+.0f}%)",
                         f"{sl[k]['slope_neg']:.3f}", f"{sl[k]['slope_pos']:.3f}"])
        out.append("\n" + table(["measure", "at GRAD 0 (u)", f"change at GRAD {lo:g}", f"change at GRAD {hi:g}",
                                 "u per GRAD unit, GRAD<0", "u per GRAD unit, GRAD>0"], srow))
        ch = v["adv_changed"]
        out.append(f"\nAdvance widths: {v['n_glyphs']} glyphs compared at every GRAD value; glyphs whose "
                   f"advance differs from GRAD 0: " + ", ".join(f"GRAD {float(g):g}: {n}" for g, n in ch.items()) +
                   ". Left side bearings change for ~" +
                   f"{max(v['lsb_changed'].values())} glyphs (outline grows inside a fixed advance).\n")
    return "".join(out)


def t_summary():
    def collect(fams, style, fn):
        vals = []
        for r in FACES:
            if r["family"] in fams and r["style"] == style:
                try:
                    v = fn(r)
                except (TypeError, KeyError, ZeroDivisionError):
                    v = None
                if v is not None:
                    vals.append(v)
        if not vals:
            return "–"
        return f"{statistics.median(vals):.3f} ({min(vals):.2f}–{max(vals):.2f})"

    def diag(r):
        d, hs = r["diag"], r["stems"]["H_stem"]
        v = [d[k]["t"] / hs for k in ("V_l", "V_r", "X_sl_lo", "X_bs_lo", "X_bs_hi", "X_sl_hi", "7_leg")
             if d.get(k) and not bad(r, k)]
        return statistics.mean(v)

    metrics = [
        ("H stem / cap", lambda r: r["stems"]["H_stem"] / r["metrics"]["cap"]),
        ("H bar / H stem (H/V)", lambda r: r["horiz"]["H_bar"] / r["stems"]["H_stem"]),
        ("n stem / H stem", lambda r: r["stems"]["n_stem"] / r["stems"]["H_stem"]),
        ("diagonals (V,X,7) / H stem", diag),
        ("O 45° corner / O side", lambda r: r["O"]["corner_t"] / r["O"]["side"]),
        ("O corner / mean(O side, O top)", lambda r: r["O"]["corner_t"] / (0.5 * (r["O"]["side"] + r["O"]["top"]))),
        ("O overshoot top, % cap", lambda r: 100 * r["overshoot"]["O"]["top"] / r["metrics"]["cap"]),
        ("o overshoot top, % x-height", lambda r: 100 * r["overshoot"]["o"]["top"] / r["metrics"]["xh"]),
        ("H bar centre / cap", lambda r: r["centres"]["H"] / r["metrics"]["cap"]),
        ("B middle / cap", lambda r: r["centres"]["B"] / r["metrics"]["cap"]),
        ("8 waist / figure height", lambda r: r["centres"]["8"] / r["metrics"]["fig"]),
        ("8 upper/lower width", lambda r: r["centres"]["widths"]["8"]["ratio"]),
        ("B upper/lower width", lambda r: r["centres"]["widths"]["B"]["ratio"]),
        ("tabular advance / cap", lambda r: (r["figures"]["tab_adv"] / r["metrics"]["cap"])
         if r["figures"].get("tab_adv") else None),
        ("x-height / cap", lambda r: r["metrics"]["xh"] / r["metrics"]["cap"]),
    ]
    head = ["measure"] + [f"{g} {s[0]}" for g in GROUPS for s in ("Regular", "Bold")]
    rows = []
    for label, fn in metrics:
        rows.append([label] + [collect(GROUPS[g], s, fn) for g in GROUPS for s in ("Regular", "Bold")])
    return table(head, rows)


def main():
    a, b = t_metrics()
    parts = [
        ("Summary: medians (range) per group", t_summary()),
        ("Vertical metrics (Regular), font units", a),
        ("Vertical metrics, normalised", b),
        ("Stems and horizontals (ratios to the H stem)", t_stems()),
        ("Diagonals: perpendicular thickness / H stem @ angle from vertical", t_diag()),
        ("Bowls: 45° corner thickness", t_bowls()),
        ("Corner geometry of the chamfered / squarish faces", t_chamfer()),
        ("Overshoot, top / bottom, % of cap height", t_overshoot()),
        ("Optical centres (fraction of cap height; figures of figure height) and bowl widths", t_centres()),
        ("Figures", t_figures()),
        ("Roboto Flex GRAD", t_grad()),
    ]
    for title, body in parts:
        print(f"### {title}\n\n{body}")
    print("### Flags raised by the measurement script (condensed)\n")
    print(flag_summary())


def flag_summary():
    import re
    lab = {"V_l": "V", "V_r": "V", "X_sl_lo": "X", "X_bs_lo": "X", "X_bs_hi": "X", "X_sl_hi": "X",
           "7_leg": "7 leg", "Z_diag": "Z", "N_diag": "N"}
    lines = []
    for r in FACES:
        taper, curved, other, offs = {}, set(), [], []
        for fl in r["flags"]:
            m = re.match(r"(\w+) tapers \(edges diverge ([+-][\d.]+) deg\)", fl)
            if m:
                taper.setdefault(lab[m[1]], []).append(abs(float(m[2])))
                continue
            m = re.match(r"(\w+) is curved or kinked", fl)
            if m:
                curved.add(lab[m[1]])
                continue
            if "chamfers are offset" in fl:
                offs.append(fl.split(":")[0])
                continue
            other.append(fl)
        parts = []
        if taper:
            parts.append("tapered strokes (edge divergence): " + ", ".join(
                f"{k} {min(v):.1f}–{max(v):.1f}°" if min(v) != max(v) else f"{k} {v[0]:.1f}°"
                for k, v in taper.items()))
        if curved:
            parts.append("curved/kinked, fit approximate: " + ", ".join(sorted(curved)))
        if offs:
            parts.append(f"inner/outer chamfers offset at {len(offs)} corners (chamfer-line distance reported)")
        parts += other
        if parts:
            lines.append(f"- **{name(r)}**: " + "; ".join(parts))
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
