"""Context-sensitive help panel rendering the explanation markdown.

Explanations exist in Korean (explanations/*.md) and English (explanations/en/*.md);
the active UI language picks which to show, falling back to Korean if an English
file is missing.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QComboBox, QTextBrowser, QVBoxLayout, QWidget

from .i18n import current_language, t

_DIR = Path(__file__).parent.parent / "refdb" / "explanations"


def _resolve(fname: str) -> Path:
    if current_language() == "en":
        en = _DIR / "en" / fname
        if en.exists():
            return en
    return _DIR / fname


TOPICS = [
    (t("Backgrounds — Shirley/Tougaard/Linear", "백그라운드 — Shirley/Tougaard/Linear"), "backgrounds.md"),
    (t("Lineshapes — GL mix / asymmetry", "라인섀입 — GL 믹스·비대칭"), "lineshapes.md"),
    (t("Constraints — doublet / FWHM link", "Constraint — doublet·FWHM 링크"), "constraints.md"),
    (t("Satellites — shake-up / plasmon", "Satellite 피크 — shake-up·plasmon"), "satellites.md"),
    (t("Charge referencing (C 1s 284.8)", "대전 보정 (C 1s 284.8)"), "charge_referencing.md"),
    (t("Recommended workflow & common errors", "권장 Fitting 절차 & 흔한 오류"), "workflow.md"),
    (t("Quantification (RSF / atomic %)", "정량 분석 (RSF·atomic %)"), "quantification.md"),
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
        path = _resolve(fname)
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
