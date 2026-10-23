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
.chrome { position: absolute; left: 96px; right: 96px; top: 38px; display: flex; justify-content: space-between; align-items: center;
          font: 500 16px/1 'Arris Mono'; letter-spacing: 0.12em; text-transform: uppercase; color: var(--dim); }
.chrome .k-l, .chrome .k-r { display: flex; align-items: center; gap: 16px; }
.chrome .k-tab { width: 30px; height: 30px; display: grid; place-items: center; background: var(--accent); color: var(--bg);
               font: 900 20px/1 'Arris'; letter-spacing: 0; clip-path: polygon(0 0, 100% 0, 100% 70%, 70% 100%, 0 100%); }
.chrome .k-brand { color: var(--ink); }
.chrome .k-sl { opacity: .6; }
.chrome .k-chip { display: inline-flex; align-items: center; height: 24px; padding: 1px; background: var(--ink); color: var(--bg);
                font-size: 12px; letter-spacing: .1em; }
.chrome .k-chip i { font-style: normal; width: 22px; height: 22px; display: grid; place-items: center; background: var(--bg); color: var(--ink); font-size: 17px; letter-spacing: 0; }
.chrome .k-chip b { font-weight: 500; padding: 0 9px 0 8px; }
.chrome .k-pager { display: flex; gap: 4px; align-items: center; }
.chrome .k-pager s { width: 4px; height: 4px; background: var(--dim); opacity: .5; }
.chrome .k-pager s.k-on { width: 24px; background: var(--ink); opacity: 1; }
.chrome .k-idx b { color: var(--ink); font-weight: 500; }
.k-xh { position: absolute; font: 200 24px/1 'Arris Mono'; color: var(--dim); }
.k-xh1 { left: 30px; top: 24px; } .k-xh2 { right: 30px; top: 24px; } .k-xh3 { left: 30px; bottom: 22px; } .k-xh4 { right: 30px; bottom: 22px; }
.k-strip { position: absolute; right: 38px; top: 240px; bottom: 84px; width: 20px; display: flex; flex-direction: column; align-items: center; gap: 14px;
          font: 500 13px/1 'Arris Mono'; color: var(--accent); }
.k-strip .k-bars { display: flex; flex-direction: column; gap: 2px; width: 16px; }
.k-strip .k-bars u { display: block; background: var(--accent); }
.k-strip .k-n { writing-mode: vertical-rl; letter-spacing: .08em; }
.k-strip .k-x { writing-mode: vertical-rl; text-orientation: sideways; font: 400 26px/1 'Arris Mono'; color: var(--ink); margin-top: -2px; }
.k-strip .k-cut { flex: 1; width: 2px; margin-top: -8px; background: repeating-linear-gradient(to bottom, var(--dim) 0 2px, transparent 2px 7px); }
.k-strip .k-v { writing-mode: vertical-rl; font-size: 11px; font-weight: 400; letter-spacing: .16em; text-transform: uppercase; white-space: nowrap; color: var(--dim); }
.caption { position: absolute; left: 96px; right: 96px; bottom: 44px; display: flex; justify-content: space-between; align-items: baseline; gap: 48px;
           font: 400 18px/1.3 'Arris Mono'; color: var(--dim); }
.k-crop { position: absolute; border: 1px solid var(--line); background: color-mix(in srgb, var(--ink) 4%, transparent); }
.k-crop::before, .k-crop::after { content: ''; position: absolute; inset: -44px -1px; border-left: 1px solid var(--dim); border-right: 1px solid var(--dim);
                              -webkit-mask: linear-gradient(#000 0 40px, transparent 40px calc(100% - 40px), #000 calc(100% - 40px)); opacity: .7; }
.k-crop::after { inset: -1px -44px; border: 0; border-top: 1px solid var(--dim); border-bottom: 1px solid var(--dim);
               -webkit-mask: linear-gradient(90deg, #000 0 40px, transparent 40px calc(100% - 40px), #000 calc(100% - 40px)); }
.k-crop .k-sn { position: absolute; left: 18px; top: 18px; font: 400 12px/1 'Arris Mono'; letter-spacing: .1em; color: var(--dim); }
.k-crop .k-codes { position: absolute; right: 18px; bottom: 16px; font: 400 12px/1.3 'Arris Mono'; letter-spacing: .1em; color: var(--dim); text-align: right; }
.caption .k-stamp { font-size: 13px; letter-spacing: .12em; text-transform: uppercase; white-space: nowrap; }
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
.void   { --bg: #04030b; --ink: #e8fff0; --dim: #3f6a52; --accent: #39ff14; --accent2: #ff2bd6; --line: #10241a; }
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


# what each slide shows, for the tag in its chrome: (pictogram, slides)
KINDS = {
    'Family': ('◆', ['cover', 'family', 'weights', 'axes', 'grade', 'colophon']),
    'Form': ('▣', ['origin', 'charset', 'figures', 'pixels', 'anatomy', 'squint']),
    'Italic': ('◢', ['italic', 'italic-poster']),
    'Text': ('¶', ['waterfall', 'editorial', 'feature']),
    'Scripts': ('◐', ['languages', 'cyrillic', 'greek', 'vietnamese']),
    'Code': ('⌨', ['code', 'code-python', 'code-react', 'code-functional', 'ligatures', 'terminal']),
    'Interface': ('◉', ['board', 'dash', 'telemetry', 'slingshot', 'watches', 'compass', 'keys']),
    'Signs': ('∑', ['math', 'features', 'exchange']),
    'Poster': ('◈', ['field', 'swiss', 'riso', 'maze', 'garden']),
}
KIND = {name: (kind, icon) for kind, (icon, names) in KINDS.items() for name in names}
STAMP = __import__('datetime').date.today().strftime('%m.%d.%Y')


def page(i, n, name, palette, title, body, caption, css):
    """A slide in the deck's chrome: a tab, the family, a tag for the kind of
    slide and its title; a pager; crosshairs at the corners; a strip of code
    up the right edge; a serial and the date under the caption."""
    import hashlib
    kind, icon = KIND[name]
    h = hashlib.md5(name.encode()).hexdigest()
    serial = f'SN-AR{i:02d}-{h[:6].upper()}'
    pager = ''.join(f'<s class="{"k-on" if k == i else ""}"></s>' for k in range(1, n + 1))
    bars = ''.join(f'<u style="height:{1 + int(c, 16) % 3}px"></u>' for c in h[6:16])
    strip = (f'<div class="k-strip"><div class="k-bars">{bars}</div><span>✕</span><span>▣</span>'
             f'<span class="k-n">{i:02d}</span><span class="k-n">{n:02d}</span>'
             f'<span class="k-v">Arris ⁄ {kind} ⁄ “cutting corners where we can”</span>'
             f'<span class="k-x">✂</span><span class="k-cut"></span></div>')
    marks = ''.join(f'<div class="k-xh k-xh{k}">+</div>' for k in range(1, 5))
    cap = (f'<div class="caption"><span>{caption}</span><span class="k-stamp">{serial} ⁄ {STAMP}</span></div>'
           if caption is not None else '')
    chrome = (f'<div class="chrome"><div class="k-l"><span class="k-tab">A</span><span class="k-brand">Arris</span>'
              f'<span class="k-chip"><i>{icon}</i><b>{kind}</b></span><span class="k-sl">/</span><span>{esc(title)}</span></div>'
              f'<div class="k-r"><span class="k-pager">{pager}</span><span class="k-idx">[<b>{i:02d}</b>/{n:02d}]</span></div></div>')
    return f'<section class="slide {palette} s-{name}">{chrome}{marks}{strip}{body}{cap}</section>', css


# --- the slides --------------------------------------------------------------------------

def _features():
    """The OpenType features a reader can turn on in Arris Mono (not the
    shaping ones the font applies by itself)."""
    from fontTools.ttLib import TTFont
    gsub = TTFont(BUILD / 'ArrisMono-Regular.ttf')['GSUB'].table
    return sorted({r.FeatureTag for r in gsub.FeatureList.FeatureRecord} - {'ccmp', 'locl'})


@slide('cover', 'night', 'A typeface')
def cover():
    lines = ''.join(f'<div class="w w{w}" style="font-weight:{w}">Arris</div>' for w in (100, 300, 600, 900))
    codes = '<br>'.join(t.upper() for t in _features())
    body = f"""
<div class="stack">{lines}</div>
<div class="side">
  <div class="kicker label">A typeface in nine weights,<br>upright, italic and mono</div>
  <div class="tag">a chamfered sans</div>
  <div class="facts">
    <div><span class="accent">Thin → Black</span><br>Upright, Italic, Mono, Watch</div>
    <div><span class="accent">wght · GRAD · WTCH</span><br>Three variable axes</div>
    <div><span class="accent">2,150</span><br>characters: Latin, Cyrillic, Greek</div>
  </div>
  <div class="clock">10:08</div>
</div>
<div class="k-crop cv"><span class="k-sn">SN-AR01<br>WGHT·GRAD·WTCH</span><div class="k-codes">{codes}</div></div>"""
    css = """
.s-cover .stack { position:absolute; left: 84px; top: 128px; }
.s-cover .w { font-size: 228px; line-height: .88; letter-spacing: -0.01em; }
.s-cover .w100 { color: #4d4a44; } .s-cover .w300 { color: #8f897d; } .s-cover .w600 { color: var(--ink); }
.s-cover .w900 { color: var(--accent); }
.s-cover .side { position:absolute; left: 1060px; right: 96px; top: 150px; bottom: 110px; display:flex; flex-direction:column; }
.s-cover .tag { font-size: 64px; font-style: italic; font-weight: 300; margin-top: 26px; }
.s-cover .facts { margin-top: 64px; display:flex; flex-direction:column; gap: 30px; font: 400 28px/1.35 'Arris'; }
.s-cover .cv { left: 1586px; top: 340px; width: 214px; height: 330px; }
.s-cover .cv .k-codes { columns: 2; column-gap: 26px; }
.s-cover .clock { margin-top: auto; font-size: 168px; font-weight: 600; font-variation-settings: 'WTCH' 100; color: var(--accent); line-height: .8; }
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
    <div class="label accent">Where it starts</div>
    <h2>Ten figures on a watch face, every corner cut.</h2>
    <p>Arris began as a watch’s clock figures. It keeps their quirks, the notch in the 2, the waist in the 3, and carries them through a whole alphabet.</p>
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
                   f'<span class="t" style="font-weight:{100 * (i + 1)}">Neon rain over Sector 7</span></div>'
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
    txt = 'Light text on a dark visor glows and looks heavier. Grade takes weight off without changing a single advance width, so the HUD never reflows.'
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
    geom = heritage.trace(rows)                         # in font units: y counts up from the bottom row
    paths = []
    for poly in getattr(geom, 'geoms', [geom]):
        for ring in [poly.exterior, *poly.interiors]:
            pts = ' '.join(f'{x * s:.1f},{(len(rows) - y) * s:.1f}' for x, y in ring.coords)
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
<div class="word" style="top:{base - 0.85 * size}px">Rain</div>
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


@slide('squint', 'paper', 'White that reads')
def squint():
    word = '8 B 0 3 5 6 9 @ ₦'
    rows = ''.join(f'<div class="r"><span class="label">{lab}</span><span class="g" style="filter: blur({b}px)">{esc(word)}</span></div>'
                   for lab, b in (('Sharp', 0), ('Squint', 3), ('Squint harder', 6)))
    body = f"""
<div class="head"><h2>Blur it, and the counters stay.</h2>
<p>Every hole and every slot between two parts is measured under a model squint, a blur five per cent of the cap height wide.
White that would close is opened: bars thin, rings grow, a stem steps aside.</p></div>
<div class="rows">{rows}</div>"""
    css = """
.s-squint .head { position:absolute; left:96px; top:130px; width: 1500px; }
.s-squint h2 { font-size: 84px; font-weight: 700; line-height: 1.02; }
.s-squint .head p { font-size: 30px; line-height: 1.45; margin-top: 22px; color: #3b3832; max-width: 1300px; }
.s-squint .rows { position:absolute; left:96px; right:96px; top: 470px; bottom: 110px; display:flex; flex-direction:column; justify-content:space-between; }
.s-squint .r { display:flex; align-items:center; gap: 40px; }
.s-squint .r .label { width: 230px; flex:none; }
.s-squint .g { font-size: 140px; font-weight: 900; line-height: 1; white-space: nowrap; letter-spacing: .02em; }
"""
    return body, 'Arris Black; the squint rule is the vision model’s, in arris.vision', css


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
  <div class="l1">Electric,</div>
  <div class="l2">wired &amp;</div>
  <div class="l3">restless.</div>
</div>
<div class="side label">Arris Black Italic<br>Arris Thin Italic</div>
<svg width="0" height="0" style="position:absolute"><filter id="deboss" x="-5%" y="-5%" width="110%" height="110%">
  <feOffset in="SourceAlpha" dx="7" dy="9" result="o"/><feGaussianBlur in="o" stdDeviation="5" result="b"/>
  <feComposite operator="out" in="SourceAlpha" in2="b" result="edge"/>
  <feFlood flood-color="#05020c" flood-opacity=".72"/><feComposite operator="in" in2="edge" result="shade"/>
  <feOffset in="SourceAlpha" dx="2" dy="3" result="lo"/><feComposite operator="out" in="lo" in2="SourceAlpha" result="lip"/>
  <feFlood flood-color="#ffffff" flood-opacity=".22"/><feComposite operator="in" in2="lip" result="light"/>
  <feMerge><feMergeNode in="SourceGraphic"/><feMergeNode in="shade"/><feMergeNode in="light"/></feMerge>
</filter></svg>"""
    css = """
.s-italic-poster .w { position:absolute; left: 96px; top: 140px; font-style: italic; line-height: .86; filter: url(#deboss); }
.s-italic-poster .w div { color: transparent; -webkit-background-clip: text; background-clip: text; }
.s-italic-poster .l1 { font-size: 260px; font-weight: 900;
  background: radial-gradient(rgba(23,16,42,.38) 1.1px, transparent 1.6px) 0 0/6px 6px, var(--accent); }
.s-italic-poster .l2 { font-size: 260px; font-weight: 100; margin-left: 260px;
  background: radial-gradient(rgba(23,16,42,.30) 1px, transparent 1.5px) 0 0/5px 5px, var(--ink); }
.s-italic-poster .l3 { font-size: 260px; font-weight: 900; margin-left: 120px;
  background: radial-gradient(rgba(23,16,42,.38) 1.1px, transparent 1.6px) 3px 3px/6px 6px, var(--accent2); }
.s-italic-poster .side { position:absolute; right: 96px; bottom: 140px; text-align:right; }
"""
    return body, None, css


@slide('waterfall', 'paper', 'Text sizes')
def waterfall():
    t = 'Rain hissed on the maglev rails as the last courier jacked in at 03:47, her watch counting down in chamfered figures.'
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
  <div class="label accent">Transit · Night shift</div>
  <h1>The rain never stops. Neither do the trains.</h1>
  <div class="dek"><i>Couriers, coders and noodle cooks ride the 03:47 maglev from Arcology 7 to the docks. We rode along to see how.</i></div>
</div>
<div class="cols">
  <p><span class="drop">A</span>t a quarter to four the platform at Arcology 7 is busier than the market below it. Couriers in rain shells check their wrists, a vendor folds a cart of steamed buns into a backpack, two students share an umbrella and one pair of earbuds: everyone is waiting for car 34, where the sleep pods start.</p>
  <p>The cars are narrow and very clean. Twelve pods fold out of the walls, each with a reading light, a charge port and a bottle of water; breakfast is a rice ball and black coffee, delivered at 05:10. Nobody complains about the size. The point, says the conductor, is that you wake up in another district with your data still your own.</p>
  <blockquote>“You fall asleep under one set of neon and wake up under another. That still feels like magic.”</blockquote>
  <p>Demand has outrun supply on most of the network. New cars arrive through next year, and three more night lines open in the spring: the Docks to the Glasshouse, Low Tide to the Spire, and a loop around the ring road. Charge your watch, bring earplugs, and ask for a lower pod.</p>
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


@slide('feature', 'paper', 'Feature')
def feature():
    nums = [('2,140', 'rose bushes'), ('26 h', 'to a day'), ('340 L', 'water a week'), ('11', 'years running'), ('0', 'sold')]
    rows = ''.join(f'<div class="r"><span class="n">{a}</span><span class="d">{b}</span></div>' for a, b in nums)
    body = f"""
<div class="kicker label">Station life · The Glasshouse</div>
<h1>Roses take their time at four hundred kilometres.</h1>
<div class="dek">In the ring’s quietest module a horticulturist and two retired pilots grow the only flowers for a million kilometres. They will not tell you their secret, but they will let you water.</div>
<div class="by mono">Words by Ines Varga · 14 min read</div>
<div class="body">
  <p><span class="drop">T</span>he Glasshouse is the last stop on the night line, and most riders sleep through it. Those who wake find a long white module, warm as a kitchen, where the air smells of soil for the first time in weeks. Mira Okonkwo has run it for eleven years. She keeps the lights on a twenty-six-hour day, because, she says, roses never agreed to ours.</p>
  <p>Everything is weighed. Water comes up from the docks in sealed bladders, 340 litres a week; what the plants breathe out goes back down the line to the scrubbers. The roses are an old French variety, grown from cuttings that flew up in a lunchbox. In low spin they climb slower and their stems come out thick, almost woody, but the flowers open the same deep red.</p>
  <p class="pull">“Up here everything is engineered. The roses are the one thing that still decides for itself.”</p>
  <p>Two retired pilots, Hal and Teodor, take the night shift. They prune by headlamp, argue about aphids that cannot possibly exist up here, and sell nothing: every bloom goes to a hospital bed, a launch or a wedding on the ring. If you want one, come and water. Bring your own cup.</p>
</div>
<div class="side"><div class="label">The Glasshouse in numbers</div>{rows}</div>"""
    css = """
.s-feature .kicker { position:absolute; left: 96px; top: 128px; color: var(--accent); }
.s-feature h1 { position:absolute; left: 96px; top: 166px; width: 1180px; font: 300 84px/1.02 'Arris'; letter-spacing: -0.01em; }
.s-feature .dek { position:absolute; left: 96px; top: 362px; width: 1120px; font: italic 400 29px/1.38 'Arris'; color: #4a463e; }
.s-feature .by { position:absolute; left: 96px; top: 506px; font-size: 16px; letter-spacing: .1em; text-transform: uppercase; color: var(--dim); }
.s-feature .body { position:absolute; left: 96px; top: 552px; width: 1180px; bottom: 96px; column-count: 2; column-gap: 56px;
                   font: 400 21px/1.52 'Arris'; }
.s-feature .body p { margin-bottom: 12px; }
.s-feature .drop { float:left; font: 800 92px/.8 'Arris'; margin: 6px 10px 0 0; color: var(--accent); }
.s-feature .pull { font: 600 30px/1.2 'Arris'; color: var(--accent); border-top: 3px solid var(--accent); border-bottom: 3px solid var(--accent);
                   padding: 12px 0; margin: 16px 0; break-inside: avoid; }
.s-feature .side { position:absolute; right: 96px; top: 166px; width: 420px; padding: 26px 28px; background: #151412; color: #f3eee3; }
.s-feature .side .label { color: #ffb000; margin-bottom: 18px; }
.s-feature .side .r { display:flex; justify-content: space-between; align-items: baseline; border-top: 1px solid #3a3731; padding: 14px 0 12px; }
.s-feature .side .n { font: 700 54px/1 'Arris'; font-feature-settings: 'tnum'; }
.s-feature .side .d { font: 400 18px 'Arris Mono'; color: #b8b1a3; text-transform: uppercase; letter-spacing: .06em; }
"""
    return body, 'Headline Light, deck Italic, text Regular 21/32; tabular figures in the sidebar', css


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


def _code(lines):
    """Lines of (text, class) runs as numbered code."""
    out = []
    for i, ln in enumerate(lines, 1):
        code = ''.join(f'<span class="{c}">{esc(t)}</span>' if c else esc(t) for t, c in ln)
        out.append(f'<div class="ln"><span class="no">{i}</span>{code}</div>')
    return ''.join(out)


CODE_CSS = """
.kw {{ color: {kw}; }} .ty {{ color: {ty}; }} .st {{ color: {st}; }} .cm {{ color: {cm}; font-style: italic; }}
.nu {{ color: {nu}; }} .fn {{ color: {fn}; }} .tg {{ color: {tg}; }} .at {{ color: {at}; }}
.no {{ display:inline-block; width: 64px; color: {no}; }}
"""


def _code_html():
    K, T, S, C, N, F = 'kw', 'ty', 'st', 'cm', 'nu', 'fn'
    lines = [
        [('// count the relay chatter, set in Arris Mono', C)],
        [('use', K), (' std::collections::HashMap;', '')],
        [('', '')],
        [('fn', K), (' ', ''), ('tally', F), ('(packets: &[&', ''), ('str', T), (']) -> ', ''), ('HashMap', T), ('<&', ''), ('str', T), (', ', ''), ('usize', T), ('> {', '')],
        [('    let', K), (' mut seen = ', ''), ('HashMap', T), ('::new();', '')],
        [('    for', K), (' p ', ''), ('in', K), (' packets.iter().filter(|p| p.len() >= ', ''), ('3', N), (') {', '')],
        [('        *seen.entry(p).or_insert(', ''), ('0', N), (') += ', ''), ('1', N), (';', '')],
        [('    }', '')],
        [('    seen', '')],
        [('}', '')],
        [('', '')],
        [('const', K), (' armed = (ice, key) => ice !== key && key <= ', ''), ('0x', N), ('FF', N), (';', '')],
        [('let', K), (' sectors = ', ''), ('0', N), ('..=', ''), ('9', N), ('; ', ''), ('/* ', C), ('inclusive', C), (' */', C)],
        [('shards |> map(decrypt) |> filter(clean)   ', ''), ('-- key <$> shards <*> ice', C)],
        [('if', K), (' node != home || id == ', ''), ('"', S), ('#{handle}', S), ('"', S), (' { ', ''), ('return', K), (' node -> home }', '')],
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
  <div class="tabs mono"><span class="on">relay.rs</span><span>uplink.ts</span><span>ice.md</span></div>
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


@slide('code-python', 'paper', 'Python')
def code_python():
    K, T, S, C, N, F = 'kw', 'ty', 'st', 'cm', 'nu', 'fn'
    lines = [
        [('# burns.py', C)],
        [('from', K), (' dataclasses ', ''), ('import', K), (' dataclass', '')],
        [],
        [('@dataclass', F), ('(frozen=', ''), ('True', K), (')', '')],
        [('class', K), (' ', ''), ('Burn', T), (':', '')],
        [('    body: ', ''), ('str', T)],
        [('    delta_v: ', ''), ('float', T), ('   ', ''), ('# km/s', C)],
        [],
        [('def', K), (' ', ''), ('cheapest', F), ('(bs: ', ''), ('list', T), ('[', ''), ('Burn', T), ('])', ''), (' -> ', ''), ('Burn', T), (' | ', ''), ('None', K), (':', '')],
        [('    ', ''), ('return', K), (' ', ''), ('min', F), ('(bs, key=', ''), ('lambda', K), (' b: b.delta_v, default=', ''), ('None', K), (')', '')],
        [],
        [('costly = [b ', ''), ('for', K), (' b ', ''), ('in', K), (' burns ', ''), ('if', K), (' b.delta_v >= ', ''), ('3.0', N), (' ', ''), ('and', K), (' b.body != ', ''), ('"Luna"', S), (']', '')],
        [('print', F), ('(', ''), ('f"{len(costly)} of {len(burns)} burns at 3 km/s or more"', S), (')', '')],
        [('assert', K), (' ', ''), ('2', N), (' ** ', ''), ('10', N), (' == ', ''), ('1_024', N), ('   ', ''), ('# ints stay exact', C)],
    ]
    body = f"""
<div class="win">
  <div class="tabs mono"><span class="on">burns.py</span><span>test_burns.py</span></div>
  <div class="code mono">{_code(lines)}</div>
  <div class="out mono"><span class="dim">$</span> python burns.py<br>3 of 41 burns at 3 km/s or more</div>
</div>"""
    css = """
.s-code-python .win { position:absolute; inset: 120px 96px 100px 96px; background:#fbf8f1; border: 2px solid var(--line); }
.s-code-python .tabs { display:flex; font-size: 22px; border-bottom: 2px solid var(--line); }
.s-code-python .tabs span { padding: 18px 30px; color: var(--dim); }
.s-code-python .tabs .on { color: var(--ink); background:#fff; border-right: 2px solid var(--line); }
.s-code-python .code { padding: 22px 40px; font-size: 29px; line-height: 1.42; white-space: pre; color:#1d1c19; }
.s-code-python .out { position:absolute; left:0; right:0; bottom:0; padding: 22px 40px; background:#151412; color:#f3eee3; font-size: 26px; line-height: 1.5; }
""" + CODE_CSS.format(kw='#c2410c', ty='#2f5cd6', st='#1f7a6c', cm='#9a9384', nu='#9333ea', fn='#b4235a', tg='#2f5cd6', at='#c2410c', no='#c9c1b0')
    return body, 'Arris Mono on paper: -> != >= == become arrows and signs; ** and 1_024 stay as written', css


@slide('code-react', 'violet', 'TypeScript and JSX')
def code_react():
    K, T, S, C, N, F, G, A = 'kw', 'ty', 'st', 'cm', 'nu', 'fn', 'tg', 'at'
    lines = [
        [('// Uplink.tsx', C)],
        [('import', K), (' { useMemo } ', ''), ('from', K), (' ', ''), ('"react"', S), (';', '')],
        [],
        [('type', K), (' ', ''), ('Props', T), (' = { pings?: ', ''), ('number', T), ('; handle: ', ''), ('string', T), (' };', '')],
        [],
        [('export const', K), (' ', ''), ('Uplink', F), (' = ({ pings = ', ''), ('0', N), (', handle }: ', ''), ('Props', T), (') => {', '')],
        [('  const', K), (' text = ', ''), ('useMemo', F), ('(() => (pings > ', ''), ('99', N), (' ? ', ''), ('"99+"', S), (' : ', ''), ('String', T), ('(pings)), [pings]);', '')],
        [('  if', K), (' (pings === ', ''), ('0', N), (' && !handle) ', ''), ('return', K), (' ', ''), ('null', K), (';', '')],
        [('  return', K), (' (', '')],
        [('    <', ''), ('section', G), (' ', ''), ('className', A), ('=', ''), ('"uplink"', S), (' ', ''), ('aria-live', A), ('=', ''), ('"polite"', S), ('>', '')],
        [('      <', ''), ('span', G), ('>', ''), ('{handle}', ''), ('</', ''), ('span', G), ('>', '')],
        [('      <', ''), ('b', G), (' ', ''), ('hidden', A), ('={pings !== ', ''), ('0', N), (' ? ', ''), ('undefined', K), (' : ', ''), ('true', K), ('}>{text}</', ''), ('b', G), ('>', '')],
        [('      <', ''), ('hr', G), (' />', '')],
        [('    </', ''), ('section', G), ('>', '')],
        [('  );', '')],
        [('};', '')],
    ]
    body = f"""
<div class="win">
  <div class="tabs mono"><span class="on">Uplink.tsx</span><span>Uplink.test.tsx</span><span>index.ts</span></div>
  <div class="code mono">{_code(lines)}</div>
</div>"""
    css = """
.s-code-react .win { position:absolute; inset: 120px 96px 100px 96px; background:#120c22; border: 2px solid var(--line); }
.s-code-react .tabs { display:flex; font-size: 22px; border-bottom: 2px solid var(--line); }
.s-code-react .tabs span { padding: 18px 30px; color: var(--dim); }
.s-code-react .tabs .on { color: var(--ink); background:#1b1330; border-right: 2px solid var(--line); }
.s-code-react .code { padding: 24px 40px; font-size: 30px; line-height: 1.45; white-space: pre; }
""" + CODE_CSS.format(kw='#ff5fae', ty='#7de0ff', st='#ffd36b', cm='#7c6aa0', nu='#c4a7ff', fn='#7cf29a', tg='#ff9e5e', at='#7de0ff', no='#3d3060')
    return body, 'Tags close as one sign: </ and /> join; => === !== become arrows and bars', css


@slide('code-functional', 'amber', 'Elixir and Haskell')
def code_functional():
    K, T, S, C, N, F = 'kw', 'ty', 'st', 'cm', 'nu', 'fn'
    ex = [
        [('defmodule', K), (' ', ''), ('Reactor', T), (' ', ''), ('do', K)],
        [('  @spec', F), (' mean([', ''), ('number', T), ('])', ''), (' :: ', ''), ('float', T)],
        [('  def', K), (' mean(core_temps) ', ''), ('do', K)],
        [('    core_temps', '')],
        [('    |> ', ''), ('Enum', T), ('.reject(&is_nil/', ''), ('1', N), (')', '')],
        [('    |> ', ''), ('Enum', T), ('.map(', ''), ('fn', K), (' r -> r * ', ''), ('1.0', N), (' ', ''), ('end', K), (')', '')],
        [('    |> ', ''), ('then', F), ('(&(', ''), ('Enum', T), ('.sum(&', ''), ('1', N), (') / length(&', ''), ('1', N), (')))', '')],
        [('  end', K)],
        [('end', K)],
        [],
        [('IO', T), ('.puts(', ''), ('"core: #{Reactor.mean([621, nil, 623])}"', S), (')', '')],
    ]
    hs = [
        [('module', K), (' ', ''), ('Main', T), (' ', ''), ('where', K)],
        [],
        [('parse', F), (' :: ', ''), ('String', T), (' -> ', ''), ('Maybe', T), (' ', ''), ('Int', T)],
        [('parse', F), (' = readMaybe', '')],
        [],
        [('tonnage', F), (' :: [', ''), ('String', T), ('] -> ', ''), ('Maybe', T), (' ', ''), ('Int', T)],
        [('tonnage', F), (' xs = sum <$> traverse parse xs', '')],
        [],
        [('pair', F), (' = (,) <$> ', ''), ('Just', T), (' ', ''), ('1', N), (' <*> ', ''), ('Just', T), (' ', ''), ('2', N)],
        [('main', F), (' = print (tonnage [', ''), ('"3000"', S), (', ', ''), ('"470"', S), ('])', '')],
    ]
    body = f"""
<div class="two">
  <div class="win"><div class="tabs mono"><span class="on">reactor.ex</span></div><div class="code mono">{_code(ex)}</div></div>
  <div class="win"><div class="tabs mono"><span class="on">Cargo.hs</span></div><div class="code mono">{_code(hs)}</div></div>
</div>"""
    css = """
.s-code-functional .two { position:absolute; inset: 120px 96px 100px 96px; display:grid; grid-template-columns: 1fr 1fr; gap: 36px; }
.s-code-functional .win { background:#14110b; border: 2px solid var(--line); }
.s-code-functional .tabs { display:flex; font-size: 22px; border-bottom: 2px solid var(--line); }
.s-code-functional .tabs span { padding: 18px 30px; color: var(--accent); }
.s-code-functional .code { padding: 26px 30px; font-size: 27px; line-height: 1.55; white-space: pre; color: #f6e7c8; }
""" + CODE_CSS.format(kw='#ff6a2a', ty='#ffd36b', st='#9fe08a', cm='#7a5a1a', nu='#f6a6ff', fn='#ffb000', tg='#ffb000', at='#ffb000', no='#4a3a18')
    return body, 'Pipelines and applicatives: |> <$> <*> :: -> #{ in one family', css


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
    flights = [('03:15', 'REYKJAVÍK', 'MG 455', 'B12', 'ON TIME'), ('03:40', 'KRAKÓW', 'MG 282', 'C04', 'BOARDING'),
               ('04:05', 'İSTANBUL', 'HX 1980', 'D21', 'DELAYED 04:50'), ('04:20', 'CERES', 'OR 7', 'X01', 'BURN T−04:12'),
               ('04:45', 'LUNA GATE', 'OR 1', 'L01', 'FUELLING'), ('05:08', 'ΑΘΗΝΑ', 'MG 611', 'C17', 'ON TIME'),
               ('05:30', 'SECTOR 9', 'LC 438', 'A09', 'LOCKDOWN'), ('05:55', 'GANYMEDE', 'OR 12', 'X04', 'QUARANTINE')]

    def tiles(s, n):
        s = s.ljust(n)[:n]
        return ''.join(f'<span class="t">{esc(ch) if ch != " " else "&nbsp;"}</span>' for ch in s)
    rows = ''.join(f'<div class="r">{tiles(t, 5)}<span class="gap"></span>{tiles(d, 10)}<span class="gap"></span>{tiles(f, 7)}'
                   f'<span class="gap"></span>{tiles(g, 3)}<span class="gap"></span><span class="st {"warn" if any(k in s for k in ("DEL", "CAN", "LOCK", "QUAR")) else ""}">{tiles(s, 13)}</span></div>'
                   for t, d, f, g, s in flights)
    head = '<div class="h mono"><span>Time</span><span>Destination</span><span>Line</span><span>Gate</span><span>Remarks</span></div>'
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
<div class="g">{gauge}<div class="read"><div class="v">412</div><div class="u label">m/s Δv left</div></div></div>
<div class="side">
  <div class="it"><div class="label">Thrust</div><div class="n">1.3<small> g</small></div></div>
  <div class="it"><div class="label">Reactor</div><div class="n">87<small> %</small></div></div>
  <div class="it"><div class="label">Burn in</div><div class="n">↱ 4:12<small> min</small></div></div>
  <div class="it"><div class="label">Dock</div><div class="n accent2">B7</div></div>
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


def _telemetry():
    """A ship's console in Arris Mono, 96 cells wide: (text, class) runs per line."""
    import math
    W = 96

    def box(title, w, rows):
        top = [('╭─ ', 'b'), (title, 't'), (' ' + '─' * (w - 5 - len(title)) + '╮', 'b')]
        out = [top]
        for r in rows:
            n = sum(len(t) for t, _ in r)
            out.append([('│ ', 'b')] + r + [(' ' * (w - 4 - n) + ' │', 'b')])
        out.append([('╰' + '─' * (w - 2) + '╯', 'b')])
        return out

    def spark(f, n):
        bars = '▁▂▃▄▅▆▇█'
        return ''.join(bars[min(7, max(0, int(f(i) * 8)))] for i in range(n))

    def gauge(frac, n):
        eighths = ' ▏▎▍▌▋▊▉█'
        full = int(frac * n)
        rest = int((frac * n - full) * 8)
        return '█' * full + (eighths[rest] if full < n else '') + ' ' * max(0, n - full - 1)

    core = spark(lambda i: 0.55 + 0.3 * math.sin(i / 3.1) + 0.12 * math.sin(i / 1.3), 30)
    flux = spark(lambda i: 0.2 + 0.75 * math.exp(-((i - 21) / 4.0) ** 2) + 0.05 * math.sin(i), 30)
    left = (box('REACTOR', 48, [[('core   ', 'l'), ('623 K ', 'v'), (core, 'g')],
                                [('output ', 'l'), (' 87 % ', 'v'), (gauge(0.87, 30), 'g')],
                                [('flux   ', 'l'), ('  ok  ', 'v'), (flux, 'w')]])
            + box('LIFE SUPPORT', 48, [[('O₂     ', 'l'), ('20.9 %', 'v'), (' ', ''), (gauge(0.70, 29), 'g')],
                                       [('CO₂    ', 'l'), (' 0.4 %', 'v'), (' ', ''), (gauge(0.08, 29), 'w')],
                                       [('hull   ', 'l'), ('  99 %', 'v'), (' ', ''), (gauge(0.99, 29), 'g')]]))
    right = (box('NAVIGATION', 47, [[('body   ', 'l'), ('CERES', 'v')],
                                    [('Δv     ', 'l'), ('412 m/s', 'v'), ('  left', 'l')],
                                    [('burn   ', 'l'), ('T−04:12', 'a'), ('  ↱ prograde', 'l')],
                                    [('range  ', 'l'), ('1.71 AU', 'v'), ('  light +14m', 'l')]])
             + box('LOG', 47, [[('03:47:12 ', 'l'), ('✓', 'g'), (' dock clamps released', '')],
                               [('03:47:40 ', 'l'), ('⚠', 'w'), (' micrometeoroid flux high', '')],
                               [('03:48:02 ', 'l'), ('✗', 'e'), (' relay SECTOR 9 lost', '')],
                               [('03:48:30 ', 'l'), ('✓', 'g'), (' burn plan locked', '')]]))
    lines = []
    for i in range(max(len(left), len(right))):
        l = left[i] if i < len(left) else [(' ' * 48, '')]
        r = right[i] if i < len(right) else []
        lines.append(l + [(' ', '')] + r)
    # the burn profile: thrust over the burn, two rows of blocks stacked (16 levels)
    n = 85

    def thrust(i):
        t = i / (n - 1)
        ramp = min(1.0, t / 0.12) * min(1.0, (1 - t) / 0.08)
        return max(0.0, min(1.0, ramp * (0.82 + 0.1 * math.sin(t * 19) + 0.08 * math.sin(t * 47))))
    bars = ' ▁▂▃▄▅▆▇█'
    hi, lo = '', ''
    for i in range(n):
        lv = int(round(thrust(i) * 16))
        lo += bars[min(8, lv)]
        hi += bars[max(0, lv - 8)]
    axis = ''.join('┼' if i % 10 == 0 else '─' for i in range(n))
    marks = ''.join(f'{("T 0" if k == 4 else "T" + ("−" if k < 4 else "+") + str(abs(k - 4) * 10)):<10}' for k in range(9))[:n]
    lines += box('BURN PROFILE', 96, [[('thrust ', 'l'), (hi, 'a')],
                                      [('  1.3 g', 'v'), (lo, 'a')],
                                      [('       ', ''), (axis, 'b')],
                                      [('       ', ''), (marks, 'l')]])
    return lines


@slide('telemetry', 'slate', 'Ship systems')
def telemetry():
    out = []
    for ln in _telemetry():
        out.append(''.join(f'<span class="{c}">{esc(t)}</span>' if c else esc(t) for t, c in ln))
    body = f'<pre class="con mono">{chr(10).join(out)}</pre>'
    css = """
.s-telemetry .con { position:absolute; left: 96px; top: 150px; font-size: 31.1419px; line-height: 37px; color: var(--ink); }
/* cells 18 px wide; rows a whole 37 px, so stacked blocks overlap a hair instead of leaving a seam */
.s-telemetry .b { color: #2e4258; } .s-telemetry .t { color: var(--accent); } .s-telemetry .l { color: #6f86a0; }
.s-telemetry .v { color: #f1f5fa; } .s-telemetry .g { color: #7cf29a; } .s-telemetry .w { color: #ffb000; }
.s-telemetry .e { color: #ff79c6; } .s-telemetry .a { color: #3fd6ff; }
"""
    return body, 'Box drawing with round corners; sparklines and a two-row chart from the eight lower blocks; gauges in eighths', css


def _flyby(cx, cy, rp, e, th0, th1, n=90):
    """Points of a hyperbolic flyby (Jupiter at the focus, perijove straight
    up the screen) from true anomaly th0 to th1, in degrees."""
    import math
    out = []
    for k in range(n + 1):
        th = math.radians(th0 + (th1 - th0) * k / n)
        r = rp * (1 + e) / (1 + e * math.cos(th))
        out.append((cx + r * math.sin(th), cy - r * math.cos(th)))
    return out


@slide('slingshot', 'void', 'Slingshot')
def slingshot():
    import math
    jup = (SOURCES / 'jupiter-hubble-2014.jpg').as_uri()
    cx, cy, R = 700, 1290, 760                                  # Jupiter on the screen: centre, radius
    rp, e = 1.12 * R, 1.6
    pts = lambda a, b: ' '.join(f'{x:.0f},{y:.0f}' for x, y in _flyby(cx, cy, rp, e, a, b))
    sx, sy = _flyby(cx, cy, rp, e, -13, -13, 1)[0]
    px, py = _flyby(cx, cy, rp, e, 0, 0, 1)[0]
    ticks = ''.join(f'<span class="{"big" if h % 10 == 0 else ""}" style="left:{(h - 246) * 18}px">{h if h % 10 == 0 else ""}</span>'
                    for h in range(246, 297))
    gbar = ''.join(f'<i class="{"on" if k < 13 else ""} {"hot" if k >= 10 else ""}"></i>' for k in range(20))
    chat = [('beltalowda_88', '#7cf29a', 'Oye, beratnas! juice time ⚡'),
            ('mira.okonkwo', '#ff8ad8', 'sasa ke? why burn at perijove'),
            ('dock_rat', '#6fd3ff', 'Oberth, kopeng. more Δv per kilo of mass'),
            ('ceres_nights', '#ffd36b', 'taki bosmang ♥'),
            ('la_tormenta', '#ff79c6', '¡vamos! 3 g y nadie vomita'),
            ('pilot_tanya', '#9ad6ff', 'держись, пилот! ★'),
            ('kopeng_zero', '#7cf29a', 'Showxa! Beltalowda!'),
            ('lumière', '#c8ff3a', 'c’est magnifique, Jupiter'),
            ('rafa.br', '#ffb000', 'vai vai vai, olha a mancha vermelha'),
            ('nikos_r', '#6fd3ff', 'Μπράβο, καπετάνιε'),
            ('linh.tran', '#ff8ad8', 'chúc may mắn, đừng ngất nhé'),
            ('hal_n_teo', '#ffd36b', 'Glasshouse says: water the roses after ♥'),
            ('beltalowda_88', '#7cf29a', 'mi pensa im gonya na fong'),
            ('mod_dock', '#ff5f5f', '[mod] no spoilers for the burn pls'),
            ('dock_rat', '#6fd3ff', 'T−41 s. hands off the stick'),
            ('oyedeng', '#c8ff3a', 'Oyedeng, sasa ke Ceres ♥')]
    msgs = ''.join(f'<div class="m"><b style="color:{c}">{esc(u)}</b> {esc(t)}</div>' for u, c, t in chat)
    body = f"""
<div class="space"></div>
<img class="jup" src="{jup}" style="left:{cx - R}px;top:{cy - R}px;width:{2 * R}px;height:{2 * R}px">
<div class="atm" style="left:{cx - R - 40}px;top:{cy - R - 40}px;width:{2 * R + 80}px;height:{2 * R + 80}px"></div>
<svg class="orbit" width="1920" height="1080">
  <polyline points="{pts(-118, -13)}" class="past"/>
  <polyline points="{pts(-13, 118)}" class="next"/>
  <polyline points="{pts(-5, 5)}" class="burn"/>
  <circle cx="{px:.0f}" cy="{py:.0f}" r="7" class="pj"/>
  <line x1="{px:.0f}" y1="{py:.0f}" x2="{px:.0f}" y2="{py - 70:.0f}" class="lead"/>
</svg>
<div class="tag pjt mono" style="left:{px - 60:.0f}px;top:{py - 112:.0f}px">PERIJOVE<br><span>1.12 RJ · T+12:07</span></div>
<div class="ship mono" style="left:{sx - 22:.0f}px;top:{sy - 22:.0f}px">◆</div>
<div class="tag shipt mono" style="left:{sx - 60:.0f}px;top:{sy + 30:.0f}px">KOPENG · 61.4 KM/S<br><span>BURN ARMED</span></div>
<div class="tape mono"><div class="ticks">{ticks}</div><div class="hd">271°</div></div>
<div class="pane fl mono">
  <div class="h">Flight</div>
  <div class="row"><span>VEL</span><b>61.4</b><i>km/s</i></div>
  <div class="row"><span>ALT</span><b>18 220</b><i>km</i></div>
  <div class="row"><span>OBERTH</span><b>+9.8</b><i>km/s</i></div>
  <div class="row"><span>Δv LEFT</span><b>42</b><i>%</i></div>
  <div class="bar"><div style="width:42%"></div></div>
  <div class="h2">Burn in</div>
  <div class="cd">T−00:41</div>
</div>
<div class="pane gl mono">
  <div class="h">Load</div>
  <div class="g"><b>3.2</b> g</div>
  <div class="gb">{gbar}</div>
  <div class="warn">● JUICE ON · CREW 4/4</div>
</div>
<div class="pane sys mono">
  <div class="cell"><span>DRIVE</span><b>74%</b></div>
  <div class="cell"><span>REACTOR</span><b>98%</b></div>
  <div class="cell"><span>PDC</span><b>2 400</b></div>
  <div class="cell"><span>TIGHTBEAM</span><b>CERES · 41 MIN</b></div>
</div>
<div class="att mono">PITCH +04.2 · YAW −11.0 · ROLL 000.0</div>
<div class="chat">
  <div class="top mono"><span class="live">● LIVE</span> BELTCAST <span class="v">14 312 watching</span></div>
  <div class="ttl">slingshot @ jupiter · 3 g · nobody pukes (again)</div>
  <div class="msgs">{msgs}</div>
  <div class="in mono">Send a message <span>☺</span></div>
</div>
<div class="glass"></div>
<svg class="frame" width="1920" height="1080"><path fill-rule="evenodd" d="M0 0H1920V1080H0Z M150 92 H1770 L1880 202 V880 L1770 990 H150 L40 880 V202 Z"/></svg>
<div class="rivets"></div>"""
    css = """
.s-slingshot { background: #010205; }
.s-slingshot .space { position:absolute; inset:0; background:
   radial-gradient(1px 1px at 12% 18%, #fff, transparent), radial-gradient(1px 1px at 33% 9%, #cfe, transparent),
   radial-gradient(1.5px 1.5px at 58% 22%, #fff, transparent), radial-gradient(1px 1px at 71% 14%, #bdf, transparent),
   radial-gradient(1px 1px at 22% 35%, #fff, transparent), radial-gradient(1px 1px at 46% 31%, #fff, transparent),
   radial-gradient(1px 1px at 64% 40%, #def, transparent), radial-gradient(1.5px 1.5px at 8% 44%, #fff, transparent),
   #010205; }
.s-slingshot .jup { position:absolute; mix-blend-mode: screen; filter: saturate(1.25) contrast(1.1) brightness(1.3); }
.s-slingshot .atm { position:absolute; border-radius: 50%; box-shadow: 0 0 60px 18px rgba(255, 200, 150, .18), inset 0 0 50px 10px rgba(1,2,5,.6); }
.s-slingshot .orbit { position:absolute; left:0; top:0; }
.s-slingshot .orbit polyline { fill:none; }
.s-slingshot .orbit .past { stroke: rgba(111, 211, 255, .55); stroke-width: 2; }
.s-slingshot .orbit .next { stroke: #6fd3ff; stroke-width: 2.5; stroke-dasharray: 12 10; filter: drop-shadow(0 0 6px #00a3ff); }
.s-slingshot .orbit .burn { stroke: #ffb000; stroke-width: 7; filter: drop-shadow(0 0 10px #ff8a00); }
.s-slingshot .orbit .pj { fill: #010205; stroke: #ffb000; stroke-width: 3; }
.s-slingshot .orbit .lead { stroke: #ffb000; stroke-width: 1.5; }
.s-slingshot .tag { position:absolute; font-size: 15px; line-height: 1.35; letter-spacing: .08em; color: #ffb000; text-shadow: 0 0 8px rgba(255,138,0,.6); }
.s-slingshot .tag span { color: #ffd9a0; }
.s-slingshot .shipt { color: #9ff0ff; text-shadow: 0 0 8px rgba(0,163,255,.8); }
.s-slingshot .shipt span { color: #c8ff3a; }
.s-slingshot .ship { position:absolute; font-size: 36px; line-height: 1; color: #e6fbff; text-shadow: 0 0 10px #00a3ff, 0 0 24px #00a3ff; }
.s-slingshot .tape { position:absolute; left: 560px; top: 118px; width: 760px; height: 54px; overflow: hidden;
                     border-bottom: 1px solid rgba(111,211,255,.5); color: #6fd3ff; }
.s-slingshot .tape .ticks span { position:absolute; bottom: 0; width: 1px; height: 10px; background: rgba(111,211,255,.6); font-size: 14px; }
.s-slingshot .tape .ticks span.big { height: 20px; background: #6fd3ff; }
.s-slingshot .tape .ticks span.big::after { content: attr(data-x); }
.s-slingshot .tape .hd { position:absolute; left: 50%; top: 0; transform: translateX(-50%); padding: 2px 10px; background: #6fd3ff; color: #010205; font-size: 20px; font-weight: 600; }
.s-slingshot .pane { position:absolute; padding: 16px 20px; color: #bfeeff; background: rgba(3, 18, 28, .58); border: 1px solid rgba(111,211,255,.45);
                     clip-path: polygon(0 0, calc(100% - 18px) 0, 100% 18px, 100% 100%, 18px 100%, 0 calc(100% - 18px)); backdrop-filter: blur(3px); }
.s-slingshot .pane .h, .s-slingshot .pane .h2 { font-size: 13px; letter-spacing: .2em; text-transform: uppercase; color: #6fd3ff; margin-bottom: 10px; }
.s-slingshot .pane .h2 { margin: 16px 0 4px; }
.s-slingshot .fl { left: 96px; top: 230px; width: 330px; }
.s-slingshot .fl .row { display:flex; align-items: baseline; gap: 10px; padding: 5px 0; border-top: 1px solid rgba(111,211,255,.15); font-size: 15px; }
.s-slingshot .fl .row span { width: 90px; color: #6fd3ff; letter-spacing: .08em; }
.s-slingshot .fl .row b { font: 600 30px/1 'Arris'; color: #e6fbff; margin-left: auto; font-feature-settings: 'tnum'; }
.s-slingshot .fl .row i { font-style: normal; width: 44px; color: #6fd3ff; }
.s-slingshot .fl .bar { height: 8px; background: rgba(111,211,255,.15); margin-top: 8px; }
.s-slingshot .fl .bar div { height: 100%; background: #c8ff3a; box-shadow: 0 0 8px #c8ff3a; }
.s-slingshot .fl .cd { font: 600 64px/1 'Arris'; font-variation-settings: 'WTCH' 100; color: #ffb000; text-shadow: 0 0 14px rgba(255,138,0,.6); }
.s-slingshot .gl { left: 470px; top: 760px; width: 300px; }
.s-slingshot .gl .g { font: 300 26px 'Arris'; color: #ffb000; }
.s-slingshot .gl .g b { font: 700 72px/1 'Arris'; text-shadow: 0 0 16px rgba(255,138,0,.6); }
.s-slingshot .gl .gb { display:flex; gap: 3px; margin: 10px 0; }
.s-slingshot .gl .gb i { flex: 1; height: 16px; background: rgba(111,211,255,.15); }
.s-slingshot .gl .gb i.on { background: #6fd3ff; } .s-slingshot .gl .gb i.on.hot { background: #ff5f5f; box-shadow: 0 0 8px #ff2b2b; }
.s-slingshot .gl .warn { font-size: 13px; letter-spacing: .14em; color: #ff8a8a; }
.s-slingshot .sys { left: 810px; top: 846px; width: 540px; display:grid; grid-template-columns: 1fr 1fr; gap: 6px 20px; }
.s-slingshot .sys .cell { display:flex; justify-content: space-between; border-top: 1px solid rgba(111,211,255,.15); padding-top: 4px; font-size: 14px; letter-spacing: .1em; }
.s-slingshot .sys .cell span { color: #6fd3ff; } .s-slingshot .sys .cell b { color: #e6fbff; font-weight: 500; }
.s-slingshot .att { position:absolute; left: 560px; top: 190px; width: 760px; text-align: center; font-size: 14px; letter-spacing: .14em; color: rgba(159, 240, 255, .75); }
.s-slingshot .chat { position:absolute; right: 120px; top: 118px; bottom: 112px; width: 400px; display:flex; flex-direction: column;
                     background: rgba(10, 6, 20, .68); border: 1px solid rgba(255, 138, 216, .35); backdrop-filter: blur(4px); }
.s-slingshot .chat .top { padding: 12px 16px; font-size: 13px; letter-spacing: .12em; color: #e6dcff; border-bottom: 1px solid rgba(255,138,216,.25); }
.s-slingshot .chat .live { color: #ff3b5c; text-shadow: 0 0 8px #ff3b5c; }
.s-slingshot .chat .v { float: right; color: #a99bd0; }
.s-slingshot .chat .ttl { padding: 10px 16px; font: 600 17px/1.3 'Arris'; color: #fff; border-bottom: 1px solid rgba(255,138,216,.25); }
.s-slingshot .chat .msgs { flex: 1; overflow: hidden; display:flex; flex-direction: column; justify-content: flex-end; padding: 8px 16px; gap: 7px; }
.s-slingshot .chat .m { font: 400 16px/1.35 'Arris'; color: #ece6ff; }
.s-slingshot .chat .m b { font-weight: 700; }
.s-slingshot .chat .in { margin: 10px 14px 14px; padding: 9px 12px; border: 1px solid rgba(255,138,216,.35); color: #8e82b4; font-size: 14px; }
.s-slingshot .chat .in span { float: right; color: #ff8ad8; }
.s-slingshot .glass { position:absolute; inset:0; pointer-events:none;
   background: linear-gradient(115deg, rgba(255,255,255,0) 30%, rgba(190,230,255,.06) 38%, rgba(255,255,255,0) 44%),
               linear-gradient(115deg, rgba(255,255,255,0) 52%, rgba(190,230,255,.04) 55%, rgba(255,255,255,0) 58%),
               radial-gradient(ellipse at 20% 10%, rgba(120,200,255,.08), transparent 45%),
               repeating-linear-gradient(0deg, rgba(255,255,255,.012) 0 1px, transparent 1px 3px); }
.s-slingshot .frame { position:absolute; left:0; top:0; }
.s-slingshot .frame path { fill: #0b0d10; filter: drop-shadow(0 0 18px rgba(0,0,0,.9)); }
.s-slingshot .chrome, .s-slingshot .k-strip, .s-slingshot .k-xh { z-index: 2; }
"""
    return body, None, css


@slide('watches', 'night', 'Watch faces')
def watches():
    faces = [("10:08", "WED 22", "#ffb000", "#050607", 600, 100, 'oct'),
             ("21:47", "62 BPM", "#3fd6ff", "#04121a", 300, 0, 'round'),
             ("06:30", "RAIN 18°", "#151412", "#f3eee3", 800, 0, 'square'),
             ("12:00", "CERES +14m", "#ff5fae", "#17102a", 900, 100, 'oct')]
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


@slide('keys', 'bone', 'Keys and signs')
def keys():
    shortcuts = [('⌘ ⇧ B', 'Plot burn'), ('⌥ ⏎', 'Engage'), ('⎋', 'Abort burn'), ('⌃ ⌥ ⏏', 'Jettison cargo'),
                 ('⇧ ⇥', 'Next waypoint'), ('⌘ ⌫', 'Clear log'), ('⇪', 'Lock helm'), ('⌦', 'Purge buffer')]
    def caps(seq):
        return ''.join(f'<span class="k">{esc(k)}</span>' for k in seq.split())
    rows = ''.join(f'<div class="r"><span class="ks">{caps(k)}</span><span class="d">{esc(d)}</span></div>' for k, d in shortcuts)
    signs = '← ↑ → ↓ ⌂ ⌚ ⌛ ⏳ ★ ✦ ✓ ✗ ⚠ ⚡ ◆ ● ◐ ▲ ▶ ♫ ⌬ ⌀'
    body = f'<div class="grid">{rows}</div><div class="signs">{esc(signs)}</div>'
    css = """
.s-keys .grid { position:absolute; left:96px; right:96px; top: 140px; display:grid; grid-template-columns: 1fr 1fr; gap: 34px 90px; }
.s-keys .r { display:flex; align-items:center; gap: 34px; border-bottom: 2px solid var(--line); padding-bottom: 22px; }
.s-keys .ks { display:flex; gap: 14px; width: 330px; flex:none; }
.s-keys .k { display:inline-flex; align-items:center; justify-content:center; min-width: 92px; height: 92px; padding: 0 16px;
             font-size: 54px; font-weight: 500; background: #f6f2e9; color: var(--ink); border: 2px solid #c9c1ae;
             border-bottom-width: 7px; clip-path: polygon(14px 0, calc(100% - 14px) 0, 100% 14px, 100% calc(100% - 14px), calc(100% - 14px) 100%, 14px 100%, 0 calc(100% - 14px), 0 14px); }
.s-keys .d { font-size: 44px; font-weight: 400; }
.s-keys .signs { position:absolute; left:96px; right:96px; bottom: 120px; font-size: 64px; letter-spacing: .14em; color: var(--accent); }
"""
    return body, 'Keyboard and technical symbols, dingbats and shapes, from the same strokes', css


@slide('math', 'ink', 'Mathematics')
def math_():
    eqs = ['e<sup>iπ</sup> + 1 = 0',
           'Δv = vₑ ln(m₀ ⁄ m₁)',
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
<div class="blk b1"><div class="label">Arris</div><p>A chamfered sans grown from the figures of a watch. Chamfered corners, octagonal bowls, a notch where the 2 turns.</p></div>
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


def _kites():
    """A deltoidal hexecontahedron's kites, flattened: five round one of
    its five-fold vertices (67.78 degrees each, so 21.1 degrees are left
    over: the slit that lets the net fold up), and a few unfolded off their
    outer edges. Returns (kites, folds, cuts, tabs) as point lists."""
    import math
    alpha, L = math.radians(67.7834), 1.0
    S = L / ((7 + math.sqrt(5)) / 6)
    AC = L * math.cos(alpha / 2) + math.sqrt(S ** 2 - (L * math.sin(alpha / 2)) ** 2)

    def kite(theta):
        A = (0.0, 0.0)
        B = (L * math.cos(theta + alpha / 2), L * math.sin(theta + alpha / 2))
        C = (AC * math.cos(theta), AC * math.sin(theta))
        D = (L * math.cos(theta - alpha / 2), L * math.sin(theta - alpha / 2))
        return [A, B, C, D]

    def reflect(P, a, b):
        (x, y), (x1, y1), (x2, y2) = P, a, b
        dx, dy = x2 - x1, y2 - y1
        t = ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)
        return (2 * (x1 + t * dx) - x, 2 * (y1 + t * dy) - y)

    base = math.radians(-90 + 21.1 / 2) + alpha / 2
    flower = [kite(base + k * alpha) for k in range(5)]
    kites = list(flower)
    folds = [(flower[k][1], flower[k][0]) for k in range(1, 5)]          # A-B shared between neighbours
    extra = []
    for k, edge in ((0, (1, 2)), (2, (2, 3)), (3, (1, 2))):              # unfolded across an outer short edge
        K = flower[k]
        a, b = K[edge[0]], K[edge[1]]
        R = [reflect(P, a, b) for P in K]
        kites.append(R)
        extra.append((k, edge))
        folds.append((a, b))
    return kites, folds, AC, S


@slide('riso', 'paper', 'Cut and fold')
def riso():
    """A papercraft sheet on a cutting mat: part of the net of a deltoidal
    hexecontahedron, sixty kites, five of them round a vertex, three
    unfolded off their edges; cut lines, valley and mountain folds, glue
    tabs, and the letters on the faces hatched in line."""
    import math
    kites, folds, AC, S = _kites()
    sc, ox, oy = 430, 905, 520                                # px per long edge; the five-fold vertex
    P = lambda q: (ox + sc * q[0], oy - sc * q[1])
    fmt = lambda pts: ' '.join(f'{x:.1f},{y:.1f}' for x, y in map(P, pts))
    # the outline (cut): union of the kites' edges that only one kite has
    from collections import Counter
    key = lambda a, b: tuple(sorted(((round(a[0], 6), round(a[1], 6)), (round(b[0], 6), round(b[1], 6)))))
    count = Counter(key(k[i], k[(i + 1) % 4]) for k in kites for i in range(4))
    cuts = [(k[i], k[(i + 1) % 4]) for k in kites for i in range(4) if count[key(k[i], k[(i + 1) % 4])] == 1]
    fold_keys = {key(a, b) for a, b in folds}
    # glue tabs on some outer edges: trapezoids, sides at 45 degrees
    tabs = []
    for n, (a, b) in enumerate(cuts):
        if n % 3 != 1 or key(a, b) in fold_keys:
            continue
        (x1, y1), (x2, y2) = P(a), P(b)
        dx, dy = x2 - x1, y2 - y1
        l = math.hypot(dx, dy)
        nx, ny = dy / l, -dx / l                                   # outward: away from the vertex
        cx, cy = (x1 + x2) / 2 - ox, (y1 + y2) / 2 - oy
        if nx * cx + ny * cy < 0:
            nx, ny = -nx, -ny
        h = 0.16 * l
        ux, uy = dx / l, dy / l
        tabs.append([(x1, y1), (x1 + nx * h + ux * h, y1 + ny * h + uy * h),
                     (x2 + nx * h - ux * h, y2 + ny * h - uy * h), (x2, y2)])
    tab_edges = {(round(t[0][0], 1), round(t[0][1], 1), round(t[3][0], 1), round(t[3][1], 1)) for t in tabs}
    svg = []
    svg.append('<defs><pattern id="hatch" width="9" height="9" patternUnits="userSpaceOnUse" patternTransform="rotate(-45)">'
               '<rect width="9" height="4" fill="#1d1b17"/></pattern>'
               '<pattern id="hatch2" width="9" height="9" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
               '<rect width="9" height="3" fill="#d2452b"/></pattern>'
               '<filter id="lift" x="-10%" y="-10%" width="120%" height="120%"><feDropShadow dx="14" dy="20" stdDeviation="14" '
               'flood-color="#04150e" flood-opacity=".55"/></filter></defs>')
    # the card the net is cut from: kites, tabs, one filled shape lifted off the mat
    shape = ''.join(f'<polygon points="{fmt(k)}"/>' for k in kites) + ''.join(
        '<polygon points="' + ' '.join(f'{x:.1f},{y:.1f}' for x, y in t) + '"/>' for t in tabs)
    svg.append(f'<g filter="url(#lift)" fill="#f4efe2">{shape}</g>')
    tints = ['#f4efe2', '#efe7d3', '#f4efe2', '#efe7d3', '#f4efe2', '#e9dfc7', '#e9dfc7', '#e9dfc7']
    for k, t in zip(kites, tints):
        svg.append(f'<polygon points="{fmt(k)}" fill="{t}"/>')
    for t in tabs:
        pts = ' '.join(f'{x:.1f},{y:.1f}' for x, y in t)
        svg.append(f'<polygon points="{pts}" fill="#e3d6b8"/>')
        mx, my = sum(q[0] for q in t) / 4, sum(q[1] for q in t) / 4
        ang = math.degrees(math.atan2(t[3][1] - t[0][1], t[3][0] - t[0][0]))
        if ang > 90 or ang < -90:
            ang += 180
        svg.append(f'<text x="{mx:.1f}" y="{my:.1f}" transform="rotate({ang:.1f} {mx:.1f} {my:.1f})" class="glue">GLUE</text>')
    # letters on the faces, hatched in line, along each kite's axis
    word = 'ARRIS&?0'
    for n, (k, ch) in enumerate(zip(kites, word)):
        cx = (k[0][0] + k[1][0] + k[2][0] + k[3][0]) / 4
        cy = (k[0][1] + k[1][1] + k[2][1] + k[3][1]) / 4
        x, y = P((cx, cy))
        ang = math.degrees(math.atan2(k[2][1] - k[0][1], k[2][0] - k[0][0]))
        rot = -(ang - 90)
        fill = 'url(#hatch2)' if n == 4 else 'url(#hatch)'
        svg.append(f'<text x="{x:.1f}" y="{y:.1f}" transform="rotate({rot:.1f} {x:.1f} {y:.1f})" class="face" fill="{fill}" '
                   f'stroke="#1d1b17" stroke-width="2">{esc(ch)}</text>')
        svg.append(f'<text x="{x:.1f}" y="{y + 64:.1f}" transform="rotate({rot:.1f} {x:.1f} {y:.1f})" class="no">{n + 1:02d}</text>')
    # folds: valley dashed, mountain dash-dot
    for n, (a, b) in enumerate(folds):
        (x1, y1), (x2, y2) = P(a), P(b)
        dash = '14 9' if n < 4 else '16 6 3 6'
        svg.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#1d1b17" stroke-width="2.4" stroke-dasharray="{dash}"/>')
    # cuts: solid, except where a tab carries on (that edge is a fold too)
    for a, b in cuts:
        (x1, y1), (x2, y2) = P(a), P(b)
        if (round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)) in tab_edges:
            svg.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#1d1b17" stroke-width="2.4" stroke-dasharray="14 9"/>')
        else:
            svg.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#1d1b17" stroke-width="3"/>')
    for t in tabs:
        pts = ' '.join(f'{x:.1f},{y:.1f}' for x, y in t)
        svg.append(f'<polyline points="{pts}" fill="none" stroke="#1d1b17" stroke-width="3"/>')
    # the slit, and the scissors on it
    (sx1, sy1), (sx2, sy2) = P(kites[0][3]), P((0, 0))
    ang = math.degrees(math.atan2(sy2 - sy1, sx2 - sx1))
    svg.append(f'<text x="{sx1 + (sx2 - sx1) * .38:.1f}" y="{sy1 + (sy2 - sy1) * .38:.1f}" class="scis" '
               f'transform="rotate({ang:.1f} {sx1 + (sx2 - sx1) * .38:.1f} {sy1 + (sy2 - sy1) * .38:.1f})">✂</text>')
    # the mat: a grid, its inch rule, its 45 and 60 degree guides
    mat = ['<svg class="mat" width="1920" height="1080">']
    for x in range(0, 1921, 48):
        mat.append(f'<line x1="{x}" y1="0" x2="{x}" y2="1080" class="{"g5" if x % 240 == 0 else "g1"}"/>')
    for y in range(0, 1081, 48):
        mat.append(f'<line x1="0" y1="{y}" x2="1920" y2="{y}" class="{"g5" if y % 240 == 0 else "g1"}"/>')
    for x0 in (-600, 300, 1200):
        mat.append(f'<line x1="{x0}" y1="1080" x2="{x0 + 1080}" y2="0" class="g6"/>')
        mat.append(f'<line x1="{x0 + 400}" y1="1080" x2="{x0 + 400 + 1080 / math.tan(math.radians(60)):.0f}" y2="0" class="g6"/>')
    for i, x in enumerate(range(240, 1921, 240)):
        mat.append(f'<text x="{x + 6}" y="1046" class="ru">{i + 1}</text>')
    mat.append('</svg>')
    body = (''.join(mat) + f'<svg class="net" width="1920" height="1080">{"".join(svg)}</svg>'
            '<div class="sheet mono"><div class="t">D60 · Deltoidal hexecontahedron</div>'
            '<div>Sheet 1 of 6 · faces 01–08</div>'
            '<div class="key"><span class="k cut"></span>cut <span class="k val"></span>valley <span class="k mtn"></span>mountain</div>'
            '<div>Score every fold. Close the slit at 01 first; the five long edges meet at one point.</div></div>')
    css = """
.s-riso { background: #1f5a43; }
.s-riso .mat, .s-riso .net { position:absolute; left:0; top:0; }
.s-riso .mat .g1 { stroke: rgba(232, 255, 240, .10); stroke-width: 1; }
.s-riso .mat .g5 { stroke: rgba(232, 255, 240, .22); stroke-width: 1.5; }
.s-riso .mat .g6 { stroke: rgba(232, 255, 240, .12); stroke-width: 1; stroke-dasharray: 2 6; }
.s-riso .mat .ru { font: 500 18px 'Arris Mono'; fill: rgba(232, 255, 240, .5); }
.s-riso .net .face { font: 900 150px 'Arris'; text-anchor: middle; dominant-baseline: central; }
.s-riso .net .no { font: 500 16px 'Arris Mono'; fill: #8c8577; text-anchor: middle; letter-spacing: .1em; }
.s-riso .net .glue { font: 600 15px 'Arris Mono'; fill: #8c7d5c; text-anchor: middle; dominant-baseline: central; letter-spacing: .3em; }
.s-riso .net .scis { font: 400 84px 'Arris Mono'; fill: #1d1b17; text-anchor: middle; dominant-baseline: central; }
.s-riso .chrome, .s-riso .k-strip, .s-riso .k-xh { color: rgba(232, 255, 240, .7); }
.s-riso .chrome .k-brand { color: #f4efe2; }
.s-riso .sheet { position:absolute; left: 96px; bottom: 96px; width: 470px; padding: 22px 26px; background: #f4efe2; color: #1d1b17;
                 font-size: 15px; line-height: 1.5; box-shadow: 10px 14px 24px rgba(4, 21, 14, .5); transform: rotate(-2deg); }
.s-riso .sheet .t { font: 800 22px/1.2 'Arris'; text-transform: uppercase; letter-spacing: .02em; margin-bottom: 6px; }
.s-riso .sheet .key { margin: 10px 0; display:flex; align-items:center; gap: 10px; text-transform: uppercase; letter-spacing: .1em; font-size: 13px; }
.s-riso .sheet .k { display:inline-block; width: 46px; height: 0; border-top: 3px solid #1d1b17; }
.s-riso .sheet .val { border-top: 3px dashed #1d1b17; }
.s-riso .sheet .mtn { border-top: 0; height: 3px; background: repeating-linear-gradient(90deg, #1d1b17 0 14px, transparent 14px 18px, #1d1b17 18px 21px, transparent 21px 25px); }
"""
    return body, None, css


@slide('maze', 'slate', '10 PRINT')
def maze():
    import random
    rng = random.Random(10)
    cols, rows = 48, 10
    lines = []
    for r in range(rows):
        cells = []
        for c in range(cols):
            hue = 170 + 150 * (c / cols) + 20 * (r / rows)
            ch = '╱' if rng.random() < 0.5 else '╲'
            cells.append(f'<span style="color:hsl({hue:.0f} 85% 68%)">{ch}</span>')
        lines.append(''.join(cells))
    body = f'<pre class="mz mono">{chr(10).join(lines)}</pre><div class="cmd mono">10 PRINT CHR$(205.5+RND(1)); : GOTO 10</div>'
    css = """
.s-maze .mz { position:absolute; left: 96px; top: 130px; font-size: 62px; line-height: 1.2; font-weight: 300; }
.s-maze .cmd { position:absolute; left: 96px; bottom: 100px; font-size: 30px; color: var(--ink); }
"""
    return body, 'The box-drawing diagonals run corner to corner, so the maze joins cell to cell', css


SOURCES = ROOT / 'presentation' / 'sources'


def _rose_stipple(path, height, F, crop=(0.0, 0.0, 1.0, 0.835), adv=0.630):
    """A Redouté plate lifted off its paper and set as Braille stipple in
    Arris Mono at F px, ``height`` px tall: his engraving was dots, and so is
    this (Floyd-Steinberg onto the dot lattice, light as density); petals
    mapped to a hot gradient, leaves to a neon one. Returns (chars, colours,
    width px, alpha image at that size)."""
    import colorsys
    import numpy as np
    from PIL import Image, ImageFilter
    sys.path.insert(0, str(ROOT / 'tools'))
    import typeart as ta
    im = Image.open(path).convert('RGB')
    W0, H0 = im.size
    im = im.crop((int(crop[0] * W0), int(crop[1] * H0), int(crop[2] * W0), int(crop[3] * H0)))
    a = np.asarray(im, dtype=np.float32) / 255
    border = np.concatenate([a[:12].reshape(-1, 3), a[:, :12].reshape(-1, 3), a[:, -12:].reshape(-1, 3)])
    paper = np.median(border, 0)
    alpha = np.clip((np.sqrt(((a - paper) ** 2).sum(2)) - 0.12) / 0.12, 0, 1)
    alpha[:, :int(0.04 * alpha.shape[1])] = 0                       # the plate's edges
    alpha[:, -int(0.04 * alpha.shape[1]):] = 0
    alpha_im = Image.fromarray((alpha * 255).astype(np.uint8)).filter(ImageFilter.MedianFilter(7))
    cw, ch = adv * F, 1.2 * F                                       # Arris Mono Bold: its bigger dots, its own advance
    width = height * im.width / im.height
    cols, rows = int(width // cw), int(height // ch)
    gw, gh = cols * 2, rows * 4
    L = np.asarray(im.convert('L').resize((gw, gh), Image.LANCZOS), dtype=np.float32) / 255
    A = np.asarray(alpha_im.resize((gw, gh), Image.LANCZOS), dtype=np.float32) / 255
    lo, hi = np.percentile(L[A > 0.5], [2, 99.5])
    Ln = np.clip((L - lo) / (hi - lo), 0, 1)
    chars = ta.braille(A * (0.28 + 0.72 * Ln ** 0.85))
    rgb = np.asarray(im.resize((cols, rows), Image.LANCZOS), dtype=np.float32) / 255
    acell = np.asarray(alpha_im.resize((cols, rows), Image.LANCZOS), dtype=np.float32) / 255
    petal = [(0, (176, 22, 116)), (0.3, (244, 42, 176)), (0.55, (255, 74, 222)), (0.78, (255, 152, 112)), (1, (255, 242, 208))]
    leaf = [(0, (24, 128, 64)), (0.35, (44, 226, 112)), (0.65, (110, 255, 64)), (1, (232, 255, 166))]
    colours = []
    for r in range(rows):
        row = []
        for c in range(cols):
            if acell[r, c] < 0.2 or chars[r][c] == '⠀':
                row.append(None)
                continue
            h, l_, _ = colorsys.rgb_to_hls(*rgb[r, c])
            green = float(np.clip(1 - abs(h * 360 - 105) / 55, 0, 1))
            t = float(np.clip((l_ - 0.05) / 0.45, 0, 1))
            cp, cl = ta.gradient(petal, t), ta.gradient(leaf, t)
            row.append(ta.hexc(tuple(cp[i] + (cl[i] - cp[i]) * green for i in range(3))))
        colours.append(row)
    chars = [''.join(c_ if col else '⠀' for c_, col in zip(line, cl)) for line, cl in zip(chars, colours)]
    return chars, colours, cols * cw, alpha_im.resize((int(cols * cw), int(rows * ch)), Image.LANCZOS)


def _rose_ascii(path, height, F, crop=(0.0, 0.0, 1.0, 0.835), sub=(6, 12)):
    """The plate as ASCII in Arris Mono at F px: each cell the glyph whose
    shape best matches the engraving's lines and light (heavy ones too, the
    @ and $). Returns (chars, colours) on the same footing as the stipple."""
    import colorsys
    import numpy as np
    from PIL import Image, ImageFilter
    sys.path.insert(0, str(ROOT / 'tools'))
    import typeart as ta
    im = Image.open(path).convert('RGB')
    W0, H0 = im.size
    im = im.crop((int(crop[0] * W0), int(crop[1] * H0), int(crop[2] * W0), int(crop[3] * H0)))
    a = np.asarray(im, dtype=np.float32) / 255
    border = np.concatenate([a[:12].reshape(-1, 3), a[:, :12].reshape(-1, 3), a[:, -12:].reshape(-1, 3)])
    paper = np.median(border, 0)
    alpha = np.clip((np.sqrt(((a - paper) ** 2).sum(2)) - 0.12) / 0.12, 0, 1)
    alpha[:, :int(0.04 * alpha.shape[1])] = 0
    alpha[:, -int(0.04 * alpha.shape[1]):] = 0
    alpha_im = Image.fromarray((alpha * 255).astype(np.uint8)).filter(ImageFilter.MedianFilter(7))
    cw, ch = 0.578 * F, 1.2 * F
    width = height * im.width / im.height
    cols, rows = int(width // cw), int(height // ch)
    glyphs = ta.glyph_grids(BUILD / 'ArrisMono-Regular.ttf', [chr(c) for c in range(32, 127)], sub)
    big = (cols * sub[0], rows * sub[1])
    Lim = im.convert('L').resize(big, Image.LANCZOS)
    L = np.asarray(Lim, dtype=np.float32) / 255
    A = np.asarray(alpha_im.resize(big, Image.LANCZOS), dtype=np.float32) / 255
    lo, hi = np.percentile(L[A > 0.5], [2, 99.5])
    Ln = np.clip((L - lo) / (hi - lo), 0, 1)
    Lb = np.asarray(Lim.filter(ImageFilter.GaussianBlur(2)), dtype=np.float32) / 255
    gy, gx = np.gradient(Lb)
    E = np.hypot(gx, gy)
    E = np.clip(E / np.percentile(E[A > 0.5], 97), 0, 1)
    chars = ta.shapes(A * np.clip(0.10 + 0.55 * E + 0.38 * Ln, 0, 1) * 0.6, glyphs)
    rgb = np.asarray(im.resize((cols, rows), Image.LANCZOS), dtype=np.float32) / 255
    acell = np.asarray(alpha_im.resize((cols, rows), Image.LANCZOS), dtype=np.float32) / 255
    colours = []
    for r in range(rows):
        row = []
        for c in range(cols):
            if acell[r, c] < 0.3 or chars[r][c] == ' ':
                row.append(None)
                continue
            row.append(tuple(float(v) for v in rgb[r, c]))
        colours.append(row)
    return chars, colours


def _glitch(chars, colours, x0, y0, F, seed):
    """The ASCII rose laid over its stipple self, broken: horizontal slices
    of a few rows, about a third of them kept, each shoved sideways and
    turned to another hue, half their characters dropped."""
    import colorsys
    import random
    sys.path.insert(0, str(ROOT / 'tools'))
    import typeart as ta
    rng = random.Random(seed)
    ch = 1.2 * F
    out, r = [], 0
    while r < len(chars):
        n = rng.randint(1, 5)
        if rng.random() < 0.5:
            dx = rng.choice([-1, 1]) * rng.uniform(10, 64)
            rot = rng.choice([0.28, 0.42, 0.55, 0.72])                    # turns of the hue wheel
            lines = []
            for k in range(r, min(r + n, len(chars))):
                runs = []
                for c, cell in zip(chars[k], colours[k]):
                    if cell is None or rng.random() > 0.66:
                        runs.append(' ')
                        continue
                    h, l_, s_ = colorsys.rgb_to_hls(*cell)
                    rr, gg, bb = colorsys.hls_to_rgb((h + rot) % 1.0, min(0.80, 0.45 + 0.5 * l_), max(0.9, s_))
                    runs.append(f'<span style="color:{ta.hexc((rr * 255, gg * 255, bb * 255))}">{esc(c)}</span>')
                lines.append(''.join(runs))
            out.append(f'<pre class="gl mono" style="left:{x0 + 16 + dx:.0f}px;top:{y0 - 12 + r * ch:.0f}px">' + '\n'.join(lines) + '</pre>')
        r += n
    return ''.join(out)


def _garden():
    """The collage: Cassini's Saturn in Braille dots, Redouté's roses over it
    in ASCII, a tracking overlay. Returns html pieces and geometry."""
    import math
    import numpy as np
    from PIL import Image, ImageFilter
    sys.path.insert(0, str(ROOT / 'tools'))
    import typeart as ta

    # Saturn, at its own proportions: 13 px Braille, dots on a near-square lattice
    sF = 13.0
    scw, sch = 0.578 * sF, 1.2 * sF
    sat = Image.open(SOURCES / 'saturn-cassini-2004-10-06.jpg').convert('RGB')
    sw = 1880.0
    sh = sw * sat.height / sat.width                                       # the photograph's own aspect
    sx0, sy0 = 70.0, 40.0
    scols, srows = int(sw // scw), int(sh // sch)
    dot_w, dot_h = scw / 2, sch / 4                                        # 3.757 x 3.9 px
    gw, gh = int(round(sw / dot_w)), int(round(sh / dot_h))                # dots across and down, true to aspect
    lum = np.asarray(sat.convert('L').resize((gw, gh), Image.LANCZOS), dtype=np.float64) / 255
    lum = np.clip((lum - 0.02) / 0.72, 0, 1) ** 0.75
    lum = np.pad(lum, ((0, max(0, srows * 4 - gh)), (0, max(0, scols * 2 - gw))))[:srows * 4, :scols * 2]
    cellum = np.asarray(sat.convert('L').resize((scols, srows), Image.LANCZOS), dtype=np.float64) / 255

    # the roses, laid over the planet, and their ASCII selves broken over them
    roses, glitch = [], []
    for path, height, cx, cy, fx, fy in ((SOURCES / 'redoute-rosa-gallica-flore-giganteo.jpg', 900, 700, 470, 0.46, 0.31),
                                          (SOURCES / 'redoute-rosa-gallica-regalis.jpg', 600, 1520, 372, 0.50, 0.25)):
        chars, colours, width, amask = _rose_stipple(path, height, 10.0)
        x0, y0 = cx - fx * width, cy - fy * height
        roses.append((chars, colours, x0, y0, amask))
        achars, acols = _rose_ascii(path, height, 15.0)
        glitch.append(_glitch(achars, acols, x0, y0, 15.0, seed=len(glitch) + 7))

    # knock the planet out behind the roses
    ko = Image.new('L', (1920, 1080), 0)
    for _, _, x0, y0, amask in roses:
        ko.paste(amask, (int(x0), int(y0)), amask)
    ko = np.asarray(ko.filter(ImageFilter.MaxFilter(9)), dtype=np.float32) / 255
    for r in range(srows):
        for c in range(scols):
            for dy in range(4):
                for dx in range(2):
                    x, y = int(sx0 + c * scw + (0.25 + 0.5 * dx) * scw), int(sy0 + r * sch + (dy + 0.5) * dot_h)
                    if 0 <= x < 1920 and 0 <= y < 1080 and ko[y, x] > 0.15:
                        lum[r * 4 + dy, c * 2 + dx] = 0
    schars = ta.braille(lum)
    satmap = [(0, (42, 15, 110)), (0.3, (123, 44, 255)), (0.5, (25, 195, 255)), (0.7, (60, 255, 122)), (0.86, (200, 255, 58)), (1, (255, 255, 255))]
    scol = [[ta.hexc(ta.gradient(satmap, cellum[r, c] ** 0.7)) if schars[r][c] != '⠀' else None for c in range(scols)]
            for r in range(srows)]
    sat_html = ta.cells_html(schars, scol, esc)
    rose_html = [(ta.cells_html(ch_, co_, esc), x0, y0) for ch_, co_, x0, y0, _ in roses]

    # the globe's ellipse on the slide, for the graticule and the readout
    gcx, gcy, grx, gry = sx0 + 0.49 * sw, sy0 + 0.575 * sh, 0.175 * sw, 0.235 * sh

    def dots(pts, cls, ch='·'):
        return ''.join(f'<span class="{cls}" style="left:{x:.0f}px;top:{y:.0f}px">{ch}</span>' for x, y in pts)

    grat = []                                                              # the contact's orbit, dashed
    for i in range(0, 220):
        t = 2 * math.pi * i / 220
        x = gcx + 2.55 * grx * math.cos(t) * math.cos(-0.12) - 1.05 * gry * math.sin(t) * math.sin(-0.12)
        y = gcy + 2.55 * grx * math.cos(t) * math.sin(-0.12) + 1.05 * gry * math.sin(t) * math.cos(-0.12)
        if i % 4 < 2:
            grat.append((x, y))
    # the contact off the limb, its trail and predicted track to the ring
    sx, sy = 300.0, 205.0
    trail = [(sx - 9 * i, sy - 4.2 * i) for i in range(1, 16)]
    track = []
    for i in range(1, 64):
        t = i / 64
        bx = (1 - t) ** 2 * sx + 2 * (1 - t) * t * 430 + t * t * 900
        by = (1 - t) ** 2 * (sy + 58) + 2 * (1 - t) * t * 420 + t * t * 330
        if i % 3 != 2:
            track.append((bx, by))
    geo = dict(sx0=sx0, sy0=sy0, sF=sF, gcx=gcx, gcy=gcy, ship=(sx, sy))
    return sat_html, rose_html, ''.join(glitch), dots(grat, 'gr'), dots(trail, 'tr'), dots(track, 'tk'), geo


def _signal(cols=40):
    """A signal trace in Braille: two rows of dots, a carrier with bursts."""
    import math
    rows = 2
    on = [[False] * (cols * 2) for _ in range(rows * 4)]
    for x in range(cols * 2):
        v = 0.5 + 0.32 * math.sin(x / 2.1) * (0.4 + 0.6 * abs(math.sin(x / 17))) + 0.12 * math.sin(x * 1.7)
        y = int(round((1 - v) * (rows * 4 - 1)))
        on[max(0, min(rows * 4 - 1, y))][x] = True
    bits = [(0, 0, 0x01), (0, 1, 0x02), (0, 2, 0x04), (1, 0, 0x08), (1, 1, 0x10), (1, 2, 0x20), (0, 3, 0x40), (1, 3, 0x80)]
    out = []
    for r in range(rows):
        out.append(''.join(chr(0x2800 + sum(b for dx, dy, b in bits if on[r * 4 + dy][c * 2 + dx])) for c in range(cols)))
    return '\n'.join(out)


@slide('garden', 'void', 'Garden in orbit')
def garden():
    sat, roses, glitch, grat, trail, track, g = _garden()
    plain = re.sub(r'style="color:[^"]*"', '', sat)
    rose_layers = ''.join(f'<pre class="rose mono" style="left:{x0:.0f}px;top:{y0:.0f}px">{h}</pre>' for h, x0, y0 in roses)
    sx, sy = g['ship']
    body = f"""
<div class="glow g1"></div><div class="glow g2"></div><div class="glow g3"></div>
<div class="sky">
  <pre class="sat ab1 mono">{plain}</pre>
  <pre class="sat ab2 mono">{plain}</pre>
  <pre class="sat mono">{sat}</pre>
</div>
<div class="hud">{grat}{trail}{track}</div>
{rose_layers}
{glitch}
<div class="ship" style="left:{sx - 9:.0f}px;top:{sy - 13:.0f}px">◆</div>
<pre class="ret mono" style="left:{sx - 52:.0f}px;top:{sy - 52:.0f}px">┌─        ─┐



└─        ─┘</pre>
<div class="lbl mono" style="left:{sx + 86:.0f}px;top:{sy - 44:.0f}px">
  <div class="b">TRK 041 ▸ CONTACT</div>
  <div>RNG 1.71 AU · BRG 233.7°</div>
  <div>Δv 412 m/s · T−04:12</div>
  <div class="b">LOCK ▮▮▮▮▯</div>
</div>
<div class="lat mono" style="left:{g['gcx'] + 300:.0f}px;top:{g['gcy'] + 210:.0f}px">
  <span class="x">+</span> LAT −12.40° · LON 233.71°
</div>
<div class="sig mono">
  <div class="h">SIG ▸ 8.4 GHz · S/N 31 dB</div>
  <pre class="w">{_signal()}</pre>
  <div class="la">SIGNVM SISTERE NON POTES</div>
</div>
<div class="tc mono"><span class="rec">●</span> REC · FRM 0041 · 03:47:12.08 UTC</div>
<pre class="lost mono">┌       ┐
   ◇
└       ┘</pre>
<div class="lostl mono">TRK 042 · SIGNAL LOST<br><span>LAST FIX 03:41:57 · RNG 2.06 AU</span></div>
<div class="scale mono"><span class="t">0</span><span class="bar"></span><span class="t">100 000 km</span></div>
<div class="latin">per aspera ad astra</div>
<div class="spec"><i>Rosa gallica</i> · flore giganteo</div>
<div class="scan"></div>"""
    css = f"""
.s-garden {{ background: #03020a; }}
.s-garden .glow {{ position:absolute; border-radius: 50%; filter: blur(40px); pointer-events:none; }}
.s-garden .g1 {{ left: {sx - 120:.0f}px; top: {sy - 110:.0f}px; width: 240px; height: 220px; background: radial-gradient(circle, rgba(0,163,255,.55), rgba(0,163,255,0) 70%); }}
.s-garden .g2 {{ left: 1180px; top: 560px; width: 520px; height: 360px; background: radial-gradient(circle, rgba(0,120,255,.20), rgba(0,120,255,0) 70%); }}
.s-garden .g3 {{ left: 60px; top: 860px; width: 600px; height: 200px; background: radial-gradient(circle, rgba(0,180,255,.18), rgba(0,180,255,0) 70%); }}
.s-garden .sat {{ position:absolute; left: {g['sx0']}px; top: {g['sy0']}px; font-size: {g['sF']}px; line-height: 1.2; font-weight: 400; }}
.s-garden .ab1 {{ color: #ff00c8; mix-blend-mode: screen; opacity: .38; transform: translateX(-2px); }}
.s-garden .ab2 {{ color: #00e5ff; mix-blend-mode: screen; opacity: .38; transform: translateX(2px); }}
.s-garden .rose {{ position:absolute; font-size: 10px; line-height: 1.2; font-weight: 700; text-shadow: 0 0 6px rgba(255, 60, 214, .55), 0 0 18px rgba(255, 43, 214, .18); }}
.s-garden .hud span {{ position:absolute; font: 400 14px/1 'Arris Mono'; transform: translate(-50%, -50%); }}
.s-garden .gr {{ color: rgba(111, 211, 255, .55); text-shadow: 0 0 6px rgba(0,163,255,.8); }}
.s-garden .tr {{ color: rgba(140, 220, 255, .55); }}
.s-garden .tk {{ color: #6fd3ff; text-shadow: 0 0 8px #00a3ff, 0 0 18px rgba(0,163,255,.6); }}
.s-garden .ship {{ position:absolute; font: 500 22px/1 'Arris'; color: #dff6ff; text-shadow: 0 0 10px #00a3ff, 0 0 24px #00a3ff, 0 0 48px rgba(0,163,255,.8); }}
.s-garden .ret {{ position:absolute; font-size: 18px; line-height: 1.2; color: #6fd3ff; text-shadow: 0 0 8px rgba(0,163,255,.8); }}
.s-garden .lbl {{ position:absolute; font-size: 15px; line-height: 1.45; color: #8fd8ff; letter-spacing: .04em; text-shadow: 0 0 8px rgba(0,163,255,.55); }}
.s-garden .lbl .b {{ color: #e6f8ff; }}
.s-garden .lat {{ position:absolute; font-size: 15px; color: #b6ffcf; letter-spacing: .06em; background: rgba(3, 2, 10, .82); padding: 4px 10px 4px 6px; }}
.s-garden .lat .x {{ color: #39ff14; font-size: 22px; vertical-align: -3px; margin-right: 8px; }}
.s-garden .sig {{ position:absolute; left: 96px; bottom: 70px; color: #6fd3ff; text-shadow: 0 0 8px rgba(0,163,255,.7); }}
.s-garden .sig .h {{ font-size: 14px; letter-spacing: .08em; margin-bottom: 6px; }}
.s-garden .sig .w {{ font-size: 16px; line-height: 1.2; color: #39c6ff; }}
.s-garden .sig .la {{ font: italic 300 15px/1 'Arris'; letter-spacing: .26em; margin-top: 12px; color: #c8ff3a; text-shadow: 0 0 8px rgba(200,255,58,.35); }}
.s-garden .gl {{ position:absolute; font-size: 15px; line-height: 1.2; font-weight: 500; mix-blend-mode: screen; opacity: .95;
               text-shadow: 0 0 6px rgba(0, 229, 255, .25); }}
.s-garden .tc {{ position:absolute; right: 96px; top: 92px; font-size: 14px; letter-spacing: .1em; color: #6c8f80; }}
.s-garden .tc .rec {{ color: #ff2bd6; text-shadow: 0 0 8px #ff2bd6; }}
.s-garden .latin {{ position:absolute; right: 96px; bottom: 72px; font: italic 300 30px/1 'Arris'; color: #c8ff3a; letter-spacing: .02em; text-shadow: 0 0 10px rgba(200,255,58,.35); }}
.s-garden .spec {{ position:absolute; left: 96px; top: 372px; font: 400 17px/1 'Arris'; color: #ff8ad8; letter-spacing: .03em; }}
.s-garden .lost {{ position:absolute; left: 1716px; top: 118px; font-size: 16px; line-height: 1.2; color: rgba(111, 211, 255, .45); }}
.s-garden .lostl {{ position:absolute; right: 96px; top: 184px; text-align: right; font-size: 13px; line-height: 1.5; letter-spacing: .06em; color: #ff5fae;
                   text-shadow: -2px 0 rgba(0, 229, 255, .6), 2px 0 rgba(255, 0, 200, .5); }}
.s-garden .lostl span {{ color: #6c8f80; text-shadow: none; }}
.s-garden .scale {{ position:absolute; left: 1150px; top: 872px; display:flex; align-items:center; gap: 12px; font-size: 13px; color: #6c8f80; letter-spacing: .06em; }}
.s-garden .scale .bar {{ display:inline-block; width: 240px; height: 7px; border: 1px solid #6c8f80; border-top: none; }}
.s-garden .scan {{ position:absolute; inset:0; pointer-events:none;
                  background: repeating-linear-gradient(to bottom, rgba(255,255,255,.035) 0 1px, transparent 1px 3px);
                  box-shadow: inset 0 0 220px rgba(0,0,0,.85); }}
"""
    return body, None, css


@slide('colophon', 'night', 'Colophon')
def colophon():
    import arris.glyphs  # noqa: F401
    from arris.glyphs.ligatures import LIGATURES
    stats = [('9', 'weights'), ('3', 'axes'), ('2,150', 'characters'), (str(len(LIGATURES)), 'ligatures'), ('6', 'families')]
    s = ''.join(f'<div><div class="n">{a}</div><div class="label">{b}</div></div>' for a, b in stats)
    codes = '<br>'.join(f'{t.upper()}-{k:03d}' for k, t in enumerate(_features(), 1))
    body = f"""
<div class="name">Arris</div>
<div class="tag">a chamfered sans</div>
<div class="stats">{s}</div>
<div class="card">
  <div class="h">Six families</div>
  <div class="b mono">Arris · Arris Italic · Arris Mono · Arris Mono Italic · Arris Watch ·
  Arris variable, wght 100–900, GRAD −100–100, WTCH 0–100</div>
  <div class="row mono"><span>TTF</span><span>WOFF2</span><span>Variable</span><a>Specimen [↗]</a></div>
</div>
<div class="codes mono">{codes}</div>"""
    css = """
.s-colophon .name { position:absolute; left: 80px; top: 100px; font-size: 380px; font-weight: 200; line-height: 1; }
.s-colophon .tag { position:absolute; left: 96px; top: 470px; font-size: 64px; font-style: italic; font-weight: 300; color: var(--dim); }
.s-colophon .stats { position:absolute; left: 96px; right: 96px; top: 640px; display:flex; justify-content:space-between; }
.s-colophon .n { font-size: 130px; font-weight: 700; color: var(--accent); line-height: 1; }
.s-colophon .stats .label { margin-top: 14px; }
.s-colophon .card { position:absolute; left: 0; bottom: 0; width: 820px; height: 196px; background: var(--accent); color: var(--bg); padding: 24px 30px 0 96px; }
.s-colophon .card .h { font: 800 34px/1 'Arris'; text-transform: uppercase; letter-spacing: .01em; }
.s-colophon .card .b { margin-top: 14px; font-size: 15px; line-height: 1.35; letter-spacing: .06em; text-transform: uppercase; }
.s-colophon .card .row { position:absolute; left: 96px; right: 0; bottom: 0; height: 46px; display:flex; align-items:center; gap: 34px;
                         font-size: 15px; letter-spacing: .1em; text-transform: uppercase; font-weight: 600; }
.s-colophon .card .row a { margin-left: auto; align-self: stretch; display:grid; place-items:center; padding: 0 34px; background: var(--bg); color: var(--ink); }
.s-colophon .codes { position:absolute; right: 96px; bottom: 50px; columns: 3; column-gap: 30px; font-size: 12px; line-height: 1.3; letter-spacing: .1em; color: var(--dim); text-align: right; }
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
        # grayscale anti-aliasing: LCD text bleeds colour into the next pixel,
        # which shows as fringes on block art and is no proof of a typeface
        browser = pw.chromium.launch(args=['--disable-lcd-text'])
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
    if only is None:                                   # a full render: no slide left over from an older numbering
        for f in (OUT / 'slides').glob('*.png'):
            f.unlink()
    render(pages, pdf=only is None)
