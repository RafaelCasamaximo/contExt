from __future__ import annotations

import sys
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

import dearpygui.dearpygui as dpg

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from context.core._mesh import Mesh
from context.core._gridPlot import GridPlotCancelled, GridSpec, build_grid_plot
from context.core._meshGeneration import MeshGeneration
from context.core._numeric import grid_coordinate
from context.core._sparseMesh import SparseMesh
from context.core._fdm import build_sparse_composite_domain, build_structured_domain, build_uniform_domain
from context.ui._meshTab import showMeshGeneration


def has_diagonal_segment(x_values, y_values) -> bool:
    return any(
        x_values[index] != x_values[index - 1] and y_values[index] != y_values[index - 1]
        for index in range(1, len(x_values))
    )


class MeshGenerationModeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contour_x = [0.0, 2.0, 0.0, 0.0]
        self.contour_y = [0.0, 2.0, 2.0, 0.0]

    def test_uniform_mesh_keeps_diagonal_as_default(self) -> None:
        mesh_x, mesh_y = Mesh.getMesh(self.contour_x, self.contour_y, 0.0, 0.0, 1.0, 1.0)
        self.assertTrue(has_diagonal_segment(mesh_x[4:], mesh_y[4:]))

    def test_uniform_mesh_right_angle_mode_removes_diagonals(self) -> None:
        mesh_x, mesh_y = Mesh.getMesh(
            self.contour_x,
            self.contour_y,
            0.0,
            0.0,
            1.0,
            1.0,
            allowDiagonal=False,
        )
        self.assertFalse(has_diagonal_segment(mesh_x[4:], mesh_y[4:]))
        self.assertEqual((mesh_x[4], mesh_y[4]), (mesh_x[-1], mesh_y[-1]))

    def test_sparse_and_adaptive_meshes_honor_right_angle_mode(self) -> None:
        sparse_mesh = SparseMesh()
        self.assertTrue(sparse_mesh.addRange(0.0, 0.0, 2.0, 2.0, 1.0, 1.0))

        sparse_x, sparse_y = sparse_mesh.get_sparse_mesh(
            self.contour_x,
            self.contour_y,
            allowDiagonal=False,
        )
        adaptive_x, adaptive_y = sparse_mesh.get_adaptive_mesh(
            self.contour_x,
            self.contour_y,
            allowDiagonal=False,
        )

        self.assertFalse(has_diagonal_segment(sparse_x, sparse_y))
        self.assertFalse(has_diagonal_segment(adaptive_x, adaptive_y))

    def test_nested_subdivision_preserves_every_original_contour_point(self) -> None:
        original_x = [0.0, 1.0, 2.0, 2.0, 0.0]
        original_y = [0.0, 1.0, 1.0, 0.0, 0.0]

        refined_x, refined_y, index_map = Mesh.subdividePath(original_x, original_y, levels=2)

        self.assertEqual(len(index_map), len(original_x))
        for old_index, new_index in enumerate(index_map):
            self.assertEqual(refined_x[new_index], original_x[old_index])
            self.assertEqual(refined_y[new_index], original_y[old_index])

    def test_uniform_subdivision_keeps_the_coarse_grid_nested(self) -> None:
        mesh_info = {
            "nx": 4,
            "ny": 3,
            "xmin": -0.1,
            "ymin": 0.2,
            "dx": 0.1,
            "dy": 0.25,
        }
        refined = Mesh.subdivideUniformMeshInfo(mesh_info, levels=3)
        factor = 2 ** 3

        self.assertEqual(refined["nx"], (mesh_info["nx"] - 1) * factor + 1)
        self.assertEqual(refined["ny"], (mesh_info["ny"] - 1) * factor + 1)

        refined_x = {
            grid_coordinate(refined["xmin"], refined["dx"], index)
            for index in range(refined["nx"])
        }
        refined_y = {
            grid_coordinate(refined["ymin"], refined["dy"], index)
            for index in range(refined["ny"])
        }
        coarse_x = {
            grid_coordinate(mesh_info["xmin"], mesh_info["dx"], index)
            for index in range(mesh_info["nx"])
        }
        coarse_y = {
            grid_coordinate(mesh_info["ymin"], mesh_info["dy"], index)
            for index in range(mesh_info["ny"])
        }

        self.assertTrue(coarse_x.issubset(refined_x))
        self.assertTrue(coarse_y.issubset(refined_y))

    def test_uniform_domain_point_set_is_a_subset_of_refined_domain(self) -> None:
        contour_x = [0.0, 1.0, 1.0, 0.0, 0.0]
        contour_y = [0.0, 0.0, 1.0, 1.0, 0.0]
        mesh_info = {
            "nx": 3,
            "ny": 3,
            "xmin": 0.0,
            "ymin": 0.0,
            "dx": 0.5,
            "dy": 0.5,
        }
        refined_x, refined_y, _ = Mesh.subdividePath(contour_x, contour_y, levels=2)
        refined_info = Mesh.subdivideUniformMeshInfo(mesh_info, levels=2)
        coarse_domain = build_uniform_domain(contour_x, contour_y, mesh_info, [[0, 4]])
        refined_domain = build_uniform_domain(refined_x, refined_y, refined_info, [[0, len(refined_x) - 1]])

        coarse_points = {
            (float(coarse_domain.x_coords[col]), float(coarse_domain.y_coords[row]))
            for row, col in zip(*coarse_domain.inside_mask.nonzero())
        }
        refined_points = {
            (float(refined_domain.x_coords[col]), float(refined_domain.y_coords[row]))
            for row, col in zip(*refined_domain.inside_mask.nonzero())
        }

        self.assertTrue(coarse_points.issubset(refined_points))


class MeshGridPlotTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contour_x = [0.0, 1.0, 1.0, 0.0, 0.0]
        self.contour_y = [0.0, 0.0, 1.0, 1.0, 0.0]

    def test_vectorized_grid_plot_includes_boundary_and_aggregates_lines(self) -> None:
        data = build_grid_plot(
            self.contour_x,
            self.contour_y,
            [GridSpec.uniform(0.0, 0.0, 0.25, 0.25, 5, 5)],
        )

        self.assertEqual(data.node_count, 25)
        self.assertEqual(len(data.horizontal_x), 10)
        self.assertEqual(len(data.horizontal_y), 10)
        self.assertEqual(len(data.vertical_x), 10)
        self.assertEqual(len(data.vertical_y), 10)

    def test_sparse_grid_count_uses_exact_union_of_coincident_nodes(self) -> None:
        data = build_grid_plot(
            self.contour_x,
            self.contour_y,
            [
                GridSpec.uniform(0.0, 0.0, 0.5, 0.5, 3, 3),
                GridSpec.uniform(0.25, 0.25, 0.25, 0.25, 3, 3),
            ],
        )

        self.assertEqual(data.node_count, 17)

    def test_grid_plot_honors_cancellation_before_work_starts(self) -> None:
        cancel_event = threading.Event()
        cancel_event.set()

        with self.assertRaises(GridPlotCancelled):
            build_grid_plot(
                self.contour_x,
                self.contour_y,
                [GridSpec.uniform(0.0, 0.0, 0.25, 0.25, 5, 5)],
                cancel_event,
            )

    def test_mesh_generation_starts_grid_calculation_on_worker_thread(self) -> None:
        class CallbackStub:
            meshGeneration = MeshGeneration()

        dpg.create_context()
        try:
            with dpg.window():
                showMeshGeneration(CallbackStub())

            callback = CallbackStub.meshGeneration
            callback.currentX = list(self.contour_x)
            callback.currentY = list(self.contour_y)
            callback.currentMeshInfo = {
                "nx": 5,
                "ny": 5,
                "xmin": 0.0,
                "ymin": 0.0,
                "dx": 0.25,
                "dy": 0.25,
            }
            callback.toggleGridFlag = True

            with (
                patch("context.core._meshGeneration.threading.Thread") as worker_type,
                patch.object(dpg, "get_frame_count", return_value=10),
                patch.object(dpg, "set_frame_callback") as set_frame_callback,
            ):
                callback.plotGrid()

            worker_type.assert_called_once()
            worker_type.return_value.start.assert_called_once_with()
            set_frame_callback.assert_called_once()
        finally:
            dpg.destroy_context()

    def test_worker_result_is_rendered_as_only_two_segment_series(self) -> None:
        class CallbackStub:
            meshGeneration = MeshGeneration()

        dpg.create_context()
        try:
            with dpg.theme(tag="grid_plot_theme"):
                pass
            with dpg.window():
                showMeshGeneration(CallbackStub())

            callback = CallbackStub.meshGeneration
            callback.currentX = list(self.contour_x)
            callback.currentY = list(self.contour_y)
            callback.currentMeshInfo = {
                "nx": 5,
                "ny": 5,
                "xmin": 0.0,
                "ymin": 0.0,
                "dx": 0.25,
                "dy": 0.25,
            }
            callback.toggleGridFlag = True
            callback._scheduleGridPlotPoll = lambda: None

            callback.plotGrid()
            callback._gridPlotThread.join(timeout=2)
            callback._pollGridPlot()

            horizontal_tag = "meshGridPlotHorizontal"
            vertical_tag = "meshGridPlotVertical"
            self.assertTrue(dpg.does_item_exist(horizontal_tag))
            self.assertTrue(dpg.does_item_exist(vertical_tag))
            self.assertTrue(dpg.get_item_configuration(horizontal_tag)["segments"])
            self.assertTrue(dpg.get_item_configuration(vertical_tag)["segments"])
            self.assertEqual(callback.internalNodeCount, 25)
        finally:
            dpg.destroy_context()


class MeshSubdivisionTests(unittest.TestCase):
    def test_sparse_subdivision_keeps_old_axis_coordinates(self) -> None:
        sparse_mesh = SparseMesh()
        self.assertTrue(sparse_mesh.addRange(0.0, 0.0, 1.0, 1.0, 0.25, 0.25))
        self.assertTrue(sparse_mesh.addRange(0.25, 0.25, 0.75, 0.75, 2, 2))
        sparse_mesh.setIntervals()
        old_x = set(sparse_mesh.dx)
        old_y = set(sparse_mesh.dy)

        sparse_mesh.subdivide(levels=2)

        self.assertTrue(old_x.issubset(set(sparse_mesh.dx)))
        self.assertTrue(old_y.issubset(set(sparse_mesh.dy)))

    def test_sparse_domain_point_set_is_a_subset_of_refined_domain(self) -> None:
        contour_x = [0.0, 1.0, 1.0, 0.0, 0.0]
        contour_y = [0.0, 0.0, 1.0, 1.0, 0.0]
        sparse_mesh = SparseMesh()
        self.assertTrue(sparse_mesh.addRange(0.0, 0.0, 1.0, 1.0, 0.25, 0.25))
        self.assertTrue(sparse_mesh.addRange(0.25, 0.25, 0.75, 0.75, 2, 2))
        coarse_domain = build_sparse_composite_domain(contour_x, contour_y, sparse_mesh, [[0, 4]])

        refined_x, refined_y, _ = Mesh.subdividePath(contour_x, contour_y, levels=1)
        sparse_mesh.subdivide(levels=1)
        refined_domain = build_sparse_composite_domain(
            refined_x,
            refined_y,
            sparse_mesh,
            [[0, len(refined_x) - 1]],
        )

        coarse_points = {
            (float(coarse_domain.x_coords[col]), float(coarse_domain.y_coords[row]))
            for row, col in zip(*coarse_domain.inside_mask.nonzero())
        }
        refined_points = {
            (float(refined_domain.x_coords[col]), float(refined_domain.y_coords[row]))
            for row, col in zip(*refined_domain.inside_mask.nonzero())
        }

        self.assertTrue(coarse_points.issubset(refined_points))

    def test_adaptive_domain_point_set_is_a_subset_of_refined_domain(self) -> None:
        contour_x = [0.0, 1.0, 1.0, 0.0, 0.0]
        contour_y = [0.0, 0.0, 1.0, 1.0, 0.0]
        adaptive_mesh = SparseMesh()
        self.assertTrue(adaptive_mesh.addRange(0.0, 0.0, 1.0, 1.0, 0.25, 0.25))
        self.assertTrue(adaptive_mesh.addRange(0.25, 0.25, 0.75, 0.75, 2, 2))
        adaptive_mesh.setIntervals()
        coarse_domain = build_structured_domain(
            contour_x,
            contour_y,
            adaptive_mesh.dx,
            adaptive_mesh.dy,
            [[0, 4]],
            mesh_kind="adaptive",
        )

        refined_x, refined_y, _ = Mesh.subdividePath(contour_x, contour_y, levels=1)
        adaptive_mesh.subdivide(levels=1)
        refined_domain = build_structured_domain(
            refined_x,
            refined_y,
            adaptive_mesh.dx,
            adaptive_mesh.dy,
            [[0, len(refined_x) - 1]],
            mesh_kind="adaptive",
        )

        coarse_points = {
            (float(coarse_domain.x_coords[col]), float(coarse_domain.y_coords[row]))
            for row, col in zip(*coarse_domain.inside_mask.nonzero())
        }
        refined_points = {
            (float(refined_domain.x_coords[col]), float(refined_domain.y_coords[row]))
            for row, col in zip(*refined_domain.inside_mask.nonzero())
        }

        self.assertTrue(coarse_points.issubset(refined_points))


class ScientificPrecisionTests(unittest.TestCase):
    def test_decimal_grid_snap_does_not_move_exact_decimal_to_previous_node(self) -> None:
        self.assertEqual(Mesh.getNode(0.3, 0.6, 0.0, 0.0, 0.1, 0.2), [0.3, 0.6])

    def test_grid_coordinates_remove_binary_tails_without_accumulation(self) -> None:
        self.assertEqual(grid_coordinate(0.0, 0.1, 3), 0.3)
        self.assertEqual(grid_coordinate(0.0, 1.0 / 3.0, 3), 1.0)

    def test_reference_distance_is_divided_independently_by_axis(self) -> None:
        dx, dy = Mesh.spacingFromDistance(1.0, 10, 4)
        self.assertEqual(dx, 0.1)
        self.assertEqual(dy, 0.25)

    def test_reference_distance_rejects_invalid_divisions(self) -> None:
        with self.assertRaises(ValueError):
            Mesh.spacingFromDistance(1.0, 0, 1)

    def test_mesh_inputs_keep_double_precision(self) -> None:
        class CallbackStub:
            meshGeneration = MeshGeneration()

        dpg.create_context()
        try:
            with dpg.window():
                showMeshGeneration(CallbackStub())

            callback = CallbackStub.meshGeneration
            callback.toggleSpacingMode()
            dpg.set_value("meshReferenceDistance", 1.0)
            dpg.set_value("meshXDivisions", 10)
            dpg.set_value("meshYDivisions", 4)
            callback.updateDividedSpacing()

            self.assertEqual(dpg.get_value("dx"), 0.1)
            self.assertEqual(dpg.get_value("dy"), 0.25)
        finally:
            dpg.destroy_context()

    def test_mesh_generation_handler_subdivides_current_mesh_in_place(self) -> None:
        class CallbackStub:
            meshGeneration = MeshGeneration()

        dpg.create_context()
        try:
            with dpg.window():
                showMeshGeneration(CallbackStub())

            callback = CallbackStub.meshGeneration
            callback.currentX = [0.0, 1.0, 1.0, 0.0, 0.0]
            callback.currentY = [0.0, 0.0, 1.0, 1.0, 0.0]
            callback.originalAreaValue = 1.0
            callback.subcontoursRanges = [[0, 1], [2, 4]]
            callback.currentMeshInfo = {
                "nx": 3,
                "ny": 3,
                "xmin": 0.0,
                "ymin": 0.0,
                "dx": 0.5,
                "dy": 0.5,
            }
            callback.toggleSpacingMode()
            dpg.set_value("meshReferenceDistance", 1.0)
            dpg.set_value("meshXDivisions", 2)
            dpg.set_value("meshYDivisions", 2)
            callback.updateDividedSpacing()
            old_points = set(zip(callback.currentX, callback.currentY))
            dpg.set_value("meshSubdivisionLevels", 2)

            callback.subdivideMesh()

            self.assertTrue(old_points.issubset(set(zip(callback.currentX, callback.currentY))))
            self.assertEqual(callback.currentMeshInfo["nx"], 9)
            self.assertEqual(callback.currentMeshInfo["ny"], 9)
            self.assertEqual(callback.currentMeshInfo["dx"], 0.125)
            self.assertEqual(callback.currentMeshInfo["dy"], 0.125)
            self.assertEqual(callback.spacingMode, "divided_distance")
            self.assertEqual(dpg.get_value("meshXDivisions"), 8)
            self.assertEqual(dpg.get_value("meshYDivisions"), 8)
            self.assertEqual(callback.subcontoursRanges[0][0], 0)
            self.assertEqual(callback.subcontoursRanges[-1][1], len(callback.currentX) - 1)
        finally:
            dpg.destroy_context()


if __name__ == "__main__":
    unittest.main()
