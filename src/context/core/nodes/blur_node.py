from __future__ import annotations

from typing import Mapping

import cv2

from ..pipeline.node import ImageArray, Node


class BlurNode(Node):
    def __init__(self, node_id: str, kernel_size: int = 5) -> None:
        super().__init__(
            id=node_id,
            type_name="blur",
            title="Blur",
            input_ports=("image",),
            output_ports=("image",),
            params={"kernel_size": self._normalize_kernel_size(kernel_size)},
        )

    def set_param(self, key: str, value: int) -> None:
        if key == "kernel_size":
            value = self._normalize_kernel_size(value)
        super().set_param(key, value)

    def process(self, inputs: Mapping[str, ImageArray | None]) -> ImageArray | None:
        image = inputs.get("image")
        if image is None:
            return None
        kernel_size = self._normalize_kernel_size(self.params.get("kernel_size", 5))
        return cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)

    @staticmethod
    def _normalize_kernel_size(value: int) -> int:
        kernel_size = max(1, int(value))
        if kernel_size % 2 == 0:
            kernel_size += 1
        return min(kernel_size, 31)
