from ._contourExtraction import ContourExtraction

class Callbacks:
    def __init__(self) -> None:
        self.contourExtraction = ContourExtraction()
        self.meshGeneration = self.contourExtraction.meshGeneration
        self.imageProcessing = self.contourExtraction.imageProcessing
        self.interpolation = self.contourExtraction.interpolation

    def refreshTranslations(self, old_locale=None):
        self.imageProcessing.refreshTranslations()
        self.contourExtraction.refreshTranslations()
        self.interpolation.refreshTranslations()
        self.meshGeneration.refreshTranslations(old_locale)
