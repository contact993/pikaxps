"""Generate a polished marketing screenshot: a fully-fitted spectrum with several
colored component peaks visible (not an empty window)."""
import sys
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from xpsfit import refdb
from xpsfit.core import fitting
from xpsfit.io import importer
from xpsfit.ui.main_window import MainWindow
from xpsfit.ui.theme import apply_theme

ROOT = Path(__file__).parent.parent


def main() -> int:
    app = QApplication(sys.argv)
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
    win.statusBar().showMessage("Fit OK — 4 components · run 🔍 진단 to validate", 0)
    win.show()

    def grab():
        out = ROOT / "docs" / "screenshot.png"
        win.grab().save(str(out))
        print("screenshot ->", out)

    QTimer.singleShot(2000, grab)
    QTimer.singleShot(2700, app.quit)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
