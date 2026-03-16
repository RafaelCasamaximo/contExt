import dearpygui.dearpygui as dpg
from . import strings

def showInterpolation(callbacks):
    with dpg.group(horizontal=True):
        with dpg.child_window(width=300):
            dpg.add_text(strings.t("interpolation.title"), tag="interpolationTitleText")
            dpg.add_listbox(
                tag='interpolationListbox',
                items=strings.option_labels("interpolation_mode"),
                default_value=strings.option_label("interpolation_mode", "nearest"),
                width=-1
            )
            dpg.add_checkbox(label=strings.t("interpolation.expand_dimensions"), tag='resizeInterpolation')
            dpg.add_text(strings.t("interpolation.node_spacing_increment"), tag="interpolationSpacingText")
            dpg.add_slider_int(tag='spacingInterpolationSlider', default_value=0, min_value=0, max_value=7, width=-1)
            dpg.add_text(strings.t("interpolation.node_removal_increment"), tag="interpolationRemovalText")
            dpg.add_slider_int(tag='removalInterpolationSlider', default_value=0, min_value=0, max_value=7, width=-1)
            dpg.add_checkbox(label=strings.t("interpolation.contour_approximation"), tag='approxPolyInterpolation')
            dpg.add_slider_float(tag='approxPolySlider', default_value=0.001, min_value=0.001, max_value=0.01, width=-1)
            dpg.add_button(tag='interpolateButton', width=-1, label=strings.t("common.apply_method"), callback=lambda sender, app_data: callbacks.interpolation.interpolate(sender, app_data))
            dpg.add_separator()
            dpg.add_button(tag='interpolationToMesh', width=-1, label=strings.t("interpolation.export_to_mesh_generation"), callback=lambda sender, app_data: callbacks.interpolation.exportToMeshGeneration(sender, app_data))
            dpg.add_separator()
            dpg.add_button(tag='exportContour', width=-1, label=strings.t("interpolation.export_contour_to_file"), callback=lambda sender, app_data: callbacks.interpolation.exportButtonCall(sender, app_data))
            pass

        with dpg.window(label=strings.t("common.save_file"), modal=False, show=False, tag="exportInterpolatedContourWindow", no_title_bar=False, min_size=[600,280]):
            dpg.add_text(strings.t("common.enter_file_name"), tag="interpolationExportFileNameLabel")
            dpg.add_input_text(tag='inputInterpolatedContourNameText')
            dpg.add_separator()
            dpg.add_text(strings.t("common.enter_file_name_before_directory"), tag="interpolationExportDirectoryHint")
            dpg.add_button(tag="interpolationSelectDirectory", label=strings.t("common.select_directory"), width=-1, callback= callbacks.interpolation.openDirectorySelector)
            dpg.add_file_dialog(directory_selector=True, min_size=[400,300], show=False, tag='interpolatedContourDirectorySelectorFileDialog', id="interpolatedContourDirectorySelectorFileDialog", callback=callbacks.interpolation.selectFolder)
            dpg.add_separator()
            dpg.add_text(strings.fmt("file_name", value=""), tag='exportInterpolatedFileName')
            dpg.add_text(strings.fmt("full_path", value=""), tag='exportInterpolatedPathName')
            with dpg.group(horizontal=True):
                dpg.add_button(tag="interpolationExportSave", label=strings.t("common.save"), width=-1, callback=lambda: callbacks.interpolation.exportIndividualContourToFile())
                dpg.add_button(tag="interpolationExportCancel", label=strings.t("common.cancel"), width=-1, callback=lambda: dpg.configure_item('exportInterpolatedContourWindow', show=False))
            dpg.add_text(strings.t("common.missing_file_name_or_directory"), tag="exportInterpolatedContourError", show=False)

        with dpg.child_window(tag='InterpolationParent'):
            with dpg.plot(tag="InterpolationPlotParent", label=strings.t("interpolation.plot"), height=-1 - 20, width=-1, equal_aspects=True):
                dpg.add_plot_legend()
                dpg.add_plot_axis(dpg.mvXAxis, label=strings.t("axes.x"), tag="Interpolation_x_axis")
                dpg.add_plot_axis(dpg.mvYAxis, label=strings.t("axes.y"), tag="Interpolation_y_axis")
            with dpg.group(horizontal=True):
                dpg.add_text(strings.fmt("original_area", value="--"), tag='area_before_interp')
                dpg.add_text(strings.fmt("interpolation_area", value="--"), tag='area_after_interp')
                dpg.add_text(strings.fmt("delta", value="--"), tag='delta_interp')
            pass


def refreshInterpolationTranslations(old_locale=None):
    old_locale = old_locale or strings.get_locale()
    interpolation_value = dpg.get_value("interpolationListbox")
    dpg.set_value("interpolationTitleText", strings.t("interpolation.title"))
    dpg.configure_item("interpolationListbox", items=strings.option_labels("interpolation_mode"))
    dpg.set_value("interpolationListbox", strings.translate_option_value("interpolation_mode", interpolation_value, old_locale))
    dpg.configure_item("resizeInterpolation", label=strings.t("interpolation.expand_dimensions"))
    dpg.set_value("interpolationSpacingText", strings.t("interpolation.node_spacing_increment"))
    dpg.set_value("interpolationRemovalText", strings.t("interpolation.node_removal_increment"))
    dpg.configure_item("approxPolyInterpolation", label=strings.t("interpolation.contour_approximation"))
    dpg.configure_item("interpolateButton", label=strings.t("common.apply_method"))
    dpg.configure_item("interpolationToMesh", label=strings.t("interpolation.export_to_mesh_generation"))
    dpg.configure_item("exportContour", label=strings.t("interpolation.export_contour_to_file"))
    dpg.configure_item("exportInterpolatedContourWindow", label=strings.t("common.save_file"))
    dpg.set_value("interpolationExportFileNameLabel", strings.t("common.enter_file_name"))
    dpg.set_value("interpolationExportDirectoryHint", strings.t("common.enter_file_name_before_directory"))
    dpg.configure_item("interpolationSelectDirectory", label=strings.t("common.select_directory"))
    dpg.configure_item("interpolationExportSave", label=strings.t("common.save"))
    dpg.configure_item("interpolationExportCancel", label=strings.t("common.cancel"))
    dpg.set_value("exportInterpolatedContourError", strings.t("common.missing_file_name_or_directory"))
    dpg.configure_item("InterpolationPlotParent", label=strings.t("interpolation.plot"))
    dpg.configure_item("Interpolation_x_axis", label=strings.t("axes.x"))
    dpg.configure_item("Interpolation_y_axis", label=strings.t("axes.y"))
