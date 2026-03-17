from ._contourExtraction import ContourExtraction
from ._simulation import Simulation

class Callbacks:
    def __init__(self) -> None:
        self.contourExtraction = ContourExtraction()
        self.meshGeneration = self.contourExtraction.meshGeneration
        self.imageProcessing = self.contourExtraction.imageProcessing
        self.interpolation = self.contourExtraction.interpolation
        self.interpolation.meshGeneration = self.meshGeneration
        self.simulation = Simulation()
        self.simulation.attachMeshGeneration(self.meshGeneration)
        self.meshGeneration.setSimulation(self.simulation)

    def refreshTranslations(self, old_locale=None):
        self.imageProcessing.refreshTranslations()
        self.contourExtraction.refreshTranslations()
        self.interpolation.refreshTranslations()
        self.meshGeneration.refreshTranslations(old_locale)
        self.simulation.refreshTranslations(old_locale)
