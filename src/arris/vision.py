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

_KERNELS: dict = {}


def gaussian_blur(a: np.ndarray, sigma_px: float) -> np.ndarray:
    """a blurred by a Gaussian of sigma_px, zero outside it: a real FFT on
    a grid padded by 4 sigma (no wrap) to a fast length, the kernel kept
    per grid (the same result as a plain FFT, to rounding, and some times
    faster: the blurs are most of a drawing's time)."""
    from scipy import fft as sfft
    pad = int(4 * sigma_px) + 2
    h, w = a.shape
    H = sfft.next_fast_len(h + 2 * pad, real=True)
    W = sfft.next_fast_len(w + 2 * pad, real=True)
    b = np.zeros((H, W))
    b[pad:pad + h, pad:pad + w] = a
    key = (H, W, sigma_px)
    if key not in _KERNELS:
        fy = np.fft.fftfreq(H)
        fx = np.fft.rfftfreq(W)
        _KERNELS[key] = np.exp(-2 * (math.pi * sigma_px) ** 2 * (fx[None, :] ** 2 + fy[:, None] ** 2))
    out = sfft.irfft2(sfft.rfft2(b) * _KERNELS[key], s=(H, W))
    return out[pad:pad + h, pad:pad + w]


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


# --- White that reads -------------------------------------------------------
#
# A white feature (a counter, the gap between a sign's bars, the notch where a
# bar runs out past a stem) is only a feature if a reader sees it. Squint at
# the drawing (blur it with a Gaussian a fixed share of the cap height wide)
# and look at the white narrower than a stem, where parts come close: white
# the blur fills in has fused, however open it is on paper.
#
# Narrow white comes in four kinds. A hole is closed white. A slot runs
# between two parts at much the same width all along (the gap between a
# sign's bars, the notch where they run out past a stem). A wedge narrows to
# nothing where two strokes meet at an angle (a K's crotch, an R's leg); the
# blur fills its point at every weight and in every face, so it is no fault.
# A shallow piece lies open along its length (where a chamfer meets a
# stroke's side): an inside corner, not white between parts.

SQUINT = 0.05       # the blur's sigma, as a share of the cap height
NARROW = 0.5        # white narrower than this many stems is narrow
READS = 0.55        # what narrow white keeps under the squint: the e's eye and the
                    # a's and s's counters at Bold and Black keep 0.52-0.59
WEDGE_KEEP = 0.6    # a slot keeps this much of its area opened by 0.4 of its half-width
SHALLOW = 0.4       # a piece open to wide white along this share of its edge is shallow


def _mask(poly, x0, y0, h, s, shape):
    img = Image.new('L', (shape[1], shape[0]), 0)
    d = ImageDraw.Draw(img)
    for q in getattr(poly, 'geoms', [poly]):
        if q.geom_type != 'Polygon':
            continue
        d.polygon([((x - x0) * s, (y0 + h - y) * s) for x, y in q.exterior.coords], fill=255)
        for r in q.interiors:
            d.polygon([((x - x0) * s, (y0 + h - y) * s) for x, y in r.coords], fill=0)
    return np.asarray(img) > 0


def _half_width(q, hi):
    """The largest r that q survives being eroded by (bisection)."""
    lo = 0.0
    for _ in range(14):
        mid = (lo + hi) / 2
        if q.buffer(-mid, join_style='mitre').is_empty:
            hi = mid
        else:
            lo = mid
    return lo


def narrow_whites(rings, sv: float, cap: float = 720.0, squint: float = SQUINT):
    """The narrow white of a drawing: [(piece, kind, depth)], kind 'hole',
    'slot', 'wedge' or 'shallow', depth how light the piece stays under the
    squint (1 - the blurred ink's median over it / the blurred ink's peak)."""
    from shapely.geometry import Polygon
    from .geom import rings_to_shapely
    if not rings:
        return []
    ink = rings_to_shapely(rings)
    rho = NARROW * sv
    closed = ink.buffer(rho, join_style='mitre').buffer(-rho, join_style='mitre')
    nw = closed.difference(ink).buffer(-0.5, join_style='mitre').buffer(0.5, join_style='mitre')
    pieces = [q for q in getattr(nw, 'geoms', [nw]) if q.geom_type == 'Polygon' and q.area > 4]
    if not pieces:
        return []
    holes = [Polygon(r) for q in getattr(ink, 'geoms', [ink]) for r in q.interiors]
    edge = ink.boundary.buffer(1.0)
    view = View(cap_arcmin=1.0, cap_units=cap, px_per_cap=144)
    s = view.unit_px
    bx0, by0, bx1, by1 = ink.bounds
    m = 4 * squint * cap
    x0, y0, w, h = bx0 - m, by0 - m, bx1 - bx0 + 2 * m, by1 - by0 + 2 * m
    seen = gaussian_blur(coverage(rings, view, x0, y0, w, h), squint * view.px_per_cap)
    peak = float(seen.max()) or 1.0
    out = []
    for q in pieces:
        msk = _mask(q, x0, y0, h, s, seen.shape)
        if msk.any():
            v = float(np.median(seen[msk]))
        else:
            c = q.representative_point()
            v = float(seen[min(seen.shape[0] - 1, max(0, int((y0 + h - c.y) * s))),
                           min(seen.shape[1] - 1, max(0, int((c.x - x0) * s)))])
        if any(hl.buffer(0.5).contains(q) for hl in holes):
            kind = 'hole'
        elif q.boundary.difference(edge).length >= SHALLOW * q.length:
            kind = 'shallow'
        else:
            r = _half_width(q, rho)
            kept = q.buffer(-0.4 * r, join_style='mitre').buffer(0.4 * r, join_style='mitre').area
            kind = 'slot' if kept >= WEDGE_KEEP * q.area else 'wedge'
        out.append((q, kind, 1.0 - v / peak))
    return out


def fused(rings, sv: float, cap: float = 720.0, zones=()):
    """The holes and slots of a drawing that the squint fills in (depth
    under READS), within ``zones`` (polygons) if any are given."""
    return [(q, kind, d) for q, kind, d in narrow_whites(rings, sv, cap)
            if kind in ('hole', 'slot') and d < READS
            and (not zones or any(q.intersects(z) for z in zones))]


OVERSHOOT_KAPPA = 0.1192   # silhouette blur (share of the zone height) at which a circle needs a 1.5% overshoot


_NEED: dict = {}
_RECT: dict = {}


def overshoot_need(rings, zone: float, kappa: float = OVERSHOOT_KAPPA):
    """(top, bottom) in font units that a glyph should reach past the zone
    (0 to ``zone``) to look as tall as a flat-edged form: its convex hull
    (openings do not count) blurred with sigma = kappa * zone, against the
    box it fills between the lines, compared at the half level. A flat top
    needs nothing; a chamfered or round one what its corners cost.

    Remembered by the hull it measures (a glyph is drawn again and again:
    every accented letter stamps its base), the box by its width: the
    blurs are most of a drawing's time."""
    from shapely.geometry import MultiPoint
    pts = [q[:2] for r in rings for q in r]
    if len(pts) < 3:
        return 0.0, 0.0
    hull = MultiPoint(pts).convex_hull
    if hull.geom_type != 'Polygon':
        return 0.0, 0.0
    from shapely.geometry import box as _box
    band = hull.intersection(_box(-1e4, 0, 1e4, zone))
    if band.is_empty or band.geom_type != 'Polygon':
        return 0.0, 0.0
    x0, _, x1, _ = band.bounds
    ring = [list(band.exterior.coords)[:-1]]
    if _area(ring[0]) < 0:
        ring = [ring[0][::-1]]
    key = (tuple(ring[0]), zone, kappa)
    if key not in _NEED:
        w = x1 - x0
        b1, t1 = silhouette_extent(ring, kappa, cap=zone, px_per_cap=160, x0=x0 - 20, w=w + 40, lo=0, hi=zone)
        rkey = (x0, x1, zone, kappa)
        if rkey not in _RECT:
            _RECT[rkey] = silhouette_extent(rect_rings(x0, 0, x1, zone), kappa, cap=zone, px_per_cap=160,
                                            x0=x0 - 20, w=w + 40, lo=0, hi=zone)
        b0, t0 = _RECT[rkey]
        if any(v != v for v in (b0, t0, b1, t1)):
            _NEED[key] = (0.0, 0.0)
        else:
            _NEED[key] = (max(t0 - t1, 0.0), max(b1 - b0, 0.0))
    return _NEED[key]
