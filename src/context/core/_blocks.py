import enum

class Blocks(enum.Enum):
    __order__ = 'importImage crop histogramEqualization claheEqualization brightnessAndContrast averageBlur gaussianBlur medianBlur gaborFilter frequencyDomainFilter grayscale laplacian sobel globalThresholding adaptiveMeanThresholding adaptiveGaussianThresholding otsuBinarization findContour'
    importImage = 0
    crop = 1
    histogramEqualization = 2
    claheEqualization = 3
    brightnessAndContrast = 4
    averageBlur = 5
    gaussianBlur = 6
    medianBlur = 7
    gaborFilter = 8
    frequencyDomainFilter = 9
    grayscale = 10
    laplacian = 11
    sobel = 12
    globalThresholding = 13
    adaptiveMeanThresholding = 14
    adaptiveGaussianThresholding = 15
    otsuBinarization = 16
    findContour = 17
