from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import QFrame, QGraphicsView, QWidget

from context.views.theme import ThemeController

from .graph_scene import GraphScene


class GraphView(QGraphicsView):
    def __init__(self, scene: GraphScene, theme_controller: ThemeController, parent: QWidget | None = None) -> None:
        super().__init__(scene, parent)
        self.setObjectName("graphView")
        self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setFrameShape(QFrame.Shape.NoFrame)
        theme_controller.themeChanged.connect(lambda _: self.viewport().update())

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
