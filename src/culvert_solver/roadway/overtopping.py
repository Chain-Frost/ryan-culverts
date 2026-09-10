"""FHWA HDS-5 roadway-overtopping calculation."""

from dataclasses import dataclass

from .._validation import finite
from ..exceptions import InvalidInputError
from ..models.roadway import RoadwayWeir


@dataclass(frozen=True, slots=True)
class RoadwayOvertoppingResult:
    """Unsubmerged roadway-weir flow at one upstream water-surface elevation."""

    roadway: RoadwayWeir
    discharge: float
    headwater_elevation: float
    tailwater_elevation: float
    upstream_head: float


def calculate_roadway_overtopping(
    roadway: RoadwayWeir,
    headwater_elevation: float,
    tailwater_elevation: float,
) -> RoadwayOvertoppingResult:
    """Calculate constant-crest, unsubmerged roadway flow using HDS-5 Eq. 3.9.

    The supported equation is ``Q = C_d L H_wr**1.5`` in SI units. This first
    roadway implementation fails closed when tailwater is above the roadway
    crest because HDS-5 requires a coefficient correction selected from Figure
    3.11C. It also leaves sag-curve segmentation to a later task.
    """
    if not isinstance(roadway, RoadwayWeir):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise InvalidInputError("roadway must be a RoadwayWeir.")
    headwater: float = finite(headwater_elevation, "headwater_elevation")
    tailwater: float = finite(tailwater_elevation, "tailwater_elevation")
    if tailwater > roadway.crest_elevation:
        raise InvalidInputError(
            "Submerged roadway overtopping is not supported: tailwater_elevation must be at or below crest_elevation."
        )
    upstream_head: float = max(0.0, headwater - roadway.crest_elevation)
    discharge: float = roadway.discharge_coefficient * roadway.crest_length * upstream_head**1.5
    return RoadwayOvertoppingResult(
        roadway=roadway,
        discharge=discharge,
        headwater_elevation=headwater,
        tailwater_elevation=tailwater,
        upstream_head=upstream_head,
    )
