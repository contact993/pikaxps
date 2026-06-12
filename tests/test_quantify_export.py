import numpy as np
import pytest

from xpsfit import refdb
from xpsfit.core import batch, lineshapes, quantify
from xpsfit.core.spectrum import BackgroundSpec, Peak, Region
from xpsfit.io import export


def make_s2p_region(scale=1.0, name="S 2p"):
    x = np.arange(158.0, 174.0, 0.05)
    y = np.zeros_like(x) + 200.0
    for c, a in ((161.8, 6000.0 * scale), (162.98, 3000.0 * scale),
                 (168.8, 2000.0 * scale), (169.98, 1000.0 * scale)):
        y += lineshapes.evaluate("GL_SUM", x, c, a, 1.0, 30.0, 0.0)
    region = Region(name=name, x=x, y=y,
                    background=BackgroundSpec(kind="LINEAR", lo=158.2, hi=173.8))
    recipe = next(r for r in refdb.load_recipes() if r["id"] == "s2p_sulfide_sulfate")
    region.peaks = refdb.recipe_peaks(recipe, area_unit=4000.0 * scale)
    return region


def test_species_areas_merge_doublets():
    region = make_s2p_region()
    from xpsfit.core import fitting
    fitting.fit_region(region)
    sp = quantify.species_areas(region)
    assert len(sp) == 2  # 4 peaks -> 2 species
    sulfide = dict(sp)["sulfide S2- 2p3/2"]
    assert sulfide == pytest.approx(9000.0, rel=0.05)  # 6000 + 3000


def test_atomic_percent():
    entries = [
        quantify.QuantEntry("C 1s", "C", area=1000.0, rsf=1.0),
        quantify.QuantEntry("O 1s", "O", area=2930.0, rsf=2.93),
    ]
    pct = quantify.atomic_percent(entries)
    assert pct[0] == pytest.approx(50.0, abs=0.01)


def test_export_csv_xlsx_figure(tmp_path):
    region = make_s2p_region()
    from xpsfit.core import fitting
    fitting.fit_region(region)
    p1 = export.export_params_csv(region, tmp_path / "params")
    p2 = export.export_curves_csv(region, tmp_path / "curves")
    p3 = export.export_excel([region], tmp_path / "all")
    f1 = export.save_figure(region, tmp_path / "fig.png")
    f2 = export.save_figure(region, tmp_path / "fig.svg")
    for p in (p1, p2, p3, f1, f2):
        assert p.exists() and p.stat().st_size > 0
    df = export.params_dataframe(region)
    assert "Area %" in df.columns and len(df) == 4
    assert df["Area %"].sum() == pytest.approx(100.0, abs=0.1)


def test_batch_fit():
    template = make_s2p_region()
    from xpsfit.core import fitting
    fitting.fit_region(template)
    targets = [make_s2p_region(scale=0.5, name="after-1h"),
               make_s2p_region(scale=0.25, name="after-2h")]
    for t in targets:
        t.peaks = []  # raw data only; model comes from template
    items, df = batch.run_batch(template, targets)
    assert all(i.success for i in items)
    assert len(df) == 2
    a1 = df.iloc[0].filter(like="sulfide").filter(like="area").iloc[0]
    a2 = df.iloc[1].filter(like="sulfide").filter(like="area").iloc[0]
    assert a1 == pytest.approx(4500.0, rel=0.1)
    assert a2 == pytest.approx(2250.0, rel=0.1)
