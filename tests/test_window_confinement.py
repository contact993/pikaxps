"""Peaks must stay inside the background window; Fit BG settles Tougaard B."""
import numpy as np
import pytest

from xpsfit.core import backgrounds, fitting, lineshapes
from xpsfit.core.spectrum import BackgroundSpec, Peak, Region


def make_c1s_with_neighbor(seed=11):
    """C 1s peak inside the window + a big foreign peak OUTSIDE it (like K 2p
    invading a wide C 1s scan)."""
    rng = np.random.default_rng(seed)
    x = np.arange(279.0, 298.0, 0.05)
    y = np.full_like(x, 1500.0)
    y += lineshapes.evaluate("GL_SUM", x, 284.8, 20000.0, 1.3, 30.0, 0.0)
    y += lineshapes.evaluate("GL_SUM", x, 295.5, 60000.0, 2.2, 30.0, 0.0)  # intruder
    y += rng.normal(0, 20, x.size)
    return Region(
        name="C 1s", x=x, y=y,
        background=BackgroundSpec(kind="LINEAR", lo=280.0, hi=291.0),
    )


def test_fit_keeps_free_centers_inside_window():
    region = make_c1s_with_neighbor()
    runaway = Peak.create(center=289.0, area=5000.0, fwhm=1.5, label="ghost")
    runaway.center.min, runaway.center.max = 279.0, 298.0  # deliberately wide
    main = Peak.create(center=284.5, area=15000.0, fwhm=1.4, label="C-C")
    region.peaks = [main, runaway]
    fitting.fit_region(region)
    lo, hi = 280.0, 291.0
    for p in region.peaks:
        assert lo - 1e-6 <= p.center.value <= hi + 1e-6, p.label
    assert main.center.value == pytest.approx(284.8, abs=0.05)


def test_fit_pulls_outside_peak_into_window():
    region = make_c1s_with_neighbor()
    outside = Peak.create(center=295.5, area=50000.0, fwhm=2.0, label="escaped")
    outside.center.min, outside.center.max = 294.0, 297.0  # fully outside window
    region.peaks = [outside]
    fitting.fit_region(region)
    assert 280.0 - 1e-6 <= outside.center.value <= 291.0 + 1e-6


def test_fit_background_tougaard_hugs_data():
    rng = np.random.default_rng(5)
    x = np.arange(50.0, 90.0, 0.1)
    peaks = (lineshapes.evaluate("GL_SUM", x, 64.0, 30000.0, 1.2, 30.0, 0.0)
             + lineshapes.evaluate("GL_SUM", x, 67.0, 22000.0, 1.2, 30.0, 0.0))
    bg_true = backgrounds.shirley_from_peaks(x, peaks, 0, x.size - 1, 2000.0, 3200.0)
    y = peaks + bg_true + rng.normal(0, 25, x.size)
    region = Region(name="Ir 4f", x=x, y=y,
                    background=BackgroundSpec(kind="TOUGAARD", lo=50.5, hi=89.5))
    msg = fitting.fit_background(region)
    assert "Tougaard B" in msg
    assert region.background.tougaard_b > 0
    bg = backgrounds.compute(region)
    i1, i2 = region.crop_indices()
    diff = (y - bg)[i1: i2 + 1]
    # hugs from below: barely crosses the data (noise-level tolerance)
    assert np.percentile(diff, 1) > -120.0
    assert diff.max() > 10000.0  # peaks clearly stand above the background


def test_fit_background_messages_for_static_kinds():
    region = make_c1s_with_neighbor()
    region.background.kind = "SHIRLEY"
    assert "끝점" in fitting.fit_background(region)
    region.background.active = True
    assert "동시 fit" in fitting.fit_background(region)
