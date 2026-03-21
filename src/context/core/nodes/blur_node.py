from __future__ import annotations

from .filter_nodes import GaussianBlurNode


class BlurNode(GaussianBlurNode):
    def __init__(self, node_id: str, kernel_size: int = 5) -> None:
        super().__init__(node_id=node_id, kernel_size=kernel_size, type_name="blur", title="Blur")
