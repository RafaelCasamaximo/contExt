import dearpygui.dearpygui as dpg

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

        self.state = {
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

    def next(self, currentMethod):
        self.blocks[self.nameHelper.index(currentMethod) + 1]()
        pass

    def importImage(self, sender, app_data):
        print('importImage')
        print(app_data)
        self.next(self.importImage.__name__)
        pass

    def crop(self):
        print('crop')
        self.next(self.crop.__name__)
        pass

    def histogramEqualization(self):
        print('histogramEqualization')
        self.next(self.histogramEqualization.__name__)
        pass

    def brightnessAndContrast(self):
        print('brightnessAndContrast')
        self.next(self.brightnessAndContrast.__name__)
        pass

    def averageBlur(self):
        print('averageBlur')
        self.next(self.averageBlur.__name__)
        pass

    def gaussianBlur(self):
        print('gaussianBlur')
        self.next(self.gaussianBlur.__name__)
        pass

    def grayscale(self):
        print('grayscale')
        self.next(self.grayscale.__name__)
        pass

    def globalThresholding(self):
        print('globalThresholding')
        self.next(self.globalThresholding.__name__)
        pass

    def adaptativeMeanThresholding(self):
        print('adaptativeMeanThresholding')
        self.next(self.adaptativeMeanThresholding.__name__)
        pass

    def adaptativeGaussianThresholding(self):
        print('adaptativeGaussianThresholding')
        self.next(self.adaptativeGaussianThresholding.__name__)
        pass

    def otsuBinarization(self):
        print('otsuBinarization')
        self.next(self.otsuBinarization.__name__)
        pass

    def findContour(self):
        print('findContour')
        self.next(self.findContour.__name__)
        pass

    def mooreNeighborhood(self):
        print('mooreNeighborhood')
        self.next(self.mooreNeighborhood.__name__)
        pass

    def exportSettings(self):
        print('exportSettings')
        pass
