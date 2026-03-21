from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Mapping
import copy

import numpy as np

ImageArray = np.ndarray
NodeVisuals = dict[str, ImageArray | None]


@dataclass
class Node(ABC):
    id: str
    type_name: str
    title: str
    input_ports: tuple[str, ...] = ()
    output_ports: tuple[str, ...] = ()
    params: dict[str, Any] = field(default_factory=dict)

    def clone(self) -> "Node":
        return copy.deepcopy(self)

    def set_param(self, key: str, value: Any) -> None:
        self.params[key] = value

    def process_with_visuals(
        self,
        inputs: Mapping[str, ImageArray | None],
    ) -> tuple[ImageArray | None, NodeVisuals]:
        result = self.process(inputs)
        return result, self.visual_outputs(inputs, result)

    def visual_outputs(
        self,
        inputs: Mapping[str, ImageArray | None],
        result: ImageArray | None,
    ) -> NodeVisuals:
        del inputs, result
        return {}

    @abstractmethod
    def process(self, inputs: Mapping[str, ImageArray | None]) -> ImageArray | None:
        raise NotImplementedError
