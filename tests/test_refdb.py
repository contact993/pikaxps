import numpy as np
import pytest

from xpsfit import refdb
from xpsfit.core import fitting, lineshapes
from xpsfit.core.spectrum import BackgroundSpec, Peak, Region


def test_db_loads_and_refs_resolve():
    db = refdb.load_db()
    refs = db["references"]
    assert "Ni" in db["elements"]
    for el, orbitals in db["elements"].items():
        for orb, info in orbitals.items():
            assert "states" in info, (el, orb)
            assert "rsf" in info, (el, orb)
            for st in info["states"]:
                assert st["ref"] in refs, (el, orb, st["state"])
                assert 0 < st["be_eV"] < 1500


def test_recipes_load_and_elements_exist():
    db = refdb.load_db()["elements"]
    for r in refdb.load_recipes():
        assert r["element"] in db, r["id"]
        assert r["orbital"] in db[r["element"]], r["id"]


def test_doublet_pair_constraints():
    pair = refdb.doublet_pair("S", "2p", center=161.8, main_index=0, area=2000.0, fwhm=1.0)
    main, partner = pair
    assert partner.center.expr == "p0_center + 1.18"
    assert partner.area.expr == "p0_area * 0.5"
    assert partner.fwhm.expr == "p0_fwhm"
    assert "2p3/2" in main.label and "2p1/2" in partner.label


def test_doublet_ratio_4f():
    pair = refdb.doublet_pair("Pt", "4f", center=71.1, main_index=3)
    assert pair[1].area.expr == "p3_area * 0.75"
    assert pair[1].center.expr == "p3_center + 3.33"


def test_recipe_simple_with_offset():
    recipe = next(r for r in refdb.load_recipes() if r["id"] == "c1s_adventitious")
    peaks = refdb.recipe_peaks(recipe, index_offset=5)
    assert len(peaks) == 4
    assert peaks[0].fwhm.expr is None
    assert peaks[1].fwhm.expr == "p5_fwhm"
    assert peaks[3].fwhm.expr == "p5_fwhm"


def test_recipe_doublet_expansion_indices():
    recipe = next(r for r in refdb.load_recipes() if r["id"] == "mo3d_oxides")
    peaks = refdb.recipe_peaks(recipe)
    assert len(peaks) == 6  # 3 species x doublet
    # partner of species 2 (peaks[3]) references its own main (index 2)
    assert peaks[3].center.expr == "p2_center + 3.15"
    assert peaks[3].area.expr.startswith("p2_area * 0.666")
    # species 2 main links fwhm to anchor (index 0)
    assert peaks[2].fwhm.expr == "p0_fwhm"


def test_recipe_fit_end_to_end():
    """A doublet recipe must produce a fittable model whose constraints hold."""
    rng = np.random.default_rng(1)
    x = np.arange(158.0, 174.0, 0.05)
    y = np.zeros_like(x) + 200.0
    for c, a in ((161.8, 6000.0), (162.98, 3000.0), (168.8, 2000.0), (169.98, 1000.0)):
        y += lineshapes.evaluate("GL_SUM", x, c, a, 1.0, 30.0, 0.0)
    y += rng.normal(0, 10, x.size)
    region = Region(name="S 2p", x=x, y=y,
                    background=BackgroundSpec(kind="LINEAR", lo=158.2, hi=173.8))
    recipe = next(r for r in refdb.load_recipes() if r["id"] == "s2p_sulfide_sulfate")
    region.peaks = refdb.recipe_peaks(recipe, area_unit=4000.0)
    res = fitting.fit_region(region)
    assert res.success
    p = region.peaks
    assert p[0].center.value == pytest.approx(161.8, abs=0.05)
    assert p[1].center.value == pytest.approx(p[0].center.value + 1.18, abs=1e-9)
    assert p[1].area.value == pytest.approx(p[0].area.value * 0.5, rel=1e-9)
    assert p[0].area.value == pytest.approx(6000.0, rel=0.05)


def test_reindex_after_delete():
    p0 = Peak.create(center=100.0)
    p1 = Peak.create(center=101.0)
    p2 = Peak.create(center=102.0)
    p3 = Peak.create(center=103.0)
    p2.fwhm.expr = "p0_fwhm"
    p3.center.expr = "p2_center + 1.0"
    p1.area.expr = "p0_area * 0.5"
    peaks = [p0, p1, p2, p3]
    # delete index 1 -> p2 becomes index 1, p3 becomes index 2
    del peaks[1]
    refdb.reindex_exprs_after_delete(peaks, 1)
    assert peaks[1].fwhm.expr == "p0_fwhm"  # unchanged (refs index 0)
    assert peaks[2].center.expr == "p1_center + 1.0"  # shifted down

    # deleting a referenced peak detaches the constraint
    peaks2 = [Peak.create(center=1.0), Peak.create(center=2.0)]
    peaks2[1].center.expr = "p0_center + 5"
    del peaks2[0]
    refdb.reindex_exprs_after_delete(peaks2, 0)
    assert peaks2[0].center.expr is None
    assert peaks2[0].center.vary is True
