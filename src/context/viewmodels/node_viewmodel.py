from __future__ import annotations

from PyQt6.QtCore import QObject, pyqtSignal

from context.core.pipeline.node import Node


class NodeViewModel(QObject):
    positionChanged = pyqtSignal(str, float, float)
    updated = pyqtSignal(str)

    def __init__(self, node: Node, x: float = 0.0, y: float = 0.0) -> None:
        super().__init__()
        self._node = node
        self._position = (x, y)

    @property
    def node_id(self) -> str:
        return self._node.id

    @property
    def node_type(self) -> str:
        return self._node.type_name

    @property
    def title(self) -> str:
        return self._node.title

    @property
    def params(self) -> dict[str, object]:
        return dict(self._node.params)

    @property
    def position(self) -> tuple[float, float]:
        return self._position

    def set_position(self, x: float, y: float) -> None:
        if self._position == (x, y):
            return
        self._position = (x, y)
        self.positionChanged.emit(self.node_id, x, y)

    def sync_from_node(self, node: Node) -> None:
        self._node = node
        self.updated.emit(node.id)
