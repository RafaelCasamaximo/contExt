from __future__ import annotations

import numpy as np
from PIL import Image
from PyQt6.QtCore import QPoint, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QImage, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsView,
    QLabel,
    QStackedLayout,
    QVBoxLayout,
    QWidget,
)

from context.localization import LocalizationController
from context.viewmodels import GraphViewModel


class PreviewCanvasView(QGraphicsView):
    _MIN_ZOOM = 0.05
    _MAX_ZOOM = 64.0
    _ZOOM_FACTOR = 1.12

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self._pixmap_item = QGraphicsPixmapItem()
        self._middle_pan_active = False
        self._last_pan_pos = QPoint()
        self._fit_pending = False

        self._pixmap_item.setTransformationMode(Qt.TransformationMode.FastTransformation)
        self._scene.addItem(self._pixmap_item)
        self.setScene(self._scene)
        self.setObjectName("previewCanvasView")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setRenderHints(QPainter.RenderHint.TextAntialiasing)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def has_image(self) -> bool:
        pixmap = self._pixmap_item.pixmap()
        return not pixmap.isNull()

    def current_zoom(self) -> float:
        return float(self.transform().m11())

    def uses_nearest_sampling(self) -> bool:
        return (
            self._pixmap_item.transformationMode() == Qt.TransformationMode.FastTransformation
            and not bool(self.renderHints() & QPainter.RenderHint.SmoothPixmapTransform)
        )

    def set_pixmap(self, pixmap: QPixmap | None) -> None:
        if pixmap is None or pixmap.isNull():
            self._pixmap_item.setPixmap(QPixmap())
            self._scene.setSceneRect(QRectF())
            self._fit_pending = False
            self.resetTransform()
            return

        self._pixmap_item.setPixmap(pixmap)
        self._pixmap_item.setTransformationMode(Qt.TransformationMode.FastTransformation)
        self._scene.setSceneRect(self._pixmap_item.boundingRect())
        self.fit_to_image()

    def fit_to_image(self) -> None:
        if not self.has_image():
            self.resetTransform()
            self._fit_pending = False
            return
        if self.viewport().width() <= 1 or self.viewport().height() <= 1:
            self._fit_pending = True
            return
        self.resetTransform()
        self.fitInView(self._pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)
        self._fit_pending = False

    def zoom_by_delta(self, angle_delta_y: int) -> None:
        if not self.has_image() or angle_delta_y == 0:
            return
        factor = self._ZOOM_FACTOR if angle_delta_y > 0 else 1.0 / self._ZOOM_FACTOR
        current_zoom = max(self._MIN_ZOOM, self.current_zoom())
        next_zoom = max(self._MIN_ZOOM, min(self._MAX_ZOOM, current_zoom * factor))
        actual_factor = next_zoom / current_zoom
        if actual_factor == 1.0:
            return
        self.scale(actual_factor, actual_factor)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self._middle_pan_active = True
            self._last_pan_pos = event.position().toPoint()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._middle_pan_active:
            current_pos = event.position().toPoint()
            delta = current_pos - self._last_pan_pos
            self._last_pan_pos = current_pos
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if self._middle_pan_active and event.button() == Qt.MouseButton.MiddleButton:
            self._middle_pan_active = False
            self.unsetCursor()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event) -> None:
        self.zoom_by_delta(event.angleDelta().y())
        event.accept()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self._fit_pending:
            self.fit_to_image()


class PreviewPanel(QWidget):
    exportAvailabilityChanged = pyqtSignal(bool)

    def __init__(
        self,
        graph_vm: GraphViewModel,
        localization_controller: LocalizationController,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._localization = localization_controller
        self._empty_label = QLabel()
        self._empty_label.setObjectName("previewEmptyState")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setMinimumSize(280, 220)
        self._empty_label.setWordWrap(True)
        self._view = PreviewCanvasView()
        self._stack = QStackedLayout()
        self._current_pixmap: QPixmap | None = None
        self._current_image: np.ndarray | None = None

        self._stack.addWidget(self._empty_label)
        self._stack.addWidget(self._view)
        self._stack.setCurrentWidget(self._empty_label)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)
        layout.addLayout(self._stack)

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

    def canvas_view(self) -> PreviewCanvasView:
        return self._view

    def uses_nearest_sampling(self) -> bool:
        return self._view.uses_nearest_sampling()

    def save_png(self, file_path: str) -> None:
        if self._current_image is None:
            raise ValueError(self._localization.tr("preview.export.unavailable"))
        Image.fromarray(self._current_image, "RGB").save(file_path, format="PNG")

    def set_image(self, image: np.ndarray | None) -> None:
        if image is None:
            self._current_image = None
            self._current_pixmap = None
            self._view.set_pixmap(None)
            self._stack.setCurrentWidget(self._empty_label)
            self._empty_label.setText(self._localization.tr("preview.unavailable"))
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
        self._view.set_pixmap(pixmap)
        self._stack.setCurrentWidget(self._view)
        self._set_export_enabled(True)

    def _on_locale_changed(self, _locale_code: str) -> None:
        if self._current_pixmap is None:
            self._empty_label.setText(self._localization.tr("preview.unavailable"))
        self._retranslate_ui()

    def _set_export_enabled(self, enabled: bool) -> None:
        self.exportAvailabilityChanged.emit(enabled)

    def _retranslate_ui(self) -> None:
        if self._current_image is None:
            self._empty_label.setText(self._localization.tr("preview.unavailable"))
