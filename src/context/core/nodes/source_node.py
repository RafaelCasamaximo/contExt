from __future__ import annotations

from typing import Mapping

from ..pipeline.node import ImageArray, Node


class SourceNode(Node):
    def __init__(self, node_id: str) -> None:
        super().__init__(
            id=node_id,
            type_name="source",
            title="Source",
            input_ports=(),
            output_ports=("image",),
            params={},
        )
        self.image: ImageArray | None = None
        self.image_path: str | None = None

    def set_image(self, image: ImageArray | None, image_path: str | None = None) -> None:
        self.image = None if image is None else image.copy()
        self.image_path = image_path

    def process(self, inputs: Mapping[str, ImageArray | None]) -> ImageArray | None:
        del inputs
        return None if self.image is None else self.image.copy()
