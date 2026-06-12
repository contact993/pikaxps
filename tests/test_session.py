import numpy as np

from xpsfit.core.session import Session
from xpsfit.core.spectrum import BackgroundSpec, Peak, Region


def test_session_round_trip(tmp_path):
    x = np.arange(280.0, 295.0, 0.1)
    y = np.exp(-((x - 285.0) ** 2)) * 1000.0 + 50.0
    p = Peak.create(center=285.0, area=900.0, fwhm=1.2, label="C-C")
    p2 = Peak.create(center=286.5, area=300.0, fwhm=1.2, label="C-O")
    p2.fwhm.expr = "p0_fwhm"
    region = Region(
        name="C 1s", x=x, y=y,
        background=BackgroundSpec(kind="SHIRLEY", lo=281.0, hi=294.0),
        peaks=[p, p2],
        source_file="sample.dat",
    )
    s = Session(regions=[region], notes="test note")
    path = s.save(tmp_path / "proj")
    assert path.suffix == ".xfp"

    s2 = Session.load(path)
    r2 = s2.regions[0]
    assert s2.notes == "test note"
    assert r2.name == "C 1s"
    assert np.allclose(r2.x, region.x)
    assert np.allclose(r2.y, region.y)
    assert r2.background.kind == "SHIRLEY"
    assert r2.background.lo == 281.0
    assert r2.peaks[1].fwhm.expr == "p0_fwhm"
    assert r2.peaks[0].label == "C-C"
    assert r2.peaks[0].center.value == 285.0


def test_charge_shift_moves_everything():
    x = np.arange(280.0, 295.0, 0.1)
    y = np.ones_like(x)
    p = Peak.create(center=285.0)
    region = Region(name="C 1s", x=x, y=y,
                    background=BackgroundSpec(kind="SHIRLEY", lo=281.0, hi=294.0), peaks=[p])
    region.shift_be(0.6)
    assert region.x[0] == 280.6
    assert region.background.lo == 281.6
    assert p.center.value == 285.6
    assert region.be_shift == 0.6
