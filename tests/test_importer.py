import numpy as np
import pandas as pd
import pytest

from xpsfit.io import importer


def write(tmp_path, name, text):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


def test_tab_dat_no_header(tmp_path):
    p = write(tmp_path, "a.dat", "850.0\t1200\n850.1\t1210\n850.2\t1190\n")
    s = importer.sniff(p)
    assert s.delimiter == "\t"
    assert s.skip_rows == 0
    assert s.n_columns == 2
    df = importer.load_table(s)
    assert df.shape == (3, 2)


def test_csv_with_header(tmp_path):
    p = write(tmp_path, "b.csv", "BE,counts\n284.0,100\n284.1,110\n284.2,120\n")
    s = importer.sniff(p)
    assert s.delimiter == ","
    assert s.skip_rows == 1
    assert s.header == ["BE", "counts"]
    df = importer.load_table(s)
    assert list(df.columns) == ["BE", "counts"]
    assert df.shape == (3, 2)


def test_messy_instrument_header(tmp_path):
    junk = "Instrument: K-Alpha\nDate 2026-06-12\nRegion Ni2p\nPass energy 50\n\n"
    body = "\n".join(f"{850 + i * 0.1:.2f}   {1000 + i}   0.97" for i in range(50))
    p = write(tmp_path, "c.txt", junk + body + "\n")
    s = importer.sniff(p)
    assert s.delimiter is None  # whitespace
    assert s.skip_rows == 5
    assert s.n_columns == 3
    df = importer.load_table(s)
    assert df.shape == (50, 3)


def test_guess_mapping_and_to_region(tmp_path):
    p = write(tmp_path, "d.dat", "\n".join(f"{300 - i * 0.1:.2f}\t{50 + i}" for i in range(30)))
    s = importer.sniff(p)
    df = importer.load_table(s)
    m = importer.guess_mapping(df)
    assert (m.x_col, m.y_col) == (0, 1)
    r = importer.to_region(df, m, name="test", source=str(p))
    assert np.all(np.diff(r.x) > 0)  # stored ascending even though file descends
    assert r.x.size == 30


def test_kinetic_energy_conversion():
    df = pd.DataFrame({"KE": [600.0, 600.5, 601.0], "I": [10.0, 20.0, 15.0]})
    m = importer.ColumnMapping(x_col=0, y_col=1, x_is_kinetic=True, photon_energy=1486.6)
    r = importer.to_region(df, m, name="ke")
    assert r.x.max() == pytest.approx(1486.6 - 600.0)
    assert r.x.min() == pytest.approx(1486.6 - 601.0)
    # intensity stays paired with its point after the axis flip
    assert r.y[np.argmin(r.x)] == 15.0


def test_excel_round_trip(tmp_path):
    p = tmp_path / "e.xlsx"
    df0 = pd.DataFrame({"Binding Energy": np.arange(280.0, 295.0, 0.5), "Counts": np.arange(30.0)})
    df0.to_excel(p, index=False, sheet_name="C1s")
    assert importer.excel_sheets(p) == ["C1s"]
    df = importer.load_excel(p, "C1s")
    assert list(df.columns) == ["Binding Energy", "Counts"]
    assert df.shape == (30, 2)
    m = importer.guess_mapping(df)
    r = importer.to_region(df, m, name="C 1s")
    assert r.x.size == 30


def test_korean_encoding(tmp_path):
    p = tmp_path / "f.csv"
    p.write_bytes("시료,측정\n284.0,100\n284.5,200\n".encode("cp949"))
    s = importer.sniff(p)
    df = importer.load_table(s)
    assert df.shape == (2, 2)
