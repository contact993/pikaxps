"""Generate realistic demo spectra into samples/ (run once; committed outputs)."""
from pathlib import Path

import numpy as np
import pandas as pd

from xpsfit.core import lineshapes

ROOT = Path(__file__).parent.parent
OUT = ROOT / "samples"
OUT.mkdir(exist_ok=True)
rng = np.random.default_rng(7)


def shirley_consistent(x, peak_sum, y1, y2):
    seg = 0.5 * (peak_sum[1:] + peak_sum[:-1]) * np.diff(x)
    cum = np.concatenate(([0.0], np.cumsum(seg)))
    return y1 + (y2 - y1) * cum / cum[-1]


def ni2p_dat():
    x = np.arange(848.0, 868.0, 0.05)
    peaks = (
        lineshapes.evaluate("GL_TAIL", x, 852.6, 42000.0, 1.0, 55.0, 0.45)
        + lineshapes.evaluate("GL_SUM", x, 853.7, 12000.0, 1.4, 30.0, 0.0)
        + lineshapes.evaluate("GL_SUM", x, 855.5, 26000.0, 2.4, 30.0, 0.0)
        + lineshapes.evaluate("GL_SUM", x, 861.0, 18000.0, 3.8, 30.0, 0.0)
    )
    bg = shirley_consistent(x, peaks, 5200.0, 11800.0)
    y = peaks + bg + rng.normal(0, np.sqrt(np.clip(peaks + bg, 1, None)) * 0.6)
    lines = [
        "# Demo: Ni 2p3/2 of partially oxidized Ni foam (synthetic)",
        "# Instrument: synthetic Al Kalpha, pass 20 eV",
        "# BE(eV)\tcounts",
    ]
    lines += [f"{bi:.2f}\t{yi:.1f}" for bi, yi in zip(x, y)]
    (OUT / "Ni2p_NiFoam.dat").write_text("\n".join(lines), encoding="utf-8")


def c1s_csv():
    x = np.arange(280.0, 294.0, 0.05)
    peaks = (
        lineshapes.evaluate("GL_SUM", x, 284.8, 30000.0, 1.25, 30.0, 0.0)
        + lineshapes.evaluate("GL_SUM", x, 286.3, 8000.0, 1.25, 30.0, 0.0)
        + lineshapes.evaluate("GL_SUM", x, 288.7, 4000.0, 1.3, 30.0, 0.0)
    )
    bg = shirley_consistent(x, peaks, 900.0, 1500.0)
    y = peaks + bg + rng.normal(0, np.sqrt(np.clip(peaks + bg, 1, None)) * 0.6)
    pd.DataFrame({"BE": np.round(x, 3), "counts": np.round(y, 1)}).to_csv(
        OUT / "C1s_carbon.csv", index=False)


def s2p_xlsx():
    x = np.arange(158.0, 174.0, 0.05)
    peaks = (
        lineshapes.evaluate("GL_SUM", x, 161.9, 22000.0, 0.95, 30.0, 0.0)
        + lineshapes.evaluate("GL_SUM", x, 163.08, 11000.0, 0.95, 30.0, 0.0)
        + lineshapes.evaluate("GL_SUM", x, 168.7, 3500.0, 1.4, 30.0, 0.0)
        + lineshapes.evaluate("GL_SUM", x, 169.88, 1750.0, 1.4, 30.0, 0.0)
    )
    bg = shirley_consistent(x, peaks, 1500.0, 2300.0)
    y = peaks + bg + rng.normal(0, np.sqrt(np.clip(peaks + bg, 1, None)) * 0.6)
    pd.DataFrame({"Binding Energy (eV)": np.round(x, 3),
                  "Intensity (counts)": np.round(y, 1)}).to_excel(
        OUT / "S2p_MoS2.xlsx", index=False, sheet_name="S2p")


def pt4f_ke_txt():
    """Kinetic-energy axis demo (Al Kalpha): tests the KE->BE wizard path."""
    be = np.arange(66.0, 82.0, 0.05)
    peaks = (
        lineshapes.evaluate("GL_TAIL", be, 71.1, 30000.0, 0.95, 55.0, 0.35)
        + lineshapes.evaluate("GL_TAIL", be, 74.43, 22500.0, 0.95, 55.0, 0.35)
        + lineshapes.evaluate("GL_SUM", be, 72.6, 6000.0, 1.4, 30.0, 0.0)
        + lineshapes.evaluate("GL_SUM", be, 75.93, 4500.0, 1.4, 30.0, 0.0)
    )
    bg = shirley_consistent(be, peaks, 2500.0, 4200.0)
    y = peaks + bg + rng.normal(0, np.sqrt(np.clip(peaks + bg, 1, None)) * 0.6)
    ke = 1486.6 - be
    order = np.argsort(ke)
    lines = ["Kinetic Energy (eV)   Counts"]
    lines += [f"{k:.2f}   {v:.1f}" for k, v in zip(ke[order], y[order])]
    (OUT / "Pt4f_kinetic.txt").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    ni2p_dat()
    c1s_csv()
    s2p_xlsx()
    pt4f_ke_txt()
    print("samples written to", OUT)
