"""Culvert crossing hydraulic solver aggregating multiple culvert groups."""

import math
from collections.abc import Callable
from dataclasses import replace

from .._validation import finite
from ..constants import GRAVITATIONAL_ACCELERATION
from ..exceptions import InvalidInputError
from ..inlet_control.coefficients import InletCoefficients
from ..models.barrel import CulvertBarrel
from ..models.crossing import CulvertCrossing
from ..models.enums import ControlType, ConvergenceCalculation
from ..models.group import CulvertGroup
from ..models.results import (
    BarrelHydraulicResult,
    ConvergenceRecord,
    CrossingHydraulicResult,
    FlowRegime,
    GroupHydraulicResult,
)
from ..models.tailwater import (
    TailwaterCondition,
    TailwaterInput,
    TailwaterRatingCurve,
    TailwaterResolution,
    resolve_tailwater,
)
from ..numerical.roots import RootResult, solve_brent
from ..numerical.tolerances import RootTolerances
from ..outlet_control.losses import EntranceLossCoefficient
from ..references.models import SourceReference
from ..roadway.overtopping import RoadwayOvertoppingResult, calculate_roadway_overtopping
from .barrel import solve_barrel_hydraulics
from .config import SolverConfiguration
from .group import solve_group_hydraulics

_HW_ROOT_TOLERANCES = RootTolerances(x_abs=1e-5, x_rel=1e-7)
_DISCHARGE_ROOT_TOLERANCES = RootTolerances(x_abs=1e-5, x_rel=1e-7)


def solve_barrel_discharge_for_headwater(
    barrel: CulvertBarrel,
    headwater_elevation: float,
    tailwater: TailwaterInput,
    *,
    inlet_coefficients: InletCoefficients | None = None,
    entrance_loss_coefficient: float | EntranceLossCoefficient | None = None,
    entrance_loss_source: SourceReference | None = None,
    configuration: SolverConfiguration | None = None,
    g: float = GRAVITATIONAL_ACCELERATION,
) -> float:
    """Solve for single-barrel discharge Q > 0 given a target upstream headwater elevation.

    The optional coefficient arguments and configuration follow the same precedence
    contract as :func:`solve_barrel_hydraulics`. A ``TailwaterInput`` boundary is
    re-resolved at every candidate barrel discharge.

    Returns 0.0 if headwater elevation is at or below the barrel inlet invert.
    """
    discharge, _ = _solve_barrel_discharge_for_headwater(
        barrel,
        headwater_elevation,
        tailwater,
        inlet_coefficients=inlet_coefficients,
        entrance_loss_coefficient=entrance_loss_coefficient,
        entrance_loss_source=entrance_loss_source,
        configuration=configuration,
        g=g,
    )
    return discharge


def solve_barrel_discharge_for_headwater_ratio(
    barrel: CulvertBarrel,
    headwater_ratio: float,
    tailwater: TailwaterInput,
    *,
    inlet_coefficients: InletCoefficients | None = None,
    entrance_loss_coefficient: float | EntranceLossCoefficient | None = None,
    entrance_loss_source: SourceReference | None = None,
    configuration: SolverConfiguration | None = None,
    g: float = GRAVITATIONAL_ACCELERATION,
) -> float:
    """Solve barrel discharge for ``HW/D`` using the common ``TailwaterInput`` contract."""
    ratio: float = finite(headwater_ratio, "headwater_ratio")
    if ratio < 0.0:
        msg = "headwater_ratio must be nonnegative."
        raise InvalidInputError(msg)
    return solve_barrel_discharge_for_headwater(
        barrel,
        headwater_elevation=barrel.inlet_invert + ratio * barrel.geometry.rise,
        tailwater=tailwater,
        inlet_coefficients=inlet_coefficients,
        entrance_loss_coefficient=entrance_loss_coefficient,
        entrance_loss_source=entrance_loss_source,
        configuration=configuration,
        g=g,
    )


def solve_group_discharge_for_headwater(
    group: CulvertGroup,
    headwater_elevation: float,
    tailwater: TailwaterInput,
    *,
    configuration: SolverConfiguration | None = None,
    g: float = GRAVITATIONAL_ACCELERATION,
) -> float:
    """Return group discharge at a given HW using total flow for ``TailwaterInput`` resolution."""
    if not isinstance(group, CulvertGroup):  # pyright: ignore[reportUnnecessaryIsInstance]
        msg = "group must be an instance of CulvertGroup."
        raise InvalidInputError(msg)
    hw_elev: float = finite(headwater_elevation, "headwater_elevation")
    if _is_fixed_tailwater(tailwater):
        barrel_discharge: float = solve_barrel_discharge_for_headwater(
            barrel=group.barrel,
            headwater_elevation=hw_elev,
            tailwater=tailwater,
            configuration=configuration,
            g=g,
        )
        return float(group.quantity) * barrel_discharge
    if hw_elev <= group.barrel.inlet_invert:
        return 0.0

    def headwater_at_discharge(discharge: float) -> float:
        return solve_group_hydraulics(
            group,
            total_discharge=discharge,
            tailwater=tailwater,
            configuration=configuration,
            g=g,
        ).barrel_result.headwater_elevation

    q_scale: float = float(group.quantity) * _barrel_discharge_scale(group.barrel, hw_elev, g)
    return _solve_coupled_discharge(
        target_headwater=hw_elev,
        tailwater=tailwater,
        initial_scale=q_scale,
        headwater_at_discharge=headwater_at_discharge,
    ).root


def solve_crossing_discharge_for_headwater(
    crossing: CulvertCrossing,
    headwater_elevation: float,
    tailwater: TailwaterInput,
    *,
    configuration: SolverConfiguration | None = None,
    g: float = GRAVITATIONAL_ACCELERATION,
) -> float:
    """Return total crossing discharge while coupling flow to ``TailwaterInput`` stage."""
    if not isinstance(crossing, CulvertCrossing):  # pyright: ignore[reportUnnecessaryIsInstance]
        msg = "crossing must be an instance of CulvertCrossing."
        raise InvalidInputError(msg)
    hw_elev: float = finite(headwater_elevation, "headwater_elevation")
    if not _is_fixed_tailwater(tailwater):
        if hw_elev <= crossing.min_headwater_reference_elevation:
            return 0.0

        def headwater_at_discharge(discharge: float) -> float:
            return solve_crossing_hydraulics(
                crossing,
                total_discharge=discharge,
                tailwater=tailwater,
                configuration=configuration,
                g=g,
            ).headwater_elevation

        q_scale: float = sum(
            float(group.quantity) * _barrel_discharge_scale(group.barrel, hw_elev, g) for group in crossing.groups
        )
        return _solve_coupled_discharge(
            target_headwater=hw_elev,
            tailwater=tailwater,
            initial_scale=q_scale,
            headwater_at_discharge=headwater_at_discharge,
        ).root

    tw_elev: float = (
        tailwater.elevation if isinstance(tailwater, TailwaterCondition) else finite(tailwater, "tailwater")
    )
    if crossing.roadway is not None and tw_elev > crossing.roadway.crest_elevation:
        msg = (
            "Submerged roadway overtopping is not supported: tailwater elevation must be at or below the roadway crest."
        )
        raise InvalidInputError(msg)
    total_discharge: float = sum(
        solve_group_discharge_for_headwater(
            group,
            headwater_elevation=hw_elev,
            tailwater=tw_elev,
            configuration=configuration,
            g=g,
        )
        for group in crossing.groups
    )
    if crossing.roadway is not None:
        total_discharge += calculate_roadway_overtopping(
            roadway=crossing.roadway,
            headwater_elevation=hw_elev,
            tailwater_elevation=tw_elev,
        ).discharge
    return total_discharge


def _solve_barrel_discharge_for_headwater(
    barrel: CulvertBarrel,
    headwater_elevation: float,
    tailwater: TailwaterInput,
    *,
    inlet_coefficients: InletCoefficients | None = None,
    entrance_loss_coefficient: float | EntranceLossCoefficient | None = None,
    entrance_loss_source: SourceReference | None = None,
    configuration: SolverConfiguration | None = None,
    g: float = GRAVITATIONAL_ACCELERATION,
) -> tuple[float, RootResult | None]:
    """Return discharge and its root diagnostics for crossing aggregation."""
    hw_elev: float = finite(headwater_elevation, "headwater_elevation")
    if hw_elev <= barrel.inlet_invert:
        return 0.0, None

    hw_depth: float = hw_elev - barrel.inlet_invert
    if hw_depth <= 1e-6:
        return 0.0, None

    q_scale: float = _barrel_discharge_scale(barrel, hw_elev, g)

    if not _is_fixed_tailwater(tailwater):

        def headwater_at_discharge(discharge: float) -> float:
            return solve_barrel_hydraulics(
                barrel=barrel,
                discharge=discharge,
                tailwater=tailwater,
                inlet_coefficients=inlet_coefficients,
                entrance_loss_coefficient=entrance_loss_coefficient,
                entrance_loss_source=entrance_loss_source,
                configuration=configuration,
                g=g,
            ).headwater_elevation

        root_result: RootResult = _solve_coupled_discharge(
            target_headwater=hw_elev,
            tailwater=tailwater,
            initial_scale=q_scale,
            headwater_at_discharge=headwater_at_discharge,
        )
        return root_result.root, root_result

    tw_elev: float
    tw_elev = tailwater.elevation if isinstance(tailwater, TailwaterCondition) else finite(tailwater, "tailwater")
    if hw_elev <= tw_elev:
        return 0.0, None

    q_lo: float = min(1e-5, q_scale * 0.01)
    q_hi: float = max(q_scale, 0.01)

    # Expand q_hi until HW(q_hi) >= headwater_elevation
    for _ in range(40):
        res_hi: BarrelHydraulicResult = solve_barrel_hydraulics(
            barrel=barrel,
            discharge=q_hi,
            tailwater=tw_elev,
            inlet_coefficients=inlet_coefficients,
            entrance_loss_coefficient=entrance_loss_coefficient,
            entrance_loss_source=entrance_loss_source,
            configuration=configuration,
            g=g,
        )
        if res_hi.headwater_elevation >= hw_elev:
            break
        q_hi *= 2.0

    # Contract q_lo until HW(q_lo) <= headwater_elevation
    for _ in range(40):
        res_lo: BarrelHydraulicResult = solve_barrel_hydraulics(
            barrel=barrel,
            discharge=q_lo,
            tailwater=tw_elev,
            inlet_coefficients=inlet_coefficients,
            entrance_loss_coefficient=entrance_loss_coefficient,
            entrance_loss_source=entrance_loss_source,
            configuration=configuration,
            g=g,
        )
        if res_lo.headwater_elevation <= hw_elev:
            break
        q_hi = q_lo
        q_lo *= 0.1
        if q_lo < 1e-12:
            return 0.0, None

    def res_q(q_val: float) -> float:
        res: BarrelHydraulicResult = solve_barrel_hydraulics(
            barrel=barrel,
            discharge=q_val,
            tailwater=tw_elev,
            inlet_coefficients=inlet_coefficients,
            entrance_loss_coefficient=entrance_loss_coefficient,
            entrance_loss_source=entrance_loss_source,
            configuration=configuration,
            g=g,
        )
        return res.headwater_elevation - hw_elev

    root_res: RootResult = solve_brent(
        function=res_q,
        lower=q_lo,
        upper=q_hi,
        tolerances=_DISCHARGE_ROOT_TOLERANCES,
    )
    return root_res.root, root_res


def _is_fixed_tailwater(tailwater: TailwaterInput) -> bool:
    return isinstance(tailwater, TailwaterCondition) or (
        isinstance(tailwater, (float, int)) and not isinstance(tailwater, bool)
    )


def _barrel_discharge_scale(barrel: CulvertBarrel, headwater_elevation: float, g: float) -> float:
    accel: float = finite(g, "g")
    if accel <= 0.0:
        msg = "g must be strictly positive."
        raise InvalidInputError(msg)
    hw_depth: float = max(0.0, headwater_elevation - barrel.inlet_invert)
    return max(0.01, barrel.geometry.area_full * math.sqrt(accel * min(barrel.geometry.rise, hw_depth)))


def _solve_coupled_discharge(
    *,
    target_headwater: float,
    tailwater: TailwaterInput,
    initial_scale: float,
    headwater_at_discharge: Callable[[float], float],
) -> RootResult:
    """Solve ``HW(Q, TW(Q)) - target`` over the boundary's supported flow range."""
    q_scale: float = max(0.01, finite(initial_scale, "initial_scale"))
    q_lo: float = min(1e-5, q_scale * 0.01)
    q_hi: float = max(q_scale, 0.01)
    maximum: float | None = None
    if isinstance(tailwater, TailwaterRatingCurve):
        q_lo = max(q_lo, tailwater.min_discharge)
        maximum = tailwater.max_discharge
        q_hi = min(max(q_hi, q_lo * 2.0), maximum)

    def residual(discharge: float) -> float:
        return headwater_at_discharge(discharge) - target_headwater

    residual_lo: float = residual(q_lo)
    if residual_lo > 0.0:
        if isinstance(tailwater, TailwaterRatingCurve):
            msg = "Target headwater requires discharge below the tailwater rating-curve range."
            raise InvalidInputError(msg)
        for _ in range(40):
            q_hi = q_lo
            q_lo *= 0.1
            residual_lo = residual(q_lo)
            if residual_lo <= 0.0:
                break
        else:
            msg = "Unable to bracket a coupled inverse solution at low discharge."
            raise InvalidInputError(msg)

    residual_hi: float = residual(q_hi)
    for _ in range(40):
        if residual_hi >= 0.0:
            break
        if maximum is not None and q_hi >= maximum:
            msg = "Target headwater requires discharge above the tailwater rating-curve range."
            raise InvalidInputError(msg)
        q_hi = min(q_hi * 2.0, maximum) if maximum is not None else q_hi * 2.0
        residual_hi = residual(q_hi)
    else:
        msg = "Unable to bracket a coupled inverse solution at high discharge."
        raise InvalidInputError(msg)

    return solve_brent(
        function=residual,
        lower=q_lo,
        upper=q_hi,
        tolerances=_DISCHARGE_ROOT_TOLERANCES,
    )


def solve_crossing_hydraulics(
    crossing: CulvertCrossing,
    total_discharge: float,
    tailwater: TailwaterInput,
    *,
    configuration: SolverConfiguration | None = None,
    g: float = GRAVITATIONAL_ACCELERATION,
) -> CrossingHydraulicResult:
    """Solve hydraulics for a multi-group culvert crossing sharing upstream headwater.

    Finds the common upstream headwater elevation HW_elev such that the sum of discharges
    across all culvert groups equals total_discharge:
        sum_i N_i * Q_i(HW_elev, TW_elev) = total_discharge

    Parameters
    ----------
    crossing : CulvertCrossing
        Crossing domain model containing one or more culvert groups.
    total_discharge : float
        Total crossing discharge Q_crossing (m³/s), strictly positive.
    tailwater : TailwaterInput
        Absolute tailwater elevation (m) or a boundary resolved at total crossing discharge.
    configuration : SolverConfiguration | None, optional
        Injectable defaults applied consistently to every group calculation.
    g : float, default=GRAVITATIONAL_ACCELERATION
        Gravitational acceleration (m/s²).

    Returns:
    -------
    CrossingHydraulicResult
        Hydraulic solution for the entire crossing and each constituent culvert group.
    """
    if not isinstance(crossing, CulvertCrossing):  # pyright: ignore[reportUnnecessaryIsInstance]
        msg = "crossing must be an instance of CulvertCrossing."
        raise InvalidInputError(msg)

    q_tot: float = finite(total_discharge, "total_discharge")
    if q_tot <= 0:
        msg = "total_discharge must be strictly positive."
        raise InvalidInputError(msg)

    tailwater_resolution: TailwaterResolution = resolve_tailwater(tailwater=tailwater, discharge=q_tot, g=g)
    tw_elev: float = tailwater_resolution.elevation

    if crossing.roadway is not None and tw_elev > crossing.roadway.crest_elevation:
        msg = (
            "Submerged roadway overtopping is not supported: tailwater elevation must be at or below the roadway crest."
        )
        raise InvalidInputError(msg)

    # Fast path for single-group crossing
    if crossing.num_groups == 1 and crossing.roadway is None:
        g0: CulvertGroup = crossing.groups[0]
        g_res0: GroupHydraulicResult = solve_group_hydraulics(
            group=g0,
            total_discharge=q_tot,
            tailwater=tw_elev,
            configuration=configuration,
            g=g,
        )
        barrel_result: BarrelHydraulicResult = replace(
            g_res0.barrel_result,
            tailwater_resolution=tailwater_resolution,
        )
        g_res0 = replace(
            g_res0,
            barrel_result=barrel_result,
            tailwater_resolution=tailwater_resolution,
        )
        return CrossingHydraulicResult(
            headwater_elevation=g_res0.barrel_result.headwater_elevation,
            total_discharge=q_tot,
            tailwater_elevation=tw_elev,
            group_results=(g_res0,),
            tailwater_resolution=tailwater_resolution,
        )

    # Multi-group crossing: solve common HW elevation
    def crossing_discharge_at_hw(hw: float) -> float:
        return solve_crossing_discharge_for_headwater(
            crossing,
            headwater_elevation=hw,
            tailwater=tw_elev,
            configuration=configuration,
            g=g,
        )

    # Bracket HW elevation:
    min_bound: float = max(crossing.min_headwater_reference_elevation, tw_elev)
    hw_lo: float = min_bound + 1e-4
    hw_hi: float = max(crossing.max_inlet_invert, tw_elev) + 1.0

    for _ in range(40):
        if crossing_discharge_at_hw(hw_hi) >= q_tot:
            break
        hw_hi += 1.0

    for _ in range(40):
        if crossing_discharge_at_hw(hw_lo) <= q_tot:
            break
        hw_lo = (hw_lo + min_bound) / 2.0

    def hw_residual(hw_val: float) -> float:
        return crossing_discharge_at_hw(hw_val) - q_tot

    hw_root: RootResult = solve_brent(
        function=hw_residual,
        lower=hw_lo,
        upper=hw_hi,
        tolerances=_HW_ROOT_TOLERANCES,
    )
    gov_hw_elev = hw_root.root

    # Build group results at solved headwater elevation
    group_results: list[GroupHydraulicResult] = []
    for grp in crossing.groups:
        q_b, discharge_root = _solve_barrel_discharge_for_headwater(
            barrel=grp.barrel,
            headwater_elevation=gov_hw_elev,
            tailwater=tw_elev,
            configuration=configuration,
            g=g,
        )
        q_grp: float = float(grp.quantity) * q_b
        if q_b > 0:
            b_res: BarrelHydraulicResult = solve_barrel_hydraulics(
                barrel=grp.barrel,
                discharge=q_b,
                tailwater=tw_elev,
                configuration=configuration,
                g=g,
            )
            b_res = replace(b_res, tailwater_resolution=tailwater_resolution)
        else:
            # Preserve an exact dry/inactive result instead of fabricating a tiny flow.
            b_res = BarrelHydraulicResult(
                barrel=grp.barrel,
                discharge=0.0,
                headwater_elevation=gov_hw_elev,
                headwater_depth=max(0.0, gov_hw_elev - grp.barrel.inlet_invert),
                tailwater_elevation=tw_elev,
                tailwater_depth=max(0.0, tw_elev - grp.barrel.outlet_invert),
                regime=FlowRegime.INACTIVE,
                control_type=ControlType.NONE,
                velocity_outlet=0.0,
                outlet_depth=0.0,
                critical_depth=0.0,
                normal_depth=None,
                profile_curve=None,
                tailwater_resolution=tailwater_resolution,
            )

        g_res = GroupHydraulicResult(
            group=grp,
            total_discharge=q_grp,
            barrel_discharge=q_b,
            barrel_result=b_res,
            discharge_convergence=(
                None
                if discharge_root is None
                else ConvergenceRecord(
                    calculation=ConvergenceCalculation.BARREL_DISCHARGE,
                    result=discharge_root,
                )
            ),
            tailwater_resolution=tailwater_resolution,
        )
        group_results.append(g_res)

    roadway_result: RoadwayOvertoppingResult | None = (
        None
        if crossing.roadway is None
        else calculate_roadway_overtopping(
            roadway=crossing.roadway,
            headwater_elevation=gov_hw_elev,
            tailwater_elevation=tw_elev,
        )
    )

    return CrossingHydraulicResult(
        headwater_elevation=gov_hw_elev,
        total_discharge=q_tot,
        tailwater_elevation=tw_elev,
        group_results=tuple(group_results),
        headwater_convergence=ConvergenceRecord(
            calculation=ConvergenceCalculation.CROSSING_HEADWATER,
            result=hw_root,
        ),
        roadway_result=roadway_result,
        tailwater_resolution=tailwater_resolution,
    )
