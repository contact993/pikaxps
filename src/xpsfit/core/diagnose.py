"""Model adequacy diagnosis: is there statistical evidence for one more peak?

Method (standard model-selection practice):
1. Fit the current model; take the residual inside the background window.
2. Estimate the noise level robustly (MAD of first differences — immune to
   leftover structure).
3. Smooth the residual with a peak-width kernel; the largest |smoothed|
   feature, in units of its noise sigma, is the z-score of unexplained
   structure. z < 3 -> residual is noise -> the model is adequate.
4. If a positive feature stands out, trial-fit with one extra peak there and
   compare BIC. dBIC < -10 is the conventional "strong evidence" threshold.
   A negative feature means the model OVERSHOOTS the data -> too many
   components or wrong lineshape/background, not a missing peak.

Everything runs on a deep copy — the user's model is never touched.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass

import numpy as np

from . import fitting
from .spectrum import Peak, Region


@dataclass
class Diagnosis:
    verdict: str
    detail: str
    z_score: float
    suspect_be: float | None = None
    negative_structure: bool = False
    delta_bic: float | None = None
    redchi_before: float = float("nan")
    redchi_after: float | None = None


def _nvarys(peaks: list[Peak]) -> int:
    params = fitting.build_parameters(peaks)
    return sum(1 for p in params.values() if p.vary)


def _bic(ssr: float, n: int, k: int) -> float:
    return n * float(np.log(max(ssr, 1e-12) / n)) + k * float(np.log(n))


def diagnose(region: Region) -> Diagnosis:
    if not region.peaks:
        return Diagnosis("피크가 없습니다", "먼저 모델을 만들고 fitting한 뒤 진단하세요.", 0.0)

    work = copy.deepcopy(region)
    res = fitting.fit_region(work)
    i1, i2 = work.crop_indices()
    x = work.x[i1: i2 + 1]
    r = res.residual[i1: i2 + 1]
    n = r.size
    if n < 20:
        return Diagnosis("데이터가 너무 적습니다", "진단에는 창 안에 20점 이상이 필요합니다.", 0.0)

    # robust noise: MAD of first differences (insensitive to leftover structure)
    sigma = 1.4826 * float(np.median(np.abs(np.diff(r)))) / np.sqrt(2.0)
    sigma = max(sigma, 1e-9)

    dx = float(np.median(np.diff(x)))
    fwhm = float(np.mean([p.fwhm.value for p in work.peaks])) or 1.0

    def kern(width_ev: float) -> np.ndarray:
        mm = max(3, int(round(width_ev / max(dx, 1e-6))))
        tt = np.arange(-mm, mm + 1) * dx
        ww = np.exp(-4.0 * np.log(2.0) * (tt / width_ev) ** 2)
        return ww / ww.sum()

    # band-pass: peak-width features pass, broad baseline drifts (background
    # endpoint noise) are removed — a missing PEAK is localized, an endpoint
    # offset is a tilt and must not trigger the alarm
    w_narrow = kern(fwhm)
    # wide kernel shrinks with the window so the band-pass always engages
    wide_ev = min(4.0 * fwhm, max(2.0 * fwhm, n * dx / 6.0))
    w_wide = kern(wide_ev)
    if w_wide.size >= n // 2 or wide_ev <= 1.5 * fwhm:
        k_eff = w_narrow  # window genuinely too small for band-pass
    else:
        pad_l = (w_wide.size - w_narrow.size) // 2
        pad_r = w_wide.size - w_narrow.size - pad_l
        k_eff = np.pad(w_narrow, (pad_l, pad_r)) - w_wide
    trim = k_eff.size // 2
    sm = np.convolve(r, k_eff, mode="same")
    sigma_sm = sigma * float(np.sqrt(np.sum(k_eff**2)))

    core = slice(trim, n - trim) if n > 2 * trim + 5 else slice(0, n)
    rel = int(np.argmax(np.abs(sm[core])))
    idx = rel + (core.start or 0)
    z = float(abs(sm[idx]) / sigma_sm)
    be = float(x[idx])
    positive = sm[idx] > 0

    ssr0 = float(np.sum(r * r))
    bic0 = _bic(ssr0, n, _nvarys(work.peaks))

    if z < 3.0:
        return Diagnosis(
            "현재 모델로 충분합니다 ✓",
            f"잔차의 가장 큰 구조가 z = {z:.1f}σ (< 3σ)로 노이즈 수준입니다.\n"
            "성분을 더 추가할 통계적 근거가 없습니다 — 피크를 늘리면 χ²는 줄지만 의미는 없습니다.",
            z, None, False, None, res.redchi, None)

    if not positive:
        if z < 5.0:
            # mild negative structure: usually background-endpoint/tail mismatch,
            # not worth alarming over (look-elsewhere effect on smoothed fields)
            return Diagnosis(
                "대체로 충분합니다 ✓",
                f"빠진 피크 신호는 없습니다. {be:.2f} eV 부근에 모델이 데이터를 약간 넘는\n"
                f"경미한 구조(z = {z:.1f}σ)가 있지만, 보통 배경 끝점/피크 꼬리의 미세 불일치로\n"
                "성분 추가·삭제 근거는 아닙니다.",
                z, None, True, None, res.redchi, None)
        return Diagnosis(
            "모델이 데이터를 초과합니다 ⚠",
            f"{be:.2f} eV 부근에서 모델이 데이터보다 뚜렷이 큽니다 (z = {z:.1f}σ).\n"
            "이건 빠진 피크가 아니라 성분 과잉 또는 라인섀입/배경 불일치 신호입니다 —\n"
            "성분을 줄이거나, 금속 피크라면 비대칭(GL_TAIL/DONIACH)으로, 배경 범위를 점검하세요.",
            z, be, True, None, res.redchi, None)

    # trial: one extra peak at the suspect position
    trial = copy.deepcopy(work)
    area0 = max(float(sm[idx]) * fwhm * 1.06, sigma * fwhm)
    extra = Peak.create(center=be, area=area0, fwhm=fwhm, label="(진단) 후보")
    extra.center.min, extra.center.max = be - 1.0, be + 1.0
    trial.peaks.append(extra)
    res1 = fitting.fit_region(trial)
    r1 = res1.residual[i1: i2 + 1]
    bic1 = _bic(float(np.sum(r1 * r1)), n, _nvarys(trial.peaks))
    dbic = bic1 - bic0

    if dbic < -10.0:
        return Diagnosis(
            f"{be:.2f} eV 부근에 성분이 더 있을 가능성이 높습니다",
            f"미설명 구조 z = {z:.1f}σ. 그 자리에 피크를 추가해 시험 fitting한 결과\n"
            f"ΔBIC = {dbic:.0f} (−10보다 작음 = 강한 통계적 근거), "
            f"red.χ² {res.redchi:.3g} → {res1.redchi:.3g}.\n\n"
            "⚠ 통계는 필요조건일 뿐입니다 — Reference DB에서 그 BE에 올 수 있는\n"
            "화학종(satellite 포함)이 있는지 확인한 뒤 추가하세요.",
            z, be, False, dbic, res.redchi, res1.redchi)
    if dbic < 0.0:
        return Diagnosis(
            f"{be:.2f} eV 신호는 애매합니다",
            f"z = {z:.1f}σ 구조가 있으나 피크 추가의 개선이 약합니다 (ΔBIC = {dbic:.0f}).\n"
            "화학적 근거(DB의 알려진 상태/satellite)가 분명할 때만 추가하세요.",
            z, be, False, dbic, res.redchi, res1.redchi)
    return Diagnosis(
        "성분 추가가 정당화되지 않습니다",
        f"{be:.2f} eV에 z = {z:.1f}σ 구조가 있지만 피크를 추가해도 BIC가 오히려 나빠집니다\n"
        f"(ΔBIC = {dbic:+.0f}). 피크 수 문제가 아니라 라인섀입(비대칭 여부)이나 배경 설정을 점검하세요.",
        z, be, False, dbic, res.redchi, res1.redchi)
