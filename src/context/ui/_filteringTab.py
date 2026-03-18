import dearpygui.dearpygui as dpg
from . import strings

def showFiltering(callbacks):
    with dpg.group(horizontal=True):
        with dpg.child_window(width=300):
            with dpg.group(horizontal=True):
                dpg.add_checkbox(tag='histogramCheckbox', callback=lambda sender, app_data: callbacks.imageProcessing.toggleAndExecuteQuery('histogramEqualization', sender, app_data))
                dpg.add_text(strings.t("filtering.histogram_equalization"), tag="filteringHistogramText")
            dpg.add_separator()

            with dpg.group(horizontal=True):
                dpg.add_checkbox(tag='claheCheckbox', callback=lambda sender, app_data: callbacks.imageProcessing.toggleAndExecuteQuery('claheEqualization', sender, app_data))
                dpg.add_text(strings.t("filtering.clahe_equalization"), tag="filteringClaheText")
            dpg.add_text(strings.t("filtering.clahe_clip_limit"), tag="filteringClaheClipLimitText")
            dpg.add_slider_float(default_value=2.0, min_value=0.1, max_value=10.0, width=-1, tag='claheClipLimitSlider', callback=lambda: callbacks.imageProcessing.executeQuery('claheEqualization'))
            dpg.add_text(strings.t("filtering.clahe_tile_grid_size"), tag="filteringClaheTileGridSizeText")
            dpg.add_slider_int(default_value=8, min_value=1, max_value=32, width=-1, tag='claheTileGridSizeSlider', callback=lambda: callbacks.imageProcessing.executeQuery('claheEqualization'))
            dpg.add_separator()

            with dpg.group(horizontal=True):
                dpg.add_checkbox(tag='brightnessAndContrastCheckbox', callback=lambda sender, app_data: callbacks.imageProcessing.toggleAndExecuteQuery('brightnessAndContrast', sender, app_data))
                dpg.add_text(strings.t("filtering.brightness_and_contrast"), tag="filteringBrightnessContrastText")
            dpg.add_text(strings.t("filtering.brightness"), tag="filteringBrightnessText")
            dpg.add_slider_int(default_value=0, min_value=-100, max_value=100, width=-1, tag='brightnessSlider', callback=lambda: callbacks.imageProcessing.executeQuery('brightnessAndContrast'))
            dpg.add_text(strings.t("filtering.contrast"), tag="filteringContrastText")
            dpg.add_slider_float(default_value=1.0, min_value=0.0, max_value=3.0, width=-1, tag='contrastSlider', callback=lambda: callbacks.imageProcessing.executeQuery('brightnessAndContrast'))
            dpg.add_separator()
                
            with dpg.group(horizontal=True):
                dpg.add_checkbox(tag='averageBlurCheckbox', callback=lambda sender, app_data: callbacks.imageProcessing.toggleAndExecuteQuery('averageBlur', sender, app_data))
                dpg.add_text(strings.t("filtering.average_blur"), tag="filteringAverageBlurText")
            dpg.add_text(strings.t("filtering.intensity"), tag="filteringAverageIntensityText")
            dpg.add_slider_int(tag='averageBlurSlider', default_value=1, min_value=1, max_value=100, width=-1, callback=lambda: callbacks.imageProcessing.executeQuery('averageBlur'))
            dpg.add_separator()

            with dpg.group(horizontal=True):
                dpg.add_checkbox(tag='gaussianBlurCheckbox', callback=lambda sender, app_data: callbacks.imageProcessing.toggleAndExecuteQuery('gaussianBlur', sender, app_data))
                dpg.add_text(strings.t("filtering.gaussian_blur"), tag="filteringGaussianBlurText")
            dpg.add_text(strings.t("filtering.intensity"), tag="filteringGaussianIntensityText")
            dpg.add_slider_int(tag='gaussianBlurSlider', default_value=1, min_value=1, max_value=100, width=-1, callback=lambda: callbacks.imageProcessing.executeQuery('gaussianBlur'))
            dpg.add_separator()

            with dpg.group(horizontal=True):
                dpg.add_checkbox(tag='medianBlurCheckbox', callback=lambda sender, app_data: callbacks.imageProcessing.toggleAndExecuteQuery('medianBlur', sender, app_data))
                dpg.add_text(strings.t("filtering.median_blur"), tag="filteringMedianBlurText")
            dpg.add_text(strings.t("filtering.intensity"), tag="filteringMedianIntensityText")
            dpg.add_slider_int(tag='medianBlurSlider', default_value=1, min_value=1, max_value=100, width=-1, callback=lambda: callbacks.imageProcessing.executeQuery('medianBlur'))
            dpg.add_checkbox(
                tag="showFilteringHistogramToggle",
                label=strings.t("histogram.show_toggle"),
                default_value=False,
                callback=lambda sender, app_data: callbacks.imageProcessing.toggleHistogramPanel("Filtering", app_data),
            )
                
            with dpg.group(tag="exportImageAsFileFilteringGroup", show=False):
                dpg.add_separator()
                dpg.add_text(strings.t("common.save_image"), tag="filteringSaveImageText")
                dpg.add_button(tag="exportImageAsFileFiltering", width=-1, label=strings.t("common.export_image_as_file"), callback=lambda sender, app_data: callbacks.imageProcessing.exportImage(sender, app_data, "Filtering"))

            with dpg.group(tag="exportHistogramAsFileFilteringGroup", show=False):
                dpg.add_separator()
                dpg.add_text(strings.t("common.save_histogram"), tag="filteringSaveHistogramText")
                dpg.add_button(tag="exportHistogramAsFileFiltering", width=-1, label=strings.t("common.export_histogram_as_file"), callback=lambda sender, app_data: callbacks.imageProcessing.exportHistogram(sender, app_data, "Filtering"))
                
            dpg.add_separator()
            dpg.add_separator()

            pass
        with dpg.child_window(tag='FilteringParent'):
            with dpg.group():
                with dpg.child_window(tag="FilteringImagePanel", height=-1):
                    with dpg.plot(tag="FilteringPlotParent", label=strings.t("filtering.plot"), height=-1, width=-1, equal_aspects=True):
                        dpg.add_plot_legend()
                        dpg.add_plot_axis(dpg.mvXAxis, label=strings.t("axes.width"), tag="Filtering_x_axis")
                        dpg.add_plot_axis(dpg.mvYAxis, label=strings.t("axes.height"), tag="Filtering_y_axis")
                with dpg.child_window(tag="FilteringHistogramPanel", height=240, show=False):
                    with dpg.plot(tag="FilteringHistogramPlotParent", label=strings.t("histogram.title"), height=-1, width=-1):
                        dpg.add_plot_legend()
                        dpg.add_plot_axis(dpg.mvXAxis, label=strings.t("histogram.intensity_axis"), tag="FilteringHistogram_x_axis")
                        dpg.add_plot_axis(dpg.mvYAxis, label=strings.t("histogram.count_axis"), tag="FilteringHistogram_y_axis")
            pass


def refreshFilteringTranslations():
    dpg.set_value("filteringHistogramText", strings.t("filtering.histogram_equalization"))
    dpg.set_value("filteringClaheText", strings.t("filtering.clahe_equalization"))
    dpg.set_value("filteringClaheClipLimitText", strings.t("filtering.clahe_clip_limit"))
    dpg.set_value("filteringClaheTileGridSizeText", strings.t("filtering.clahe_tile_grid_size"))
    dpg.set_value("filteringBrightnessContrastText", strings.t("filtering.brightness_and_contrast"))
    dpg.set_value("filteringBrightnessText", strings.t("filtering.brightness"))
    dpg.set_value("filteringContrastText", strings.t("filtering.contrast"))
    dpg.set_value("filteringAverageBlurText", strings.t("filtering.average_blur"))
    dpg.set_value("filteringAverageIntensityText", strings.t("filtering.intensity"))
    dpg.set_value("filteringGaussianBlurText", strings.t("filtering.gaussian_blur"))
    dpg.set_value("filteringGaussianIntensityText", strings.t("filtering.intensity"))
    dpg.set_value("filteringMedianBlurText", strings.t("filtering.median_blur"))
    dpg.set_value("filteringMedianIntensityText", strings.t("filtering.intensity"))
    dpg.configure_item("showFilteringHistogramToggle", label=strings.t("histogram.show_toggle"))
    dpg.set_value("filteringSaveImageText", strings.t("common.save_image"))
    dpg.configure_item("exportImageAsFileFiltering", label=strings.t("common.export_image_as_file"))
    dpg.set_value("filteringSaveHistogramText", strings.t("common.save_histogram"))
    dpg.configure_item("exportHistogramAsFileFiltering", label=strings.t("common.export_histogram_as_file"))
    dpg.configure_item("FilteringPlotParent", label=strings.t("filtering.plot"))
    dpg.configure_item("Filtering_x_axis", label=strings.t("axes.width"))
    dpg.configure_item("Filtering_y_axis", label=strings.t("axes.height"))
    dpg.configure_item("FilteringHistogramPlotParent", label=strings.t("histogram.title"))
    dpg.configure_item("FilteringHistogram_x_axis", label=strings.t("histogram.intensity_axis"))
    dpg.configure_item("FilteringHistogram_y_axis", label=strings.t("histogram.count_axis"))
