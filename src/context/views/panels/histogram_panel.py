from __future__ import annotations

import numpy as np
from PyQt6.QtCore import QPointF, QRectF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QImage, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QStackedLayout, QVBoxLayout, QWidget

from context.localization import LocalizationController
from context.viewmodels import GraphViewModel
from context.views.theme import ThemeController


class _HistogramPlot(QWidget):
    _CHANNEL_COLORS = (
        QColor("#ef4444"),
        QColor("#22c55e"),
        QColor("#3b82f6"),
        QColor("#facc15"),
    )

    def __init__(self, theme_controller: ThemeController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._theme_controller = theme_controller
        self._histograms: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray] | None = None
        self.setObjectName("histogramPlot")
        self.setMinimumHeight(180)
        self._theme_controller.themeChanged.connect(self._on_theme_changed)

    def has_histogram(self) -> bool:
        return self._histograms is not None

    def rgb_histograms(self) -> tuple[np.ndarray, np.ndarray, np.ndarray] | None:
        if self._histograms is None:
            return None
        return tuple(channel.copy() for channel in self._histograms[:3])

    def luminance_histogram(self) -> np.ndarray | None:
        if self._histograms is None:
            return None
        return self._histograms[3].copy()

    def set_histograms(
        self,
        histograms: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray] | None,
    ) -> None:
        self._histograms = histograms
        self.update()

    def render_plot_image(self, size: QSize) -> QImage:
        image = QImage(size, QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(Qt.GlobalColor.transparent)
        painter = QPainter(image)
        self._draw_histogram_plot(painter, QRectF(0.0, 0.0, float(size.width()), float(size.height())))
        painter.end()
        return image

    def paintEvent(self, event) -> None:  # pragma: no cover - exercised through Qt rendering
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self._draw_histogram_plot(painter, QRectF(self.rect()))

    def _draw_histogram_plot(self, painter: QPainter, rect: QRectF) -> None:
        theme = self._theme_controller.theme
        card_rect = rect.adjusted(1.0, 1.0, -1.0, -1.0)

        painter.setPen(QPen(QColor(theme.border_soft), 1.0))
        painter.setBrush(QColor(theme.surface_raised))
        painter.drawRoundedRect(card_rect, 18.0, 18.0)

        if self._histograms is None:
            return

        plot_rect = card_rect.adjusted(14.0, 14.0, -14.0, -14.0)
        grid_pen = QPen(QColor(theme.border_soft), 1.0)
        grid_pen.setCosmetic(True)
        painter.setPen(grid_pen)
        for column in range(1, 4):
            x = plot_rect.left() + (plot_rect.width() * column / 4.0)
            painter.drawLine(QPointF(x, plot_rect.top()), QPointF(x, plot_rect.bottom()))
        for row in range(1, 4):
            y = plot_rect.top() + (plot_rect.height() * row / 4.0)
            painter.drawLine(QPointF(plot_rect.left(), y), QPointF(plot_rect.right(), y))

        peak = max(int(channel.max()) for channel in self._histograms)
        if peak <= 0:
            return

        for histogram, color in zip(self._histograms, self._CHANNEL_COLORS, strict=True):
            path = QPainterPath()
            for index, value in enumerate(histogram.tolist()):
                x = plot_rect.left() + (plot_rect.width() * index / 255.0)
                normalized = float(value) / float(peak)
                y = plot_rect.bottom() - (plot_rect.height() * normalized)
                if index == 0:
                    path.moveTo(x, y)
                else:
                    path.lineTo(x, y)
            pen = QPen(color, 1.75)
            pen.setCosmetic(True)
            painter.setPen(pen)
            painter.drawPath(path)

    def _on_theme_changed(self, _theme) -> None:
        self.update()


class HistogramPanel(QWidget):
    exportAvailabilityChanged = pyqtSignal(bool)
    saveRequested = pyqtSignal()

    def __init__(
        self,
        graph_vm: GraphViewModel,
        theme_controller: ThemeController,
        localization_controller: LocalizationController,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._theme_controller = theme_controller
        self._localization = localization_controller
        self._plot = _HistogramPlot(theme_controller)
        self._empty_label = QLabel()
        self._empty_label.setObjectName("histogramEmptyState")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setWordWrap(True)
        self._export_button = QPushButton()
        self._export_button.setObjectName("histogramExportButton")
        self._export_button.clicked.connect(self.saveRequested.emit)
        self._stack = QStackedLayout()

        legend_layout = QHBoxLayout()
        legend_layout.setContentsMargins(0, 0, 0, 0)
        legend_layout.setSpacing(8)
        for text, object_name in (
            ("R", "histogramLegendRed"),
            ("G", "histogramLegendGreen"),
            ("B", "histogramLegendBlue"),
            ("L", "histogramLegendLuma"),
        ):
            chip = QLabel(text)
            chip.setObjectName(object_name)
            chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
            legend_layout.addWidget(chip)
        legend_layout.addStretch(1)
        legend_layout.addWidget(self._export_button)

        self._stack.addWidget(self._empty_label)
        self._stack.addWidget(self._plot)
        self._stack.setCurrentWidget(self._empty_label)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)
        layout.addLayout(legend_layout)
        layout.addLayout(self._stack, 1)

        graph_vm.previewUpdated.connect(self.set_image)
        self._localization.localeChanged.connect(self._on_locale_changed)
        self._retranslate_ui()
        self._set_export_enabled(False)

    def has_image(self) -> bool:
        return self._plot.has_histogram()

    def has_exportable_histogram(self) -> bool:
        return self._plot.has_histogram()

    def channel_histograms(self) -> tuple[np.ndarray, np.ndarray, np.ndarray] | None:
        return self._plot.rgb_histograms()

    def luminance_histogram(self) -> np.ndarray | None:
        return self._plot.luminance_histogram()

    def save_png(self, file_path: str) -> None:
        if not self.has_exportable_histogram():
            raise ValueError(self._localization.tr("histogram.export.unavailable"))
        export_image = self._render_export_image()
        export_image.save(file_path, "PNG")

    def set_image(self, image: np.ndarray | None) -> None:
        if image is None:
            self._plot.set_histograms(None)
            self._stack.setCurrentWidget(self._empty_label)
            self._empty_label.setText(self._localization.tr("histogram.unavailable"))
            self._set_export_enabled(False)
            return

        rgb_histograms = tuple(
            np.bincount(image[:, :, channel].reshape(-1), minlength=256).astype(np.int64)
            for channel in range(3)
        )
        luminance = np.clip(
            np.round(
                (0.299 * image[:, :, 0])
                + (0.587 * image[:, :, 1])
                + (0.114 * image[:, :, 2])
            ),
            0,
            255,
        ).astype(np.uint8)
        luminance_histogram = np.bincount(luminance.reshape(-1), minlength=256).astype(np.int64)
        self._plot.set_histograms((*rgb_histograms, luminance_histogram))
        self._stack.setCurrentWidget(self._plot)
        self._set_export_enabled(True)

    def _render_export_image(self) -> QImage:
        theme = self._theme_controller.theme
        width = 960
        height = 420
        image = QImage(width, height, QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(QColor(theme.surface).rgba())

        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        chips = (
            ("R", QColor("#ef4444")),
            ("G", QColor("#22c55e")),
            ("B", QColor("#3b82f6")),
            ("L", QColor("#facc15")),
        )
        chip_rect = QRectF(24.0, 20.0, 44.0, 28.0)
        chip_gap = 10.0
        for text, color in chips:
            self._draw_legend_chip(painter, chip_rect, text, color)
            chip_rect.translate(chip_rect.width() + chip_gap, 0.0)

        plot_rect = QRectF(24.0, 68.0, float(width) - 48.0, float(height) - 92.0)
        plot_image = self._plot.render_plot_image(plot_rect.size().toSize())
        painter.drawImage(plot_rect.topLeft(), plot_image)
        painter.end()
        return image

    def _draw_legend_chip(self, painter: QPainter, rect: QRectF, text: str, color: QColor) -> None:
        theme = self._theme_controller.theme
        painter.setPen(QPen(QColor(theme.border_soft), 1.0))
        painter.setBrush(QColor(theme.surface_raised))
        painter.drawRoundedRect(rect, 11.0, 11.0)
        font = QFont()
        font.setBold(True)
        font.setPointSize(10)
        painter.setFont(font)
        painter.setPen(QPen(color))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)

    def _on_locale_changed(self, _locale_code: str) -> None:
        if not self._plot.has_histogram():
            self._empty_label.setText(self._localization.tr("histogram.unavailable"))
        self._retranslate_ui()

    def _set_export_enabled(self, enabled: bool) -> None:
        self._export_button.setEnabled(enabled)
        self.exportAvailabilityChanged.emit(enabled)

    def _retranslate_ui(self) -> None:
        self._export_button.setText(self._localization.tr("histogram.action.export"))
        if not self._plot.has_histogram():
            self._empty_label.setText(self._localization.tr("histogram.unavailable"))
