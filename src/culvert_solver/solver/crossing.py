"""Culvert crossing hydraulic solver aggregating multiple culvert groups."""

import math

from .._validation import finite
from ..constants import GRAVITATIONAL_ACCELERATION
from ..exceptions import InvalidInputError
from ..inlet_control.coefficients import InletCoefficients
from ..models.barrel import CulvertBarrel
from ..models.crossing import CulvertCrossing
from ..models.enums import ControlType, ConvergenceCalculation
from ..models.results import (
    BarrelHydraulicResult,
    ConvergenceRecord,
    CrossingHydraulicResult,
    FlowRegime,
    GroupHydraulicResult,
)
from ..models.tailwater import TailwaterCondition
from ..numerical.roots import RootResult, solve_brent
from ..numerical.tolerances import RootTolerances
from ..outlet_control.losses import EntranceLossCoefficient
from ..references.models import SourceReference
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
    if isinstance(tailwater, TailwaterCondition):
        tw_elev = tailwater.elevation
    else:
        tw_elev = finite(tailwater, "tailwater")

    hw_elev: float = finite(headwater_elevation, "headwater_elevation")
    if hw_elev <= barrel.inlet_invert or hw_elev <= tw_elev:
        return 0.0, None

    hw_depth = hw_elev - barrel.inlet_invert
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
        res_hi = solve_barrel_hydraulics(
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
        res_lo = solve_barrel_hydraulics(
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
        res = solve_barrel_hydraulics(
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

    root_res = solve_brent(
        res_q,
        q_lo,
        q_hi,
        tolerances=_DISCHARGE_ROOT_TOLERANCES,
    )
    return root_res.root, root_res


def solve_crossing_hydraulics(
    crossing: CulvertCrossing,
    total_discharge: float,
    tailwater: TailwaterCondition | float,
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

    Returns
    -------
    CrossingHydraulicResult
        Hydraulic solution for the entire crossing and each constituent culvert group.
    """
    if not isinstance(crossing, CulvertCrossing):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise InvalidInputError("crossing must be an instance of CulvertCrossing.")

    q_tot: float = finite(total_discharge, "total_discharge")
    if q_tot <= 0:
        raise InvalidInputError("total_discharge must be strictly positive.")

    tw_elev: float
    if isinstance(tailwater, TailwaterCondition):
        tw_elev = tailwater.elevation
    else:
        tw_elev = finite(tailwater, "tailwater")

    # Fast path for single-group crossing
    if crossing.num_groups == 1:
        g0 = crossing.groups[0]
        g_res0 = solve_group_hydraulics(
            group=g0,
            total_discharge=q_tot,
            tailwater=tw_elev,
            configuration=configuration,
            g=g,
        )
        return CrossingHydraulicResult(
            headwater_elevation=g_res0.barrel_result.headwater_elevation,
            total_discharge=q_tot,
            tailwater_elevation=tw_elev,
            group_results=(g_res0,),
        )

    # Multi-group crossing: solve common HW elevation
    def crossing_discharge_at_hw(hw: float) -> float:
        total_q = 0.0
        for grp in crossing.groups:
            q_b = solve_barrel_discharge_for_headwater(
                barrel=grp.barrel,
                headwater_elevation=hw,
                tailwater=tw_elev,
                configuration=configuration,
                g=g,
            )
            total_q += float(grp.quantity) * q_b
        return total_q

    # Bracket HW elevation:
    min_bound = max(crossing.min_inlet_invert, tw_elev)
    hw_lo = min_bound + 1e-4
    hw_hi = max(crossing.max_inlet_invert, tw_elev) + 1.0

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

    hw_root = solve_brent(
        hw_residual,
        hw_lo,
        hw_hi,
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
        q_grp = float(grp.quantity) * q_b
        if q_b > 0:
            b_res = solve_barrel_hydraulics(
                barrel=grp.barrel,
                discharge=q_b,
                tailwater=tw_elev,
                configuration=configuration,
                g=g,
            )
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
                    ConvergenceCalculation.BARREL_DISCHARGE,
                    discharge_root,
                )
            ),
        )
        group_results.append(g_res)

    return CrossingHydraulicResult(
        headwater_elevation=gov_hw_elev,
        total_discharge=q_tot,
        tailwater_elevation=tw_elev,
        group_results=tuple(group_results),
        headwater_convergence=ConvergenceRecord(
            ConvergenceCalculation.CROSSING_HEADWATER,
            hw_root,
        ),
    )
