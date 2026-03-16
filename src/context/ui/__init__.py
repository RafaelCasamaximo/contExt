import dearpygui.dearpygui as dpg
from ._extractionTab import refreshContourExtractionTranslations, showContourExtraction
from ._filteringTab import refreshFilteringTranslations, showFiltering
from ._meshTab import refreshMeshTranslations, showMeshGeneration
from ._processingTab import refreshProcessingTranslations, showProcessing
from ._thresholdingTab import refreshThresholdingTranslations, showThresholding
from ._interpolationTab import refreshInterpolationTranslations, showInterpolation
from ._theme import applyTheme
from . import strings

"""
    A classe Interface é responsável por gerar os elementos visuais do programa.
    O uso da biblioteca DearPyGUI faz com que seja possível executar o programa em windows ou linux
    e ainda utilizar dos benefícios da acerelação de hardware.        
"""
class Interface:

    """
        Define os parâmetros e inicia a função Show.
    """
    def __init__(self, callbacks) -> None:
        self.callbacks = callbacks
        self.show()
        pass

    """
        Cria o contexto e a janela do DPG e invoca a função showTabBar para a renderização de cada uma das tabs e seus conteúdos.
    """
    def show(self):
        dpg.create_context()
        dpg.create_viewport(title=strings.t("app.title"), width=900, height=600, min_height=600, min_width=900)

        with dpg.window(tag="Main"):
            applyTheme()
            with dpg.group(horizontal=True):
                dpg.add_text(strings.t("app.language"), tag="languageLabel")
                dpg.add_combo(
                    strings.available_locales(),
                    default_value=strings.get_locale(),
                    width=140,
                    tag="languageSelector",
                    callback=self.changeLocale,
                )
            self.showTabBar()
            self.createSaveImageDialog()
            pass
        
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("Main", True)
        dpg.start_dearpygui()
        dpg.destroy_context()
        pass

    """
        Responsável pela invocação das tabs individuais.
    """
    def showTabBar(self):
        with dpg.tab_bar():
            self.showTabs()
        pass

    """
        Cria as diferentes tabs do programa e chama o método show<Tab> para popular cada uma das abas.
        Processing: Importação e Cropping da imagem.
        Filtering: Ajustes em níveis de cor, brilho, contraste e blurring na imagem.
        Thresholding: Ajustes na binarização da imagem. Para que a binarização ocorra a imagem é automaticamente convertida para tons de cinza.
        Contour Extraction: Extrai o contorno dos objetos presentes na imagem binarizada. Permite a exportação do arquivo .txt com os dados do contorno.
        Mesh Generation: Gera a malha e possibilita as configurações necessária para método matemáticos com os pontos resultantes da aba anterior. Permite a importação de novos pontos.
    """
    def showTabs(self):
        dpg.add_texture_registry(show=False, tag='textureRegistry')
        with dpg.tab(tag="processingTab", label=strings.t("app.tabs.processing")):
            showProcessing(self.callbacks)
            pass
        with dpg.tab(tag="filteringTab", label=strings.t("app.tabs.filtering")):
            showFiltering(self.callbacks)
            pass
        with dpg.tab(tag="thresholdingTab", label=strings.t("app.tabs.thresholding")):
            showThresholding(self.callbacks)
            pass
        with dpg.tab(tag="contourExtractionTab", label=strings.t("app.tabs.contour_extraction")):
            showContourExtraction(self.callbacks)
            pass
        with dpg.tab(tag="interpolationTab", label=strings.t("app.tabs.interpolation")):
            showInterpolation(self.callbacks)
            pass
        with dpg.tab(tag="meshGenerationTab", label=strings.t("app.tabs.mesh_generation")):
            showMeshGeneration(self.callbacks)
            pass
        self.callbacks.imageProcessing.disableAllTags()
        pass

    def createSaveImageDialog(self):
        with dpg.window(label=strings.t("common.export_image_as_file"), modal=False, show=False, tag="exportImageAsFile", no_title_bar=False, min_size=[600,255]):
            dpg.add_text(strings.t("common.enter_file_name"), tag="exportImageDialogFileNameLabel")
            dpg.add_input_text(tag="imageNameExportAsFile")
            dpg.add_separator()
            dpg.add_text(strings.t("common.enter_file_name_before_directory"), tag="exportImageDialogDirectoryHint")
            dpg.add_button(tag="exportImageDialogSelectDirectory", width=-1, label=strings.t("common.select_directory"), callback=self.callbacks.imageProcessing.exportImageDirectorySelector)
            dpg.add_file_dialog(directory_selector=True, min_size=[400,300], show=False, tag='exportImageDirectorySelector', id="exportImageDirectorySelector", callback=lambda sender, app_data: self.callbacks.imageProcessing.exportImageSelectDirectory(sender, app_data))
            dpg.add_separator()
            dpg.add_text(strings.fmt("file_name", value=""), tag="exportImageFileName")
            dpg.add_text(strings.fmt("full_path", value=""), tag="exportImageFilePath")
            with dpg.group(horizontal=True):
                dpg.add_button(tag="exportImageDialogSave", label=strings.t("common.save"), width=-1, callback=self.callbacks.imageProcessing.exportImageAsFile)
                dpg.add_button(tag="exportImageDialogCancel", label=strings.t("common.cancel"), width=-1, callback=lambda: dpg.configure_item("exportImageAsFile", show=False))
            dpg.add_text(strings.t("common.missing_file_name_or_directory"), tag="exportImageError", show=False)

    def changeLocale(self, sender=None, app_data=None):
        old_locale = strings.get_locale()
        strings.set_locale(app_data)
        self.refreshTranslations(old_locale)

    def refreshTranslations(self, old_locale=None):
        dpg.set_viewport_title(strings.t("app.title"))
        dpg.set_value("languageLabel", strings.t("app.language"))
        dpg.configure_item("processingTab", label=strings.t("app.tabs.processing"))
        dpg.configure_item("filteringTab", label=strings.t("app.tabs.filtering"))
        dpg.configure_item("thresholdingTab", label=strings.t("app.tabs.thresholding"))
        dpg.configure_item("contourExtractionTab", label=strings.t("app.tabs.contour_extraction"))
        dpg.configure_item("interpolationTab", label=strings.t("app.tabs.interpolation"))
        dpg.configure_item("meshGenerationTab", label=strings.t("app.tabs.mesh_generation"))

        dpg.configure_item("exportImageAsFile", label=strings.t("common.export_image_as_file"))
        dpg.set_value("exportImageDialogFileNameLabel", strings.t("common.enter_file_name"))
        dpg.set_value("exportImageDialogDirectoryHint", strings.t("common.enter_file_name_before_directory"))
        dpg.configure_item("exportImageDialogSelectDirectory", label=strings.t("common.select_directory"))
        dpg.configure_item("exportImageDialogSave", label=strings.t("common.save"))
        dpg.configure_item("exportImageDialogCancel", label=strings.t("common.cancel"))
        dpg.set_value("exportImageError", strings.t("common.missing_file_name_or_directory"))

        refreshProcessingTranslations()
        refreshFilteringTranslations()
        refreshThresholdingTranslations(old_locale)
        refreshContourExtractionTranslations(old_locale)
        refreshInterpolationTranslations(old_locale)
        refreshMeshTranslations(old_locale)
        self.callbacks.refreshTranslations(old_locale)
