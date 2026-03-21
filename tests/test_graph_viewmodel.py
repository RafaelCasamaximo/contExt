from __future__ import annotations

import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
import json

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

    def test_pipeline_roundtrip_restores_positions_connections_and_preview(self) -> None:
        self.graph_vm.set_node_param(self.blur_id, "kernel_size", 11)
        self.graph_vm.set_source_image(self._sample_image(), "embedded-source.png")
        self._wait_until(lambda: self.graph_vm.current_preview() is not None)
        original_preview = self.graph_vm.current_preview()
        self.assertIsNotNone(original_preview)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "roundtrip.ctxp"
            self.assertTrue(self.graph_vm.save_pipeline(str(path)))
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["format"], "context.pipeline")
            self.assertEqual(payload["version"], 1)
            source_entry = next(entry for entry in payload["nodes"] if entry["type"] == "source")
            self.assertIn("image_png_base64", source_entry["state"])

            restored = GraphViewModel(bootstrap_default_graph=False, debounce_ms=0)
            self.assertTrue(restored.load_pipeline(str(path)))

            self._wait_until(lambda: restored.current_preview() is not None)
            self.assertEqual(set(restored.graph.nodes), {self.source_id, self.blur_id, self.preview_id})
            self.assertEqual(restored.node_viewmodels[self.source_id].position, (0.0, 0.0))
            self.assertEqual(restored.node_viewmodels[self.blur_id].position, (220.0, 0.0))
            self.assertEqual(restored.node_viewmodels[self.preview_id].position, (440.0, 0.0))
            self.assertEqual(restored.get_node(self.blur_id).params["kernel_size"], 11)
            self.assertEqual(len(restored.graph.list_connections()), 2)
            self.assertTrue(np.array_equal(restored.current_preview(), original_preview))
            restored_source = restored.get_node(self.source_id)
            self.assertEqual(restored_source.image_path, "embedded-source.png")

    def test_invalid_pipeline_payload_is_rejected_without_mutating_graph(self) -> None:
        previous_node_ids = set(self.graph_vm.graph.nodes)
        previous_connections = list(self.graph_vm.graph.list_connections())
        payload = {
            "format": "context.pipeline",
            "version": 999,
            "nodes": [],
            "connections": [],
        }

        self.assertFalse(self.graph_vm.load_pipeline_payload(payload))
        self.assertEqual(set(self.graph_vm.graph.nodes), previous_node_ids)
        self.assertEqual(self.graph_vm.graph.list_connections(), previous_connections)

    def test_frequency_node_exposes_spectrum_visual(self) -> None:
        graph_vm = GraphViewModel(bootstrap_default_graph=False, debounce_ms=0)
        source = graph_vm.add_source_node((0.0, 0.0))
        frequency = graph_vm.add_node("frequency_domain_filter", (220.0, 0.0))
        preview = graph_vm.add_preview_node((440.0, 0.0))
        assert source is not None
        assert frequency is not None
        assert preview is not None

        graph_vm.connect_nodes(source.node_id, "image", frequency.node_id, "image")
        graph_vm.connect_nodes(frequency.node_id, "image", preview.node_id, "image")
        graph_vm.set_node_param(frequency.node_id, "mode", "low_pass")
        graph_vm.set_source_image(self._sample_image())

        self._wait_until(lambda: graph_vm.current_preview() is not None)
        self._wait_until(lambda: graph_vm.node_visual(frequency.node_id, "frequency_spectrum") is not None)

        spectrum = graph_vm.node_visual(frequency.node_id, "frequency_spectrum")
        spatial = graph_vm.current_preview()
        self.assertIsNotNone(spectrum)
        self.assertIsNotNone(spatial)
        self.assertEqual(spectrum.shape[2], 3)
        self.assertEqual(spectrum.dtype, np.uint8)
        self.assertFalse(np.array_equal(spectrum, spatial))

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
