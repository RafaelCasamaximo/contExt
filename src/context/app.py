from __future__ import annotations

from pathlib import Path
import sys

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from .localization import LocalizationController
from .preferences import PreferencesController
from .viewmodels import GraphViewModel
from .views.main_window import MainWindow
from .views.splash_window import SplashWindow
from .views.theme import ThemeController


class App:
    def __init__(
        self,
        preferences_path: Path | None = None,
        bootstrap_interval_ms: int = 90,
        auto_continue_ms: int = 1200,
    ) -> None:
        self.qt_app = QApplication.instance() or QApplication(sys.argv)
        self.qt_app.setApplicationName("ContExt")
        self.qt_app.setOrganizationName("ContExt")

        self.preferences = PreferencesController(path_override=preferences_path)
        loaded_preferences = self.preferences.load()

        self.localization_controller = LocalizationController(initial_locale=loaded_preferences.locale)
        self.theme_controller = ThemeController(initial_theme=loaded_preferences.theme)
        self.graph_viewmodel: GraphViewModel | None = None
        self.window: MainWindow | None = None
        self.splash = SplashWindow(
            self.theme_controller,
            self.localization_controller,
            auto_continue_ms=auto_continue_ms,
        )

        self._bootstrap_interval_ms = bootstrap_interval_ms
        self._startup_index = 0
        self._has_started = False
        self._entered_main_window = False
        self._startup_steps = [
            ("startup.step.preferences", self._noop_step),
            ("startup.step.theme", self._noop_step),
            ("startup.step.locale", self._noop_step),
            ("startup.step.workspace", self._build_main_window),
        ]

        self.theme_controller.themeChanged.connect(self._apply_stylesheet)
        self.theme_controller.themeChanged.connect(lambda theme: self.preferences.set_theme(theme.name))
        self.localization_controller.localeChanged.connect(self.preferences.set_locale)

        self.splash.themeSelected.connect(self.theme_controller.set_theme)
        self.splash.localeSelected.connect(self.localization_controller.set_locale)
        self.splash.continueRequested.connect(self._enter_main_window)

        self._apply_stylesheet(self.theme_controller.theme)

    def start(self) -> None:
        if self._has_started:
            return
        self._has_started = True
        self.splash.show()
        QTimer.singleShot(0, self._run_next_startup_step)

    def exec(self) -> int:
        self.start()
        return self.qt_app.exec()

    def shutdown(self) -> None:
        if self.window is not None:
            self.window.close()
        self.splash.close()

    def _run_next_startup_step(self) -> None:
        if self._startup_index >= len(self._startup_steps):
            self.splash.mark_ready()
            return

        status_key, callback = self._startup_steps[self._startup_index]
        self._startup_index += 1
        self.splash.set_progress(self._startup_index, len(self._startup_steps), status_key)
        callback()
        QTimer.singleShot(self._bootstrap_interval_ms, self._run_next_startup_step)

    def _build_main_window(self) -> None:
        if self.window is not None:
            return
        self.graph_viewmodel = GraphViewModel(localization_controller=self.localization_controller)
        self.window = MainWindow(
            theme_controller=self.theme_controller,
            localization_controller=self.localization_controller,
            graph_viewmodel=self.graph_viewmodel,
        )

    def _enter_main_window(self) -> None:
        if self._entered_main_window:
            return
        if self.window is None:
            return
        self._entered_main_window = True
        self.splash.close()
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()

    def _apply_stylesheet(self, theme) -> None:
        self.qt_app.setStyleSheet(self.theme_controller.stylesheet())

    @staticmethod
    def _noop_step() -> None:
        return None


def run() -> int:
    return App().exec()
