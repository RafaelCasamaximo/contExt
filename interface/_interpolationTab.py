import dearpygui.dearpygui as dpg

def showInterpolation(callbacks):
    with dpg.group(horizontal=True):
        with dpg.child_window(width=300):
            pass
        with dpg.child_window(tag='InterpolationParent'):
            with dpg.plot(tag="InterpolationPlotParent", label="Interpolation", height=-1, width=-1):
                dpg.add_plot_legend()
                dpg.add_plot_axis(dpg.mvXAxis, label="Width", tag="Interpolation_x_axis")
                dpg.add_plot_axis(dpg.mvYAxis, label="Height", tag="Interpolation_y_axis")
                dpg.fit_axis_data("Interpolation_y_axis")