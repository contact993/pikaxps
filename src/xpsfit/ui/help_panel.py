"""Context-sensitive Korean help panel rendering the explanation markdown."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QComboBox, QTextBrowser, QVBoxLayout, QWidget

_DIR = Path(__file__).parent.parent / "refdb" / "explanations"

TOPICS = [
    ("백그라운드 — Shirley/Tougaard/Linear", "backgrounds.md"),
    ("라인섀입 — GL 믹스·비대칭", "lineshapes.md"),
    ("Constraint — doublet·FWHM 링크", "constraints.md"),
    ("Satellite 피크 — shake-up·plasmon", "satellites.md"),
    ("대전 보정 (C 1s 284.8)", "charge_referencing.md"),
    ("권장 Fitting 절차 & 흔한 오류", "workflow.md"),
    ("정량 분석 (RSF·atomic %)", "quantification.md"),
]

CONTEXT_TO_TOPIC = {
    "background": "backgrounds.md",
    "lineshape": "lineshapes.md",
    "constraint": "constraints.md",
    "satellite": "satellites.md",
    "charge": "charge_referencing.md",
    "workflow": "workflow.md",
    "quantify": "quantification.md",
}


class HelpPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        self.topic_combo = QComboBox()
        for title, fname in TOPICS:
            self.topic_combo.addItem(title, fname)
        self.topic_combo.currentIndexChanged.connect(self._load_current)
        layout.addWidget(self.topic_combo)
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        layout.addWidget(self.browser, stretch=1)
        self._load_current()

    def _load_current(self) -> None:
        fname = self.topic_combo.currentData()
        path = _DIR / fname
        if path.exists():
            self.browser.setMarkdown(path.read_text(encoding="utf-8"))
        else:
            self.browser.setPlainText(f"(missing: {fname})")

    def show_context(self, key: str) -> None:
        fname = CONTEXT_TO_TOPIC.get(key)
        if not fname:
            return
        idx = self.topic_combo.findData(fname)
        if idx >= 0:
            self.topic_combo.setCurrentIndex(idx)
