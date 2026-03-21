from __future__ import annotations

import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
from PIL import Image

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from context.core.nodes import BlurNode
from context.viewmodels import GraphViewModel


class GraphViewModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.graph_vm = GraphViewModel(bootstrap_default_graph=False, debounce_ms=0)
        source = self.graph_vm.add_source_node((0.0, 0.0))
        blur = self.graph_vm.add_blur_node((220.0, 0.0))
        preview = self.graph_vm.add_preview_node((440.0, 0.0))
        assert source is not None
        assert preview is not None
        self.source_id = source.node_id
        self.blur_id = blur.node_id
        self.preview_id = preview.node_id
        self.graph_vm.connect_nodes(self.source_id, "image", self.blur_id, "image")
        self.graph_vm.connect_nodes(self.blur_id, "image", self.preview_id, "image")

    def test_disconnect_clears_preview_after_reprocessing(self) -> None:
        self.graph_vm.set_source_image(self._sample_image())
        self._wait_until(lambda: self.graph_vm.current_preview() is not None)

        self.graph_vm.disconnect_nodes(self.blur_id, "image", self.preview_id, "image")
        self._wait_until(lambda: self.graph_vm.current_preview() is None)

    def test_latest_generation_wins(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sample.png"
            Image.fromarray(self._sample_image(), "RGB").save(path)
            self.graph_vm.load_image(str(path))
        self._wait_until(lambda: self.graph_vm.current_preview() is not None)

        original_process = BlurNode.process

        def delayed_process(node, inputs):
            kernel_size = int(node.params["kernel_size"])
            if kernel_size == 5:
                time.sleep(0.25)
            else:
                time.sleep(0.02)
            result = original_process(node, inputs)
            if result is not None:
                result = result.copy()
                result[0, 0, 0] = kernel_size
            return result

        with patch.object(BlurNode, "process", autospec=True, side_effect=delayed_process):
            self.graph_vm.set_node_param(self.blur_id, "kernel_size", 5)
            QTest.qWait(10)
            self.graph_vm.set_node_param(self.blur_id, "kernel_size", 9)

            self._wait_until(
                lambda: self.graph_vm.current_preview() is not None and self.graph_vm.current_preview()[0, 0, 0] == 9,
                timeout_ms=5000,
            )
            QTest.qWait(400)
            self.app.processEvents()

        preview = self.graph_vm.current_preview()
        self.assertIsNotNone(preview)
        self.assertEqual(int(preview[0, 0, 0]), 9)

    def _wait_until(self, predicate, timeout_ms: int = 3000) -> None:
        deadline = time.monotonic() + (timeout_ms / 1000)
        while time.monotonic() < deadline:
            self.app.processEvents()
            if predicate():
                return
            QTest.qWait(20)
        self.fail("Timed out waiting for asynchronous graph processing.")

    @staticmethod
    def _sample_image() -> np.ndarray:
        image = np.zeros((48, 48, 3), dtype=np.uint8)
        image[:, ::4] = 255
        image[::6, :] = 96
        return image


if __name__ == "__main__":
    unittest.main()
