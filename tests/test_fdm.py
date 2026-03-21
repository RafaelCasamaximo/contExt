from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from context.core._fdm import build_sparse_composite_domain, build_structured_domain, build_uniform_domain, solve_dirichlet_problem
from context.core._sparseMesh import SparseMesh


class FiniteDifferenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contour_x = [0.0, 1.0, 1.0, 0.0, 0.0]
        self.contour_y = [0.0, 0.0, 1.0, 1.0, 0.0]
        self.mesh_info = {
            "nx": 5,
            "ny": 5,
            "xmin": 0.0,
            "ymin": 0.0,
            "dx": 0.25,
            "dy": 0.25,
        }
        self.ranges = [[0, 1], [1, 2], [2, 3], [3, 4]]

    def test_build_uniform_domain_counts_nodes(self) -> None:
        domain = build_uniform_domain(self.contour_x, self.contour_y, self.mesh_info, self.ranges)
        self.assertEqual(domain.domain_count, 25)
        self.assertEqual(domain.boundary_count, 16)
        self.assertEqual(domain.internal_count, 9)
        self.assertEqual(sum(domain.boundary_counts.values()), 16)

    def test_constant_dirichlet_boundary_stays_constant(self) -> None:
        domain = build_uniform_domain(self.contour_x, self.contour_y, self.mesh_info, self.ranges)
        result = solve_dirichlet_problem(domain, {0: 1.0, 1: 1.0, 2: 1.0, 3: 1.0})
        values = result.values[domain.inside_mask]
        self.assertTrue(np.allclose(values, 1.0))
        self.assertEqual(result.system_size, 9)

    def test_opposite_dirichlet_sides_create_gradient(self) -> None:
        domain = build_uniform_domain(self.contour_x, self.contour_y, self.mesh_info, self.ranges)
        result = solve_dirichlet_problem(domain, {0: 0.0, 1: 1.0, 2: 1.0, 3: 0.0})
        center_value = result.values[2, 2]
        self.assertGreater(center_value, 0.4)
        self.assertLess(center_value, 0.6)

    def test_poisson_source_with_zero_boundary_is_positive_inside(self) -> None:
        domain = build_uniform_domain(self.contour_x, self.contour_y, self.mesh_info, self.ranges)
        result = solve_dirichlet_problem(
            domain,
            {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0},
            problem_key="poisson",
            source_term=1.0,
        )
        self.assertGreater(result.values[2, 2], 0.0)

    def test_adaptive_structured_domain_counts_nodes(self) -> None:
        x_coords = np.array([0.0, 0.2, 0.5, 0.7, 1.0], dtype=float)
        y_coords = np.array([0.0, 0.15, 0.55, 0.8, 1.0], dtype=float)
        domain = build_structured_domain(self.contour_x, self.contour_y, x_coords, y_coords, self.ranges, mesh_kind="adaptive")
        self.assertEqual(domain.domain_count, 25)
        self.assertEqual(domain.boundary_count, 16)
        self.assertEqual(domain.internal_count, 9)

    def test_adaptive_constant_dirichlet_stays_constant(self) -> None:
        x_coords = np.array([0.0, 0.2, 0.5, 0.7, 1.0], dtype=float)
        y_coords = np.array([0.0, 0.15, 0.55, 0.8, 1.0], dtype=float)
        domain = build_structured_domain(self.contour_x, self.contour_y, x_coords, y_coords, self.ranges, mesh_kind="adaptive")
        result = solve_dirichlet_problem(domain, {0: 2.5, 1: 2.5, 2: 2.5, 3: 2.5})
        values = result.values[domain.inside_mask]
        self.assertTrue(np.allclose(values, 2.5))

    def test_adaptive_poisson_source_with_zero_boundary_is_positive_inside(self) -> None:
        x_coords = np.array([0.0, 0.2, 0.5, 0.7, 1.0], dtype=float)
        y_coords = np.array([0.0, 0.15, 0.55, 0.8, 1.0], dtype=float)
        domain = build_structured_domain(self.contour_x, self.contour_y, x_coords, y_coords, self.ranges, mesh_kind="adaptive")
        result = solve_dirichlet_problem(
            domain,
            {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0},
            problem_key="poisson",
            source_term=1.0,
        )
        self.assertGreater(result.values[2, 2], 0.0)

    def test_sparse_constant_dirichlet_stays_constant(self) -> None:
        sparse_mesh = SparseMesh()
        self.assertTrue(sparse_mesh.addRange(0.0, 0.0, 1.0, 1.0, 0.25, 0.25))
        self.assertTrue(sparse_mesh.addRange(0.25, 0.25, 0.75, 0.75, 2, 2))
        sparse_domain = build_sparse_composite_domain(self.contour_x, self.contour_y, sparse_mesh, self.ranges)
        result = solve_dirichlet_problem(sparse_domain, {0: 1.0, 1: 1.0, 2: 1.0, 3: 1.0})
        values = result.values[sparse_domain.inside_mask]
        self.assertTrue(np.allclose(values, 1.0))

    def test_sparse_domain_refines_patch_with_extra_nodes(self) -> None:
        sparse_mesh = SparseMesh()
        self.assertTrue(sparse_mesh.addRange(0.0, 0.0, 1.0, 1.0, 0.25, 0.25))
        self.assertTrue(sparse_mesh.addRange(0.25, 0.25, 0.75, 0.75, 2, 2))
        sparse_domain = build_sparse_composite_domain(self.contour_x, self.contour_y, sparse_mesh, self.ranges)
        uniform_domain = build_uniform_domain(self.contour_x, self.contour_y, self.mesh_info, self.ranges)
        self.assertGreater(sparse_domain.domain_count, uniform_domain.domain_count)
        self.assertGreaterEqual(len(sparse_domain.patches), 1)


if __name__ == "__main__":
    unittest.main()
