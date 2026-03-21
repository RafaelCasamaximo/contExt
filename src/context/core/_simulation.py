from __future__ import annotations

import csv
import os.path
from time import perf_counter

import cv2
import dearpygui.dearpygui as dpg
import numpy as np

from ._fdm import (
    build_sparse_composite_domain,
    build_structured_domain,
    build_uniform_domain,
    solve_dirichlet_problem,
)
from ..ui import strings


PNG_CANVAS_WIDTH = 1400
PNG_CANVAS_HEIGHT = 960
PNG_MARGIN_LEFT = 90
PNG_MARGIN_TOP = 55
PNG_MARGIN_BOTTOM = 80
PNG_MARGIN_RIGHT = 90
PNG_COLORBAR_GAP = 46
PNG_COLORBAR_WIDTH = 48
PNG_LABEL_GAP = 12
SOLUTION_COLOR_BINS = 24


class Simulation:
    def __init__(self) -> None:
        self.meshGeneration = None
        self.problem_key = "laplace"
        self.source_term = 0.0
        self.regions: list[dict[str, int | str]] = []
        self.region_values: dict[int, float] = {}
        self.region_counts: dict[int, int] = {}
        self.active_region_id: int | None = None
        self.domain = None
        self.result = None
        self.solve_time_seconds: float | None = None
        self.status_message = strings.t("simulation.status.awaiting_mesh")

        self.csvExportFilePath = None
        self.csvExportFileName = None
        self.pngExportFilePath = None
        self.pngExportFileName = None

        self.scaleMinValue: float | None = None
        self.scaleMaxValue: float | None = None
        self.scaleDisplayMin = 0.0
        self.scaleDisplayMax = 1.0
        self.scaleIsConstant = False

        self.solutionPlotSeries: list[str] = []
        self.solutionPlotThemes: list[str] = []

    def attachMeshGeneration(self, meshGeneration) -> None:
        self.meshGeneration = meshGeneration

    def meshChanged(self) -> None:
        self.domain = None
        self.result = None
        self.solve_time_seconds = None
        self.csvExportFilePath = None
        self.csvExportFileName = None
        self.pngExportFilePath = None
        self.pngExportFileName = None
        self._resetScaleState()
        self.syncWithMesh()

    def _uiReady(self) -> bool:
        return dpg.does_item_exist("simulationStatusText")

    def _paletteStops(self) -> list[tuple[int, int, int, int]]:
        return [
            (40, 64, 153, 255),
            (37, 95, 180, 255),
            (34, 124, 196, 255),
            (42, 150, 194, 255),
            (67, 174, 176, 255),
            (108, 196, 157, 255),
            (159, 214, 131, 255),
            (206, 222, 102, 255),
            (238, 210, 73, 255),
            (247, 178, 56, 255),
            (240, 131, 48, 255),
            (220, 79, 56, 255),
        ]

    def _samplePaletteColor(self, normalized: float) -> tuple[int, int, int, int]:
        stops = self._paletteStops()
        normalized = min(max(float(normalized), 0.0), 1.0)
        if len(stops) == 1:
            return stops[0]
        if normalized == 1.0:
            return stops[-1]

        position = normalized * (len(stops) - 1)
        left_index = int(position)
        right_index = min(left_index + 1, len(stops) - 1)
        blend = position - left_index
        left_color = stops[left_index]
        right_color = stops[right_index]
        return tuple(
            int(round(left_color[channel] + (right_color[channel] - left_color[channel]) * blend))
            for channel in range(4)
        )

    def _resetScaleState(self) -> None:
        self.scaleMinValue = None
        self.scaleMaxValue = None
        self.scaleDisplayMin = 0.0
        self.scaleDisplayMax = 1.0
        self.scaleIsConstant = False

    def _updateScaleState(self) -> None:
        if self.domain is None or self.result is None:
            self._resetScaleState()
            return

        values = self.result.values[self.domain.inside_mask]
        self.scaleMinValue = float(np.nanmin(values))
        self.scaleMaxValue = float(np.nanmax(values))
        self.scaleIsConstant = bool(np.isclose(self.scaleMinValue, self.scaleMaxValue))

        if self.scaleIsConstant:
            constant_value = self.scaleMinValue
            padding = max(abs(constant_value) * 0.05, 1.0e-6)
            self.scaleDisplayMin = constant_value - padding
            self.scaleDisplayMax = constant_value + padding
            return

        self.scaleDisplayMin = self.scaleMinValue
        self.scaleDisplayMax = self.scaleMaxValue

    def _renderColorScale(self) -> None:
        if not self._uiReady():
            return

        if self.scaleMinValue is None or self.scaleMaxValue is None:
            min_label = "--"
            max_label = "--"
            status = strings.t("simulation.scale_pending")
        elif self.scaleIsConstant:
            min_label = f"{self.scaleMinValue:.6g}"
            max_label = f"{self.scaleMaxValue:.6g}"
            status = strings.t("simulation.scale_constant", value=f"{self.scaleMinValue:.6g}")
        else:
            min_label = f"{self.scaleMinValue:.6g}"
            max_label = f"{self.scaleMaxValue:.6g}"
            status = strings.t(
                "simulation.scale_range",
                min=f"{self.scaleMinValue:.6g}",
                max=f"{self.scaleMaxValue:.6g}",
            )
        dpg.set_value("simulationColorScaleMinValue", min_label)
        dpg.set_value("simulationColorScaleMaxValue", max_label)
        dpg.set_value("simulationColorScaleStatus", status)

    def _regionLabel(self, region: dict[str, int | str]) -> str:
        return strings.t(
            "simulation.region_label",
            index=int(region["id"]) + 1,
            lower=int(region["lower"]),
            upper=int(region["upper"]),
        )

    def _currentRegion(self) -> dict[str, int | str] | None:
        if self.active_region_id is None:
            return None
        for region in self.regions:
            if int(region["id"]) == self.active_region_id:
                return region
        return None

    def _clearSolutionPlot(self) -> None:
        for item in self.solutionPlotSeries:
            if dpg.does_item_exist(item):
                dpg.delete_item(item)
        for item in self.solutionPlotThemes:
            if dpg.does_item_exist(item):
                dpg.delete_item(item)
        self.solutionPlotSeries.clear()
        self.solutionPlotThemes.clear()

    def _setStatus(self, key: str, **params) -> None:
        self.status_message = strings.t(key, **params)
        if self._uiReady():
            dpg.set_value("simulationStatusText", self.status_message)

    def _renderExportState(self) -> None:
        if not self._uiReady():
            return

        csv_file_name = self.csvExportFileName or ""
        csv_full_path = ""
        if self.csvExportFilePath is not None and self.csvExportFileName is not None:
            csv_full_path = os.path.join(self.csvExportFilePath, self.csvExportFileName)

        png_file_name = self.pngExportFileName or ""
        png_full_path = ""
        if self.pngExportFilePath is not None and self.pngExportFileName is not None:
            png_full_path = os.path.join(self.pngExportFilePath, self.pngExportFileName)

        dpg.set_value("simulationCsvExportFileName", strings.fmt("file_name", value=csv_file_name))
        dpg.set_value("simulationCsvExportPathName", strings.fmt("full_path", value=csv_full_path))
        dpg.set_value("simulationPngExportFileName", strings.fmt("file_name", value=png_file_name))
        dpg.set_value("simulationPngExportPathName", strings.fmt("full_path", value=png_full_path))

    def _renderProblemState(self, old_locale=None) -> None:
        if not self._uiReady():
            return
        if old_locale is None:
            selected = strings.option_label("simulation_problem", self.problem_key)
        else:
            current_value = dpg.get_value("simulationProblemList")
            selected = strings.translate_option_value("simulation_problem", current_value, old_locale)
            self.problem_key = strings.option_key("simulation_problem", selected)

        dpg.configure_item("simulationProblemList", items=strings.option_labels("simulation_problem"))
        dpg.set_value("simulationProblemList", selected)
        dpg.configure_item("simulationSourceTerm", enabled=self.problem_key == "poisson")

    def _renderRegionState(self) -> None:
        if not self._uiReady():
            return

        if self.regions:
            labels = [self._regionLabel(region) for region in self.regions]
            current_region = self._currentRegion() or self.regions[0]
            self.active_region_id = int(current_region["id"])
            current_label = self._regionLabel(current_region)
            dpg.configure_item("simulationRegionList", items=labels, enabled=True)
            dpg.set_value("simulationRegionList", current_label)
        else:
            dpg.configure_item("simulationRegionList", items=[strings.t("simulation.no_regions")], enabled=False)
            dpg.set_value("simulationRegionList", strings.t("simulation.no_regions"))

        region = self._currentRegion()
        if region is None:
            dpg.set_value("simulationRegionRange", strings.t("simulation.region_range_empty"))
            dpg.set_value("simulationRegionNodeCount", strings.t("simulation.region_boundary_nodes", value="--"))
            dpg.configure_item("simulationBoundaryValue", default_value=0.0)
            dpg.set_value("simulationBoundaryValue", 0.0)
            return

        region_id = int(region["id"])
        dpg.set_value(
            "simulationRegionRange",
            strings.t(
                "simulation.region_range",
                lower=int(region["lower"]),
                upper=int(region["upper"]),
            ),
        )
        dpg.set_value(
            "simulationRegionNodeCount",
            strings.t("simulation.region_boundary_nodes", value=self.region_counts.get(region_id, 0)),
        )
        current_value = self.region_values.get(region_id, 0.0)
        dpg.configure_item("simulationBoundaryValue", default_value=current_value)
        dpg.set_value("simulationBoundaryValue", current_value)

    def _renderStats(self) -> None:
        if not self._uiReady():
            return

        if self.domain is None:
            dpg.set_value("simulationDomainNodeCount", strings.t("simulation.domain_nodes", value="--"))
            dpg.set_value("simulationBoundaryNodeCount", strings.t("simulation.boundary_nodes", value="--"))
            dpg.set_value("simulationInternalNodeCount", strings.t("simulation.internal_nodes", value="--"))
        else:
            dpg.set_value("simulationDomainNodeCount", strings.t("simulation.domain_nodes", value=self.domain.domain_count))
            dpg.set_value("simulationBoundaryNodeCount", strings.t("simulation.boundary_nodes", value=self.domain.boundary_count))
            dpg.set_value("simulationInternalNodeCount", strings.t("simulation.internal_nodes", value=self.domain.internal_count))

        if self.result is None:
            dpg.set_value("simulationSystemSize", strings.t("simulation.system_size", value="--"))
            dpg.set_value("simulationResidual", strings.t("simulation.residual", value="--"))
            dpg.set_value("simulationMinValue", strings.t("simulation.min_value", value="--"))
            dpg.set_value("simulationMaxValue", strings.t("simulation.max_value", value="--"))
            dpg.set_value("simulationMeanValue", strings.t("simulation.mean_value", value="--"))
            dpg.set_value("simulationSolveTime", strings.t("simulation.solve_time", value="--"))
            dpg.configure_item("simulationExportCsvButton", enabled=False)
            dpg.configure_item("simulationExportPngButton", enabled=False)
            self._renderColorScale()
            return

        dpg.set_value("simulationSystemSize", strings.t("simulation.system_size", value=self.result.system_size))
        dpg.set_value("simulationResidual", strings.t("simulation.residual", value=f"{self.result.residual:.3e}"))
        dpg.set_value("simulationMinValue", strings.t("simulation.min_value", value=f"{self.result.min_value:.6g}"))
        dpg.set_value("simulationMaxValue", strings.t("simulation.max_value", value=f"{self.result.max_value:.6g}"))
        dpg.set_value("simulationMeanValue", strings.t("simulation.mean_value", value=f"{self.result.mean_value:.6g}"))
        dpg.set_value(
            "simulationSolveTime",
            strings.t("simulation.solve_time", value=f"{(self.solve_time_seconds or 0.0):.4f}s"),
        )
        dpg.configure_item("simulationExportCsvButton", enabled=True)
        dpg.configure_item("simulationExportPngButton", enabled=True)
        self._renderColorScale()

    def _plotContour(self) -> None:
        self._clearSolutionPlot()
        if not self._uiReady() or self.meshGeneration is None:
            return
        contour_x = getattr(self.meshGeneration, "currentX", [])
        contour_y = getattr(self.meshGeneration, "currentY", [])
        if not contour_x or not contour_y:
            return

        contour_tag = "simulationContourSeries"
        dpg.add_line_series(
            contour_x,
            contour_y,
            label=strings.t("simulation.contour"),
            tag=contour_tag,
            parent="Simulation_y_axis",
        )
        self.solutionPlotSeries.append(contour_tag)
        dpg.fit_axis_data("Simulation_x_axis")
        dpg.fit_axis_data("Simulation_y_axis")

    def _plotSolution(self) -> None:
        self._plotContour()
        if not self._uiReady() or self.domain is None or self.result is None:
            self._renderColorScale()
            return

        values = self.result.values
        rows, cols = np.argwhere(self.domain.inside_mask).T
        node_x = [float(self.domain.x_coords[col]) for col in cols]
        node_y = [float(self.domain.y_coords[row]) for row in rows]
        node_values = [float(values[row, col]) for row, col in zip(rows, cols)]

        bin_points = [{"x": [], "y": [], "color": self._samplePaletteColor(index / (SOLUTION_COLOR_BINS - 1))} for index in range(SOLUTION_COLOR_BINS)]
        if self.scaleIsConstant:
            constant_index = SOLUTION_COLOR_BINS // 2
            for x_value, y_value in zip(node_x, node_y):
                bin_points[constant_index]["x"].append(x_value)
                bin_points[constant_index]["y"].append(y_value)
        else:
            scale = self.scaleMaxValue - self.scaleMinValue
            for x_value, y_value, node_value in zip(node_x, node_y, node_values):
                normalized = (node_value - self.scaleMinValue) / scale
                index = min(int(normalized * (SOLUTION_COLOR_BINS - 1)), SOLUTION_COLOR_BINS - 1)
                bin_points[index]["x"].append(x_value)
                bin_points[index]["y"].append(y_value)

        for index, bucket in enumerate(bin_points):
            if not bucket["x"]:
                continue
            theme_tag = f"simulationSolutionTheme{index}"
            series_tag = f"simulationSolutionSeries{index}"
            with dpg.theme(tag=theme_tag):
                with dpg.theme_component(dpg.mvScatterSeries):
                    dpg.add_theme_color(dpg.mvPlotCol_MarkerFill, bucket["color"], category=dpg.mvThemeCat_Plots)
                    dpg.add_theme_color(dpg.mvPlotCol_MarkerOutline, bucket["color"], category=dpg.mvThemeCat_Plots)
                    dpg.add_theme_style(dpg.mvPlotStyleVar_Marker, dpg.mvPlotMarker_Circle, category=dpg.mvThemeCat_Plots)
                    dpg.add_theme_style(dpg.mvPlotStyleVar_MarkerSize, 5, category=dpg.mvThemeCat_Plots)
                    dpg.add_theme_style(dpg.mvPlotStyleVar_MarkerWeight, 1, category=dpg.mvThemeCat_Plots)
            dpg.add_scatter_series(bucket["x"], bucket["y"], label="", tag=series_tag, parent="Simulation_y_axis")
            dpg.bind_item_theme(series_tag, theme_tag)
            self.solutionPlotThemes.append(theme_tag)
            self.solutionPlotSeries.append(series_tag)

        dpg.fit_axis_data("Simulation_x_axis")
        dpg.fit_axis_data("Simulation_y_axis")
        self._renderColorScale()

    def _collectRegions(self) -> list[dict[str, int | str]]:
        if self.meshGeneration is None or not getattr(self.meshGeneration, "currentX", None):
            return []
        ranges = getattr(self.meshGeneration, "subcontoursRanges", None) or [[0, len(self.meshGeneration.currentX) - 1]]
        regions = []
        for region_id, (lower, upper) in enumerate(ranges):
            regions.append({"id": region_id, "lower": int(lower), "upper": int(upper)})
        return regions

    def _hasUniformMesh(self) -> bool:
        if self.meshGeneration is None:
            return False
        if self.meshGeneration.sparseMeshHandler is not None:
            return False
        mesh_info = getattr(self.meshGeneration, "currentMeshInfo", {})
        return bool(self.meshGeneration.currentX) and mesh_info.get("nx") is not None

    def _buildDomainForCurrentMesh(self):
        if self.meshGeneration is None:
            raise ValueError("Mesh generation state is unavailable.")

        contour_x = self.meshGeneration.currentX
        contour_y = self.meshGeneration.currentY
        subcontours_ranges = getattr(self.meshGeneration, "subcontoursRanges", None)
        sparse_handler = self.meshGeneration.sparseMeshHandler

        if sparse_handler is None:
            return build_uniform_domain(
                contour_x,
                contour_y,
                self.meshGeneration.currentMeshInfo,
                subcontours_ranges,
            )

        if self.meshGeneration.toggleZoomFlag:
            return build_sparse_composite_domain(
                contour_x,
                contour_y,
                sparse_handler,
                subcontours_ranges,
            )

        sparse_handler.setIntervals()
        return build_structured_domain(
            contour_x,
            contour_y,
            sparse_handler.dx,
            sparse_handler.dy,
            subcontours_ranges,
            mesh_kind="adaptive",
        )

    def syncWithMesh(self, sender=None, app_data=None) -> None:
        previous_values = self.region_values.copy()
        self.regions = self._collectRegions()
        self.region_values = {int(region["id"]): previous_values.get(int(region["id"]), 0.0) for region in self.regions}
        self.region_counts = {int(region["id"]): 0 for region in self.regions}
        if self.regions and self.active_region_id is None:
            self.active_region_id = int(self.regions[0]["id"])
        elif self.active_region_id is not None and all(int(region["id"]) != self.active_region_id for region in self.regions):
            self.active_region_id = int(self.regions[0]["id"]) if self.regions else None

        self.domain = None
        self.result = None
        self.solve_time_seconds = None
        self.csvExportFilePath = None
        self.csvExportFileName = None
        self.pngExportFilePath = None
        self.pngExportFileName = None
        self._resetScaleState()

        if self.meshGeneration is None or not getattr(self.meshGeneration, "currentX", None):
            self._setStatus("simulation.status.awaiting_mesh")
            self._renderRegionState()
            self._renderStats()
            self._renderExportState()
            self._plotContour()
            return

        try:
            self.domain = self._buildDomainForCurrentMesh()
            self.region_counts = self.domain.boundary_counts.copy()
            self._setStatus("simulation.status.ready")
        except ValueError as error:
            self.domain = None
            self._setStatus("simulation.status.analysis_failed", error=str(error))

        self._renderRegionState()
        self._renderStats()
        self._renderExportState()
        self._plotContour()

    def selectRegion(self, sender=None, app_data=None) -> None:
        label = app_data
        for region in self.regions:
            if self._regionLabel(region) == label:
                self.active_region_id = int(region["id"])
                break
        self._renderRegionState()

    def applyBoundaryValue(self, sender=None, app_data=None) -> None:
        region = self._currentRegion()
        if region is None:
            return
        region_id = int(region["id"])
        self.region_values[region_id] = float(dpg.get_value("simulationBoundaryValue"))
        self._setStatus("simulation.status.boundary_updated")
        self._renderRegionState()

    def changeProblem(self, sender=None, app_data=None) -> None:
        self.problem_key = strings.option_key("simulation_problem", dpg.get_value("simulationProblemList"))
        self._renderProblemState()

    def solve(self, sender=None, app_data=None) -> None:
        if self._uiReady():
            self.problem_key = strings.option_key("simulation_problem", dpg.get_value("simulationProblemList"))
            self.source_term = float(dpg.get_value("simulationSourceTerm"))

        self.syncWithMesh()
        if self.domain is None:
            return

        start = perf_counter()
        try:
            self.result = solve_dirichlet_problem(
                self.domain,
                self.region_values,
                problem_key=self.problem_key,
                source_term=self.source_term,
            )
        except ValueError as error:
            self.result = None
            self._resetScaleState()
            self._setStatus("simulation.status.solve_failed", error=str(error))
            self._renderStats()
            self._plotContour()
            return

        self.solve_time_seconds = perf_counter() - start
        self._updateScaleState()
        self._setStatus("simulation.status.solved")
        self._renderStats()
        self._plotSolution()

    def openCsvDirectorySelector(self, sender=None, app_data=None) -> None:
        if dpg.get_value("simulationCsvFileNameInput") != "":
            dpg.configure_item("simulationCsvDirectorySelector", show=True)

    def selectCsvFileFolder(self, sender=None, app_data=None) -> None:
        self.csvExportFilePath = app_data["file_path_name"]
        self.csvExportFileName = dpg.get_value("simulationCsvFileNameInput") + ".csv"
        self._renderExportState()

    def exportSolutionCsvToFile(self, path: str) -> None:
        if self.result is None or self.domain is None:
            raise ValueError("No solution is available for CSV export.")

        with open(path, "w", newline="", encoding="utf-8") as output_file:
            writer = csv.writer(output_file)
            writer.writerow(["i", "j", "x", "y", "value", "region_id", "node_type"])
            for row in range(self.domain.ny):
                for col in range(self.domain.nx):
                    if not self.domain.inside_mask[row, col]:
                        continue
                    node_type = "boundary" if self.domain.boundary_mask[row, col] else "internal"
                    region_id = int(self.domain.region_ids[row, col]) if self.domain.boundary_mask[row, col] else ""
                    writer.writerow(
                        [
                            col,
                            row,
                            float(self.domain.x_coords[col]),
                            float(self.domain.y_coords[row]),
                            float(self.result.values[row, col]),
                            region_id,
                            node_type,
                        ]
                    )

    def exportSolutionCsv(self, sender=None, app_data=None) -> None:
        if self.result is None or self.domain is None:
            return
        if self.csvExportFilePath is None:
            dpg.configure_item("simulationCsvExportError", show=True)
            return

        dpg.configure_item("simulationCsvExportError", show=False)
        output_path = os.path.join(self.csvExportFilePath, self.csvExportFileName)
        self.exportSolutionCsvToFile(output_path)
        self._setStatus("simulation.status.csv_exported")
        dpg.configure_item("simulationCsvExportWindow", show=False)

    def _mapDataPoint(self, x_value: float, y_value: float, x_min: float, y_min: float, scale: float, plot_left: float, plot_top: float, plot_height: float) -> tuple[float, float]:
        pixel_x = plot_left + (x_value - x_min) * scale
        pixel_y = plot_top + plot_height - (y_value - y_min) * scale
        return pixel_x, pixel_y

    def _rgbToBgr(self, color: tuple[int, int, int] | tuple[int, int, int, int]) -> tuple[int, int, int]:
        return int(color[2]), int(color[1]), int(color[0])

    def exportVisualizationPngToFile(self, path: str) -> None:
        if self.result is None or self.domain is None or self.meshGeneration is None:
            raise ValueError("No solution is available for PNG export.")

        image = np.full((PNG_CANVAS_HEIGHT, PNG_CANVAS_WIDTH, 3), 255, dtype=np.uint8)
        font = cv2.FONT_HERSHEY_SIMPLEX
        text_color = (24, 34, 49)
        muted_text_color = (90, 99, 109)

        def draw_text(text: str, x: float, y: float, color: tuple[int, int, int] = text_color, scale: float = 0.52):
            cv2.putText(
                image,
                text,
                (int(round(x)), int(round(y))),
                font,
                scale,
                self._rgbToBgr(color),
                1,
                cv2.LINE_AA,
            )

        contour_x = [float(value) for value in self.meshGeneration.currentX]
        contour_y = [float(value) for value in self.meshGeneration.currentY]
        rows, cols = np.argwhere(self.domain.inside_mask).T
        node_x = [float(self.domain.x_coords[col]) for col in cols]
        node_y = [float(self.domain.y_coords[row]) for row in rows]
        node_values = [float(self.result.values[row, col]) for row, col in zip(rows, cols)]

        data_x_values = contour_x + node_x
        data_y_values = contour_y + node_y
        x_min = min(data_x_values)
        x_max = max(data_x_values)
        y_min = min(data_y_values)
        y_max = max(data_y_values)
        data_width = max(x_max - x_min, 1.0e-9)
        data_height = max(y_max - y_min, 1.0e-9)

        max_plot_width = (
            PNG_CANVAS_WIDTH
            - PNG_MARGIN_LEFT
            - PNG_MARGIN_RIGHT
            - PNG_COLORBAR_GAP
            - PNG_COLORBAR_WIDTH
            - 90
        )
        max_plot_height = PNG_CANVAS_HEIGHT - PNG_MARGIN_TOP - PNG_MARGIN_BOTTOM
        scale = min(max_plot_width / data_width, max_plot_height / data_height)
        plot_width = data_width * scale
        plot_height = data_height * scale
        plot_left = PNG_MARGIN_LEFT + (max_plot_width - plot_width) / 2
        plot_top = PNG_MARGIN_TOP + (max_plot_height - plot_height) / 2
        plot_right = plot_left + plot_width
        plot_bottom = plot_top + plot_height

        cv2.rectangle(
            image,
            (int(round(plot_left)), int(round(plot_top))),
            (int(round(plot_right)), int(round(plot_bottom))),
            self._rgbToBgr((78, 89, 102)),
            2,
        )
        draw_text(strings.t("simulation.plot"), plot_left, 28)

        if self.scaleIsConstant:
            constant_index = 0.5
            colors = [self._samplePaletteColor(constant_index)[:3] for _ in node_values]
        else:
            scale_span = self.scaleMaxValue - self.scaleMinValue
            colors = [
                self._samplePaletteColor((value - self.scaleMinValue) / scale_span)[:3]
                for value in node_values
            ]

        pixel_spacing = min(self.domain.dx * scale, self.domain.dy * scale)
        node_radius = max(3, min(8, int(round(pixel_spacing * 0.18))))

        for x_value, y_value, color in zip(node_x, node_y, colors):
            pixel_x, pixel_y = self._mapDataPoint(x_value, y_value, x_min, y_min, scale, plot_left, plot_top, plot_height)
            cv2.circle(
                image,
                (int(round(pixel_x)), int(round(pixel_y))),
                node_radius,
                self._rgbToBgr(color),
                -1,
                cv2.LINE_AA,
            )

        contour_pixels = np.array(
            [
                self._mapDataPoint(x_value, y_value, x_min, y_min, scale, plot_left, plot_top, plot_height)
                for x_value, y_value in zip(contour_x, contour_y)
            ],
            dtype=np.int32,
        ).reshape((-1, 1, 2))
        cv2.polylines(image, [contour_pixels], True, self._rgbToBgr(text_color), 2, cv2.LINE_AA)

        colorbar_left = plot_right + PNG_COLORBAR_GAP
        colorbar_right = colorbar_left + PNG_COLORBAR_WIDTH
        colorbar_top = plot_top
        colorbar_bottom = plot_bottom
        colorbar_height = max(int(round(colorbar_bottom - colorbar_top)), 2)
        for offset in range(colorbar_height):
            normalized = 1.0 - (offset / (colorbar_height - 1))
            color = self._samplePaletteColor(normalized)[:3]
            cv2.line(
                image,
                (int(round(colorbar_left)), int(round(colorbar_top + offset))),
                (int(round(colorbar_right)), int(round(colorbar_top + offset))),
                self._rgbToBgr(color),
                1,
            )
        cv2.rectangle(
            image,
            (int(round(colorbar_left)), int(round(colorbar_top))),
            (int(round(colorbar_right)), int(round(colorbar_bottom))),
            self._rgbToBgr((78, 89, 102)),
            1,
        )

        label_left = colorbar_right + PNG_LABEL_GAP
        draw_text(strings.t("simulation.color_scale"), colorbar_left - 6, colorbar_top - 12)

        if self.scaleIsConstant:
            value_label = f"{self.scaleMinValue:.6g}"
            draw_text(value_label, label_left, colorbar_top + 4)
            draw_text(value_label, label_left, colorbar_bottom - 4)
            draw_text(strings.t("simulation.scale_constant", value=value_label), colorbar_left - 6, colorbar_bottom + 24, muted_text_color, 0.46)
        else:
            mid_value = (self.scaleMinValue + self.scaleMaxValue) / 2.0
            draw_text(f"{self.scaleMaxValue:.6g}", label_left, colorbar_top + 4)
            draw_text(f"{mid_value:.6g}", label_left, (colorbar_top + colorbar_bottom) / 2 + 4)
            draw_text(f"{self.scaleMinValue:.6g}", label_left, colorbar_bottom - 4)

        draw_text(strings.t("axes.x"), plot_left + plot_width / 2 - 5, plot_bottom + 34)
        draw_text(strings.t("axes.y"), plot_left - 16, plot_top - 10)
        draw_text(f"{x_min:.6g}", plot_left, plot_bottom + 18, muted_text_color, 0.46)
        draw_text(f"{x_max:.6g}", plot_right - 40, plot_bottom + 18, muted_text_color, 0.46)
        draw_text(f"{y_min:.6g}", plot_left - 46, plot_bottom - 2, muted_text_color, 0.46)
        draw_text(f"{y_max:.6g}", plot_left - 46, plot_top + 4, muted_text_color, 0.46)

        cv2.imwrite(path, image)

    def openPngDirectorySelector(self, sender=None, app_data=None) -> None:
        if dpg.get_value("simulationPngFileNameInput") != "":
            dpg.configure_item("simulationPngDirectorySelector", show=True)

    def selectPngFileFolder(self, sender=None, app_data=None) -> None:
        self.pngExportFilePath = app_data["file_path_name"]
        self.pngExportFileName = dpg.get_value("simulationPngFileNameInput") + ".png"
        self._renderExportState()

    def exportVisualizationPng(self, sender=None, app_data=None) -> None:
        if self.result is None or self.domain is None:
            return
        if self.pngExportFilePath is None:
            dpg.configure_item("simulationPngExportError", show=True)
            return

        dpg.configure_item("simulationPngExportError", show=False)
        output_path = os.path.join(self.pngExportFilePath, self.pngExportFileName)
        self.exportVisualizationPngToFile(output_path)
        self._setStatus("simulation.status.png_exported")
        dpg.configure_item("simulationPngExportWindow", show=False)

    def refreshTranslations(self, old_locale=None) -> None:
        if not self._uiReady():
            return

        dpg.set_value("simulationTitleText", strings.t("simulation.title"))
        dpg.set_value("simulationDescriptionText", strings.t("simulation.description"))
        dpg.set_value("simulationProblemText", strings.t("simulation.problem_type"))
        dpg.set_value("simulationSourceText", strings.t("simulation.source_term"))
        dpg.configure_item("simulationRefreshButton", label=strings.t("simulation.refresh_regions"))
        dpg.set_value("simulationBoundaryRegionsText", strings.t("simulation.boundary_regions"))
        dpg.set_value("simulationBoundaryValueText", strings.t("simulation.boundary_value"))
        dpg.configure_item("simulationApplyBoundaryButton", label=strings.t("simulation.apply_boundary_value"))
        dpg.configure_item("simulationSolveButton", label=strings.t("simulation.solve"))
        dpg.set_value("simulationResultsText", strings.t("simulation.results"))
        dpg.configure_item("simulationExportCsvButton", label=strings.t("simulation.export_solution_csv"))
        dpg.configure_item("simulationExportPngButton", label=strings.t("simulation.export_visualization_png"))
        dpg.set_value("simulationColorScaleText", strings.t("simulation.color_scale"))
        dpg.configure_item("simulationPlotParent", label=strings.t("simulation.plot"))
        dpg.configure_item("Simulation_x_axis", label=strings.t("axes.x"))
        dpg.configure_item("Simulation_y_axis", label=strings.t("axes.y"))

        dpg.configure_item("simulationCsvExportWindow", label=strings.t("common.save_file"))
        dpg.set_value("simulationCsvExportFileNameLabel", strings.t("common.enter_file_name"))
        dpg.set_value("simulationCsvExportDirectoryHint", strings.t("common.enter_file_name_before_directory"))
        dpg.configure_item("simulationCsvSelectDirectoryButton", label=strings.t("common.select_directory"))
        dpg.configure_item("simulationCsvExportSave", label=strings.t("common.save"))
        dpg.configure_item("simulationCsvExportCancel", label=strings.t("common.cancel"))
        dpg.set_value("simulationCsvExportError", strings.t("common.missing_file_name_or_directory"))

        dpg.configure_item("simulationPngExportWindow", label=strings.t("common.save_file"))
        dpg.set_value("simulationPngExportFileNameLabel", strings.t("common.enter_file_name"))
        dpg.set_value("simulationPngExportDirectoryHint", strings.t("common.enter_file_name_before_directory"))
        dpg.configure_item("simulationPngSelectDirectoryButton", label=strings.t("common.select_directory"))
        dpg.configure_item("simulationPngExportSave", label=strings.t("common.save"))
        dpg.configure_item("simulationPngExportCancel", label=strings.t("common.cancel"))
        dpg.set_value("simulationPngExportError", strings.t("common.missing_file_name_or_directory"))

        self._renderProblemState(old_locale=old_locale)
        self._renderRegionState()
        self._renderStats()
        self._renderExportState()
        self._renderColorScale()
        dpg.set_value("simulationStatusText", self.status_message)

        if self.result is None:
            self._plotContour()
        else:
            self._plotSolution()
