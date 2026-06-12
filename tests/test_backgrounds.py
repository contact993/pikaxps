import numpy as np

from xpsfit.core import backgrounds
from xpsfit.core.spectrum import BackgroundSpec, Region


def _gauss(x, c, a, f):
    s = f / 2.3548200450309493
    return a * np.exp(-0.5 * ((x - c) / s) ** 2) / (s * np.sqrt(2 * np.pi))


def make_shirley_consistent(x, peak, y1, y2):
    """Build y = peak + B where B is the exact Shirley background of `peak`."""
    seg = 0.5 * (peak[1:] + peak[:-1]) * np.diff(x)
    cum = np.concatenate(([0.0], np.cumsum(seg)))
    b = y1 + (y2 - y1) * cum / cum[-1]
    return peak + b, b


def test_shirley_recovers_true_background():
    x = np.arange(850.0, 870.0, 0.05)
    peak = _gauss(x, 858.0, 5000.0, 1.6)
    y, b_true = make_shirley_consistent(x, peak, 100.0, 600.0)
    b = backgrounds.shirley(x, y, 0, x.size - 1, avg=1)
    assert np.max(np.abs(b - b_true)) < 1.0  # counts, vs step of 500


def test_shirley_endpoints_and_direction():
    x = np.arange(0.0, 20.0, 0.05)
    y = _gauss(x, 10.0, 1000.0, 1.5) + np.linspace(50, 250, x.size)
    b = backgrounds.shirley(x, y, 0, x.size - 1, avg=1)
    assert abs(b[0] - y[0]) < 1e-6
    assert abs(b[-1] - y[-1]) < 1e-6
    assert np.all(np.diff(b) >= -1e-9)  # rises toward high BE


def test_linear_endpoints():
    x = np.linspace(0, 10, 101)
    y = 2.0 * x + 5.0
    b = backgrounds.linear(x, y, 0, 100, avg=1)
    assert np.allclose(b, y)


def test_shirley_linear_zero_slope_is_shirley():
    x = np.arange(0.0, 20.0, 0.1)
    y = _gauss(x, 10.0, 1000.0, 1.5) + 100.0
    b1 = backgrounds.shirley(x, y, 0, x.size - 1)
    b2 = backgrounds.shirley_linear(x, y, 0, x.size - 1, slope=0.0)
    assert np.allclose(b1, b2)


def test_tougaard_autoscale_meets_high_be_endpoint():
    x = np.arange(850.0, 880.0, 0.1)
    y = _gauss(x, 860.0, 8000.0, 2.0) + 50.0
    # add a synthetic loss tail so the high-BE side sits above baseline
    y += 30.0 / (1.0 + np.exp(-(x - 862.0)))
    b = backgrounds.tougaard(x, y, 0, x.size - 1, b=0.0)
    assert abs(b[-1] - y[-1]) < 5.0
    assert np.all(np.diff(b) >= -1e-9)


def test_compute_dispatch():
    x = np.arange(0.0, 10.0, 0.1)
    y = _gauss(x, 5.0, 100.0, 1.0) + 10.0
    for kind in ("NONE", "LINEAR", "SHIRLEY", "SHIRLEY_LINEAR", "TOUGAARD"):
        r = Region(name="t", x=x, y=y, background=BackgroundSpec(kind=kind))
        b = backgrounds.compute(r)
        assert b.shape == y.shape
        assert np.all(np.isfinite(b))
