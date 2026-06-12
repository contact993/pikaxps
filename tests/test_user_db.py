import json

import pytest

from xpsfit import refdb


@pytest.fixture
def user_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(refdb, "USER_DB_DIR", tmp_path)
    refdb.load_db.cache_clear()
    yield tmp_path
    refdb.load_db.cache_clear()


def find_state(el, orb, name):
    for st in refdb.elements()[el][orb]["states"]:
        if st["state"] == name:
            return st
    return None


def test_add_new_state_under_existing_orbital(user_dir):
    refdb.save_user_state("Ni", "2p", {
        "state": "Ni-Fe LDH (우리 랩)", "be_eV": 855.9, "range": [855.6, 856.2],
        "notes_ko": "랩 표준 시료 기준", "ref": "Kim et al., J. Mater. Chem. A (2025)",
    })
    st = find_state("Ni", "2p", "Ni-Fe LDH (우리 랩)")
    assert st is not None and st["user"] is True
    assert st["be_eV"] == 855.9
    assert "Kim et al." in refdb.reference_text(st["ref"])  # free-text passthrough
    # built-in states still present
    assert find_state("Ni", "2p", "Ni(0) metal") is not None


def test_override_builtin_state_by_name_and_delete_restores(user_dir):
    refdb.save_user_state("C", "1s", {
        "state": "C-C / C-H (adventitious)", "be_eV": 285.0,
        "ref": "우리 장비 교정 기준",
    })
    st = find_state("C", "1s", "C-C / C-H (adventitious)")
    assert st["be_eV"] == 285.0 and st.get("user")
    assert refdb.delete_user_state("C", "1s", "C-C / C-H (adventitious)")
    st2 = find_state("C", "1s", "C-C / C-H (adventitious)")
    assert st2["be_eV"] == 284.8 and not st2.get("user")  # built-in restored


def test_new_element_orbital_with_meta(user_dir):
    refdb.save_user_state("W", "4f", {
        "state": "W(0) metal", "be_eV": 31.4, "ref": "Moulder handbook",
    }, orbital_meta={"spin_orbit_splitting_eV": 2.18, "doublet_area_ratio": "4:3", "rsf": 9.8})
    assert "W" in refdb.elements()
    info = refdb.elements()["W"]["4f"]
    assert info["spin_orbit_splitting_eV"] == 2.18
    # doublet expansion works with user-provided metadata
    pair = refdb.doublet_pair("W", "4f", 31.4, main_index=0)
    assert pair[1].center.expr == "p0_center + 2.18"
    assert pair[1].area.expr == "p0_area * 0.75"
    # quantify/guess path recognizes it
    assert refdb.guess_element_orbital("W 4f scan") == ("W", "4f")


def test_user_file_format_is_plain_json(user_dir):
    refdb.save_user_state("O", "1s", {"state": "테스트", "be_eV": 530.5, "ref": "x"})
    d = json.loads(refdb.user_db_path().read_text(encoding="utf-8"))
    assert d["elements"]["O"]["1s"]["states"][0]["state"] == "테스트"


def test_corrupt_user_file_ignored(user_dir):
    refdb.USER_DB_DIR.mkdir(exist_ok=True)
    refdb.user_db_path().write_text("{ not json", encoding="utf-8")
    refdb.load_db.cache_clear()
    assert "Ni" in refdb.elements()  # built-in still loads
