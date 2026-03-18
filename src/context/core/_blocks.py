import enum

class Blocks(enum.Enum):
    __order__ = 'importImage crop histogramEqualization claheEqualization brightnessAndContrast averageBlur gaussianBlur medianBlur grayscale laplacian sobel globalThresholding adaptiveMeanThresholding adaptiveGaussianThresholding otsuBinarization findContour'
    importImage = 0
    crop = 1
    histogramEqualization = 2
    claheEqualization = 3
    brightnessAndContrast = 4
    averageBlur = 5
    gaussianBlur = 6
    medianBlur = 7
    grayscale = 8
    laplacian = 9
    sobel = 10
    globalThresholding = 11
    adaptiveMeanThresholding = 12
    adaptiveGaussianThresholding = 13
    otsuBinarization = 14
    findContour = 15
