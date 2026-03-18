import dearpygui.dearpygui as dpg
import numpy as np
import cv2
import pydicom
import os.path
from ._blocks import Blocks
from ._texture import Texture
from ..ui import strings

DEFAULT_CLAHE_CLIP_LIMIT = 2.0
DEFAULT_CLAHE_TILE_GRID_SIZE = 8
DEFAULT_GABOR_KERNEL_SIZE = 11
DEFAULT_GABOR_SIGMA = 4.0
DEFAULT_GABOR_THETA = 0.0
DEFAULT_GABOR_LAMBDA = 10.0
DEFAULT_GABOR_GAMMA = 0.5
DEFAULT_GABOR_PSI = 0.0
DEFAULT_FREQUENCY_CUTOFF = 24
DEFAULT_FREQUENCY_BAND_MIN = 12
DEFAULT_FREQUENCY_BAND_MAX = 48
DEFAULT_FREQUENCY_MASK_RADIUS = 8

class ImageProcessing:
    def __init__(self) -> None:

        self.filePath = None
        self.fileName = None
        self.exportImageFilePath = None
        self.exportHistogramFilePath = None
        self.currentTab = None
        self.currentHistogramTab = None
        self.resetContours = None
        self.originalResolution = None
        self.currentResolution = None
        self.histogramPlotState = {
            "Processing": {"series": [], "themes": []},
            "Filtering": {"series": [], "themes": []},
            "Frequency": {"series": [], "themes": []},
            "Thresholding": {"series": [], "themes": []},
        }
        self.frequencyMask = None
        self.frequencyMaskShape = None
        self.frequencyMaskMode = "draw"
        self.frequencySpectrumPreview = None

        self.blocks = [
            {
                'method': self.importImage,
                'name': self.importImage.__name__,
                'status': True,
                'output': None,
                'tab': 'Processing'
            },
            {
                'method': self.crop,
                'name': self.crop.__name__,
                'status': True,
                'output': None,
                'tab': 'Processing'
            },
            {
                'method': self.histogramEqualization,
                'name': self.histogramEqualization.__name__,
                'status': False,
                'output': None,
                'tab': 'Filtering'
            },
            {
                'method': self.claheEqualization,
                'name': self.claheEqualization.__name__,
                'status': False,
                'output': None,
                'tab': 'Filtering'
            },
            {
                'method': self.brightnessAndContrast,
                'name': self.brightnessAndContrast.__name__,
                'status': False,
                'output': None,
                'tab': 'Filtering'
            },
            {
                'method': self.averageBlur,
                'name': self.averageBlur.__name__,
                'status': False,
                'output': None,
                'tab': 'Filtering'
            },
            {
                'method': self.gaussianBlur,
                'name': self.gaussianBlur.__name__,
                'status': False,
                'output': None,
                'tab': 'Filtering'
            },
            {
                'method': self.medianBlur,
                'name': self.medianBlur.__name__,
                'status': False,
                'output': None,
                'tab': 'Filtering'
            },
            {
                'method': self.gaborFilter,
                'name': self.gaborFilter.__name__,
                'status': False,
                'output': None,
                'tab': 'Frequency'
            },
            {
                'method': self.frequencyDomainFilter,
                'name': self.frequencyDomainFilter.__name__,
                'status': False,
                'output': None,
                'tab': 'Frequency'
            },
            {
                'method': self.grayscale,
                'name': self.grayscale.__name__,
                'status': True,
                'output': None,
                'tab': 'Thresholding'
            },
            {
                'method': self.laplacian,
                'name': self.laplacian.__name__,
                'status': False,
                'output': None,
                'tab': 'Thresholding'
            },
            {
                'method': self.sobel,
                'name': self.sobel.__name__,
                'status': False,
                'output': None,
                'tab': 'Thresholding'
            },
            {
                'method': self.globalThresholding,
                'name': self.globalThresholding.__name__,
                'status': False,
                'output': None,
                'tab': 'Thresholding'
            },
            {
                'method': self.adaptiveMeanThresholding,
                'name': self.adaptiveMeanThresholding.__name__,
                'status': False,
                'output': None,
                'tab': 'Thresholding'
            },
            {
                'method': self.adaptiveGaussianThresholding,
                'name': self.adaptiveGaussianThresholding.__name__,
                'status': False,
                'output': None,
                'tab': 'Thresholding'
            },
            {
                'method': self.otsuBinarization,
                'name': self.otsuBinarization.__name__,
                'status': False,
                'output': None,
                'tab': 'Thresholding'
            },
            {
                'method': self.findContour,
                'name': self.findContour.__name__,
                'status': True,
                'output': None,
                'tab': 'ContourExtraction'
            },
        ]

        pass

    def getCurrentResolution(self):
        return self.currentResolution

    def renderFileInfo(self):
        dpg.set_value('file_name_text', strings.fmt("file_name", value=self.fileName or ""))
        dpg.set_value('file_path_text', strings.fmt("file_path", value=self.filePath or ""))

    def renderResolutionInfo(self):
        original_width = "--"
        original_height = "--"
        current_width = "--"
        current_height = "--"

        if self.originalResolution is not None:
            original_width = self.originalResolution[0]
            original_height = self.originalResolution[1]
        if self.currentResolution is not None:
            current_width = self.currentResolution[0]
            current_height = self.currentResolution[1]

        dpg.set_value('originalWidth', strings.fmt("width_px", value=original_width))
        dpg.set_value('originalHeight', strings.fmt("height_px", value=original_height))
        dpg.set_value('currentWidth', strings.fmt("width_px", value=current_width))
        dpg.set_value('currentHeight', strings.fmt("height_px", value=current_height))

    def renderExportState(self):
        export_file_name = ""
        export_full_path = ""

        if self.exportImageFilePath is not None:
            export_file_name = os.path.basename(self.exportImageFilePath)
            export_full_path = self.exportImageFilePath

        dpg.set_value('exportImageFileName', strings.fmt("file_name", value=export_file_name))
        dpg.set_value('exportImageFilePath', strings.fmt("full_path", value=export_full_path))

    def renderHistogramExportState(self):
        export_file_name = ""
        export_full_path = ""

        if self.exportHistogramFilePath is not None:
            export_file_name = os.path.basename(self.exportHistogramFilePath)
            export_full_path = self.exportHistogramFilePath

        dpg.set_value('exportHistogramFileName', strings.fmt("file_name", value=export_file_name))
        dpg.set_value('exportHistogramFilePath', strings.fmt("full_path", value=export_full_path))

    def refreshTranslations(self):
        self.renderFileInfo()
        self.renderResolutionInfo()
        self.renderExportState()
        if dpg.does_item_exist('exportHistogramFileName'):
            self.renderHistogramExportState()

    def _stageMethodByTab(self, tab):
        return {
            'Processing': Blocks.histogramEqualization.name,
            'Filtering': Blocks.gaborFilter.name,
            'Frequency': Blocks.grayscale.name,
            'Thresholding': Blocks.findContour.name,
        }[tab]

    def _histogramPlotAxes(self, tab):
        return {
            'Processing': ("ProcessingHistogram_x_axis", "ProcessingHistogram_y_axis"),
            'Filtering': ("FilteringHistogram_x_axis", "FilteringHistogram_y_axis"),
            'Frequency': ("FrequencyHistogram_x_axis", "FrequencyHistogram_y_axis"),
            'Thresholding': ("ThresholdingHistogram_x_axis", "ThresholdingHistogram_y_axis"),
        }[tab]

    def _histogramPanelTag(self, tab):
        return {
            'Processing': "ProcessingHistogramPanel",
            'Filtering': "FilteringHistogramPanel",
            'Frequency': "FrequencyHistogramPanel",
            'Thresholding': "ThresholdingHistogramPanel",
        }[tab]

    def _histogramImagePanelTag(self, tab):
        return {
            'Processing': "ProcessingImagePanel",
            'Filtering': "FilteringImagePanel",
            'Frequency': "FrequencyParent",
            'Thresholding': "ThresholdingImagePanel",
        }[tab]

    def _histogramStageTitle(self, tab):
        return {
            'Processing': strings.t("app.tabs.processing"),
            'Filtering': strings.t("app.tabs.filtering"),
            'Frequency': strings.t("app.tabs.frequency"),
            'Thresholding': strings.t("app.tabs.thresholding"),
        }[tab]

    def _histogramLegendColor(self, label):
        colors = {
            strings.t("histogram.channel_red"): (230, 76, 60, 255),
            strings.t("histogram.channel_green"): (46, 204, 113, 255),
            strings.t("histogram.channel_blue"): (52, 152, 219, 255),
            strings.t("histogram.channel_intensity"): (108, 117, 125, 255),
        }
        return colors[label]

    def _isGrayscaleImage(self, image):
        if image is None:
            return True
        if len(image.shape) == 2:
            return True
        if image.shape[2] == 1:
            return True
        return (
            np.array_equal(image[:, :, 0], image[:, :, 1])
            and np.array_equal(image[:, :, 1], image[:, :, 2])
        )

    def getCurrentOutputForTab(self, tab):
        method_name = self._stageMethodByTab(tab)
        return self.blocks[self.getLastActiveBeforeMethod(method_name)]['output']

    def buildHistogramSeries(self, image):
        bins = list(range(256))
        if image is None:
            return []

        if self._isGrayscaleImage(image):
            grayscale = image if len(image.shape) == 2 else image[:, :, 0]
            histogram = cv2.calcHist([grayscale], [0], None, [256], [0, 256]).ravel()
            return [
                {
                    "label": strings.t("histogram.channel_intensity"),
                    "x": bins,
                    "y": histogram.tolist(),
                    "color": self._histogramLegendColor(strings.t("histogram.channel_intensity")),
                }
            ]

        channel_config = [
            (2, strings.t("histogram.channel_red")),
            (1, strings.t("histogram.channel_green")),
            (0, strings.t("histogram.channel_blue")),
        ]
        histogram_series = []
        for channel_index, label in channel_config:
            histogram = cv2.calcHist([image], [channel_index], None, [256], [0, 256]).ravel()
            histogram_series.append(
                {
                    "label": label,
                    "x": bins,
                    "y": histogram.tolist(),
                    "color": self._histogramLegendColor(label),
                }
            )
        return histogram_series

    def _clearHistogramPlot(self, tab):
        state = self.histogramPlotState[tab]
        for tag in state["series"]:
            if dpg.does_item_exist(tag):
                dpg.delete_item(tag)
        for tag in state["themes"]:
            if dpg.does_item_exist(tag):
                dpg.delete_item(tag)
        state["series"].clear()
        state["themes"].clear()

    def _createHistogramTheme(self, tag, color):
        with dpg.theme(tag=tag):
            with dpg.theme_component(dpg.mvLineSeries):
                dpg.add_theme_color(dpg.mvPlotCol_Line, color, category=dpg.mvThemeCat_Plots)

    def updateHistogramForTab(self, tab):
        x_axis_tag, y_axis_tag = self._histogramPlotAxes(tab)
        if not dpg.does_item_exist(y_axis_tag):
            return

        self._clearHistogramPlot(tab)
        image = self.getCurrentOutputForTab(tab)
        histogram_series = self.buildHistogramSeries(image)
        if not histogram_series:
            dpg.set_axis_limits(x_axis_tag, 0, 255)
            dpg.set_axis_limits(y_axis_tag, 0, 1)
            return

        max_value = 1.0
        for index, series in enumerate(histogram_series):
            series_tag = f"{tab}HistogramSeries{index}"
            theme_tag = f"{tab}HistogramTheme{index}"
            self._createHistogramTheme(theme_tag, series["color"])
            dpg.add_line_series(series["x"], series["y"], label=series["label"], parent=y_axis_tag, tag=series_tag)
            dpg.bind_item_theme(series_tag, theme_tag)
            self.histogramPlotState[tab]["series"].append(series_tag)
            self.histogramPlotState[tab]["themes"].append(theme_tag)
            max_value = max(max_value, max(series["y"]))

        dpg.set_axis_limits(x_axis_tag, 0, 255)
        dpg.set_axis_limits(y_axis_tag, 0, max_value * 1.05)

    def updateAllHistograms(self):
        for tab in self.histogramPlotState.keys():
            self.updateHistogramForTab(tab)

    def toggleHistogramPanel(self, tab, enabled):
        panel_tag = self._histogramPanelTag(tab)
        image_panel_tag = self._histogramImagePanelTag(tab)
        if dpg.does_item_exist(panel_tag):
            dpg.configure_item(panel_tag, show=bool(enabled))
        if dpg.does_item_exist(image_panel_tag):
            dpg.configure_item(image_panel_tag, height=-260 if enabled else -1)
        if enabled:
            self.updateHistogramForTab(tab)

    def _storeBlockOutput(self, block_index, image):
        self.blocks[block_index]['output'] = image
        if dpg.does_item_exist(self.blocks[block_index]['tab']):
            Texture.updateTexture(self.blocks[block_index]['tab'], image)
        tab = self.blocks[block_index]['tab']
        if tab in self.histogramPlotState:
            self.updateHistogramForTab(tab)
        if block_index <= Blocks.frequencyDomainFilter.value:
            self.updateFrequencyPreview()

    def _rgbToBgr(self, color):
        return int(color[2]), int(color[1]), int(color[0])

    def _grayscaleImage(self, image):
        if image is None:
            return None
        if len(image.shape) == 2:
            return image.copy()
        if image.shape[2] == 1:
            return image[:, :, 0].copy()
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    def _applyLuminanceTransform(self, image, transform):
        img_yuv = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)
        img_yuv[:, :, 0] = transform(img_yuv[:, :, 0])
        return cv2.cvtColor(img_yuv, cv2.COLOR_YUV2BGR)

    def _claheParameters(self):
        clip_limit = DEFAULT_CLAHE_CLIP_LIMIT
        tile_grid_size = DEFAULT_CLAHE_TILE_GRID_SIZE

        if dpg.does_item_exist('claheClipLimitSlider'):
            clip_limit = float(dpg.get_value('claheClipLimitSlider'))
        if dpg.does_item_exist('claheTileGridSizeSlider'):
            tile_grid_size = int(dpg.get_value('claheTileGridSizeSlider'))

        return clip_limit, max(1, tile_grid_size)

    def _gaborParameters(self):
        kernel_size = DEFAULT_GABOR_KERNEL_SIZE
        sigma = DEFAULT_GABOR_SIGMA
        theta = DEFAULT_GABOR_THETA
        lambd = DEFAULT_GABOR_LAMBDA
        gamma = DEFAULT_GABOR_GAMMA
        psi = DEFAULT_GABOR_PSI

        if dpg.does_item_exist('gaborKernelSlider'):
            kernel_size = int(dpg.get_value('gaborKernelSlider'))
        if dpg.does_item_exist('gaborSigmaSlider'):
            sigma = float(dpg.get_value('gaborSigmaSlider'))
        if dpg.does_item_exist('gaborThetaSlider'):
            theta = float(dpg.get_value('gaborThetaSlider'))
        if dpg.does_item_exist('gaborLambdaSlider'):
            lambd = float(dpg.get_value('gaborLambdaSlider'))
        if dpg.does_item_exist('gaborGammaSlider'):
            gamma = float(dpg.get_value('gaborGammaSlider'))
        if dpg.does_item_exist('gaborPsiSlider'):
            psi = float(dpg.get_value('gaborPsiSlider'))

        if kernel_size % 2 == 0:
            kernel_size += 1
        return kernel_size, sigma, np.deg2rad(theta), lambd, gamma, np.deg2rad(psi)

    def _frequencyFilterMode(self):
        if dpg.does_item_exist('frequencyFilterModeListbox'):
            return strings.option_key("frequency_filter_mode", dpg.get_value('frequencyFilterModeListbox'))
        return "none"

    def _frequencyFilterParameters(self):
        cutoff = DEFAULT_FREQUENCY_CUTOFF
        band_min = DEFAULT_FREQUENCY_BAND_MIN
        band_max = DEFAULT_FREQUENCY_BAND_MAX

        if dpg.does_item_exist('frequencyCutoffSlider'):
            cutoff = int(dpg.get_value('frequencyCutoffSlider'))
        if dpg.does_item_exist('frequencyBandMinSlider'):
            band_min = int(dpg.get_value('frequencyBandMinSlider'))
        if dpg.does_item_exist('frequencyBandMaxSlider'):
            band_max = int(dpg.get_value('frequencyBandMaxSlider'))
        if band_min > band_max:
            band_min, band_max = band_max, band_min

        return max(1, cutoff), max(1, band_min), max(1, band_max)

    def _frequencyMaskRadius(self):
        if dpg.does_item_exist('frequencyMaskRadiusSlider'):
            return max(1, int(dpg.get_value('frequencyMaskRadiusSlider')))
        return DEFAULT_FREQUENCY_MASK_RADIUS

    def _frequencySourceImage(self):
        return self.blocks[self.getLastActiveBeforeMethod('frequencyDomainFilter')]['output']

    def _frequencySpatialOutput(self):
        return self.blocks[self.getLastActiveBeforeMethod('grayscale')]['output']

    def _resetFrequencyState(self):
        self.frequencyMask = None
        self.frequencyMaskShape = None
        self.frequencySpectrumPreview = None
        self.frequencyMaskMode = "draw"
        if dpg.does_item_exist("frequencyMaskModeButton"):
            dpg.configure_item("frequencyMaskModeButton", label=strings.t("frequency.mask_mode_draw"))

    def _ensureFrequencyMask(self, shape):
        if self.frequencyMask is None or self.frequencyMaskShape != shape:
            self.frequencyMask = np.zeros(shape, dtype=bool)
            self.frequencyMaskShape = shape

    def _frequencySpectrumPreviewImage(self, shifted_spectrum):
        magnitude = np.log1p(np.abs(shifted_spectrum))
        normalized = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX)
        preview = normalized.astype(np.uint8)
        return cv2.cvtColor(preview, cv2.COLOR_GRAY2BGR)

    def _frequencyBaseMask(self, shape):
        mode = self._frequencyFilterMode()
        cutoff, band_min, band_max = self._frequencyFilterParameters()
        rows, cols = shape
        center_y = rows // 2
        center_x = cols // 2
        yy, xx = np.ogrid[:rows, :cols]
        distance = np.sqrt((yy - center_y) ** 2 + (xx - center_x) ** 2)
        mask = np.ones((rows, cols), dtype=np.float32)

        if mode == "low_pass":
            mask = (distance <= cutoff).astype(np.float32)
        elif mode == "high_pass":
            mask = (distance >= cutoff).astype(np.float32)
        elif mode == "band_pass":
            mask = ((distance >= band_min) & (distance <= band_max)).astype(np.float32)
        elif mode == "band_stop":
            mask = ((distance < band_min) | (distance > band_max)).astype(np.float32)

        return mask

    def _combinedFrequencyMask(self, shape):
        self._ensureFrequencyMask(shape)
        mask = self._frequencyBaseMask(shape)
        mask[self.frequencyMask] = 0.0
        return mask

    def _updateFrequencySpectrumTexture(self, preview_image):
        self.frequencySpectrumPreview = preview_image
        if dpg.does_item_exist("FrequencySpectrum"):
            Texture.updateTexture("FrequencySpectrum", preview_image)

    def updateFrequencyPreview(self):
        source_image = self._frequencySourceImage()
        if source_image is None:
            return

        grayscale = self._grayscaleImage(source_image)
        self._ensureFrequencyMask(grayscale.shape)
        shifted = np.fft.fftshift(np.fft.fft2(grayscale.astype(np.float32)))
        if self.blocks[Blocks.frequencyDomainFilter.value]['status']:
            shifted = shifted * self._combinedFrequencyMask(grayscale.shape)
        self._updateFrequencySpectrumTexture(self._frequencySpectrumPreviewImage(shifted))

    def handleFrequencyControlChange(self, sender=None, app_data=None):
        if self._frequencyFilterMode() != "none":
            self.blocks[Blocks.frequencyDomainFilter.value]['status'] = True
            if dpg.does_item_exist("frequencyDomainCheckbox"):
                dpg.set_value("frequencyDomainCheckbox", True)

        if self.blocks[Blocks.frequencyDomainFilter.value]['status']:
            self.executeQuery('frequencyDomainFilter')
        else:
            self.updateFrequencyPreview()

    def toggleFrequencyMaskMode(self, sender=None, app_data=None):
        self.frequencyMaskMode = "erase" if self.frequencyMaskMode == "draw" else "draw"
        if dpg.does_item_exist("frequencyMaskModeButton"):
            label_key = "frequency.mask_mode_erase" if self.frequencyMaskMode == "erase" else "frequency.mask_mode_draw"
            dpg.configure_item("frequencyMaskModeButton", label=strings.t(label_key))

    def resetFrequencyMask(self, sender=None, app_data=None):
        if self.frequencyMask is not None:
            self.frequencyMask.fill(False)

        if self.blocks[Blocks.frequencyDomainFilter.value]['status']:
            self.executeQuery('frequencyDomainFilter')
        else:
            self.updateFrequencyPreview()

    def _applyFrequencyMaskCircle(self, row, col, radius, erase=False):
        if self.frequencyMask is None:
            return

        rows, cols = self.frequencyMask.shape
        yy, xx = np.ogrid[:rows, :cols]
        mirrored_points = {
            (int(row), int(col)),
            (rows - 1 - int(row), cols - 1 - int(col)),
        }
        for center_row, center_col in mirrored_points:
            circle = (yy - center_row) ** 2 + (xx - center_col) ** 2 <= radius ** 2
            self.frequencyMask[circle] = not erase

    def handleFrequencySpectrumClick(self, sender=None, app_data=None):
        source_image = self._frequencySourceImage()
        if source_image is None:
            return

        grayscale = self._grayscaleImage(source_image)
        self._ensureFrequencyMask(grayscale.shape)
        mouse_x, mouse_y = dpg.get_plot_mouse_pos()
        col = int(round(mouse_x))
        row = int(round(mouse_y))
        if row < 0 or col < 0 or row >= grayscale.shape[0] or col >= grayscale.shape[1]:
            return

        self._applyFrequencyMaskCircle(row, col, self._frequencyMaskRadius(), erase=self.frequencyMaskMode == "erase")
        self.blocks[Blocks.frequencyDomainFilter.value]['status'] = True
        if dpg.does_item_exist("frequencyDomainCheckbox"):
            dpg.set_value("frequencyDomainCheckbox", True)
        self.executeQuery('frequencyDomainFilter')

    def saveHistogramPlotToFile(self, histogram_series, stage_title, path):
        if not histogram_series:
            raise ValueError("No histogram data available for export.")

        canvas_width = 1280
        canvas_height = 780
        margin_left = 90
        margin_top = 70
        margin_bottom = 95
        margin_right = 180
        plot_left = margin_left
        plot_top = margin_top
        plot_right = canvas_width - margin_right
        plot_bottom = canvas_height - margin_bottom
        plot_width = plot_right - plot_left
        plot_height = plot_bottom - plot_top
        max_count = max(max(series["y"]) for series in histogram_series) or 1.0

        canvas = np.full((canvas_height, canvas_width, 3), 255, dtype=np.uint8)
        font = cv2.FONT_HERSHEY_SIMPLEX
        title = f"{stage_title} - {strings.t('histogram.title')}"
        cv2.putText(canvas, title, (margin_left, 34), font, 0.9, (36, 45, 58), 2, cv2.LINE_AA)

        cv2.rectangle(canvas, (plot_left, plot_top), (plot_right, plot_bottom), (122, 130, 138), 1)
        cv2.putText(canvas, strings.t("histogram.intensity_axis"), (plot_left + plot_width // 2 - 35, canvas_height - 28), font, 0.55, (36, 45, 58), 1, cv2.LINE_AA)
        cv2.putText(canvas, strings.t("histogram.count_axis"), (22, plot_top - 14), font, 0.55, (36, 45, 58), 1, cv2.LINE_AA)
        cv2.putText(canvas, "0", (plot_left - 8, plot_bottom + 24), font, 0.45, (90, 99, 109), 1, cv2.LINE_AA)
        cv2.putText(canvas, "255", (plot_right - 20, plot_bottom + 24), font, 0.45, (90, 99, 109), 1, cv2.LINE_AA)
        cv2.putText(canvas, str(int(max_count)), (plot_left - 48, plot_top + 4), font, 0.45, (90, 99, 109), 1, cv2.LINE_AA)
        cv2.putText(canvas, "0", (plot_left - 18, plot_bottom + 4), font, 0.45, (90, 99, 109), 1, cv2.LINE_AA)

        x_points = np.linspace(plot_left, plot_right, 256)
        for series in histogram_series:
            points = []
            for x_point, value in zip(x_points, series["y"]):
                y_point = plot_bottom - (value / max_count) * plot_height
                points.append([int(round(x_point)), int(round(y_point))])
            point_array = np.array(points, dtype=np.int32).reshape((-1, 1, 2))
            cv2.polylines(canvas, [point_array], False, self._rgbToBgr(series["color"]), 2, cv2.LINE_AA)

        legend_x = plot_right + 34
        legend_y = plot_top + 24
        for index, series in enumerate(histogram_series):
            y = legend_y + (index * 34)
            cv2.line(canvas, (legend_x, y), (legend_x + 28, y), self._rgbToBgr(series["color"]), 3, cv2.LINE_AA)
            cv2.putText(canvas, series["label"], (legend_x + 40, y + 4), font, 0.52, (36, 45, 58), 1, cv2.LINE_AA)

        cv2.imwrite(path, canvas)

    def exportHistogramToFile(self, tab, path):
        image = self.getCurrentOutputForTab(tab)
        if image is None:
            raise ValueError("No image available for histogram export.")
        histogram_series = self.buildHistogramSeries(image)
        self.saveHistogramPlotToFile(histogram_series, self._histogramStageTitle(tab), path)


    def executeQuery(self, methodName):
        executeFlag = 0
        for entry in self.blocks:
            if executeFlag == 0 and entry['name'] == methodName:
                executeFlag = 1
            if executeFlag == 1 and entry['status'] is True:
                entry['method']()
        try:
            dpg.get_item_callback("removeExtractContour")()
        except:
            pass

    def executeQueryFromNext(self, methodName):
        executeFlag = 0
        for entry in self.blocks:
            if executeFlag == 0 and entry['name'] == methodName:
                executeFlag = 1
                continue
            if executeFlag == 1 and entry['status'] is True:
                entry['method']()
        try:
            dpg.get_item_callback("removeExtractContour")()
        except:
            pass

    def toggleAndExecuteQuery(self, methodName, sender = None, app_data = None):
        self.toggleEffect(methodName, sender, app_data)
        if dpg.get_value(sender) is True:
            self.executeQuery(methodName)
        else:
            self.retrieveFromLastActive(methodName, sender, app_data)
            self.executeQueryFromNext(methodName)
        try:
            dpg.get_item_callback("removeExtractContour")()
        except:
            pass

    def getIdByMethod(self, methodName):
        id = 0
        for entry in self.blocks:
            if entry['name'] == methodName:
                return id
            id += 1

    def retrieveFromLastActive(self, methodName, sender = None, app_data = None):
        self.blocks[self.getIdByMethod(methodName)]['output'] = self.blocks[self.getLastActiveBeforeMethod(methodName)]['output']
        texture_tag = self.blocks[self.getIdByMethod(methodName)]['tab']
        if dpg.does_item_exist(texture_tag):
            Texture.updateTexture(texture_tag, self.blocks[self.getIdByMethod(methodName)]['output'])
        tab = self.blocks[self.getIdByMethod(methodName)]['tab']
        if tab in self.histogramPlotState:
            self.updateHistogramForTab(tab)
        if self.getIdByMethod(methodName) <= Blocks.frequencyDomainFilter.value:
            self.updateFrequencyPreview()

    def getLastActiveBeforeMethod(self, methodName):
        lastActiveIndex = 0
        lastActive = 0
        for entry in self.blocks:
            if entry['name'] == methodName:
                break
            if entry['status'] is True:
                lastActiveIndex = lastActive 
            lastActive += 1
        return lastActiveIndex

    def openImage(self, filePath):
        # Check if image is .dcm or .dicom or other format
        if filePath.endswith('.dcm') or filePath.endswith('.dicom'):
            return self.openDicom(filePath)
        return self.openOtherImage(filePath)

    def openDicom(self, filePath):
        ds = pydicom.dcmread(filePath)
        pixelArray = ds.pixel_array
        _, encodedImage = cv2.imencode('.jpg', pixelArray)
        numpyarray = cv2.imdecode(encodedImage, cv2.IMREAD_COLOR)
        return numpyarray
    
    def openOtherImage(self, filePath):
        stream = open(filePath, "rb")
        bytes = bytearray(stream.read())
        numpyarray = np.asarray(bytes, dtype=np.uint8)
        bgrImage = cv2.imdecode(numpyarray, cv2.IMREAD_COLOR)
        return bgrImage

    def openFile(self, sender = None, app_data = None):
        self.filePath = app_data['file_path_name']
        self.fileName = app_data['file_name']

        if os.path.isfile(self.filePath) is False:
            dpg.configure_item('noPath', show=True)
            return

        dpg.set_value("brightnessSlider",0)
        dpg.set_value("contrastSlider",1)
        dpg.set_value("claheClipLimitSlider", DEFAULT_CLAHE_CLIP_LIMIT)
        dpg.set_value("claheTileGridSizeSlider", DEFAULT_CLAHE_TILE_GRID_SIZE)
        dpg.set_value("gaborKernelSlider", DEFAULT_GABOR_KERNEL_SIZE)
        dpg.set_value("gaborSigmaSlider", DEFAULT_GABOR_SIGMA)
        dpg.set_value("gaborThetaSlider", DEFAULT_GABOR_THETA)
        dpg.set_value("gaborLambdaSlider", DEFAULT_GABOR_LAMBDA)
        dpg.set_value("gaborGammaSlider", DEFAULT_GABOR_GAMMA)
        dpg.set_value("gaborPsiSlider", DEFAULT_GABOR_PSI)
        dpg.set_value("frequencyCutoffSlider", DEFAULT_FREQUENCY_CUTOFF)
        dpg.set_value("frequencyBandMinSlider", DEFAULT_FREQUENCY_BAND_MIN)
        dpg.set_value("frequencyBandMaxSlider", DEFAULT_FREQUENCY_BAND_MAX)
        dpg.set_value("frequencyMaskRadiusSlider", DEFAULT_FREQUENCY_MASK_RADIUS)
        dpg.set_value("frequencyFilterModeListbox", strings.option_label("frequency_filter_mode", "none"))
        dpg.set_value("averageBlurSlider",1)
        dpg.set_value("gaussianBlurSlider",1)
        dpg.set_value("medianBlurSlider",1)
        dpg.set_value("laplacianSlider",1)
        dpg.set_value("globalThresholdSlider",127)
        
        try:
            dpg.get_item_callback("removeExtractContour")()
        except:
            pass
        self.uncheckAllTags()
        self._resetFrequencyState()
        for entry in self.blocks[1:-1]:
            if entry['name'] != self.grayscale.__name__ and entry['name'] != self.crop.__name__:
                entry['status'] = False
        self.executeQuery('importImage')
        self.enableAllTags()
        pass

    def cancelImportImage(self, sender = None, app_data = None):
        dpg.hide_item("file_dialog_id")
        pass

    def toggleEffect(self, methodName, sender = None, app_data = None):
        for entry in self.blocks:
            if entry['name'] == methodName:
                entry['status'] = dpg.get_value(sender)
        pass

    def importImage(self, sender = None, app_data = None):
        # Cria imagem na aba
        self.blocks[Blocks.importImage.value]['output'] = self.openImage(self.filePath)

        Texture.createAllTextures(self.blocks[Blocks.importImage.value]['output'])
        self.updateAllHistograms()
        self.updateFrequencyPreview()

        # Popula os dados na lateral
        self.renderFileInfo()

        shape = self.blocks[Blocks.importImage.value]['output'].shape
        self.originalResolution = (shape[1], shape[0])
        self.currentResolution = (shape[1], shape[0])

        self.renderResolutionInfo()

        dpg.set_value('endX', shape[0])
        dpg.set_value('endY', shape[1])
        dpg.configure_item("exportImageAsFileProcessingGroup", show=True)
        dpg.configure_item("exportImageAsFileFilteringGroup", show=True)
        dpg.configure_item("exportImageAsFileFrequencyGroup", show=True)
        dpg.configure_item("exportImageAsFileThresholdingGroup", show=True)
        dpg.configure_item("exportHistogramAsFileProcessingGroup", show=True)
        dpg.configure_item("exportHistogramAsFileFilteringGroup", show=True)
        dpg.configure_item("exportHistogramAsFileFrequencyGroup", show=True)
        dpg.configure_item("exportHistogramAsFileThresholdingGroup", show=True)
        pass


    def resetCrop(self, sender = None, app_data = None):

        if self.blocks[Blocks.importImage.value]['output'] is None:
            dpg.configure_item('noImage', show=True)
            self.blocks[Blocks.crop.value]['status'] = False
            return

        self.blocks[Blocks.crop.value]['output'] = self.blocks[Blocks.importImage.value]['output']

        shape = self.blocks[Blocks.crop.value]['output'].shape
        self.currentResolution = (shape[1], shape[0])

        self.renderResolutionInfo()
        dpg.set_value('endX', shape[0])
        dpg.set_value('endY', shape[1])

        Texture.createAllTextures(self.blocks[Blocks.importImage.value]['output'])
        self.updateAllHistograms()
        self.updateFrequencyPreview()

        pass

    def crop(self, sender=None, app_data=None):

        startX = dpg.get_value('startX')
        endX = dpg.get_value('endX')
        startY = dpg.get_value('startY')
        endY = dpg.get_value('endY')

        if startX >= endX or startY >= endY:
            dpg.configure_item('incorrectCrop', show=True)
            dpg.set_value('cropCheckbox', False)
            self.blocks[Blocks.crop.value]['status'] = False
            return

        if self.blocks[Blocks.importImage.value]['output'] is None:
            dpg.configure_item('noImage', show=True)
            dpg.set_value('cropCheckbox', False)
            self.blocks[Blocks.crop.value]['status'] = False
            return

        self.blocks[Blocks.crop.value]['output'] = self.blocks[Blocks.importImage.value]['output'][startX:endX, startY:endY]

        shape = self.blocks[Blocks.crop.value]['output'].shape
        self.currentResolution = (shape[1], shape[0])

        self.renderResolutionInfo()

        dpg.set_value('endX', shape[0])
        dpg.set_value('endY', shape[1])

        Texture.createAllTextures(self.blocks[Blocks.crop.value]['output'])
        self.updateAllHistograms()
        self._resetFrequencyState()
        self.updateFrequencyPreview()

    def histogramEqualization(self, sender=None, app_data=None):
        image = self.blocks[self.getLastActiveBeforeMethod('histogramEqualization')]['output']
        if image is None:
            return

        dst = self._applyLuminanceTransform(image, cv2.equalizeHist)
        self._storeBlockOutput(Blocks.histogramEqualization.value, dst)
        pass

    def claheEqualization(self, sender=None, app_data=None):
        image = self.blocks[self.getLastActiveBeforeMethod('claheEqualization')]['output']
        if image is None:
            return

        clip_limit, tile_grid_size = self._claheParameters()
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(tile_grid_size, tile_grid_size))
        dst = self._applyLuminanceTransform(image, clahe.apply)
        self._storeBlockOutput(Blocks.claheEqualization.value, dst)
        pass

    def brightnessAndContrast(self, sender=None, app_data=None):

        image = self.blocks[self.getLastActiveBeforeMethod('brightnessAndContrast')]['output']
        alpha = dpg.get_value('contrastSlider')
        beta = dpg.get_value('brightnessSlider')
        outputImage = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)

        self._storeBlockOutput(Blocks.brightnessAndContrast.value, outputImage)
        pass

    def averageBlur(self, sender=None, app_data=None):
        image = self.blocks[self.getLastActiveBeforeMethod('averageBlur')]['output']

        kernelSize = (2 * dpg.get_value('averageBlurSlider')) - 1
        kernel = np.ones((kernelSize,kernelSize),np.float32)/(kernelSize*kernelSize)
        dst = cv2.filter2D(image,-1,kernel)

        self._storeBlockOutput(Blocks.averageBlur.value, dst)
        pass

    def gaussianBlur(self, sender=None, app_data=None):
        image = self.blocks[self.getLastActiveBeforeMethod('gaussianBlur')]['output']

        kernelSize = (2 * dpg.get_value('gaussianBlurSlider')) - 1
        dst = cv2.GaussianBlur(image, (kernelSize,kernelSize), 0)

        self._storeBlockOutput(Blocks.gaussianBlur.value, dst)
        pass

    def medianBlur(self, sender=None, app_data=None):
        image = self.blocks[self.getLastActiveBeforeMethod('medianBlur')]['output']
        kernel = (2 * dpg.get_value('medianBlurSlider')) - 1

        median = cv2.medianBlur(image, kernel)

        self._storeBlockOutput(Blocks.medianBlur.value, median)
        pass

    def gaborFilter(self, sender=None, app_data=None):
        image = self.blocks[self.getLastActiveBeforeMethod('gaborFilter')]['output']
        if image is None:
            return

        grayscale = self._grayscaleImage(image)
        kernel_size, sigma, theta, lambd, gamma, psi = self._gaborParameters()
        kernel = cv2.getGaborKernel((kernel_size, kernel_size), sigma, theta, lambd, gamma, psi, ktype=cv2.CV_32F)
        filtered = cv2.filter2D(grayscale.astype(np.float32), cv2.CV_32F, kernel)
        normalized = cv2.normalize(np.abs(filtered), None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        output_image = cv2.cvtColor(normalized, cv2.COLOR_GRAY2BGR)

        self._storeBlockOutput(Blocks.gaborFilter.value, output_image)
        pass

    def frequencyDomainFilter(self, sender=None, app_data=None):
        image = self.blocks[self.getLastActiveBeforeMethod('frequencyDomainFilter')]['output']
        if image is None:
            return

        grayscale = self._grayscaleImage(image).astype(np.float32)
        shifted = np.fft.fftshift(np.fft.fft2(grayscale))
        masked_shifted = shifted * self._combinedFrequencyMask(grayscale.shape)
        reconstructed = np.fft.ifft2(np.fft.ifftshift(masked_shifted))
        reconstructed = np.clip(np.real(reconstructed), 0, 255).astype(np.uint8)
        output_image = cv2.cvtColor(reconstructed, cv2.COLOR_GRAY2BGR)

        self._updateFrequencySpectrumTexture(self._frequencySpectrumPreviewImage(masked_shifted))
        self._storeBlockOutput(Blocks.frequencyDomainFilter.value, output_image)
        pass

    def grayscale(self, sender=None, app_data=None):

        if self.blocks[self.getLastActiveBeforeMethod('grayscale')]['output'] is None:
            return

        image = self.blocks[self.getLastActiveBeforeMethod('grayscale')]['output'].copy()


        excludeBlue = dpg.get_value('excludeBlueChannel')
        excludeGreen = dpg.get_value('excludeGreenChannel')
        excludeRed = dpg.get_value('excludeRedChannel')

        if excludeBlue:
            image[:, :, 0] = 0
        if excludeGreen:
            image[:, :, 1] = 0
        if excludeRed:
            image[:, :, 2] = 0

        grayMask = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        image[:, :, 0] = grayMask
        image[:, :, 1] = grayMask
        image[:, :, 2] = grayMask

        self._storeBlockOutput(Blocks.grayscale.value, image)
        pass

    def laplacian(self, sender=None, app_data=None):
        image = self.blocks[Blocks.grayscale.value]['output'].copy()

        kernelSize = (2 * dpg.get_value('laplacianSlider')) - 1
        laplacian = cv2.Laplacian(image, cv2.CV_8U, ksize=kernelSize)
                
        self._storeBlockOutput(Blocks.laplacian.value, laplacian)
        pass

    def sobel(self, sender=None, app_data=None):
        image = self.blocks[self.getLastActiveBeforeMethod('sobel')]['output']

        sobel = None
        value = strings.option_key("sobel_axis", dpg.get_value('sobelListbox'))

        if value == 'x_axis':
            sobel = cv2.Sobel(image, cv2.CV_8U, 1, 0, ksize=3)
        elif value == 'y_axis':
            sobel = cv2.Sobel(image, cv2.CV_8U, 0, 1, ksize=3)
        elif value == 'xy_axis':
            sobel = cv2.bitwise_or(cv2.Sobel(image, cv2.CV_8U, 1, 0, ksize=3), cv2.Sobel(image, cv2.CV_8U, 0, 1, ksize=3))

        self._storeBlockOutput(Blocks.sobel.value, sobel)
        pass

    def globalThresholding(self, sender=None, app_data=None):
        image = self.blocks[self.getLastActiveBeforeMethod('globalThresholding')]['output']
        threshold = dpg.get_value('globalThresholdSlider')

        thresholdMode = cv2.THRESH_BINARY 
        invertFlag = dpg.get_value('invertGlobalThresholding')
        if invertFlag:
            thresholdMode = cv2.THRESH_BINARY_INV

        (T, threshInv) = cv2.threshold(image, threshold, 255, thresholdMode)

        self._storeBlockOutput(Blocks.globalThresholding.value, threshInv)
        pass

    def adaptiveMeanThresholding(self, sender=None, app_data=None):
        image = self.blocks[self.getLastActiveBeforeMethod('adaptiveMeanThresholding')]['output'].copy()

        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        threshInv = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY,11,2)
        image = cv2.cvtColor(threshInv, cv2.COLOR_GRAY2BGR)

        self._storeBlockOutput(Blocks.adaptiveMeanThresholding.value, image)

        pass

    def adaptiveGaussianThresholding(self, sender=None, app_data=None):

        image = self.blocks[self.getLastActiveBeforeMethod('adaptiveGaussianThresholding')]['output'].copy()

        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        threshInv = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY,11,2)
        image = cv2.cvtColor(threshInv, cv2.COLOR_GRAY2BGR)

        self._storeBlockOutput(Blocks.adaptiveGaussianThresholding.value, image)

        pass

    def otsuBinarization(self, sender=None, app_data=None):
        image = self.blocks[self.getLastActiveBeforeMethod('adaptiveGaussianThresholding')]['output'].copy()
        
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        ret, threshInv = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        threshInv = cv2.cvtColor(threshInv, cv2.COLOR_GRAY2BGR)


        self._storeBlockOutput(Blocks.otsuBinarization.value, threshInv)
        pass

    def findContour(self, sender=None, app_data=None):

        if self.blocks[self.getLastActiveBeforeMethod('findContour')]['output'] is None:
            return

        image = self.blocks[self.getLastActiveBeforeMethod('findContour')]['output'].copy()
        Texture.updateTexture(self.blocks[Blocks.findContour.value]['tab'], image)
        pass

    def exportImage(self, sender = None, app_data = None, tab = None):

        self.exportImageFilePath = None
        self.renderExportState()
        dpg.set_value('imageNameExportAsFile', '')
        self.currentTab = tab
        dpg.configure_item('exportImageAsFile', show=True)
        pass

    def exportHistogram(self, sender = None, app_data = None, tab = None):
        self.exportHistogramFilePath = None
        self.renderHistogramExportState()
        dpg.set_value('histogramNameExportAsFile', '')
        self.currentHistogramTab = tab
        dpg.configure_item('exportHistogramAsFile', show=True)
        pass

    def exportImageDirectorySelector(self, sender = None, app_data = None):
        imageName = dpg.get_value('imageNameExportAsFile')
        if imageName == '':
            return
        dpg.configure_item('exportImageAsFile', show=True)
        dpg.configure_item('exportImageDirectorySelector', show=True)
        pass

    def exportImageSelectDirectory(self, sender = None, app_data = None):
        exportImageFileName = dpg.get_value('imageNameExportAsFile')
        exportImageFilePath = app_data['file_path_name']
        self.exportImageFilePath = os.path.join(exportImageFilePath, exportImageFileName + '.jpg')
        self.renderExportState()
        pass

    def exportHistogramDirectorySelector(self, sender = None, app_data = None):
        histogram_name = dpg.get_value('histogramNameExportAsFile')
        if histogram_name == '':
            return
        dpg.configure_item('exportHistogramAsFile', show=True)
        dpg.configure_item('exportHistogramDirectorySelector', show=True)
        pass

    def exportHistogramSelectDirectory(self, sender = None, app_data = None):
        histogram_file_name = dpg.get_value('histogramNameExportAsFile')
        histogram_file_path = app_data['file_path_name']
        self.exportHistogramFilePath = os.path.join(histogram_file_path, histogram_file_name + '.png')
        self.renderHistogramExportState()
        pass

    def exportImageAsFile(self, sender = None, app_data = None):
        if self.exportImageFilePath is None:
            dpg.configure_item("exportImageError", show=True)
            return

        dpg.configure_item("exportImageError", show=False)

        lastTabIndex = {
            'Processing': Blocks.histogramEqualization.name,
            'Filtering': Blocks.gaborFilter.name,
            'Frequency': Blocks.grayscale.name,
            'Thresholding': Blocks.findContour.name,
        }
        path = self.exportImageFilePath
        if self.currentTab == 'FrequencySpectrum':
            image = self.frequencySpectrumPreview
        else:
            image = self.blocks[self.getLastActiveBeforeMethod(lastTabIndex[self.currentTab])]['output']
        if image is None:
            dpg.configure_item("exportImageError", show=True)
            return
        cv2.imwrite(path, image)
        dpg.configure_item('exportImageAsFile', show=False)

    def exportHistogramAsFile(self, sender = None, app_data = None):
        if self.exportHistogramFilePath is None:
            dpg.configure_item("exportHistogramError", show=True)
            return

        dpg.configure_item("exportHistogramError", show=False)
        self.exportHistogramToFile(self.currentHistogramTab, self.exportHistogramFilePath)
        dpg.configure_item('exportHistogramAsFile', show=False)

    def enableAllTags(self):
        checkboxes = [
            'histogramCheckbox',
            'claheCheckbox',
            'claheClipLimitSlider',
            'claheTileGridSizeSlider',
            'brightnessAndContrastCheckbox',
            'averageBlurCheckbox',
            'gaussianBlurCheckbox',
            'medianBlurCheckbox',
            'gaborCheckbox',
            'gaborKernelSlider',
            'gaborSigmaSlider',
            'gaborThetaSlider',
            'gaborLambdaSlider',
            'gaborGammaSlider',
            'gaborPsiSlider',
            'frequencyDomainCheckbox',
            'frequencyFilterModeListbox',
            'frequencyCutoffSlider',
            'frequencyBandMinSlider',
            'frequencyBandMaxSlider',
            'frequencyMaskRadiusSlider',
            'frequencyMaskModeButton',
            'frequencyResetMaskButton',
            'showProcessingHistogramToggle',
            'showFilteringHistogramToggle',
            'excludeBlueChannel',
            'excludeGreenChannel',
            'excludeRedChannel',
            'showThresholdingHistogramToggle',
            'laplacianCheckbox',
            'sobelCheckbox',
            'globalThresholdingCheckbox',
            'invertGlobalThresholding',
            'adaptiveThresholdingCheckbox',
            'adaptiveGaussianThresholdingCheckbox',
            'otsuBinarization',
            'matlabModeCheckbox',
            'extractContourButton',
            'updateContourButton',
            'exportImageAsFileProcessing',
            'exportImageAsFileFiltering',
            'exportImageAsFileFrequency',
            'exportSpectrumAsFileFrequency',
            'exportImageAsFileThresholding',
            'exportHistogramAsFileProcessing',
            'exportHistogramAsFileFiltering',
            'exportHistogramAsFileFrequency',
            'exportHistogramAsFileThresholding'
        ]
        for checkbox in checkboxes:
            dpg.configure_item(checkbox, enabled=True)
        pass

    def disableAllTags(self):
        checkboxes = [
            'histogramCheckbox',
            'claheCheckbox',
            'claheClipLimitSlider',
            'claheTileGridSizeSlider',
            'brightnessAndContrastCheckbox',
            'averageBlurCheckbox',
            'gaussianBlurCheckbox',
            'medianBlurCheckbox',
            'gaborCheckbox',
            'gaborKernelSlider',
            'gaborSigmaSlider',
            'gaborThetaSlider',
            'gaborLambdaSlider',
            'gaborGammaSlider',
            'gaborPsiSlider',
            'frequencyDomainCheckbox',
            'frequencyFilterModeListbox',
            'frequencyCutoffSlider',
            'frequencyBandMinSlider',
            'frequencyBandMaxSlider',
            'frequencyMaskRadiusSlider',
            'frequencyMaskModeButton',
            'frequencyResetMaskButton',
            'showProcessingHistogramToggle',
            'showFilteringHistogramToggle',
            'excludeBlueChannel',
            'excludeGreenChannel',
            'excludeRedChannel',
            'showThresholdingHistogramToggle',
            'laplacianCheckbox',
            'sobelCheckbox',
            'globalThresholdingCheckbox',
            'invertGlobalThresholding',
            'adaptiveThresholdingCheckbox',
            'adaptiveGaussianThresholdingCheckbox',
            'otsuBinarization',
            'matlabModeCheckbox',
            'extractContourButton',
            'updateContourButton',
            'exportImageAsFileProcessing',
            'exportImageAsFileFiltering',
            'exportImageAsFileFrequency',
            'exportSpectrumAsFileFrequency',
            'exportImageAsFileThresholding',
            'exportHistogramAsFileProcessing',
            'exportHistogramAsFileFiltering',
            'exportHistogramAsFileFrequency',
            'exportHistogramAsFileThresholding'
        ]
        for checkbox in checkboxes:
            dpg.configure_item(checkbox, enabled=False)
        pass

    def uncheckAllTags(self):
        checkboxes = [
            'histogramCheckbox',
            'claheCheckbox',
            'brightnessAndContrastCheckbox',
            'averageBlurCheckbox',
            'gaussianBlurCheckbox',
            'medianBlurCheckbox',
            'gaborCheckbox',
            'frequencyDomainCheckbox',
            'showProcessingHistogramToggle',
            'showFilteringHistogramToggle',
            'excludeBlueChannel',
            'excludeGreenChannel',
            'excludeRedChannel',
            'showThresholdingHistogramToggle',
            'laplacianCheckbox',
            'sobelCheckbox',
            'globalThresholdingCheckbox',
            'invertGlobalThresholding',
            'adaptiveThresholdingCheckbox',
            'adaptiveGaussianThresholdingCheckbox',
            'otsuBinarization',
            'matlabModeCheckbox'
        ]
        for checkbox in checkboxes:
            dpg.set_value(checkbox, False)
        for tab in [tab for tab in self.histogramPlotState.keys() if tab != "Frequency"]:
            panel_tag = self._histogramPanelTag(tab)
            if dpg.does_item_exist(panel_tag):
                dpg.configure_item(panel_tag, show=False)
            image_panel_tag = self._histogramImagePanelTag(tab)
            if dpg.does_item_exist(image_panel_tag):
                dpg.configure_item(image_panel_tag, height=-1)
        pass
