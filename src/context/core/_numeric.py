from __future__ import annotations

from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_EVEN, localcontext
from math import isclose

import numpy as np


DECIMAL_PRECISION = 34
FLOAT_DTYPE = np.float64
RELATIVE_TOLERANCE = 1.0e-12
ABSOLUTE_TOLERANCE = 1.0e-15


def as_decimal(value: float | int | str) -> Decimal:
    """Preserve the decimal value entered by the user before float64 conversion."""
    return Decimal(str(value))


def divide_distance(distance: float, parts: int) -> float:
    if distance <= 0:
        raise ValueError("distance must be greater than zero")
    if parts < 1:
        raise ValueError("parts must be at least one")
    with localcontext() as context:
        context.prec = DECIMAL_PRECISION
        return float(as_decimal(distance) / as_decimal(parts))


def interpolate_value(start: float, end: float, numerator: int, denominator: int) -> float:
    if denominator < 1:
        raise ValueError("denominator must be at least one")
    if not 0 <= numerator <= denominator:
        raise ValueError("numerator must be between zero and denominator")
    with localcontext() as context:
        context.prec = DECIMAL_PRECISION
        ratio = as_decimal(numerator) / as_decimal(denominator)
        value = as_decimal(start) + (as_decimal(end) - as_decimal(start)) * ratio
    return float(format(float(value), ".15g"))


def grid_coordinate(origin: float, spacing: float, index: int) -> float:
    """Build a grid coordinate without accumulating repeated binary additions."""
    if spacing <= 0:
        raise ValueError("spacing must be greater than zero")
    with localcontext() as context:
        context.prec = DECIMAL_PRECISION
        value = as_decimal(origin) + as_decimal(spacing) * as_decimal(index)
    # IEEE-754 double precision guarantees 15 significant decimal digits.
    # Canonicalizing at that boundary removes arithmetic tails such as
    # 0.30000000000000004 without claiming unsupported extra precision.
    return float(format(float(value), ".15g"))


def floor_grid_index(value: float, origin: float, spacing: float) -> int:
    if spacing <= 0:
        raise ValueError("spacing must be greater than zero")
    with localcontext() as context:
        context.prec = DECIMAL_PRECISION
        ratio = (as_decimal(value) - as_decimal(origin)) / as_decimal(spacing)
        return int(ratio.to_integral_value(rounding=ROUND_FLOOR))


def snap_down_to_grid(value: float, origin: float, spacing: float) -> float:
    return grid_coordinate(origin, spacing, floor_grid_index(value, origin, spacing))


def grid_count(start: float, end: float, spacing: float) -> int:
    if spacing <= 0:
        raise ValueError("spacing must be greater than zero")
    if end < start:
        raise ValueError("grid end must not be smaller than grid start")
    with localcontext() as context:
        context.prec = DECIMAL_PRECISION
        ratio = (as_decimal(end) - as_decimal(start)) / as_decimal(spacing)
        nearest = ratio.to_integral_value(rounding=ROUND_HALF_EVEN)
        tolerance = max(abs(ratio), Decimal(1)) * Decimal(str(RELATIVE_TOLERANCE))
        rounding = ROUND_HALF_EVEN if abs(ratio - nearest) <= tolerance else ROUND_CEILING
        intervals = int(ratio.to_integral_value(rounding=rounding))
    return intervals + 1


def fitted_grid_end(start: float, end: float, spacing: float) -> tuple[int, float]:
    count = grid_count(start, end, spacing)
    return count, grid_coordinate(start, spacing, count - 1)


def values_close(left: float, right: float) -> bool:
    return isclose(
        float(left),
        float(right),
        rel_tol=RELATIVE_TOLERANCE,
        abs_tol=ABSOLUTE_TOLERANCE,
    )


def coordinate_key(value: float) -> str:
    """Stable float64 topology key with 15 significant decimal digits."""
    return format(float(value), ".15g")
