"""A small model of the eye, for measuring outlines instead of eyeballing them.

Glyph outlines are rasterised to ink coverage and passed through a contrast
sensitivity filter for a given viewing condition (the angular size of the cap
height). The filter is the Mannos-Sakrison CSF, used as a low-pass: below its
peak frequency it passes everything, so it models blur, not contrast
adaptation. An oblique-effect term lowers sensitivity for diagonal spatial
frequencies by stretching their frequency, which is how the cut-off differs
between orientations.

Measurements built on it:

* ``perceived_top`` / ``perceived_bottom``: where the blurred glyph crosses half
  the plateau of a long horizontal bar of the same weight. A flat top crosses at
  its edge; chamfered tops cross lower, which is what overshoot must repay.
* ``weight_response``: the blurred peak of a long bar at any angle and thickness,
  for balancing horizontal, vertical and diagonal strokes.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageDraw


@dataclass(frozen=True)
class View:
    cap_arcmin: float          # angular size of the cap height
    cap_units: float = 720.0   # cap height in font units
    px_per_cap: int = 144      # raster resolution (well above the eye's)
    oblique: float = 0.0       # oblique effect: frequency stretch at 45 degrees

    @property
    def unit_px(self) -> float:
        return self.px_per_cap / self.cap_units

    @property
    def ppd(self) -> float:   # raster pixels per degree of visual angle
        return self.px_per_cap / (self.cap_arcmin / 60)


# Viewing conditions used throughout (cap height in arcminutes):
WATCH_CLOCK = 44.0   # 36 px cap on a 200 ppi watch at 35 cm
TEXT = 22.0          # a 10 pt cap at 40 cm
SMALL = 11.0         # a 7 px watch label


def _area(r):
    return sum(r[i - 1][0] * r[i][1] - r[i][0] * r[i - 1][1] for i in range(len(r))) / 2


def coverage(rings, view: View, x0: float, y0: float, w: float, h: float, ss: int = 4) -> np.ndarray:
    """Ink coverage of the rectangle [x0, x0+w] x [y0, y0+h] (font units),
    rows top to bottom, at the view's raster resolution."""
    s = view.unit_px
    W, H = int(math.ceil(w * s)), int(math.ceil(h * s))
    img = Image.new('L', (W * ss, H * ss), 0)
    d = ImageDraw.Draw(img)
    for r in sorted(rings, key=lambda r: -abs(_area(r))):
        pts = [((x - x0) * s * ss, (y0 + h - y) * s * ss) for x, y in r]
        d.polygon(pts, fill=255 if _area(r) > 0 else 0)
    a = np.asarray(img, dtype=np.float64) / 255.0
    return a.reshape(H, ss, W, ss).mean(axis=(1, 3))


def csf_lowpass(f: np.ndarray) -> np.ndarray:
    """Mannos-Sakrison CSF, normalised to 1 at its peak and held at 1 below it."""
    a = 2.6 * (0.0192 + 0.114 * f) * np.exp(-(0.114 * f) ** 1.1)
    fpk = 8.0  # cycles per degree, near the function's maximum
    peak = 2.6 * (0.0192 + 0.114 * fpk) * math.exp(-(0.114 * fpk) ** 1.1)
    return np.where(f < fpk, 1.0, a / peak)


def perceive(cov: np.ndarray, view: View, pad: int | None = None) -> np.ndarray:
    pad = pad if pad is not None else int(view.px_per_cap * 0.5)
    a = np.pad(cov, pad)
    fy = np.fft.fftfreq(a.shape[0]) * view.ppd   # cycles per degree
    fx = np.fft.fftfreq(a.shape[1]) * view.ppd
    FX, FY = np.meshgrid(fx, fy)
    f = np.hypot(FX, FY)
    if view.oblique:
        theta = np.arctan2(FY, FX)
        f = f * (1 + view.oblique * np.sin(2 * theta) ** 2)
    out = np.fft.ifft2(np.fft.fft2(a) * csf_lowpass(f)).real
    return out[pad:-pad, pad:-pad] if pad else out


def bar_rings(thickness: float, length: float, angle_deg: float = 0.0, cx=0.0, cy=0.0):
    t = math.radians(angle_deg)
    d, n = (math.cos(t), math.sin(t)), (-math.sin(t), math.cos(t))
    L, T = length / 2, thickness / 2
    pts = [(cx + sx * L * d[0] + sy * T * n[0], cy + sx * L * d[1] + sy * T * n[1])
           for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    return [pts]


def weight_response(thickness: float, angle_deg: float, view: View) -> float:
    """Blurred peak of a long bar: the perceived darkness of a stroke."""
    L = view.cap_units * 2
    rings = bar_rings(thickness, L, angle_deg)
    half = view.cap_units * 0.75
    cov = coverage(rings, view, -half, -half, 2 * half, 2 * half)
    p = perceive(cov, view)
    c = p.shape[0] // 2, p.shape[1] // 2
    return float(p[c[0] - 3:c[0] + 4, c[1] - 3:c[1] + 4].max())


def bar_plateau(thickness: float, view: View) -> float:
    return weight_response(thickness, 0.0, view)


def _crossing(profile: np.ndarray, thr: float, ys: np.ndarray, from_top: bool) -> float:
    idx = np.nonzero(profile >= thr)[0]
    if not len(idx):
        return float('nan')
    i = idx[0] if from_top else idx[-1]
    j = i - 1 if from_top else i + 1
    if j < 0 or j >= len(profile):
        return float(ys[i])
    # linear interpolation between the last sample below and the first above
    a, b = profile[j], profile[i]
    t = (thr - a) / (b - a) if b != a else 0.0
    return float(ys[j] + (ys[i] - ys[j]) * t)


def perceived_extent(rings, view: View, thr: float, x0: float, w: float, lo: float, hi: float):
    """(bottom, top) of the blurred glyph's iso-contour at ``thr``, font units."""
    margin = view.cap_units * 0.4
    y0, h = lo - margin, (hi - lo) + 2 * margin
    cov = coverage(rings, view, x0 - margin, y0, w + 2 * margin, h)
    p = perceive(cov, view)
    prof = p.max(axis=1)                         # rows top to bottom
    ys = y0 + h - (np.arange(len(prof)) + 0.5) / view.unit_px
    return _crossing(prof, thr, ys, from_top=False), _crossing(prof, thr, ys, from_top=True)


# --- Shape-size perception -------------------------------------------------
#
# Blur at the eye's resolution barely moves the top of a chamfered bowl, yet a
# round or cut-cornered form still looks short at every size: the eye judges a
# form's extent from its bulk near the extremity, over a window that scales
# with the form. Model that as a Gaussian over the glyph's silhouette with
# sigma a fixed fraction of the cap height, calibrated on circles against
# measured overshoots in well-made fonts, then transfer it to any shape.

def gaussian_blur(a: np.ndarray, sigma_px: float) -> np.ndarray:
    pad = int(4 * sigma_px) + 2
    b = np.pad(a, pad)
    fy = np.fft.fftfreq(b.shape[0])
    fx = np.fft.fftfreq(b.shape[1])
    FX, FY = np.meshgrid(fx, fy)
    G = np.exp(-2 * (math.pi * sigma_px) ** 2 * (FX ** 2 + FY ** 2))
    out = np.fft.ifft2(np.fft.fft2(b) * G).real
    return out[pad:-pad, pad:-pad]


def silhouette(rings):
    """The outer contours only: a glyph's form, ignoring its counters."""
    return [r for r in rings if _area(r) > 0]


def silhouette_extent(rings, kappa: float, cap: float = 720.0, px_per_cap: int = 240,
                      x0: float = -100, w: float = 800, lo: float = 0, hi: float = 720):
    """(bottom, top) of the half-level contour of the silhouette blurred with
    sigma = kappa * cap, in font units."""
    view = View(cap_arcmin=1.0, cap_units=cap, px_per_cap=px_per_cap)
    margin = cap * (4 * kappa + 0.1)
    y0, h = lo - margin, (hi - lo) + 2 * margin
    cov = coverage(silhouette(rings), view, x0 - margin, y0, w + 2 * margin, h)
    p = gaussian_blur(cov, kappa * px_per_cap)
    prof = p.max(axis=1)
    ys = y0 + h - (np.arange(len(prof)) + 0.5) / view.unit_px
    return _crossing(prof, 0.5, ys, from_top=False), _crossing(prof, 0.5, ys, from_top=True)


def circle_rings(d: float, cx: float, cy: float, n: int = 720):
    return [[(cx + d / 2 * math.cos(2 * math.pi * i / n), cy + d / 2 * math.sin(2 * math.pi * i / n))
             for i in range(n)]]


def rect_rings(x0, y0, x1, y1):
    return [[(x0, y0), (x1, y0), (x1, y1), (x0, y1)]]
