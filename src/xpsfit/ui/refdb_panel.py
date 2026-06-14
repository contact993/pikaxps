"""Reference DB panel: browse binding energies, show guide lines, insert
constrained peaks / doublets / recipes into the current region."""
from __future__ import annotations

import re

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QPushButton,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

from .. import refdb
from .i18n import current_language, t
from ..core.spectrum import Peak
from ..refdb import guess_element_orbital  # re-export (quantify_panel imports from here)


def _note(d: dict) -> str:
    """Localized note: English if the UI is English and a note_en exists, else Korean."""
    if current_language() == "en" and d.get("notes_en"):
        return d["notes_en"]
    return d.get("notes_ko", "")


class RefDbPanel(QWidget):
    guidesRequested = Signal(list)  # [(be, label)]
    guidesCleared = Signal()
    insertPeaks = Signal(list)  # list[Peak] ready to append to current region

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        row = QHBoxLayout()
        row.setSpacing(6)
        self.element_combo = QComboBox()
        self._rebuild_elements()
        self.element_combo.currentIndexChanged.connect(self._fill_states)
        row.addWidget(self.element_combo)
        self.search = QLineEdit()
        self.search.setPlaceholderText(t("Search states (e.g. oxide)", "상태 검색 (예: oxide)"))
        self.search.textChanged.connect(self._fill_states)
        row.addWidget(self.search)
        layout.addLayout(row)

        src = QLabel(t(
            "BE values are <b>literature references</b> — hover a state to see its source. "
            "Verify against the cited source before publication.",
            "BE 값은 <b>문헌 레퍼런스</b>입니다 — 각 상태에 마우스를 올리면 출처가 표시됩니다. "
            "출판 전 인용 원문으로 확인하세요."))
        src.setWordWrap(True)
        src.setProperty("class", "subtle")
        layout.addWidget(src)

        self.info = QLabel("")
        self.info.setWordWrap(True)
        self.info.setProperty("class", "note")
        layout.addWidget(self.info)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([t("Chemical state", "화학 상태"), "BE (eV)"])
        self.tree.setRootIsDecorated(False)
        self.tree.setAlternatingRowColors(True)
        self.tree.setUniformRowHeights(True)
        self.tree.header().setStretchLastSection(False)
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
        self.tree.itemSelectionChanged.connect(self._selection_changed)
        layout.addWidget(self.tree, stretch=1)

        self.ref_label = QLabel("")
        self.ref_label.setWordWrap(True)
        self.ref_label.setProperty("class", "subtle")
        layout.addWidget(self.ref_label)

        btns = QHBoxLayout()
        self.btn_guide = QPushButton(t("Show guide lines", "가이드선 표시"))
        self.btn_guide.setToolTip(t("Mark the selected states' BE positions on the plot as dashed lines",
                                    "선택한 상태들의 BE 위치를 플롯에 점선으로 표시"))
        self.btn_guide.clicked.connect(self._show_guides)
        self.btn_clear = QPushButton(t("Clear", "지우기"))
        self.btn_clear.clicked.connect(self.guidesCleared.emit)
        btns.addWidget(self.btn_guide)
        btns.addWidget(self.btn_clear)
        layout.addLayout(btns)

        btns_user = QHBoxLayout()
        self.btn_add_state = QPushButton(t("＋ My reference", "＋ 내 레퍼런스"))
        self.btn_add_state.setToolTip(t(
            "Add a binding energy/range/source from a reference you use.\n"
            "Same name as a built-in entry overrides it (★).\n"
            "Saved to ~/.xpsfit/user_refdb.json — kept across updates.",
            "직접 참고하는 문헌의 BE/범위/출처를 DB에 추가합니다.\n"
            "내장 항목과 같은 이름이면 내 값으로 덮어씁니다 (★).\n"
            "저장: ~/.xpsfit/user_refdb.json — 앱 업데이트에도 유지"))
        self.btn_add_state.clicked.connect(lambda: self._edit_state(new=True))
        self.btn_edit_state = QPushButton(t("✎ Edit", "✎ 수정"))
        self.btn_edit_state.setToolTip(t("Edit the selected state with your own value (overlay; built-in DB kept)",
                                         "선택한 상태를 내 값으로 수정해 저장 (내장 DB는 그대로, 오버레이로 덮음)"))
        self.btn_edit_state.clicked.connect(lambda: self._edit_state(new=False))
        self.btn_del_state = QPushButton("🗑")
        self.btn_del_state.setFixedWidth(40)
        self.btn_del_state.setToolTip(t("Delete the selected ★ (user) entry — a built-in one is restored if it exists",
                                        "선택한 ★(사용자) 항목 삭제 — 내장 항목이 있으면 복원됩니다"))
        self.btn_del_state.clicked.connect(self._delete_state)
        btns_user.addWidget(self.btn_add_state)
        btns_user.addWidget(self.btn_edit_state)
        btns_user.addWidget(self.btn_del_state)
        layout.addLayout(btns_user)

        btns2 = QHBoxLayout()
        self.btn_peak = QPushButton(t("Insert peak", "피크 삽입"))
        self.btn_peak.setToolTip(t("Insert a single peak at the selected state's BE (center bounded to the literature range)",
                                   "선택한 상태의 BE에 단일 피크 삽입 (center는 문헌 범위로 제한)"))
        self.btn_peak.clicked.connect(self._insert_single)
        self.btn_doublet = QPushButton(t("Insert doublet", "Doublet 삽입"))
        self.btn_doublet.setToolTip(t("Insert the spin-orbit pair with splitting / area-ratio / FWHM constraints",
                                      "spin-orbit 짝 피크를 splitting/면적비/FWHM constraint와 함께 삽입"))
        self.btn_doublet.clicked.connect(self._insert_doublet)
        btns2.addWidget(self.btn_peak)
        btns2.addWidget(self.btn_doublet)
        layout.addLayout(btns2)

        rec_row = QHBoxLayout()
        self.recipe_combo = QComboBox()
        for r in refdb.load_recipes():
            self.recipe_combo.addItem(r["name"], r)
        self.recipe_combo.currentIndexChanged.connect(self._recipe_info)
        rec_row.addWidget(self.recipe_combo, stretch=1)
        self.btn_recipe = QPushButton(t("Insert recipe", "Recipe 삽입"))
        self.btn_recipe.setToolTip(t("Insert a literature-based multi-peak set with constraints in one click",
                                     "문헌 기반 멀티피크 세트를 constraint와 함께 한 번에 삽입"))
        self.btn_recipe.clicked.connect(self._insert_recipe)
        rec_row.addWidget(self.btn_recipe)
        layout.addLayout(rec_row)
        self.recipe_info = QLabel("")
        self.recipe_info.setWordWrap(True)
        self.recipe_info.setProperty("class", "subtle")
        layout.addWidget(self.recipe_info)

        # set later by main window: peak count of current region & data scale
        self.index_offset_provider = lambda: 0
        self.area_unit_provider = lambda: 1000.0

        self._fill_states()
        self._recipe_info()

    # ---------- helpers ----------

    def _rebuild_elements(self, select: tuple[str, str] | None = None) -> None:
        current = select or self.element_combo.currentData()
        self.element_combo.blockSignals(True)
        self.element_combo.clear()
        db = refdb.elements()
        for el in sorted(db):
            for orb in db[el]:
                self.element_combo.addItem(f"{el} {orb}", (el, orb))
        self.element_combo.blockSignals(False)
        if current:
            for i in range(self.element_combo.count()):
                if self.element_combo.itemData(i) == tuple(current):
                    self.element_combo.setCurrentIndex(i)
                    break

    def current_orbital(self) -> tuple[str, str, dict]:
        el, orb = self.element_combo.currentData()
        return el, orb, refdb.elements()[el][orb]

    def select_for_region(self, region_name: str) -> None:
        hit = guess_element_orbital(region_name)
        if hit:
            # findData can't compare python tuples through QVariant; match manually
            for i in range(self.element_combo.count()):
                if self.element_combo.itemData(i) == hit:
                    self.element_combo.setCurrentIndex(i)
                    return

    def _fill_states(self) -> None:
        el, orb, info = self.current_orbital()
        split = info.get("spin_orbit_splitting_eV")
        ratio = info.get("doublet_area_ratio")
        rsf = info.get("rsf")
        parts = []
        if split:
            parts.append(f"splitting {split} eV · ratio {ratio}")
        if rsf:
            parts.append(f"RSF {rsf}")
        note = _note(info)
        self.info.setText(" · ".join(parts) + (f"\n⚠ {note}" if note else ""))
        query = self.search.text().strip().lower()
        self.tree.clear()
        for st in info["states"]:
            text = f"{st['state']} {_note(st)}".lower()
            if query and query not in text:
                continue
            display = ("★ " if st.get("user") else "") + st["state"]
            item = QTreeWidgetItem([display, f"{st['be_eV']:.1f}"])
            tip = []
            if st.get("user"):
                tip.append(t("★ user entry (~/.xpsfit/user_refdb.json)", "★ 사용자 항목 (~/.xpsfit/user_refdb.json)"))
            if "range" in st:
                tip.append(t(f"Literature range: {st['range'][0]}–{st['range'][1]} eV",
                             f"문헌 범위: {st['range'][0]}–{st['range'][1]} eV"))
            if st.get("lineshape_hint"):
                tip.append(t(f"Lineshape: {st['lineshape_hint']}", f"라인섀입: {st['lineshape_hint']}"))
            if _note(st):
                tip.append(_note(st))
            tip.append(refdb.reference_text(st["ref"]))
            item.setToolTip(0, "\n".join(tip))
            item.setToolTip(1, "\n".join(tip))
            item.setData(0, Qt.ItemDataRole.UserRole, st)
            self.tree.addTopLevelItem(item)

    def _selected_states(self) -> list[dict]:
        return [i.data(0, Qt.ItemDataRole.UserRole) for i in self.tree.selectedItems()]

    def _selection_changed(self) -> None:
        states = self._selected_states()
        if states:
            self.ref_label.setText("출처: " + refdb.reference_text(states[0]["ref"]))

    # ---------- user DB editing ----------

    def _edit_state(self, new: bool) -> None:
        from .state_editor import StateEditorDialog
        el, orb, _ = self.current_orbital()
        state = None
        if not new:
            sel = self._selected_states()
            if not sel:
                self.ref_label.setText("수정할 상태를 먼저 선택하세요.")
                return
            state = sel[0]
        dlg = StateEditorDialog(element=el, orbital=orb, state=state, parent=self)
        if dlg.exec() == StateEditorDialog.DialogCode.Accepted and dlg.saved_key:
            self._rebuild_elements(select=dlg.saved_key)
            self._fill_states()
            self.ref_label.setText("저장됨 — ★ 표시된 항목이 내 레퍼런스입니다.")

    def _delete_state(self) -> None:
        sel = self._selected_states()
        if not sel or not sel[0].get("user"):
            self.ref_label.setText("★(사용자) 항목을 선택해야 삭제할 수 있습니다 — 내장 항목은 삭제 불가.")
            return
        el, orb, _ = self.current_orbital()
        if refdb.delete_user_state(el, orb, sel[0]["state"]):
            self._rebuild_elements(select=(el, orb))
            self._fill_states()
            self.ref_label.setText("삭제됨 — 같은 이름의 내장 항목이 있으면 복원됐습니다.")

    # ---------- actions ----------

    def _show_guides(self) -> None:
        states = self._selected_states() or [
            self.tree.topLevelItem(i).data(0, Qt.ItemDataRole.UserRole)
            for i in range(self.tree.topLevelItemCount())
        ]
        self.guidesRequested.emit([(st["be_eV"], st["state"]) for st in states])

    def _insert_single(self) -> None:
        states = self._selected_states()
        if not states:
            return
        peaks: list[Peak] = []
        offset = self.index_offset_provider()
        unit = self.area_unit_provider()
        for st in states:
            tol = (st["range"][1] - st["range"][0]) / 2 if "range" in st else 0.5
            peaks.append(refdb.make_peak(st["state"], st["be_eV"], tol, unit))
        self.insertPeaks.emit(peaks)

    def _insert_doublet(self) -> None:
        states = self._selected_states()
        if not states:
            return
        el, orb, info = self.current_orbital()
        if not info.get("spin_orbit_splitting_eV"):
            self.ref_label.setText("이 오비탈(s)은 doublet이 없습니다 — '피크 삽입'을 사용하세요.")
            return
        peaks: list[Peak] = []
        offset = self.index_offset_provider()
        unit = self.area_unit_provider()
        for st in states:
            tol = (st["range"][1] - st["range"][0]) / 2 if "range" in st else 0.5
            pair = refdb.doublet_pair(el, orb, st["be_eV"], main_index=offset + len(peaks),
                                      label=st["state"], area=unit, center_tol=tol)
            peaks.extend(pair)
        self.insertPeaks.emit(peaks)

    def _recipe_info(self) -> None:
        r = self.recipe_combo.currentData()
        if r:
            desc = (r.get("description_en") if current_language() == "en" and r.get("description_en")
                    else r.get("description_ko", ""))
            self.recipe_info.setText(f"{desc}\n{t('Source', '출처')}: {refdb.reference_text(r['ref'])}")

    def _insert_recipe(self) -> None:
        r = self.recipe_combo.currentData()
        if not r:
            return
        peaks = refdb.recipe_peaks(r, index_offset=self.index_offset_provider(),
                                   area_unit=self.area_unit_provider())
        self.insertPeaks.emit(peaks)
