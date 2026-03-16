import dearpygui.dearpygui as dpg
from . import strings
from ._theme import bind_vector_themes

def showMeshGeneration(callbacks):
    with dpg.group(horizontal=True):
        with dpg.child_window(width=300, tag="meshGeneration"):
                
            with dpg.file_dialog(directory_selector=False, show=False, min_size=[400,300], tag='txt_file_dialog_id', callback=callbacks.meshGeneration.openContourFile):
                dpg.add_file_extension("", color=(150, 255, 150, 255))
                dpg.add_file_extension(".txt", color=(0, 255, 255, 255))
                dpg.add_file_extension(".dat", color=(0, 255, 255, 255))


            dpg.add_text(strings.t("mesh.select_contour_file"), tag="meshSelectContourFileText")
            dpg.add_button(tag="import_contour", width=-1, label=strings.t("mesh.import_contour"), callback=lambda: dpg.show_item("txt_file_dialog_id"))

            dpg.add_text(strings.fmt("file_name", value=""), tag="contour_file_name_text")
            dpg.add_text(strings.fmt("file_path", value=""), tag="contour_file_path_text")
                
            with dpg.window(label=strings.t("common.error"), modal=True, show=False, tag="txtFileErrorPopup"):
                dpg.add_text(strings.t("mesh.invalid_contour_message"), tag="meshInvalidContourText")
                dpg.add_button(tag="meshInvalidContourOk", label=strings.t("common.ok"), width=-1, callback=lambda: dpg.configure_item("txtFileErrorPopup", show=False))

            dpg.add_separator()

            dpg.add_text(strings.t("contour_extraction.contour_ordering"), tag="meshContourOrderingText")
            dpg.add_button(tag='contour_ordering2', width=-1, label=strings.t("common.counterclockwise"), callback=callbacks.meshGeneration.toggleOrdering)
            with dpg.tooltip("contour_ordering2"):
                dpg.add_text(strings.t("contour_extraction.contour_ordering_tooltip"), tag="meshContourOrderingTooltipText")

            dpg.add_separator()

            dpg.add_text(strings.t("mesh.mesh_grid"), tag="meshGridText")
            dpg.add_button(label=strings.t("mesh.plot_mesh_grid"), width=-1, tag='plotGrid', callback=callbacks.meshGeneration.toggleGrid, enabled=False)
            with dpg.tooltip("plotGrid"):
                dpg.add_text(strings.t("mesh.mesh_grid_tooltip"), tag="meshGridTooltipText")
                
            dpg.add_separator()

            dpg.add_text(strings.t("mesh.mesh_generation_options"), tag="meshGenerationOptionsText")
            dpg.add_text(strings.t("mesh.original_node_count"), tag="nodeNumber")
            with dpg.tooltip("nodeNumber", tag="nodeNumberTooltip", show=False):
                dpg.add_text(strings.t("mesh.node_number_tooltip"), tag="nodeNumberTooltipText")
            dpg.add_text(strings.fmt("nx", value="--"), tag='original_nx')
            dpg.add_text(strings.fmt("ny", value="--"), tag='original_ny')
            dpg.add_text(strings.t("mesh.node_count"), tag="meshNodeCountText")
            dpg.add_text(strings.fmt("nx", value="--"), tag='nx')
            dpg.add_text(strings.fmt("ny", value="--"), tag='ny')

            dpg.add_text(strings.t("mesh.original_node_spacing"), tag="meshOriginalNodeSpacingText")
            dpg.add_text(strings.fmt("dx", value="--"), tag='original_dx')
            dpg.add_text(strings.fmt("dy", value="--"), tag='original_dy')
            dpg.add_text(strings.t("mesh.node_spacing"), tag="meshNodeSpacingText")
            with dpg.group(horizontal=True):
                dpg.add_text(strings.fmt("dx", value=""), tag="meshDxLabel")
                dpg.add_input_float(tag='dx', width=-1, default_value=1, min_value=0.000001, min_clamped=True, callback=lambda: dpg.configure_item("dxVector", x=[0, dpg.get_value('dx')]))
            with dpg.group(horizontal=True):
                dpg.add_text(strings.fmt("dy", value=""), tag="meshDyLabel")
                dpg.add_input_float(tag='dy', width=-1, default_value=1, min_value=0.000001, min_clamped=True, callback=lambda: dpg.configure_item("dyVector", y=[0, dpg.get_value('dy')]))

            dpg.add_text(strings.t("mesh.original_mesh_origin"), tag="meshOriginalOriginText")
            dpg.add_text(strings.fmt("x", value="--"), tag='original_xi')
            dpg.add_text(strings.fmt("y", value="--"), tag='original_yi')
            dpg.add_text(strings.t("mesh.mesh_origin"), tag="meshOriginText")
            with dpg.group(horizontal=True):
                dpg.add_text(strings.fmt("x", value=""), tag="meshXiLabel")
                dpg.add_input_float(tag='xi', width=-1)
            with dpg.group(horizontal=True):
                dpg.add_text(strings.fmt("y", value=""), tag="meshYiLabel")
                dpg.add_input_float(tag='yi', width=-1)
            dpg.add_button(tag="meshApplyChangesButton", label=strings.t("common.apply_changes"), width=-1, callback= callbacks.meshGeneration.updateMesh)
            dpg.add_separator()
                
            with dpg.group(tag="sparseGroup"):
                dpg.add_text(strings.t("mesh.sparse_and_adaptive_mesh"), tag="meshSparseAdaptiveText")
                dpg.add_button(label=strings.t("mesh.add_mesh_zoom_region"), width=-1, enabled=False, tag="sparseButton", callback=lambda: dpg.configure_item("sparsePopup", show=True))
                dpg.add_button(label=strings.t("mesh.reset_mesh"), tag='resetMesh', width=-1, callback=callbacks.meshGeneration.resetMesh, show=False)
                with dpg.tooltip("resetMesh"):
                    dpg.add_text(strings.t("mesh.reset_mesh_tooltip"), tag="meshResetTooltipText")






            dpg.add_separator()
            dpg.add_text(strings.t("mesh.edit_active_subcontours"), tag="editContourText", show=True)
            dpg.add_button(tag='editContour', show=True, label=strings.t("mesh.edit_contour"), width=-1, callback = callbacks.meshGeneration.subcontoursTabInit)


            
            # EDIT CONTOUR WINDOW
            with dpg.window(label=strings.t("mesh.edit_active_subcontours"), modal=True, show=False, tag="editContourPopup", min_size=[900,600]):
                with dpg.group(horizontal=True):
                    with dpg.child_window(width=300, tag="editContourColumn",):
                        
                        # SUBCONTOUR TABLE STRUCTURE
                        dpg.add_text(strings.t("mesh.subcontours_data"), tag="subcontoursDataText")
                        with dpg.table(tag='EditContourTable', header_row=True, policy=dpg.mvTable_SizingFixedFit, row_background=True,
                            resizable=True, no_host_extendX=False, hideable=True,
                            borders_innerV=True, delay_search=True, borders_outerV=True, borders_innerH=True,
                            borders_outerH=True, parent='editContourColumn'):
                                dpg.add_table_column(tag="editContourTableColorColumn", label=strings.t("contour_extraction.table.color"), width_fixed=True)
                                dpg.add_table_column(tag="editContourTableSizeColumn", label=strings.t("contour_extraction.table.size"), width_fixed=True)
                                dpg.add_table_column(tag="editContourTableRangeColumn", label=strings.t("mesh.index_range"), width_fixed=True)


                    with dpg.child_window(tag='EditContourParent'):
                        # SUBCONTOURS BAR CONTROL
                        dpg.add_text(strings.t("mesh.subcontours_panel"), tag="subcontoursPanelText")
                        with dpg.group(horizontal=True):
                            dpg.add_text(strings.t("mesh.number"), tag="subcontoursNumberText")
                            dpg.add_slider_int(default_value=1, width=-1, min_value=1, max_value=10, tag="subcontoursCount", callback=callbacks.meshGeneration.createSubcontour)
                        with dpg.plot(label=strings.t("mesh.subcontours_range_control"), height=80, width=-1, tag="subcontourBarsPlot", no_mouse_pos=True):
                            with dpg.plot_axis(dpg.mvXAxis, tag="subcontourBarsPlotAxisX", no_gridlines=True):
                                dpg.set_axis_limits(dpg.last_item(), 0, 50)

                            with dpg.plot_axis(dpg.mvYAxis, tag="subcontourBarsPlotAxisY", no_gridlines=True):
                                dpg.set_axis_ticks(dpg.last_item(), (("", -10), ("", 0), ("", 10)))

                        # PLOTAR CONTORNO ATUAL
                        with dpg.plot(tag="subcontourNodesPlot", label=strings.t("mesh.subcontours_plot"), height=-1 - 20, width=-1, equal_aspects=True):
                            dpg.add_plot_axis(dpg.mvXAxis, label=strings.t("axes.x"), tag="subcontourNodesPlotAxisX")
                            dpg.add_plot_axis(dpg.mvYAxis, label=strings.t("axes.y"), tag="subcontourNodesPlotAxisY")

                            
                        with dpg.group(horizontal=True) as lowerLine:
                            closeButton = dpg.add_button(tag="subcontoursCloseButton", label=strings.t("common.close"), callback=callbacks.meshGeneration.saveSubcontoursEdit)

                    
            # dpg.set_item_pos(closeButton, (, ))
            # dpg.get_item_width(dpg.get_active_window()) 
            with dpg.item_handler_registry() as resizeEditSubcontourTab:
                #dpg.add_item_resize_handler(callback=lambda: print(dpg.get_item_rect_max(lowerLine), dpg.get_item_rect_size(lowerLine)))
                #dpg.add_item_resize_handler(callback=lambda: dpg.set_item_pos(closeButton, (, )))
                pass
            dpg.bind_item_handler_registry("editContourPopup", resizeEditSubcontourTab)








            dpg.add_separator()
            dpg.add_text(strings.t("mesh.save_mesh"), tag="exportMeshText", show=False)
            dpg.add_button(tag='exportMesh', show=False, label=strings.t("mesh.export_mesh"), width=-1, callback=lambda: dpg.configure_item("exportMeshFile", show=True))
            with dpg.tooltip("exportMesh", tag="exportMeshTooltip", show=False):
                dpg.add_text(strings.t("mesh.export_mesh_tooltip"), tag="exportMeshTooltipText")



            




                
            with dpg.window(label=strings.t("mesh.add_mesh_zoom_region"), modal=True, show=False, tag="sparsePopup", min_size=[400,420]):
                dpg.add_text(strings.t("mesh.mesh_zoom_type"), tag="meshZoomTypeText")
                dpg.add_button(tag='meshZoomType', enabled=True, label=strings.t("common.sparse"), width=-1, callback=callbacks.meshGeneration.toggleZoom)
                with dpg.tooltip("meshZoomType"):
                    dpg.add_text(strings.t("mesh.mesh_zoom_type_tooltip"), tag="meshZoomTypeTooltip")
                    
                dpg.add_separator()
                dpg.add_text(strings.t("mesh.zoom_region_name"), tag="zoomRegionNameText")
                dpg.add_input_text(tag="zoomRegionName", default_value=strings.t("mesh.default_zoom_region_name", index=1))

                dpg.add_separator()
                dpg.add_text(strings.t("mesh.zoom_node_size"), tag="zoomNodeSizeText")
                dpg.add_listbox(tag='dxListbox', items=strings.option_labels("zoom_node_size"), default_value=strings.option_label("zoom_node_size", "div2"))
                    
                dpg.add_separator()
                dpg.add_text(strings.t("mesh.zoom_bottom"), tag="zoomBottomText")
                with dpg.group(horizontal=True):
                    dpg.add_text(strings.fmt("bottom_x", value=""), tag="zoomBottomXLabel")
                    dpg.add_input_float(tag='xi_zoom')
                with dpg.group(horizontal=True):
                    dpg.add_text(strings.fmt("bottom_y", value=""), tag="zoomBottomYLabel")
                    dpg.add_input_float(tag='yi_zoom')

                dpg.add_separator()
                dpg.add_text(strings.t("mesh.zoom_top"), tag="zoomTopText")
                with dpg.group(horizontal=True):
                    dpg.add_text(strings.fmt("top_x", value=""), tag="zoomTopXLabel")
                    dpg.add_input_float(tag='xf_zoom')
                with dpg.group(horizontal=True):
                    dpg.add_text(strings.fmt("top_y", value=""), tag="zoomTopYLabel")
                    dpg.add_input_float(tag='yf_zoom')
                    
                dpg.add_separator()
                with dpg.group(horizontal=True):
                    dpg.add_button(tag="meshAddZoomButton", label=strings.t("mesh.add_zoom"), width=-1, callback=callbacks.meshGeneration.addZoomRegion)
                    dpg.add_button(tag="meshAddZoomCancel", label=strings.t("common.cancel"), width=-1, callback=lambda: dpg.configure_item("sparsePopup", show=False))
                dpg.add_text(strings.t("mesh.invalid_zoom_range"), tag="addZoomError", show=False)

            with dpg.window(label=strings.t("common.save_file"), modal=False, show=False, tag="exportMeshFile", no_title_bar=False, min_size=[600,255]):
                dpg.add_text(strings.t("common.enter_file_name"), tag="meshExportFileNameLabel")
                dpg.add_input_text(tag='inputMeshNameText')
                dpg.add_separator()
                dpg.add_text(strings.t("common.enter_file_name_before_directory"), tag="meshExportDirectoryHint")
                dpg.add_button(tag="meshSelectDirectory", label=strings.t("common.select_directory"), width=-1, callback= callbacks.meshGeneration.openMeshDirectorySelector)
                dpg.add_file_dialog(directory_selector=True, min_size=[400,300], show=False, tag='meshDirectorySelectorFileDialog', id="meshDirectorySelectorFileDialog", callback=callbacks.meshGeneration.selectMeshFileFolder)
                dpg.add_separator()
                dpg.add_text(strings.fmt("file_name", value=""), tag='exportMeshFileName')
                dpg.add_text(strings.fmt("full_path", value=""), tag='exportMeshPathName')
                with dpg.group(horizontal=True):
                    dpg.add_button(tag="meshExportSave", label=strings.t("common.save"), width=-1, callback=lambda: callbacks.meshGeneration.exportMesh())
                    dpg.add_button(tag="meshExportCancel", label=strings.t("common.cancel"), width=-1, callback=lambda: dpg.configure_item('exportMeshFile', show=False))
                dpg.add_text(strings.t("common.missing_file_name_or_directory"), tag="exportMeshError", show=False)

            dpg.add_separator()

        
        with dpg.child_window(tag='MeshGenerationParent'):
            with dpg.plot(tag="meshPlotParent", label=strings.t("mesh.plot"), height=-1 - 20, width=-1, equal_aspects=True):
                dpg.add_plot_legend()
                dpg.add_plot_axis(dpg.mvXAxis, label=strings.t("axes.x"), tag="x_axis")
                dpg.add_plot_axis(dpg.mvYAxis, label=strings.t("axes.y"), tag="y_axis")
                dpg.add_line_series([0, 1], [0, 0],  parent="y_axis", tag="dxVector")
                dpg.add_line_series([0, 0], [0, 1],  parent="y_axis", tag="dyVector")
                bind_vector_themes("dxVector", "dyVector")

            with dpg.group(horizontal=True):
                dpg.add_text(strings.fmt("original_area", value="--"), tag='original_area')
                dpg.add_text(strings.fmt("current_area", value="--"), tag='current_area')
                dpg.add_text(strings.fmt("difference", value="--"), tag='difference')
            with dpg.group(horizontal=True):
                dpg.add_text(strings.fmt("contour_node_count", value="--"), tag='contour_nodes_number')
                dpg.add_text(strings.fmt("internal_node_count", value="--"), tag='current_nodes_number', show=False)   
            pass


def refreshMeshTranslations(old_locale=None):
    old_locale = old_locale or strings.get_locale()
    zoom_size_value = dpg.get_value("dxListbox")
    dpg.set_value("meshSelectContourFileText", strings.t("mesh.select_contour_file"))
    dpg.configure_item("import_contour", label=strings.t("mesh.import_contour"))
    dpg.configure_item("txtFileErrorPopup", label=strings.t("common.error"))
    dpg.set_value("meshInvalidContourText", strings.t("mesh.invalid_contour_message"))
    dpg.configure_item("meshInvalidContourOk", label=strings.t("common.ok"))
    dpg.set_value("meshContourOrderingText", strings.t("contour_extraction.contour_ordering"))
    dpg.set_value("meshContourOrderingTooltipText", strings.t("contour_extraction.contour_ordering_tooltip"))
    dpg.set_value("meshGridText", strings.t("mesh.mesh_grid"))
    dpg.set_value("meshGridTooltipText", strings.t("mesh.mesh_grid_tooltip"))
    dpg.set_value("meshGenerationOptionsText", strings.t("mesh.mesh_generation_options"))
    dpg.set_value("nodeNumber", strings.t("mesh.original_node_count"))
    dpg.set_value("nodeNumberTooltipText", strings.t("mesh.node_number_tooltip"))
    dpg.set_value("meshNodeCountText", strings.t("mesh.node_count"))
    dpg.set_value("meshOriginalNodeSpacingText", strings.t("mesh.original_node_spacing"))
    dpg.set_value("meshNodeSpacingText", strings.t("mesh.node_spacing"))
    dpg.set_value("meshDxLabel", strings.fmt("dx", value=""))
    dpg.set_value("meshDyLabel", strings.fmt("dy", value=""))
    dpg.set_value("meshOriginalOriginText", strings.t("mesh.original_mesh_origin"))
    dpg.set_value("meshOriginText", strings.t("mesh.mesh_origin"))
    dpg.set_value("meshXiLabel", strings.fmt("x", value=""))
    dpg.set_value("meshYiLabel", strings.fmt("y", value=""))
    dpg.configure_item("meshApplyChangesButton", label=strings.t("common.apply_changes"))
    dpg.set_value("meshSparseAdaptiveText", strings.t("mesh.sparse_and_adaptive_mesh"))
    dpg.configure_item("sparseButton", label=strings.t("mesh.add_mesh_zoom_region"))
    dpg.configure_item("resetMesh", label=strings.t("mesh.reset_mesh"))
    dpg.set_value("meshResetTooltipText", strings.t("mesh.reset_mesh_tooltip"))
    dpg.set_value("editContourText", strings.t("mesh.edit_active_subcontours"))
    dpg.configure_item("editContour", label=strings.t("mesh.edit_contour"))
    dpg.configure_item("editContourPopup", label=strings.t("mesh.edit_active_subcontours"))
    dpg.set_value("subcontoursDataText", strings.t("mesh.subcontours_data"))
    dpg.configure_item("editContourTableColorColumn", label=strings.t("contour_extraction.table.color"))
    dpg.configure_item("editContourTableSizeColumn", label=strings.t("contour_extraction.table.size"))
    dpg.configure_item("editContourTableRangeColumn", label=strings.t("mesh.index_range"))
    dpg.set_value("subcontoursPanelText", strings.t("mesh.subcontours_panel"))
    dpg.set_value("subcontoursNumberText", strings.t("mesh.number"))
    dpg.configure_item("subcontourBarsPlot", label=strings.t("mesh.subcontours_range_control"))
    dpg.configure_item("subcontourNodesPlot", label=strings.t("mesh.subcontours_plot"))
    dpg.configure_item("subcontourNodesPlotAxisX", label=strings.t("axes.x"))
    dpg.configure_item("subcontourNodesPlotAxisY", label=strings.t("axes.y"))
    dpg.configure_item("subcontoursCloseButton", label=strings.t("common.close"))
    dpg.set_value("exportMeshText", strings.t("mesh.save_mesh"))
    dpg.configure_item("exportMesh", label=strings.t("mesh.export_mesh"))
    dpg.set_value("exportMeshTooltipText", strings.t("mesh.export_mesh_tooltip"))
    dpg.configure_item("sparsePopup", label=strings.t("mesh.add_mesh_zoom_region"))
    dpg.set_value("meshZoomTypeText", strings.t("mesh.mesh_zoom_type"))
    dpg.set_value("zoomRegionNameText", strings.t("mesh.zoom_region_name"))
    dpg.set_value("zoomNodeSizeText", strings.t("mesh.zoom_node_size"))
    dpg.configure_item("dxListbox", items=strings.option_labels("zoom_node_size"))
    dpg.set_value("dxListbox", strings.translate_option_value("zoom_node_size", zoom_size_value, old_locale))
    dpg.set_value("zoomBottomText", strings.t("mesh.zoom_bottom"))
    dpg.set_value("zoomBottomXLabel", strings.fmt("bottom_x", value=""))
    dpg.set_value("zoomBottomYLabel", strings.fmt("bottom_y", value=""))
    dpg.set_value("zoomTopText", strings.t("mesh.zoom_top"))
    dpg.set_value("zoomTopXLabel", strings.fmt("top_x", value=""))
    dpg.set_value("zoomTopYLabel", strings.fmt("top_y", value=""))
    dpg.configure_item("meshAddZoomButton", label=strings.t("mesh.add_zoom"))
    dpg.configure_item("meshAddZoomCancel", label=strings.t("common.cancel"))
    dpg.set_value("addZoomError", strings.t("mesh.invalid_zoom_range"))
    dpg.configure_item("exportMeshFile", label=strings.t("common.save_file"))
    dpg.set_value("meshExportFileNameLabel", strings.t("common.enter_file_name"))
    dpg.set_value("meshExportDirectoryHint", strings.t("common.enter_file_name_before_directory"))
    dpg.configure_item("meshSelectDirectory", label=strings.t("common.select_directory"))
    dpg.configure_item("meshExportSave", label=strings.t("common.save"))
    dpg.configure_item("meshExportCancel", label=strings.t("common.cancel"))
    dpg.set_value("exportMeshError", strings.t("common.missing_file_name_or_directory"))
    dpg.configure_item("meshPlotParent", label=strings.t("mesh.plot"))
    dpg.configure_item("x_axis", label=strings.t("axes.x"))
    dpg.configure_item("y_axis", label=strings.t("axes.y"))
