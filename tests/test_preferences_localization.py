from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from context.localization import LocalizationController
from context.preferences import PreferencesController


class PreferencesLocalizationTests(unittest.TestCase):
    def test_preferences_save_and_reload_theme_and_locale(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "preferences.json"
            preferences = PreferencesController(path_override=path)
            preferences.load()
            preferences.set_theme("material_light")
            preferences.set_locale("en")

            reloaded = PreferencesController(path_override=path).load()
            self.assertEqual(reloaded.theme, "material_light")
            self.assertEqual(reloaded.locale, "en")

    def test_preferences_fallback_to_defaults_for_invalid_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "preferences.json"
            path.write_text('{"theme": "unknown", "locale": "xx"}', encoding="utf-8")

            reloaded = PreferencesController(path_override=path).load()
            self.assertEqual(reloaded.theme, "material_dark")
            self.assertEqual(reloaded.locale, "pt-BR")

    def test_localization_translates_and_falls_back(self) -> None:
        localization = LocalizationController(initial_locale="en")
        self.assertEqual(localization.tr("status.loaded_image", name="sample.png"), "Loaded sample.png")

        localization.set_locale("pt-BR")
        self.assertEqual(
            localization.tr("status.loaded_image", name="sample.png"),
            "Imagem carregada: sample.png",
        )
        self.assertEqual(localization.tr("missing.translation.key"), "missing.translation.key")


if __name__ == "__main__":
    unittest.main()
