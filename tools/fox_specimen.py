"""A four-page specimen of the pangram: every weight upright, every weight
italic, a waterfall of sizes, and the Mono. US Letter, landscape.

usage: fox_specimen.py [out.pdf]        (default proofs/quick-brown-fox.pdf)
needs: the built fonts in build/, Playwright's Chromium
"""
from __future__ import annotations

import html
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / 'build'
FOX = 'The quick brown fox jumps over the lazy dog'
NAMES = ['Thin', 'ExtraLight', 'Light', 'Regular', 'Medium', 'SemiBold', 'Bold', 'ExtraBold', 'Black']


def fonts():
    vf = (BUILD / 'Arris[GRAD,WTCH,wght].ttf').as_uri()
    vfi = (BUILD / 'Arris-Italic[GRAD,WTCH,wght].ttf').as_uri()
    css = [f"@font-face {{ font-family: 'Arris'; src: url('{vf}'); font-weight: 100 900; font-style: normal; }}",
           f"@font-face {{ font-family: 'Arris'; src: url('{vfi}'); font-weight: 100 900; font-style: italic; }}"]
    for i, n in enumerate(NAMES):
        css.append(f"@font-face {{ font-family: 'Arris Mono'; src: url('{(BUILD / f'ArrisMono-{n}.ttf').as_uri()}'); "
                   f"font-weight: {100 * (i + 1)}; }}")
    return '\n'.join(css)


def page(title, folio, rows):
    return (f'<section><header><span>Arris</span><span>{title}</span><span>{folio} / 4</span></header>'
            f'<div class="rows">{rows}</div><footer>{html.escape(FOX)}</footer></section>')


def weights(italic=False, family='Arris', size=24):
    style = 'italic' if italic else 'normal'
    return ''.join(f'<div class="r"><span class="lab">{100 * (i + 1)} {n}{" Italic" if italic else ""}</span>'
                   f'<span class="s" style="font-family:\'{family}\';font-weight:{100 * (i + 1)};font-style:{style};font-size:{size}pt">{FOX}</span></div>'
                   for i, n in enumerate(NAMES))


def waterfall():
    out = []
    for w, n in ((400, 'Regular'), (900, 'Black')):
        for pt in ((72, 48, 30, 18) if w == 400 else (36, 24)):
            out.append(f'<div class="r"><span class="lab">{n} {pt} pt</span>'
                       f'<span class="s" style="font-weight:{w};font-size:{pt}pt">{FOX}</span></div>')
    for pt in (14, 12, 10, 9, 8):
        out.append(f'<div class="r"><span class="lab">Regular {pt} pt</span>'
                   f'<span class="s wrap" style="font-weight:400;font-size:{pt}pt">{FOX}. {FOX.upper()}. 0123456789 '
                   f'&amp; ? ! (Arris, a chamfered sans.) {FOX}.</span></div>')
    return ''.join(out)


def mono():
    rows = weights(family='Arris Mono', size=19)
    for pt in (28, 14, 10):
        rows += (f'<div class="r"><span class="lab">Mono {pt} pt</span>'
                 f'<span class="s" style="font-family:\'Arris Mono\';font-weight:400;font-size:{pt}pt">{FOX} -&gt; 0O 1lI</span></div>')
    return rows


CSS = """
@page { size: 11in 8.5in; margin: 0; }
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Arris'; color: #151412; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
section { width: 11in; height: 8.5in; padding: 0.55in 0.6in; background: #f3eee3; position: relative; overflow: hidden;
          page-break-after: always; break-after: page; display: flex; flex-direction: column; }
header, footer { display: flex; justify-content: space-between; font: 500 8pt 'Arris Mono'; letter-spacing: .14em;
                 text-transform: uppercase; color: #8c8577; }
header { border-bottom: 0.5pt solid #cfc8b8; padding-bottom: 8pt; }
footer { position: absolute; left: .6in; right: .6in; bottom: .4in; }
.rows { flex: 1; display: flex; flex-direction: column; justify-content: space-evenly; padding: 10pt 0 24pt; }
.r { display: flex; align-items: baseline; gap: 14pt; border-bottom: 0.5pt solid #e1dbcd; padding: 2pt 0 4pt; }
.lab { flex: none; width: 1.15in; font: 400 7.5pt 'Arris Mono'; letter-spacing: .08em; text-transform: uppercase; color: #8c8577; }
.s { white-space: nowrap; overflow: hidden; line-height: 1.12; }
.s.wrap { white-space: normal; line-height: 1.35; max-height: 2.8em; }
"""


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'proofs' / 'quick-brown-fox.pdf'
    body = (page('Upright, nine weights', 1, weights()) + page('Italic, nine weights', 2, weights(italic=True))
            + page('Sizes', 3, waterfall()) + page('Arris Mono', 4, mono()))
    doc = f'<!doctype html><html><head><meta charset="utf-8"><style>{fonts()}{CSS}</style></head><body>{body}</body></html>'
    work = BUILD / 'fox.html'
    work.write_text(doc, encoding='utf-8')
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b = pw.chromium.launch(args=['--disable-lcd-text'])
        pg = b.new_page()
        pg.goto(work.as_uri())
        pg.evaluate('document.fonts.ready')
        pg.wait_for_timeout(300)
        pg.pdf(path=str(out), width='11in', height='8.5in', print_background=True)
        b.close()
    print(out)


if __name__ == '__main__':
    main()
