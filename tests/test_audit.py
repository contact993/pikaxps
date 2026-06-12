import numpy as np
import pytest

from xpsfit import refdb
from xpsfit.core import audit, fitting, lineshapes
from xpsfit.core.spectrum import BackgroundSpec, Peak, Region


def topics(report, severity=None):
    return [(f.topic, f.severity) for f in report.findings
            if severity is None or f.severity == severity]


def messages(report):
    return " | ".join(f.message for f in report.findings)


def make_pt4f_region(seed=4):
    """Pt 4f doublet data (3.33 eV, 4:3) with realistic noise."""
    rng = np.random.default_rng(seed)
    x = np.arange(66.0, 80.0, 0.05)
    y = np.full_like(x, 800.0)
    y += lineshapes.evaluate("GL_SUM", x, 71.1, 20000.0, 1.0, 30.0, 0.0)
    y += lineshapes.evaluate("GL_SUM", x, 74.43, 15000.0, 1.0, 30.0, 0.0)
    y += rng.normal(0, 15, x.size)
    return Region(name="Pt 4f", x=x, y=y,
                  background=BackgroundSpec(kind="LINEAR", lo=66.3, hi=79.7))


def test_missing_doublet_partner_flagged():
    region = make_pt4f_region()
    region.peaks = [Peak.create(center=71.1, area=20000.0, fwhm=1.0, label="Pt(0)")]
    fitting.fit_region(region)
    report = audit.audit(region)
    msgs = messages(report)
    assert any(t == "Doublet" and s == "bad" for t, s in topics(report))
    assert "74.4" in msgs  # expected partner position mentioned


def test_constrained_doublet_passes():
    region = make_pt4f_region()
    region.peaks = refdb.doublet_pair("Pt", "4f", 71.1, main_index=0, label="Pt(0)",
                                      area=20000.0, fwhm=1.0)
    fitting.fit_region(region)
    report = audit.audit(region)
    assert any(t == "Doublet" and s == "ok" for t, s in topics(report))
    assert not any(t == "Doublet" and s == "bad" for t, s in topics(report))
    # Pt(0) is asymmetric in the DB -> symmetric GL should be warned about
    assert any(t == "라인섀입" and s == "warn" for t, s in topics(report))


def test_freed_doublet_with_wrong_ratio_warned():
    region = make_pt4f_region()
    p0 = Peak.create(center=71.1, area=20000.0, fwhm=1.0, label="Pt(0) 4f7/2")
    p1 = Peak.create(center=74.43, area=20000.0, fwhm=1.0, label="Pt(0) 4f5/2")  # 1:1!
    region.peaks = [p0, p1]
    report = audit.audit(region)
    assert any("면적비" in f.message and f.severity == "warn" for f in report.findings)


def test_unknown_state_and_narrow_fwhm():
    region = make_pt4f_region()
    ghost = Peak.create(center=77.5, area=3000.0, fwhm=0.2, label="ghost")
    main = refdb.doublet_pair("Pt", "4f", 71.1, main_index=1, label="Pt(0)",
                              area=20000.0, fwhm=1.0)
    region.peaks = [ghost] + main
    report = audit.audit(region)
    msgs = messages(report)
    assert any(t == "FWHM" and s == "bad" for t, s in topics(report))  # 0.2 eV
    assert "매칭되지 않습니다" in msgs  # 77.5 eV unknown for Pt 4f


def test_c1s_charge_reference_check():
    rng = np.random.default_rng(2)
    x = np.arange(280.0, 292.0, 0.05)
    y = np.full_like(x, 500.0) + lineshapes.evaluate("GL_SUM", x, 285.4, 15000.0, 1.3, 30.0, 0.0)
    y += rng.normal(0, 12, x.size)
    region = Region(name="C 1s", x=x, y=y,
                    background=BackgroundSpec(kind="LINEAR", lo=280.3, hi=291.7))
    region.peaks = [Peak.create(center=285.4, area=15000.0, fwhm=1.3, label="C-C")]
    fitting.fit_region(region)
    report = audit.audit(region)
    assert any(t == "대전 보정" and s == "warn" for t, s in topics(report))
    assert "BE Shift" in messages(report)


def test_overlapping_peaks_flagged():
    region = make_pt4f_region()
    region.peaks = [Peak.create(center=71.1, area=10000.0, fwhm=1.0, label="A"),
                    Peak.create(center=71.3, area=10000.0, fwhm=1.0, label="B")]
    report = audit.audit(region)
    assert any(t == "과적합" and s == "warn" for t, s in topics(report))


def test_empty_model_info():
    region = make_pt4f_region()
    report = audit.audit(region)
    assert report.findings[0].severity == "info"


def test_necessity_ghost_peak_flagged():
    """A peak whose presence doesn't change the fit ('same before/after') is
    flagged as not required; real peaks read as essential."""
    rng = np.random.default_rng(9)
    x = np.arange(276.0, 296.0, 0.05)
    y = np.full_like(x, 600.0)
    y += lineshapes.evaluate("GL_SUM", x, 284.8, 20000.0, 1.3, 30.0, 0.0)
    y += lineshapes.evaluate("GL_SUM", x, 288.6, 6000.0, 1.4, 30.0, 0.0)
    y += rng.normal(0, 12, x.size)
    region = Region(name="C 1s", x=x, y=y,
                    background=BackgroundSpec(kind="LINEAR", lo=276.3, hi=295.7))
    region.peaks = [
        Peak.create(center=284.8, area=20000.0, fwhm=1.3, label="C-C"),
        Peak.create(center=288.6, area=6000.0, fwhm=1.4, label="O-C=O"),
        Peak.create(center=281.5, area=300.0, fwhm=1.5, label="ghost"),  # nothing there
    ]
    fitting.fit_region(region)
    report = audit.audit(region)
    nec = {f.message.split(":")[0]: f.severity for f in report.findings if f.topic == "필요성"}
    assert nec["C-C"] == "ok"
    assert nec["O-C=O"] == "ok"
    assert nec["ghost"] in ("bad", "warn")
    ghost_msg = next(f.message for f in report.findings
                     if f.topic == "필요성" and f.message.startswith("ghost"))
    assert "ΔBIC" in ghost_msg


def test_necessity_doublet_removed_as_unit():
    region = make_pt4f_region()
    region.peaks = refdb.doublet_pair("Pt", "4f", 71.1, main_index=0, label="Pt(0)",
                                      area=20000.0, fwhm=1.0)
    region.peaks.append(Peak.create(center=77.0, area=200.0, fwhm=1.2, label="extra"))
    fitting.fit_region(region)
    report = audit.audit(region)
    nec = [f for f in report.findings if f.topic == "필요성"]
    # partner not tested separately: only main(pair) + extra
    assert len(nec) == 2
    main_f = next(f for f in nec if f.message.startswith("Pt(0)"))
    assert main_f.severity == "ok" and "doublet 쌍" in main_f.message
