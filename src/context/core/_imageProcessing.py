import dearpygui.dearpygui as dpg
import numpy as np
import cv2
import pydicom
import os.path
from ._blocks import Blocks
from ._texture import Texture
from ..ui import strings

class ImageProcessing:
    def __init__(self) -> None:

        self.filePath = None
        self.fileName = None
        self.exportImageFilePath = None
        self.currentTab = None
        self.resetContours = None
        self.originalResolution = None
        self.currentResolution = None

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
                'status': True,
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
                'method': self.laplacian,
                'name': self.laplacian.__name__,
                'status': False,
                'output': None,
                'tab': 'Thresholding'
            },
            {
                'method': self.sobel,
                'name': self.sobel.__name__,
                'status': False,
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
                'method': self.adaptiveMeanThresholding,
                'name': self.adaptiveMeanThresholding.__name__,
                'status': False,
                'output': None,
                'tab': 'Thresholding'
            },
            {
                'method': self.adaptiveGaussianThresholding,
                'name': self.adaptiveGaussianThresholding.__name__,
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

    def getCurrentResolution(self):
        return self.currentResolution

    def renderFileInfo(self):
        dpg.set_value('file_name_text', strings.fmt("file_name", value=self.fileName or ""))
        dpg.set_value('file_path_text', strings.fmt("file_path", value=self.filePath or ""))

    def renderResolutionInfo(self):
        original_width = "--"
        original_height = "--"
        current_width = "--"
        current_height = "--"

        if self.originalResolution is not None:
            original_width = self.originalResolution[0]
            original_height = self.originalResolution[1]
        if self.currentResolution is not None:
            current_width = self.currentResolution[0]
            current_height = self.currentResolution[1]

        dpg.set_value('originalWidth', strings.fmt("width_px", value=original_width))
        dpg.set_value('originalHeight', strings.fmt("height_px", value=original_height))
        dpg.set_value('currentWidth', strings.fmt("width_px", value=current_width))
        dpg.set_value('currentHeight', strings.fmt("height_px", value=current_height))

    def renderExportState(self):
        export_file_name = ""
        export_full_path = ""

        if self.exportImageFilePath is not None:
            export_file_name = os.path.basename(self.exportImageFilePath)
            export_full_path = self.exportImageFilePath

        dpg.set_value('exportImageFileName', strings.fmt("file_name", value=export_file_name))
        dpg.set_value('exportImageFilePath', strings.fmt("full_path", value=export_full_path))

    def refreshTranslations(self):
        self.renderFileInfo()
        self.renderResolutionInfo()
        self.renderExportState()


    def executeQuery(self, methodName):
        executeFlag = 0
        for entry in self.blocks:
            if executeFlag == 0 and entry['name'] == methodName:
                executeFlag = 1
            if executeFlag == 1 and entry['status'] is True:
                entry['method']()
        try:
            dpg.get_item_callback("removeExtractContour")()
        except:
            pass

    def executeQueryFromNext(self, methodName):
        executeFlag = 0
        for entry in self.blocks:
            if executeFlag == 0 and entry['name'] == methodName:
                executeFlag = 1
                continue
            if executeFlag == 1 and entry['status'] is True:
                entry['method']()
        try:
            dpg.get_item_callback("removeExtractContour")()
        except:
            pass

    def toggleAndExecuteQuery(self, methodName, sender = None, app_data = None):
        self.toggleEffect(methodName, sender, app_data)
        if dpg.get_value(sender) is True:
            self.executeQuery(methodName)
        else:
            self.retrieveFromLastActive(methodName, sender, app_data)
            self.executeQueryFromNext(methodName)
        try:
            dpg.get_item_callback("removeExtractContour")()
        except:
            pass

    def getIdByMethod(self, methodName):
        id = 0
        for entry in self.blocks:
            if entry['name'] == methodName:
                return id
            id += 1

    def retrieveFromLastActive(self, methodName, sender = None, app_data = None):
        self.blocks[self.getIdByMethod(methodName)]['output'] = self.blocks[self.getLastActiveBeforeMethod(methodName)]['output']
        Texture.updateTexture(self.blocks[self.getIdByMethod(methodName)]['tab'], self.blocks[self.getIdByMethod(methodName)]['output'])

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
        # Check if image is .dcm or .dicom or other format
        if filePath.endswith('.dcm') or filePath.endswith('.dicom'):
            return self.openDicom(filePath)
        return self.openOtherImage(filePath)

    def openDicom(self, filePath):
        ds = pydicom.dcmread(filePath)
        pixelArray = ds.pixel_array
        _, encodedImage = cv2.imencode('.jpg', pixelArray)
        numpyarray = cv2.imdecode(encodedImage, cv2.IMREAD_COLOR)
        return numpyarray
    
    def openOtherImage(self, filePath):
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

        dpg.set_value("brightnessSlider",0)
        dpg.set_value("contrastSlider",1)
        dpg.set_value("averageBlurSlider",1)
        dpg.set_value("gaussianBlurSlider",1)
        dpg.set_value("medianBlurSlider",1)
        dpg.set_value("laplacianSlider",1)
        dpg.set_value("globalThresholdSlider",127)
        
        try:
            dpg.get_item_callback("removeExtractContour")()
        except:
            pass
        self.uncheckAllTags()
        for entry in self.blocks[1:-1]:
            if entry['name'] != self.grayscale.__name__ and entry['name'] != self.crop.__name__:
                entry['status'] = False
        self.executeQuery('importImage')
        self.enableAllTags()
        pass

    def cancelImportImage(self, sender = None, app_data = None):
        dpg.hide_item("file_dialog_id")
        pass

    def toggleEffect(self, methodName, sender = None, app_data = None):
        for entry in self.blocks:
            if entry['name'] == methodName:
                entry['status'] = dpg.get_value(sender)
        pass

    def importImage(self, sender = None, app_data = None):
        # Cria imagem na aba
        self.blocks[Blocks.importImage.value]['output'] = self.openImage(self.filePath)

        Texture.createAllTextures(self.blocks[Blocks.importImage.value]['output'])

        # Popula os dados na lateral
        self.renderFileInfo()

        shape = self.blocks[Blocks.importImage.value]['output'].shape
        self.originalResolution = (shape[1], shape[0])
        self.currentResolution = (shape[1], shape[0])

        self.renderResolutionInfo()

        dpg.set_value('endX', shape[0])
        dpg.set_value('endY', shape[1])
        dpg.configure_item("exportImageAsFileProcessingGroup", show=True)
        dpg.configure_item("exportImageAsFileFilteringGroup", show=True)
        dpg.configure_item("exportImageAsFileThresholdingGroup", show=True)
        pass


    def resetCrop(self, sender = None, app_data = None):

        if self.blocks[Blocks.importImage.value]['output'] is None:
            dpg.configure_item('noImage', show=True)
            self.blocks[Blocks.crop.value]['status'] = False
            return

        self.blocks[Blocks.crop.value]['output'] = self.blocks[Blocks.importImage.value]['output']

        shape = self.blocks[Blocks.crop.value]['output'].shape
        self.currentResolution = (shape[1], shape[0])

        self.renderResolutionInfo()
        dpg.set_value('endX', shape[0])
        dpg.set_value('endY', shape[1])

        Texture.createAllTextures(self.blocks[Blocks.importImage.value]['output'])

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
        self.currentResolution = (shape[1], shape[0])

        self.renderResolutionInfo()

        dpg.set_value('endX', shape[0])
        dpg.set_value('endY', shape[1])

        Texture.createAllTextures(self.blocks[Blocks.crop.value]['output'])

    def histogramEqualization(self, sender=None, app_data=None):

        img_yuv = cv2.cvtColor(self.blocks[self.getLastActiveBeforeMethod('histogramEqualization')]['output'], cv2.COLOR_BGR2YUV)
        img_yuv[:,:,0] = cv2.equalizeHist(img_yuv[:,:,0])
        dst = cv2.cvtColor(img_yuv, cv2.COLOR_YUV2BGR)
        self.blocks[Blocks.histogramEqualization.value]['output'] = dst
        Texture.updateTexture(self.blocks[Blocks.histogramEqualization.value]['tab'], dst)
        pass

    def brightnessAndContrast(self, sender=None, app_data=None):

        image = self.blocks[self.getLastActiveBeforeMethod('brightnessAndContrast')]['output']
        alpha = dpg.get_value('contrastSlider')
        beta = dpg.get_value('brightnessSlider')
        outputImage = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)

        self.blocks[Blocks.brightnessAndContrast.value]['output'] = outputImage
        Texture.updateTexture(self.blocks[Blocks.brightnessAndContrast.value]['tab'], outputImage)
        pass

    def averageBlur(self, sender=None, app_data=None):
        image = self.blocks[self.getLastActiveBeforeMethod('averageBlur')]['output']

        kernelSize = (2 * dpg.get_value('averageBlurSlider')) - 1
        kernel = np.ones((kernelSize,kernelSize),np.float32)/(kernelSize*kernelSize)
        dst = cv2.filter2D(image,-1,kernel)

        self.blocks[Blocks.averageBlur.value]['output'] = dst
        Texture.updateTexture(self.blocks[Blocks.averageBlur.value]['tab'], dst)
        pass

    def gaussianBlur(self, sender=None, app_data=None):
        image = self.blocks[self.getLastActiveBeforeMethod('gaussianBlur')]['output']

        kernelSize = (2 * dpg.get_value('gaussianBlurSlider')) - 1
        dst = cv2.GaussianBlur(image, (kernelSize,kernelSize), 0)

        self.blocks[Blocks.gaussianBlur.value]['output'] = dst
        Texture.updateTexture(self.blocks[Blocks.gaussianBlur.value]['tab'], dst)
        pass

    def medianBlur(self, sender=None, app_data=None):
        image = self.blocks[self.getLastActiveBeforeMethod('medianBlur')]['output']
        kernel = (2 * dpg.get_value('medianBlurSlider')) - 1

        median = cv2.medianBlur(image, kernel)

        self.blocks[Blocks.medianBlur.value]['output'] = median
        Texture.updateTexture(self.blocks[Blocks.medianBlur.value]['tab'], median)
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
        Texture.updateTexture(self.blocks[Blocks.grayscale.value]['tab'], image)
        pass

    def laplacian(self, sender=None, app_data=None):
        image = self.blocks[Blocks.grayscale.value]['output'].copy()

        kernelSize = (2 * dpg.get_value('laplacianSlider')) - 1
        laplacian = cv2.Laplacian(image, cv2.CV_8U, ksize=kernelSize)
                
        self.blocks[Blocks.laplacian.value]['output'] = laplacian
        Texture.updateTexture(self.blocks[Blocks.laplacian.value]['tab'], laplacian)
        pass

    def sobel(self, sender=None, app_data=None):
        image = self.blocks[self.getLastActiveBeforeMethod('sobel')]['output']

        sobel = None
        value = strings.option_key("sobel_axis", dpg.get_value('sobelListbox'))

        if value == 'x_axis':
            sobel = cv2.Sobel(image, cv2.CV_8U, 1, 0, ksize=3)
        elif value == 'y_axis':
            sobel = cv2.Sobel(image, cv2.CV_8U, 0, 1, ksize=3)
        elif value == 'xy_axis':
            sobel = cv2.bitwise_or(cv2.Sobel(image, cv2.CV_8U, 1, 0, ksize=3), cv2.Sobel(image, cv2.CV_8U, 0, 1, ksize=3))

        self.blocks[Blocks.sobel.value]['output'] = sobel
        Texture.updateTexture(self.blocks[Blocks.sobel.value]['tab'], sobel)
        pass

    def globalThresholding(self, sender=None, app_data=None):
        image = self.blocks[self.getLastActiveBeforeMethod('globalThresholding')]['output']
        threshold = dpg.get_value('globalThresholdSlider')

        thresholdMode = cv2.THRESH_BINARY 
        invertFlag = dpg.get_value('invertGlobalThresholding')
        if invertFlag:
            thresholdMode = cv2.THRESH_BINARY_INV

        (T, threshInv) = cv2.threshold(image, threshold, 255, thresholdMode)

        self.blocks[Blocks.globalThresholding.value]['output'] = threshInv
        Texture.updateTexture(self.blocks[Blocks.globalThresholding.value]['tab'], threshInv)
        pass

    def adaptiveMeanThresholding(self, sender=None, app_data=None):
        image = self.blocks[self.getLastActiveBeforeMethod('adaptiveMeanThresholding')]['output'].copy()

        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        threshInv = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY,11,2)
        image = cv2.cvtColor(threshInv, cv2.COLOR_GRAY2BGR)

        self.blocks[Blocks.adaptiveMeanThresholding.value]['output'] = image
        Texture.updateTexture(self.blocks[Blocks.adaptiveMeanThresholding.value]['tab'], image)

        pass

    def adaptiveGaussianThresholding(self, sender=None, app_data=None):

        image = self.blocks[self.getLastActiveBeforeMethod('adaptiveGaussianThresholding')]['output'].copy()

        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        threshInv = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY,11,2)
        image = cv2.cvtColor(threshInv, cv2.COLOR_GRAY2BGR)

        self.blocks[Blocks.adaptiveGaussianThresholding.value]['output'] = image
        Texture.updateTexture(self.blocks[Blocks.adaptiveGaussianThresholding.value]['tab'], image)

        pass

    def otsuBinarization(self, sender=None, app_data=None):
        image = self.blocks[self.getLastActiveBeforeMethod('adaptiveGaussianThresholding')]['output'].copy()
        
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        ret, threshInv = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        threshInv = cv2.cvtColor(threshInv, cv2.COLOR_GRAY2BGR)


        self.blocks[Blocks.otsuBinarization.value]['output'] = threshInv
        Texture.updateTexture(self.blocks[Blocks.otsuBinarization.value]['tab'], threshInv)
        pass

    def findContour(self, sender=None, app_data=None):

        if self.blocks[self.getLastActiveBeforeMethod('findContour')]['output'] is None:
            return

        image = self.blocks[self.getLastActiveBeforeMethod('findContour')]['output'].copy()
        Texture.updateTexture(self.blocks[Blocks.findContour.value]['tab'], image)
        pass

    def exportImage(self, sender = None, app_data = None, tab = None):

        self.exportImageFilePath = None
        self.renderExportState()
        dpg.set_value('imageNameExportAsFile', '')
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
        self.renderExportState()
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

    def enableAllTags(self):
        checkboxes = [
            'histogramCheckbox',
            'brightnessAndContrastCheckbox',
            'averageBlurCheckbox',
            'gaussianBlurCheckbox',
            'medianBlurCheckbox',
            'excludeBlueChannel',
            'excludeGreenChannel',
            'excludeRedChannel',
            'laplacianCheckbox',
            'sobelCheckbox',
            'globalThresholdingCheckbox',
            'invertGlobalThresholding',
            'adaptiveThresholdingCheckbox',
            'adaptiveGaussianThresholdingCheckbox',
            'otsuBinarization',
            'matlabModeCheckbox',
            'extractContourButton',
            'updateContourButton',
            'exportImageAsFileProcessing',
            'exportImageAsFileFiltering',
            'exportImageAsFileThresholding'
        ]
        for checkbox in checkboxes:
            dpg.configure_item(checkbox, enabled=True)
        pass

    def disableAllTags(self):
        checkboxes = [
            'histogramCheckbox',
            'brightnessAndContrastCheckbox',
            'averageBlurCheckbox',
            'gaussianBlurCheckbox',
            'medianBlurCheckbox',
            'excludeBlueChannel',
            'excludeGreenChannel',
            'excludeRedChannel',
            'laplacianCheckbox',
            'sobelCheckbox',
            'globalThresholdingCheckbox',
            'invertGlobalThresholding',
            'adaptiveThresholdingCheckbox',
            'adaptiveGaussianThresholdingCheckbox',
            'otsuBinarization',
            'matlabModeCheckbox',
            'extractContourButton',
            'updateContourButton',
            'exportImageAsFileProcessing',
            'exportImageAsFileFiltering',
            'exportImageAsFileThresholding'
        ]
        for checkbox in checkboxes:
            dpg.configure_item(checkbox, enabled=False)
        pass

    def uncheckAllTags(self):
        checkboxes = [
            'histogramCheckbox',
            'brightnessAndContrastCheckbox',
            'averageBlurCheckbox',
            'gaussianBlurCheckbox',
            'medianBlurCheckbox',
            'excludeBlueChannel',
            'excludeGreenChannel',
            'excludeRedChannel',
            'laplacianCheckbox',
            'sobelCheckbox',
            'globalThresholdingCheckbox',
            'invertGlobalThresholding',
            'adaptiveThresholdingCheckbox',
            'adaptiveGaussianThresholdingCheckbox',
            'otsuBinarization',
            'matlabModeCheckbox',
            'extractContourButton',
            'updateContourButton',
            'exportImageAsFileProcessing',
            'exportImageAsFileFiltering',
            'exportImageAsFileThresholding'
        ]
        for checkbox in checkboxes:
            dpg.set_value(checkbox, False)
        pass
