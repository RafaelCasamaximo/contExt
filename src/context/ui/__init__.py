import dearpygui.dearpygui as dpg

from . import strings
from ._extractionTab import showContourExtraction
from ._filteringTab import showFiltering
from ._interpolationTab import showInterpolation
from ._meshTab import showMeshGeneration
from ._processingTab import showProcessing
from ._simulationTab import showSimulation
from ._theme import DEFAULT_THEME, apply_theme, bind_startup_themes
from ._thresholdingTab import showThresholding


VIEWPORT_WIDTH = 1120
VIEWPORT_HEIGHT = 720
VIEWPORT_MIN_WIDTH = 980
VIEWPORT_MIN_HEIGHT = 680


class Interface:
    def __init__(self, callbacks) -> None:
        self.callbacks = callbacks
        self.selected_locale = strings.get_locale()
        self.selected_theme = DEFAULT_THEME
        self.main_initialized = False
        self.show()

    def show(self):
        dpg.create_context()
        dpg.create_viewport(
            title=strings.t("app.title"),
            width=VIEWPORT_WIDTH,
            height=VIEWPORT_HEIGHT,
            min_width=VIEWPORT_MIN_WIDTH,
            min_height=VIEWPORT_MIN_HEIGHT,
        )

        apply_theme(self.selected_theme)
        self.showStartupScreen()

        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("Startup", True)
        dpg.start_dearpygui()
        dpg.destroy_context()

    def showStartupScreen(self):
        with dpg.window(
            tag="Startup",
            no_title_bar=True,
            no_resize=True,
            no_move=True,
            no_collapse=True,
            width=VIEWPORT_WIDTH,
            height=VIEWPORT_HEIGHT,
            pos=(0, 0),
        ):
            dpg.add_spacer(height=90)
            with dpg.group(horizontal=True):
                dpg.add_spacer(width=330)
                with dpg.child_window(tag="startupCard", width=460, height=420, border=True):
                    dpg.add_text(strings.t("startup.eyebrow"), tag="startupEyebrow")
                    dpg.add_spacer(height=6)
                    dpg.add_text(strings.t("app.title"), tag="startupAppTitle")
                    dpg.add_text(strings.t("startup.subtitle"), tag="startupSubtitle", wrap=410)
                    dpg.add_separator()
                    dpg.add_text(strings.t("startup.language"), tag="startupLanguageLabel")
                    dpg.add_combo(
                        strings.available_locales(),
                        default_value=self.selected_locale,
                        width=-1,
                        tag="startupLanguageSelector",
                        callback=self.changeStartupLocale,
                    )
                    dpg.add_text(strings.t("startup.theme"), tag="startupThemeLabel")
                    dpg.add_combo(
                        strings.option_labels("theme"),
                        default_value=strings.option_label("theme", self.selected_theme),
                        width=-1,
                        tag="startupThemeSelector",
                        callback=self.changeStartupTheme,
                    )
                    dpg.add_spacer(height=10)
                    dpg.add_button(
                        tag="startupEnterButton",
                        width=-1,
                        label=strings.t("startup.enter"),
                        callback=self.launchMainApp,
                    )

        bind_startup_themes()

    def launchMainApp(self, sender=None, app_data=None):
        if self.main_initialized:
            return

        self.main_initialized = True
        apply_theme(self.selected_theme)
        self.showMainWindow()
        dpg.set_primary_window("Main", True)
        dpg.delete_item("Startup")

    def showMainWindow(self):
        with dpg.window(tag="Main"):
            self.showTabBar()
            self.createSaveImageDialog()
            self.createSaveHistogramDialog()

    def showTabBar(self):
        with dpg.tab_bar():
            self.showTabs()

    def showTabs(self):
        dpg.add_texture_registry(show=False, tag="textureRegistry")
        with dpg.tab(tag="processingTab", label=strings.t("app.tabs.processing")):
            showProcessing(self.callbacks)
        with dpg.tab(tag="filteringTab", label=strings.t("app.tabs.filtering")):
            showFiltering(self.callbacks)
        with dpg.tab(tag="thresholdingTab", label=strings.t("app.tabs.thresholding")):
            showThresholding(self.callbacks)
        with dpg.tab(tag="contourExtractionTab", label=strings.t("app.tabs.contour_extraction")):
            showContourExtraction(self.callbacks)
        with dpg.tab(tag="interpolationTab", label=strings.t("app.tabs.interpolation")):
            showInterpolation(self.callbacks)
        with dpg.tab(tag="meshGenerationTab", label=strings.t("app.tabs.mesh_generation")):
            showMeshGeneration(self.callbacks)
        with dpg.tab(tag="simulationTab", label=strings.t("app.tabs.simulation")):
            showSimulation(self.callbacks)
        self.callbacks.imageProcessing.disableAllTags()

    def createSaveImageDialog(self):
        with dpg.window(
            label=strings.t("common.export_image_as_file"),
            modal=False,
            show=False,
            tag="exportImageAsFile",
            no_title_bar=False,
            min_size=[600, 255],
        ):
            dpg.add_text(strings.t("common.enter_file_name"), tag="exportImageDialogFileNameLabel")
            dpg.add_input_text(tag="imageNameExportAsFile")
            dpg.add_separator()
            dpg.add_text(strings.t("common.enter_file_name_before_directory"), tag="exportImageDialogDirectoryHint")
            dpg.add_button(
                tag="exportImageDialogSelectDirectory",
                width=-1,
                label=strings.t("common.select_directory"),
                callback=self.callbacks.imageProcessing.exportImageDirectorySelector,
            )
            dpg.add_file_dialog(
                directory_selector=True,
                min_size=[400, 300],
                show=False,
                tag="exportImageDirectorySelector",
                callback=lambda sender, app_data: self.callbacks.imageProcessing.exportImageSelectDirectory(sender, app_data),
            )
            dpg.add_separator()
            dpg.add_text(strings.fmt("file_name", value=""), tag="exportImageFileName")
            dpg.add_text(strings.fmt("full_path", value=""), tag="exportImageFilePath")
            with dpg.group(horizontal=True):
                dpg.add_button(
                    tag="exportImageDialogSave",
                    label=strings.t("common.save"),
                    width=-1,
                    callback=self.callbacks.imageProcessing.exportImageAsFile,
                )
                dpg.add_button(
                    tag="exportImageDialogCancel",
                    label=strings.t("common.cancel"),
                    width=-1,
                    callback=lambda: dpg.configure_item("exportImageAsFile", show=False),
                )
            dpg.add_text(strings.t("common.missing_file_name_or_directory"), tag="exportImageError", show=False)

    def createSaveHistogramDialog(self):
        with dpg.window(
            label=strings.t("common.export_histogram_as_file"),
            modal=False,
            show=False,
            tag="exportHistogramAsFile",
            no_title_bar=False,
            min_size=[600, 255],
        ):
            dpg.add_text(strings.t("common.enter_file_name"), tag="exportHistogramDialogFileNameLabel")
            dpg.add_input_text(tag="histogramNameExportAsFile")
            dpg.add_separator()
            dpg.add_text(strings.t("common.enter_file_name_before_directory"), tag="exportHistogramDialogDirectoryHint")
            dpg.add_button(
                tag="exportHistogramDialogSelectDirectory",
                width=-1,
                label=strings.t("common.select_directory"),
                callback=self.callbacks.imageProcessing.exportHistogramDirectorySelector,
            )
            dpg.add_file_dialog(
                directory_selector=True,
                min_size=[400, 300],
                show=False,
                tag="exportHistogramDirectorySelector",
                callback=lambda sender, app_data: self.callbacks.imageProcessing.exportHistogramSelectDirectory(sender, app_data),
            )
            dpg.add_separator()
            dpg.add_text(strings.fmt("file_name", value=""), tag="exportHistogramFileName")
            dpg.add_text(strings.fmt("full_path", value=""), tag="exportHistogramFilePath")
            with dpg.group(horizontal=True):
                dpg.add_button(
                    tag="exportHistogramDialogSave",
                    label=strings.t("common.save"),
                    width=-1,
                    callback=self.callbacks.imageProcessing.exportHistogramAsFile,
                )
                dpg.add_button(
                    tag="exportHistogramDialogCancel",
                    label=strings.t("common.cancel"),
                    width=-1,
                    callback=lambda: dpg.configure_item("exportHistogramAsFile", show=False),
                )
            dpg.add_text(strings.t("common.missing_file_name_or_directory"), tag="exportHistogramError", show=False)

    def changeStartupLocale(self, sender=None, app_data=None):
        self.selected_locale = strings.set_locale(app_data)
        self.refreshStartupTranslations()

    def changeStartupTheme(self, sender=None, app_data=None):
        self.selected_theme = strings.option_key("theme", app_data)
        apply_theme(self.selected_theme)
        bind_startup_themes()

    def refreshStartupTranslations(self):
        dpg.set_viewport_title(strings.t("app.title"))
        dpg.set_value("startupEyebrow", strings.t("startup.eyebrow"))
        dpg.set_value("startupAppTitle", strings.t("app.title"))
        dpg.set_value("startupSubtitle", strings.t("startup.subtitle"))
        dpg.set_value("startupLanguageLabel", strings.t("startup.language"))
        dpg.set_value("startupThemeLabel", strings.t("startup.theme"))
        dpg.configure_item("startupThemeSelector", items=strings.option_labels("theme"))
        dpg.set_value("startupThemeSelector", strings.option_label("theme", self.selected_theme))
        dpg.configure_item("startupEnterButton", label=strings.t("startup.enter"))
