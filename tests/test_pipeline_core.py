from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from context.core.nodes import BlurNode, PreviewNode, SourceNode
from context.core.pipeline import Executor, Graph, Node


class TrackingNode(Node):
    def __init__(self, node_id: str, call_log: list[str], source_value: int | None = None) -> None:
        super().__init__(
            id=node_id,
            type_name="tracking",
            title=node_id,
            input_ports=() if source_value is not None else ("image",),
            output_ports=("image",),
            params={},
        )
        self._call_log = call_log
        self._source_value = source_value

    def process(self, inputs):
        self._call_log.append(self.id)
        if self._source_value is not None:
            return np.full((6, 6, 3), self._source_value, dtype=np.uint8)
        image = inputs.get("image")
        return None if image is None else image.copy()


class PipelineCoreTests(unittest.TestCase):
    def test_graph_enforces_singletons_input_ownership_and_cycle_rejection(self) -> None:
        graph = Graph()
        graph.add_node(SourceNode("source-1"))
        graph.add_node(BlurNode("blur-1"))
        graph.add_node(BlurNode("blur-2"))
        graph.add_node(PreviewNode("preview-1"))

        with self.assertRaises(ValueError):
            graph.add_node(SourceNode("source-2"))

        graph.connect("source-1", "image", "blur-1", "image")
        graph.connect("blur-1", "image", "blur-2", "image")
        graph.connect("blur-2", "image", "preview-1", "image")

        with self.assertRaises(ValueError):
            graph.connect("source-1", "image", "preview-1", "image")

        with self.assertRaises(ValueError):
            graph.connect("blur-2", "image", "blur-1", "image")

    def test_executor_only_recomputes_impacted_descendants(self) -> None:
        call_log: list[str] = []
        graph = Graph()
        graph.add_node(TrackingNode("source", call_log, source_value=32))
        graph.add_node(TrackingNode("left-1", call_log))
        graph.add_node(TrackingNode("left-2", call_log))
        graph.add_node(TrackingNode("right-1", call_log))

        graph.connect("source", "image", "left-1", "image")
        graph.connect("left-1", "image", "left-2", "image")
        graph.connect("source", "image", "right-1", "image")

        first_result = Executor.execute(graph, {}, {"source"})
        self.assertEqual(call_log, ["source", "left-1", "right-1", "left-2"])
        self.assertEqual(first_result.results["left-2"].shape, (6, 6, 3))

        call_log.clear()
        second_result = Executor.execute(graph, first_result.results, {"left-1"})
        self.assertEqual(call_log, ["left-1", "left-2"])
        self.assertNotIn("right-1", call_log)
        self.assertIn("right-1", second_result.results)

    def test_blur_node_preserves_shape_and_changes_image(self) -> None:
        source = SourceNode("source")
        preview = PreviewNode("preview")
        blur = BlurNode("blur", kernel_size=7)

        image = np.zeros((32, 32, 3), dtype=np.uint8)
        image[:, ::4] = 255
        source.set_image(image)

        graph = Graph()
        graph.add_node(source)
        graph.add_node(blur)
        graph.add_node(preview)
        graph.connect("source", "image", "blur", "image")
        graph.connect("blur", "image", "preview", "image")

        result = Executor.execute(graph, {}, {"source"}).results["preview"]
        self.assertIsNotNone(result)
        self.assertEqual(result.shape, image.shape)
        self.assertEqual(result.dtype, image.dtype)
        self.assertFalse(np.array_equal(result, image))


if __name__ == "__main__":
    unittest.main()
