import dearpygui.dearpygui as dpg
import cv2
import os.path
import random
from ._mesh import Mesh
from ._texture import Texture
from ._blocks import Blocks
from ._meshGeneration import MeshGeneration
from ._imageProcessing import ImageProcessing
from ._interpolation import Interpolation

class ContourExtraction:

    def __init__(self) -> None:

        self.filePath = None
        self.meshGeneration = MeshGeneration()
        self.imageProcessing = ImageProcessing()
        self.interpolation = Interpolation()
        self.contourTableEntry = []
        self.exportFilePath = None
        self.exportFileName = None
        self.exportSelectPath = None
        self.exportSelectFileName = None
        self.toggleDrawContoursFlag = True
        self.toggleMeshImport = False

    def extractContour(self, sender=None, app_data=None):

        globalThresholdSelectedFlag = dpg.get_value('globalThresholdingCheckbox')
        adaptativeThresholdSelectedFlag = dpg.get_value('adaptativeThresholdingCheckbox')
        adaptativeGaussianThresholdSelectedFlag = dpg.get_value('adaptativeGaussianThresholdingCheckbox')
        otsuBinarizationFlag = dpg.get_value('otsuBinarization')

        if globalThresholdSelectedFlag == False and adaptativeThresholdSelectedFlag == False and adaptativeGaussianThresholdSelectedFlag == False and otsuBinarizationFlag == False:
            dpg.configure_item('nonBinary', show=True)
            return

        image = self.imageProcessing.blocks[self.imageProcessing.getLastActiveBeforeMethod('findContour')]['output'].copy()
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


        approximationMode = None
        value = dpg.get_value('approximationModeListbox')
        if value == 'None':
            approximationMode = cv2.CHAIN_APPROX_NONE
        elif value == 'Simple':
            approximationMode = cv2.CHAIN_APPROX_SIMPLE
        elif value == 'TC89_L1':
            approximationMode = cv2.CHAIN_APPROX_TC89_L1
        elif value == 'TC89_KCOS':
            approximationMode = cv2.CHAIN_APPROX_TC89_KCOS

        thicknessValue = dpg.get_value('contourThicknessSlider')

        contours, hierarchy = cv2.findContours(image, cv2.RETR_LIST, approximationMode)
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

        self.removeContour()

        for idx, contour in enumerate(contours):
            contourColor = (random.randint(0,255),random.randint(0,255),random.randint(0,255), 255)
            contourColorBGR = (contourColor[2], contourColor[1], contourColor[0])
            self.contourTableEntry.append(
                {
                    'id': idx,
                    'pointsNo': len(contour),
                    'color': contourColorBGR,
                    'data': contour,
                    'contourX': [x[0][0] for x in contour],
                    'contourY': [x[0][1] for x in contour],
                }
            )
            cv2.drawContours(image, contour, -1, contourColor, thicknessValue)

        self.contourTableEntry = list(sorted(self.contourTableEntry, key=lambda x: x['pointsNo'], reverse=True))

        dpg.add_separator(tag='separator1', parent='ContourExtractionParent')
        dpg.add_button(tag='toggleDrawContoursButton', width=-1, label='Hide All Contours', parent='ContourExtractionParent', callback=self.toggleDrawContours)
        dpg.add_separator(tag='separator2', parent='ContourExtractionParent')
        dpg.add_button(tag='removeExtractContour', width=-1, label='Remove Contour', parent='ContourExtractionParent', callback=self.removeContour)
        dpg.add_separator(tag='separator3', parent='ContourExtractionParent')
        dpg.add_button(tag='exportSelectedContours', width=-1, label='Export Selected Contours as Files', parent='ContourExtractionParent', callback=self.exportSelectedButtonCall)
        dpg.add_separator(tag='separator4', parent='ContourExtractionParent')
        with dpg.table(tag='ContourExtractionTable', header_row=True, policy=dpg.mvTable_SizingFixedFit, row_background=True,
            resizable=True, no_host_extendX=False, hideable=True,
            borders_innerV=True, delay_search=True, borders_outerV=True, borders_innerH=True,
            borders_outerH=True, parent='ContourExtractionParent'):

            dpg.add_table_column(label="Id", width_fixed=True)
            dpg.add_table_column(label="Color", width_fixed=True)
            dpg.add_table_column(label="Visible", width_fixed=True)
            dpg.add_table_column(label="Size", width_fixed=True)
            dpg.add_table_column(label="Position", width_fixed=True)
            dpg.add_table_column(label="Export to Mesh Generation", width_fixed=True)
            dpg.add_table_column(label="Export Contour", width_fixed=True)
            dpg.add_table_column(label="Export to Interpolation", width_fixed=True)


            for contourEntry in self.contourTableEntry:
                with dpg.table_row():
                    for j in range(8):
                        if j == 0:
                            dpg.add_text(contourEntry['id'])
                        if j == 1:
                            dpg.add_color_button(default_value=contourEntry['color'])
                        if j == 2:
                            dpg.add_checkbox(tag='checkboxContourId' + str(contourEntry['id']), callback= lambda sender, app_data: self.redrawContours(), default_value=True)
                        if j == 3:
                            dpg.add_text(contourEntry['pointsNo'])
                        if j == 4:
                            xmin = min(contourEntry["contourX"])
                            ymin = min(contourEntry["contourY"])
                            xmax = max(contourEntry["contourX"])
                            ymax = max(contourEntry["contourY"])
                            dpg.add_text("Xmin = " + str(xmin) + "\nYmin = " + str(ymin) + "\nXmax = " + str(xmax) + "\nYmax = " + str(ymax), tag="position" + str(contourEntry['id']))
                        if j == 5:
                            dpg.add_button(label='Export to Mesh Generation', width=-1, tag="exportMeshGeneration" + str(contourEntry['id']), callback=self.exportToMeshGeneration)
                        if j == 6:
                            dpg.add_button(label='Export Individual Contour', tag="exportContour" + str(contourEntry['id']), callback=self.exportButtonCall)
                        if j == 7:
                            dpg.add_button(label='Export to Interpolation', tag="exportInterpolation" + str(contourEntry['id']), callback=self.exportToInterpolation)

        self.imageProcessing.blocks[Blocks.findContour.value]['output'] = image
        Texture.updateTexture(self.imageProcessing.blocks[Blocks.findContour.value]['tab'], image)

        dpg.configure_item('contour_ordering', enabled=True)
        dpg.configure_item('contourExportOption', enabled=True)
        xRes = int(dpg.get_value("currentWidth")[6:-2])
        yRes = int(dpg.get_value("currentHeight")[7:-2])
        dpg.set_value("currentWidthOffset", 'Current: 0')
        dpg.set_value("currentHeightOffset", 'Current: 0')
        dpg.set_value("currentMaxWidth", 'Current: ' + str(xRes))
        dpg.set_value("currentMaxHeight", 'Current: ' + str(yRes))
        dpg.configure_item("maxWidthMapping", default_value = xRes)
        dpg.configure_item("maxHeightMapping", default_value = yRes)

    def toggleDrawContours(self, sender = None, app_data = None):
        self.toggleDrawContoursFlag = not self.toggleDrawContoursFlag
        if self.toggleDrawContoursFlag:
            dpg.configure_item('toggleDrawContoursButton', label="Hide All Contours")
            self.showAllContours()
        else:
            dpg.configure_item('toggleDrawContoursButton', label="Show All Contours")
            self.hideAllContours()
        pass

    def toggleExportOnMesh(self, sender = None, app_data = None):
        self.toggleMeshImport = not self.toggleMeshImport
        if self.toggleMeshImport:
            dpg.configure_item('contourExportOption', label="Enable")
            dpg.set_value("contourExportOptionTooltip", "Click to Disable option export as mesh.")
        else:
            dpg.configure_item('contourExportOption', label="Disable")
            dpg.set_value("contourExportOptionTooltip", "Click to Enable option export as mesh.")
        pass
    
    def exportToMeshGeneration(self, sender, app_data=None):
        auxId = int(sender[20:])
        for i in self.contourTableEntry:
            if i["id"] == auxId:
                entry = i
                break
        xarray = entry["contourX"]
        yarray = entry["contourY"]
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
        self.meshGeneration.originalX = [nx, xmin, xmax, dx] + xarray
        self.meshGeneration.originalY = [ny, ymin, ymax, dy] + yarray

        f = open("outputCtoMesh.txt", "a")
        f.write(' '.join(map(str, self.meshGeneration.originalX)))
        f.write(' '.join(map(str, self.meshGeneration.originalY)))
        f.close()
        self.meshGeneration.importContour()
        pass

    def exportToInterpolation(self, sender, app_data=None):
        auxId = int(sender[19:])
        for i in self.contourTableEntry:
            if i["id"] == auxId:
                entry = i
                break
        xarray = entry["contourX"]
        yarray = entry["contourY"]
        xarray.append(xarray[0])
        yarray.append(yarray[0])
        self.interpolation.originalX = xarray
        self.interpolation.originalY = yarray
        self.interpolation.extractContour()
        pass

    def updateContour(self, sender, app_data=None):
        xRes = int(dpg.get_value("currentWidth")[6:-2])
        yRes = int(dpg.get_value("currentHeight")[7:-2])
        xoffset = float(dpg.get_value("widthOffset"))
        yoffset = float(dpg.get_value("heightOffset"))
        w = float(dpg.get_value("maxWidthMapping"))
        h = float(dpg.get_value("maxHeightMapping"))
        matlabFlag = dpg.get_value("matlabModeCheckbox")

        for i in range(len(self.contourTableEntry)):
            entry = self.contourTableEntry[i]
            xarray = [x[0][0] for x in entry["data"]]
            yarray = [x[0][1] for x in entry["data"]]
            if matlabFlag:
                yarray = Mesh.convert_matlab(yarray, yRes - 1)
                xarray = xarray[::-1]
                yarray = yarray[::-1]
            xarray, yarray = Mesh.change_scale(xarray, yarray, xRes, yRes, w, h, xoffset, yoffset)
            self.contourTableEntry[i]["contourX"] = xarray
            self.contourTableEntry[i]["contourY"] = yarray
            xmin = min(xarray)
            ymin = min(yarray)
            xmax = max(xarray)
            ymax = max(yarray)
            dpg.set_value("position" + str(entry['id']), "Xmin = " + str(xmin) + "\nYmin = " + str(ymin) + "\nXmax = " + str(xmax) + "\nYmax = " + str(ymax))

        dpg.set_value("currentWidthOffset", 'Current: ' + str(xoffset))
        dpg.set_value("currentHeightOffset", 'Current: ' + str(yoffset))
        dpg.set_value("currentMaxWidth", 'Current: ' + str(w))
        dpg.set_value("currentMaxHeight", 'Current: ' + str(h)) 
        dpg.delete_item("resetContour")
        dpg.add_button(tag="resetContour", width=-1, label="Reset Contour Properties", parent="changeContourParent", callback=self.resetContour)

    def removeContour(self, sender=None, app_data=None):
        self.hideAllContours()
        dpg.delete_item('separator1')
        dpg.delete_item('removeExtractContour')
        dpg.delete_item('ContourExtractionTable')
        dpg.delete_item('toggleDrawContoursButton')
        dpg.delete_item('separator2')
        dpg.delete_item('exportAllContours')
        dpg.delete_item('exportSelectedContours')
        dpg.delete_item('separator3')
        dpg.delete_item('separator4')
        dpg.configure_item('contour_ordering', enabled=False)
        dpg.configure_item('contourExportOption', enabled=False)
        self.contourTableEntry = []
        self.showContourFlag = True
        pass

    def resetContour(self, sender, app_data=None):
        for i in range(len(self.contourTableEntry)):
            entry = self.contourTableEntry[i]
            xarray = [x[0][0] for x in entry["data"]]
            yarray = [x[0][1] for x in entry["data"]]
            self.contourTableEntry[i]["contourX"] = xarray
            self.contourTableEntry[i]["contourY"] = yarray
            xmin = min(xarray)
            ymin = min(yarray)
            xmax = max(xarray)
            ymax = max(yarray)
            dpg.set_value("position" + str(entry['id']), "Xmin = " + str(xmin) + "\nYmin = " + str(ymin) + "\nXmax = " + str(xmax) + "\nYmax = " + str(ymax))
        
        dpg.delete_item("resetContour")
        xRes = int(dpg.get_value("currentWidth")[6:-2])
        yRes = int(dpg.get_value("currentHeight")[7:-2])
        dpg.set_value("currentWidthOffset", 'Current: 0')
        dpg.set_value("currentHeightOffset", 'Current: 0')
        dpg.set_value("currentMaxWidth", 'Current: ' + str(xRes))
        dpg.set_value("currentMaxHeight", 'Current: ' + str(yRes))
        dpg.set_value("maxWidthMapping", xRes)
        dpg.set_value("maxHeightMapping", yRes)
        dpg.set_value("widthOffset", 0)
        dpg.set_value("heightOffset", 0)
        dpg.set_value("matlabModeCheckbox", False)

    def redrawContours(self):
        image = self.imageProcessing.blocks[self.imageProcessing.getLastActiveBeforeMethod('findContour')]['output'].copy()

        thicknessValue = dpg.get_value('contourThicknessSlider')

        for entry in self.contourTableEntry:
            drawContour = dpg.get_value('checkboxContourId' + str(entry['id']))
            if drawContour:
                cv2.drawContours(image, entry['data'], -1, (entry['color'][2], entry['color'][1], entry['color'][0]), thicknessValue)

        self.imageProcessing.blocks[Blocks.findContour.value]['output'] = image
        Texture.updateTexture(self.imageProcessing.blocks[Blocks.findContour.value]['tab'], image)

    def hideAllContours(self, sender = None, app_data = None):
        for entry in self.contourTableEntry:
            dpg.set_value('checkboxContourId' + str(entry['id']), False)
        self.redrawContours()


    def showAllContours(self, sender = None, app_data = None):
        for entry in self.contourTableEntry:
            dpg.set_value('checkboxContourId' + str(entry['id']), True)
        self.redrawContours()

    def selectFolder(self, sender=None, app_data=None):

        self.exportFilePath = app_data['file_path_name']

        self.exportFileName = dpg.get_value('inputContourNameText') + '.txt'
        filePath = os.path.join(self.exportFilePath, self.exportFileName)

        dpg.set_value('exportFileName', 'File Name: ' + self.exportFileName)
        dpg.set_value('exportPathName', 'Complete Path Name: ' + filePath)

        pass

    def openDirectorySelector(self, sender=None, app_data=None):
        if dpg.get_value('inputContourId') != '' and dpg.get_value('inputContourNameText') != '':
            dpg.configure_item('directorySelectorFileDialog', show=True)


    def openExportSelectedDirectorySelector(self, sender=None, app_data=None):
        if dpg.get_value('inputSelectedContourNameText') != '':
            dpg.configure_item('directoryFolderExportSelected', show=True)
        

    def selectExportAllFolder(self, sender=None, app_data=None):
        self.exportSelectPath = app_data['file_path_name']
        self.exportSelectFileName = dpg.get_value('inputSelectedContourNameText')
        filesPath = os.path.join(self.exportSelectPath, self.exportSelectFileName + '-<id>.txt')

        dpg.set_value('exportSelectedFileName', 'File Name: ' + self.exportSelectFileName + '-<id>.txt')
        dpg.set_value('exportSelectedPathName', 'Complete Path Name: ' + filesPath)
        pass

    def exportButtonCall(self, sender, app_data=None):
        auxId = sender[13:]
        dpg.set_value('inputContourNameText', '')
        dpg.set_value('contourIdExportText', 'Contour ID: ' + auxId)
        dpg.set_value('exportFileName', 'File Name: ')
        dpg.set_value('exportPathName', 'Complete Path Name: ')
        self.exportFileName = None
        self.exportFilePath = None
        dpg.configure_item('exportContourWindow', show=True)
        pass

    def exportSelectedButtonCall(self, sender=None, app_data=None):
        dpg.set_value('inputSelectedContourNameText', '')
        dpg.set_value('exportSelectedFileName', 'File Default Name: ')
        dpg.set_value('exportSelectedPathName', 'Complete Path Name: ')

        self.exportSelectPath = None
        self.exportSelectFileName = None

        dpg.configure_item('exportSelectedContourWindow', show=True)
        pass

    def exportSelectedContourToFile(self, sender=None, app_data=None):
        if self.exportSelectPath is None:
            dpg.configure_item("exportSelectedContourError", show=True)
            return

        dpg.configure_item("exportSelectedContourError", show=False)
        selectedContours = []
        for entry in self.contourTableEntry:
            if dpg.get_value('checkboxContourId' + str(entry['id'])) == True:
                selectedContours.append(entry)

        for selectedContour in selectedContours:
            self.exportContourToFile(selectedContour['id'], os.path.join(self.exportSelectPath, self.exportSelectFileName + '_' + str(selectedContour['id'])) + '.txt')
        self.exportFilePath = None
        self.exportFileName = None
        dpg.configure_item('exportSelectedContourWindow', show=False)
        pass

    def exportIndividualContourToFile(self, sender=None, app_data=None):
        if self.exportFilePath is None:
            dpg.configure_item("exportContourError", show=True)
            return

        dpg.configure_item("exportContourError", show=False)
        auxId = int(dpg.get_value("contourIdExportText")[12:])
        self.exportContourToFile(auxId, os.path.join(self.exportFilePath, self.exportFileName))
        dpg.configure_item('exportContourWindow', show=False)
        pass

    def exportContourToFile(self, auxId, path):
        for i in self.contourTableEntry:
            if i["id"] == auxId:
                entry = i
                break
        xarray = entry["contourX"]
        yarray = entry["contourY"]
        if self.toggleMeshImport:
            self.meshGeneration.exportContourOnMesh(xarray, yarray, path)
        else:
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
            Mesh.export_coords_mesh(path, xarray, yarray, nx, ny, xmin, ymin, xmax, ymax, dx, dy, self.meshGeneration.toggleOrderingFlag)
            pass