"""Four-arc oval geometry reconstructed from HY-8 concrete ShapeDB radii.

The nominal HY-8 "elliptical" product is not a mathematical ellipse: HEC-10
VII.C describes two pairs of circular arcs with long/short radii. ShapeDB v8
stores the two long radii, side radius, and half rise. This geometry joins
those arcs tangentially, then scales horizontal coordinates to the nominal
catalogue width. This is a source-derived *reconstruction*, not an assertion
that HY-8 uses identical interior-section numerical methods.
"""

import math
from collections.abc import Callable
from functools import lru_cache
from typing import Self

from .._validation import finite
from ..exceptions import InvalidInputError
from .base import CrossSectionGeometry
from .hy8_oval_catalogue import HY8_CONCRETE_OVALS, Hy8ConcreteOvalSize

_INCH_M = 0.0254
_FT2_M2 = 0.09290304
_CATALOGUE_MATCH_TOLERANCE_M = 2e-6
# A catalogue entry whose independently reconstructed geometric area differs
# beyond this *data reconciliation* tolerance must not be used for hydraulics.
# This is not an engineering accuracy or headwater acceptance tolerance.
_MAX_CATALOGUE_AREA_DIFFERENCE = 0.005
_ARC_PANELS = 128


def _simpson(function: Callable[[float], float], start: float, end: float) -> float:
    """Integrate a smooth parameterised arc (no endpoint singularities)."""
    if end <= start:
        return 0.0
    step = (end - start) / _ARC_PANELS
    total = function(start) + function(end)
    total += 4.0 * sum(function(start + index * step) for index in range(1, _ARC_PANELS, 2))
    total += 2.0 * sum(function(start + index * step) for index in range(2, _ARC_PANELS, 2))
    return total * step / 3.0


class Hy8ConcreteOvalGeometry(CrossSectionGeometry):
    """Nominal horizontal HY-8 concrete oval, using four source-backed arcs.

    Construct by exact nominal catalogue dimensions or zero-based row index.
    Rows whose arc-derived area disagrees materially with ShapeDB fail closed.
    No arbitrary dimensions, nearest-size substitution, or rotation are allowed.
    """

    __slots__ = (
        "_corner_radius",
        "_half_rise",
        "_horizontal_scale",
        "_join_height",
        "_long_radius",
        "_rise",
        "_side_offset",
        "_span",
        "_vertical_shift",
        "catalogue_index",
    )

    def __init__(self, catalogue_index: int) -> None:
        if isinstance(catalogue_index, bool) or not isinstance(catalogue_index, int):
            msg = "HY-8 oval catalogue_index must be an integer."
            raise InvalidInputError(msg)
        if not 0 <= catalogue_index < len(HY8_CONCRETE_OVALS):
            msg = "Unknown HY-8 concrete oval catalogue index."
            raise InvalidInputError(msg)
        size = HY8_CONCRETE_OVALS[catalogue_index]
        if size.bottom_radius_in != size.top_radius_in:
            msg = "Non-symmetric HY-8 oval top/bottom arcs are not supported."
            raise InvalidInputError(msg)
        if size.half_rise_in * 2 != size.rise_in:
            msg = "HY-8 oval catalogue half rise differs from nominal rise."
            raise InvalidInputError(msg)

        span = size.span_in * _INCH_M
        half_rise = size.half_rise_in * _INCH_M
        long_radius = size.bottom_radius_in * _INCH_M
        corner_radius = size.corner_radius_in * _INCH_M
        radial_difference = long_radius - corner_radius
        vertical_shift = long_radius - half_rise
        if not (long_radius > corner_radius > 0 and 0 < vertical_shift < radial_difference):
            msg = "Invalid HY-8 oval source radii: a tangent four-arc profile cannot be formed."
            raise InvalidInputError(msg)

        side_offset = math.sqrt(radial_difference**2 - vertical_shift**2)
        join_height = long_radius * vertical_shift / radial_difference - vertical_shift
        if not (0 < join_height < min(corner_radius, half_rise)):
            msg = "Invalid HY-8 oval source radii: arc junction is outside the section."
            raise InvalidInputError(msg)

        horizontal_scale = span / (2.0 * (side_offset + corner_radius))
        self.catalogue_index = catalogue_index
        self._span = span
        self._rise = 2.0 * half_rise
        self._half_rise = half_rise
        self._long_radius = long_radius
        self._corner_radius = corner_radius
        self._vertical_shift = vertical_shift
        self._side_offset = side_offset
        self._join_height = join_height
        self._horizontal_scale = horizontal_scale

        ratio = abs(self.area_full / self.shape_db_area_full - 1.0)
        if ratio > _MAX_CATALOGUE_AREA_DIFFERENCE:
            msg = (
                f"HY-8 oval catalogue row {catalogue_index} area reconciliation failed "
                f"({ratio:.2%} versus ShapeDB); the rounded radii do not resolve its "
                "hydraulic geometry sufficiently. Do not silently use an exact ellipse."
            )
            raise InvalidInputError(msg)

    @classmethod
    def from_mm(cls, span_mm: float, rise_mm: float) -> Self:
        """Select an exact catalogue pair supplied in millimetres."""
        span = finite(span_mm, "span_mm") * 0.001
        rise = finite(rise_mm, "rise_mm") * 0.001
        for size in HY8_CONCRETE_OVALS:
            if (
                abs(span - size.span_in * _INCH_M) <= _CATALOGUE_MATCH_TOLERANCE_M
                and abs(rise - size.rise_in * _INCH_M) <= _CATALOGUE_MATCH_TOLERANCE_M
            ):
                return cls(size.row_index)
        msg = "The requested HY-8 concrete oval is not an exact ShapeDB catalogue size."
        raise InvalidInputError(msg)

    @property
    def catalogue_size(self) -> Hy8ConcreteOvalSize:
        """The provenance-bearing ShapeDB entry for this geometry."""
        return HY8_CONCRETE_OVALS[self.catalogue_index]

    @property
    def span(self) -> float:
        """Maximum nominal internal width (m)."""
        return self._span

    @property
    def rise(self) -> float:
        """Nominal opening rise (m)."""
        return self._rise

    @property
    def shape_db_area_full(self) -> float:
        """Source-reported full opening area (m²), independent of reconstruction."""
        return self.catalogue_size.area_ft2 * _FT2_M2

    @property
    def shape_db_area_difference_percent(self) -> float:
        """Signed discrepancy between reconstructed and tabulated full area."""
        return 100.0 * (self.area_full / self.shape_db_area_full - 1.0)

    def _side_area_primitive(self, z: float) -> float:
        r = self._corner_radius
        return self._side_offset * z + 0.5 * (
            z * math.sqrt(max(0.0, r * r - z * z)) + r * r * math.asin(min(1.0, z / r))
        )

    def _top_area_primitive(self, z: float) -> float:
        r = self._long_radius
        u = z + self._vertical_shift
        return 0.5 * (u * math.sqrt(max(0.0, r * r - u * u)) + r * r * math.asin(min(1.0, u / r)))

    def _integrated_half_width(self, lower: float, upper: float) -> float:
        """Integrate raw right-hand half width on z in [0, half_rise]."""
        joint = self._join_height
        result = 0.0
        if lower < joint:
            stop = min(joint, upper)
            result += self._side_area_primitive(stop) - self._side_area_primitive(lower)
        if upper > joint:
            start = max(joint, lower)
            result += self._top_area_primitive(upper) - self._top_area_primitive(start)
        return result

    @property
    def area_full(self) -> float:
        """Full source-derived arc-section flow area (m²)."""
        return 4.0 * self._horizontal_scale * self._integrated_half_width(0.0, self._half_rise)

    def area(self, depth: float) -> float:
        """Depth-dependent flow area; symmetric about the half rise."""
        y = self._depth(depth)
        if y == 0:
            return 0.0
        if y >= self.rise:
            return self.area_full
        if y > self._half_rise:
            return self.area_full - self.area(self.rise - y)
        z = self._half_rise - y
        return 2.0 * self._horizontal_scale * self._integrated_half_width(z, self._half_rise)

    def top_width(self, depth: float) -> float:
        """Free-surface width, including the circular-arc shoulders."""
        y = self._depth(depth)
        if y == 0 or y >= self.rise:
            return 0.0
        z = abs(y - self._half_rise)
        if z < self._join_height:
            radius_width = self._side_offset + math.sqrt(max(0.0, self._corner_radius**2 - z**2))
        else:
            radius_width = math.sqrt(max(0.0, self._long_radius**2 - (z + self._vertical_shift) ** 2))
        return 2.0 * self._horizontal_scale * radius_width

    def _one_side_length(self, z_start: float) -> float:
        """Arc length from height z_start to the crown on one side."""
        scale = self._horizontal_scale
        total = 0.0
        if z_start < self._join_height:
            radius = self._corner_radius
            low = math.asin(min(1.0, z_start / radius))
            high = math.asin(min(1.0, self._join_height / radius))

            def side_integrand(theta: float) -> float:
                return radius * math.hypot(scale * math.sin(theta), math.cos(theta))

            total += _simpson(side_integrand, low, high)

        long_radius = self._long_radius
        start = max(self._join_height, z_start)
        top_start_angle = math.acos(min(1.0, (start + self._vertical_shift) / long_radius))

        def top_integrand(theta: float) -> float:
            return long_radius * math.hypot(scale * math.cos(theta), math.sin(theta))

        total += _simpson(top_integrand, 0.0, top_start_angle)
        return total

    @property
    def wetted_perimeter_full(self) -> float:
        """Four symmetric quarter-arcs in metres."""
        return 4.0 * self._one_side_length(0.0)

    def wetted_perimeter(self, depth: float) -> float:
        """Wetted contour length measured from the invert."""
        y = self._depth(depth)
        if y == 0:
            return 0.0
        if y >= self.rise:
            return self.wetted_perimeter_full
        if y > self._half_rise:
            return self.wetted_perimeter_full - self.wetted_perimeter(self.rise - y)
        return 2.0 * self._one_side_length(self._half_rise - y)

    @staticmethod
    def _depth(depth: float) -> float:
        y = finite(depth, "depth")
        if y < 0:
            msg = "depth must be nonnegative."
            raise InvalidInputError(msg)
        return y


@lru_cache(maxsize=64)
def hy8_oval_max_conveyance_depth(catalogue_index: int) -> float:
    """Cache the rising-branch Manning conveyance peak per catalogue row."""
    geometry = Hy8ConcreteOvalGeometry(catalogue_index)
    lower, upper = 0.0, geometry.rise
    for _ in range(64):
        first = lower + (upper - lower) / 3.0
        second = upper - (upper - lower) / 3.0
        if geometry.area(first) * geometry.hydraulic_radius(first) ** (2.0 / 3.0) < (
            geometry.area(second) * geometry.hydraulic_radius(second) ** (2.0 / 3.0)
        ):
            lower = first
        else:
            upper = second
    return 0.5 * (lower + upper)
