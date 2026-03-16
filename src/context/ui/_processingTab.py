import dearpygui.dearpygui as dpg
from . import strings

def showProcessing(callbacks):
    with dpg.group(horizontal=True):
        with dpg.child_window(width=300):
            
            with dpg.file_dialog(directory_selector=False, min_size=[400,300], show=False, tag='file_dialog_id', callback=callbacks.imageProcessing.openFile, cancel_callback=callbacks.imageProcessing.cancelImportImage):
                dpg.add_file_extension("", color=(150, 255, 150, 255))
                dpg.add_file_extension(".jpg", color=(0, 255, 255, 255))
                dpg.add_file_extension(".png", color=(0, 255, 255, 255))
                dpg.add_file_extension(".dcm", color=(0, 255, 255, 255))
                dpg.add_file_extension(".dicom", color=(0, 255, 255, 255))
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

            dpg.add_text(strings.t("processing.select_image"), tag="processingSelectImageText")
            dpg.add_button(tag="import_image", width=-1, label=strings.t("processing.import_image"), callback=lambda: dpg.show_item("file_dialog_id"))
            dpg.add_text(strings.fmt("file_name", value=""), tag="file_name_text")
            dpg.add_text(strings.fmt("file_path", value=""), tag="file_path_text")
            dpg.add_separator()
    
            dpg.add_text(strings.t("processing.cropping"), tag="processingCroppingText")
            dpg.add_text(strings.t("processing.original_resolution"), tag="processingOriginalResolutionText")
            dpg.add_text(strings.fmt("width_px", value=""), tag='originalWidth')
            dpg.add_text(strings.fmt("height_px", value=""), tag='originalHeight')
            dpg.add_text(strings.t("processing.current_resolution"), tag="processingCurrentResolutionText")
            dpg.add_text(strings.fmt("width_px", value=""), tag='currentWidth')
            dpg.add_text(strings.fmt("height_px", value=""), tag='currentHeight')
            dpg.add_text(strings.t("processing.new_resolution"), tag="processingNewResolutionText")
            dpg.add_separator();
            dpg.add_text(strings.t("processing.start_width"), tag="processingStartWidthText")
            dpg.add_input_int(tag='startY', width=-1)
            dpg.add_separator();
            dpg.add_text(strings.t("processing.start_height"), tag="processingStartHeightText")
            dpg.add_input_int(tag='startX', width=-1)
            dpg.add_separator();
            dpg.add_text(strings.t("processing.end_width"), tag="processingEndWidthText")
            dpg.add_input_int(tag='endY', width=-1)
            dpg.add_separator();
            dpg.add_text(strings.t("processing.end_height"), tag="processingEndHeightText")
            dpg.add_input_int(tag='endX', width=-1)
            dpg.add_separator();
            dpg.add_button(tag="processingResetButton", label=strings.t("common.reset"), width=-1, callback=lambda: callbacks.imageProcessing.resetCrop())
            dpg.add_button(tag="processingApplyChangesButton", label=strings.t("common.apply_changes"), width=-1, callback=lambda: callbacks.imageProcessing.executeQuery('crop'))

            with dpg.group(tag="exportImageAsFileProcessingGroup", show=False):
                dpg.add_separator()
                dpg.add_text(strings.t("common.save_image"), tag="processingSaveImageText")
                dpg.add_button(tag="exportImageAsFileProcessing", width=-1, label=strings.t("common.export_image_as_file"), callback=lambda sender, app_data: callbacks.imageProcessing.exportImage(sender, app_data, "Processing"))

            with dpg.window(label=strings.t("processing.invalid_crop_title"), modal=True, show=False, tag="incorrectCrop", no_title_bar=False):
                dpg.add_text(strings.t("processing.invalid_crop_message"), tag="processingInvalidCropText")
                dpg.add_button(tag="processingInvalidCropOk", label=strings.t("common.ok"), width=-1, callback=lambda: dpg.configure_item("incorrectCrop", show=False))

            with dpg.window(label=strings.t("processing.no_image_title"), modal=True, show=False, tag="noImage", no_title_bar=False):
                dpg.add_text(strings.t("processing.no_image_message"), tag="processingNoImageText")
                dpg.add_button(tag="processingNoImageOk", label=strings.t("common.ok"), width=-1, callback=lambda: dpg.configure_item("noImage", show=False))
            dpg.add_separator()

            with dpg.window(label=strings.t("processing.invalid_path_title"), modal=True, show=False, tag="noPath", no_title_bar=False):
                dpg.add_text(strings.t("processing.invalid_path_message"), tag="processingInvalidPathText")
                dpg.add_button(tag="processingInvalidPathOk", label=strings.t("common.ok"), width=-1, callback=lambda: dpg.configure_item("noPath", show=False))
            dpg.add_separator()

            pass

        with dpg.child_window(tag='ProcessingParent'):
            with dpg.plot(tag="ProcessingPlotParent", label=strings.t("processing.plot"), height=-1, width=-1, equal_aspects=True):
                dpg.add_plot_legend()
                dpg.add_plot_axis(dpg.mvXAxis, label=strings.t("axes.width"), tag="Processing_x_axis")
                dpg.add_plot_axis(dpg.mvYAxis, label=strings.t("axes.height"), tag="Processing_y_axis")
            pass

def wrapperCropInterpolation(sender=None, app_data=None, user_data=None):
    user_data.imageProcessing.resetContours()
    user_data.imageProcessing.executeQuery('crop')


def refreshProcessingTranslations():
    dpg.set_value("processingSelectImageText", strings.t("processing.select_image"))
    dpg.configure_item("import_image", label=strings.t("processing.import_image"))
    dpg.set_value("processingCroppingText", strings.t("processing.cropping"))
    dpg.set_value("processingOriginalResolutionText", strings.t("processing.original_resolution"))
    dpg.set_value("processingCurrentResolutionText", strings.t("processing.current_resolution"))
    dpg.set_value("processingNewResolutionText", strings.t("processing.new_resolution"))
    dpg.set_value("processingStartWidthText", strings.t("processing.start_width"))
    dpg.set_value("processingStartHeightText", strings.t("processing.start_height"))
    dpg.set_value("processingEndWidthText", strings.t("processing.end_width"))
    dpg.set_value("processingEndHeightText", strings.t("processing.end_height"))
    dpg.configure_item("processingResetButton", label=strings.t("common.reset"))
    dpg.configure_item("processingApplyChangesButton", label=strings.t("common.apply_changes"))
    dpg.set_value("processingSaveImageText", strings.t("common.save_image"))
    dpg.configure_item("exportImageAsFileProcessing", label=strings.t("common.export_image_as_file"))
    dpg.configure_item("incorrectCrop", label=strings.t("processing.invalid_crop_title"))
    dpg.set_value("processingInvalidCropText", strings.t("processing.invalid_crop_message"))
    dpg.configure_item("processingInvalidCropOk", label=strings.t("common.ok"))
    dpg.configure_item("noImage", label=strings.t("processing.no_image_title"))
    dpg.set_value("processingNoImageText", strings.t("processing.no_image_message"))
    dpg.configure_item("processingNoImageOk", label=strings.t("common.ok"))
    dpg.configure_item("noPath", label=strings.t("processing.invalid_path_title"))
    dpg.set_value("processingInvalidPathText", strings.t("processing.invalid_path_message"))
    dpg.configure_item("processingInvalidPathOk", label=strings.t("common.ok"))
    dpg.configure_item("ProcessingPlotParent", label=strings.t("processing.plot"))
    dpg.configure_item("Processing_x_axis", label=strings.t("axes.width"))
    dpg.configure_item("Processing_y_axis", label=strings.t("axes.height"))
