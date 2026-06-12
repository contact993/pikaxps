"""Interactive spectrum plot: data, background, components, envelope, residual.

Binding-energy axis is inverted (XPS convention). Background endpoints are
draggable vertical lines; each peak has a draggable handle at its apex.
"""
from __future__ import annotations

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from ..core import fitting, lineshapes
from ..core.spectrum import Region

pg.setConfigOptions(antialias=True, background="w", foreground="k")

COMPONENT_COLORS = [
    "#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e",
    "#8c564b", "#e377c2", "#17becf", "#bcbd22", "#7f7f7f",
]


class SpectrumPlot(pg.GraphicsLayoutWidget):
    backgroundRangeChanged = Signal(float, float)  # lo, hi (eV)
    peakDragged = Signal(int, float, float)  # index, center, apex height (above bg)
    peakClicked = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setBackground("#ffffff")
        self.main = self.addPlot(row=0, col=0)
        self.resid = self.addPlot(row=1, col=0)
        self.ci.layout.setRowStretchFactor(0, 4)
        self.ci.layout.setRowStretchFactor(1, 1)
        self.resid.setXLink(self.main)
        axis_pen = pg.mkPen("#c2ccd9", width=1)
        text_pen = pg.mkPen("#5b6b7e")
        for p in (self.main, self.resid):
            p.getViewBox().invertX(True)
            p.showGrid(x=True, y=True, alpha=0.12)
            for side in ("left", "bottom"):
                ax = p.getAxis(side)
                ax.setPen(axis_pen)
                ax.setTextPen(text_pen)
        self.main.setLabel("left", "Intensity", units="counts",
                           color="#5b6b7e", **{"font-size": "12pt"})
        self.resid.setLabel("left", "Residual (Data−Fit)", color="#5b6b7e")
        self.resid.setLabel("bottom", "Binding energy", units="eV",
                            color="#5b6b7e", **{"font-size": "12pt"})

        self.data_item = self.main.plot([], [], pen=None, symbol="o", symbolSize=4.5,
                                        symbolPen=pg.mkPen("#7a8aa0", width=0.9),
                                        symbolBrush=None, name="data")
        # points outside the background window: shown but visually muted
        self.data_dim_item = self.main.plot([], [], pen=None, symbol="o", symbolSize=4,
                                            symbolPen=pg.mkPen("#d4dae3", width=0.8),
                                            symbolBrush=None)
        self.bg_item = self.main.plot([], [], pen=pg.mkPen("#888888", width=1.2,
                                                           style=Qt.PenStyle.DashLine))
        self.envelope_item = self.main.plot([], [], pen=pg.mkPen("#000000", width=1.8))
        self.resid_item = self.resid.plot([], [], pen=pg.mkPen("#1f77b4", width=1.0),
                                          connect="finite")
        self.resid.addItem(pg.InfiniteLine(0.0, angle=0, pen=pg.mkPen("#aaaaaa", width=0.8)))

        self.component_items: list[pg.PlotDataItem] = []
        self.fill_items: list[pg.FillBetweenItem] = []
        self.handles: list[pg.TargetItem] = []
        self.guide_items: list = []

        self.lo_line = pg.InfiniteLine(angle=90, movable=True,
                                       pen=pg.mkPen("#00880088", width=1.5),
                                       hoverPen=pg.mkPen("#00bb00", width=2.5),
                                       label="BG", labelOpts={"position": 0.95, "color": "#008800"})
        self.hi_line = pg.InfiniteLine(angle=90, movable=True,
                                       pen=pg.mkPen("#00880088", width=1.5),
                                       hoverPen=pg.mkPen("#00bb00", width=2.5))
        for line in (self.lo_line, self.hi_line):
            self.main.addItem(line)
            line.setVisible(False)
            line.sigPositionChangeFinished.connect(self._emit_bg_range)

        # invisible curve mirroring the background; fills are drawn against it
        self._bg_proxy_item = pg.PlotDataItem()

        self._region: Region | None = None
        self._updating = False
        self._highlight = -1

    # ---------- public API ----------

    def set_region(self, region: Region | None) -> None:
        self._region = region
        if region is None or region.x.size == 0:
            self.data_item.setData([], [])
            self.data_dim_item.setData([], [])
            self.bg_item.setData([], [])
            self.envelope_item.setData([], [])
            self.resid_item.setData([], [])
            self._clear_components()
            self.lo_line.setVisible(False)
            self.hi_line.setVisible(False)
            return
        i1, i2 = region.crop_indices()
        self._updating = True
        self.lo_line.setPos(region.x[i1])
        self.hi_line.setPos(region.x[i2])
        self._updating = False
        show = region.background.kind != "NONE"
        self.lo_line.setVisible(show)
        self.hi_line.setVisible(show)
        self.main.setTitle(region.name, color="#1e2a3a", size="14pt", bold=True)
        self.refresh_model()
        self.zoom_to_window()

    def refresh_model(self) -> None:
        """Recompute background/components/envelope from the current model."""
        region = self._region
        if region is None or region.x.size == 0:
            return
        res = fitting.eval_model(region)
        i1, i2 = region.crop_indices()
        inside = np.zeros(region.x.size, dtype=bool)
        inside[i1: i2 + 1] = True
        if region.background.kind == "NONE":
            inside[:] = True  # no window -> nothing to mute
        self.data_item.setData(region.x[inside], region.y[inside])
        self.data_dim_item.setData(region.x[~inside], region.y[~inside])
        if region.background.kind != "NONE":
            self.bg_item.setData(region.x[i1: i2 + 1], res.background[i1: i2 + 1])
        else:
            self.bg_item.setData([], [])
        self._bg_proxy_item.setData(region.x, res.background)
        self._sync_components(len(region.peaks))
        for i, comp in enumerate(res.components):
            self.component_items[i].setData(region.x, res.background + comp)
        if region.peaks:
            self.envelope_item.setData(region.x[inside], res.envelope[inside])
        else:
            self.envelope_item.setData([], [])
        resid = np.where(inside, res.residual, np.nan)
        self.resid_item.setData(region.x, resid)
        self._sync_handles(res)

    def highlight_component(self, index: int) -> None:
        """Selected peak (table row) gets a thick outline in the plot."""
        self._highlight = index
        for j, item in enumerate(self.component_items):
            color = COMPONENT_COLORS[j % len(COMPONENT_COLORS)]
            item.setPen(pg.mkPen(color, width=3.2 if j == index else 1.2))

    def zoom_to_window(self) -> None:
        """Frame the view on the background window (small margin keeps the
        green lines grabbable); full autorange when no window is set."""
        region = self._region
        if region is None or region.x.size == 0:
            return
        if region.background.kind == "NONE":
            self.main.autoRange()
            return
        i1, i2 = region.crop_indices()
        x0, x1 = float(region.x[i1]), float(region.x[i2])
        pad = (x1 - x0) * 0.08 or 1.0
        self.main.setXRange(x0 - pad, x1 + pad, padding=0)
        yw = region.y[i1: i2 + 1]
        ylo, yhi = float(yw.min()), float(yw.max())
        ypad = (yhi - ylo) * 0.10 or 1.0
        self.main.setYRange(ylo - ypad, yhi + ypad, padding=0)

    def show_guides(self, guides: list[tuple[float, str]]) -> None:
        """Vertical dashed reference lines: [(be_eV, label), ...]."""
        self.clear_guides()
        for be, label in guides:
            line = pg.InfiniteLine(
                pos=be, angle=90,
                pen=pg.mkPen("#cc6600", width=1.2, style=Qt.PenStyle.DashLine),
                label=label, labelOpts={"position": 0.9, "color": "#cc6600",
                                        "rotateAxis": (1, 0), "anchors": [(0.5, 0), (0.5, 0)]},
            )
            self.main.addItem(line)
            self.guide_items.append(line)

    def clear_guides(self) -> None:
        for g in self.guide_items:
            self.main.removeItem(g)
        self.guide_items.clear()

    # ---------- internals ----------

    def _clear_components(self) -> None:
        for item in self.component_items:
            self.main.removeItem(item)
        for f in self.fill_items:
            self.main.removeItem(f)
        for h in self.handles:
            self.main.removeItem(h)
        self.component_items.clear()
        self.fill_items.clear()
        self.handles.clear()

    def _sync_components(self, n: int) -> None:
        while len(self.component_items) > n:
            self.main.removeItem(self.component_items.pop())
            self.main.removeItem(self.fill_items.pop())
            self.main.removeItem(self.handles.pop())
        while len(self.component_items) < n:
            i = len(self.component_items)
            color = COMPONENT_COLORS[i % len(COMPONENT_COLORS)]
            curve = self.main.plot([], [], pen=pg.mkPen(
                color, width=3.2 if i == self._highlight else 1.2))
            fill_color = QColor(color)
            fill_color.setAlpha(60)
            fill = pg.FillBetweenItem(curve, self._bg_proxy_item, brush=pg.mkBrush(fill_color))
            self.main.addItem(fill)
            handle = pg.TargetItem(movable=True, size=11,
                                   pen=pg.mkPen(color, width=1.5),
                                   brush=pg.mkBrush("#ffffff"))
            handle.index = i
            handle.sigPositionChangeFinished.connect(self._handle_moved)
            self.main.addItem(handle)
            self.component_items.append(curve)
            self.fill_items.append(fill)
            self.handles.append(handle)

    def _sync_handles(self, res) -> None:
        region = self._region
        self._updating = True
        try:
            for i, p in enumerate(region.peaks):
                c = p.center.value
                j = int(np.clip(np.searchsorted(region.x, c), 0, region.x.size - 1))
                apex = res.background[j] + (res.components[i][j] if i < len(res.components) else 0.0)
                self.handles[i].setPos(c, apex)
                self.handles[i].setToolTip(p.label or f"Peak {i + 1}")
        finally:
            self._updating = False

    def _handle_moved(self, handle) -> None:
        if self._updating or self._region is None:
            return
        i = handle.index
        x, y = handle.pos().x(), handle.pos().y()
        res = fitting.eval_model(self._region)
        j = int(np.clip(np.searchsorted(self._region.x, x), 0, self._region.x.size - 1))
        height = max(y - res.background[j], 1e-6)
        self.peakDragged.emit(i, float(x), float(height))

    def _emit_bg_range(self) -> None:
        if self._updating:
            return
        lo, hi = self.lo_line.value(), self.hi_line.value()
        self.backgroundRangeChanged.emit(float(min(lo, hi)), float(max(lo, hi)))


def height_to_area(region: Region, peak_index: int, height: float) -> float:
    """Convert a dragged apex height into the area parameter for that peak."""
    p = region.peaks[peak_index]
    unit = lineshapes.evaluate(p.shape, region.x, p.center.value, 1.0,
                               p.fwhm.value, p.mix.value, p.asym.value)
    peak_max = float(unit.max())
    return height / peak_max if peak_max > 0 else p.area.value
