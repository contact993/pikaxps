"""Quantification panel: per-region areas / RSF -> atomic %."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHeaderView, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from .. import refdb
from ..core.quantify import QuantEntry, atomic_percent, region_total_area
from ..core.session import Session
from .refdb_panel import guess_element_orbital


class QuantifyPanel(QWidget):
    HEADERS = ["Region", "Element", "Area (Σpeaks)", "RSF", "Atomic %"]

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        note = QLabel("RSF 기본값 = Scofield 단면적 (C 1s=1). 장비 RSF가 있으면 셀에서 직접 수정 후 다시 계산.")
        note.setWordWrap(True)
        note.setProperty("class", "note")
        layout.addWidget(note)
        self.table = QTableWidget(0, len(self.HEADERS))
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(30)
        layout.addWidget(self.table, stretch=1)
        self.btn = QPushButton("다시 계산")
        self.btn.clicked.connect(self.recompute)
        layout.addWidget(self.btn)
        self.session: Session | None = None

    def set_session(self, session: Session) -> None:
        self.session = session
        self.rebuild()

    def rebuild(self) -> None:
        regions = [r for r in (self.session.regions if self.session else []) if r.peaks]
        self.table.setRowCount(len(regions))
        for i, r in enumerate(regions):
            hit = guess_element_orbital(r.name)
            rsf = 1.0
            label = "?"
            if hit:
                el, orb = hit
                rsf = refdb.elements()[el][orb].get("rsf", 1.0)
                label = f"{el} {orb}"
            self._set(i, 0, r.name, editable=False)
            self._set(i, 1, label, editable=False)
            self._set(i, 2, f"{region_total_area(r):.1f}", editable=False)
            self._set(i, 3, f"{rsf}", editable=True)
            self._set(i, 4, "", editable=False)
        self.recompute()

    def recompute(self) -> None:
        regions = [r for r in (self.session.regions if self.session else []) if r.peaks]
        entries = []
        for i, r in enumerate(regions):
            try:
                rsf = float(self.table.item(i, 3).text())
            except (ValueError, AttributeError):
                rsf = 1.0
            entries.append(QuantEntry(r.name, r.name, region_total_area(r), rsf))
            self._set(i, 2, f"{region_total_area(r):.1f}", editable=False)
        for i, pct in enumerate(atomic_percent(entries)):
            self._set(i, 4, f"{pct:.1f}", editable=False)

    def _set(self, row: int, col: int, text: str, editable: bool) -> None:
        item = QTableWidgetItem(text)
        flags = Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
        if editable:
            flags |= Qt.ItemFlag.ItemIsEditable
        item.setFlags(flags)
        self.table.setItem(row, col, item)
