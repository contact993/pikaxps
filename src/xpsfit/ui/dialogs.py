"""Small dialogs: batch fitting. (Charge correction lives inline in the
Regions panel as the BE Shift control.)"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QFileDialog, QHBoxLayout, QLabel, QListWidget, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout,
)

from ..core import batch
from ..core.spectrum import Region
from ..io import importer


class BatchFitDialog(QDialog):
    """Apply the current region's model to a set of files and tabulate results."""

    def __init__(self, template: Region, parent=None):
        super().__init__(parent)
        self.template = template
        self.setWindowTitle(f"Batch fit — 모델: {template.name}")
        self.resize(720, 480)
        self.result_df = None
        self.result_items: list[batch.BatchItem] = []

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            "현재 region의 백그라운드 설정과 피크 모델(constraint 포함)을 여러 파일에 동일 적용합니다.\n"
            "파일은 자동 감지로 파싱됩니다 (열 구조가 같은 export 파일에 사용)."))
        row = QHBoxLayout()
        self.file_list = QListWidget()
        row.addWidget(self.file_list, stretch=1)
        col = QVBoxLayout()
        btn_add = QPushButton("파일 추가…")
        btn_add.clicked.connect(self._add_files)
        btn_run = QPushButton("실행")
        btn_run.clicked.connect(self._run)
        col.addWidget(btn_add)
        col.addWidget(btn_run)
        col.addStretch(1)
        row.addLayout(col)
        layout.addLayout(row)
        self.table = QTableWidget(0, 0)
        layout.addWidget(self.table, stretch=1)
        btn_export = QPushButton("결과 CSV 저장…")
        btn_export.clicked.connect(self._export)
        layout.addWidget(btn_export)

    def _add_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self, "Batch files", "", "Data (*.dat *.txt *.csv *.xlsx);;All files (*)")
        for f in files:
            self.file_list.addItem(f)

    def _load(self, path: str) -> Region | None:
        p = Path(path)
        try:
            if importer.is_excel_file(p):
                df = importer.load_excel(p)
            else:
                df = importer.load_table(importer.sniff(p))
            mapping = importer.guess_mapping(df)
            return importer.to_region(df, mapping, name=p.stem, source=str(p))
        except Exception:  # noqa: BLE001
            return None

    def _run(self) -> None:
        targets = []
        for i in range(self.file_list.count()):
            r = self._load(self.file_list.item(i).text())
            if r is not None:
                targets.append(r)
        if not targets:
            return
        self.result_items, df = batch.run_batch(self.template, targets)
        self.result_df = df
        self.table.setRowCount(len(df))
        self.table.setColumnCount(len(df.columns))
        self.table.setHorizontalHeaderLabels([str(c) for c in df.columns])
        for r in range(len(df)):
            for c in range(len(df.columns)):
                self.table.setItem(r, c, QTableWidgetItem(str(df.iat[r, c])))

    def _export(self) -> None:
        if self.result_df is None:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save results", "batch_results.csv", "CSV (*.csv)")
        if path:
            self.result_df.to_csv(path, index=False)
