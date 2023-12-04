import dearpygui.dearpygui as dpg
from ._texture import Texture
import cv2
import numpy as np

class Interpolation:
    def __init__(self) -> None:
        self.contours = []
        self.dimensions = None
        self.THICKNESS = 1

    def resetContours(self, sender=None, app_data=None):
        dpg.configure_item("cropInterpolation", show=False)
        dpg.delete_item("InterpolationTable")
        self.contours = []

    def extractCountour(self, sender=None, app_data=None):
        dpg.delete_item("InterpolationTable")
        self.createTable()
    
    def removeContour(self, sender=None, app_data=None, user_data=None):
        for contourEntry in self.contours:
            if (user_data == contourEntry['id']):
                self.contours.remove(contourEntry)
        dpg.delete_item("InterpolationTable")
        self.createTable()

    def createTable(self):
        with dpg.table(tag="InterpolationTable", header_row=True, policy=dpg.mvTable_SizingFixedFit, row_background=True,
            resizable=True, no_host_extendX=False, hideable=True,
            borders_innerV=True, delay_search=True, borders_outerV=True, borders_innerH=True,
            borders_outerH=True, parent='InterpolationParent'):
        
            dpg.add_table_column(label="Id", width_fixed=True)
            dpg.add_table_column(label="Color scale", width_fixed=True)
            dpg.add_table_column(label="Delete", width_fixed=True)

            for contourEntry in self.contours:
                with dpg.table_row():
                    for j in range(3):
                        if j == 0:
                            dpg.add_text(contourEntry['id'])
                        if j == 1:
                            dpg.add_slider_int(default_value=contourEntry['sliderInterpolationValue'], min_value=0, max_value=255, tag="colorScaleSlider" + str(contourEntry['id']), callback=self.colorScale, user_data=contourEntry['id'], width=200)
                        if j == 2:
                            dpg.add_button(label="Delete contour", user_data=contourEntry['id'], callback=self.removeContour)

        self.createImageContour()
            
    def createImageContour(self):
        blackImage = np.zeros(self.dimensions, dtype= np.uint8)
        for contourEntry in self.contours:
            colorContour = (contourEntry['color'][2], contourEntry['color'][1], contourEntry['color'][0], 255)
            cv2.drawContours(blackImage, contourEntry["data"], -1, colorContour, self.THICKNESS)
        Texture.updateTexture("Interpolation", blackImage)

    def colorScale(self, sender=None, app_data=None, user_data=None):
        blackImage = np.zeros(self.dimensions, dtype= np.uint8)
        slider = dpg.get_value("colorScaleSlider" + str(user_data))
        for contourEntry in self.contours:
            colorContour = (contourEntry['color'][2], contourEntry['color'][1], contourEntry['color'][0], 255)
            if (user_data == contourEntry['id']):
                contourEntry['color'] = (slider, slider, slider, 255)
                contourEntry['sliderInterpolationValue'] = slider
                cv2.drawContours(blackImage, contourEntry["data"], -1, contourEntry['color'], self.THICKNESS)
            else:
                cv2.drawContours(blackImage, contourEntry["data"], -1, colorContour, self.THICKNESS)
        Texture.updateTexture("Interpolation", blackImage)