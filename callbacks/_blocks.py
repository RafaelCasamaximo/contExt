import enum

class Blocks(enum.Enum):
    __order__ = 'importImage crop histogramEqualization brightnessAndContrast averageBlur gaussianBlur medianBlur grayscale laplacian sobel globalThresholding adaptativeMeanThresholding adaptativeGaussianThresholding otsuBinarization findContour'
    importImage = 0
    crop = 1
    histogramEqualization = 2
    brightnessAndContrast = 3
    averageBlur = 4
    gaussianBlur = 5
    medianBlur = 6
    grayscale = 7
    laplacian = 8
    sobel = 9
    globalThresholding = 10
    adaptativeMeanThresholding = 11
    adaptativeGaussianThresholding = 12
    otsuBinarization = 13
    findContour = 14