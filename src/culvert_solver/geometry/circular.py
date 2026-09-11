"""Analytical circular cross-section geometry."""

import math
from dataclasses import dataclass
from typing import Self

from .._validation import finite
from ..exceptions import InvalidInputError
from ..units.conversion import dimension_mm_to_m
from .base import CrossSectionGeometry


@dataclass(frozen=True, slots=True)
class CircularGeometry(CrossSectionGeometry):
    """Circular pipe barrel geometry defined by internal diameter in metres.

    All properties and methods return SI units.
    """

    diameter: float

    def __post_init__(self) -> None:
        val: float = finite(self.diameter, "diameter")
        if val <= 0:
            msg = "diameter must be strictly positive."
            raise InvalidInputError(msg)
        object.__setattr__(self, "diameter", val)

    @classmethod
    def from_mm(cls, diameter_mm: float) -> Self:
        """Construct circular geometry from an internal diameter in millimetres."""
        return cls(diameter=dimension_mm_to_m(diameter_mm))

    @property
    def span(self) -> float:
        """Internal diameter in metres."""
        return self.diameter

    @property
    def rise(self) -> float:
        """Internal diameter in metres."""
        return self.diameter

    @property
    def area_full(self) -> float:
        """Full circular cross-sectional area in square metres (pi * D² / 4)."""
        return math.pi * self.diameter * self.diameter / 4.0

    @property
    def wetted_perimeter_full(self) -> float:
        """Full circular wetted perimeter in metres (pi * D)."""
        return math.pi * self.diameter

    @property
    def hydraulic_radius_full(self) -> float:
        """Full circular hydraulic radius in metres (D / 4)."""
        return self.diameter / 4.0

    def area(self, depth: float) -> float:
        """Wetted flow area at the specified depth in square metres."""
        y: float = finite(depth, "depth")
        if y < 0:
            msg = "depth must be nonnegative."
            raise InvalidInputError(msg)
        if y == 0:
            return 0.0
        if y >= self.diameter:
            return self.area_full

        d: float = self.diameter
        xi: float = max(-1.0, min(1.0, 1.0 - 2.0 * y / d))
        theta: float = 2.0 * math.acos(xi)
        return (d * d / 8.0) * (theta - math.sin(theta))

    def wetted_perimeter(self, depth: float) -> float:
        """Wetted perimeter at the specified depth in metres."""
        y: float = finite(depth, "depth")
        if y < 0:
            msg = "depth must be nonnegative."
            raise InvalidInputError(msg)
        if y == 0:
            return 0.0
        if y >= self.diameter:
            return self.wetted_perimeter_full

        d: float = self.diameter
        xi: float = max(-1.0, min(1.0, 1.0 - 2.0 * y / d))
        theta: float = 2.0 * math.acos(xi)
        return d * theta / 2.0

    def top_width(self, depth: float) -> float:
        """Free-surface top width at the specified depth in metres.

        Returns 0.0 for depth <= 0 and for depth >= diameter (closed crown).
        """
        y: float = finite(depth, "depth")
        if y < 0:
            msg = "depth must be nonnegative."
            raise InvalidInputError(msg)
        if y == 0 or y >= self.diameter:
            return 0.0

        d: float = self.diameter
        return 2.0 * math.sqrt(max(0.0, y * (d - y)))

    def hydrostatic_pressure_moment(self, depth: float) -> float:
        """Return the exact circular-segment hydrostatic first moment in cubic metres."""
        y: float = finite(depth, "depth")
        if y < 0.0 or y > self.diameter:
            msg = "depth must be between zero and the geometry rise."
            raise InvalidInputError(msg)
        if y == 0.0:
            return 0.0
        radius = self.diameter / 2.0
        theta = 2.0 * math.acos(max(-1.0, min(1.0, (radius - y) / radius)))
        area = 0.5 * radius * radius * (theta - math.sin(theta))
        centroid_term = (2.0 / 3.0) * radius**3 * math.sin(theta / 2.0) ** 3
        return area * (y - radius) + centroid_term
