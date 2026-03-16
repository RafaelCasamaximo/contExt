import dearpygui.dearpygui as dpg
from . import strings

def showThresholding(callbacks):
    with dpg.group(horizontal=True):
        with dpg.child_window(width=300):

            dpg.add_text(strings.t("thresholding.grayscale_conversion"), tag="thresholdingGrayscaleText")
            dpg.add_checkbox(label=strings.t("thresholding.exclude_blue_channel"), tag='excludeBlueChannel', callback=lambda: callbacks.imageProcessing.executeQuery('grayscale'))
            dpg.add_checkbox(label=strings.t("thresholding.exclude_green_channel"), tag='excludeGreenChannel', callback=lambda: callbacks.imageProcessing.executeQuery('grayscale'))
            dpg.add_checkbox(label=strings.t("thresholding.exclude_red_channel"), tag='excludeRedChannel', callback=lambda: callbacks.imageProcessing.executeQuery('grayscale'))
            dpg.add_separator()

            with dpg.group(horizontal=True):
                dpg.add_checkbox(tag='laplacianCheckbox', callback=lambda sender, app_data: callbacks.imageProcessing.toggleAndExecuteQuery('laplacian', sender, app_data))
                dpg.add_text(strings.t("thresholding.laplacian"), tag="thresholdingLaplacianText")
            dpg.add_text(strings.t("filtering.intensity"), tag="thresholdingLaplacianIntensityText")
            dpg.add_slider_int(tag='laplacianSlider', default_value=1, min_value=1, max_value=8, width=-1, callback=lambda: callbacks.imageProcessing.executeQuery('laplacian'))
            dpg.add_separator()

            dpg.add_checkbox(tag='sobelCheckbox', label=strings.t("thresholding.sobel"), callback=lambda sender, app_data: callbacks.imageProcessing.toggleAndExecuteQuery('sobel', sender, app_data))
            dpg.add_listbox(tag='sobelListbox', items=strings.option_labels("sobel_axis"), width=-1, default_value=strings.option_label("sobel_axis", "x_axis"), callback=lambda: callbacks.imageProcessing.executeQuery('sobel'))
            dpg.add_separator()

            with dpg.group(horizontal=True):
                dpg.add_checkbox(tag='globalThresholdingCheckbox', callback=lambda sender, app_data: callbacks.imageProcessing.toggleAndExecuteQuery('globalThresholding', sender, app_data))
                dpg.add_text(strings.t("thresholding.global_thresholding"), tag="thresholdingGlobalText")
            with dpg.group(horizontal=True):
                dpg.add_checkbox(tag='invertGlobalThresholding', callback=lambda: callbacks.imageProcessing.executeQuery('globalThresholding'))
                dpg.add_text(strings.t("thresholding.invert_thresholding"), tag="thresholdingInvertText")
            dpg.add_text(strings.t("thresholding.threshold"), tag="thresholdingThresholdText")
            dpg.add_slider_int(tag='globalThresholdSlider', default_value=127, min_value=0, max_value=255, width=-1, callback=lambda: callbacks.imageProcessing.executeQuery('globalThresholding'))
            dpg.add_separator()

            with dpg.group(horizontal=True):
                dpg.add_checkbox(tag='adaptiveThresholdingCheckbox', callback=lambda sender, app_data: callbacks.imageProcessing.toggleAndExecuteQuery('adaptiveMeanThresholding', sender, app_data))
                dpg.add_text(strings.t("thresholding.adaptive_mean_thresholding"), tag="thresholdingAdaptiveMeanText")
            dpg.add_separator()

            with dpg.group(horizontal=True):
                dpg.add_checkbox(tag='adaptiveGaussianThresholdingCheckbox', callback=lambda sender, app_data: callbacks.imageProcessing.toggleAndExecuteQuery('adaptiveGaussianThresholding', sender, app_data))
                dpg.add_text(strings.t("thresholding.adaptive_gaussian_thresholding"), tag="thresholdingAdaptiveGaussianText")
            dpg.add_separator()

            with dpg.group(horizontal=True):
                dpg.add_checkbox(tag='otsuBinarization', callback=lambda sender, app_data: callbacks.imageProcessing.toggleAndExecuteQuery('otsuBinarization', sender, app_data))
                dpg.add_text(strings.t("thresholding.otsu_binarization"), tag="thresholdingOtsuText")
            dpg.add_text(strings.t("thresholding.gaussian_blur_hint"), tag="thresholdingHintText")

            with dpg.group(tag="exportImageAsFileThresholdingGroup", show=False):
                dpg.add_separator()
                dpg.add_text(strings.t("common.save_image"), tag="thresholdingSaveImageText")
                dpg.add_button(tag="exportImageAsFileThresholding", label=strings.t("common.export_image_as_file"), width=-1, callback=lambda sender, app_data: callbacks.imageProcessing.exportImage(sender, app_data, "Thresholding"))

            dpg.add_separator()
            dpg.add_separator()

            pass
        with dpg.child_window(tag='ThresholdingParent'):
            with dpg.plot(tag="ThresholdingPlotParent", label=strings.t("thresholding.plot"), height=-1, width=-1, equal_aspects=True):
                dpg.add_plot_legend()
                dpg.add_plot_axis(dpg.mvXAxis, label=strings.t("axes.width"), tag="Thresholding_x_axis")
                dpg.add_plot_axis(dpg.mvYAxis, label=strings.t("axes.height"), tag="Thresholding_y_axis")


def refreshThresholdingTranslations(old_locale=None):
    old_locale = old_locale or strings.get_locale()
    sobel_value = dpg.get_value("sobelListbox")
    dpg.set_value("thresholdingGrayscaleText", strings.t("thresholding.grayscale_conversion"))
    dpg.configure_item("excludeBlueChannel", label=strings.t("thresholding.exclude_blue_channel"))
    dpg.configure_item("excludeGreenChannel", label=strings.t("thresholding.exclude_green_channel"))
    dpg.configure_item("excludeRedChannel", label=strings.t("thresholding.exclude_red_channel"))
    dpg.set_value("thresholdingLaplacianText", strings.t("thresholding.laplacian"))
    dpg.set_value("thresholdingLaplacianIntensityText", strings.t("filtering.intensity"))
    dpg.configure_item("sobelCheckbox", label=strings.t("thresholding.sobel"))
    dpg.configure_item("sobelListbox", items=strings.option_labels("sobel_axis"))
    dpg.set_value("sobelListbox", strings.translate_option_value("sobel_axis", sobel_value, old_locale))
    dpg.set_value("thresholdingGlobalText", strings.t("thresholding.global_thresholding"))
    dpg.set_value("thresholdingInvertText", strings.t("thresholding.invert_thresholding"))
    dpg.set_value("thresholdingThresholdText", strings.t("thresholding.threshold"))
    dpg.set_value("thresholdingAdaptiveMeanText", strings.t("thresholding.adaptive_mean_thresholding"))
    dpg.set_value("thresholdingAdaptiveGaussianText", strings.t("thresholding.adaptive_gaussian_thresholding"))
    dpg.set_value("thresholdingOtsuText", strings.t("thresholding.otsu_binarization"))
    dpg.set_value("thresholdingHintText", strings.t("thresholding.gaussian_blur_hint"))
    dpg.set_value("thresholdingSaveImageText", strings.t("common.save_image"))
    dpg.configure_item("exportImageAsFileThresholding", label=strings.t("common.export_image_as_file"))
    dpg.configure_item("ThresholdingPlotParent", label=strings.t("thresholding.plot"))
    dpg.configure_item("Thresholding_x_axis", label=strings.t("axes.width"))
    dpg.configure_item("Thresholding_y_axis", label=strings.t("axes.height"))
