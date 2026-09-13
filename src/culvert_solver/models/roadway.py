"""Roadway crest models for supported overtopping calculations."""

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from itertools import pairwise

from .._validation import finite
from ..exceptions import InvalidInputError
from ..references.models import SourceReference

FHWA_HDS5_ROADWAY_OVERTOPPING = SourceReference(
    source_id="FHWA-HDS5-2012-EQ-3.9",
    publication="Hydraulic Design of Highway Culverts",
    edition="Third Edition, April 2012",
    locator="Section 3.1.5, Equation 3.9 and Figures 3.10-3.12",
    url="https://www.fhwa.dot.gov/engineering/hydraulics/pubs/12026/hif12026.pdf",
    applicability=(
        "Broad-crested-weir flow over a roadway embankment; the SI discharge "
        "coefficient must be selected for the actual crest and overtopping depth."
    ),
    notes=(
        "Equation 3.9 is applied to constant crests and to the horizontal integration "
        "segments used for irregular roadway profiles. Downstream submergence is handled "
        "only by the separately sourced correction implemented by the roadway solver."
    ),
)

FHWA_HY8_ROADWAY_PROFILE_INTEGRATION = SourceReference(
    source_id="FHWA-RD-88-125-ROADWAY-PROFILE",
    publication="HYDRAIN - Integrated Drainage Design Computer System, Volume VI. HY8 - Culvert Analysis",
    edition="FHWA-RD-88-125, July 1988",
    locator="Section 3, Roadway Overtopping, printed pages 19-20",
    url="https://rosap.ntl.bts.gov/view/dot/68373/dot_68373_DS1.pdf",
    applicability=(
        "Roadway profiles described by station/elevation coordinates; the roadway-weir "
        "equation is integrated between adjacent coordinates with four-point Gaussian quadrature."
    ),
    notes=(
        "The reference states that the weir coefficient and submergence reduction are "
        "evaluated at each integration point."
    ),
)

FHWA_BRIDGE_WATERWAYS_ROADWAY_SUBMERGENCE = SourceReference(
    source_id="FHWA-RD-86-108-ROADWAY-SUBMERGENCE",
    publication="Bridge Waterways Analysis Model: Research Report",
    edition="FHWA-RD-86-108, July 1986",
    locator="Figure 10, roadway overtopping submergence relationship",
    url="https://rosap.ntl.bts.gov/view/dot/54268",
    applicability=(
        "Downstream-submergence reduction for paved and gravel roadway overtopping. "
        "The correction is applied as a multiplier to the free-flow roadway discharge coefficient."
    ),
)

EPA_SWMM_ROADWAY_SUBMERGENCE_DIGITISATION = SourceReference(
    source_id="EPA-SWMM-5.2-ROADWAY-SUBMERGENCE-DIGITISATION",
    publication="EPA Storm Water Management Model roadway-weir implementation",
    edition="SWMM 5.2",
    locator="src/solver/roadway.c, Kt_Paved and Kt_Gravel tables",
    url="https://github.com/USEPA/Stormwater-Management-Model/blob/develop/src/solver/roadway.c",
    applicability=(
        "Digital ordinates for the paved and gravel roadway submergence curves. "
        "The implementation identifies FHWA/RD-86/108 Figure 10 as the source of the data."
    ),
    notes=(
        "Used as transparent digitisation evidence only; the FHWA publication remains the "
        "governing engineering source. Values above the published ratio range are not extrapolated."
    ),
)


class RoadwaySurface(StrEnum):
    """Roadway surface classes supported by the sourced submergence relationship."""

    PAVED = "paved"
    GRAVEL = "gravel"


@dataclass(frozen=True, slots=True)
class RoadwayCrestPoint:
    """One horizontal station/elevation coordinate on an irregular roadway crest."""

    station: float
    elevation: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "station", finite(self.station, "station"))
        object.__setattr__(self, "elevation", finite(self.elevation, "elevation"))


@dataclass(frozen=True, slots=True)
class RoadwayCrestProfile:
    """Piecewise-linear roadway crest defined by increasing station coordinates."""

    points: tuple[RoadwayCrestPoint, ...]

    def __init__(self, points: Sequence[RoadwayCrestPoint]) -> None:
        processed_points = tuple(points)
        if len(processed_points) < 2:
            msg = "RoadwayCrestProfile requires at least two station/elevation points."
            raise InvalidInputError(msg)
        if not all(
            isinstance(point, RoadwayCrestPoint)  # pyright: ignore[reportUnnecessaryIsInstance]
            for point in processed_points
        ):
            msg = "points must contain only RoadwayCrestPoint values."
            raise InvalidInputError(msg)
        for left, right in pairwise(processed_points):
            if right.station <= left.station:
                msg = "Roadway crest stations must be strictly increasing."
                raise InvalidInputError(msg)
        object.__setattr__(self, "points", processed_points)

    @property
    def crest_length(self) -> float:
        """Horizontal station span of the roadway profile in metres."""
        return self.points[-1].station - self.points[0].station

    @property
    def minimum_crest_elevation(self) -> float:
        """Lowest roadway elevation represented by the profile."""
        return min(point.elevation for point in self.points)


@dataclass(frozen=True, slots=True)
class RoadwayWeir:
    """A constant-elevation roadway crest represented as a broad-crested weir.

    ``discharge_coefficient`` is the SI coefficient in
    ``Q = C_d L H**1.5`` and therefore has units of m**0.5/s. HDS-5 requires
    it to be selected from the roadway geometry and overtopping-depth curves;
    the library intentionally supplies no universal default.

    ``surface`` is optional for free overflow. It must be ``PAVED`` or
    ``GRAVEL`` before a supported downstream-submergence correction can be
    applied.
    """

    crest_elevation: float
    crest_length: float
    discharge_coefficient: float
    label: str = ""
    coefficient_source: SourceReference = FHWA_HDS5_ROADWAY_OVERTOPPING
    surface: RoadwaySurface | None = None

    def __post_init__(self) -> None:
        crest_elevation: float = finite(self.crest_elevation, "crest_elevation")
        crest_length: float = finite(self.crest_length, "crest_length")
        if crest_length <= 0.0:
            msg = "crest_length must be strictly positive."
            raise InvalidInputError(msg)
        discharge_coefficient: float = finite(self.discharge_coefficient, "discharge_coefficient")
        if discharge_coefficient <= 0.0:
            msg = "discharge_coefficient must be strictly positive."
            raise InvalidInputError(msg)
        if not isinstance(self.coefficient_source, SourceReference):  # pyright: ignore[reportUnnecessaryIsInstance]
            msg = "coefficient_source must be a SourceReference."
            raise InvalidInputError(msg)
        if self.surface is not None and not isinstance(  # pyright: ignore[reportUnnecessaryIsInstance]
            self.surface, RoadwaySurface
        ):
            msg = "surface must be a RoadwaySurface or None."
            raise InvalidInputError(msg)
        object.__setattr__(self, "crest_elevation", crest_elevation)
        object.__setattr__(self, "crest_length", crest_length)
        object.__setattr__(self, "discharge_coefficient", discharge_coefficient)

    @property
    def minimum_crest_elevation(self) -> float:
        """Lowest roadway elevation represented by the constant crest."""
        return self.crest_elevation


@dataclass(frozen=True, slots=True)
class RoadwayProfileWeir:
    """An irregular roadway crest integrated between station/elevation coordinates."""

    profile: RoadwayCrestProfile
    discharge_coefficient: float
    label: str = ""
    coefficient_source: SourceReference = FHWA_HDS5_ROADWAY_OVERTOPPING
    integration_source: SourceReference = FHWA_HY8_ROADWAY_PROFILE_INTEGRATION
    surface: RoadwaySurface | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.profile, RoadwayCrestProfile):  # pyright: ignore[reportUnnecessaryIsInstance]
            msg = "profile must be a RoadwayCrestProfile."
            raise InvalidInputError(msg)
        discharge_coefficient: float = finite(self.discharge_coefficient, "discharge_coefficient")
        if discharge_coefficient <= 0.0:
            msg = "discharge_coefficient must be strictly positive."
            raise InvalidInputError(msg)
        if not isinstance(self.coefficient_source, SourceReference):  # pyright: ignore[reportUnnecessaryIsInstance]
            msg = "coefficient_source must be a SourceReference."
            raise InvalidInputError(msg)
        if not isinstance(self.integration_source, SourceReference):  # pyright: ignore[reportUnnecessaryIsInstance]
            msg = "integration_source must be a SourceReference."
            raise InvalidInputError(msg)
        if self.surface is not None and not isinstance(  # pyright: ignore[reportUnnecessaryIsInstance]
            self.surface, RoadwaySurface
        ):
            msg = "surface must be a RoadwaySurface or None."
            raise InvalidInputError(msg)
        object.__setattr__(self, "discharge_coefficient", discharge_coefficient)

    @property
    def crest_length(self) -> float:
        """Horizontal station span of the roadway profile in metres."""
        return self.profile.crest_length

    @property
    def crest_elevation(self) -> float:
        """Minimum crest elevation, retained as a scalar compatibility summary."""
        return self.minimum_crest_elevation

    @property
    def minimum_crest_elevation(self) -> float:
        """Lowest roadway elevation represented by the profile."""
        return self.profile.minimum_crest_elevation


type RoadwayOvertoppingInput = RoadwayWeir | RoadwayProfileWeir
