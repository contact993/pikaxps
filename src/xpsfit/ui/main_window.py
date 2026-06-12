"""Main window: region list | interactive plot | peak table | refdb/help/quantify docks."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDoubleSpinBox, QFileDialog, QHBoxLayout,
    QInputDialog, QLabel, QListWidget, QListWidgetItem, QMainWindow, QMenu,
    QMessageBox, QPushButton, QTabWidget, QVBoxLayout, QWidget, QDockWidget,
)

from .. import APP_NAME, __version__
from ..core import fitting
from ..core.session import EXTENSION, Session
from ..core.spectrum import BACKGROUND_TYPES, Region
from ..io import export
from .dialogs import BatchFitDialog
from .help_panel import HelpPanel
from .import_wizard import ImportWizard
from .peak_table import PeakTable
from .plot_widget import SpectrumPlot, height_to_area
from .quantify_panel import QuantifyPanel
from .refdb_panel import RefDbPanel

BG_LABELS = {
    "NONE": "None", "LINEAR": "Linear", "SHIRLEY": "Shirley",
    "SHIRLEY_LINEAR": "Shirley + Linear", "TOUGAARD": "Tougaard (U2)",
}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} {__version__}")
        self.resize(1380, 860)
        self.session = Session()
        self._current = -1

        # --- central: controls + plot ---
        central = QWidget()
        v = QVBoxLayout(central)
        v.setContentsMargins(8, 8, 8, 8)
        v.setSpacing(8)
        controls = QHBoxLayout()
        controls.setSpacing(8)
        controls.addWidget(QLabel("Background:"))
        self.bg_combo = QComboBox()
        for kind in BACKGROUND_TYPES:
            self.bg_combo.addItem(BG_LABELS[kind], kind)
        self.bg_combo.setCurrentText(BG_LABELS["SHIRLEY"])
        self.bg_combo.setToolTip("백그라운드 모델 — 선택하면 Help 패널에 설명이 표시됩니다")
        self.bg_combo.setStatusTip("백그라운드 종류 선택 (Shirley가 기본 — 자세한 설명은 도움말 탭)")
        self.bg_combo.currentIndexChanged.connect(self._bg_kind_changed)
        controls.addWidget(self.bg_combo)

        self.slope_spin = QDoubleSpinBox()
        self.slope_spin.setRange(-1e6, 1e6)
        self.slope_spin.setDecimals(2)
        self.slope_spin.setPrefix("slope ")
        self.slope_spin.setToolTip("Shirley+Linear의 선형 기울기 (counts/eV), 0 = 순수 Shirley")
        self.slope_spin.valueChanged.connect(self._bg_params_changed)
        self.slope_spin.setVisible(False)
        controls.addWidget(self.slope_spin)

        self.tg_b = QDoubleSpinBox()
        self.tg_b.setRange(0.0, 1e5)
        self.tg_b.setDecimals(1)
        self.tg_b.setPrefix("B ")
        self.tg_b.setToolTip("Tougaard B (eV²) — 0이면 고BE 끝점에 맞춰 자동 스케일")
        self.tg_b.valueChanged.connect(self._bg_params_changed)
        self.tg_b.setVisible(False)
        self.tg_c = QDoubleSpinBox()
        self.tg_c.setRange(1.0, 1e5)
        self.tg_c.setDecimals(0)
        self.tg_c.setValue(1643.0)
        self.tg_c.setPrefix("C ")
        self.tg_c.setToolTip("Tougaard C (eV²), universal = 1643")
        self.tg_c.valueChanged.connect(self._bg_params_changed)
        self.tg_c.setVisible(False)
        controls.addWidget(self.tg_b)
        controls.addWidget(self.tg_c)

        self.btn_fit_bg = QPushButton("Fit BG")
        self.btn_fit_bg.setToolTip(
            "백그라운드만 데이터에 먼저 맞춥니다 (피크 추가 전 1단계).\n"
            "Tougaard: B를 자동 결정 · Shirley/Linear: 끝점으로 자동 결정(세로선 조절)")
        self.btn_fit_bg.setStatusTip("Fit BG: 피크를 넣기 전에 백그라운드만 먼저 데이터에 맞춥니다")
        self.btn_fit_bg.clicked.connect(self._fit_bg)
        controls.addWidget(self.btn_fit_bg)

        self.bg_active_check = QCheckBox("BG 동시 fit")
        self.bg_active_check.setToolTip(
            "Active Shirley (Sherwood 방식): 백그라운드를 피크 모델에서 유도해 피크와 함께 최적화합니다.\n"
            "노이즈와 창 안의 다른 구조에 덜 민감 — 일반 Shirley로 백그라운드가 이상할 때 켜 보세요.")
        self.bg_active_check.setStatusTip("BG 동시 fit: Fit Region 때 Shirley 백그라운드를 피크와 함께 최적화")
        self.bg_active_check.toggled.connect(self._bg_active_toggled)
        controls.addWidget(self.bg_active_check)

        self.btn_reset_range = QPushButton("↔ Range reset")
        self.btn_reset_range.setToolTip("백그라운드/fitting 범위를 전체 데이터로 되돌립니다 (자르기 취소)")
        self.btn_reset_range.setStatusTip("Range reset: 잘라낸 범위를 취소하고 전체 데이터로 복귀")
        self.btn_reset_range.clicked.connect(self._reset_range)
        controls.addWidget(self.btn_reset_range)
        controls.addStretch(1)

        self.btn_fit_peak = QPushButton("Optimise Peak")
        self.btn_fit_peak.setToolTip("선택한 피크만 최적화 (나머지는 고정) — XPSPEAK의 Optimise Peak")
        self.btn_fit_peak.setStatusTip("Optimise Peak: 테이블에서 선택한 피크 하나만 최적화")
        self.btn_fit_peak.clicked.connect(self._fit_selected_peak)
        self.btn_fit = QPushButton("⚡ Fit Region")
        self.btn_fit.setObjectName("primary")
        self.btn_fit.setToolTip("현재 region의 모든 피크를 constraint대로 최적화 (수렴까지 자동 반복)")
        self.btn_fit.setStatusTip("Fit Region: 모든 피크를 수렴할 때까지 반복 최적화")
        self.btn_fit.clicked.connect(self._fit_region)
        self.btn_fit_all = QPushButton("Fit All")
        self.btn_fit_all.setToolTip("모든 region을 순서대로 최적화 — XPSPEAK의 Optimise All Regions")
        self.btn_fit_all.setStatusTip("Fit All: 모델이 있는 모든 region을 차례로 최적화")
        self.btn_fit_all.clicked.connect(self._fit_all)
        self.btn_diagnose = QPushButton("🔍 진단")
        self.btn_diagnose.setToolTip(
            "Fitting 종합 감사 — 리뷰어가 보는 항목을 자동 점검합니다:\n"
            "· FWHM 물리성 / 파라미터가 경계에 붙었는지\n"
            "· 각 피크의 BE를 레퍼런스 DB와 대조 (모르는 상태 지적)\n"
            "· doublet 짝 존재·간격·면적비 vs 이론값\n"
            "· 금속 상태의 비대칭 라인섀입 / satellite 누락\n"
            "· 과적합 신호 (겹친 피크, 1% 미만 성분, 면적 0)\n"
            "· C 1s 대전 보정 상태 · 잔차 통계(z + ΔBIC)")
        self.btn_diagnose.setStatusTip("진단: FWHM·레퍼런스·doublet·라인섀입·satellite·잔차를 종합 감사")
        self.btn_diagnose.clicked.connect(self._diagnose)
        self.btn_export = QPushButton("Export ▾")
        self.btn_export.setStatusTip("Export: 파라미터 CSV · 곡선 CSV · 전체 Excel · 논문용 그림 저장")
        export_menu = QMenu(self)
        export_menu.addAction("Peak parameters (CSV)…", self.export_params)
        export_menu.addAction("Fitted curves (CSV)…", self.export_curves)
        export_menu.addAction("All regions (Excel)…", self.export_excel)
        export_menu.addAction("Figure (PNG/SVG/PDF)…", self.export_figure)
        self.btn_export.setMenu(export_menu)
        for b in (self.btn_fit_peak, self.btn_fit, self.btn_fit_all,
                  self.btn_diagnose, self.btn_export):
            controls.addWidget(b)
        v.addLayout(controls)

        self.plot = SpectrumPlot()
        self.plot.backgroundRangeChanged.connect(self._bg_range_dragged)
        self.plot.peakDragged.connect(self._peak_dragged)
        v.addWidget(self.plot, stretch=1)
        self.setCentralWidget(central)
        # table row selection <-> bold component outline in the plot

        # --- left dock: regions ---
        self.region_list = QListWidget()
        self.region_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.region_list.currentRowChanged.connect(self._region_selected)
        self.region_list.itemDoubleClicked.connect(self._rename_region)
        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(2, 2, 2, 2)
        ll.addWidget(self.region_list)
        lb = QHBoxLayout()
        b_imp = QPushButton("＋ Import")
        b_imp.setStatusTip("Import: 데이터 파일(.dat/.txt/.csv/.xlsx/.xls/.vms)을 불러옵니다")
        b_imp.clicked.connect(self.import_data)
        b_paste = QPushButton("📋 Paste")
        b_paste.setToolTip("클립보드의 표 데이터(엑셀에서 복사한 BE/강도 열)를 새 region으로")
        b_paste.setStatusTip("Paste: 엑셀에서 복사한 데이터를 붙여넣어 region 생성 (⌘⇧V)")
        b_paste.clicked.connect(self.paste_data)
        b_del = QPushButton("－")
        b_del.setFixedWidth(36)
        b_del.setToolTip("선택한 region 삭제")
        b_del.clicked.connect(self._remove_region)
        lb.addWidget(b_imp)
        lb.addWidget(b_paste)
        lb.addWidget(b_del)
        ll.addLayout(lb)

        # --- BE shift (대전 보정): ±값을 정해 전체/선택 region에 일괄 적용 ---
        shift_label = QLabel("BE Shift (대전 보정)")
        shift_label.setProperty("class", "subtle")
        ll.addWidget(shift_label)
        sr1 = QHBoxLayout()
        self.shift_spin = QDoubleSpinBox()
        self.shift_spin.setRange(-50.0, 50.0)
        self.shift_spin.setDecimals(2)
        self.shift_spin.setSingleStep(0.05)
        self.shift_spin.setSuffix(" eV")
        self.shift_spin.setToolTip("적용할 시프트 (+면 고BE 쪽으로). 예: C-C가 285.10에 나왔으면 -0.30")
        sr1.addWidget(self.shift_spin, stretch=1)
        b_auto = QPushButton("C-C→284.8")
        b_auto.setToolTip("fitting된 adventitious C-C 피크(284.8 근처, 최대 면적)를 찾아\n필요한 시프트를 자동 계산해 채웁니다. C 1s를 먼저 피크분리하세요.")
        b_auto.setStatusTip("C-C→284.8: fitting된 C-C 피크로부터 필요한 시프트를 자동 계산")
        b_auto.clicked.connect(self._auto_shift_from_c1s)
        sr1.addWidget(b_auto)
        ll.addLayout(sr1)
        sr2 = QHBoxLayout()
        self.shift_all_check = QCheckBox("전체 적용")
        self.shift_all_check.setChecked(True)
        self.shift_all_check.setToolTip("끄면 위 목록에서 선택(⌘클릭으로 복수 선택)한 region에만 적용")
        sr2.addWidget(self.shift_all_check)
        b_shift = QPushButton("Shift 적용")
        b_shift.setStatusTip("Shift 적용: 위의 ± 값을 전체(또는 선택한) region의 BE축에 적용")
        b_shift.clicked.connect(self._apply_shift)
        sr2.addWidget(b_shift, stretch=1)
        ll.addLayout(sr2)

        dock_regions = QDockWidget("Regions", self)
        dock_regions.setWidget(left)
        dock_regions.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock_regions)

        # --- bottom dock: peak table ---
        self.peak_table = PeakTable()
        self.peak_table.modelChanged.connect(self._model_edited)
        self.peak_table.peakSelected.connect(self.plot.highlight_component)
        dock_table = QDockWidget("Peaks", self)
        dock_table.setWidget(self.peak_table)
        dock_table.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dock_table)

        # --- right dock: refdb / help / quantify ---
        self.refdb_panel = RefDbPanel()
        self.refdb_panel.guidesRequested.connect(self.plot.show_guides)
        self.refdb_panel.guidesCleared.connect(self.plot.clear_guides)
        self.refdb_panel.insertPeaks.connect(self._insert_peaks)
        self.refdb_panel.index_offset_provider = lambda: len(self._region().peaks) if self._region() else 0
        self.refdb_panel.area_unit_provider = self._area_unit
        self.help_panel = HelpPanel()
        self.quantify_panel = QuantifyPanel()
        tabs = QTabWidget()
        tabs.addTab(self.refdb_panel, "Reference DB")
        tabs.addTab(self.help_panel, "도움말")
        tabs.addTab(self.quantify_panel, "Quantify")
        self.right_tabs = tabs
        dock_right = QDockWidget("Reference / Help", self)
        dock_right.setWidget(tabs)
        dock_right.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock_right)

        # sensible startup proportions: roomy DB panel, compact region list
        self.resizeDocks([dock_regions, dock_right], [190, 420], Qt.Orientation.Horizontal)
        self.resizeDocks([dock_table], [250], Qt.Orientation.Vertical)

        self._build_menu()
        self.statusBar().showMessage("Import data to begin — File ▸ Import Data…")

    # ---------- menu ----------

    def _build_menu(self) -> None:
        m_file = self.menuBar().addMenu("&File")
        self._add_action(m_file, "Import Data…", self.import_data, QKeySequence.StandardKey.Open)
        self._add_action(m_file, "Paste Data (클립보드)…", self.paste_data, "Ctrl+Shift+V")
        self._add_action(m_file, "Open Project…", self.open_project)
        self._add_action(m_file, "Save Project", self.save_project, QKeySequence.StandardKey.Save)
        self._add_action(m_file, "Save Project As…", lambda: self.save_project(force_dialog=True))
        m_file.addSeparator()
        m_export = m_file.addMenu("Export")
        self._add_action(m_export, "Peak parameters (CSV)…", self.export_params)
        self._add_action(m_export, "Fitted curves (CSV)…", self.export_curves)
        self._add_action(m_export, "All regions (Excel)…", self.export_excel)
        self._add_action(m_export, "Figure (PNG/SVG/PDF)…", self.export_figure)
        m_file.addSeparator()
        self._add_action(m_file, "Quit", self.close, QKeySequence.StandardKey.Quit)

        m_tools = self.menuBar().addMenu("&Tools")
        self._add_action(m_tools, "Batch Fit (여러 파일 동일 모델)…", self.batch_fit)

        m_help = self.menuBar().addMenu("&Help")
        self._add_action(m_help, "권장 Fitting 절차", lambda: self._show_help("workflow"))
        self._add_action(m_help, "백그라운드 설명", lambda: self._show_help("background"))
        self._add_action(m_help, "About", self._about)

    def _add_action(self, menu, text, slot, shortcut=None) -> QAction:
        act = QAction(text, self)
        if shortcut:
            act.setShortcut(shortcut)
        act.triggered.connect(slot)
        menu.addAction(act)
        return act

    # ---------- region helpers ----------

    def _region(self) -> Region | None:
        if 0 <= self._current < len(self.session.regions):
            return self.session.regions[self._current]
        return None

    def _area_unit(self) -> float:
        r = self._region()
        if r is None or r.y.size == 0:
            return 1000.0
        return max(float(r.y.max() - r.y.min()), 10.0) * 1.5

    def _refresh_region_list(self, select: int | None = None) -> None:
        self.region_list.blockSignals(True)
        self.region_list.clear()
        for r in self.session.regions:
            text = r.name
            if abs(r.be_shift) > 1e-9:
                text += f"  ({r.be_shift:+.2f} eV)"
            item = QListWidgetItem(text, self.region_list)
            item.setToolTip(f"{r.name} — 적용된 시프트 {r.be_shift:+.2f} eV"
                            if abs(r.be_shift) > 1e-9 else r.name)
        self.region_list.blockSignals(False)
        if select is not None and 0 <= select < len(self.session.regions):
            self.region_list.setCurrentRow(select)
        elif self.session.regions:
            self.region_list.setCurrentRow(0)
        else:
            self._region_selected(-1)

    def _region_selected(self, row: int) -> None:
        self._current = row
        region = self._region()
        self.plot.clear_guides()
        self.plot.set_region(region)
        self.peak_table.set_region(region)
        if region is not None:
            self.bg_combo.blockSignals(True)
            idx = self.bg_combo.findData(region.background.kind)
            self.bg_combo.setCurrentIndex(max(0, idx))
            self.bg_combo.blockSignals(False)
            self._sync_bg_param_widgets(region)
            self.refdb_panel.select_for_region(region.name)
        self.quantify_panel.set_session(self.session)

    def _rename_region(self, item) -> None:
        region = self._region()
        if region is None:
            return
        name, ok = QInputDialog.getText(self, "Rename region", "이름 (예: Ni 2p):", text=region.name)
        if ok and name.strip():
            region.name = name.strip()
            self._refresh_region_list(select=self._current)

    def _remove_region(self) -> None:
        if self._region() is None:
            return
        del self.session.regions[self._current]
        self._refresh_region_list()

    # ---------- background ----------

    def _sync_bg_param_widgets(self, region: Region) -> None:
        kind = region.background.kind
        self.slope_spin.setVisible(kind == "SHIRLEY_LINEAR")
        self.tg_b.setVisible(kind == "TOUGAARD")
        self.tg_c.setVisible(kind == "TOUGAARD")
        self.bg_active_check.setVisible(kind == "SHIRLEY")
        self.bg_active_check.blockSignals(True)
        self.bg_active_check.setChecked(region.background.active)
        self.bg_active_check.blockSignals(False)
        self.slope_spin.blockSignals(True)
        self.slope_spin.setValue(region.background.slope)
        self.slope_spin.blockSignals(False)
        self.tg_b.blockSignals(True)
        self.tg_b.setValue(region.background.tougaard_b)
        self.tg_b.blockSignals(False)
        self.tg_c.blockSignals(True)
        self.tg_c.setValue(region.background.tougaard_c)
        self.tg_c.blockSignals(False)

    def _bg_kind_changed(self) -> None:
        region = self._region()
        if region is None:
            return
        region.background.kind = self.bg_combo.currentData()
        self._sync_bg_param_widgets(region)
        self.help_panel.show_context("background")
        self.right_tabs.setCurrentWidget(self.help_panel)
        self.plot.set_region(region)
        self.peak_table.refresh()

    def _bg_params_changed(self) -> None:
        region = self._region()
        if region is None:
            return
        region.background.slope = self.slope_spin.value()
        region.background.tougaard_b = self.tg_b.value()
        region.background.tougaard_c = self.tg_c.value()
        self.plot.refresh_model()

    def _bg_active_toggled(self, on: bool) -> None:
        region = self._region()
        if region is None:
            return
        region.background.active = on
        self.plot.refresh_model()
        self.peak_table.refresh()

    def _reset_range(self) -> None:
        region = self._region()
        if region is None:
            return
        region.background.lo = None
        region.background.hi = None
        self.plot.set_region(region)
        self.peak_table.refresh()
        self.statusBar().showMessage("범위를 전체 데이터로 초기화했습니다", 4000)

    def _fit_bg(self) -> None:
        region = self._region()
        if region is None:
            return
        msg = fitting.fit_background(region)
        self._sync_bg_param_widgets(region)
        self.plot.refresh_model()
        self.peak_table.refresh()
        self.statusBar().showMessage(msg, 9000)

    def _bg_range_dragged(self, lo: float, hi: float) -> None:
        region = self._region()
        if region is None:
            return
        region.background.lo = lo
        region.background.hi = hi
        self.plot.refresh_model()
        self.peak_table.refresh()
        self.plot.zoom_to_window()

    # ---------- model edits ----------

    def _model_edited(self) -> None:
        self.plot.refresh_model()
        self.peak_table.refresh()
        self.quantify_panel.rebuild()

    def _insert_peaks(self, peaks: list) -> None:
        region = self._region()
        if region is None:
            QMessageBox.information(self, APP_NAME, "먼저 데이터를 import 하세요.")
            return
        region.peaks.extend(peaks)
        self._model_edited()
        self.statusBar().showMessage(f"{len(peaks)}개 피크 삽입됨 (constraint 포함)", 4000)

    def _peak_dragged(self, index: int, center: float, height: float) -> None:
        region = self._region()
        if region is None or index >= len(region.peaks):
            return
        p = region.peaks[index]
        if p.center.expr is None:
            i1, i2 = region.crop_indices()
            lo = max(p.center.min, float(region.x[i1]))
            hi = min(p.center.max, float(region.x[i2]))
            p.center.value = min(max(center, lo), hi)
        if p.area.expr is None:
            p.area.value = max(height_to_area(region, index, height), 0.0)
        self._model_edited()

    # ---------- fitting ----------

    def _fit_region(self) -> None:
        region = self._region()
        if region is None or not region.peaks:
            self.statusBar().showMessage("피크가 없습니다 — Reference DB에서 삽입하거나 Add peak", 4000)
            return
        self.setCursor(Qt.CursorShape.WaitCursor)
        try:
            res, rounds = fitting.fit_until_converged(region)
        finally:
            self.unsetCursor()
        self._model_edited()
        self.statusBar().showMessage(
            f"Fit {'OK' if res.success else 'FAILED'} — {rounds} round(s), "
            f"reduced χ² = {res.redchi:.4g} · {res.message}", 10000)

    def _fit_selected_peak(self) -> None:
        region = self._region()
        row = self.peak_table.table.currentRow()
        if region is None or row < 0 or row >= len(region.peaks):
            self.statusBar().showMessage("피크 테이블에서 최적화할 피크를 선택하세요", 4000)
            return
        res, rounds = fitting.fit_until_converged(region, only_peak=row, max_rounds=4)
        self._model_edited()
        self.statusBar().showMessage(f"Peak {row} optimised — reduced χ² = {res.redchi:.4g}", 6000)

    def _diagnose(self) -> None:
        """Comprehensive fit audit: physics + literature + statistics."""
        from ..core import audit as audit_mod
        region = self._region()
        if region is None or not region.peaks:
            self.statusBar().showMessage("진단하려면 먼저 피크 모델을 만들고 fitting하세요", 6000)
            return
        self.setCursor(Qt.CursorShape.WaitCursor)
        try:
            report = audit_mod.audit(region)
        finally:
            self.unsetCursor()
        d = report.diagnosis
        if d is not None and d.suspect_be is not None:
            self.plot.show_guides([(d.suspect_be, "진단: 미설명 구조")])
        self._show_audit_dialog(region.name, report)
        bad, warn, ok = report.counts()
        self.statusBar().showMessage(f"진단 완료 — 문제 {bad} · 확인 필요 {warn} · 통과 {ok}", 9000)

    def _show_audit_dialog(self, region_name: str, report) -> None:
        from PySide6.QtWidgets import QDialogButtonBox, QTextBrowser, QVBoxLayout

        icons = {"bad": "✖", "warn": "⚠", "ok": "✓", "info": "ℹ"}
        colors = {"bad": "#c0392b", "warn": "#b07d12", "ok": "#1e8e4e", "info": "#5b6b7e"}
        order = {"bad": 0, "warn": 1, "info": 2, "ok": 3}
        bad, warn, ok = report.counts()
        rows = []
        for f in sorted(report.findings, key=lambda f: order[f.severity]):
            rows.append(
                f"<tr><td style='color:{colors[f.severity]}; font-weight:700; padding:4px 8px 4px 0;'>"
                f"{icons[f.severity]}</td>"
                f"<td style='color:#5b6b7e; padding:4px 10px 4px 0; white-space:nowrap;'>[{f.topic}]</td>"
                f"<td style='padding:4px 0;'>{f.message}</td></tr>")
        html = (
            f"<h3 style='margin:0 0 4px 0;'>Fitting 진단 — {region_name}</h3>"
            f"<p style='color:#5b6b7e; margin:0 0 10px 0;'>"
            f"<b style='color:{colors['bad']}'>문제 {bad}</b> · "
            f"<b style='color:{colors['warn']}'>확인 필요 {warn}</b> · "
            f"<b style='color:{colors['ok']}'>통과 {ok}</b></p>"
            f"<table style='border-collapse:collapse;'>{''.join(rows)}</table>"
            f"<p style='color:#5b6b7e; font-size:12px; margin-top:12px;'>기준: Biesinger "
            f"<i>Appl. Surf. Sci.</i> 257 (2011), Baer <i>JVST A</i> 37 (2019) 보고 권고 + BIC 모델 선택</p>")
        dlg = QDialog(self)
        dlg.setWindowTitle(f"진단 — {region_name}")
        dlg.resize(720, 480)
        lay = QVBoxLayout(dlg)
        browser = QTextBrowser()
        browser.setHtml(html)
        lay.addWidget(browser)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(dlg.reject)
        buttons.accepted.connect(dlg.accept)
        buttons.clicked.connect(lambda *_: dlg.accept())
        lay.addWidget(buttons)
        dlg.exec()

    def _fit_all(self) -> None:
        self.setCursor(Qt.CursorShape.WaitCursor)
        try:
            n = 0
            for r in self.session.regions:
                if r.peaks:
                    fitting.fit_until_converged(r)
                    n += 1
        finally:
            self.unsetCursor()
        self._model_edited()
        self.statusBar().showMessage(f"{n}개 region 최적화 완료", 6000)

    # ---------- file actions ----------

    def import_data(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Import data", "",
            "XPS data (*.dat *.txt *.csv *.xlsx *.xls *.vms);;All files (*)")
        if not path:
            return
        if Path(path).suffix.lower() == ".vms":
            from ..io.vamas_io import load_vamas
            try:
                regions = load_vamas(path)
            except Exception as e:  # noqa: BLE001
                QMessageBox.warning(self, APP_NAME, f"VAMAS 읽기 실패: {e}")
                return
            self.session.regions.extend(regions)
            self._refresh_region_list(select=len(self.session.regions) - 1)
            return
        wizard = ImportWizard(path, self)
        if wizard.exec() == QDialog.DialogCode.Accepted and wizard.result_regions:
            self.session.regions.extend(wizard.result_regions)
            self._refresh_region_list(select=len(self.session.regions) - len(wizard.result_regions))
            if len(wizard.result_regions) > 1:
                self.statusBar().showMessage(
                    f"{len(wizard.result_regions)}개 시트를 region으로 가져왔습니다", 6000)

    def paste_data(self) -> None:
        """New region from clipboard table data (e.g. two columns copied in Excel)."""
        wizard = ImportWizard(None, self)
        if wizard.exec() == QDialog.DialogCode.Accepted and wizard.result_regions:
            self.session.regions.extend(wizard.result_regions)
            self._refresh_region_list(select=len(self.session.regions) - 1)

    def open_project(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open project", "",
                                              f"XPSFit project (*{EXTENSION})")
        if not path:
            return
        try:
            self.session = Session.load(path)
        except Exception as e:  # noqa: BLE001
            QMessageBox.warning(self, APP_NAME, f"프로젝트 열기 실패: {e}")
            return
        self._refresh_region_list()
        self.statusBar().showMessage(f"열림: {path}", 5000)

    def save_project(self, force_dialog: bool = False) -> None:
        path = self.session.path
        if path is None or force_dialog:
            p, _ = QFileDialog.getSaveFileName(self, "Save project", "project" + EXTENSION,
                                               f"XPSFit project (*{EXTENSION})")
            if not p:
                return
            path = p
        saved = self.session.save(path)
        self.statusBar().showMessage(f"저장됨: {saved}", 5000)

    def export_params(self) -> None:
        region = self._region()
        if region is None:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export parameters",
                                              f"{region.name}_params.csv", "CSV (*.csv)")
        if path:
            export.export_params_csv(region, path)

    def export_curves(self) -> None:
        region = self._region()
        if region is None:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export curves",
                                              f"{region.name}_curves.csv", "CSV (*.csv)")
        if path:
            export.export_curves_csv(region, path)

    def export_excel(self) -> None:
        if not self.session.regions:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export Excel", "xpsfit_results.xlsx",
                                              "Excel (*.xlsx)")
        if path:
            export.export_excel(self.session.regions, path)

    def export_figure(self) -> None:
        region = self._region()
        if region is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export figure", f"{region.name}.png",
            "PNG (*.png);;SVG (*.svg);;PDF (*.pdf)")
        if path:
            export.save_figure(region, path)
            self.statusBar().showMessage(f"Figure 저장됨: {path}", 5000)

    # ---------- tools ----------

    def _auto_shift_from_c1s(self) -> None:
        """Fill the shift spinbox from the fitted adventitious C-C peak."""
        best = None
        for r in self.session.regions:
            for p in r.peaks:
                if 282.5 <= p.center.value <= 287.5 and (best is None or p.area.value > best.area.value):
                    best = p
        if best is None:
            self.statusBar().showMessage(
                "fitting된 C 1s 피크가 없습니다 — C 1s region을 먼저 피크분리하세요", 7000)
            return
        delta = 284.8 - best.center.value
        self.shift_spin.setValue(delta)
        self.statusBar().showMessage(
            f"C-C {best.center.value:.2f} eV 기준 → {delta:+.2f} eV 계산됨. 'Shift 적용'을 누르세요", 9000)
        self.help_panel.show_context("charge")

    def _apply_shift(self) -> None:
        delta = self.shift_spin.value()
        if not self.session.regions or abs(delta) < 1e-9:
            return
        if self.shift_all_check.isChecked() or not self.region_list.selectedIndexes():
            targets = list(self.session.regions)
        else:
            rows = sorted({ix.row() for ix in self.region_list.selectedIndexes()})
            targets = [self.session.regions[i] for i in rows if i < len(self.session.regions)]
        for r in targets:
            r.shift_be(delta)
        current = self._current
        self._refresh_region_list(select=current)
        self.statusBar().showMessage(f"{len(targets)}개 region에 {delta:+.2f} eV 적용됨", 7000)

    def batch_fit(self) -> None:
        region = self._region()
        if region is None or not region.peaks:
            QMessageBox.information(self, APP_NAME,
                                    "현재 region에 fitting 모델이 있어야 합니다 (템플릿으로 사용).")
            return
        BatchFitDialog(region, self).exec()

    def _show_help(self, key: str) -> None:
        self.help_panel.show_context(key)
        self.right_tabs.setCurrentWidget(self.help_panel)

    def _about(self) -> None:
        QMessageBox.about(
            self, APP_NAME,
            f"<b>{APP_NAME} {__version__}</b><br>"
            "XPS peak fitting — XPSPEAK 워크플로 + 레퍼런스 DB + 한국어 가이드<br>"
            "엔진: lmfit / scipy · UI: PySide6 + pyqtgraph<br><br>"
            "BE 데이터베이스 출처: Biesinger et al., Moulder Handbook, NIST SRD 20")
