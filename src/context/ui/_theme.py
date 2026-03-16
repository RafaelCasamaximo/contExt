import dearpygui.dearpygui as dpg
import platform
from ..paths import asset_path

def applyTheme():

    icon_path = asset_path("icons", "Icon.ico")

    dpg.set_viewport_small_icon(icon_path)
    dpg.set_viewport_large_icon(icon_path)

    with dpg.theme() as global_theme:
        with dpg.theme_component(0):
            # Main Styles
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 8, 8)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 20, 4)
            dpg.add_theme_style(dpg.mvStyleVar_CellPadding, 4, 2)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 8, 4)
            dpg.add_theme_style(dpg.mvStyleVar_ItemInnerSpacing, 4, 4)
            dpg.add_theme_style(dpg.mvStyleVar_IndentSpacing, 20)
            dpg.add_theme_style(dpg.mvStyleVar_ScrollbarSize, 14)
            dpg.add_theme_style(dpg.mvStyleVar_GrabMinSize, 20)

            # Border Styles
            dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 1)
            dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 1)
            dpg.add_theme_style(dpg.mvStyleVar_PopupBorderSize, 1)
            dpg.add_theme_style(dpg.mvStyleVar_FrameBorderSize, 0)

            # Rounding Style
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 12)
            dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 12)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4)
            dpg.add_theme_style(dpg.mvStyleVar_PopupRounding, 12)
            dpg.add_theme_style(dpg.mvStyleVar_ScrollbarRounding, 9)
            dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 12)
            dpg.add_theme_style(dpg.mvStyleVar_TabRounding, 12)

    dpg.bind_theme(global_theme)

    # FIXME: Blurry font on Windows with DPI scaling
    # https://github.com/hoffstadt/DearPyGui/issues/1380

    if platform.system() == "Windows":
        fontPath = asset_path("fonts", "Inter-Regular.otf")
    else:
        fontPath = asset_path("fonts", "Inter-Regular.otf")

    try:
        with dpg.font_registry():
            default_font = dpg.add_font(fontPath, 16)

        dpg.bind_font(default_font)
    except:
        pass
