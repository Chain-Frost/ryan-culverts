"""Abstract base class and protocol for hydraulic cross-section geometries."""

from abc import ABC, abstractmethod

from .._validation import finite
from ..exceptions import InvalidInputError


class CrossSectionGeometry(ABC):
    """Abstract base class for culvert barrel cross-section geometries.

    All physical dimensions and computed quantities are in SI units (metres,
    square metres). Subclasses implement specific shapes (e.g. circular,
    rectangular box).
    """

    @property
    @abstractmethod
    def span(self) -> float:
        """Maximum internal horizontal width in metres."""

    @property
    @abstractmethod
    def rise(self) -> float:
        """Maximum internal vertical height in metres."""

    @property
    @abstractmethod
    def area_full(self) -> float:
        """Full cross-sectional flow area in square metres."""

    @property
    @abstractmethod
    def wetted_perimeter_full(self) -> float:
        """Full internal wetted perimeter in metres."""

    @property
    def hydraulic_radius_full(self) -> float:
        """Full hydraulic radius in metres (area_full / wetted_perimeter_full)."""
        return self.area_full / self.wetted_perimeter_full

    def is_full(self, depth: float) -> bool:
        """Return True if water depth reaches or exceeds the conduit rise."""
        y: float = finite(depth, "depth")
        if y < 0:
            raise InvalidInputError("depth must be nonnegative.")
        return y >= self.rise

    @abstractmethod
    def area(self, depth: float) -> float:
        """Wetted flow area at the specified depth in square metres."""

    @abstractmethod
    def wetted_perimeter(self, depth: float) -> float:
        """Wetted perimeter at the specified depth in metres."""

    @abstractmethod
    def top_width(self, depth: float) -> float:
        """Free-surface top width at the specified depth in metres.

        Returns 0.0 when depth <= 0 or when depth >= rise (closed conduit at/above crown).
        """

    def hydraulic_radius(self, depth: float) -> float:
        """Hydraulic radius R = A / P at the specified depth in metres.

        Returns 0.0 for depth <= 0.
        Returns hydraulic_radius_full for depth >= rise.
        """
        y: float = finite(depth, "depth")
        if y < 0:
            raise InvalidInputError("depth must be nonnegative.")
        if y == 0:
            return 0.0
        if y >= self.rise:
            return self.hydraulic_radius_full
        p: float = self.wetted_perimeter(y)
        if p == 0:
            return 0.0
        return self.area(y) / p

    def hydraulic_depth(self, depth: float) -> float:
        """Hydraulic depth D_h = A / T at the specified depth in metres.

        Raises InvalidInputError when top width is 0 (dry conduit or closed conduit at/above crown).
        """
        y: float = finite(depth, "depth")
        if y < 0:
            raise InvalidInputError("depth must be nonnegative.")
        if y == 0:
            raise InvalidInputError("Hydraulic depth is undefined for zero depth (dry section).")
        if y >= self.rise:
            raise InvalidInputError(
                "Hydraulic depth is undefined for closed-conduit flow at or above the crown."
            )
        t: float = self.top_width(y)
        if t <= 0:
            raise InvalidInputError(
                "Hydraulic depth is undefined when free-surface top width is zero."
            )
        return self.area(y) / t

    def hydrostatic_pressure_moment(self, depth: float) -> float:
        """Return ``integral(area(z), z=0..depth)`` in cubic metres.

        This generic composite-Simpson implementation supports future geometry
        classes. Performance-sensitive built-in shapes override it analytically.
        """
        y = finite(depth, "depth")
        if y < 0.0 or y > self.rise:
            raise InvalidInputError("depth must be between zero and the geometry rise.")
        if y == 0.0:
            return 0.0
        panels = 64
        dz = y / panels
        weighted_area = self.area(0.0) + self.area(y)
        for index in range(1, panels):
            weighted_area += (4.0 if index % 2 else 2.0) * self.area(index * dz)
        return weighted_area * dz / 3.0
