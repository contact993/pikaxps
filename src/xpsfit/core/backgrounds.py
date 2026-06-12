"""Background models: linear, iterative Shirley, Shirley+linear, Tougaard (U2).

All functions take x ascending in binding energy and return the background
over the full x array (flat extrapolation outside the [i1, i2] window).
Physics convention: the inelastic step rises toward HIGHER binding energy,
so the background interpolates from y[i1] (low BE) up to y[i2] (high BE).
"""
from __future__ import annotations

import numpy as np

from .spectrum import BackgroundSpec, Region


def _endpoint(y: np.ndarray, i: int, avg: int) -> float:
    half = max(0, avg // 2)
    lo, hi = max(0, i - half), min(y.size, i + half + 1)
    return float(np.mean(y[lo:hi]))


def linear(x: np.ndarray, y: np.ndarray, i1: int, i2: int, avg: int = 3) -> np.ndarray:
    y1, y2 = _endpoint(y, i1, avg), _endpoint(y, i2, avg)
    bg = np.interp(x, [x[i1], x[i2]], [y1, y2])
    bg[: i1] = y1
    bg[i2 + 1:] = y2
    return bg


def shirley(
    x: np.ndarray,
    y: np.ndarray,
    i1: int,
    i2: int,
    avg: int = 3,
    max_iter: int = 100,
    tol: float = 1e-7,
) -> np.ndarray:
    """Iterative Shirley: B(E) = y1 + (y2-y1) * A(<E)/A_total of the peak signal."""
    y1, y2 = _endpoint(y, i1, avg), _endpoint(y, i2, avg)
    xs, ys = x[i1: i2 + 1], y[i1: i2 + 1]
    bg = np.linspace(y1, y2, xs.size)
    for _ in range(max_iter):
        signal = np.clip(ys - bg, 0.0, None)
        seg = 0.5 * (signal[1:] + signal[:-1]) * np.diff(xs)
        cum = np.concatenate(([0.0], np.cumsum(seg)))
        total = cum[-1]
        if total <= 0:
            bg_new = np.linspace(y1, y2, xs.size)
        else:
            bg_new = y1 + (y2 - y1) * cum / total
        delta = float(np.max(np.abs(bg_new - bg)))
        bg = bg_new
        if delta < tol * max(1.0, abs(y2 - y1)):
            break
    out = np.empty_like(y, dtype=float)
    out[: i1] = y1
    out[i1: i2 + 1] = bg
    out[i2 + 1:] = y2
    return out


def shirley_linear(
    x: np.ndarray, y: np.ndarray, i1: int, i2: int, slope: float, avg: int = 3
) -> np.ndarray:
    """XPSPEAK's "Shirley+Linear": a sloped line anchored at the low-BE endpoint
    is removed first, Shirley runs on the remainder, then the line is added back.
    slope=0 reduces to plain Shirley."""
    line = slope * (x - x[i1])
    bg = shirley(x, y - line, i1, i2, avg=avg)
    return bg + line


def tougaard_raw(
    x: np.ndarray, y: np.ndarray, i1: int, i2: int, c: float = 1643.0, avg: int = 3
) -> tuple[np.ndarray, float]:
    """Unscaled Tougaard loss integral over the window and the low-BE baseline."""
    y_lo = _endpoint(y, i1, avg)
    xs = x[i1: i2 + 1]
    ys = np.clip(y[i1: i2 + 1] - y_lo, 0.0, None)
    n = xs.size
    dx = np.gradient(xs)
    raw = np.zeros(n)
    for k in range(1, n):
        t = xs[k] - xs[:k]
        kern = t / (c + t * t) ** 2
        raw[k] = float(np.sum(kern * ys[:k] * dx[:k]))
    return raw, y_lo


def tougaard(
    x: np.ndarray,
    y: np.ndarray,
    i1: int,
    i2: int,
    b: float = 0.0,
    c: float = 1643.0,
    avg: int = 3,
) -> np.ndarray:
    """Tougaard U2 background: B(E) = b * sum_{E' < E} K(E - E') * (y(E') - y_lo) dE',
    K(T) = T / (c + T^2)^2.  Loss electrons appear at higher BE than their parent,
    so the integral runs over lower binding energies.
    b <= 0: auto-scale so the background meets the data at the high-BE endpoint.
    """
    raw, y_lo = tougaard_raw(x, y, i1, i2, c, avg)
    if b <= 0:
        y_hi = _endpoint(y, i2, avg) - y_lo
        b = (y_hi / raw[-1]) if raw[-1] > 0 else 0.0
    seg = y_lo + b * raw
    out = np.empty_like(y, dtype=float)
    out[: i1] = y_lo
    out[i1: i2 + 1] = seg
    out[i2 + 1:] = seg[-1]
    return out


def shirley_from_peaks(
    x: np.ndarray, peaks_sum: np.ndarray, i1: int, i2: int, y1: float, y2: float
) -> np.ndarray:
    """Active Shirley (Sherwood): background derived from the PEAK MODEL instead
    of the raw data — B(E) = y1 + (y2-y1)·A_model(<E)/A_model_total. Used when
    peaks and background are optimized together; immune to noise and to other
    structures inside the window."""
    xs = x[i1: i2 + 1]
    ps = np.clip(peaks_sum[i1: i2 + 1], 0.0, None)
    seg = 0.5 * (ps[1:] + ps[:-1]) * np.diff(xs)
    cum = np.concatenate(([0.0], np.cumsum(seg)))
    total = cum[-1]
    if total <= 0:
        inner = np.linspace(y1, y2, xs.size)
    else:
        inner = y1 + (y2 - y1) * cum / total
    out = np.empty_like(x, dtype=float)
    out[: i1] = y1
    out[i1: i2 + 1] = inner
    out[i2 + 1:] = y2
    return out


def compute(region: Region) -> np.ndarray:
    """Evaluate the region's BackgroundSpec over region.x."""
    x, y = region.x, region.y
    if x.size < 3:
        return np.zeros_like(y)
    i1, i2 = region.crop_indices()
    bg: BackgroundSpec = region.background
    if bg.kind == "NONE":
        return np.zeros_like(y)
    if bg.kind == "LINEAR":
        return linear(x, y, i1, i2, bg.avg_points)
    if bg.kind == "SHIRLEY":
        return shirley(x, y, i1, i2, bg.avg_points)
    if bg.kind == "SHIRLEY_LINEAR":
        return shirley_linear(x, y, i1, i2, bg.slope, bg.avg_points)
    if bg.kind == "TOUGAARD":
        return tougaard(x, y, i1, i2, bg.tougaard_b, bg.tougaard_c, bg.avg_points)
    raise ValueError(f"unknown background kind: {bg.kind}")
