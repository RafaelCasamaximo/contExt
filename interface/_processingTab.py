import dearpygui.dearpygui as dpg

def showProcessing(callbacks):
    with dpg.group(horizontal=True):
        with dpg.child_window(width=300):
            

            with dpg.file_dialog(directory_selector=False, min_size=[400,300], show=False, tag='file_dialog_id', callback=callbacks.imageProcessing.openFile, cancel_callback=callbacks.imageProcessing.cancelImportImage):
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
            dpg.add_text('File Name:', tag='file_name_text')
            dpg.add_text('File Path:', tag='file_path_text')
            dpg.add_separator()
    
            dpg.add_text('Cropping')
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
            
            dpg.add_button(label='Reset', callback=lambda: callbacks.imageProcessing.resetCrop())
            dpg.add_button(label='Apply Changes', callback=lambda: callbacks.imageProcessing.executeQuery('crop'))

            with dpg.group(tag="exportImageAsFileProcessingGroup", show=False):
                dpg.add_separator()
                dpg.add_text("Save Image")
                dpg.add_button(tag='exportImageAsFileProcessing', label='Export Image as File', callback=lambda sender, app_data: callbacks.imageProcessing.exportImage(sender, app_data, 'Processing'))

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
            with dpg.plot(tag="ProcessingPlotParent", label="Processing", height=650, width=650):
                dpg.add_plot_legend()
                dpg.add_plot_axis(dpg.mvXAxis, label="Width", tag="Processing_x_axis")
                dpg.add_plot_axis(dpg.mvYAxis, label="Height", tag="Processing_y_axis")
                dpg.fit_axis_data("Processing_x_axis")
                dpg.fit_axis_data("Processing_y_axis")
            pass