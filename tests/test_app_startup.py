from __future__ import annotations

import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from context.app import App
from context.meta import APP_VERSION
from context.viewmodels import GraphViewModel


class AppStartupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_start_screen_new_project_waits_for_user_and_persists_preferences(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            prefs_path = Path(tmpdir) / "preferences.json"
            app = App(preferences_path=prefs_path)
            app.start()
            try:
                self._wait_until(lambda: app.splash.isVisible())
                self.assertTrue(app.splash.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground))
                self.assertIsNone(app.window)
                QTest.qWait(200)
                self.app.processEvents()
                self.assertIsNone(app.window)

                app.splash.set_theme_selection("material_light")
                app.splash.set_locale_selection("en")
                self.app.processEvents()

                self.assertIn(APP_VERSION, app.splash.version_label.text())
                app.splash.new_project_button.click()

                self._wait_until(lambda: app.window is not None and app.window.isVisible(), timeout_ms=4000)
                self.assertFalse(app.splash.isVisible())
                self.assertEqual(app.window.theme_name, "material_light")
                self.assertEqual(app.window.locale_code, "en")
                self.assertEqual(len(app.window.graph_viewmodel.graph.nodes), 2)

                saved = json.loads(prefs_path.read_text(encoding="utf-8"))
                self.assertEqual(saved["theme"], "material_light")
                self.assertEqual(saved["locale"], "en")
            finally:
                app.shutdown()

    def test_start_screen_open_project_loads_pipeline(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline_path = Path(tmpdir) / "startup-load.ctxp"
            self._build_pipeline_file(pipeline_path)

            app = App(preferences_path=Path(tmpdir) / "preferences.json")
            app.start()
            try:
                self._wait_until(lambda: app.splash.isVisible())
                with patch("context.app.QFileDialog.getOpenFileName", return_value=(str(pipeline_path), "Context Pipeline")):
                    app.splash.open_project_button.click()

                self._wait_until(lambda: app.window is not None and app.window.isVisible(), timeout_ms=4000)
                self.assertFalse(app.splash.isVisible())
                self.assertEqual(len(app.window.graph_viewmodel.graph.nodes), 3)
                self.assertEqual(len(app.window.graph_viewmodel.graph.list_connections()), 2)
                self.assertEqual(app.window.graph_viewmodel.graph.find_node_by_type("blur").params["kernel_size"], 9)
            finally:
                app.shutdown()

    def test_start_screen_cancel_open_keeps_screen_visible(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = App(preferences_path=Path(tmpdir) / "preferences.json")
            app.start()
            try:
                self._wait_until(lambda: app.splash.isVisible())
                with patch("context.app.QFileDialog.getOpenFileName", return_value=("", "")):
                    app.splash.open_project_button.click()
                QTest.qWait(120)
                self.app.processEvents()
                self.assertTrue(app.splash.isVisible())
                self.assertIsNone(app.window)
            finally:
                app.shutdown()

    def _build_pipeline_file(self, pipeline_path: Path) -> None:
        graph_vm = GraphViewModel(bootstrap_default_graph=False, debounce_ms=0)
        source = graph_vm.add_source_node((0.0, 0.0))
        blur = graph_vm.add_blur_node((220.0, 0.0))
        preview = graph_vm.add_preview_node((440.0, 0.0))
        assert source is not None
        assert preview is not None
        graph_vm.connect_nodes(source.node_id, "image", blur.node_id, "image")
        graph_vm.connect_nodes(blur.node_id, "image", preview.node_id, "image")
        graph_vm.set_node_param(blur.node_id, "kernel_size", 9)
        self.assertTrue(graph_vm.save_pipeline(str(pipeline_path)))

    def _wait_until(self, predicate, timeout_ms: int = 3000) -> None:
        deadline = time.monotonic() + (timeout_ms / 1000)
        while time.monotonic() < deadline:
            self.app.processEvents()
            if predicate():
                return
            QTest.qWait(20)
        self.fail("Timed out waiting for the startup flow.")


if __name__ == "__main__":
    unittest.main()
