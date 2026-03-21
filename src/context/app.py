from __future__ import annotations

from pathlib import Path
import sys

from PyQt6.QtWidgets import QApplication, QFileDialog

from .localization import LocalizationController
from .meta import APP_NAME, APP_VERSION
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
        del bootstrap_interval_ms, auto_continue_ms
        self.qt_app = QApplication.instance() or QApplication(sys.argv)
        self.qt_app.setApplicationName(APP_NAME)
        self.qt_app.setOrganizationName(APP_NAME)

        self.preferences = PreferencesController(path_override=preferences_path)
        loaded_preferences = self.preferences.load()

        self.localization_controller = LocalizationController(initial_locale=loaded_preferences.locale)
        self.theme_controller = ThemeController(initial_theme=loaded_preferences.theme)
        self.graph_viewmodel: GraphViewModel | None = None
        self.window: MainWindow | None = None
        self.splash = SplashWindow(
            self.theme_controller,
            self.localization_controller,
            version_text=APP_VERSION,
        )

        self._has_started = False

        self.theme_controller.themeChanged.connect(self._apply_stylesheet)
        self.theme_controller.themeChanged.connect(lambda theme: self.preferences.set_theme(theme.name))
        self.localization_controller.localeChanged.connect(self.preferences.set_locale)

        self.splash.themeSelected.connect(self.theme_controller.set_theme)
        self.splash.localeSelected.connect(self.localization_controller.set_locale)
        self.splash.newProjectRequested.connect(self._start_new_project)
        self.splash.openProjectRequested.connect(self._open_project_from_splash)
        self.splash.quitRequested.connect(self.qt_app.quit)

        self._apply_stylesheet(self.theme_controller.theme)

    def start(self) -> None:
        if self._has_started:
            return
        self._has_started = True
        self.splash.show()

    def exec(self) -> int:
        self.start()
        return self.qt_app.exec()

    def shutdown(self) -> None:
        if self.window is not None:
            self.window.close()
            self.window = None
        self.graph_viewmodel = None
        self.splash.close()

    def _start_new_project(self) -> None:
        self._replace_main_window(bootstrap_default_graph=True)
        self._show_main_window()

    def _open_project_from_splash(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self.splash,
            self.localization_controller.tr("dialog.open_pipeline.title"),
            "",
            self.localization_controller.tr("dialog.open_pipeline.filter"),
        )
        if not file_path:
            return

        window = self._build_main_window(bootstrap_default_graph=False)
        if not window.load_pipeline_from_path(file_path):
            window.close()
            self.window = None
            self.graph_viewmodel = None
            return

        self._show_main_window()

    def _build_main_window(self, *, bootstrap_default_graph: bool) -> MainWindow:
        self.graph_viewmodel = GraphViewModel(
            localization_controller=self.localization_controller,
            bootstrap_default_graph=bootstrap_default_graph,
        )
        self.window = MainWindow(
            theme_controller=self.theme_controller,
            localization_controller=self.localization_controller,
            graph_viewmodel=self.graph_viewmodel,
        )
        return self.window

    def _replace_main_window(self, *, bootstrap_default_graph: bool) -> MainWindow:
        if self.window is not None:
            self.window.close()
        self.window = None
        self.graph_viewmodel = None
        return self._build_main_window(bootstrap_default_graph=bootstrap_default_graph)

    def _show_main_window(self) -> None:
        if self.window is None:
            return
        self.splash.close()
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()

    def _apply_stylesheet(self, _theme) -> None:
        self.qt_app.setStyleSheet(self.theme_controller.stylesheet())


def run() -> int:
    return App().exec()
