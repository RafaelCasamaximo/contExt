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
            "Thresholding": {"series": [], "themes": []},
        }

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
            'Filtering': Blocks.grayscale.name,
            'Thresholding': Blocks.findContour.name,
        }[tab]

    def _histogramPlotAxes(self, tab):
        return {
            'Processing': ("ProcessingHistogram_x_axis", "ProcessingHistogram_y_axis"),
            'Filtering': ("FilteringHistogram_x_axis", "FilteringHistogram_y_axis"),
            'Thresholding': ("ThresholdingHistogram_x_axis", "ThresholdingHistogram_y_axis"),
        }[tab]

    def _histogramPanelTag(self, tab):
        return {
            'Processing': "ProcessingHistogramPanel",
            'Filtering': "FilteringHistogramPanel",
            'Thresholding': "ThresholdingHistogramPanel",
        }[tab]

    def _histogramImagePanelTag(self, tab):
        return {
            'Processing': "ProcessingImagePanel",
            'Filtering': "FilteringImagePanel",
            'Thresholding': "ThresholdingImagePanel",
        }[tab]

    def _histogramStageTitle(self, tab):
        return {
            'Processing': strings.t("app.tabs.processing"),
            'Filtering': strings.t("app.tabs.filtering"),
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
        Texture.updateTexture(self.blocks[block_index]['tab'], image)
        tab = self.blocks[block_index]['tab']
        if tab in self.histogramPlotState:
            self.updateHistogramForTab(tab)

    def _rgbToBgr(self, color):
        return int(color[2]), int(color[1]), int(color[0])

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
        Texture.updateTexture(self.blocks[self.getIdByMethod(methodName)]['tab'], self.blocks[self.getIdByMethod(methodName)]['output'])
        tab = self.blocks[self.getIdByMethod(methodName)]['tab']
        if tab in self.histogramPlotState:
            self.updateHistogramForTab(tab)

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
        dpg.configure_item("exportImageAsFileThresholdingGroup", show=True)
        dpg.configure_item("exportHistogramAsFileProcessingGroup", show=True)
        dpg.configure_item("exportHistogramAsFileFilteringGroup", show=True)
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
            'Filtering': Blocks.grayscale.name,
            'Thresholding': Blocks.findContour.name,
        }
        path = self.exportImageFilePath
        image = self.blocks[self.getLastActiveBeforeMethod(lastTabIndex[self.currentTab])]['output']
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
            'exportImageAsFileThresholding',
            'exportHistogramAsFileProcessing',
            'exportHistogramAsFileFiltering',
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
            'exportImageAsFileThresholding',
            'exportHistogramAsFileProcessing',
            'exportHistogramAsFileFiltering',
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
        for tab in self.histogramPlotState.keys():
            panel_tag = self._histogramPanelTag(tab)
            if dpg.does_item_exist(panel_tag):
                dpg.configure_item(panel_tag, show=False)
            image_panel_tag = self._histogramImagePanelTag(tab)
            if dpg.does_item_exist(image_panel_tag):
                dpg.configure_item(image_panel_tag, height=-1)
        pass
