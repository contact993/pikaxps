import numpy as np
import pytest

from xpsfit.core import lineshapes as ls

X = np.arange(270.0, 300.0, 0.02)
CENTER, FWHM = 285.0, 1.4


@pytest.mark.parametrize(
    "shape,asym",
    [("GL_SUM", 0.0), ("GL_PRODUCT", 0.0), ("VOIGT", 0.0), ("GL_TAIL", 0.8), ("DONIACH", 0.1)],
)
def test_unit_area(shape, asym):
    y = ls.evaluate(shape, X, CENTER, 1.0, FWHM, 30.0, asym)
    area = np.trapezoid(y, X)
    assert area == pytest.approx(1.0, abs=0.03)


def test_gl_sum_limits():
    assert np.allclose(ls.gl_sum(X, CENTER, FWHM, 0.0), ls.gaussian(X, CENTER, FWHM))
    assert np.allclose(ls.gl_sum(X, CENTER, FWHM, 100.0), ls.lorentzian(X, CENTER, FWHM))


def test_gaussian_fwhm():
    y = ls.gaussian(X, CENTER, FWHM)
    above = X[y >= y.max() / 2.0]
    assert (above[-1] - above[0]) == pytest.approx(FWHM, abs=0.05)


def test_tail_zero_is_symmetric():
    assert np.allclose(
        ls.gl_tail(X, CENTER, FWHM, 30.0, 0.0), ls.gl_sum(X, CENTER, FWHM, 30.0)
    )


def test_tail_skews_to_high_be():
    y = ls.gl_tail(X, CENTER, FWHM, 30.0, 1.5)
    centroid = np.trapezoid(X * y, X) / np.trapezoid(y, X)
    assert centroid > CENTER + 0.1


def test_doniach_alpha0_matches_lorentzian_shape():
    y1 = ls.doniach_sunjic(X, CENTER, FWHM, 0.0)
    y2 = ls.lorentzian(X, CENTER, FWHM)
    y2 = y2 / np.trapezoid(y2, X)
    assert np.max(np.abs(y1 - y2)) < 0.02 * y2.max()


def test_area_scaling():
    y = ls.evaluate("GL_SUM", X, CENTER, 12345.0, FWHM, 30.0, 0.0)
    assert np.trapezoid(y, X) == pytest.approx(12345.0, rel=0.01)
