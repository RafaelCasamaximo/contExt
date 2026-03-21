from __future__ import annotations

import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QLabel, QScrollArea, QVBoxLayout, QWidget

from context.viewmodels import GraphViewModel


class PreviewPanel(QWidget):
    def __init__(self, graph_vm: GraphViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._image_label = QLabel("Preview unavailable")
        self._image_label.setObjectName("secondaryLabel")
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_label.setMinimumSize(280, 220)
        self._current_pixmap: QPixmap | None = None

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._image_label)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.addWidget(scroll)

        graph_vm.previewUpdated.connect(self.set_image)

    def has_image(self) -> bool:
        return self._current_pixmap is not None

    def set_image(self, image: np.ndarray | None) -> None:
        if image is None:
            self._current_pixmap = None
            self._image_label.setPixmap(QPixmap())
            self._image_label.setText("Preview unavailable")
            return

        height, width, channels = image.shape
        bytes_per_line = channels * width
        qimage = QImage(
            image.data,
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
