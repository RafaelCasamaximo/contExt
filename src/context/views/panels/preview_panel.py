from __future__ import annotations

import numpy as np
from PIL import Image
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from context.localization import LocalizationController
from context.viewmodels import GraphViewModel


class PreviewPanel(QWidget):
    exportAvailabilityChanged = pyqtSignal(bool)
    saveRequested = pyqtSignal()

    def __init__(
        self,
        graph_vm: GraphViewModel,
        localization_controller: LocalizationController,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._localization = localization_controller
        self._image_label = QLabel(self._localization.tr("preview.unavailable"))
        self._image_label.setObjectName("secondaryLabel")
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_label.setMinimumSize(280, 220)
        self._save_button = QPushButton()
        self._save_button.clicked.connect(lambda: self.saveRequested.emit())
        self._current_pixmap: QPixmap | None = None
        self._current_image: np.ndarray | None = None

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._image_label)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)
        layout.addWidget(self._save_button, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(scroll)

        graph_vm.previewUpdated.connect(self.set_image)
        self._localization.localeChanged.connect(self._on_locale_changed)
        self._retranslate_ui()
        self._set_export_enabled(False)

    def has_image(self) -> bool:
        return self._current_image is not None

    def has_exportable_image(self) -> bool:
        return self._current_image is not None

    def current_image(self) -> np.ndarray | None:
        if self._current_image is None:
            return None
        return self._current_image.copy()

    def save_png(self, file_path: str) -> None:
        if self._current_image is None:
            raise ValueError(self._localization.tr("preview.export.unavailable"))
        Image.fromarray(self._current_image, "RGB").save(file_path, format="PNG")

    def set_image(self, image: np.ndarray | None) -> None:
        if image is None:
            self._current_image = None
            self._current_pixmap = None
            self._image_label.setPixmap(QPixmap())
            self._image_label.setText(self._localization.tr("preview.unavailable"))
            self._set_export_enabled(False)
            return

        display_image = np.ascontiguousarray(image.copy())
        self._current_image = display_image
        height, width, channels = display_image.shape
        bytes_per_line = channels * width
        qimage = QImage(
            display_image.data,
            width,
            height,
            bytes_per_line,
            QImage.Format.Format_RGB888,
        ).copy()
        pixmap = QPixmap.fromImage(qimage)
        self._current_pixmap = pixmap
        self._image_label.setText("")
        self._image_label.setPixmap(
            pixmap.scaled(
                480,
                320,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        self._set_export_enabled(True)

    def _on_locale_changed(self, _locale_code: str) -> None:
        if self._current_pixmap is None:
            self._image_label.setText(self._localization.tr("preview.unavailable"))
        self._retranslate_ui()

    def _set_export_enabled(self, enabled: bool) -> None:
        self._save_button.setEnabled(enabled)
        self.exportAvailabilityChanged.emit(enabled)

    def _retranslate_ui(self) -> None:
        self._save_button.setText(self._localization.tr("action.save_preview"))
