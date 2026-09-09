"""Explicit engineering dimension conversion."""

from .._validation import finite
from ..exceptions import InvalidInputError


def dimension_mm_to_m(dimension_mm: float) -> float:
    """Convert a strictly positive culvert dimension in millimetres to metres."""
    value: float = finite(value=dimension_mm, name="dimension_mm")
    converted: float = value / 1000.0
    if converted <= 0:
        raise InvalidInputError("Dimension must remain positive and representable in metres.")
    return converted
