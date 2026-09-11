"""Corrected FHWA-HRT-06-138 modern box-inlet relationships."""

import math
from dataclasses import dataclass
from enum import StrEnum

from .._validation import finite, positive_integer
from ..constants import GRAVITATIONAL_ACCELERATION
from ..exceptions import InvalidInputError
from ..geometry.filleted_rectangular import FilletedRectangularGeometry
from ..geometry.rectangular import RectangularGeometry
from ..models.enums import GeometryShape, InletEquationForm
from ..outlet_control.losses import EntranceLossCoefficient
from ..references.models import SourceReference
from .coefficients import InletCoefficients

FHWA_MODERN_BOX_HW_D_MIN = 0.4
FHWA_MODERN_BOX_HW_D_MAX = 2.3
_SIX_INCHES = 0.1524
_TWELVE_INCHES = 0.3048

FHWA_HRT_06_138_REFERENCE = SourceReference(
    source_id="FHWA-HRT-06-138-CORRECTED-TABLES-11-12",
    publication="Effects of Inlet Geometry on Hydraulic Performance of Box Culverts",
    edition="Corrected errata version, 2007",
    locator="Tables 11 and 12, printed pages 85-86",
    url="https://www.fhwa.dot.gov/publications/research/infrastructure/hydraulics/06138/06138.pdf",
    applicability=(
        "Modern reinforced-concrete box inlet configurations represented by Figure 93; "
        "the polynomial is useful only for approximately 0.4 < HW/D < 2.3."
    ),
    notes=(
        "Uses dimensionless discharge Q/(A*sqrt(g*D)) and net opening area when corner "
        "fillets are present. These are not HY-8's recomputed South Dakota-box polynomials."
    ),
)


class BoxWingwallTreatment(StrEnum):
    """Supported Figure 93 wingwall arrangements."""

    FLARED_30 = "30-degree flared"
    EXTENDED_SIDES_0 = "0-degree extended sides"


class BoxCrownTreatment(StrEnum):
    """Supported box-inlet crown-edge treatments."""

    SQUARE_EDGE = "square edge"
    BEVEL_45 = "45-degree straight bevel"
    ROUNDED_8_INCH = "8-inch radius"


@dataclass(frozen=True, slots=True)
class ModernBoxInlet:
    """Physical identity needed to select a corrected Figure 93 inlet relationship."""

    geometry: RectangularGeometry | FilletedRectangularGeometry
    wingwall_treatment: BoxWingwallTreatment
    crown_treatment: BoxCrownTreatment
    barrel_count: int = 1
    headwall_skew_degrees: float = 0.0

    def __post_init__(self) -> None:
        if not isinstance(  # pyright: ignore[reportUnnecessaryIsInstance]
            self.geometry, (RectangularGeometry, FilletedRectangularGeometry)
        ):
            msg = "geometry must be RectangularGeometry or FilletedRectangularGeometry."
            raise InvalidInputError(msg)
        try:
            wingwall = BoxWingwallTreatment(self.wingwall_treatment)
        except (TypeError, ValueError) as exc:
            msg = "wingwall_treatment is not supported."
            raise InvalidInputError(msg) from exc
        try:
            crown = BoxCrownTreatment(self.crown_treatment)
        except (TypeError, ValueError) as exc:
            msg = "crown_treatment is not supported."
            raise InvalidInputError(msg) from exc
        count: int = positive_integer(self.barrel_count, "barrel_count")
        skew: float = finite(self.headwall_skew_degrees, "headwall_skew_degrees")
        if skew < 0.0 or skew > 45.0:
            msg = "headwall_skew_degrees must be between 0 and 45."
            raise InvalidInputError(msg)
        object.__setattr__(self, "wingwall_treatment", wingwall)
        object.__setattr__(self, "crown_treatment", crown)
        object.__setattr__(self, "barrel_count", count)
        object.__setattr__(self, "headwall_skew_degrees", skew)

    @property
    def corner_fillet(self) -> float:
        """Corner-fillet leg length in metres, or zero for a sharp-corner box."""
        if isinstance(self.geometry, FilletedRectangularGeometry):
            return self.geometry.fillet
        return 0.0

    @property
    def span_to_rise_ratio(self) -> float:
        """Nominal clear span-to-rise ratio of one barrel."""
        return self.geometry.span / self.geometry.rise

    @property
    def net_opening_area(self) -> float:
        """Total net opening area across all barrels in square metres."""
        return self.geometry.area_full * self.barrel_count


@dataclass(frozen=True, slots=True)
class ModernBoxInletCoefficients:
    """One corrected FHWA-HRT-06-138 Tables 11 and 12 configuration row."""

    sketch: int
    description: str
    ke: float
    k1: float | None
    m1: float | None
    k2: float
    m2: float
    c: float
    y: float
    polynomial: tuple[float, float, float, float, float, float]
    reference: SourceReference = FHWA_HRT_06_138_REFERENCE

    def form_2_inlet_coefficients(self) -> InletCoefficients:
        """Return the corrected Table 11 Form 2 constants for the general solver."""
        return InletCoefficients(
            name=self.description,
            chart=None,
            scale=None,
            form=InletEquationForm.WEIR,
            k=self.k2,
            m=self.m2,
            c=self.c,
            y=self.y,
            shape=GeometryShape.RECTANGULAR,
            reference=self.reference,
        )

    def entrance_loss_coefficient(self) -> EntranceLossCoefficient:
        """Return the corrected Table 11 outlet-control entrance-loss coefficient."""
        return EntranceLossCoefficient(
            name=self.description,
            ke=self.ke,
            shape=GeometryShape.RECTANGULAR,
            reference=self.reference,
        )


@dataclass(frozen=True, slots=True)
class ModernBoxInletResult:
    """Direct Table 12 polynomial evaluation for a supported modern box inlet."""

    inlet: ModernBoxInlet
    coefficients: ModernBoxInletCoefficients
    discharge: float
    flow_parameter: float
    headwater_ratio: float
    headwater_depth: float


_ROWS: dict[int, ModernBoxInletCoefficients] = {
    1: ModernBoxInletCoefficients(
        sketch=1,
        description="30-degree flared, beveled crown, single barrel",
        ke=0.26,
        k1=0.005,
        m1=1.05,
        k2=0.44,
        m2=0.74,
        c=0.04,
        y=0.48,
        polynomial=(0.163450, 0.127103, 0.256193, -0.131630, 0.025211, -0.001600),
    ),
    2: ModernBoxInletCoefficients(
        sketch=2,
        description="30-degree flared, beveled crown, multiple barrels",
        ke=0.32,
        k1=None,
        m1=None,
        k2=0.47,
        m2=0.68,
        c=0.04,
        y=0.62,
        polynomial=(0.112542, 0.375074, 0.002657, -0.026380, 0.006867, -0.000470),
    ),
    3: ModernBoxInletCoefficients(
        sketch=3,
        description="30-degree flared, beveled crown, 2:1 to 4:1 span/rise",
        ke=0.20,
        k1=None,
        m1=None,
        k2=0.48,
        m2=0.65,
        c=0.041,
        y=0.57,
        polynomial=(0.182681, 0.209471, 0.158774, -0.092970, 0.019381, -0.001310),
    ),
    4: ModernBoxInletCoefficients(
        sketch=4,
        description="30-degree flared, beveled crown, 15-degree skew",
        ke=0.36,
        k1=None,
        m1=None,
        k2=0.69,
        m2=0.49,
        c=0.029,
        y=0.95,
        polynomial=(0.182031, 0.686256, -0.277040, 0.082113, -0.011670, 0.000654),
    ),
    5: ModernBoxInletCoefficients(
        sketch=5,
        description="30-degree flared, beveled crown, 30- to 45-degree skew",
        ke=0.45,
        k1=None,
        m1=None,
        k2=0.69,
        m2=0.49,
        c=0.027,
        y=1.02,
        polynomial=(0.363958, 0.283523, 0.069040, -0.044221, 0.008965, -0.000595),
    ),
    6: ModernBoxInletCoefficients(
        sketch=6,
        description="extended sides, square-edged crown",
        ke=0.79,
        k1=0.055,
        m1=0.68,
        k2=0.55,
        m2=0.64,
        c=0.047,
        y=0.55,
        polynomial=(0.278122, -0.002930, 0.448521, -0.228310, 0.044973, -0.002990),
    ),
    7: ModernBoxInletCoefficients(
        sketch=7,
        description="extended sides, beveled crown, zero or 6-inch fillets",
        ke=0.48,
        k1=None,
        m1=None,
        k2=0.56,
        m2=0.62,
        c=0.045,
        y=0.55,
        polynomial=(0.244295, 0.129322, 0.339620, -0.189660, 0.038635, -0.002600),
    ),
    8: ModernBoxInletCoefficients(
        8,
        "extended sides, beveled crown, multiple barrels",
        0.52,
        None,
        None,
        0.55,
        0.59,
        0.038,
        0.69,
        (0.164261, 0.438420, -0.031280, -0.019190, 0.006288, -0.000460),
    ),
    9: ModernBoxInletCoefficients(
        9,
        "extended sides, beveled crown, 2:1 to 4:1 span/rise",
        0.37,
        None,
        None,
        0.61,
        0.57,
        0.041,
        0.67,
        (0.254968, 0.273934, 0.154712, -0.099110, 0.020506, -0.001350),
    ),
    10: ModernBoxInletCoefficients(
        10,
        "extended sides, rounded crown, zero or 6-inch fillets",
        0.24,
        None,
        None,
        0.56,
        0.62,
        0.038,
        0.67,
        (0.203424, 0.310920, 0.107830, -0.076090, 0.015779, -0.001020),
    ),
    11: ModernBoxInletCoefficients(
        sketch=11,
        description="extended sides, rounded crown, 12-inch fillets",
        ke=0.30,
        k1=None,
        m1=None,
        k2=0.56,
        m2=0.62,
        c=0.038,
        y=0.67,
        polynomial=(0.203424, 0.310920, 0.107830, -0.076090, 0.015779, -0.001020),
    ),
    12: ModernBoxInletCoefficients(
        sketch=12,
        description="extended sides, rounded crown, 12-inch fillets, multiple barrels",
        ke=0.54,
        k1=None,
        m1=None,
        k2=0.55,
        m2=0.60,
        c=0.023,
        y=0.96,
        polynomial=(0.103150, 0.619895, -0.231470, 0.071093, -0.010750, 0.000628),
    ),
    13: ModernBoxInletCoefficients(
        sketch=13,
        description="extended sides, rounded crown, no fillets, 2:1 to 4:1 span/rise",
        ke=0.30,
        k1=None,
        m1=None,
        k2=0.61,
        m2=0.57,
        c=0.033,
        y=0.79,
        polynomial=(0.199715, 0.446748, -0.024140, -0.023340, 0.006761, -0.000480),
    ),
}


def _is_dimension(value: float, expected: float) -> bool:
    return math.isclose(value, expected, rel_tol=0.0, abs_tol=1e-6)


def resolve_modern_box_inlet_coefficients(inlet: ModernBoxInlet) -> ModernBoxInletCoefficients:
    """Resolve the unique corrected coefficient row for a supported physical inlet.

    Unsupported or ambiguous combinations fail closed instead of falling back to a
    visually similar inlet.
    """
    if not isinstance(inlet, ModernBoxInlet):  # pyright: ignore[reportUnnecessaryIsInstance]
        msg = "inlet must be a ModernBoxInlet."
        raise InvalidInputError(msg)
    count: int = inlet.barrel_count
    ratio: float = inlet.span_to_rise_ratio
    skew: float = inlet.headwall_skew_degrees
    fillet: float = inlet.corner_fillet
    regular_single: bool = count == 1 and 1.0 <= ratio < 2.0
    regular_multiple: bool = 2 <= count <= 4 and 1.0 <= ratio < 2.0
    wide_single: bool = count == 1 and 2.0 <= ratio <= 4.0

    if inlet.wingwall_treatment is BoxWingwallTreatment.FLARED_30:
        if inlet.crown_treatment is not BoxCrownTreatment.BEVEL_45:
            msg = "The corrected 30-degree-flared rows require a 45-degree crown bevel."
            raise InvalidInputError(msg)
        if not (_is_dimension(fillet, 0.0) or _is_dimension(fillet, _SIX_INCHES)):
            msg = "The supported field-cast flared rows use zero or 6-inch corner fillets."
            raise InvalidInputError(msg)
        if math.isclose(a=skew, b=15.0, abs_tol=1e-9) and regular_multiple:
            return _ROWS[4]
        if 30.0 <= skew <= 45.0 and regular_multiple:
            return _ROWS[5]
        if not math.isclose(a=skew, b=0.0, abs_tol=1e-9):
            msg = "The requested skew/count/ratio combination is not represented in Figure 93."
            raise InvalidInputError(msg)
        if regular_single:
            return _ROWS[1]
        if regular_multiple:
            return _ROWS[2]
        if wide_single:
            return _ROWS[3]

    if inlet.wingwall_treatment is BoxWingwallTreatment.EXTENDED_SIDES_0:
        if not math.isclose(skew, 0.0, abs_tol=1e-9):
            msg = "The corrected extended-side rows do not represent skewed headwalls."
            raise InvalidInputError(msg)
        if inlet.crown_treatment is BoxCrownTreatment.SQUARE_EDGE:
            if regular_single and _is_dimension(fillet, 0.0):
                return _ROWS[6]
        elif inlet.crown_treatment is BoxCrownTreatment.BEVEL_45:
            if regular_single and (_is_dimension(fillet, 0.0) or _is_dimension(fillet, _SIX_INCHES)):
                return _ROWS[7]
            if regular_multiple and _is_dimension(fillet, _SIX_INCHES):
                return _ROWS[8]
            if wide_single and _is_dimension(fillet, 0.0):
                return _ROWS[9]
        elif inlet.crown_treatment is BoxCrownTreatment.ROUNDED_8_INCH:
            if regular_single and (_is_dimension(fillet, 0.0) or _is_dimension(fillet, _SIX_INCHES)):
                return _ROWS[10]
            if regular_single and _is_dimension(fillet, _TWELVE_INCHES):
                return _ROWS[11]
            if regular_multiple and _is_dimension(fillet, _TWELVE_INCHES):
                return _ROWS[12]
            if wide_single and _is_dimension(fillet, 0.0):
                return _ROWS[13]

    msg = (
        "The inlet's flare, crown, fillet, skew, barrel-count, and span/rise combination "
        "does not match a corrected FHWA-HRT-06-138 Figure 93 row."
    )
    raise InvalidInputError(msg)


def calculate_modern_box_inlet_headwater(
    inlet: ModernBoxInlet,
    discharge: float,
    *,
    g: float = GRAVITATIONAL_ACCELERATION,
) -> ModernBoxInletResult:
    """Evaluate the corrected Table 12 polynomial within its documented useful range."""
    q: float = finite(discharge, "discharge")
    if q <= 0.0:
        msg = "discharge must be strictly positive for the Table 12 fit."
        raise InvalidInputError(msg)
    acceleration: float = finite(g, "g")
    if acceleration <= 0.0:
        msg = "g must be strictly positive."
        raise InvalidInputError(msg)
    coefficients: ModernBoxInletCoefficients = resolve_modern_box_inlet_coefficients(inlet)
    flow_parameter: float = q / (inlet.net_opening_area * math.sqrt(acceleration * inlet.geometry.rise))
    a, b, c, d, e, f = coefficients.polynomial
    ratio: float = a + flow_parameter * (
        b + flow_parameter * (c + flow_parameter * (d + flow_parameter * (e + flow_parameter * f)))
    )
    if not (FHWA_MODERN_BOX_HW_D_MIN < ratio < FHWA_MODERN_BOX_HW_D_MAX):
        msg = "The Table 12 result is outside its documented useful range (approximately 0.4 < HW/D < 2.3)."
        raise InvalidInputError(msg)
    return ModernBoxInletResult(
        inlet=inlet,
        coefficients=coefficients,
        discharge=q,
        flow_parameter=flow_parameter,
        headwater_ratio=ratio,
        headwater_depth=ratio * inlet.geometry.rise,
    )
