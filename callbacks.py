# -*- coding: utf-8 -*-
import dearpygui.dearpygui as dpg
import numpy as np
import cv2
import enum
from mesh import Mesh
import random

class Tabs(enum.Enum):
    __order__ = 'Processing Filtering Thresholding ContourExtraction'
    Processing = 0
    Filtering = 1
    Thresholding = 2
    ContourExtraction = 3

class Blocks(enum.Enum):
    __order__ = 'importImage crop histogramEqualization brightnessAndContrast averageBlur gaussianBlur medianBlur grayscale globalThresholding adaptativeMeanThresholding adaptativeGaussianThresholding otsuBinarization findContour exportSettings'
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
    exportSettings = 13

class Callbacks:
    def __init__(self) -> None:

        self.filePath = None
        self.fileName = None
        self.txtFilePath = None
        self.txtFileName = None
        self.toggleOrderingFlag = True
        self.toggleZoomFlag = True
        self.zoomRegionNumber = 0
        self.sparseMeshHandler = None
        self.originalX = []
        self.originalY = []
        self.currentX = []
        self.currentY = []
        self.contourTableEntry = []

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
                'status': True,
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
            {
                'method': self.exportSettings,
                'name': self.exportSettings.__name__,
                'status': False,
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
        self.executeQuery('importImage')
        pass

    # TODO: Create Texture
    def createTexture(self, textureTag, textureImage):
        self.deleteTexture(textureTag)
        height = textureImage.shape[0]
        width = textureImage.shape[1]
        textureData = self.textureToData(textureImage)
        dpg.add_dynamic_texture(width=width, height=height, default_value=textureData, tag=textureTag, parent='textureRegistry')
        dpg.add_image(textureTag, parent=textureTag + 'Parent', tag=textureTag + 'Image')
        pass

    # TODO: Delete Texture
    def deleteTexture(self, textureTag):
        try:
            dpg.delete_item(textureTag)
            dpg.delete_item(textureTag + 'Image')
        except:
            pass
        pass

    # TODO: Update Texture
    def updateTexture(self, textureTag, textureImage):
        textureData = self.textureToData(textureImage)
        dpg.set_value(textureTag, textureData)
        pass

    def createAllTextures(self, textureImage):
        for tab in Tabs:
            self.createTexture(tab.name, textureImage)

    # TODO: Delete all textures
    def deleteAllTextures(self):
        for tab in Tabs:
            self.deleteTexture(tab.name)
        pass

    def updateAllTextures(self, textureImage):
        for tab in Tabs:
            self.updateTexture(tab.name, textureImage)
        pass

    # TODO: Convert texture to data
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
        pass


    def resetCrop(self, sender = None, app_data = None):
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
                }
            )
            cv2.drawContours(image, contour, -1, contourColor, thicknessValue)

        self.contourTableEntry = list(sorted(self.contourTableEntry, key=lambda x: x['pointsNo'], reverse=True))

        try:
            dpg.delete_item('ContourExtractionTable')
            dpg.delete_item('showAllContoursButton')
            dpg.delete_item('hideAllContoursButton')
        except:
            pass

        dpg.add_button(tag='showAllContoursButton', label='Show All Contours', parent='ContourExtractionParent', callback=lambda sender, app_data: self.showAllContours())
        dpg.add_button(tag='hideAllContoursButton', label='Hide All Contours', parent='ContourExtractionParent', callback=lambda sender, app_data: self.hideAllContours())
        with dpg.table(tag='ContourExtractionTable', header_row=True, policy=dpg.mvTable_SizingFixedFit, row_background=True,
            resizable=True, no_host_extendX=False, hideable=True,
            borders_innerV=True, delay_search=True, borders_outerV=True, borders_innerH=True,
            borders_outerH=True, parent='ContourExtractionParent'):

            dpg.add_table_column(label="Id", width_fixed=True)
            dpg.add_table_column(label="Size", width_fixed=True)
            dpg.add_table_column(label="Color", width_fixed=True)
            dpg.add_table_column(label="Visible", width_fixed=True)
            dpg.add_table_column(label="Export to Mesh Generation", width_fixed=True)


            for contourEntry in self.contourTableEntry:
                with dpg.table_row():
                    for j in range(5):
                        if j == 0:
                            dpg.add_text(contourEntry['id'])
                        if j == 1:
                            dpg.add_text(contourEntry['pointsNo'])
                        if j == 2:
                            dpg.add_color_button(default_value=contourEntry['color'])
                        if j == 3:
                            dpg.add_checkbox(tag='checkboxContourId' + str(contourEntry['id']), callback= lambda sender, app_data: self.redrawContours(), default_value=True)
                        if j == 4:
                            dpg.add_button(label='Export')
        
        self.blocks[Blocks.findContour.value]['output'] = image
        self.updateTexture(self.blocks[Blocks.findContour.value]['tab'], image)

    def redrawContours(self):
        image = self.blocks[self.getLastActiveBeforeMethod('findContour')]['output'].copy()

        thicknessValue = dpg.get_value('contourThicknessSlider')

        for entry in self.contourTableEntry:
            drawContour = dpg.get_value('checkboxContourId' + str(entry['id']))
            if drawContour:
                cv2.drawContours(image, entry['data'], -1, entry['color'], thicknessValue)

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

    def exportSettings(self, sender=None, app_data=None):

        pass
        
    def plotMesh(self, sender=None, app_data=None):
        nx = self.currentX[0]
        ny = self.currentY[0]
        xmin = self.currentX[1]
        ymin = self.currentY[1]
        dx = self.currentX[3]
        dy = self.currentY[3]

        dpg.set_value("original_xi", 'x:' + str(xmin))
        dpg.set_value("original_yi", 'y:' + str(ymin))
        dpg.set_value("original_dx", 'dx:' + str(dx))
        dpg.set_value("original_dy", 'dy:' + str(dy))
        dpg.set_value("original_nx", 'nx:' + str(nx))
        dpg.set_value("original_ny", 'ny:' + str(ny))
        dpg.set_value("nx", 'nx:' + str(nx))
        dpg.set_value("ny", 'ny:' + str(ny))
        dpg.configure_item("dx", default_value = dx)
        dpg.configure_item("dy", default_value = dy)
        dpg.configure_item("xi", default_value = xmin)
        dpg.configure_item("yi", default_value = ymin)

        self.currentX = self.currentX[4:]
        self.currentY = self.currentY[4:]
        dpg.set_value("original_area", "Original Area: " + str(Mesh.get_area(self.currentX, self.currentY)))
        dpg.add_line_series(self.currentX, self.currentY, label="Original Mesh", tag="originalMeshPlot", parent='y_axis')
        dpg.fit_axis_data("x_axis")
        dpg.fit_axis_data("y_axis")

    def importContour(self, sender = None, app_data = None):
        self.txtFilePath = app_data['file_path_name']
        self.txtFileName = app_data['file_name']
        dpg.configure_item('contour_ordering', enabled=True)

        dpg.set_value('contour_file_name_text', 'File Name: ' + self.txtFileName)
        dpg.set_value('contour_file_path_text', 'File Path: ' + self.txtFilePath)
        self.originalX = []
        self.originalY = []
        f = open(self.txtFilePath,'r')
        for line in f.readlines():
            aux = line.split()
            self.originalX.append(float(aux[0]))
            self.originalY.append(float(aux[1]))
        f.close()
        self.currentX = self.originalX
        self.currentY = self.originalY
        self.originalX = self.originalX[4:]
        self.originalY = self.originalY[4:]
        self.plotMesh()

    def toggleOrdering(self, sender = None, app_data = None):
        self.toggleOrderingFlag = not self.toggleOrderingFlag
        self.originalX = self.originalX[::-1]
        self.originalY = self.originalY[::-1]
        self.currentX = self.currentX[::-1]
        self.currentY = self.currentY[::-1]
        if self.toggleOrderingFlag:
            dpg.configure_item('contour_ordering', label="Anticlockwise")
        else:
            dpg.configure_item('contour_ordering', label="Clockwise")
        pass

    def toggleZoom(self, sender = None, app_data = None):
        self.toggleZoomFlag = not self.toggleZoomFlag
        if self.toggleZoomFlag:
            dpg.configure_item('meshZoomType', label="Sparse")
        else:
            dpg.configure_item('meshZoomType', label="Adaptative")
        pass

    def addZoomRegion(self, sender = None, app_data = None):
        self.zoomRegionNumber += 1
        dpg.configure_item("sparsePopup", show=False)
        dpg.set_value("meshZoomTypeTooltip", "You cannot add diferent types of zoom on the same mesh.")
        dpg.configure_item("zoomRegionName", default_value="Zoom region " + str(self.zoomRegionNumber + 1))
        pass

    def updateMesh(self, sender=None, app_data=None):
        dx = dpg.get_value("dx")
        dy = dpg.get_value("dy")
        xmin = dpg.get_value("xi")
        ymin = dpg.get_value("yi")
        self.currentX, self.currentY = Mesh.getMesh(self.originalX, self.originalY, xmin, ymin, dx, dy)
        nx = self.currentX[0]
        ny = self.currentY[0]
        xmin = self.currentX[1]
        ymin = self.currentY[1]
        dx = self.currentX[3]
        dy = self.currentY[3]

        dpg.set_value("nx", 'nx:' + str(int(nx)))
        dpg.set_value("ny", 'ny:' + str(int(ny)))
        dpg.configure_item("dx", default_value = dx)
        dpg.configure_item("dy", default_value = dy)
        dpg.configure_item("xi", default_value = xmin)
        dpg.configure_item("yi", default_value = ymin)

        self.currentX = self.currentX[4:]
        self.currentY = self.currentY[4:]

        area = Mesh.get_area(self.currentX, self.currentY)
        dpg.set_value("current_area", "Currente Area: " + str(area))
        aux = dpg.get_value("original_area")
        originalArea = float(aux[15:])
        dif = abs(originalArea - area)
        dpg.set_value("difference", "Difference: " + str(dif) + " ({:.2f}%)".format(100*dif/originalArea))

        dpg.delete_item("meshPlot")
        dpg.add_line_series(self.currentX, self.currentY, label="Currente Mesh", tag="meshPlot", parent='y_axis')
        dpg.fit_axis_data("x_axis")
        dpg.fit_axis_data("y_axis")
        pass