"""The source drawings: Dymaxion's Draft zone numerals and the Chamfer rule.

``heritage/draft_lettering.py`` is a verbatim copy of the watch face's
``tools/draft-lettering.py`` (commit in ``heritage/SOURCE_COMMIT``). Its ZONE
table holds the 9x12 figure masters with two-module stems; the watch enlarges
them three times and cuts every exposed corner at 45 degrees.

``trace`` applies that same rule exactly, in module units with y up (row 0
is the top of the cap height), and returns the ink as a shapely geometry.
"""
from __future__ import annotations

import re
from functools import cache
from pathlib import Path

import shapely
import shapely.affinity
from shapely.geometry import Polygon

ROOT = Path(__file__).resolve().parents[2]


@cache
def tables() -> dict[str, dict[str, list[str]]]:
    src = (ROOT / 'heritage' / 'draft_lettering.py').read_text()
    ns: dict = {}
    exec(compile(src, 'draft_lettering.py', 'exec'), ns)  # trusted local copy
    return {'ZONE': ns['ZONE'], 'TEXT': ns['TEXT']}


def zone(ch: str) -> list[str]:
    return tables()['ZONE'][ch]


def trace(rows: list[str]):
    """The Chamfer rule on a pixel master, exactly, in module units (y up)."""
    H, W = len(rows), len(rows[0])

    def ink(x, y):
        return 0 <= y < H and 0 <= x < W and rows[y][x] == '#'

    polys = []
    for y in range(H):
        for x in range(W):
            x0, x1, y0, y1, mx, my = x, x + 1, y, y + 1, x + .5, y + .5
            up, dn, lf, rt = ink(x, y - 1), ink(x, y + 1), ink(x - 1, y), ink(x + 1, y)
            if ink(x, y):
                p = []
                for corner, a, b, cut in [((x0, y0), up, lf, [(x0, my), (mx, y0)]),
                                          ((x1, y0), up, rt, [(mx, y0), (x1, my)]),
                                          ((x1, y1), dn, rt, [(x1, my), (mx, y1)]),
                                          ((x0, y1), dn, lf, [(mx, y1), (x0, my)])]:
                    p += cut if (not a and not b) else [corner]
                polys.append(Polygon(p))
            else:
                if up and lf: polys.append(Polygon([(x0, y0), (mx, y0), (x0, my)]))
                if up and rt: polys.append(Polygon([(x1, y0), (x1, my), (mx, y0)]))
                if dn and rt: polys.append(Polygon([(x1, y1), (mx, y1), (x1, my)]))
                if dn and lf: polys.append(Polygon([(x0, y1), (x0, my), (mx, y1)]))
    g = shapely.union_all(polys).buffer(0)
    # flip to y-up: row 0 sits at the top of the cap height
    return shapely.affinity.scale(g, 1, -1, origin=(0, H / 2))
