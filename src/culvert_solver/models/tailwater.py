"""Fixed and discharge-dependent downstream tailwater boundaries."""

from dataclasses import dataclass
from enum import StrEnum
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
        "Normal-depth approximation for a downstream channel without controls that " "require a backwater calculation."
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


@dataclass(frozen=True, slots=True)
class TailwaterResolution:
    """Resolved absolute tailwater elevation and calculation provenance."""

    elevation: float
    method: TailwaterMethod
    discharge: float
    channel_invert_elevation: float | None = None
    depth: float | None = None
    roughness: float | None = None
    friction_slope: float | None = None
    channel_section: OpenChannelSection | None = None
    normal_depth_result: ChannelNormalDepthResult | None = None
    source: SourceReference | None = None

    def __post_init__(self) -> None:
        elevation: float = finite(self.elevation, "elevation")
        discharge: float = _nonnegative_discharge(self.discharge)
        if not isinstance(self.method, TailwaterMethod):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise InvalidInputError("method must be a TailwaterMethod.")
        invert: None | float = (
            None
            if self.channel_invert_elevation is None
            else finite(self.channel_invert_elevation, "channel_invert_elevation")
        )
        depth: None | float = None if self.depth is None else finite(self.depth, "depth")
        roughness: None | float = None if self.roughness is None else finite(self.roughness, "roughness")
        slope: None | float = None if self.friction_slope is None else finite(self.friction_slope, "friction_slope")
        if depth is not None and depth < 0.0:
            raise InvalidInputError("depth must be nonnegative.")
        if self.method is TailwaterMethod.MANNING_NORMAL_DEPTH:
            if (
                invert is None
                or depth is None
                or roughness is None
                or slope is None
                or self.channel_section is None
                or self.normal_depth_result is None
            ):
                raise InvalidInputError(
                    "A Manning tailwater resolution requires channel geometry, invert, "
                    "depth, roughness, friction slope, and normal-depth result."
                )
            if roughness <= 0.0 or slope <= 0.0:
                raise InvalidInputError("Manning tailwater roughness and friction slope must be positive.")
            if self.source is None:
                raise InvalidInputError("A Manning tailwater resolution requires a source.")
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
class ManningChannelTailwater:
    """Normal-depth tailwater for a prismatic downstream channel.

    ``friction_slope`` is the Manning energy slope. Representative bed slope is
    an approximation valid only under the documented uniform-flow assumption.
    """

    section: OpenChannelSection
    channel_invert_elevation: float
    roughness: float
    friction_slope: float
    source: SourceReference = FHWA_HDS5_NORMAL_DEPTH_TAILWATER

    def __post_init__(self) -> None:
        if not isinstance(self.section, OpenChannelSection):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise InvalidInputError("section must satisfy the OpenChannelSection protocol.")
        invert: float = finite(self.channel_invert_elevation, "channel_invert_elevation")
        roughness: float = finite(self.roughness, "roughness")
        slope: float = finite(self.friction_slope, "friction_slope")
        if roughness <= 0.0:
            raise InvalidInputError("roughness must be strictly positive.")
        if slope <= 0.0:
            raise InvalidInputError("friction_slope must be strictly positive.")
        if not isinstance(self.source, SourceReference):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise InvalidInputError("source must be a SourceReference.")
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
            source=self.source,
        )


type TailwaterInput = TailwaterBoundary | float


def resolve_tailwater(
    tailwater: TailwaterInput,
    discharge: float,
    *,
    g: float = GRAVITATIONAL_ACCELERATION,
) -> TailwaterResolution:
    """Resolve a numeric, fixed, or flow-dependent tailwater boundary."""
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
            raise InvalidInputError("Tailwater boundary resolution must retain the requested discharge.")
        return resolution
    raise InvalidInputError("tailwater must be a finite elevation or satisfy the TailwaterBoundary protocol.")


def _nonnegative_discharge(discharge: float) -> float:
    q: float = finite(discharge, "discharge")
    if q < 0.0:
        raise InvalidInputError("discharge must be nonnegative.")
    return q


def _positive_gravity(g: float) -> float:
    accel: float = finite(g, "g")
    if accel <= 0.0:
        raise InvalidInputError("g must be strictly positive.")
    return accel
