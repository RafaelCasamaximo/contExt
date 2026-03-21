from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from io import BytesIO
import base64
import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from .graph import Connection, Graph
from .node import Node


PIPELINE_FORMAT = "context.pipeline"
PIPELINE_VERSION = 1
PIPELINE_EXTENSION = ".ctxp"
SUPPORTED_NODE_TYPES = ("source", "blur", "preview")


class PipelineSerializationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class LoadedPipelineNode:
    node: Node
    position: tuple[float, float]


@dataclass(frozen=True, slots=True)
class PipelineDocument:
    nodes: tuple[LoadedPipelineNode, ...]
    connections: tuple[Connection, ...]


def export_pipeline_payload(
    graph: Graph,
    node_positions: Mapping[str, tuple[float, float]],
) -> dict[str, Any]:
    nodes_payload: list[dict[str, Any]] = []
    for node_id in sorted(graph.nodes):
        node = graph.nodes[node_id]
        x, y = node_positions.get(node_id, (0.0, 0.0))
        entry: dict[str, Any] = {
            "id": node.id,
            "type": node.type_name,
            "position": {"x": float(x), "y": float(y)},
            "params": dict(node.params),
        }
        if node.type_name == "source" and getattr(node, "image", None) is not None:
            entry["state"] = {
                "image_png_base64": _encode_image(node.image),
                "image_name": Path(node.image_path).name if node.image_path else "source.png",
            }
        nodes_payload.append(entry)

    connections_payload = [
        {
            "source_node_id": connection.source_node_id,
            "source_port": connection.source_port,
            "target_node_id": connection.target_node_id,
            "target_port": connection.target_port,
        }
        for connection in graph.list_connections()
    ]

    return {
        "format": PIPELINE_FORMAT,
        "version": PIPELINE_VERSION,
        "nodes": nodes_payload,
        "connections": connections_payload,
    }


def load_pipeline_payload(payload: object) -> PipelineDocument:
    if not isinstance(payload, dict):
        raise PipelineSerializationError("Pipeline payload must be a JSON object.")
    if payload.get("format") != PIPELINE_FORMAT:
        raise PipelineSerializationError("Unsupported pipeline format.")

    version = payload.get("version")
    if version != PIPELINE_VERSION:
        raise PipelineSerializationError(f"Unsupported pipeline version: {version!r}.")

    raw_nodes = payload.get("nodes")
    raw_connections = payload.get("connections")
    if not isinstance(raw_nodes, list):
        raise PipelineSerializationError("Pipeline payload must contain a 'nodes' list.")
    if not isinstance(raw_connections, list):
        raise PipelineSerializationError("Pipeline payload must contain a 'connections' list.")

    loaded_nodes: list[LoadedPipelineNode] = []
    graph = Graph()
    for raw_node in raw_nodes:
        loaded_node = _load_node_entry(raw_node)
        graph.add_node(loaded_node.node.clone())
        loaded_nodes.append(loaded_node)

    for raw_connection in raw_connections:
        connection = _load_connection_entry(raw_connection)
        graph.connect(
            connection.source_node_id,
            connection.source_port,
            connection.target_node_id,
            connection.target_port,
        )

    return PipelineDocument(tuple(loaded_nodes), tuple(graph.list_connections()))


def read_pipeline_file(path: str | Path) -> PipelineDocument:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PipelineSerializationError("Pipeline file is not valid JSON.") from exc
    except OSError as exc:
        raise PipelineSerializationError("Pipeline file could not be read.") from exc
    return load_pipeline_payload(payload)


def write_pipeline_file(
    path: str | Path,
    graph: Graph,
    node_positions: Mapping[str, tuple[float, float]],
) -> dict[str, Any]:
    payload = export_pipeline_payload(graph, node_positions)
    try:
        Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError as exc:
        raise PipelineSerializationError("Pipeline file could not be written.") from exc
    return payload


def _load_node_entry(raw_node: object) -> LoadedPipelineNode:
    if not isinstance(raw_node, dict):
        raise PipelineSerializationError("Every node entry must be an object.")

    node_id = raw_node.get("id")
    node_type = raw_node.get("type")
    params = raw_node.get("params", {})
    position = raw_node.get("position")
    state = raw_node.get("state", {})

    if not isinstance(node_id, str) or not node_id:
        raise PipelineSerializationError("Every node must have a non-empty 'id'.")
    if node_type not in SUPPORTED_NODE_TYPES:
        raise PipelineSerializationError(f"Unsupported node type: {node_type!r}.")
    if not isinstance(params, dict):
        raise PipelineSerializationError(f"Node '{node_id}' has invalid params.")
    if not isinstance(position, dict):
        raise PipelineSerializationError(f"Node '{node_id}' must define a position object.")

    x = _coerce_number(position.get("x"), f"Node '{node_id}' has an invalid x position.")
    y = _coerce_number(position.get("y"), f"Node '{node_id}' has an invalid y position.")

    node = _instantiate_node(node_id, node_type, params, state)
    return LoadedPipelineNode(node=node, position=(x, y))


def _load_connection_entry(raw_connection: object) -> Connection:
    if not isinstance(raw_connection, dict):
        raise PipelineSerializationError("Every connection entry must be an object.")

    source_node_id = raw_connection.get("source_node_id")
    source_port = raw_connection.get("source_port")
    target_node_id = raw_connection.get("target_node_id")
    target_port = raw_connection.get("target_port")
    values = (source_node_id, source_port, target_node_id, target_port)
    if not all(isinstance(value, str) and value for value in values):
        raise PipelineSerializationError("Connections must define source and target node/port ids.")
    return Connection(source_node_id, source_port, target_node_id, target_port)


def _instantiate_node(node_id: str, node_type: str, params: dict[str, Any], state: object) -> Node:
    if node_type == "source":
        from ..nodes.source_node import SourceNode

        node = SourceNode(node_id)
        if state is not None and not isinstance(state, dict):
            raise PipelineSerializationError(f"Node '{node_id}' has invalid state data.")
        if isinstance(state, dict) and "image_png_base64" in state:
            encoded_image = state.get("image_png_base64")
            image_name = state.get("image_name")
            if not isinstance(encoded_image, str) or not encoded_image:
                raise PipelineSerializationError(f"Node '{node_id}' has an invalid embedded image.")
            if image_name is not None and not isinstance(image_name, str):
                raise PipelineSerializationError(f"Node '{node_id}' has an invalid embedded image name.")
            node.set_image(_decode_image(encoded_image), image_name or "source.png")
        return node

    if node_type == "blur":
        from ..nodes.blur_node import BlurNode

        kernel_size = params.get("kernel_size", 5)
        try:
            node = BlurNode(node_id, int(kernel_size))
        except (TypeError, ValueError) as exc:
            raise PipelineSerializationError(f"Node '{node_id}' has an invalid kernel size.") from exc
        for key, value in params.items():
            if key == "kernel_size":
                continue
            node.set_param(key, value)
        return node

    if node_type == "preview":
        from ..nodes.preview_node import PreviewNode

        node = PreviewNode(node_id)
        for key, value in params.items():
            node.set_param(key, value)
        return node

    raise PipelineSerializationError(f"Unsupported node type: {node_type!r}.")


def _encode_image(image: np.ndarray) -> str:
    buffer = BytesIO()
    Image.fromarray(image, "RGB").save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def _decode_image(encoded_image: str) -> np.ndarray:
    try:
        image_bytes = base64.b64decode(encoded_image.encode("ascii"))
    except (ValueError, UnicodeEncodeError) as exc:
        raise PipelineSerializationError("Embedded source image is not valid base64.") from exc

    try:
        with Image.open(BytesIO(image_bytes)) as image:
            rgb = image.convert("RGB")
            return np.array(rgb, dtype=np.uint8)
    except OSError as exc:
        raise PipelineSerializationError("Embedded source image is not a valid PNG.") from exc


def _coerce_number(value: object, message: str) -> float:
    if isinstance(value, bool):
        raise PipelineSerializationError(message)
    if not isinstance(value, (int, float)):
        raise PipelineSerializationError(message)
    return float(value)
