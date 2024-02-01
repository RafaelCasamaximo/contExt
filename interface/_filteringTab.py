import dearpygui.dearpygui as dpg

def showFiltering(callbacks):
    with dpg.group(horizontal=True):
        with dpg.child_window(width=300):
            with dpg.group(horizontal=True):
                dpg.add_checkbox(tag='histogramCheckbox', callback=lambda sender, app_data: callbacks.imageProcessing.toggleAndExecuteQuery('histogramEqualization', sender, app_data))
                dpg.add_text('Histogram Equalization')
            dpg.add_separator()

            with dpg.group(horizontal=True):
                dpg.add_checkbox(tag='brightnessAndContrastCheckbox', callback=lambda sender, app_data: callbacks.imageProcessing.toggleAndExecuteQuery('brightnessAndContrast', sender, app_data))
                dpg.add_text('Brightness and Contrast')
            dpg.add_text('Brightness')
            dpg.add_slider_int(default_value=0, min_value=-100, max_value=100, width=-1, tag='brightnessSlider', callback=lambda: callbacks.imageProcessing.executeQuery('brightnessAndContrast'))
            dpg.add_text('Contrast')
            dpg.add_slider_float(default_value=1.0, min_value=0.0, max_value=3.0, width=-1, tag='contrastSlider', callback=lambda: callbacks.imageProcessing.executeQuery('brightnessAndContrast'))
            dpg.add_separator()
                
            with dpg.group(horizontal=True):
                dpg.add_checkbox(tag='averageBlurCheckbox', callback=lambda sender, app_data: callbacks.imageProcessing.toggleAndExecuteQuery('averageBlur', sender, app_data))
                dpg.add_text('Average Blur')
            dpg.add_text('Intensity')
            dpg.add_slider_int(tag='averageBlurSlider', default_value=1, min_value=1, max_value=100, width=-1, callback=lambda: callbacks.imageProcessing.executeQuery('averageBlur'))
            dpg.add_separator()

            with dpg.group(horizontal=True):
                dpg.add_checkbox(tag='gaussianBlurCheckbox', callback=lambda sender, app_data: callbacks.imageProcessing.toggleAndExecuteQuery('gaussianBlur', sender, app_data))
                dpg.add_text('Gaussian Blur')
            dpg.add_text('Intensity')
            dpg.add_slider_int(tag='gaussianBlurSlider', default_value=1, min_value=1, max_value=100, width=-1, callback=lambda: callbacks.imageProcessing.executeQuery('gaussianBlur'))
            dpg.add_separator()

            with dpg.group(horizontal=True):
                dpg.add_checkbox(tag='medianBlurCheckbox', callback=lambda sender, app_data: callbacks.imageProcessing.toggleAndExecuteQuery('medianBlur', sender, app_data))
                dpg.add_text('Median Blur')
            dpg.add_text('Intensity')
            dpg.add_slider_int(tag='medianBlurSlider', default_value=1, min_value=1, max_value=100, width=-1, callback=lambda: callbacks.imageProcessing.executeQuery('medianBlur'))
                
            with dpg.group(tag="exportImageAsFileFilteringGroup", show=False):
                dpg.add_separator()
                dpg.add_text("Save Image")
                dpg.add_button(tag='exportImageAsFileFiltering', width=-1, label='Export Image as File', callback=lambda sender, app_data: callbacks.imageProcessing.exportImage(sender, app_data, 'Filtering'))
                
            dpg.add_separator()
            dpg.add_separator()

            pass
        with dpg.child_window(tag='FilteringParent'):
            with dpg.plot(tag="FilteringPlotParent", label="Filtering", height=-1, width=-1, equal_aspects=True):
                dpg.add_plot_legend()
                dpg.add_plot_axis(dpg.mvXAxis, label="Width", tag="Filtering_x_axis")
                dpg.add_plot_axis(dpg.mvYAxis, label="Height", tag="Filtering_y_axis")
            pass