"""Tests for outlet control loss coefficients and full-flow hydraulic solver."""

from typing import cast

import pytest

from culvert_solver.exceptions import InvalidInputError
from culvert_solver.geometry.circular import CircularGeometry
from culvert_solver.geometry.rectangular import RectangularGeometry
from culvert_solver.hydraulics.critical import calculate_critical_depth
from culvert_solver.models.barrel import CulvertBarrel
from culvert_solver.models.enums import GeometryShape
from culvert_solver.models.tailwater import TailwaterCondition
from culvert_solver.outlet_control.full_flow import (
    FullFlowOutletResult,
    calculate_full_flow_outlet_headwater,
)
from culvert_solver.outlet_control.losses import (
    BOX_CONCRETE_FLARED_WINGWALLS_30_75,
    BOX_CONCRETE_HEADWALL_SQUARE,
    BOX_CONCRETE_PARALLEL_WINGWALLS_0,
    PIPE_CMP_HEADWALL,
    PIPE_CMP_PROJECTING,
    PIPE_CONCRETE_SOCKET_END,
    PIPE_CONCRETE_SQUARE_EDGE,
    STANDARD_EXIT_LOSS_COEFFICIENT,
    EntranceLossCoefficient,
    calculate_entrance_loss,
    calculate_exit_loss,
    calculate_friction_loss,
    calculate_total_head_loss,
)


def test_entrance_loss_coefficients_standards() -> None:
    """Verify standard entrance loss coefficients match HDS-5 Table C.2."""
    assert PIPE_CONCRETE_SQUARE_EDGE.ke == 0.5
    assert PIPE_CONCRETE_SQUARE_EDGE.shape == "circular"
    assert PIPE_CONCRETE_SOCKET_END.ke == 0.2

    assert PIPE_CMP_PROJECTING.ke == 0.9
    assert PIPE_CMP_HEADWALL.ke == 0.5

    assert BOX_CONCRETE_FLARED_WINGWALLS_30_75.ke == 0.4
    assert BOX_CONCRETE_FLARED_WINGWALLS_30_75.shape == "rectangular"
    assert BOX_CONCRETE_HEADWALL_SQUARE.ke == 0.5
    assert BOX_CONCRETE_PARALLEL_WINGWALLS_0.ke == 0.7

    assert STANDARD_EXIT_LOSS_COEFFICIENT == 1.0


def test_entrance_loss_coefficient_validation() -> None:
    """Verify validation on EntranceLossCoefficient."""
    with pytest.raises(InvalidInputError, match="name must be nonempty"):
        EntranceLossCoefficient(name="  ", ke=0.5)

    with pytest.raises(InvalidInputError, match="ke must be nonnegative"):
        EntranceLossCoefficient(name="Invalid Ke", ke=-0.1)

    with pytest.raises(InvalidInputError, match="shape must be"):
        EntranceLossCoefficient(
            name="Invalid Shape", ke=0.5, shape=cast(GeometryShape, "trapezoidal")
        )


def test_entrance_loss_shape_mismatch_is_rejected() -> None:
    """A pipe loss coefficient cannot silently apply to a box culvert."""
    barrel = CulvertBarrel(
        geometry=RectangularGeometry(span=2.0, rise=1.0),
        length=20.0,
        inlet_invert=10.0,
        outlet_invert=9.8,
        roughness=0.013,
    )
    with pytest.raises(InvalidInputError, match="cannot be used"):
        calculate_full_flow_outlet_headwater(barrel, 1.0, 9.8, PIPE_CONCRETE_SQUARE_EDGE)


def test_loss_calculation_functions() -> None:
    """Verify individual and total head loss functions."""
    hv = 0.4
    ke = 0.5
    length = 50.0
    sf = 0.004

    he = calculate_entrance_loss(velocity_head=hv, ke=ke)
    assert he == pytest.approx(0.2, abs=1e-9)

    hf = calculate_friction_loss(length=length, friction_slope=sf)
    assert hf == pytest.approx(0.2, abs=1e-9)

    ho = calculate_exit_loss(velocity_head=hv, ko=1.0)
    assert ho == pytest.approx(0.4, abs=1e-9)

    total_h = calculate_total_head_loss(entrance_loss=he, friction_loss=hf, exit_loss=ho)
    assert total_h == pytest.approx(0.8, abs=1e-9)


def test_loss_calculation_validation() -> None:
    """Verify loss calculation functions reject negative inputs."""
    with pytest.raises(InvalidInputError):
        calculate_total_head_loss(-0.1, 0.2, 0.2)
    with pytest.raises(InvalidInputError):
        calculate_total_head_loss(0.1, -0.2, 0.2)
    with pytest.raises(InvalidInputError):
        calculate_total_head_loss(0.1, 0.2, -0.2)


def test_full_flow_circular_submerged_outlet() -> None:
    """Verify full-flow outlet control for circular culvert with submerged tailwater."""
    geom = CircularGeometry.from_mm(diameter_mm=1000.0)
    barrel = CulvertBarrel(
        geometry=geom,
        length=100.0,
        inlet_invert=10.0,
        outlet_invert=9.5,
        roughness=0.013,
    )
    q = 2.0
    tw_elev = 11.0  # Outlet crown is at 9.5 + 1.0 = 10.5 m, so 11.0 m is submerged

    result: FullFlowOutletResult = calculate_full_flow_outlet_headwater(
        barrel=barrel,
        discharge=q,
        tailwater=tw_elev,
        entrance_loss_coefficient=PIPE_CONCRETE_SQUARE_EDGE,
    )

    # Hand calculation:
    # A = pi * 0.5^2 = 0.785398 m^2
    # V = 2.0 / A = 2.546479 m/s
    # hv = V^2 / (2 * 9.80665) = 0.330620 m
    # P = pi * 1.0 = 3.141593 m
    # R = 0.25 m
    # Sf = (0.013 * 2.0 / (A * 0.25^(2/3)))^2 = 0.00695848
    # hf = 100 * Sf = 0.695848 m
    # he = 0.5 * hv = 0.165310 m
    # ho = 1.0 * hv = 0.330620 m
    # H = 1.191778 m
    # Fixed independently from HDS-5 Equations 3.1-3.5, printed pages
    # 3.9-3.10, using g=9.80665 m/s².
    v_expected = 2.5464790894703255
    hv_expected = 0.3306203317702589
    hf_expected = 0.6958467261846067
    he_expected = 0.16531016588512945
    ho_expected = 0.3306203317702589
    h_total_expected = 1.191777223839995

    assert geom.area_full == pytest.approx(0.7853981633974483, rel=1e-14)
    assert geom.hydraulic_radius_full == pytest.approx(0.25, rel=1e-14)
    assert result.velocity == pytest.approx(v_expected, rel=1e-12)
    assert result.velocity_head == pytest.approx(hv_expected, rel=1e-12)
    assert result.friction_loss == pytest.approx(hf_expected, rel=1e-12)
    assert result.entrance_loss == pytest.approx(he_expected, rel=1e-12)
    assert result.exit_loss == pytest.approx(ho_expected, rel=1e-12)
    assert result.total_head_loss == pytest.approx(h_total_expected, rel=1e-12)

    # Submerged tailwater depth = 11.0 - 9.5 = 1.5 m > D (1.0 m)
    assert result.tailwater_depth == pytest.approx(1.5, abs=1e-6)
    assert result.effective_tailwater_depth == pytest.approx(1.5, abs=1e-6)
    assert result.hydraulic_grade_elevation_outlet == pytest.approx(11.0, abs=1e-6)

    # HW_elev = HGL_out + H = 11.0 + H
    assert result.headwater_elevation == pytest.approx(11.0 + h_total_expected, rel=1e-5)
    # HW_depth = HW_elev - 10.0
    assert result.headwater_depth == pytest.approx(1.0 + h_total_expected, rel=1e-5)


def test_full_flow_circular_unsubmerged_effective_tw() -> None:
    """Verify effective tailwater approximation ho = (dc + D)/2 when TW is low."""
    geom = CircularGeometry.from_mm(diameter_mm=1200.0)
    d = 1.2
    barrel = CulvertBarrel(
        geometry=geom,
        length=50.0,
        inlet_invert=100.0,
        outlet_invert=99.5,
        roughness=0.012,
    )
    q = 2.5
    # Low tailwater below outlet invert
    tw_elev = 99.0

    crit = calculate_critical_depth(geom, q)
    dc = crit.depth
    ho_eff_expected = (dc + d) / 2.0

    result: FullFlowOutletResult = calculate_full_flow_outlet_headwater(
        barrel=barrel,
        discharge=q,
        tailwater=TailwaterCondition(elevation=tw_elev),
        entrance_loss_coefficient=0.5,
    )

    assert result.tailwater_depth == 0.0
    assert result.critical_depth == pytest.approx(dc, rel=1e-6)
    assert result.effective_tailwater_depth == pytest.approx(ho_eff_expected, rel=1e-6)
    assert result.hydraulic_grade_elevation_outlet == pytest.approx(
        99.5 + ho_eff_expected, rel=1e-6
    )
    assert result.headwater_elevation == pytest.approx(
        99.5 + ho_eff_expected + result.total_head_loss, rel=1e-6
    )
    assert result.headwater_depth == pytest.approx(result.headwater_elevation - 100.0, rel=1e-6)


def test_full_flow_rectangular_box() -> None:
    """Verify full-flow outlet control for rectangular concrete box culvert."""
    geom = RectangularGeometry.from_mm(span_mm=2400.0, rise_mm=1800.0)
    barrel = CulvertBarrel(
        geometry=geom,
        length=60.0,
        inlet_invert=50.0,
        outlet_invert=49.7,
        roughness=0.012,
    )
    q = 12.0
    tw_elev = 52.0  # outlet invert is 49.7, crown is 49.7 + 1.8 = 51.5, so 52.0 is submerged

    result = calculate_full_flow_outlet_headwater(
        barrel=barrel,
        discharge=q,
        tailwater=tw_elev,
        entrance_loss_coefficient=BOX_CONCRETE_FLARED_WINGWALLS_30_75,
    )

    area = 2.4 * 1.8
    perimeter = 2.0 * (2.4 + 1.8)
    r = area / perimeter
    v = q / area
    hv = (v * v) / (2.0 * 9.80665)
    sf = (0.012 * q / (area * (r ** (2.0 / 3.0)))) ** 2

    assert result.velocity == pytest.approx(v, rel=1e-5)
    assert result.velocity_head == pytest.approx(hv, rel=1e-5)
    assert result.entrance_loss == pytest.approx(0.4 * hv, rel=1e-5)
    assert result.friction_loss == pytest.approx(60.0 * sf, rel=1e-5)
    assert result.exit_loss == pytest.approx(1.0 * hv, rel=1e-5)
    assert result.headwater_elevation == pytest.approx(tw_elev + result.total_head_loss, rel=1e-5)


def test_full_flow_horizontal_barrel() -> None:
    """Verify full-flow calculation supports horizontal barrels (S0 = 0)."""
    geom = CircularGeometry.from_mm(diameter_mm=1000.0)
    barrel = CulvertBarrel(
        geometry=geom,
        length=40.0,
        inlet_invert=20.0,
        outlet_invert=20.0,
        roughness=0.013,
    )
    assert barrel.is_horizontal
    assert barrel.slope == 0.0

    tw_elev = 21.5  # Submerged (crown is at 21.0)
    result = calculate_full_flow_outlet_headwater(
        barrel=barrel,
        discharge=1.8,
        tailwater=tw_elev,
        entrance_loss_coefficient=0.5,
    )

    # For horizontal barrel, inlet_invert == outlet_invert:
    # HW = HW_elev - 20.0 = (21.5 + H) - 20.0 = 1.5 + H
    assert result.headwater_depth == pytest.approx(1.5 + result.total_head_loss, rel=1e-6)
    assert result.headwater_elevation == pytest.approx(21.5 + result.total_head_loss, rel=1e-6)


def test_full_flow_input_validation() -> None:
    """Verify input validation and error raising."""
    geom = CircularGeometry.from_mm(diameter_mm=1000.0)
    barrel = CulvertBarrel(
        geometry=geom,
        length=50.0,
        inlet_invert=10.0,
        outlet_invert=9.5,
        roughness=0.013,
    )

    # Zero or negative discharge
    with pytest.raises(InvalidInputError, match="discharge must be strictly positive"):
        calculate_full_flow_outlet_headwater(
            barrel=barrel,
            discharge=0.0,
            tailwater=10.0,
            entrance_loss_coefficient=0.5,
        )

    with pytest.raises(InvalidInputError, match="discharge must be strictly positive"):
        calculate_full_flow_outlet_headwater(
            barrel=barrel,
            discharge=-1.5,
            tailwater=10.0,
            entrance_loss_coefficient=0.5,
        )

    # Negative Ke
    with pytest.raises(InvalidInputError, match="entrance_loss_coefficient must be nonnegative"):
        calculate_full_flow_outlet_headwater(
            barrel=barrel,
            discharge=2.0,
            tailwater=10.0,
            entrance_loss_coefficient=-0.2,
        )

    # Negative Ko
    with pytest.raises(InvalidInputError, match="exit_loss_coefficient must be nonnegative"):
        calculate_full_flow_outlet_headwater(
            barrel=barrel,
            discharge=2.0,
            tailwater=10.0,
            entrance_loss_coefficient=0.5,
            exit_loss_coefficient=-1.0,
        )
