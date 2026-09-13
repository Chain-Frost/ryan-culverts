"""FHWA roadway-overtopping calculations for constant and irregular crests."""

from dataclasses import dataclass

from .._validation import finite
from ..exceptions import InvalidInputError
from ..models.roadway import (
    EPA_SWMM_ROADWAY_SUBMERGENCE_DIGITISATION,
    FHWA_BRIDGE_WATERWAYS_ROADWAY_SUBMERGENCE,
    FHWA_HDS5_ROADWAY_OVERTOPPING,
    RoadwayCrestPoint,
    RoadwayCrestProfile,
    RoadwayOvertoppingInput,
    RoadwayProfileWeir,
    RoadwaySurface,
    RoadwayWeir,
)
from ..references.models import SourceReference

_GAUSS_4: tuple[tuple[float, float], ...] = (
    (-0.8611363115940526, 0.3478548451374538),
    (-0.3399810435848563, 0.6521451548625461),
    (0.3399810435848563, 0.6521451548625461),
    (0.8611363115940526, 0.3478548451374538),
)

# EPA SWMM identifies these digital ordinates as derived from FHWA/RD-86/108
# Figure 10. A zero-ratio unity point records the no-reduction region explicitly;
# values above ratio 1.0 are rejected rather than extrapolated or clamped.
_SUBMERGENCE_FACTORS: dict[RoadwaySurface, tuple[tuple[float, float], ...]] = {
    RoadwaySurface.PAVED: (
        (0.0, 1.0),
        (0.80, 1.0),
        (0.85, 0.98),
        (0.90, 0.92),
        (0.93, 0.85),
        (0.95, 0.80),
        (0.97, 0.70),
        (0.98, 0.60),
        (0.99, 0.50),
        (1.00, 0.40),
    ),
    RoadwaySurface.GRAVEL: (
        (0.0, 1.0),
        (0.75, 1.0),
        (0.80, 0.985),
        (0.83, 0.97),
        (0.86, 0.93),
        (0.89, 0.90),
        (0.90, 0.87),
        (0.92, 0.80),
        (0.94, 0.70),
        (0.96, 0.60),
        (0.98, 0.50),
        (0.99, 0.40),
        (1.00, 0.24),
    ),
}


@dataclass(frozen=True, slots=True)
class RoadwaySubmergenceCorrection:
    """One sourced downstream-submergence correction applied to roadway flow."""

    surface: RoadwaySurface
    ratio: float
    factor: float
    source: SourceReference = FHWA_BRIDGE_WATERWAYS_ROADWAY_SUBMERGENCE
    digitisation_source: SourceReference = EPA_SWMM_ROADWAY_SUBMERGENCE_DIGITISATION


@dataclass(frozen=True, slots=True)
class RoadwayOvertoppingSegmentResult:
    """Flow contribution from one weighted horizontal roadway integration segment."""

    source_interval_index: int
    interval_start_station: float
    interval_end_station: float
    integration_station: float
    effective_length: float
    crest_elevation: float
    upstream_head: float
    downstream_head: float
    discharge: float
    effective_discharge_coefficient: float
    integration_source: SourceReference
    submergence_correction: RoadwaySubmergenceCorrection | None = None


@dataclass(frozen=True, slots=True)
class RoadwayOvertoppingResult:
    """Roadway-weir flow at one upstream and downstream water-surface elevation."""

    roadway: RoadwayOvertoppingInput
    discharge: float
    headwater_elevation: float
    tailwater_elevation: float
    upstream_head: float
    segment_results: tuple[RoadwayOvertoppingSegmentResult, ...] = ()


def _submergence_correction(
    surface: RoadwaySurface | None,
    upstream_head: float,
    downstream_head: float,
) -> RoadwaySubmergenceCorrection | None:
    """Return the bounded paved/gravel correction or fail closed when unsupported."""
    if downstream_head <= 0.0 or upstream_head <= 0.0:
        return None
    if surface is None:
        msg = (
            "Submerged roadway overtopping requires roadway.surface to be "
            "RoadwaySurface.PAVED or RoadwaySurface.GRAVEL."
        )
        raise InvalidInputError(msg)

    ratio = downstream_head / upstream_head
    if ratio < 0.0 or ratio > 1.0:
        msg = (
            "Submerged roadway overtopping is outside the supported FHWA correction range: "
            "downstream_head / upstream_head must be between 0.0 and 1.0."
        )
        raise InvalidInputError(msg)

    table = _SUBMERGENCE_FACTORS[surface]
    factor = table[-1][1]
    for (x0, y0), (x1, y1) in zip(table, table[1:]):
        if ratio <= x1:
            fraction = (ratio - x0) / (x1 - x0)
            factor = y0 + fraction * (y1 - y0)
            break

    return RoadwaySubmergenceCorrection(
        surface=surface,
        ratio=ratio,
        factor=factor,
    )


def _segment_result(
    *,
    roadway: RoadwayOvertoppingInput,
    source_interval_index: int,
    interval_start_station: float,
    interval_end_station: float,
    integration_station: float,
    effective_length: float,
    crest_elevation: float,
    headwater_elevation: float,
    tailwater_elevation: float,
    integration_source: SourceReference,
) -> RoadwayOvertoppingSegmentResult:
    upstream_head = max(0.0, headwater_elevation - crest_elevation)
    downstream_head = max(0.0, tailwater_elevation - crest_elevation)
    correction = _submergence_correction(
        roadway.surface,
        upstream_head,
        downstream_head,
    )
    submergence_factor = 1.0 if correction is None else correction.factor
    effective_coefficient = roadway.discharge_coefficient * submergence_factor
    discharge = effective_coefficient * effective_length * upstream_head**1.5
    return RoadwayOvertoppingSegmentResult(
        source_interval_index=source_interval_index,
        interval_start_station=interval_start_station,
        interval_end_station=interval_end_station,
        integration_station=integration_station,
        effective_length=effective_length,
        crest_elevation=crest_elevation,
        upstream_head=upstream_head,
        downstream_head=downstream_head,
        discharge=discharge,
        effective_discharge_coefficient=effective_coefficient,
        integration_source=integration_source,
        submergence_correction=correction,
    )


def _split_parameters(
    left: RoadwayCrestPoint,
    right: RoadwayCrestPoint,
    levels: tuple[float, ...],
) -> tuple[float, ...]:
    """Return interval fractions split where a hydraulic level crosses the linear crest."""
    elevation_change = right.elevation - left.elevation
    parameters = [0.0, 1.0]
    if elevation_change != 0.0:
        for level in levels:
            fraction = (level - left.elevation) / elevation_change
            if 0.0 < fraction < 1.0:
                parameters.append(fraction)
    return tuple(sorted(set(parameters)))


def _profile_segment_results(
    roadway: RoadwayProfileWeir,
    headwater_elevation: float,
    tailwater_elevation: float,
) -> tuple[RoadwayOvertoppingSegmentResult, ...]:
    results: list[RoadwayOvertoppingSegmentResult] = []
    points = roadway.profile.points
    for interval_index, (left, right) in enumerate(zip(points, points[1:])):
        station_change = right.station - left.station
        elevation_change = right.elevation - left.elevation
        split_parameters = _split_parameters(
            left,
            right,
            (headwater_elevation, tailwater_elevation),
        )
        for lower, upper in zip(split_parameters, split_parameters[1:]):
            interval_start_station = left.station + lower * station_change
            interval_end_station = left.station + upper * station_change
            midpoint = (lower + upper) / 2.0
            half_span = (upper - lower) / 2.0
            for abscissa, weight in _GAUSS_4:
                fraction = midpoint + half_span * abscissa
                station = left.station + fraction * station_change
                crest_elevation = left.elevation + fraction * elevation_change
                effective_length = weight * half_span * station_change
                results.append(
                    _segment_result(
                        roadway=roadway,
                        source_interval_index=interval_index,
                        interval_start_station=interval_start_station,
                        interval_end_station=interval_end_station,
                        integration_station=station,
                        effective_length=effective_length,
                        crest_elevation=crest_elevation,
                        headwater_elevation=headwater_elevation,
                        tailwater_elevation=tailwater_elevation,
                        integration_source=roadway.integration_source,
                    )
                )
    return tuple(results)


def calculate_roadway_overtopping(
    roadway: RoadwayOvertoppingInput,
    headwater_elevation: float,
    tailwater_elevation: float,
) -> RoadwayOvertoppingResult:
    """Calculate roadway flow from HDS-5 Equation 3.9 with bounded extensions.

    Constant-elevation ``RoadwayWeir`` inputs preserve the original direct
    broad-crested-weir calculation. ``RoadwayProfileWeir`` inputs integrate the
    same equation over a piecewise-linear station/elevation profile using the
    four-point Gaussian procedure documented for FHWA HY8.

    When tailwater is above a local crest, the paved or gravel submergence
    factor is linearly interpolated from the source-traceable digital ordinates.
    Ratios above the supported endpoint are rejected rather than extrapolated.
    """
    if not isinstance(  # pyright: ignore[reportUnnecessaryIsInstance]
        roadway,
        (RoadwayWeir, RoadwayProfileWeir),
    ):
        msg = "roadway must be a RoadwayWeir or RoadwayProfileWeir."
        raise InvalidInputError(msg)
    headwater = finite(headwater_elevation, "headwater_elevation")
    tailwater = finite(tailwater_elevation, "tailwater_elevation")
    if tailwater > headwater:
        msg = "Reverse roadway flow is not supported: tailwater_elevation must not exceed headwater_elevation."
        raise InvalidInputError(msg)

    if isinstance(roadway, RoadwayWeir):
        segment_results = (
            _segment_result(
                roadway=roadway,
                source_interval_index=0,
                interval_start_station=0.0,
                interval_end_station=roadway.crest_length,
                integration_station=roadway.crest_length / 2.0,
                effective_length=roadway.crest_length,
                crest_elevation=roadway.crest_elevation,
                headwater_elevation=headwater,
                tailwater_elevation=tailwater,
                integration_source=FHWA_HDS5_ROADWAY_OVERTOPPING,
            ),
        )
    else:
        segment_results = _profile_segment_results(
            roadway,
            headwater_elevation=headwater,
            tailwater_elevation=tailwater,
        )

    discharge = sum(segment.discharge for segment in segment_results)
    return RoadwayOvertoppingResult(
        roadway=roadway,
        discharge=discharge,
        headwater_elevation=headwater,
        tailwater_elevation=tailwater,
        upstream_head=max(0.0, headwater - roadway.minimum_crest_elevation),
        segment_results=segment_results,
    )
