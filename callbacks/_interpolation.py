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

    def ramer_douglas_peucker(self, points, epsilon):
        if len(points) < 3:
            return points
        # Encontrar a maior distância
        dmax = 0
        index = 0
        end = len(points)
        for i in range(1, end - 1):
            d = self.perpendicular_distance(points[i], points[0], points[-1])
            if d > dmax:
                index = i
                dmax = d
        # Se a maior distância é maior que epsilon, simplificar recursivamente
        if dmax > epsilon:
            rec_results1 = self.ramer_douglas_peucker(points[:index+1], epsilon)
            rec_results2 = self.ramer_douglas_peucker(points[index:], epsilon)
            result = rec_results1[:-1] + rec_results2
        else:
            result = [points[0], points[-1]]
        return result

    def perpendicular_distance(self, point, line_start, line_end):
        if line_start == line_end:
            return np.linalg.norm(np.array(point) - np.array(line_start))
        else:
            n = np.abs(np.cross(np.array(line_end) - np.array(line_start), np.array(line_start) - np.array(point)))
            d = np.linalg.norm(np.array(line_end) - np.array(line_start))
            return n / d

    def calculate_arclength(self, points):
        length = 0
        for i in range(1, len(points)):
            length += np.linalg.norm(np.array(points[i]) - np.array(points[i-1]))
        return length

    def interpolate(self, sender=None, app_data=None):
        dpg.delete_item("originalPlot")
        dpg.delete_item("interpolationPlot")
        dpg.delete_item("originalResizedPlot")
        interpolationMode = dpg.get_value('interpolationListbox')
        spacingValue = dpg.get_value('spacingInterpolationSlider') + 1
        removalValue = dpg.get_value('removalInterpolationSlider')
        resizeCheckbox = dpg.get_value('resizeInterpolation')
        approxPolyCheckbox = dpg.get_value('approxPolyInterpolation')
        percArcLeng = dpg.get_value('approxPolySlider')

        self.currentX = []
        self.currentY = []

        x = []
        y = []

        for line_x, line_y in zip(self.originalX, self.originalY):
            x.append(float(line_x))
            y.append(float(line_y))

        if not approxPolyCheckbox:
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

        # Aplica approxPoly
        if approxPolyCheckbox:
            points = list(zip(x, y))
            arclength = self.calculate_arclength(points)
            epsilon = percArcLeng * arclength
            simplified_points = self.ramer_douglas_peucker(points, epsilon)
            x, y = zip(*simplified_points)  # Unzip simplified points

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



    """
    O código daqui para baixo não deveria existir e é uma aberração.
    A função de exportar o contorno da aba ContourExtraction para um arquivo é atrelada com os parâmetros definidos na interface de ContourExtraction e não existem em mais nenhum lugar do código.
    Por conta disso, para saber dados como xRes, yRes e etc, é necessário pegar os parametros da aba do contourExtraction ou replicar TODOS os parametros nessa aba (o que seria redundante, então, realizamos a primeira opção).
    Por causa disso, qualquer alteração feita na aba do ContourExtraction é refletida na hora de salvar o contorno da aba interpolation, MAS SÓ NA HORA DE SALVAR E NÃO VISUALMENTE NO RESTO DA ABA.
    Pra corrigir isso, seria necessário desacoplar os parâmetros da outra aba e criar um estado para a aplicação que permitisse outras abas lerem esses parâmetros cada vez que uma mudança é realizada. Mas, para fazer isso
    seria necessário reescrever a maior parte do código e não é viável no momento :)
    Além disso, grande parte das funções abaixo são cópias das mesmas funções que existem dentro da aba e da callback do ContourExtraction. Isso acontece porque o DearPyGui em python não possui "namespaces" pra tags
    e nem um sistema parecido, então tudo começa a ficar com um nome gigante e tem que ser repetido porque passar como parâmetro toda vez também é inviável. :)))))))
    Isso tudo dito, agora é possível exportar um contorno da interpolação para um arquivo! :D
    """


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
    

    def openDirectorySelector(self, sender=None, app_data=None):
        if dpg.get_value('inputInterpolatedContourNameText') != '':
            dpg.configure_item('interpolatedContourDirectorySelectorFileDialog', show=True)

    
    def selectFolder(self, sender=None, app_data=None):

        self.exportFilePath = app_data['file_path_name']

        self.exportFileName = dpg.get_value('inputInterpolatedContourNameText') + '.txt'
        filePath = os.path.join(self.exportFilePath, self.exportFileName)

        dpg.set_value('exportInterpolatedFileName', 'File Name: ' + self.exportFileName)
        dpg.set_value('exportInterpolatedPathName', 'Complete Path Name: ' + filePath)

        pass

    def exportButtonCall(self, sender, app_data=None):
        auxId = sender[13:]
        dpg.set_value('inputInterpolatedContourNameText', '')
        dpg.set_value('exportInterpolatedFileName', 'File Name: ')
        dpg.set_value('exportInterpolatedPathName', 'Complete Path Name: ')
        self.exportFileName = None
        self.exportFilePath = None
        dpg.configure_item('exportInterpolatedContourWindow', show=True)
        pass

    def exportIndividualContourToFile(self, sender=None, app_data=None):
            if self.exportFilePath is None:
                dpg.configure_item("exportInterpolatedContourError", show=True)
                return

            dpg.configure_item("exportInterpolatedContourError", show=False)
            self.exportContourToFile(os.path.join(self.exportFilePath, self.exportFileName))
            dpg.configure_item('exportInterpolatedContourWindow', show=False)
            pass

    def exportContourToFile(self, path):
        xarray = self.currentX
        yarray = self.currentY

        xRes = int(dpg.get_value("currentWidth")[6:-2])
        yRes = int(dpg.get_value("currentHeight")[7:-2])
        w = float(dpg.get_value("currentMaxWidth")[9:])
        h = float(dpg.get_value("currentMaxHeight")[9:])
        dx = w/xRes
        dy = h/yRes
        xmin = min(xarray)
        ymin = min(yarray)
        xmax = max(xarray)
        ymax = max(yarray)
        nx = round((xmax - xmin)/dx) + 1
        ny = round((ymax - ymin)/dy) + 1
        xarray.append(xarray[0])
        yarray.append(yarray[0])
        Mesh.export_coords_mesh(path, xarray, yarray, nx, ny, xmin, ymin, xmax, ymax, dx, dy, 1)
        pass