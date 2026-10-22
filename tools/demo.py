"""A demonstration of the whole family, set from the built fonts by
HarfBuzz with their features on (so ligatures, marks, locl and kerning
show as a reader would see them), and a terminal screen from Arris Mono.

usage: demo.py out.png      (build the fonts first: README, Building)
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from fontTools.ttLib import TTFont
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from hbspec import line  # noqa: E402
from terminal_proofs import tui  # noqa: E402

VF = 'build/Arris[GRAD,WTCH,wght].ttf'
VFI = 'build/Arris-Italic[GRAD,WTCH,wght].ttf'
REG = 'build/Arris-Regular.ttf'
MONO = 'build/ArrisMono-Regular.ttf'
MONOI = 'build/ArrisMono-Italic.ttf'
LABEL = 'build/ArrisMono-Medium.ttf'

PANGRAM = 'Sphinx of black quartz, judge my vow · 0123456789'

SECTIONS = [
    ('Arris', [
        (VF, 'Arris', 150, ['wght=100']),
        (VF, 'Arris', 150, ['wght=400']),
        (VF, 'Arris', 150, ['wght=900']),
    ], 'row'),
    ('Weight 100–900', [(VF, PANGRAM, 40, [f'wght={w}']) for w in (100, 300, 500, 700, 900)], 'col'),
    ('Italic: chamfers become curves, cursive forms', [
        (VFI, 'The quick brown fox jumps over the lazy dog · 12:45', 40, ['wght=300']),
        (VFI, 'Sensible, expressive, swift · kek yes · ffi 3/8', 40, ['wght=600']),
        (VFI, 'Ваш ясный кругозор мягко взвешивает', 40, ['wght=900']),
    ], 'col'),
    ('Grade and watch axes', [
        (VF, 'Grade −100  Hamburgefonstiv 10:08', 40, ['wght=600', 'GRAD=-100']),
        (VF, 'Grade +100  Hamburgefonstiv 10:08', 40, ['wght=600', 'GRAD=100']),
        (VF, 'Watch 100  Hamburgefonstiv 10:08', 40, ['wght=600', 'WTCH=100']),
    ], 'col'),
    ('Languages', [
        (REG, 'Tiếng Việt: Người ta có thể ăn kính mà không hại gì.', 36, []),
        (REG, 'Hànyǔ Pīnyīn: nǚ lǜ · Zażółć gęślą jaźń · Příliš žluťoučký kůň', 36, []),
        (REG, 'Қазақша: Әр ұлттың өз тілі бар · Oʻzbek: Gʻalaba · Ўзбек: Ғалаба', 36, []),
        (REG, 'Ελληνικά: Ξεσκεπάζω την ψυχοφθόρα βδελυγμία · ϐ ϑ ϖ ϰ Ϙ Ϛ', 36, []),
        (REG, 'вдж ий кл птц шщ  (Russian)', 36, []),
        (REG, 'вдж ий кл птц шщ  (Bulgarian)', 36, ['lang=bg']),
        (VFI, 'бгдпт  (Russian italic)', 36, ['wght=400']),
        (VFI, 'бгдпт  (Serbian italic)', 36, ['wght=400', 'lang=sr']),
    ], 'col'),
    ('Symbols', [
        (REG, '€ £ ¥ ₹ ₽ ₺ ₴ ₸ ₩ ₪ ₫ ₿ ₦ ₱ ₲ ₵ $ ¢', 40, []),
        (REG, 'H₂O · E=mc² · x²+y²  ½ ⅓ ¾ ⅞ · Ⅻ Ⅳ ⅹ · № ℃ ™ ℓ ℮ ℞ ℗', 40, []),
        (REG, '← ↑ → ↓ ↔ ⇒ ⇔ ↺ ⇄  ∀x∈ℝ ∑ ∫ ∂ ∇ √ ∞ ≈ ≠ ≤ ⊆ ∪ ⊕ ⊗', 40, []),
        (REG, '■ □ ▲ △ ● ○ ◆ ◇ ★ ☆ ✓ ✗ ♠ ♣ ♥ ♦ ⌘ ⌥ ⏎ ⚙ ⚠ ⚡ ⌚ ⏰ ♫', 40, []),
        (VF, '← ⇒ ∑ ∫ ★ ♥ ⌘ ₿ ¶ § & @ #', 40, ['wght=900']),
    ], 'col'),
    ('Arris Mono: programming ligatures', [
        (MONO, 'const ok = (a, b) => a !== b && a >= 0;', 36, []),
        (MONO, 'if x != y || x <= 0 { x |> f }  // -> :: := ..=', 36, []),
        (MONO, '<!-- html --> </> #{ } ~~> <$> 0xFF 1_000 www', 36, []),
        (MONOI, 'fn main() -> Result<(), Error> { Ok(()) }  // italic', 36, []),
        (MONO, '<= >= != == ===  (ss03: plain comparisons)', 36, ['ss03']),
    ], 'col'),
]


def label(text):
    return line(LABEL, text, 22, [])


def _tint(img, level=110):
    return img.point(lambda v: 255 - (255 - v) * (255 - level) // 255)


def section(title, rows, layout):
    imgs = [line(path, text, px, feats) for path, text, px, feats in rows]
    if layout == 'row':
        body = Image.new('L', (sum(i.width for i in imgs) + 40 * (len(imgs) - 1), max(i.height for i in imgs)), 255)
        x = 0
        for i in imgs:
            body.paste(i, (x, 0)); x += i.width + 40
    else:
        body = Image.new('L', (max(i.width for i in imgs), sum(i.height for i in imgs)), 255)
        y = 0
        for i in imgs:
            body.paste(i, (0, y)); y += i.height
    head = _tint(label(title))
    out = Image.new('L', (max(head.width, body.width), head.height + body.height), 255)
    out.paste(head, (0, 0)); out.paste(body, (0, head.height))
    return out


def terminal():
    path = Path('/tmp/demo-tui.txt')
    path.write_text('\n'.join(tui()) + '\n', encoding='utf-8')
    out = '/tmp/demo-tui.png'
    subprocess.run([sys.executable, 'tools/cell_proof.py', out, '30', f'{MONO}::@{path}'], check=True,
                   stdout=subprocess.DEVNULL)
    img = Image.open(out).convert('L')
    head = _tint(label('Arris Mono: a terminal (box drawing, blocks, Braille, Powerline)'))
    page = Image.new('L', (max(head.width, img.width), head.height + img.height), 255)
    page.paste(head, (0, 0)); page.paste(img, (0, head.height))
    return page


def missing():
    """Characters in the demo that a font lacks (they would show as .notdef)."""
    out = []
    for _, rows, _ in SECTIONS:
        for path, text, _, _ in rows:
            cmap = TTFont(path).getBestCmap()
            out += [(path, ch) for ch in text if ord(ch) not in cmap and ch not in ' \n']
    return out


if __name__ == '__main__':
    gone = missing()
    if gone:
        print('missing:', sorted(set(gone)))
    parts = [section(*s) for s in SECTIONS] + [terminal()]
    pad, gap = 48, 40
    W = max(p.width for p in parts) + 2 * pad
    H = sum(p.height for p in parts) + gap * (len(parts) - 1) + 2 * pad
    page = Image.new('L', (W, H), 255)
    y = pad
    for p in parts:
        page.paste(p, (pad, y)); y += p.height + gap
    page.save(sys.argv[1])
    print(page.size)
