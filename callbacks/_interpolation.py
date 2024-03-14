import dearpygui.dearpygui as dpg
from ._texture import Texture
import cv2
import numpy as np
import pandas as pd
from ._meshGeneration import MeshGeneration
import os.path
from ._mesh import Mesh
from ._scopeList  import ScopeList

class Interpolation:
    def __init__(self) -> None:
        self.originalX = []
        self.originalY = []
        self.currentX  = []
        self.currentY  = []
        self.originalXResized = []
        self.originalYResized = []
        self.meshGeneration = MeshGeneration()
        self.exportFilePath = None
        self.exportFileName = None
        self.methodApplied = False

    def remove_values(self, vec, nan_remove):  
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
        dpg.delete_item("originalPlot")
        dpg.delete_item("interpolationPlot")
        dpg.add_line_series(self.originalX, self.originalY, label='Original Contour', tag="originalPlot", parent="Interpolation_y_axis")
        dpg.set_value('area_after_interp', 'Interpolation Area: --')
        dpg.set_value("area_before_interp", "Original Area: " + str(Mesh.get_area(self.originalX, self.originalY)))
        dpg.fit_axis_data("Interpolation_x_axis")
        dpg.fit_axis_data("Interpolation_y_axis")

    def interpolate(self, sender=None, app_data=None):
        dpg.delete_item("originalPlot")
        dpg.delete_item("interpolationPlot")
        dpg.delete_item("originalResizedPlot")
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

        original_area = Mesh.get_area(self.originalX, self.originalY)

        if resizeCheckbox:
            x = np.array(x) * spacingValue
            y = np.array(y) * spacingValue
            self.originalXResized = np.array(self.originalX) * spacingValue
            self.originalYResized = np.array(self.originalY) * spacingValue
            dpg.add_line_series(self.originalXResized, self.originalYResized, label='Original Contour Resized', tag="originalResizedPlot", parent="Interpolation_y_axis")
            original_area = Mesh.get_area(self.originalX, self.originalY) * spacingValue * spacingValue
            dpg.set_value("area_before_interp", "Original Area Resized: " + str(original_area))
        else:
            dpg.set_value("area_before_interp", "Original Area: " + str(original_area))
        
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
        elif interpolationMode == 'Nearest':
            x_interpolated = pd.Series(x_extended).interpolate(method='nearest', limit_direction='both')
            y_interpolated = pd.Series(y_extended).interpolate(method='nearest', limit_direction='both')
        elif interpolationMode == 'Quadratic':
            x_interpolated = pd.Series(x_extended).interpolate(method='quadratic', limit_direction='both')
            y_interpolated = pd.Series(y_extended).interpolate(method='quadratic', limit_direction='both')
        elif interpolationMode == 'Spline3':
            x_interpolated = pd.Series(x_extended).interpolate(method='spline', limit_direction='both', order=3)
            y_interpolated = pd.Series(y_extended).interpolate(method='spline', limit_direction='both', order=3)
        
        for interpolated_x, interpolated_y in zip(x_interpolated, y_interpolated):
            self.currentX.append(float(interpolated_x))
            self.currentY.append(float(interpolated_y))

        # Define a flag indicando que o método de interpolação foi aplicado
        self.methodApplied = True
        area_interpolated = Mesh.get_area(self.currentX, self.currentY)

        dif = abs(original_area - area_interpolated)
            
        dpg.set_value("area_after_interp", "Interpolation Area: {:.2f}".format(area_interpolated))
        dpg.set_value("delta_interp", "Delta: {:.2f}%".format(abs(100*dif/original_area)))

        dpg.add_line_series(self.currentX, self.currentY, label='Interpolated Contour', tag="interpolationPlot", parent="Interpolation_y_axis")
        dpg.add_line_series(self.originalX, self.originalY, label='Original Contour', tag="originalPlot", parent="Interpolation_y_axis")
        dpg.fit_axis_data("Interpolation_x_axis")
        dpg.fit_axis_data("Interpolation_y_axis")

    def exportToMeshGeneration(self, sender=None, app_data=None):
        spacingValue = dpg.get_value('spacingInterpolationSlider')
        resizeCheckbox = dpg.get_value('resizeInterpolation')

        xRes = int(dpg.get_value("currentWidth")[6:-2])
        yRes = int(dpg.get_value("currentHeight")[7:-2])
        w = float(dpg.get_value("currentMaxWidth")[9:])
        h = float(dpg.get_value("currentMaxHeight")[9:])
        
        # Verifica se o método de interpolação foi aplicado
        if self.methodApplied:
            if resizeCheckbox:
                xRes = xRes * spacingValue
                yRes = yRes * spacingValue
                w = w * spacingValue
                h = h * spacingValue
            self.methodApplied = False  # Resetar a flag após usar

        dx = w/xRes
        dy = h/yRes
        
        xmin = min(self.currentX)
        ymin = min(self.currentY)
        xmax = max(self.currentX)
        ymax = max(self.currentY)
            
        nx = round((xmax - xmin)/dx) + 1
        ny = round((ymax - ymin)/dy) + 1

        self.meshGeneration.originalX = [nx, xmin, xmax, dx] + self.currentX
        self.meshGeneration.originalY = [ny, ymin, ymax, dy] + self.currentY
        self.meshGeneration.subcontours = ScopeList(0, len(self.currentX))

        f = open("outputInterpToMesh.txt", "a")
        f.write(' '.join(map(str, self.meshGeneration.originalX)))
        f.write(' '.join(map(str, self.meshGeneration.originalY)))
        f.close()
        self.meshGeneration.importContour()