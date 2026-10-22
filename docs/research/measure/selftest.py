"""Check the slicing measurements against synthetic outlines with known answers.

  uv run --no-project --with fonttools --with skia-pathops --with numpy python selftest.py
"""

import math

from fontTools.pens.recordingPen import RecordingPen

from geom import Outline
from measure_fonts import m_bowl, stroke_fit


class _G:
    def __init__(self, rec, width=1000):
        self.rec, self.width = rec, width

    def draw(self, pen):
        self.rec.replay(pen)


def poly(pen, pts):
    pen.moveTo(pts[0])
    for p in pts[1:]:
        pen.lineTo(p)
    pen.closePath()


def octagon(x0, y0, x1, y1, c):
    return [(x0 + c, y0), (x1 - c, y0), (x1, y0 + c), (x1, y1 - c), (x1 - c, y1), (x0 + c, y1),
            (x0, y1 - c), (x0, y0 + c)]


def outline(rec):
    return Outline.from_glyphset({"g": _G(rec)}, "g")


def check(label, got, want, tol=0.05):
    ok = abs(got - want) <= tol
    print(f"{'ok ' if ok else 'BAD'} {label}: got {got:.3f}, want {want:.3f}")
    return ok


def main():
    good = True
    # 1. octagonal ring: sides 80, top/bottom 60, outer chamfer leg 100, inner leg 50
    tv, th, Lo, Li = 80, 60, 100, 50
    rec = RecordingPen()
    poly(rec, octagon(0, 0, 500, 700, Lo))
    inner = octagon(tv, th, 500 - tv, 700 - th, Li)[::-1]       # reversed = hole
    poly(rec, inner)
    o = outline(rec)

    class FakeG:                                          # minimal Glyphs stand-in
        def __call__(self, ch):
            return o
    flags = []
    b = m_bowl(FakeG(), "O", {"cap": 700}, flags)
    good &= check("octagon side", b["side"], tv)
    good &= check("octagon top", b["top"], th)
    good &= check("octagon corner (chamfer-line distance)", b["corner_t"], (tv + th - Lo + Li) / math.sqrt(2))
    good &= check("outer chamfer leg", b["ch_out_dx"], Lo)
    good &= check("inner chamfer leg", b["ch_in_dx"], Li)

    # 2. straight diagonal stroke, 30 deg from vertical, perpendicular thickness 70
    a, t = math.radians(30), 70.0
    w = t / math.cos(a)                                   # horizontal cut width
    dx = 700 * math.tan(a)
    rec = RecordingPen()
    poly(rec, [(100, 0), (100 + w, 0), (100 + w + dx, 700), (100 + dx, 700)])
    s = stroke_fit(outline(rec), [200, 300, 400, 500], lambda iv: iv[0] if len(iv) == 1 else None)
    good &= check("diagonal perpendicular thickness", s["t"], t)
    good &= check("diagonal angle from vertical", s["angle"], 30.0)

    # 3. two overlapping rectangles (overlap removal): one 90-unit stem
    rec = RecordingPen()
    poly(rec, [(0, 0), (90, 0), (90, 700), (0, 700)])
    poly(rec, [(0, 300), (90, 300), (90, 400), (0, 400)])
    iv = outline(rec).hslice(350)
    good &= check("overlapping contours slice as one interval", len(iv), 1, 0)
    good &= check("overlap stem width", iv[0][1] - iv[0][0], 90)

    # 4. circular ring (quadratic curves through the flattening path): 45-degree thickness
    from fontTools.pens.transformPen import TransformPen
    rec = RecordingPen()

    def circle(pen, cx, cy, r):
        """8 quadratic arcs; on-curve points every 45 degrees lie exactly on the circle."""
        on = [(cx + r * math.cos(math.radians(45 * i)), cy + r * math.sin(math.radians(45 * i)))
              for i in range(8)]
        ro = r / math.cos(math.radians(22.5))
        off = [(cx + ro * math.cos(math.radians(45 * i + 22.5)),
                cy + ro * math.sin(math.radians(45 * i + 22.5))) for i in range(8)]
        pen.moveTo(on[0])
        for i in range(8):
            pen.qCurveTo(off[i], on[(i + 1) % 8])
        pen.closePath()

    circle(rec, 400, 400, 300)
    rec2 = RecordingPen()
    circle(rec2, 400, 400, 220)
    # reverse the inner circle by mirroring it in x about its centre
    tp = TransformPen(rec, (-1, 0, 0, 1, 800, 0))
    rec2.replay(tp)
    o = outline(rec)
    b = m_bowl(FakeG(), "O", {"cap": 700}, flags)
    good &= check("ring side (radial 80)", b["side"], 80, 0.5)
    good &= check("ring 45-degree corner", b["corner_t"], 80, 0.5)
    print("ALL OK" if good else "SOME CHECKS FAILED")


if __name__ == "__main__":
    main()
