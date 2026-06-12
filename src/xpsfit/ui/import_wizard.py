"""Import wizard: raw preview -> delimiter/header -> column mapping -> Region.

Key UX: 자동 감지가 틀려도 사용자가 미리보기에서 직접 고칠 수 있다 —
데이터 시작 줄 클릭 지정, 구분자/열 선택, KE→BE 변환.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QGuiApplication
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QPlainTextEdit, QSpinBox, QTableWidget, QTableWidgetItem, QVBoxLayout,
)

from ..core.spectrum import Region
from ..io import importer

DELIM_OPTIONS = [("자동/공백 (whitespace)", None), ("Tab", "\t"), ("Comma ,", ","), ("Semicolon ;", ";")]


class ImportWizard(QDialog):
    """One dialog, live preview. exec() == Accepted -> .result_region is set.

    Three source modes: text file, Excel workbook, or pasted text
    (path=None -> paste mode, prefilled from the clipboard).
    """

    def __init__(self, path: str | Path | None, parent=None, paste_text: str | None = None):
        super().__init__(parent)
        self.path = Path(path) if path else None
        self.paste_mode = self.path is None
        self.result_region: Region | None = None
        self.result_regions: list[Region] = []
        self.df: pd.DataFrame | None = None
        self.is_excel = bool(self.path) and importer.is_excel_file(self.path)
        title = "Paste Data — 클립보드 붙여넣기" if self.paste_mode else f"Import — {self.path.name}"
        self.setWindowTitle(title)
        self.resize(860, 680)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # --- parsing controls ---
        parse_box = QGroupBox("1. 데이터 붙여넣기" if self.paste_mode else "1. 파일 파싱")
        pl = QHBoxLayout(parse_box)
        if self.is_excel:
            pv = QVBoxLayout()
            pv.addWidget(QLabel("가져올 시트 선택 — <b>체크한 시트가 각각 region</b>이 됩니다 (클릭 = 미리보기)"))
            self.sheet_list = QListWidget()
            self.sheet_list.setMaximumHeight(118)
            self._sheet_cache: dict[str, pd.DataFrame | None] = {}
            sheets = importer.excel_sheets(self.path)
            for s in sheets:
                try:
                    self._sheet_cache[s] = importer.load_excel(self.path, s)
                except Exception:  # noqa: BLE001 - non-data sheet
                    self._sheet_cache[s] = None
                ok = self._sheet_cache[s] is not None
                item = QListWidgetItem(s if ok else f"{s}  (표 데이터 없음)")
                item.setData(Qt.ItemDataRole.UserRole, s)
                if ok:
                    item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
                                  | Qt.ItemFlag.ItemIsUserCheckable)
                    item.setCheckState(Qt.CheckState.Unchecked)
                else:
                    item.setFlags(Qt.ItemFlag.NoItemFlags)
                self.sheet_list.addItem(item)
            # default: check scan/survey-named sheets, else the first parsable one
            valid = [i for i in range(self.sheet_list.count())
                     if self._sheet_cache[sheets[i]] is not None]
            scanlike = [i for i in valid
                        if any(k in sheets[i].lower() for k in ("scan", "survey"))]
            for i in (scanlike or valid[:1]):
                self.sheet_list.item(i).setCheckState(Qt.CheckState.Checked)
            if valid:
                self.sheet_list.setCurrentRow((scanlike or valid)[0])
            self.sheet_list.currentRowChanged.connect(self._reparse)
            self.sheet_list.itemChanged.connect(self._sheet_checks_changed)
            pv.addWidget(self.sheet_list)
            self.sheet_count_label = QLabel("")
            self.sheet_count_label.setProperty("class", "subtle")
            pv.addWidget(self.sheet_count_label)
            pl.addLayout(pv)
        else:
            if self.paste_mode:
                text = paste_text if paste_text is not None else QGuiApplication.clipboard().text()
                self.sniffed = importer.sniff_text(text or "")
            else:
                self.sniffed = importer.sniff(self.path)
            pl.addWidget(QLabel("구분자:"))
            self.delim_combo = QComboBox()
            for name, val in DELIM_OPTIONS:
                self.delim_combo.addItem(name, val)
            idx = next((i for i, (_, v) in enumerate(DELIM_OPTIONS) if v == self.sniffed.delimiter), 0)
            self.delim_combo.setCurrentIndex(idx)
            self.delim_combo.currentIndexChanged.connect(self._reparse)
            pl.addWidget(self.delim_combo)
            pl.addWidget(QLabel("데이터 시작 행:"))
            self.skip_spin = QSpinBox()
            self.skip_spin.setRange(0, 999)
            self.skip_spin.setValue(self.sniffed.skip_rows)
            self.skip_spin.setToolTip("이 줄부터 숫자 데이터로 해석합니다. 아래 원본 미리보기에서 줄을 클릭해도 됩니다.")
            self.skip_spin.valueChanged.connect(self._reparse)
            pl.addWidget(self.skip_spin)
            pl.addStretch(1)
        layout.addWidget(parse_box)

        # --- raw view: paste box (editable) or file preview (click = data start) ---
        if self.paste_mode:
            self.paste_edit = QPlainTextEdit()
            self.paste_edit.setFont(QFont("Menlo", 11))
            self.paste_edit.setMinimumHeight(130)
            self.paste_edit.setMaximumHeight(180)
            self.paste_edit.setPlaceholderText(
                "여기에 붙여넣으세요 (⌘V) — 엑셀/오리진에서 BE·강도 두 열을 복사하면 됩니다.\n"
                "헤더 행이 섞여 있어도 자동으로 건너뜁니다.")
            if self.sniffed.text:
                self.paste_edit.setPlainText(self.sniffed.text)
            self._paste_timer = QTimer(self)
            self._paste_timer.setSingleShot(True)
            self._paste_timer.setInterval(250)
            self._paste_timer.timeout.connect(self._paste_changed)
            self.paste_edit.textChanged.connect(self._paste_timer.start)
            layout.addWidget(self.paste_edit)
        elif not self.is_excel:
            self.raw_list = QListWidget()
            self.raw_list.setFont(QFont("Menlo", 11))
            self.raw_list.setMinimumHeight(120)
            self.raw_list.setMaximumHeight(170)
            self.raw_list.setToolTip("원본 파일 미리보기 — 데이터가 시작되는 줄을 클릭하세요")
            for i, ln in enumerate(self.sniffed.lines[:120]):
                QListWidgetItem(f"{i:>3} │ {ln[:160]}", self.raw_list)
            self.raw_list.itemClicked.connect(
                lambda item: self.skip_spin.setValue(self.raw_list.row(item)))
            layout.addWidget(self.raw_list)

        # --- parsed table preview ---
        self.preview = QTableWidget(0, 0)
        self.preview.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.preview.setFixedHeight(170)
        layout.addWidget(QLabel("파싱 결과 미리보기 (앞 12행):"))
        layout.addWidget(self.preview)

        # --- column mapping ---
        map_box = QGroupBox("2. 열 선택")
        ml = QHBoxLayout(map_box)
        ml.addWidget(QLabel("X (에너지):"))
        self.x_combo = QComboBox()
        ml.addWidget(self.x_combo)
        ml.addWidget(QLabel("Y (강도):"))
        self.y_combo = QComboBox()
        ml.addWidget(self.y_combo)
        self.ke_check = QCheckBox("X는 Kinetic Energy (BE로 변환)")
        self.ke_check.setToolTip("BE = hν − KE 로 변환합니다 (일함수 무시, 통상 관례)")
        ml.addWidget(self.ke_check)
        self.hv_combo = QComboBox()
        self.hv_combo.addItem("Al Kα 1486.6 eV", importer.AL_KALPHA)
        self.hv_combo.addItem("Mg Kα 1253.6 eV", importer.MG_KALPHA)
        self.hv_combo.addItem("직접 입력…", None)
        self.hv_spin = QDoubleSpinBox()
        self.hv_spin.setRange(10.0, 20000.0)
        self.hv_spin.setValue(importer.AL_KALPHA)
        self.hv_spin.setSuffix(" eV")
        self.hv_spin.setVisible(False)
        self.hv_combo.currentIndexChanged.connect(
            lambda: self.hv_spin.setVisible(self.hv_combo.currentData() is None))
        self.ke_check.toggled.connect(lambda on: (self.hv_combo.setEnabled(on), self.hv_spin.setEnabled(on)))
        self.hv_combo.setEnabled(False)
        self.hv_spin.setEnabled(False)
        ml.addWidget(self.hv_combo)
        ml.addWidget(self.hv_spin)
        ml.addStretch(1)
        layout.addWidget(map_box)

        # --- region name ---
        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Region 이름:"))
        self.name_edit = QLineEdit("Pasted data" if self.paste_mode else self.path.stem)
        self.name_edit.setToolTip("예: 'Ni 2p' 처럼 원소+오비탈로 지으면 정량 패널이 자동 인식합니다")
        name_row.addWidget(self.name_edit)
        layout.addLayout(name_row)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                                   | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._reparse()
        if self.is_excel:
            self._sheet_checks_changed()

    # ---------- logic ----------

    def _paste_changed(self) -> None:
        """Re-sniff pasted text from scratch (delimiter/skip auto-detected again)."""
        self.sniffed = importer.sniff_text(self.paste_edit.toPlainText())
        self.delim_combo.blockSignals(True)
        idx = next((i for i, (_, v) in enumerate(DELIM_OPTIONS)
                    if v == self.sniffed.delimiter), 0)
        self.delim_combo.setCurrentIndex(idx)
        self.delim_combo.blockSignals(False)
        self.skip_spin.blockSignals(True)
        self.skip_spin.setValue(self.sniffed.skip_rows)
        self.skip_spin.blockSignals(False)
        self._reparse()

    def _current_sheet(self) -> str | None:
        item = self.sheet_list.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _checked_sheets(self) -> list[str]:
        out = []
        for i in range(self.sheet_list.count()):
            item = self.sheet_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                s = item.data(Qt.ItemDataRole.UserRole)
                if self._sheet_cache.get(s) is not None:
                    out.append(s)
        return out

    def _sheet_checks_changed(self) -> None:
        n = len(self._checked_sheets())
        multi = n > 1
        self.name_edit.setEnabled(not multi)
        self.sheet_count_label.setText(
            f"{n}개 시트 선택됨 — 각 region 이름은 시트명을 사용합니다" if multi
            else ("시트를 체크하세요" if n == 0 else ""))

    def _reparse(self) -> None:
        try:
            if self.is_excel:
                sheet = self._current_sheet()
                if sheet is None or self._sheet_cache.get(sheet) is None:
                    return
                self.df = self._sheet_cache[sheet]
                auto = sheet
                if self.name_edit.text() in ("", self.path.stem, getattr(self, "_auto_name", "")):
                    self.name_edit.setText(auto)
                self._auto_name = auto
            else:
                if self.paste_mode:
                    self.sniffed.text = self.paste_edit.toPlainText()
                    self.sniffed.lines = self.sniffed.text.splitlines()[:400]
                self.sniffed.delimiter = self.delim_combo.currentData()
                self.sniffed.skip_rows = self.skip_spin.value()
                self.sniffed.header = []
                if self.sniffed.skip_rows > 0:
                    cand = self.sniffed.lines[self.sniffed.skip_rows - 1].split(
                        self.sniffed.delimiter) if self.sniffed.delimiter else \
                        self.sniffed.lines[self.sniffed.skip_rows - 1].split()
                    cand = [c.strip() for c in cand if c.strip()]
                    if cand and not any(importer._is_number(c) for c in cand):
                        self.sniffed.header = cand
                self.df = importer.load_table(self.sniffed)
        except Exception as e:  # noqa: BLE001 - show parse problems in the preview
            self.df = None
            self.preview.setRowCount(1)
            self.preview.setColumnCount(1)
            self.preview.setItem(0, 0, QTableWidgetItem(f"파싱 실패: {e}"))
            return
        self._fill_preview()
        self._fill_mapping()

    def _fill_preview(self) -> None:
        df = self.df
        n = min(12, len(df))
        self.preview.setRowCount(n)
        self.preview.setColumnCount(df.shape[1])
        self.preview.setHorizontalHeaderLabels([str(c) for c in df.columns])
        for r in range(n):
            for c in range(df.shape[1]):
                self.preview.setItem(r, c, QTableWidgetItem(f"{df.iat[r, c]:g}"))

    def _fill_mapping(self) -> None:
        df = self.df
        guess = importer.guess_mapping(df)
        for combo in (self.x_combo, self.y_combo):
            combo.blockSignals(True)
            combo.clear()
            combo.addItems([str(c) for c in df.columns])
            combo.blockSignals(False)
        self.x_combo.setCurrentIndex(guess.x_col)
        self.y_combo.setCurrentIndex(min(guess.y_col, df.shape[1] - 1))
        self.ke_check.setChecked(guess.x_is_kinetic)

    def _accept(self) -> None:
        if self.df is None or self.df.shape[1] < 2 or len(self.df) < 4:
            self.preview.setToolTip("유효한 데이터가 없습니다")
            return
        hv = self.hv_combo.currentData()
        mapping = importer.ColumnMapping(
            x_col=self.x_combo.currentIndex(),
            y_col=self.y_combo.currentIndex(),
            x_is_kinetic=self.ke_check.isChecked(),
            photon_energy=float(hv if hv is not None else self.hv_spin.value()),
        )
        if self.is_excel:
            sheets = self._checked_sheets() or ([self._current_sheet()] if self._current_sheet() else [])
            regions = []
            for s in sheets:
                df = self._sheet_cache[s]
                if df is None or df.shape[1] < 2 or len(df) < 4:
                    continue
                # reuse the dialog's column choice when it fits this sheet, else auto
                if max(mapping.x_col, mapping.y_col) < df.shape[1]:
                    m = importer.ColumnMapping(mapping.x_col, mapping.y_col,
                                               mapping.x_is_kinetic, mapping.photon_energy)
                else:
                    m = importer.guess_mapping(df)
                name = s if len(sheets) > 1 else (self.name_edit.text().strip() or s)
                regions.append(importer.to_region(df, m, name=name, source=str(self.path)))
            if not regions:
                self.preview.setToolTip("선택된 시트에 유효한 데이터가 없습니다")
                return
            self.result_regions = regions
            self.result_region = regions[0]
        else:
            fallback = "Pasted data" if self.paste_mode else self.path.stem
            region = importer.to_region(
                self.df, mapping, name=self.name_edit.text().strip() or fallback,
                source="clipboard" if self.paste_mode else str(self.path),
            )
            self.result_regions = [region]
            self.result_region = region
        self.accept()
