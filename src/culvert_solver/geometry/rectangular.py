"""Analytical rectangular box cross-section geometry."""

from typing import Self

from .._validation import finite
from ..exceptions import InvalidInputError
from ..units.conversion import dimension_mm_to_m
from .base import CrossSectionGeometry


class RectangularGeometry(CrossSectionGeometry):
    """Rectangular box culvert barrel geometry defined by internal span and rise in metres.

    All properties and methods return SI units.
    """

    __slots__ = ("_rise", "_span")

    def __init__(self, span: float, rise: float) -> None:
        s: float = finite(span, "span")
        if s <= 0:
            raise InvalidInputError("span must be strictly positive.")
        r: float = finite(rise, "rise")
        if r <= 0:
            raise InvalidInputError("rise must be strictly positive.")
        self._span: float = s
        self._rise: float = r

    @classmethod
    def from_mm(cls, span_mm: float, rise_mm: float) -> Self:
        """Construct rectangular geometry from internal span and rise in millimetres."""
        return cls(
            span=dimension_mm_to_m(span_mm),
            rise=dimension_mm_to_m(rise_mm),
        )

    @property
    def span(self) -> float:
        """Internal horizontal span (width) in metres."""
        return self._span

    @property
    def rise(self) -> float:
        """Internal vertical rise (height) in metres."""
        return self._rise

    @property
    def area_full(self) -> float:
        """Full cross-sectional flow area in square metres (span * rise)."""
        return self._span * self._rise

    @property
    def wetted_perimeter_full(self) -> float:
        """Full internal wetted perimeter in metres (2 * (span + rise))."""
        return 2.0 * (self._span + self._rise)

    def area(self, depth: float) -> float:
        """Wetted flow area at the specified depth in square metres."""
        y: float = finite(depth, "depth")
        if y < 0:
            raise InvalidInputError("depth must be nonnegative.")
        if y == 0:
            return 0.0
        if y >= self._rise:
            return self.area_full
        return self._span * y

    def wetted_perimeter(self, depth: float) -> float:
        """Wetted perimeter at the specified depth in metres."""
        y: float = finite(depth, "depth")
        if y < 0:
            raise InvalidInputError("depth must be nonnegative.")
        if y == 0:
            return 0.0
        if y >= self._rise:
            return self.wetted_perimeter_full
        return self._span + 2.0 * y

    def top_width(self, depth: float) -> float:
        """Free-surface top width at the specified depth in metres.

        Returns 0.0 for depth <= 0 and for depth >= rise (closed top slab).
        """
        y: float = finite(depth, "depth")
        if y < 0:
            raise InvalidInputError("depth must be nonnegative.")
        if y == 0 or y >= self._rise:
            return 0.0
        return self._span

    def hydrostatic_pressure_moment(self, depth: float) -> float:
        """Return the exact rectangular hydrostatic first moment in cubic metres."""
        y: float = finite(depth, "depth")
        if y < 0.0 or y > self._rise:
            raise InvalidInputError("depth must be between zero and the geometry rise.")
        return 0.5 * self._span * y * y

    def __repr__(self) -> str:
        return f"RectangularGeometry(span={self._span!r}, rise={self._rise!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RectangularGeometry):
            return NotImplemented
        return self._span == other._span and self._rise == other._rise
