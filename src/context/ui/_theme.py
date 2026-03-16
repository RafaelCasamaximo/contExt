import dearpygui.dearpygui as dpg

from ..paths import asset_path


DEFAULT_THEME = "dark"

GLOBAL_THEME_TAG = "contExt_global_theme"
STARTUP_CARD_THEME_TAG = "contExt_startup_card_theme"
ACCENT_BUTTON_THEME_TAG = "contExt_accent_button_theme"
GRID_PLOT_THEME_TAG = "grid_plot_theme"
VECTOR_PLOT_THEME_TAG = "contExt_vector_plot_theme"
FONT_REGISTRY_TAG = "contExt_font_registry"
DEFAULT_FONT_TAG = "contExt_default_font"

_CURRENT_THEME = DEFAULT_THEME

_PALETTES = {
    "dark": {
        "background": (11, 18, 27, 255),
        "surface": (18, 28, 40, 255),
        "surface_alt": (24, 37, 54, 255),
        "surface_card": (21, 32, 47, 255),
        "border": (57, 80, 108, 255),
        "text": (234, 240, 248, 255),
        "text_muted": (134, 151, 174, 255),
        "accent": (43, 112, 246, 255),
        "accent_hover": (63, 128, 255, 255),
        "accent_active": (29, 89, 215, 255),
        "accent_soft": (31, 56, 92, 255),
        "separator": (73, 95, 121, 255),
        "grid": (96, 114, 136, 180),
    },
    "light": {
        "background": (242, 246, 251, 255),
        "surface": (255, 255, 255, 255),
        "surface_alt": (229, 237, 246, 255),
        "surface_card": (248, 251, 255, 255),
        "border": (188, 201, 219, 255),
        "text": (24, 34, 49, 255),
        "text_muted": (100, 116, 137, 255),
        "accent": (24, 99, 224, 255),
        "accent_hover": (14, 112, 249, 255),
        "accent_active": (18, 77, 184, 255),
        "accent_soft": (214, 229, 248, 255),
        "separator": (202, 213, 227, 255),
        "grid": (140, 154, 171, 175),
    },
}


def current_theme() -> str:
    return _CURRENT_THEME


def _palette(theme_name: str) -> dict[str, tuple[int, int, int, int]]:
    return _PALETTES.get(theme_name, _PALETTES[DEFAULT_THEME])


def _recreate_theme(tag: str):
    if dpg.does_item_exist(tag):
        dpg.delete_item(tag)
    # Dear PyGui can retain the alias for a deleted item-bound theme.
    if dpg.does_alias_exist(tag):
        dpg.remove_alias(tag)


def _ensure_font():
    font_path = asset_path("fonts", "Inter-Regular.otf")

    try:
        if not dpg.does_item_exist(FONT_REGISTRY_TAG):
            with dpg.font_registry(tag=FONT_REGISTRY_TAG):
                dpg.add_font(font_path, 16, tag=DEFAULT_FONT_TAG)

        dpg.bind_font(DEFAULT_FONT_TAG)
    except Exception:
        pass


def _build_global_theme(theme_name: str):
    colors = _palette(theme_name)
    _recreate_theme(GLOBAL_THEME_TAG)

    with dpg.theme(tag=GLOBAL_THEME_TAG):
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 16, 16)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 12, 8)
            dpg.add_theme_style(dpg.mvStyleVar_CellPadding, 8, 6)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 12, 10)
            dpg.add_theme_style(dpg.mvStyleVar_ItemInnerSpacing, 8, 6)
            dpg.add_theme_style(dpg.mvStyleVar_IndentSpacing, 20)
            dpg.add_theme_style(dpg.mvStyleVar_ScrollbarSize, 14)
            dpg.add_theme_style(dpg.mvStyleVar_GrabMinSize, 16)
            dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 1)
            dpg.add_theme_style(dpg.mvStyleVar_ChildBorderSize, 1)
            dpg.add_theme_style(dpg.mvStyleVar_PopupBorderSize, 1)
            dpg.add_theme_style(dpg.mvStyleVar_FrameBorderSize, 1)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 16)
            dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 16)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 10)
            dpg.add_theme_style(dpg.mvStyleVar_PopupRounding, 14)
            dpg.add_theme_style(dpg.mvStyleVar_ScrollbarRounding, 12)
            dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 12)
            dpg.add_theme_style(dpg.mvStyleVar_TabRounding, 10)

            dpg.add_theme_color(dpg.mvThemeCol_Text, colors["text"])
            dpg.add_theme_color(dpg.mvThemeCol_TextDisabled, colors["text_muted"])
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, colors["background"])
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, colors["surface"])
            dpg.add_theme_color(dpg.mvThemeCol_PopupBg, colors["surface"])
            dpg.add_theme_color(dpg.mvThemeCol_Border, colors["border"])
            dpg.add_theme_color(dpg.mvThemeCol_Separator, colors["separator"])
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, colors["surface_alt"])
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, colors["accent_soft"])
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, colors["surface_alt"])
            dpg.add_theme_color(dpg.mvThemeCol_Button, colors["accent"])
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, colors["accent_hover"])
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, colors["accent_active"])
            dpg.add_theme_color(dpg.mvThemeCol_Header, colors["accent_soft"])
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, colors["accent"])
            dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, colors["accent_active"])
            dpg.add_theme_color(dpg.mvThemeCol_Tab, colors["surface_alt"])
            dpg.add_theme_color(dpg.mvThemeCol_TabHovered, colors["accent_soft"])
            dpg.add_theme_color(dpg.mvThemeCol_TabActive, colors["accent"])
            dpg.add_theme_color(dpg.mvThemeCol_TabUnfocused, colors["surface"])
            dpg.add_theme_color(dpg.mvThemeCol_TabUnfocusedActive, colors["surface_alt"])
            dpg.add_theme_color(dpg.mvThemeCol_TitleBg, colors["surface"])
            dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, colors["surface_alt"])
            dpg.add_theme_color(dpg.mvThemeCol_MenuBarBg, colors["surface"])
            dpg.add_theme_color(dpg.mvThemeCol_CheckMark, colors["accent"])
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, colors["accent"])
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, colors["accent_hover"])

            dpg.add_theme_color(dpg.mvPlotCol_FrameBg, colors["surface"], category=dpg.mvThemeCat_Plots)
            dpg.add_theme_color(dpg.mvPlotCol_PlotBg, colors["surface"], category=dpg.mvThemeCat_Plots)
            dpg.add_theme_color(dpg.mvPlotCol_PlotBorder, colors["border"], category=dpg.mvThemeCat_Plots)
            dpg.add_theme_color(dpg.mvPlotCol_LegendBg, colors["background"], category=dpg.mvThemeCat_Plots)
            dpg.add_theme_color(dpg.mvPlotCol_LegendBorder, colors["border"], category=dpg.mvThemeCat_Plots)
            dpg.add_theme_color(dpg.mvPlotCol_LegendText, colors["text"], category=dpg.mvThemeCat_Plots)
            dpg.add_theme_color(dpg.mvPlotCol_AxisText, colors["text"], category=dpg.mvThemeCat_Plots)
            dpg.add_theme_color(dpg.mvPlotCol_AxisGrid, colors["grid"], category=dpg.mvThemeCat_Plots)
            dpg.add_theme_color(dpg.mvPlotCol_TitleText, colors["text"], category=dpg.mvThemeCat_Plots)


def _build_startup_card_theme(theme_name: str):
    colors = _palette(theme_name)
    _recreate_theme(STARTUP_CARD_THEME_TAG)

    with dpg.theme(tag=STARTUP_CARD_THEME_TAG):
        with dpg.theme_component(dpg.mvChildWindow):
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, colors["surface_card"])
            dpg.add_theme_color(dpg.mvThemeCol_Border, colors["border"])
            dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 22)
            dpg.add_theme_style(dpg.mvStyleVar_ChildBorderSize, 1)
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 24, 24)


def _build_accent_button_theme(theme_name: str):
    colors = _palette(theme_name)
    _recreate_theme(ACCENT_BUTTON_THEME_TAG)

    with dpg.theme(tag=ACCENT_BUTTON_THEME_TAG):
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_color(dpg.mvThemeCol_Button, colors["accent"])
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, colors["accent_hover"])
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, colors["accent_active"])
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 14)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 16, 12)


def _build_plot_series_themes(theme_name: str):
    colors = _palette(theme_name)
    _recreate_theme(GRID_PLOT_THEME_TAG)
    _recreate_theme(VECTOR_PLOT_THEME_TAG)

    with dpg.theme(tag=GRID_PLOT_THEME_TAG):
        with dpg.theme_component(dpg.mvLineSeries):
            dpg.add_theme_color(dpg.mvPlotCol_Line, colors["grid"], category=dpg.mvThemeCat_Plots)

    with dpg.theme(tag=VECTOR_PLOT_THEME_TAG):
        with dpg.theme_component(dpg.mvLineSeries):
            dpg.add_theme_color(dpg.mvPlotCol_Line, colors["accent"], category=dpg.mvThemeCat_Plots)
            dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight, 3, category=dpg.mvThemeCat_Plots)


def apply_theme(theme_name: str = DEFAULT_THEME) -> str:
    global _CURRENT_THEME

    theme_name = theme_name if theme_name in _PALETTES else DEFAULT_THEME
    icon_path = asset_path("icons", "Icon.ico")

    dpg.set_viewport_small_icon(icon_path)
    dpg.set_viewport_large_icon(icon_path)

    _build_global_theme(theme_name)
    _build_startup_card_theme(theme_name)
    _build_accent_button_theme(theme_name)
    _build_plot_series_themes(theme_name)
    dpg.bind_theme(GLOBAL_THEME_TAG)
    _ensure_font()

    _CURRENT_THEME = theme_name
    return _CURRENT_THEME


def bind_startup_themes(card_tag: str = "startupCard", button_tag: str = "startupEnterButton"):
    if dpg.does_item_exist(card_tag):
        dpg.bind_item_theme(card_tag, STARTUP_CARD_THEME_TAG)
    if dpg.does_item_exist(button_tag):
        dpg.bind_item_theme(button_tag, ACCENT_BUTTON_THEME_TAG)


def bind_vector_themes(*item_tags: str):
    for item_tag in item_tags:
        if dpg.does_item_exist(item_tag):
            dpg.bind_item_theme(item_tag, VECTOR_PLOT_THEME_TAG)
