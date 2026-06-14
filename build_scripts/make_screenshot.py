"""Generate a polished marketing screenshot: a fully-fitted spectrum with several
colored component peaks visible (not an empty window).

Usage:
    python build_scripts/make_screenshot.py [en|ko]

The UI language is forced in-process (without touching the user's saved
setting) so the captured screenshot is fully English or fully Korean.
Output: docs/screenshot.png (en) or docs/screenshot-ko.png (ko).
"""
import sys
from pathlib import Path

# Pick language BEFORE Qt/app strings are built, and keep it out of Qt's argv.
_LANG = "ko" if (len(sys.argv) > 1 and sys.argv[1].lower().startswith("ko")) else "en"

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from xpsfit import refdb
from xpsfit.core import fitting
from xpsfit.io import importer
from xpsfit.ui import i18n
from xpsfit.ui.i18n import t
from xpsfit.ui.main_window import MainWindow
from xpsfit.ui.theme import apply_theme

# Force the language for this process only (no QSettings write).
i18n._LANG = _LANG

ROOT = Path(__file__).parent.parent


def main() -> int:
    app = QApplication([sys.argv[0]])  # keep our lang arg away from Qt
    apply_theme(app)
    win = MainWindow()
    win.resize(1600, 980)

    # Ni 2p3/2 — metal + NiO + multiplet + satellite = four filled, colored peaks
    sniffed = importer.sniff(ROOT / "samples" / "Ni2p_NiFoam.dat")
    df = importer.load_table(sniffed)
    region = importer.to_region(df, importer.guess_mapping(df), name="Ni 2p",
                                source=str(sniffed.path))
    win.session.regions.append(region)
    win._refresh_region_list()

    recipe = next(r for r in refdb.load_recipes() if r["id"] == "ni2p3_screen")
    region.peaks = refdb.recipe_peaks(recipe, area_unit=win._area_unit())
    fitting.fit_until_converged(region)
    win._model_edited()
    win.peak_table.table.setCurrentCell(0, 1)  # highlight first peak
    win.statusBar().showMessage(
        t("Fit OK — 4 components · run the fit auditor to validate",
          "피팅 완료 — 성분 4개 · 핏 오디터로 검증하세요"), 0)
    win.show()

    suffix = "-ko" if _LANG == "ko" else ""
    out = ROOT / "docs" / f"screenshot{suffix}.png"

    def grab():
        win.grab().save(str(out))
        print("screenshot ->", out)

    QTimer.singleShot(2000, grab)
    QTimer.singleShot(2700, app.quit)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
