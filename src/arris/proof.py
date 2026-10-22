"""Proof rendering: rings to images, without going through a font file."""
from __future__ import annotations

from PIL import Image, ImageDraw


def render(items, scale=0.25, pad=40, gap=40, height=None, baseline=None, ink=0, paper=255):
    """items: list of (rings, advance). Draws left to right on one line.
    Coordinates are font units; y is flipped. Holes are drawn with paper."""
    asc = height if height is not None else 800
    desc = baseline if baseline is not None else 250
    W = int(pad * 2 + sum(a for _, a in items) * scale + gap * scale * max(len(items) - 1, 0))
    H = int(pad * 2 + (asc + desc) * scale)
    img = Image.new('L', (W, H), paper)
    d = ImageDraw.Draw(img)
    x0 = pad
    for rings, adv in items:
        def tx(pt):
            return (x0 + pt[0] * scale, pad + (asc - pt[1]) * scale)
        # signed area: >0 shells (ink), <0 holes (paper); draw shells first
        def area(r):
            return sum(r[i - 1][0] * r[i][1] - r[i][0] * r[i - 1][1] for i in range(len(r))) / 2
        for r in sorted(rings, key=lambda r: -area(r)):
            d.polygon([tx(p) for p in r], fill=ink if area(r) > 0 else paper)
        x0 += (adv + gap) * scale
    return img


def supersample(fn, k=4, **kw):
    kw = dict(kw)
    kw['scale'] = kw.get('scale', 0.25) * k
    kw['pad'] = kw.get('pad', 40) * k
    img = fn(**kw)
    return img.resize((img.width // k, img.height // k), Image.LANCZOS)


def render_svg(items, scale=0.25, pad=40, gap=40, height=800, baseline=250, ink='#000', paper='#fff'):
    """Like ``render`` but through cairo: exact, antialiased."""
    import io
    import cairosvg
    W = pad * 2 + (sum(a for _, a in items) + gap * max(len(items) - 1, 0)) * scale
    H = pad * 2 + (height + baseline) * scale
    paths, x0 = [], pad
    for rings, adv in items:
        for r in rings:
            pts = [(x0 + x * scale, pad + (height - y) * scale) for x, y in r]
            paths.append('M' + 'L'.join(f'{x:.2f},{y:.2f}' for x, y in pts) + 'Z')
        x0 += (adv + gap) * scale
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{H:.0f}">'
           f'<rect width="100%" height="100%" fill="{paper}"/>'
           f'<path fill="{ink}" fill-rule="nonzero" d="{" ".join(paths)}"/></svg>')
    png = cairosvg.svg2png(bytestring=svg.encode())
    return Image.open(io.BytesIO(png)).convert('L')
