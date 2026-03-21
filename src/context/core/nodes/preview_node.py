from __future__ import annotations

from typing import Mapping

from ..pipeline.node import ImageArray, Node


class PreviewNode(Node):
    def __init__(self, node_id: str) -> None:
        super().__init__(
            id=node_id,
            type_name="preview",
            title="Preview",
            input_ports=("image",),
            output_ports=(),
            params={},
        )

    def process(self, inputs: Mapping[str, ImageArray | None]) -> ImageArray | None:
        image = inputs.get("image")
        return None if image is None else image.copy()
