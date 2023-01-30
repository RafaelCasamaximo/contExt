import dearpygui.dearpygui as dpg
import cv2
import numpy as np
import random

dpg.create_context()
dpg.create_viewport(title='Custom Title', width=800, height=600)
dpg.setup_dearpygui()





dpg.set_viewport_vsync(False)

img = cv2.imread('./test2.png', 1) 
data = np.flip(img, 2)  # because the camera data comes in as BGR and we need RGB
data = data.ravel()  # flatten camera data to a 1 d stricture
data = np.asfarray(data, dtype='f')  # change data type to 32bit floats
texture_data = np.true_divide(data, 255.0)  # normalize image data to prepare for GPU

dimensions = img.shape
height = img.shape[0]
width = img.shape[1]

with dpg.texture_registry(show=False):
    dpg.add_raw_texture(width=width, height=height, default_value=texture_data, format=dpg.mvFormat_Float_rgb, tag="texture_tag")

with dpg.window(label="Tutorial"):
    dpg.add_image("texture_tag")

dpg.show_metrics()








dpg.show_viewport()

while dpg.is_dearpygui_running():

    # updating the texture in a while loop the frame rate will be limited to the camera frame rate.
    # commenting out the "ret, frame = vid.read()" line will show the full speed that operations and updating a texture can run at
    img = cv2.imread('./test' + str(random.randint(2, 4)) + '.png', 1) 
    data = np.flip(img, 2)  # because the camera data comes in as BGR and we need RGB
    data = data.ravel()  # flatten camera data to a 1 d stricture
    data = np.asfarray(data, dtype='f')  # change data type to 32bit floats
    texture_data = np.true_divide(data, 255.0)  # normalize image data to prepare for GPU

    dpg.set_value("texture_tag", texture_data)
    dpg.render_dearpygui_frame()


dpg.destroy_context()


