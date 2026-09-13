"""Fixed and discharge-dependent downstream tailwater boundaries."""

from bisect import bisect_left
from dataclasses import dataclass
from enum import StrEnum
from itertools import pairwise
from typing import Protocol, runtime_checkable

from .._validation import finite
from ..channel.geometry import OpenChannelSection
from ..channel.uniform import ChannelNormalDepthResult, calculate_channel_normal_depth
from ..constants import GRAVITATIONAL_ACCELERATION
from ..exceptions import InvalidInputError
from ..references.models import SourceReference

FHWA_HDS5_NORMAL_DEPTH_TAILWATER = SourceReference(
    source_id="FHWA-HDS5-2012-SECTION-1.4.4",
    publication="Hydraulic Design of Highway Culverts",
    edition="Third Edition, April 2012",
    locator="Section 1.4.4, Tailwater (printed page 1.19; PDF page 35)",
    url="https://www.fhwa.dot.gov/engineering/hydraulics/pubs/12026/hif12026.pdf",
    applicability=(
        "Normal-depth approximation for a downstream channel without controls that require a backwater calculation."
    ),
    notes=(
        "A prismatic uniform-flow boundary is not a receiving-reach backwater model; "
        "impoundments, constrictions, junctions, tidal effects, and other downstream "
        "controls require a more detailed method."
    ),
)


class TailwaterMethod(StrEnum):
    """Method used to obtain a downstream tailwater elevation."""

    FIXED_ELEVATION = "fixed_elevation"
    MANNING_NORMAL_DEPTH = "manning_normal_depth"
    RATING_CURVE = "rating_curve"


class TailwaterInterpolation(StrEnum):
    """How a tailwater rating curve supplied its resolved elevation."""

    EXACT_POINT = "exact_point"
    LINEAR = "linear"


@dataclass(frozen=True, slots=True)
class TailwaterRatingPoint:
    """One user-supplied discharge and absolute water-surface elevation pair."""

    discharge: float
    elevation: float

    def __post_init__(self) -> None:
        discharge: float = _nonnegative_discharge(self.discharge)
        elevation: float = finite(self.elevation, "elevation")
        object.__setattr__(self, "discharge", discharge)
        object.__setattr__(self, "elevation", elevation)


@dataclass(frozen=True, slots=True)
class TailwaterResolution:
    """Resolved absolute tailwater elevation and calculation provenance.

    ``depth`` is relative to ``channel_invert_elevation`` for a Manning
    boundary; it is not culvert-outlet-relative tailwater depth.
    """

    elevation: float
    method: TailwaterMethod
    discharge: float
    channel_invert_elevation: float | None = None
    depth: float | None = None
    roughness: float | None = None
    friction_slope: float | None = None
    channel_section: OpenChannelSection | None = None
    normal_depth_result: ChannelNormalDepthResult | None = None
    method_source: SourceReference | None = None
    roughness_source: SourceReference | None = None
    slope_source: SourceReference | None = None
    geometry_source: SourceReference | None = None
    channel_invert_source: SourceReference | None = None
    rating_curve: tuple[TailwaterRatingPoint, ...] | None = None
    rating_curve_source: SourceReference | None = None
    interpolation: TailwaterInterpolation | None = None

    def __post_init__(self) -> None:
        elevation: float = finite(self.elevation, "elevation")
        discharge: float = _nonnegative_discharge(self.discharge)
        if not isinstance(self.method, TailwaterMethod):  # pyright: ignore[reportUnnecessaryIsInstance]
            msg = "method must be a TailwaterMethod."
            raise InvalidInputError(msg)
        invert: float | None = (
            None
            if self.channel_invert_elevation is None
            else finite(self.channel_invert_elevation, "channel_invert_elevation")
        )
        depth: float | None = None if self.depth is None else finite(self.depth, "depth")
        roughness: float | None = None if self.roughness is None else finite(self.roughness, "roughness")
        slope: float | None = None if self.friction_slope is None else finite(self.friction_slope, "friction_slope")
        for name in (
            "method_source",
            "roughness_source",
            "slope_source",
            "geometry_source",
            "channel_invert_source",
            "rating_curve_source",
        ):
            value = getattr(self, name)
            if value is not None and not isinstance(  # pyright: ignore[reportUnnecessaryIsInstance]
                value, SourceReference
            ):
                msg = f"{name} must be a SourceReference when supplied."
                raise InvalidInputError(msg)
        if self.interpolation is not None and not isinstance(  # pyright: ignore[reportUnnecessaryIsInstance]
            self.interpolation, TailwaterInterpolation
        ):
            msg = "interpolation must be a TailwaterInterpolation when supplied."
            raise InvalidInputError(msg)
        if depth is not None and depth < 0.0:
            msg = "depth must be nonnegative."
            raise InvalidInputError(msg)
        if self.method is TailwaterMethod.MANNING_NORMAL_DEPTH:
            if (
                invert is None
                or depth is None
                or roughness is None
                or slope is None
                or self.channel_section is None
                or self.normal_depth_result is None
            ):
                msg = (
                    "A Manning tailwater resolution requires channel geometry, invert, "
                    "depth, roughness, friction slope, and normal-depth result."
                )
                raise InvalidInputError(msg)
            if roughness <= 0.0 or slope <= 0.0:
                msg = "Manning tailwater roughness and friction slope must be positive."
                raise InvalidInputError(msg)
            if self.method_source is None:
                msg = "A Manning tailwater resolution requires a method_source."
                raise InvalidInputError(msg)
        if self.method is TailwaterMethod.RATING_CURVE and (
            self.rating_curve is None or self.rating_curve_source is None or self.interpolation is None
        ):
            msg = (
                "A rating-curve tailwater resolution requires the rating curve, rating_curve_source, and interpolation."
            )
            raise InvalidInputError(msg)
        object.__setattr__(self, "elevation", elevation)
        object.__setattr__(self, "discharge", discharge)
        object.__setattr__(self, "channel_invert_elevation", invert)
        object.__setattr__(self, "depth", depth)
        object.__setattr__(self, "roughness", roughness)
        object.__setattr__(self, "friction_slope", slope)


@runtime_checkable
class TailwaterBoundary(Protocol):
    """Flow-dependent or fixed tailwater boundary contract."""

    def resolve(
        self,
        discharge: float,
        *,
        g: float = GRAVITATIONAL_ACCELERATION,
    ) -> TailwaterResolution:
        """Resolve absolute tailwater elevation for the receiving discharge."""
        ...


@dataclass(frozen=True, slots=True)
class TailwaterCondition:
    """Downstream tailwater specified as an absolute water-surface elevation."""

    elevation: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "elevation", finite(self.elevation, "elevation"))

    def depth_at_invert(self, outlet_invert: float) -> float:
        """Return nonnegative tailwater depth at a barrel outlet invert."""
        return max(0.0, self.elevation - finite(outlet_invert, "outlet_invert"))

    def resolve(
        self,
        discharge: float,
        *,
        g: float = GRAVITATIONAL_ACCELERATION,
    ) -> TailwaterResolution:
        """Return this fixed elevation through the common boundary interface."""
        q: float = _nonnegative_discharge(discharge)
        _positive_gravity(g)
        return TailwaterResolution(
            elevation=self.elevation,
            method=TailwaterMethod.FIXED_ELEVATION,
            discharge=q,
        )


@dataclass(frozen=True, slots=True)
class TailwaterRatingCurve:
    """User-supplied monotonic discharge/elevation tailwater boundary.

    The curve uses exact elevations at supplied points and linear interpolation
    between them. Discharges outside its closed range are rejected; the boundary
    never clamps or extrapolates.
    """

    points: tuple[TailwaterRatingPoint, ...]
    rating_curve_source: SourceReference

    def __post_init__(self) -> None:
        try:
            points: tuple[TailwaterRatingPoint, ...] = tuple(self.points)
        except TypeError as exc:
            msg = "points must be an iterable of TailwaterRatingPoint values."
            raise InvalidInputError(msg) from exc
        if len(points) < 2:
            msg = "points must contain at least two rating-curve points."
            raise InvalidInputError(msg)
        if any(
            not isinstance(point, TailwaterRatingPoint)  # pyright: ignore[reportUnnecessaryIsInstance]
            for point in points
        ):
            msg = "points must contain only TailwaterRatingPoint values."
            raise InvalidInputError(msg)
        for lower, upper in pairwise(points):
            if upper.discharge <= lower.discharge:
                msg = "Rating-curve discharges must be strictly increasing."
                raise InvalidInputError(msg)
            if upper.elevation < lower.elevation:
                msg = "Rating-curve elevations must be nondecreasing."
                raise InvalidInputError(msg)
        if not isinstance(  # pyright: ignore[reportUnnecessaryIsInstance]
            self.rating_curve_source, SourceReference
        ):
            msg = "rating_curve_source must be a SourceReference."
            raise InvalidInputError(msg)
        object.__setattr__(self, "points", points)

    def resolve(
        self,
        discharge: float,
        *,
        g: float = GRAVITATIONAL_ACCELERATION,
    ) -> TailwaterResolution:
        """Resolve an in-range stage without clamping or extrapolation."""
        q: float = _nonnegative_discharge(discharge)
        _positive_gravity(g)
        minimum: float = self.points[0].discharge
        maximum: float = self.points[-1].discharge
        if q < minimum or q > maximum:
            msg = f"discharge {q} is outside the tailwater rating-curve range [{minimum}, {maximum}]."
            raise InvalidInputError(msg)

        index: int = bisect_left(a=self.points, x=q, key=lambda point: point.discharge)
        if index < len(self.points) and self.points[index].discharge == q:
            elevation: float = self.points[index].elevation
            interpolation: TailwaterInterpolation = TailwaterInterpolation.EXACT_POINT
        else:
            lower: TailwaterRatingPoint = self.points[index - 1]
            upper: TailwaterRatingPoint = self.points[index]
            fraction: float = (q - lower.discharge) / (upper.discharge - lower.discharge)
            elevation = lower.elevation + fraction * (upper.elevation - lower.elevation)
            interpolation = TailwaterInterpolation.LINEAR

        return TailwaterResolution(
            elevation=elevation,
            method=TailwaterMethod.RATING_CURVE,
            discharge=q,
            rating_curve=self.points,
            rating_curve_source=self.rating_curve_source,
            interpolation=interpolation,
        )

    @property
    def min_discharge(self) -> float:
        """Lowest discharge supported without extrapolation."""
        return self.points[0].discharge

    @property
    def max_discharge(self) -> float:
        """Highest discharge supported without extrapolation."""
        return self.points[-1].discharge


@dataclass(frozen=True, slots=True)
class ManningChannelTailwater:
    """Normal-depth tailwater for a prismatic downstream channel.

    ``friction_slope`` is the Manning energy slope. Representative bed slope is
    an approximation valid only under the documented uniform-flow assumption.
    ``method_source`` documents that method; the other source fields document
    the independently selected project parameters.
    """

    section: OpenChannelSection
    channel_invert_elevation: float
    roughness: float
    friction_slope: float
    method_source: SourceReference = FHWA_HDS5_NORMAL_DEPTH_TAILWATER
    roughness_source: SourceReference | None = None
    slope_source: SourceReference | None = None
    geometry_source: SourceReference | None = None
    channel_invert_source: SourceReference | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.section, OpenChannelSection):  # pyright: ignore[reportUnnecessaryIsInstance]
            msg = "section must satisfy the OpenChannelSection protocol."
            raise InvalidInputError(msg)
        invert: float = finite(self.channel_invert_elevation, "channel_invert_elevation")
        roughness: float = finite(self.roughness, "roughness")
        slope: float = finite(self.friction_slope, "friction_slope")
        if roughness <= 0.0:
            msg = "roughness must be strictly positive."
            raise InvalidInputError(msg)
        if slope <= 0.0:
            msg = "friction_slope must be strictly positive."
            raise InvalidInputError(msg)
        for name, value in (
            ("method_source", self.method_source),
            ("roughness_source", self.roughness_source),
            ("slope_source", self.slope_source),
            ("geometry_source", self.geometry_source),
            ("channel_invert_source", self.channel_invert_source),
        ):
            if value is not None and not isinstance(  # pyright: ignore[reportUnnecessaryIsInstance]
                value, SourceReference
            ):
                msg = f"{name} must be a SourceReference when supplied."
                raise InvalidInputError(msg)
        object.__setattr__(self, "channel_invert_elevation", invert)
        object.__setattr__(self, "roughness", roughness)
        object.__setattr__(self, "friction_slope", slope)

    def resolve(
        self,
        discharge: float,
        *,
        g: float = GRAVITATIONAL_ACCELERATION,
    ) -> TailwaterResolution:
        """Resolve normal depth and absolute downstream water-surface elevation."""
        q: float = _nonnegative_discharge(discharge)
        result: ChannelNormalDepthResult = calculate_channel_normal_depth(
            section=self.section,
            discharge=q,
            friction_slope=self.friction_slope,
            roughness=self.roughness,
            g=g,
        )
        return TailwaterResolution(
            elevation=self.channel_invert_elevation + result.depth,
            method=TailwaterMethod.MANNING_NORMAL_DEPTH,
            discharge=q,
            channel_invert_elevation=self.channel_invert_elevation,
            depth=result.depth,
            roughness=self.roughness,
            friction_slope=self.friction_slope,
            channel_section=self.section,
            normal_depth_result=result,
            method_source=self.method_source,
            roughness_source=self.roughness_source,
            slope_source=self.slope_source,
            geometry_source=self.geometry_source,
            channel_invert_source=self.channel_invert_source,
        )


type TailwaterInput = TailwaterBoundary | float


def resolve_tailwater(
    tailwater: TailwaterInput,
    discharge: float,
    *,
    g: float = GRAVITATIONAL_ACCELERATION,
) -> TailwaterResolution:
    """Resolve a numeric, fixed, or flow-dependent ``TailwaterInput`` boundary."""
    q: float = _nonnegative_discharge(discharge)
    accel: float = _positive_gravity(g)
    if isinstance(tailwater, (float, int)) and not isinstance(tailwater, bool):
        return TailwaterResolution(
            elevation=finite(tailwater, "tailwater"),
            method=TailwaterMethod.FIXED_ELEVATION,
            discharge=q,
        )
    if isinstance(tailwater, TailwaterBoundary):
        resolution: TailwaterResolution = tailwater.resolve(q, g=accel)
        if resolution.discharge != q:
            msg = "Tailwater boundary resolution must retain the requested discharge."
            raise InvalidInputError(msg)
        return resolution
    msg = "tailwater must be a finite elevation or satisfy the TailwaterBoundary protocol."
    raise InvalidInputError(msg)


def _nonnegative_discharge(discharge: float) -> float:
    q: float = finite(discharge, "discharge")
    if q < 0.0:
        msg = "discharge must be nonnegative."
        raise InvalidInputError(msg)
    return q


def _positive_gravity(g: float) -> float:
    accel: float = finite(g, "g")
    if accel <= 0.0:
        msg = "g must be strictly positive."
        raise InvalidInputError(msg)
    return accel
