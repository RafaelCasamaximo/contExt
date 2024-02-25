import dearpygui.dearpygui as dpg
import cv2
import numpy as np
import enum

class Tabs(enum.Enum):
    __order__ = 'Processing Filtering Thresholding ContourExtraction'
    Processing = 0
    Filtering = 1
    Thresholding = 2
    ContourExtraction = 3

class Texture:

    def createTexture(textureTag, textureImage):
        Texture.deleteTexture(textureTag)
        height = textureImage.shape[0]
        width = textureImage.shape[1]
        textureData = Texture.textureToData(textureImage)
        dpg.add_raw_texture(width=width, height=height, default_value=textureData, tag=textureTag, parent='textureRegistry')
        # dpg.add_image(textureTag, parent=textureTag + 'Parent', tag=textureTag + 'Image')
        dpg.add_image_series(texture_tag=textureTag, parent=textureTag + "_y_axis", bounds_min=[0, 0], bounds_max=[width, height], tag=textureTag + 'Image')
        dpg.fit_axis_data(textureTag + "_x_axis")
        dpg.fit_axis_data(textureTag + "_y_axis")
        pass

    def deleteTexture(textureTag):
        try:
            dpg.delete_item(textureTag)
            dpg.delete_item(textureTag + 'Image')
        except:
            pass
        pass

    def updateTexture(textureTag, textureImage):
        textureData = Texture.textureToData(textureImage)
        dpg.set_value(textureTag, textureData)
        pass

    def createAllTextures(textureImage):
        for tab in Tabs:
            Texture.createTexture(tab.name, textureImage)

    def deleteAllTextures():
        for tab in Tabs:
            Texture.deleteTexture(tab.name)
        pass

    def updateAllTextures(textureImage):
        for tab in Tabs:
            Texture.updateTexture(tab.name, textureImage)
        pass

    def textureToData(texture):
        auxImg = cv2.cvtColor(texture, cv2.COLOR_RGB2BGRA)
        auxImg = np.asfarray(auxImg, dtype='f')
        auxImg = auxImg.ravel()
        auxImg = np.true_divide(auxImg, 255.0)
        return auxImg