"""Inlet control headwater solver combining unsubmerged, transition, and submerged flow."""

from dataclasses import dataclass

from .._validation import finite
from ..constants import GRAVITATIONAL_ACCELERATION
from ..exceptions import InvalidInputError
from ..geometry.circular import CircularGeometry
from ..geometry.filleted_rectangular import FilletedRectangularGeometry
from ..geometry.rectangular import RectangularGeometry
from ..hydraulics.critical import CriticalDepthResult, calculate_critical_depth
from ..models.barrel import CulvertBarrel
from ..models.enums import GeometryShape, HydraulicWarningCode, InletEquationForm
from ..models.materials import CONCRETE, CONCRETE_BOX, CONCRETE_PIPE, CORRUGATED_STEEL
from ..models.results import FlowRegime, HydraulicWarning
from .coefficients import (
    BOX_CONCRETE_FLARED_WINGWALLS_30_75,
    CIRCULAR_CMP_HEADWALL,
    CIRCULAR_CONCRETE_SQUARE_EDGE,
    InletCoefficients,
)
from .fhwa import (
    KU_SI,
    Q_STAR_SUBMERGED_THRESHOLD,
    Q_STAR_UNSUBMERGED_LIMIT,
    flow_parameter,
    submerged_headwater,
    transition_headwater,
    unsubmerged_headwater_form_1,
    unsubmerged_headwater_form_2,
)

# HDS-5 Section 3.5.2, printed page 3.39. Values above the laboratory
# curve range use a separately fitted general-orifice extension in HY-8.
HDS5_LABORATORY_HW_D_MAX: float = 3.0

# HY-8 8.0.1.2 comparison reports show a version-specific marker near this
# ratio. The local threshold is deliberately a conservative review boundary,
# not a claim about HY-8's cross-version behaviour.
EXTREME_HEADWATER_RATIO: float = 10.0


@dataclass(frozen=True, slots=True)
class InletControlResult:
    """Inlet control headwater evaluation result."""

    headwater_depth: float
    headwater_elevation: float
    regime: FlowRegime
    discharge: float
    flow_parameter: float
    headwater_ratio: float
    critical_depth: float | None = None
    specific_energy: float | None = None
    warnings: tuple[HydraulicWarning, ...] = ()


def _high_head_warnings(headwater_ratio: float) -> tuple[HydraulicWarning, ...]:
    """Return stable review warnings for results above HDS-5's laboratory curve range."""
    if headwater_ratio <= HDS5_LABORATORY_HW_D_MAX:
        return ()

    warnings: list[HydraulicWarning] = [
        HydraulicWarning(
            code=HydraulicWarningCode.INLET_CONTROL_HIGH_HEAD_EXTENSION,
            message=(
                "Inlet-control HW/D exceeds the HDS-5 laboratory curve range of 3.0; "
                "the direct Appendix A.3 orifice relationship is an extrapolated "
                "project method and requires engineering review."
            ),
        )
    ]
    if headwater_ratio > EXTREME_HEADWATER_RATIO:
        warnings.append(
            HydraulicWarning(
                code=HydraulicWarningCode.INLET_CONTROL_EXTREME_HEADWATER,
                message=(
                    "Inlet-control HW/D exceeds the project's extreme-headwater review "
                    "threshold of 10.0; do not treat this result as ordinarily validated."
                ),
            )
        )
    return tuple(warnings)


def _default_coefficients_for_barrel(barrel: CulvertBarrel) -> InletCoefficients:
    """Select standard default inlet coefficients based on geometry and material."""
    if isinstance(barrel.geometry, CircularGeometry):
        if barrel.material == CORRUGATED_STEEL:
            return CIRCULAR_CMP_HEADWALL
        if barrel.material in {CONCRETE, CONCRETE_PIPE}:
            return CIRCULAR_CONCRETE_SQUARE_EDGE
        msg = (
            "No default inlet coefficients exist for this circular barrel material; "
            "provide inlet_coefficients explicitly."
        )
        raise InvalidInputError(msg)
    if isinstance(barrel.geometry, (RectangularGeometry, FilletedRectangularGeometry)):
        if barrel.material in {CONCRETE, CONCRETE_BOX}:
            return BOX_CONCRETE_FLARED_WINGWALLS_30_75
        msg = (
            "No default inlet coefficients exist for this rectangular barrel material; "
            "provide inlet_coefficients explicitly."
        )
        raise InvalidInputError(msg)
    msg = "No default inlet coefficients exist for this geometry; provide them explicitly."
    raise InvalidInputError(msg)


def _validate_coefficient_shape(barrel: CulvertBarrel, coefficients: InletCoefficients) -> None:
    """Reject empirical coefficients that do not apply to the barrel geometry family."""
    if isinstance(barrel.geometry, CircularGeometry):
        barrel_shape: GeometryShape = GeometryShape.CIRCULAR
    elif isinstance(barrel.geometry, (RectangularGeometry, FilletedRectangularGeometry)):
        barrel_shape = GeometryShape.RECTANGULAR
    else:
        barrel_shape = GeometryShape.ANY
    if coefficients.shape not in (GeometryShape.ANY, barrel_shape):
        msg = (
            f"Inlet coefficients for {coefficients.shape.value!r} geometry cannot be used "
            f"with {barrel_shape.value!r} geometry."
        )
        raise InvalidInputError(msg)


def calculate_inlet_control_headwater(
    barrel: CulvertBarrel,
    discharge: float,
    *,
    coefficients: InletCoefficients | None = None,
    g: float = GRAVITATIONAL_ACCELERATION,
) -> InletControlResult:
    """Calculate the upstream headwater depth and elevation under inlet control.

    Evaluates Form 1 or Form 2 unsubmerged weir flow, submerged orifice flow,
    or the project's cubic-Hermite implementation of the HDS-5 requirement for a
    smooth transition tangent to both bounding curves. This is not HY-8's fitted
    fifth-degree polynomial method.
    """
    q: float = finite(discharge, "discharge")
    if q < 0:
        msg = "discharge must be nonnegative."
        raise InvalidInputError(msg)
    accel: float = finite(g, "g")
    if accel <= 0:
        msg = "g must be strictly positive."
        raise InvalidInputError(msg)

    coeffs: InletCoefficients = coefficients or barrel.inlet_coefficients or _default_coefficients_for_barrel(barrel)
    _validate_coefficient_shape(barrel, coeffs)

    rise: float = barrel.geometry.rise
    area: float = barrel.geometry.area_full
    slope: float = barrel.slope

    q_star: float = flow_parameter(q, area, rise)

    if q == 0.0:
        return InletControlResult(
            headwater_depth=0.0,
            headwater_elevation=barrel.inlet_invert,
            regime=FlowRegime.INLET_CONTROL_UNSUBMERGED,
            discharge=0.0,
            flow_parameter=0.0,
            headwater_ratio=0.0,
            critical_depth=0.0,
            specific_energy=0.0,
        )

    # 1. Unsubmerged weir flow (q* <= 3.5)
    if q_star <= Q_STAR_UNSUBMERGED_LIMIT:
        regime: FlowRegime = FlowRegime.INLET_CONTROL_UNSUBMERGED
        if coeffs.form is InletEquationForm.SPECIFIC_HEAD:
            crit_res: CriticalDepthResult = calculate_critical_depth(barrel.geometry, q, g=accel)
            hc_d: float = crit_res.specific_energy / rise
            hwi_d: float = unsubmerged_headwater_form_1(q_star, hc_d, slope, coeffs)
            yc_val: float | None = crit_res.depth
            ec_val: float | None = crit_res.specific_energy
        else:
            hwi_d = unsubmerged_headwater_form_2(q_star, coeffs)
            yc_val = None
            ec_val = None

    # 2. Submerged orifice flow (q* >= 4.0)
    elif q_star >= Q_STAR_SUBMERGED_THRESHOLD:
        regime = FlowRegime.INLET_CONTROL_SUBMERGED
        hwi_d = submerged_headwater(q_star, slope, coeffs)
        yc_val = None
        ec_val = None

    # 3. Transition zone (3.5 < q* < 4.0)
    else:
        # Evaluate unsubmerged headwater at q* = 3.5
        if coeffs.form is InletEquationForm.SPECIFIC_HEAD:
            # Flow at q* = 3.5 in SI units
            q1: float = (3.5 * area * (rise**0.5)) / 1.811
            crit_res1: CriticalDepthResult = calculate_critical_depth(barrel.geometry, q1, g=accel)
            hwi_d1: float = unsubmerged_headwater_form_1(3.5, crit_res1.specific_energy / rise, slope, coeffs)
            critical_area: float = barrel.geometry.area(crit_res1.depth)
            discharge_per_q_star: float = area * (rise**0.5) / KU_SI
            critical_head_tangent: float = q1 * discharge_per_q_star / (accel * critical_area**2 * rise)
            unsubmerged_tangent: float = critical_head_tangent + coeffs.k * coeffs.m * (
                Q_STAR_UNSUBMERGED_LIMIT ** (coeffs.m - 1.0)
            )
        else:
            hwi_d1 = unsubmerged_headwater_form_2(3.5, coeffs)
            unsubmerged_tangent = coeffs.k * coeffs.m * (Q_STAR_UNSUBMERGED_LIMIT ** (coeffs.m - 1.0))

        # Evaluate submerged headwater at q* = 4.0
        hwi_d2: float = submerged_headwater(4.0, slope, coeffs)
        submerged_tangent: float = 2.0 * coeffs.c * Q_STAR_SUBMERGED_THRESHOLD

        hwi_d = transition_headwater(
            q_star=q_star,
            hwi_d_unsub_at_limit=hwi_d1,
            hwi_d_sub_at_threshold=hwi_d2,
            unsubmerged_tangent=unsubmerged_tangent,
            submerged_tangent=submerged_tangent,
        )
        regime = FlowRegime.INLET_CONTROL_TRANSITION
        yc_val = None
        ec_val = None

    hwi: float = hwi_d * rise
    return InletControlResult(
        headwater_depth=hwi,
        headwater_elevation=barrel.inlet_invert + hwi,
        regime=regime,
        discharge=q,
        flow_parameter=q_star,
        headwater_ratio=hwi_d,
        critical_depth=yc_val,
        specific_energy=ec_val,
        warnings=_high_head_warnings(hwi_d),
    )
