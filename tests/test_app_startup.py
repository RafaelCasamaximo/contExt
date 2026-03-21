from __future__ import annotations

import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from context.app import App


class AppStartupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_splash_interaction_cancels_auto_continue_and_persists_preferences(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            prefs_path = Path(tmpdir) / "preferences.json"
            app = App(preferences_path=prefs_path, bootstrap_interval_ms=40, auto_continue_ms=150)
            app.start()
            try:
                self._wait_until(lambda: app.splash.isVisible())
                app.splash.set_theme_selection("material_light")
                app.splash.set_locale_selection("en")

                self._wait_until(lambda: app.splash.is_ready)
                QTest.qWait(250)
                self.app.processEvents()

                self.assertTrue(app.window is not None)
                self.assertFalse(app.window.isVisible())

                app.splash.continue_button.click()
                self._wait_until(lambda: app.window is not None and app.window.isVisible(), timeout_ms=4000)
                self.assertEqual(app.window.theme_name, "material_light")
                self.assertEqual(app.window.locale_code, "en")

                saved = json.loads(prefs_path.read_text(encoding="utf-8"))
                self.assertEqual(saved["theme"], "material_light")
                self.assertEqual(saved["locale"], "en")
            finally:
                app.shutdown()

    def test_splash_auto_continues_without_interaction(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            prefs_path = Path(tmpdir) / "preferences.json"
            app = App(preferences_path=prefs_path, bootstrap_interval_ms=0, auto_continue_ms=120)
            app.start()
            try:
                self._wait_until(lambda: app.window is not None and app.window.isVisible(), timeout_ms=4000)
                self.assertFalse(app.splash.isVisible())
            finally:
                app.shutdown()

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
