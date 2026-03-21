from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QActionGroup
from PyQt6.QtWidgets import QApplication, QDockWidget, QFileDialog, QMainWindow

from context.viewmodels import GraphViewModel
from context.views.canvas import GraphScene, GraphView
from context.views.panels import PreviewPanel, PropertiesPanel
from context.views.theme import ThemeController


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("appRoot")
        self.setWindowTitle("ContExt | PyQt6 Graph")
        self.resize(1440, 920)

        self.theme_controller = ThemeController(initial_theme="material_dark")
        self.graph_viewmodel = GraphViewModel()
        self.graph_scene = GraphScene(self.graph_viewmodel, self.theme_controller)
        self.graph_view = GraphView(self.graph_scene, self.theme_controller)
        self.properties_panel = PropertiesPanel(self.graph_viewmodel)
        self.properties_panel.setObjectName("propertiesSurface")
        self.preview_panel = PreviewPanel(self.graph_viewmodel)
        self.preview_panel.setObjectName("previewSurface")
        self._theme_actions: dict[str, QAction] = {}

        self.setCentralWidget(self.graph_view)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._build_dock("Properties", self.properties_panel))
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._build_dock("Preview", self.preview_panel))

        self._build_actions()
        self._wire_status_bar()
        self.theme_controller.themeChanged.connect(self._apply_theme)
        self._apply_theme(self.theme_controller.theme)

    @property
    def theme_name(self) -> str:
        return self.theme_controller.theme_name

    def set_theme(self, theme_name: str) -> None:
        self.theme_controller.set_theme(theme_name)

    def _build_actions(self) -> None:
        open_image_action = QAction("Open Image...", self)
        open_image_action.triggered.connect(self._open_image_dialog)
        delete_selected_action = QAction("Delete Selected", self)
        delete_selected_action.triggered.connect(self.graph_scene.delete_selected_items)
        theme_group = QActionGroup(self)
        theme_group.setExclusive(True)
        for theme_name, label in (("material_light", "Material Light"), ("material_dark", "Material Dark")):
            action = QAction(label, self)
            action.setCheckable(True)
            action.triggered.connect(lambda checked=False, name=theme_name: self.set_theme(name))
            theme_group.addAction(action)
            self._theme_actions[theme_name] = action

        file_menu = self.menuBar().addMenu("File")
        file_menu.addAction(open_image_action)
        file_menu.addSeparator()
        file_menu.addAction("Quit", self.close)

        edit_menu = self.menuBar().addMenu("Edit")
        edit_menu.addAction(delete_selected_action)

        view_menu = self.menuBar().addMenu("View")
        view_menu.addAction(self._theme_actions["material_light"])
        view_menu.addAction(self._theme_actions["material_dark"])

        toolbar = self.addToolBar("Main")
        toolbar.addAction(open_image_action)
        toolbar.addAction(delete_selected_action)
        toolbar.addSeparator()
        toolbar.addAction(self._theme_actions["material_light"])
        toolbar.addAction(self._theme_actions["material_dark"])

    def _wire_status_bar(self) -> None:
        self.graph_viewmodel.errorRaised.connect(lambda message: self.statusBar().showMessage(message, 4000))
        self.graph_viewmodel.imageLoaded.connect(
            lambda path: self.statusBar().showMessage(f"Loaded {Path(path).name}", 3000)
        )
        self.graph_viewmodel.processingChanged.connect(self._on_processing_changed)

    def _on_processing_changed(self, is_processing: bool) -> None:
        if is_processing:
            self.statusBar().showMessage("Processing graph...")
        else:
            self.statusBar().showMessage("Ready", 2000)

    def _apply_theme(self, theme) -> None:
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(self.theme_controller.stylesheet())
        for theme_name, action in self._theme_actions.items():
            action.setChecked(theme_name == self.theme_controller.theme_name)
        self.statusBar().showMessage(f"{theme.label} enabled", 2000)

    def _open_image_dialog(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)",
        )
        if file_path:
            self.graph_viewmodel.load_image(file_path)

    @staticmethod
    def _build_dock(title: str, widget) -> QDockWidget:
        dock = QDockWidget(title)
        dock.setObjectName(f"{title.lower()}Dock")
        dock.setWidget(widget)
        dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | QDockWidget.DockWidgetFeature.DockWidgetFloatable)
        return dock
