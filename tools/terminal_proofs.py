"""The terminal and UI glyphs' proof sheets, from the built fonts (build them
first: build_fonts.py 100,400,900 [mono] [italic] and 400,900 mono italic).

usage: terminal_proofs.py   -> proofs/terminal-*.png

Every sheet is set as a terminal sets text: rows at the font's line height,
glyphs at their advances (tools/cell_proof.py), so cells that should join
are seen joining.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

TMP = Path(tempfile.mkdtemp())
DING = ('✓✔✕✖✗✘✚✛✜✢✣✤✥✦✧✱✲✳✴✵✶✷✸✹❌❎❓❔❕❗➔➜➤★☆☐☑☒☰☱☲☳☴☵☶☷☺☹♠♣♥♦♤♧♡♢♩♪♫♬⚠⚡⚙⚐⚑⚫⚪⬆⬇⬅➡⬛⬜⬤'
        '')
TILE = [
    '┌──┬──┐ ┏━━┳━━┓ ╔══╦══╗ ╭──┬──╮ ┍━━┯━━┑ ╓──╥──╖ ╱╲╱╲╱╲ ▛▀▀▜ ░░▒▒▓▓██',
    '│  │  │ ┃  ┃  ┃ ║  ║  ║ │  │  │ │  │  │ ║  ║  ║ ╲╱╲╱╲╱ ▌▞▚▐ ░░▒▒▓▓██',
    '├──┼──┤ ┣━━╋━━┫ ╠══╬══╣ ├──┼──┤ ┝━━┿━━┥ ╟──╫──╢ ╱╲╱╲╱╲ ▌▚▞▐ ░░▒▒▓▓██',
    '│  │  │ ┃  ┃  ┃ ║  ║  ║ │  │  │ │  │  │ ║  ║  ║ ╳╳╳╳╳╳ ▙▄▄▟ ▁▂▃▄▅▆▇█',
    '└──┴──┘ ┗━━┻━━┛ ╚══╩══╝ ╰──┴──╯ ┕━━┷━━┙ ╙──╨──╜ ╲╱╲╱╲╱ ▗▖▝▘ █▇▆▅▄▃▂▁',
    '┄┄┄┄┄┄┄ ┅┅┅┅┅┅┅ ┈┈┈┈┈┈┈ ┉┉┉┉┉┉┉ ╌╌╌╌╌╌╌ ╍╍╍╍╍╍╍ ┆┇┊┋╎╏ ▏▎▍▌▋▊▉█ ▕▐ ▔▔',
    '┆┆┆┆┆┆┆ ┇┇┇┇┇┇┇ ┊┊┊┊┊┊┊ ┋┋┋┋┋┋┋ ╎╎╎╎╎╎╎ ╏╏╏╏╏╏╏ ┆┇┊┋╎╏ ▏▎▍▌▋▊▉█ ▕▐ ▔▔',
]


def table(start, end, per, spaced=True, blank=True):
    """Code points in rows, a space between glyphs and a blank row between
    rows (each glyph reads on its own)."""
    cps = [chr(c) for c in range(start, end + 1)]
    rows = []
    for i in range(0, len(cps), per):
        rows.append((' ' if spaced else '').join(cps[i:i + per]))
        if blank:
            rows.append('')
    return rows[:-1] if blank else rows


def tui():
    """A TUI: a Powerline prompt, a framed window with a title, a progress
    bar, sparklines in blocks and Braille, shades, shapes, every kind of
    frame, and dingbats."""
    W, L = 46, 14

    def row(left, right):
        return '│' + left.ljust(L) + '│' + right.ljust(W - L - 3) + '│'

    def full(text):
        return '│' + text.ljust(W - 2) + '│'

    rows = [
        '«1» {E0A0} main {E0B0}«2» ~/code/arris-type {E0B0}«0» {E0B1} make proofs   «3»{E0B2} 12:04 {E0B3} ✓ «0»',
        '╭─┤ Arris Mono ├' + '─' * (W - 17) + '╮',
        full(' build    ▕' + '█' * 18 + '▌' + ' ' * 7 + '▏ 72%'),
        full(' tests    ✓ 4 passed  ✗ 0 failed  ⚠ 1'),
        '├' + '─' * L + '┬' + '─' * (W - L - 3) + '┤',
        row(' cpu ▁▂▃▅▆▇█▇', ' ⣀⣤⣶⣿⣿⣷⣦⣄⡀⢀⣠⣴⣾⣿⣷⣦⣤⣀ net ░▒▓█'),
        row(' mem ████▋', ' ◆ fonts  ● vf  ○ docs  ★ ok'),
        '├' + '─' * L + '┼' + '─' * (W - L - 3) + '┤',
        row(' ▶ Thin', ' ┏━━━━━━━━┓ ╔════════╗ ┌┄┄┄┐'),
        row(' ▷ Regular', ' ┃ heavy  ┃ ║ double ║ ┆   ┆'),
        row(' ▸ Black', ' ┗━━━━━━━━┛ ╚════════╝ └┄┄┄┘'),
        '╰' + '─' * L + '┴' + '─' * (W - L - 3) + '╯',
        ' ☐ todo ☑ done ☒ dropped ☰ menu ♫ ⚙ ⚡ ➜ ⬆ ⬇',
    ]
    for r in rows[1:-1]:
        assert len(r) == W, (len(r), r)
    return rows


def write(name, rows):
    path = TMP / name
    path.write_text('\n'.join(rows) + '\n', encoding='utf-8')
    return f'@{path}'


def sheet(out, px, *blocks):
    args = [f'{src}::{text}::{label}' for src, text, label in blocks]
    subprocess.run([sys.executable, 'tools/cell_proof.py', f'proofs/{out}', str(px), *args], check=True)


M = 'build/ArrisMono-{}.ttf'
P = 'build/Arris-{}.ttf'
WEIGHTS = [('Thin', 'Thin'), ('Regular', 'Regular'), ('Black', 'Black'), ('BlackItalic', 'Black Italic')]

if __name__ == '__main__':
    box = write('box.txt', table(0x2500, 0x257F, 32))
    sheet('terminal-box.png', 30, *[(M.format(f), box, f'Mono {n}') for f, n in WEIGHTS],
          (P.format('Regular'), box, 'Arris Regular'))
    tiling = write('tiling.txt', TILE)
    sheet('terminal-tiling.png', 40, *[(M.format(f), tiling, f'Mono {n}') for f, n in WEIGHTS])
    t = write('tui.txt', tui())
    sheet('terminal-tui.png', 30, *[(M.format(f), t, f'Mono {n}') for f, n in WEIGHTS])
    blocks = write('blocks.txt', table(0x2580, 0x259F, 32))
    sheet('terminal-blocks.png', 40, *[(M.format(f) + '+grid', blocks, f'Mono {n}') for f, n in WEIGHTS[:3]])
    braille = write('braille.txt', table(0x2800, 0x28FF, 32, spaced=False, blank=False))
    sheet('terminal-braille.png', 34, *[(M.format(f), braille, f'Mono {n}') for f, n in WEIGHTS[:3]])
    shapes = write('shapes.txt', table(0x25A0, 0x25FF, 24))
    sheet('terminal-shapes.png', 64, *[(P.format(f), shapes, n) for f, n in WEIGHTS],
          (M.format('Regular'), shapes, 'Mono Regular'))
    lines = [' '.join(DING[i:i + 26]) for i in range(0, len(DING), 26)]
    ding = write('dingbats.txt', [r for line in lines for r in (line, '')][:-1])
    sheet('terminal-dingbats.png', 64, *[(P.format(f), ding, n) for f, n in WEIGHTS],
          (M.format('Regular'), ding, 'Mono Regular'), (M.format('Black'), ding, 'Mono Black'))
