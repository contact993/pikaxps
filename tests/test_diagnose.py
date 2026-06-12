import numpy as np
import pytest

from xpsfit.core import diagnose, fitting, lineshapes
from xpsfit.core.spectrum import BackgroundSpec, Peak, Region


def make_two_peak_data(noise=12.0, seed=8):
    rng = np.random.default_rng(seed)
    x = np.arange(276.0, 296.0, 0.05)
    y = np.full_like(x, 600.0)
    y += lineshapes.evaluate("GL_SUM", x, 284.8, 20000.0, 1.3, 30.0, 0.0)
    y += lineshapes.evaluate("GL_SUM", x, 288.6, 5000.0, 1.4, 30.0, 0.0)
    y += rng.normal(0, noise, x.size)
    return Region(name="C 1s", x=x, y=y,
                  background=BackgroundSpec(kind="LINEAR", lo=276.3, hi=295.7))


def test_missing_peak_is_detected():
    region = make_two_peak_data()
    region.peaks = [Peak.create(center=284.8, area=20000.0, fwhm=1.3, label="C-C")]
    d = diagnose.diagnose(region)
    assert d.z_score > 5.0
    assert d.suspect_be == pytest.approx(288.6, abs=0.4)
    assert d.delta_bic is not None and d.delta_bic < -10.0
    assert "가능성이 높" in d.verdict
    # user's model untouched by the trial fit
    assert len(region.peaks) == 1


def test_adequate_model_reports_no_evidence():
    region = make_two_peak_data()
    region.peaks = [Peak.create(center=284.8, area=20000.0, fwhm=1.3, label="C-C"),
                    Peak.create(center=288.6, area=5000.0, fwhm=1.4, label="O-C=O")]
    fitting.fit_region(region)
    d = diagnose.diagnose(region)
    assert d.z_score < 5.0  # mild bg-endpoint mismatch allowed
    assert d.suspect_be is None  # nothing flagged on the plot
    assert "충분" in d.verdict


def test_no_peaks_guidance():
    region = make_two_peak_data()
    d = diagnose.diagnose(region)
    assert "피크가 없습니다" in d.verdict
