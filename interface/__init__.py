import dearpygui.dearpygui as dpg
from ._extractionTab import showContourExtraction
from ._filteringTab import showFiltering
from ._meshTab import showMeshGeneration
from ._processingTab import showProcessing
from ._thresholdingTab import showThresholding
from ._theme import applyTheme

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
        dpg.create_viewport(title='ContExt - Image Processing Engine for Differential Calculus', width=900, height=600, min_height=600, min_width=900)

        with dpg.window(tag="Main"):
            applyTheme()
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
        with dpg.tab(label='Processing'):
            showProcessing(self.callbacks)
            pass
        with dpg.tab(label='Filtering'):
            showFiltering(self.callbacks)
            pass
        with dpg.tab(label='Thresholding'):
            showThresholding(self.callbacks)
            pass
        with dpg.tab(label='Contour Extraction'):
            showContourExtraction(self.callbacks)
            pass
        with dpg.tab(label='Mesh Generation'):
            showMeshGeneration(self.callbacks)
            pass
        self.callbacks.imageProcessing.disableAllTags()
        pass

    def createSaveImageDialog(self):
        with dpg.window(label="Export Image as File", modal=False, show=False, tag="exportImageAsFile", no_title_bar=False, min_size=[600,255]):
            dpg.add_text("Name your file")
            dpg.add_input_text(tag='imageNameExportAsFile')
            dpg.add_separator()
            dpg.add_text("You MUST enter a File Name to select a directory")
            dpg.add_button(width=-1, label='Select the directory', callback=self.callbacks.imageProcessing.exportImageDirectorySelector)
            dpg.add_file_dialog(directory_selector=True, min_size=[400,300], show=False, tag='exportImageDirectorySelector', id="exportImageDirectorySelector", callback=lambda sender, app_data: self.callbacks.imageProcessing.exportImageSelectDirectory(sender, app_data))
            dpg.add_separator()
            dpg.add_text('File Name: ', tag='exportImageFileName')
            dpg.add_text('Complete Path Name: ', tag='exportImageFilePath')
            with dpg.group(horizontal=True):
                dpg.add_button(label='Save', width=-1, callback=self.callbacks.imageProcessing.exportImageAsFile)
                dpg.add_button(label='Cancel', width=-1, callback=lambda: dpg.configure_item('exportImageAsFile', show=False))
            dpg.add_text("Missing file name or directory.", tag="exportImageError", show=False)