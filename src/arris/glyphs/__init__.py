"""All glyph modules, registered in dependency order."""
from . import figures, caps, lower, punct  # noqa: F401
from . import marks

# Accented letters: Latin-1, Latin Extended-A, and Romanian's comma letters.
CHARS = [chr(c) for c in range(0xC0, 0x180)] + ['Ș', 'ș', 'Ț', 'ț']
BASES = {spec.unicode and chr(spec.unicode): name for name, spec in marks.REGISTRY.items() if spec.unicode}
ACCENTED = marks.compose(CHARS, BASES)
