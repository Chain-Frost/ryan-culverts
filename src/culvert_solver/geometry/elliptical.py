"""Analytical geometry for horizontal and vertical elliptical culverts."""

import math
from typing import Self

from .._validation import finite
from ..exceptions import InvalidInputError
from ..units.conversion import dimension_mm_to_m
from .base import CrossSectionGeometry

_ARC_SIMPSON_PANELS = 256


class _EllipticalGeometry(CrossSectionGeometry):
    """Shared exact-area ellipse geometry with numerical incomplete arc length."""

    __slots__ = ("_rise", "_span")

    def __init__(self, span: float, rise: float) -> None:
        span_value = finite(span, "span")
        rise_value = finite(rise, "rise")
        if span_value <= 0:
            msg = "span must be strictly positive."
            raise InvalidInputError(msg)
        if rise_value <= 0:
            msg = "rise must be strictly positive."
            raise InvalidInputError(msg)
        self._span = span_value
        self._rise = rise_value

    @classmethod
    def from_mm(cls, span_mm: float, rise_mm: float) -> Self:
        """Create an ellipse from millimetre span and rise dimensions."""
        return cls(
            span=dimension_mm_to_m(span_mm),
            rise=dimension_mm_to_m(rise_mm),
        )

    @property
    def span(self) -> float:
        """Maximum horizontal width in metres."""
        return self._span

    @property
    def rise(self) -> float:
        """Maximum vertical height in metres."""
        return self._rise

    @property
    def area_full(self) -> float:
        """Full ellipse area in square metres."""
        return math.pi * self.span * self.rise / 4.0

    @property
    def wetted_perimeter_full(self) -> float:
        """Full ellipse perimeter in metres."""
        return 2.0 * self._arc_length(-math.pi / 2.0, math.pi / 2.0)

    def is_full(self, depth: float) -> bool:
        """Return whether depth reaches or exceeds the crown."""
        return self._validated_depth(depth) >= self.rise

    def area(self, depth: float) -> float:
        """Flow area below a depth measured vertically from the invert."""
        y = self._validated_depth(depth)
        if y == 0.0:
            return 0.0
        if y >= self.rise:
            return self.area_full
        eta = self._normalized_vertical(y)
        root = math.sqrt(max(0.0, 1.0 - eta * eta))
        return (self.span * self.rise / 4.0) * (
            eta * root + math.asin(eta) + math.pi / 2.0
        )

    def wetted_perimeter(self, depth: float) -> float:
        """Wetted ellipse arc length below the water surface."""
        y = self._validated_depth(depth)
        if y == 0.0:
            return 0.0
        if y >= self.rise:
            return self.wetted_perimeter_full
        theta = math.asin(self._normalized_vertical(y))
        return 2.0 * self._arc_length(-math.pi / 2.0, theta)

    def top_width(self, depth: float) -> float:
        """Free-surface width at the supplied depth."""
        y = self._validated_depth(depth)
        if y == 0.0 or y >= self.rise:
            return 0.0
        eta = self._normalized_vertical(y)
        return self.span * math.sqrt(max(0.0, 1.0 - eta * eta))

    def _validated_depth(self, depth: float) -> float:
        y = finite(depth, "depth")
        if y < 0:
            msg = "depth must be nonnegative."
            raise InvalidInputError(msg)
        return y

    def _normalized_vertical(self, depth: float) -> float:
        return (2.0 * depth / self.rise) - 1.0

    def _arc_length(self, start: float, end: float) -> float:
        """Integrate one side of the ellipse using deterministic composite Simpson."""
        if end <= start:
            return 0.0
        semi_span = self.span / 2.0
        semi_rise = self.rise / 2.0
        step = (end - start) / _ARC_SIMPSON_PANELS

        def integrand(theta: float) -> float:
            return math.hypot(
                semi_span * math.sin(theta),
                semi_rise * math.cos(theta),
            )

        total = integrand(start) + integrand(end)
        total += 4.0 * sum(
            integrand(start + index * step)
            for index in range(1, _ARC_SIMPSON_PANELS, 2)
        )
        total += 2.0 * sum(
            integrand(start + index * step)
            for index in range(2, _ARC_SIMPSON_PANELS, 2)
        )
        return total * step / 3.0

    def __repr__(self) -> str:
        return f"{type(self).__name__}(span={self.span}, rise={self.rise})"

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return False
        assert isinstance(other, _EllipticalGeometry)
        return self.span == other.span and self.rise == other.rise


class HorizontalEllipseGeometry(_EllipticalGeometry):
    """Closed ellipse with the major axis horizontal."""

    def __init__(self, span: float, rise: float) -> None:
        super().__init__(span=span, rise=rise)
        if self.span <= self.rise:
            msg = "horizontal ellipse requires span > rise; use CircularGeometry when span == rise."
            raise InvalidInputError(msg)


class VerticalEllipseGeometry(_EllipticalGeometry):
    """Closed ellipse with the major axis vertical."""

    def __init__(self, span: float, rise: float) -> None:
        super().__init__(span=span, rise=rise)
        if self.rise <= self.span:
            msg = "vertical ellipse requires rise > span; use CircularGeometry when span == rise."
            raise InvalidInputError(msg)
