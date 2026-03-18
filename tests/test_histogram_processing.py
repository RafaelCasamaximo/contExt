from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import cv2
import dearpygui.dearpygui as dpg
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from context.core._blocks import Blocks
from context.core._imageProcessing import ImageProcessing
from context.ui._filteringTab import showFiltering
from context.ui._processingTab import showProcessing
from context.ui._thresholdingTab import showThresholding


class CallbackStub:
    pass


class HistogramProcessingTests(unittest.TestCase):
    def test_clahe_equalization_applies_parameters_and_preserves_shape(self) -> None:
        image_processing = ImageProcessing()

        image = np.full((32, 32, 3), 96, dtype=np.uint8)
        image[8:24, 8:24] = 112
        image_processing.blocks[Blocks.crop.value]["output"] = image

        dpg.create_context()
        try:
            with dpg.window():
                dpg.add_slider_float(tag="claheClipLimitSlider", default_value=3.5)
                dpg.add_slider_int(tag="claheTileGridSizeSlider", default_value=4)

            with patch("context.core._imageProcessing.Texture.updateTexture"), patch.object(
                image_processing, "updateHistogramForTab"
            ):
                image_processing.claheEqualization()
        finally:
            dpg.destroy_context()

        output = image_processing.blocks[Blocks.claheEqualization.value]["output"]

        self.assertIsNotNone(output)
        self.assertEqual(output.shape, image.shape)
        self.assertFalse(np.array_equal(output, image))

    def test_clahe_equalization_uses_previous_histogram_block_output(self) -> None:
        image_processing = ImageProcessing()

        image = np.zeros((32, 32, 3), dtype=np.uint8)
        image[:, :16] = 50
        image[:, 16:] = 120
        image_processing.blocks[Blocks.crop.value]["output"] = image
        image_processing.blocks[Blocks.histogramEqualization.value]["status"] = True
        image_processing.blocks[Blocks.claheEqualization.value]["status"] = True

        dpg.create_context()
        try:
            with dpg.window():
                dpg.add_slider_float(tag="claheClipLimitSlider", default_value=2.0)
                dpg.add_slider_int(tag="claheTileGridSizeSlider", default_value=8)

            with patch("context.core._imageProcessing.Texture.updateTexture"), patch.object(
                image_processing, "updateHistogramForTab"
            ):
                image_processing.histogramEqualization()
                image_processing.claheEqualization()
        finally:
            dpg.destroy_context()

        histogram_output = image_processing.blocks[Blocks.histogramEqualization.value]["output"]
        clahe_output = image_processing.blocks[Blocks.claheEqualization.value]["output"]
        expected = cv2.cvtColor(histogram_output, cv2.COLOR_BGR2YUV)
        expected[:, :, 0] = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(expected[:, :, 0])
        expected = cv2.cvtColor(expected, cv2.COLOR_YUV2BGR)

        self.assertTrue(np.array_equal(clahe_output, expected))

    def test_build_histogram_series_handles_color_and_grayscale(self) -> None:
        image_processing = ImageProcessing()

        color_image = np.zeros((8, 8, 3), dtype=np.uint8)
        color_image[:, :, 0] = 25
        color_image[:, :, 1] = 125
        color_image[:, :, 2] = 225
        color_series = image_processing.buildHistogramSeries(color_image)

        self.assertEqual(len(color_series), 3)
        self.assertEqual(sum(color_series[0]["y"]), 64.0)
        self.assertEqual(sum(color_series[1]["y"]), 64.0)
        self.assertEqual(sum(color_series[2]["y"]), 64.0)

        grayscale = np.full((8, 8), 90, dtype=np.uint8)
        grayscale_bgr = np.stack([grayscale, grayscale, grayscale], axis=2)
        grayscale_series = image_processing.buildHistogramSeries(grayscale_bgr)

        self.assertEqual(len(grayscale_series), 1)
        self.assertEqual(grayscale_series[0]["y"][90], 64.0)

    def test_preprocessor_histogram_tabs_and_png_export_smoke(self) -> None:
        image_processing = ImageProcessing()
        callbacks = CallbackStub()
        callbacks.imageProcessing = image_processing

        dpg.create_context()
        try:
            with dpg.window():
                dpg.add_texture_registry(show=False, tag="textureRegistry")
                showProcessing(callbacks)
                showFiltering(callbacks)
                showThresholding(callbacks)

            for tag in (
                "showProcessingHistogramToggle",
                "ProcessingHistogramPanel",
                "ProcessingHistogram_x_axis",
                "showFilteringHistogramToggle",
                "FilteringHistogramPanel",
                "FilteringHistogram_x_axis",
                "claheCheckbox",
                "claheClipLimitSlider",
                "claheTileGridSizeSlider",
                "showThresholdingHistogramToggle",
                "ThresholdingHistogramPanel",
                "ThresholdingHistogram_x_axis",
            ):
                self.assertTrue(dpg.does_item_exist(tag))

            color_image = np.zeros((16, 16, 3), dtype=np.uint8)
            color_image[:, :8, 2] = 255
            color_image[:, 8:, 1] = 180

            grayscale = np.full((16, 16), 127, dtype=np.uint8)
            grayscale_bgr = np.stack([grayscale, grayscale, grayscale], axis=2)

            image_processing.blocks[Blocks.importImage.value]["output"] = color_image
            image_processing.blocks[Blocks.crop.value]["output"] = color_image
            image_processing.blocks[Blocks.grayscale.value]["output"] = grayscale_bgr

            image_processing.toggleHistogramPanel("Processing", True)
            self.assertTrue(dpg.does_item_exist("ProcessingHistogramSeries0"))

            with tempfile.TemporaryDirectory() as temp_dir:
                for tab in ("Processing", "Filtering", "Thresholding"):
                    output_path = Path(temp_dir) / f"{tab.lower()}_histogram.png"
                    image_processing.exportHistogramToFile(tab, str(output_path))
                    self.assertTrue(output_path.exists())
                    self.assertGreater(output_path.stat().st_size, 0)
        finally:
            dpg.destroy_context()


if __name__ == "__main__":
    unittest.main()
