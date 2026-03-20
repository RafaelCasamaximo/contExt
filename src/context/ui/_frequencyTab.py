import dearpygui.dearpygui as dpg

from . import strings


def showFrequency(callbacks):
    with dpg.group(horizontal=True):
        with dpg.child_window(width=320):
            with dpg.group(horizontal=True):
                dpg.add_checkbox(
                    tag="gaborCheckbox",
                    callback=lambda sender, app_data: callbacks.imageProcessing.toggleAndExecuteQuery("gaborFilter", sender, app_data),
                )
                dpg.add_text(strings.t("frequency.gabor_filter"), tag="frequencyGaborText")
            dpg.add_text(strings.t("frequency.gabor_kernel_size"), tag="frequencyGaborKernelText")
            dpg.add_slider_int(
                tag="gaborKernelSlider",
                default_value=11,
                min_value=3,
                max_value=31,
                width=-1,
                callback=lambda: callbacks.imageProcessing.executeQuery("gaborFilter"),
            )
            dpg.add_text(strings.t("frequency.gabor_sigma"), tag="frequencyGaborSigmaText")
            dpg.add_slider_float(
                tag="gaborSigmaSlider",
                default_value=4.0,
                min_value=0.1,
                max_value=20.0,
                width=-1,
                callback=lambda: callbacks.imageProcessing.executeQuery("gaborFilter"),
            )
            dpg.add_text(strings.t("frequency.gabor_theta"), tag="frequencyGaborThetaText")
            dpg.add_slider_float(
                tag="gaborThetaSlider",
                default_value=0.0,
                min_value=0.0,
                max_value=180.0,
                width=-1,
                callback=lambda: callbacks.imageProcessing.executeQuery("gaborFilter"),
            )
            dpg.add_text(strings.t("frequency.gabor_lambda"), tag="frequencyGaborLambdaText")
            dpg.add_slider_float(
                tag="gaborLambdaSlider",
                default_value=10.0,
                min_value=1.0,
                max_value=32.0,
                width=-1,
                callback=lambda: callbacks.imageProcessing.executeQuery("gaborFilter"),
            )
            dpg.add_text(strings.t("frequency.gabor_gamma"), tag="frequencyGaborGammaText")
            dpg.add_slider_float(
                tag="gaborGammaSlider",
                default_value=0.5,
                min_value=0.1,
                max_value=2.0,
                width=-1,
                callback=lambda: callbacks.imageProcessing.executeQuery("gaborFilter"),
            )
            dpg.add_text(strings.t("frequency.gabor_psi"), tag="frequencyGaborPsiText")
            dpg.add_slider_float(
                tag="gaborPsiSlider",
                default_value=0.0,
                min_value=0.0,
                max_value=180.0,
                width=-1,
                callback=lambda: callbacks.imageProcessing.executeQuery("gaborFilter"),
            )
            dpg.add_separator()

            with dpg.group(horizontal=True):
                dpg.add_checkbox(
                    tag="frequencyDomainCheckbox",
                    callback=lambda sender, app_data: callbacks.imageProcessing.toggleAndExecuteQuery("frequencyDomainFilter", sender, app_data),
                )
                dpg.add_text(strings.t("frequency.frequency_filter"), tag="frequencyFilterText")
            dpg.add_text(strings.t("frequency.filter_mode"), tag="frequencyFilterModeText")
            dpg.add_listbox(
                tag="frequencyFilterModeListbox",
                items=strings.option_labels("frequency_filter_mode"),
                default_value=strings.option_label("frequency_filter_mode", "none"),
                width=-1,
                callback=callbacks.imageProcessing.handleFrequencyControlChange,
            )
            dpg.add_text(strings.t("frequency.cutoff_radius"), tag="frequencyCutoffRadiusText")
            dpg.add_slider_int(
                tag="frequencyCutoffSlider",
                default_value=24,
                min_value=1,
                max_value=256,
                width=-1,
                callback=callbacks.imageProcessing.handleFrequencyControlChange,
            )
            dpg.add_text(strings.t("frequency.band_min_radius"), tag="frequencyBandMinText")
            dpg.add_slider_int(
                tag="frequencyBandMinSlider",
                default_value=12,
                min_value=1,
                max_value=256,
                width=-1,
                callback=callbacks.imageProcessing.handleFrequencyControlChange,
            )
            dpg.add_text(strings.t("frequency.band_max_radius"), tag="frequencyBandMaxText")
            dpg.add_slider_int(
                tag="frequencyBandMaxSlider",
                default_value=48,
                min_value=1,
                max_value=256,
                width=-1,
                callback=callbacks.imageProcessing.handleFrequencyControlChange,
            )
            dpg.add_separator()

            dpg.add_text(strings.t("frequency.manual_mask"), tag="frequencyManualMaskText")
            dpg.add_text(strings.t("frequency.mask_radius"), tag="frequencyMaskRadiusText")
            dpg.add_slider_int(
                tag="frequencyMaskRadiusSlider",
                default_value=8,
                min_value=1,
                max_value=64,
                width=-1,
                callback=callbacks.imageProcessing.handleFrequencyControlChange,
            )
            dpg.add_button(
                tag="frequencyMaskModeButton",
                width=-1,
                label=strings.t("frequency.mask_mode_draw"),
                callback=callbacks.imageProcessing.toggleFrequencyMaskMode,
            )
            dpg.add_button(
                tag="frequencyResetMaskButton",
                width=-1,
                label=strings.t("frequency.reset_mask"),
                callback=callbacks.imageProcessing.resetFrequencyMask,
            )
            dpg.add_text(strings.t("frequency.mask_hint"), tag="frequencyMaskHintText", wrap=290)

            with dpg.group(tag="exportImageAsFileFrequencyGroup", show=False):
                dpg.add_separator()
                dpg.add_text(strings.t("common.save_image"), tag="frequencySaveImageText")
                dpg.add_button(
                    tag="exportImageAsFileFrequency",
                    width=-1,
                    label=strings.t("common.export_image_as_file"),
                    callback=lambda sender, app_data: callbacks.imageProcessing.exportImage(sender, app_data, "Frequency"),
                )
                dpg.add_button(
                    tag="exportSpectrumAsFileFrequency",
                    width=-1,
                    label=strings.t("frequency.export_spectrum_as_file"),
                    callback=lambda sender, app_data: callbacks.imageProcessing.exportImage(sender, app_data, "FrequencySpectrum"),
                )

            with dpg.group(tag="exportHistogramAsFileFrequencyGroup", show=False):
                dpg.add_separator()
                dpg.add_text(strings.t("common.save_histogram"), tag="frequencySaveHistogramText")
                dpg.add_button(
                    tag="exportHistogramAsFileFrequency",
                    width=-1,
                    label=strings.t("common.export_histogram_as_file"),
                    callback=lambda sender, app_data: callbacks.imageProcessing.exportHistogram(sender, app_data, "Frequency"),
                )

        with dpg.child_window(tag="FrequencyParent"):
            with dpg.group():
                with dpg.child_window(tag="FrequencyImagePanel", height=-180):
                    with dpg.table(
                        tag="FrequencyTopTable",
                        header_row=False,
                        policy=dpg.mvTable_SizingStretchProp,
                        borders_innerV=True,
                        borders_outerV=False,
                        borders_innerH=False,
                        borders_outerH=False,
                        resizable=False,
                    ):
                        dpg.add_table_column(init_width_or_weight=1.0)
                        dpg.add_table_column(init_width_or_weight=1.0)
                        with dpg.table_row():
                            with dpg.table_cell():
                                with dpg.plot(tag="FrequencyPlotParent", label=strings.t("frequency.processed_plot"), height=-1, width=-1, equal_aspects=True):
                                    dpg.add_plot_legend()
                                    dpg.add_plot_axis(dpg.mvXAxis, label=strings.t("axes.width"), tag="Frequency_x_axis")
                                    dpg.add_plot_axis(dpg.mvYAxis, label=strings.t("axes.height"), tag="Frequency_y_axis")
                            with dpg.table_cell():
                                with dpg.plot(tag="FrequencySpectrumPlotParent", label=strings.t("frequency.spectrum_plot"), height=-1, width=-1, equal_aspects=True):
                                    dpg.add_plot_legend()
                                    dpg.add_plot_axis(dpg.mvXAxis, label=strings.t("axes.width"), tag="FrequencySpectrum_x_axis")
                                    dpg.add_plot_axis(dpg.mvYAxis, label=strings.t("axes.height"), tag="FrequencySpectrum_y_axis")

                with dpg.item_handler_registry(tag="FrequencySpectrumHandlers"):
                    dpg.add_item_clicked_handler(callback=callbacks.imageProcessing.handleFrequencySpectrumClick)
                dpg.bind_item_handler_registry("FrequencySpectrumPlotParent", "FrequencySpectrumHandlers")

                with dpg.child_window(tag="FrequencyHistogramPanel", height=160):
                    with dpg.plot(tag="FrequencyHistogramPlotParent", label=strings.t("histogram.title"), height=-1, width=-1):
                        dpg.add_plot_legend()
                        dpg.add_plot_axis(dpg.mvXAxis, label=strings.t("histogram.intensity_axis"), tag="FrequencyHistogram_x_axis")
                        dpg.add_plot_axis(dpg.mvYAxis, label=strings.t("histogram.count_axis"), tag="FrequencyHistogram_y_axis")


def refreshFrequencyTranslations(old_locale=None):
    old_locale = old_locale or strings.get_locale()
    mode_value = dpg.get_value("frequencyFilterModeListbox")

    dpg.set_value("frequencyGaborText", strings.t("frequency.gabor_filter"))
    dpg.set_value("frequencyGaborKernelText", strings.t("frequency.gabor_kernel_size"))
    dpg.set_value("frequencyGaborSigmaText", strings.t("frequency.gabor_sigma"))
    dpg.set_value("frequencyGaborThetaText", strings.t("frequency.gabor_theta"))
    dpg.set_value("frequencyGaborLambdaText", strings.t("frequency.gabor_lambda"))
    dpg.set_value("frequencyGaborGammaText", strings.t("frequency.gabor_gamma"))
    dpg.set_value("frequencyGaborPsiText", strings.t("frequency.gabor_psi"))
    dpg.set_value("frequencyFilterText", strings.t("frequency.frequency_filter"))
    dpg.set_value("frequencyFilterModeText", strings.t("frequency.filter_mode"))
    dpg.configure_item("frequencyFilterModeListbox", items=strings.option_labels("frequency_filter_mode"))
    dpg.set_value("frequencyFilterModeListbox", strings.translate_option_value("frequency_filter_mode", mode_value, old_locale))
    dpg.set_value("frequencyCutoffRadiusText", strings.t("frequency.cutoff_radius"))
    dpg.set_value("frequencyBandMinText", strings.t("frequency.band_min_radius"))
    dpg.set_value("frequencyBandMaxText", strings.t("frequency.band_max_radius"))
    dpg.set_value("frequencyManualMaskText", strings.t("frequency.manual_mask"))
    dpg.set_value("frequencyMaskRadiusText", strings.t("frequency.mask_radius"))
    dpg.configure_item("frequencyResetMaskButton", label=strings.t("frequency.reset_mask"))
    dpg.set_value("frequencyMaskHintText", strings.t("frequency.mask_hint"))
    dpg.set_value("frequencySaveImageText", strings.t("common.save_image"))
    dpg.configure_item("exportImageAsFileFrequency", label=strings.t("common.export_image_as_file"))
    dpg.configure_item("exportSpectrumAsFileFrequency", label=strings.t("frequency.export_spectrum_as_file"))
    dpg.set_value("frequencySaveHistogramText", strings.t("common.save_histogram"))
    dpg.configure_item("exportHistogramAsFileFrequency", label=strings.t("common.export_histogram_as_file"))
    dpg.configure_item("FrequencyPlotParent", label=strings.t("frequency.processed_plot"))
    dpg.configure_item("Frequency_x_axis", label=strings.t("axes.width"))
    dpg.configure_item("Frequency_y_axis", label=strings.t("axes.height"))
    dpg.configure_item("FrequencySpectrumPlotParent", label=strings.t("frequency.spectrum_plot"))
    dpg.configure_item("FrequencySpectrum_x_axis", label=strings.t("axes.width"))
    dpg.configure_item("FrequencySpectrum_y_axis", label=strings.t("axes.height"))
    dpg.configure_item("FrequencyHistogramPlotParent", label=strings.t("histogram.title"))
    dpg.configure_item("FrequencyHistogram_x_axis", label=strings.t("histogram.intensity_axis"))
    dpg.configure_item("FrequencyHistogram_y_axis", label=strings.t("histogram.count_axis"))
