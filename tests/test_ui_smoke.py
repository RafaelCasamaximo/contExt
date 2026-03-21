from __future__ import annotations

import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from context.views.main_window import MainWindow


class UiSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_main_window_graph_flow_updates_preview(self) -> None:
        window = MainWindow()
        window.show()
        try:
            self.assertEqual(window.theme_name, "material_dark")
            self.assertEqual(window.locale_code, "pt-BR")
            self.assertNotEqual(window.theme_controller.theme.canvas_bg.lower(), "#ffffff")
            self.assertNotEqual(window.graph_view.backgroundBrush().color().name().lower(), "#ffffff")
            window.set_locale("en")
            self.assertEqual(window.locale_code, "en")
            self.assertEqual(window._file_menu.title(), "File")
            window.set_theme("material_light")
            self.assertEqual(window.theme_name, "material_light")
            self.assertEqual(window.graph_scene.theme_name, "material_light")

            blur_vm = window.graph_viewmodel.add_blur_node((240.0, 120.0))
            self.assertIsNotNone(blur_vm)
            source_vm = window.graph_viewmodel.graph.find_node_by_type("source")
            preview_vm = window.graph_viewmodel.graph.find_node_by_type("preview")
            assert source_vm is not None
            assert preview_vm is not None

            blur_item = window.graph_scene.node_item(blur_vm.node_id)
            self.assertIsNotNone(blur_item)
            self.assertTrue(
                window.graph_viewmodel.connect_nodes(source_vm.id, "image", blur_vm.node_id, "image")
            )
            self.assertTrue(
                window.graph_viewmodel.connect_nodes(blur_vm.node_id, "image", preview_vm.id, "image")
            )

            with tempfile.TemporaryDirectory() as tmpdir:
                path = Path(tmpdir) / "ui-sample.png"
                Image.fromarray(self._sample_image(), "RGB").save(path)
                window.graph_viewmodel.load_image(str(path))

            self._wait_until(lambda: window.preview_panel.has_image())
            first_preview = window.graph_viewmodel.current_preview()
            self.assertIsNotNone(first_preview)
            self.assertTrue(window._save_preview_action.isEnabled())
            self.assertEqual(window._open_pipeline_action.text(), "Open Pipeline...")
            self.assertEqual(window.preview_panel._save_button.text(), "Save Preview as PNG...")

            slider = blur_item.embedded_slider()
            self.assertIsNotNone(slider)
            self.assertEqual(slider.value(), 5)
            slider.setValue(9)

            self._wait_until(
                lambda: window.graph_viewmodel.current_preview() is not None
                and not np.array_equal(window.graph_viewmodel.current_preview(), first_preview),
                timeout_ms=5000,
            )
            self.assertEqual(window.graph_viewmodel.get_node(blur_vm.node_id).params["kernel_size"], 9)
            self.assertEqual(slider.value(), 9)
            window.set_theme("material_dark")
            self.assertEqual(window.theme_name, "material_dark")
            self.assertEqual(blur_item.theme_name, "material_dark")
            self.assertTrue(window.preview_panel.has_image())
            with tempfile.TemporaryDirectory() as tmpdir:
                preview_path = Path(tmpdir) / "preview-output"
                pipeline_path = Path(tmpdir) / "graph-state"
                self.assertTrue(window.save_preview_to_path(str(preview_path)))
                self.assertTrue((Path(tmpdir) / "preview-output.png").exists())
                saved_preview = np.array(Image.open(Path(tmpdir) / "preview-output.png").convert("RGB"))
                self.assertEqual(saved_preview.shape, first_preview.shape)

                self.assertTrue(window.save_pipeline_to_path(str(pipeline_path)))
                saved_pipeline = Path(tmpdir) / "graph-state.ctxp"
                self.assertTrue(saved_pipeline.exists())

                restored = MainWindow()
                restored.show()
                try:
                    self.assertTrue(restored.load_pipeline_from_path(str(saved_pipeline)))
                    self._wait_until(lambda: restored.preview_panel.has_image())
                    self.assertEqual(len(restored.graph_viewmodel.graph.nodes), 3)
                    self.assertEqual(len(restored.graph_viewmodel.graph.list_connections()), 2)
                    self.assertEqual(
                        restored.graph_viewmodel.get_node(blur_vm.node_id).params["kernel_size"],
                        9,
                    )
                finally:
                    restored.close()
        finally:
            window.close()

    def _wait_until(self, predicate, timeout_ms: int = 3000) -> None:
        deadline = time.monotonic() + (timeout_ms / 1000)
        while time.monotonic() < deadline:
            self.app.processEvents()
            if predicate():
                return
            QTest.qWait(20)
        self.fail("Timed out waiting for the Qt UI to settle.")

    @staticmethod
    def _sample_image() -> np.ndarray:
        image = np.zeros((64, 64, 3), dtype=np.uint8)
        image[:, ::8] = 255
        image[:, :, 1] = 48
        return image


if __name__ == "__main__":
    unittest.main()
