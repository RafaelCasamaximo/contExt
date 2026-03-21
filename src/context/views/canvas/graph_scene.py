from __future__ import annotations

from math import floor

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QPainter, QPen, QTransform
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsSceneContextMenuEvent, QGraphicsSceneMouseEvent, QMenu

from context.core.pipeline import Connection
from context.localization import LocalizationController
from context.viewmodels import GraphViewModel, NodeViewModel
from context.views.theme import ThemeController

from .edge_item import EdgeItem
from .node_item import NodeItem
from .port_item import PortItem


class GraphScene(QGraphicsScene):
    SNAP_RADIUS = 28.0

    def __init__(
        self,
        graph_vm: GraphViewModel,
        theme_controller: ThemeController,
        localization_controller: LocalizationController,
    ) -> None:
        super().__init__()
        self._graph_vm = graph_vm
        self._theme_controller = theme_controller
        self._localization = localization_controller
        self._node_items: dict[str, NodeItem] = {}
        self._edge_items: dict[tuple[str, str, str, str], EdgeItem] = {}
        self._drag_source_port: PortItem | None = None
        self._temporary_edge: EdgeItem | None = None
        self._snap_target_port: PortItem | None = None
        self.setSceneRect(-1600.0, -1200.0, 3200.0, 2400.0)

        self._graph_vm.nodeAdded.connect(self._add_node_item)
        self._graph_vm.nodeRemoved.connect(self._remove_node_item)
        self._graph_vm.nodeChanged.connect(self._refresh_node_item)
        self._graph_vm.connectionAdded.connect(self._add_edge_item)
        self._graph_vm.connectionRemoved.connect(self._remove_edge_item)
        self._graph_vm.nodeResultUpdated.connect(self._set_result_state)
        self.selectionChanged.connect(self._handle_selection_changed)
        self._theme_controller.themeChanged.connect(self._on_theme_changed)
        self._localization.localeChanged.connect(self._on_locale_changed)

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
            snap_target = self._find_snap_target(event.scenePos())
            self._set_snap_target(snap_target)
            if snap_target is not None:
                self._temporary_edge.set_target_point(snap_target.scene_center())
            else:
                self._temporary_edge.set_target_point(event.scenePos())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self._drag_source_port is not None and self._temporary_edge is not None:
            release_snap_target = self._find_snap_target(event.scenePos())
            if release_snap_target is not None:
                self._set_snap_target(release_snap_target)
            target = self._snap_target_port or self._port_at(event.scenePos())
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
        add_actions: dict[object, str] = {}
        for category, definitions in self._graph_vm.grouped_menu_definitions().items():
            submenu = menu.addMenu(self._localization.tr(f"menu.node_category.{category}"))
            for definition in definitions:
                action = submenu.addAction(self._localization.tr(definition.title_key))
                if definition.singleton and self._graph_vm.graph.find_node_by_type(definition.type_name) is not None:
                    action.setEnabled(False)
                add_actions[action] = definition.type_name
        delete_selected = None
        if self.selectedItems():
            menu.addSeparator()
            delete_selected = menu.addAction(self._localization.tr("graph.menu.delete_selected"))

        chosen = menu.exec(event.screenPos())
        scene_pos = event.scenePos()
        if chosen in add_actions:
            self._graph_vm.add_node(add_actions[chosen], (scene_pos.x(), scene_pos.y()))
        elif chosen == delete_selected:
            self.delete_selected_items()
        event.accept()

    def _add_node_item(self, node_vm: NodeViewModel) -> None:
        item = NodeItem(node_vm, self._graph_vm, self._theme_controller, self._localization)
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
            item.refresh_from_model()

    def _set_result_state(self, node_id: str, result) -> None:
        item = self._node_items.get(node_id)
        if item is not None:
            item.set_result_state(result is not None)
            item.refresh_from_model()

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
        self._set_snap_target(None)
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

    def _on_locale_changed(self, _locale_code: str) -> None:
        for node_item in self._node_items.values():
            node_item.update()
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

    def _find_snap_target(self, scene_pos: QPointF) -> PortItem | None:
        if self._drag_source_port is None:
            return None

        radius = self.SNAP_RADIUS
        search_rect = QRectF(scene_pos.x() - radius, scene_pos.y() - radius, radius * 2, radius * 2)
        best_target: PortItem | None = None
        best_distance_sq: float | None = None

        for item in self.items(search_rect, Qt.ItemSelectionMode.IntersectsItemShape):
            if not isinstance(item, PortItem):
                continue
            if not self._is_valid_target(self._drag_source_port, item):
                continue
            center = item.scene_center()
            dx = center.x() - scene_pos.x()
            dy = center.y() - scene_pos.y()
            distance_sq = (dx * dx) + (dy * dy)
            if distance_sq > radius * radius:
                continue
            if best_distance_sq is None or distance_sq < best_distance_sq:
                best_distance_sq = distance_sq
                best_target = item
        return best_target

    def _set_snap_target(self, port_item: PortItem | None) -> None:
        if self._snap_target_port is port_item:
            return
        if self._snap_target_port is not None:
            self._snap_target_port.set_snap_highlighted(False)
        self._snap_target_port = port_item
        if self._snap_target_port is not None:
            self._snap_target_port.set_snap_highlighted(True)

    def _is_valid_target(self, source_port: PortItem, target_port: PortItem | None) -> bool:
        if target_port is None:
            return False
        if source_port.node_id == target_port.node_id:
            return False
        if source_port.direction != "output" or target_port.direction != "input":
            return False
        if self._graph_vm.graph.get_input_connection(target_port.node_id, target_port.port_name) is not None:
            return False
        if self._graph_vm.graph.has_path(target_port.node_id, source_port.node_id):
            return False
        return True

    @staticmethod
    def _edge_key(connection: Connection) -> tuple[str, str, str, str]:
        return (
            connection.source_node_id,
            connection.source_port,
            connection.target_node_id,
            connection.target_port,
        )
