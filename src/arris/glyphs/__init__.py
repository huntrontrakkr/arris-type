"""All glyph modules, registered in dependency order."""
from . import figures, caps, lower, punct, extra_latin, cyrillic, greek, symbols  # noqa: F401
from . import italic_forms  # noqa: F401  (the italic's own lowercase)
from . import latin_plus  # noqa: F401  (Vietnamese, pinyin, Latin Extended-B and Additional; combining marks)
from . import cyrillic_ext, cyrillic_locl, greek_ext  # noqa: F401  (Cyrillic beyond Russian with locl; Greek symbols)
from . import african  # noqa: F401  (West African Latin: Ɛ Ɔ Ɲ Ɓ Ɗ Ƙ Ƴ and their lowercase)
from . import marks

# Accented letters: Latin-1, Latin Extended-A, and Romanian's comma letters.
CHARS = [chr(c) for c in range(0xC0, 0x180)] + [chr(c) for c in (0x218, 0x219, 0x21A, 0x21B)] + \
    [chr(c) for c in range(0x400, 0x460)] + [chr(c) for c in range(0x370, 0x400)]
ALIASES = dict(cyrillic.ALIASES) | dict(greek.ALIASES) | dict(symbols.ALIASES) | dict(cyrillic_ext.ALIASES) | dict(greek_ext.ALIASES) | \
    dict(african.ALIASES)
BASES = {chr(spec.unicode): name for name, spec in marks.REGISTRY.items() if spec.unicode}
BASES.update({chr(cp): name for cp, name in ALIASES.items()})
ACCENTED = marks.compose(CHARS, BASES)

from . import terminal, shapes, dingbats  # noqa: E402,F401  (terminal cells, geometric shapes, dingbats)
from . import genpunct, supsubs, currency, letterlike, numberforms  # noqa: E402,F401  (docs/coverage/symbols-plus.md)
ALIASES.update(genpunct.ALIASES | letterlike.ALIASES | numberforms.ALIASES)
from . import arrows, operators, technical  # noqa: E402,F401  (arrows, operators, technical symbols)
from . import features  # noqa: E402,F401  (variants of everything above)
from . import origin  # noqa: E402,F401  (ss20: the watch's pixel figures)
from . import ligatures  # noqa: E402,F401  (the monospaced cut's programming ligatures)
