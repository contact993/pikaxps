"""Launch the real app, load a sample, insert recipe, fit, screenshot, quit.
Used as an end-to-end sanity check on a real display."""
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

    sniffed = importer.sniff(ROOT / "samples" / "Ni2p_NiFoam.dat")
    df = importer.load_table(sniffed)
    region = importer.to_region(df, importer.guess_mapping(df), name="Ni 2p",
                                source=str(sniffed.path))
    win.session.regions.append(region)
    win._refresh_region_list()

    recipe = next(r for r in refdb.load_recipes() if r["id"] == "ni2p3_screen")
    region.peaks = refdb.recipe_peaks(recipe, area_unit=win._area_unit())
    res = fitting.fit_region(region)
    print(f"fit success={res.success} redchi={res.redchi:.1f}")
    win._model_edited()
    win.show()

    def grab():
        out = ROOT / "docs" / "screenshot.png"
        out.parent.mkdir(exist_ok=True)
        win.grab().save(str(out))
        print("screenshot ->", out)

    QTimer.singleShot(1800, grab)
    QTimer.singleShot(2600, app.quit)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
