"""The reference-font set and static-instance loading.

Variable fonts are instanced with fontTools.varLib.instancer at the requested
wght, every other axis pinned at its default, and cached under
fonts/instances/.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

HERE = Path(__file__).resolve().parent
FONTS = HERE / "fonts"
CACHE = FONTS / "instances"


@dataclass(frozen=True)
class Face:
    family: str
    group: str            # neutral | chamfer | mono
    style: str            # Regular | Bold
    file: str             # file name in fonts/
    loc: tuple = ()       # ((tag, value), ...) for variable fonts

    @property
    def label(self):
        return f"{self.family} {self.style}"


def _vf(family, group, file, weights=(("Regular", 400), ("Bold", 700)), extra=()):
    return [Face(family, group, s, file, (("wght", w),) + tuple(extra)) for s, w in weights]


def _st(family, group, stem, styles=("Regular", "Bold")):
    return [Face(family, group, s, f"{stem}-{s}.ttf") for s in styles]


FACES: list[Face] = [
    # neutral references
    *_vf("Roboto", "neutral", "Roboto[wdth,wght].ttf"),
    *_vf("Inter", "neutral", "Inter[opsz,wght].ttf"),
    *_vf("Jost", "neutral", "Jost[wght].ttf"),
    *_vf("Montserrat", "neutral", "Montserrat[wght].ttf"),
    *_st("Barlow", "neutral", "Barlow"),
    *_st("Atkinson Hyperlegible", "neutral", "AtkinsonHyperlegible"),
    *_st("B612", "neutral", "B612"),
    *_st("B612 Mono", "mono", "B612Mono"),
    # chamfered / octagonal relatives
    *_st("Chakra Petch", "chamfer", "ChakraPetch"),
    *_vf("Oxanium", "chamfer", "Oxanium[wght].ttf"),
    *_vf("Orbitron", "chamfer", "Orbitron[wght].ttf"),
    *_st("Aldrich", "chamfer", "Aldrich", ("Regular",)),
    *_st("Michroma", "chamfer", "Michroma", ("Regular",)),
    *_st("Share Tech Mono", "chamfer", "ShareTechMono", ("Regular",)),
    *_st("Tomorrow", "chamfer", "Tomorrow"),
    *_vf("Saira", "chamfer", "Saira[wdth,wght].ttf"),
    *_st("Rajdhani", "chamfer", "Rajdhani"),
    *_st("Turret Road", "chamfer", "TurretRoad"),
    *_st("Bai Jamjuree", "chamfer", "BaiJamjuree"),
    # monospaced
    *_vf("JetBrains Mono", "mono", "JetBrainsMono[wght].ttf"),
    *_st("IBM Plex Mono", "mono", "IBMPlexMono"),
    *_vf("Roboto Mono", "mono", "RobotoMono[wght].ttf"),
    *_st("Space Mono", "mono", "SpaceMono"),
    *_vf("Red Hat Mono", "mono", "RedHatMono[wght].ttf"),
]

ROBOTO_FLEX = "RobotoFlex[GRAD,XOPQ,XTRA,YOPQ,YTAS,YTDE,YTFI,YTLC,YTUC,opsz,slnt,wdth,wght].ttf"


def full_location(font: TTFont, loc: dict) -> dict:
    """Pin every fvar axis: requested value or the axis default."""
    out = {}
    for a in font["fvar"].axes:
        out[a.axisTag] = loc.get(a.axisTag, a.defaultValue)
    return out


def instance(file: str, loc: dict) -> TTFont:
    """Static instance of a variable font (cached), or the static font."""
    src = FONTS / file
    if not loc:
        return TTFont(src)
    CACHE.mkdir(parents=True, exist_ok=True)
    key = "_".join(f"{k}{v:g}" for k, v in sorted(loc.items()))
    out = CACHE / f"{src.stem.split('[')[0]}__{key}.ttf"
    if out.exists():
        return TTFont(out)
    vf = TTFont(src)
    st = instancer.instantiateVariableFont(vf, full_location(vf, loc), inplace=False,
                                           updateFontNames=False)
    st.save(out)
    return TTFont(out)


def load(face: Face) -> TTFont:
    return instance(face.file, dict(face.loc))
