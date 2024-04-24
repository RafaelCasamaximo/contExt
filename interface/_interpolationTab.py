import dearpygui.dearpygui as dpg

def showInterpolation(callbacks):
    with dpg.group(horizontal=True):
        with dpg.child_window(width=300):
            dpg.add_text('Interpolation')
            dpg.add_listbox(tag='interpolationListbox', items=['Nearest', 'Bilinear', 'Bicubic', 'Quadratic', 'Spline3'], width=-1)
            dpg.add_checkbox(label='Expand Dimensions', tag='resizeInterpolation')
            dpg.add_text('Node Spacing Increment')
            dpg.add_slider_int(tag='spacingInterpolationSlider', default_value=1, min_value=1, max_value=7, width=-1)
            dpg.add_text('Node Removal Increment')
            dpg.add_slider_int(tag='removalInterpolationSlider', default_value=0, min_value=0, max_value=7, width=-1)
            dpg.add_button(tag='interpolateButton', width=-1, label='Apply Method', callback=lambda sender, app_data: callbacks.interpolation.interpolate(sender, app_data))
            dpg.add_separator()
            dpg.add_button(tag='interpolationToMesh', width=-1, label='Export to Mesh Generation', callback=lambda sender, app_data: callbacks.interpolation.exportToMeshGeneration(sender, app_data))
            dpg.add_separator()
            dpg.add_button(tag='exportContour', width=-1, label='Export Contour to File', callback=lambda sender, app_data: callbacks.interpolation.exportButtonCall(sender, app_data))
            pass

        with dpg.window(label="Save File", modal=False, show=False, tag="exportInterpolatedContourWindow", no_title_bar=False, min_size=[600,280]):
            dpg.add_text("Name your file")
            dpg.add_input_text(tag='inputInterpolatedContourNameText')
            dpg.add_separator()
            dpg.add_text("You MUST enter a File Name to select a directory")
            dpg.add_button(label='Select the directory', width=-1, callback= callbacks.interpolation.openDirectorySelector)
            dpg.add_file_dialog(directory_selector=True, min_size=[400,300], show=False, tag='interpolatedContourDirectorySelectorFileDialog', id="interpolatedContourDirectorySelectorFileDialog", callback=callbacks.interpolation.selectFolder)
            dpg.add_separator()
            dpg.add_text('File Name: ', tag='exportInterpolatedFileName')
            dpg.add_text('Complete Path Name: ', tag='exportInterpolatedPathName')
            with dpg.group(horizontal=True):
                dpg.add_button(label='Save', width=-1, callback=lambda: callbacks.interpolation.exportIndividualContourToFile())
                dpg.add_button(label='Cancel', width=-1, callback=lambda: dpg.configure_item('exportInterpolatedContourWindow', show=False))
            dpg.add_text("Missing file name or directory.", tag="exportInterpolatedContourError", show=False)

        with dpg.child_window(tag='InterpolationParent'):
            with dpg.plot(tag="InterpolationPlotParent", label="Interpolation Plot", height=-1 - 20, width=-1, equal_aspects=True):
                dpg.add_plot_legend()
                dpg.add_plot_axis(dpg.mvXAxis, label="x", tag="Interpolation_x_axis")
                dpg.add_plot_axis(dpg.mvYAxis, label="y", tag="Interpolation_y_axis")
            with dpg.group(horizontal=True):
                dpg.add_text('Original Area: --', tag='area_before_interp')
                dpg.add_text('Current Area: --', tag='area_after_interp')
                dpg.add_text('Delta: --', tag='delta_interp')
            pass