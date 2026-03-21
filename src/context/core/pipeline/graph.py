from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from .node import Node


@dataclass(frozen=True, slots=True)
class Connection:
    source_node_id: str
    source_port: str
    target_node_id: str
    target_port: str


class Graph:
    _SINGLETON_TYPES = {"source", "preview"}

    def __init__(self) -> None:
        self.nodes: dict[str, Node] = {}
        self._input_bindings: dict[tuple[str, str], Connection] = {}
        self._output_bindings: dict[tuple[str, str], set[Connection]] = {}

    def clone(self) -> "Graph":
        clone = Graph()
        for node in self.nodes.values():
            clone.add_node(node.clone())
        for connection in self.list_connections():
            clone.connect(
                connection.source_node_id,
                connection.source_port,
                connection.target_node_id,
                connection.target_port,
            )
        return clone

    def add_node(self, node: Node) -> None:
        if node.id in self.nodes:
            raise ValueError(f"Node '{node.id}' already exists.")
        if node.type_name in self._SINGLETON_TYPES and self.find_node_by_type(node.type_name) is not None:
            raise ValueError(f"Only one '{node.type_name}' node is allowed.")
        self.nodes[node.id] = node
        for port in node.output_ports:
            self._output_bindings[(node.id, port)] = set()

    def remove_node(self, node_id: str) -> list[Connection]:
        node = self.nodes.get(node_id)
        if node is None:
            raise KeyError(f"Unknown node '{node_id}'.")

        removed = [
            connection
            for connection in self.list_connections()
            if connection.source_node_id == node_id or connection.target_node_id == node_id
        ]
        for connection in removed:
            self.disconnect(
                connection.source_node_id,
                connection.source_port,
                connection.target_node_id,
                connection.target_port,
            )
        for port in node.output_ports:
            self._output_bindings.pop((node.id, port), None)
        self.nodes.pop(node_id, None)
        return removed

    def connect(self, source_node_id: str, source_port: str, target_node_id: str, target_port: str) -> Connection:
        source = self._get_node(source_node_id)
        target = self._get_node(target_node_id)
        self._validate_output_port(source, source_port)
        self._validate_input_port(target, target_port)
        if source_node_id == target_node_id:
            raise ValueError("Self connections are not allowed.")
        if (target_node_id, target_port) in self._input_bindings:
            raise ValueError(f"Input port '{target_node_id}:{target_port}' already has a connection.")
        if self.has_path(target_node_id, source_node_id):
            raise ValueError("Connection would create a cycle.")

        connection = Connection(source_node_id, source_port, target_node_id, target_port)
        self._input_bindings[(target_node_id, target_port)] = connection
        self._output_bindings[(source_node_id, source_port)].add(connection)
        return connection

    def disconnect(self, source_node_id: str, source_port: str, target_node_id: str, target_port: str) -> None:
        connection = Connection(source_node_id, source_port, target_node_id, target_port)
        existing = self._input_bindings.get((target_node_id, target_port))
        if existing != connection:
            raise KeyError("Connection does not exist.")

        self._input_bindings.pop((target_node_id, target_port), None)
        outgoing = self._output_bindings.get((source_node_id, source_port))
        if outgoing is not None:
            outgoing.discard(connection)

    def find_node_by_type(self, type_name: str) -> Node | None:
        for node in self.nodes.values():
            if node.type_name == type_name:
                return node
        return None

    def list_connections(self) -> list[Connection]:
        connections: list[Connection] = []
        for binding in self._output_bindings.values():
            connections.extend(binding)
        return sorted(
            connections,
            key=lambda conn: (conn.source_node_id, conn.source_port, conn.target_node_id, conn.target_port),
        )

    def get_input_connection(self, node_id: str, port: str) -> Connection | None:
        return self._input_bindings.get((node_id, port))

    def predecessors(self, node_id: str) -> set[str]:
        return {
            connection.source_node_id
            for connection in self._input_bindings.values()
            if connection.target_node_id == node_id
        }

    def successors(self, node_id: str) -> set[str]:
        return {
            connection.target_node_id
            for connection in self.list_connections()
            if connection.source_node_id == node_id
        }

    def collect_downstream(self, start_node_ids: set[str]) -> set[str]:
        seeds = {node_id for node_id in start_node_ids if node_id in self.nodes}
        queue: deque[str] = deque(seeds)
        visited = set(seeds)
        while queue:
            current = queue.popleft()
            for successor in self.successors(current):
                if successor not in visited:
                    visited.add(successor)
                    queue.append(successor)
        return visited

    def topological_order(self, subset: set[str] | None = None) -> list[str]:
        if subset is None:
            subset = set(self.nodes)
        else:
            subset = {node_id for node_id in subset if node_id in self.nodes}

        indegree = {node_id: 0 for node_id in subset}
        for connection in self.list_connections():
            if connection.source_node_id in subset and connection.target_node_id in subset:
                indegree[connection.target_node_id] += 1

        queue: deque[str] = deque(
            node_id for node_id in self.nodes if node_id in subset and indegree[node_id] == 0
        )
        ordered: list[str] = []
        while queue:
            node_id = queue.popleft()
            ordered.append(node_id)
            for successor in sorted(self.successors(node_id)):
                if successor not in indegree:
                    continue
                indegree[successor] -= 1
                if indegree[successor] == 0:
                    queue.append(successor)

        if len(ordered) != len(subset):
            raise ValueError("Graph contains a cycle.")
        return ordered

    def has_path(self, source_node_id: str, target_node_id: str) -> bool:
        if source_node_id == target_node_id:
            return True

        queue: deque[str] = deque([source_node_id])
        visited = {source_node_id}
        while queue:
            current = queue.popleft()
            for successor in self.successors(current):
                if successor == target_node_id:
                    return True
                if successor not in visited:
                    visited.add(successor)
                    queue.append(successor)
        return False

    def _get_node(self, node_id: str) -> Node:
        node = self.nodes.get(node_id)
        if node is None:
            raise KeyError(f"Unknown node '{node_id}'.")
        return node

    @staticmethod
    def _validate_input_port(node: Node, port: str) -> None:
        if port not in node.input_ports:
            raise ValueError(f"Node '{node.id}' has no input port '{port}'.")

    @staticmethod
    def _validate_output_port(node: Node, port: str) -> None:
        if port not in node.output_ports:
            raise ValueError(f"Node '{node.id}' has no output port '{port}'.")
