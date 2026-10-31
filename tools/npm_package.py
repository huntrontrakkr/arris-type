"""The web fonts of a release as an npm package, @arristype/arris.

    python3 tools/npm_package.py build/release/Arris-<version>.zip build/npm

Takes the release zip's WOFF2s (web/) and its licence, and writes a package
a site can install or load from a CDN:

    files/            every WOFF2: Arris (variable, and static as an
                      alternative), Arris Mono, Arris Watch
    index.css         Arris (variable), Arris Mono and Arris Watch
    arris.css         Arris alone: the variable fonts, upright and italic
    arris-static.css  Arris as nine static weights a style, instead of arris.css
    mono.css          Arris Mono, nine weights, upright and italic
    watch.css         Arris Watch, nine weights
    package.json  README.md  OFL.txt  AUTHORS.txt

A face downloads only when a page uses it, so index.css costs nothing
until then. The font version 1.005 is npm's 1.5.0 (a minor revision of
the font is a minor version of the package). Standard library only: the
release workflow runs it without the build's environment.
"""
from __future__ import annotations

import json
import re
import sys
import zipfile
from pathlib import Path

NAME = '@arristype/arris'
REPO = 'https://github.com/huntrontrakkr/arris-type'
WEIGHTS = {'Thin': 100, 'ExtraLight': 200, 'Light': 300, 'Regular': 400, 'Medium': 500,
           'SemiBold': 600, 'Bold': 700, 'ExtraBold': 800, 'Black': 900}
# the variable fonts under names a bundler takes as they are (no brackets or commas)
VARIABLE = {'Arris[GRAD,WTCH,wght].woff2': 'Arris-Variable.woff2',
            'Arris-Italic[GRAD,WTCH,wght].woff2': 'Arris-Italic-Variable.woff2'}


def semver(version: str) -> str:
    """1.005 -> 1.5.0."""
    major, _, minor = version.partition('.')
    return f'{int(major)}.{int(minor or 0)}.0'


def face(family: str, file: str, weight: str, style: str) -> str:
    return (f'@font-face {{\n  font-family: "{family}";\n  font-style: {style};\n  font-weight: {weight};\n'
            f'  font-display: swap;\n  src: url("./files/{file}") format("woff2");\n}}\n')


def statics(family: str, prefix: str, files: set[str]) -> str:
    """A static family's faces: each weight, upright and (where there is one) italic."""
    out = []
    for style_name, weight in WEIGHTS.items():
        for italic in (False, True):
            stem = ('Italic' if style_name == 'Regular' else f'{style_name}Italic') if italic else style_name
            file = f'{prefix}-{stem}.woff2'
            if file in files:
                out.append(face(family, file, str(weight), 'italic' if italic else 'normal'))
    return '\n'.join(out)


def readme(version: str, npm_version: str) -> str:
    return f"""# Arris

A chamfered geometric sans family with an industrial character, a cursive
italic, and a monospaced companion. Nine weights, and a variable font with
three axes: weight (`wght` 100–900), grade (`GRAD` −100–100) and watch
(`WTCH` 0–100). This package is the web fonts of Arris {version}: WOFF2 and
CSS. The desktop fonts (TTF) are in the release zip on
[GitHub]({REPO}/releases).

Site: [arristype.com](https://arristype.com) · Source: [GitHub]({REPO})

## Install

```
npm install {NAME}
```

```js
import '{NAME}';              // Arris (variable), Arris Mono and Arris Watch
import '{NAME}/arris.css';    // or one family: arris.css, mono.css, watch.css
```

Or from a CDN, without installing:

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/{NAME}@{npm_version.split('.')[0]}/index.css">
```

A face downloads only when a page uses it.

## Use

```css
body {{ font-family: "Arris", sans-serif; font-weight: 400; }}
em   {{ font-style: italic; }}                       /* the cursive italic */
code {{ font-family: "Arris Mono", monospace; }}     /* with programming ligatures */
h1   {{ font-weight: 850; font-variation-settings: "GRAD" 50, "WTCH" 100; }}
```

| File | Family | What it is |
|---|---|---|
| `arris.css` | Arris | The variable fonts, upright and italic: any weight from 100 to 900, and grade and watch through `font-variation-settings`. |
| `arris-static.css` | Arris | Nine static weights a style, instead of `arris.css` (use one or the other). |
| `mono.css` | Arris Mono | Nine weights, upright and italic, every glyph on one advance. |
| `watch.css` | Arris Watch | Nine weights with the watch's own stroke balance. |
| `index.css` | all three | `arris.css`, `mono.css` and `watch.css`. |

Features through `font-feature-settings`: `tnum` (default) `pnum` `zero`
`ss01` `sups` `subs` `frac` `case`, and `ss20`, the figures in the watch's
pixels; in Mono, `ss03` turns the ligatures off.

## Licence

SIL Open Font License 1.1 (`OFL.txt`), no Reserved Font Name.
"""


def main() -> int:
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    src, out = Path(sys.argv[1]), Path(sys.argv[2])
    m = re.fullmatch(r'Arris-(\d+\.\d+)\.zip', src.name)
    if not m:
        sys.exit(f'{src.name}: not a release zip (Arris-<version>.zip)')
    version = m.group(1)
    files_dir = out / 'files'
    files_dir.mkdir(parents=True, exist_ok=True)
    top = f'Arris-{version}'
    with zipfile.ZipFile(src) as z:
        web = [n for n in z.namelist() if n.startswith(f'{top}/web/') and n.endswith('.woff2')]
        names = set()
        for n in web:
            base = n.rsplit('/', 1)[1]
            name = VARIABLE.get(base, base)
            (files_dir / name).write_bytes(z.read(n))
            names.add(name)
        for doc in ('OFL.txt', 'AUTHORS.txt'):
            (out / doc).write_bytes(z.read(f'{top}/{doc}'))
    if set(VARIABLE.values()) - names:
        sys.exit(f'{src.name}: no variable web fonts in web/')
    arris = (face('Arris', VARIABLE['Arris[GRAD,WTCH,wght].woff2'], '100 900', 'normal') + '\n'
             + face('Arris', VARIABLE['Arris-Italic[GRAD,WTCH,wght].woff2'], '100 900', 'italic'))
    css = {
        'arris.css': arris,
        'arris-static.css': statics('Arris', 'Arris', names),
        'mono.css': statics('Arris Mono', 'ArrisMono', names),
        'watch.css': statics('Arris Watch', 'ArrisWatch', names),
    }
    css['index.css'] = '\n'.join(css[k] for k in ('arris.css', 'mono.css', 'watch.css'))
    head = f'/* Arris {version}, SIL Open Font License 1.1: {REPO} */\n'
    for k, v in css.items():
        (out / k).write_text(head + v)
    npm_version = semver(version)
    pkg = {
        'name': NAME,
        'version': npm_version,
        'description': ('Arris, a chamfered geometric sans family with an industrial character, a cursive italic, '
                        'and a monospaced companion: web fonts (WOFF2) and CSS, variable on three axes.'),
        'keywords': ['font', 'fonts', 'typeface', 'variable-font', 'woff2', 'sans-serif', 'monospace', 'italic',
                     'arris', 'chamfer'],
        'homepage': 'https://arristype.com',
        'bugs': f'{REPO}/issues',
        'repository': {'type': 'git', 'url': f'git+{REPO}.git'},
        'license': 'OFL-1.1',
        'author': 'Wade Hunter',
        'main': 'index.css',
        'style': 'index.css',
        'exports': {'.': './index.css', './*.css': './*.css', './files/*': './files/*',
                    './package.json': './package.json'},
        'sideEffects': ['*.css'],
        'files': ['files', '*.css', 'OFL.txt', 'AUTHORS.txt'],
        'fontVersion': version,
    }
    (out / 'package.json').write_text(json.dumps(pkg, indent=2) + '\n')
    (out / 'README.md').write_text(readme(version, npm_version))
    print(f'{NAME}@{npm_version} (Arris {version}): {len(names)} fonts in {out}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
