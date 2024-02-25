import dearpygui.dearpygui as dpg
from ._texture import Texture
import cv2
import numpy as np
import pandas as pd

class Interpolation:
    def __init__(self) -> None:
        self.originalX = []
        self.originalY = []
        self.currentX  = []
        self.currentY  = []

    def remove_values(self, vec, nan_remove):  # Definindo como método da classe Interpolation
        result = []
        count = 0
        for i, val in enumerate(vec):
            if i == 0 or i == len(vec) - 1:
                result.append(val)
            elif count < nan_remove:
                result.append(np.nan)
                count += 1
            else:
                result.append(val)
                count = 0
        return result

    def extractContour(self, sender=None, app_data=None):
        dpg.delete_item("interpolationPlot")
        dpg.add_line_series(self.originalX, self.originalY, tag="interpolationPlot", parent="Interpolation_y_axis")

    def interpolate(self, sender=None, app_data=None):
        dpg.delete_item("interpolationPlot")
        interpolationMode = dpg.get_value('interpolationListbox')
        spacingValue = dpg.get_value('spacingInterpolationSlider')
        removalValue = dpg.get_value('removalInterpolationSlider')
        resizeCheckbox = dpg.get_value('resizeInterpolation')

        self.currentX = []
        self.currentY = []
        
        x = []
        y = []
        for line_x, line_y in zip(self.originalX, self.originalY):
            x.append(float(line_x))
            y.append(float(line_y))

        x = self.remove_values(x, removalValue)
        y = self.remove_values(y, removalValue)
        if resizeCheckbox:
            x = np.array(x) * spacingValue
            y = np.array(y) * spacingValue

        x_extended = []
        y_extended = []
        for i, (val_x, val_y) in enumerate(zip(x, y)):
            if i == len(x) - 1:
                x_extended.append(val_x)
                y_extended.append(val_y)
            else:
                x_extended.extend([val_x] + [np.nan] * (spacingValue - 1))
                y_extended.extend([val_y] + [np.nan] * (spacingValue - 1))
        if interpolationMode == 'Bilinear':
            x_interpolated = pd.Series(x_extended).interpolate(method='linear', limit_direction='both')
            y_interpolated = pd.Series(y_extended).interpolate(method='linear', limit_direction='both')
        elif interpolationMode == 'Bicubic':
            x_interpolated = pd.Series(x_extended).interpolate(method='cubic', limit_direction='both')
            y_interpolated = pd.Series(y_extended).interpolate(method='cubic', limit_direction='both')
        
        for interpolated_x, interpolated_y in zip(x_interpolated, y_interpolated):
            self.currentX.append(float(interpolated_x))
            self.currentY.append(float(interpolated_y))

        dpg.add_line_series(self.currentX, self.currentY, tag="interpolationPlot", parent="Interpolation_y_axis")