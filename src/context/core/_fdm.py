from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.sparse import lil_matrix
from scipy.sparse.linalg import spsolve
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union


SPARSE_INTERFACE_TOLERANCE = 1.0e-6
SPARSE_MAX_ITERATIONS = 50


@dataclass(slots=True)
class BoundaryRegion:
    region_id: int
    lower: int
    upper: int
    line: LineString


@dataclass(slots=True)
class DomainNode:
    row: int
    col: int
    x: float
    y: float


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
    physical_boundary_mask: np.ndarray
    interface_boundary_mask: np.ndarray
    interface_ids: np.ndarray
    mesh_kind: str = "structured"

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
class PatchDomain:
    patch_id: int
    bounds: tuple[float, float, float, float]
    domain: DiscreteDomain
    coarse_interface_nodes: list[DomainNode]
    fine_interface_nodes: list[DomainNode]


@dataclass(slots=True)
class CompositeDomain:
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
    physical_boundary_mask: np.ndarray
    interface_boundary_mask: np.ndarray
    interface_ids: np.ndarray
    background_domain: DiscreteDomain
    coarse_domain: DiscreteDomain
    patches: list[PatchDomain]
    mesh_kind: str = "sparse"

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


def _coordinate_key(value: float) -> float:
    return round(float(value), 12)


def _minimum_spacing(coords: np.ndarray) -> float:
    if coords.size < 2:
        raise ValueError("Coordinate arrays must contain at least two points.")
    spacing = np.diff(coords)
    positive = spacing[spacing > 0.0]
    if positive.size == 0:
        raise ValueError("Coordinate arrays must be strictly increasing.")
    return float(np.min(positive))


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


def _build_polygon(contour_x: list[float], contour_y: list[float]) -> Polygon:
    if len(contour_x) != len(contour_y) or len(contour_x) < 4:
        raise ValueError("Contour must be closed and contain at least four points.")

    polygon = Polygon(list(zip(contour_x, contour_y)))
    if not polygon.is_valid:
        polygon = polygon.buffer(0)
    if polygon.is_empty:
        raise ValueError("Contour does not define a valid polygon.")
    return polygon


def _as_coordinate_array(values: list[float] | np.ndarray, *, name: str) -> np.ndarray:
    coords = np.asarray(values, dtype=float)
    if coords.ndim != 1 or coords.size < 2:
        raise ValueError(f"{name} must contain at least two coordinates.")
    if np.any(np.diff(coords) <= 0.0):
        raise ValueError(f"{name} must be strictly increasing.")
    return coords


def _point_on_rectangle_boundary(
    x_value: float,
    y_value: float,
    bounds: tuple[float, float, float, float],
    tolerance: float,
) -> bool:
    xi, yi, xf, yf = bounds
    on_vertical = (
        (abs(x_value - xi) <= tolerance or abs(x_value - xf) <= tolerance)
        and yi - tolerance <= y_value <= yf + tolerance
    )
    on_horizontal = (
        (abs(y_value - yi) <= tolerance or abs(y_value - yf) <= tolerance)
        and xi - tolerance <= x_value <= xf + tolerance
    )
    return on_vertical or on_horizontal


def _classify_rectangle_edge(
    x_value: float,
    y_value: float,
    bounds: tuple[float, float, float, float],
    tolerance: float,
) -> str:
    xi, yi, xf, yf = bounds
    if abs(x_value - xi) <= tolerance:
        return "west"
    if abs(x_value - xf) <= tolerance:
        return "east"
    if abs(y_value - yi) <= tolerance:
        return "south"
    if abs(y_value - yf) <= tolerance:
        return "north"
    raise ValueError("Point is not on the rectangle boundary.")


def _extract_domain_nodes(domain: DiscreteDomain, mask: np.ndarray) -> list[DomainNode]:
    nodes: list[DomainNode] = []
    for row, col in np.argwhere(mask):
        nodes.append(
            DomainNode(
                row=int(row),
                col=int(col),
                x=float(domain.x_coords[col]),
                y=float(domain.y_coords[row]),
            )
        )
    return nodes


def _build_domain_from_polygon(
    polygon: Polygon,
    x_coords: np.ndarray,
    y_coords: np.ndarray,
    regions: list[BoundaryRegion],
    *,
    interface_rectangles: list[tuple[int, tuple[float, float, float, float]]] | None = None,
    mesh_kind: str = "structured",
) -> DiscreteDomain:
    nx = int(x_coords.size)
    ny = int(y_coords.size)
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

    physical_boundary_mask = np.zeros_like(inside_mask)
    interface_boundary_mask = np.zeros_like(inside_mask)
    interface_ids = np.full((ny, nx), -1, dtype=int)
    region_ids = np.full((ny, nx), -1, dtype=int)
    boundary_counts = {region.region_id: 0 for region in regions}

    tolerance = max(_minimum_spacing(x_coords), _minimum_spacing(y_coords)) * 1.0e-9 + 1.0e-12

    for row, col in np.argwhere(boundary_mask):
        x_value = float(x_coords[col])
        y_value = float(y_coords[row])
        point = Point(x_value, y_value)
        closest_region = min(regions, key=lambda region: region.line.distance(point))
        is_physical = bool(closest_region.line.distance(point) <= tolerance)

        interface_id = -1
        if not is_physical and interface_rectangles:
            for patch_id, bounds in interface_rectangles:
                if _point_on_rectangle_boundary(x_value, y_value, bounds, tolerance):
                    interface_id = int(patch_id)
                    break

        if not is_physical and interface_id < 0:
            is_physical = True

        if is_physical:
            physical_boundary_mask[row, col] = True
            region_ids[row, col] = closest_region.region_id
            boundary_counts[closest_region.region_id] += 1
        else:
            interface_boundary_mask[row, col] = True
            interface_ids[row, col] = interface_id

    boundary_mask = physical_boundary_mask | interface_boundary_mask
    internal_mask = inside_mask & ~boundary_mask

    return DiscreteDomain(
        nx=nx,
        ny=ny,
        xmin=float(x_coords[0]),
        ymin=float(y_coords[0]),
        dx=_minimum_spacing(x_coords),
        dy=_minimum_spacing(y_coords),
        x_coords=x_coords,
        y_coords=y_coords,
        inside_mask=inside_mask,
        boundary_mask=boundary_mask,
        internal_mask=internal_mask,
        region_ids=region_ids,
        boundary_counts=boundary_counts,
        regions=regions,
        physical_boundary_mask=physical_boundary_mask,
        interface_boundary_mask=interface_boundary_mask,
        interface_ids=interface_ids,
        mesh_kind=mesh_kind,
    )


def build_structured_domain(
    contour_x: list[float],
    contour_y: list[float],
    x_coords: list[float] | np.ndarray,
    y_coords: list[float] | np.ndarray,
    subcontours_ranges: list[list[int]] | None = None,
    *,
    excluded_rectangles: list[tuple[int, tuple[float, float, float, float]]] | None = None,
    clip_bounds: tuple[float, float, float, float] | None = None,
    interface_rectangles: list[tuple[int, tuple[float, float, float, float]]] | None = None,
    mesh_kind: str = "structured",
) -> DiscreteDomain:
    x_array = _as_coordinate_array(x_coords, name="x_coords")
    y_array = _as_coordinate_array(y_coords, name="y_coords")
    polygon = _build_polygon(contour_x, contour_y)

    if clip_bounds is not None:
        polygon = polygon.intersection(box(*clip_bounds))
        if polygon.is_empty:
            raise ValueError("Contour and refinement patch do not overlap.")

    if excluded_rectangles:
        excluded = unary_union([box(*bounds) for _, bounds in excluded_rectangles])
        polygon = polygon.difference(excluded)
        if polygon.is_empty:
            raise ValueError("Contour is fully removed by sparse refinement regions.")

    regions = _build_regions(contour_x, contour_y, subcontours_ranges)
    return _build_domain_from_polygon(
        polygon,
        x_array,
        y_array,
        regions,
        interface_rectangles=interface_rectangles,
        mesh_kind=mesh_kind,
    )


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

    nx = int(mesh_info["nx"])
    ny = int(mesh_info["ny"])
    xmin = float(mesh_info["xmin"])
    ymin = float(mesh_info["ymin"])
    dx = float(mesh_info["dx"])
    dy = float(mesh_info["dy"])

    if nx < 2 or ny < 2 or dx <= 0.0 or dy <= 0.0:
        raise ValueError("Mesh must be a positive uniform grid.")

    x_coords = xmin + np.arange(nx, dtype=float) * dx
    y_coords = ymin + np.arange(ny, dtype=float) * dy
    return build_structured_domain(
        contour_x,
        contour_y,
        x_coords,
        y_coords,
        subcontours_ranges,
        mesh_kind="uniform",
    )


def build_sparse_composite_domain(
    contour_x: list[float],
    contour_y: list[float],
    sparse_mesh_handler,
    subcontours_ranges: list[list[int]] | None = None,
) -> CompositeDomain:
    if sparse_mesh_handler is None or len(getattr(sparse_mesh_handler, "ranges", [])) == 0:
        raise ValueError("Sparse mesh metadata is incomplete.")

    sparse_mesh_handler.setIntervals()
    global_x = _as_coordinate_array(sparse_mesh_handler.dx, name="x_coords")
    global_y = _as_coordinate_array(sparse_mesh_handler.dy, name="y_coords")
    regions = _build_regions(contour_x, contour_y, subcontours_ranges)

    base_range = sparse_mesh_handler.ranges[0]
    coarse_x = base_range["xi"] + np.arange(base_range["nx"], dtype=float) * float(base_range["dx"])
    coarse_y = base_range["yi"] + np.arange(base_range["ny"], dtype=float) * float(base_range["dy"])

    patch_bounds: list[tuple[int, tuple[float, float, float, float]]] = []
    for patch_id, patch_range in enumerate(sparse_mesh_handler.ranges[1:]):
        patch_bounds.append(
            (
                patch_id,
                (
                    float(patch_range["xi"]),
                    float(patch_range["yi"]),
                    float(patch_range["xf"]),
                    float(patch_range["yf"]),
                ),
            )
        )

    coarse_domain = build_structured_domain(
        contour_x,
        contour_y,
        coarse_x,
        coarse_y,
        subcontours_ranges,
        excluded_rectangles=patch_bounds,
        interface_rectangles=patch_bounds,
        mesh_kind="sparse_coarse",
    )
    background_domain = build_structured_domain(
        contour_x,
        contour_y,
        coarse_x,
        coarse_y,
        subcontours_ranges,
        mesh_kind="sparse_background",
    )

    patches: list[PatchDomain] = []
    for patch_id, bounds in patch_bounds:
        patch_range = sparse_mesh_handler.ranges[patch_id + 1]
        patch_x = patch_range["xi"] + np.arange(patch_range["nx"], dtype=float) * float(patch_range["dx"])
        patch_y = patch_range["yi"] + np.arange(patch_range["ny"], dtype=float) * float(patch_range["dy"])
        try:
            patch_domain = build_structured_domain(
                contour_x,
                contour_y,
                patch_x,
                patch_y,
                subcontours_ranges,
                clip_bounds=bounds,
                interface_rectangles=[(patch_id, bounds)],
                mesh_kind="sparse_patch",
            )
        except ValueError:
            continue

        if patch_domain.domain_count == 0:
            continue

        patches.append(
            PatchDomain(
                patch_id=patch_id,
                bounds=bounds,
                domain=patch_domain,
                coarse_interface_nodes=_extract_domain_nodes(
                    coarse_domain,
                    coarse_domain.interface_ids == patch_id,
                ),
                fine_interface_nodes=_extract_domain_nodes(
                    patch_domain,
                    patch_domain.interface_ids == patch_id,
                ),
            )
        )

    x_index = {_coordinate_key(value): index for index, value in enumerate(global_x)}
    y_index = {_coordinate_key(value): index for index, value in enumerate(global_y)}

    inside_mask = np.zeros((global_y.size, global_x.size), dtype=bool)
    boundary_mask = np.zeros_like(inside_mask)
    physical_boundary_mask = np.zeros_like(inside_mask)
    interface_boundary_mask = np.zeros_like(inside_mask)
    interface_ids = np.full((global_y.size, global_x.size), -1, dtype=int)
    region_ids = np.full((global_y.size, global_x.size), -1, dtype=int)

    def project_domain(domain: DiscreteDomain) -> None:
        for row, col in np.argwhere(domain.inside_mask):
            global_row = y_index[_coordinate_key(domain.y_coords[row])]
            global_col = x_index[_coordinate_key(domain.x_coords[col])]
            inside_mask[global_row, global_col] = True

        for row, col in np.argwhere(domain.interface_boundary_mask):
            global_row = y_index[_coordinate_key(domain.y_coords[row])]
            global_col = x_index[_coordinate_key(domain.x_coords[col])]
            interface_boundary_mask[global_row, global_col] = True
            interface_ids[global_row, global_col] = int(domain.interface_ids[row, col])

        for row, col in np.argwhere(domain.physical_boundary_mask):
            global_row = y_index[_coordinate_key(domain.y_coords[row])]
            global_col = x_index[_coordinate_key(domain.x_coords[col])]
            physical_boundary_mask[global_row, global_col] = True
            boundary_mask[global_row, global_col] = True
            region_ids[global_row, global_col] = int(domain.region_ids[row, col])

    project_domain(coarse_domain)
    for patch in patches:
        project_domain(patch.domain)

    boundary_counts = {region.region_id: 0 for region in regions}
    for region_id in region_ids[boundary_mask]:
        boundary_counts[int(region_id)] += 1

    internal_mask = inside_mask & ~boundary_mask
    return CompositeDomain(
        nx=int(global_x.size),
        ny=int(global_y.size),
        xmin=float(global_x[0]),
        ymin=float(global_y[0]),
        dx=_minimum_spacing(global_x),
        dy=_minimum_spacing(global_y),
        x_coords=global_x,
        y_coords=global_y,
        inside_mask=inside_mask,
        boundary_mask=boundary_mask,
        internal_mask=internal_mask,
        region_ids=region_ids,
        boundary_counts=boundary_counts,
        regions=regions,
        physical_boundary_mask=physical_boundary_mask,
        interface_boundary_mask=interface_boundary_mask,
        interface_ids=interface_ids,
        background_domain=background_domain,
        coarse_domain=coarse_domain,
        patches=patches,
        mesh_kind="sparse",
    )


def _boundary_field_from_values(
    domain: DiscreteDomain,
    boundary_values: dict[int, float],
    fixed_boundary_values: np.ndarray | None = None,
) -> np.ndarray:
    field = np.full((domain.ny, domain.nx), np.nan, dtype=float)

    if fixed_boundary_values is not None:
        if fixed_boundary_values.shape != field.shape:
            raise ValueError("Fixed boundary values do not match the domain shape.")
        fixed_mask = np.isfinite(fixed_boundary_values) & domain.boundary_mask
        field[fixed_mask] = fixed_boundary_values[fixed_mask]

    for row, col in np.argwhere(domain.physical_boundary_mask):
        region_id = int(domain.region_ids[row, col])
        if region_id not in boundary_values:
            raise ValueError("All boundary regions must have an assigned value.")
        field[row, col] = float(boundary_values[region_id])

    unresolved = domain.boundary_mask & ~np.isfinite(field)
    if np.any(unresolved):
        raise ValueError("Discrete domain contains unresolved Dirichlet boundary values.")

    return field


def _local_coefficients(domain: DiscreteDomain, row: int, col: int) -> tuple[float, float, float, float, float]:
    h_w = float(domain.x_coords[col] - domain.x_coords[col - 1])
    h_e = float(domain.x_coords[col + 1] - domain.x_coords[col])
    h_s = float(domain.y_coords[row] - domain.y_coords[row - 1])
    h_n = float(domain.y_coords[row + 1] - domain.y_coords[row])

    if min(h_w, h_e, h_s, h_n) <= 0.0:
        raise ValueError("Structured grid spacings must be positive.")

    a_e = 2.0 / (h_e * (h_e + h_w))
    a_w = 2.0 / (h_w * (h_e + h_w))
    a_n = 2.0 / (h_n * (h_n + h_s))
    a_s = 2.0 / (h_s * (h_n + h_s))
    a_p = a_e + a_w + a_n + a_s
    return a_w, a_e, a_s, a_n, a_p


def _solve_structured_problem(
    domain: DiscreteDomain,
    boundary_values: dict[int, float],
    *,
    problem_key: str = "laplace",
    source_term: float = 0.0,
    fixed_boundary_values: np.ndarray | None = None,
) -> SolveResult:
    if problem_key not in {"laplace", "poisson"}:
        raise ValueError("Unsupported problem type.")

    rhs_source = 0.0 if problem_key == "laplace" else float(source_term)
    boundary_field = _boundary_field_from_values(domain, boundary_values, fixed_boundary_values)
    values = np.full((domain.ny, domain.nx), np.nan, dtype=float)
    values[domain.boundary_mask] = boundary_field[domain.boundary_mask]

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

    matrix = lil_matrix((system_size, system_size), dtype=float)
    vector = np.zeros(system_size, dtype=float)

    for row, col in internal_positions:
        row = int(row)
        col = int(col)
        index = equation_index[row, col]
        a_w, a_e, a_s, a_n, a_p = _local_coefficients(domain, row, col)
        matrix[index, index] = a_p
        vector[index] = rhs_source

        neighbors = (
            (row, col - 1, a_w),
            (row, col + 1, a_e),
            (row - 1, col, a_s),
            (row + 1, col, a_n),
        )

        for next_row, next_col, coeff in neighbors:
            if domain.internal_mask[next_row, next_col]:
                matrix[index, equation_index[next_row, next_col]] -= coeff
                continue
            if domain.boundary_mask[next_row, next_col]:
                vector[index] += coeff * boundary_field[next_row, next_col]
                continue
            raise ValueError("Discrete domain contains an unsupported boundary configuration.")

    matrix = matrix.tocsr()
    solution = np.asarray(spsolve(matrix, vector), dtype=float).reshape(-1)
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


def _build_edge_samples(
    nodes: list[DomainNode],
    values: np.ndarray,
    bounds: tuple[float, float, float, float],
) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    tolerance = max(abs(bounds[2] - bounds[0]), abs(bounds[3] - bounds[1]), 1.0) * 1.0e-12
    edge_data: dict[str, list[tuple[float, float]]] = {edge: [] for edge in ("west", "east", "south", "north")}

    for node in nodes:
        edge = _classify_rectangle_edge(node.x, node.y, bounds, tolerance)
        coordinate = node.y if edge in {"west", "east"} else node.x
        edge_data[edge].append((float(coordinate), float(values[node.row, node.col])))

    interpolators: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for edge, samples in edge_data.items():
        if not samples:
            continue
        samples.sort(key=lambda item: item[0])
        coordinates = np.asarray([sample[0] for sample in samples], dtype=float)
        sample_values = np.asarray([sample[1] for sample in samples], dtype=float)
        unique_coordinates, unique_indices = np.unique(coordinates, return_index=True)
        interpolators[edge] = (unique_coordinates, sample_values[unique_indices])

    return interpolators


def _sample_rectangle_boundary_values(
    source_nodes: list[DomainNode],
    source_values: np.ndarray,
    target_nodes: list[DomainNode],
    bounds: tuple[float, float, float, float],
) -> np.ndarray:
    if not target_nodes:
        return np.zeros(0, dtype=float)

    interpolators = _build_edge_samples(source_nodes, source_values, bounds)
    tolerance = max(abs(bounds[2] - bounds[0]), abs(bounds[3] - bounds[1]), 1.0) * 1.0e-12
    result = np.zeros(len(target_nodes), dtype=float)

    for index, node in enumerate(target_nodes):
        edge = _classify_rectangle_edge(node.x, node.y, bounds, tolerance)
        if edge not in interpolators:
            raise ValueError("Sparse interface interpolation could not determine edge samples.")
        coordinates, sample_values = interpolators[edge]
        coordinate = node.y if edge in {"west", "east"} else node.x
        result[index] = float(np.interp(coordinate, coordinates, sample_values))

    return result


def _boundary_field_from_samples(domain: DiscreteDomain, nodes: list[DomainNode], samples: np.ndarray) -> np.ndarray:
    field = np.full((domain.ny, domain.nx), np.nan, dtype=float)
    for node, value in zip(nodes, samples):
        field[node.row, node.col] = float(value)
    return field


def _map_values_to_global(
    destination: np.ndarray,
    source_domain: DiscreteDomain,
    source_values: np.ndarray,
    x_index: dict[float, int],
    y_index: dict[float, int],
) -> None:
    for row, col in np.argwhere(source_domain.inside_mask):
        global_row = y_index[_coordinate_key(source_domain.y_coords[row])]
        global_col = x_index[_coordinate_key(source_domain.x_coords[col])]
        destination[global_row, global_col] = float(source_values[row, col])


def _solve_sparse_composite_problem(
    domain: CompositeDomain,
    boundary_values: dict[int, float],
    *,
    problem_key: str = "laplace",
    source_term: float = 0.0,
) -> SolveResult:
    if problem_key not in {"laplace", "poisson"}:
        raise ValueError("Unsupported problem type.")

    interface_field = np.full((domain.coarse_domain.ny, domain.coarse_domain.nx), np.nan, dtype=float)
    if domain.patches:
        background_result = _solve_structured_problem(
            domain.background_domain,
            boundary_values,
            problem_key=problem_key,
            source_term=source_term,
        )
        for patch in domain.patches:
            for node in patch.coarse_interface_nodes:
                interface_field[node.row, node.col] = float(background_result.values[node.row, node.col])

    last_coarse_result: SolveResult | None = None
    last_patch_results: dict[int, SolveResult] = {}
    interface_delta = 0.0
    converged = not domain.patches

    for _ in range(SPARSE_MAX_ITERATIONS if domain.patches else 1):
        last_coarse_result = _solve_structured_problem(
            domain.coarse_domain,
            boundary_values,
            problem_key=problem_key,
            source_term=source_term,
            fixed_boundary_values=interface_field,
        )

        interface_delta = 0.0
        current_patch_results: dict[int, SolveResult] = {}

        for patch in domain.patches:
            fine_samples = _sample_rectangle_boundary_values(
                patch.coarse_interface_nodes,
                last_coarse_result.values,
                patch.fine_interface_nodes,
                patch.bounds,
            )
            fine_field = _boundary_field_from_samples(patch.domain, patch.fine_interface_nodes, fine_samples)
            patch_result = _solve_structured_problem(
                patch.domain,
                boundary_values,
                problem_key=problem_key,
                source_term=source_term,
                fixed_boundary_values=fine_field,
            )
            current_patch_results[patch.patch_id] = patch_result

            new_coarse_samples = _sample_rectangle_boundary_values(
                patch.fine_interface_nodes,
                patch_result.values,
                patch.coarse_interface_nodes,
                patch.bounds,
            )
            old_coarse_samples = np.asarray(
                [interface_field[node.row, node.col] for node in patch.coarse_interface_nodes],
                dtype=float,
            )
            if old_coarse_samples.size > 0:
                interface_delta = max(
                    interface_delta,
                    float(np.max(np.abs(new_coarse_samples - old_coarse_samples))),
                )
            for node, value in zip(patch.coarse_interface_nodes, new_coarse_samples):
                interface_field[node.row, node.col] = float(value)

        last_patch_results = current_patch_results
        if interface_delta < SPARSE_INTERFACE_TOLERANCE:
            converged = True
            break

    if last_coarse_result is None:
        raise ValueError("Sparse composite solve could not initialize the coarse problem.")
    if not converged:
        raise ValueError("Sparse interface coupling did not converge.")

    x_index = {_coordinate_key(value): index for index, value in enumerate(domain.x_coords)}
    y_index = {_coordinate_key(value): index for index, value in enumerate(domain.y_coords)}
    values = np.full((domain.ny, domain.nx), np.nan, dtype=float)

    _map_values_to_global(values, domain.coarse_domain, last_coarse_result.values, x_index, y_index)
    for patch in domain.patches:
        patch_result = last_patch_results[patch.patch_id]
        _map_values_to_global(values, patch.domain, patch_result.values, x_index, y_index)

    residual = last_coarse_result.residual
    for patch_result in last_patch_results.values():
        residual = max(residual, patch_result.residual)
    residual = max(residual, interface_delta)

    system_size = domain.coarse_domain.internal_count + sum(patch.domain.internal_count for patch in domain.patches)
    domain_values = values[domain.inside_mask]
    return SolveResult(
        values=values,
        system_size=system_size,
        residual=float(residual),
        min_value=float(np.nanmin(domain_values)),
        max_value=float(np.nanmax(domain_values)),
        mean_value=float(np.nanmean(domain_values)),
    )


def solve_dirichlet_problem(
    domain: DiscreteDomain | CompositeDomain,
    boundary_values: dict[int, float],
    *,
    problem_key: str = "laplace",
    source_term: float = 0.0,
) -> SolveResult:
    if isinstance(domain, CompositeDomain):
        return _solve_sparse_composite_problem(
            domain,
            boundary_values,
            problem_key=problem_key,
            source_term=source_term,
        )

    return _solve_structured_problem(
        domain,
        boundary_values,
        problem_key=problem_key,
        source_term=source_term,
    )
