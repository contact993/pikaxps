import numpy as np
import pytest

from xpsfit.core import backgrounds, fitting, lineshapes
from xpsfit.core.spectrum import BackgroundSpec, Peak, Region


def make_region(active=True, noise=15.0, seed=3):
    """Data built as peaks + EXACT Shirley-of-peaks: the self-consistent case
    the active background should nail."""
    rng = np.random.default_rng(seed)
    x = np.arange(276.0, 296.0, 0.05)
    peaks = (lineshapes.evaluate("GL_SUM", x, 284.8, 20000.0, 1.3, 30.0, 0.0)
             + lineshapes.evaluate("GL_SUM", x, 286.4, 6000.0, 1.3, 30.0, 0.0))
    bg = backgrounds.shirley_from_peaks(x, peaks, 0, x.size - 1, 800.0, 1400.0)
    y = peaks + bg + rng.normal(0, noise, x.size)
    return Region(
        name="C 1s", x=x, y=y,
        background=BackgroundSpec(kind="SHIRLEY", lo=276.3, hi=295.7, active=active),
    )


def test_active_shirley_recovers_parameters():
    region = make_region(active=True)
    p0 = Peak.create(center=284.6, area=15000.0, fwhm=1.5, label="C-C")
    p1 = Peak.create(center=286.2, area=4000.0, fwhm=1.5, label="C-O")
    p1.fwhm.expr = "p0_fwhm"
    region.peaks = [p0, p1]
    res, rounds = fitting.fit_until_converged(region)
    assert res.success
    assert rounds >= 1
    assert p0.center.value == pytest.approx(284.8, abs=0.03)
    assert p0.area.value == pytest.approx(20000.0, rel=0.04)
    assert p1.area.value == pytest.approx(6000.0, rel=0.08)


def test_active_bg_serialization_roundtrip():
    spec = BackgroundSpec(kind="SHIRLEY", active=True)
    d = spec.to_dict()
    assert d["active"] is True
    spec2 = BackgroundSpec.from_dict(d)
    assert spec2.active is True


def test_eval_model_active_matches_static_when_disabled():
    region = make_region(active=False)
    region.peaks = [Peak.create(center=284.8, area=20000.0, fwhm=1.3)]
    res_static = fitting.eval_model(region)
    region.background.active = True
    res_active = fitting.eval_model(region)
    # both follow the data step; active one is derived from the model
    assert res_static.background.shape == res_active.background.shape
    assert abs(res_active.background[0] - res_static.background[0]) < 60.0


def test_fit_until_converged_rounds():
    region = make_region(active=True)
    region.peaks = [Peak.create(center=284.5, area=10000.0, fwhm=1.6)]
    res, rounds = fitting.fit_until_converged(region, max_rounds=6)
    assert 1 <= rounds <= 6
    assert np.isfinite(res.redchi)
