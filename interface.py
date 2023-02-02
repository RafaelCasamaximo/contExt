from subprocess import call
import dearpygui.dearpygui as dpg
from math import *

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
            self.showTabBar()
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

                dpg.add_text('Select a image to use.')
                dpg.add_button(tag='import_image', label='Import Image', callback=lambda: dpg.show_item("file_dialog_id"))
                with dpg.tooltip("import_image"):
                    dpg.add_text("Não é possível importar mais de uma imagem! Feche o programa e abra-o novamente para importar outra imagem.")
                dpg.add_text('File Name:', tag='file_name_text')
                dpg.add_text('File Path:', tag='file_path_text')
                dpg.add_separator()

                with dpg.group(horizontal=True):
                    dpg.add_checkbox(callback=lambda sender, app_data: self.callbacks.toggleEffect('crop', sender, app_data))
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
                    dpg.add_text('Start X')
                    dpg.add_input_int(tag='startX')
                with dpg.group(horizontal=True):
                    dpg.add_text('Start Y')
                    dpg.add_input_int(tag='startY')
                with dpg.group(horizontal=True):
                    dpg.add_text('End X')
                    dpg.add_input_int(tag='endX')
                with dpg.group(horizontal=True):
                    dpg.add_text('End Y')
                    dpg.add_input_int(tag='endY')
                dpg.add_button(label='Apply Changes', callback=lambda: self.callbacks.executeQuery('crop'))
                dpg.add_separator()

                pass
            with dpg.child_window(tag='ProcessingParent'):
                pass

    def showFiltering(self):
        with dpg.group(horizontal=True):
            with dpg.child_window(width=300):
                with dpg.group(horizontal=True):
                    dpg.add_checkbox(callback=lambda sender, app_data: self.callbacks.toggleAndExecuteQuery('histogramEqualization', sender, app_data));
                    dpg.add_text('Histogram Equalization')
                dpg.add_separator()

                with dpg.group(horizontal=True):
                    dpg.add_checkbox(callback=lambda sender, app_data: self.callbacks.toggleAndExecuteQuery('brightnessAndContrast', sender, app_data))
                    dpg.add_text('Brightness and Contrast')
                dpg.add_text('Brightness')
                dpg.add_slider_int(default_value=0, min_value=-100, max_value=100, tag='brightnessSlider', callback=lambda: self.callbacks.executeQuery('brightnessAndContrast'))
                dpg.add_text('Contrast')
                dpg.add_slider_float(default_value=1.0, min_value=0.0, max_value=3.0, tag='contrastSlider', callback=lambda: self.callbacks.executeQuery('brightnessAndContrast'))
                dpg.add_separator()
                
                with dpg.group(horizontal=True):
                    dpg.add_checkbox(callback=lambda sender, app_data: self.callbacks.toggleAndExecuteQuery('averageBlur', sender, app_data))
                    dpg.add_text('Average Blur')
                dpg.add_text('Intensity')
                dpg.add_slider_int(tag='averageBlurSlider', default_value=1, min_value=1, max_value=100, callback=lambda: self.callbacks.executeQuery('averageBlur'))
                dpg.add_separator()

                with dpg.group(horizontal=True):
                    dpg.add_checkbox(callback=lambda sender, app_data: self.callbacks.toggleAndExecuteQuery('gaussianBlur', sender, app_data))
                    dpg.add_text('Gaussian Blur')
                dpg.add_text('Intensity')
                dpg.add_slider_int(tag='gaussianBlurSlider', default_value=1, min_value=1, max_value=100, callback=lambda: self.callbacks.executeQuery('gaussianBlur'))
                dpg.add_separator()

                with dpg.group(horizontal=True):
                    dpg.add_checkbox(callback=lambda sender, app_data: self.callbacks.toggleAndExecuteQuery('medianBlur', sender, app_data))
                    dpg.add_text('Median Blur')
                dpg.add_text('Intensity')
                dpg.add_slider_int(tag='medianBlurSlider', default_value=1, min_value=1, max_value=100, callback=lambda: self.callbacks.executeQuery('medianBlur'))
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
                    dpg.add_checkbox(callback=lambda sender, app_data: self.callbacks.toggleAndExecuteQuery('globalThresholding', sender, app_data))
                    dpg.add_text('Global Thresholding')
                with dpg.group(horizontal=True):
                    dpg.add_checkbox(tag='invertGlobalThresholding', callback=lambda: self.callbacks.executeQuery('globalThresholding'))
                    dpg.add_text('Invert Tresholding')
                dpg.add_text('Threshold')
                dpg.add_slider_int(tag='globalThresholdSlider', default_value=127, min_value=0, max_value=255, callback=lambda: self.callbacks.executeQuery('globalThresholding'))
                dpg.add_separator()

                with dpg.group(horizontal=True):
                    dpg.add_checkbox(callback=lambda sender, app_data: self.callbacks.toggleAndExecuteQuery('adaptativeMeanThresholding', sender, app_data))
                    dpg.add_text('Adaptative Mean Thresholding')
                dpg.add_separator()

                with dpg.group(horizontal=True):
                    dpg.add_checkbox(callback=lambda sender, app_data: self.callbacks.toggleAndExecuteQuery('adaptativeGaussianThresholding', sender, app_data))
                    dpg.add_text('Adaptative Gaussian Thresholding')
                dpg.add_separator()

                with dpg.group(horizontal=True):
                    dpg.add_checkbox(callback=lambda sender, app_data: self.callbacks.toggleAndExecuteQuery('otsuBinarization', sender, app_data))
                    dpg.add_text('Otsu\'s Binarization')
                dpg.add_text('(Works better after Gaussian Blur)')
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
                dpg.add_slider_int(tag='contourThicknessSlider', default_value=1, min_value=1, max_value=100)
                dpg.add_button(label='Apply Method', callback=lambda sender, app_data: self.callbacks.extractContour(sender, app_data))

                dpg.add_separator()
                dpg.add_text('Moore Neighborhood')
                dpg.add_text('Initial Pixel')
                dpg.add_input_int(label='X', min_value=0, min_clamped=True)
                dpg.add_input_int(label='Y', min_value=0, min_clamped=True)
                dpg.add_text('Search Direction')
                dpg.add_listbox(items=['Up', 'Right', 'Down', 'Left'])
                dpg.add_button(label='Apply Method')
                dpg.add_separator()


                dpg.add_text('Export Settings')
                dpg.add_text('Max Width Mapping')
                dpg.add_input_double()
                dpg.add_text('Max Height Mapping')
                dpg.add_input_double()
                dpg.add_text('X Offset')
                dpg.add_input_double()
                dpg.add_text('Y Offset')
                dpg.add_input_double()
                dpg.add_checkbox(label='Matlab mode')
                dpg.add_checkbox(label='Metadata')
                dpg.add_button(label='Export Contour')
                dpg.add_separator()


                pass
            with dpg.child_window(tag='ContourExtractionParent'):
                pass

    def showMeshGeneration(self):
        with dpg.group(horizontal=True):
            with dpg.child_window(width=300):
                
                with dpg.file_dialog(directory_selector=False, show=False, min_size=[400,300], tag='txt_file_dialog_id', id="txt_file_dialog_id", callback=self.callbacks.importContour):
                    dpg.add_file_extension("", color=(150, 255, 150, 255))
                    dpg.add_file_extension(".txt", color=(0, 255, 255, 255))
                    dpg.add_file_extension(".dat", color=(0, 255, 255, 255))


                dpg.add_text('Select a contour file to use.')
                dpg.add_button(tag='import_contour', label='Import Contour', callback=lambda: dpg.show_item("txt_file_dialog_id"))

                dpg.add_text('File Name:', tag='contour_file_name_text')
                dpg.add_text('File Path:', tag='contour_file_path_text')
                dpg.add_separator()

                dpg.add_text('Contour ordering')
                dpg.add_button(tag='contour_ordering', enabled=False, label='Anticlockwise', callback=self.callbacks.toggleOrdering)
                with dpg.tooltip("contour_ordering"):
                        dpg.add_text("Click to change contour ordering. If the ordering is incorrect the mesh generation may have some errors")

                dpg.add_separator()

                dpg.add_text('Original Nodes Number:')
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
                
                dpg.add_text('Sparse and adataptive mesh')
                dpg.add_button(label='Add mesh zoom region', tag="sparseButton", callback=lambda: dpg.configure_item("sparsePopup", show=True))

                with dpg.window(label='Add mesh zoom region', modal=True, show=False, tag="sparsePopup", no_title_bar=True, min_size=[400,300]):
                    dpg.add_text('Type of mesh zoom')
                    dpg.add_button(tag='meshZoomType', enabled=True, label='Sparse', callback=self.callbacks.toggleZoom)
                    with dpg.tooltip("meshZoomType"):
                        dpg.add_text("Click to change the mesh zoom type.", tag="meshZoomTypeTooltip")
                    
                    dpg.add_separator()
                    dpg.add_text('Zoom region name')
                    dpg.add_input_text(tag="zoomRegionName", default_value="Zoom region 1")

                    dpg.add_separator()
                    dpg.add_text('Zoom node size')
                    dpg.add_listbox(tag='dxListbox', items=['Divide by 2', 'Divide by 4', 'Divide by 8', 'Divide by 16'])
                    
                    dpg.add_separator()
                    dpg.add_text('Zoom bottom')
                    with dpg.group(horizontal=True):
                        dpg.add_text('Bottom x:')
                        dpg.add_input_float(tag='xi_zoom')
                    with dpg.group(horizontal=True):
                        dpg.add_text('Bottom y:')
                        dpg.add_input_float(tag='yi_zoom')

                    dpg.add_separator()
                    dpg.add_text('Zoom top')
                    with dpg.group(horizontal=True):
                        dpg.add_text('Top x:')
                        dpg.add_input_float(tag='xf_zoom')
                    with dpg.group(horizontal=True):
                        dpg.add_text('top y:')
                        dpg.add_input_float(tag='yf_zoom')
                    
                    dpg.add_separator()
                    with dpg.group(horizontal=True):
                        dpg.add_button(label="Add zoom", width=75, callback=self.callbacks.addZoomRegion)
                        dpg.add_button(label="Cancel", width=75, callback=lambda: dpg.configure_item("sparsePopup", show=False))

            with dpg.child_window(tag='MeshGenerationParent'):
                with dpg.plot(tag="meshPlotParent", label="Mesh Plot", height=650, width=750):
                    dpg.add_plot_legend()
                    dpg.add_plot_axis(dpg.mvXAxis, label="x", tag="x_axis")
                    dpg.add_plot_axis(dpg.mvYAxis, label="y", tag="y_axis")

                dpg.add_text('Original Area: --', tag='original_area')
                dpg.add_text('Current Area: --', tag='current_area')
                dpg.add_text('Difference: --', tag='difference')   
                pass
