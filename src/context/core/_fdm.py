from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from shapely.geometry import LineString, Point, Polygon


@dataclass(slots=True)
class BoundaryRegion:
    region_id: int
    lower: int
    upper: int
    line: LineString


@dataclass(slots=True)
class DiscreteDomain:
    nx: int
    ny: int
    xmin: float
    ymin: float
    dx: float
    dy: float
    x_coords: np.ndarray
    y_coords: np.ndarray
    inside_mask: np.ndarray
    boundary_mask: np.ndarray
    internal_mask: np.ndarray
    region_ids: np.ndarray
    boundary_counts: dict[int, int]
    regions: list[BoundaryRegion]

    @property
    def internal_count(self) -> int:
        return int(np.count_nonzero(self.internal_mask))

    @property
    def boundary_count(self) -> int:
        return int(np.count_nonzero(self.boundary_mask))

    @property
    def domain_count(self) -> int:
        return int(np.count_nonzero(self.inside_mask))


@dataclass(slots=True)
class SolveResult:
    values: np.ndarray
    system_size: int
    residual: float
    min_value: float
    max_value: float
    mean_value: float


def _normalize_ranges(subcontours_ranges: list[list[int]] | None, point_count: int) -> list[tuple[int, int]]:
    if point_count < 2:
        raise ValueError("Contour must contain at least two points.")
    if not subcontours_ranges:
        return [(0, point_count - 1)]

    normalized: list[tuple[int, int]] = []
    last_index = point_count - 1
    for lower, upper in subcontours_ranges:
        lower = max(0, min(int(lower), last_index))
        upper = max(0, min(int(upper), last_index))
        if upper < lower:
            lower, upper = upper, lower
        normalized.append((lower, upper))
    return normalized or [(0, point_count - 1)]


def _build_regions(
    contour_x: list[float],
    contour_y: list[float],
    subcontours_ranges: list[list[int]] | None,
) -> list[BoundaryRegion]:
    point_count = len(contour_x)
    ranges = _normalize_ranges(subcontours_ranges, point_count)
    regions: list[BoundaryRegion] = []

    for region_id, (lower, upper) in enumerate(ranges):
        points = [(float(contour_x[index]), float(contour_y[index])) for index in range(lower, upper + 1)]
        if len(points) == 1:
            points.append(points[0])
        regions.append(
            BoundaryRegion(
                region_id=region_id,
                lower=lower,
                upper=upper,
                line=LineString(points),
            )
        )
    return regions


def build_uniform_domain(
    contour_x: list[float],
    contour_y: list[float],
    mesh_info: dict[str, float | int | None],
    subcontours_ranges: list[list[int]] | None = None,
) -> DiscreteDomain:
    required = ("nx", "ny", "xmin", "ymin", "dx", "dy")
    for key in required:
        if mesh_info.get(key) is None:
            raise ValueError("Mesh metadata is incomplete.")

    if len(contour_x) != len(contour_y) or len(contour_x) < 4:
        raise ValueError("Contour must be closed and contain at least four points.")

    polygon = Polygon(list(zip(contour_x, contour_y)))
    if not polygon.is_valid:
        polygon = polygon.buffer(0)
    if polygon.is_empty:
        raise ValueError("Contour does not define a valid polygon.")

    nx = int(mesh_info["nx"])
    ny = int(mesh_info["ny"])
    xmin = float(mesh_info["xmin"])
    ymin = float(mesh_info["ymin"])
    dx = float(mesh_info["dx"])
    dy = float(mesh_info["dy"])

    if nx < 2 or ny < 2 or dx <= 0 or dy <= 0:
        raise ValueError("Mesh must be a positive uniform grid.")

    x_coords = xmin + np.arange(nx, dtype=float) * dx
    y_coords = ymin + np.arange(ny, dtype=float) * dy
    inside_mask = np.zeros((ny, nx), dtype=bool)

    for row, y_value in enumerate(y_coords):
        for col, x_value in enumerate(x_coords):
            inside_mask[row, col] = polygon.covers(Point(float(x_value), float(y_value)))

    boundary_mask = np.zeros_like(inside_mask)
    for row in range(ny):
        for col in range(nx):
            if not inside_mask[row, col]:
                continue
            for dcol, drow in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                next_col = col + dcol
                next_row = row + drow
                if not (0 <= next_col < nx and 0 <= next_row < ny) or not inside_mask[next_row, next_col]:
                    boundary_mask[row, col] = True
                    break

    internal_mask = inside_mask & ~boundary_mask
    regions = _build_regions(contour_x, contour_y, subcontours_ranges)
    region_ids = np.full((ny, nx), -1, dtype=int)
    boundary_counts = {region.region_id: 0 for region in regions}

    for row, col in np.argwhere(boundary_mask):
        point = Point(float(x_coords[col]), float(y_coords[row]))
        closest_region = min(regions, key=lambda region: region.line.distance(point))
        region_ids[row, col] = closest_region.region_id
        boundary_counts[closest_region.region_id] += 1

    return DiscreteDomain(
        nx=nx,
        ny=ny,
        xmin=xmin,
        ymin=ymin,
        dx=dx,
        dy=dy,
        x_coords=x_coords,
        y_coords=y_coords,
        inside_mask=inside_mask,
        boundary_mask=boundary_mask,
        internal_mask=internal_mask,
        region_ids=region_ids,
        boundary_counts=boundary_counts,
        regions=regions,
    )


def solve_dirichlet_problem(
    domain: DiscreteDomain,
    boundary_values: dict[int, float],
    *,
    problem_key: str = "laplace",
    source_term: float = 0.0,
) -> SolveResult:
    for region in domain.regions:
        if region.region_id not in boundary_values:
            raise ValueError("All boundary regions must have an assigned value.")

    if problem_key not in {"laplace", "poisson"}:
        raise ValueError("Unsupported problem type.")

    rhs_source = 0.0 if problem_key == "laplace" else float(source_term)
    values = np.full((domain.ny, domain.nx), np.nan, dtype=float)

    for row, col in np.argwhere(domain.boundary_mask):
        region_id = int(domain.region_ids[row, col])
        values[row, col] = float(boundary_values[region_id])

    system_size = domain.internal_count
    if system_size == 0:
        domain_values = values[domain.inside_mask]
        return SolveResult(
            values=values,
            system_size=0,
            residual=0.0,
            min_value=float(np.nanmin(domain_values)),
            max_value=float(np.nanmax(domain_values)),
            mean_value=float(np.nanmean(domain_values)),
        )

    equation_index = np.full((domain.ny, domain.nx), -1, dtype=int)
    internal_positions = np.argwhere(domain.internal_mask)
    for index, (row, col) in enumerate(internal_positions):
        equation_index[row, col] = index

    matrix = np.zeros((system_size, system_size), dtype=float)
    vector = np.zeros(system_size, dtype=float)
    coeff_x = 1.0 / (domain.dx * domain.dx)
    coeff_y = 1.0 / (domain.dy * domain.dy)
    diagonal = 2.0 * coeff_x + 2.0 * coeff_y

    for row, col in internal_positions:
        index = equation_index[row, col]
        matrix[index, index] = diagonal
        vector[index] = rhs_source

        for next_col, next_row, coeff in (
            (col - 1, row, coeff_x),
            (col + 1, row, coeff_x),
            (col, row - 1, coeff_y),
            (col, row + 1, coeff_y),
        ):
            if domain.internal_mask[next_row, next_col]:
                matrix[index, equation_index[next_row, next_col]] -= coeff
                continue
            if domain.boundary_mask[next_row, next_col]:
                region_id = int(domain.region_ids[next_row, next_col])
                vector[index] += coeff * float(boundary_values[region_id])
                continue
            raise ValueError("Discrete domain contains an unsupported boundary configuration.")

    solution = np.linalg.solve(matrix, vector)
    values[domain.internal_mask] = solution
    residual = float(np.max(np.abs(matrix @ solution - vector)))
    domain_values = values[domain.inside_mask]

    return SolveResult(
        values=values,
        system_size=system_size,
        residual=residual,
        min_value=float(np.nanmin(domain_values)),
        max_value=float(np.nanmax(domain_values)),
        mean_value=float(np.nanmean(domain_values)),
    )
