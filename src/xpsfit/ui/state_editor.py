"""Editor for user reference-DB entries (saved to ~/.xpsfit/user_refdb.json)."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QVBoxLayout,
)

from .. import refdb


class StateEditorDialog(QDialog):
    """Add or edit one chemical state with the user's own citation.
    Same state name as a built-in entry -> your value overrides it (★)."""

    def __init__(self, element: str = "", orbital: str = "",
                 state: dict | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("내 레퍼런스 추가/수정")
        self.resize(520, 0)
        lay = QVBoxLayout(self)
        info = QLabel("저장 위치: <code>~/.xpsfit/user_refdb.json</code> — 앱을 업데이트해도 유지되고, "
                      "이 파일을 복사하면 다른 컴퓨터로 옮길 수 있습니다.<br>"
                      "내장 항목과 <b>같은 상태 이름</b>으로 저장하면 그 값을 덮어씁니다 (★ 표시).")
        info.setWordWrap(True)
        info.setProperty("class", "subtle")
        lay.addWidget(info)

        form = QFormLayout()
        self.el_edit = QLineEdit(element)
        self.el_edit.setPlaceholderText("예: Ni")
        self.orb_edit = QLineEdit(orbital)
        self.orb_edit.setPlaceholderText("예: 2p")
        form.addRow("원소:", self.el_edit)
        form.addRow("오비탈:", self.orb_edit)
        self.name_edit = QLineEdit(state.get("state", "") if state else "")
        self.name_edit.setPlaceholderText("예: Ni-Fe LDH (우리 랩)")
        form.addRow("상태 이름*:", self.name_edit)
        self.be_spin = QDoubleSpinBox()
        self.be_spin.setRange(0.0, 1500.0)
        self.be_spin.setDecimals(2)
        self.be_spin.setSuffix(" eV")
        self.be_spin.setValue(state.get("be_eV", 285.0) if state else 285.0)
        form.addRow("BE (주성분)*:", self.be_spin)
        self.lo_spin = QDoubleSpinBox()
        self.hi_spin = QDoubleSpinBox()
        for s in (self.lo_spin, self.hi_spin):
            s.setRange(0.0, 1500.0)
            s.setDecimals(2)
            s.setSuffix(" eV")
        rng = (state or {}).get("range")
        self.lo_spin.setValue(rng[0] if rng else self.be_spin.value() - 0.3)
        self.hi_spin.setValue(rng[1] if rng else self.be_spin.value() + 0.3)
        self.be_spin.valueChanged.connect(self._sync_range_defaults)
        form.addRow("문헌 범위 (하한):", self.lo_spin)
        form.addRow("문헌 범위 (상한):", self.hi_spin)
        self.hint_edit = QLineEdit((state or {}).get("lineshape_hint", ""))
        self.hint_edit.setPlaceholderText("예: asymmetric (DS), strong satellite ~786")
        form.addRow("라인섀입 힌트:", self.hint_edit)
        self.note_edit = QLineEdit((state or {}).get("notes_ko", ""))
        self.note_edit.setPlaceholderText("메모 (선택)")
        form.addRow("메모:", self.note_edit)
        self.ref_edit = QLineEdit((state or {}).get("ref", ""))
        self.ref_edit.setPlaceholderText("예: Kim et al., J. Mater. Chem. A 13 (2025) 1234")
        form.addRow("출처*:", self.ref_edit)
        lay.addLayout(form)

        # extra metadata, needed only when this element/orbital is new
        self.meta_box = QGroupBox("새 원소/오비탈 정보 (DB에 없는 조합일 때만)")
        mf = QFormLayout(self.meta_box)
        self.split_spin = QDoubleSpinBox()
        self.split_spin.setRange(0.0, 60.0)
        self.split_spin.setDecimals(2)
        self.split_spin.setSuffix(" eV")
        self.split_spin.setSpecialValueText("없음 (s 오비탈)")
        mf.addRow("Spin-orbit splitting:", self.split_spin)
        self.ratio_edit = QLineEdit()
        self.ratio_edit.setPlaceholderText("p: 2:1 · d: 3:2 · f: 4:3")
        mf.addRow("Doublet 면적비:", self.ratio_edit)
        self.rsf_spin = QDoubleSpinBox()
        self.rsf_spin.setRange(0.01, 100.0)
        self.rsf_spin.setDecimals(2)
        self.rsf_spin.setValue(1.0)
        mf.addRow("RSF (C 1s=1):", self.rsf_spin)
        lay.addWidget(self.meta_box)
        self.el_edit.textChanged.connect(self._update_meta_visibility)
        self.orb_edit.textChanged.connect(self._update_meta_visibility)
        self._update_meta_visibility()

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save
                                   | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        lay.addWidget(buttons)
        self.saved_key: tuple[str, str] | None = None

    def _sync_range_defaults(self) -> None:
        self.lo_spin.setValue(self.be_spin.value() - 0.3)
        self.hi_spin.setValue(self.be_spin.value() + 0.3)

    def _combo_exists(self) -> bool:
        el = self.el_edit.text().strip().capitalize()
        orb = self.orb_edit.text().strip().lower()
        db = refdb.elements()
        return el in db and orb in db[el]

    def _update_meta_visibility(self) -> None:
        self.meta_box.setVisible(not self._combo_exists())
        self.adjustSize()

    def _save(self) -> None:
        el = self.el_edit.text().strip().capitalize()
        orb = self.orb_edit.text().strip().lower()
        name = self.name_edit.text().strip()
        ref = self.ref_edit.text().strip()
        if not el or not orb or not name or not ref:
            self.ref_edit.setPlaceholderText("원소/오비탈/상태 이름/출처는 필수입니다")
            return
        state = {
            "state": name,
            "be_eV": self.be_spin.value(),
            "range": [self.lo_spin.value(), self.hi_spin.value()],
            "lineshape_hint": self.hint_edit.text().strip() or None,
            "notes_ko": self.note_edit.text().strip() or None,
            "ref": ref,
        }
        meta = None
        if not self._combo_exists():
            meta = {
                "spin_orbit_splitting_eV": self.split_spin.value() or None,
                "doublet_area_ratio": self.ratio_edit.text().strip() or None,
                "rsf": self.rsf_spin.value(),
            }
        refdb.save_user_state(el, orb, state, orbital_meta=meta)
        self.saved_key = (el, orb)
        self.accept()
