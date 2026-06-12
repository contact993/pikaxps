"""VAMAS (ISO 14976, .vms) import via the `vamas` package: one Region per block."""
from __future__ import annotations

from pathlib import Path

import numpy as np

from ..core.spectrum import Region


def load_vamas(path: str | Path) -> list[Region]:
    from vamas import Vamas  # deferred: optional heavy import

    data = Vamas(str(path))
    regions: list[Region] = []
    for block in data.blocks:
        n = int(block.num_y_values) // max(1, int(block.num_corresponding_variables))
        x = np.asarray(block.x_start) + np.arange(n) * float(block.x_step)
        yvar = block.corresponding_variables[0]
        y = np.asarray(yvar.y_values, dtype=float)[:n]
        label = " ".join(
            t for t in (block.species_label, block.transition_or_charge_state_label) if t
        ).strip() or block.block_identifier
        x_label = (block.x_label or "").lower()
        if "kinetic" in x_label:
            hv = float(block.analysis_source_characteristic_energy or 1486.6)
            x = hv - x
        order = np.argsort(x)
        regions.append(Region(name=label, x=x[order], y=y[order], source_file=str(path)))
    return regions
