"""Package a release: the built fonts, the licence, the readme, in one zip.

    uv run python tools/package.py        -> build/release/Arris-<version>.zip

Layout inside the zip:
    Arris-<version>/
      static/        every static TTF (Arris, Arris Watch, Arris Mono, their italics)
      variable/      Arris[GRAD,WTCH,wght].ttf, Arris-Italic[GRAD,WTCH,wght].ttf
      web/           WOFF2 of all of the above
      OFL.txt  AUTHORS.txt  README.md

It packages what is in build/; build first (build/scripts/rebuild.sh). It
checks that every font carries the release version and the licence, and
refuses to package a mixed or stale set.
"""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from arris.font import LICENSE_URL, VERSION  # noqa: E402

BUILD = ROOT / 'build'


def check(path: Path) -> list[str]:
    f = TTFont(path, lazy=True)
    name = f['name']
    problems = []
    if f'{f["head"].fontRevision:.3f}' != VERSION:
        problems.append(f'version {f["head"].fontRevision:.3f}, not {VERSION}')
    if str(name.getName(14, 3, 1, 0x409)) != LICENSE_URL:
        problems.append('no licence URL')
    if f['OS/2'].fsType != 0:
        problems.append(f'fsType {f["OS/2"].fsType}')
    return problems


def main():
    statics = sorted(p for p in BUILD.glob('Arris*.ttf') if '[' not in p.name)
    variables = sorted(BUILD.glob('Arris*[[]*.ttf'))
    if not statics or len(variables) != 2:
        sys.exit(f'nothing to package: {len(statics)} static, {len(variables)} variable fonts in build/')
    bad = {p.name: c for p in statics + variables if (c := check(p))}
    if bad:
        for n, c in bad.items():
            print(f'  {n}: {", ".join(c)}')
        sys.exit(f'{len(bad)} fonts are not release fonts: rebuild')
    top = f'Arris-{VERSION}'
    out = BUILD / 'release' / f'{top}.zip'
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for p in statics:
            z.write(p, f'{top}/static/{p.name}')
        for p in variables:
            z.write(p, f'{top}/variable/{p.name}')
        for p in statics + variables:
            f = TTFont(p)
            f.flavor = 'woff2'
            w = out.parent / (p.stem + '.woff2')
            f.save(w)
            z.write(w, f'{top}/web/{w.name}')
            w.unlink()
        for doc in ('OFL.txt', 'AUTHORS.txt', 'README.md'):
            z.write(ROOT / doc, f'{top}/{doc}')
    print(f'{out}: {len(statics)} static, {len(variables)} variable, {out.stat().st_size / 1e6:.1f} MB')


if __name__ == '__main__':
    main()
