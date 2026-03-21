from __future__ import annotations

import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

import numpy as np

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QSlider, QSpinBox

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from context.localization import LocalizationController
from context.viewmodels import GraphViewModel
from context.views.canvas import GraphScene
from context.views.panels.properties_panel import PropertiesPanel
from context.views.theme import ThemeController


class FilterNodeCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_grouped_menu_catalog_exposes_categories_and_hides_legacy_blur_alias(self) -> None:
        graph_vm = GraphViewModel(bootstrap_default_graph=False, debounce_ms=0)
        grouped = graph_vm.grouped_menu_definitions()

        self.assertEqual(tuple(grouped), ("input", "processing", "filtering", "frequency", "thresholding", "output"))
        self.assertEqual([definition.type_name for definition in grouped["input"]], ["source"])
        self.assertEqual([definition.type_name for definition in grouped["processing"]], ["crop"])
        self.assertIn("gaussian_blur", [definition.type_name for definition in grouped["filtering"]])
        self.assertIn("frequency_domain_filter", [definition.type_name for definition in grouped["frequency"]])
        self.assertIn("otsu_binarization", [definition.type_name for definition in grouped["thresholding"]])
        self.assertNotIn("blur", [definition.type_name for definition in grouped["filtering"]])

    def test_new_filter_pipeline_processes_and_roundtrips(self) -> None:
        graph_vm = GraphViewModel(bootstrap_default_graph=False, debounce_ms=0)
        source = graph_vm.add_source_node((0.0, 0.0))
        crop = graph_vm.add_node("crop", (220.0, 0.0))
        gaussian = graph_vm.add_node("gaussian_blur", (440.0, 0.0))
        grayscale = graph_vm.add_node("grayscale", (660.0, 0.0))
        otsu = graph_vm.add_node("otsu_binarization", (880.0, 0.0))
        preview = graph_vm.add_preview_node((1100.0, 0.0))
        assert source is not None
        assert crop is not None
        assert gaussian is not None
        assert grayscale is not None
        assert otsu is not None
        assert preview is not None

        graph_vm.connect_nodes(source.node_id, "image", crop.node_id, "image")
        graph_vm.connect_nodes(crop.node_id, "image", gaussian.node_id, "image")
        graph_vm.connect_nodes(gaussian.node_id, "image", grayscale.node_id, "image")
        graph_vm.connect_nodes(grayscale.node_id, "image", otsu.node_id, "image")
        graph_vm.connect_nodes(otsu.node_id, "image", preview.node_id, "image")

        graph_vm.set_node_param(crop.node_id, "end_x", 24)
        graph_vm.set_node_param(crop.node_id, "end_y", 24)
        graph_vm.set_node_param(gaussian.node_id, "kernel_size", 9)
        graph_vm.set_source_image(self._sample_image(), "sample.png")

        self._wait_until(lambda: graph_vm.current_preview() is not None)
        preview_image = graph_vm.current_preview()
        self.assertIsNotNone(preview_image)
        self.assertEqual(preview_image.shape, (24, 24, 3))
        self.assertTrue(set(np.unique(preview_image[:, :, 0]).tolist()).issubset({0, 255}))

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "filter-pipeline.ctxp"
            self.assertTrue(graph_vm.save_pipeline(str(path)))

            restored = GraphViewModel(bootstrap_default_graph=False, debounce_ms=0)
            self.assertTrue(restored.load_pipeline(str(path)))
            self._wait_until(lambda: restored.current_preview() is not None)

            restored_preview = restored.current_preview()
            self.assertIsNotNone(restored_preview)
            self.assertEqual(restored_preview.shape, (24, 24, 3))
            self.assertTrue(np.array_equal(restored_preview, preview_image))
            self.assertIn("gaussian_blur", {node.type_name for node in restored.graph.nodes.values()})

    def test_properties_panel_renders_dynamic_widgets_for_new_nodes(self) -> None:
        localization = LocalizationController(initial_locale="en")
        graph_vm = GraphViewModel(localization_controller=localization, bootstrap_default_graph=False, debounce_ms=0)
        grayscale = graph_vm.add_node("grayscale", (0.0, 0.0))
        frequency = graph_vm.add_node("frequency_domain_filter", (220.0, 0.0))
        assert grayscale is not None
        assert frequency is not None

        panel = PropertiesPanel(graph_vm, localization)
        graph_vm.set_selected_node(grayscale.node_id)
        self.app.processEvents()

        self.assertEqual(panel._form.rowCount(), 3)
        for row in range(panel._form.rowCount()):
            widget = panel._form.itemAt(row, QFormLayout.ItemRole.FieldRole).widget()
            self.assertIsInstance(widget, QCheckBox)

        graph_vm.set_selected_node(frequency.node_id)
        self.app.processEvents()

        self.assertEqual(panel._form.rowCount(), 4)
        mode_widget = panel._form.itemAt(0, QFormLayout.ItemRole.FieldRole).widget()
        cutoff_widget = panel._form.itemAt(1, QFormLayout.ItemRole.FieldRole).widget()
        self.assertIsInstance(mode_widget, QComboBox)
        self.assertIsInstance(cutoff_widget, QSpinBox)

    def test_crop_spinbox_survives_value_change_while_connected(self) -> None:
        localization = LocalizationController(initial_locale="en")
        graph_vm = GraphViewModel(localization_controller=localization, bootstrap_default_graph=False, debounce_ms=0)
        source = graph_vm.add_source_node((0.0, 0.0))
        crop = graph_vm.add_node("crop", (220.0, 0.0))
        gaussian = graph_vm.add_node("gaussian_blur", (440.0, 0.0))
        preview = graph_vm.add_preview_node((660.0, 0.0))
        assert source is not None
        assert crop is not None
        assert gaussian is not None
        assert preview is not None

        graph_vm.connect_nodes(source.node_id, "image", crop.node_id, "image")
        graph_vm.connect_nodes(crop.node_id, "image", gaussian.node_id, "image")
        graph_vm.connect_nodes(gaussian.node_id, "image", preview.node_id, "image")
        graph_vm.set_source_image(self._sample_image(), "sample.png")
        self._wait_until(lambda: graph_vm.current_preview() is not None)

        panel = PropertiesPanel(graph_vm, localization)
        graph_vm.set_selected_node(crop.node_id)
        self.app.processEvents()

        start_x_widget = panel._form.itemAt(0, QFormLayout.ItemRole.FieldRole).widget()
        self.assertIsInstance(start_x_widget, QSpinBox)
        start_x_widget.setValue(5)
        self.app.processEvents()

        self.assertEqual(start_x_widget.value(), 5)
        self.assertEqual(graph_vm.get_node(crop.node_id).params["start_x"], 5)
        self._wait_until(lambda: graph_vm.current_preview() is not None)

    def test_node_items_render_inline_controls_and_frequency_preview(self) -> None:
        localization = LocalizationController(initial_locale="en")
        theme = ThemeController(initial_theme="material_dark")
        graph_vm = GraphViewModel(localization_controller=localization, bootstrap_default_graph=False, debounce_ms=0)
        scene = GraphScene(graph_vm, theme, localization)

        source = graph_vm.add_source_node((0.0, 0.0))
        crop = graph_vm.add_node("crop", (220.0, 0.0))
        brightness = graph_vm.add_node("brightness_contrast", (440.0, 0.0))
        grayscale = graph_vm.add_node("grayscale", (660.0, 0.0))
        frequency = graph_vm.add_node("frequency_domain_filter", (880.0, 0.0))
        preview = graph_vm.add_preview_node((1100.0, 0.0))
        assert source is not None
        assert crop is not None
        assert brightness is not None
        assert grayscale is not None
        assert frequency is not None
        assert preview is not None

        graph_vm.connect_nodes(source.node_id, "image", crop.node_id, "image")
        graph_vm.connect_nodes(crop.node_id, "image", frequency.node_id, "image")
        graph_vm.connect_nodes(frequency.node_id, "image", preview.node_id, "image")

        crop_item = scene.node_item(crop.node_id)
        brightness_item = scene.node_item(brightness.node_id)
        grayscale_item = scene.node_item(grayscale.node_id)
        frequency_item = scene.node_item(frequency.node_id)
        self.assertIsNotNone(crop_item)
        self.assertIsNotNone(brightness_item)
        self.assertIsNotNone(grayscale_item)
        self.assertIsNotNone(frequency_item)
        assert crop_item is not None
        assert brightness_item is not None
        assert grayscale_item is not None
        assert frequency_item is not None

        self.assertIsInstance(crop_item.embedded_slider("start_x"), QSlider)
        self.assertIsInstance(crop_item.embedded_spinbox("start_x"), QSpinBox)
        self.assertIsInstance(brightness_item.embedded_slider("contrast"), QSlider)
        self.assertIsInstance(brightness_item.embedded_double_spinbox("contrast"), QDoubleSpinBox)
        self.assertIsInstance(grayscale_item.embedded_checkbox("exclude_red"), QCheckBox)
        self.assertIsInstance(frequency_item.embedded_combobox("mode"), QComboBox)
        self.assertIsInstance(frequency_item.embedded_slider("cutoff"), QSlider)

        brightness_spinbox = brightness_item.embedded_double_spinbox("contrast")
        grayscale_checkbox = grayscale_item.embedded_checkbox("exclude_red")
        frequency_combo = frequency_item.embedded_combobox("mode")
        assert brightness_spinbox is not None
        assert grayscale_checkbox is not None
        assert frequency_combo is not None

        brightness_spinbox.setValue(1.7)
        grayscale_checkbox.setChecked(True)
        frequency_combo.setCurrentIndex(frequency_combo.findData("low_pass"))
        self.app.processEvents()

        self.assertAlmostEqual(float(graph_vm.get_node(brightness.node_id).params["contrast"]), 1.7, places=1)
        self.assertTrue(graph_vm.get_node(grayscale.node_id).params["exclude_red"])
        self.assertEqual(graph_vm.get_node(frequency.node_id).params["mode"], "low_pass")

        graph_vm.set_source_image(self._sample_image(), "sample.png")
        self._wait_until(lambda: frequency_item.has_frequency_preview())

        crop_end_x_slider = crop_item.embedded_slider("end_x")
        frequency_cutoff_slider = frequency_item.embedded_slider("cutoff")
        assert crop_end_x_slider is not None
        assert frequency_cutoff_slider is not None
        self.assertEqual(crop_end_x_slider.maximum(), self._sample_image().shape[1])
        self.assertLess(frequency_cutoff_slider.maximum(), 2048)

    def _wait_until(self, predicate, timeout_ms: int = 3000) -> None:
        deadline = time.monotonic() + (timeout_ms / 1000)
        while time.monotonic() < deadline:
            self.app.processEvents()
            if predicate():
                return
            QTest.qWait(20)
        self.fail("Timed out waiting for graph processing.")

    @staticmethod
    def _sample_image() -> np.ndarray:
        image = np.zeros((48, 48, 3), dtype=np.uint8)
        image[:, :, 0] = 220
        image[::4, :, 1] = 180
        image[:, ::4, 2] = 255
        return image


if __name__ == "__main__":
    unittest.main()
