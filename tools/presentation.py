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


SERIES = ['#c98000', '#00a1cb', '#ea5098', '#73a500']   # validated (dataviz) on the night surface: band, CVD, contrast


def _optics_data():
    """Measured: each round's overshoot past its lines (mean of top and
    bottom, per cent of its zone) and the optical centre's rise (per cent of
    the zone) at each weight, from the engine with and without
    draw.OPTICAL."""
    sys.path.insert(0, str(ROOT / 'src'))
    import arris.glyphs  # noqa: F401
    import arris.draw as D
    from arris.font import place
    from arris.instances import params
    cfg = D.OPTICAL
    W = list(range(100, 901, 100))
    over = {}
    for label, n, zone in (('O', 'O', 720), ('C G S', 'S', 720), ('0 8', 'zero', 720), ('o c', 'o', 540)):
        row = []
        for w in W:
            p = params(w)
            D.OPTICAL = None
            r0, _ = place(n, p)
            D.OPTICAL = cfg
            r1, _ = place(n, p)
            y0 = [q[1] for r in r0 for q in r]
            y1 = [q[1] for r in r1 for q in r]
            row.append(100 * ((max(y1) - max(y0)) + (min(y0) - min(y1))) / 2 / zone)
        over[label] = row
    centre = {}
    for label, n, zone in (('Capitals · B E H 8', 'B', 720), ('Lowercase · a e', 'e', 540)):
        row = []
        for w in W:
            g = D.draw(n, params(w))                          # the correction as applied: its warp at the middle
            f = getattr(g, 'warp', None)
            row.append(100 * (f(zone / 2) - zone / 2) / zone if f else 0.0)
        centre[label] = row
    return W, over, centre


def _chart(W, series, x0, y0, w, h, ymax, yticks, unit, area=False, gid='c'):
    """A thin-line chart over weight, as SVG: recessive grid, a gradient wash
    under each line, a dot and a direct label (ink, beside a colour chip)
    at each line's end."""
    X = lambda wt: x0 + (wt - W[0]) / (W[-1] - W[0]) * w
    Y = lambda v: y0 + h - v / ymax * h
    out = [f'<defs>']
    for k, name in enumerate(series):
        c = SERIES[k]
        out.append(f'<linearGradient id="{gid}{k}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{c}" stop-opacity=".34"/>'
                   f'<stop offset="1" stop-color="{c}" stop-opacity="0"/></linearGradient>')
    out.append('</defs>')
    for t in yticks:
        out.append(f'<line x1="{x0}" y1="{Y(t):.1f}" x2="{x0 + w}" y2="{Y(t):.1f}" class="gl"/>'
                   f'<text x="{x0 - 12}" y="{Y(t) + 5:.1f}" class="yt">{t:g}{unit}</text>')
    for wt, lab in ((100, 'Thin'), (400, 'Regular'), (700, 'Bold'), (900, 'Black')):
        out.append(f'<text x="{X(wt):.1f}" y="{y0 + h + 28}" class="xt">{lab}</text>'
                   f'<line x1="{X(wt):.1f}" y1="{y0 + h}" x2="{X(wt):.1f}" y2="{y0 + h + 7}" class="gl"/>')
    labels = []
    for k, (name, vals) in enumerate(series.items()):
        c = SERIES[k]
        pts = ' '.join(f'{X(wt):.1f},{Y(v):.1f}' for wt, v in zip(W, vals))
        if area:
            out.append(f'<polygon points="{X(W[0]):.1f},{Y(0):.1f} {pts} {X(W[-1]):.1f},{Y(0):.1f}" fill="url(#{gid}{k})"/>')
        out.append(f'<polyline points="{pts}" class="ln" stroke="{c}" style="color:{c}"/>')
        out.append(f'<circle cx="{X(W[-1]):.1f}" cy="{Y(vals[-1]):.1f}" r="5" fill="{c}" class="dot"/>'
                   f'<circle cx="{X(W[0]):.1f}" cy="{Y(vals[0]):.1f}" r="5" fill="{c}" class="dot"/>')
        labels.append([Y(vals[-1]), name, c, vals[-1], vals[0]])
    labels.sort()
    for i in range(1, len(labels)):                               # keep the end labels apart
        labels[i][0] = max(labels[i][0], labels[i - 1][0] + 24)
    for yy, name, c, last, first in labels:
        out.append(f'<rect x="{x0 + w + 16}" y="{yy - 6:.1f}" width="12" height="12" rx="2" fill="{c}"/>'
                   f'<text x="{x0 + w + 36}" y="{yy + 5:.1f}" class="dl">{esc(name)}<tspan class="dv" dx="10">{first:.2f} → {last:.2f}{unit}</tspan></text>')
    return ''.join(out)


def _outline_svg(names, w, scale, ox, base, cls, warp=True):
    """Glyph outlines from the engine as one SVG path (even-odd), set side
    by side from ox along a baseline at y = base (SVG down), at a weight."""
    import arris.draw as D
    from arris.font import place
    from arris.instances import params
    cfg = D.OPTICAL
    D.OPTICAL = cfg if warp else None
    x, d = ox, []
    try:
        for n in names:
            rings, adv = place(n, params(w))
            for r in rings:
                d.append('M' + ' L'.join(f'{x + q[0] * scale:.2f},{base - q[1] * scale:.2f}' for q in r) + 'Z')
            x += adv * scale
    finally:
        D.OPTICAL = cfg
    return f'<path d="{" ".join(d)}" class="{cls}" fill-rule="evenodd"/>', x


@slide('squint', 'night', 'White that reads')
def squint():
    W, over, centre = _optics_data()
    glyphs = ''.join(f'<span style="filter: blur({b}px)">{esc(ch)}</span>'
                     for ch, b in zip('8B03@₦6', (0, 0.8, 1.6, 2.4, 3.2, 4.2, 5.4)))
    # overshoot, magnified: H and S at Regular on the cap line, a lens on S's top
    from arris.font import place
    from arris.instances import params
    sc, base = 0.38, 410
    h_s, xe = _outline_svg(['H', 'S'], 400, sc, 16, base, 'ink')
    cap_y = base - 720 * sc
    adv_h = place('H', params(400))[1] * sc
    s_rings, adv_s = place('S', params(400))
    top = max(q[1] for r in s_rings for q in r)
    xs_top = [q[0] for r in s_rings for q in r if q[1] > top - 0.5]
    fx = 16 + adv_h + (min(xs_top) + max(xs_top)) / 2 * sc     # the middle of S's top edge
    fy = cap_y
    k, R, lc = 20, 62, (150, 66)
    lens = (f'<clipPath id="lens"><circle cx="{lc[0]}" cy="{lc[1]}" r="{R}"/></clipPath>'
            f'<line x1="{fx:.1f}" y1="{fy - 2:.1f}" x2="{lc[0] + R * 0.8:.1f}" y2="{lc[1] + R * 0.6:.1f}" class="lensarm"/>'
            f'<g clip-path="url(#lens)"><rect x="{lc[0] - R}" y="{lc[1] - R}" width="{2 * R}" height="{2 * R}" class="lensbg"/>'
            f'<g transform="translate({lc[0]},{lc[1]}) scale({k}) translate({-fx:.2f},{-fy:.2f})">{h_s}'
            f'<line x1="0" y1="{cap_y:.2f}" x2="700" y2="{cap_y:.2f}" class="capln" vector-effect="non-scaling-stroke"/></g></g>'
            f'<circle cx="{lc[0]}" cy="{lc[1]}" r="{R}" class="lensring"/>'
            f'<circle cx="{fx:.1f}" cy="{fy - 1:.1f}" r="4" class="focus"/>')
    o_s = top - 720
    shoot = (f'<svg class="ov" width="530" height="440">'
             f'<line x1="0" y1="{base}" x2="530" y2="{base}" class="ruler"/><line x1="0" y1="{cap_y:.1f}" x2="530" y2="{cap_y:.1f}" class="capln"/>'
             f'<text x="526" y="{cap_y - 8:.1f}" class="lineL">cap line</text><text x="526" y="{base - 8:.1f}" class="lineL">baseline</text>'
             f'{h_s}{lens}<text x="{lc[0] + R + 16}" y="{lc[1] - 4}" class="ann">+{o_s:.1f} units</text>'
             f'<text x="{lc[0] + R + 16}" y="{lc[1] + 20}" class="ann2">S past the cap line, at Regular;</text>'
             f'<text x="{lc[0] + R + 16}" y="{lc[1] + 40}" class="ann2">H stays on it</text></svg>')
    # the optical centre: B at Light, as drawn (grey) and as corrected (outline)
    sb, bb = 0.48, 400
    b0, xb = _outline_svg(['B'], 300, sb, 16, bb, 'ghost', warp=False)
    b1, _ = _outline_svg(['B'], 300, sb, 16, bb, 'edge')
    mid = bb - 360 * sb
    b_rings, _ = place('B', params(300))
    import arris.draw as D
    gB = D.draw('B', params(300))
    rise = gB.warp(360.0) - 360.0
    cen = (f'<svg class="ce" width="390" height="440">'
           f'<line x1="0" y1="{mid:.1f}" x2="390" y2="{mid:.1f}" class="midln"/>'
           f'<line x1="0" y1="{bb}" x2="390" y2="{bb}" class="ruler"/><line x1="0" y1="{bb - 720 * sb:.1f}" x2="390" y2="{bb - 720 * sb:.1f}" class="ruler"/>'
           f'{b0}{b1}<text x="386" y="{mid + 20:.1f}" class="lineL">geometric</text><text x="386" y="{mid + 36:.1f}" class="lineL">middle</text>'
           f'<text x="{xb + 16:.0f}" y="{bb - 720 * sb + 34:.1f}" class="ann">+{rise:.0f}</text>'
           f'<text x="{xb + 16:.0f}" y="{bb - 720 * sb + 56:.1f}" class="ann2">units up,</text>'
           f'<text x="{xb + 16:.0f}" y="{bb - 720 * sb + 74:.1f}" class="ann2">at Light</text>'
           f'<rect x="{xb + 16:.0f}" y="{bb - 92:.1f}" width="12" height="12" class="kg"/><text x="{xb + 34:.0f}" y="{bb - 81:.1f}" class="ann2">drawn</text>'
           f'<rect x="{xb + 16:.0f}" y="{bb - 66:.1f}" width="12" height="12" class="kc"/><text x="{xb + 34:.0f}" y="{bb - 55:.1f}" class="ann2">seen</text></svg>')
    ch1 = _chart(W, over, 70, 40, 560, 200, 0.9, (0, 0.3, 0.6, 0.9), '%', gid='o')
    ch2 = _chart(W, centre, 70, 40, 560, 200, 4, (0, 1, 2, 3, 4), '%', area=True, gid='m')
    body = f"""
<div class="glow g1"></div><div class="glow g2"></div>
<div class="head"><div class="label kick">Optical corrections · measured, not guessed</div>
<h2>Blur it, and the counters stay.</h2>
<p>Every hole and slot is measured under a model squint, a blur five per cent of the cap height wide, and white that would close
is opened. Then the two corrections type has always made by eye, made by measurement: letters whose bowls turn at cut corners
reach past the lines, and every middle sits a little high.</p></div>
<div class="strip"><div class="sl label">Sharp</div><div class="gs">{glyphs}</div><div class="sl label r">Squint</div></div>
<div class="card c1"><div class="ct label">Overshoot</div><div class="cs">Arris has no curves, but its bowls are octagons: S's top
turns down at 45° at both ends, so it holds less ink at the line than H's square-cut stems and looks short. A blur says by how much, and the top
reaches past by that.</div>{shoot}</div>
<div class="card c2"><div class="ct label">Optical centre</div><div class="cs">The eye finds the middle above the middle. Bars rise
until the top counter is 0.86 of the bottom one; strokes keep their weight.</div>{cen}</div>
<div class="card c3"><div class="ct label">Overshoot by weight · per cent of the line height</div><svg width="860" height="290">{ch1}</svg></div>
<div class="card c4"><div class="ct label">Middle raised by weight · per cent of the zone</div><svg width="860" height="290">{ch2}</svg></div>"""
    css = """
.s-squint .glow { position:absolute; border-radius: 50%; filter: blur(80px); pointer-events: none; }
.s-squint .g1 { left: 980px; top: 300px; width: 760px; height: 520px; background: radial-gradient(circle, rgba(0,161,203,.16), transparent 70%); }
.s-squint .g2 { left: 80px; top: 560px; width: 760px; height: 420px; background: radial-gradient(circle, rgba(201,128,0,.14), transparent 70%); }
.s-squint .head { position:absolute; left:96px; top:112px; width: 1180px; }
.s-squint .kick { color: var(--accent); }
.s-squint h2 { font-size: 60px; font-weight: 800; line-height: 1.02; margin-top: 10px; letter-spacing: -0.005em; }
.s-squint .head p { font-size: 21px; line-height: 1.5; margin-top: 14px; color: #bdb5a6; }
.s-squint .strip { position:absolute; left: 1330px; right: 96px; top: 118px; height: 210px; display:flex; flex-direction: column; justify-content: center;
                   padding: 0 26px; border: 1px solid #2a2e33; background: linear-gradient(160deg, rgba(255,255,255,.05), rgba(255,255,255,0) 60%); border-radius: 6px; }
.s-squint .strip .gs { font: 900 64px/1 'Arris'; color: var(--ink); display:flex; justify-content: space-between; margin: 10px 0; }
.s-squint .strip .sl { font-size: 13px; } .s-squint .strip .sl.r { text-align: right; }
.s-squint .card { position:absolute; border: 1px solid #2a2e33; border-radius: 6px; padding: 18px 22px;
                  background: linear-gradient(160deg, rgba(255,255,255,.055), rgba(255,255,255,.01) 55%, rgba(255,255,255,0));
                  box-shadow: inset 0 1px 0 rgba(255,255,255,.06); }
.s-squint .ct { color: var(--ink); font-size: 14px; letter-spacing: .14em; }
.s-squint .cs { margin-top: 8px; font: 400 15px/1.45 'Arris'; color: #9d968a; }
.s-squint .c1 { left: 96px; top: 368px; width: 560px; height: 600px; }
.s-squint .c2 { left: 676px; top: 368px; width: 420px; height: 600px; }
.s-squint .c3 { left: 1116px; top: 368px; width: 708px; height: 292px; }
.s-squint .c4 { left: 1116px; top: 676px; width: 708px; height: 292px; }
.s-squint .card svg { position:absolute; left: 0; bottom: 0; overflow: visible; }
.s-squint .c3 svg, .s-squint .c4 svg { left: 4px; bottom: 4px; transform: scale(.8); transform-origin: 0 100%; }
.s-squint .c1 svg { left: 16px; bottom: 26px; } .s-squint .c2 svg { left: 14px; bottom: 26px; }
.s-squint svg .ink { fill: #f1ebdd; } .s-squint svg .ghost { fill: rgba(241,235,221,.22); }
.s-squint svg .edge { fill: none; stroke: #00a1cb; stroke-width: 2; }
.s-squint svg .ruler { stroke: #3a3f45; stroke-width: 1; }
.s-squint svg .capln { stroke: #c98000; stroke-width: 1.5; }
.s-squint svg .midln { stroke: #c98000; stroke-width: 1.5; stroke-dasharray: 6 5; }
.s-squint svg .lensbg { fill: #0c0e10; }
.s-squint svg .focus { fill: none; stroke: #c98000; stroke-width: 2; }
.s-squint svg .lineL { font: 400 12px 'Arris Mono'; fill: #6f6a60; text-anchor: end; letter-spacing: .08em; }
.s-squint svg .kg { fill: rgba(241,235,221,.22); } .s-squint svg .kc { fill: none; stroke: #00a1cb; stroke-width: 2; }
.s-squint svg .lensring { fill: none; stroke: #c98000; stroke-width: 2.5; filter: drop-shadow(0 0 8px rgba(201,128,0,.6)); }
.s-squint svg .lensarm { stroke: #c98000; stroke-width: 1.5; }
.s-squint svg .ann { font: 700 30px 'Arris'; fill: #f1ebdd; } .s-squint svg .ann2 { font: 400 13px 'Arris Mono'; fill: #9d968a; letter-spacing: .06em; }
.s-squint svg .gl { stroke: #2a2e33; stroke-width: 1; }
.s-squint svg .yt { font: 400 14px 'Arris Mono'; fill: #6f6a60; text-anchor: end; }
.s-squint svg .xt { font: 400 14px 'Arris Mono'; fill: #6f6a60; text-anchor: middle; }
.s-squint svg .ln { fill: none; stroke-width: 2.5; stroke-linejoin: round; filter: drop-shadow(0 0 5px currentColor); }
.s-squint svg .dot { stroke: #0c0e10; stroke-width: 2; }
.s-squint svg .dl { font: 600 16px 'Arris'; fill: #f1ebdd; } .s-squint svg .dv { font: 400 13px 'Arris Mono'; fill: #9d968a; }
"""
    return body, 'Measured in arris.vision and draw.OPTICAL; WTCH 100 keeps the watch’s pixel-exact drawing', css


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


def _sphere(tilt, spin):
    """Unit sphere point (lat, lon in degrees) -> (x, y, z) after the spin
    about the pole and the tilt toward the viewer; z > 0 faces us."""
    import math
    t, sp = math.radians(tilt), math.radians(spin)

    def f(lat, lon):
        la, lo = math.radians(lat), math.radians(lon) + sp
        x, y, z = math.cos(la) * math.sin(lo), math.sin(la), math.cos(la) * math.cos(lo)
        return x, y * math.cos(t) - z * math.sin(t), z * math.cos(t) + y * math.sin(t)
    return f


def _plane(tilt):
    """A point in the equatorial plane (x, z) -> (x, y, z) after the tilt."""
    import math
    t = math.radians(tilt)
    return lambda x, z: (x, -z * math.sin(t), z * math.cos(t))


def _runs(pts, keep):
    """Split a polyline into runs of consecutive points that keep() keeps
    or not: [(kept, [points])]."""
    out = []
    for q in pts:
        k = keep(q)
        if out and out[-1][0] == k:
            out[-1][1].append(q)
        else:
            if out:
                out[-1][1].append(q)          # close the gap at the change
            out.append((k, [q]))
    return out


def _wire_nav(cx, cy, R, W_, H_):
    """The flyby's nav display: Jupiter as a wireframe (the far side dashed,
    belts by line density, the Great Red Spot as rings on the surface), its
    equatorial rings, the hyperbola in its own plane with timestamps, the
    burn, the ship and its velocity vector. Returns (svg, labels html)."""
    import math
    tilt, spin = 18, -30
    S = _sphere(tilt, spin)
    P = lambda x, y: (cx + R * x, cy - R * y)
    xy = lambda run: ' '.join(f'{P(q[0], q[1])[0]:.1f},{P(q[0], q[1])[1]:.1f}' for q in run)
    svg, labels = [], []
    def latlon(lat0, lat1, step, cls):
        for lat in [lat0 + k * step for k in range(int(round((lat1 - lat0) / step)) + 1)]:
            for front, run in _runs([S(lat, lon) for lon in range(-180, 181, 3)], lambda q: q[2] >= 0):
                svg.append(f'<polyline points="{xy(run)}" class="{cls} {"fr" if front else "bk"}"/>')
    latlon(-80, 80, 10, 'lat')
    for lon in range(-180, 180, 15):
        for front, run in _runs([S(lat, lon) for lat in range(-90, 91, 3)], lambda q: q[2] >= 0):
            svg.append(f'<polyline points="{xy(run)}" class="lon {"fr" if front else "bk"}"/>')
    for a, b in ((7, 17), (-17, -7), (24, 29), (-29, -24)):
        latlon(a, b, 2.5, 'belt')
    for k, (ra, rb) in enumerate(((11, 5.5), (7, 3.5), (3, 1.5))):
        pts = [S(-22 + rb * math.sin(math.radians(u)), 18 + ra * math.cos(math.radians(u)) / math.cos(math.radians(-22 + rb * math.sin(math.radians(u)))))
               for u in range(0, 361, 8)]
        svg.append(f'<polyline points="{xy(pts)}" class="grs"/>')
    svg.append(f'<circle cx="{cx}" cy="{cy}" r="{R}" class="limb"/>')
    E = _plane(tilt)
    hidden = lambda q: q[2] < 0 and q[0] ** 2 + q[1] ** 2 < 1
    for rr in (1.8, 2.54):
        pts = [E(rr * math.sin(math.radians(a)), rr * math.cos(math.radians(a))) for a in range(0, 361, 4)]
        for vis, run in _runs(pts, lambda q: not hidden(q)):
            svg.append(f'<polyline points="{xy(run)}" class="ring {"" if vis else "hid"}"/>')
    def unit(v):
        n = math.sqrt(sum(c * c for c in v))
        return tuple(c / n for c in v)
    e1, e2 = unit((1.0, 0.18, -0.25)), unit((0.0, -0.42, 0.9))
    rp, e, w = 1.22, 1.55, math.radians(118)
    def fly(nu):
        r = rp * (1 + e) / (1 + e * math.cos(math.radians(nu)))
        a = math.radians(nu) + w
        return tuple(r * math.cos(a) * u + r * math.sin(a) * v for u, v in zip(e1, e2))
    for vis, run in _runs([fly(n / 2) for n in range(-230, 231)], lambda q: not hidden(q)):
        svg.append(f'<polyline points="{xy(run)}" class="trk {"" if vis else "hid"}"/>')
    for vis, run in _runs([fly(n / 2) for n in range(-30, 31)], lambda q: not hidden(q)):
        if vis:
            svg.append(f'<polyline points="{xy(run)}" class="burn"/>')
    for n, lab in ((-60, 'T−12'), (-40, 'NAU'), (0, 'PJ'), (40, 'T+12')):
        q = fly(n)
        x, y = P(q[0], q[1])
        if hidden(q) or not (0 < x < W_ and 0 < y < H_):
            continue
        svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{4 if lab in ("PJ", "NOW") else 3}" class="tick {"pj" if lab == "PJ" else ""}"/>')
        labels.append(f'<div class="tl mono {"pj" if lab == "PJ" else ""}" style="left:{x + 8:.0f}px;top:{y - 20:.0f}px">{lab}</div>')
    q0, q1 = fly(-40), fly(-36)
    (sx, sy), (tx, ty) = P(q0[0], q0[1]), P(q1[0], q1[1])
    d = math.hypot(tx - sx, ty - sy)
    ux, uy = (tx - sx) / d, (ty - sy) / d
    svg.append(f'<line x1="{sx:.1f}" y1="{sy:.1f}" x2="{sx + 60 * ux:.1f}" y2="{sy + 60 * uy:.1f}" class="vec"/>')
    svg.append(f'<rect x="{sx - 10:.1f}" y="{sy - 10:.1f}" width="20" height="20" class="lock"/>')
    return ''.join(svg), ''.join(labels)


@slide('slingshot', 'void', 'Slingshot')
def slingshot():
    import math
    src = lambda f: (SOURCES / f).as_uri()
    # the nav display, up in the corner
    nx, ny, nw, nh = 112, 116, 520, 380
    nav_svg, nav_labels = _wire_nav(nw / 2 + 10, nh / 2 + 18, 112, nw, nh)
    # gauges: arcs of 240 degrees
    def arc(cx_, cy_, r, frac, cls):
        a0, a1 = math.radians(150), math.radians(150 + 240 * frac)
        x0, y0 = cx_ + r * math.cos(a0), cy_ + r * math.sin(a0)
        x1, y1 = cx_ + r * math.cos(a1), cy_ + r * math.sin(a1)
        return f'<path d="M{x0:.1f},{y0:.1f} A{r},{r} 0 {1 if 240 * frac > 180 else 0} 1 {x1:.1f},{y1:.1f}" class="{cls}"/>'
    gauges = ''.join(arc(x, 64, 52, f, c) for x, f, c in ((64, 1, 'gbg'), (64, 3.2 / 5, 'ghot'), (200, 1, 'gbg'), (200, .74, 'gon')))
    ticks = ''.join(f'<span class="{"big" if h % 10 == 0 else ""}" style="left:{(h - 241) * 12}px">'
                    f'{"<em>" + str(h) + "</em>" if h % 10 == 0 else ""}</span>' for h in range(241, 302))
    events = [(0.06, 'LAINAP', ''), (0.22, 'JUS', ''), (0.38, 'NAU', 'now'), (0.48, 'BERN', 'burn'), (0.62, 'PERIJOV', 'pj'), (0.86, 'KATOF', '')]
    ev = ''.join(f'<div class="ev {c}" style="left:{f * 100:.0f}%"><i></i><span>{t}</span></div>' for f, t, c in events)
    # the chat: photo avatars, a few pixel ones, images posted
    av = lambda f: f'<img class="av" src="{src(f)}">'
    def face(f, fx, fy, zoom, size=34, cls='av'):
        # a round crop centred on a face at (fx, fy) of the picture, the
        # picture zoom times the circle's width (kept covering the circle)
        from PIL import Image as _Im
        w0, h0 = _Im.open(SOURCES / f).size
        Wr, Hr = zoom * size, zoom * size * h0 / w0
        left = min(0.0, max(size - Wr, size / 2 - fx * Wr))
        top = min(0.0, max(size - Hr, size / 2 - fy * Hr))
        return (f'<span class="{cls}" style="background-image:url({src(f)});background-size:{Wr:.0f}px {Hr:.0f}px;'
                f'background-position:{left:.0f}px {top:.0f}px"></span>')
    crop = lambda f, pos: f'<span class="av" style="background-image:url({src(f)});background-position:{pos}"></span>'
    msgs = [
        ('pin', None, 'dock_rat', '#6fd3ff', 'flaitplan: slinshot, 3 g ka perijov, den gonya hom fo Ceres', None),
        ('m', av('eva-pettit.jpg'), 'beltalowda_88', '#7cf29a', 'Oye, beratnas! taim fo jus ⚡', None),
        ('m', crop('redoute-rosa-gallica-flore-giganteo.jpg', '48% 28%'), 'mira.okonkwo', '#ff8ad8', 'bern ka perijov, sasa ke?', None),
        ('m', face('nasa-s61-02845.jpg', 0.48, 0.22, 4.2), 'dock_rat', '#6fd3ff', 'Oberth, kopeng. mo Δv fo im kilo', 'MOD'),
        ('m', av('eva-parmitano.jpg'), 'pilot_tanya', '#9ad6ff', '3 g? dat fo inyalowda', ('stapp-sled.gif', 'GIF')),
        ('cheer', av('cat-grass.jpg'), 'ceres_nights', '#ffd36b', 'taki bosmang, gut kofi fo to lowda ♥', '500'),
        ('m', crop('saturn-cassini-2004-10-06.jpg', '52% 50%'), 'nikos_r', '#6fd3ff', 'Μπράβο, καπετάνιε o7', None),
        ('m', face('nasa-iss070e014334.jpg', 0.355, 0.285, 6.5), 'linh.tran', '#ff8ad8', 'kopailot, nau', ('ducreux-yawning.jpg', 'IMG')),
        ('m', face('nasa-iss046e017204.jpg', 0.47, 0.44, 1.8), 'hal_n_teo', '#ffd36b', 'Glashaus sa oye ♥', 'SAB 8'),
    ]
    rows = []
    for k, (kind, a, user, col, text, extra) in enumerate(msgs):
        ts = f'03:{12 + k // 2:02d}'
        if kind == 'pin':
            rows.append(f'<div class="pin"><span class="pk mono">◆ PIN</span><b style="color:{col}">{esc(user)}</b><div>{esc(text)}</div></div>')
            continue
        badge = ''
        post = ''
        if isinstance(extra, tuple):
            f_, tag = extra
            post = f'<div class="post"><img src="{src(f_)}"><span class="pt mono">{"▶ " if tag == "GIF" else ""}{tag}</span></div>'
        elif kind == 'cheer':
            badge = f'<span class="bits mono">◆ {extra}</span>'
        elif extra:
            badge = f'<span class="bd mono">{extra}</span>'
        rows.append(f'<div class="{"cheer" if kind == "cheer" else "m"}">{a}<div class="mb"><div class="nm"><b style="color:{col}">{esc(user)}</b>{badge}'
                    f'<span class="ts mono">{ts}</span></div><div class="tx">{esc(text)}</div>{post}</div></div>')
    viewers = ''.join(f'<img class="vw" src="{src(f)}">' for f in ('cat-tabby.jpg', 'eva-pettit.jpg', 'cat-grass.jpg', 'ducreux-yawning.jpg'))
    # Jupiter's limb in the photograph as shown (fitted: a circle, to half a
    # pixel): the horizon, a graticule over the disc as seen from above the
    # pole, the ground track to perijove, the belts named, the Red Spot below
    LX, LY, LR = 2280, 3466, 3288
    pol = lambda r, a: (LX + r * math.cos(a), LY + r * math.sin(a))
    win = lambda x, y: 40 < x < 1880 and 92 < y < 990
    def arcpts(r, a0, a1, n=240):
        out = [pol(r, a0 + (a1 - a0) * k / n) for k in range(n + 1)]
        return ' '.join(f'{x:.1f},{y:.1f}' for x, y in out if win(x, y))
    A0, A1 = math.radians(-148), math.radians(-78)
    ov = [f'<polyline points="{arcpts(LR + 3, A0, A1)}" class="hz"/>',
          f'<polyline points="{arcpts(LR + 26, A0, A1)}" class="hz2"/>']
    for k in range(-148, -77):
        a_ = math.radians(k)
        x0, y0 = pol(LR + 3, a_)
        if not win(x0, y0):
            continue
        L_ = 14 if k % 5 == 0 else 6
        x1, y1 = pol(LR + 3 + L_, a_)
        ov.append(f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" class="ht"/>')
    for deg in range(4, 44, 4):                              # latitude rings, orthographic from above the pole
        ov.append(f'<polyline points="{arcpts(LR * math.cos(math.radians(deg)), A0, A1)}" class="gr {"gr5" if deg % 12 == 0 else ""}"/>')
    for k in range(-148, -77, 4):                            # meridians, converging on the pole far below
        a_ = math.radians(k)
        pts = [pol(LR * math.cos(math.radians(t)), a_) for t in range(0, 50)]
        pts = [q for q in pts if win(*q)]
        if len(pts) > 1:
            ov.append('<polyline points="' + ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts) + '" class="gr"/>')
    # the ground track: in from the south-west, grazing toward the horizon
    trk = []
    for k in range(0, 101):
        t = k / 100
        a_ = math.radians(-150 + 41 * t)
        r = LR * math.cos(math.radians(38 - 36.5 * t ** 0.7))
        trk.append(pol(r, a_))
    ov.append('<polyline points="' + ' '.join(f'{x:.1f},{y:.1f}' for x, y in trk if win(x, y)) + '" class="gtk"/>')
    for t, lab in ((0.3, 'T−08'), (0.62, 'T−04'), (1.0, 'PERIJOV')):
        a_ = math.radians(-150 + 41 * t)
        x, y = pol(LR * math.cos(math.radians(38 - 36.5 * t ** 0.7)), a_)
        ov.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{5 if lab == "PERIJOV" else 3.5}" class="gp {"pj" if lab == "PERIJOV" else ""}"/>')
        ov.append(f'<text x="{x + 10:.1f}" y="{y - 10:.1f}" class="gl {"pj" if lab == "PERIJOV" else ""}">{lab}</text>')
    # belt names along their rings
    for deg, name in ((10, 'NNTB · 40°N'), (22, 'NTZ · 24°N')):
        x, y = pol(LR * math.cos(math.radians(deg)), math.radians(-113.5))
        if win(x, y):
            ov.append(f'<text x="{x:.1f}" y="{y - 6:.1f}" class="bl" transform="rotate(-23 {x:.1f} {y:.1f})">{name}</text>')
    hx, hy = pol(LR + 3, math.radians(-107.5))
    ov.append(f'<polyline points="{hx:.1f},{hy:.1f} {hx - 36:.1f},{hy - 70:.1f} {hx - 236:.1f},{hy - 70:.1f}" class="ld"/>')
    ov.append(f'<text x="{hx - 236:.1f}" y="{hy - 78:.1f}" class="cl">HORAIZON · 1 BAR</text>')
    ov.append(f'<text x="{hx - 236:.1f}" y="{hy - 56:.1f}" class="cl dim">18 220 km · −0.6°</text>')
    ov.append('<g class="off"><polygon points="1200,960 1188,944 1212,944"/><text x="1222" y="958">GRS · 16 350 km</text></g>')
    view_hud = f'<svg class="vhud" width="1920" height="1080">{"".join(ov)}</svg>'
    body = f"""
<img class="view" src="{src('juno-pj18-jupiter.png')}">
{view_hud}
<div class="haze"></div>
<div class="bore"><i></i></div>
<div class="tape mono"><div class="ticks">{ticks}</div><div class="hd">271</div></div>
<div class="att mono"><span>PICH +04.2</span><span>YAU −11.0</span><span>ROL 000.0</span></div>
<div class="mfd nav" style="left:{nx}px;top:{ny}px;width:{nw}px;height:{nh}px">
  <svg class="hud" width="{nw}" height="{nh}">{nav_svg}</svg>{nav_labels}
  <div class="mh mono">NAVI · FLAIBAI · FAS 3/5</div>
  <div class="mr mono">PJ 1.22 RJ<br>V∞ 14.1<br>e 1.55</div>
</div>
<div class="mfd cam" style="left:112px;top:560px;width:380px;height:300px">
  <img src="{src('nasa-s62-00303.jpg')}"><div class="red"></div><div class="scan"></div>
  <div class="mh mono"><span class="rec">●</span> PAILOT · KAM 2</div>
  <div class="bio mono">3.2 g · HARTA 168 · O2 91% · GREIAUT DANGA</div>
</div>
<div class="burnblk mono"><span>TAIM FO BERN</span><b>T−00:41</b></div>
<div class="gg mono"><svg width="264" height="110">{gauges}</svg>
  <div class="g1"><b>3.2</b>g LOWD</div><div class="g2"><b>74</b>% DRAIV</div></div>
<div class="tline mono"><div class="ax"></div>{ev}</div>
<div class="flt mono"><span>SPID <b>61.4</b> km/s</span><span>ALTO <b>18 220</b> km</span><span>Δv <b>42</b>%</span><span>OBERTH <b>+9.8</b></span></div>
<div class="tips">
  <div class="goal"><div class="gt mono">BITS GOL · nyu kofi masin</div><div class="gb"><i></i></div><div class="gn mono">◆ 3 120 / 5 000 bits</div></div>
  <div class="tip">{av('cat-tabby.jpg')}<div><div class="tt"><b>la_tormenta</b> da <span class="amt">◆ 250 bits</span></div><div class="tm">“mo jus, kopeng!”</div></div></div>
  <div class="tip big">{av('eva-pettit.jpg')}<div><div class="tt"><b>beltalowda_88</b> da <span class="amt">◆ 1 000 bits</span></div><div class="tm">“fo Glashaus roses ♥ taki”</div></div></div>
</div>
<div class="chat">
  <div class="sh">{face('nasa-s66-46270.jpg', 0.50, 0.53, 3.2, 48, 'av sha')}<div><div class="mono s1"><span class="live">● LAIV</span> beltcast <span class="up">03:12:44</span></div>
     <div class="s2">slinshot ka Jupita · 3 g · na mang vomit (wa?)</div>
     <div class="s3 mono">{viewers}<span>14 312 lowda showxa</span></div></div></div>
  <div class="msgs">{''.join(rows)}</div>
  <div class="in mono"><span>Sen mesaj, kopeng</span><span class="ic">o7 ☺ GIF</span></div>
</div>
<div class="glass"></div>
<svg class="frame" width="1920" height="1080"><path fill-rule="evenodd" d="M0 0H1920V1080H0Z M150 92 H1770 L1880 202 V880 L1770 990 H150 L40 880 V202 Z"/>
  <path d="M150 92 H1770 L1880 202 V880 L1770 990 H150 L40 880 V202 Z" class="edge"/></svg>"""
    css = """
.s-slingshot { background: #01030a; }
.s-slingshot .view { position:absolute; left: 0; top: -40px; width: 1920px; height: 1200px; object-fit: cover; transform: scaleX(-1);
                     filter: saturate(1.15) contrast(1.08); }
.s-slingshot .haze { position:absolute; inset:0; background: radial-gradient(ellipse at 70% 30%, rgba(0, 120, 200, .10), transparent 50%),
                     linear-gradient(180deg, rgba(1,3,10,.35), transparent 30%, transparent 70%, rgba(1,3,10,.5)); }
.s-slingshot .bore { position:absolute; left: 900px; top: 470px; width: 80px; height: 80px; border: 1.5px solid rgba(200,255,58,.9); border-radius: 50%;
                     }
.s-slingshot .bore::before, .s-slingshot .bore::after { content: ''; position:absolute; top: 38px; width: 60px; height: 2px; background: rgba(200,255,58,.9); }
.s-slingshot .bore::before { left: -70px; } .s-slingshot .bore::after { right: -70px; }
.s-slingshot .bore i { position:absolute; left: 36px; top: 36px; width: 6px; height: 6px; background: #c8ff3a; }
.s-slingshot .tape { position:absolute; left: 640px; top: 112px; width: 600px; height: 46px; overflow: hidden; color: #c8ff3a;
                     -webkit-mask: linear-gradient(90deg, transparent, #000 15%, #000 85%, transparent); }
.s-slingshot .tape .ticks span { position:absolute; bottom: 0; width: 1px; height: 8px; background: rgba(200,255,58,.7); }
.s-slingshot .tape .ticks span.big { height: 16px; background: #c8ff3a; }
.s-slingshot .tape .ticks em { position:absolute; bottom: 20px; left: -14px; font: normal 13px 'Arris Mono'; }
.s-slingshot .tape .hd { position:absolute; left: 50%; bottom: 0; transform: translateX(-50%); font-size: 20px; color: #c8ff3a;
                         border: 1.5px solid #c8ff3a; padding: 2px 10px 0; background: rgba(1,3,10,.8); }
.s-slingshot .att { position:absolute; left: 640px; top: 166px; width: 600px; display:flex; justify-content: center; gap: 30px;
                    font-size: 13px; letter-spacing: .16em; color: rgba(220, 255, 180, .8); }
.s-slingshot .mfd { position:absolute; background: rgba(6, 10, 14, .72); border: 1px solid rgba(233,251,255,.28); overflow: hidden;
                    clip-path: polygon(0 0, calc(100% - 16px) 0, 100% 16px, 100% 100%, 16px 100%, 0 calc(100% - 16px));
                    }
.s-slingshot .mfd .mh { position:absolute; left: 14px; top: 10px; font-size: 12px; letter-spacing: .2em; color: #5fe3ff; }
.s-slingshot .mfd .mr { position:absolute; right: 16px; top: 10px; text-align: right; font-size: 12px; line-height: 1.45; letter-spacing: .12em; color: #bfeeff; }
.s-slingshot .hud { position:absolute; left:0; top:0; }
.s-slingshot .hud polyline, .s-slingshot .hud path, .s-slingshot .hud circle, .s-slingshot .hud rect { fill: none; }
.s-slingshot .hud .lat.fr, .s-slingshot .hud .lon.fr { stroke: rgba(95, 227, 255, .6); stroke-width: 1; }
.s-slingshot .hud .lat.bk, .s-slingshot .hud .lon.bk { stroke: rgba(95, 227, 255, .14); stroke-width: 1; stroke-dasharray: 2 4; }
.s-slingshot .hud .belt.fr { stroke: rgba(255, 176, 0, .5); stroke-width: 1; } .s-slingshot .hud .belt.bk { stroke: none; }
.s-slingshot .hud .grs { stroke: #ff5f3a; stroke-width: 1.2; }
.s-slingshot .hud .limb { stroke: #5fe3ff; stroke-width: 2; }
.s-slingshot .hud .ring { stroke: rgba(95, 227, 255, .35); stroke-width: 1; stroke-dasharray: 5 5; }
.s-slingshot .hud .hid { stroke-opacity: .25 !important; stroke-dasharray: 2 5; }
.s-slingshot .hud .trk { stroke: #e6fbff; stroke-width: 1.6; }
.s-slingshot .hud .trk.hid { stroke: #5fe3ff; filter: none; }
.s-slingshot .hud .burn { stroke: #ffb000; stroke-width: 4; }
.s-slingshot .hud .tick { fill: #01030a; stroke: #e6fbff; stroke-width: 1.6; } .s-slingshot .hud .tick.pj { stroke: #ffb000; stroke-width: 2.4; }
.s-slingshot .hud .vec { stroke: #c8ff3a; stroke-width: 1.6; } .s-slingshot .hud .lock { stroke: #c8ff3a; stroke-width: 1.2; stroke-dasharray: 6 8; }
.s-slingshot .tl { position:absolute; font-size: 11px; letter-spacing: .12em; color: #bfeeff; }
.s-slingshot .tl.pj { color: #ffb000; }
.s-slingshot .cam img { position:absolute; left: -101px; top: 0; width: 560px; filter: saturate(.55) contrast(1.2) brightness(.95); }
.s-slingshot .cam { border-color: rgba(255, 90, 90, .6); }
.s-slingshot .cam .red { position:absolute; inset: 0; background: radial-gradient(ellipse at 50% 45%, transparent 35%, rgba(120, 0, 0, .55) 85%),
                         linear-gradient(rgba(60, 255, 160, .10), rgba(60, 255, 160, .10)); mix-blend-mode: normal; }
.s-slingshot .cam .scan { position:absolute; inset:0; background: repeating-linear-gradient(0deg, rgba(0,0,0,.28) 0 1px, transparent 1px 3px); }
.s-slingshot .cam .mh { color: #ffdede; } .s-slingshot .cam .rec { color: #ff3b3b; }
.s-slingshot .cam .bio { position:absolute; left: 14px; bottom: 10px; font-size: 11px; letter-spacing: .12em; color: #ffb3b3; }
.s-slingshot .burnblk { position:absolute; left: 540px; top: 760px; color: #ffb000; }
.s-slingshot .burnblk span { display:block; font-size: 12px; letter-spacing: .24em; }
.s-slingshot .burnblk b { font: 300 64px/1 'Arris'; font-variation-settings: 'WTCH' 100; }
.s-slingshot .gg { position:absolute; left: 532px; top: 838px; width: 264px; height: 120px; }
.s-slingshot .gg svg { position:absolute; left: 0; top: 0; }
.s-slingshot .gg .gbg { stroke: rgba(95,227,255,.18); stroke-width: 8; fill: none; }
.s-slingshot .gg .gon { stroke: #5fe3ff; stroke-width: 8; fill: none; }
.s-slingshot .gg .ghot { stroke: #ffb000; stroke-width: 8; fill: none; }
.s-slingshot .gg .g1, .s-slingshot .gg .g2 { position:absolute; top: 44px; width: 128px; text-align: center; font-size: 10px; letter-spacing: .16em; color: #bfeeff; }
.s-slingshot .gg .g1 { left: 0; } .s-slingshot .gg .g2 { left: 136px; }
.s-slingshot .gg b { display:block; font: 300 30px/1 'Arris'; color: #e6fbff; }
.s-slingshot .tline { position:absolute; left: 830px; width: 500px; top: 900px; height: 50px; color: #bfeeff; }
.s-slingshot .tline .ax { position:absolute; left: 0; right: 0; top: 20px; height: 1px; background: rgba(95,227,255,.7); }
.s-slingshot .tline .ev { position:absolute; top: 12px; }
.s-slingshot .tline .ev i { display:block; width: 1px; height: 16px; background: #5fe3ff; }
.s-slingshot .tline .ev span { position:absolute; top: -18px; left: -4px; font-size: 10px; letter-spacing: .12em; white-space: nowrap; }
.s-slingshot .tline .ev.now i { width: 2px; height: 30px; margin-top: -7px; background: #c8ff3a; }
.s-slingshot .tline .ev.now span { color: #c8ff3a; }
.s-slingshot .tline .ev.burn i { width: 50px; height: 5px; margin-top: 6px; background: #ffb000; }
.s-slingshot .tline .ev.burn span, .s-slingshot .tline .ev.pj span { color: #ffb000; }
.s-slingshot .flt { position:absolute; left: 830px; top: 812px; width: 500px; display:flex; justify-content: space-between; font-size: 12px; letter-spacing: .1em; color: #5fe3ff; }
.s-slingshot .flt b { font: 400 22px 'Arris'; color: #e6fbff; margin: 0 2px 0 4px; }
.s-slingshot .chat { position:absolute; right: 120px; top: 112px; bottom: 112px; width: 440px; display:flex; flex-direction: column;
                     background: rgba(12, 8, 26, .9); border: 1px solid rgba(155, 120, 255, .4);
                     clip-path: polygon(0 0, calc(100% - 20px) 0, 100% 20px, 100% 100%, 20px 100%, 0 calc(100% - 20px)); }
.s-slingshot .chat .sh { display:flex; gap: 12px; padding: 14px; border-bottom: 1px solid rgba(155,120,255,.3); background: rgba(155,120,255,.08); }
.s-slingshot .chat .sh .sha { width: 48px; height: 48px; outline: 2px solid #ff3b5c; outline-offset: 2px; }
.s-slingshot .chat .s1 { font-size: 12px; letter-spacing: .12em; color: #e6dcff; }
.s-slingshot .chat .live { color: #fff; background: #ff3b5c; padding: 1px 6px; margin-right: 6px; }
.s-slingshot .chat .up { color: #a99bd0; margin-left: 6px; }
.s-slingshot .chat .s2 { font: 700 17px/1.25 'Arris'; color: #fff; margin: 5px 0; }
.s-slingshot .chat .s3 { display:flex; align-items:center; font-size: 12px; color: #a99bd0; }
.s-slingshot .chat .s3 .vw { width: 20px; height: 20px; border-radius: 50%; object-fit: cover; margin-right: -5px; border: 2px solid #120c22; }
.s-slingshot .chat .s3 span { margin-left: 12px; }
.s-slingshot .chat .msgs { flex: 1; overflow: hidden; display:flex; flex-direction: column; justify-content: flex-end; padding: 8px 12px; gap: 8px; }
.s-slingshot .chat .m, .s-slingshot .chat .cheer { display:flex; gap: 9px; align-items: flex-start; }
.s-slingshot .chat .av { flex: none; width: 34px; height: 34px; border-radius: 50%; object-fit: cover; background-size: 300%; display:block; }
.s-slingshot .chat .mb { flex: 1; min-width: 0; }
.s-slingshot .chat .nm { font-size: 13px; display:flex; align-items: center; gap: 6px; }
.s-slingshot .chat .nm b { font: 700 14px 'Arris'; }
.s-slingshot .chat .bd { font-size: 10px; letter-spacing: .1em; padding: 0 5px; border: 1px solid rgba(155,120,255,.6); color: #cbbcff; }
.s-slingshot .chat .ts { margin-left: auto; font-size: 10px; color: #6c6290; }
.s-slingshot .chat .tx { font: 400 15px/1.3 'Arris'; color: #ece6ff; }
.s-slingshot .chat .post { position: relative; margin-top: 6px; width: 230px; height: 118px; border-radius: 6px; overflow: hidden; border: 1px solid rgba(155,120,255,.4); }
.s-slingshot .chat .post img { width: 100%; height: 100%; object-fit: cover; }
.s-slingshot .chat .post .pt { position:absolute; left: 6px; bottom: 6px; font-size: 10px; letter-spacing: .14em; padding: 2px 6px; background: rgba(0,0,0,.75); color: #fff; }
.s-slingshot .chat .pin { margin-bottom: auto; padding: 8px 10px; border: 1px solid rgba(95,227,255,.4); background: rgba(95,227,255,.06); font: 400 14px/1.35 'Arris'; color: #dff6ff; }
.s-slingshot .chat .pk { font-size: 10px; letter-spacing: .2em; color: #5fe3ff; margin-right: 8px; }
.s-slingshot .chat .cheer { padding: 7px 9px; background: linear-gradient(90deg, rgba(255,176,0,.22), rgba(255,43,214,.12)); border-left: 3px solid #ffb000; }
.s-slingshot .chat .bits { font-size: 10px; color: #01030a; background: #ffb000; padding: 1px 6px; }
.s-slingshot .chat .in { display:flex; justify-content: space-between; margin: 8px 12px 14px; padding: 9px 12px; border: 1px solid rgba(155,120,255,.45); color: #8e82b4; font-size: 13px; }
.s-slingshot .chat .ic { color: #ff8ad8; }
.s-slingshot .tips { position:absolute; left: 664px; top: 226px; width: 330px; display:flex; flex-direction: column; gap: 10px; }
.s-slingshot .tips .goal { padding: 10px 12px; background: rgba(12, 8, 26, .82); border: 1px solid rgba(255,176,0,.5); }
.s-slingshot .tips .gt { font-size: 11px; letter-spacing: .16em; color: #ffb000; }
.s-slingshot .tips .gb { height: 8px; margin: 8px 0 6px; background: rgba(255,176,0,.18); }
.s-slingshot .tips .gb i { display:block; width: 62%; height: 100%; background: repeating-linear-gradient(90deg, #ffb000 0 8px, #ffcf5a 8px 10px); }
.s-slingshot .tips .gn { font-size: 11px; color: #ffd9a0; text-align: right; }
.s-slingshot .tips .tip { display:flex; gap: 10px; align-items: center; padding: 9px 12px; background: linear-gradient(90deg, rgba(255,43,214,.32), rgba(12,8,26,.85));
                          border-left: 3px solid #ff2bd6; }
.s-slingshot .tips .tip.big { background: linear-gradient(90deg, rgba(255,176,0,.36), rgba(12,8,26,.85)); border-left-color: #ffb000; }
.s-slingshot .tips .av { flex: none; width: 34px; height: 34px; border-radius: 50%; object-fit: cover; }
.s-slingshot .tips .tt { font: 400 15px 'Arris'; color: #fff; }
.s-slingshot .tips .tt b { font-weight: 700; }
.s-slingshot .tips .amt { font: 700 15px 'Arris'; color: #ffd36b; }
.s-slingshot .tips .tm { font: italic 400 14px 'Arris'; color: #f1e6ff; }
.s-slingshot .vhud { position:absolute; left:0; top:0; }
.s-slingshot .vhud polyline, .s-slingshot .vhud circle { fill: none; }
.s-slingshot .vhud .hz { stroke: #e9fbff; stroke-width: 1.4; }
.s-slingshot .vhud .hz2 { stroke: rgba(233, 251, 255, .45); stroke-width: 1; stroke-dasharray: 2 6; }
.s-slingshot .vhud .ht { stroke: rgba(233, 251, 255, .8); stroke-width: 1; }
.s-slingshot .vhud .gr { stroke: rgba(233, 251, 255, .26); stroke-width: 1; }
.s-slingshot .vhud .gr5 { stroke: rgba(233, 251, 255, .45); }
.s-slingshot .vhud .gtk { stroke: #c8ff3a; stroke-width: 1.4; stroke-dasharray: 10 6; }
.s-slingshot .vhud .gp { stroke: #c8ff3a; stroke-width: 1.4; fill: #0b0f14; }
.s-slingshot .vhud .gp.pj { stroke: #ffb000; }
.s-slingshot .vhud text { font: 500 12px 'Arris Mono'; letter-spacing: .14em; fill: #e9fbff; }
.s-slingshot .vhud .gl { fill: #c8ff3a; } .s-slingshot .vhud .gl.pj { fill: #ffb000; }
.s-slingshot .vhud .bl { fill: rgba(233, 251, 255, .75); font-size: 11px; }
.s-slingshot .vhud .ld { stroke: rgba(233, 251, 255, .8); stroke-width: 1; fill: none; }
.s-slingshot .vhud .cl.dim { fill: rgba(233, 251, 255, .6); }
.s-slingshot .vhud .off polygon { fill: #ff6f4f; } .s-slingshot .vhud .off text { fill: #ff9c80; }
.s-slingshot .glass { position:absolute; inset:0; pointer-events:none;
   background: linear-gradient(115deg, rgba(255,255,255,0) 30%, rgba(190,230,255,.06) 38%, rgba(255,255,255,0) 44%),
               linear-gradient(115deg, rgba(255,255,255,0) 52%, rgba(190,230,255,.035) 55%, rgba(255,255,255,0) 58%),
               radial-gradient(ellipse at 18% 8%, rgba(120,200,255,.07), transparent 45%); }
.s-slingshot .frame { position:absolute; left:0; top:0; }
.s-slingshot .frame path { fill: #07090c; }
.s-slingshot .frame .edge { fill: none; stroke: rgba(95, 227, 255, .35); stroke-width: 1.5; }
.s-slingshot .chrome, .s-slingshot .k-strip, .s-slingshot .k-xh { z-index: 5; }
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
