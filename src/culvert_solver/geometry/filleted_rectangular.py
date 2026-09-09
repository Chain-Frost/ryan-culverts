"""Rectangular box geometry with equal 45-degree internal corner fillets."""

import math
from typing import Self

from .._validation import finite
from ..exceptions import InvalidInputError
from ..units.conversion import dimension_mm_to_m
from .base import CrossSectionGeometry


class FilletedRectangularGeometry(CrossSectionGeometry):
    """Box culvert section with an equal triangular fillet at each internal corner.

    ``span`` and ``rise`` are the maximum clear dimensions. ``fillet`` is the
    horizontal and vertical leg length of each 45-degree triangular fillet. All
    dimensions and returned quantities use SI units.
    """

    __slots__ = ("_fillet", "_rise", "_span")

    def __init__(self, span: float, rise: float, fillet: float) -> None:
        span_value: float = finite(span, "span")
        rise_value: float = finite(rise, "rise")
        fillet_value: float = finite(fillet, "fillet")
        if span_value <= 0:
            raise InvalidInputError("span must be strictly positive.")
        if rise_value <= 0:
            raise InvalidInputError("rise must be strictly positive.")
        if fillet_value <= 0:
            raise InvalidInputError("fillet must be strictly positive.")
        if 2.0 * fillet_value >= min(span_value, rise_value):
            raise InvalidInputError("fillet must be less than half the span and rise.")
        self._span: float = span_value
        self._rise: float = rise_value
        self._fillet: float = fillet_value

    @classmethod
    def from_mm(cls, span_mm: float, rise_mm: float, fillet_mm: float) -> Self:
        """Construct a filleted box from millimetre dimensions."""
        return cls(
            span=dimension_mm_to_m(span_mm),
            rise=dimension_mm_to_m(rise_mm),
            fillet=dimension_mm_to_m(fillet_mm),
        )

    @property
    def span(self) -> float:
        """Maximum internal horizontal span in metres."""
        return self._span

    @property
    def rise(self) -> float:
        """Maximum internal vertical rise in metres."""
        return self._rise

    @property
    def fillet(self) -> float:
        """Horizontal and vertical fillet leg length in metres."""
        return self._fillet

    @property
    def area_full(self) -> float:
        """Net full-flow area after removing four triangular fillets."""
        return self._span * self._rise - 2.0 * self._fillet**2

    @property
    def wetted_perimeter_full(self) -> float:
        """Internal perimeter including all four diagonal fillet faces."""
        return 2.0 * (self._span + self._rise) + 4.0 * (math.sqrt(2.0) - 2.0) * self._fillet

    def _depth(self, depth: float) -> float:
        value: float = finite(depth, "depth")
        if value < 0:
            raise InvalidInputError("depth must be nonnegative.")
        return min(value, self._rise)

    def area(self, depth: float) -> float:
        """Wetted net area at ``depth`` in square metres."""
        y: float = self._depth(depth)
        if y == 0.0:
            return 0.0
        if y >= self._rise:
            return self.area_full
        a: float = self._fillet
        if y < a:
            return (self._span - 2.0 * a) * y + y * y
        area: float = self._span * y - a * a
        if y > self._rise - a:
            top_submergence: float = y - (self._rise - a)
            area -= top_submergence * top_submergence
        return area

    def wetted_perimeter(self, depth: float) -> float:
        """Wetted boundary length, excluding the free surface for partial flow."""
        y: float = self._depth(depth)
        if y == 0.0:
            return 0.0
        if y >= self._rise:
            return self.wetted_perimeter_full
        a: float = self._fillet
        bottom_width: float = self._span - 2.0 * a
        if y < a:
            return bottom_width + 2.0 * math.sqrt(2.0) * y
        perimeter: float = bottom_width + 2.0 * math.sqrt(2.0) * a
        if y <= self._rise - a:
            return perimeter + 2.0 * (y - a)
        perimeter += 2.0 * (self._rise - 2.0 * a)
        return perimeter + 2.0 * math.sqrt(2.0) * (y - (self._rise - a))

    def top_width(self, depth: float) -> float:
        """Free-surface width at ``depth`` in metres."""
        y: float = self._depth(depth)
        if y == 0.0 or y >= self._rise:
            return 0.0
        a: float = self._fillet
        if y < a:
            return self._span - 2.0 * (a - y)
        if y <= self._rise - a:
            return self._span
        return self._span - 2.0 * (y - (self._rise - a))

    def __repr__(self) -> str:
        return (
            f"FilletedRectangularGeometry(span={self._span!r}, rise={self._rise!r}, "
            f"fillet={self._fillet!r})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FilletedRectangularGeometry):
            return NotImplemented
        return (
            self._span == other._span
            and self._rise == other._rise
            and self._fillet == other._fillet
        )
