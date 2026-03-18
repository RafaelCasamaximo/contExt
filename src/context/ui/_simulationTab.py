import dearpygui.dearpygui as dpg

from . import strings


SIMULATION_COLORMAP_COLORS = [
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

SIMULATION_SCALE_TEXTURE_WIDTH = 512
SIMULATION_SCALE_TEXTURE_HEIGHT = 22


def _sampleSimulationScaleColor(normalized: float) -> tuple[int, int, int, int]:
    normalized = min(max(float(normalized), 0.0), 1.0)
    if len(SIMULATION_COLORMAP_COLORS) == 1:
        return SIMULATION_COLORMAP_COLORS[0]
    if normalized == 1.0:
        return SIMULATION_COLORMAP_COLORS[-1]

    position = normalized * (len(SIMULATION_COLORMAP_COLORS) - 1)
    left_index = int(position)
    right_index = min(left_index + 1, len(SIMULATION_COLORMAP_COLORS) - 1)
    blend = position - left_index
    left_color = SIMULATION_COLORMAP_COLORS[left_index]
    right_color = SIMULATION_COLORMAP_COLORS[right_index]
    return tuple(
        int(round(left_color[channel] + (right_color[channel] - left_color[channel]) * blend))
        for channel in range(4)
    )


def _buildSimulationScaleTextureData() -> list[float]:
    texture_data: list[float] = []
    for _ in range(SIMULATION_SCALE_TEXTURE_HEIGHT):
        for column in range(SIMULATION_SCALE_TEXTURE_WIDTH):
            color = _sampleSimulationScaleColor(column / (SIMULATION_SCALE_TEXTURE_WIDTH - 1))
            texture_data.extend(channel / 255.0 for channel in color)
    return texture_data


def showSimulation(callbacks):
    if not dpg.does_item_exist("textureRegistry"):
        dpg.add_texture_registry(show=False, tag="textureRegistry")
    dpg.add_colormap_registry(show=False, tag="simulationColormapRegistry")
    dpg.add_colormap(
        SIMULATION_COLORMAP_COLORS,
        qualitative=False,
        tag="simulationColormap",
        parent="simulationColormapRegistry",
    )
    if not dpg.does_item_exist("simulationScaleTexture"):
        dpg.add_static_texture(
            SIMULATION_SCALE_TEXTURE_WIDTH,
            SIMULATION_SCALE_TEXTURE_HEIGHT,
            _buildSimulationScaleTextureData(),
            tag="simulationScaleTexture",
            parent="textureRegistry",
        )

    with dpg.group(horizontal=True):
        with dpg.child_window(width=320):
            dpg.add_text(strings.t("simulation.title"), tag="simulationTitleText")
            dpg.add_text(strings.t("simulation.description"), tag="simulationDescriptionText", wrap=280)
            dpg.add_separator()

            dpg.add_text(strings.t("simulation.problem_type"), tag="simulationProblemText")
            dpg.add_listbox(
                tag="simulationProblemList",
                items=strings.option_labels("simulation_problem"),
                default_value=strings.option_label("simulation_problem", "laplace"),
                width=-1,
                callback=callbacks.simulation.changeProblem,
            )

            dpg.add_text(strings.t("simulation.source_term"), tag="simulationSourceText")
            dpg.add_input_float(tag="simulationSourceTerm", width=-1, default_value=0.0, enabled=False)
            dpg.add_button(
                tag="simulationRefreshButton",
                width=-1,
                label=strings.t("simulation.refresh_regions"),
                callback=callbacks.simulation.syncWithMesh,
            )

            dpg.add_separator()
            dpg.add_text(strings.t("simulation.boundary_regions"), tag="simulationBoundaryRegionsText")
            dpg.add_listbox(
                tag="simulationRegionList",
                items=[strings.t("simulation.no_regions")],
                default_value=strings.t("simulation.no_regions"),
                width=-1,
                num_items=6,
                callback=callbacks.simulation.selectRegion,
            )
            dpg.add_text(strings.t("simulation.region_range_empty"), tag="simulationRegionRange")
            dpg.add_text(strings.t("simulation.region_boundary_nodes", value="--"), tag="simulationRegionNodeCount")
            dpg.add_text(strings.t("simulation.boundary_value"), tag="simulationBoundaryValueText")
            dpg.add_input_float(tag="simulationBoundaryValue", width=-1, default_value=0.0)
            dpg.add_button(
                tag="simulationApplyBoundaryButton",
                width=-1,
                label=strings.t("simulation.apply_boundary_value"),
                callback=callbacks.simulation.applyBoundaryValue,
            )

            dpg.add_separator()
            dpg.add_button(
                tag="simulationSolveButton",
                width=-1,
                label=strings.t("simulation.solve"),
                callback=callbacks.simulation.solve,
            )
            dpg.add_text(strings.t("simulation.status.awaiting_mesh"), tag="simulationStatusText", wrap=280)

            dpg.add_separator()
            dpg.add_text(strings.t("simulation.results"), tag="simulationResultsText")
            dpg.add_text(strings.t("simulation.domain_nodes", value="--"), tag="simulationDomainNodeCount")
            dpg.add_text(strings.t("simulation.boundary_nodes", value="--"), tag="simulationBoundaryNodeCount")
            dpg.add_text(strings.t("simulation.internal_nodes", value="--"), tag="simulationInternalNodeCount")
            dpg.add_text(strings.t("simulation.system_size", value="--"), tag="simulationSystemSize")
            dpg.add_text(strings.t("simulation.residual", value="--"), tag="simulationResidual")
            dpg.add_text(strings.t("simulation.min_value", value="--"), tag="simulationMinValue")
            dpg.add_text(strings.t("simulation.max_value", value="--"), tag="simulationMaxValue")
            dpg.add_text(strings.t("simulation.mean_value", value="--"), tag="simulationMeanValue")
            dpg.add_text(strings.t("simulation.solve_time", value="--"), tag="simulationSolveTime")

            dpg.add_separator()
            dpg.add_button(
                tag="simulationExportCsvButton",
                width=-1,
                enabled=False,
                label=strings.t("simulation.export_solution_csv"),
                callback=lambda: dpg.configure_item("simulationCsvExportWindow", show=True),
            )
            dpg.add_button(
                tag="simulationExportPngButton",
                width=-1,
                enabled=False,
                label=strings.t("simulation.export_visualization_png"),
                callback=lambda: dpg.configure_item("simulationPngExportWindow", show=True),
            )

        with dpg.window(
            label=strings.t("common.save_file"),
            modal=False,
            show=False,
            tag="simulationCsvExportWindow",
            no_title_bar=False,
            min_size=[600, 255],
        ):
            dpg.add_text(strings.t("common.enter_file_name"), tag="simulationCsvExportFileNameLabel")
            dpg.add_input_text(tag="simulationCsvFileNameInput")
            dpg.add_separator()
            dpg.add_text(strings.t("common.enter_file_name_before_directory"), tag="simulationCsvExportDirectoryHint")
            dpg.add_button(
                tag="simulationCsvSelectDirectoryButton",
                width=-1,
                label=strings.t("common.select_directory"),
                callback=callbacks.simulation.openCsvDirectorySelector,
            )
            dpg.add_file_dialog(
                directory_selector=True,
                min_size=[400, 300],
                show=False,
                tag="simulationCsvDirectorySelector",
                callback=callbacks.simulation.selectCsvFileFolder,
            )
            dpg.add_separator()
            dpg.add_text(strings.fmt("file_name", value=""), tag="simulationCsvExportFileName")
            dpg.add_text(strings.fmt("full_path", value=""), tag="simulationCsvExportPathName")
            with dpg.group(horizontal=True):
                dpg.add_button(
                    tag="simulationCsvExportSave",
                    width=-1,
                    label=strings.t("common.save"),
                    callback=callbacks.simulation.exportSolutionCsv,
                )
                dpg.add_button(
                    tag="simulationCsvExportCancel",
                    width=-1,
                    label=strings.t("common.cancel"),
                    callback=lambda: dpg.configure_item("simulationCsvExportWindow", show=False),
                )
            dpg.add_text(strings.t("common.missing_file_name_or_directory"), tag="simulationCsvExportError", show=False)

        with dpg.window(
            label=strings.t("common.save_file"),
            modal=False,
            show=False,
            tag="simulationPngExportWindow",
            no_title_bar=False,
            min_size=[600, 255],
        ):
            dpg.add_text(strings.t("common.enter_file_name"), tag="simulationPngExportFileNameLabel")
            dpg.add_input_text(tag="simulationPngFileNameInput")
            dpg.add_separator()
            dpg.add_text(strings.t("common.enter_file_name_before_directory"), tag="simulationPngExportDirectoryHint")
            dpg.add_button(
                tag="simulationPngSelectDirectoryButton",
                width=-1,
                label=strings.t("common.select_directory"),
                callback=callbacks.simulation.openPngDirectorySelector,
            )
            dpg.add_file_dialog(
                directory_selector=True,
                min_size=[400, 300],
                show=False,
                tag="simulationPngDirectorySelector",
                callback=callbacks.simulation.selectPngFileFolder,
            )
            dpg.add_separator()
            dpg.add_text(strings.fmt("file_name", value=""), tag="simulationPngExportFileName")
            dpg.add_text(strings.fmt("full_path", value=""), tag="simulationPngExportPathName")
            with dpg.group(horizontal=True):
                dpg.add_button(
                    tag="simulationPngExportSave",
                    width=-1,
                    label=strings.t("common.save"),
                    callback=callbacks.simulation.exportVisualizationPng,
                )
                dpg.add_button(
                    tag="simulationPngExportCancel",
                    width=-1,
                    label=strings.t("common.cancel"),
                    callback=lambda: dpg.configure_item("simulationPngExportWindow", show=False),
                )
            dpg.add_text(strings.t("common.missing_file_name_or_directory"), tag="simulationPngExportError", show=False)

        with dpg.child_window(tag="SimulationParent"):
            with dpg.group():
                with dpg.child_window(tag="SimulationPlotPanel", height=-140):
                    with dpg.plot(tag="simulationPlotParent", label=strings.t("simulation.plot"), height=-1, width=-1, equal_aspects=True):
                        dpg.add_plot_legend()
                        dpg.add_plot_axis(dpg.mvXAxis, label=strings.t("axes.x"), tag="Simulation_x_axis")
                        dpg.add_plot_axis(dpg.mvYAxis, label=strings.t("axes.y"), tag="Simulation_y_axis")
                with dpg.child_window(tag="SimulationScalePanel", height=120, no_scrollbar=True):
                    dpg.add_text(strings.t("simulation.color_scale"), tag="simulationColorScaleText")
                    dpg.add_image("simulationScaleTexture", tag="simulationColorScaleImage", width=SIMULATION_SCALE_TEXTURE_WIDTH, height=22)
                    with dpg.group(horizontal=True):
                        dpg.add_text("--", tag="simulationColorScaleMinValue")
                        dpg.add_spacer(width=24)
                        dpg.add_text("--", tag="simulationColorScaleMaxValue")
                    dpg.add_text(strings.t("simulation.scale_pending"), tag="simulationColorScaleStatus", wrap=360)
