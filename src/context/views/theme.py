from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtCore import QObject, pyqtSignal


@dataclass(frozen=True, slots=True)
class MaterialTheme:
    name: str
    label: str
    is_dark: bool
    window_bg: str
    surface: str
    surface_raised: str
    surface_alt: str
    canvas_bg: str
    grid_minor: str
    grid_major: str
    text_primary: str
    text_secondary: str
    text_inverse: str
    border: str
    border_soft: str
    selection: str
    success: str
    edge: str
    edge_preview: str
    edge_selected: str
    input_port: str
    output_port: str
    source_accent: str
    blur_accent: str
    preview_accent: str
    shadow: str

    def accent_for_node(self, node_type: str) -> str:
        accents = {
            "source": self.source_accent,
            "blur": self.blur_accent,
            "preview": self.preview_accent,
        }
        return accents.get(node_type, self.selection)


THEMES: dict[str, MaterialTheme] = {
    "material_light": MaterialTheme(
        name="material_light",
        label="Material Light",
        is_dark=False,
        window_bg="#edf2f7",
        surface="#ffffff",
        surface_raised="#f8fafc",
        surface_alt="#eef2ff",
        canvas_bg="#e6edf5",
        grid_minor="#d5dfeb",
        grid_major="#b8c8da",
        text_primary="#0f172a",
        text_secondary="#526072",
        text_inverse="#ffffff",
        border="#c7d2df",
        border_soft="#d9e2ec",
        selection="#2563eb",
        success="#0f766e",
        edge="#2563eb",
        edge_preview="#94a3b8",
        edge_selected="#dc2626",
        input_port="#2563eb",
        output_port="#f97316",
        source_accent="#0f766e",
        blur_accent="#ea580c",
        preview_accent="#4338ca",
        shadow="#0f172a24",
    ),
    "material_dark": MaterialTheme(
        name="material_dark",
        label="Material Dark",
        is_dark=True,
        window_bg="#0b1220",
        surface="#111827",
        surface_raised="#182235",
        surface_alt="#0f1a2d",
        canvas_bg="#08111f",
        grid_minor="#142035",
        grid_major="#23324a",
        text_primary="#e5eefb",
        text_secondary="#94a3b8",
        text_inverse="#f8fafc",
        border="#30445f",
        border_soft="#24354d",
        selection="#38bdf8",
        success="#2dd4bf",
        edge="#60a5fa",
        edge_preview="#64748b",
        edge_selected="#fb7185",
        input_port="#38bdf8",
        output_port="#fb923c",
        source_accent="#14b8a6",
        blur_accent="#fb923c",
        preview_accent="#818cf8",
        shadow="#00000070",
    ),
}


class ThemeController(QObject):
    themeChanged = pyqtSignal(object)

    def __init__(self, initial_theme: str = "material_dark") -> None:
        super().__init__()
        self._theme_name = ""
        self._theme = THEMES["material_dark"]
        self.set_theme(initial_theme)

    @property
    def theme_name(self) -> str:
        return self._theme_name

    @property
    def theme(self) -> MaterialTheme:
        return self._theme

    def set_theme(self, theme_name: str) -> None:
        if theme_name not in THEMES:
            raise ValueError(f"Unknown theme '{theme_name}'.")
        if theme_name == self._theme_name:
            return
        self._theme_name = theme_name
        self._theme = THEMES[theme_name]
        self.themeChanged.emit(self._theme)

    def stylesheet(self) -> str:
        theme = self._theme
        return f"""
QWidget {{
    color: {theme.text_primary};
    font-family: Arial;
    font-size: 13px;
}}
QMainWindow, QWidget#appRoot {{
    background-color: {theme.window_bg};
}}
QMenuBar {{
    background-color: {theme.surface};
    color: {theme.text_primary};
    border-bottom: 1px solid {theme.border_soft};
    padding: 4px 8px;
}}
QMenuBar::item {{
    padding: 8px 12px;
    border-radius: 10px;
    background: transparent;
}}
QMenuBar::item:selected {{
    background-color: {theme.surface_alt};
}}
QMenu {{
    background-color: {theme.surface};
    color: {theme.text_primary};
    border: 1px solid {theme.border_soft};
    padding: 8px;
}}
QMenu::item {{
    padding: 8px 14px;
    border-radius: 10px;
}}
QMenu::item:selected {{
    background-color: {theme.surface_alt};
}}
QToolBar {{
    background-color: {theme.surface};
    border: none;
    border-bottom: 1px solid {theme.border_soft};
    spacing: 6px;
    padding: 8px;
}}
QToolButton {{
    background-color: {theme.surface_raised};
    color: {theme.text_primary};
    border: 1px solid {theme.border_soft};
    border-radius: 14px;
    padding: 8px 12px;
}}
QToolButton:hover {{
    border-color: {theme.selection};
}}
QToolButton:checked {{
    background-color: {theme.selection};
    color: {theme.text_inverse};
    border-color: {theme.selection};
}}
QStatusBar {{
    background-color: {theme.surface};
    color: {theme.text_secondary};
    border-top: 1px solid {theme.border_soft};
}}
QDockWidget {{
    color: {theme.text_primary};
}}
QDockWidget::title {{
    background-color: {theme.surface_raised};
    border: 1px solid {theme.border_soft};
    border-bottom: none;
    padding: 10px 14px;
    text-align: left;
}}
QWidget#propertiesSurface, QWidget#previewSurface {{
    background-color: {theme.surface};
    border: 1px solid {theme.border_soft};
    border-radius: 22px;
}}
QScrollArea {{
    background: transparent;
    border: none;
}}
QScrollArea > QWidget > QWidget {{
    background: transparent;
}}
QLabel#secondaryLabel {{
    color: {theme.text_secondary};
}}
QLabel#nodeChipLabel {{
    background-color: {theme.surface_alt};
    color: {theme.text_primary};
    border: 1px solid {theme.border_soft};
    border-radius: 11px;
    padding: 2px 10px;
    font-weight: 600;
}}
QWidget#nodeControlCard {{
    background-color: {theme.surface_raised};
    border: 1px solid {theme.border_soft};
    border-radius: 16px;
}}
QSpinBox {{
    background-color: {theme.surface_raised};
    color: {theme.text_primary};
    border: 1px solid {theme.border_soft};
    border-radius: 12px;
    padding: 7px 10px;
}}
QSpinBox:focus {{
    border-color: {theme.selection};
}}
QSlider::groove:horizontal {{
    height: 6px;
    border-radius: 3px;
    background: {theme.border};
}}
QSlider::sub-page:horizontal {{
    background: {theme.selection};
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    background: {theme.text_inverse};
    border: 3px solid {theme.selection};
    width: 16px;
    margin: -7px 0;
    border-radius: 11px;
}}
QGraphicsView#graphView {{
    border: none;
    background: {theme.canvas_bg};
}}
"""
