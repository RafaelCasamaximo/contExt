from pprint import pprint
import dearpygui.dearpygui as dpg
import numpy as np
import cv2
import enum

class Blocks(enum.Enum):
    __order__ = 'importImage crop histogramEqualization brightnessAndContrast averageBlur gaussianBlur grayscale globalThresholding adaptativeMeanThresholding adaptativeGaussianThresholding otsuBinarization findContour mooreNeighborhood exportSettings'
    importImage = 0
    crop = 1
    histogramEqualization = 2
    brightnessAndContrast = 3
    averageBlur = 4
    gaussianBlur = 5
    grayscale = 6
    globalThresholding = 7
    adaptativeMeanThresholding = 8
    adaptativeGaussianThresholding = 9
    otsuBinarization = 10
    findContour = 11
    mooreNeighborhood = 12
    exportSettings = 13

class Callbacks:
    def __init__(self) -> None:

        self.filePath = None

        self.blocks = [
            {
                'method': self.importImage,
                'name': self.importImage.__name__,
                'status': False,
                'output': None,
            },
            {
                'method': self.crop,
                'name': self.crop.__name__,
                'status': False,
                'output': None,
            },
            {
                'method': self.histogramEqualization,
                'name': self.histogramEqualization.__name__,
                'status': False,
                'output': None,
            },
            {
                'method': self.brightnessAndContrast,
                'name': self.brightnessAndContrast.__name__,
                'status': False,
                'output': None,
            },
            {
                'method': self.averageBlur,
                'name': self.averageBlur.__name__,
                'status': False,
                'output': None,
            },
            {
                'method': self.gaussianBlur,
                'name': self.gaussianBlur.__name__,
                'status': False,
                'output': None,
            },
            {
                'method': self.grayscale,
                'name': self.grayscale.__name__,
                'status': False,
                'output': None,
            },
            {
                'method': self.globalThresholding,
                'name': self.globalThresholding.__name__,
                'status': False,
                'output': None,
            },
            {
                'method': self.adaptativeMeanThresholding,
                'name': self.adaptativeMeanThresholding.__name__,
                'status': False,
                'output': None,
            },
            {
                'method': self.adaptativeGaussianThresholding,
                'name': self.adaptativeGaussianThresholding.__name__,
                'status': False,
                'output': None,
            },
            {
                'method': self.otsuBinarization,
                'name': self.otsuBinarization.__name__,
                'status': False,
                'output': None,
            },
            {
                'method': self.findContour,
                'name': self.findContour.__name__,
                'status': False,
                'output': None,
            },
            {
                'method': self.mooreNeighborhood,
                'name': self.mooreNeighborhood.__name__,
                'status': False,
                'output': None,
            },
            {
                'method': self.exportSettings,
                'name': self.exportSettings.__name__,
                'status': False,
                'output': None,
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
            if executeFlag == 1 and entry['status'] is False:
                # TODO: Um método que verifica qual o último status true e coloca como resultado do método atual o resultado do último status ativo
                # (Serve para o método atual sempre poder pegar o output do último método para aplicar o processamento de imagem)
                pass
        pass

    def openFile(self, sender = None, app_data = None):
        self.filePath = app_data['file_path_name']
        self.executeQuery('importImage')
        pass

    # TODO: Create Texture
    def createTexture(self, textureTag, textureImage):
        height = textureImage.shape[0]
        width = textureImage.shape[1]
        textureData = self.textureToData(textureImage)
        dpg.add_raw_texture(width=width, height=height, default_value=textureData, tag=textureTag, parent='textureRegistry', format=dpg.mvFormat_Float_rgb)
        dpg.add_image(textureTag, parent=textureTag + 'Parent', tag=textureTag + 'Image')
        pass

    # TODO: Delete Texture
    def deleteTexture(self, textureTag):
        dpg.delete_item(textureTag)
        dpg.delete_item(textureTag + 'Image')
        pass

    # TODO: Update Texture
    def updateTexture(self, textureTag, textureImage):
        textureData = self.textureToData(textureImage)
        dpg.set_value(textureTag, textureData)
        pass

    # TODO: Create all textures
    def createAllTextures(self):
        pass

    # TODO: Delete all textures

    def deleteAllTextures(self):
        pass
    # TODO: Update all textures
    def updateAllTextures(self):
        pass

    # TODO: Convert texture to data
    def textureToData(self, texture):
        auxImg = np.flip(texture, 2)
        auxImg = np.asfarray(auxImg, dtype='f')  # change data type to 32bit floats
        auxImg = auxImg.ravel()
        auxImg = np.true_divide(auxImg, 255.0)
        return auxImg


    def importImage(self, sender = None, app_data = None):
        self.blocks[Blocks.importImage]['output'] = cv2.imread(self.filePath, cv2.IMREAD_COLOR)
        pass

    def resetCrop(self, sender = None, app_data = None):

        pass

    def crop(self, sender=None, app_data=None):

        pass

    def histogramEqualization(self, sender=None, app_data=None):

        pass

    def brightnessAndContrast(self, sender=None, app_data=None):

        pass

    def averageBlur(self, sender=None, app_data=None):

        pass

    def gaussianBlur(self, sender=None, app_data=None):

        pass

    def grayscale(self, sender=None, app_data=None):

        pass

    def globalThresholding(self, sender=None, app_data=None):

        pass

    def adaptativeMeanThresholding(self, sender=None, app_data=None):

        pass

    def adaptativeGaussianThresholding(self, sender=None, app_data=None):

        pass

    def otsuBinarization(self, sender=None, app_data=None):

        pass

    def findContour(self, sender=None, app_data=None):

        pass

    def mooreNeighborhood(self, sender=None, app_data=None):

        pass

    def exportSettings(self, sender=None, app_data=None):

        pass
