import numpy as np
import pytest

from xpsfit.core import fitting, lineshapes
from xpsfit.core.spectrum import BackgroundSpec, Peak, Region


def make_doublet_region(noise=20.0, seed=42):
    """Synthetic Fe 2p-like doublet: 2:1 area ratio, 13.1 eV splitting, linear bg.
    Window edges sit ~17 eV from the peaks so Lorentzian tails don't bias the
    endpoint background estimate."""
    rng = np.random.default_rng(seed)
    x = np.arange(690.0, 740.0, 0.05)
    y = lineshapes.evaluate("GL_SUM", x, 707.0, 30000.0, 1.8, 30.0, 0.0)
    y += lineshapes.evaluate("GL_SUM", x, 720.1, 15000.0, 1.8, 30.0, 0.0)
    y += np.linspace(500.0, 800.0, x.size)
    y += rng.normal(0.0, noise, x.size)
    return Region(
        name="Fe 2p", x=x, y=y,
        background=BackgroundSpec(kind="LINEAR", lo=690.5, hi=739.5, avg_points=5),
    )


def test_golden_fit_recovers_parameters():
    region = make_doublet_region()
    region.peaks = [
        Peak.create(center=706.6, area=20000.0, fwhm=1.5, label="Fe 2p3/2"),
        Peak.create(center=719.6, area=10000.0, fwhm=1.5, label="Fe 2p1/2"),
    ]
    res = fitting.fit_region(region)
    assert res.success
    assert region.peaks[0].center.value == pytest.approx(707.0, abs=0.03)
    assert region.peaks[1].center.value == pytest.approx(720.1, abs=0.03)
    assert region.peaks[0].area.value == pytest.approx(30000.0, rel=0.03)
    assert region.peaks[1].area.value == pytest.approx(15000.0, rel=0.03)
    assert region.peaks[0].fwhm.value == pytest.approx(1.8, abs=0.06)


def test_doublet_constraints_hold_exactly():
    region = make_doublet_region()
    p0 = Peak.create(center=706.8, area=20000.0, fwhm=1.6, label="3/2")
    p1 = Peak.create(center=719.9, area=10000.0, fwhm=1.6, label="1/2")
    p1.center.expr = "p0_center + 13.1"
    p1.area.expr = "p0_area * 0.5"
    p1.fwhm.expr = "p0_fwhm"
    region.peaks = [p0, p1]
    res = fitting.fit_region(region)
    assert res.success
    assert p1.center.value == pytest.approx(p0.center.value + 13.1, abs=1e-9)
    assert p1.area.value == pytest.approx(p0.area.value * 0.5, rel=1e-9)
    assert p1.fwhm.value == pytest.approx(p0.fwhm.value, rel=1e-9)


def test_optimise_single_peak_freezes_others():
    region = make_doublet_region()
    region.peaks = [
        Peak.create(center=706.5, area=20000.0, fwhm=1.6),
        Peak.create(center=719.5, area=10000.0, fwhm=1.6),
    ]
    before = (region.peaks[1].center.value, region.peaks[1].area.value)
    fitting.fit_region(region, only_peak=0)
    after = (region.peaks[1].center.value, region.peaks[1].area.value)
    assert before == after


def test_eval_model_shapes():
    region = make_doublet_region()
    region.peaks = [Peak.create(center=707.0, area=30000.0, fwhm=1.8)]
    res = fitting.eval_model(region)
    assert res.envelope.shape == region.x.shape
    assert len(res.components) == 1


def test_area_fractions_sum_to_100():
    region = make_doublet_region()
    region.peaks = [
        Peak.create(center=707.0, area=30000.0, fwhm=1.8),
        Peak.create(center=720.1, area=15000.0, fwhm=1.8),
    ]
    fr = fitting.area_fractions(region)
    assert sum(fr) == pytest.approx(100.0, abs=1e-6)
    assert fr[0] == pytest.approx(66.67, abs=1.0)
