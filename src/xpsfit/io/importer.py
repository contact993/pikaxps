"""Flexible text/Excel import with auto-detection, feeding the Import Wizard.

Typical inputs: instrument ASCII exports (.dat/.txt/.csv) with unknown
delimiters and junk header lines, or Excel workbooks. The wizard flow is:
sniff() -> show preview + guessed mapping -> user adjusts -> to_region().
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from ..core.spectrum import Region

AL_KALPHA = 1486.6  # eV
MG_KALPHA = 1253.6  # eV

_DELIMS = {"\t": "tab", ",": "comma", ";": "semicolon", None: "whitespace"}


def _read_text(path: Path) -> str:
    for enc in ("utf-8-sig", "utf-8", "cp949", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="latin-1", errors="replace")


def _tokens(line: str, delim: str | None) -> list[str]:
    toks = line.split(delim) if delim else line.split()
    return [t.strip() for t in toks if t.strip() != ""]


def _is_number(tok: str) -> bool:
    try:
        float(tok)
        return True
    except ValueError:
        return False


@dataclass
class SniffResult:
    """What we guessed about a text source; every field is user-overridable.
    Source is either a file (path) or raw text (e.g. clipboard paste)."""

    path: Path | None
    lines: list[str]
    delimiter: str | None = None  # None = any whitespace
    skip_rows: int = 0
    n_columns: int = 0
    header: list[str] = field(default_factory=list)
    text: str | None = None  # set when the source is pasted text

    @property
    def delimiter_name(self) -> str:
        return _DELIMS.get(self.delimiter, repr(self.delimiter))


def sniff_text(text: str, path: Path | None = None, max_lines: int = 400) -> SniffResult:
    """Detect delimiter and the first data row of a numeric table in raw text."""
    lines = text.splitlines()[:max_lines]
    best = SniffResult(path=path, lines=lines, text=None if path else text)
    best_score = -1.0
    for delim in ("\t", ",", ";", None):
        for skip in range(min(len(lines), 60)):
            toks = _tokens(lines[skip], delim)
            if len(toks) < 2 or not all(_is_number(t) for t in toks):
                continue
            ncol = len(toks)
            good = 0
            total = 0
            for ln in lines[skip:]:
                if not ln.strip():
                    continue
                total += 1
                t = _tokens(ln, delim)
                if len(t) == ncol and all(_is_number(v) for v in t):
                    good += 1
            if total == 0:
                continue
            score = good / total - skip * 0.001
            if score > best_score:
                best_score = score
                best = SniffResult(path=path, lines=lines, delimiter=delim,
                                   skip_rows=skip, n_columns=ncol,
                                   text=None if path else text)
            break  # first parsable row for this delimiter is enough
    if best.n_columns and best.skip_rows > 0:
        cand = _tokens(best.lines[best.skip_rows - 1], best.delimiter)
        if len(cand) == best.n_columns and not any(_is_number(t) for t in cand):
            best.header = cand
    return best


def sniff(path: str | Path, max_lines: int = 400) -> SniffResult:
    path = Path(path)
    return sniff_text(_read_text(path), path=path, max_lines=max_lines)


def load_table(sniffed: SniffResult) -> pd.DataFrame:
    """Parse the full source with the (possibly user-corrected) sniff settings."""
    import io as _io

    source = _io.StringIO(sniffed.text) if sniffed.text is not None else sniffed.path
    df = pd.read_csv(
        source,
        sep=sniffed.delimiter if sniffed.delimiter else r"\s+",
        skiprows=sniffed.skip_rows,
        header=None,
        engine="python",
        comment=None,
        encoding_errors="replace",
        on_bad_lines="skip",
    )
    df = df.apply(pd.to_numeric, errors="coerce").dropna(axis=0, how="any")
    names = sniffed.header if len(sniffed.header) == df.shape[1] else None
    df.columns = names or [f"col {i + 1}" for i in range(df.shape[1])]
    return df.reset_index(drop=True)


def excel_engine(path: str | Path) -> str | None:
    """Pick the engine from file magic, not the extension. Returns None for
    'fake' Excel files (instrument text exports renamed to .xls)."""
    with open(path, "rb") as f:
        head = f.read(8)
    if head[:4] == b"PK\x03\x04":
        return "openpyxl"  # real .xlsx (zip)
    if head == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
        return "xlrd"  # real legacy .xls (OLE2)
    return None


def is_excel_file(path: str | Path) -> bool:
    return Path(path).suffix.lower() in (".xlsx", ".xlsm", ".xls") \
        and excel_engine(path) is not None


def excel_sheets(path: str | Path) -> list[str]:
    xl = pd.ExcelFile(path, engine=excel_engine(path))
    return list(xl.sheet_names)


def load_excel(path: str | Path, sheet: str | int = 0) -> pd.DataFrame:
    """Extract the numeric data table from one sheet.

    Robust to instrument layouts (e.g. Thermo Avantage): junk rows above,
    spacer columns between data columns, parameter text blocks to the side,
    and a name row + unit row above the data. Strategy: keep columns that are
    mostly numeric, find the contiguous numeric block, and read headers from
    up to two rows just above it.
    """
    raw = pd.read_excel(path, sheet_name=sheet, header=None, engine=excel_engine(path))
    if raw.empty:
        raise ValueError("empty sheet")
    num = raw.apply(pd.to_numeric, errors="coerce")
    counts = num.notna().sum()
    frac = num.notna().mean()
    keep = [c for c in raw.columns if counts[c] >= 5 and frac[c] >= 0.5]
    if len(keep) < 2:
        # fall back: any column with a meaningful number of numeric cells
        keep = [c for c in raw.columns if counts[c] >= max(5, 0.2 * len(raw))]
    if len(keep) < 2:
        raise ValueError("시트에서 숫자 데이터 열을 찾지 못했습니다")
    data = num[keep]
    rows_ok = data.notna().all(axis=1)
    first_row = int(rows_ok.idxmax()) if rows_ok.any() else None
    if first_row is None:
        raise ValueError("시트에서 숫자 데이터 행을 찾지 못했습니다")
    df = data.loc[rows_ok].reset_index(drop=True)

    # header = up to two text rows directly above the block, joined per column
    names = []
    for c in keep:
        parts = []
        for r in (first_row - 2, first_row - 1):
            if 0 <= r < len(raw):
                v = raw.iloc[r][c]
                if isinstance(v, str) and v.strip():
                    parts.append(v.strip())
        names.append(" ".join(parts))
    if not any(names):
        names = [f"col {i + 1}" for i in range(len(keep))]
    else:
        names = [n or f"col {i + 1}" for i, n in enumerate(names)]
    df.columns = names
    return df


@dataclass
class ColumnMapping:
    x_col: int = 0
    y_col: int = 1
    x_is_kinetic: bool = False
    photon_energy: float = AL_KALPHA


def to_region(df: pd.DataFrame, mapping: ColumnMapping, name: str, source: str = "") -> Region:
    x = df.iloc[:, mapping.x_col].to_numpy(dtype=float)
    y = df.iloc[:, mapping.y_col].to_numpy(dtype=float)
    if mapping.x_is_kinetic:
        x = mapping.photon_energy - x  # BE = hv - KE (work function ignored, as usual)
    order = np.argsort(x)
    return Region(name=name, x=x[order], y=y[order], source_file=source)


def guess_mapping(df: pd.DataFrame) -> ColumnMapping:
    """Heuristic: x = first monotonic column; KE if labeled kinetic or if a
    binding-energy interpretation would be implausible (>1600 eV)."""
    x_col = 0
    for i in range(df.shape[1]):
        v = df.iloc[:, i].to_numpy(dtype=float)
        d = np.diff(v)
        if v.size > 2 and (np.all(d > 0) or np.all(d < 0)):
            x_col = i
            break
    y_col = 1 if x_col == 0 else 0
    if df.shape[1] <= max(x_col, y_col):
        y_col = x_col  # degenerate single-column file; wizard will complain
    label = str(df.columns[x_col]).lower()
    kinetic = "kinetic" in label or label.startswith("ke")
    return ColumnMapping(x_col=x_col, y_col=y_col, x_is_kinetic=kinetic)
