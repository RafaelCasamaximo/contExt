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
from ..ui import strings

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
        self.exportContourId = None
        self.toggleDrawContoursFlag = True
        self.toggleMeshImport = False
        self.mappingState = {
            "max_width": None,
            "max_height": None,
            "width_offset": 0,
            "height_offset": 0,
        }
        self.interpolation.imageProcessing = self.imageProcessing
        self.interpolation.contourExtraction = self

    def getImageResolution(self):
        return self.imageProcessing.getCurrentResolution()

    def getMappingDimensions(self):
        return self.mappingState["max_width"], self.mappingState["max_height"]

    def resetMappingState(self):
        resolution = self.getImageResolution()
        if resolution is None:
            return
        self.mappingState["max_width"] = resolution[0]
        self.mappingState["max_height"] = resolution[1]
        self.mappingState["width_offset"] = 0
        self.mappingState["height_offset"] = 0
        dpg.configure_item("maxWidthMapping", default_value=resolution[0])
        dpg.configure_item("maxHeightMapping", default_value=resolution[1])
        dpg.set_value("maxWidthMapping", resolution[0])
        dpg.set_value("maxHeightMapping", resolution[1])
        dpg.set_value("widthOffset", 0)
        dpg.set_value("heightOffset", 0)

    def renderMappingState(self):
        max_width = self.mappingState["max_width"]
        max_height = self.mappingState["max_height"]
        width_offset = self.mappingState["width_offset"]
        height_offset = self.mappingState["height_offset"]

        dpg.set_value("currentWidthOffset", strings.fmt("current", value=width_offset if width_offset is not None else "--"))
        dpg.set_value("currentHeightOffset", strings.fmt("current", value=height_offset if height_offset is not None else "--"))
        dpg.set_value("currentMaxWidth", strings.fmt("current", value=max_width if max_width is not None else "--"))
        dpg.set_value("currentMaxHeight", strings.fmt("current", value=max_height if max_height is not None else "--"))

    def renderPosition(self, entry):
        xmin = min(entry["contourX"])
        ymin = min(entry["contourY"])
        xmax = max(entry["contourX"])
        ymax = max(entry["contourY"])
        return strings.fmt("position", xmin=xmin, ymin=ymin, xmax=xmax, ymax=ymax)

    def renderExportState(self):
        contour_id = "" if self.exportContourId is None else self.exportContourId
        export_file_name = self.exportFileName or ""
        export_path_name = ""
        if self.exportFilePath is not None and self.exportFileName is not None:
            export_path_name = os.path.join(self.exportFilePath, self.exportFileName)

        selected_pattern = ""
        selected_path_name = ""
        if self.exportSelectFileName is not None:
            selected_pattern = self.exportSelectFileName + '-<id>.txt'
        if self.exportSelectPath is not None and self.exportSelectFileName is not None:
            selected_path_name = os.path.join(self.exportSelectPath, selected_pattern)

        dpg.set_value("contourIdExportText", strings.fmt("contour_id", value=contour_id))
        dpg.set_value("exportFileName", strings.fmt("file_name", value=export_file_name))
        dpg.set_value("exportPathName", strings.fmt("full_path", value=export_path_name))
        dpg.set_value("exportSelectedFileName", strings.fmt("default_file_name", value=selected_pattern))
        dpg.set_value("exportSelectedPathName", strings.fmt("full_path", value=selected_path_name))

    def renderToggleLabels(self):
        if dpg.does_item_exist('toggleDrawContoursButton'):
            label_key = "contour_extraction.hide_all_contours" if self.toggleDrawContoursFlag else "contour_extraction.show_all_contours"
            dpg.configure_item('toggleDrawContoursButton', label=strings.t(label_key))
        label_key = "common.enable" if self.toggleMeshImport else "common.disable"
        tooltip_key = "contour_extraction.export_mesh_tooltip_disable" if self.toggleMeshImport else "contour_extraction.export_mesh_tooltip_enable"
        dpg.configure_item('contourExportOption', label=strings.t(label_key))
        dpg.set_value("contourExportOptionTooltip", strings.t(tooltip_key))

    def refreshContourTableTranslations(self):
        if not dpg.does_item_exist("ContourExtractionTable"):
            return
        dpg.configure_item("contourTableColumnId", label=strings.t("contour_extraction.table.id"))
        dpg.configure_item("contourTableColumnColor", label=strings.t("contour_extraction.table.color"))
        dpg.configure_item("contourTableColumnVisible", label=strings.t("contour_extraction.table.visible"))
        dpg.configure_item("contourTableColumnSize", label=strings.t("contour_extraction.table.size"))
        dpg.configure_item("contourTableColumnPosition", label=strings.t("contour_extraction.table.position"))
        dpg.configure_item("contourTableColumnMesh", label=strings.t("contour_extraction.table.export_to_mesh_generation"))
        dpg.configure_item("contourTableColumnContour", label=strings.t("contour_extraction.table.export_contour"))
        dpg.configure_item("contourTableColumnInterpolation", label=strings.t("contour_extraction.table.export_to_interpolation"))

        for contourEntry in self.contourTableEntry:
            contour_id = contourEntry['id']
            dpg.configure_item("exportMeshGeneration" + str(contour_id), label=strings.t("contour_extraction.buttons.export_to_mesh_generation"))
            dpg.configure_item("exportContour" + str(contour_id), label=strings.t("contour_extraction.buttons.export_individual_contour"))
            dpg.configure_item("exportInterpolation" + str(contour_id), label=strings.t("contour_extraction.buttons.export_to_interpolation"))
            dpg.set_value("position" + str(contour_id), self.renderPosition(contourEntry))

    def refreshTranslations(self):
        self.renderMappingState()
        self.renderExportState()
        self.renderToggleLabels()
        if dpg.does_item_exist("resetContour"):
            dpg.configure_item("resetContour", label=strings.t("contour_extraction.reset_contour_properties"))
        if dpg.does_item_exist("removeExtractContour"):
            dpg.configure_item("removeExtractContour", label=strings.t("contour_extraction.remove_contour"))
        if dpg.does_item_exist("exportSelectedContours"):
            dpg.configure_item("exportSelectedContours", label=strings.t("contour_extraction.export_selected_contours"))
        self.refreshContourTableTranslations()

    def extractContour(self, sender=None, app_data=None):

        globalThresholdSelectedFlag = dpg.get_value('globalThresholdingCheckbox')
        adaptiveThresholdSelectedFlag = dpg.get_value('adaptiveThresholdingCheckbox')
        adaptiveGaussianThresholdSelectedFlag = dpg.get_value('adaptiveGaussianThresholdingCheckbox')
        otsuBinarizationFlag = dpg.get_value('otsuBinarization')

        if globalThresholdSelectedFlag == False and adaptiveThresholdSelectedFlag == False and adaptiveGaussianThresholdSelectedFlag == False and otsuBinarizationFlag == False:
            dpg.configure_item('nonBinary', show=True)
            return

        image = self.imageProcessing.blocks[self.imageProcessing.getLastActiveBeforeMethod('findContour')]['output'].copy()
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


        approximationMode = None
        value = strings.option_key("approximation_mode", dpg.get_value('approximationModeListbox'))
        if value == 'none':
            approximationMode = cv2.CHAIN_APPROX_NONE
        elif value == 'simple':
            approximationMode = cv2.CHAIN_APPROX_SIMPLE
        elif value == 'tc89_l1':
            approximationMode = cv2.CHAIN_APPROX_TC89_L1
        elif value == 'tc89_kcos':
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
        dpg.add_button(tag='toggleDrawContoursButton', width=-1, label=strings.t("contour_extraction.hide_all_contours"), parent='ContourExtractionParent', callback=self.toggleDrawContours)
        dpg.add_separator(tag='separator2', parent='ContourExtractionParent')
        dpg.add_button(tag='removeExtractContour', width=-1, label=strings.t("contour_extraction.remove_contour"), parent='ContourExtractionParent', callback=self.removeContour)
        dpg.add_separator(tag='separator3', parent='ContourExtractionParent')
        dpg.add_button(tag='exportSelectedContours', width=-1, label=strings.t("contour_extraction.export_selected_contours"), parent='ContourExtractionParent', callback=self.exportSelectedButtonCall)
        dpg.add_separator(tag='separator4', parent='ContourExtractionParent')
        with dpg.table(tag='ContourExtractionTable', header_row=True, policy=dpg.mvTable_SizingFixedFit, row_background=True,
            resizable=True, no_host_extendX=False, hideable=True,
            borders_innerV=True, delay_search=True, borders_outerV=True, borders_innerH=True,
            borders_outerH=True, parent='ContourExtractionParent'):

            dpg.add_table_column(tag="contourTableColumnId", label=strings.t("contour_extraction.table.id"), width_fixed=True)
            dpg.add_table_column(tag="contourTableColumnColor", label=strings.t("contour_extraction.table.color"), width_fixed=True)
            dpg.add_table_column(tag="contourTableColumnVisible", label=strings.t("contour_extraction.table.visible"), width_fixed=True)
            dpg.add_table_column(tag="contourTableColumnSize", label=strings.t("contour_extraction.table.size"), width_fixed=True)
            dpg.add_table_column(tag="contourTableColumnPosition", label=strings.t("contour_extraction.table.position"), width_fixed=True)
            dpg.add_table_column(tag="contourTableColumnMesh", label=strings.t("contour_extraction.table.export_to_mesh_generation"), width_fixed=True)
            dpg.add_table_column(tag="contourTableColumnContour", label=strings.t("contour_extraction.table.export_contour"), width_fixed=True)
            dpg.add_table_column(tag="contourTableColumnInterpolation", label=strings.t("contour_extraction.table.export_to_interpolation"), width_fixed=True)


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
                            dpg.add_text(self.renderPosition(contourEntry), tag="position" + str(contourEntry['id']))
                        if j == 5:
                            dpg.add_button(label=strings.t("contour_extraction.buttons.export_to_mesh_generation"), width=-1, tag="exportMeshGeneration" + str(contourEntry['id']), callback=self.exportToMeshGeneration)
                        if j == 6:
                            dpg.add_button(label=strings.t("contour_extraction.buttons.export_individual_contour"), tag="exportContour" + str(contourEntry['id']), callback=self.exportButtonCall)
                        if j == 7:
                            dpg.add_button(label=strings.t("contour_extraction.buttons.export_to_interpolation"), tag="exportInterpolation" + str(contourEntry['id']), callback=self.exportToInterpolation)

        self.imageProcessing.blocks[Blocks.findContour.value]['output'] = image
        Texture.updateTexture(self.imageProcessing.blocks[Blocks.findContour.value]['tab'], image)

        dpg.configure_item('contour_ordering', enabled=True)
        dpg.configure_item('contourExportOption', enabled=True)
        self.resetMappingState()
        self.renderMappingState()

    def toggleDrawContours(self, sender = None, app_data = None):
        self.toggleDrawContoursFlag = not self.toggleDrawContoursFlag
        if self.toggleDrawContoursFlag:
            self.showAllContours()
        else:
            self.hideAllContours()
        self.renderToggleLabels()
        pass

    def toggleExportOnMesh(self, sender = None, app_data = None):
        self.toggleMeshImport = not self.toggleMeshImport
        self.renderToggleLabels()
        pass
    
    def exportToMeshGeneration(self, sender, app_data=None):
        auxId = int(sender[20:])
        for i in self.contourTableEntry:
            if i["id"] == auxId:
                entry = i
                break
        xarray = entry["contourX"]
        yarray = entry["contourY"]
        current_resolution = self.getImageResolution()
        xRes = current_resolution[0]
        yRes = current_resolution[1]
        w, h = self.getMappingDimensions()
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
        current_resolution = self.getImageResolution()
        xRes = current_resolution[0]
        yRes = current_resolution[1]
        xoffset = float(dpg.get_value("widthOffset"))
        yoffset = float(dpg.get_value("heightOffset"))
        w = float(dpg.get_value("maxWidthMapping"))
        h = float(dpg.get_value("maxHeightMapping"))
        matlabFlag = dpg.get_value("matlabModeCheckbox")
        self.mappingState["width_offset"] = xoffset
        self.mappingState["height_offset"] = yoffset
        self.mappingState["max_width"] = w
        self.mappingState["max_height"] = h

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
            dpg.set_value("position" + str(entry['id']), self.renderPosition(self.contourTableEntry[i]))

        self.renderMappingState()
        if dpg.does_item_exist("resetContour"):
            dpg.delete_item("resetContour")
        dpg.add_button(tag="resetContour", width=-1, label=strings.t("contour_extraction.reset_contour_properties"), parent="changeContourParent", callback=self.resetContour)

    def removeContour(self, sender=None, app_data=None):
        self.hideAllContours()
        for item in (
            'separator1',
            'removeExtractContour',
            'ContourExtractionTable',
            'toggleDrawContoursButton',
            'separator2',
            'exportAllContours',
            'exportSelectedContours',
            'separator3',
            'separator4',
        ):
            if dpg.does_item_exist(item):
                dpg.delete_item(item)
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
            dpg.set_value("position" + str(entry['id']), self.renderPosition(self.contourTableEntry[i]))
        
        if dpg.does_item_exist("resetContour"):
            dpg.delete_item("resetContour")
        self.resetMappingState()
        self.renderMappingState()
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
        self.renderExportState()

        pass

    def openDirectorySelector(self, sender=None, app_data=None):
        if self.exportContourId is not None and dpg.get_value('inputContourNameText') != '':
            dpg.configure_item('directorySelectorFileDialog', show=True)


    def openExportSelectedDirectorySelector(self, sender=None, app_data=None):
        if dpg.get_value('inputSelectedContourNameText') != '':
            dpg.configure_item('directoryFolderExportSelected', show=True)
        

    def selectExportAllFolder(self, sender=None, app_data=None):
        self.exportSelectPath = app_data['file_path_name']
        self.exportSelectFileName = dpg.get_value('inputSelectedContourNameText')
        self.renderExportState()
        pass

    def exportButtonCall(self, sender, app_data=None):
        auxId = sender[13:]
        dpg.set_value('inputContourNameText', '')
        self.exportContourId = int(auxId)
        self.exportFileName = None
        self.exportFilePath = None
        self.renderExportState()
        dpg.configure_item('exportContourWindow', show=True)
        pass

    def exportSelectedButtonCall(self, sender=None, app_data=None):
        dpg.set_value('inputSelectedContourNameText', '')

        self.exportSelectPath = None
        self.exportSelectFileName = None
        self.renderExportState()

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
        auxId = self.exportContourId
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
            current_resolution = self.getImageResolution()
            xRes = current_resolution[0]
            yRes = current_resolution[1]
            w, h = self.getMappingDimensions()
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
