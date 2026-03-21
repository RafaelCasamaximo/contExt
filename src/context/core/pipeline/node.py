from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Mapping
import copy

import numpy as np

ImageArray = np.ndarray


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

    @abstractmethod
    def process(self, inputs: Mapping[str, ImageArray | None]) -> ImageArray | None:
        raise NotImplementedError
