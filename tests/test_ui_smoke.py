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

from PyQt6.QtCore import QPointF, Qt, QEvent
from PyQt6.QtGui import QMouseEvent
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
            self.assertEqual(window.windowTitle(), "ContExt | untitled.ctxp")
            self.assertNotEqual(window.theme_controller.theme.canvas_bg.lower(), "#ffffff")
            self.assertNotEqual(window.graph_view.backgroundBrush().color().name().lower(), "#ffffff")
            window.set_locale("en")
            self.assertEqual(window.locale_code, "en")
            self.assertEqual(window._file_menu.title(), "File")
            self.assertEqual(window._histogram_dock.windowTitle(), "Histogram")
            window.set_theme("material_light")
            self.assertEqual(window.theme_name, "material_light")
            self.assertEqual(window.graph_scene.theme_name, "material_light")

            blur_vm = window.graph_viewmodel.add_blur_node((240.0, 120.0))
            self.assertIsNotNone(blur_vm)
            source_vm = window.graph_viewmodel.graph.find_node_by_type("source")
            preview_vm = window.graph_viewmodel.graph.find_node_by_type("preview")
            assert source_vm is not None
            assert preview_vm is not None

            source_item = window.graph_scene.node_item(source_vm.id)
            blur_item = window.graph_scene.node_item(blur_vm.node_id)
            preview_item = window.graph_scene.node_item(preview_vm.id)
            self.assertIsNotNone(source_item)
            self.assertIsNotNone(blur_item)
            self.assertIsNotNone(preview_item)
            assert source_item is not None
            assert blur_item is not None
            assert preview_item is not None
            self.assertTrue(
                window.graph_viewmodel.connect_nodes(source_vm.id, "image", blur_vm.node_id, "image")
            )
            self.assertTrue(
                window.graph_viewmodel.connect_nodes(blur_vm.node_id, "image", preview_vm.id, "image")
            )

            source_item = window.graph_scene.node_item(source_vm.id)
            blur_item = window.graph_scene.node_item(blur_vm.node_id)
            preview_item = window.graph_scene.node_item(preview_vm.id)
            self.assertIsNotNone(source_item)
            self.assertIsNotNone(blur_item)
            self.assertIsNotNone(preview_item)
            assert source_item is not None
            assert blur_item is not None
            assert preview_item is not None

            source_button = source_item.embedded_action_button()
            preview_button = preview_item.embedded_action_button()
            self.assertIsNotNone(source_button)
            self.assertIsNotNone(preview_button)
            assert source_button is not None
            assert preview_button is not None
            self.assertFalse(preview_button.isEnabled())

            with tempfile.TemporaryDirectory() as tmpdir:
                path = Path(tmpdir) / "ui-sample.png"
                Image.fromarray(self._sample_image(), "RGB").save(path)
                with patch("context.views.canvas.node_item.QFileDialog.getOpenFileName", return_value=(str(path), "Images")):
                    source_button.click()

            self._wait_until(lambda: window.preview_panel.has_image())
            first_preview = window.graph_viewmodel.current_preview()
            self.assertIsNotNone(first_preview)
            self.assertTrue(window._save_preview_action.isEnabled())
            self.assertTrue(window._save_histogram_action.isEnabled())
            self.assertEqual(window._open_pipeline_action.text(), "Open Pipeline...")
            self.assertEqual(source_button.text(), "Open Image...")
            self.assertEqual(preview_button.text(), "Save Preview\nas PNG...")
            self.assertTrue(preview_button.isEnabled())

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
            self.assertTrue(window.histogram_panel.has_image())
            with tempfile.TemporaryDirectory() as tmpdir:
                preview_path = Path(tmpdir) / "preview-output"
                pipeline_path = Path(tmpdir) / "graph-state"
                with patch("context.views.canvas.node_item.QFileDialog.getSaveFileName", return_value=(str(preview_path), "PNG")):
                    preview_button.click()
                self.assertTrue((Path(tmpdir) / "preview-output.png").exists())
                saved_preview = np.array(Image.open(Path(tmpdir) / "preview-output.png").convert("RGB"))
                self.assertEqual(saved_preview.shape, first_preview.shape)

                self.assertTrue(window.save_pipeline_to_path(str(pipeline_path)))
                saved_pipeline = Path(tmpdir) / "graph-state.ctxp"
                self.assertTrue(saved_pipeline.exists())
                self.assertEqual(window.windowTitle(), "ContExt | graph-state.ctxp")

                restored = MainWindow()
                restored.show()
                try:
                    self.assertTrue(restored.load_pipeline_from_path(str(saved_pipeline)))
                    self._wait_until(lambda: restored.preview_panel.has_image())
                    self.assertEqual(restored.windowTitle(), "ContExt | graph-state.ctxp")
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

    def test_loading_pipeline_then_switching_theme_does_not_crash(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline_path = Path(tmpdir) / "theme-reload.ctxp"

            source_window = MainWindow()
            source_window.show()
            try:
                blur_vm = source_window.graph_viewmodel.add_blur_node((240.0, 120.0))
                assert blur_vm is not None
                source_vm = source_window.graph_viewmodel.graph.find_node_by_type("source")
                preview_vm = source_window.graph_viewmodel.graph.find_node_by_type("preview")
                assert source_vm is not None
                assert preview_vm is not None
                self.assertTrue(source_window.graph_viewmodel.connect_nodes(source_vm.id, "image", blur_vm.node_id, "image"))
                self.assertTrue(source_window.graph_viewmodel.connect_nodes(blur_vm.node_id, "image", preview_vm.id, "image"))
                self.assertTrue(source_window.save_pipeline_to_path(str(pipeline_path)))
            finally:
                source_window.close()

            window = MainWindow()
            window.show()
            try:
                self.assertTrue(window.load_pipeline_from_path(str(pipeline_path)))
                self.app.processEvents()
                window.set_theme("material_light")
                self.app.processEvents()
                window.set_theme("material_dark")
                self.app.processEvents()
                self.assertEqual(window.theme_name, "material_dark")
                self.assertEqual(len(window.graph_scene._node_items), 3)
            finally:
                window.close()

    def test_loading_pipeline_after_source_image_is_set_does_not_crash(self) -> None:
        window = MainWindow()
        window.show()
        try:
            source_vm = window.graph_viewmodel.graph.find_node_by_type("source")
            preview_vm = window.graph_viewmodel.graph.find_node_by_type("preview")
            assert source_vm is not None
            assert preview_vm is not None

            with tempfile.TemporaryDirectory() as tmpdir:
                image_path = Path(tmpdir) / "reload-source.png"
                pipeline_path = Path(tmpdir) / "reload-source.ctxp"
                Image.fromarray(self._sample_image(), "RGB").save(image_path)
                window.graph_viewmodel.load_image(str(image_path))
                for _ in range(20):
                    self.app.processEvents()

                self.assertTrue(window.save_pipeline_to_path(str(pipeline_path)))
                self.assertTrue(window.load_pipeline_from_path(str(pipeline_path)))
                for _ in range(20):
                    self.app.processEvents()

                self.assertIsNotNone(window.graph_scene.node_item(source_vm.id))
                self.assertIsNotNone(window.graph_scene.node_item(preview_vm.id))
        finally:
            window.close()

    def test_deleting_multiple_selected_nodes_does_not_crash(self) -> None:
        window = MainWindow()
        window.show()
        try:
            source_vm = window.graph_viewmodel.graph.find_node_by_type("source")
            preview_vm = window.graph_viewmodel.graph.find_node_by_type("preview")
            blur_vm = window.graph_viewmodel.add_blur_node((240.0, 120.0))
            median_vm = window.graph_viewmodel.add_node("median_blur", (520.0, 120.0))
            assert source_vm is not None
            assert preview_vm is not None
            assert blur_vm is not None
            assert median_vm is not None

            self.assertTrue(window.graph_viewmodel.connect_nodes(source_vm.id, "image", blur_vm.node_id, "image"))
            self.assertTrue(window.graph_viewmodel.connect_nodes(blur_vm.node_id, "image", median_vm.node_id, "image"))
            self.assertTrue(window.graph_viewmodel.connect_nodes(median_vm.node_id, "image", preview_vm.id, "image"))
            window.graph_viewmodel.set_source_image(self._sample_image())
            for _ in range(20):
                self.app.processEvents()

            for node_id in (source_vm.id, blur_vm.node_id, median_vm.node_id):
                item = window.graph_scene.node_item(node_id)
                self.assertIsNotNone(item)
                assert item is not None
                item.setSelected(True)
            for _ in range(5):
                self.app.processEvents()

            window.graph_scene.delete_selected_items()
            for _ in range(20):
                self.app.processEvents()

            self.assertEqual(set(window.graph_viewmodel.graph.nodes), {preview_vm.id})
        finally:
            window.close()

    def test_graph_view_hides_scrollbars_and_supports_middle_mouse_pan(self) -> None:
        window = MainWindow()
        window.show()
        try:
            view = window.graph_view
            viewport = view.viewport()
            self.assertEqual(view.horizontalScrollBarPolicy(), Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.assertEqual(view.verticalScrollBarPolicy(), Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

            view.resize(640, 420)
            view.show()
            self.app.processEvents()
            view.horizontalScrollBar().setValue((view.horizontalScrollBar().maximum() + view.horizontalScrollBar().minimum()) // 2)
            view.verticalScrollBar().setValue((view.verticalScrollBar().maximum() + view.verticalScrollBar().minimum()) // 2)

            horizontal_before = view.horizontalScrollBar().value()
            vertical_before = view.verticalScrollBar().value()
            press_pos = QPointF(220.0, 180.0)
            move_pos = QPointF(260.0, 225.0)

            press_event = QMouseEvent(
                QEvent.Type.MouseButtonPress,
                press_pos,
                press_pos,
                Qt.MouseButton.MiddleButton,
                Qt.MouseButton.MiddleButton,
                Qt.KeyboardModifier.NoModifier,
            )
            move_event = QMouseEvent(
                QEvent.Type.MouseMove,
                move_pos,
                move_pos,
                Qt.MouseButton.NoButton,
                Qt.MouseButton.MiddleButton,
                Qt.KeyboardModifier.NoModifier,
            )
            release_event = QMouseEvent(
                QEvent.Type.MouseButtonRelease,
                move_pos,
                move_pos,
                Qt.MouseButton.MiddleButton,
                Qt.MouseButton.NoButton,
                Qt.KeyboardModifier.NoModifier,
            )

            QApplication.sendEvent(viewport, press_event)
            QApplication.sendEvent(viewport, move_event)
            QApplication.sendEvent(viewport, release_event)
            self.app.processEvents()

            self.assertNotEqual(view.horizontalScrollBar().value(), horizontal_before)
            self.assertNotEqual(view.verticalScrollBar().value(), vertical_before)
        finally:
            window.close()

    def test_preview_panel_supports_middle_mouse_pan_zoom_nearest_and_histogram(self) -> None:
        window = MainWindow()
        window.show()
        try:
            source_vm = window.graph_viewmodel.graph.find_node_by_type("source")
            preview_vm = window.graph_viewmodel.graph.find_node_by_type("preview")
            assert source_vm is not None
            assert preview_vm is not None
            self.assertTrue(window.graph_viewmodel.connect_nodes(source_vm.id, "image", preview_vm.id, "image"))

            source_item = window.graph_scene.node_item(source_vm.id)
            self.assertIsNotNone(source_item)
            assert source_item is not None
            source_button = source_item.embedded_action_button()
            self.assertIsNotNone(source_button)
            assert source_button is not None

            with tempfile.TemporaryDirectory() as tmpdir:
                path = Path(tmpdir) / "preview-large.png"
                Image.fromarray(self._sample_image(size=256), "RGB").save(path)
                with patch("context.views.canvas.node_item.QFileDialog.getOpenFileName", return_value=(str(path), "Images")):
                    source_button.click()

            self._wait_until(lambda: window.preview_panel.has_image() and window.histogram_panel.has_image())
            preview_view = window.preview_panel.canvas_view()
            viewport = preview_view.viewport()

            self.assertEqual(preview_view.horizontalScrollBarPolicy(), Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.assertEqual(preview_view.verticalScrollBarPolicy(), Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.assertTrue(window.preview_panel.uses_nearest_sampling())

            preview_view.resize(160, 160)
            preview_view.show()
            self.app.processEvents()

            zoom_before = preview_view.current_zoom()
            for _ in range(6):
                preview_view.zoom_by_delta(120)
            self.app.processEvents()
            self.assertGreater(preview_view.current_zoom(), zoom_before)

            horizontal_before = preview_view.horizontalScrollBar().value()
            vertical_before = preview_view.verticalScrollBar().value()
            press_pos = QPointF(90.0, 90.0)
            move_pos = QPointF(126.0, 132.0)

            press_event = QMouseEvent(
                QEvent.Type.MouseButtonPress,
                press_pos,
                press_pos,
                Qt.MouseButton.MiddleButton,
                Qt.MouseButton.MiddleButton,
                Qt.KeyboardModifier.NoModifier,
            )
            move_event = QMouseEvent(
                QEvent.Type.MouseMove,
                move_pos,
                move_pos,
                Qt.MouseButton.NoButton,
                Qt.MouseButton.MiddleButton,
                Qt.KeyboardModifier.NoModifier,
            )
            release_event = QMouseEvent(
                QEvent.Type.MouseButtonRelease,
                move_pos,
                move_pos,
                Qt.MouseButton.MiddleButton,
                Qt.MouseButton.NoButton,
                Qt.KeyboardModifier.NoModifier,
            )

            QApplication.sendEvent(viewport, press_event)
            QApplication.sendEvent(viewport, move_event)
            QApplication.sendEvent(viewport, release_event)
            self.app.processEvents()

            self.assertNotEqual(preview_view.horizontalScrollBar().value(), horizontal_before)
            self.assertNotEqual(preview_view.verticalScrollBar().value(), vertical_before)

            histograms = window.histogram_panel.channel_histograms()
            self.assertIsNotNone(histograms)
            assert histograms is not None
            luminance_histogram = window.histogram_panel.luminance_histogram()
            self.assertIsNotNone(luminance_histogram)
            assert luminance_histogram is not None
            preview_image = window.graph_viewmodel.current_preview()
            self.assertIsNotNone(preview_image)
            assert preview_image is not None
            expected_pixels = preview_image.shape[0] * preview_image.shape[1]
            self.assertEqual(len(histograms), 3)
            self.assertTrue(all(channel.shape == (256,) for channel in histograms))
            self.assertTrue(all(int(channel.sum()) == expected_pixels for channel in histograms))
            self.assertEqual(luminance_histogram.shape, (256,))
            self.assertEqual(int(luminance_histogram.sum()), expected_pixels)
            self.assertTrue(window._save_histogram_action.isEnabled())

            with tempfile.TemporaryDirectory() as tmpdir:
                histogram_path = Path(tmpdir) / "final-histogram"
                self.assertTrue(window.save_histogram_to_path(str(histogram_path)))
                self.assertTrue((Path(tmpdir) / "final-histogram.png").exists())
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
    def _sample_image(size: int = 64) -> np.ndarray:
        image = np.zeros((size, size, 3), dtype=np.uint8)
        image[:, ::8] = 255
        image[::8, :] = 200
        image[:, :, 1] = 48
        image[:, :, 2] = np.linspace(0, 255, size, dtype=np.uint8)
        return image


if __name__ == "__main__":
    unittest.main()
