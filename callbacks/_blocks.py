import enum

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