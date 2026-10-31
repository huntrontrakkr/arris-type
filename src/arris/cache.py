"""The drawing cache.

What the engine draws once it keeps, for every process and every run that
asks for the same drawing from the same code: build/cache/draw.sqlite, or
the file ARRIS_CACHE names (empty: no cache). A drawing is keyed by what
it is, the glyph, its parameters and the flags of the call, and stamped
with the code it came from: each module that took part, by a hash of its
source. Which modules took part is watched as the drawing is made:
``using`` opens a record, and sys.monitoring names the module of every
function that starts while it is open. Each is widened by the modules it
imports, which hold the constants it reads. A stamp is read against the
code as it is now, so a change to one glyph module keeps every drawing
that did not run it; ``prune`` drops the rest.
"""
from __future__ import annotations

import hashlib
import inspect
import os
import re
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
KEY = 'v2'                                  # the shape of keys and stamps: change it and every row is new
LEAVES = frozenset({'font', 'cache'})      # in by their own code alone: font builds fonts from drawings and the
                                            # cache keeps them; what they import is not a drawing's

_HASHES: dict[str, str] | None = None
_IMPORTS: dict[str, frozenset[str]] = {}
_VALID: dict[str | None, bool] = {}
_FILES: dict[str, str] = {}
_DEPS: list[set[str]] = []
_DB: tuple[int, sqlite3.Connection] | None = None


def hashes() -> dict[str, str]:
    """Every module of the package by a hash of its source, named from the
    package root ('draw', 'glyphs.technical'). version.py is left out: a
    version is not a drawing's. font is in by its drawing functions alone:
    its name table is not a drawing's either."""
    global _HASHES
    if _HASHES is None:
        out: dict[str, str] = {}
        for f in sorted(ROOT.rglob('*.py')):
            if '__pycache__' in f.parts or f.name == 'version.py':
                continue
            name = _module_name(f)
            if not name:
                continue
            if name == 'font':
                from . import font
                src = ''.join(inspect.getsource(x) for x in (font.Metrics, font._place_drawn, font._body,
                                                              font._shift_record, font.mark_over))
                out[name] = hashlib.sha1(src.encode()).hexdigest()[:12]
            else:
                out[name] = hashlib.sha1(f.read_bytes()).hexdigest()[:12]
        _HASHES = out
    return _HASHES


def _module_name(f: Path) -> str:
    """A file's module name from the package root; '' for the package itself."""
    name = f.relative_to(ROOT).with_suffix('').as_posix().replace('/', '.')
    name = name.removesuffix('.__init__')
    return '' if name == '__init__' else name


_IMPORT = re.compile(r'^[ \t]*from[ \t]+(\.+)([\w.]*)[ \t]+import[ \t]+([^\n#]+)', re.MULTILINE)


def imports(name: str) -> frozenset[str]:
    """The package modules a module imports, by name: where its constants come from."""
    if name not in _IMPORTS:
        out: set[str] = set()
        if name not in LEAVES:
            f = ROOT / (name.replace('.', '/') + '.py')
            if not f.is_file():
                f = ROOT / name.replace('.', '/') / '__init__.py'
            pkg = name.rpartition('.')[0]
            for dots, mod, names in _IMPORT.findall(f.read_text(encoding='utf-8')):
                base = pkg
                for _ in dots[1:]:
                    base = base.rpartition('.')[0]
                if mod:
                    out.add(f'{base}.{mod}'.strip('.'))
                else:                                       # from . import a, b: modules by name
                    for n in names.replace('(', ' ').replace(')', ' ').split(','):
                        words = n.split()
                        if words:
                            out.add(f'{base}.{words[0]}'.strip('.'))
        _IMPORTS[name] = frozenset(m for m in out if m in hashes() and m != 'cache')
    return _IMPORTS[name]


# the watch: sys.monitoring tells of every Python function that starts while
# a record is open, and the function's file names its module
_TOOL = 3                                   # a tool id of our own (0, 1, 2 and 5 are the debugger's, coverage's, the profiler's, the optimizer's)


def _module_of(filename: str) -> str:
    m = _FILES.get(filename)
    if m is None:
        f = Path(filename)
        try:
            f.resolve().relative_to(ROOT)
            m = _module_name(f.resolve())
        except ValueError:
            m = ''
        if m in ('cache', 'version'):
            m = ''
        _FILES[filename] = m
    return m


def _started(code, offset):
    m = _module_of(code.co_filename)
    if m:
        for rec in _DEPS:
            rec.add(m)
    return sys.monitoring.DISABLE           # once a function is named it need not tell again until the next record


class using:
    """A record of the modules a drawing runs, open while it is drawn:
    ``with using() as mods: ...``. Records nest: a drawing made inside
    another counts for both, and starts from what the other has seen."""

    def __enter__(self) -> set[str]:
        mon = sys.monitoring
        self.mods: set[str] = set(_DEPS[-1]) if _DEPS else set()
        if not _DEPS:
            mon.use_tool_id(_TOOL, 'arris.cache')
            mon.register_callback(_TOOL, mon.events.PY_START, _started)
            mon.set_events(_TOOL, mon.events.PY_START)
        _DEPS.append(self.mods)
        mon.restart_events()                # every function tells once more, for this record
        return self.mods

    def __exit__(self, *exc) -> bool:
        _DEPS.pop()
        if not _DEPS:
            mon = sys.monitoring
            mon.set_events(_TOOL, 0)
            mon.register_callback(_TOOL, mon.events.PY_START, None)
            mon.free_tool_id(_TOOL)
        return False


def used(*modules: str) -> None:
    """Name modules the drawing in hand came from without running them: a
    drawing taken from the cache inside another names its own."""
    for rec in _DEPS:
        rec.update(m for m in modules if m)


def stamp(modules) -> str:
    """The code a drawing came from: the modules that ran, each with the
    modules it imports, each with its hash."""
    mods = set(modules)
    for m in list(mods):
        mods |= imports(m)
    h = hashes()
    return KEY + ' ' + ' '.join(f'{m}={h[m]}' for m in sorted(mods) if m in h)


def valid(st: str | None) -> bool:
    """Whether a stamp names the code as it is now."""
    if st not in _VALID:
        h = hashes()
        parts = (st or '').split()
        _VALID[st] = bool(parts) and parts[0] == KEY and all(
            '=' in q and h.get(q.partition('=')[0]) == q.partition('=')[2] for q in parts[1:])
    return _VALID[st]


def engine_hash() -> str:
    """One hash of the engine's drawing code as a whole: for logs, not keys."""
    h = hashes()
    return hashlib.sha1(' '.join(f'{m}={h[m]}' for m in sorted(h)).encode()).hexdigest()


def key(*parts) -> str:
    """A row's key: what a drawing is."""
    return hashlib.sha1(repr((KEY,) + parts).encode()).hexdigest()


def path() -> str:
    return os.environ.get('ARRIS_CACHE', str(ROOT.parents[1] / 'build' / 'cache' / 'draw.sqlite'))


def db() -> sqlite3.Connection | None:
    """This process's connection (opened afresh in a forked child); None with no cache."""
    global _DB
    p = path()
    if not p:
        return None
    if _DB is None or _DB[0] != os.getpid():
        Path(p).parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(p, timeout=300, isolation_level=None)
        # a fresh file: workers racing to switch it to WAL get "locked" at
        # once, not after the timeout, so try again until one has (WAL stays
        # with the file, and the switch is then a no-op for the rest)
        for tries in range(200):
            try:
                con.execute('PRAGMA journal_mode=WAL')
                con.execute('CREATE TABLE IF NOT EXISTS draw (k TEXT PRIMARY KEY, e TEXT, v BLOB)')
                con.execute('CREATE TABLE IF NOT EXISTS anchor (k TEXT PRIMARY KEY, e TEXT, v TEXT)')   # draw._anchor
                break
            except sqlite3.OperationalError as e:
                if 'locked' not in str(e) or tries == 199:
                    raise
                time.sleep(0.05)
        con.execute('PRAGMA synchronous=NORMAL')
        _DB = (os.getpid(), con)
    return _DB[1]


def prune() -> int:
    """Drop every drawing whose code has changed; returns how many went."""
    con = db()
    if con is None:
        return 0
    n = 0
    for table in ('draw', 'anchor'):
        stale = [e for (e,) in con.execute(f'SELECT DISTINCT e FROM {table}').fetchall() if not valid(e)]
        for e in stale:
            n += con.execute(f'DELETE FROM {table} WHERE e = ?', (e,)).rowcount
    con.execute('PRAGMA wal_checkpoint(TRUNCATE)')
    return n
