import dearpygui.dearpygui as dpg

def showContourExtraction(callbacks):
    with dpg.group(horizontal=True):
        with dpg.child_window(width=300):
            dpg.add_text('OpenCV2 Find Contour')
            dpg.add_text('Approximation Mode')
            dpg.add_listbox(tag='approximationModeListbox', items=['None', 'Simple', 'TC89_L1', 'TC89_KCOS'])
            dpg.add_text('')
            dpg.add_text('Contour Thickness')
            dpg.add_text('(Only for the drawing)')
            dpg.add_slider_int(tag='contourThicknessSlider', default_value=3, min_value=1, max_value=100)
            dpg.add_button(tag='extractContourButton', label='Apply Method', callback=lambda sender, app_data: callbacks.contourExtraction.extractContour(sender, app_data))
            with dpg.window(label="ERROR! The image must be in a binary color scheme!", modal=True, show=False, tag="nonBinary", no_title_bar=False):
                dpg.add_text("ERROR: You must select a binarization filter on the Thresholding Tab.")
                dpg.add_button(label="OK", width=75, callback=lambda: dpg.configure_item("nonBinary", show=False))
            
            dpg.add_separator()
            
            dpg.add_text('Contour Ordering')
            dpg.add_button(tag='contour_ordering', enabled=False, label='Anticlockwise', callback=callbacks.meshGeneration.toggleOrdering)
            with dpg.tooltip("contour_ordering"):
                dpg.add_text("Click to change contour ordering for export.")
            dpg.add_text('Export on Mesh')
            dpg.add_button(tag='contourExportOption', enabled=False, label='Disable', callback=callbacks.contourExtraction.toggleExportOnMesh)
            with dpg.tooltip("contourExportOption"):
                dpg.add_text("Click to enable option export on mesh.", tag="contourExportOptionTooltip")
                dpg.add_text("Saved contours are aproximated to the mesh of tab Mesh Generation when enabled")
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
                dpg.add_button(tag='updtadeContourButton', label='Apply Changes', callback=callbacks.contourExtraction.updateContour)
            dpg.add_separator()
            dpg.add_separator()

            with dpg.window(label="Save File", modal=False, show=False, tag="exportContourWindow", no_title_bar=False, min_size=[600,280]):
                dpg.add_text("Name your file")
                dpg.add_input_text(tag='inputContourNameText')
                dpg.add_separator()
                dpg.add_text("You MUST enter a File Name to select a directory")
                dpg.add_button(label='Select the directory', callback= callbacks.contourExtraction.openDirectorySelector)
                dpg.add_file_dialog(directory_selector=True, min_size=[400,300], show=False, tag='directorySelectorFileDialog', id="directorySelectorFileDialog", callback=callbacks.contourExtraction.selectFolder)
                dpg.add_separator()
                dpg.add_text('Contour ID: ', tag='contourIdExportText')
                dpg.add_text('File Name: ', tag='exportFileName')
                dpg.add_text('Complete Path Name: ', tag='exportPathName')
                with dpg.group(horizontal=True):
                    dpg.add_button(label='Save', callback=lambda: callbacks.contourExtraction.exportIndividualContourToFile())
                    dpg.add_button(label='Cancel', callback=lambda: dpg.configure_item('exportContourWindow', show=False))
                dpg.add_text("Missing file name or directory.", tag="exportContourError", show=False)

            with dpg.window(label="Save Files", modal=False, show=False, tag="exportSelectedContourWindow", no_title_bar=False, min_size=[600,255]):
                dpg.add_text("Name the prefix of your file")
                dpg.add_input_text(tag='inputSelectedContourNameText')
                dpg.add_separator()
                dpg.add_text("You MUST enter a prefix to the File Name to select a directory")
                dpg.add_button(label='Select the directory', callback= callbacks.contourExtraction.openExportSelectedDirectorySelector)
                dpg.add_file_dialog(directory_selector=True, min_size=[400,300], show=False, tag='directoryFolderExportSelected', id="directoryFolderExportSelected", callback=callbacks.contourExtraction.selectExportAllFolder)
                dpg.add_separator()
                dpg.add_text('File Default Name: ', tag='exportSelectedFileName')
                dpg.add_text('Complete Path Name: ', tag='exportSelectedPathName')
                with dpg.group(horizontal=True):
                    dpg.add_button(label='Save', callback=callbacks.contourExtraction.exportSelectedContourToFile)
                    dpg.add_button(label='Cancel', callback=lambda: dpg.configure_item('exportSelectedContourWindow', show=False))
                dpg.add_text("Missing file name or directory.", tag="exportSelectedContourError", show=False)
                    
                pass
        with dpg.child_window(tag='ContourExtractionParent'):
            with dpg.plot(tag="ContourExtractionPlotParent", label="ContourExtraction", height=650, width=650):
                dpg.add_plot_legend()
                dpg.add_plot_axis(dpg.mvXAxis, label="Width", tag="ContourExtraction_x_axis")
                dpg.add_plot_axis(dpg.mvYAxis, label="Height", tag="ContourExtraction_y_axis")
                dpg.fit_axis_data("ContourExtraction_x_axis")
                dpg.fit_axis_data("ContourExtraction_y_axis")