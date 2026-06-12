"""lmfit-based fitting of a Region: peaks on top of a static background.

XPSPEAK semantics are kept: the background is computed from the data
(not co-fitted), peaks are optimized against (data - background) inside
the background window. Constraints between peaks are lmfit expressions
on parameters named p{i}_{center|area|fwhm|mix|asym}.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from lmfit import Parameters, minimize

from . import backgrounds, lineshapes
from .spectrum import Peak, Region


def param_name(peak_index: int, param: str) -> str:
    return f"p{peak_index}_{param}"


def build_parameters(peaks: list[Peak], only_peak: int | None = None) -> Parameters:
    """Two passes: plain params first, then exprs (so cross-references resolve).

    only_peak: if given, every other peak's parameters are frozen
    (XPSPEAK's "Optimise Peak" vs "Optimise Region").
    """
    params = Parameters()
    for i, peak in enumerate(peaks):
        for pname, spec in peak.params().items():
            vary = spec.vary and spec.expr is None
            if only_peak is not None and i != only_peak:
                vary = False
            params.add(
                param_name(i, pname),
                value=spec.value,
                vary=vary,
                min=spec.min,
                max=spec.max,
            )
    for i, peak in enumerate(peaks):
        for pname, spec in peak.params().items():
            if spec.expr and not (only_peak is not None and i != only_peak):
                params[param_name(i, pname)].expr = spec.expr
    return params


def eval_peaks(params: Parameters, peaks: list[Peak], x: np.ndarray) -> list[np.ndarray]:
    comps = []
    for i, peak in enumerate(peaks):
        v = {n: float(params[param_name(i, n)].value) for n in Peak.PARAM_NAMES}
        comps.append(
            lineshapes.evaluate(peak.shape, x, v["center"], v["area"], v["fwhm"], v["mix"], v["asym"])
        )
    return comps


@dataclass
class FitResult:
    success: bool
    message: str
    redchi: float
    nfev: int
    background: np.ndarray
    components: list[np.ndarray]
    envelope: np.ndarray  # background + sum(components), full x range
    residual: np.ndarray  # y - envelope, full x range
    stderr: dict[str, float | None] = field(default_factory=dict)
    report: str = ""


def _uses_active_bg(region: Region) -> bool:
    return (region.background.kind == "SHIRLEY" and region.background.active
            and bool(region.peaks))


def _bg_endpoints(region: Region) -> tuple[float, float]:
    i1, i2 = region.crop_indices()
    avg = region.background.avg_points
    return (backgrounds._endpoint(region.y, i1, avg),
            backgrounds._endpoint(region.y, i2, avg))


def eval_model(region: Region) -> FitResult:
    """Evaluate the current model without optimizing (for live plotting)."""
    params = build_parameters(region.peaks)
    comps = eval_peaks(params, region.peaks, region.x) if region.peaks else []
    if _uses_active_bg(region):
        i1, i2 = region.crop_indices()
        y1, y2 = _bg_endpoints(region)
        bg = backgrounds.shirley_from_peaks(region.x, np.sum(comps, axis=0), i1, i2, y1, y2)
    else:
        bg = backgrounds.compute(region)
    envelope = bg + (np.sum(comps, axis=0) if comps else 0.0)
    return FitResult(
        success=True, message="evaluated", redchi=float("nan"), nfev=0,
        background=bg, components=comps, envelope=envelope,
        residual=region.y - envelope,
    )


def fit_region(
    region: Region,
    only_peak: int | None = None,
    weight: str = "none",
    max_nfev: int = 5000,
) -> FitResult:
    """Optimize peak parameters; writes best values back into region.peaks."""
    if not region.peaks:
        return eval_model(region)
    i1, i2 = region.crop_indices()
    xw = region.x[i1: i2 + 1]
    active = _uses_active_bg(region)
    if active:
        y1, y2 = _bg_endpoints(region)
        yw = region.y[i1: i2 + 1]
    else:
        bg = backgrounds.compute(region)
        yw = (region.y - bg)[i1: i2 + 1]
    if weight == "poisson":
        w = 1.0 / np.sqrt(np.clip(region.y[i1: i2 + 1], 1.0, None))
    else:
        w = None

    params = build_parameters(region.peaks, only_peak=only_peak)
    _clamp_centers_to_window(params, region.peaks, float(xw[0]), float(xw[-1]))

    def residual(p: Parameters) -> np.ndarray:
        model = np.sum(eval_peaks(p, region.peaks, xw), axis=0)
        if active:
            # background re-derived from the current peak model every iteration
            bgw = backgrounds.shirley_from_peaks(xw, model, 0, xw.size - 1, y1, y2)
            r = yw - (model + bgw)
        else:
            r = yw - model
        return r * w if w is not None else r

    out = minimize(residual, params, method="leastsq", max_nfev=max_nfev)

    stderr: dict[str, float | None] = {}
    for i, peak in enumerate(region.peaks):
        for pname in Peak.PARAM_NAMES:
            full = param_name(i, pname)
            par = out.params[full]
            spec = getattr(peak, pname)
            spec.value = float(par.value)
            stderr[full] = float(par.stderr) if par.stderr is not None else None

    comps = eval_peaks(out.params, region.peaks, region.x)
    if active:
        bg = backgrounds.shirley_from_peaks(region.x, np.sum(comps, axis=0), i1, i2, y1, y2)
    envelope = bg + np.sum(comps, axis=0)
    return FitResult(
        success=bool(out.success),
        message=str(out.message),
        redchi=float(out.redchi) if out.redchi is not None else float("nan"),
        nfev=int(out.nfev),
        background=bg,
        components=comps,
        envelope=envelope,
        residual=region.y - envelope,
        stderr=stderr,
        report="",
    )


def _clamp_centers_to_window(
    params: Parameters, peaks: list[Peak], x_lo: float, x_hi: float
) -> None:
    """Free peak centers may not leave the background window — otherwise the
    optimizer parks ghost peaks on whatever structure sits outside the fit
    range (it costs nothing there)."""
    for i, peak in enumerate(peaks):
        if peak.center.expr:
            continue
        par = params[param_name(i, "center")]
        lo = max(par.min, x_lo)
        hi = min(par.max, x_hi)
        if lo >= hi:  # bounds entirely outside the window -> pull into it
            lo, hi = x_lo, x_hi
        par.min, par.max = lo, hi
        par.value = float(np.clip(par.value, lo, hi))


def fit_background(region: Region) -> str:
    """Fit/settle the background alone, BEFORE any peaks (user workflow step 1).

    TOUGAARD: choose B so the background hugs the data from below across the
    whole window (5th percentile of pointwise ratios — robust to noise).
    SHIRLEY/LINEAR are fully determined by the window endpoints, so there is
    nothing to optimize — adjust the green lines instead (or enable
    'BG 동시 fit' to co-fit an active Shirley with the peaks later).
    """
    bgs = region.background
    i1, i2 = region.crop_indices()
    if bgs.kind == "TOUGAARD":
        raw, y_lo = backgrounds.tougaard_raw(
            region.x, region.y, i1, i2, bgs.tougaard_c, bgs.avg_points)
        yw = region.y[i1: i2 + 1]
        mask = raw > raw.max() * 1e-3 if raw.max() > 0 else np.zeros_like(raw, bool)
        if not mask.any():
            return "Tougaard: 창 안에 적분할 신호가 없습니다 — 범위를 확인하세요"
        ratios = (yw[mask] - y_lo) / raw[mask]
        b = float(max(0.0, np.percentile(ratios, 5.0)))
        bgs.tougaard_b = round(b, 2)
        return f"Tougaard B = {b:.1f}로 맞춤 (데이터 아래에 닿도록) — B 스핀박스로 미세조정 가능"
    if bgs.kind == "SHIRLEY" and bgs.active:
        return "BG 동시 fit이 켜져 있습니다 — Fit Region 때 피크와 함께 최적화됩니다"
    if bgs.kind in ("SHIRLEY", "SHIRLEY_LINEAR", "LINEAR"):
        return ("이 백그라운드는 끝점 데이터로 자동 결정됩니다 — 초록 세로선을 조절하세요. "
                "(Shirley를 피크와 함께 fitting하려면 'BG 동시 fit' 체크)")
    return "NONE 백그라운드는 fitting할 것이 없습니다"


def fit_until_converged(
    region: Region,
    only_peak: int | None = None,
    weight: str = "none",
    max_rounds: int = 8,
    rtol: float = 1e-3,
) -> tuple[FitResult, int]:
    """XPSPEAK-style repeated optimization: keep re-running the fit from the
    previous solution until reduced chi-squared stops improving. With a static
    Shirley each round is identical, but with constraints near bounds or an
    active background, restarts often keep improving for a few rounds."""
    res = fit_region(region, only_peak=only_peak, weight=weight)
    rounds = 1
    prev = res.redchi
    while rounds < max_rounds:
        res = fit_region(region, only_peak=only_peak, weight=weight)
        rounds += 1
        if not np.isfinite(res.redchi) or not np.isfinite(prev):
            break
        if prev <= 0 or abs(prev - res.redchi) / prev < rtol:
            break
        prev = res.redchi
    return res, rounds


def area_fractions(region: Region) -> list[float]:
    """Relative component areas (%) within the background window."""
    if not region.peaks:
        return []
    i1, i2 = region.crop_indices()
    xw = region.x[i1: i2 + 1]
    params = build_parameters(region.peaks)
    comps = eval_peaks(params, region.peaks, xw)
    areas = [max(0.0, float(np.trapezoid(c, xw))) for c in comps]
    total = sum(areas)
    return [100.0 * a / total if total > 0 else 0.0 for a in areas]
