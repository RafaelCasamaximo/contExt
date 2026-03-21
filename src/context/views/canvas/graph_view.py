from __future__ import annotations

from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import QFrame, QGraphicsView, QWidget

from context.views.theme import ThemeController

from .graph_scene import GraphScene


class GraphView(QGraphicsView):
    def __init__(self, scene: GraphScene, theme_controller: ThemeController, parent: QWidget | None = None) -> None:
        super().__init__(scene, parent)
        self._theme_controller = theme_controller
        self._disposed = False
        self._middle_pan_active = False
        self._last_pan_pos = QPoint()
        self.setObjectName("graphView")
        self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._theme_controller.themeChanged.connect(self._on_theme_changed)

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

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete):
            scene = self.scene()
            if isinstance(scene, GraphScene):
                scene.delete_selected_items()
            event.accept()
            return
        super().keyPressEvent(event)

    def wheelEvent(self, event) -> None:
        factor = 1.12 if event.angleDelta().y() > 0 else 1 / 1.12
        self.scale(factor, factor)

    def dispose(self) -> None:
        if self._disposed:
            return
        self._disposed = True
        try:
            self._theme_controller.themeChanged.disconnect(self._on_theme_changed)
        except (TypeError, RuntimeError):
            pass

    def closeEvent(self, event) -> None:
        self.dispose()
        super().closeEvent(event)

    def _on_theme_changed(self, _theme) -> None:
        if not self._disposed:
            self.viewport().update()
