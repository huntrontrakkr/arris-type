"""The drawing cache: what stamps a drawing, and when a stamp is stale."""
import sqlite3

import arris.glyphs  # noqa: F401
from arris import cache
from arris.font import _place
from arris.instances import params


def test_hashes_name_the_modules():
    h = cache.hashes()
    assert {'draw', 'geom', 'params', 'font', 'glyphs.caps', 'glyphs.technical'} <= set(h)
    assert 'version' not in h and not any(m.split('.')[0] == 'vf' for m in h) and all(len(v) == 12 for v in h.values())
    assert {'draw', 'glyphs.figures', 'glyphs.letterframe'} <= cache.imports('glyphs.caps') and not cache.imports('font')


def test_a_drawing_is_stamped_with_what_it_ran(tmp_path, monkeypatch):
    monkeypatch.setenv('ARRIS_CACHE', str(tmp_path / 'draw.sqlite'))
    monkeypatch.setattr(cache, '_DB', None)
    monkeypatch.setattr('arris.font._MEM', {})
    p = params(400, 0, watch=0)
    with cache.using() as mods:
        _place('uni23ED', p)
    assert {'draw', 'geom', 'font', 'glyphs.technical'} <= mods
    assert 'glyphs.cyrillic' not in mods
    con = sqlite3.connect(tmp_path / 'draw.sqlite')
    (e,) = con.execute('SELECT e FROM draw').fetchone()
    assert cache.valid(e) and 'glyphs.technical=' in e and 'glyphs.cyrillic=' not in e
    # a drawing taken from the cache inside another drawing counts for the other
    monkeypatch.setattr('arris.font._MEM', {})
    with cache.using() as outer:
        _place('uni23ED', p)
    assert 'glyphs.technical' in outer


def test_a_stamp_reads_the_code_as_it_is(monkeypatch):
    st = cache.stamp({'glyphs.caps'})
    assert cache.valid(st) and 'glyphs.caps=' in st and 'glyphs.technical=' not in st
    monkeypatch.setattr(cache, '_HASHES', dict(cache.hashes(), **{'glyphs.caps': 'ffffffffffff'}))
    monkeypatch.setattr(cache, '_VALID', {})
    assert not cache.valid(st)
    assert cache.valid(cache.stamp({'glyphs.technical'}))
    assert not cache.valid('a0b1c2d3e4f5') and not cache.valid(None)                 # rows of the old shape


def test_drawings_are_kept_and_dropped_with_their_code(tmp_path, monkeypatch):
    monkeypatch.setenv('ARRIS_CACHE', str(tmp_path / 'draw.sqlite'))
    monkeypatch.setattr(cache, '_DB', None)
    monkeypatch.setattr('arris.font._MEM', {})
    p = params(400, 0, watch=0)
    first = _place('A', p)
    con = sqlite3.connect(tmp_path / 'draw.sqlite')
    rows = con.execute('SELECT e FROM draw').fetchall()
    assert len(rows) == 1 and cache.valid(rows[0][0]) and 'glyphs.caps=' in rows[0][0]
    monkeypatch.setattr('arris.font._MEM', {})
    assert _place('A', p) == first                                        # from the file
    # the glyph's module changes: the row is stale, the drawing is made again and the row replaced
    monkeypatch.setattr(cache, '_HASHES', dict(cache.hashes(), **{'glyphs.caps': 'ffffffffffff'}))
    monkeypatch.setattr(cache, '_VALID', {})
    monkeypatch.setattr('arris.font._MEM', {})
    assert _place('A', p) == first
    rows = con.execute('SELECT e FROM draw').fetchall()
    assert len(rows) == 1 and 'glyphs.caps=ffffffffffff' in rows[0][0]
    # a row from other code goes with prune, the current one stays
    con.execute("INSERT INTO draw VALUES ('k', 'v2 draw=000000000000', x'00')"); con.commit()
    assert cache.prune() == 1
    assert con.execute('SELECT count(*) FROM draw').fetchone()[0] == 1
