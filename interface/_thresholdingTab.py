import dearpygui.dearpygui as dpg

def showThresholding(callbacks):
    with dpg.group(horizontal=True):
        with dpg.child_window(width=300):

            dpg.add_text('Grayscale Conversion')
            dpg.add_checkbox(label='Exclude Blue Channel', tag='excludeBlueChannel', callback=lambda: callbacks.imageProcessing.executeQuery('grayscale'))
            dpg.add_checkbox(label='Exclude Green Channel', tag='excludeGreenChannel', callback=lambda: callbacks.imageProcessing.executeQuery('grayscale'))
            dpg.add_checkbox(label='Exclude Red Channel', tag='excludeRedChannel', callback=lambda: callbacks.imageProcessing.executeQuery('grayscale'))
            dpg.add_separator()

            with dpg.group(horizontal=True):
                dpg.add_checkbox(tag='laplacianCheckbox', callback=lambda sender, app_data: callbacks.imageProcessing.toggleAndExecuteQuery('laplacian', sender, app_data))
                dpg.add_text('Laplacian')
            dpg.add_text('Intensity')
            dpg.add_slider_int(tag='laplacianSlider', default_value=1, min_value=1, max_value=8, width=-1, callback=lambda: callbacks.imageProcessing.executeQuery('laplacian'))
            dpg.add_separator()

            dpg.add_checkbox(tag='sobelCheckbox', label='Sobel', callback=lambda sender, app_data: callbacks.imageProcessing.toggleAndExecuteQuery('sobel', sender, app_data))
            dpg.add_listbox(tag='sobelListbox', items=['X-Axis', 'Y-Axis', 'XY-Axis'], width=-1, callback=lambda: callbacks.imageProcessing.executeQuery('sobel'))
            dpg.add_separator()

            with dpg.group(horizontal=True):
                dpg.add_checkbox(tag='globalThresholdingCheckbox', callback=lambda sender, app_data: callbacks.imageProcessing.toggleAndExecuteQuery('globalThresholding', sender, app_data))
                dpg.add_text('Global Thresholding')
            with dpg.group(horizontal=True):
                dpg.add_checkbox(tag='invertGlobalThresholding', callback=lambda: callbacks.imageProcessing.executeQuery('globalThresholding'))
                dpg.add_text('Invert Tresholding')
            dpg.add_text('Threshold')
            dpg.add_slider_int(tag='globalThresholdSlider', default_value=127, min_value=0, max_value=255, width=-1, callback=lambda: callbacks.imageProcessing.executeQuery('globalThresholding'))
            dpg.add_separator()

            with dpg.group(horizontal=True):
                dpg.add_checkbox(tag='adaptativeThresholdingCheckbox', callback=lambda sender, app_data: callbacks.imageProcessing.toggleAndExecuteQuery('adaptativeMeanThresholding', sender, app_data))
                dpg.add_text('Adaptative Mean Thresholding')
            dpg.add_separator()

            with dpg.group(horizontal=True):
                dpg.add_checkbox(tag='adaptativeGaussianThresholdingCheckbox', callback=lambda sender, app_data: callbacks.imageProcessing.toggleAndExecuteQuery('adaptativeGaussianThresholding', sender, app_data))
                dpg.add_text('Adaptative Gaussian Thresholding')
            dpg.add_separator()

            with dpg.group(horizontal=True):
                dpg.add_checkbox(tag='otsuBinarization', callback=lambda sender, app_data: callbacks.imageProcessing.toggleAndExecuteQuery('otsuBinarization', sender, app_data))
                dpg.add_text('Otsu\'s Binarization')
            dpg.add_text('(Works better after Gaussian Blur)')

            with dpg.group(tag="exportImageAsFileThresholdingGroup", show=False):
                dpg.add_separator()
                dpg.add_text("Save Image")
                dpg.add_button(tag='exportImageAsFileThresholding', label='Export Image as File', width=-1, callback=lambda sender, app_data: callbacks.imageProcessing.exportImage(sender, app_data, 'Thresholding'))

            dpg.add_separator()
            dpg.add_separator()

            pass
        with dpg.child_window(tag='ThresholdingParent'):
            with dpg.plot(tag="ThresholdingPlotParent", label="Thresholding", height=-1, width=-1, equal_aspects=True):
                dpg.add_plot_legend()
                dpg.add_plot_axis(dpg.mvXAxis, label="Width", tag="Thresholding_x_axis")
                dpg.add_plot_axis(dpg.mvYAxis, label="Height", tag="Thresholding_y_axis")