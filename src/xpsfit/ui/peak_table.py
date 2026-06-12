"""Peak parameter table (XPSPEAK-style) + per-peak constraint dialog."""
from __future__ import annotations

import math

import numpy as np
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from .. import refdb
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout,
    QGridLayout, QGroupBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from ..core import fitting
from ..core.spectrum import PEAK_SHAPES, ParamSpec, Peak, Region

PARAM_COLS = [("center", "Center (eV)"), ("fwhm", "FWHM (eV)"), ("area", "Area"),
              ("mix", "%L-G"), ("asym", "Asym")]
PARAM_LABELS = {"center": "Center", "fwhm": "FWHM", "area": "Area",
                "mix": "%L-G", "asym": "Asym"}


class ConstraintDialog(QDialog):
    """XPSPEAK's peak form: value / fix / bounds / relation per parameter."""

    def __init__(self, peak: Peak, peak_index: int, n_peaks: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Peak {peak_index} constraints — {peak.label or 'unnamed'}")
        self.peak = peak
        layout = QVBoxLayout(self)
        hint = QLabel(
            f"이 피크의 번호는 <b>p{peak_index}</b>. 다른 피크 참조 예: "
            f"<code>p0_center + 1.18</code>, <code>p0_area * 0.5</code>, <code>p0_fwhm</code>"
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)
        self.editors: dict[str, dict] = {}
        grid = QGridLayout()
        for col, text in enumerate(["", "Value", "Vary", "Min", "Max", "Relation (expr)"]):
            grid.addWidget(QLabel(f"<b>{text}</b>"), 0, col)
        for row, (pname, label) in enumerate(PARAM_COLS, start=1):
            spec: ParamSpec = getattr(peak, pname)
            value = QLineEdit(f"{spec.value:.4g}")
            vary = QCheckBox()
            vary.setChecked(spec.vary)
            lo = QLineEdit("" if not math.isfinite(spec.min) else f"{spec.min:.4g}")
            hi = QLineEdit("" if not math.isfinite(spec.max) else f"{spec.max:.4g}")
            expr = QLineEdit(spec.expr or "")
            expr.setPlaceholderText("예: p0_fwhm")
            grid.addWidget(QLabel(label), row, 0)
            for col, w in enumerate((value, vary, lo, hi, expr), start=1):
                grid.addWidget(w, row, col)
            self.editors[pname] = {"value": value, "vary": vary, "min": lo, "max": hi, "expr": expr}
        layout.addLayout(grid)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                                   | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @staticmethod
    def _parse(text: str, default: float) -> float:
        try:
            return float(text)
        except ValueError:
            return default

    def apply(self) -> None:
        for pname, ed in self.editors.items():
            spec: ParamSpec = getattr(self.peak, pname)
            spec.value = self._parse(ed["value"].text(), spec.value)
            spec.vary = ed["vary"].isChecked()
            spec.min = self._parse(ed["min"].text(), -math.inf) if ed["min"].text().strip() else -math.inf
            spec.max = self._parse(ed["max"].text(), math.inf) if ed["max"].text().strip() else math.inf
            spec.expr = ed["expr"].text().strip() or None


class DoubletParamsDialog(QDialog):
    """Splitting/ratio for a doublet when the orbital isn't recognized."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Doublet 파라미터")
        form = QFormLayout(self)
        hint = QLabel("Region 이름에서 원소/오비탈을 인식하지 못해 직접 입력합니다.\n"
                      "(이름을 'Ir 4f'처럼 지으면 다음부터 자동입니다)")
        hint.setWordWrap(True)
        form.addRow(hint)
        self.split_spin = QDoubleSpinBox()
        self.split_spin.setRange(0.05, 60.0)
        self.split_spin.setDecimals(2)
        self.split_spin.setValue(1.18)
        self.split_spin.setSuffix(" eV")
        form.addRow("Spin-orbit splitting:", self.split_spin)
        self.ratio_combo = QComboBox()
        self.ratio_combo.setEditable(True)
        self.ratio_combo.addItems(["2:1", "3:2", "4:3"])
        form.addRow("면적비 (p 2:1 · d 3:2 · f 4:3):", self.ratio_combo)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                                   | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)


class SatelliteDialog(QDialog):
    """Pick the parent peak and the satellite offset."""

    def __init__(self, others: list, default_delta: float = 6.0, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Satellite 지정")
        form = QFormLayout(self)
        hint = QLabel("Satellite(shake-up 등)는 주피크보다 높은 BE에 나타나는 넓고 약한 피크입니다.\n"
                      "위치를 주피크에 묶고, 정량 시 면적을 주피크 화학종에 합산합니다.\n"
                      "전형적 Δ: Cu(II) ~8.5 · Ni(II) ~6.1 · Co(II) ~6.3 · π-π*(sp² C) ~6.6 eV")
        hint.setWordWrap(True)
        form.addRow(hint)
        self.parent_combo = QComboBox()
        for j, q in others:
            self.parent_combo.addItem(f"{q.label or f'Peak {j + 1}'}  ({q.center.value:.2f} eV)", j)
        form.addRow("주피크:", self.parent_combo)
        self.delta_spin = QDoubleSpinBox()
        self.delta_spin.setRange(0.5, 20.0)
        self.delta_spin.setDecimals(2)
        self.delta_spin.setValue(default_delta)
        self.delta_spin.setSuffix(" eV")
        form.addRow("주피크로부터 Δ (+고BE):", self.delta_spin)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                                   | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)


class PeakTable(QWidget):
    modelChanged = Signal()  # any parameter/peak-list change
    peakSelected = Signal(int)

    HEADERS = ["Type", "Label", "Shape", "Center", "FWHM", "Area", "Area %", "%L-G", "Asym", "Link", ""]
    KIND_LABEL = {"single": "단일", "doublet_main": "Doublet", "satellite": "Satellite"}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.region: Region | None = None
        self._updating = False

        self.table = QTableWidget(0, len(self.HEADERS))
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setMinimumSectionSize(58)
        self.table.verticalHeader().setVisible(True)
        self.table.verticalHeader().setDefaultSectionSize(32)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setWordWrap(False)
        self.table.cellChanged.connect(self._cell_changed)
        self.table.currentCellChanged.connect(lambda r, *_: self.peakSelected.emit(r) if r >= 0 else None)

        self.btn_add_doublet = QPushButton("＋ Doublet")
        self.btn_add_doublet.setToolTip(
            "spin-orbit 짝 피크를 한 번에 추가합니다 — 간격·면적비·FWHM이 이론값으로 자동 고정.\n"
            "p/d/f 오비탈의 주성분은 반드시 이걸로 추가하세요 (자유 피크 2개로 두면\n"
            "옵티마이저가 doublet 구조를 모른 채 제멋대로 배치합니다).")
        self.btn_add_doublet.clicked.connect(self._add_doublet)
        btn_add = QPushButton("＋ Peak")
        btn_add.setToolTip("구속 없는 단일 피크 추가 — satellite, s 오비탈, 기타 성분용.\n"
                           "p/d/f 주성분에는 ＋ Doublet을 쓰세요.")
        btn_add.setStatusTip("＋ Peak: 단일 자유 피크 추가 (satellite·s 오비탈용)")
        btn_add.clicked.connect(self._add_peak)
        btn_del = QPushButton("－ Delete")
        btn_del.setToolTip("선택한 피크 삭제 (다른 피크의 관계식 번호는 자동 보정)")
        btn_del.setStatusTip("－ Delete: 테이블에서 선택한 피크를 삭제합니다")
        btn_del.clicked.connect(self._delete_peak)
        btn_free = QPushButton("🔓 Free")
        btn_free.setToolTip("선택한 피크의 관계식·고정·범위 제한을 모두 해제합니다.\n"
                            "이론값(doublet 간격·비율 포함)이 데이터와 안 맞을 때 사용 —\n"
                            "해제 후에는 비율이 비물리적으로 갈 수 있으니 결과를 꼭 확인하세요.")
        btn_free.setStatusTip("🔓 Free: 선택한 피크의 관계식·고정·범위를 모두 해제 "
                              "(이론값이 데이터와 안 맞을 때 — 해제 내역은 여기 상태바에 표시됩니다)")
        btn_free.clicked.connect(self._free_peak)

        top = QHBoxLayout()
        top.setSpacing(6)
        top.addWidget(self.btn_add_doublet)
        top.addWidget(btn_add)
        top.addWidget(btn_del)
        top.addWidget(btn_free)
        top.addStretch(1)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 8)
        layout.setSpacing(6)
        layout.addLayout(top)
        layout.addWidget(self.table)

    # ---------- sync ----------

    def set_region(self, region: Region | None) -> None:
        self.region = region
        ctx = self._doublet_context()
        if ctx is None:
            self.btn_add_doublet.setEnabled(False)
            self.btn_add_doublet.setText("＋ Doublet")
            self.btn_add_doublet.setStatusTip(
                "Region 이름을 'Ir 4f'처럼 지으면 해당 오비탈의 doublet 추가가 활성화됩니다")
        else:
            el, orb, info = ctx
            self.btn_add_doublet.setEnabled(True)
            self.btn_add_doublet.setText(f"＋ {el} {orb} Doublet")
            self.btn_add_doublet.setStatusTip(
                f"＋ Doublet: {el} {orb} 짝 추가 — 간격 {info['spin_orbit_splitting_eV']} eV · "
                f"면적비 {info['doublet_area_ratio']} · FWHM 링크 자동 고정")
        self.refresh()

    def _doublet_context(self):
        if self.region is None:
            return None
        hit = refdb.guess_element_orbital(self.region.name)
        if not hit:
            return None
        info = refdb.elements()[hit[0]][hit[1]]
        if not info.get("spin_orbit_splitting_eV"):
            return None
        return hit[0], hit[1], info

    def refresh(self) -> None:
        self._updating = True
        try:
            region = self.region
            n = len(region.peaks) if region else 0
            self.table.setRowCount(n)
            if not region:
                return
            from .plot_widget import COMPONENT_COLORS
            fractions = fitting.area_fractions(region)
            for i, p in enumerate(region.peaks):
                self._make_type_combo(i, p)
                self._set_item(i, 1, p.label, editable=True)
                # match the component color used in the plot
                tint = QColor(COMPONENT_COLORS[i % len(COMPONENT_COLORS)])
                tint.setAlpha(55)
                self.table.item(i, 1).setBackground(tint)
                shape_combo = QComboBox()
                shape_combo.addItems(PEAK_SHAPES)
                shape_combo.setCurrentText(p.shape)
                shape_combo.currentTextChanged.connect(
                    lambda s, row=i: self._shape_changed(row, s))
                self.table.setCellWidget(i, 2, shape_combo)
                for col, (pname, _) in zip((3, 4, 5), PARAM_COLS[:3]):
                    spec = getattr(p, pname)
                    self._set_item(i, col, f"{spec.value:.3f}" if pname != "area" else f"{spec.value:.1f}",
                                   editable=spec.expr is None,
                                   tooltip=self._spec_tooltip(spec))
                self._set_item(i, 6, f"{fractions[i]:.1f}" if i < len(fractions) else "-", editable=False)
                self._set_item(i, 7, f"{p.mix.value:.0f}", editable=p.mix.expr is None,
                               tooltip="0 = Gaussian, 100 = Lorentzian")
                self._set_item(i, 8, f"{p.asym.value:.2f}", editable=p.asym.expr is None,
                               tooltip="GL_TAIL: 지수꼬리 길이(eV) / DONIACH: α")
                btn = QPushButton("🔗" if self._has_constraint(p) else "…")
                btn.setToolTip("값 고정 / 범위 / 다른 피크와의 관계식 설정")
                btn.setFixedWidth(40)
                btn.clicked.connect(lambda _=False, row=i: self._open_constraints(row))
                self.table.setCellWidget(i, 9, btn)
        finally:
            self._updating = False

    def _make_type_combo(self, row: int, p: Peak) -> None:
        combo = QComboBox()
        if p.kind == "doublet_partner":
            combo.addItem("└ 짝")
            combo.setEnabled(False)
            combo.setToolTip("Doublet 짝 — 간격·면적비·FWHM이 주피크에 묶여 있습니다.\n"
                             "풀려면 주피크를 '단일'로 바꾸거나 🔓 Free를 쓰세요.")
        else:
            combo.addItems(["단일", "Doublet", "Satellite"])
            combo.setCurrentText(self.KIND_LABEL.get(p.kind, "단일"))
            combo.setToolTip("이 피크의 역할:\n"
                             "· Doublet — spin-orbit 짝을 자동 생성 (간격·면적비·FWHM 고정)\n"
                             "· Satellite — 주피크에 위치를 묶고, 정량 시 면적을 주피크 화학종에 합산\n"
                             "· 단일 — 구속 없는 일반 피크")
            combo.currentTextChanged.connect(lambda t, r=row: self._type_changed(r, t))
        self.table.setCellWidget(row, 0, combo)

    def _partner_row(self, row: int) -> int | None:
        pat = f"p{row}_center"
        for j, q in enumerate(self.region.peaks):
            if j != row and q.kind == "doublet_partner" and pat in (q.center.expr or ""):
                return j
        return None

    def _fix_orphan_kinds(self) -> None:
        """After deletes/frees, partners/satellites whose ties were severed
        become plain singles; mains without partners lose doublet status."""
        peaks = self.region.peaks
        for i, q in enumerate(peaks):
            if q.kind in ("doublet_partner", "satellite") and not (q.center.expr or q.area.expr):
                q.kind = "single"
            if q.kind == "doublet_main" and self._partner_row(i) is None:
                q.kind = "single"

    def _type_changed(self, row: int, text: str) -> None:
        if self._updating or self.region is None or row >= len(self.region.peaks):
            return
        p = self.region.peaks[row]
        current = self.KIND_LABEL.get(p.kind, "단일")
        if text == current:
            return
        if text == "Doublet":
            self._convert_to_doublet(row)
        elif text == "Satellite":
            self._convert_to_satellite(row)
        else:
            self._convert_to_single(row)

    def _convert_to_single(self, row: int) -> None:
        from .. import refdb as _refdb
        p = self.region.peaks[row]
        if p.kind == "doublet_main":
            j = self._partner_row(row)
            if j is not None:
                del self.region.peaks[j]
                _refdb.reindex_exprs_after_delete(self.region.peaks, j)
            self._status(f"{p.label or f'Peak {row + 1}'}: doublet 해제 — 짝 피크를 제거했습니다")
        elif p.kind == "satellite":
            p.center.expr = None
            p.center.vary = True
            self._status(f"{p.label or f'Peak {row + 1}'}: satellite 해제 — 위치 구속을 풀었습니다")
        p.kind = "single"
        self._fix_orphan_kinds()
        self.modelChanged.emit()

    def _convert_to_doublet(self, row: int, split: float | None = None,
                            ratio_text: str | None = None) -> None:
        """Spawn the spin-orbit partner for an existing peak. Splitting/ratio
        come from the recognized orbital, or from the dialog (any element)."""
        from .. import refdb as _refdb
        p = self.region.peaks[row]
        if p.kind == "satellite":
            p.center.expr = None
            p.center.vary = True
        if split is None:
            ctx = self._doublet_context()
            if ctx is not None:
                _, _, info = ctx
                split = float(info["spin_orbit_splitting_eV"])
                ratio_text = info["doublet_area_ratio"]
            else:
                dlg = DoubletParamsDialog(self)
                if dlg.exec() != QDialog.DialogCode.Accepted:
                    self.refresh()
                    return
                split = dlg.split_spin.value()
                ratio_text = dlg.ratio_combo.currentText().strip() or "2:1"
        factor = _refdb.ratio_factor(ratio_text)
        partner = Peak.create(center=p.center.value + split, area=p.area.value * factor,
                              fwhm=p.fwhm.value, mix=p.mix.value,
                              label=f"{p.label or f'Peak {row + 1}'} 짝")
        partner.kind = "doublet_partner"
        partner.center = ParamSpec(value=p.center.value + split,
                                   expr=f"p{row}_center + {split:g}")
        partner.area = ParamSpec(value=p.area.value * factor,
                                 expr=f"p{row}_area * {factor:.6g}")
        partner.fwhm = ParamSpec(value=p.fwhm.value, expr=f"p{row}_fwhm")
        partner.mix = ParamSpec(value=p.mix.value, vary=False, min=0.0, max=100.0)
        p.kind = "doublet_main"
        self.region.peaks.append(partner)
        self.modelChanged.emit()
        self._status(f"{p.label or f'Peak {row + 1}'} → Doublet: 짝 생성 "
                     f"(간격 {split:g} eV · 면적비 {ratio_text} · FWHM 링크)")

    def _convert_to_satellite(self, row: int, parent: int | None = None,
                              delta: float | None = None) -> None:
        """Tie this peak to a parent: center = parent + Δ. Its area is counted
        with the parent species in quantification (shake-up intensity belongs
        to the same species)."""
        p = self.region.peaks[row]
        if p.kind == "doublet_main":
            self._convert_to_single(row)
            p = self.region.peaks[row]
        if parent is None:
            others = [(j, q) for j, q in enumerate(self.region.peaks) if j != row]
            if not others:
                self._status("Satellite로 지정하려면 주피크가 따로 있어야 합니다")
                self.refresh()
                return
            dlg = SatelliteDialog(others, default_delta=6.0, parent=self)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                self.refresh()
                return
            parent = dlg.parent_combo.currentData()
            delta = dlg.delta_spin.value()
        parent_peak = self.region.peaks[parent]
        p.kind = "satellite"
        p.center = ParamSpec(value=parent_peak.center.value + delta,
                             expr=f"p{parent}_center + {delta:g}")
        if p.fwhm.value < 2.0:
            p.fwhm.value = 2.8  # shake-up structures are broad
        if not p.label or p.label.startswith("Peak"):
            p.label = f"{parent_peak.label or f'Peak {parent + 1}'} satellite"
        self.modelChanged.emit()
        self._status(f"{p.label}: satellite 지정 — 위치 = 주피크 +{delta:g} eV, "
                     f"정량 시 면적은 주피크 화학종에 합산됩니다 (Δ는 🔗에서 수정/해제 가능)")

    @staticmethod
    def _has_constraint(p: Peak) -> bool:
        return any(s.expr or not s.vary for s in p.params().values())

    @staticmethod
    def _spec_tooltip(spec: ParamSpec) -> str:
        parts = []
        if spec.expr:
            parts.append(f"관계식: {spec.expr}")
        if not spec.vary and not spec.expr:
            parts.append("고정됨")
        if math.isfinite(spec.min) or math.isfinite(spec.max):
            parts.append(f"범위 [{spec.min:.4g}, {spec.max:.4g}]")
        return " · ".join(parts)

    def _set_item(self, row: int, col: int, text: str, editable: bool, tooltip: str = "") -> None:
        item = QTableWidgetItem(text)
        flags = Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
        if editable:
            flags |= Qt.ItemFlag.ItemIsEditable
        else:
            item.setForeground(Qt.GlobalColor.darkGray)
        item.setFlags(flags)
        if tooltip:
            item.setToolTip(tooltip)
        self.table.setItem(row, col, item)

    # ---------- edits ----------

    def _cell_changed(self, row: int, col: int) -> None:
        if self._updating or self.region is None or row >= len(self.region.peaks):
            return
        p = self.region.peaks[row]
        item = self.table.item(row, col)
        if item is None:
            return
        text = item.text().strip()
        try:
            if col == 1:
                p.label = text
            elif col == 3:
                p.center.value = float(text)
            elif col == 4:
                p.fwhm.value = float(text)
            elif col == 5:
                p.area.value = float(text)
            elif col == 7:
                p.mix.value = min(100.0, max(0.0, float(text)))
            elif col == 8:
                p.asym.value = float(text)
            else:
                return
        except ValueError:
            pass
        self.modelChanged.emit()

    def _shape_changed(self, row: int, shape: str) -> None:
        if self._updating or self.region is None:
            return
        p = self.region.peaks[row]
        p.shape = shape
        if shape in ("GL_TAIL", "DONIACH") and p.asym.value == 0.0:
            p.asym.value = 0.5 if shape == "GL_TAIL" else 0.1
            p.asym.vary = True
        self.modelChanged.emit()

    def _add_peak(self) -> None:
        if self.region is None or self.region.x.size == 0:
            return
        # new peaks live inside the background window, never outside it
        i1, i2 = self.region.crop_indices()
        xw = self.region.x[i1: i2 + 1]
        yw = self.region.y[i1: i2 + 1]
        center = float(xw[int(np.argmax(yw))]) if xw.size else float(self.region.x[0])
        span = float(yw.max() - yw.min()) if yw.size else 100.0
        peak = Peak.create(center=center, area=max(span, 10.0) * 1.5, fwhm=1.5,
                           label=f"Peak {len(self.region.peaks) + 1}")
        peak.center.min, peak.center.max = float(xw[0]), float(xw[-1])
        self.region.peaks.append(peak)
        self.modelChanged.emit()

    def _add_doublet(self) -> None:
        """Insert a spin-orbit pair (splitting/ratio/FWHM constrained) at the
        strongest position inside the background window."""
        ctx = self._doublet_context()
        if ctx is None or self.region is None or self.region.x.size == 0:
            return
        el, orb, info = ctx
        i1, i2 = self.region.crop_indices()
        xw = self.region.x[i1: i2 + 1]
        yw = self.region.y[i1: i2 + 1]
        center = float(xw[int(np.argmax(yw))]) if xw.size else float(self.region.x[0])
        span = float(yw.max() - yw.min()) if yw.size else 100.0
        pair = refdb.doublet_pair(el, orb, center, main_index=len(self.region.peaks),
                                  label=f"{el}", area=max(span, 10.0) * 1.5, fwhm=1.2)
        pair[0].center.min, pair[0].center.max = float(xw[0]), float(xw[-1])
        self.region.peaks.extend(pair)
        self.modelChanged.emit()
        self._status(f"＋ {el} {orb} doublet 추가됨 — 간격 {info['spin_orbit_splitting_eV']} eV · "
                     f"면적비 {info['doublet_area_ratio']} · FWHM 링크 고정. 핸들을 끌어 위치를 잡고 Fit 하세요.")

    def _delete_peak(self) -> None:
        row = self.table.currentRow()
        if self.region is None or row < 0 or row >= len(self.region.peaks):
            return
        del self.region.peaks[row]
        refdb.reindex_exprs_after_delete(self.region.peaks, row)
        self._fix_orphan_kinds()
        self.modelChanged.emit()

    def _status(self, text: str, msec: int = 9000) -> None:
        win = self.window()
        if hasattr(win, "statusBar"):
            win.statusBar().showMessage(text, msec)

    def _free_peak(self) -> None:
        """Drop every constraint on the selected peak (theory values don't
        always match real data — let the user release them in one click)."""
        import math
        row = self.table.currentRow()
        if self.region is None or row < 0 or row >= len(self.region.peaks):
            self._status("🔓 Free: 먼저 테이블에서 해제할 피크를 클릭해 선택하세요", 6000)
            return
        p = self.region.peaks[row]
        released = [PARAM_LABELS.get(n, n) for n, s in p.params().items() if s.expr]
        unfixed = [PARAM_LABELS.get(n, n) for n, s in p.params().items()
                   if not s.vary and not s.expr]
        for name, spec in p.params().items():
            spec.expr = None
            spec.vary = True
        p.center.min = p.center.value - 2.0
        p.center.max = p.center.value + 2.0
        p.fwhm.min, p.fwhm.max = 0.2, 6.0
        p.area.min, p.area.max = 0.0, math.inf
        p.mix.min, p.mix.max = 0.0, 100.0
        p.kind = "single"
        self._fix_orphan_kinds()
        self.modelChanged.emit()
        parts = []
        if released:
            parts.append(f"관계식 해제: {', '.join(released)}")
        if unfixed:
            parts.append(f"고정 해제: {', '.join(unfixed)}")
        parts.append(f"범위 확장: center {p.center.value:.2f}±2.0 eV, FWHM 0.2–6.0")
        self._status(f"🔓 {p.label or f'Peak {row + 1}'} — " + " · ".join(parts))

    def _open_constraints(self, row: int) -> None:
        if self.region is None or row >= len(self.region.peaks):
            return
        dlg = ConstraintDialog(self.region.peaks[row], row, len(self.region.peaks), self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            dlg.apply()
            self.modelChanged.emit()
