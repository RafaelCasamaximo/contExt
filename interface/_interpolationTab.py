import dearpygui.dearpygui as dpg

def showInterpolation(callbacks):
    with dpg.group(horizontal=True):
        with dpg.child_window(width=300):
            pass
        with dpg.child_window(tag='InterpolationParent'):
            pass