"""Batch fitting: apply one region's model (background + peaks) to many spectra.

Typical use: the same Ni 2p window measured before/after reaction across
several samples — fit them all with an identical constrained model and
compare areas in one table.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass

import pandas as pd

from . import fitting
from .quantify import species_areas
from .spectrum import Region


@dataclass
class BatchItem:
    name: str
    region: Region
    success: bool = False
    redchi: float = float("nan")


def apply_template(template: Region, target: Region) -> Region:
    """Copy the template's background spec and peak model onto target data."""
    target.background = copy.deepcopy(template.background)
    lo, hi = target.x[0], target.x[-1]
    if target.background.lo is not None:
        target.background.lo = max(lo, target.background.lo)
    if target.background.hi is not None:
        target.background.hi = min(hi, target.background.hi)
    target.peaks = copy.deepcopy(template.peaks)
    return target


def run_batch(template: Region, targets: list[Region]) -> tuple[list[BatchItem], pd.DataFrame]:
    items: list[BatchItem] = []
    rows = []
    for t in targets:
        region = apply_template(template, t)
        res = fitting.fit_region(region)
        items.append(BatchItem(name=region.name, region=region,
                               success=res.success, redchi=res.redchi))
        row: dict = {"Sample": region.name, "ok": res.success, "red. chi2": round(res.redchi, 2)}
        total = sum(a for _, a in species_areas(region)) or 1.0
        for label, area in species_areas(region):
            row[f"{label} area"] = round(area, 1)
            row[f"{label} %"] = round(100.0 * area / total, 2)
        rows.append(row)
    return items, pd.DataFrame(rows)
