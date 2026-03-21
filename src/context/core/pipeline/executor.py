from __future__ import annotations

from dataclasses import dataclass

from .graph import Graph
from .node import ImageArray


@dataclass(slots=True)
class ExecutionResult:
    generation: int
    invalidated: frozenset[str]
    impacted_order: tuple[str, ...]
    results: dict[str, ImageArray | None]


class Executor:
    @staticmethod
    def execute(
        graph: Graph,
        cached_results: dict[str, ImageArray | None] | None,
        invalidated: set[str],
        generation: int = 0,
    ) -> ExecutionResult:
        cached = dict(cached_results or {})
        impacted = graph.collect_downstream(invalidated)
        if not impacted:
            return ExecutionResult(generation, frozenset(), tuple(), cached)

        for node_id in graph.topological_order(impacted):
            node = graph.nodes[node_id]
            inputs = {
                port: cached.get(connection.source_node_id) if connection is not None else None
                for port in node.input_ports
                for connection in [graph.get_input_connection(node_id, port)]
            }
            cached[node_id] = node.process(inputs)

        return ExecutionResult(generation, frozenset(invalidated), tuple(graph.topological_order(impacted)), cached)
