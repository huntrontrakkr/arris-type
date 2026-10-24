"""A magazine spread set in Arris: a test of the face at article length.

US Letter, portrait: kicker, headline, italic deck, byline, three columns of
body text with a drop cap, subheads, a pull quote, a picture with a caption
and a data sidebar in tabular figures. Writes proofs/magazine-page.pdf and
.png.

usage: magazine_page.py [body_pt]        (default 9.5)
needs: the static fonts in build/, Playwright's Chromium
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / 'build'
SOURCES = ROOT / 'presentation' / 'sources'

FACES = [('Arris', 'Light', 300, 'normal'), ('Arris', 'Regular', 400, 'normal'), ('Arris', 'Italic', 400, 'italic'),
         ('Arris', 'LightItalic', 300, 'italic'), ('Arris', 'SemiBold', 600, 'normal'), ('Arris', 'SemiBoldItalic', 600, 'italic'),
         ('Arris', 'Bold', 700, 'normal'), ('Arris', 'ExtraBold', 800, 'normal'), ('Arris', 'Black', 900, 'normal'),
         ('Arris Mono', 'Regular', 400, 'normal'), ('Arris Mono', 'Medium', 500, 'normal')]

BODY = [
    ('p', '<span class="drop">T</span>he coffee comes first. Before the burn plan, before the radiation check, before anyone '
          'says the word <i>perijove</i>, Tanya Okafor-Reyes pours two cups from a sealed bladder and clips them into '
          'the cradle beside her seat. One is for her. The other is for whoever is flying right seat that day, and on '
          'this run that is me.'),
    ('p', 'Okafor-Reyes has flown thirty-one slingshots around Jupiter. It is not a record (the record belongs to a '
          'Belter named Dawes, who stopped counting at sixty), but it is enough that the dock crews at Ganymede call '
          'her by her first name and the insurers call her by her last. Her ship, the <i>Kopeng</i>, is a long-hauler '
          'with a cargo spine of ice and machine parts and a cockpit about the size of a kitchen table.'),
    ('h', 'Why you burn at the bottom'),
    ('p', 'The physics is old and stubborn. A rocket gains the most from its fuel where it is already moving fastest, '
          'and nothing in the outer system moves faster than a ship falling toward the largest planet there is. '
          'Burn at the deepest point of the fall, the perijove, and every kilogram of propellant buys almost ten '
          'kilometres a second more than it would out in the dark. Pilots call it the Oberth gift. Accountants call '
          'it the only reason the route exists.'),
    ('p', 'What the physics leaves out is the weight. For forty-one seconds the drive pushes at three gravities, and '
          'the body takes it badly. The ship pumps the crew full of the cocktail everyone calls juice, a mix of '
          'stimulants and vessel tighteners that keeps the blood where the brain can use it. It works. It also makes '
          'your hands shake for an hour afterwards, which is why the coffee is poured before the burn and not after.'),
    ('quote', '“Up there you feel how heavy you really are. Then the burn stops, and you weigh nothing, '
              'and for a second you think you could stay.”'),
    ('h', 'Forty-one seconds'),
    ('p', 'We come in over the north pole, where the clouds are blue and knotted like old rope, and fall toward the '
          'equator in a long silent curve. The cockpit is quiet except for the countdown, which Okafor-Reyes reads '
          'aloud in Lang Belta out of habit: <i>taim fo bern</i>, time for the burn. At T minus ten she stops talking. '
          'At zero the seat comes up to meet me like a wave and does not stop.'),
    ('p', 'It is hard to describe three gravities to anyone who has not felt them. Your cheeks slide toward your ears. '
          'Your arms become sandbags. The edges of your sight go grey, then the grey closes in toward the centre, '
          'and you learn exactly how many seconds you have before it reaches the middle. On the display the numbers '
          'climb: velocity, then the gain, then a small green bar that fills toward the line marked <span class="m">KATOF</span>. '
          'Below us the Great Red Spot slides past like a slow eye.'),
    ('p', 'Then it is over. The drive cuts, the weight vanishes, and the coffee in its cradle trembles and settles. '
          'Okafor-Reyes checks the numbers twice, logs the burn, and only then reaches for her cup. "Sixty-one point '
          'four," she says. "Good one." Behind us Jupiter is already shrinking, and ahead there is nothing but four '
          'months of dark and the faint, specific light of the Sun.'),
    ('h', 'The economics of falling'),
    ('p', 'Every slingshot is a bet. Arrive a second late and the burn is wasted on a shallower curve; arrive a '
          'second early and the radiation belts take their share of your electronics and your bones. The cargo '
          'companies pay pilots like Okafor-Reyes not for courage but for timing, and she is very, very good at timing.'),
    ('p', 'She is also, she says, nearly done. Two more runs pay off the <i>Kopeng</i>. After that she plans to fly the '
          'short routes around the inner moons, where the gravity is gentle and nobody needs juice to get home. '
          '"I will miss it," she admits. "Not the weight. The quiet after." She finishes her coffee, unclips the cup, '
          'and starts the checklist for the long way back.'),
]

SIDEBAR = [('31', 'slingshots flown by Okafor-Reyes'), ('3.2 g', 'peak load during the burn'),
           ('41 s', 'length of the perijove burn'), ('61.4 km/s', 'speed at perijove'),
           ('+9.8 km/s', 'gained from the Oberth effect'), ('4 mo', 'coasting time to the inner system')]


CSS = """
@page { size: 8.5in 11in; margin: 0; }
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #f6f2ea; color: #17161a; font-family: 'Arris'; -webkit-font-smoothing: antialiased; font-kerning: normal; }
.page { position: relative; width: 8.5in; height: 11in; padding: 0.55in 0.6in 0.5in; overflow: hidden; background: #f6f2ea;
        page-break-after: always; break-after: page; }
.top { display: flex; justify-content: space-between; font: 500 7pt 'Arris Mono'; letter-spacing: .14em;
       text-transform: uppercase; color: #8d867a; border-bottom: 0.6pt solid #17161a; padding-bottom: 5pt; }
.top b { color: #17161a; font-weight: 500; }
.kicker { margin-top: 20pt; font: 600 8pt 'Arris'; letter-spacing: .16em; text-transform: uppercase; color: #d2452b; }
h1 { margin-top: 6pt; font: 900 46pt/0.92 'Arris'; letter-spacing: -0.012em; }
h1 i { font-style: italic; font-weight: 300; }
.dek { margin-top: 11pt; width: 5.4in; font: italic 300 14.5pt/1.32 'Arris'; color: #3b3a3f; }
.by { margin-top: 10pt; font: 400 7pt 'Arris Mono'; letter-spacing: .12em; text-transform: uppercase; color: #8d867a; }
.cols { column-count: 3; column-gap: 0.22in; font: 400 BODY_PTpt/LEADpt 'Arris'; hyphens: auto; }
.c1 { margin-top: 14pt; height: 6.3in; column-fill: auto; }
.c2 { margin-top: 14pt; height: 5.0in; column-fill: balance; }
.hero { margin-top: 16pt; position: relative; height: 3.7in; overflow: hidden; }
.hero img { width: 100%; height: 100%; object-fit: cover; object-position: 30% 55%; }
.hero .cap { position: absolute; left: 10pt; bottom: 9pt; font: 400 6.8pt/1.35 'Arris Mono'; letter-spacing: .06em; color: #f6f2ea; }
.hero .tag { position: absolute; right: 10pt; top: 9pt; font: 500 6.8pt 'Arris Mono'; letter-spacing: .14em; color: #ffb000; }
.cols p { margin: 0; text-indent: 1.2em; }
.cols p:first-child, .cols h3 + p, .cols blockquote + p, .cols .fig + p, .cols .side + p { text-indent: 0; }
.cols i { font-style: italic; }
.cols .m { font: 500 0.88em 'Arris Mono'; letter-spacing: .04em; }
.drop { float: left; font: 900 DROPpt/0.78 'Arris'; margin: 3pt 4pt 0 0; color: #d2452b; }
h3 { margin: 9pt 0 3pt; font: 700 H3pt/1.2 'Arris'; letter-spacing: .1em; text-transform: uppercase; break-after: avoid; }
blockquote { margin: 8pt 0 9pt; padding: 7pt 0; border-top: 1.4pt solid #d2452b; border-bottom: 0.6pt solid #d2452b;
             font: italic 600 QUOTEpt/1.18 'Arris'; color: #d2452b; break-inside: avoid; }
.fig { break-inside: avoid; margin: 2pt 0 8pt; }
.fig img { display: block; width: 100%; height: 1.55in; object-fit: cover; object-position: 50% 40%; }
.fig .cap { margin-top: 4pt; font: 400 6.6pt/1.35 'Arris Mono'; color: #6d675e; }
.side { break-inside: avoid; margin: 4pt 0 8pt; padding: 8pt 9pt 6pt; background: #17161a; color: #f6f2ea; }
.side .t { font: 500 6.6pt 'Arris Mono'; letter-spacing: .14em; text-transform: uppercase; color: #ffb000; margin-bottom: 5pt; }
.side .r { display: flex; justify-content: space-between; align-items: baseline; gap: 8pt; padding: 3pt 0; border-top: 0.5pt solid #3a3833; }
.side b { font: 700 12pt 'Arris'; font-feature-settings: 'tnum'; white-space: nowrap; }
.side span { font: 400 6.6pt/1.25 'Arris Mono'; color: #bdb5a8; text-align: right; }
.foot { position: absolute; left: 0.6in; right: 0.6in; bottom: 0.32in; display: flex; justify-content: space-between;
        font: 400 6.6pt 'Arris Mono'; letter-spacing: .12em; text-transform: uppercase; color: #8d867a; }
"""


def blocks(body_pt):
    """The article as a list of HTML blocks in reading order."""
    jup = (SOURCES / 'juno-pj18-jupiter.png').as_uri()
    out = []
    for kind, text in BODY:
        out.append(f'<p>{text}</p>' if kind == 'p' else f'<h3>{text}</h3>' if kind == 'h' else f'<blockquote>{text}</blockquote>')
    fig = (f'<div class="fig"><img src="{jup}"><div class="cap">The view from the right seat: the cloud bands of the '
           f'southern hemisphere, 18,220 km below, eleven seconds before the burn.</div></div>')
    side = '<div class="side"><div class="t">The run in numbers</div>' + ''.join(
        f'<div class="r"><b>{a}</b><span>{b}</span></div>' for a, b in SIDEBAR) + '</div>'
    out.insert(4, fig)
    out.insert(10, side)
    return out


def html(body_pt, split=None):
    """The spread: an opening page (headline, deck, the first columns) and a
    second page of three full columns; ``split`` blocks go on the first."""
    faces = '\n'.join(f"@font-face {{ font-family: '{fam}'; src: url('{(BUILD / (fam.replace(' ', '') + '-' + st + '.ttf')).as_uri()}'); "
                      f"font-weight: {w}; font-style: {it}; }}" for fam, st, w, it in FACES)
    bl = blocks(body_pt)
    split = len(bl) if split is None else split
    lead = body_pt * 1.47
    css = CSS.replace('BODY_PT', f'{body_pt}').replace('LEAD', f'{lead:.2f}').replace('DROP', f'{body_pt * 4.1:.1f}') \
        .replace('H3', f'{body_pt * 0.92:.1f}').replace('QUOTE', f'{body_pt * 1.55:.1f}')
    foot = lambda n: (f'<div class="foot"><span>Outer Line · 14</span><span>Set in Arris · text {body_pt}/{lead:.1f} pt</span>'
                      f'<span>{n}</span></div>')
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{faces}{css}</style></head><body>
<div class="page">
<div class="top"><span><b>Outer Line</b> · Issue 14</span><span>Long haul</span><span>October 2983</span></div>
<div class="kicker">Long haul · The Jupiter run</div>
<h1>Three g and a<br>cup of <i>coffee</i></h1>
<div class="dek">Thirty-one times, Tanya Okafor-Reyes has dived toward the largest planet in the system and fired
her engine at the bottom of the fall. We rode along for number thirty-two.</div>
<div class="by">Words by Ines Varga · Pictures NASA / Juno · 9 min read</div>
<div class="cols c1">{''.join(bl[:split])}</div>{foot(22)}</div>
<div class="page">
<div class="top"><span><b>Outer Line</b> · Issue 14</span><span>Long haul</span><span>October 2983</span></div>
<div class="hero"><img src="{(SOURCES / 'juno-pj18-jupiter.png').as_uri()}"><span class="tag">PERIJOVE · T−00:11</span>
<span class="cap">Jupiter's southern clouds and the Great Red Spot from 18,220 km. NASA / JPL-Caltech / SwRI / MSSS, Juno Perijove 18.</span></div>
<div class="cols c2">{''.join(bl[split:])}</div>{foot(23)}</div>
</body></html>"""


def main():
    pt = float(sys.argv[1]) if len(sys.argv) > 1 else 9.5
    out = ROOT / 'proofs' / 'magazine-page'
    work = BUILD / 'magazine.html'
    from playwright.sync_api import sync_playwright
    n = len(blocks(pt))
    with sync_playwright() as pw:
        b = pw.chromium.launch(args=['--disable-lcd-text'])
        pg = b.new_page(viewport={'width': 816, 'height': 2112}, device_scale_factor=2.5)
        fits = lambda sel: pg.evaluate(f"(() => {{ const c = document.querySelector('{sel}'); return c.scrollWidth <= c.clientWidth + 1; }})()")
        split = n
        while split > 1:                          # as many blocks on the opening page as fit
            work.write_text(html(pt, split), encoding='utf-8')
            pg.goto(work.as_uri()); pg.evaluate('document.fonts.ready'); pg.wait_for_timeout(150)
            if fits('.c1'):
                break
            split -= 1
        print('opening page:', split, 'of', n, 'blocks; second page fits:', fits('.c2'))
        pg.wait_for_timeout(300)
        pg.screenshot(path=str(out.with_suffix('.png')), full_page=True)
        pg.pdf(path=str(out.with_suffix('.pdf')), width='8.5in', height='11in', print_background=True)
        b.close()
    from PIL import Image
    im = Image.open(out.with_suffix('.png'))
    h = im.height // 2
    spread = Image.new('RGB', (im.width * 2 + 40, h), '#d8d2c6')
    spread.paste(im.crop((0, 0, im.width, h)), (0, 0))
    spread.paste(im.crop((0, h, im.width, 2 * h)), (im.width + 40, 0))
    spread.save(out.with_suffix('.png'))
    print(out.with_suffix('.pdf'))


if __name__ == '__main__':
    main()
