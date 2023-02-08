from subprocess import call
import dearpygui.dearpygui as dpg
from math import *
import os
import sys
import platform

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
            self.applyTheme()
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
            self.showProcessing()
            pass
        with dpg.tab(label='Filtering'):
            self.showFiltering()
            pass
        with dpg.tab(label='Thresholding'):
            self.showThresholding()
            pass
        with dpg.tab(label='Contour Extraction'):
            self.showContourExtraction()
            pass
        with dpg.tab(label='Mesh Generation'):
            self.showMeshGeneration()
            pass
        self.callbacks.disableAllTags()
        pass

    def showProcessing(self):
        with dpg.group(horizontal=True):
            with dpg.child_window(width=300):

                with dpg.file_dialog(directory_selector=False, min_size=[400,300], show=False, tag='file_dialog_id', id="file_dialog_id", callback=self.callbacks.openFile):
                    dpg.add_file_extension("", color=(150, 255, 150, 255))
                    dpg.add_file_extension(".jpg", color=(0, 255, 255, 255))
                    dpg.add_file_extension(".png", color=(0, 255, 255, 255))
                    dpg.add_file_extension(".jpeg", color=(0, 255, 255, 255))
                    dpg.add_file_extension(".bmp", color=(0, 255, 255, 255))
                    dpg.add_file_extension(".pgm", color=(0, 255, 255, 255))
                    dpg.add_file_extension(".ppm", color=(0, 255, 255, 255))
                    dpg.add_file_extension(".sr", color=(0, 255, 255, 255))
                    dpg.add_file_extension(".ras", color=(0, 255, 255, 255))
                    dpg.add_file_extension(".jpe", color=(0, 255, 255, 255))
                    dpg.add_file_extension(".jp2", color=(0, 255, 255, 255))
                    dpg.add_file_extension(".tiff", color=(0, 255, 255, 255))
                    dpg.add_file_extension(".tif", color=(0, 255, 255, 255))

                dpg.add_text('Select a Image to Use')
                dpg.add_button(tag='import_image', label='Import Image', callback=lambda: dpg.show_item("file_dialog_id"))
                with dpg.tooltip("import_image"):
                    dpg.add_text("It is not possible to import more than one image! Close the program and open it again to import another image.")
                dpg.add_text('File Name:', tag='file_name_text')
                dpg.add_text('File Path:', tag='file_path_text')
                dpg.add_separator()

                with dpg.group(horizontal=True):
                    dpg.add_checkbox(tag='cropCheckbox', callback=lambda sender, app_data: self.callbacks.toggleEffect('crop', sender, app_data))
                    dpg.add_text('Cropping')
                    dpg.add_button(label='Reset', callback=lambda: self.callbacks.resetCrop())
                dpg.add_text('Original Resolution:')
                dpg.add_text('Width:', tag='originalWidth')
                dpg.add_text('Height:', tag='originalHeight')
                dpg.add_text('Current Resolution:')
                dpg.add_text('Width:', tag='currentWidth')
                dpg.add_text('Height:', tag='currentHeight')
                dpg.add_text('New Resolution')
                with dpg.group(horizontal=True):
                    dpg.add_text('Start Width')
                    dpg.add_input_int(tag='startY')
                with dpg.group(horizontal=True):
                    dpg.add_text('Start Height')
                    dpg.add_input_int(tag='startX')
                with dpg.group(horizontal=True):
                    dpg.add_text('End Width')
                    dpg.add_input_int(tag='endY')
                with dpg.group(horizontal=True):
                    dpg.add_text('End Height')
                    dpg.add_input_int(tag='endX')

                dpg.add_button(label='Apply Changes', callback=lambda: self.callbacks.executeQuery('crop'))

                with dpg.group(tag="exportImageAsFileProcessingGroup", show=False):
                    dpg.add_separator()
                    dpg.add_text("Save Image")
                    dpg.add_button(tag='exportImageAsFileProcessing', label='Export Image as File', callback=lambda sender, app_data: self.callbacks.exportImage(sender, app_data, 'Processing'))

                with dpg.window(label="ERROR! Crop not possible!", modal=True, show=False, tag="incorrectCrop", no_title_bar=False):
                    dpg.add_text("ERROR: The start values must be smaller than the end values.")
                    dpg.add_button(label="OK", width=75, callback=lambda: dpg.configure_item("incorrectCrop", show=False))

                with dpg.window(label="ERROR! There is no image!", modal=True, show=False, tag="noImage", no_title_bar=False):
                    dpg.add_text("ERROR: You must import an image.")
                    dpg.add_button(label="OK", width=75, callback=lambda: dpg.configure_item("noImage", show=False))
                dpg.add_separator()

                with dpg.window(label="ERROR! Select an image!", modal=True, show=False, tag="noPath", no_title_bar=False):
                    dpg.add_text("ERROR: This is not a valid path.")
                    dpg.add_button(label="OK", width=75, callback=lambda: dpg.configure_item("noPath", show=False))
                dpg.add_separator()

                pass

            with dpg.child_window(tag='ProcessingParent'):
                pass

    def showFiltering(self):
        with dpg.group(horizontal=True):
            with dpg.child_window(width=300):
                with dpg.group(horizontal=True):
                    dpg.add_checkbox(tag='histogramCheckbox', callback=lambda sender, app_data: self.callbacks.toggleAndExecuteQuery('histogramEqualization', sender, app_data));
                    dpg.add_text('Histogram Equalization')
                dpg.add_separator()

                with dpg.group(horizontal=True):
                    dpg.add_checkbox(tag='brightnessAndContrastCheckbox', callback=lambda sender, app_data: self.callbacks.toggleAndExecuteQuery('brightnessAndContrast', sender, app_data))
                    dpg.add_text('Brightness and Contrast')
                dpg.add_text('Brightness')
                dpg.add_slider_int(default_value=0, min_value=-100, max_value=100, tag='brightnessSlider', callback=lambda: self.callbacks.executeQuery('brightnessAndContrast'))
                dpg.add_text('Contrast')
                dpg.add_slider_float(default_value=1.0, min_value=0.0, max_value=3.0, tag='contrastSlider', callback=lambda: self.callbacks.executeQuery('brightnessAndContrast'))
                dpg.add_separator()
                
                with dpg.group(horizontal=True):
                    dpg.add_checkbox(tag='averageBlurCheckbox', callback=lambda sender, app_data: self.callbacks.toggleAndExecuteQuery('averageBlur', sender, app_data))
                    dpg.add_text('Average Blur')
                dpg.add_text('Intensity')
                dpg.add_slider_int(tag='averageBlurSlider', default_value=1, min_value=1, max_value=100, callback=lambda: self.callbacks.executeQuery('averageBlur'))
                dpg.add_separator()

                with dpg.group(horizontal=True):
                    dpg.add_checkbox(tag='gaussianBlurCheckbox', callback=lambda sender, app_data: self.callbacks.toggleAndExecuteQuery('gaussianBlur', sender, app_data))
                    dpg.add_text('Gaussian Blur')
                dpg.add_text('Intensity')
                dpg.add_slider_int(tag='gaussianBlurSlider', default_value=1, min_value=1, max_value=100, callback=lambda: self.callbacks.executeQuery('gaussianBlur'))
                dpg.add_separator()

                with dpg.group(horizontal=True):
                    dpg.add_checkbox(tag='medianBlurCheckbox', callback=lambda sender, app_data: self.callbacks.toggleAndExecuteQuery('medianBlur', sender, app_data))
                    dpg.add_text('Median Blur')
                dpg.add_text('Intensity')
                dpg.add_slider_int(tag='medianBlurSlider', default_value=1, min_value=1, max_value=100, callback=lambda: self.callbacks.executeQuery('medianBlur'))
                
                with dpg.group(tag="exportImageAsFileFilteringGroup", show=False):
                    dpg.add_separator()
                    dpg.add_text("Save Image")
                    dpg.add_button(tag='exportImageAsFileFiltering', label='Export Image as File', callback=lambda sender, app_data: self.callbacks.exportImage(sender, app_data, 'Filtering'))
                
                dpg.add_separator()
                dpg.add_separator()

                pass
            with dpg.child_window(tag='FilteringParent'):
                pass

    def showThresholding(self):
        with dpg.group(horizontal=True):
            with dpg.child_window(width=300):

                dpg.add_text('Grayscale Conversion')
                dpg.add_checkbox(label='Exclude Blue Channel', tag='excludeBlueChannel', callback=lambda: self.callbacks.executeQuery('grayscale'))
                dpg.add_checkbox(label='Exclude Green Channel', tag='excludeGreenChannel', callback=lambda: self.callbacks.executeQuery('grayscale'))
                dpg.add_checkbox(label='Exclude Red Channel', tag='excludeRedChannel', callback=lambda: self.callbacks.executeQuery('grayscale'))
                dpg.add_separator()

                with dpg.group(horizontal=True):
                    dpg.add_checkbox(tag='globalThresholdingCheckbox', callback=lambda sender, app_data: self.callbacks.toggleAndExecuteQuery('globalThresholding', sender, app_data))
                    dpg.add_text('Global Thresholding')
                with dpg.group(horizontal=True):
                    dpg.add_checkbox(tag='invertGlobalThresholding', callback=lambda: self.callbacks.executeQuery('globalThresholding'))
                    dpg.add_text('Invert Tresholding')
                dpg.add_text('Threshold')
                dpg.add_slider_int(tag='globalThresholdSlider', default_value=127, min_value=0, max_value=255, callback=lambda: self.callbacks.executeQuery('globalThresholding'))
                dpg.add_separator()

                with dpg.group(horizontal=True):
                    dpg.add_checkbox(tag='adaptativeThresholdingCheckbox', callback=lambda sender, app_data: self.callbacks.toggleAndExecuteQuery('adaptativeMeanThresholding', sender, app_data))
                    dpg.add_text('Adaptative Mean Thresholding')
                dpg.add_separator()

                with dpg.group(horizontal=True):
                    dpg.add_checkbox(tag='adaptativeGaussianThresholdingCheckbox', callback=lambda sender, app_data: self.callbacks.toggleAndExecuteQuery('adaptativeGaussianThresholding', sender, app_data))
                    dpg.add_text('Adaptative Gaussian Thresholding')
                dpg.add_separator()

                with dpg.group(horizontal=True):
                    dpg.add_checkbox(tag='otsuBinarization', callback=lambda sender, app_data: self.callbacks.toggleAndExecuteQuery('otsuBinarization', sender, app_data))
                    dpg.add_text('Otsu\'s Binarization')
                dpg.add_text('(Works better after Gaussian Blur)')

                with dpg.group(tag="exportImageAsFileThresholdingGroup", show=False):
                    dpg.add_separator()
                    dpg.add_text("Save Image")
                    dpg.add_button(tag='exportImageAsFileThresholding', label='Export Image as File', callback=lambda sender, app_data: self.callbacks.exportImage(sender, app_data, 'Thresholding'))

                dpg.add_separator()
                dpg.add_separator()

                pass
            with dpg.child_window(tag='ThresholdingParent'):
                pass

    def showContourExtraction(self):
        with dpg.group(horizontal=True):
            with dpg.child_window(width=300):
                dpg.add_text('OpenCV2 Find Contour')
                dpg.add_text('Approximation Mode')
                dpg.add_listbox(tag='approximationModeListbox', items=['None', 'Simple', 'TC89_L1', 'TC89_KCOS'])
                dpg.add_text('')
                dpg.add_text('Contour Thickness')
                dpg.add_text('(Only for the drawing)')
                dpg.add_slider_int(tag='contourThicknessSlider', default_value=3, min_value=1, max_value=100)
                dpg.add_button(tag='extractContourButton', label='Apply Method', callback=lambda sender, app_data: self.callbacks.extractContour(sender, app_data))
                with dpg.window(label="ERROR! The image must be in a binary color scheme!", modal=True, show=False, tag="nonBinary", no_title_bar=False):
                    dpg.add_text("ERROR: You must select a binarization filter on the Thresholding Tab.")
                    dpg.add_button(label="OK", width=75, callback=lambda: dpg.configure_item("nonBinary", show=False))
                dpg.add_separator()

                dpg.add_text('Contour Properties')
                dpg.add_text('Max Width Mapping')
                dpg.add_text('Current: --', tag="currentMaxWidth")
                dpg.add_input_double(tag='maxWidthMapping')
                dpg.add_text('Max Height Mapping')
                dpg.add_text('Current: --', tag="currentMaxHeight")
                dpg.add_input_double(tag='maxHeightMapping')
                dpg.add_text('Width Offset')
                dpg.add_text('Current: --', tag="currentWidthOffset")
                dpg.add_input_double(tag='widthOffset')
                dpg.add_text('Height Offset')
                dpg.add_text('Current: --', tag="currentHeightOffset")
                dpg.add_input_double(tag='heightOffset')
                dpg.add_checkbox(label='Matlab mode', tag='matlabModeCheckbox')
                with dpg.group(tag="changeContourParent"):
                    dpg.add_button(tag='updtadeContourButton', label='Apply Changes', callback=self.callbacks.updateContour)
                dpg.add_separator()
                dpg.add_separator()

                with dpg.window(label="Save File", modal=False, show=False, tag="exportContourWindow", no_title_bar=False, min_size=[600,280]):
                    dpg.add_text("Name your file")
                    dpg.add_input_text(tag='inputContourNameText')
                    dpg.add_separator()
                    dpg.add_text("You MUST enter a File Name to select a directory")
                    dpg.add_button(label='Select the directory', callback= self.callbacks.openDirectorySelector)
                    dpg.add_file_dialog(directory_selector=True, min_size=[400,300], show=False, tag='directorySelectorFileDialog', id="directorySelectorFileDialog", callback=self.callbacks.selectFolder)
                    dpg.add_separator()
                    dpg.add_text('Contour ID: ', tag='contourIdExportText')
                    dpg.add_text('File Name: ', tag='exportFileName')
                    dpg.add_text('Complete Path Name: ', tag='exportPathName')
                    with dpg.group(horizontal=True):
                        dpg.add_button(label='Save', callback=lambda: self.callbacks.exportIndividualContourToFile())
                        dpg.add_button(label='Cancel', callback=lambda: dpg.configure_item('exportContourWindow', show=False))
                    dpg.add_text("Missing file name or directory.", tag="exportContourError", show=False)

                with dpg.window(label="Save Files", modal=False, show=False, tag="exportSelectedContourWindow", no_title_bar=False, min_size=[600,255]):
                    dpg.add_text("Name the prefix of your file")
                    dpg.add_input_text(tag='inputSelectedContourNameText')
                    dpg.add_separator()
                    dpg.add_text("You MUST enter a prefix to the File Name to select a directory")
                    dpg.add_button(label='Select the directory', callback= self.callbacks.openExportSelectedDirectorySelector)
                    dpg.add_file_dialog(directory_selector=True, min_size=[400,300], show=False, tag='directoryFolderExportSelected', id="directoryFolderExportSelected", callback=self.callbacks.selectExportAllFolder)
                    dpg.add_separator()
                    dpg.add_text('File Default Name: ', tag='exportSelectedFileName')
                    dpg.add_text('Complete Path Name: ', tag='exportSelectedPathName')
                    with dpg.group(horizontal=True):
                        dpg.add_button(label='Save', callback=self.callbacks.exportSelectedContourToFile)
                        dpg.add_button(label='Cancel', callback=lambda: dpg.configure_item('exportSelectedContourWindow', show=False))
                    dpg.add_text("Missing file name or directory.", tag="exportSelectedContourError", show=False)
                    
                pass
            with dpg.child_window(tag='ContourExtractionParent'):
                pass


    def showMeshGeneration(self):
        with dpg.group(horizontal=True):
            with dpg.child_window(width=300, tag="meshGeneration"):
                
                with dpg.file_dialog(directory_selector=False, show=False, min_size=[400,300], tag='txt_file_dialog_id', id="txt_file_dialog_id", callback=self.callbacks.openContourFile):
                    dpg.add_file_extension("", color=(150, 255, 150, 255))
                    dpg.add_file_extension(".txt", color=(0, 255, 255, 255))
                    dpg.add_file_extension(".dat", color=(0, 255, 255, 255))


                dpg.add_text('Select a contour file to use.')
                dpg.add_button(tag='import_contour', label='Import Contour', callback=lambda: dpg.show_item("txt_file_dialog_id"))

                dpg.add_text('File Name:', tag='contour_file_name_text')
                dpg.add_text('File Path:', tag='contour_file_path_text')
                
                with dpg.window(label='Error', modal=True, show=False, tag="txtFileErrorPopup"):
                    dpg.add_text("File doesn't contain a valid contour")
                    dpg.add_button(label="Ok", callback=lambda: dpg.configure_item("txtFileErrorPopup", show=False))

                dpg.add_separator()

                dpg.add_text('Contour Ordering')
                dpg.add_button(tag='contour_ordering', enabled=False, label='Anticlockwise', callback=self.callbacks.toggleOrdering)
                with dpg.tooltip("contour_ordering"):
                    dpg.add_text("Click to change contour ordering. If the ordering is incorrect the mesh generation may have some errors")

                dpg.add_separator()

                dpg.add_text("Mesh Grid")
                dpg.add_button(label ='Plot Mesh Grid', tag='plotGrid', callback=self.callbacks.toggleGrid, enabled=False)
                with dpg.tooltip("plotGrid"):
                    dpg.add_text("Click to draw mesh grid and count the number of internal node. Might take a while.")
                
                dpg.add_separator()

                dpg.add_text('Mesh Generation Options')
                dpg.add_text('Original Nodes Number:', tag="nodeNumber")
                with dpg.tooltip("nodeNumber", tag="nodeNumberTooltip", show=False):
                        dpg.add_text("Doesn't account submesh nodes number.")
                dpg.add_text('nx: --', tag='original_nx')
                dpg.add_text('ny: --', tag='original_ny')
                dpg.add_text('Nodes Number:')
                dpg.add_text('nx: --', tag='nx')
                dpg.add_text('ny: --', tag='ny')

                dpg.add_text('Original Node Size:')
                dpg.add_text('dx: --', tag='original_dx')
                dpg.add_text('dy: --', tag='original_dy')
                dpg.add_text('Node Size')
                with dpg.group(horizontal=True):
                    dpg.add_text('dx:')
                    dpg.add_input_float(tag='dx', default_value=1, min_value=1, min_clamped=True)
                with dpg.group(horizontal=True):
                    dpg.add_text('dy:')
                    dpg.add_input_float(tag='dy', default_value=1, min_value=1, min_clamped=True)

                dpg.add_text('Original Mesh Start:')
                dpg.add_text('x: --', tag='original_xi')
                dpg.add_text('y: --', tag='original_yi')
                dpg.add_text('Mesh Start')
                with dpg.group(horizontal=True):
                    dpg.add_text('x:')
                    dpg.add_input_float(tag='xi')
                with dpg.group(horizontal=True):
                    dpg.add_text('y:')
                    dpg.add_input_float(tag='yi')
                dpg.add_button(label='Apply Changes', callback= self.callbacks.updateMesh)
                dpg.add_separator()
                
                with dpg.group(tag="sparseGroup"):
                    dpg.add_text('Sparse and Adataptive Mesh')
                    dpg.add_button(label='Add Mesh Zoom Region', enabled=False, tag="sparseButton", callback=lambda: dpg.configure_item("sparsePopup", show=True))
                    dpg.add_button(label ='Reset Mesh', tag='resetMesh', callback=self.callbacks.resetMesh, show=False)
                    with dpg.tooltip("resetMesh"):
                        dpg.add_text("Click to remove all zoom regions.")

                dpg.add_separator()
                
                dpg.add_text("Save Mesh")
                dpg.add_button(tag='exportMesh', enabled=False, label='Export Mesh', callback=lambda: dpg.configure_item("exportMeshFile", show=True))
                with dpg.tooltip("exportMesh"):
                    dpg.add_text("Click to save mesh data in text files.")
                
                with dpg.window(label='Add Mesh Zoom Region', modal=True, show=False, tag="sparsePopup", min_size=[400,420]):
                    dpg.add_text('Type of Mesh Zoom')
                    dpg.add_button(tag='meshZoomType', enabled=True, label='Sparse', callback=self.callbacks.toggleZoom)
                    with dpg.tooltip("meshZoomType"):
                        dpg.add_text("Click to change the mesh zoom type.", tag="meshZoomTypeTooltip")
                    
                    dpg.add_separator()
                    dpg.add_text('Zoom Region Name')
                    dpg.add_input_text(tag="zoomRegionName", default_value="Zoom region 1")

                    dpg.add_separator()
                    dpg.add_text('Zoom Node Size')
                    dpg.add_listbox(tag='dxListbox', items=['Divided by 2', 'Divided by 4', 'Divided by 8', 'Divided by 16'])
                    
                    dpg.add_separator()
                    dpg.add_text('Zoom Bottom')
                    with dpg.group(horizontal=True):
                        dpg.add_text('Bottom x:')
                        dpg.add_input_float(tag='xi_zoom')
                    with dpg.group(horizontal=True):
                        dpg.add_text('Bottom y:')
                        dpg.add_input_float(tag='yi_zoom')

                    dpg.add_separator()
                    dpg.add_text('Zoom Top')
                    with dpg.group(horizontal=True):
                        dpg.add_text('Top x:')
                        dpg.add_input_float(tag='xf_zoom')
                    with dpg.group(horizontal=True):
                        dpg.add_text('Top y:')
                        dpg.add_input_float(tag='yf_zoom')
                    
                    dpg.add_separator()
                    with dpg.group(horizontal=True):
                        dpg.add_button(label="Add Zoom", width=100, callback=self.callbacks.addZoomRegion)
                        dpg.add_button(label="Cancel", width=100, callback=lambda: dpg.configure_item("sparsePopup", show=False))
                    dpg.add_text("Invalid range due to overlap", tag="addZoomError", show=False)

                with dpg.window(label="Save File", modal=False, show=False, tag="exportMeshFile", no_title_bar=False, min_size=[600,255]):
                    dpg.add_text("Name your file")
                    dpg.add_input_text(tag='inputMeshNameText')
                    dpg.add_separator()
                    dpg.add_text("You MUST enter a File Name to select a directory")
                    dpg.add_button(label='Select the directory', callback= self.callbacks.openMeshDirectorySelector)
                    dpg.add_file_dialog(directory_selector=True, min_size=[400,300], show=False, tag='meshDirectorySelectorFileDialog', id="meshDirectorySelectorFileDialog", callback=self.callbacks.selectMeshFileFolder)
                    dpg.add_separator()
                    dpg.add_text('File Name: ', tag='exportMeshFileName')
                    dpg.add_text('Complete Path Name: ', tag='exportMeshPathName')
                    with dpg.group(horizontal=True):
                        dpg.add_button(label='Save', callback=lambda: self.callbacks.exportMesh())
                        dpg.add_button(label='Cancel', callback=lambda: dpg.configure_item('exportMeshWindow', show=False))
                    dpg.add_text("Missing file name or directory.", tag="exportMeshError", show=False)

                dpg.add_separator()

            with dpg.child_window(tag='MeshGenerationParent'):
                with dpg.theme(tag="grid_plot_theme"):
                    with dpg.theme_component(dpg.mvLineSeries):
                        dpg.add_theme_color(dpg.mvPlotCol_Line, (100, 100, 100), category=dpg.mvThemeCat_Plots)
                with dpg.plot(tag="meshPlotParent", label="Mesh Plot", height=650, width=650):
                    dpg.add_plot_legend()
                    dpg.add_plot_axis(dpg.mvXAxis, label="x", tag="x_axis")
                    dpg.add_plot_axis(dpg.mvYAxis, label="y", tag="y_axis")

                with dpg.group(horizontal=True):
                    dpg.add_text('Original Area: --', tag='original_area')
                    dpg.add_text('Current Area: --', tag='current_area')
                    dpg.add_text('Difference: --', tag='difference')
                with dpg.group(horizontal=True):
                    dpg.add_text('Contour Nodes Number: --', tag='contour_nodes_number')
                    dpg.add_text('Internal Nodes Number: --', tag='current_nodes_number', show=False)   
                pass


    def applyTheme(self):

        dpg.set_viewport_small_icon("icons/Icon.ico")
        dpg.set_viewport_large_icon("icons/Icon.ico")

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

        fontPath = ''
        fontPathWindows = 'fonts\Inter-Regular.otf'
        fontPathLinux = 'fonts/Inter-Regular.otf'

        if platform.system() == 'Windows':
            fontPath = fontPathWindows
        else:
            fontPath = fontPathLinux

        if platform.system() == 'Windows':
            fontPath = self.get_correct_path(fontPath)

        try:
            with dpg.font_registry():
                default_font = dpg.add_font(fontPath, 16)

            dpg.bind_font(default_font)
        except:
            pass

    def get_correct_path(self, relative_path):
        return os.path.join(
            os.environ.get(
                "_MEIPASS2",
                os.path.abspath(".")
            ),
            relative_path
        )

    def createSaveImageDialog(self):
        with dpg.window(label="Export Image as File", modal=False, show=False, tag="exportImageAsFile", no_title_bar=False, min_size=[600,255]):
            dpg.add_text("Name your file")
            dpg.add_input_text(tag='imageNameExportAsFile')
            dpg.add_separator()
            dpg.add_text("You MUST enter a File Name to select a directory")
            dpg.add_button(label='Select the directory', callback=self.callbacks.exportImageDirectorySelector)
            dpg.add_file_dialog(directory_selector=True, min_size=[400,300], show=False, tag='exportImageDirectorySelector', id="exportImageDirectorySelector", callback=lambda sender, app_data: self.callbacks.exportImageSelectDirectory(sender, app_data))
            dpg.add_separator()
            dpg.add_text('File Name: ', tag='exportImageFileName')
            dpg.add_text('Complete Path Name: ', tag='exportImageFilePath')
            with dpg.group(horizontal=True):
                dpg.add_button(label='Save', callback=self.callbacks.exportImageAsFile)
                dpg.add_button(label='Cancel', callback=lambda: dpg.configure_item('exportImageAsFile', show=False))
            dpg.add_text("Missing file name or directory.", tag="exportImageError", show=False)     