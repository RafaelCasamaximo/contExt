from __future__ import annotations

from dataclasses import dataclass

from .graph import Graph
from .node import ImageArray, NodeVisuals


@dataclass(slots=True)
class ExecutionResult:
    generation: int
    invalidated: frozenset[str]
    impacted_order: tuple[str, ...]
    results: dict[str, ImageArray | None]
    visuals: dict[str, NodeVisuals]


class Executor:
    @staticmethod
    def execute(
        graph: Graph,
        cached_results: dict[str, ImageArray | None] | None,
        invalidated: set[str],
        generation: int = 0,
        cached_visuals: dict[str, NodeVisuals] | None = None,
    ) -> ExecutionResult:
        cached = dict(cached_results or {})
        visuals = {node_id: dict(node_visuals) for node_id, node_visuals in (cached_visuals or {}).items()}
        impacted = graph.collect_downstream(invalidated)
        if not impacted:
            return ExecutionResult(generation, frozenset(), tuple(), cached, visuals)

        for node_id in graph.topological_order(impacted):
            node = graph.nodes[node_id]
            inputs = {
                port: cached.get(connection.source_node_id) if connection is not None else None
                for port in node.input_ports
                for connection in [graph.get_input_connection(node_id, port)]
            }
            result, node_visuals = node.process_with_visuals(inputs)
            cached[node_id] = result
            if node_visuals:
                visuals[node_id] = node_visuals
            else:
                visuals.pop(node_id, None)

        return ExecutionResult(
            generation,
            frozenset(invalidated),
            tuple(graph.topological_order(impacted)),
            cached,
            visuals,
        )
