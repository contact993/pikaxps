"""Reference database: binding energies, doublet parameters, fitting recipes.

JSON files live next to this module; everything is user-editable. Expansion
helpers turn DB entries into constrained Peak lists ready to insert into a
Region (expr indices are offset by the region's existing peak count).
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from ..core.spectrum import ParamSpec, Peak

_DIR = Path(__file__).parent

# user overlay: survives app updates, syncable between machines
USER_DB_DIR = Path.home() / ".xpsfit"


def user_db_path() -> Path:
    return USER_DB_DIR / "user_refdb.json"


def load_user_db() -> dict:
    p = user_db_path()
    if p.exists():
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(d.get("elements"), dict):
                return d
        except (json.JSONDecodeError, OSError):
            pass
    return {"elements": {}}


_ORB_META_KEYS = ("spin_orbit_splitting_eV", "doublet_area_ratio", "rsf", "notes_ko")


@lru_cache(maxsize=1)
def load_db() -> dict:
    """Built-in literature DB with the user's overlay merged on top.

    States match by name: a user state with the same name replaces the
    built-in one; new names are appended (flagged "user": True). Orbital
    metadata (splitting/ratio/RSF) is only overridden where the user file
    provides a value.
    """
    base = json.loads((_DIR / "binding_energies.json").read_text(encoding="utf-8"))
    user = load_user_db()
    for el, orbs in user.get("elements", {}).items():
        b_el = base["elements"].setdefault(el, {})
        for orb, info in orbs.items():
            b_orb = b_el.setdefault(orb, {
                "spin_orbit_splitting_eV": None, "doublet_area_ratio": None,
                "rsf": 1.0, "states": [],
            })
            for k in _ORB_META_KEYS:
                if info.get(k) is not None:
                    b_orb[k] = info[k]
            names = {s["state"]: i for i, s in enumerate(b_orb.setdefault("states", []))}
            for st in info.get("states", []):
                st = dict(st)
                st["user"] = True
                if st["state"] in names:
                    b_orb["states"][names[st["state"]]] = st
                else:
                    b_orb["states"].append(st)
    return base


def save_user_state(element: str, orbital: str, state: dict,
                    orbital_meta: dict | None = None) -> None:
    """Add/replace one state in the user overlay (matched by state name)."""
    db = load_user_db()
    el = db["elements"].setdefault(element, {})
    orb = el.setdefault(orbital, {})
    if orbital_meta:
        for k in _ORB_META_KEYS:
            if orbital_meta.get(k) is not None:
                orb[k] = orbital_meta[k]
    states = orb.setdefault("states", [])
    state = {k: v for k, v in state.items() if v not in (None, "")}
    for i, s in enumerate(states):
        if s["state"] == state["state"]:
            states[i] = state
            break
    else:
        states.append(state)
    USER_DB_DIR.mkdir(parents=True, exist_ok=True)
    user_db_path().write_text(json.dumps(db, ensure_ascii=False, indent=1), encoding="utf-8")
    load_db.cache_clear()


def delete_user_state(element: str, orbital: str, state_name: str) -> bool:
    """Remove a user-overlay state (built-in entries reappear if overridden)."""
    db = load_user_db()
    try:
        states = db["elements"][element][orbital]["states"]
    except KeyError:
        return False
    kept = [s for s in states if s["state"] != state_name]
    if len(kept) == len(states):
        return False
    db["elements"][element][orbital]["states"] = kept
    if not kept and len(db["elements"][element][orbital]) == 1:
        del db["elements"][element][orbital]
        if not db["elements"][element]:
            del db["elements"][element]
    USER_DB_DIR.mkdir(parents=True, exist_ok=True)
    user_db_path().write_text(json.dumps(db, ensure_ascii=False, indent=1), encoding="utf-8")
    load_db.cache_clear()
    return True


@lru_cache(maxsize=1)
def load_recipes() -> list[dict]:
    return json.loads((_DIR / "recipes.json").read_text(encoding="utf-8"))["recipes"]


def reference_text(key: str) -> str:
    return load_db().get("references", {}).get(key, key)


def elements() -> dict:
    return load_db()["elements"]


def ratio_factor(ratio: str | None) -> float:
    """'2:1' -> 0.5 (partner area = main * factor)."""
    if not ratio:
        return 0.5
    a, b = ratio.split(":")
    return float(b) / float(a)


_ORBITAL_SUFFIX = {"p": ("3/2", "1/2"), "d": ("5/2", "3/2"), "f": ("7/2", "5/2")}


def doublet_labels(orbital: str) -> tuple[str, str]:
    suf = _ORBITAL_SUFFIX.get(orbital[-1], ("", ""))
    return (f"{orbital}{suf[0]}", f"{orbital}{suf[1]}") if suf[0] else (orbital, orbital)


def make_peak(
    label: str,
    center: float,
    center_tol: float = 0.5,
    area: float = 1000.0,
    fwhm: float = 1.4,
    mix: float = 30.0,
    shape: str = "GL_SUM",
) -> Peak:
    p = Peak.create(center=center, area=area, fwhm=fwhm, mix=mix, shape=shape, label=label)
    p.center.min = center - center_tol
    p.center.max = center + center_tol
    return p


def doublet_pair(
    element: str,
    orbital: str,
    center: float,
    main_index: int,
    label: str = "",
    area: float = 1000.0,
    fwhm: float = 1.4,
    mix: float = 30.0,
    center_tol: float = 0.5,
) -> list[Peak]:
    """Main + spin-orbit partner with exact splitting/ratio/width constraints.
    main_index is the main peak's index in the destination region."""
    orb = elements()[element][orbital]
    split = orb["spin_orbit_splitting_eV"]
    factor = ratio_factor(orb["doublet_area_ratio"])
    lab_main, lab_partner = doublet_labels(orbital)
    main = make_peak(f"{label or element} {lab_main}", center, center_tol, area, fwhm, mix)
    main.kind = "doublet_main"
    partner = Peak.create(center=center + split, area=area * factor, fwhm=fwhm, mix=mix,
                          label=f"{label or element} {lab_partner}")
    partner.kind = "doublet_partner"
    partner.center = ParamSpec(value=center + split, expr=f"p{main_index}_center + {split}")
    partner.area = ParamSpec(value=area * factor, expr=f"p{main_index}_area * {factor:.6g}")
    partner.fwhm = ParamSpec(value=fwhm, expr=f"p{main_index}_fwhm")
    partner.mix = ParamSpec(value=mix, vary=False, min=0.0, max=100.0)
    return [main, partner]


def recipe_peaks(recipe: dict, index_offset: int = 0, area_unit: float = 1000.0) -> list[Peak]:
    """Expand a recipe into constrained peaks. The first species is the anchor
    for link_fwhm; doublet recipes expand each species into a spin-orbit pair."""
    out: list[Peak] = []
    anchor_index: int | None = None
    is_doublet = recipe.get("doublet", False)
    for spec in recipe["peaks"]:
        idx = index_offset + len(out)
        area = area_unit * spec.get("area_scale", 1.0)
        kwargs = dict(
            label=spec["label"],
            center=spec["center"],
            center_tol=spec.get("center_tol", 0.5),
            area=area,
            fwhm=spec.get("fwhm", 1.4),
            mix=spec.get("mix", 30.0),
        )
        if is_doublet:
            pair = doublet_pair(recipe["element"], recipe["orbital"], main_index=idx, **kwargs)
            main = pair[0]
        else:
            main = make_peak(shape=spec.get("shape", "GL_SUM"), **kwargs)
            pair = [main]
        if anchor_index is None:
            anchor_index = idx
        elif spec.get("link_fwhm"):
            main.fwhm = ParamSpec(value=main.fwhm.value, expr=f"p{anchor_index}_fwhm")
        out.extend(pair)
    return out


def guess_element_orbital(name: str) -> tuple[str, str] | None:
    """'Ni 2p' / 'ni2p' / 'CHR-Ir Ir4f Scan' -> ('Ni', '2p') / ('Ir', '4f')."""
    m = re.search(r"([A-Z][a-z]?)\s*([1-7][spdf])", name.strip().capitalize())
    if not m:
        m = re.search(r"([A-Za-z]{1,2})\s*([1-7][spdf])", name)
    if not m:
        return None
    el = m.group(1).capitalize()
    orb = m.group(2).lower()
    db = elements()
    if el in db and orb in db[el]:
        return el, orb
    return None


def reindex_exprs_after_delete(peaks: list[Peak], deleted_index: int) -> None:
    """Fix p{i}_ references after removing a peak: higher indices shift down by
    one; references to the deleted peak are detached (value kept, expr cleared)."""

    def fix(expr: str) -> str | None:
        broken = False

        def repl(m: re.Match) -> str:
            nonlocal broken
            i = int(m.group(1))
            if i == deleted_index:
                broken = True
                return m.group(0)
            return f"p{i - 1}_" if i > deleted_index else m.group(0)

        new = re.sub(r"\bp(\d+)_", repl, expr)
        return None if broken else new

    for p in peaks:
        for spec in p.params().values():
            if spec.expr:
                fixed = fix(spec.expr)
                if fixed is None:
                    spec.expr = None
                    spec.vary = True
                else:
                    spec.expr = fixed
