"""Roadway crest model for supported overtopping calculations."""

from dataclasses import dataclass

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
        "This release supports a constant-elevation crest and unsubmerged flow only. "
        "Irregular crest segmentation and downstream-submergence correction are deferred."
    ),
)


@dataclass(frozen=True, slots=True)
class RoadwayWeir:
    """A constant-elevation roadway crest represented as a broad-crested weir.

    ``discharge_coefficient`` is the SI coefficient in
    ``Q = C_d L H**1.5`` and therefore has units of m**0.5/s. HDS-5 requires
    it to be selected from the roadway geometry and overtopping-depth curves;
    the library intentionally supplies no universal default.
    """

    crest_elevation: float
    crest_length: float
    discharge_coefficient: float
    label: str = ""
    coefficient_source: SourceReference = FHWA_HDS5_ROADWAY_OVERTOPPING

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
        object.__setattr__(self, "crest_elevation", crest_elevation)
        object.__setattr__(self, "crest_length", crest_length)
        object.__setattr__(self, "discharge_coefficient", discharge_coefficient)
