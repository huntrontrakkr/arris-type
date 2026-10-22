"""The Arris presentation: thirty-odd designed slides set in the built fonts.

Each slide is a 1920x1080 HTML page (CSS: the variable font's three axes,
OpenType features, the Mono family's nine weights); headless Chromium
renders them to presentation/slides/NN-name.png and the whole deck to one
vector PDF, presentation/arris.pdf. Build the fonts first (README).

usage: presentation.py [name ...]      (default: every slide)
needs: Playwright's Chromium (LD_LIBRARY_PATH for its libraries if the
system lacks them)
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = Path(__import__('os').environ.get('ARRIS_BUILD', ROOT / 'build'))
OUT = ROOT / 'presentation'
W, H = 1920, 1080


def font_css():
    vf = (BUILD / 'Arris[GRAD,WTCH,wght].ttf').as_uri()
    vfi = (BUILD / 'Arris-Italic[GRAD,WTCH,wght].ttf').as_uri()
    css = [f"@font-face {{ font-family: 'Arris'; src: url('{vf}'); font-weight: 100 900; font-style: normal; }}",
           f"@font-face {{ font-family: 'Arris'; src: url('{vfi}'); font-weight: 100 900; font-style: italic; }}"]
    names = ['Thin', 'ExtraLight', 'Light', 'Regular', 'Medium', 'SemiBold', 'Bold', 'ExtraBold', 'Black']
    for i, n in enumerate(names):
        w = 100 * (i + 1)
        up = (BUILD / f'ArrisMono-{n}.ttf').as_uri()
        it = (BUILD / f'ArrisMono-{"Italic" if n == "Regular" else n + "Italic"}.ttf').as_uri()
        css.append(f"@font-face {{ font-family: 'Arris Mono'; src: url('{up}'); font-weight: {w}; font-style: normal; }}")
        css.append(f"@font-face {{ font-family: 'Arris Mono'; src: url('{it}'); font-weight: {w}; font-style: italic; }}")
    return '\n'.join(css)


BASE = """
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { width: 1920px; height: 1080px; }
body { font-family: 'Arris'; -webkit-font-smoothing: antialiased; }
.slide { position: relative; width: 1920px; height: 1080px; overflow: hidden; padding: 96px;
         background: var(--bg); color: var(--ink); page-break-after: always; break-after: page; }
.mono { font-family: 'Arris Mono'; }
.chrome { position: absolute; left: 96px; right: 96px; top: 44px; display: flex; justify-content: space-between;
          font: 500 18px/1 'Arris Mono'; letter-spacing: 0.12em; text-transform: uppercase; color: var(--dim); }
.caption { position: absolute; left: 96px; right: 96px; bottom: 44px; display: flex; justify-content: space-between;
           font: 400 18px/1.3 'Arris Mono'; color: var(--dim); }
.label { font: 500 18px/1.2 'Arris Mono'; letter-spacing: 0.1em; text-transform: uppercase; color: var(--dim); }
.accent { color: var(--accent); }
.accent2 { color: var(--accent2); }
.dim { color: var(--dim); }
/* palettes */
.night  { --bg: #0c0e10; --ink: #f1ebdd; --dim: #6f6a60; --accent: #ffb000; --accent2: #3fd6ff; --line: #24282c; }
.paper  { --bg: #f3eee3; --ink: #151412; --dim: #8c8577; --accent: #e0402a; --accent2: #2f5cd6; --line: #d9d1c1; }
.ink    { --bg: #151412; --ink: #f3eee3; --dim: #7d776b; --accent: #e0402a; --accent2: #ffb000; --line: #2d2b27; }
.amber  { --bg: #0b0a08; --ink: #ffb000; --dim: #7a5a1a; --accent: #ffd36b; --accent2: #ff6a2a; --line: #2a2214; }
.signal { --bg: #e8402a; --ink: #111; --dim: #6b1d12; --accent: #fff3e6; --accent2: #111; --line: #c43420; }
.cyan   { --bg: #06141a; --ink: #d8f6ff; --dim: #4f7480; --accent: #3fd6ff; --accent2: #ffb000; --line: #12303a; }
.violet { --bg: #17102a; --ink: #f4ecff; --dim: #7c6aa0; --accent: #ff5fae; --accent2: #7de0ff; --line: #2a2045; }
.bone   { --bg: #e9e4d8; --ink: #1d2a2e; --dim: #8a8f86; --accent: #1f7a6c; --accent2: #d0602c; --line: #cfc8b8; }
.slate  { --bg: #0d1520; --ink: #e6edf5; --dim: #5d7086; --accent: #7cf29a; --accent2: #ff79c6; --line: #1b2836; }
"""


def esc(s):
    return html.escape(s, quote=False)


SLIDES = []


def slide(name, palette, title):
    """Register a slide drawing: fn() -> (body html, caption, extra css)."""
    def deco(fn):
        SLIDES.append((name, palette, title, fn))
        return fn
    return deco


def page(i, n, name, palette, title, body, caption, css):
    cap = f'<div class="caption"><span>{caption}</span><span>Arris · {i:02d}</span></div>' if caption is not None else ''
    return (f'<section class="slide {palette} s-{name}"><div class="chrome"><span>Arris</span>'
            f'<span>{esc(title)}</span><span>{i:02d} / {n:02d}</span></div>{body}{cap}</section>', css)


# --- the slides --------------------------------------------------------------------------

@slide('cover', 'night', 'A typeface')
def cover():
    weights = [900, 700, 500, 300, 100]
    word = ''.join(f'<span style="font-weight:{w}">{c}</span>' for c, w in zip('Arris', weights))
    body = f"""
<div class="wrap">
  <div class="kicker label">A typeface grown from the figures of a watch</div>
  <h1>{word}</h1>
  <div class="row">
    <div><span class="accent">Thin → Black</span><br>Upright, Italic, Mono, Watch</div>
    <div><span class="accent">wght GRAD WTCH</span><br>Three variable axes</div>
    <div><span class="accent">2,150</span><br>characters, Latin Cyrillic Greek</div>
    <div class="clock">10:08</div>
  </div>
</div>"""
    css = """
.s-cover .wrap { position:absolute; left:96px; right:96px; top:150px; bottom:110px; display:flex; flex-direction:column; justify-content:space-between; }
.s-cover h1 { font-size: 520px; line-height: .8; letter-spacing: -0.02em; margin-left: -20px; }
.s-cover .row { display:flex; gap: 80px; align-items:flex-end; font: 400 30px/1.35 'Arris'; }
.s-cover .row > div { min-width: 340px; }
.s-cover .clock { margin-left:auto; font-size: 150px; font-weight: 600; font-variation-settings: 'WTCH' 100; color: var(--accent); line-height: .8; }
"""
    return body, 'Arris, Arris Mono, Arris Watch', css


@slide('origin', 'night', 'Where it comes from')
def origin():
    body = """
<div class="grid">
  <div class="watch">
    <div class="bezel"></div>
    <div class="face">
      <div class="date mono">WED 22 OCT</div>
      <div class="time" style="font-variation-settings:'WTCH' 100; font-weight:600">10:08</div>
      <div class="bar mono">▕████████▋ ▏ 82%</div>
    </div>
  </div>
  <div class="text">
    <div class="label accent">The Chamfer figures</div>
    <h2>Ten pixel figures on a watch face became an alphabet.</h2>
    <p>Dymaxion's figures are drawn on a twelve-row grid with two-pixel strokes, every exposed corner cut at forty-five degrees. Arris keeps every quirk they have: the 2's notch, the 3's waist, the 4's clip, the 1's flag. At SemiBold, with the watch's own stroke balance, its figures are those pixels.</p>
  </div>
</div>"""
    css = """
.s-origin .grid { position:absolute; inset: 150px 96px 120px 96px; display:grid; grid-template-columns: 760px 1fr; gap: 110px; align-items:center; }
.s-origin .watch { position:relative; width:760px; height:760px; }
.s-origin .bezel { position:absolute; inset:0; background:#1b1e21; clip-path: polygon(29% 0, 71% 0, 100% 29%, 100% 71%, 71% 100%, 29% 100%, 0 71%, 0 29%); }
.s-origin .face { position:absolute; inset:46px; background:#050607; clip-path: polygon(29% 0, 71% 0, 100% 29%, 100% 71%, 71% 100%, 29% 100%, 0 71%, 0 29%);
                  display:flex; flex-direction:column; align-items:center; justify-content:center; gap: 26px; }
.s-origin .time { font-size: 250px; line-height:.8; color: var(--accent); }
.s-origin .date { font-size: 34px; letter-spacing:.2em; color: var(--accent2); }
.s-origin .bar { font-size: 30px; color: var(--dim); line-height:1.2; }
.s-origin h2 { font-weight: 600; font-size: 68px; line-height: 1.08; margin: 26px 0 36px; }
.s-origin p { font-size: 30px; line-height: 1.5; color: #cfc8b9; max-width: 860px; }
"""
    return body, 'The figures at SemiBold with the watch balance (WTCH 100) are the watch’s pixels', css


@slide('family', 'paper', 'The family')
def family():
    rows = [("Arris", "normal", 400, "'WTCH' 0", "Nine weights, measured optics"),
            ("Arris Italic", "italic", 400, "'WTCH' 0", "Curves where the upright has chamfers; cursive forms"),
            ("Arris Watch", "normal", 600, "'WTCH' 100", "The watch's own stroke balance"),
            ("Arris Mono", "mono", 400, "", "The figures' pitch, programming ligatures"),
            ("Arris Mono Italic", "monoi", 400, "", "The Mono, slanted, its chamfers curved"),
            ("Arris[wght,GRAD,WTCH]", "normal", 300, "'WTCH' 0", "Variable: weight, grade, watch")]
    out = []
    for name, st, w, var, note in rows:
        fam = "'Arris Mono'" if st.startswith('mono') else "'Arris'"
        style = 'italic' if st in ('italic', 'monoi') else 'normal'
        out.append(f'<div class="r"><div class="n" style="font-family:{fam};font-style:{style};font-weight:{w};'
                   f'font-variation-settings:{var or "normal"}">{name}</div><div class="d label">{note}</div></div>')
    body = f'<div class="list">{"".join(out)}</div>'
    css = """
.s-family .list { position:absolute; inset: 140px 96px 110px 96px; display:flex; flex-direction:column; justify-content:space-between; }
.s-family .r { display:flex; align-items:baseline; justify-content:space-between; border-bottom: 2px solid var(--line); padding-bottom: 18px; }
.s-family .n { font-size: 104px; line-height: 1; }
.s-family .d { max-width: 520px; text-align:right; }
"""
    return body, 'Six families from one engine', css


@slide('weights', 'paper', 'Nine weights')
def weights():
    names = ['Thin', 'ExtraLight', 'Light', 'Regular', 'Medium', 'SemiBold', 'Bold', 'ExtraBold', 'Black']
    rows = ''.join(f'<div class="r"><span class="w label">{100 * (i + 1)} {n}</span>'
                   f'<span class="t" style="font-weight:{100 * (i + 1)}">Quartz glyphs vex 1234</span></div>'
                   for i, n in enumerate(names))
    body = f'<div class="stack">{rows}</div>'
    css = """
.s-weights .stack { position:absolute; inset: 130px 96px 100px 96px; display:flex; flex-direction:column; justify-content:space-between; }
.s-weights .r { display:flex; align-items:baseline; gap: 40px; }
.s-weights .w { width: 260px; flex: none; }
.s-weights .t { font-size: 86px; line-height: 1; white-space: nowrap; }
"""
    return body, 'Thin to Black; the steps stay visible at Thin, the openings at Black', css


@slide('axes', 'night', 'Three axes')
def axes():
    def band(tag, label, vals, extra=''):
        cells = ''.join(f'<div class="c"><div class="g" style="font-variation-settings:\'{tag}\' {v}{extra}">Ag8</div>'
                        f'<div class="label">{tag} {v}</div></div>' for v in vals)
        return f'<div class="band"><div class="h"><span class="accent">{tag}</span> {label}</div><div class="cells">{cells}</div></div>'
    body = (band('wght', 'Weight', [100, 233, 366, 500, 633, 766, 900]) +
            band('GRAD', 'Grade: weight without width', [-100, -66, -33, 0, 33, 66, 100], ", 'wght' 500") +
            band('WTCH', "Watch: the watch's stroke balance", [0, 17, 33, 50, 67, 83, 100], ", 'wght' 600"))
    body = f'<div class="bands">{body}</div>'
    css = """
.s-axes .bands { position:absolute; inset: 130px 96px 100px 96px; display:flex; flex-direction:column; justify-content:space-between; }
.s-axes .h { font: 500 30px/1 'Arris'; margin-bottom: 14px; }
.s-axes .cells { display:grid; grid-template-columns: repeat(7, 1fr); }
.s-axes .g { font-size: 112px; line-height: 1; }
"""
    return body, 'Grade changes weight without moving a glyph; watch moves toward the watch’s balance', css


@slide('grade', 'night', 'Grade for dark screens')
def grade():
    txt = 'Light text on a dark screen glows and looks heavier. Grade takes weight off without changing a single advance width, so the line never reflows.'
    body = f"""
<div class="two">
  <div class="p light"><div class="label">Ink on paper · GRAD 0</div><p style="font-variation-settings:'GRAD' 0">{txt}</p></div>
  <div class="p dark"><div class="label">Dark screen · GRAD 0</div><p style="font-variation-settings:'GRAD' 0">{txt}</p></div>
  <div class="p dark"><div class="label accent">Dark screen · GRAD −50</div><p style="font-variation-settings:'GRAD' -50">{txt}</p></div>
</div>"""
    css = """
.s-grade .two { position:absolute; inset: 150px 96px 120px 96px; display:grid; grid-template-columns: repeat(3, 1fr); gap: 36px; }
.s-grade .p { padding: 56px 48px; display:flex; flex-direction:column; gap: 30px; }
.s-grade .light { background:#f3eee3; color:#151412; }
.s-grade .dark { background:#000; color:#f3eee3; border: 2px solid #24282c; }
.s-grade p { font-size: 46px; line-height: 1.32; font-weight: 400; }
"""
    return body, 'The perception study recommends GRAD −50 for dark watch palettes, −25 for transflective screens in daylight', css


@slide('charset', 'paper', 'Character set')
def charset():
    rows = ['ABCDEFGHIJKLM', 'NOPQRSTUVWXYZ', 'abcdefghijklm', 'nopqrstuvwxyz', '0123456789&@?',
            'ÆØÅßÞĐŁŊŒĦ€£¥', 'АБВГДЖЗЛФЦЩЯЮ', 'ΑΓΔΘΛΞΠΣΦΨΩαβ']
    cells = ''.join(f'<div class="c">{esc(ch)}</div>' for r in rows for ch in r)
    body = f'<div class="grid">{cells}</div>'
    css = """
.s-charset .grid { position:absolute; inset: 120px 96px 96px 96px; display:grid; grid-template-columns: repeat(13, 1fr); grid-auto-rows: 1fr; }
.s-charset .c { font-size: 82px; line-height: 1; display:flex; align-items:center; justify-content:center; border-right: 1px solid var(--line); border-bottom: 1px solid var(--line); }
.s-charset .c:nth-child(13n+1) { border-left: 1px solid var(--line); }
.s-charset .c:nth-child(-n+13) { border-top: 1px solid var(--line); }
.s-charset .c:nth-child(26n+1), .s-charset .c:nth-child(26n+14) { }
"""
    return body, 'Latin with Extended-A, B and Vietnamese; Cyrillic for some forty languages; Greek', css


@slide('figures', 'night', 'The figures')
def figures():
    notes = {'1': 'the flag, notched', '2': 'the notch', '3': 'the waist', '4': 'the clip', '7': 'straightened'}
    cells = ''.join(f'<div class="f"><div class="d">{d}</div><div class="label {"accent" if d in notes else ""}">'
                    f'{notes.get(d, "&nbsp;")}</div></div>' for d in '0123456789')
    strip = ''.join(f'<span style="font-weight:{w}">1234</span>' for w in (100, 300, 500, 700, 900))
    body = (f'<div class="row">{cells}</div><div class="strip">{strip}</div>'
            f'<div class="sub">The quirks stay, at every weight.</div>')
    css = """
.s-figures .row { position:absolute; left:96px; right:96px; top: 170px; display:grid; grid-template-columns: repeat(10, 1fr); }
.s-figures .f { display:flex; flex-direction:column; align-items:center; text-align:center; }
.s-figures .d { font-size: 250px; line-height: .8; font-weight: 600; font-variation-settings: 'WTCH' 100; }
.s-figures .f .label { margin-top: 30px; }
.s-figures .strip { position:absolute; left:96px; right:96px; top: 560px; display:flex; justify-content:space-between; font-size: 130px; line-height: 1; color: var(--accent); }
.s-figures .sub { position:absolute; left:96px; bottom: 130px; font-size: 64px; font-weight: 300; }
"""
    return body, 'Arris Watch SemiBold: the figures as the watch draws them', css


@slide('pixels', 'night', 'From pixels')
def pixels():
    from arris import heritage
    rows = heritage.zone('2')
    s = 62
    rects = ''.join(f'<rect x="{x * s}" y="{y * s}" width="{s - 3}" height="{s - 3}" rx="2" fill="{"#6b5420" if c == "#" else "#171a1d"}"/>'
                    for y, r in enumerate(rows) for x, c in enumerate(r))
    geom = heritage.trace(rows)
    paths = []
    for poly in getattr(geom, 'geoms', [geom]):
        for ring in [poly.exterior, *poly.interiors]:
            pts = ' '.join(f'{x * s:.1f},{y * s:.1f}' for x, y in ring.coords)
            paths.append(f'M{pts}Z')
    svg = (f'<svg width="{9 * s}" height="{12 * s}" viewBox="-2 -2 {9 * s + 4} {12 * s + 4}">{rects}'
           f'<path d="{" ".join(paths)}" fill="none" stroke="#ffb000" stroke-width="5" fill-rule="evenodd"/></svg>')
    steps = ''.join(f'<div class="st"><div class="g" style="font-weight:{w}">2</div><div class="label">{w}</div></div>'
                    for w in (100, 300, 500, 700, 900))
    body = f"""
<div class="grid">
  <div class="px">{svg}<div class="label">The watch’s master: 9 × 12 pixels, every exposed corner cut</div></div>
  <div class="arrow accent">→</div>
  <div class="steps">{steps}</div>
</div>"""
    css = """
.s-pixels .grid { position:absolute; inset: 150px 96px 120px 96px; display:flex; align-items:center; gap: 70px; }
.s-pixels .px { display:flex; flex-direction:column; gap: 26px; width: 560px; }
.s-pixels .arrow { font-size: 160px; font-weight: 200; }
.s-pixels .steps { display:flex; gap: 34px; align-items:flex-end; }
.s-pixels .g { font-size: 250px; line-height: .8; }
.s-pixels .st .label { margin-top: 24px; }
"""
    return body, 'The pixel rule becomes a stroke engine: outer corners cut, crotches filled, at any weight', css


@slide('anatomy', 'paper', 'Anatomy')
def anatomy():
    size = 520
    base, cap, xh = 720, 720 - 0.72 * size, 720 - 0.54 * size
    lines = ''.join(f'<div class="ln" style="top:{y}px"><span class="label">{t}</span></div>'
                    for y, t in ((cap, 'cap height 720'), (xh, 'x-height 540'), (base, 'baseline 0')))
    body = f"""
{lines}
<div class="word" style="top:{base - 0.85 * size}px">Rang</div>
<div class="note n1"><span class="accent">●</span> Chamfered corners: the watch’s pixel rule</div>
<div class="note n2"><span class="accent">●</span> The r’s notch, carried into n, m, h</div>
<div class="note n3"><span class="accent">●</span> Bowls are octagons</div>"""
    css = f"""
.s-anatomy .ln {{ position:absolute; left:96px; right:96px; border-top: 2px solid var(--accent2); opacity:.55; }}
.s-anatomy .ln .label {{ position:absolute; right:0; top: 8px; color: var(--accent2); }}
.s-anatomy .word {{ position:absolute; left: 110px; font-size: {size}px; line-height: 1; font-weight: 500; letter-spacing: .01em; }}
.s-anatomy .note {{ position:absolute; font: 400 26px/1.3 'Arris'; max-width: 420px; }}
.s-anatomy .n1 {{ left: 120px; top: 900px; }}
.s-anatomy .n2 {{ left: 760px; top: 900px; }}
.s-anatomy .n3 {{ left: 1340px; top: 900px; }}
"""
    return body, 'Cap height 0.72 em, x-height 0.54 em', css


@slide('italic', 'paper', 'The italic')
def italic():
    pairs = ''.join(f'<div class="p"><span class="u">{c}</span><span class="i">{c}</span></div>' for c in 'aefksy')
    body = f"""
<div class="head"><h2><i>Cursive,</i> not slanted.</h2>
<p>Ten degrees of slant, every chamfer a curve, and forms of its own: an entry flag, an exit tail, a looped k, a diagonal s.</p></div>
<div class="pairs">{pairs}</div>"""
    css = """
.s-italic .head { position:absolute; left:96px; top:140px; width: 1300px; }
.s-italic h2 { font-size: 120px; font-weight: 700; line-height: 1; }
.s-italic h2 i { color: var(--accent); }
.s-italic .head p { font-size: 32px; line-height: 1.45; margin-top: 28px; color: #3b3832; max-width: 1050px; }
.s-italic .pairs { position:absolute; left:96px; right:96px; top: 520px; display:grid; grid-template-columns: repeat(6, 1fr); }
.s-italic .p { font-size: 270px; line-height: 1; display:flex; gap: 6px; }
.s-italic .u { color: #bdb5a4; font-weight: 300; }
.s-italic .i { font-style: italic; font-weight: 500; }
"""
    return body, 'Upright and italic, light and medium: a e f k s y', css


@slide('italic-poster', 'violet', 'Italic, Black')
def italic_poster():
    body = """
<div class="w">
  <div class="l1">Expressive,</div>
  <div class="l2">swift &amp;</div>
  <div class="l3">sensible.</div>
</div>
<div class="side label">Arris Black Italic<br>Arris Thin Italic</div>"""
    css = """
.s-italic-poster .w { position:absolute; left: 96px; top: 140px; font-style: italic; line-height: .86; }
.s-italic-poster .l1 { font-size: 260px; font-weight: 900; color: var(--accent); }
.s-italic-poster .l2 { font-size: 260px; font-weight: 100; margin-left: 260px; }
.s-italic-poster .l3 { font-size: 260px; font-weight: 900; color: var(--accent2); margin-left: 120px; }
.s-italic-poster .side { position:absolute; right: 96px; bottom: 140px; text-align:right; }
"""
    return body, None, css


@slide('waterfall', 'paper', 'Text sizes')
def waterfall():
    t = 'Six spokes nearly sixty degrees apart; a figure two with a notch; quiet x-heights for long reading.'
    rows = ''.join(f'<div class="r"><span class="label">{s} px</span><span class="t" style="font-size:{s}px">{t}</span></div>'
                   for s in (14, 18, 24, 32, 44, 60, 84))
    body = f'<div class="stack">{rows}</div>'
    css = """
.s-waterfall .stack { position:absolute; inset: 140px 0 110px 96px; display:flex; flex-direction:column; justify-content:space-between; }
.s-waterfall .r { display:flex; align-items:baseline; gap: 36px; white-space: nowrap; }
.s-waterfall .r .label { width: 110px; flex: none; }
.s-waterfall .t { line-height: 1.1; -webkit-mask-image: linear-gradient(to right, #000 80%, transparent 99%); mask-image: linear-gradient(to right, #000 80%, transparent 99%); }
"""
    return body, 'Arris Regular, 14 to 84 pixels', css


@slide('editorial', 'bone', 'Editorial')
def editorial():
    body = """
<div class="hed">
  <div class="label accent">Feature · Type design</div>
  <h1>The figures that grew an alphabet</h1>
  <div class="dek"><i>How ten pixel numerals on a wrist became a type family with nine weights, three axes and two thousand characters.</i></div>
</div>
<div class="cols">
  <p><span class="drop">A</span> watch face has room for very little: ten figures, a colon, a few letters for the day. Dymaxion’s were drawn on a grid twelve pixels tall with strokes two pixels wide, and every corner the grid left exposed was cut at forty-five degrees. That single rule gave them their character: a notch where the 2 turns, a waist in the 3, a clipped corner on the 4.</p>
  <p>Arris takes the rule and the quirks seriously. The pixels become centrelines, the corners a rule the outline engine applies at any weight, so a Thin keeps its steps and a Black keeps its openings. Letters reuse the figures’ moves: the 3’s waist sits in B, the 2’s notch in Z, the beaks of 2, 3 and 5 in C, G, J and S.</p>
  <blockquote>“Measured optics are the default; the watch’s balance is a setting.”</blockquote>
  <p>The italic is not a slanted roman. Its chamfers become curves, its k loops, its s turns on a diagonal, and an entry flag borrowed from the 1 starts the strokes that need one. The monospaced cut keeps the figures’ pitch, and joins its programming ligatures the way the best code faces do.</p>
</div>"""
    css = """
.s-editorial .hed { position:absolute; left:96px; top:130px; width: 1730px; }
.s-editorial h1 { font-size: 112px; font-weight: 800; line-height: .98; margin: 18px 0 22px; letter-spacing: -0.01em; }
.s-editorial .dek { font-size: 34px; line-height: 1.35; color: #3d4a4d; max-width: 1300px; }
.s-editorial .cols { position:absolute; left:96px; right:96px; top: 545px; bottom: 100px; column-count: 3; column-gap: 64px; font-size: 25px; line-height: 1.5; }
.s-editorial .cols p { margin-bottom: 14px; }
.s-editorial .drop { float:left; font-size: 104px; line-height: .8; font-weight: 700; margin: 6px 10px 0 0; color: var(--accent); }
.s-editorial blockquote { font: italic 600 34px/1.22 'Arris'; color: var(--accent); margin: 18px 0; break-inside: avoid; }
"""
    return body, 'Headline ExtraBold, deck Italic, text Regular 25/37', css


@slide('languages', 'paper', 'Languages')
def languages():
    words = [('Welcome', 'English'), ('Bienvenue', 'Français'), ('Willkommen', 'Deutsch'), ('Bienvenido', 'Español'),
             ('Bem-vindo', 'Português'), ('Witamy', 'Polski'), ('Vítejte', 'Čeština'), ('Hoş geldiniz', 'Türkçe'),
             ('Chào mừng', 'Tiếng Việt'), ('Üdvözöljük', 'Magyar'), ('Velkomin', 'Íslenska'), ('Välkommen', 'Svenska'),
             ('Sveiki atvykę', 'Lietuvių'), ('Laipni lūdzam', 'Latviešu'), ('Croeso', 'Cymraeg'), ('Xoş gəlmisiniz', 'Azərbaycan'),
             ('Bun venit', 'Română'), ('Huānyíng', 'Pīnyīn'), ('Dobrodošli', 'Hrvatski'), ('Tervetuloa', 'Suomi'),
             ('Добро пожаловать', 'Русский'), ('Ласкаво просимо', 'Українська'), ('Добре дошли', 'Български'), ('Қош келдіңіз', 'Қазақша'),
             ('Тавтай морилно уу', 'Монгол'), ('Xush kelibsiz', 'Oʻzbekcha'), ('Сардэчна запрашаем', 'Беларуская'), ('Καλώς ήρθατε', 'Ελληνικά')]
    cells = ''.join(f'<div class="c"><div class="w" {"lang=bg" if l == "Български" else ""}>{esc(w)}</div><div class="label">{esc(l)}</div></div>'
                    for w, l in words)
    body = f'<div class="grid">{cells}</div>'
    css = """
.s-languages .grid { position:absolute; inset: 130px 96px 100px 96px; display:grid; grid-template-columns: repeat(4, 1fr); grid-auto-rows: 1fr; gap: 0 40px; }
.s-languages .c { border-top: 2px solid var(--line); padding-top: 14px; }
.s-languages .w { font-size: 44px; font-weight: 500; line-height: 1.1; white-space: nowrap; }
.s-languages .label { margin-top: 8px; }
"""
    return body, 'Twenty-eight languages from one family; Bulgarian takes its own forms (locl)', css


@slide('cyrillic', 'ink', 'Cyrillic')
def cyrillic():
    body = """
<div class="big">Шрифт</div>
<div class="cmp">
  <div><div class="label">Русский</div><div class="s" lang="ru">вдижклптцшщ</div></div>
  <div><div class="label accent">Български (locl)</div><div class="s" lang="bg">вдижклптцшщ</div></div>
  <div><div class="label">Курсив: русский · српски (locl)</div><div class="s it"><span lang="ru">бгдпт</span> · <span lang="sr">бгдпт</span></div></div>
</div>
<div class="txt">Съешь же ещё этих мягких французских булок, да выпей чаю. Әр ұлттың өз тілі бар.</div>"""
    css = """
.s-cyrillic .big { position:absolute; left: 80px; top: 90px; font-size: 420px; font-weight: 800; line-height: 1; color: var(--accent); }
.s-cyrillic .cmp { position:absolute; left: 96px; right: 96px; top: 600px; display:grid; grid-template-columns: repeat(3, 1fr); gap: 40px; }
.s-cyrillic .s { font-size: 76px; line-height: 1.15; margin-top: 10px; }
.s-cyrillic .it { font-style: italic; }
.s-cyrillic .txt { position:absolute; left:96px; right: 96px; bottom: 120px; font-size: 36px; color: #cfc8b9; }
"""
    return body, 'Russian, Bulgarian and Serbian forms of the same letters, chosen by language', css


@slide('greek', 'bone', 'Greek')
def greek():
    body = """
<div class="big">Τυπογραφία</div>
<div class="abc">Α Β Γ Δ Ε Ζ Η Θ Ι Κ Λ Μ Ν Ξ Ο Π Ρ Σ Τ Υ Φ Χ Ψ Ω</div>
<div class="abc l">α β γ δ ε ζ η θ ι κ λ μ ν ξ ο π ρ σ ς τ υ φ χ ψ ω</div>
<div class="txt">Ξεσκεπάζω την ψυχοφθόρα βδελυγμία · ϐ ϑ ϖ ϰ ϱ · Ϙ Ϛ Ϝ Ϟ Ϡ</div>"""
    css = """
.s-greek .big { position:absolute; left: 80px; top: 120px; font-size: 300px; font-weight: 300; line-height: 1; }
.s-greek .abc { position:absolute; left: 96px; right: 96px; top: 560px; font-size: 64px; letter-spacing: .06em; font-weight: 600; color: var(--accent); }
.s-greek .abc.l { top: 670px; font-weight: 400; color: var(--ink); }
.s-greek .txt { position:absolute; left:96px; bottom: 130px; font-size: 40px; font-style: italic; }
"""
    return body, 'Monotonic Greek with the symbol, archaic and lunate forms', css


@slide('vietnamese', 'cyan', 'Stacked marks')
def vietnamese():
    body = """
<div class="big">Tiếng Việt</div>
<div class="txt">Người ta có thể ăn kính mà không hại gì.<br>Ở đây có những ước mơ lớn, ổn định và rực rỡ.</div>
<div class="marks">Ấ Ầ Ẩ Ẫ Ậ Ắ Ằ Ẳ Ẵ Ặ Ế Ề Ể Ễ Ệ Ố Ồ Ổ Ỗ Ộ Ớ Ờ Ở Ỡ Ợ Ứ Ừ Ử Ữ Ự</div>"""
    css = """
.s-vietnamese .big { position:absolute; left: 80px; top: 120px; font-size: 300px; font-weight: 700; line-height: 1.05; color: var(--accent); }
.s-vietnamese .txt { position:absolute; left:96px; top: 520px; font-size: 56px; line-height: 1.4; }
.s-vietnamese .marks { position:absolute; left:96px; right: 96px; bottom: 130px; font-size: 58px; letter-spacing: .08em; color: var(--accent2); }
"""
    return body, 'Marks stack a gap apart and lighten as a unit before they would leave the line', css


def _code_html():
    K, T, S, C, N, F = 'kw', 'ty', 'st', 'cm', 'nu', 'fn'
    lines = [
        [('// a tiny pipeline, set in Arris Mono', C)],
        [('use', K), (' std::collections::HashMap;', '')],
        [('', '')],
        [('fn', K), (' ', ''), ('tally', F), ('(words: &[&', ''), ('str', T), (']) -> ', ''), ('HashMap', T), ('<&', ''), ('str', T), (', ', ''), ('usize', T), ('> {', '')],
        [('    let', K), (' mut counts = ', ''), ('HashMap', T), ('::new();', '')],
        [('    for', K), (' w ', ''), ('in', K), (' words.iter().filter(|w| w.len() >= ', ''), ('3', N), (') {', '')],
        [('        *counts.entry(w).or_insert(', ''), ('0', N), (') += ', ''), ('1', N), (';', '')],
        [('    }', '')],
        [('    counts', '')],
        [('}', '')],
        [('', '')],
        [('const', K), (' ready = (a, b) => a !== b && a <= ', ''), ('0x', N), ('FF', N), (';', '')],
        [('let', K), (' range = ', ''), ('0', N), ('..=', ''), ('9', N), ('; ', ''), ('/* ', C), ('inclusive', C), (' */', C)],
        [('xs |> map(f) |> filter(g)   ', ''), ('-- f <$> xs <*> ys', C)],
        [('if', K), (' x != y || y == ', ''), ('"', S), ('#{name}', S), ('"', S), (' { ', ''), ('return', K), (' x -> y }', '')],
    ]
    out = []
    for i, ln in enumerate(lines, 1):
        code = ''.join(f'<span class="{c}">{esc(t)}</span>' if c else esc(t) for t, c in ln)
        out.append(f'<div class="ln"><span class="no">{i}</span>{code}</div>')
    return ''.join(out)


@slide('code', 'slate', 'Arris Mono')
def code():
    body = f"""
<div class="win">
  <div class="tabs mono"><span class="on">tally.rs</span><span>pipeline.ts</span><span>notes.md</span></div>
  <div class="code mono">{_code_html()}</div>
</div>"""
    css = """
.s-code .win { position:absolute; inset: 120px 96px 100px 96px; background:#0a1018; border: 2px solid var(--line); }
.s-code .tabs { display:flex; font-size: 22px; border-bottom: 2px solid var(--line); }
.s-code .tabs span { padding: 18px 30px; color: var(--dim); }
.s-code .tabs .on { color: var(--ink); background:#0f1824; border-right: 2px solid var(--line); }
.s-code .code { padding: 30px 40px; font-size: 32px; line-height: 1.5; white-space: pre; }
.s-code .no { display:inline-block; width: 70px; color: #34475c; }
.s-code .kw { color: #ff79c6; } .s-code .ty { color: #7de0ff; } .s-code .st { color: #ffd36b; }
.s-code .cm { color: #5d7086; font-style: italic; } .s-code .nu { color: #bd93f9; } .s-code .fn { color: #7cf29a; }
"""
    return body, 'Ligatures on (calt): -> => != !== <= >= ..= |> <$> <*> #{ /*', css


@slide('ligatures', 'night', 'Programming ligatures')
def ligatures():
    import arris.glyphs  # noqa: F401
    from arris.draw import REGISTRY
    from arris.glyphs.ligatures import LIGATURES
    chars = {n: chr(s.unicode) for n, s in REGISTRY.items() if s.unicode}
    pick = ['->', '=>', '<->', '<=>', '|->', '->>', '~~>', '==', '===', '!=', '!==', '<=', '>=', '::', ':=', '..=',
            '|>', '<|>', '</>', '<!--', '<$>', '<*>', '#{', '#[', '#_', '/*', '//', '>>']
    have = {''.join(chars[c] for c in comps) for _, comps in LIGATURES}
    cells = ''.join(f'<div class="c"><div class="g mono">{esc(s)}</div><div class="s mono">{esc(s)}</div></div>'
                    for s in pick if s in have)
    body = f'<div class="grid">{cells}</div>'
    css = """
.s-ligatures .grid { position:absolute; inset: 130px 96px 100px 96px; display:grid; grid-template-columns: repeat(7, 1fr); grid-auto-rows: 1fr; gap: 0; }
.s-ligatures .c { border: 1px solid var(--line); display:flex; flex-direction:column; align-items:center; justify-content:center; gap: 10px; }
.s-ligatures .g { font-size: 92px; line-height: 1; font-weight: 400; }
.s-ligatures .s { font-size: 22px; color: var(--dim); font-variant-ligatures: none; font-feature-settings: 'calt' 0; letter-spacing: .3em; }
"""
    return body, 'Each one cell per character wide, so the grid never moves', css


@slide('terminal', 'slate', 'In the terminal')
def terminal():
    sys.path.insert(0, str(ROOT / 'tools'))
    from terminal_proofs import tui
    rows = tui()
    colours = {'«1»': '</span><span class="p1">', '«2»': '</span><span class="p2">', '«3»': '</span><span class="p3">', '«0»': '</span><span>'}
    out = []
    for r in rows:
        r = re.sub(r'\{([0-9A-Fa-f]{4,5})\}', lambda m: chr(int(m.group(1), 16)), r)
        r = esc(r)
        for k, v in colours.items():
            r = r.replace(esc(k), v)
        out.append(f'<span>{r}</span>')
    body = f'<pre class="term mono">{chr(10).join(out)}</pre>'
    css = """
.s-terminal .term { position:absolute; left: 96px; top: 130px; font-size: 54px; line-height: 1.2; color: #cfe3f5; }
.s-terminal .p1 { background:#7cf29a; color:#0d1520; } .s-terminal .p2 { background:#33475e; color:#e6edf5; }
.s-terminal .p3 { color:#ff79c6; }
"""
    return body, 'Box drawing, blocks, shades, Braille and Powerline fill the cell and join row to row', css


@slide('board', 'amber', 'Departures')
def board():
    flights = [('08:15', 'REYKJAVÍK', 'FI 455', 'B12', 'ON TIME'), ('08:40', 'KRAKÓW', 'LO 282', 'C04', 'BOARDING'),
               ('09:05', 'İSTANBUL', 'TK 1980', 'D21', 'DELAYED 09:50'), ('09:20', 'HÀ NỘI', 'VN 36', 'E07', 'GATE OPEN'),
               ('09:45', 'ALMATY', 'KC 942', 'B03', 'ON TIME'), ('10:08', 'ΑΘΗΝΑ', 'A3 611', 'C17', 'ON TIME'),
               ('10:30', 'SOFIA', 'FB 438', 'A09', 'CANCELLED'), ('10:55', 'PRAHA', 'OK 641', 'D02', 'ON TIME')]

    def tiles(s, n):
        s = s.ljust(n)[:n]
        return ''.join(f'<span class="t">{esc(ch) if ch != " " else "&nbsp;"}</span>' for ch in s)
    rows = ''.join(f'<div class="r">{tiles(t, 5)}<span class="gap"></span>{tiles(d, 10)}<span class="gap"></span>{tiles(f, 7)}'
                   f'<span class="gap"></span>{tiles(g, 3)}<span class="gap"></span><span class="st {"warn" if "DEL" in s or "CAN" in s else ""}">{tiles(s, 13)}</span></div>'
                   for t, d, f, g, s in flights)
    head = '<div class="h mono"><span>Time</span><span>Destination</span><span>Flight</span><span>Gate</span><span>Remarks</span></div>'
    body = f'<div class="b">{head}{rows}</div>'
    css = """
.s-board .b { position:absolute; left: 96px; top: 140px; }
.s-board .h { display:grid; grid-template-columns: 228px 412px 300px 150px 1fr; font-size: 22px; letter-spacing:.2em; text-transform: uppercase; color: var(--dim); margin-bottom: 16px; }
.s-board .r { display:flex; margin-bottom: 14px; }
.s-board .t { font: 600 46px/1 'Arris Mono'; width: 40px; height: 66px; display:inline-flex; align-items:center; justify-content:center; background:#1a1610;
              margin-right: 3px; position: relative; }
.s-board .t::after { content:''; position:absolute; left:0; right:0; top: 50%; height: 2px; background:#0b0a08; }
.s-board .gap { width: 24px; }
.s-board .warn .t { color: var(--accent2); }
"""
    return body, 'Arris Mono SemiBold, one tile per cell', css


@slide('dash', 'cyan', 'Instruments')
def dash():
    ticks = []
    import math
    for i in range(0, 41):
        a = math.radians(225 - i * 270 / 40)
        r0, r1 = (330, 372) if i % 5 == 0 else (350, 372)
        ticks.append(f'<line x1="{400 + r0 * math.cos(a):.1f}" y1="{400 - r0 * math.sin(a):.1f}" x2="{400 + r1 * math.cos(a):.1f}" '
                     f'y2="{400 - r1 * math.sin(a):.1f}" stroke="{"#3fd6ff" if i <= 19 else "#12303a"}" stroke-width="{8 if i % 5 == 0 else 4}"/>')
    gauge = f'<svg width="800" height="800" viewBox="0 0 800 800">{"".join(ticks)}</svg>'
    body = f"""
<div class="g">{gauge}<div class="read"><div class="v">128</div><div class="u label">km/h</div></div></div>
<div class="side">
  <div class="it"><div class="label">Range</div><div class="n">412<small> km</small></div></div>
  <div class="it"><div class="label">Outside</div><div class="n">−4<small> °C</small></div></div>
  <div class="it"><div class="label">Next</div><div class="n">↱ 600<small> m</small></div></div>
  <div class="it"><div class="label">Gear</div><div class="n accent2">D</div></div>
</div>"""
    css = """
.s-dash .g { position:absolute; left: 96px; top: 150px; width: 800px; height: 800px; }
.s-dash .read { position:absolute; inset: 0; display:flex; flex-direction:column; align-items:center; justify-content:center; }
.s-dash .v { font-size: 300px; font-weight: 700; line-height: .8; font-variation-settings: 'GRAD' -50; }
.s-dash .u { margin-top: 30px; font-size: 26px; }
.s-dash .side { position:absolute; left: 1060px; right: 96px; top: 190px; display:grid; grid-template-columns: 1fr 1fr; gap: 70px 60px; }
.s-dash .n { font-size: 130px; font-weight: 300; line-height: 1; margin-top: 10px; font-variation-settings: 'GRAD' -50; white-space: nowrap; }
.s-dash .n small { font-size: 40px; color: var(--dim); }
"""
    return body, 'Grade −50 on the dark display', css


@slide('watches', 'night', 'Watch faces')
def watches():
    faces = [("10:08", "WED 22", "#ffb000", "#050607", 600, 100, 'oct'),
             ("21:47", "62 BPM", "#3fd6ff", "#04121a", 300, 0, 'round'),
             ("06:30", "SUN 18°", "#151412", "#f3eee3", 800, 0, 'square'),
             ("12:00", "100%", "#ff5fae", "#17102a", 900, 100, 'oct')]
    out = []
    for t, sub, ink, bg, w, wt, shape in faces:
        out.append(f'<div class="w"><div class="f {shape}" style="background:{bg};color:{ink}"><div class="t" style="font-weight:{w};'
                   f'font-variation-settings:\'WTCH\' {wt}">{t}</div><div class="s mono">{esc(sub)}</div></div>'
                   f'<div class="label">wght {w} · WTCH {wt}</div></div>')
    body = f'<div class="row">{"".join(out)}</div>'
    css = """
.s-watches .row { position:absolute; left: 96px; right: 96px; top: 250px; display:grid; grid-template-columns: repeat(4, 1fr); gap: 50px; }
.s-watches .w .label { margin-top: 30px; text-align:center; }
.s-watches .f { aspect-ratio: 1; display:flex; flex-direction:column; align-items:center; justify-content:center; gap: 18px; border: 14px solid #23272b; }
.s-watches .oct { clip-path: polygon(29% 0, 71% 0, 100% 29%, 100% 71%, 71% 100%, 29% 100%, 0 71%, 0 29%); border: none; }
.s-watches .round { border-radius: 50%; }
.s-watches .t { font-size: 128px; line-height: .8; }
.s-watches .s { font-size: 26px; letter-spacing: .15em; }
"""
    return body, 'SemiBold Watch, Light, ExtraBold, Black Watch', css


@slide('compass', 'paper', 'Arrows')
def compass():
    import math
    arrows = '→↗↑↖←↙↓↘'
    pts = []
    for i, a in enumerate(arrows):
        ang = math.radians(i * 45)
        x, y = 600 + 330 * math.cos(ang), 450 - 330 * math.sin(ang)
        w = 100 + 100 * i
        pts.append(f'<div class="a" style="left:{x - 90:.0f}px;top:{y - 110:.0f}px;font-weight:{w}">{a}</div>')
    rest = '⇄ ⇆ ⇉ ⇶ ↯ ↺ ↻ ⟶ ⟹ ⟷ ↦ ↠ ↬ ⇀ ⇌ ⇨ ⇧'
    body = f"""
<div class="rose">{''.join(pts)}<div class="c">N</div></div>
<div class="list">{rest}</div>"""
    css = """
.s-compass .rose { position:absolute; left: 96px; top: 120px; width: 1200px; height: 900px; }
.s-compass .a { position:absolute; width: 180px; text-align:center; font-size: 180px; line-height: 1; }
.s-compass .c { position:absolute; left: 540px; top: 370px; width: 120px; text-align:center; font-size: 140px; font-weight: 800; color: var(--accent); line-height: 1; }
.s-compass .list { position:absolute; left: 1330px; right: 96px; top: 200px; font-size: 92px; line-height: 1.45; letter-spacing: .1em; }
"""
    return body, 'One head for every arrow: a sharp point, barbs cut square', css


@slide('math', 'ink', 'Mathematics')
def math_():
    eqs = ['e<sup>iπ</sup> + 1 = 0',
           '∑ 1/n² = π²/6',
           '∫ e<sup>−x²</sup> dx = √π',
           '∀ε &gt; 0 ∃δ &gt; 0 : |x − a| &lt; δ ⇒ |f(x) − L| &lt; ε',
           'A ∩ (B ∪ C) = (A ∩ B) ∪ (A ∩ C)',
           '∇ · E = ρ ⁄ ε₀   ∮ B · dl = μ₀I']
    rows = ''.join(f'<div class="e">{e}</div>' for e in eqs)
    body = f'<div class="stack">{rows}</div>'
    css = """
.s-math .stack { position:absolute; inset: 150px 96px 120px 96px; display:flex; flex-direction:column; justify-content:space-between; }
.s-math .e { font-size: 84px; font-weight: 300; line-height: 1; }
.s-math .e:nth-child(1) { font-size: 150px; font-weight: 600; color: var(--accent2); }
.s-math sup { font-size: .6em; vertical-align: .7em; line-height: 0; }
"""
    return body, 'Operators sit on the axis; the arrows and relations share the font’s strokes', css


@slide('features', 'paper', 'OpenType features')
def features():
    rows = [('frac', '1/2  7/8', 'frac'), ('sups', 'x2 + y2', 'sups'), ('subs', 'H2O CO2', 'subs'),
            ('zero', '0 Ø O', 'zero'), ('ss01', '2001', 'ss01'), ('ss02', '555', 'ss02'), ('case', '(A-Z) [HI]', 'case'),
            ('calt', '12:45', 'calt'), ('pnum', '1110', 'pnum'), ('cv01', 'aaa', 'cv01')]
    cells = ''.join(f'<div class="r"><span class="tag mono accent">{t}</span><span class="off" style="font-feature-settings:\'calt\' 0">{esc(s)}</span>'
                    f'<span class="arr dim">→</span><span class="on" style="font-feature-settings:\'{f}\' 1">{esc(s)}</span></div>'
                    for t, s, f in rows)
    body = f'<div class="grid">{cells}</div>'
    css = """
.s-features .grid { position:absolute; inset: 140px 96px 110px 96px; display:grid; grid-template-columns: 1fr 1fr; grid-auto-rows: 1fr; gap: 0 90px; }
.s-features .r { display:grid; grid-template-columns: 120px 1fr 70px 1fr; align-items:center; border-top: 2px solid var(--line); font-size: 64px; }
.s-features .tag { font-size: 24px; }
.s-features .off { color: #a59d8d; }
"""
    return body, 'Fractions, super- and subscripts, slashed and dotted zero, open five, case forms, the time colon', css


@slide('exchange', 'night', 'Exchange')
def exchange():
    rows = [('€', 'EUR', 'Euro', '1.0000', '+0.00'), ('£', 'GBP', 'Pound', '0.8641', '−0.12'), ('¥', 'JPY', 'Yen', '163.27', '+0.48'),
            ('₹', 'INR', 'Rupee', '91.402', '+0.07'), ('₺', 'TRY', 'Lira', '36.815', '+1.21'), ('₴', 'UAH', 'Hryvnia', '45.110', '−0.31'),
            ('₸', 'KZT', 'Tenge', '548.90', '+0.22'), ('₩', 'KRW', 'Won', '1504.6', '−0.09'), ('₫', 'VND', 'Dong', '27 410', '+0.03'),
            ('₿', 'BTC', 'Bitcoin', '0.0000', '+2.40')]
    out = ''.join(f'<div class="r"><span class="s">{a}</span><span class="c mono">{b}</span><span class="n">{c}</span>'
                  f'<span class="v mono">{d}</span><span class="d mono {"up" if e.startswith("+") else "dn"}">{e}%</span></div>'
                  for a, b, c, d, e in rows)
    body = f'<div class="t">{out}</div>'
    css = """
.s-exchange .t { position:absolute; inset: 140px 96px 100px 96px; display:flex; flex-direction:column; justify-content:space-between; }
.s-exchange .r { display:grid; grid-template-columns: 140px 170px 1fr 330px 230px; align-items:baseline; border-bottom: 2px solid var(--line); padding-bottom: 6px; }
.s-exchange .s { font-size: 66px; font-weight: 700; color: var(--accent); line-height: 1; }
.s-exchange .c { font-size: 34px; color: var(--dim); }
.s-exchange .n { font-size: 44px; }
.s-exchange .v { font-size: 56px; text-align: right; }
.s-exchange .d { font-size: 36px; text-align: right; }
.s-exchange .up { color: #7cf29a; } .s-exchange .dn { color: #ff6a5a; }
"""
    return body, 'Every currency sign, drawn from the letters, with tabular figures', css


@slide('field', 'night', 'A weight field')
def field():
    import math
    cols, rows = 16, 7
    cells = []
    for r in range(rows):
        for c in range(cols):
            d = math.hypot((c - 7.5) / 7.5, (r - 3) / 3)
            w = int(900 - 800 * min(d, 1.0))
            g = int(100 * math.cos(d * 2.2))
            col = '#ffb000' if d < 0.35 else '#f1ebdd'
            cells.append(f'<span style="font-weight:{w};font-variation-settings:\'GRAD\' {g};color:{col}">8</span>')
    body = f'<div class="f">{"".join(cells)}</div>'
    css = """
.s-field .f { position:absolute; left: 96px; right: 96px; top: 120px; bottom: 110px; display:grid; grid-template-columns: repeat(16, 1fr); align-items:center; justify-items:center; }
.s-field .f span { font-size: 128px; line-height: 1; }
"""
    return body, 'One figure, weight and grade varied across the field', css


@slide('swiss', 'signal', 'Poster')
def swiss():
    body = """
<div class="a">a</div>
<div class="blk b1"><div class="label">Arris</div><p>A geometric sans grown from the figures of a watch. Chamfered corners, octagonal bowls, a notch where the 2 turns.</p></div>
<div class="blk b2"><div class="label">Weights</div><p>100 200 300 400 500 600 700 800 900</p></div>
<div class="blk b3"><div class="label">Axes</div><p>wght · GRAD · WTCH</p></div>"""
    css = """
.s-swiss .a { position:absolute; right: -70px; bottom: -330px; font-size: 1450px; font-weight: 900; line-height: 1; color: var(--accent2); }
.s-swiss .blk { position:absolute; left: 96px; width: 520px; }
.s-swiss .blk p { font-size: 34px; line-height: 1.3; font-weight: 500; color: var(--accent); margin-top: 8px; }
.s-swiss .b1 { top: 150px; } .s-swiss .b2 { top: 460px; } .s-swiss .b3 { top: 620px; }
.s-swiss .label { color: #111; }
"""
    return body, None, css


@slide('colophon', 'night', 'Colophon')
def colophon():
    stats = [('9', 'weights'), ('3', 'axes'), ('2,150', 'characters'), ('69', 'ligatures'), ('6', 'families')]
    s = ''.join(f'<div><div class="n">{a}</div><div class="label">{b}</div></div>' for a, b in stats)
    body = f"""
<div class="name">Arris</div>
<div class="stats">{s}</div>
<div class="small mono">Grown from Dymaxion’s Chamfer figures · drawn by a stroke engine, every corner under one rule · fontbakery: 0 failures</div>"""
    css = """
.s-colophon .name { position:absolute; left: 80px; top: 120px; font-size: 380px; font-weight: 200; line-height: 1; }
.s-colophon .stats { position:absolute; left: 96px; right: 96px; top: 600px; display:flex; justify-content:space-between; }
.s-colophon .n { font-size: 130px; font-weight: 700; color: var(--accent); line-height: 1; }
.s-colophon .stats .label { margin-top: 14px; }
.s-colophon .small { position:absolute; left: 96px; bottom: 120px; font-size: 22px; color: var(--dim); }
"""
    return body, None, css


# --- assembly ------------------------------------------------------------------------------

def build_pages(only=None):
    n = len(SLIDES)
    pages = []
    for i, (name, pal, title, fn) in enumerate(SLIDES, 1):
        if only and name not in only:
            continue
        body, caption, css = fn()
        html_, css = page(i, n, name, pal, title, body, caption, css)
        pages.append((i, name, html_, css))
    return pages


def document(pages):
    css = font_css() + BASE + ''.join(c for _, _, _, c in pages)
    body = ''.join(h for _, _, h, _ in pages)
    return f'<!doctype html><html><head><meta charset="utf-8"><style>{css}\n@page {{ size: 1920px 1080px; margin: 0; }}</style></head><body>{body}</body></html>'


def missing_chars(pages):
    """Characters the slides use that neither Arris nor Arris Mono has."""
    from fontTools.ttLib import TTFont
    have = set(TTFont(BUILD / 'Arris[GRAD,WTCH,wght].ttf').getBestCmap()) | set(TTFont(BUILD / 'ArrisMono-Regular.ttf').getBestCmap())
    text = ''.join(html.unescape(re.sub(r'<[^>]+>', ' ', h)) for _, _, h, _ in pages)
    return sorted({c for c in text if ord(c) > 32 and ord(c) not in have})


def render(pages, pdf=True):
    from playwright.sync_api import sync_playwright
    (OUT / 'slides').mkdir(parents=True, exist_ok=True)
    work = BUILD / 'presentation'
    work.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        pg = browser.new_page(viewport={'width': W, 'height': H})
        for i, name, h, css in pages:
            f = work / f'{i:02d}-{name}.html'
            f.write_text(document([(i, name, h, css)]), encoding='utf-8')
            pg.goto(f.as_uri())
            pg.evaluate('document.fonts.ready')
            pg.wait_for_timeout(150)
            pg.screenshot(path=str(OUT / 'slides' / f'{i:02d}-{name}.png'))
            print('  ', f'{i:02d}-{name}.png')
        if pdf:
            f = work / 'deck.html'
            f.write_text(document(pages), encoding='utf-8')
            pg.goto(f.as_uri())
            pg.evaluate('document.fonts.ready')
            pg.wait_for_timeout(300)
            pg.pdf(path=str(OUT / 'arris.pdf'), width='1920px', height='1080px', print_background=True)
            print('   arris.pdf')
        browser.close()


if __name__ == '__main__':
    only = set(sys.argv[1:]) or None
    pages = build_pages(only)
    gone = missing_chars(pages)
    if gone:
        print('missing:', ' '.join(gone))
    render(pages, pdf=only is None)
