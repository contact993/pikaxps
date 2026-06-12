"""Comprehensive fit audit: physics + literature + statistics.

A flat residual is NECESSARY but not SUFFICIENT — a fit can match the data
perfectly and still be chemically wrong. This audit checks what an
experienced reviewer would (criteria follow Biesinger 2011 and the
Baer 2019 reporting guidelines):

- FWHM sanity (noise-fitting, blown-up widths, parameters stuck at bounds)
- Binding energies vs the reference DB (is each component a known state?)
- Spin-orbit doublet integrity (partner present? splitting/ratio vs theory)
- Lineshape (metallic states need asymmetry; symmetric GL inflates oxides)
- Expected satellites (Cu(II)/Co(II)/Ni(II)... 'satellite' hints in the DB)
- Overfit signals (near-coincident peaks, <1% components, zero areas)
- Charge reference (C 1s C-C on 284.8)
- Residual statistics (band-passed z-score + trial-peak dBIC) — one item only

Severities: "bad" (must fix) > "warn" (check) > "ok" (passed) > "info".
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import numpy as np

from .. import refdb
from ..refdb import guess_element_orbital
from . import diagnose, fitting
from .spectrum import Peak, Region

SAT_WORDS = ("sat", "shake", "plasmon", "multiplet", "loss", "후보", "위성")
FWHM_MIN, FWHM_MAX = 0.35, 3.0
DB_MATCH_TOL = 0.5  # eV beyond the literature range before we complain


@dataclass
class Finding:
    severity: str  # "bad" | "warn" | "ok" | "info"
    topic: str
    message: str


@dataclass
class AuditReport:
    findings: list[Finding]
    diagnosis: "diagnose.Diagnosis | None" = None

    def counts(self) -> tuple[int, int, int]:
        bad = sum(1 for f in self.findings if f.severity == "bad")
        warn = sum(1 for f in self.findings if f.severity == "warn")
        ok = sum(1 for f in self.findings if f.severity == "ok")
        return bad, warn, ok


def _is_satellite_like(p: Peak) -> bool:
    if getattr(p, "kind", "single") == "satellite":
        return True
    lab = (p.label or "").lower()
    return any(w in lab for w in SAT_WORDS)


def _at_bound(value: float, lo: float, hi: float) -> str | None:
    span = max(hi - lo, 1e-9)
    if np.isfinite(lo) and abs(value - lo) < 0.02 * span:
        return "하한"
    if np.isfinite(hi) and abs(value - hi) < 0.02 * span:
        return "상한"
    return None


def _label(p: Peak, i: int) -> str:
    return p.label or f"Peak {i + 1}"


def audit(region: Region) -> AuditReport:
    if not region.peaks:
        return AuditReport([Finding("info", "모델",
                                    "피크가 없습니다 — 모델을 만들고 fitting한 뒤 진단하세요.")])

    out: list[Finding] = []
    peaks = region.peaks
    i1, i2 = region.crop_indices()
    wlo, whi = float(region.x[i1]), float(region.x[i2])
    fractions = fitting.area_fractions(region)
    hit = guess_element_orbital(region.name)
    orb_info = refdb.elements()[hit[0]][hit[1]] if hit else None

    # ---------- per-peak: FWHM / bounds / area ----------
    for i, p in enumerate(peaks):
        name = _label(p, i)
        f = p.fwhm.value
        if f < FWHM_MIN:
            out.append(Finding("bad", "FWHM",
                f"{name}: FWHM {f:.2f} eV — 비물리적으로 좁습니다. 노이즈 스파이크를 피팅했을 가능성 (제거 권장)."))
        elif f > FWHM_MAX and not _is_satellite_like(p):
            out.append(Finding("warn", "FWHM",
                f"{name}: FWHM {f:.2f} eV — 단일 화학종으로 보기엔 넓습니다. "
                f"여러 상태의 합이거나 satellite/multiplet라면 라벨에 표기하세요."))
        if p.area.value <= 0.0 or (i < len(fractions) and fractions[i] < 0.01):
            out.append(Finding("bad", "면적",
                f"{name}: 면적이 0입니다 — 기여 없는 성분. 제거하거나 초기값을 바꿔 다시 fitting하세요."))
        elif i < len(fractions) and fractions[i] < 1.0:
            out.append(Finding("warn", "면적",
                f"{name}: 기여 {fractions[i]:.1f}% — 1% 미만. 화학적 근거가 없으면 과적합일 수 있습니다."))
        if p.center.expr is None:
            b = _at_bound(p.center.value, p.center.min, p.center.max)
            if b:
                out.append(Finding("warn", "경계",
                    f"{name}: center {p.center.value:.2f} eV가 허용 범위 {b}에 붙었습니다 — "
                    f"최적값이 범위 밖일 수 있으니 범위를 넓히거나 모델을 재검토하세요."))
        if p.fwhm.expr is None and p.fwhm.vary:
            b = _at_bound(p.fwhm.value, p.fwhm.min, p.fwhm.max)
            if b:
                out.append(Finding("warn", "경계",
                    f"{name}: FWHM이 허용 범위 {b}({p.fwhm.value:.2f} eV)에 붙었습니다."))

    # ---------- overlap (overfit) ----------
    free_idx = [i for i, p in enumerate(peaks) if p.center.expr is None]
    for a in range(len(free_idx)):
        for b in range(a + 1, len(free_idx)):
            i, j = free_idx[a], free_idx[b]
            dc = abs(peaks[i].center.value - peaks[j].center.value)
            if dc < 0.4:
                out.append(Finding("warn", "과적합",
                    f"{_label(peaks[i], i)} ↔ {_label(peaks[j], j)} 간격이 {dc:.2f} eV — "
                    f"사실상 같은 성분일 수 있습니다. 하나로 합치는 것을 검토하세요."))

    # ---------- reference DB ----------
    if orb_info is None:
        out.append(Finding("info", "레퍼런스",
            "Region 이름에서 원소/오비탈을 인식하지 못해 문헌 대조를 건너뜁니다 — "
            "이름을 'Ni 2p'처럼 지으면 DB 검사가 활성화됩니다."))
    else:
        el, orb = hit
        states = orb_info["states"]
        for i, p in enumerate(peaks):
            if _is_satellite_like(p) or p.center.expr is not None:
                continue
            c = p.center.value
            best, best_d = None, float("inf")
            for st in states:
                lo, hi_ = st.get("range", [st["be_eV"] - 0.3, st["be_eV"] + 0.3])
                d = 0.0 if lo <= c <= hi_ else min(abs(c - lo), abs(c - hi_))
                if d < best_d:
                    best, best_d = st, d
            if best_d == 0.0:
                msg = f"{_label(p, i)} ({c:.2f} eV) ↔ {best['state']} 문헌 범위와 일치"
                if best.get("lineshape_hint"):
                    msg += f" · 권장 라인섀입: {best['lineshape_hint']}"
                out.append(Finding("ok", "레퍼런스", msg))
                hint = (best.get("lineshape_hint") or "").lower()
                if "asym" in hint and p.shape in ("GL_SUM", "GL_PRODUCT", "VOIGT") and p.asym.value == 0.0:
                    out.append(Finding("warn", "라인섀입",
                        f"{_label(p, i)}: '{best['state']}'는 비대칭 피크입니다 — 대칭 GL로 두면 "
                        f"고BE 꼬리가 다른 성분(산화물)으로 흡수돼 과대평가됩니다. GL_TAIL 또는 DONIACH로 바꾸세요."))
                if "satellite" in hint:
                    m = re.search(r"satellite\s*~?(\d+\.?\d*)", hint)
                    sat_be = float(m.group(1)) if m else c + 6.0
                    if wlo <= sat_be <= whi:
                        has_sat = any(_is_satellite_like(q) or abs(q.center.value - sat_be) < 1.5
                                      for q in peaks if q is not p)
                        if not has_sat:
                            out.append(Finding("warn", "Satellite",
                                f"'{best['state']}'는 ~{sat_be:.0f} eV에 satellite를 동반합니다 — "
                                f"satellite 피크 없이 fitting하면 그 면적이 다른 성분으로 샙니다."))
            elif best_d <= DB_MATCH_TOL:
                out.append(Finding("ok", "레퍼런스",
                    f"{_label(p, i)} ({c:.2f} eV) ≈ {best['state']} (문헌 범위에서 {best_d:.2f} eV)"))
            else:
                out.append(Finding("warn", "레퍼런스",
                    f"{_label(p, i)} ({c:.2f} eV): {el} {orb}의 알려진 상태와 매칭되지 않습니다 "
                    f"(가장 가까운: {best['state']} {best['be_eV']:.1f} eV, {best_d:.1f} eV 차이). "
                    f"대전 보정, 다른 원소 간섭, satellite 여부를 확인하세요."))

        # ---------- doublet integrity ----------
        split = orb_info.get("spin_orbit_splitting_eV")
        ratio = orb_info.get("doublet_area_ratio")
        if split and split > 0.3:
            factor = refdb.ratio_factor(ratio)
            tied = sum(1 for p in peaks if p.center.expr and "center" in p.center.expr)
            if tied:
                out.append(Finding("ok", "Doublet",
                    f"{tied}개 피크가 constraint로 짝지어져 있습니다 (간격 {split} eV · 면적비 {ratio} 고정 유지)."))
            for i, p in enumerate(peaks):
                if _is_satellite_like(p) or p.center.expr is not None:
                    continue
                if i < len(fractions) and fractions[i] < 10.0:
                    continue  # minor components: don't demand partners
                expected = p.center.value + split
                partner = None
                for j, q in enumerate(peaks):
                    if q is p:
                        continue
                    if abs(q.center.value - expected) < max(0.35, 0.15 * split):
                        partner = (j, q)
                        break
                if partner is None:
                    if expected <= whi:
                        out.append(Finding("bad", "Doublet",
                            f"{_label(p, i)} ({p.center.value:.2f} eV): {orb} doublet 짝이 없습니다 — "
                            f"{expected:.2f} eV 부근에 {orb[-1]}짝({ratio})이 있어야 합니다. "
                            f"자유 피크를 지우고 피크 테이블의 '＋ Doublet'으로 다시 추가하세요."))
                    else:
                        out.append(Finding("info", "Doublet",
                            f"{_label(p, i)}: doublet 짝({expected:.1f} eV)이 창 밖 — 주성분만 fitting하는 관례면 OK."))
                elif partner[1].area.expr is None:
                    j, q = partner
                    r = q.area.value / max(p.area.value, 1e-9)
                    dev = abs(r - factor) / factor
                    dsplit = abs(q.center.value - p.center.value - split)
                    if dev > 0.25:
                        out.append(Finding("warn", "Doublet",
                            f"{_label(p, i)}/{_label(q, j)}: 면적비 {r:.2f} — 이론 {factor:.2f}({ratio})에서 "
                            f"{dev * 100:.0f}% 벗어났습니다. 물리적 근거(Coster-Kronig 등)가 없으면 비율을 고정하세요."))
                    if dsplit > 0.2:
                        out.append(Finding("warn", "Doublet",
                            f"{_label(p, i)}/{_label(q, j)}: 간격 {q.center.value - p.center.value:.2f} eV — "
                            f"이론 {split} eV에서 {dsplit:.2f} eV 벗어남."))

        # ---------- charge reference (C 1s region) ----------
        if el == "C" and orb == "1s":
            cands = [p for p in peaks if 283.8 <= p.center.value <= 286.2 and not _is_satellite_like(p)]
            if cands:
                main = max(cands, key=lambda p: p.area.value)
                dev = main.center.value - 284.8
                if abs(dev) > 0.25:
                    out.append(Finding("warn", "대전 보정",
                        f"C-C 피크가 {main.center.value:.2f} eV — 기준 284.8에서 {dev:+.2f} eV. "
                        f"Regions 패널의 BE Shift로 전체 보정을 하세요 (C-C→284.8 버튼)."))
                else:
                    out.append(Finding("ok", "대전 보정", f"C-C {main.center.value:.2f} eV — 284.8 기준 OK."))

    # ---------- residual statistics (one item) ----------
    d = diagnose.diagnose(region)
    sev = "ok" if "충분" in d.verdict else ("bad" if "가능성이 높" in d.verdict else "warn")
    out.append(Finding(sev, "잔차 통계", f"{d.verdict} — {d.detail.splitlines()[0]}"))

    return AuditReport(out, d)
