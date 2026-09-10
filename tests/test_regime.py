"""Tests for culvert hydraulic regime selection and single-barrel solver."""

from dataclasses import replace

import pytest

from culvert_solver.exceptions import InvalidInputError
from culvert_solver.geometry.circular import CircularGeometry
from culvert_solver.geometry.rectangular import RectangularGeometry
from culvert_solver.inlet_control.coefficients import (
    CIRCULAR_CMP_HEADWALL,
    CIRCULAR_CONCRETE_SQUARE_EDGE,
)
from culvert_solver.inlet_control.fhwa import flow_parameter
from culvert_solver.models.barrel import CulvertBarrel
from culvert_solver.models.enums import (
    ControlType,
    ConvergenceCalculation,
    ExitLossSelectionBasis,
    HydraulicWarningCode,
    ProfileCurve,
)
from culvert_solver.models.materials import (
    CONCRETE,
    CORRUGATED_STEEL,
    SMOOTH_HDPE,
    resolve_manning_roughness,
)
from culvert_solver.models.results import BarrelHydraulicResult, FlowRegime
from culvert_solver.models.tailwater import TailwaterCondition
from culvert_solver.outlet_control.losses import PIPE_CMP_HEADWALL, PIPE_CONCRETE_SOCKET_END
from culvert_solver.profiles.direct_step import InletControlProfile, WaterSurfaceProfile
from culvert_solver.references.models import SourceReference
from culvert_solver.solver.barrel import solve_barrel_hydraulics
from culvert_solver.solver.config import DEFAULT_SOLVER_CONFIGURATION
from culvert_solver.solver.regime import determine_governing_regime


def test_steep_slope_inlet_control() -> None:
    """Verify steep slope with low tailwater is governed by inlet control."""
    geom = CircularGeometry.from_mm(diameter_mm=1000.0)
    barrel = CulvertBarrel(
        geometry=geom,
        length=50.0,
        inlet_invert=10.0,
        outlet_invert=9.0,  # S0 = 1.0 / 50 = 0.02 (steep)
        roughness=0.013,
        material=CONCRETE,
    )
    q = 1.2
    tw_elev = 9.0  # Tailwater at outlet invert (TW_depth = 0.0)

    result: BarrelHydraulicResult = solve_barrel_hydraulics(
        barrel=barrel,
        discharge=q,
        tailwater=tw_elev,
        inlet_coefficients=CIRCULAR_CONCRETE_SQUARE_EDGE,
    )

    assert result.control_type == "inlet_control"
    assert result.regime in (
        FlowRegime.INLET_CONTROL_UNSUBMERGED,
        FlowRegime.INLET_CONTROL_TRANSITION,
        FlowRegime.INLET_CONTROL_SUBMERGED,
    )
    assert result.headwater_depth > 0
    assert result.headwater_elevation == pytest.approx(10.0 + result.headwater_depth)
    assert result.velocity_outlet > 0
    assert result.normal_depth is not None
    assert result.profile_curve is ProfileCurve.S2
    assert result.outlet_depth > result.normal_depth
    assert result.outlet_sequent_depth is None
    assert result.hydraulic_jump_swept_out is True
    assert result.inlet_control_headwater_elevation == result.headwater_elevation
    assert result.outlet_control_headwater_elevation is None
    assert result.full_flow_headwater_elevation is not None
    assert not result.warnings
    assert result.tailwater_depth == 0.0


def test_inlet_control_swept_out_jump_uses_s2_profile() -> None:
    """Use S2 routing when tailwater cannot sustain the outlet conjugate depth."""
    geom = CircularGeometry(diameter=1.2)
    barrel = CulvertBarrel(
        geometry=geom,
        length=30.0,
        inlet_invert=10.0,
        outlet_invert=9.7,
        roughness=0.012,
        material=CONCRETE,
    )

    low_tailwater = solve_barrel_hydraulics(barrel, 1.0, 9.7)
    moderate_tailwater = solve_barrel_hydraulics(barrel, 1.0, 10.3)

    assert low_tailwater.control_type is ControlType.INLET
    assert moderate_tailwater.control_type is ControlType.INLET
    assert low_tailwater.normal_depth is not None
    assert low_tailwater.profile_curve is ProfileCurve.S2
    assert low_tailwater.outlet_depth > low_tailwater.normal_depth
    assert moderate_tailwater.profile_curve is ProfileCurve.S2
    assert moderate_tailwater.tailwater_depth > moderate_tailwater.outlet_depth
    assert moderate_tailwater.outlet_depth == pytest.approx(low_tailwater.outlet_depth)
    assert moderate_tailwater.velocity_outlet == pytest.approx(low_tailwater.velocity_outlet)
    assert moderate_tailwater.outlet_sequent_depth is not None
    assert moderate_tailwater.tailwater_depth < moderate_tailwater.outlet_sequent_depth
    assert moderate_tailwater.hydraulic_jump_swept_out is True
    assert not moderate_tailwater.warnings


def test_inlet_control_reports_in_barrel_jump_and_tailwater_velocity() -> None:
    """An identified JS1 transition uses tailwater depth at the barrel outlet."""
    barrel = CulvertBarrel(
        geometry=CircularGeometry(diameter=1.2),
        length=30.0,
        inlet_invert=10.0,
        outlet_invert=9.7,
        roughness=0.012,
        material=CONCRETE,
    )

    result = solve_barrel_hydraulics(barrel, 1.0, 10.45)

    assert result.control_type is ControlType.INLET
    assert result.profile_curve is ProfileCurve.JS1
    assert result.hydraulic_jump_station is not None
    assert result.hydraulic_jump_swept_out is False
    assert result.outlet_depth == pytest.approx(result.tailwater_depth)
    assert result.velocity_outlet == pytest.approx(result.discharge / barrel.geometry.area(result.tailwater_depth))
    jump_records = [
        record for record in result.convergence if record.calculation is ConvergenceCalculation.HYDRAULIC_JUMP
    ]
    assert len(jump_records) == 1
    assert jump_records[0].result.root == result.hydraulic_jump_station
    assert not result.warnings


def test_m2_candidate_is_not_suppressed_by_full_flow_shortcut() -> None:
    """A free-surface M2 candidate can govern above the lower full-flow estimate."""
    barrel = CulvertBarrel(
        geometry=CircularGeometry(diameter=1.2),
        length=30.0,
        inlet_invert=10.0,
        outlet_invert=9.7,
        roughness=0.020,
        material=CONCRETE,
    )

    result = solve_barrel_hydraulics(barrel, 2.0, 9.7)

    assert result.normal_depth is not None
    assert result.normal_depth > result.critical_depth
    assert result.control_type is ControlType.OUTLET
    assert result.regime is FlowRegime.OUTLET_CONTROL_FREE_SURFACE
    assert result.profile_curve is ProfileCurve.M2
    assert result.headwater_elevation == pytest.approx(11.2755621109687)
    assert result.outlet_depth == pytest.approx(result.critical_depth)
    assert isinstance(result.profile, WaterSurfaceProfile)
    assert result.profile.curve_type is ProfileCurve.M2
    assert result.profile.points[0].station == 0.0
    assert result.profile.points[-1].station == barrel.length
    assert result.outlet_control_losses is not None
    assert result.outlet_control_losses.entrance is not None
    assert result.outlet_control_losses.friction is None
    assert result.outlet_control_losses.exit is None
    assert result.outlet_control_losses.total is None
    calculations = {record.calculation for record in result.convergence}
    assert ConvergenceCalculation.CRITICAL_DEPTH in calculations
    assert ConvergenceCalculation.NORMAL_DEPTH in calculations
    assert not result.warnings


def test_mixed_m2_full_flow_reach_is_reported() -> None:
    """Outlet control reports the upstream full length rather than flattening M2."""
    barrel = CulvertBarrel(
        geometry=CircularGeometry(diameter=1.2),
        length=100.0,
        inlet_invert=10.0,
        outlet_invert=9.9,
        roughness=0.012,
        material=CONCRETE,
    )

    result = solve_barrel_hydraulics(
        barrel,
        3.0,
        9.9,
        entrance_loss_coefficient=0.5,
    )

    assert result.control_type is ControlType.OUTLET
    assert result.regime is FlowRegime.OUTLET_CONTROL_MIXED
    assert result.profile_curve is ProfileCurve.M2
    assert result.full_flow_length == pytest.approx(68.46, abs=0.02)
    assert result.headwater_elevation == pytest.approx(12.015, abs=0.001)
    assert isinstance(result.profile, WaterSurfaceProfile)
    assert result.profile.curve_type is ProfileCurve.M2
    assert result.profile.full_flow_length == result.full_flow_length
    assert result.profile.profile_limit_station == result.full_flow_length
    assert not result.warnings


def test_type6_free_outfall_retains_mixed_barrel_profile() -> None:
    """An inlet-governed Type 6 case retains its M2/full barrel profile."""
    barrel = CulvertBarrel(
        geometry=CircularGeometry(diameter=0.9),
        length=10.0,
        inlet_invert=100.2,
        outlet_invert=100.0,
        roughness=0.020,
        material=CORRUGATED_STEEL,
        inlet_coefficients=CIRCULAR_CMP_HEADWALL,
        entrance_loss_coefficient=PIPE_CMP_HEADWALL,
    )

    result = solve_barrel_hydraulics(barrel, 4.63, 100.1)

    assert result.control_type is ControlType.INLET
    assert result.regime is FlowRegime.INLET_CONTROL_SUBMERGED
    assert result.profile_curve is ProfileCurve.M2
    assert result.full_flow_length == pytest.approx(9.991, abs=0.001)
    assert result.velocity_outlet == pytest.approx(7.281, abs=0.001)
    assert tuple(warning.code for warning in result.warnings) == (
        HydraulicWarningCode.INLET_CONTROL_HIGH_HEAD_EXTENSION,
    )


def test_high_tailwater_forces_outlet_control_full() -> None:
    """Verify high tailwater submerging outlet forces full-flow outlet control."""
    geom = CircularGeometry.from_mm(diameter_mm=1000.0)
    barrel = CulvertBarrel(
        geometry=geom,
        length=50.0,
        inlet_invert=10.0,
        outlet_invert=9.5,
        roughness=0.013,
        material=CONCRETE,
    )
    q = 1.5
    # Outlet crown is at 9.5 + 1.0 = 10.5. Tailwater at 12.0 m is highly submerged.
    tw_elev = 12.0

    result = solve_barrel_hydraulics(
        barrel=barrel,
        discharge=q,
        tailwater=tw_elev,
        entrance_loss_coefficient=0.5,
    )

    assert result.control_type == "outlet_control"
    assert result.regime == FlowRegime.OUTLET_CONTROL_FULL
    assert result.tailwater_depth == pytest.approx(2.5, abs=1e-6)
    # Under full-flow outlet control, HW_elev > TW_elev
    assert result.headwater_elevation > tw_elev
    assert result.velocity_outlet == pytest.approx(q / geom.area_full, rel=1e-5)
    assert result.full_flow_length == barrel.length
    assert result.outlet_control_losses is not None
    assert result.full_flow_losses is not None
    assert result.exit_loss_selection is not None
    assert result.exit_loss_selection.ko == 1.0
    assert result.exit_loss_selection.basis is ExitLossSelectionBasis.HDS5_STANDARD
    assert result.exit_loss_selection.source is not None
    assert result.outlet_control_losses is result.full_flow_losses
    losses = result.outlet_control_losses
    assert losses.entrance is not None
    assert losses.friction is not None
    assert losses.exit is not None
    assert losses.total == pytest.approx(losses.entrance + losses.friction + losses.exit)
    assert not result.warnings


def test_shallow_submerged_outlet_routes_upstream_s1_profile() -> None:
    """A shallow submerged outlet joins an upstream S1 reach to full flow."""
    barrel = CulvertBarrel(
        geometry=CircularGeometry(diameter=1.2),
        length=30.0,
        inlet_invert=10.0,
        outlet_invert=9.7,
        roughness=0.012,
        material=CONCRETE,
    )

    result = solve_barrel_hydraulics(barrel, 1.0, 10.901)

    assert result.regime is FlowRegime.OUTLET_CONTROL_MIXED
    assert 0.0 < result.full_flow_length < barrel.length
    assert result.profile_curve is ProfileCurve.S1
    assert result.headwater_elevation == pytest.approx(10.9882, abs=0.0001)
    assert result.outlet_depth == barrel.geometry.rise
    assert isinstance(result.profile, WaterSurfaceProfile)
    assert result.profile.curve_type is ProfileCurve.S1
    assert result.profile.points[0].station == 0.0
    assert not result.warnings


def test_shallow_submerged_outlet_locates_upstream_js1_profile() -> None:
    """A shallow submerged outlet can sustain a jump before its full reach."""
    barrel = CulvertBarrel(
        geometry=CircularGeometry(diameter=1.2),
        length=30.0,
        inlet_invert=10.0,
        outlet_invert=9.7,
        roughness=0.012,
        material=CONCRETE,
    )

    result = solve_barrel_hydraulics(barrel, 3.0, 10.901)

    assert result.control_type is ControlType.INLET
    assert result.profile_curve is ProfileCurve.JS1
    assert result.full_flow_length == pytest.approx(0.202, abs=0.001)
    assert result.hydraulic_jump_station == pytest.approx(17.53, abs=0.02)
    assert result.hydraulic_jump_swept_out is False
    assert result.outlet_depth == barrel.geometry.rise
    assert isinstance(result.profile, InletControlProfile)
    assert result.profile.curve_type is ProfileCurve.JS1
    assert result.profile.hydraulic_jump_station == result.hydraulic_jump_station
    assert not result.warnings


def test_mild_slope_outlet_control_backwater() -> None:
    """Verify mild slope with subcritical tailwater governed by outlet control free surface."""
    geom = RectangularGeometry.from_mm(span_mm=2000.0, rise_mm=1500.0)
    barrel = CulvertBarrel(
        geometry=geom,
        length=60.0,
        inlet_invert=15.0,
        outlet_invert=14.94,  # S0 = 0.06 / 60 = 0.001 (very mild)
        roughness=0.013,
        material=CONCRETE,
    )
    q = 4.0
    # Tailwater high enough to cause significant backwater, but below crown.
    # (crown = 14.94 + 1.5 = 16.44)
    tw_elev = 16.2  # TW depth = 16.2 - 14.94 = 1.26 m

    result = solve_barrel_hydraulics(
        barrel=barrel,
        discharge=q,
        tailwater=tw_elev,
        entrance_loss_coefficient=0.4,
    )

    assert result.control_type == "outlet_control"
    assert result.regime in (
        FlowRegime.OUTLET_CONTROL_FREE_SURFACE,
        FlowRegime.OUTLET_CONTROL_FULL,
    )
    assert result.headwater_elevation > tw_elev


def test_inlet_control_transition_regime() -> None:
    """Verify flow regime properly flags INLET_CONTROL_TRANSITION when 3.5 < q* < 4.0."""
    geom = CircularGeometry.from_mm(diameter_mm=1200.0)
    barrel = CulvertBarrel(
        geometry=geom,
        length=30.0,
        inlet_invert=20.0,
        outlet_invert=18.5,  # Steep slope S0 = 1.5 / 30 = 0.05
        roughness=0.013,
        material=CONCRETE,
    )
    # Find discharge where flow parameter q* is approximately 3.75 (inside 3.5 to 4.0)
    # q* = 1.811 * Q / (A * D^0.5) => Q = 3.75 * A * D^0.5 / 1.811
    q_target = 3.75 * geom.area_full * (geom.rise**0.5) / 1.811
    qs = flow_parameter(q_target, geom.area_full, geom.rise)
    assert 3.5 < qs < 4.0

    result = determine_governing_regime(
        barrel=barrel,
        discharge=q_target,
        tailwater=TailwaterCondition(elevation=18.5),
        inlet_coefficients=CIRCULAR_CONCRETE_SQUARE_EDGE,
    )

    assert result.control_type == "inlet_control"
    assert result.regime == FlowRegime.INLET_CONTROL_TRANSITION


def test_horizontal_barrel_regime() -> None:
    """Verify horizontal barrel (S0 = 0) regime calculation."""
    geom = CircularGeometry.from_mm(diameter_mm=1000.0)
    barrel = CulvertBarrel(
        geometry=geom,
        length=40.0,
        inlet_invert=10.0,
        outlet_invert=10.0,
        roughness=0.013,
        material=CONCRETE,
    )
    assert barrel.is_horizontal

    result = solve_barrel_hydraulics(
        barrel=barrel,
        discharge=1.5,
        tailwater=10.0,
    )

    assert result.normal_depth is None
    assert result.headwater_elevation > 10.0
    assert result.regime is not None


def test_regime_input_validation() -> None:
    """Verify input validation for solver."""
    geom = CircularGeometry.from_mm(diameter_mm=1000.0)
    barrel = CulvertBarrel(
        geometry=geom,
        length=40.0,
        inlet_invert=10.0,
        outlet_invert=9.5,
        roughness=0.013,
        material=CONCRETE,
    )

    with pytest.raises(InvalidInputError, match="discharge must be strictly positive"):
        solve_barrel_hydraulics(barrel=barrel, discharge=0.0, tailwater=10.0)

    with pytest.raises(InvalidInputError, match="discharge must be strictly positive"):
        solve_barrel_hydraulics(barrel=barrel, discharge=-2.0, tailwater=10.0)

    with pytest.raises(InvalidInputError, match="entrance_loss_coefficient must be nonnegative"):
        solve_barrel_hydraulics(
            barrel=barrel,
            discharge=1.0,
            tailwater=10.0,
            entrance_loss_coefficient=-0.3,
        )


def test_solver_configuration_changes_adopted_default() -> None:
    """Verify an injected default is used by the real calculation path."""
    barrel = CulvertBarrel(
        geometry=CircularGeometry.from_mm(diameter_mm=1000.0),
        length=40.0,
        inlet_invert=10.0,
        outlet_invert=9.5,
        roughness=0.013,
        material=CONCRETE,
    )
    configured = replace(
        DEFAULT_SOLVER_CONFIGURATION,
        default_circular_concrete_loss=PIPE_CONCRETE_SOCKET_END,
    )

    baseline = solve_barrel_hydraulics(barrel, 1.5, 12.0)
    changed = solve_barrel_hydraulics(barrel, 1.5, 12.0, configuration=configured)

    assert changed.headwater_elevation < baseline.headwater_elevation
    assert changed.inlet_coefficient_selection is not None
    assert changed.entrance_loss_selection is not None
    assert changed.entrance_loss_selection.ke == PIPE_CONCRETE_SOCKET_END.ke
    assert changed.adopted_roughness == barrel.roughness


def test_solver_preserves_user_supplied_sources() -> None:
    """Verify manufacturer/project references survive into calculation results."""
    source = SourceReference(
        source_id="manufacturer-spec-2026",
        publication="Manufacturer hydraulic specification",
        edition="2026",
        locator="Table 4",
        url=None,
        applicability="DN1000 test product",
    )
    barrel = CulvertBarrel(
        geometry=CircularGeometry.from_mm(diameter_mm=1000.0),
        length=40.0,
        inlet_invert=10.0,
        outlet_invert=9.5,
        roughness=0.011,
        material=CONCRETE,
        roughness_source=source,
    )

    result = solve_barrel_hydraulics(
        barrel,
        1.5,
        12.0,
        entrance_loss_coefficient=0.35,
        entrance_loss_source=source,
    )

    assert result.roughness_source is source
    assert result.entrance_loss_selection is not None
    assert result.entrance_loss_selection.source is source


def test_solver_preserves_plastic_fallback_applicability_notices() -> None:
    """An explicitly accepted plastic fallback remains auditable end to end."""
    roughness = resolve_manning_roughness(SMOOTH_HDPE, allow_documented_fallback=True)
    barrel = CulvertBarrel(
        geometry=CircularGeometry(diameter=1.0),
        length=20.0,
        inlet_invert=10.0,
        outlet_invert=9.8,
        roughness=roughness.value,
        material=SMOOTH_HDPE,
        roughness_selection=roughness,
    )

    result = solve_barrel_hydraulics(
        barrel,
        1.0,
        9.8,
        inlet_coefficients=CIRCULAR_CONCRETE_SQUARE_EDGE,
        entrance_loss_coefficient=0.5,
    )

    assert result.adopted_roughness == roughness.value
    assert result.roughness_selection_basis is roughness.basis
    assert result.roughness_source is roughness.source
    assert result.roughness_notices == roughness.notices
