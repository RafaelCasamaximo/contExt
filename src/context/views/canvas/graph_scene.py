from __future__ import annotations

from math import floor

from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QColor, QPainter, QPen, QTransform
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsSceneContextMenuEvent, QGraphicsSceneMouseEvent, QMenu

from context.core.pipeline import Connection
from context.viewmodels import GraphViewModel, NodeViewModel
from context.views.theme import ThemeController

from .edge_item import EdgeItem
from .node_item import NodeItem
from .port_item import PortItem


class GraphScene(QGraphicsScene):
    def __init__(self, graph_vm: GraphViewModel, theme_controller: ThemeController) -> None:
        super().__init__()
        self._graph_vm = graph_vm
        self._theme_controller = theme_controller
        self._node_items: dict[str, NodeItem] = {}
        self._edge_items: dict[tuple[str, str, str, str], EdgeItem] = {}
        self._drag_source_port: PortItem | None = None
        self._temporary_edge: EdgeItem | None = None
        self.setSceneRect(-1600.0, -1200.0, 3200.0, 2400.0)

        self._graph_vm.nodeAdded.connect(self._add_node_item)
        self._graph_vm.nodeRemoved.connect(self._remove_node_item)
        self._graph_vm.nodeChanged.connect(self._refresh_node_item)
        self._graph_vm.connectionAdded.connect(self._add_edge_item)
        self._graph_vm.connectionRemoved.connect(self._remove_edge_item)
        self._graph_vm.nodeResultUpdated.connect(self._set_result_state)
        self.selectionChanged.connect(self._handle_selection_changed)
        self._theme_controller.themeChanged.connect(self._on_theme_changed)

        for node_vm in self._graph_vm.list_nodes():
            self._add_node_item(node_vm)
        for connection in self._graph_vm.graph.list_connections():
            self._add_edge_item(connection)

    @property
    def theme_name(self) -> str:
        return self._theme_controller.theme_name

    def node_item(self, node_id: str) -> NodeItem | None:
        return self._node_items.get(node_id)

    def begin_connection(self, port_item: PortItem) -> None:
        self._clear_temporary_edge()
        self._drag_source_port = port_item
        self._temporary_edge = EdgeItem(port_item, self._theme_controller)
        self._temporary_edge.set_target_point(port_item.scene_center())
        self.addItem(self._temporary_edge)

    def drawBackground(self, painter: QPainter, rect) -> None:  # pragma: no cover - Qt paint path
        theme = self._theme_controller.theme
        painter.fillRect(rect, QColor(theme.canvas_bg))
        self._draw_grid(painter, rect, 28, QColor(theme.grid_minor), 1.0)
        self._draw_grid(painter, rect, 140, QColor(theme.grid_major), 1.2)

    def delete_selected_items(self) -> None:
        selected_items = list(self.selectedItems())
        for item in selected_items:
            if isinstance(item, EdgeItem) and item.connection is not None:
                connection = item.connection
                self._graph_vm.disconnect_nodes(
                    connection.source_node_id,
                    connection.source_port,
                    connection.target_node_id,
                    connection.target_port,
                )
        for item in selected_items:
            if isinstance(item, NodeItem):
                self._graph_vm.remove_node(item.node_vm.node_id)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self._temporary_edge is not None:
            self._temporary_edge.set_target_point(event.scenePos())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self._drag_source_port is not None and self._temporary_edge is not None:
            target = self._port_at(event.scenePos())
            if self._is_valid_target(self._drag_source_port, target):
                self._graph_vm.connect_nodes(
                    self._drag_source_port.node_id,
                    self._drag_source_port.port_name,
                    target.node_id,
                    target.port_name,
                )
            self._clear_temporary_edge()
        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event: QGraphicsSceneContextMenuEvent) -> None:
        menu = QMenu()
        add_source = menu.addAction("Add Source")
        add_blur = menu.addAction("Add Blur")
        add_preview = menu.addAction("Add Preview")
        delete_selected = None
        if self.selectedItems():
            menu.addSeparator()
            delete_selected = menu.addAction("Delete Selected")

        chosen = menu.exec(event.screenPos())
        scene_pos = event.scenePos()
        if chosen == add_source:
            self._graph_vm.add_node("source", (scene_pos.x(), scene_pos.y()))
        elif chosen == add_blur:
            self._graph_vm.add_node("blur", (scene_pos.x(), scene_pos.y()))
        elif chosen == add_preview:
            self._graph_vm.add_node("preview", (scene_pos.x(), scene_pos.y()))
        elif chosen == delete_selected:
            self.delete_selected_items()
        event.accept()

    def _add_node_item(self, node_vm: NodeViewModel) -> None:
        item = NodeItem(node_vm, self._graph_vm, self._theme_controller)
        item.geometryChanged.connect(self._update_edges_for_node)
        self._node_items[node_vm.node_id] = item
        self.addItem(item)

    def _remove_node_item(self, node_id: str) -> None:
        item = self._node_items.pop(node_id, None)
        if item is None:
            return
        self.removeItem(item)

    def _add_edge_item(self, connection: Connection) -> None:
        source_item = self._node_items[connection.source_node_id]
        target_item = self._node_items[connection.target_node_id]
        edge = EdgeItem(
            source_item.output_port(connection.source_port),
            self._theme_controller,
            target_item.input_port(connection.target_port),
            connection,
        )
        key = self._edge_key(connection)
        self._edge_items[key] = edge
        self.addItem(edge)

    def _remove_edge_item(self, connection: Connection) -> None:
        edge = self._edge_items.pop(self._edge_key(connection), None)
        if edge is not None:
            self.removeItem(edge)

    def _refresh_node_item(self, node_id: str) -> None:
        item = self._node_items.get(node_id)
        if item is not None:
            item.update()

    def _set_result_state(self, node_id: str, result) -> None:
        item = self._node_items.get(node_id)
        if item is not None:
            item.set_result_state(result is not None)

    def _update_edges_for_node(self, node_id: str) -> None:
        for key, edge in self._edge_items.items():
            if node_id in (key[0], key[2]):
                edge.update_path()

    def _handle_selection_changed(self) -> None:
        node_id = None
        for item in self.selectedItems():
            if isinstance(item, NodeItem):
                node_id = item.node_vm.node_id
                break
        self._graph_vm.set_selected_node(node_id)

    def _clear_temporary_edge(self) -> None:
        if self._temporary_edge is not None:
            self.removeItem(self._temporary_edge)
        self._drag_source_port = None
        self._temporary_edge = None

    def _on_theme_changed(self, _theme) -> None:
        for node_item in self._node_items.values():
            node_item.update()
        for edge in self._edge_items.values():
            edge.update_path()
        if self._temporary_edge is not None:
            self._temporary_edge.update_path()
        self.update(self.sceneRect())
        for view in self.views():
            view.viewport().update()

    @staticmethod
    def _draw_grid(painter: QPainter, rect, spacing: int, color: QColor, width: float) -> None:
        pen = QPen(color, width)
        painter.setPen(pen)

        left = floor(rect.left() / spacing) * spacing
        top = floor(rect.top() / spacing) * spacing

        x = left
        while x <= rect.right():
            painter.drawLine(int(x), int(rect.top()), int(x), int(rect.bottom()))
            x += spacing

        y = top
        while y <= rect.bottom():
            painter.drawLine(int(rect.left()), int(y), int(rect.right()), int(y))
            y += spacing

    def _port_at(self, scene_pos: QPointF) -> PortItem | None:
        item = self.itemAt(scene_pos, QTransform())
        return item if isinstance(item, PortItem) else None

    @staticmethod
    def _is_valid_target(source_port: PortItem, target_port: PortItem | None) -> bool:
        if target_port is None:
            return False
        if source_port.node_id == target_port.node_id:
            return False
        return source_port.direction == "output" and target_port.direction == "input"

    @staticmethod
    def _edge_key(connection: Connection) -> tuple[str, str, str, str]:
        return (
            connection.source_node_id,
            connection.source_port,
            connection.target_node_id,
            connection.target_port,
        )
