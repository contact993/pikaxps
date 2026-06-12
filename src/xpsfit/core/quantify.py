"""RSF-based quantification.

Doublet partners (area defined by an expr referencing the main peak) are
folded into their main peak, so a species' area is the full doublet sum.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import numpy as np

from .fitting import area_fractions
from .spectrum import Region

_EXPR_REF = re.compile(r"\bp(\d+)_area\b")
_CENTER_REF = re.compile(r"\bp(\d+)_center\b")


def species_areas(region: Region) -> list[tuple[str, float]]:
    """(label, area) per chemical species. Doublet partners merge into the
    peak their area expression references; satellites merge into the parent
    their center is tied to (shake-up intensity belongs to the same species —
    Biesinger's Cu(0):Cu(II) protocol)."""
    totals: dict[int, float] = {}
    owner: dict[int, int] = {}
    for i, p in enumerate(region.peaks):
        m = _EXPR_REF.search(p.area.expr or "")
        if m:
            owner[i] = int(m.group(1))
        elif getattr(p, "kind", "single") == "satellite":
            mc = _CENTER_REF.search(p.center.expr or "")
            owner[i] = int(mc.group(1)) if mc else i
        else:
            owner[i] = i
    for i, p in enumerate(region.peaks):
        root = i
        seen = set()
        while owner[root] != root and root not in seen:
            seen.add(root)
            root = owner[root]
        totals[root] = totals.get(root, 0.0) + max(0.0, p.area.value)
    return [(region.peaks[i].label or f"Peak {i + 1}", a) for i, a in sorted(totals.items())]


@dataclass
class QuantEntry:
    region_name: str
    label: str  # e.g. "Ni 2p"
    area: float
    rsf: float

    @property
    def corrected(self) -> float:
        return self.area / self.rsf if self.rsf > 0 else 0.0


def atomic_percent(entries: list[QuantEntry]) -> list[float]:
    corr = np.array([e.corrected for e in entries], dtype=float)
    total = corr.sum()
    return [100.0 * c / total if total > 0 else 0.0 for c in corr]


def region_total_area(region: Region) -> float:
    return sum(max(0.0, p.area.value) for p in region.peaks)


def state_table(region: Region) -> list[tuple[str, float, float]]:
    """(label, area, % of region) per species, doublets merged."""
    sp = species_areas(region)
    total = sum(a for _, a in sp)
    fractions = area_fractions(region)  # noqa: F841 (kept for API symmetry)
    return [(label, a, 100.0 * a / total if total > 0 else 0.0) for label, a in sp]
