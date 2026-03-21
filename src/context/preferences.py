from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

from PyQt6.QtCore import QStandardPaths


@dataclass(slots=True)
class AppPreferences:
    theme: str = "material_dark"
    locale: str = "pt-BR"


class PreferencesController:
    def __init__(self, path_override: Path | None = None) -> None:
        self._path = Path(path_override) if path_override is not None else self._default_path()
        self.preferences = AppPreferences()

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> AppPreferences:
        from .localization import SUPPORTED_LOCALES
        from .views.theme import THEMES

        if not self._path.exists():
            self.preferences = AppPreferences()
            return self.preferences

        try:
            payload = json.loads(self._path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            self.preferences = AppPreferences()
            return self.preferences

        theme_name = str(payload.get("theme", AppPreferences.theme))
        locale_code = str(payload.get("locale", AppPreferences.locale))
        self.preferences = AppPreferences(
            theme=theme_name if theme_name in THEMES else AppPreferences().theme,
            locale=locale_code if locale_code in SUPPORTED_LOCALES else AppPreferences().locale,
        )
        return self.preferences

    def set_theme(self, theme_name: str) -> None:
        if self.preferences.theme == theme_name:
            return
        self.preferences.theme = theme_name
        self.save()

    def set_locale(self, locale_code: str) -> None:
        if self.preferences.locale == locale_code:
            return
        self.preferences.locale = locale_code
        self.save()

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(asdict(self.preferences), indent=2), encoding="utf-8")

    @staticmethod
    def _default_path() -> Path:
        config_root = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation)
        if config_root:
            return Path(config_root) / "preferences.json"
        return Path.home() / ".context" / "preferences.json"
