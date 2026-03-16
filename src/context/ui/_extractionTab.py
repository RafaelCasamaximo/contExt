import dearpygui.dearpygui as dpg
from . import strings

def showContourExtraction(callbacks):
    with dpg.group(horizontal=True):
        with dpg.child_window(width=300):
            dpg.add_text(strings.t("contour_extraction.title"), tag="contourExtractionTitleText")
            dpg.add_text(strings.t("contour_extraction.approximation_mode"), tag="contourApproximationModeText")
            dpg.add_listbox(
                tag='approximationModeListbox',
                items=strings.option_labels("approximation_mode"),
                default_value=strings.option_label("approximation_mode", "none"),
                width=-1
            )
            dpg.add_text('', tag="contourSpacerText")
            dpg.add_text(strings.t("contour_extraction.contour_thickness"), tag="contourThicknessText")
            dpg.add_text(strings.t("contour_extraction.drawing_hint"), tag="contourDrawingHintText")
            dpg.add_slider_int(tag='contourThicknessSlider', default_value=3, min_value=1, max_value=100,  width=-1)
            dpg.add_button(tag='extractContourButton', width=-1, label=strings.t("common.apply_method"), callback=lambda sender, app_data: callbacks.contourExtraction.extractContour(sender, app_data))
            with dpg.window(label=strings.t("contour_extraction.non_binary_title"), modal=True, show=False, tag="nonBinary", no_title_bar=False):
                dpg.add_text(strings.t("contour_extraction.non_binary_message"), tag="contourNonBinaryText")
                dpg.add_button(tag="contourNonBinaryOk", label=strings.t("common.ok"), width=-1, callback=lambda: dpg.configure_item("nonBinary", show=False))
            
            dpg.add_separator()
            
            dpg.add_text(strings.t("contour_extraction.contour_ordering"), tag="contourOrderingText")
            dpg.add_button(tag='contour_ordering', width=-1, enabled=False, label=strings.t("common.counterclockwise"), callback=callbacks.meshGeneration.toggleOrdering)
            with dpg.tooltip("contour_ordering"):
                dpg.add_text(strings.t("contour_extraction.contour_ordering_tooltip"), tag="contourOrderingTooltipText")
            dpg.add_text(strings.t("contour_extraction.export_as_mesh"), tag="contourExportAsMeshText")
            dpg.add_button(tag='contourExportOption', width=-1, enabled=False, label=strings.t("common.disable"), callback=callbacks.contourExtraction.toggleExportOnMesh)
            with dpg.tooltip("contourExportOption"):
                dpg.add_text(strings.t("contour_extraction.export_mesh_tooltip_enable"), tag="contourExportOptionTooltip")
                dpg.add_text(strings.t("contour_extraction.export_mesh_tooltip_details"), tag="contourExportOptionTooltipDetails")
            dpg.add_separator()

            dpg.add_text(strings.t("contour_extraction.contour_properties"), tag="contourPropertiesText")
            dpg.add_text(strings.t("contour_extraction.max_width_mapping"), tag="contourMaxWidthText")
            dpg.add_text(strings.fmt("current", value="--"), tag="currentMaxWidth")
            dpg.add_input_double(tag='maxWidthMapping', width=-1)
            dpg.add_text(strings.t("contour_extraction.max_height_mapping"), tag="contourMaxHeightText")
            dpg.add_text(strings.fmt("current", value="--"), tag="currentMaxHeight")
            dpg.add_input_double(tag='maxHeightMapping', width=-1)
            dpg.add_text(strings.t("contour_extraction.width_offset"), tag="contourWidthOffsetText")
            dpg.add_text(strings.fmt("current", value="--"), tag="currentWidthOffset")
            dpg.add_input_double(tag='widthOffset', width=-1)
            dpg.add_text(strings.t("contour_extraction.height_offset"), tag="contourHeightOffsetText")
            dpg.add_text(strings.fmt("current", value="--"), tag="currentHeightOffset")
            dpg.add_input_double(tag='heightOffset', width=-1)
            dpg.add_checkbox(label=strings.t("contour_extraction.matlab_mode"), tag='matlabModeCheckbox')
            with dpg.group(tag="changeContourParent"):
                dpg.add_button(tag='updateContourButton', width=-1, label=strings.t("common.apply_changes"), callback=callbacks.contourExtraction.updateContour)
            dpg.add_separator()
            dpg.add_separator()

            with dpg.window(label=strings.t("common.save_file"), modal=False, show=False, tag="exportContourWindow", no_title_bar=False, min_size=[600,280]):
                dpg.add_text(strings.t("common.enter_file_name"), tag="contourExportFileNameLabel")
                dpg.add_input_text(tag='inputContourNameText')
                dpg.add_separator()
                dpg.add_text(strings.t("common.enter_file_name_before_directory"), tag="contourExportDirectoryHint")
                dpg.add_button(tag="contourSelectDirectory", label=strings.t("common.select_directory"), width=-1, callback= callbacks.contourExtraction.openDirectorySelector)
                dpg.add_file_dialog(directory_selector=True, min_size=[400,300], show=False, tag='directorySelectorFileDialog', id="directorySelectorFileDialog", callback=callbacks.contourExtraction.selectFolder)
                dpg.add_separator()
                dpg.add_text(strings.fmt("contour_id", value=""), tag='contourIdExportText')
                dpg.add_text(strings.fmt("file_name", value=""), tag='exportFileName')
                dpg.add_text(strings.fmt("full_path", value=""), tag='exportPathName')
                with dpg.group(horizontal=True):
                    dpg.add_button(tag="contourExportSave", label=strings.t("common.save"), width=-1, callback=lambda: callbacks.contourExtraction.exportIndividualContourToFile())
                    dpg.add_button(tag="contourExportCancel", label=strings.t("common.cancel"), width=-1, callback=lambda: dpg.configure_item('exportContourWindow', show=False))
                dpg.add_text(strings.t("common.missing_file_name_or_directory"), tag="exportContourError", show=False)

            with dpg.window(label=strings.t("common.save_files"), modal=False, show=False, tag="exportSelectedContourWindow", no_title_bar=False, min_size=[600,255]):
                dpg.add_text(strings.t("common.enter_file_prefix"), tag="contourExportSelectedPrefixLabel")
                dpg.add_input_text(tag='inputSelectedContourNameText')
                dpg.add_separator()
                dpg.add_text(strings.t("common.enter_file_prefix_before_directory"), tag="contourExportSelectedDirectoryHint")
                dpg.add_button(tag="contourSelectDirectorySelected", label=strings.t("common.select_directory"), width=-1, callback= callbacks.contourExtraction.openExportSelectedDirectorySelector)
                dpg.add_file_dialog(directory_selector=True, min_size=[400,300], show=False, tag='directoryFolderExportSelected', id="directoryFolderExportSelected", callback=callbacks.contourExtraction.selectExportAllFolder)
                dpg.add_separator()
                dpg.add_text(strings.fmt("default_file_name", value=""), tag='exportSelectedFileName')
                dpg.add_text(strings.fmt("full_path", value=""), tag='exportSelectedPathName')
                with dpg.group(horizontal=True):
                    dpg.add_button(tag="contourExportSelectedSave", label=strings.t("common.save"), width=-1, callback=callbacks.contourExtraction.exportSelectedContourToFile)
                    dpg.add_button(tag="contourExportSelectedCancel", label=strings.t("common.cancel"), width=-1, callback=lambda: dpg.configure_item('exportSelectedContourWindow', show=False))
                dpg.add_text(strings.t("common.missing_file_name_or_directory"), tag="exportSelectedContourError", show=False)
                    
                pass
        with dpg.child_window(tag='ContourExtractionParent'):
            with dpg.plot(tag="ContourExtractionPlotParent", label=strings.t("contour_extraction.plot"), height=-1 - 50, width=-1, equal_aspects=True):
                dpg.add_plot_legend()
                dpg.add_plot_axis(dpg.mvXAxis, label=strings.t("axes.width"), tag="ContourExtraction_x_axis")
                dpg.add_plot_axis(dpg.mvYAxis, label=strings.t("axes.height"), tag="ContourExtraction_y_axis")
                

def refreshContourExtractionTranslations(old_locale=None):
    old_locale = old_locale or strings.get_locale()
    approximation_value = dpg.get_value("approximationModeListbox")
    dpg.set_value("contourExtractionTitleText", strings.t("contour_extraction.title"))
    dpg.set_value("contourApproximationModeText", strings.t("contour_extraction.approximation_mode"))
    dpg.configure_item("approximationModeListbox", items=strings.option_labels("approximation_mode"))
    dpg.set_value("approximationModeListbox", strings.translate_option_value("approximation_mode", approximation_value, old_locale))
    dpg.set_value("contourThicknessText", strings.t("contour_extraction.contour_thickness"))
    dpg.set_value("contourDrawingHintText", strings.t("contour_extraction.drawing_hint"))
    dpg.configure_item("extractContourButton", label=strings.t("common.apply_method"))
    dpg.configure_item("nonBinary", label=strings.t("contour_extraction.non_binary_title"))
    dpg.set_value("contourNonBinaryText", strings.t("contour_extraction.non_binary_message"))
    dpg.configure_item("contourNonBinaryOk", label=strings.t("common.ok"))
    dpg.set_value("contourOrderingText", strings.t("contour_extraction.contour_ordering"))
    dpg.set_value("contourOrderingTooltipText", strings.t("contour_extraction.contour_ordering_tooltip"))
    dpg.set_value("contourExportAsMeshText", strings.t("contour_extraction.export_as_mesh"))
    dpg.set_value("contourExportOptionTooltipDetails", strings.t("contour_extraction.export_mesh_tooltip_details"))
    dpg.set_value("contourPropertiesText", strings.t("contour_extraction.contour_properties"))
    dpg.set_value("contourMaxWidthText", strings.t("contour_extraction.max_width_mapping"))
    dpg.set_value("contourMaxHeightText", strings.t("contour_extraction.max_height_mapping"))
    dpg.set_value("contourWidthOffsetText", strings.t("contour_extraction.width_offset"))
    dpg.set_value("contourHeightOffsetText", strings.t("contour_extraction.height_offset"))
    dpg.configure_item("matlabModeCheckbox", label=strings.t("contour_extraction.matlab_mode"))
    dpg.configure_item("updateContourButton", label=strings.t("common.apply_changes"))
    dpg.configure_item("exportContourWindow", label=strings.t("common.save_file"))
    dpg.set_value("contourExportFileNameLabel", strings.t("common.enter_file_name"))
    dpg.set_value("contourExportDirectoryHint", strings.t("common.enter_file_name_before_directory"))
    dpg.configure_item("contourSelectDirectory", label=strings.t("common.select_directory"))
    dpg.configure_item("contourExportSave", label=strings.t("common.save"))
    dpg.configure_item("contourExportCancel", label=strings.t("common.cancel"))
    dpg.set_value("exportContourError", strings.t("common.missing_file_name_or_directory"))
    dpg.configure_item("exportSelectedContourWindow", label=strings.t("common.save_files"))
    dpg.set_value("contourExportSelectedPrefixLabel", strings.t("common.enter_file_prefix"))
    dpg.set_value("contourExportSelectedDirectoryHint", strings.t("common.enter_file_prefix_before_directory"))
    dpg.configure_item("contourSelectDirectorySelected", label=strings.t("common.select_directory"))
    dpg.configure_item("contourExportSelectedSave", label=strings.t("common.save"))
    dpg.configure_item("contourExportSelectedCancel", label=strings.t("common.cancel"))
    dpg.set_value("exportSelectedContourError", strings.t("common.missing_file_name_or_directory"))
    dpg.configure_item("ContourExtractionPlotParent", label=strings.t("contour_extraction.plot"))
    dpg.configure_item("ContourExtraction_x_axis", label=strings.t("axes.width"))
    dpg.configure_item("ContourExtraction_y_axis", label=strings.t("axes.height"))
