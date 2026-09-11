"""Internal validation shared by the public foundation types."""

import math

from .exceptions import InvalidInputError


def finite(value: object, name: str) -> float:
    """Accept finite built-in real scalars, excluding booleans."""
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        msg = f"{name} must be a finite real number."
        raise InvalidInputError(msg)
    try:
        result = float(value)
    except OverflowError as exc:
        msg = f"{name} is outside floating-point range."
        raise InvalidInputError(msg) from exc
    if not math.isfinite(result):
        msg = f"{name} must be finite."
        raise InvalidInputError(msg)
    return result


def positive_integer(value: object, name: str) -> int:
    """Validate an integer count without silently truncating floats."""
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        msg = f"{name} must be a positive integer."
        raise InvalidInputError(msg)
    return value
