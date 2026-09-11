"""Culvert crossing hydraulic solver aggregating multiple culvert groups."""

import math
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
    tailwater: TailwaterCondition | float,
    *,
    inlet_coefficients: InletCoefficients | None = None,
    entrance_loss_coefficient: float | EntranceLossCoefficient | None = None,
    entrance_loss_source: SourceReference | None = None,
    configuration: SolverConfiguration | None = None,
    g: float = GRAVITATIONAL_ACCELERATION,
) -> float:
    """Solve for single-barrel discharge Q > 0 given a target upstream headwater elevation.

    The optional coefficient arguments and configuration follow the same precedence
    contract as :func:`solve_barrel_hydraulics`.

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
    tailwater: TailwaterCondition | float,
    *,
    inlet_coefficients: InletCoefficients | None = None,
    entrance_loss_coefficient: float | EntranceLossCoefficient | None = None,
    entrance_loss_source: SourceReference | None = None,
    configuration: SolverConfiguration | None = None,
    g: float = GRAVITATIONAL_ACCELERATION,
) -> float:
    """Solve barrel discharge for ``HW/D`` measured above the inlet invert."""
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
    tailwater: TailwaterCondition | float,
    *,
    configuration: SolverConfiguration | None = None,
    g: float = GRAVITATIONAL_ACCELERATION,
) -> float:
    """Return total discharge through an identical parallel-barrel group at a given HW."""
    if not isinstance(group, CulvertGroup):  # pyright: ignore[reportUnnecessaryIsInstance]
        msg = "group must be an instance of CulvertGroup."
        raise InvalidInputError(msg)
    barrel_discharge: float = solve_barrel_discharge_for_headwater(
        barrel=group.barrel,
        headwater_elevation=headwater_elevation,
        tailwater=tailwater,
        configuration=configuration,
        g=g,
    )
    return float(group.quantity) * barrel_discharge


def solve_crossing_discharge_for_headwater(
    crossing: CulvertCrossing,
    headwater_elevation: float,
    tailwater: TailwaterCondition | float,
    *,
    configuration: SolverConfiguration | None = None,
    g: float = GRAVITATIONAL_ACCELERATION,
) -> float:
    """Return combined culvert and roadway discharge at a target headwater elevation."""
    if not isinstance(crossing, CulvertCrossing):  # pyright: ignore[reportUnnecessaryIsInstance]
        msg = "crossing must be an instance of CulvertCrossing."
        raise InvalidInputError(msg)
    hw_elev: float = finite(headwater_elevation, "headwater_elevation")
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
    tailwater: TailwaterCondition | float,
    *,
    inlet_coefficients: InletCoefficients | None = None,
    entrance_loss_coefficient: float | EntranceLossCoefficient | None = None,
    entrance_loss_source: SourceReference | None = None,
    configuration: SolverConfiguration | None = None,
    g: float = GRAVITATIONAL_ACCELERATION,
) -> tuple[float, RootResult | None]:
    """Return discharge and its root diagnostics for crossing aggregation."""
    tw_elev: float
    tw_elev = tailwater.elevation if isinstance(tailwater, TailwaterCondition) else finite(tailwater, "tailwater")

    hw_elev: float = finite(headwater_elevation, "headwater_elevation")
    if hw_elev <= barrel.inlet_invert or hw_elev <= tw_elev:
        return 0.0, None

    hw_depth: float = hw_elev - barrel.inlet_invert
    if hw_depth <= 1e-6:
        return 0.0, None

    # Initial scaling for Q
    a: float = barrel.geometry.area_full
    d: float = barrel.geometry.rise
    q_scale: float = max(0.01, a * math.sqrt(g * min(d, hw_depth)))

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
    tailwater : TailwaterCondition | float
        Downstream tailwater condition or elevation (m).
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
