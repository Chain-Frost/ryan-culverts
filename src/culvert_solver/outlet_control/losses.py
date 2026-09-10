"""Entrance, friction, and exit loss definitions and calculations for outlet control."""

from dataclasses import dataclass

from .._validation import finite
from ..exceptions import InvalidInputError
from ..geometry.circular import CircularGeometry
from ..geometry.filleted_rectangular import FilletedRectangularGeometry
from ..geometry.rectangular import RectangularGeometry
from ..hydraulics.primitives import friction_head_loss, minor_head_loss
from ..models.barrel import CulvertBarrel
from ..models.enums import ExitLossSelectionBasis, GeometryShape
from ..references.models import SourceReference

_HDS5_TABLE_C2_REF = SourceReference(
    source_id="FHWA-HDS5-2012-TABLE-C2",
    publication="Hydraulic Design of Highway Culverts",
    edition="Third Edition, April 2012",
    locator="Appendix C, Table C.2: Entrance Loss Coefficients (also Table 3.2)",
    url="https://www.fhwa.dot.gov/engineering/hydraulics/pubs/12026/hif12026.pdf",
    applicability="Entrance loss coefficient Ke for pipe and box culverts in outlet control.",
    notes="Adopted from FHWA / Bureau of Public Roads design guidance.",
)

_HDS5_SECTION_314_EXIT_REF = SourceReference(
    source_id="FHWA-HDS5-2012-EQ-3.4C",
    publication="Hydraulic Design of Highway Culverts",
    edition="Third Edition, April 2012",
    locator="Section 3.1.4, Equation 3.4c: Exit Loss",
    url="https://www.fhwa.dot.gov/engineering/hydraulics/pubs/12026/hif12026.pdf",
    applicability=("Exit loss ho = 1.0 * V^2 / (2*g) for culverts discharging into a reservoir or pool."),
    notes="Exit loss coefficient Ko = 1.0 for sudden deceleration to zero receiving velocity.",
)

STANDARD_EXIT_LOSS_COEFFICIENT: float = 1.0


@dataclass(frozen=True, slots=True)
class EntranceLossCoefficient:
    """Entrance loss coefficient Ke and source metadata for culvert outlet control."""

    name: str
    ke: float
    shape: GeometryShape = GeometryShape.ANY
    reference: SourceReference = _HDS5_TABLE_C2_REF

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise InvalidInputError("name must be nonempty text.")
        ke_val: float = finite(self.ke, "ke")
        if ke_val < 0:
            raise InvalidInputError("ke must be nonnegative.")
        try:
            shape_val = GeometryShape(self.shape)
        except (TypeError, ValueError) as exc:
            raise InvalidInputError("shape must be GeometryShape.CIRCULAR, RECTANGULAR, or ANY.") from exc
        object.__setattr__(self, "ke", ke_val)
        object.__setattr__(self, "shape", shape_val)


@dataclass(frozen=True, slots=True)
class ExitLossSelection:
    """Resolved exit-loss coefficient with selection basis and source provenance."""

    ko: float
    name: str
    basis: ExitLossSelectionBasis
    source: SourceReference | None

    def __post_init__(self) -> None:
        ko_val = finite(self.ko, "ko")
        if ko_val < 0:
            raise InvalidInputError("ko must be nonnegative.")
        if not self.name.strip():
            raise InvalidInputError("name must be nonempty text.")
        if self.basis is ExitLossSelectionBasis.HDS5_STANDARD and self.source is None:
            raise InvalidInputError("The HDS-5 standard exit loss must identify its source.")
        object.__setattr__(self, "ko", ko_val)

    @property
    def used_default(self) -> bool:
        """Return whether the HDS-5 reservoir/pool assumption supplied the value."""
        return self.basis is ExitLossSelectionBasis.HDS5_STANDARD


STANDARD_EXIT_LOSS_SELECTION = ExitLossSelection(
    ko=STANDARD_EXIT_LOSS_COEFFICIENT,
    name="HDS-5 reservoir or pool exit loss",
    basis=ExitLossSelectionBasis.HDS5_STANDARD,
    source=_HDS5_SECTION_314_EXIT_REF,
)


def resolve_exit_loss_coefficient(override: float | None = None) -> ExitLossSelection:
    """Resolve Ko from an optional numeric override or the sourced HDS-5 default."""
    if override is None:
        return STANDARD_EXIT_LOSS_SELECTION
    ko: float = finite(override, "exit_loss_coefficient")
    if ko < 0:
        raise InvalidInputError("exit_loss_coefficient must be nonnegative.")
    return ExitLossSelection(
        ko=ko,
        name="User-specified Ko",
        basis=ExitLossSelectionBasis.USER_OVERRIDE,
        source=None,
    )


def validate_entrance_loss_shape(barrel: CulvertBarrel, coefficient: EntranceLossCoefficient) -> None:
    """Reject an entrance-loss coefficient for a different geometry family."""
    if isinstance(barrel.geometry, CircularGeometry):
        barrel_shape: GeometryShape = GeometryShape.CIRCULAR
    elif isinstance(barrel.geometry, (RectangularGeometry, FilletedRectangularGeometry)):
        barrel_shape = GeometryShape.RECTANGULAR
    else:
        barrel_shape = GeometryShape.ANY
    if coefficient.shape not in (GeometryShape.ANY, barrel_shape):
        raise InvalidInputError(
            f"Entrance-loss coefficient for {coefficient.shape.value!r} geometry cannot be "
            f"used with {barrel_shape.value!r} geometry."
        )


# Circular concrete pipe entrance loss coefficients (HDS-5 Table C.2)
PIPE_CONCRETE_SQUARE_EDGE = EntranceLossCoefficient(
    name="Pipe, Concrete: Headwall or headwall and wingwalls, square-edge",
    ke=0.5,
    shape=GeometryShape.CIRCULAR,
)
PIPE_CONCRETE_SOCKET_END = EntranceLossCoefficient(
    name="Pipe, Concrete: Headwall or headwall and wingwalls, socket end (groove-end)",
    ke=0.2,
    shape=GeometryShape.CIRCULAR,
)
PIPE_CONCRETE_ROUNDED = EntranceLossCoefficient(
    name="Pipe, Concrete: Headwall or headwall and wingwalls, rounded (radius = 1/12 D)",
    ke=0.2,
    shape=GeometryShape.CIRCULAR,
)
PIPE_CONCRETE_PROJECTING_SQUARE = EntranceLossCoefficient(
    name="Pipe, Concrete: Projecting from fill, square cut end",
    ke=0.5,
    shape=GeometryShape.CIRCULAR,
)
PIPE_CONCRETE_PROJECTING_SOCKET = EntranceLossCoefficient(
    name="Pipe, Concrete: Projecting from fill, socket end",
    ke=0.2,
    shape=GeometryShape.CIRCULAR,
)
PIPE_CONCRETE_MITERED = EntranceLossCoefficient(
    name="Pipe, Concrete: Mitered to conform to fill slope",
    ke=0.7,
    shape=GeometryShape.CIRCULAR,
)
PIPE_CONCRETE_BEVELED = EntranceLossCoefficient(
    name="Pipe, Concrete: Beveled edges, 33.7 deg or 45 deg bevels",
    ke=0.2,
    shape=GeometryShape.CIRCULAR,
)

# Circular corrugated metal pipe entrance loss coefficients (HDS-5 Table C.2)
PIPE_CMP_PROJECTING = EntranceLossCoefficient(
    name="Pipe, CMP: Projecting from fill (no headwall)",
    ke=0.9,
    shape=GeometryShape.CIRCULAR,
)
PIPE_CMP_HEADWALL = EntranceLossCoefficient(
    name="Pipe, CMP: Headwall or headwall and wingwalls square-edge",
    ke=0.5,
    shape=GeometryShape.CIRCULAR,
)
PIPE_CMP_MITERED = EntranceLossCoefficient(
    name="Pipe, CMP: Mitered to conform to fill slope",
    ke=0.7,
    shape=GeometryShape.CIRCULAR,
)
PIPE_CMP_END_SECTION = EntranceLossCoefficient(
    name="Pipe, CMP: End-section conforming to fill slope",
    ke=0.5,
    shape=GeometryShape.CIRCULAR,
)
PIPE_CMP_BEVELED = EntranceLossCoefficient(
    name="Pipe, CMP: Beveled edges, 33.7 deg or 45 deg bevels",
    ke=0.2,
    shape=GeometryShape.CIRCULAR,
)

# Reinforced concrete box culvert entrance loss coefficients (HDS-5 Table C.2)
BOX_CONCRETE_FLARED_WINGWALLS_30_75 = EntranceLossCoefficient(
    name="Box, RC: Wingwalls at 30 deg to 75 deg to barrel, square top edge",
    ke=0.4,
    shape=GeometryShape.RECTANGULAR,
)
BOX_CONCRETE_FLARED_WINGWALLS_ROUNDED = EntranceLossCoefficient(
    name="Box, RC: Wingwalls at 30 deg to 75 deg to barrel, crown edge rounded to radius = 1/12 D",
    ke=0.2,
    shape=GeometryShape.RECTANGULAR,
)
BOX_CONCRETE_PARALLEL_WINGWALLS_0 = EntranceLossCoefficient(
    name="Box, RC: Wingwalls parallel (extension of sides), square top edge",
    ke=0.7,
    shape=GeometryShape.RECTANGULAR,
)
BOX_CONCRETE_WINGWALLS_10_25 = EntranceLossCoefficient(
    name="Box, RC: Wingwalls at 10 deg to 25 deg to barrel, square top edge",
    ke=0.5,
    shape=GeometryShape.RECTANGULAR,
)
BOX_CONCRETE_HEADWALL_SQUARE = EntranceLossCoefficient(
    name="Box, RC: Headwall parallel to embankment (no wingwalls), square edges on 3 sides",
    ke=0.5,
    shape=GeometryShape.RECTANGULAR,
)
BOX_CONCRETE_HEADWALL_ROUNDED = EntranceLossCoefficient(
    name="Box, RC: Headwall parallel to embankment (no wingwalls), rounded edges (radius = 1/12 D)",
    ke=0.2,
    shape=GeometryShape.RECTANGULAR,
)


def calculate_entrance_loss(velocity_head: float, ke: float) -> float:
    """Entrance loss he = Ke * hv in metres."""
    return minor_head_loss(ke, velocity_head)


def calculate_friction_loss(length: float, friction_slope: float) -> float:
    """Friction loss hf = L * Sf in metres."""
    return friction_head_loss(length, friction_slope)


def calculate_exit_loss(
    velocity_head: float,
    ko: float = STANDARD_EXIT_LOSS_COEFFICIENT,
) -> float:
    """Exit loss ho = Ko * hv in metres."""
    return minor_head_loss(ko, velocity_head)


def calculate_total_head_loss(
    entrance_loss: float,
    friction_loss: float,
    exit_loss: float,
) -> float:
    """Total head loss H = he + hf + ho in metres."""
    he: float = finite(entrance_loss, "entrance_loss")
    if he < 0:
        raise InvalidInputError("entrance_loss must be nonnegative.")
    hf: float = finite(friction_loss, "friction_loss")
    if hf < 0:
        raise InvalidInputError("friction_loss must be nonnegative.")
    ho: float = finite(exit_loss, "exit_loss")
    if ho < 0:
        raise InvalidInputError("exit_loss must be nonnegative.")
    return he + hf + ho
