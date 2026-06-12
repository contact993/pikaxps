"""Exports: parameter tables (CSV/Excel), curve data, publication figures."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..core import fitting
from ..core.quantify import species_areas
from ..core.spectrum import Region


def params_dataframe(region: Region) -> pd.DataFrame:
    fractions = fitting.area_fractions(region)
    rows = []
    for i, p in enumerate(region.peaks):
        rows.append({
            "#": i,
            "Label": p.label or f"Peak {i + 1}",
            "Shape": p.shape,
            "Center (eV)": round(p.center.value, 3),
            "FWHM (eV)": round(p.fwhm.value, 3),
            "Area": round(p.area.value, 1),
            "Area %": round(fractions[i], 2) if i < len(fractions) else None,
            "%L-G": round(p.mix.value, 1),
            "Asym": round(p.asym.value, 3),
            "Center constraint": p.center.expr or ("fixed" if not p.center.vary else ""),
            "Area constraint": p.area.expr or ("fixed" if not p.area.vary else ""),
            "FWHM constraint": p.fwhm.expr or ("fixed" if not p.fwhm.vary else ""),
        })
    return pd.DataFrame(rows)


def curves_dataframe(region: Region) -> pd.DataFrame:
    res = fitting.eval_model(region)
    data = {
        "BE (eV)": region.x,
        "Raw": region.y,
        "Background": res.background,
        "Envelope": res.envelope,
        "Residual": res.residual,
    }
    for i, comp in enumerate(res.components):
        label = region.peaks[i].label or f"Peak {i + 1}"
        data[f"{label}"] = res.background + comp
    return pd.DataFrame(data)


def export_excel(regions: list[Region], path: str | Path) -> Path:
    path = Path(path).with_suffix(".xlsx")
    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        summary_rows = []
        for r in regions:
            sheet = r.name[:28] or "Region"
            params_dataframe(r).to_excel(xw, sheet_name=f"{sheet} params"[:31], index=False)
            curves_dataframe(r).to_excel(xw, sheet_name=f"{sheet} curves"[:31], index=False)
            for label, area in species_areas(r):
                summary_rows.append({"Region": r.name, "Species": label, "Area (doublet sum)": round(area, 1)})
        if summary_rows:
            pd.DataFrame(summary_rows).to_excel(xw, sheet_name="Species summary", index=False)
    return path


def export_params_csv(region: Region, path: str | Path) -> Path:
    path = Path(path).with_suffix(".csv")
    params_dataframe(region).to_csv(path, index=False)
    return path


def export_curves_csv(region: Region, path: str | Path) -> Path:
    path = Path(path).with_suffix(".csv")
    curves_dataframe(region).to_csv(path, index=False)
    return path


COMPONENT_COLORS = [
    "#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e",
    "#8c564b", "#e377c2", "#17becf", "#bcbd22", "#7f7f7f",
]


def make_figure(region: Region, show_residual: bool = True, title: str | None = None):
    """Publication-style matplotlib figure (BE axis reversed, components filled)."""
    import matplotlib
    matplotlib.use("Agg", force=False)
    import matplotlib.pyplot as plt

    res = fitting.eval_model(region)
    if show_residual and region.peaks:
        fig, (ax, axr) = plt.subplots(
            2, 1, sharex=True, figsize=(6, 5),
            gridspec_kw={"height_ratios": [4, 1], "hspace": 0.06},
        )
    else:
        fig, ax = plt.subplots(figsize=(6, 4.2))
        axr = None

    ax.plot(region.x, region.y, "o", ms=2.5, mfc="none", mec="#444444", mew=0.7, label="Data")
    if region.background.kind != "NONE":
        ax.plot(region.x, res.background, "--", lw=1.0, color="#888888", label="Background")
    for i, comp in enumerate(res.components):
        color = COMPONENT_COLORS[i % len(COMPONENT_COLORS)]
        label = region.peaks[i].label or f"Peak {i + 1}"
        ax.fill_between(region.x, res.background, res.background + comp,
                        alpha=0.35, color=color, lw=0)
        ax.plot(region.x, res.background + comp, lw=1.0, color=color, label=label)
    if region.peaks:
        ax.plot(region.x, res.envelope, lw=1.4, color="#000000", label="Envelope")
    ax.set_ylabel("Intensity (counts)")
    ax.set_title(title or region.name)
    ax.legend(fontsize=7, frameon=False)
    ax.invert_xaxis()
    if axr is not None:
        axr.axhline(0.0, color="#888888", lw=0.7)
        axr.plot(region.x, res.residual, lw=0.8, color="#1f77b4")
        axr.set_ylabel("Res.")
        axr.set_xlabel("Binding energy (eV)")
        span = float(np.max(np.abs(res.residual))) if res.residual.size else 1.0
        axr.set_ylim(-1.3 * span, 1.3 * span)
        fig.subplots_adjust(left=0.13, right=0.97, top=0.93, bottom=0.11)
    else:
        ax.set_xlabel("Binding energy (eV)")
        fig.tight_layout()
    return fig


def save_figure(region: Region, path: str | Path, dpi: int = 300) -> Path:
    path = Path(path)
    fig = make_figure(region)
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    import matplotlib.pyplot as plt
    plt.close(fig)
    return path
