from __future__ import annotations

from dataclasses import dataclass
from threading import Event
from typing import Sequence

import numpy as np
from shapely import intersects_xy, prepare
from shapely.geometry import Polygon

from ._numeric import FLOAT_DTYPE, grid_coordinate


class GridPlotCancelled(Exception):
    """Raised internally when a newer grid plot supersedes the current one."""


@dataclass(frozen=True, slots=True)
class GridSpec:
    """Immutable description of one Cartesian grid used by the renderer."""

    nx: int
    ny: int
    xmin: float | None = None
    ymin: float | None = None
    dx: float | None = None
    dy: float | None = None
    x_coordinates: tuple[float, ...] | None = None
    y_coordinates: tuple[float, ...] | None = None

    @classmethod
    def uniform(
        cls,
        xmin: float,
        ymin: float,
        dx: float,
        dy: float,
        nx: int,
        ny: int,
    ) -> GridSpec:
        return cls(
            nx=int(nx),
            ny=int(ny),
            xmin=float(xmin),
            ymin=float(ymin),
            dx=float(dx),
            dy=float(dy),
        )

    @classmethod
    def from_axes(
        cls,
        x_coordinates: Sequence[float],
        y_coordinates: Sequence[float],
    ) -> GridSpec:
        x_values = tuple(float(value) for value in x_coordinates)
        y_values = tuple(float(value) for value in y_coordinates)
        return cls(
            nx=len(x_values),
            ny=len(y_values),
            x_coordinates=x_values,
            y_coordinates=y_values,
        )

    def coordinate_arrays(self) -> tuple[np.ndarray, np.ndarray]:
        if self.x_coordinates is not None and self.y_coordinates is not None:
            return (
                np.asarray(self.x_coordinates, dtype=FLOAT_DTYPE),
                np.asarray(self.y_coordinates, dtype=FLOAT_DTYPE),
            )

        if None in (self.xmin, self.ymin, self.dx, self.dy):
            raise ValueError("uniform grid origin and spacing are required")
        if self.nx < 1 or self.ny < 1:
            raise ValueError("grid dimensions must be positive")

        x_values = np.fromiter(
            (grid_coordinate(self.xmin, self.dx, index) for index in range(self.nx)),
            dtype=FLOAT_DTYPE,
            count=self.nx,
        )
        y_values = np.fromiter(
            (grid_coordinate(self.ymin, self.dy, index) for index in range(self.ny)),
            dtype=FLOAT_DTYPE,
            count=self.ny,
        )
        return x_values, y_values


@dataclass(frozen=True, slots=True)
class GridPlotData:
    horizontal_x: tuple[float, ...]
    horizontal_y: tuple[float, ...]
    vertical_x: tuple[float, ...]
    vertical_y: tuple[float, ...]
    node_count: int


def _check_cancelled(cancel_event: Event | None) -> None:
    if cancel_event is not None and cancel_event.is_set():
        raise GridPlotCancelled


def _run_bounds(mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    padded = np.empty(mask.size + 2, dtype=np.int8)
    padded[0] = 0
    padded[-1] = 0
    padded[1:-1] = mask
    transitions = np.diff(padded)
    starts = np.flatnonzero(transitions == 1)
    ends = np.flatnonzero(transitions == -1) - 1
    return starts, ends


def _append_horizontal_segments(
    mask: np.ndarray,
    x_values: np.ndarray,
    y_values: np.ndarray,
    x_parts: list[np.ndarray],
    y_parts: list[np.ndarray],
    cancel_event: Event | None,
) -> None:
    for row_index, y_value in enumerate(y_values):
        if row_index % 64 == 0:
            _check_cancelled(cancel_event)
        starts, ends = _run_bounds(mask[row_index])
        if starts.size == 0:
            continue
        x_parts.append(np.column_stack((x_values[starts], x_values[ends])).reshape(-1))
        y_parts.append(np.full(starts.size * 2, y_value, dtype=FLOAT_DTYPE))


def _append_vertical_segments(
    mask: np.ndarray,
    x_values: np.ndarray,
    y_values: np.ndarray,
    x_parts: list[np.ndarray],
    y_parts: list[np.ndarray],
    cancel_event: Event | None,
) -> None:
    for column_index, x_value in enumerate(x_values):
        if column_index % 64 == 0:
            _check_cancelled(cancel_event)
        starts, ends = _run_bounds(mask[:, column_index])
        if starts.size == 0:
            continue
        x_parts.append(np.full(starts.size * 2, x_value, dtype=FLOAT_DTYPE))
        y_parts.append(np.column_stack((y_values[starts], y_values[ends])).reshape(-1))


def _flatten(parts: list[np.ndarray]) -> tuple[float, ...]:
    if not parts:
        return ()
    return tuple(float(value) for value in np.concatenate(parts))


def build_grid_plot(
    contour_x: Sequence[float],
    contour_y: Sequence[float],
    grid_specs: Sequence[GridSpec],
    cancel_event: Event | None = None,
) -> GridPlotData:
    """Classify and aggregate grid segments without touching Dear PyGui state."""

    if len(contour_x) != len(contour_y) or len(contour_x) < 4:
        raise ValueError("a closed contour with at least four points is required")
    if not grid_specs:
        raise ValueError("at least one grid is required")

    polygon = Polygon(zip(contour_x, contour_y))
    if not polygon.is_valid:
        polygon = polygon.buffer(0)
    if polygon.is_empty:
        raise ValueError("the contour does not define a valid polygon")
    prepare(polygon)

    horizontal_x_parts: list[np.ndarray] = []
    horizontal_y_parts: list[np.ndarray] = []
    vertical_x_parts: list[np.ndarray] = []
    vertical_y_parts: list[np.ndarray] = []
    covered_point_parts: list[np.ndarray] = []
    single_grid_count = 0

    for spec in grid_specs:
        _check_cancelled(cancel_event)
        x_values, y_values = spec.coordinate_arrays()
        if x_values.size != spec.nx or y_values.size != spec.ny:
            raise ValueError("grid axis lengths do not match its dimensions")

        inside_mask = np.asarray(
            intersects_xy(polygon, x_values[np.newaxis, :], y_values[:, np.newaxis]),
            dtype=bool,
        )
        _check_cancelled(cancel_event)

        _append_horizontal_segments(
            inside_mask,
            x_values,
            y_values,
            horizontal_x_parts,
            horizontal_y_parts,
            cancel_event,
        )
        _append_vertical_segments(
            inside_mask,
            x_values,
            y_values,
            vertical_x_parts,
            vertical_y_parts,
            cancel_event,
        )

        row_indices, column_indices = np.nonzero(inside_mask)
        if len(grid_specs) == 1:
            single_grid_count = int(row_indices.size)
        elif row_indices.size:
            # complex128 keeps both float64 components intact and allows an exact,
            # vectorized union of coincident nodes across sparse refinement ranges.
            covered_point_parts.append(
                x_values[column_indices].astype(np.complex128)
                + 1j * y_values[row_indices].astype(np.complex128)
            )

    _check_cancelled(cancel_event)
    if len(grid_specs) == 1:
        node_count = single_grid_count
    elif covered_point_parts:
        node_count = int(np.unique(np.concatenate(covered_point_parts)).size)
    else:
        node_count = 0

    return GridPlotData(
        horizontal_x=_flatten(horizontal_x_parts),
        horizontal_y=_flatten(horizontal_y_parts),
        vertical_x=_flatten(vertical_x_parts),
        vertical_y=_flatten(vertical_y_parts),
        node_count=node_count,
    )
