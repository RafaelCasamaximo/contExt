from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import dearpygui.dearpygui as dpg

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from context.core._simulation import Simulation
from context.ui._simulationTab import showSimulation


class MeshStub:
    def __init__(self) -> None:
        self.currentX = [0.0, 1.0, 1.0, 0.0, 0.0]
        self.currentY = [0.0, 0.0, 1.0, 1.0, 0.0]
        self.currentMeshInfo = {
            "nx": 5,
            "ny": 5,
            "xmin": 0.0,
            "ymin": 0.0,
            "dx": 0.25,
            "dy": 0.25,
        }
        self.subcontoursRanges = [[0, 1], [1, 2], [2, 3], [3, 4]]
        self.sparseMeshHandler = None


class CallbackStub:
    pass


class SimulationExportTests(unittest.TestCase):
    def test_scale_widget_and_png_export_smoke(self) -> None:
        simulation = Simulation()
        simulation.attachMeshGeneration(MeshStub())
        callbacks = CallbackStub()
        callbacks.simulation = simulation

        dpg.create_context()
        try:
            with dpg.window():
                showSimulation(callbacks)

            simulation.syncWithMesh()
            simulation.region_values = {0: 0.0, 1: 1.0, 2: 1.0, 3: 0.0}
            simulation.solve()

            self.assertIsNotNone(simulation.result)
            self.assertTrue(dpg.does_item_exist("simulationColorScale"))

            with tempfile.TemporaryDirectory() as temp_dir:
                output_path = Path(temp_dir) / "field.png"
                simulation.exportVisualizationPngToFile(str(output_path))
                self.assertTrue(output_path.exists())
                self.assertGreater(output_path.stat().st_size, 0)
        finally:
            dpg.destroy_context()


if __name__ == "__main__":
    unittest.main()
