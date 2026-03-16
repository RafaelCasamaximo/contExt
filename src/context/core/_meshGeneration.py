import dearpygui.dearpygui as dpg
import os.path
import colorsys
import random
from ._mesh import Mesh
from ._sparseMesh import SparseMesh
from ._scopeList  import ScopeList
from math import floor, ceil
from ..ui import strings

class MeshGeneration:
    
    def __init__(self) -> None:

        self.filePath = None
        self.txtFilePath = None
        self.txtFileName = None
        self.toggleOrderingFlag = True
        self.toggleZoomFlag = True
        self.toggleGridFlag = False
        self.sparseMeshHandler = None
        self.countGrid = 0
        self.originalX = []
        self.originalY = []
        self.currentX  = []
        self.currentY  = []
        self.exportFilePath = None
        self.exportFileName = None
        self.originalMeshInfo = {
            "nx": None,
            "ny": None,
            "xmin": None,
            "ymin": None,
            "dx": None,
            "dy": None,
        }
        self.currentMeshInfo = {
            "nx": None,
            "ny": None,
            "xmin": None,
            "ymin": None,
            "dx": None,
            "dy": None,
        }
        self.originalAreaValue = None
        self.currentAreaValue = None
        self.differenceValue = None
        self.differencePercent = None
        self.contourNodeCount = None
        self.internalNodeCount = None
        self.zoomRegionSpecs = []

        # Subcontours feature
        self.subcontours = None

        self.firstSubcontourEdit = True

        self.subcontoursRanges = []
        self.fullScope = [0, 100]
        self.fullScopeSize = self.fullScope[1] - self.fullScope[0]
        self.subcontoursLines = []
        self.scopeLines  = []
        self.scopeColors = []
        self.scopeThemes = []

    def renderFileInfo(self):
        dpg.set_value('contour_file_name_text', strings.fmt("file_name", value=self.txtFileName or ""))
        dpg.set_value('contour_file_path_text', strings.fmt("file_path", value=self.txtFilePath or ""))

    def renderMeshMetadata(self):
        dpg.set_value("original_xi", strings.fmt("x", value=self.originalMeshInfo["xmin"] if self.originalMeshInfo["xmin"] is not None else "--"))
        dpg.set_value("original_yi", strings.fmt("y", value=self.originalMeshInfo["ymin"] if self.originalMeshInfo["ymin"] is not None else "--"))
        dpg.set_value("original_dx", strings.fmt("dx", value=self.originalMeshInfo["dx"] if self.originalMeshInfo["dx"] is not None else "--"))
        dpg.set_value("original_dy", strings.fmt("dy", value=self.originalMeshInfo["dy"] if self.originalMeshInfo["dy"] is not None else "--"))
        dpg.set_value("original_nx", strings.fmt("nx", value=int(self.originalMeshInfo["nx"]) if self.originalMeshInfo["nx"] is not None else "--"))
        dpg.set_value("original_ny", strings.fmt("ny", value=int(self.originalMeshInfo["ny"]) if self.originalMeshInfo["ny"] is not None else "--"))
        dpg.set_value("nx", strings.fmt("nx", value=int(self.currentMeshInfo["nx"]) if self.currentMeshInfo["nx"] is not None else "--"))
        dpg.set_value("ny", strings.fmt("ny", value=int(self.currentMeshInfo["ny"]) if self.currentMeshInfo["ny"] is not None else "--"))

    def renderAreaStats(self):
        original_area = "--" if self.originalAreaValue is None else self.originalAreaValue
        current_area = "--" if self.currentAreaValue is None else self.currentAreaValue
        contour_nodes = "--" if self.contourNodeCount is None else self.contourNodeCount
        internal_nodes = "--" if self.internalNodeCount is None else self.internalNodeCount

        dpg.set_value("original_area", strings.fmt("original_area", value=original_area))
        dpg.set_value("current_area", strings.fmt("current_area", value=current_area))
        if self.differenceValue is None or self.differencePercent is None:
            dpg.set_value("difference", strings.fmt("difference", value="--"))
        else:
            dpg.set_value("difference", strings.fmt("difference_percent", value=self.differenceValue, percent=self.differencePercent))
        dpg.set_value("contour_nodes_number", strings.fmt("contour_node_count", value=contour_nodes))
        dpg.set_value("current_nodes_number", strings.fmt("internal_node_count", value=internal_nodes))

    def renderExportState(self):
        export_file_name = self.exportFileName or ""
        export_path = ""
        if self.exportFilePath is not None and self.exportFileName is not None:
            export_path = os.path.join(self.exportFilePath, self.exportFileName)
        dpg.set_value('exportMeshFileName', strings.fmt("file_name", value=export_file_name))
        dpg.set_value('exportMeshPathName', strings.fmt("full_path", value=export_path))

    def renderToggleLabels(self):
        ordering_label = strings.t("common.counterclockwise") if self.toggleOrderingFlag else strings.t("common.clockwise")
        dpg.configure_item('contour_ordering', label=ordering_label)
        dpg.configure_item('contour_ordering2', label=ordering_label)
        zoom_label = strings.t("common.sparse") if self.toggleZoomFlag else strings.t("common.adaptive")
        dpg.configure_item('meshZoomType', label=zoom_label)
        grid_label = strings.t("mesh.hide_mesh_grid") if self.toggleGridFlag else strings.t("mesh.plot_mesh_grid")
        dpg.configure_item("plotGrid", label=grid_label)
        tooltip_key = "mesh.mesh_zoom_type_tooltip" if self.sparseMeshHandler is None else "mesh.mesh_zoom_type_locked_tooltip"
        dpg.set_value("meshZoomTypeTooltip", strings.t(tooltip_key))

    def renderZoomRegion(self, index, spec, range_data=None):
        option_label = strings.option_label("zoom_node_size", spec["division_key"])
        dpg.set_value("zoomTxt" + str(index), spec["name"])
        dpg.set_value("listBoxZoom" + str(index), strings.fmt("node_size", value=option_label))

        if range_data is None:
            range_data = spec
        dpg.set_value("xminZoom" + str(index), strings.fmt("bottom_x", value=range_data['xi']))
        dpg.set_value("yminZoom" + str(index), strings.fmt("bottom_y", value=range_data['yi']))
        dpg.set_value("xmaxZoom" + str(index), strings.fmt("top_x", value=range_data['xf']))
        dpg.set_value("ymaxZoom" + str(index), strings.fmt("top_y", value=range_data['yf']))
        dpg.configure_item("removeZoom" + str(index), label=strings.t("mesh.remove_zoom_region"))

    def refreshTranslations(self, old_locale=None):
        old_locale = old_locale or strings.get_locale()
        self.renderFileInfo()
        self.renderMeshMetadata()
        self.renderAreaStats()
        self.renderExportState()
        self.renderToggleLabels()
        if dpg.does_item_exist("originalMeshPlot"):
            dpg.configure_item("originalMeshPlot", label=strings.t("mesh.original_mesh"))
        if dpg.does_item_exist("meshPlot"):
            dpg.configure_item("meshPlot", label=strings.t("mesh.current_mesh"))
        for index, spec in enumerate(self.zoomRegionSpecs, start=1):
            if dpg.does_item_exist("zoomTxt" + str(index)):
                range_data = None
                if self.sparseMeshHandler is not None and len(self.sparseMeshHandler.ranges) > index:
                    range_data = self.sparseMeshHandler.ranges[index]
                self.renderZoomRegion(index, spec, range_data=range_data)
        next_index = len(self.zoomRegionSpecs) + 1
        previous_default = strings.t("mesh.default_zoom_region_name", locale=old_locale, index=next_index)
        if dpg.get_value("zoomRegionName") == previous_default:
            dpg.set_value("zoomRegionName", strings.t("mesh.default_zoom_region_name", index=next_index))


    def createSubcontour(self):        
        subcontoursCount = dpg.get_value("subcontoursCount")

        self.subcontoursLines = []
        for n in range(1, subcontoursCount):
            self.subcontoursLines.append(n * self.fullScopeSize/subcontoursCount)

        for linObj in self.scopeLines:
            dpg.delete_item(linObj)

        self.scopeLines.clear()

        scopesLimits = [self.fullScope[0]]
        for lin in self.subcontoursLines:
            self.scopeLines.append(dpg.add_drag_line(label="", color=[255, 0, 0, 255], default_value=lin, callback=self.updateSubcontours, parent="subcontourBarsPlot"))
            # floor(lin) - floor(1 - (lin - floor(lin)))
            scopesLimits.extend([ceil(lin) - 1,    ceil(lin)])
        scopesLimits.append(self.fullScope[1])

        self.subcontoursRanges = [[scopesLimits[2*i], scopesLimits[2*i+1]] for i in range(0, subcontoursCount)]


        self.scopeColors = []
        self.scopeThemes = []
        # for i in range(0, subcontoursCount):
        #     self.scopeColors.append((random.randint(0,255), random.randint(0,255), random.randint(0,255), 255))
        n = subcontoursCount
        colorShiftValue = random.random()
        self.scopeColors = [tuple(map(lambda x: x * 255, colorsys.hsv_to_rgb(1/n * i + colorShiftValue, 1, 1))) for i in range(0, n)]
        random.shuffle(self.scopeColors)

        for c in reversed(self.scopeColors):
            with dpg.theme() as item_theme:
                with dpg.theme_component(dpg.mvBarSeries):
                    dpg.add_theme_color(dpg.mvPlotCol_Fill, c, category=dpg.mvThemeCat_Plots)
                with dpg.theme_component(dpg.mvLineSeries):
                    dpg.add_theme_color(dpg.mvPlotCol_Line, c, category=dpg.mvThemeCat_Plots)
            self.scopeThemes.append(item_theme)

        


        self.plotSubcontourBar()
        self.plotSubcontourNode()
        self.updateSubcontourTable()

    def plotSubcontourBar(self):
        dpg.delete_item("subcontourBarsPlotAxisX")
        with dpg.plot_axis(dpg.mvXAxis, tag="subcontourBarsPlotAxisX", parent="subcontourBarsPlot", no_gridlines=True):
            dpg.set_axis_limits(dpg.last_item(), 0, self.fullScope[1])
            ticks = [("0", 0), (f"{self.fullScope[1]}", self.fullScope[1])]
            if (len(self.subcontoursLines) > 0):
                ticks.extend([(f"{ceil(dpg.get_value(lin))-1} {ceil(dpg.get_value(lin))}", dpg.get_value(lin)) for lin in self.scopeLines])
            dpg.set_axis_ticks(dpg.last_item(), tuple(ticks))

        dpg.delete_item("subcontourBarsPlotAxisY")
        with dpg.plot_axis(dpg.mvYAxis, tag="subcontourBarsPlotAxisY", parent="subcontourBarsPlot", no_gridlines=True):
            dpg.set_axis_ticks(dpg.last_item(), (("", -10), ("", 0), ("", 10    )))

            bar = dpg.add_bar_series([self.fullScope[1]], [0], label="T",  weight=1, horizontal=True)
            dpg.bind_item_theme(bar, self.scopeThemes[0])
            if (len(self.subcontoursLines) > 0):
                k = 1
                for lin in reversed(self.scopeLines):
                    bar = dpg.add_bar_series([dpg.get_value(lin)], [0], label="T",  weight=1, horizontal=True)
                    dpg.bind_item_theme(bar, self.scopeThemes[k])
                    k += 1

    def plotSubcontourNode(self):
        dpg.delete_item("subcontourNodesPlotAxisY")
        with dpg.plot_axis(dpg.mvYAxis, label=strings.t("axes.y"), tag="subcontourNodesPlotAxisY", parent="subcontourNodesPlot"):
            for scope, theme in zip(self.subcontoursRanges, reversed(self.scopeThemes)):
                xSeries = [self.currentX[i] for i in range(scope[0], scope[1]+1)]
                ySeries = [self.currentY[i] for i in range(scope[0], scope[1]+1)]
                nodes = dpg.add_line_series(xSeries, ySeries)
                dpg.bind_item_theme(nodes, theme)




    def updateSubcontours(self):
        self.subcontoursLines.clear()
        for linObj in self.scopeLines:
            self.subcontoursLines.append(dpg.get_value(linObj))

        subcontoursCount = dpg.get_value("subcontoursCount")
        scopesLimits = [self.fullScope[0]]
        for lin in self.subcontoursLines:
            #floor(lin) - floor(1 - (lin - floor(lin)))
            scopesLimits.extend([ceil(lin) - 1,    ceil(lin)])
        scopesLimits.append(self.fullScope[1])

        self.subcontoursRanges = [[scopesLimits[2*i], scopesLimits[2*i+1]] for i in range(0, subcontoursCount)]


        self.plotSubcontourBar()
        self.plotSubcontourNode()
        self.updateSubcontourTable()


    def updateSubcontourTable(self):
        dpg.delete_item('EditContourTable')
        with dpg.table(tag='EditContourTable', header_row=True, policy=dpg.mvTable_SizingFixedFit, row_background=True,
            resizable=True, no_host_extendX=False, hideable=True,
            borders_innerV=True, delay_search=True, borders_outerV=True, borders_innerH=True,
            borders_outerH=True, parent='editContourColumn'):
                dpg.add_table_column(tag="editContourTableColorColumn", label=strings.t("contour_extraction.table.color"), width_fixed=True)
                dpg.add_table_column(tag="editContourTableSizeColumn", label=strings.t("contour_extraction.table.size"), width_fixed=True)
                dpg.add_table_column(tag="editContourTableRangeColumn", label=strings.t("mesh.index_range"), width_fixed=True)


                activeSubcontours = [
                    {
                        "color": scopeColor,
                        "lower": scopeRange[0],
                        "upper": scopeRange[1],
                        "size":  scopeRange[1] - scopeRange[0] + 1
                     } for scopeRange, scopeColor in zip(self.subcontoursRanges, self.scopeColors)]

                for sub in activeSubcontours:
                    with dpg.table_row():
                        with dpg.table_cell():
                            dpg.add_color_button(default_value = sub['color'])
                        with dpg.table_cell():
                            dpg.add_text(str(sub['size']))
                        with dpg.table_cell():
                            dpg.add_text(f"[{sub['lower']}, {sub['upper']}]")




    def subcontoursTabInit(self):
        dpg.configure_item("editContourPopup", show=True)

        if self.firstSubcontourEdit:
            self.firstSubcontourEdit = False
            self.createSubcontour()
        else:
            self.plotSubcontourBar()
            self.plotSubcontourNode()
            self.updateSubcontourTable()

        

            

    def saveSubcontoursEdit(self):
        self.savedSubcontourData = {
            "subcontoursRanges":    self.subcontoursRanges,
            "fullScope":            self.fullScope,
            "fullScopeSize":        self.fullScopeSize,
            "subcontoursLines":     self.subcontoursLines,
            "scopeLines":           self.scopeLines,
            "scopeColors":          self.scopeColors,
            "scopeThemes":          self.scopeThemes
        }

        dpg.configure_item("editContourPopup", show=False)



        


                








    def openContourFile(self, sender = None, app_data = None):
        self.txtFilePath = app_data['file_path_name']
        self.txtFileName = app_data['file_name']
        self.renderFileInfo()

        self.originalX = []
        self.originalY = []
        f = open(self.txtFilePath,'r')
        for line in f.readlines():
            aux = line.split()
            if(len(aux) != 2):
                print("The file does not contain a valid contour.")
                dpg.configure_item("txtFileErrorPopup", show=True)
                return
            try:
                self.originalX.append(float(aux[0]))
                self.originalY.append(float(aux[1]))
            except:
                print("The file does not contain a valid contour.")
                dpg.configure_item("txtFileErrorPopup", show=True)
                return
        f.close()
        self.importContour()

    def cancelImportContour(self, sender = None, app_data = None):
        dpg.hide_item("txt_file_dialog_id")

    def importContour(self, sender = None, app_data = None):
        if self.toggleGridFlag:
            self.removeGrid()
        for item in ("meshPlot", "originalMeshPlot"):
            if dpg.does_item_exist(item):
                dpg.delete_item(item)
        dpg.configure_item('contour_ordering2', enabled=True)
        dpg.configure_item('sparseButton', enabled=True)
        dpg.configure_item('plotGrid', enabled=True)

        if self.currentX == [] and self.currentY == []:
            dpg.configure_item("exportMesh", show=True)
            dpg.configure_item("exportMeshText", show=True)
            dpg.configure_item("exportMeshTooltip", show=True)
            dpg.add_separator(parent="meshGeneration")


        self.currentX = self.originalX
        self.currentY = self.originalY
        self.originalX = self.originalX[4:]
        self.originalY = self.originalY[4:]

        if not self.toggleOrderingFlag:
            self.originalX = self.originalX[::-1]
            self.originalY = self.originalY[::-1]
            self.toggleOrdering()
        
        self.currentX = self.currentX[:4] + self.originalX
        self.currentY = self.currentY[:4] + self.originalY

        nx = self.currentX[0]
        ny = self.currentY[0]
        xmin = self.currentX[1]
        ymin = self.currentY[1]
        dx = self.currentX[3]
        dy = self.currentY[3]
        self.originalMeshInfo.update({"nx": nx, "ny": ny, "xmin": xmin, "ymin": ymin, "dx": dx, "dy": dy})
        self.currentMeshInfo.update({"nx": nx, "ny": ny, "xmin": xmin, "ymin": ymin, "dx": dx, "dy": dy})
        self.renderMeshMetadata()
        dpg.configure_item("dx", default_value = dx)
        dpg.configure_item("dy", default_value = dy)
        dpg.configure_item("xi", default_value = xmin)
        dpg.configure_item("yi", default_value = ymin)
        dpg.configure_item("xi_zoom", default_value = xmin)
        dpg.configure_item("yi_zoom", default_value = ymin)
        dpg.configure_item("xf_zoom", default_value = xmin + dx, min_value = xmin + dx)
        dpg.configure_item("yf_zoom", default_value = ymin + dy, min_value = ymin + dy)

        self.currentAreaValue = None
        self.differenceValue = None
        self.differencePercent = None

        self.currentX = self.currentX[4:]
        self.currentY = self.currentY[4:]
        self.originalAreaValue = Mesh.get_area(self.currentX, self.currentY)
        self.currentAreaValue = None
        self.contourNodeCount = None
        self.internalNodeCount = None
        self.renderAreaStats()
        dpg.add_line_series(self.currentX, self.currentY, label=strings.t("mesh.original_mesh"), tag="originalMeshPlot", parent='y_axis')
        dpg.fit_axis_data("x_axis")
        dpg.fit_axis_data("y_axis")

        dpg.configure_item("dxVector", x=[0, dpg.get_value('dx')])
        dpg.configure_item("dyVector", y=[0, dpg.get_value('dy')])

        self.subcontours = ScopeList(0, len(self.currentX))
        self.fullScope = [0, len(self.currentX)-1]
        self.fullScopeSize = self.fullScope[1] - self.fullScope[0]
        dpg.set_value("subcontoursCount", 1)
        self.createSubcontour()
        #print(self.subcontours.getScopes())

    def toggleOrdering(self, sender = None, app_data = None):
        self.toggleOrderingFlag = not self.toggleOrderingFlag
        self.renderToggleLabels()

    def toggleZoom(self, sender = None, app_data = None):
        self.toggleZoomFlag = not self.toggleZoomFlag
        self.renderToggleLabels()

    def addZoomRegion(self, sender = None, app_data = None):
        division_key = strings.option_key("zoom_node_size", dpg.get_value("dxListbox"))
        division_map = {"div2": 2, "div4": 4, "div8": 8, "div16": 16}
        n = division_map[division_key]
        name = dpg.get_value("zoomRegionName")
        dx = dpg.get_value("dx")
        dy = dpg.get_value("dy")
        xmin = dpg.get_value("xi_zoom")
        ymin = dpg.get_value("yi_zoom")
        xmax = dpg.get_value("xf_zoom")
        ymax = dpg.get_value("yf_zoom")

        if self.sparseMeshHandler == None:
            self.sparseMeshHandler = SparseMesh()
            self.sparseMeshHandler.addRange(dpg.get_value("xi"), dpg.get_value("yi"), max(self.originalX), max(self.originalY), dx, dy)
        if not self.sparseMeshHandler.addRange(xmin, ymin, xmax, ymax, n, n):
            dpg.configure_item("addZoomError", show=True)
            return

        dpg.configure_item("addZoomError", show=False)
        nZoom = len(self.sparseMeshHandler.ranges) - 1
        spec = {
            "name": name,
            "division_key": division_key,
            "xi": xmin,
            "yi": ymin,
            "xf": xmax,
            "yf": ymax,
        }
        self.zoomRegionSpecs.append(spec)
        dpg.add_separator(tag="separatorZoomStart" + str(nZoom), parent="sparseGroup")
        dpg.add_text(name, tag="zoomTxt" + str(nZoom), parent="sparseGroup")
        dpg.add_text("", tag="listBoxZoom" + str(nZoom), parent="sparseGroup")
        dpg.add_text("", tag="xminZoom" + str(nZoom), parent="sparseGroup")
        dpg.add_text("", tag="yminZoom" + str(nZoom), parent="sparseGroup")
        dpg.add_text("", tag="xmaxZoom" + str(nZoom), parent="sparseGroup")
        dpg.add_text("", tag="ymaxZoom" + str(nZoom), parent="sparseGroup")
        dpg.add_button(tag="removeZoom" + str(nZoom), width=-1, label=strings.t("mesh.remove_zoom_region"), parent="sparseGroup", callback=self.removeZoomRegion)
        self.renderZoomRegion(nZoom, spec)

        if nZoom == 2:
            dpg.configure_item("resetMesh", show=True)
        dpg.configure_item("sparsePopup", show=False)
        dpg.configure_item("meshZoomType", enabled=False)
        self.renderToggleLabels()
        self.updateMesh()
        dpg.configure_item("zoomRegionName", default_value=strings.t("mesh.default_zoom_region_name", index=nZoom + 1))


    def removeZoomRegion(self, sender, app_data=None):
        nZoom = len(self.sparseMeshHandler.ranges)
        nRegion = int(sender[10:])
        self.removeGrid()
        self.sparseMeshHandler.ranges.pop(nRegion)
        self.zoomRegionSpecs.pop(nRegion - 1)

        if nZoom < 4:
            dpg.configure_item("resetMesh", show=False)
        if nZoom == 2:
            self.sparseMeshHandler = None
            dpg.configure_item("meshZoomType", enabled=True)
        else:
            for i in range(nRegion, nZoom - 1):
                self.renderZoomRegion(i, self.zoomRegionSpecs[i - 1], range_data=self.sparseMeshHandler.ranges[i])
        dpg.delete_item("separatorZoomStart" + str(nZoom - 1))
        dpg.delete_item("zoomTxt" + str(nZoom - 1))
        dpg.delete_item("listBoxZoom" + str(nZoom - 1))
        dpg.delete_item("xminZoom" + str(nZoom - 1))
        dpg.delete_item("yminZoom" + str(nZoom - 1))
        dpg.delete_item("xmaxZoom" + str(nZoom - 1))
        dpg.delete_item("ymaxZoom" + str(nZoom - 1))
        dpg.delete_item("removeZoom" + str(nZoom - 1))
        dpg.delete_item("plotRec" +  str(nZoom - 1))
        self.renderToggleLabels()
        self.updateMesh()

    def updateMesh(self, sender=None, app_data=None):
        tempScopeList = []
        for i in self.subcontours.getScopes()[:-1]:
            tempScopeList.append([self.currentX[i[0]], self.currentY[i[0]], self.currentX[i[1]], self.currentY[i[1]]])


        dx = dpg.get_value("dx")
        dy = dpg.get_value("dy")
        xmin = dpg.get_value("xi")
        ymin = dpg.get_value("yi")
        self.removeGrid()

        if self.sparseMeshHandler == None:
            self.currentX, self.currentY = Mesh.getMesh(self.originalX, self.originalY, xmin, ymin, dx, dy)
            nx = self.currentX[0]
            ny = self.currentY[0]
            xmin = self.currentX[1]
            ymin = self.currentY[1]
            dx = self.currentX[3]
            dy = self.currentY[3]

            self.currentX = self.currentX[4:]
            self.currentY = self.currentY[4:]
            self.currentMeshInfo.update({"nx": nx, "ny": ny, "xmin": xmin, "ymin": ymin, "dx": dx, "dy": dy})
            self.renderMeshMetadata()

            for i in range(len(tempScopeList)):
                j = tempScopeList[i]
                p1 = Mesh.getNode(j[0], j[1], xmin, ymin, dx, dy)
                p2 = Mesh.getNode(j[2], j[3], xmin, ymin, dx, dy)
                tempScopeList[i] = [p1[0], p1[1], p2[0], p2[1]]

            self.plotGrid()
        else:
            self.sparseMeshHandler.updateRanges(dx, dy, xmin, ymin)

            if self.toggleZoomFlag == True:
                self.currentX, self.currentY = self.sparseMeshHandler.get_sparse_mesh(self.originalX, self.originalY)
                nx = self.sparseMeshHandler.ranges[0]["nx"]
                ny = self.sparseMeshHandler.ranges[0]["ny"]
                dpg.configure_item("nodeNumber", show=True)

                for i in range(len(tempScopeList)):
                    j = tempScopeList[i]
                    p1 = self.sparseMeshHandler.getNode(j[0], j[2])
                    p2 = self.sparseMeshHandler.getNode(j[2], j[3])
                    tempScopeList[i] = [p1[0], p1[1], p2[0], p2[1]]
            else:
                self.currentX, self.currentY = self.sparseMeshHandler.get_adaptive_mesh(self.originalX, self.originalY)
                nx = len(self.sparseMeshHandler.dx)
                ny = len(self.sparseMeshHandler.dy)
                
                for i in range(len(tempScopeList)):
                    j = tempScopeList[i]
                    p1 = self.sparseMeshHandler.getXNode(j[0])
                    p2 = self.sparseMeshHandler.getYNode(j[1])
                    p3 = self.sparseMeshHandler.getXNode(j[2])
                    p4 = self.sparseMeshHandler.getYNode(j[3])
                    tempScopeList[i] = [p1, p2, p3, p4]
            
            self.currentMeshInfo.update({"nx": nx, "ny": ny, "xmin": xmin, "ymin": ymin, "dx": dx, "dy": dy})
            self.renderMeshMetadata()
            self.plotGrid()
            for i in range(1,len(self.sparseMeshHandler.ranges)):
                if dpg.does_item_exist("plotRec" +  str(i)):
                    dpg.delete_item("plotRec" +  str(i))
                r = self.sparseMeshHandler.ranges[i]
                self.renderZoomRegion(i, self.zoomRegionSpecs[i - 1], range_data=r)
                if dpg.does_item_exist("plotRec" +  str(i)):
                    dpg.delete_item("plotRec" +  str(i))
                dpg.add_line_series([r['xi'],r['xi'],r['xf'],r['xf'],r['xi']], [r['yi'],r['yf'],r['yf'],r['yi'],r['yi']], tag="plotRec" +  str(i), label=self.zoomRegionSpecs[i - 1]["name"], parent="y_axis")

            aux = self.sparseMeshHandler.ranges[0]
            xmin = aux["xi"]
            ymin = aux["yi"]
            dx = aux["dx"]
            dy = aux["dy"]

        dpg.configure_item("dx", default_value = dx)
        dpg.configure_item("dy", default_value = dy)
        dpg.configure_item("xi", default_value = xmin)
        dpg.configure_item("yi", default_value = ymin)

        area = Mesh.get_area(self.currentX, self.currentY)
        self.currentAreaValue = area
        originalArea = self.originalAreaValue
        dif = abs(originalArea - area)
        self.differenceValue = dif
        self.differencePercent = abs(100*dif/originalArea)
        self.contourNodeCount = len(self.currentX)
        self.renderAreaStats()

        if dpg.does_item_exist("meshPlot"):
            dpg.delete_item("meshPlot")
        dpg.add_line_series(self.currentX, self.currentY, label=strings.t("mesh.current_mesh"), tag="meshPlot", parent='y_axis')
        dpg.fit_axis_data("x_axis")
        dpg.fit_axis_data("y_axis")

        dpg.configure_item("dxVector", x=[0, dpg.get_value('dx')])
        dpg.configure_item("dyVector", y=[0, dpg.get_value('dy')])

        self.subcontours = ScopeList(0, len(self.currentX))
        self.fullScope = [0, len(self.currentX)-1]
        self.fullScopeSize = self.fullScope[1] - self.fullScope[0]
        dpg.set_value("subcontoursCount", 1)
        self.createSubcontour()
        #print(self.subcontours.getScopes())
        
        for j in tempScopeList:
            a = Mesh.getIndex(self.currentX, self.currentY, j[0], j[1])
            b = Mesh.getIndex(self.currentX, self.currentY, j[2], j[3])
            self.subcontours.createScope(a,b)
        #print(self.subcontours.getScopes())

    def plotGrid(self, sender=None, app_data=None):
        if self.toggleGridFlag:
            dpg.configure_item("current_nodes_number", show=True)
            nInternalNodes = self.drawGrid()
            self.internalNodeCount = nInternalNodes
            self.renderAreaStats()
        else:
            dpg.configure_item("current_nodes_number", show=False)

    def drawGrid(self, sender=None, app_data=None):
        dpg.configure_item('plotGrid', enabled=False)
        nInternalNodes = 0       
        meshTypeFlag = 0
        if self.sparseMeshHandler != None:
            if self.toggleZoomFlag:
                meshTypeFlag = 1
            else:
                meshTypeFlag = 2

        if meshTypeFlag == 2:
            dx = self.sparseMeshHandler.dx
            dy = self.sparseMeshHandler.dy
        else:
            dx = dpg.get_value("dx")
            dy = dpg.get_value("dy")
        xmin = dpg.get_value("xi")
        ymin = dpg.get_value("yi")
        nx = int(self.currentMeshInfo["nx"])
        ny = int(self.currentMeshInfo["ny"])


        for i in range(ny):
            flag = True
            xGrid = []
            yGrid = []
            for j in range(nx):
                if meshTypeFlag == 2:
                    auxX = dx[j]
                    auxY = dy[i]
                else:
                    auxX = xmin + j * dx
                    auxY = ymin + i * dy

                if Mesh.insidePolygon(self.currentX, self.currentY, auxX, auxY):
                    if flag:
                        flag = False
                        xGrid.append(auxX)
                        yGrid.append(auxY)
                        xGrid.append(auxX)
                        yGrid.append(auxY)
                    else:
                        xGrid[-1] = auxX
                        yGrid[-1] = auxY
                    nInternalNodes += 1
                else:
                    flag = True
            tam = len(xGrid)
            count = 0
            while count < tam:
                dpg.add_line_series(xGrid[count:count + 2], yGrid[count:count + 2], tag="meshGridPlotY0/" + str(i) + "/" + str(count), parent='y_axis')
                dpg.bind_item_theme("meshGridPlotY0/" + str(i) + "/"  + str(count), "grid_plot_theme")
                count += 2
            if count > self.countGrid:
                self.countGrid = count 

        for j in range(nx):
            flag = True
            xGrid = []
            yGrid = []
            for i in range(ny):
                if meshTypeFlag == 2:
                    auxX = dx[j]
                    auxY = dy[i]
                else:
                    auxX = xmin + j * dx
                    auxY = ymin + i * dy

                if Mesh.insidePolygon(self.currentX, self.currentY, auxX, auxY):
                    if flag:
                        flag = False
                        xGrid.append(auxX)
                        yGrid.append(auxY)
                        xGrid.append(auxX)
                        yGrid.append(auxY)
                    else:
                        xGrid[-1] = auxX
                        yGrid[-1] = auxY
                else:
                    flag = True

            tam = len(xGrid)
            count = 0
            while count < tam:
                dpg.add_line_series(xGrid[count:count + 2], yGrid[count:count + 2], tag="meshGridPlotX0/" + str(j) + "/" + str(count), parent='y_axis')
                dpg.bind_item_theme("meshGridPlotX0/" + str(j) + "/"  + str(count), "grid_plot_theme")
                count += 2
            if count > self.countGrid:
                self.countGrid = count 
        
        if meshTypeFlag == 1:
            nAux = 0
            for z in range(1, len(self.sparseMeshHandler.ranges)):
                r = self.sparseMeshHandler.ranges[z]
                for i in range(r["ny"]):
                    flag = True
                    xGrid = []
                    yGrid = []
                    for j in range(r["nx"]):
                        auxX = r["xi"] + j * r["dx"]
                        auxY = r["yi"] + i * r["dy"]
                        if Mesh.insidePolygon(self.currentX, self.currentY, auxX, auxY):
                            if flag:
                                flag = False
                                xGrid.append(auxX)
                                yGrid.append(auxY)
                                xGrid.append(auxX)
                                yGrid.append(auxY)
                            else:
                                xGrid[-1] = auxX
                                yGrid[-1] = auxY
                            nAux += 1
                        else:
                            flag = True
                    tam = len(xGrid)
                    count = 0
                    while count < tam:
                        dpg.add_line_series(xGrid[count:count + 2], yGrid[count:count + 2], tag="meshGridPlotY" + str(z) + "/" + str(i) + "/" + str(count), parent='y_axis')
                        dpg.bind_item_theme("meshGridPlotY" + str(z) + "/" + str(i) + "/" + str(count), "grid_plot_theme")
                        count += 2
                    if count > self.countGrid:
                        self.countGrid = count 

                for j in range(r["nx"]):
                    flag = True
                    xGrid = []
                    yGrid = []
                    for i in range(r["ny"]):
                        auxX = r["xi"] + j * r["dx"]
                        auxY = r["yi"] + i * r["dy"]
                        if Mesh.insidePolygon(self.currentX, self.currentY, auxX, auxY):
                            if flag:
                                flag = False
                                xGrid.append(auxX)
                                yGrid.append(auxY)
                                xGrid.append(auxX)
                                yGrid.append(auxY)
                            else:
                                xGrid[-1] = auxX
                                yGrid[-1] = auxY
                        else:
                            flag = True
                    tam = len(xGrid)
                    count = 0
                    while count < tam:
                        dpg.add_line_series(xGrid[count:count + 2], yGrid[count:count + 2], tag="meshGridPlotX" + str(z) + "/" + str(j) + "/" + str(count), parent='y_axis')
                        dpg.bind_item_theme("meshGridPlotX" + str(z) + "/" + str(j) + "/" + str(count), "grid_plot_theme")
                        count += 2
                    if count > self.countGrid:
                        self.countGrid = count 
                
                #nAux -= (1 + (r["xf"] - r["xi"])//dx) * (1 + (r["yf"] - r["yi"])//dy)    
            nInternalNodes += nAux - nAux//4
        dpg.configure_item('plotGrid', enabled=True)
        return nInternalNodes

    def removeGrid(self, sender=None, app_data=None):
        if self.sparseMeshHandler == None or not self.toggleZoomFlag:
            n = 1
            nx = [int(self.currentMeshInfo["nx"])]
            ny = [int(self.currentMeshInfo["ny"])]
        else:
            aux = self.sparseMeshHandler.ranges
            n = len(aux)
            nx = []
            ny = []
            for r in aux:
                nx.append(r["nx"])
                ny.append(r["ny"])
        for k in range(0,self.countGrid,2):
            for z in range(n):
                for i in range(ny[z]):
                        dpg.delete_item("meshGridPlotY" + str(z) + "/" + str(i) + "/" + str(k))
                for j in range(nx[z]):
                        dpg.delete_item("meshGridPlotX" + str(z) + "/" + str(j) + "/" + str(k))
        self.countGrid = 0

    def toggleGrid(self, sender=None, app_data=None):
        self.toggleGridFlag = not self.toggleGridFlag
        self.renderToggleLabels()
        if self.toggleGridFlag:
            self.updateMesh()
        else:
            self.removeGrid()

    def resetMesh(self, sender=None, app_data=None):
        for i in range(1,len(self.sparseMeshHandler.ranges)):
            dpg.delete_item("separatorZoomStart" + str(i))
            dpg.delete_item("zoomTxt" + str(i))
            dpg.delete_item("listBoxZoom" + str(i))
            dpg.delete_item("xminZoom" + str(i))
            dpg.delete_item("yminZoom" + str(i))
            dpg.delete_item("xmaxZoom" + str(i))
            dpg.delete_item("ymaxZoom" + str(i))
            dpg.delete_item("removeZoom" + str(i))
            dpg.delete_item("plotRec" +  str(i))

        dpg.configure_item("meshZoomType", enabled=True)
        dpg.configure_item("resetMesh", show=False)
        self.sparseMeshHandler = None
        self.zoomRegionSpecs = []
        self.renderToggleLabels()
        self.updateMesh()

    def openMeshDirectorySelector(self, sender=None, app_data=None):
        if dpg.get_value('inputMeshNameText') != '':
            dpg.configure_item('meshDirectorySelectorFileDialog', show=True)

    def selectMeshFileFolder(self, sender=None, app_data=None):

        self.exportFilePath = app_data['file_path_name']

        self.exportFileName = dpg.get_value('inputMeshNameText') + '.txt'
        self.renderExportState()

        pass

    def exportMesh(self, sender=None, app_data=None):
        if self.exportFilePath is None:
            dpg.configure_item("exportMeshError", show=True)
            return

        dpg.configure_item("exportMeshError", show=False)
        filePath = os.path.join(self.exportFilePath, self.exportFileName)
        if self.sparseMeshHandler != None:
            if self.toggleZoomFlag:
                SparseMesh.export_coords_mesh(filePath, self.currentX, self.currentY, self.toggleOrderingFlag)
                filePathRanges = filePath[:-4] + "_ranges.txt"
                self.sparseMeshHandler.export_ranges(filePathRanges)
            else:
                SparseMesh.export_coords_mesh(filePath, self.currentX, self.currentY, self.toggleOrderingFlag)
                filePathDx = filePath[:-4] + "_dx.txt"
                filePathDy = filePath[:-4] + "_dy.txt"
                self.sparseMeshHandler.export_node_size_mesh(filePathDx, filePathDy)
        else:
            nx = int(self.currentMeshInfo["nx"])
            ny = int(self.currentMeshInfo["ny"])
            xmin = min(self.currentX)
            ymin = min(self.currentY)
            xmax = max(self.currentX)
            ymax = max(self.currentY)
            dx = (xmax - xmin)/(nx - 1)
            dy = (ymax - ymin)/(ny - 1)
            Mesh.export_coords_mesh(filePath, self.currentX, self.currentY, nx, ny, xmin, ymin, xmax, ymax, dx, dy, self.toggleOrderingFlag)
        self.exportFilePath = None
        self.exportFileName = None
        dpg.configure_item("exportMeshFile", show=False)

    def exportContourOnMesh(self, xarray, yarray, path):
        if self.sparseMeshHandler == None:
            dx = dpg.get_value("dx")
            dy = dpg.get_value("dy")
            xmin = dpg.get_value("xi")
            ymin = dpg.get_value("yi")
            xarray, yarray = Mesh.getMesh(xarray, yarray, xmin, ymin, dx, dy)
            xmax = max(xarray)
            ymax = max(yarray)
            nx = (xmax - xmin)// dx + 1
            ny = (ymax - ymin)// dy + 1
            Mesh.export_coords_mesh(path, self.currentX, self.currentY, nx, ny, xmin, ymin, xmax, ymax, dx, dy, self.toggleOrderingFlag)
        else:
            if self.toggleZoomFlag == True:
                xarray, yarray = self.sparseMeshHandler.get_sparse_mesh(xarray, yarray)
            else:
                xarray, yarray = self.sparseMeshHandler.get_adaptive_mesh(xarray, yarray)
            self.sparseMeshHandler.export_coords_mesh(path, self.currentX, self.currentY, self.toggleOrderingFlag)
