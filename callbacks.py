from pprint import pprint
import dearpygui.dearpygui as dpg
import numpy as np
import cv2

class Callbacks:
    def __init__(self) -> None:
        self.blocks = [self.importImage, self.crop, self.histogramEqualization, self.brightnessAndContrast,
        self.averageBlur, self.gaussianBlur, self.grayscale, self.globalThresholding, self.adaptativeMeanThresholding,
        self.adaptativeGaussianThresholding, self.otsuBinarization, self.findContour, self.mooreNeighborhood, self.exportSettings]

        self.nameHelper = [
            'importImage',
            'crop',
            'histogramEqualization',
            'brightnessAndContrast',
            'averageBlur',
            'gaussianBlur',
            'grayscale',
            'globalThresholding',
            'adaptativeMeanThresholding',
            'adaptativeGaussianThresholding',
            'otsuBinarization',
            'findContour',
            'mooreNeighborhood',
            'exportSettings',
        ]

        self.activationStatus = {
            'importImage': True,
            'crop': False,
            'histogramEqualization': False,
            'brightnessAndContrast': False,
            'averageBlur': False,
            'gaussianBlur': False,
            'grayscale': True,
            'globalThresholding': False,
            'adaptativeMeanThresholding': False,
            'adaptativeGaussianThresholding': False,
            'otsuBinarization': False,
            'findContour': False,
            'mooreNeighborhood': False,
            'exportSettings': False,
        }

        self.state = {
            'latestOutput'
            'importImageOutput': None,
            'cropOutput': None,
            'histogramEqualizationOutput': None,
            'brightnessAndContrastOutput': None,
            'averageBlurOutput': None,
            'gaussianBlurOutput': None,
            'grayscaleOutput': None,
            'globalThresholdingOutput': None,
            'adaptativeMeanThresholdingOutput': None,
            'adaptativeGaussianThresholdingOutput': None,
            'otsuBinarizationOutput': None,
            'findContourOutput': None,
            'mooreNeighborhoodOutput': None,
            'exportSettingsOutput': None,
        }
        

        
    pass

    def setMethodActiveStatus(self, sender = None, app_data = None, method = None):
        self.activationStatus[method] = dpg.get_value(sender)
        pass


    def next(self, currentMethod):
        self.blocks[self.nameHelper.index(currentMethod) + 1]()
        pass

    def importImage(self, sender=None, app_data=None):

        if self.activationStatus[self.importImage.__name__] is False:
            self.next(self.importImage.__name__)
            return

        print('importImage')
        img = cv2.imread(app_data['file_path_name'], cv2.IMREAD_COLOR)
        
        # height, width, number of channels in image
        height = img.shape[0]
        width = img.shape[1]

        dpg.set_value('file_name_text', 'File Name: ' + app_data['file_name'])
        dpg.set_value('file_path_text', 'File Path: ' + app_data['file_path_name'])
        dpg.set_value('originalWidth', 'Width: ' + str(width) + 'px')
        dpg.set_value('originalHeight', 'Height: ' + str(height) + 'px')
        dpg.set_value('currentWidth', 'Width: ' + str(width) + 'px')
        dpg.set_value('currentHeight', 'Height: ' + str(height) + 'px')

        self.state['importImageOutput'] = {
            'image': img,
        }

        self.state['latestOutput'] = {
            'image': img,
        }

        auxImg = np.flip(img, 2)
        auxImg = np.asfarray(auxImg, dtype='f')  # change data type to 32bit floats
        auxImg = auxImg.ravel()
        auxImg = np.true_divide(auxImg, 255.0)  # normalize image data to prepare for GPU

        try:
            dpg.add_texture_registry(show=False, tag='texture_registry')
            dpg.add_raw_texture(width=width, height=height, default_value=auxImg, tag="processing", parent='texture_registry', format=dpg.mvFormat_Float_rgb)
            dpg.add_image('processing', parent='processingImageParent', tag='processingImage')
        except:
            dpg.delete_item('processing')
            dpg.delete_item('processingImage')
            dpg.add_raw_texture(width=width, height=height, default_value=auxImg, tag="processing", parent='texture_registry', format=dpg.mvFormat_Float_rgb)
            dpg.add_image('processing', parent='processingImageParent', tag='processingImage')

            
        self.next(self.importImage.__name__)
        pass

    def resetCrop(self, sender = None, app_data = None):
        if self.activationStatus[self.crop.__name__] is False:
            self.next(self.crop.__name__)
            return

        print('reset crop')
        croppedImage = self.state['latestOutput']['image']

        self.state['cropOutput'] = {
            'image': croppedImage,
        }

        self.state['latestOutput'] = {
            'image': croppedImage,
        }

        height = croppedImage.shape[0]
        width = croppedImage.shape[1]

        dpg.set_value('currentWidth', 'Width: ' + str(width) + 'px')
        dpg.set_value('currentHeight', 'Height: ' + str(height) + 'px')

        auxImg = np.flip(croppedImage, 2)
        auxImg = np.asfarray(auxImg, dtype='f')  # change data type to 32bit floats
        auxImg = auxImg.ravel()
        auxImg = np.true_divide(auxImg, 255.0)  # normalize image data to prepare for GPU

        try:
            dpg.add_texture_registry(show=False, tag='texture_registry')
            dpg.add_raw_texture(width=width, height=height, default_value=auxImg, tag="processing", parent='texture_registry', format=dpg.mvFormat_Float_rgb)
            dpg.add_image('processing', parent='processingImageParent', tag='processingImage')
        except:
            dpg.delete_item('processing')
            dpg.delete_item('processingImage')
            dpg.add_raw_texture(width=width, height=height, default_value=auxImg, tag="processing", parent='texture_registry', format=dpg.mvFormat_Float_rgb)
            dpg.add_image('processing', parent='processingImageParent', tag='processingImage')



        self.next(self.crop.__name__)
        pass

    def crop(self, sender=None, app_data=None):

        if self.activationStatus[self.crop.__name__] is False:
            self.next(self.crop.__name__)
            return

        print('crop')
        startX = dpg.get_value('startX')
        endX = dpg.get_value('endX')
        startY = dpg.get_value('startY')
        endY = dpg.get_value('endY')
        croppedImage = self.state['latestOutput']['image'][startX:endX, startY:endY]

        self.state['cropOutput'] = {
            'image': croppedImage,
        }

        self.state['latestOutput'] = {
            'image': croppedImage,
        }

        height = croppedImage.shape[0]
        width = croppedImage.shape[1]

        dpg.set_value('currentWidth', 'Width: ' + str(width) + 'px')
        dpg.set_value('currentHeight', 'Height: ' + str(height) + 'px')

        auxImg = np.flip(croppedImage, 2)
        auxImg = np.asfarray(auxImg, dtype='f')  # change data type to 32bit floats
        auxImg = auxImg.ravel()
        auxImg = np.true_divide(auxImg, 255.0)  # normalize image data to prepare for GPU

        try:
            dpg.add_texture_registry(show=False, tag='texture_registry')
            dpg.add_raw_texture(width=width, height=height, default_value=auxImg, tag="processing", parent='texture_registry', format=dpg.mvFormat_Float_rgb)
            dpg.add_image('processing', parent='processingImageParent', tag='processingImage')
        except:
            dpg.delete_item('processing')
            dpg.delete_item('processingImage')
            dpg.add_raw_texture(width=width, height=height, default_value=auxImg, tag="processing", parent='texture_registry', format=dpg.mvFormat_Float_rgb)
            dpg.add_image('processing', parent='processingImageParent', tag='processingImage')



        self.next(self.crop.__name__)
        pass

    def histogramEqualization(self, sender=None, app_data=None):

        if self.activationStatus[self.histogramEqualization.__name__] is False:
            self.next(self.histogramEqualization.__name__)
            return

        print('histogramEqualization')

        img = self.state['latestOutput']['image']
        dst = cv2.equalizeHist(img)

        height = dst.shape[0]
        width = dst.shape[1]

        auxImg = np.flip(dst, 2)
        auxImg = np.asfarray(auxImg, dtype='f')  # change data type to 32bit floats
        auxImg = auxImg.ravel()
        auxImg = np.true_divide(auxImg, 255.0)  # normalize image data to prepare for GPU

        try:
            dpg.add_texture_registry(show=False, tag='texture_registry')
            dpg.add_raw_texture(width=width, height=height, default_value=auxImg, tag="processing", parent='texture_registry', format=dpg.mvFormat_Float_rgb)
            dpg.add_image('processing', parent='FilteringImageParent', tag='processingImage')
        except:
            dpg.delete_item('processing')
            dpg.delete_item('processingImage')
            dpg.add_raw_texture(width=width, height=height, default_value=auxImg, tag="processing", parent='texture_registry', format=dpg.mvFormat_Float_rgb)
            dpg.add_image('processing', parent='FilteringImageParent', tag='processingImage')

        self.next(self.histogramEqualization.__name__)
        pass

    def brightnessAndContrast(self, sender=None, app_data=None):

        if self.activationStatus[self.brightnessAndContrast.__name__] is False:
            self.next(self.brightnessAndContrast.__name__)
            return

        print('brightnessAndContrast')
        self.next(self.brightnessAndContrast.__name__)
        pass

    def averageBlur(self, sender=None, app_data=None):

        if self.activationStatus[self.averageBlur.__name__] is False:
            self.next(self.averageBlur.__name__)
            return

        print('averageBlur')
        self.next(self.averageBlur.__name__)
        pass

    def gaussianBlur(self, sender=None, app_data=None):

        if self.activationStatus[self.gaussianBlur.__name__] is False:
            self.next(self.gaussianBlur.__name__)
            return

        print('gaussianBlur')
        self.next(self.gaussianBlur.__name__)
        pass

    def grayscale(self, sender=None, app_data=None):

        if self.activationStatus[self.grayscale.__name__] is False:
            self.next(self.grayscale.__name__)
            return

        print('grayscale')
        self.next(self.grayscale.__name__)
        pass

    def globalThresholding(self, sender=None, app_data=None):

        if self.activationStatus[self.globalThresholding.__name__] is False:
            self.next(self.globalThresholding.__name__)
            return
        
        print('globalThresholding')
        self.next(self.globalThresholding.__name__)
        pass

    def adaptativeMeanThresholding(self, sender=None, app_data=None):

        if self.activationStatus[self.adaptativeMeanThresholding.__name__] is False:
            self.next(self.adaptativeMeanThresholding.__name__)
            return

        print('adaptativeMeanThresholding')
        self.next(self.adaptativeMeanThresholding.__name__)
        pass

    def adaptativeGaussianThresholding(self, sender=None, app_data=None):

        if self.activationStatus[self.adaptativeGaussianThresholding.__name__] is False:
            self.next(self.adaptativeGaussianThresholding.__name__)
            return

        print('adaptativeGaussianThresholding')
        self.next(self.adaptativeGaussianThresholding.__name__)
        pass

    def otsuBinarization(self, sender=None, app_data=None):

        if self.activationStatus[self.otsuBinarization.__name__] is False:
            self.next(self.otsuBinarization.__name__)
            return

        print('otsuBinarization')
        self.next(self.otsuBinarization.__name__)
        pass

    def findContour(self, sender=None, app_data=None):

        if self.activationStatus[self.findContour.__name__] is False:
            self.next(self.findContour.__name__)
            return

        print('findContour')
        self.next(self.findContour.__name__)
        pass

    def mooreNeighborhood(self, sender=None, app_data=None):

        if self.activationStatus[self.mooreNeighborhood.__name__] is False:
            self.next(self.mooreNeighborhood.__name__)
            return

        print('mooreNeighborhood')
        self.next(self.mooreNeighborhood.__name__)
        pass

    def exportSettings(self, sender=None, app_data=None):

        if self.activationStatus[self.exportSettings.__name__] is False:
            return

        print('exportSettings')
        pass
