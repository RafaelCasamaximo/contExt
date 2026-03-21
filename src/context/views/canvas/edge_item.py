from __future__ import annotations

from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QColor, QPainterPath, QPen
from PyQt6.QtWidgets import QGraphicsPathItem

from context.core.pipeline import Connection
from context.views.theme import ThemeController


class EdgeItem(QGraphicsPathItem):
    def __init__(
        self,
        source_port,
        theme_controller: ThemeController,
        target_port=None,
        connection: Connection | None = None,
    ) -> None:
        super().__init__()
        self.source_port = source_port
        self._theme_controller = theme_controller
        self.target_port = target_port
        self.connection = connection
        self._target_point = QPointF()
        self._disposed = False
        self.setFlag(self.GraphicsItemFlag.ItemIsSelectable, True)
        self.setZValue(-1)
        self._theme_controller.themeChanged.connect(self._on_theme_changed)
        self.update_path()

    def set_target_point(self, point: QPointF) -> None:
        self._target_point = point
        self.update_path()

    def update_path(self) -> None:
        start = self.source_port.scene_center()
        end = self.target_port.scene_center() if self.target_port is not None else self._target_point
        dx = max(80.0, abs(end.x() - start.x()) * 0.5)
        path = QPainterPath(start)
        path.cubicTo(start.x() + dx, start.y(), end.x() - dx, end.y(), end.x(), end.y())
        self.setPath(path)

        theme = self._theme_controller.theme
        color = QColor(theme.edge if self.connection is not None else theme.edge_preview)
        if self.isSelected():
            color = QColor(theme.edge_selected)
        pen_width = 3.0 if self.connection is not None else 2.4
        self.setPen(
            QPen(
                color,
                pen_width,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin,
            )
        )

    def itemChange(self, change, value):
        if change == self.GraphicsItemChange.ItemSelectedHasChanged:
            self.update_path()
        return super().itemChange(change, value)

    def dispose(self) -> None:
        if self._disposed:
            return
        self._disposed = True
        try:
            self._theme_controller.themeChanged.disconnect(self._on_theme_changed)
        except (TypeError, RuntimeError):
            pass

    def _on_theme_changed(self, _theme) -> None:
        if not self._disposed:
            self.update_path()
