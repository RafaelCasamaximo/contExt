import dearpygui.dearpygui as dpg

def showInterpolation(callbacks):
    with dpg.group(horizontal=True):
        with dpg.child_window(width=300):
            dpg.add_text('Interpolation')
            dpg.add_listbox(tag='interpolationListbox', items=['Bilinear', 'Bicubic'], width=-1)
            dpg.add_checkbox(label='Expand Dimensions', tag='resizeInterpolation')
            dpg.add_text('Node Spacing Increment')
            dpg.add_slider_int(tag='spacingInterpolationSlider', default_value=1, min_value=1, max_value=7, width=-1)
            dpg.add_text('Node Removal Increment')
            dpg.add_slider_int(tag='removalInterpolationSlider', default_value=0, min_value=0, max_value=7, width=-1)
            dpg.add_button(tag='interpolateButton', width=-1, label='Apply Method', callback=lambda sender, app_data: callbacks.interpolation.interpolate(sender, app_data))
            dpg.add_separator()
            pass
        with dpg.child_window(tag='InterpolationParent'):
            with dpg.plot(tag="InterpolationPlotParent", label="Interpolation", height=-1, width=-1, equal_aspects=True):
                dpg.add_plot_legend()
                dpg.add_plot_axis(dpg.mvXAxis, label="Width", tag="Interpolation_x_axis")
                dpg.add_plot_axis(dpg.mvYAxis, label="Height", tag="Interpolation_y_axis")