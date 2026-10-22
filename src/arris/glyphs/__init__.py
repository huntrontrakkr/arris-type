"""All glyph modules, registered in dependency order."""
from . import figures, caps, lower, punct, extra_latin, cyrillic, greek, symbols  # noqa: F401
from . import italic_forms  # noqa: F401  (the italic's own lowercase)
from . import marks

# Accented letters: Latin-1, Latin Extended-A, and Romanian's comma letters.
CHARS = [chr(c) for c in range(0xC0, 0x180)] + [chr(c) for c in (0x218, 0x219, 0x21A, 0x21B)] + \
    [chr(c) for c in range(0x400, 0x460)] + [chr(c) for c in range(0x370, 0x400)]
ALIASES = dict(cyrillic.ALIASES) | dict(greek.ALIASES) | dict(symbols.ALIASES)
BASES = {chr(spec.unicode): name for name, spec in marks.REGISTRY.items() if spec.unicode}
BASES.update({chr(cp): name for cp, name in ALIASES.items()})
ACCENTED = marks.compose(CHARS, BASES)

from . import terminal, shapes, dingbats  # noqa: E402,F401  (terminal cells, geometric shapes, dingbats)
from . import features  # noqa: E402,F401  (variants of everything above)
