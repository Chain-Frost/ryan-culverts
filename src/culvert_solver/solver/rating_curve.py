"""Rating curve generator for culvert barrels, groups, and crossings."""

from collections.abc import Sequence
from dataclasses import dataclass

from .._validation import finite, positive_integer
from ..constants import GRAVITATIONAL_ACCELERATION
from ..exceptions import InvalidInputError
from ..inlet_control.coefficients import InletCoefficients
from ..models.barrel import CulvertBarrel
from ..models.crossing import CulvertCrossing
from ..models.enums import ControlType
from ..models.results import FlowRegime, HydraulicWarning
from ..models.tailwater import TailwaterCondition
from ..outlet_control.losses import EntranceLossCoefficient
from .barrel import solve_barrel_hydraulics
from .config import SolverConfiguration
from .crossing import solve_crossing_hydraulics


@dataclass(frozen=True, slots=True)
class RatingCurvePoint:
    """Hydraulic performance metrics at a single operating discharge."""

    discharge: float
    headwater_elevation: float
    headwater_depth: float
    tailwater_elevation: float
    tailwater_depth: float
    outlet_velocity: float
    control_type: ControlType
    regime: FlowRegime
    warnings: tuple[HydraulicWarning, ...] = ()


@dataclass(frozen=True, slots=True)
class RatingCurveResult:
    """Complete discharge rating curve across multiple operating points."""

    points: tuple[RatingCurvePoint, ...]
    min_discharge: float
    max_discharge: float


def generate_discharge_range(
    min_discharge: float,
    max_discharge: float,
    num_points: int = 11,
) -> tuple[float, ...]:
    """Generate linearly spaced positive discharges for rating curve evaluation.

    Parameters
    ----------
    min_discharge : float
        Minimum discharge Q_min (m³/s), strictly positive.
    max_discharge : float
        Maximum discharge Q_max (m³/s), strictly greater than min_discharge.
    num_points : int, default=11
        Number of points in sequence, must be at least 2.

    Returns
    -------
    tuple[float, ...]
        Linearly spaced sequence of discharges.
    """
    q_min: float = finite(min_discharge, "min_discharge")
    if q_min <= 0:
        raise InvalidInputError("min_discharge must be strictly positive.")

    q_max: float = finite(max_discharge, "max_discharge")
    if q_max <= q_min:
        raise InvalidInputError("max_discharge must be strictly greater than min_discharge.")

    n: int = positive_integer(num_points, "num_points")
    if n < 2:
        raise InvalidInputError("num_points must be at least 2.")

    step = (q_max - q_min) / float(n - 1)
    return tuple(q_min + i * step for i in range(n))


def generate_barrel_rating_curve(
    barrel: CulvertBarrel,
    discharges: Sequence[float],
    tailwater: TailwaterCondition | float,
    *,
    inlet_coefficients: InletCoefficients | None = None,
    entrance_loss_coefficient: float | EntranceLossCoefficient | None = None,
    configuration: SolverConfiguration | None = None,
    g: float = GRAVITATIONAL_ACCELERATION,
) -> RatingCurveResult:
    """Generate a rating curve for a single culvert barrel across specified discharges.

    Parameters
    ----------
    barrel : CulvertBarrel
        Culvert barrel domain model.
    discharges : Sequence[float]
        Sequence of strictly positive flow rates Q (m³/s), ordered monotonically.
    tailwater : TailwaterCondition | float
        Tailwater boundary condition or elevation (m).
    inlet_coefficients : InletCoefficients | None, optional
        Inlet control regression constants.
    entrance_loss_coefficient : float | EntranceLossCoefficient | None, optional
        Inlet entrance loss coefficient Ke.
    configuration : SolverConfiguration | None, optional
        Injectable defaults applied consistently to every rating point.
    g : float, default=GRAVITATIONAL_ACCELERATION
        Gravitational acceleration (m/s²).

    Returns
    -------
    RatingCurveResult
        Rating curve points sorted by discharge.
    """
    if not discharges:
        raise InvalidInputError("discharges must contain at least one value.")

    pts: list[RatingCurvePoint] = []
    for q_raw in discharges:
        q = finite(q_raw, "discharge")
        if q <= 0:
            raise InvalidInputError("all discharge values must be strictly positive.")

        res = solve_barrel_hydraulics(
            barrel=barrel,
            discharge=q,
            tailwater=tailwater,
            inlet_coefficients=inlet_coefficients,
            entrance_loss_coefficient=entrance_loss_coefficient,
            configuration=configuration,
            g=g,
        )

        pt = RatingCurvePoint(
            discharge=q,
            headwater_elevation=res.headwater_elevation,
            headwater_depth=res.headwater_depth,
            tailwater_elevation=res.tailwater_elevation,
            tailwater_depth=res.tailwater_depth,
            outlet_velocity=res.velocity_outlet,
            control_type=res.control_type,
            regime=res.regime,
            warnings=res.warnings,
        )
        pts.append(pt)

    sorted_pts = tuple(sorted(pts, key=lambda p: p.discharge))
    return RatingCurveResult(
        points=sorted_pts,
        min_discharge=sorted_pts[0].discharge,
        max_discharge=sorted_pts[-1].discharge,
    )


def generate_crossing_rating_curve(
    crossing: CulvertCrossing,
    discharges: Sequence[float],
    tailwater: TailwaterCondition | float,
    *,
    configuration: SolverConfiguration | None = None,
    g: float = GRAVITATIONAL_ACCELERATION,
) -> RatingCurveResult:
    """Generate a rating curve for a multi-group road crossing across specified discharges.

    Parameters
    ----------
    crossing : CulvertCrossing
        Culvert crossing domain model.
    discharges : Sequence[float]
        Sequence of strictly positive total crossing discharges Q (m³/s).
    tailwater : TailwaterCondition | float
        Tailwater boundary condition or elevation (m).
    configuration : SolverConfiguration | None, optional
        Injectable defaults applied consistently to every crossing calculation.
    g : float, default=GRAVITATIONAL_ACCELERATION
        Gravitational acceleration (m/s²).

    Returns
    -------
    RatingCurveResult
        Rating curve points sorted by discharge.
    """
    if not discharges:
        raise InvalidInputError("discharges must contain at least one value.")

    tw_elev: float
    if isinstance(tailwater, TailwaterCondition):
        tw_elev = tailwater.elevation
    else:
        tw_elev = finite(tailwater, "tailwater")

    tw_depth = max(0.0, tw_elev - crossing.min_outlet_invert)

    pts: list[RatingCurvePoint] = []
    for q_raw in discharges:
        q = finite(q_raw, "discharge")
        if q <= 0:
            raise InvalidInputError("all discharge values must be strictly positive.")

        c_res = solve_crossing_hydraulics(
            crossing=crossing,
            total_discharge=q,
            tailwater=tw_elev,
            configuration=configuration,
            g=g,
        )

        # Report the maximum active outlet velocity. A multi-group point is explicitly
        # mixed when active groups do not share one control or regime.
        active_results = tuple(
            group_result
            for group_result in c_res.group_results
            if group_result.barrel_discharge > 0.0
        )
        v_out_max = max(
            group_result.barrel_result.velocity_outlet for group_result in active_results
        )
        control_types = {result.barrel_result.control_type for result in active_results}
        regimes = {result.barrel_result.regime for result in active_results}
        control_type = next(iter(control_types)) if len(control_types) == 1 else ControlType.MIXED
        regime = next(iter(regimes)) if len(regimes) == 1 else FlowRegime.MIXED
        point_warnings = tuple(
            dict.fromkeys(
                warning
                for group_result in active_results
                for warning in group_result.barrel_result.warnings
            )
        )

        hw_depth = c_res.headwater_elevation - crossing.min_inlet_invert

        pt = RatingCurvePoint(
            discharge=q,
            headwater_elevation=c_res.headwater_elevation,
            headwater_depth=hw_depth,
            tailwater_elevation=tw_elev,
            tailwater_depth=tw_depth,
            outlet_velocity=v_out_max,
            control_type=control_type,
            regime=regime,
            warnings=point_warnings,
        )
        pts.append(pt)

    sorted_pts = tuple(sorted(pts, key=lambda p: p.discharge))
    return RatingCurveResult(
        points=sorted_pts,
        min_discharge=sorted_pts[0].discharge,
        max_discharge=sorted_pts[-1].discharge,
    )
