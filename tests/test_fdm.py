from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "context" / "core"))

from _fdm import build_uniform_domain, solve_dirichlet_problem


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


if __name__ == "__main__":
    unittest.main()
