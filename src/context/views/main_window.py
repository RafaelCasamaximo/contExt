from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QActionGroup, QCloseEvent
from PyQt6.QtWidgets import QApplication, QDockWidget, QFileDialog, QMainWindow

from context.core.pipeline import PIPELINE_EXTENSION
from context.localization import LocalizationController
from context.meta import APP_NAME
from context.viewmodels import GraphViewModel
from context.views.canvas import GraphScene, GraphView
from context.views.panels import HistogramPanel, PreviewPanel, PropertiesPanel
from context.views.theme import ThemeController


class MainWindow(QMainWindow):
    DEFAULT_PIPELINE_NAME = f"untitled{PIPELINE_EXTENSION}"

    def __init__(
        self,
        theme_controller: ThemeController | None = None,
        localization_controller: LocalizationController | None = None,
        graph_viewmodel: GraphViewModel | None = None,
    ) -> None:
        super().__init__()
        self.setObjectName("appRoot")

        self.theme_controller = theme_controller or ThemeController(initial_theme="material_dark")
        self.localization_controller = localization_controller or LocalizationController(initial_locale="pt-BR")
        self.graph_viewmodel = graph_viewmodel or GraphViewModel(localization_controller=self.localization_controller)
        self.graph_scene = GraphScene(self.graph_viewmodel, self.theme_controller, self.localization_controller)
        self.graph_view = GraphView(self.graph_scene, self.theme_controller)
        self.properties_panel = PropertiesPanel(self.graph_viewmodel, self.localization_controller)
        self.properties_panel.setObjectName("propertiesSurface")
        self.preview_panel = PreviewPanel(self.graph_viewmodel, self.localization_controller)
        self.preview_panel.setObjectName("previewSurface")
        self.histogram_panel = HistogramPanel(
            self.graph_viewmodel,
            self.theme_controller,
            self.localization_controller,
        )
        self.histogram_panel.setObjectName("histogramSurface")
        self._current_pipeline_name = self.DEFAULT_PIPELINE_NAME

        self._theme_actions: dict[str, QAction] = {}
        self._language_actions: dict[str, QAction] = {}

        self._open_pipeline_action = QAction(self)
        self._open_pipeline_action.triggered.connect(self._open_pipeline_dialog)
        self._save_pipeline_action = QAction(self)
        self._save_pipeline_action.triggered.connect(self._save_pipeline_dialog)
        self._save_preview_action = QAction(self)
        self._save_preview_action.triggered.connect(self._save_preview_dialog)
        self._save_histogram_action = QAction(self)
        self._save_histogram_action.triggered.connect(self._save_histogram_dialog)
        self._open_image_action = QAction(self)
        self._open_image_action.triggered.connect(self._open_image_dialog)
        self._delete_selected_action = QAction(self)
        self._delete_selected_action.triggered.connect(self.graph_scene.delete_selected_items)
        self._quit_action = QAction(self)
        self._quit_action.triggered.connect(self.close)

        self._file_menu = self.menuBar().addMenu("")
        self._edit_menu = self.menuBar().addMenu("")
        self._view_menu = self.menuBar().addMenu("")
        self._language_menu = self.menuBar().addMenu("")
        self.setCentralWidget(self.graph_view)
        self._properties_dock = self._build_dock(self.properties_panel)
        self._preview_dock = self._build_dock(self.preview_panel)
        self._histogram_dock = self._build_dock(self.histogram_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._properties_dock)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._preview_dock)
        self.splitDockWidget(self._properties_dock, self._preview_dock, Qt.Orientation.Vertical)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._histogram_dock)
        self.splitDockWidget(self._preview_dock, self._histogram_dock, Qt.Orientation.Vertical)

        self.resize(1440, 920)
        self._build_actions()
        self._wire_status_bar()

        self.theme_controller.themeChanged.connect(self._apply_theme)
        self.localization_controller.localeChanged.connect(self._retranslate_ui)
        self.preview_panel.exportAvailabilityChanged.connect(self._sync_preview_export_state)
        self.histogram_panel.exportAvailabilityChanged.connect(self._sync_histogram_export_state)
        self.histogram_panel.saveRequested.connect(self._save_histogram_dialog)
        self._retranslate_ui()
        self._apply_theme(self.theme_controller.theme)
        self._sync_preview_export_state(self.preview_panel.has_exportable_image())
        self._sync_histogram_export_state(self.histogram_panel.has_exportable_histogram())

    @property
    def theme_name(self) -> str:
        return self.theme_controller.theme_name

    @property
    def locale_code(self) -> str:
        return self.localization_controller.locale

    def set_theme(self, theme_name: str) -> None:
        self.theme_controller.set_theme(theme_name)

    def set_locale(self, locale_code: str) -> None:
        self.localization_controller.set_locale(locale_code)

    def closeEvent(self, event: QCloseEvent) -> None:
        self.graph_view.dispose()
        self.graph_scene.dispose()
        super().closeEvent(event)

    def _build_actions(self) -> None:
        theme_group = QActionGroup(self)
        theme_group.setExclusive(True)
        for theme_name in self.theme_controller.available_themes():
            action = QAction(self)
            action.setCheckable(True)
            action.triggered.connect(lambda checked=False, name=theme_name: self.set_theme(name))
            theme_group.addAction(action)
            self._theme_actions[theme_name] = action

        language_group = QActionGroup(self)
        language_group.setExclusive(True)
        for locale_code in self.localization_controller.available_locales():
            action = QAction(self)
            action.setCheckable(True)
            action.triggered.connect(lambda checked=False, code=locale_code: self.set_locale(code))
            language_group.addAction(action)
            self._language_actions[locale_code] = action

        self._file_menu.addAction(self._open_pipeline_action)
        self._file_menu.addAction(self._save_pipeline_action)
        self._file_menu.addAction(self._save_preview_action)
        self._file_menu.addAction(self._save_histogram_action)
        self._file_menu.addSeparator()
        self._file_menu.addAction(self._open_image_action)
        self._file_menu.addSeparator()
        self._file_menu.addAction(self._quit_action)

        self._edit_menu.addAction(self._delete_selected_action)

        for action in self._theme_actions.values():
            self._view_menu.addAction(action)
        for action in self._language_actions.values():
            self._language_menu.addAction(action)

    def _wire_status_bar(self) -> None:
        self.graph_viewmodel.errorRaised.connect(lambda message: self.statusBar().showMessage(message, 4000))
        self.graph_viewmodel.imageLoaded.connect(
            lambda path: self.statusBar().showMessage(
                self.localization_controller.tr("status.loaded_image", name=Path(path).name),
                3000,
            )
        )
        self.graph_viewmodel.processingChanged.connect(self._on_processing_changed)

    def _on_processing_changed(self, is_processing: bool) -> None:
        key = "status.processing" if is_processing else "status.ready"
        self.statusBar().showMessage(self.localization_controller.tr(key), 2000 if not is_processing else 0)

    def _apply_theme(self, theme) -> None:
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(self.theme_controller.stylesheet())
        for theme_name, action in self._theme_actions.items():
            action.setChecked(theme_name == self.theme_controller.theme_name)
        self.statusBar().showMessage(
            self.localization_controller.tr(
                "status.theme_enabled",
                theme=self.localization_controller.tr(f"theme.name.{theme.name}"),
            ),
            2000,
        )

    def _retranslate_ui(self, _locale: str | None = None) -> None:
        tr = self.localization_controller.tr
        self._update_window_title()
        self._file_menu.setTitle(tr("menu.file"))
        self._edit_menu.setTitle(tr("menu.edit"))
        self._view_menu.setTitle(tr("menu.view"))
        self._language_menu.setTitle(tr("menu.language"))
        self._open_pipeline_action.setText(tr("action.open_pipeline"))
        self._save_pipeline_action.setText(tr("action.save_pipeline"))
        self._save_preview_action.setText(tr("action.save_preview"))
        self._save_histogram_action.setText(tr("action.save_histogram"))
        self._open_image_action.setText(tr("action.open_image"))
        self._delete_selected_action.setText(tr("action.delete_selected"))
        self._quit_action.setText(tr("action.quit"))
        self._properties_dock.setWindowTitle(tr("dock.properties"))
        self._preview_dock.setWindowTitle(tr("dock.preview"))
        self._histogram_dock.setWindowTitle(tr("dock.histogram"))
        for theme_name, action in self._theme_actions.items():
            action.setText(tr(f"theme.name.{theme_name}"))
        for locale_code, action in self._language_actions.items():
            action.setText(tr(f"language.name.{locale_code}"))
            action.setChecked(locale_code == self.localization_controller.locale)
        self.statusBar().showMessage(
            tr(
                "status.language_enabled",
                language=tr(f"language.name.{self.localization_controller.locale}"),
            ),
            2000,
        )

    def _open_image_dialog(self) -> None:
        tr = self.localization_controller.tr
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            tr("dialog.open_image.title"),
            "",
            tr("dialog.open_image.filter"),
        )
        if file_path:
            self.graph_viewmodel.load_image(file_path)

    def _open_pipeline_dialog(self) -> None:
        tr = self.localization_controller.tr
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            tr("dialog.open_pipeline.title"),
            "",
            tr("dialog.open_pipeline.filter"),
        )
        if file_path:
            self.load_pipeline_from_path(file_path)

    def _save_pipeline_dialog(self) -> None:
        tr = self.localization_controller.tr
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            tr("dialog.save_pipeline.title"),
            "",
            tr("dialog.save_pipeline.filter"),
        )
        if file_path:
            self.save_pipeline_to_path(file_path)

    def _save_preview_dialog(self) -> None:
        tr = self.localization_controller.tr
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            tr("dialog.save_preview.title"),
            "",
            tr("dialog.save_preview.filter"),
        )
        if file_path:
            self.save_preview_to_path(file_path)

    def _save_histogram_dialog(self) -> None:
        tr = self.localization_controller.tr
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            tr("dialog.save_histogram.title"),
            "",
            tr("dialog.save_histogram.filter"),
        )
        if file_path:
            self.save_histogram_to_path(file_path)

    def load_pipeline_from_path(self, file_path: str) -> bool:
        if not self.graph_viewmodel.load_pipeline(file_path):
            return False
        self._current_pipeline_name = Path(file_path).name
        self._update_window_title()
        self.statusBar().showMessage(
            self.localization_controller.tr("status.loaded_pipeline", name=Path(file_path).name),
            3000,
        )
        return True

    def save_pipeline_to_path(self, file_path: str) -> bool:
        normalized_path = self._ensure_suffix(file_path, PIPELINE_EXTENSION)
        if not self.graph_viewmodel.save_pipeline(normalized_path):
            return False
        self._current_pipeline_name = Path(normalized_path).name
        self._update_window_title()
        self.statusBar().showMessage(
            self.localization_controller.tr("status.saved_pipeline", name=Path(normalized_path).name),
            3000,
        )
        return True

    def save_preview_to_path(self, file_path: str) -> bool:
        normalized_path = self._ensure_suffix(file_path, ".png")
        try:
            self.preview_panel.save_png(normalized_path)
        except ValueError as exc:
            self.statusBar().showMessage(str(exc), 3000)
            return False
        self.statusBar().showMessage(
            self.localization_controller.tr("status.saved_preview", name=Path(normalized_path).name),
            3000,
        )
        return True

    def save_histogram_to_path(self, file_path: str) -> bool:
        normalized_path = self._ensure_suffix(file_path, ".png")
        try:
            self.histogram_panel.save_png(normalized_path)
        except ValueError as exc:
            self.statusBar().showMessage(str(exc), 3000)
            return False
        self.statusBar().showMessage(
            self.localization_controller.tr("status.saved_histogram", name=Path(normalized_path).name),
            3000,
        )
        return True

    def _sync_preview_export_state(self, has_preview: bool) -> None:
        self._save_preview_action.setEnabled(has_preview)

    def _sync_histogram_export_state(self, has_histogram: bool) -> None:
        self._save_histogram_action.setEnabled(has_histogram)

    def _update_window_title(self) -> None:
        self.setWindowTitle(f"{APP_NAME} | {self._current_pipeline_name}")

    @staticmethod
    def _ensure_suffix(file_path: str, suffix: str) -> str:
        path = Path(file_path)
        if path.suffix:
            return str(path)
        return str(path.with_suffix(suffix))

    @staticmethod
    def _build_dock(widget) -> QDockWidget:
        dock = QDockWidget("")
        dock.setWidget(widget)
        dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | QDockWidget.DockWidgetFeature.DockWidgetFloatable)
        return dock
