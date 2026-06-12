"""Peak lineshapes. Every shape is evaluated unit-area over the given x window,
then scaled by the peak's area parameter — so fitted areas are directly usable
for RSF quantification.

mix is %Lorentzian, 0..100 (XPSPEAK convention "0:G, 100:L").
"""
from __future__ import annotations

import numpy as np
from scipy.special import voigt_profile

_LN2 = np.log(2.0)


def gaussian(x: np.ndarray, center: float, fwhm: float) -> np.ndarray:
    sigma = fwhm / (2.0 * np.sqrt(2.0 * _LN2))
    return np.exp(-0.5 * ((x - center) / sigma) ** 2) / (sigma * np.sqrt(2.0 * np.pi))


def lorentzian(x: np.ndarray, center: float, fwhm: float) -> np.ndarray:
    gamma = fwhm / 2.0
    return gamma / (np.pi * ((x - center) ** 2 + gamma**2))


def _trapz_norm(y: np.ndarray, x: np.ndarray) -> np.ndarray:
    a = float(np.trapezoid(y, x))
    return y / a if a > 0 else y


def gl_sum(x: np.ndarray, center: float, fwhm: float, mix: float) -> np.ndarray:
    m = np.clip(mix, 0.0, 100.0) / 100.0
    return (1.0 - m) * gaussian(x, center, fwhm) + m * lorentzian(x, center, fwhm)


def gl_product(x: np.ndarray, center: float, fwhm: float, mix: float) -> np.ndarray:
    """CasaXPS-style GL product form; normalized numerically over the window."""
    m = np.clip(mix, 0.0, 100.0) / 100.0
    u = (x - center) ** 2 / fwhm**2
    y = np.exp(-4.0 * _LN2 * (1.0 - m) * u) / (1.0 + 4.0 * m * u)
    return _trapz_norm(y, x)


def voigt(x: np.ndarray, center: float, fwhm: float, mix: float) -> np.ndarray:
    """True Voigt. mix splits the total width: L-FWHM = mix% of fwhm, rest Gaussian."""
    m = np.clip(mix, 0.0, 100.0) / 100.0
    fwhm_l = max(m * fwhm, 1e-6)
    fwhm_g = max((1.0 - m) * fwhm, 1e-6)
    sigma = fwhm_g / (2.0 * np.sqrt(2.0 * _LN2))
    gamma = fwhm_l / 2.0
    return voigt_profile(x - center, sigma, gamma)


def gl_tail(x: np.ndarray, center: float, fwhm: float, mix: float, ts: float) -> np.ndarray:
    """XPSPEAK-style asymmetric peak: GL convolved with a one-sided exponential
    decay (length ts, eV) toward higher binding energy. ts=0 -> symmetric GL."""
    base = gl_sum(x, center, fwhm, mix)
    if ts <= 1e-6 or x.size < 4:
        return base
    dx = float(np.median(np.diff(x)))
    if dx <= 0:
        return base
    n_tail = max(3, int(np.ceil(5.0 * ts / dx)))
    t = np.arange(n_tail) * dx
    kern = np.exp(-t / ts)
    kern /= kern.sum()
    # pad on the high-BE side so the tail doesn't wrap
    padded = np.concatenate([base, np.zeros(n_tail)])
    conv = np.convolve(padded, kern, mode="full")[: x.size]
    return _trapz_norm(conv, x)


def doniach_sunjic(x: np.ndarray, center: float, fwhm: float, alpha: float) -> np.ndarray:
    """Doniach-Šunjić for metallic (conduction-band screened) peaks.
    fwhm acts as the Lorentzian width Γ; alpha is the asymmetry (0 -> Lorentzian).
    Normalized numerically over the window (the analytic DS area diverges).
    Asymmetric tail extends toward higher binding energy."""
    gamma = fwhm / 2.0
    a = np.clip(alpha, 0.0, 0.95)
    e = x - center
    num = np.cos(np.pi * a / 2.0 + (1.0 - a) * np.arctan(e / gamma))
    den = (e**2 + gamma**2) ** ((1.0 - a) / 2.0)
    return _trapz_norm(num / den, x)


def evaluate(shape: str, x: np.ndarray, center: float, area: float, fwhm: float,
             mix: float, asym: float) -> np.ndarray:
    if shape == "GL_SUM":
        y = gl_sum(x, center, fwhm, mix)
    elif shape == "GL_PRODUCT":
        y = gl_product(x, center, fwhm, mix)
    elif shape == "VOIGT":
        y = voigt(x, center, fwhm, mix)
    elif shape == "GL_TAIL":
        y = gl_tail(x, center, fwhm, mix, asym)
    elif shape == "DONIACH":
        y = doniach_sunjic(x, center, fwhm, asym)
    else:
        raise ValueError(f"unknown shape: {shape}")
    return area * y
