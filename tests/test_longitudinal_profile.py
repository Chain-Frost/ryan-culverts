"""Focused tests for typed longitudinal HGL/EGL profile results."""

import pytest

from culvert_solver.geometry.circular import CircularGeometry
from culvert_solver.models.barrel import CulvertBarrel
from culvert_solver.models.materials import CONCRETE
from culvert_solver.profiles.longitudinal import HydraulicProfileState
from culvert_solver.solver.barrel import solve_barrel_hydraulics


def test_positive_slope_full_flow_reconciles_scalar_losses() -> None:
    """Pressurised profile endpoints reconcile with the existing full-flow energy balance."""
    barrel = CulvertBarrel(
        geometry=CircularGeometry(diameter=1.0),
        length=50.0,
        inlet_invert=10.0,
        outlet_invert=9.5,
        roughness=0.013,
        material=CONCRETE,
    )

    result = solve_barrel_hydraulics(
        barrel=barrel,
        discharge=1.5,
        tailwater=12.0,
        entrance_loss_coefficient=0.5,
    )

    profile = result.longitudinal_profile
    losses = result.full_flow_losses
    assert profile is not None
    assert losses is not None
    assert len(profile.points) == 2
    assert all(point.state is HydraulicProfileState.PRESSURISED for point in profile.points)
    assert all(point.water_surface_elevation is None for point in profile.points)
    assert profile.points[0].station == 0.0
    assert profile.points[-1].station == barrel.length
    assert profile.points[0].energy_grade_elevation - profile.points[-1].energy_grade_elevation == pytest.approx(
        losses.friction
    )
    assert profile.points[-1].hydraulic_grade_elevation == pytest.approx(result.tailwater_elevation)
    assert profile.entrance_loss == pytest.approx(losses.entrance)
    assert profile.friction_loss == pytest.approx(losses.friction)
    assert profile.exit_loss == pytest.approx(losses.exit)


def test_horizontal_full_flow_has_friction_gradient() -> None:
    """A horizontal pressurised barrel still exposes the friction-driven HGL gradient."""
    barrel = CulvertBarrel(
        geometry=CircularGeometry(diameter=1.0),
        length=40.0,
        inlet_invert=10.0,
        outlet_invert=10.0,
        roughness=0.013,
        material=CONCRETE,
    )

    result = solve_barrel_hydraulics(
        barrel=barrel,
        discharge=1.2,
        tailwater=12.0,
        entrance_loss_coefficient=0.5,
    )

    profile = result.longitudinal_profile
    assert profile is not None
    assert profile.points[0].invert_elevation == profile.points[-1].invert_elevation
    assert profile.points[0].friction_slope > 0.0
    assert profile.points[0].hydraulic_grade_elevation > profile.points[-1].hydraulic_grade_elevation
    assert profile.points[-1].cumulative_friction_loss == pytest.approx(profile.friction_loss)


def test_m2_to_upstream_full_reach_is_one_coherent_profile() -> None:
    """Existing M2/full support is exposed as one ordered mixed profile."""
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

    profile = result.longitudinal_profile
    assert profile is not None
    assert profile.is_mixed
    assert profile.transition_stations == pytest.approx((result.full_flow_length,))
    assert profile.points[0].station == 0.0
    assert profile.points[-1].station == barrel.length
    assert tuple(point.station for point in profile.points) == tuple(sorted(point.station for point in profile.points))
    assert profile.points[0].state is HydraulicProfileState.PRESSURISED
    assert profile.points[-1].state is HydraulicProfileState.FREE_SURFACE
    assert profile.points[0].water_surface_elevation is None
    assert profile.points[-1].water_surface_elevation is not None
    assert profile.exit_loss is None


def test_submerged_outlet_mixed_reach_marks_downstream_pressurised_state() -> None:
    """A supported shallow-submerged mixed case exposes its downstream full reach."""
    barrel = CulvertBarrel(
        geometry=CircularGeometry(diameter=1.2),
        length=30.0,
        inlet_invert=10.0,
        outlet_invert=9.7,
        roughness=0.012,
        material=CONCRETE,
    )

    result = solve_barrel_hydraulics(barrel, 1.0, 10.901)

    profile = result.longitudinal_profile
    losses = result.full_flow_losses
    assert profile is not None
    assert losses is not None
    assert profile.is_mixed
    assert profile.transition_stations
    assert profile.points[0].state is HydraulicProfileState.FREE_SURFACE
    assert profile.points[-1].state is HydraulicProfileState.PRESSURISED
    assert profile.points[-1].water_surface_elevation is None
    assert profile.points[-1].hydraulic_grade_elevation == pytest.approx(result.tailwater_elevation, abs=2e-6)
    assert profile.exit_loss == pytest.approx(losses.exit)
