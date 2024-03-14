import dearpygui.dearpygui as dpg

def showInterpolation(callbacks):
    with dpg.group(horizontal=True):
        with dpg.child_window(width=300):
            dpg.add_text('Interpolation')
            dpg.add_listbox(tag='interpolationListbox', items=['Nearest', 'Bilinear', 'Bicubic', 'Quadratic', 'Spline3'], width=-1)
            dpg.add_checkbox(label='Expand Dimensions', tag='resizeInterpolation')
            dpg.add_text('Node Spacing Increment')
            dpg.add_slider_int(tag='spacingInterpolationSlider', default_value=1, min_value=1, max_value=7, width=-1)
            dpg.add_text('Node Removal Increment')
            dpg.add_slider_int(tag='removalInterpolationSlider', default_value=0, min_value=0, max_value=7, width=-1)
            dpg.add_button(tag='interpolateButton', width=-1, label='Apply Method', callback=lambda sender, app_data: callbacks.interpolation.interpolate(sender, app_data))
            dpg.add_separator()
            dpg.add_button(tag='interpolationToMesh', width=-1, label='Export to Mesh Generation', callback=lambda sender, app_data: callbacks.interpolation.exportToMeshGeneration(sender, app_data))
            # dpg.add_button(tag='interpolationExport', width=-1, label='Export Individual Contour', callback=lambda sender, app_data: )
            # dpg.add_separator()
            pass
        with dpg.child_window(tag='InterpolationParent'):
            with dpg.plot(tag="InterpolationPlotParent", label="Interpolation Plot", height=-1 - 20, width=-1, equal_aspects=True):
                dpg.add_plot_legend()
                dpg.add_plot_axis(dpg.mvXAxis, label="x", tag="Interpolation_x_axis")
                dpg.add_plot_axis(dpg.mvYAxis, label="y", tag="Interpolation_y_axis")
            with dpg.group(horizontal=True):
                dpg.add_text('Original Area: --', tag='area_before_interp')
                dpg.add_text('Current Area: --', tag='area_after_interp')
                dpg.add_text('Delta: --', tag='delta_interp')
            pass