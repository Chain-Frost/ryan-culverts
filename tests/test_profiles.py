"""Tests for direct-step backwater profile solver and partial-flow outlet control."""

import pytest

from culvert_solver.exceptions import InvalidInputError
from culvert_solver.geometry.circular import CircularGeometry
from culvert_solver.geometry.rectangular import RectangularGeometry
from culvert_solver.hydraulics.critical import calculate_critical_depth
from culvert_solver.hydraulics.normal import calculate_normal_depth
from culvert_solver.models.barrel import CulvertBarrel
from culvert_solver.models.enums import ProfileCurve
from culvert_solver.models.tailwater import TailwaterCondition
from culvert_solver.outlet_control.losses import (
    BOX_CONCRETE_FLARED_WINGWALLS_30_75,
    PIPE_CONCRETE_SQUARE_EDGE,
)
from culvert_solver.outlet_control.partial_flow import (
    PartialFlowOutletResult,
    calculate_partial_flow_outlet_headwater,
)
from culvert_solver.profiles.direct_step import (
    InletControlProfile,
    WaterSurfaceProfile,
    compute_backwater_profile,
    compute_inlet_control_s2_profile,
    compute_steep_inlet_control_profile,
)


def test_inlet_control_s2_profile_routes_downstream() -> None:
    """An S2 profile falls from critical depth toward normal depth downstream."""
    geom = CircularGeometry(diameter=1.2)
    barrel = CulvertBarrel(
        geometry=geom,
        length=30.0,
        inlet_invert=10.0,
        outlet_invert=9.7,
        roughness=0.012,
    )
    q = 1.0
    critical = calculate_critical_depth(geom, q).depth
    normal = calculate_normal_depth(geom, q, barrel.slope, barrel.roughness).depth

    profile: InletControlProfile = compute_inlet_control_s2_profile(barrel, q)
    refined = compute_inlet_control_s2_profile(barrel, q, num_steps=400)

    assert profile.curve_type is ProfileCurve.S2
    assert profile.points[0].station == 0.0
    assert profile.points[-1].station == barrel.length
    assert profile.inlet_depth == pytest.approx(critical, rel=1e-6)
    assert normal < profile.outlet_depth < critical
    assert profile.outlet_depth == pytest.approx(refined.outlet_depth, abs=1e-3)
    assert refined.outlet_depth == pytest.approx(0.4136573803, abs=1e-6)
    assert all(
        first.station < second.station for first, second in zip(profile.points, profile.points[1:], strict=False)
    )
    assert all(
        first.water_depth > second.water_depth
        for first, second in zip(profile.points, profile.points[1:], strict=False)
    )


def test_inlet_control_s2_profile_rejects_nonsteep_slope() -> None:
    """S2 routing fails clearly when normal depth is not below critical depth."""
    barrel = CulvertBarrel(
        geometry=RectangularGeometry(span=2.0, rise=1.5),
        length=50.0,
        inlet_invert=10.0,
        outlet_invert=9.99,
        roughness=0.013,
    )

    with pytest.raises(InvalidInputError, match="normal depth below critical depth"):
        compute_inlet_control_s2_profile(barrel, 3.0)


def test_steep_profile_locates_in_barrel_hydraulic_jump() -> None:
    """S2 conjugate depth intersects an S1 tailwater profile inside the barrel."""
    barrel = CulvertBarrel(
        geometry=CircularGeometry(diameter=1.2),
        length=30.0,
        inlet_invert=10.0,
        outlet_invert=9.7,
        roughness=0.012,
    )

    profile = compute_steep_inlet_control_profile(barrel, 1.0, 10.45)
    refined = compute_steep_inlet_control_profile(barrel, 1.0, 10.45, num_steps=200)

    assert profile.curve_type is ProfileCurve.JS1
    assert profile.hydraulic_jump_swept_out is False
    assert profile.hydraulic_jump_station is not None
    assert 0.0 < profile.hydraulic_jump_station < barrel.length
    assert profile.hydraulic_jump_station == pytest.approx(
        refined.hydraulic_jump_station,
        abs=0.1,
    )
    assert refined.hydraulic_jump_station == pytest.approx(25.60633937, abs=5e-3)
    assert profile.outlet_depth == pytest.approx(0.75)
    jump_points = tuple(
        point for point in profile.points if point.station == pytest.approx(profile.hydraulic_jump_station)
    )
    assert len(jump_points) == 2
    assert jump_points[0].water_depth < jump_points[1].water_depth


def test_steep_profile_reports_s1_reaching_inlet() -> None:
    """A sufficiently high sub-crown boundary routes S1 to the inlet without a jump."""
    barrel = CulvertBarrel(
        geometry=CircularGeometry(diameter=1.2),
        length=30.0,
        inlet_invert=10.0,
        outlet_invert=9.7,
        roughness=0.012,
    )

    profile = compute_steep_inlet_control_profile(barrel, 1.0, 10.7)
    refined = compute_steep_inlet_control_profile(barrel, 1.0, 10.7, num_steps=800)

    assert profile.curve_type is ProfileCurve.S1
    assert profile.hydraulic_jump_station is None
    assert profile.hydraulic_jump_swept_out is False
    assert profile.points[0].station == 0.0
    assert profile.outlet_depth == pytest.approx(1.0)
    assert refined.inlet_depth == pytest.approx(0.6439884203, abs=1e-6)


def test_m2_drawdown_profile_box() -> None:
    """Verify M2 drawdown profile on mild slope with tailwater below critical depth."""
    geom = RectangularGeometry.from_mm(span_mm=2000.0, rise_mm=1500.0)
    barrel = CulvertBarrel(
        geometry=geom,
        length=50.0,
        inlet_invert=10.0,
        outlet_invert=9.9,  # S0 = 0.1 / 50 = 0.002
        roughness=0.013,
    )
    q = 3.0
    tw_elev = 9.9  # Tailwater depth = 0.0 (at outlet invert)

    crit = calculate_critical_depth(geom, q)
    norm = calculate_normal_depth(geom, q, barrel.slope, barrel.roughness)
    yc = crit.depth
    yn = norm.depth
    assert yn > yc  # Mild slope

    profile: WaterSurfaceProfile = compute_backwater_profile(
        barrel=barrel,
        discharge=q,
        tailwater=tw_elev,
        entrance_loss_coefficient=0.4,
    )
    refined = compute_backwater_profile(
        barrel=barrel,
        discharge=q,
        tailwater=tw_elev,
        entrance_loss_coefficient=0.4,
        num_steps=800,
    )

    assert profile.curve_type == "M2"
    assert not profile.is_full_flow
    assert len(profile.points) >= 5

    # Station ordering: first point is inlet (x = 0.0), last point is outlet (x = 50.0)
    assert profile.points[0].station == pytest.approx(0.0, abs=1e-6)
    assert profile.points[-1].station == pytest.approx(50.0, abs=1e-6)

    # In an M2 profile, depth increases going upstream (y_inlet > y_outlet = yc)
    assert profile.outlet_depth == pytest.approx(yc, rel=1e-5)
    assert profile.inlet_depth > profile.outlet_depth
    assert profile.inlet_depth <= yn
    assert refined.inlet_depth == pytest.approx(0.7301922412, abs=1e-6)

    # Headwater depth and elevation accounting
    vin = profile.inlet_velocity
    hv_in = (vin * vin) / (2.0 * 9.80665)
    he_expected = 0.4 * hv_in
    assert profile.inlet_headwater_depth == pytest.approx(profile.inlet_depth + hv_in + he_expected, rel=1e-6)
    assert profile.inlet_headwater_elevation == pytest.approx(10.0 + profile.inlet_headwater_depth, rel=1e-6)


def test_m1_backwater_profile_box() -> None:
    """Verify M1 backwater curve on mild slope with high tailwater (TW > yn)."""
    geom = RectangularGeometry.from_mm(span_mm=2000.0, rise_mm=1500.0)
    barrel = CulvertBarrel(
        geometry=geom,
        length=60.0,
        inlet_invert=20.0,
        outlet_invert=19.88,  # S0 = 0.12 / 60 = 0.002
        roughness=0.013,
    )
    q = 3.0
    norm = calculate_normal_depth(geom, q, barrel.slope, barrel.roughness)
    yn = norm.depth

    # Set tailwater higher than normal depth, but below crown (crown is at 19.88 + 1.5 = 21.38)
    tw_elev = 19.88 + yn + 0.3
    tw_depth = yn + 0.3

    profile = compute_backwater_profile(
        barrel=barrel,
        discharge=q,
        tailwater=tw_elev,
        entrance_loss_coefficient=BOX_CONCRETE_FLARED_WINGWALLS_30_75,
    )
    refined = compute_backwater_profile(
        barrel=barrel,
        discharge=q,
        tailwater=tw_elev,
        entrance_loss_coefficient=BOX_CONCRETE_FLARED_WINGWALLS_30_75,
        num_steps=800,
    )

    assert profile.curve_type == "M1"
    assert not profile.is_full_flow
    assert profile.outlet_depth == pytest.approx(tw_depth, rel=1e-5)

    # On M1 curve, depth decreases going upstream towards normal depth (y_inlet < y_outlet)
    assert profile.inlet_depth < profile.outlet_depth
    assert profile.inlet_depth >= yn
    assert refined.inlet_depth == pytest.approx(0.9790035248, abs=1e-6)


def test_h2_profile_horizontal_circular() -> None:
    """Verify H2 drawdown profile in a horizontal circular culvert (S0 = 0)."""
    geom = CircularGeometry.from_mm(diameter_mm=1200.0)
    barrel = CulvertBarrel(
        geometry=geom,
        length=40.0,
        inlet_invert=15.0,
        outlet_invert=15.0,
        roughness=0.012,
    )
    assert barrel.is_horizontal

    q = 1.5
    tw_elev = 15.0  # Free outfall at invert

    crit = calculate_critical_depth(geom, q)
    yc = crit.depth

    profile = compute_backwater_profile(
        barrel=barrel,
        discharge=q,
        tailwater=TailwaterCondition(elevation=tw_elev),
        entrance_loss_coefficient=PIPE_CONCRETE_SQUARE_EDGE,
    )
    refined = compute_backwater_profile(
        barrel=barrel,
        discharge=q,
        tailwater=TailwaterCondition(elevation=tw_elev),
        entrance_loss_coefficient=PIPE_CONCRETE_SQUARE_EDGE,
        num_steps=800,
    )

    assert profile.curve_type == "H2"
    assert not profile.is_full_flow
    assert profile.outlet_depth == pytest.approx(yc, rel=1e-5)
    # Depth increases going upstream in horizontal barrel
    assert profile.inlet_depth > profile.outlet_depth
    assert refined.inlet_depth == pytest.approx(0.8774316585, abs=1e-6)


def test_long_barrel_reaches_normal_depth() -> None:
    """Verify long barrel asymptotically approaches normal depth."""
    geom = RectangularGeometry.from_mm(span_mm=1500.0, rise_mm=1200.0)
    barrel = CulvertBarrel(
        geometry=geom,
        length=500.0,  # Very long barrel
        inlet_invert=50.0,
        outlet_invert=48.5,  # S0 = 1.5 / 500 = 0.003
        roughness=0.013,
    )
    q = 2.0
    tw_elev = 48.5

    norm = calculate_normal_depth(geom, q, barrel.slope, barrel.roughness)
    yn = norm.depth

    profile = compute_backwater_profile(
        barrel=barrel,
        discharge=q,
        tailwater=tw_elev,
        entrance_loss_coefficient=0.5,
    )

    assert profile.reaches_normal_depth
    assert profile.inlet_depth == pytest.approx(yn, rel=1e-3)


def test_m2_profile_continues_as_full_flow_to_inlet() -> None:
    """An M2 curve reaching the crown charges friction over the full upstream reach."""
    barrel = CulvertBarrel(
        geometry=CircularGeometry(diameter=1.2),
        length=100.0,
        inlet_invert=10.0,
        outlet_invert=9.9,
        roughness=0.012,
    )

    profile = compute_backwater_profile(
        barrel,
        3.0,
        9.9,
        entrance_loss_coefficient=0.5,
    )

    assert profile.curve_type is ProfileCurve.M2
    assert profile.is_full_flow is False
    refined = compute_backwater_profile(
        barrel,
        3.0,
        9.9,
        entrance_loss_coefficient=0.5,
        num_steps=800,
    )

    # Independent composite-Simpson integration of
    # dx/dy=(1-Fr²)/(S0-Sf) gives station 68.4449163 m at y=D.
    assert profile.full_flow_length == pytest.approx(68.46, abs=0.02)
    assert refined.full_flow_length == pytest.approx(68.4449163, abs=5e-4)
    assert profile.full_flow_length == pytest.approx(refined.full_flow_length, abs=0.02)
    assert not profile.reaches_normal_depth
    assert profile.inlet_depth == barrel.geometry.rise
    assert profile.points[0].froude_number is None
    assert profile.inlet_headwater_elevation == pytest.approx(12.015, abs=0.001)


def test_backwater_profile_rejects_submerged_outlet_inference() -> None:
    """A submerged outlet alone cannot force a whole-barrel full-flow profile."""
    geom = CircularGeometry.from_mm(diameter_mm=1000.0)
    barrel = CulvertBarrel(
        geometry=geom,
        length=50.0,
        inlet_invert=10.0,
        outlet_invert=9.8,
        roughness=0.013,
    )
    # Outlet crown is at 9.8 + 1.0 = 10.8 m. Tailwater at 11.2 m is fully submerged.
    tw_elev = 11.2

    with pytest.raises(InvalidInputError, match="does not infer full-barrel flow"):
        compute_backwater_profile(
            barrel=barrel,
            discharge=1.8,
            tailwater=tw_elev,
            entrance_loss_coefficient=0.5,
        )


def test_calculate_partial_flow_outlet_headwater() -> None:
    """Verify calculate_partial_flow_outlet_headwater solver wrapper."""
    geom = RectangularGeometry.from_mm(span_mm=2400.0, rise_mm=1800.0)
    barrel = CulvertBarrel(
        geometry=geom,
        length=45.0,
        inlet_invert=30.0,
        outlet_invert=29.85,
        roughness=0.013,
    )
    q = 5.0
    tw_elev = 30.2  # tw_depth = 30.2 - 29.85 = 0.35 m

    res: PartialFlowOutletResult = calculate_partial_flow_outlet_headwater(
        barrel=barrel,
        discharge=q,
        tailwater=tw_elev,
        entrance_loss_coefficient=0.4,
    )

    assert res.barrel_rise == 1.8
    assert res.tailwater_depth == pytest.approx(0.35, abs=1e-6)
    assert res.inlet_depth > 0
    assert res.headwater_elevation > 30.0
    assert res.headwater_depth == pytest.approx(res.headwater_elevation - 30.0, abs=1e-9)
    assert res.entrance_loss >= 0.0


def test_profile_validation_errors() -> None:
    """Verify input validation errors for profile calculation."""
    geom = CircularGeometry.from_mm(diameter_mm=1000.0)
    barrel = CulvertBarrel(
        geometry=geom,
        length=50.0,
        inlet_invert=10.0,
        outlet_invert=9.8,
        roughness=0.013,
    )

    # Nonpositive discharge
    with pytest.raises(InvalidInputError, match="discharge must be strictly positive"):
        compute_backwater_profile(
            barrel=barrel,
            discharge=0.0,
            tailwater=10.0,
            entrance_loss_coefficient=0.5,
        )

    # Step count < 5
    with pytest.raises(InvalidInputError, match="num_steps must be at least 5"):
        compute_backwater_profile(
            barrel=barrel,
            discharge=1.0,
            tailwater=10.0,
            entrance_loss_coefficient=0.5,
            num_steps=3,
        )

    # Negative entrance loss coefficient
    with pytest.raises(InvalidInputError, match="entrance_loss_coefficient must be nonnegative"):
        compute_backwater_profile(
            barrel=barrel,
            discharge=1.0,
            tailwater=10.0,
            entrance_loss_coefficient=-0.5,
        )
