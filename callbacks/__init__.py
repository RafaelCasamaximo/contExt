from ._contourExtraction import ContourExtraction

class Callbacks:
    def __init__(self) -> None:
        self.contourExtraction = ContourExtraction()
        self.meshGeneration = self.contourExtraction.meshGeneration
        self.imageProcessing = self.contourExtraction.imageProcessing
        self.interpolation = self.contourExtraction.interpolation