"""Application theme: light palette + stylesheet.

Forced light theme so the UI matches the white plot canvas; Fusion style
gives identical rendering on macOS and Windows.
"""
from __future__ import annotations

from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import QApplication

ACCENT = "#2563eb"
ACCENT_DARK = "#1d4ed8"
BG = "#f3f4f7"
PANEL = "#ffffff"
BORDER = "#dde2ea"
TEXT = "#1e2a3a"
TEXT_SUBTLE = "#5b6b7e"
SELECTION_BG = "#dbe7fe"

QSS = f"""
* {{
    color: {TEXT};
}}
QMainWindow, QDialog {{
    background: {BG};
}}
QToolTip {{
    background: #243042;
    color: #f3f6fb;
    border: none;
    padding: 6px 9px;
    font-size: 12px;
}}

/* ---------- docks & tabs ---------- */
QDockWidget {{
    titlebar-close-icon: none;
    titlebar-normal-icon: none;
    font-weight: 600;
    color: {TEXT_SUBTLE};
}}
QDockWidget::title {{
    padding: 7px 12px 5px 12px;
    background: {BG};
    text-transform: uppercase;
}}
QTabWidget::pane {{
    border: 1px solid {BORDER};
    border-radius: 8px;
    background: {PANEL};
    top: -1px;
}}
QTabBar::tab {{
    background: transparent;
    padding: 7px 14px;
    margin-right: 2px;
    color: {TEXT_SUBTLE};
    border: none;
    border-bottom: 2px solid transparent;
    font-weight: 600;
}}
QTabBar::tab:selected {{
    color: {ACCENT};
    border-bottom: 2px solid {ACCENT};
}}
QTabBar::tab:hover:!selected {{
    color: {TEXT};
}}

/* ---------- inputs ---------- */
QComboBox, QLineEdit, QSpinBox, QDoubleSpinBox {{
    background: {PANEL};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 4px 8px;
    min-height: 20px;
    selection-background-color: {SELECTION_BG};
    selection-color: {TEXT};
}}
QComboBox:focus, QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
    border: 1.5px solid {ACCENT};
}}
QComboBox::drop-down {{
    border: none;
    width: 22px;
}}
QComboBox QAbstractItemView {{
    background: {PANEL};
    border: 1px solid {BORDER};
    border-radius: 6px;
    selection-background-color: {SELECTION_BG};
    selection-color: {TEXT};
    padding: 4px;
}}

/* ---------- buttons ---------- */
QPushButton {{
    background: {PANEL};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 5px 14px;
    min-height: 20px;
}}
QPushButton:hover {{
    background: #f0f4fb;
    border-color: #c4cfde;
}}
QPushButton:pressed {{
    background: #e4ebf7;
}}
QPushButton:disabled {{
    color: #9aa7b8;
    background: {BG};
}}
QPushButton#primary {{
    background: {ACCENT};
    border: 1px solid {ACCENT_DARK};
    color: white;
    font-weight: 600;
    padding: 5px 18px;
}}
QPushButton#primary:hover {{
    background: {ACCENT_DARK};
}}

/* ---------- item views ---------- */
QListWidget, QTreeWidget, QTableWidget {{
    background: {PANEL};
    alternate-background-color: #f7f9fc;
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 2px;
    outline: 0;
}}
QListWidget::item {{
    padding: 7px 10px;
    border-radius: 6px;
    margin: 1px 2px;
}}
QTreeWidget::item {{
    padding: 5px 4px;
}}
QListWidget::item:selected, QTreeWidget::item:selected {{
    background: {SELECTION_BG};
    color: {TEXT};
}}
/* peak table rows keep their component color; selection = thick outline */
QTableWidget::item:selected {{
    background: transparent;
    color: {TEXT};
    border-top: 2.5px solid {ACCENT};
    border-bottom: 2.5px solid {ACCENT};
}}
QListWidget::item:hover:!selected, QTreeWidget::item:hover:!selected {{
    background: #eef2f8;
}}
QHeaderView::section {{
    background: {PANEL};
    color: {TEXT_SUBTLE};
    font-weight: 600;
    border: none;
    border-bottom: 1.5px solid {BORDER};
    padding: 6px 8px;
}}
QTableWidget {{
    gridline-color: #eef1f6;
}}
QTableCornerButton::section {{
    background: {PANEL};
    border: none;
    border-bottom: 1.5px solid {BORDER};
}}

/* ---------- misc ---------- */
QGraphicsView {{
    border: 1px solid {BORDER};
    border-radius: 8px;
    background: {PANEL};
}}
QTextBrowser {{
    background: {PANEL};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 10px 14px;
}}
QGroupBox {{
    border: 1px solid {BORDER};
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 6px;
    background: {PANEL};
    font-weight: 600;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
    color: {TEXT_SUBTLE};
}}
QStatusBar {{
    background: {BG};
    color: {TEXT_SUBTLE};
}}
QMenuBar {{
    background: {BG};
}}
QMenuBar::item:selected {{
    background: {SELECTION_BG};
    border-radius: 4px;
}}
QMenu {{
    background: {PANEL};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 4px;
}}
QMenu::item {{
    padding: 6px 24px 6px 14px;
    border-radius: 5px;
}}
QMenu::item:selected {{
    background: {SELECTION_BG};
}}
QScrollBar:vertical {{
    background: transparent;
    width: 11px;
    margin: 2px;
}}
QScrollBar::handle:vertical {{
    background: #c6cfdc;
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: #aab7c9;
}}
QScrollBar::add-line, QScrollBar::sub-line {{
    height: 0; width: 0;
}}
QScrollBar:horizontal {{
    background: transparent;
    height: 11px;
    margin: 2px;
}}
QScrollBar::handle:horizontal {{
    background: #c6cfdc;
    border-radius: 4px;
    min-width: 30px;
}}
QLabel[class="subtle"] {{
    color: {TEXT_SUBTLE};
    font-size: 12px;
}}
QLabel[class="note"] {{
    color: {TEXT_SUBTLE};
    font-size: 12px;
    background: #f0f4fb;
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 7px 10px;
}}
"""


def apply_theme(app: QApplication) -> None:
    app.setStyle("Fusion")
    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Window, QColor(BG))
    pal.setColor(QPalette.ColorRole.Base, QColor(PANEL))
    pal.setColor(QPalette.ColorRole.AlternateBase, QColor("#f7f9fc"))
    pal.setColor(QPalette.ColorRole.Text, QColor(TEXT))
    pal.setColor(QPalette.ColorRole.WindowText, QColor(TEXT))
    pal.setColor(QPalette.ColorRole.ButtonText, QColor(TEXT))
    pal.setColor(QPalette.ColorRole.Button, QColor(PANEL))
    pal.setColor(QPalette.ColorRole.Highlight, QColor(SELECTION_BG))
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor(TEXT))
    pal.setColor(QPalette.ColorRole.Link, QColor(ACCENT))
    pal.setColor(QPalette.ColorRole.PlaceholderText, QColor("#9aa7b8"))
    pal.setColor(QPalette.ColorRole.ToolTipBase, QColor("#243042"))
    pal.setColor(QPalette.ColorRole.ToolTipText, QColor("#f3f6fb"))
    app.setPalette(pal)

    font = QFont()
    font.setPointSize(13)  # readable default; Korean falls back to Apple SD Gothic
    app.setFont(font)

    app.setStyleSheet(QSS)
