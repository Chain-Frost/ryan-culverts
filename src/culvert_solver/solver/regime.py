"""Hydraulic regime selection and governing solution for a single culvert barrel."""

from dataclasses import replace

from .._validation import finite
from ..constants import GRAVITATIONAL_ACCELERATION
from ..exceptions import InvalidInputError
from ..hydraulics.critical import CriticalDepthResult, calculate_critical_depth
from ..hydraulics.normal import NormalDepthResult, calculate_normal_depth
from ..hydraulics.primitives import cross_section_velocity
from ..inlet_control.coefficients import InletCoefficients
from ..inlet_control.solver import InletControlResult, calculate_inlet_control_headwater
from ..models.barrel import CulvertBarrel
from ..models.enums import (
    ControlType,
    ConvergenceCalculation,
    HydraulicWarningCode,
    ProfileCurve,
)
from ..models.results import (
    BarrelHydraulicResult,
    ConvergenceRecord,
    FlowRegime,
    HeadLossComponents,
    HydraulicWarning,
)
from ..models.tailwater import TailwaterCondition
from ..outlet_control.full_flow import (
    FullFlowOutletResult,
    calculate_downstream_full_flow_length,
    calculate_full_flow_outlet_headwater,
)
from ..outlet_control.losses import EntranceLossCoefficient
from ..outlet_control.partial_flow import (
    PartialFlowOutletResult,
    calculate_partial_flow_outlet_headwater,
)
from ..profiles.direct_step import (
    InletControlProfile,
    WaterSurfaceProfile,
    compute_steep_inlet_control_profile,
)
from ..references.models import SourceReference
from ..solver.resolvers import EntranceLossSelection, InletCoefficientSelection
from .config import SolverConfiguration
from .resolvers import resolve_entrance_loss_coefficient, resolve_inlet_coefficients


def determine_governing_regime(
    barrel: CulvertBarrel,
    discharge: float,
    tailwater: TailwaterCondition | float,
    *,
    inlet_coefficients: InletCoefficients | None = None,
    entrance_loss_coefficient: float | EntranceLossCoefficient | None = None,
    entrance_loss_source: SourceReference | None = None,
    configuration: SolverConfiguration | None = None,
    g: float = GRAVITATIONAL_ACCELERATION,
) -> BarrelHydraulicResult:
    """Determine the governing hydraulic control regime and calculate headwater elevation.

    Compares physically admissible inlet- and outlet-control candidates. Supported
    profile paths include S1/S2, hydraulic jumps, and selected mixed free/full states;
    unresolved states retain structured warnings.

    Parameters
    ----------
    barrel : CulvertBarrel
        Culvert barrel domain model.
    discharge : float
        Discharge Q (m³/s), strictly positive.
    tailwater : TailwaterCondition | float
        Tailwater boundary condition or absolute elevation (m).
    inlet_coefficients : InletCoefficients | None, optional
        Empirical inlet control regression coefficients.
    entrance_loss_coefficient : float | EntranceLossCoefficient | None, optional
        Inlet entrance loss coefficient Ke for outlet control.
    entrance_loss_source : SourceReference | None, optional
        Provenance for a numeric entrance-loss override.
    configuration : SolverConfiguration | None, optional
        Injectable project defaults used only when explicit and barrel values are absent.
    g : float, default=GRAVITATIONAL_ACCELERATION
        Gravitational acceleration (m/s²).

    Returns:
    -------
    BarrelHydraulicResult
        Complete hydraulic result for the barrel including governing regime,
        headwater elevation, depths, and outlet velocity.
    """
    q: float = finite(discharge, "discharge")
    if q <= 0:
        msg = "discharge must be strictly positive."
        raise InvalidInputError(msg)

    tw_elev: float
    tw_elev = tailwater.elevation if isinstance(tailwater, TailwaterCondition) else finite(tailwater, "tailwater")

    tw_depth: float = max(0.0, tw_elev - barrel.outlet_invert)

    inlet_selection: InletCoefficientSelection = resolve_inlet_coefficients(
        barrel, override=inlet_coefficients, configuration=configuration
    )
    entrance_selection: EntranceLossSelection = resolve_entrance_loss_coefficient(
        barrel,
        override=entrance_loss_coefficient,
        override_source=entrance_loss_source,
        configuration=configuration,
    )

    # Calculate critical and normal depths
    crit_res: CriticalDepthResult = calculate_critical_depth(geometry=barrel.geometry, discharge=q, g=g)
    yc: float = crit_res.depth
    convergence: list[ConvergenceRecord] = []
    if crit_res.convergence is not None:
        convergence.append(
            ConvergenceRecord(calculation=ConvergenceCalculation.CRITICAL_DEPTH, result=crit_res.convergence)
        )

    yn: float | None = None
    if not barrel.is_horizontal:
        norm_res: NormalDepthResult = calculate_normal_depth(
            geometry=barrel.geometry,
            discharge=q,
            slope=barrel.slope,
            roughness=barrel.roughness,
            g=g,
        )
        if norm_res.convergence is not None:
            convergence.append(
                ConvergenceRecord(calculation=ConvergenceCalculation.NORMAL_DEPTH, result=norm_res.convergence)
            )
        if not norm_res.capacity_exceeded:
            yn = norm_res.depth

    # 1. Inlet control calculation
    inlet_res: InletControlResult = calculate_inlet_control_headwater(
        barrel=barrel, discharge=q, coefficients=inlet_selection.coefficients, g=g
    )
    hw_inlet_elev: float = inlet_res.headwater_elevation
    hw_inlet_depth: float = inlet_res.headwater_depth

    # 2. Outlet control calculations
    full_res: FullFlowOutletResult = calculate_full_flow_outlet_headwater(
        barrel,
        discharge=q,
        tailwater=tw_elev,
        entrance_loss_coefficient=entrance_selection.ke,
        g=g,
    )
    hw_full_elev: float = full_res.headwater_elevation
    full_flow_losses = HeadLossComponents(
        entrance=full_res.entrance_loss,
        friction=full_res.friction_loss,
        exit=full_res.exit_loss,
        total=full_res.total_head_loss,
    )

    hw_outlet_elev: float
    outlet_regime: FlowRegime
    profile_outlet_depth: float | None = None
    outlet_profile_curve: ProfileCurve | None = None
    outlet_full_flow_length = 0.0
    warnings: list[HydraulicWarning] = list(inlet_res.warnings)
    outlet_control_losses: HeadLossComponents | None = None
    selected_profile: WaterSurfaceProfile | InletControlProfile | None = None

    rise: float = barrel.geometry.rise
    steep_profile: InletControlProfile | None = None
    outlet_sequent_depth: float | None = None
    hydraulic_jump_station: float | None = None
    hydraulic_jump_swept_out: bool | None = None
    if tw_depth < rise and yn is not None and yn < yc:
        steep_profile = compute_steep_inlet_control_profile(barrel=barrel, discharge=q, tailwater=tw_elev, g=g)
        outlet_sequent_depth = steep_profile.outlet_sequent_depth
        hydraulic_jump_station = steep_profile.hydraulic_jump_station
        hydraulic_jump_swept_out = steep_profile.hydraulic_jump_swept_out

    if tw_depth >= rise:
        submerged_full_length: float = calculate_downstream_full_flow_length(
            barrel=barrel, discharge=q, tailwater=tw_elev
        )
        outlet_full_flow_length: float = submerged_full_length
        if submerged_full_length >= barrel.length - 1e-9:
            hw_outlet_elev = hw_full_elev
            outlet_regime = FlowRegime.OUTLET_CONTROL_FULL
            outlet_profile_curve = ProfileCurve.FULL
        else:
            outlet_regime = FlowRegime.OUTLET_CONTROL_MIXED
            transition_station: float = barrel.length - submerged_full_length
            transition_barrel: CulvertBarrel = replace(
                barrel,
                length=transition_station,
                outlet_invert=barrel.inlet_invert - barrel.slope * transition_station,
            )
            crown_offset: float = max(1e-8, rise * 1e-6)
            transition_tailwater: float = transition_barrel.outlet_crown - crown_offset

            if yn is not None and yn < yc:
                steep_profile = compute_steep_inlet_control_profile(
                    barrel=transition_barrel,
                    discharge=q,
                    tailwater=transition_tailwater,
                    g=g,
                )
                selected_profile = steep_profile
                outlet_sequent_depth = steep_profile.outlet_sequent_depth
                hydraulic_jump_station = steep_profile.hydraulic_jump_station
                hydraulic_jump_swept_out = steep_profile.hydraulic_jump_swept_out
                outlet_profile_curve = steep_profile.curve_type
                if steep_profile.curve_type in {ProfileCurve.S2, ProfileCurve.JS1}:
                    # A jump leaves the upstream reach connected to inlet control.
                    hw_outlet_elev = float("-inf")
                else:
                    transition_result: PartialFlowOutletResult = calculate_partial_flow_outlet_headwater(
                        barrel=transition_barrel,
                        discharge=q,
                        tailwater=transition_tailwater,
                        entrance_loss_coefficient=entrance_selection.ke,
                        g=g,
                    )
                    hw_outlet_elev = transition_result.headwater_elevation
                    selected_profile = transition_result.profile
                    outlet_control_losses = HeadLossComponents(entrance=transition_result.entrance_loss)
            elif yn is not None:
                transition_result = calculate_partial_flow_outlet_headwater(
                    barrel=transition_barrel,
                    discharge=q,
                    tailwater=transition_tailwater,
                    entrance_loss_coefficient=entrance_selection.ke,
                    g=g,
                )
                hw_outlet_elev = transition_result.headwater_elevation
                outlet_profile_curve = transition_result.profile.curve_type
                selected_profile = transition_result.profile
                outlet_control_losses = HeadLossComponents(entrance=transition_result.entrance_loss)
            else:
                hw_outlet_elev = hw_full_elev
                outlet_control_losses = full_flow_losses
                warnings.append(
                    HydraulicWarning(
                        code=HydraulicWarningCode.MIXED_FLOW_NOT_RESOLVED,
                        message=(
                            "Tailwater submerges the outlet, but the full-flow HGL falls below "
                            "the crown upstream and normal depth exceeds barrel capacity. The "
                            "downstream full length is reported, but the upstream profile is "
                            "not yet resolved."
                        ),
                    )
                )
    elif steep_profile is not None and steep_profile.curve_type in {
        ProfileCurve.S2,
        ProfileCurve.JS1,
    }:
        # A swept-out jump or an identified in-barrel jump leaves a supercritical
        # reach connected to the inlet control, blocking downstream influence.
        hw_outlet_elev = float("-inf")
        outlet_regime = FlowRegime.OUTLET_CONTROL_FREE_SURFACE
        selected_profile = steep_profile
    else:
        # Free-surface partial flow backwater profile
        partial_res: PartialFlowOutletResult = calculate_partial_flow_outlet_headwater(
            barrel,
            discharge=q,
            tailwater=tw_elev,
            entrance_loss_coefficient=entrance_selection.ke,
            g=g,
        )
        if partial_res.profile.is_full_flow:
            hw_outlet_elev = hw_full_elev
            outlet_regime = FlowRegime.OUTLET_CONTROL_FULL
            outlet_profile_curve = ProfileCurve.FULL
            outlet_control_losses = full_flow_losses
        else:
            hw_outlet_elev = partial_res.headwater_elevation
            outlet_regime = (
                FlowRegime.OUTLET_CONTROL_MIXED
                if partial_res.full_flow_length > 0.0
                else FlowRegime.OUTLET_CONTROL_FREE_SURFACE
            )
            profile_outlet_depth = partial_res.outlet_depth
            outlet_profile_curve = partial_res.profile.curve_type
            outlet_full_flow_length = partial_res.full_flow_length
            outlet_control_losses = HeadLossComponents(entrance=partial_res.entrance_loss)
        selected_profile = partial_res.profile

    if outlet_regime is FlowRegime.OUTLET_CONTROL_FULL:
        outlet_control_losses = full_flow_losses
    if selected_profile is not None:
        convergence.extend(selected_profile.convergence)

    # 3. Governing control selection: max(HW_inlet, HW_outlet)
    gov_control: ControlType
    gov_regime: FlowRegime
    gov_hw_elev: float
    gov_hw_depth: float
    gov_profile_curve: ProfileCurve | None

    if hw_inlet_elev >= hw_outlet_elev:
        gov_control = ControlType.INLET
        gov_hw_elev = hw_inlet_elev
        gov_hw_depth = hw_inlet_depth
        gov_regime = inlet_res.regime
        gov_profile_curve = None
    else:
        gov_control = ControlType.OUTLET
        gov_hw_elev = hw_outlet_elev
        gov_hw_depth = gov_hw_elev - barrel.inlet_invert
        gov_regime = outlet_regime
        gov_profile_curve = outlet_profile_curve

    # 4. Outlet velocity calculation
    v_out: float
    outlet_depth: float
    if tw_depth >= rise:
        v_out = cross_section_velocity(q, barrel.geometry.area_full)
        outlet_depth = rise
        if steep_profile is not None:
            gov_profile_curve = steep_profile.curve_type
    else:
        # Free-surface outlet velocity
        y_out: float
        if gov_control is ControlType.OUTLET:
            y_out = profile_outlet_depth if profile_outlet_depth is not None else max(tw_depth, yc)
        else:
            # HDS-5 section 3.1.6 permits normal depth as the inlet-control
            # outlet-velocity approximation.  Tailwater can replace that depth
            # only after a supported S1/jump calculation demonstrates downstream
            # control; that profile logic is not yet implemented here.
            if steep_profile is not None:
                y_out = steep_profile.outlet_depth
                gov_profile_curve = steep_profile.curve_type
            elif outlet_full_flow_length > 0.0 and outlet_profile_curve is not None:
                # A mixed M2/full outlet path remains the physical barrel profile
                # even when the inlet-control headwater candidate governs.
                y_out = profile_outlet_depth if profile_outlet_depth is not None else yc
                gov_profile_curve = outlet_profile_curve
            elif barrel.is_horizontal or (yn is not None and yn >= yc):
                y_out = max(tw_depth, yc)
            else:
                y_out = yn if yn is not None else yc
                warning_code = (
                    HydraulicWarningCode.INLET_OUTLET_DEPTH_APPROXIMATION
                    if yn is not None
                    else HydraulicWarningCode.MIXED_FLOW_NOT_RESOLVED
                )
                if all(warning.code is not warning_code for warning in warnings):
                    warnings.append(
                        HydraulicWarning(
                            code=warning_code,
                            message=(
                                "Outlet depth uses the HDS-5 normal-depth approximation because "
                                "S1 and hydraulic-jump location are not yet resolved."
                                if yn is not None
                                else "Normal depth exceeds barrel capacity; a possible mixed-flow "
                                "state is not yet resolved, so critical depth is used for velocity."
                            ),
                        )
                    )

        safe_y = min(rise - 1e-4, max(1e-4, y_out))
        outlet_depth = safe_y
        v_out = cross_section_velocity(discharge=q, area=barrel.geometry.area(depth=safe_y))

    return BarrelHydraulicResult(
        barrel=barrel,
        discharge=q,
        headwater_elevation=gov_hw_elev,
        headwater_depth=gov_hw_depth,
        tailwater_elevation=tw_elev,
        tailwater_depth=tw_depth,
        regime=gov_regime,
        control_type=gov_control,
        velocity_outlet=v_out,
        outlet_depth=outlet_depth,
        critical_depth=yc,
        normal_depth=yn,
        profile_curve=gov_profile_curve,
        outlet_sequent_depth=outlet_sequent_depth,
        hydraulic_jump_station=hydraulic_jump_station,
        hydraulic_jump_swept_out=hydraulic_jump_swept_out,
        full_flow_length=outlet_full_flow_length,
        inlet_control_headwater_elevation=hw_inlet_elev,
        outlet_control_headwater_elevation=(None if hw_outlet_elev == float("-inf") else hw_outlet_elev),
        full_flow_headwater_elevation=hw_full_elev,
        warnings=tuple(warnings),
        inlet_coefficient_selection=inlet_selection,
        entrance_loss_selection=entrance_selection,
        exit_loss_selection=full_res.exit_loss_selection,
        adopted_roughness=barrel.roughness,
        roughness_selection_basis=barrel.roughness_selection_basis,
        roughness_source=barrel.roughness_source,
        roughness_notices=barrel.roughness_notices,
        outlet_control_losses=outlet_control_losses,
        full_flow_losses=full_flow_losses,
        profile=selected_profile,
        convergence=tuple(convergence),
    )
