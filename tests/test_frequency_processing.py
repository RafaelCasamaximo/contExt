from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import dearpygui.dearpygui as dpg
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from context.core._blocks import Blocks
from context.core._imageProcessing import ImageProcessing
from context.ui._filteringTab import showFiltering
from context.ui._frequencyTab import showFrequency
from context.ui._processingTab import showProcessing
from context.ui._thresholdingTab import showThresholding


class CallbackStub:
    pass


class FrequencyProcessingTests(unittest.TestCase):
    def _build_ui(self, image_processing: ImageProcessing) -> None:
        callbacks = CallbackStub()
        callbacks.imageProcessing = image_processing
        with dpg.window():
            dpg.add_texture_registry(show=False, tag="textureRegistry")
            showProcessing(callbacks)
            showFiltering(callbacks)
            showFrequency(callbacks)
            showThresholding(callbacks)

    def test_gabor_filter_preserves_shape_and_changes_image(self) -> None:
        image_processing = ImageProcessing()
        image = np.zeros((48, 48, 3), dtype=np.uint8)
        image[:, ::4] = 255
        image_processing.blocks[Blocks.crop.value]["output"] = image

        dpg.create_context()
        try:
            self._build_ui(image_processing)
            with patch("context.core._imageProcessing.Texture.updateTexture"), patch.object(
                image_processing, "updateHistogramForTab"
            ):
                image_processing.gaborFilter()
        finally:
            dpg.destroy_context()

        output = image_processing.blocks[Blocks.gaborFilter.value]["output"]
        self.assertIsNotNone(output)
        self.assertEqual(output.shape, image.shape)
        self.assertFalse(np.array_equal(output, image))

    def test_frequency_domain_filter_creates_spatial_output_and_spectrum_preview(self) -> None:
        image_processing = ImageProcessing()
        image = np.zeros((64, 64, 3), dtype=np.uint8)
        image[::4, :] = 255
        image_processing.blocks[Blocks.crop.value]["output"] = image
        image_processing.blocks[Blocks.gaborFilter.value]["status"] = True
        image_processing.blocks[Blocks.gaborFilter.value]["output"] = image

        dpg.create_context()
        try:
            self._build_ui(image_processing)
            dpg.set_value("frequencyFilterModeListbox", "Low-pass")
            dpg.set_value("frequencyCutoffSlider", 10)
            with patch("context.core._imageProcessing.Texture.updateTexture"), patch.object(
                image_processing, "updateHistogramForTab"
            ):
                image_processing.frequencyDomainFilter()
        finally:
            dpg.destroy_context()

        output = image_processing.blocks[Blocks.frequencyDomainFilter.value]["output"]
        self.assertIsNotNone(output)
        self.assertEqual(output.shape, image.shape)
        self.assertIsNotNone(image_processing.frequencySpectrumPreview)
        self.assertEqual(image_processing.frequencySpectrumPreview.shape, image.shape)

    def test_manual_frequency_mask_is_symmetric(self) -> None:
        image_processing = ImageProcessing()
        image_processing._ensureFrequencyMask((32, 32))
        image_processing._applyFrequencyMaskCircle(5, 7, 2)

        self.assertTrue(image_processing.frequencyMask[5, 7])
        self.assertTrue(image_processing.frequencyMask[26, 24])


if __name__ == "__main__":
    unittest.main()
