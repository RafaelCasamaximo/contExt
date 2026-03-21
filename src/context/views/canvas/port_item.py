from __future__ import annotations

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QPainter, QPen
from PyQt6.QtWidgets import QGraphicsObject, QGraphicsSceneMouseEvent

from context.views.theme import ThemeController


class PortItem(QGraphicsObject):
    RADIUS = 7.0

    def __init__(
        self,
        node_id: str,
        port_name: str,
        direction: str,
        theme_controller: ThemeController,
        parent: QGraphicsObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.node_id = node_id
        self.port_name = port_name
        self.direction = direction
        self._theme_controller = theme_controller
        self._snap_highlighted = False
        self._disposed = False
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setAcceptHoverEvents(True)
        self._theme_controller.themeChanged.connect(self._on_theme_changed)

    def boundingRect(self) -> QRectF:
        diameter = self.RADIUS * 2
        return QRectF(-self.RADIUS, -self.RADIUS, diameter, diameter)

    def paint(self, painter: QPainter, option, widget=None) -> None:  # pragma: no cover - Qt paint path
        del option, widget
        theme = self._theme_controller.theme
        color = QColor(theme.output_port if self.direction == "output" else theme.input_port)
        border_color = QColor(theme.surface)
        border_width = 2.0
        brush_color = color
        if self._snap_highlighted:
            border_color = QColor(theme.selection)
            border_width = 3.0
            brush_color = QColor(theme.selection)
        painter.setPen(QPen(border_color, border_width))
        painter.setBrush(QBrush(brush_color))
        painter.drawEllipse(self.boundingRect())
        inner_rect = self.boundingRect().adjusted(4.0, 4.0, -4.0, -4.0)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(theme.surface))
        painter.drawEllipse(inner_rect)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self.direction == "output" and event.button() == Qt.MouseButton.LeftButton:
            scene = self.scene()
            if scene is not None and hasattr(scene, "begin_connection"):
                scene.begin_connection(self)
            event.accept()
            return
        super().mousePressEvent(event)

    def set_snap_highlighted(self, highlighted: bool) -> None:
        if self._snap_highlighted == highlighted:
            return
        self._snap_highlighted = highlighted
        self.update()

    def dispose(self) -> None:
        if self._disposed:
            return
        self._disposed = True
        try:
            self._theme_controller.themeChanged.disconnect(self._on_theme_changed)
        except (TypeError, RuntimeError):
            pass

    def scene_center(self):
        return self.mapToScene(self.boundingRect().center())

    def _on_theme_changed(self, _theme) -> None:
        if not self._disposed:
            self.update()
