"""Internal validation shared by the public foundation types."""

import math

from .exceptions import InvalidInputError


def finite(value: object, name: str) -> float:
    """Accept finite built-in real scalars, excluding booleans."""
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise InvalidInputError(f"{name} must be a finite real number.")
    try:
        result = float(value)
    except OverflowError as exc:
        raise InvalidInputError(f"{name} is outside floating-point range.") from exc
    if not math.isfinite(result):
        raise InvalidInputError(f"{name} must be finite.")
    return result


def positive_integer(value: object, name: str) -> int:
    """Validate an integer count without silently truncating floats."""
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise InvalidInputError(f"{name} must be a positive integer.")
    return value
