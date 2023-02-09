# -*- coding: utf-8 -*-
import dearpygui.dearpygui as dpg
import numpy as np
import cv2
import enum
from mesh import Mesh
from sparseMesh import SparseMesh
import random
import os.path

class Tabs(enum.Enum):
    __order__ = 'Processing Filtering Thresholding ContourExtraction'
    Processing = 0
    Filtering = 1
    Thresholding = 2
    ContourExtraction = 3

class Blocks(enum.Enum):
    __order__ = 'importImage crop histogramEqualization brightnessAndContrast averageBlur gaussianBlur medianBlur grayscale globalThresholding adaptativeMeanThresholding adaptativeGaussianThresholding otsuBinarization findContour'
    importImage = 0
    crop = 1
    histogramEqualization = 2
    brightnessAndContrast = 3
    averageBlur = 4
    gaussianBlur = 5
    medianBlur = 6
    grayscale = 7
    globalThresholding = 8
    adaptativeMeanThresholding = 9
    adaptativeGaussianThresholding = 10
    otsuBinarization = 11
    findContour = 12

class Callbacks:
    def __init__(self) -> None:

        self.filePath = None
        self.fileName = None
        self.txtFilePath = None
        self.txtFileName = None
        self.toggleOrderingFlag = True
        self.toggleZoomFlag = True
        self.toggleGridFlag = False
        self.sparseMeshHandler = None
        self.countGrid = 0
        self.originalX = []
        self.originalY = []
        self.currentX = []
        self.currentY = []
        self.contourTableEntry = []
        self.exportFilePath = None
        self.exportFileName = None
        self.exportSelectPath = None
        self.exportSelectFileName = None
        self.exportImageFilePath = None
        self.currentTab = None

        self.blocks = [
            {
                'method': self.importImage,
                'name': self.importImage.__name__,
                'status': True,
                'output': None,
                'tab': 'Processing'
            },
            {
                'method': self.crop,
                'name': self.crop.__name__,
                'status': False,
                'output': None,
                'tab': 'Processing'
            },
            {
                'method': self.histogramEqualization,
                'name': self.histogramEqualization.__name__,
                'status': False,
                'output': None,
                'tab': 'Filtering'
            },
            {
                'method': self.brightnessAndContrast,
                'name': self.brightnessAndContrast.__name__,
                'status': False,
                'output': None,
                'tab': 'Filtering'
            },
            {
                'method': self.averageBlur,
                'name': self.averageBlur.__name__,
                'status': False,
                'output': None,
                'tab': 'Filtering'
            },
            {
                'method': self.gaussianBlur,
                'name': self.gaussianBlur.__name__,
                'status': False,
                'output': None,
                'tab': 'Filtering'
            },
            {
                'method': self.medianBlur,
                'name': self.medianBlur.__name__,
                'status': False,
                'output': None,
                'tab': 'Filtering'
            },
            {
                'method': self.grayscale,
                'name': self.grayscale.__name__,
                'status': True,
                'output': None,
                'tab': 'Thresholding'
            },
            {
                'method': self.globalThresholding,
                'name': self.globalThresholding.__name__,
                'status': False,
                'output': None,
                'tab': 'Thresholding'
            },
            {
                'method': self.adaptativeMeanThresholding,
                'name': self.adaptativeMeanThresholding.__name__,
                'status': False,
                'output': None,
                'tab': 'Thresholding'
            },
            {
                'method': self.adaptativeGaussianThresholding,
                'name': self.adaptativeGaussianThresholding.__name__,
                'status': False,
                'output': None,
                'tab': 'Thresholding'
            },
            {
                'method': self.otsuBinarization,
                'name': self.otsuBinarization.__name__,
                'status': False,
                'output': None,
                'tab': 'Thresholding'
            },
            {
                'method': self.findContour,
                'name': self.findContour.__name__,
                'status': True,
                'output': None,
                'tab': 'ContourExtraction'
            },
        ]

        pass


    def executeQuery(self, methodName):
        executeFlag = 0
        for entry in self.blocks:
            if executeFlag == 0 and entry['name'] == methodName:
                executeFlag = 1
            if executeFlag == 1 and entry['status'] is True:
                entry['method']()
        pass

    def executeQueryFromNext(self, methodName):
        executeFlag = 0
        for entry in self.blocks:
            if executeFlag == 0 and entry['name'] == methodName:
                executeFlag = 1
                continue
            if executeFlag == 1 and entry['status'] is True:
                entry['method']()
        pass

    def toggleAndExecuteQuery(self, methodName, sender = None, app_data = None):
        self.toggleEffect(methodName, sender, app_data)
        if dpg.get_value(sender) is True:
            self.executeQuery(methodName)
        else:
            self.retrieveFromLastActive(methodName, sender, app_data)
            self.executeQueryFromNext(methodName)
        pass

    def getIdByMethod(self, methodName):
        id = 0
        for entry in self.blocks:
            if entry['name'] == methodName:
                return id
            id += 1

    def retrieveFromLastActive(self, methodName, sender = None, app_data = None):
        self.blocks[self.getIdByMethod(methodName)]['output'] = self.blocks[self.getLastActiveBeforeMethod(methodName)]['output']
        self.updateTexture(self.blocks[self.getIdByMethod(methodName)]['tab'], self.blocks[self.getIdByMethod(methodName)]['output'])

    def getLastActiveBeforeMethod(self, methodName):
        lastActiveIndex = 0
        lastActive = 0
        for entry in self.blocks:
            if entry['name'] == methodName:
                break
            if entry['status'] is True:
                lastActiveIndex = lastActive 
            lastActive += 1
        return lastActiveIndex

    def openImage(self, filePath):
        stream = open(filePath, "rb")
        bytes = bytearray(stream.read())
        numpyarray = np.asarray(bytes, dtype=np.uint8)
        bgrImage = cv2.imdecode(numpyarray, cv2.IMREAD_COLOR)
        return bgrImage

    def openFile(self, sender = None, app_data = None):
        self.filePath = app_data['file_path_name']
        self.fileName = app_data['file_name']

        if os.path.isfile(self.filePath) is False:
            dpg.configure_item('noPath', show=True)
            return

        self.executeQuery('importImage')
        self.enableAllTags()
        pass

    def createTexture(self, textureTag, textureImage):
        self.deleteTexture(textureTag)
        height = textureImage.shape[0]
        width = textureImage.shape[1]
        textureData = self.textureToData(textureImage)
        dpg.add_dynamic_texture(width=width, height=height, default_value=textureData, tag=textureTag, parent='textureRegistry')
        dpg.add_image(textureTag, parent=textureTag + 'Parent', tag=textureTag + 'Image')
        pass

    def deleteTexture(self, textureTag):
        try:
            dpg.delete_item(textureTag)
            dpg.delete_item(textureTag + 'Image')
        except:
            pass
        pass

    def updateTexture(self, textureTag, textureImage):
        textureData = self.textureToData(textureImage)
        dpg.set_value(textureTag, textureData)
        pass

    def createAllTextures(self, textureImage):
        for tab in Tabs:
            self.createTexture(tab.name, textureImage)

    def deleteAllTextures(self):
        for tab in Tabs:
            self.deleteTexture(tab.name)
        pass

    def updateAllTextures(self, textureImage):
        for tab in Tabs:
            self.updateTexture(tab.name, textureImage)
        pass

    def textureToData(self, texture):
        auxImg = cv2.cvtColor(texture, cv2.COLOR_RGB2BGRA)
        auxImg = np.asfarray(auxImg, dtype='f')
        auxImg = auxImg.ravel()
        auxImg = np.true_divide(auxImg, 255.0)
        return auxImg

    def toggleEffect(self, methodName, sender = None, app_data = None):
        for entry in self.blocks:
            if entry['name'] == methodName:
                entry['status'] = dpg.get_value(sender)
        pass

    def disableAllTags(self):
        checkboxes = [
            'cropCheckbox',
            'histogramCheckbox',
            'brightnessAndContrastCheckbox',
            'averageBlurCheckbox',
            'gaussianBlurCheckbox',
            'medianBlurCheckbox',
            'excludeBlueChannel',
            'excludeGreenChannel',
            'excludeRedChannel',
            'globalThresholdingCheckbox',
            'invertGlobalThresholding',
            'adaptativeThresholdingCheckbox',
            'adaptativeGaussianThresholdingCheckbox',
            'otsuBinarization',
            'matlabModeCheckbox',
            'extractContourButton',
            'updtadeContourButton',
            'exportImageAsFileProcessing',
            'exportImageAsFileFiltering',
            'exportImageAsFileThresholding'
        ]
        for checkbox in checkboxes:
            dpg.configure_item(checkbox, enabled=False)
        pass

    def enableAllTags(self):
        checkboxes = [
            'cropCheckbox',
            'histogramCheckbox',
            'brightnessAndContrastCheckbox',
            'averageBlurCheckbox',
            'gaussianBlurCheckbox',
            'medianBlurCheckbox',
            'excludeBlueChannel',
            'excludeGreenChannel',
            'excludeRedChannel',
            'globalThresholdingCheckbox',
            'invertGlobalThresholding',
            'adaptativeThresholdingCheckbox',
            'adaptativeGaussianThresholdingCheckbox',
            'otsuBinarization',
            'matlabModeCheckbox',
            'extractContourButton',
            'updtadeContourButton',
            'exportImageAsFileProcessing',
            'exportImageAsFileFiltering',
            'exportImageAsFileThresholding'
        ]
        for checkbox in checkboxes:
            dpg.configure_item(checkbox, enabled=True)
        pass

    def exportImage(self, sender = None, app_data = None, tab = None):

        dpg.set_value('exportImageFileName', 'File Name: ')
        dpg.set_value('exportImageFilePath', 'Complete Path Name: ')
        dpg.set_value('imageNameExportAsFile', '')
        self.exportImageFilePath = None
        self.currentTab = tab
        dpg.configure_item('exportImageAsFile', show=True)
        pass

    def exportImageDirectorySelector(self, sender = None, app_data = None):
        imageName = dpg.get_value('imageNameExportAsFile')
        if imageName == '':
            return
        dpg.configure_item('exportImageAsFile', show=True)
        dpg.configure_item('exportImageDirectorySelector', show=True)
        pass

    def exportImageSelectDirectory(self, sender = None, app_data = None):
        exportImageFileName = dpg.get_value('imageNameExportAsFile')
        exportImageFilePath = app_data['file_path_name']
        self.exportImageFilePath = os.path.join(exportImageFilePath, exportImageFileName + '.jpg')
        dpg.set_value('exportImageFileName', 'File Name: ' + exportImageFileName + '.jpg')
        dpg.set_value('exportImageFilePath', 'File Path: ' + self.exportImageFilePath)
        pass

    def exportImageAsFile(self, sender = None, app_data = None):
        if self.exportImageFilePath is None:
            dpg.configure_item("exportImageError", show=True)
            return

        dpg.configure_item("exportImageError", show=False)

        lastTabIndex = {
            'Processing': Blocks.histogramEqualization.name,
            'Filtering': Blocks.grayscale.name,
            'Thresholding': Blocks.findContour.name,
        }
        path = self.exportImageFilePath
        image = self.blocks[self.getLastActiveBeforeMethod(lastTabIndex[self.currentTab])]['output']
        cv2.imwrite(path, image)
        dpg.configure_item('exportImageAsFile', show=False)

    def importImage(self, sender = None, app_data = None):
        # Cria imagem na aba
        dpg.hide_item('import_image')
        self.blocks[Blocks.importImage.value]['output'] = self.openImage(self.filePath)

        self.createAllTextures(self.blocks[Blocks.importImage.value]['output'])

        # Popula os dados na lateral
        dpg.set_value('file_name_text', 'File Name: ' + self.fileName)
        dpg.set_value('file_path_text', 'File Path: ' + self.filePath)

        shape = self.blocks[Blocks.importImage.value]['output'].shape

        dpg.set_value('originalWidth', 'Width: ' + str(shape[1]) + 'px')
        dpg.set_value('originalHeight', 'Height: ' + str(shape[0]) + 'px')
        dpg.set_value('currentWidth', 'Width: ' + str(shape[1]) + 'px')
        dpg.set_value('currentHeight', 'Height: ' + str(shape[0]) + 'px')

        dpg.set_value('endX', shape[0])
        dpg.set_value('endY', shape[1])
        dpg.configure_item("exportImageAsFileProcessingGroup", show=True)
        dpg.configure_item("exportImageAsFileFilteringGroup", show=True)
        dpg.configure_item("exportImageAsFileThresholdingGroup", show=True)
        pass


    def resetCrop(self, sender = None, app_data = None):

        if self.blocks[Blocks.importImage.value]['output'] is None:
            dpg.configure_item('noImage', show=True)
            dpg.set_value('cropCheckbox', False)
            self.blocks[Blocks.crop.value]['status'] = False
            return

        self.blocks[Blocks.crop.value]['output'] = self.blocks[Blocks.importImage.value]['output']

        shape = self.blocks[Blocks.crop.value]['output'].shape

        dpg.set_value('currentWidth', 'Width: ' + str(shape[1]) + 'px')
        dpg.set_value('currentHeight', 'Height: ' + str(shape[0]) + 'px')
        dpg.set_value('endX', shape[0])
        dpg.set_value('endY', shape[1])

        self.createAllTextures(self.blocks[Blocks.importImage.value]['output'])

        pass

    def crop(self, sender=None, app_data=None):
        startX = dpg.get_value('startX')
        endX = dpg.get_value('endX')
        startY = dpg.get_value('startY')
        endY = dpg.get_value('endY')

        if startX >= endX or startY >= endY:
            dpg.configure_item('incorrectCrop', show=True)
            dpg.set_value('cropCheckbox', False)
            self.blocks[Blocks.crop.value]['status'] = False
            return

        if self.blocks[Blocks.importImage.value]['output'] is None:
            dpg.configure_item('noImage', show=True)
            dpg.set_value('cropCheckbox', False)
            self.blocks[Blocks.crop.value]['status'] = False
            return

        self.blocks[Blocks.crop.value]['output'] = self.blocks[Blocks.importImage.value]['output'][startX:endX, startY:endY]

        shape = self.blocks[Blocks.crop.value]['output'].shape

        dpg.set_value('currentWidth', 'Width: ' + str(shape[1]) + 'px')
        dpg.set_value('currentHeight', 'Height: ' + str(shape[0]) + 'px')

        dpg.set_value('endX', shape[0])
        dpg.set_value('endY', shape[1])

        self.createAllTextures(self.blocks[Blocks.crop.value]['output'])
        pass

    def histogramEqualization(self, sender=None, app_data=None):

        img_yuv = cv2.cvtColor(self.blocks[self.getLastActiveBeforeMethod('histogramEqualization')]['output'], cv2.COLOR_BGR2YUV)
        img_yuv[:,:,0] = cv2.equalizeHist(img_yuv[:,:,0])
        dst = cv2.cvtColor(img_yuv, cv2.COLOR_YUV2BGR)
        self.blocks[Blocks.histogramEqualization.value]['output'] = dst
        self.updateTexture(self.blocks[Blocks.histogramEqualization.value]['tab'], dst)
        pass

    def brightnessAndContrast(self, sender=None, app_data=None):

        image = self.blocks[self.getLastActiveBeforeMethod('brightnessAndContrast')]['output']
        alpha = dpg.get_value('contrastSlider')
        beta = dpg.get_value('brightnessSlider')
        outputImage = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)

        self.blocks[Blocks.brightnessAndContrast.value]['output'] = outputImage
        self.updateTexture(self.blocks[Blocks.brightnessAndContrast.value]['tab'], outputImage)
        pass

    def averageBlur(self, sender=None, app_data=None):
        image = self.blocks[self.getLastActiveBeforeMethod('averageBlur')]['output']

        kernelSize = (2 * dpg.get_value('averageBlurSlider')) - 1
        kernel = np.ones((kernelSize,kernelSize),np.float32)/(kernelSize*kernelSize)
        dst = cv2.filter2D(image,-1,kernel)

        self.blocks[Blocks.averageBlur.value]['output'] = dst
        self.updateTexture(self.blocks[Blocks.averageBlur.value]['tab'], dst)
        pass

    def gaussianBlur(self, sender=None, app_data=None):
        image = self.blocks[self.getLastActiveBeforeMethod('gaussianBlur')]['output']

        kernelSize = (2 * dpg.get_value('gaussianBlurSlider')) - 1
        dst = cv2.GaussianBlur(image, (kernelSize,kernelSize), 0)

        self.blocks[Blocks.gaussianBlur.value]['output'] = dst
        self.updateTexture(self.blocks[Blocks.gaussianBlur.value]['tab'], dst)
        pass

    def medianBlur(self, sender=None, app_data=None):
        image = self.blocks[self.getLastActiveBeforeMethod('medianBlur')]['output']
        kernel = (2 * dpg.get_value('medianBlurSlider')) - 1

        median = cv2.medianBlur(image, kernel)

        self.blocks[Blocks.medianBlur.value]['output'] = median
        self.updateTexture(self.blocks[Blocks.medianBlur.value]['tab'], median)
        pass

    def grayscale(self, sender=None, app_data=None):

        if self.blocks[self.getLastActiveBeforeMethod('grayscale')]['output'] is None:
            return

        image = self.blocks[self.getLastActiveBeforeMethod('grayscale')]['output'].copy()


        excludeBlue = dpg.get_value('excludeBlueChannel')
        excludeGreen = dpg.get_value('excludeGreenChannel')
        excludeRed = dpg.get_value('excludeRedChannel')

        if excludeBlue:
            image[:, :, 0] = 0
        if excludeGreen:
            image[:, :, 1] = 0
        if excludeRed:
            image[:, :, 2] = 0

        grayMask = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        image[:, :, 0] = grayMask
        image[:, :, 1] = grayMask
        image[:, :, 2] = grayMask

        self.blocks[Blocks.grayscale.value]['output'] = image
        self.updateTexture(self.blocks[Blocks.grayscale.value]['tab'], image)
        pass

    def globalThresholding(self, sender=None, app_data=None):
        image = self.blocks[Blocks.grayscale.value]['output'].copy()
        threshold = dpg.get_value('globalThresholdSlider')

        thresholdMode = cv2.THRESH_BINARY 
        invertFlag = dpg.get_value('invertGlobalThresholding')
        if invertFlag:
            thresholdMode = cv2.THRESH_BINARY_INV

        (T, threshInv) = cv2.threshold(image, threshold, 255, thresholdMode)

        self.blocks[Blocks.globalThresholding.value]['output'] = threshInv
        self.updateTexture(self.blocks[Blocks.globalThresholding.value]['tab'], threshInv)
        pass

    def adaptativeMeanThresholding(self, sender=None, app_data=None):
        image = self.blocks[self.getLastActiveBeforeMethod('adaptativeMeanThresholding')]['output'].copy()

        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        threshInv = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY,11,2)
        image = cv2.cvtColor(threshInv, cv2.COLOR_GRAY2BGR)

        self.blocks[Blocks.adaptativeMeanThresholding.value]['output'] = image
        self.updateTexture(self.blocks[Blocks.adaptativeMeanThresholding.value]['tab'], image)

        pass

    def adaptativeGaussianThresholding(self, sender=None, app_data=None):

        image = self.blocks[self.getLastActiveBeforeMethod('adaptativeGaussianThresholding')]['output'].copy()

        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        threshInv = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY,11,2)
        image = cv2.cvtColor(threshInv, cv2.COLOR_GRAY2BGR)

        self.blocks[Blocks.adaptativeGaussianThresholding.value]['output'] = image
        self.updateTexture(self.blocks[Blocks.adaptativeGaussianThresholding.value]['tab'], image)

        pass

    def otsuBinarization(self, sender=None, app_data=None):
        image = self.blocks[self.getLastActiveBeforeMethod('adaptativeGaussianThresholding')]['output'].copy()
        
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        ret, threshInv = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        threshInv = cv2.cvtColor(threshInv, cv2.COLOR_GRAY2BGR)


        self.blocks[Blocks.otsuBinarization.value]['output'] = threshInv
        self.updateTexture(self.blocks[Blocks.otsuBinarization.value]['tab'], threshInv)
        pass

    def findContour(self, sender=None, app_data=None):

        if self.blocks[self.getLastActiveBeforeMethod('findContour')]['output'] is None:
            return

        image = self.blocks[self.getLastActiveBeforeMethod('findContour')]['output'].copy()
        self.updateTexture(self.blocks[Blocks.findContour.value]['tab'], image)
        pass

    def extractContour(self, sender=None, app_data=None):

        globalThresholdSelectedFlag = dpg.get_value('globalThresholdingCheckbox')
        adaptativeThresholdSelectedFlag = dpg.get_value('adaptativeThresholdingCheckbox')
        adaptativeGaussianThresholdSelectedFlag = dpg.get_value('adaptativeGaussianThresholdingCheckbox')
        otsuBinarizationFlag = dpg.get_value('otsuBinarization')

        if globalThresholdSelectedFlag == False and adaptativeThresholdSelectedFlag == False and adaptativeGaussianThresholdSelectedFlag == False and otsuBinarizationFlag == False:
            dpg.configure_item('nonBinary', show=True)
            return

        image = self.blocks[self.getLastActiveBeforeMethod('findContour')]['output'].copy()
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

        self.contourTableEntry = []

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

        try:
            dpg.delete_item('ContourExtractionTable')
            dpg.delete_item('showAllContoursButton')
            dpg.delete_item('hideAllContoursButton')
            dpg.delete_item('separator1')
            dpg.delete_item('exportAllContours')
            dpg.delete_item('exportSelectedContours')
            dpg.delete_item('separator2')
        except:
            pass

        dpg.add_button(tag='showAllContoursButton', label='Show All Contours', parent='ContourExtractionParent', callback=lambda sender, app_data: self.showAllContours())
        dpg.add_button(tag='hideAllContoursButton', label='Hide All Contours', parent='ContourExtractionParent', callback=lambda sender, app_data: self.hideAllContours())
        dpg.add_separator(tag='separator1', parent='ContourExtractionParent')
        dpg.add_button(tag='exportSelectedContours', label='Export Selected Contours as Files', parent='ContourExtractionParent', callback=self.exportSelectedButtonCall)
        dpg.add_separator(tag='separator2', parent='ContourExtractionParent')
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


            for contourEntry in self.contourTableEntry:
                with dpg.table_row():
                    for j in range(7):
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
                            dpg.add_button(label='Export to Mesh Generation', tag="exportMeshGeneration" + str(contourEntry['id']), callback=self.exportToMeshGeneration)
                        if j == 6:
                            dpg.add_button(label='Export Individual Contour', tag="exportContour" + str(contourEntry['id']), callback=self.exportButtonCall)

        self.blocks[Blocks.findContour.value]['output'] = image
        self.updateTexture(self.blocks[Blocks.findContour.value]['tab'], image)

        dpg.configure_item('contour_ordering', enabled=True)
        xRes = int(dpg.get_value("currentWidth")[6:-2])
        yRes = int(dpg.get_value("currentHeight")[7:-2])
        dpg.set_value("currentWidthOffset", 'Current: 0')
        dpg.set_value("currentHeightOffset", 'Current: 0')
        dpg.set_value("currentMaxWidth", 'Current: ' + str(xRes))
        dpg.set_value("currentMaxHeight", 'Current: ' + str(yRes))
        dpg.configure_item("maxWidthMapping", default_value = xRes)
        dpg.configure_item("maxHeightMapping", default_value = yRes)

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
        self.originalX = [nx, xmin, xmax, dx] + xarray
        self.originalY = [ny, ymin, ymax, dy] + yarray
        self.importContour()
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
        dpg.add_button(tag="resetContour", label="Reset Contour Properties", parent="changeContourParent", callback=self.resetContour)

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
        image = self.blocks[self.getLastActiveBeforeMethod('findContour')]['output'].copy()

        thicknessValue = dpg.get_value('contourThicknessSlider')

        for entry in self.contourTableEntry:
            drawContour = dpg.get_value('checkboxContourId' + str(entry['id']))
            if drawContour:
                cv2.drawContours(image, entry['data'], -1, (entry['color'][2], entry['color'][1], entry['color'][0]), thicknessValue)

        self.blocks[Blocks.findContour.value]['output'] = image
        self.updateTexture(self.blocks[Blocks.findContour.value]['tab'], image)

    def hideAllContours(self):
        for entry in self.contourTableEntry:
            dpg.set_value('checkboxContourId' + str(entry['id']), False)
        self.redrawContours()


    def showAllContours(self):
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
        xRes = int(dpg.get_value("currentWidth")[6:-2])
        yRes = int(dpg.get_value("currentHeight")[7:-2])
        w = int(dpg.get_value("currentMaxWidth")[9:])
        h = int(dpg.get_value("currentMaxHeight")[9:])
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
        Mesh.export_coords_mesh(path, xarray, yarray, nx, ny, xmin, ymin, xmax, ymax, dx, dy, self.toggleOrderingFlag)
        pass

    def openContourFile(self, sender = None, app_data = None):
        self.txtFilePath = app_data['file_path_name']
        self.txtFileName = app_data['file_name']
        
        dpg.set_value('contour_file_name_text', 'File Name: ' + self.txtFileName)
        dpg.set_value('contour_file_path_text', 'File Path: ' + self.txtFilePath)

        self.originalX = []
        self.originalY = []
        f = open(self.txtFilePath,'r')
        for line in f.readlines():
            aux = line.split()
            if(len(aux) != 2):
                print("File doesn't contain a valid contour")
                dpg.configure_item("txtFileErrorPopup", show=True)
                return
            try:
                self.originalX.append(float(aux[0]))
                self.originalY.append(float(aux[1]))
            except:
                print("File doesn't contain a valid contour")
                dpg.configure_item("txtFileErrorPopup", show=True)
                return
        if not self.toggleOrderingFlag:
            self.originalX = self.originalX[:4] + self.originalX[4::-1]
            self.originalY = self.originalY[:4] + self.originalY[4::-1]
        f.close()
        self.importContour()
        
    def importContour(self, sender = None, app_data = None):
        if self.toggleGridFlag:
            self.removeGrid()
        dpg.delete_item("meshPlot")
        dpg.delete_item("originalMeshPlot")
        dpg.configure_item('contour_ordering2', enabled=True)
        dpg.configure_item('sparseButton', enabled=True)
        dpg.configure_item('plotGrid', enabled=True)

        self.currentX = self.originalX
        self.currentY = self.originalY
        self.originalX = self.originalX[4:]
        self.originalY = self.originalY[4:]

        nx = self.currentX[0]
        ny = self.currentY[0]
        xmin = self.currentX[1]
        ymin = self.currentY[1]
        xmax = self.currentX[2]
        ymax = self.currentY[2]
        dx = self.currentX[3]
        dy = self.currentY[3]

        dpg.set_value("original_xi", 'x: ' + str(xmin))
        dpg.set_value("original_yi", 'y: ' + str(ymin))
        dpg.set_value("original_dx", 'dx: ' + str(dx))
        dpg.set_value("original_dy", 'dy: ' + str(dy))
        dpg.set_value("original_nx", 'nx: ' + str(int(nx)))
        dpg.set_value("original_ny", 'ny: ' + str(int(ny)))
        dpg.set_value("nx", 'nx: ' + str(int(nx)))
        dpg.set_value("ny", 'ny: ' + str(int(ny)))
        dpg.configure_item("dx", default_value = dx, min_value = dx)
        dpg.configure_item("dy", default_value = dy, min_value = dy)
        dpg.configure_item("xi", default_value = xmin)
        dpg.configure_item("yi", default_value = ymin)
        dpg.configure_item("xi_zoom", default_value = xmin, min_value = xmin)
        dpg.configure_item("yi_zoom", default_value = ymin, min_value = ymin)
        dpg.configure_item("xf_zoom", default_value = xmin + dx, min_value = xmin + dx, max_value = xmax)
        dpg.configure_item("yf_zoom", default_value = ymin + dy, min_value = ymin + dy, max_value = ymax)
        dpg.configure_item("exportMesh", enabled=True)

        self.currentX = self.currentX[4:]
        self.currentY = self.currentY[4:]
        dpg.set_value("original_area", "Original Area: " + str(Mesh.get_area(self.currentX, self.currentY)))
        dpg.add_line_series(self.currentX, self.currentY, label="Original Mesh", tag="originalMeshPlot", parent='y_axis')
        dpg.fit_axis_data("x_axis")
        dpg.fit_axis_data("y_axis")     

    def toggleOrdering(self, sender = None, app_data = None):
        self.toggleOrderingFlag = not self.toggleOrderingFlag
        if self.toggleOrderingFlag:
            dpg.configure_item('contour_ordering', label="Anticlockwise")
            dpg.configure_item('contour_ordering2', label="Anticlockwise")
        else:
            dpg.configure_item('contour_ordering', label="Clockwise")
            dpg.configure_item('contour_ordering2', label="Clockwise")
        pass

    def toggleZoom(self, sender = None, app_data = None):
        self.toggleZoomFlag = not self.toggleZoomFlag
        if self.toggleZoomFlag:
            dpg.configure_item('meshZoomType', label="Sparse")
        else:
            dpg.configure_item('meshZoomType', label="Adaptative")
        pass

    def addZoomRegion(self, sender = None, app_data = None):
        listBoxValue = dpg.get_value("dxListbox")
        n = int(listBoxValue[11:])
        name = dpg.get_value("zoomRegionName")
        dx = dpg.get_value("dx")
        dy = dpg.get_value("dy")
        xmin = dpg.get_value("xi_zoom")
        ymin = dpg.get_value("yi_zoom")
        xmax = dpg.get_value("xf_zoom")
        ymax = dpg.get_value("yf_zoom")

        if self.sparseMeshHandler == None:
            self.sparseMeshHandler = SparseMesh()
            self.sparseMeshHandler.addRange(dpg.get_value("xi"), dpg.get_value("yi"), max(self.originalX), max(self.originalY), dx, dy)
        if not self.sparseMeshHandler.addRange(xmin, ymin, xmax, ymax, n, n):
            dpg.configure_item("addZoomError", show=True)
            return

        dpg.configure_item("addZoomError", show=False)
        nZoom = len(self.sparseMeshHandler.ranges) - 1
        dpg.add_separator(tag="separatorZoomStart" + str(nZoom), parent="sparseGroup")
        dpg.add_text(name, tag="zoomTxt" + str(nZoom), parent="sparseGroup")
        dpg.add_text("Node Size: " + listBoxValue, tag="listBoxZoom" + str(nZoom), parent="sparseGroup")
        dpg.add_text("Bottom x: " + str(xmin), tag="xminZoom" + str(nZoom), parent="sparseGroup")
        dpg.add_text("Bottom y: " + str(xmin), tag="yminZoom" + str(nZoom), parent="sparseGroup")
        dpg.add_text("Top x: " + str(xmin), tag="xmaxZoom" + str(nZoom), parent="sparseGroup")
        dpg.add_text("Top x: " + str(xmin), tag="ymaxZoom" + str(nZoom), parent="sparseGroup")
        dpg.add_button(tag="removeZoom" + str(nZoom), label="Remove Zoom Region", parent="sparseGroup", callback=self.removeZoomRegion)

        if nZoom == 2:
            dpg.configure_item("resetMesh", show=True)
        dpg.configure_item("sparsePopup", show=False)
        dpg.configure_item("meshZoomType", enabled=False)
        dpg.set_value("meshZoomTypeTooltip", "You cannot add diferent types of zoom on the same mesh.")
        self.updateMesh()
        dpg.configure_item("zoomRegionName", default_value="Zoom region " + str(nZoom + 1))


    def removeZoomRegion(self, sender, app_data=None):
        nZoom = len(self.sparseMeshHandler.ranges)
        nRegion = int(sender[10:])
        self.removeGrid()
        aux = self.sparseMeshHandler.ranges.pop(nRegion)

        if nZoom < 4:
            dpg.configure_item("resetMesh", show=False)
        if nZoom == 2:
            self.sparseMeshHandler = None
            dpg.configure_item("meshZoomType", enabled=True)
            dpg.set_value("meshZoomTypeTooltip", "Click to change the mesh zoom type.")
        else:
            for i in range(nRegion, nZoom):
                name = dpg.get_value("zoomTxt" + str(i + 1))
                nodeSize = dpg.get_value("listBoxZoom" + str(i + 1))
                dpg.set_value("zoomTxt" + str(i), name)
                dpg.set_value("listBoxZoom" + str(i), nodeSize)
            pass
        dpg.delete_item("separatorZoomStart" + str(nZoom - 1))
        dpg.delete_item("zoomTxt" + str(nZoom - 1))
        dpg.delete_item("listBoxZoom" + str(nZoom - 1))
        dpg.delete_item("xminZoom" + str(nZoom - 1))
        dpg.delete_item("yminZoom" + str(nZoom - 1))
        dpg.delete_item("xmaxZoom" + str(nZoom - 1))
        dpg.delete_item("ymaxZoom" + str(nZoom - 1))
        dpg.delete_item("removeZoom" + str(nZoom - 1))
        dpg.delete_item("plotRec" +  str(nZoom - 1))
        self.updateMesh()

    def updateMesh(self, sender=None, app_data=None):
        dx = dpg.get_value("dx")
        dy = dpg.get_value("dy")
        xmin = dpg.get_value("xi")
        ymin = dpg.get_value("yi")
        self.removeGrid()

        if self.sparseMeshHandler == None:
            self.currentX, self.currentY = Mesh.getMesh(self.originalX, self.originalY, xmin, ymin, dx, dy)
            nx = self.currentX[0]
            ny = self.currentY[0]
            xmin = self.currentX[1]
            ymin = self.currentY[1]
            dx = self.currentX[3]
            dy = self.currentY[3]

            self.currentX = self.currentX[4:]
            self.currentY = self.currentY[4:]
            dpg.set_value("nx", 'nx: ' + str(int(nx)))
            dpg.set_value("ny", 'ny: ' + str(int(ny)))
            self.plotGrid()
        else:
            self.sparseMeshHandler.updateRanges(dx, dy, xmin, ymin)

            if self.toggleZoomFlag == True:
                self.currentX, self.currentY = self.sparseMeshHandler.get_sparse_mesh(self.originalX, self.originalY)
                nx = self.sparseMeshHandler.ranges[0]["nx"]
                ny = self.sparseMeshHandler.ranges[0]["ny"]
                dpg.configure_item("nodeNumber", show=True)
            else:
                self.currentX, self.currentY = self.sparseMeshHandler.get_adaptative_mesh(self.originalX, self.originalY)
                nx = len(self.sparseMeshHandler.dx)
                ny = len(self.sparseMeshHandler.dy)
            
            dpg.set_value("nx", 'nx: ' + str(int(nx)))
            dpg.set_value("ny", 'ny: ' + str(int(ny)))
            self.plotGrid()
            for i in range(1,len(self.sparseMeshHandler.ranges)):
                dpg.delete_item("plotRec" +  str(i))
                r = self.sparseMeshHandler.ranges[i]
                dpg.set_value("xminZoom" + str(i), "Bottom x: " + str(r['xi']))
                dpg.set_value("yminZoom" + str(i), "Bottom y: " + str(r['yi']))
                dpg.set_value("xmaxZoom" + str(i), "Top x: " + str(r['xf']))
                dpg.set_value("ymaxZoom" + str(i), "Top y: " + str(r['yf']))
                dpg.delete_item("plotRec" +  str(i))
                dpg.add_line_series([r['xi'],r['xi'],r['xf'],r['xf'],r['xi']], [r['yi'],r['yf'],r['yf'],r['yi'],r['yi']], tag="plotRec" +  str(i), label=dpg.get_value("zoomTxt" + str(i)), parent="y_axis")

            aux = self.sparseMeshHandler.ranges[0]
            xmin = aux["xi"]
            ymin = aux["yi"]
            dx = aux["dx"]
            dy = aux["dy"]

        dpg.configure_item("dx", default_value = dx)
        dpg.configure_item("dy", default_value = dy)
        dpg.configure_item("xi", default_value = xmin)
        dpg.configure_item("yi", default_value = ymin)

        area = Mesh.get_area(self.currentX, self.currentY)
        dpg.set_value("current_area", "Currente Area: " + str(area))
        aux = dpg.get_value("original_area")
        originalArea = float(aux[15:])
        dif = abs(originalArea - area)
        dpg.set_value("difference", "Difference: " + str(dif) + " ({:.2f}%)".format(100*dif/originalArea))
        dpg.set_value("contour_nodes_number", "Contour Nodes Number: " + str(len(self.currentX)))

        dpg.delete_item("meshPlot")
        dpg.add_line_series(self.currentX, self.currentY, label="Current Mesh", tag="meshPlot", parent='y_axis')
        dpg.fit_axis_data("x_axis")
        dpg.fit_axis_data("y_axis")

    def plotGrid(self, sender=None, app_data=None):
        if self.toggleGridFlag:
            dpg.configure_item("current_nodes_number", show=True)
            nInternalNodes = self.drawGrid()
            dpg.set_value("current_nodes_number","Internal Nodes Number: " + str(nInternalNodes))
        else:
            dpg.configure_item("current_nodes_number", show=False)

    def drawGrid(self, sender=None, app_data=None):
        nInternalNodes = 0       
        meshTypeFlag = 0
        if self.sparseMeshHandler != None:
            if self.toggleZoomFlag:
                meshTypeFlag = 1
            else:
                meshTypeFlag = 2

        if meshTypeFlag == 2:
            dx = self.sparseMeshHandler.dx
            dy = self.sparseMeshHandler.dy
        else:
            dx = dpg.get_value("dx")
            dy = dpg.get_value("dy")
        xmin = dpg.get_value("xi")
        ymin = dpg.get_value("yi")
        nx = int(dpg.get_value("nx")[4:])
        ny = int(dpg.get_value("ny")[4:])


        for i in range(ny):
            flag = True
            xGrid = []
            yGrid = []
            for j in range(nx):
                if meshTypeFlag == 2:
                    auxX = dx[j]
                    auxY = dy[i]
                else:
                    auxX = xmin + j * dx
                    auxY = ymin + i * dy

                if Mesh.insidePolygon(self.currentX, self.currentY, auxX, auxY):
                    if flag:
                        flag = False
                        xGrid.append(auxX)
                        yGrid.append(auxY)
                        xGrid.append(auxX)
                        yGrid.append(auxY)
                    else:
                        xGrid[-1] = auxX
                        yGrid[-1] = auxY
                    nInternalNodes += 1
                else:
                    flag = True
            tam = len(xGrid)
            count = 0
            while count < tam:
                dpg.add_line_series(xGrid[count:count + 2], yGrid[count:count + 2], tag="meshGridPlotY0/" + str(i) + "/" + str(count), parent='y_axis')
                dpg.bind_item_theme("meshGridPlotY0/" + str(i) + "/"  + str(count), "grid_plot_theme")
                count += 2
            if count > self.countGrid:
                self.countGrid = count 

        for j in range(nx):
            flag = True
            xGrid = []
            yGrid = []
            for i in range(ny):
                if meshTypeFlag == 2:
                    auxX = dx[j]
                    auxY = dy[i]
                else:
                    auxX = xmin + j * dx
                    auxY = ymin + i * dy

                if Mesh.insidePolygon(self.currentX, self.currentY, auxX, auxY):
                    if flag:
                        flag = False
                        xGrid.append(auxX)
                        yGrid.append(auxY)
                        xGrid.append(auxX)
                        yGrid.append(auxY)
                    else:
                        xGrid[-1] = auxX
                        yGrid[-1] = auxY
                else:
                    flag = True

            tam = len(xGrid)
            count = 0
            while count < tam:
                dpg.add_line_series(xGrid[count:count + 2], yGrid[count:count + 2], tag="meshGridPlotX0/" + str(j) + "/" + str(count), parent='y_axis')
                dpg.bind_item_theme("meshGridPlotX0/" + str(j) + "/"  + str(count), "grid_plot_theme")
                count += 2
            if count > self.countGrid:
                self.countGrid = count 
        
        if meshTypeFlag == 1:
            nAux = 0
            for z in range(1, len(self.sparseMeshHandler.ranges)):
                r = self.sparseMeshHandler.ranges[z]
                for i in range(r["ny"]):
                    flag = True
                    xGrid = []
                    yGrid = []
                    for j in range(r["nx"]):
                        auxX = r["xi"] + j * r["dx"]
                        auxY = r["yi"] + i * r["dy"]
                        if Mesh.insidePolygon(self.currentX, self.currentY, auxX, auxY):
                            if flag:
                                flag = False
                                xGrid.append(auxX)
                                yGrid.append(auxY)
                                xGrid.append(auxX)
                                yGrid.append(auxY)
                            else:
                                xGrid[-1] = auxX
                                yGrid[-1] = auxY
                            nAux += 1
                        else:
                            flag = True
                    tam = len(xGrid)
                    count = 0
                    while count < tam:
                        dpg.add_line_series(xGrid[count:count + 2], yGrid[count:count + 2], tag="meshGridPlotY" + str(z) + "/" + str(i) + "/" + str(count), parent='y_axis')
                        dpg.bind_item_theme("meshGridPlotY" + str(z) + "/" + str(i) + "/" + str(count), "grid_plot_theme")
                        count += 2
                    if count > self.countGrid:
                        self.countGrid = count 

                for j in range(r["nx"]):
                    flag = True
                    xGrid = []
                    yGrid = []
                    for i in range(r["ny"]):
                        auxX = r["xi"] + j * r["dx"]
                        auxY = r["yi"] + i * r["dy"]
                        if Mesh.insidePolygon(self.currentX, self.currentY, auxX, auxY):
                            if flag:
                                flag = False
                                xGrid.append(auxX)
                                yGrid.append(auxY)
                                xGrid.append(auxX)
                                yGrid.append(auxY)
                            else:
                                xGrid[-1] = auxX
                                yGrid[-1] = auxY
                        else:
                            flag = True
                    tam = len(xGrid)
                    count = 0
                    while count < tam:
                        dpg.add_line_series(xGrid[count:count + 2], yGrid[count:count + 2], tag="meshGridPlotX" + str(z) + "/" + str(j) + "/" + str(count), parent='y_axis')
                        dpg.bind_item_theme("meshGridPlotX" + str(z) + "/" + str(j) + "/" + str(count), "grid_plot_theme")
                        count += 2
                    if count > self.countGrid:
                        self.countGrid = count 
                
                nAux -= (1 + (r["xf"] - r["xi"])//dx) * (1 + (r["yf"] - r["yi"])//dy)    
            nInternalNodes += nAux
        return nInternalNodes

    def removeGrid(self, sender=None, app_data=None):
        if self.sparseMeshHandler == None or not self.toggleZoomFlag:
            n = 1
            nx = [int(dpg.get_value("nx")[4:])]
            ny = [int(dpg.get_value("ny")[4:])]
        else:
            aux = self.sparseMeshHandler.ranges
            n = len(aux)
            nx = []
            ny = []
            for r in aux:
                nx.append(r["nx"])
                ny.append(r["ny"])
        for k in range(0,self.countGrid,2):
            for z in range(n):
                for i in range(ny[z]):
                        dpg.delete_item("meshGridPlotY" + str(z) + "/" + str(i) + "/" + str(k))
                for j in range(nx[z]):
                        dpg.delete_item("meshGridPlotX" + str(z) + "/" + str(j) + "/" + str(k))
        self.countGrid = 0

    def toggleGrid(self, sender=None, app_data=None):
        self.toggleGridFlag = not self.toggleGridFlag
        if self.toggleGridFlag:
            dpg.configure_item("plotGrid", label="Remove Plot Mesh Grid")
            self.updateMesh()
        else:
            dpg.configure_item("plotGrid", label="Plot Mesh Grid")
            self.removeGrid()

    def resetMesh(self, sender=None, app_data=None):
        for i in range(1,len(self.sparseMeshHandler.ranges)):
            dpg.delete_item("separatorZoomStart" + str(i))
            dpg.delete_item("zoomTxt" + str(i))
            dpg.delete_item("listBoxZoom" + str(i))
            dpg.delete_item("xminZoom" + str(i))
            dpg.delete_item("yminZoom" + str(i))
            dpg.delete_item("xmaxZoom" + str(i))
            dpg.delete_item("ymaxZoom" + str(i))
            dpg.delete_item("removeZoom" + str(i))
            dpg.delete_item("plotRec" +  str(i))

        dpg.configure_item("meshZoomType", enabled=True)
        dpg.set_value("meshZoomTypeTooltip", "Click to change the mesh zoom type.")
        dpg.configure_item("resetMesh", show=False)
        self.sparseMeshHandler = None
        self.updateMesh()

    def openMeshDirectorySelector(self, sender=None, app_data=None):
        if dpg.get_value('inputMeshNameText') != '':
            dpg.configure_item('meshDirectorySelectorFileDialog', show=True)

    def selectMeshFileFolder(self, sender=None, app_data=None):

        self.exportFilePath = app_data['file_path_name']

        self.exportFileName = dpg.get_value('inputMeshNameText') + '.txt'
        filePath = os.path.join(self.exportFilePath, self.exportFileName)

        dpg.set_value('exportMeshFileName', 'File Name: ' + self.exportFileName)
        dpg.set_value('exportMeshPathName', 'Complete Path Name: ' + filePath)

        pass

    def exportMesh(self, sender=None, app_data=None):
        if self.exportFilePath is None:
            dpg.configure_item("exportMeshError", show=True)
            return

        dpg.configure_item("exportMeshError", show=False)
        filePath = os.path.join(self.exportFilePath, self.exportFileName)
        if self.sparseMeshHandler != None:
            if self.toggleZoomFlag:
                self.sparseMeshHandler.export_coords_mesh(filePath, self.currentX, self.currentY, self.toggleOrderingFlag)
                filePathDx = filePath[:-4] + "_dx.txt"
                filePathDy = filePath[:-4] + "_dy.txt"
                self.sparseMeshHandler.export_node_size_mesh(filePathDx, filePathDy)
            else:
                self.sparseMeshHandler.export_coords_mesh(filePath, self.currentX, self.currentY, self.toggleOrderingFlag)
                filePathRanges = filePath[:-4] + "_ranges.txt"
                self.sparseMeshHandler.export_ranges(filePathRanges)
        else:
            nx = int(dpg.get_value("nx")[4:])
            ny = int(dpg.get_value("ny")[4:])
            xmin = min(self.currentX)
            ymin = min(self.currentY)
            xmax = max(self.currentX)
            ymax = max(self.currentY)
            dx = (xmax - xmin)/(nx - 1)
            dy = (ymax - ymin)/(ny - 1)
            Mesh.export_coords_mesh(filePath, self.currentX, self.currentY, nx, ny, xmin, ymin, xmax, ymax, dx, dy, self.toggleOrderingFlag)
            self.exportFilePath = None
            self.exportFileName = None
            dpg.configure_item("exportMeshFile", show=False)