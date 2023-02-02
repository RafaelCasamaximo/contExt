import dearpygui.dearpygui as dpg
import cv2
import numpy as np
import random

dpg.create_context()
dpg.create_viewport(title='Custom Title', width=800, height=600)
dpg.setup_dearpygui()

with dpg.window(label="Tutorial"):

    with dpg.table(header_row=True, policy=dpg.mvTable_SizingFixedFit, row_background=True, reorderable=True,
                   resizable=True, no_host_extendX=False, hideable=True,
                   borders_innerV=True, delay_search=True, borders_outerV=True, borders_innerH=True,
                   borders_outerH=True):

        dpg.add_table_column(label="AAA", width_fixed=True)
        dpg.add_table_column(label="BBB", width_fixed=True)
        dpg.add_table_column(label="CCC", width_stretch=True, init_width_or_weight=0.0)
        dpg.add_table_column(label="DDD", width_stretch=True, init_width_or_weight=0.0)

        for i in range(0, 5):
            with dpg.table_row():
                for j in range(0, 4):
                    if j == 2 or j == 3:
                        dpg.add_button(label=f"Stretch {i},{j}")
                    else:
                        dpg.add_text(f"Fixed {i}, {j}")

dpg.show_metrics()
dpg.show_viewport()

while dpg.is_dearpygui_running():
    dpg.render_dearpygui_frame()


dpg.destroy_context()


