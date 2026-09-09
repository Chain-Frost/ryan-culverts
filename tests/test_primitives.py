"""Analytical and contract tests for SI hydraulic primitives."""

import math

import pytest

from culvert_solver import (
    GRAVITATIONAL_ACCELERATION,
    InvalidInputError,
    cross_section_velocity,
    friction_head_loss,
    froude_number,
    manning_discharge,
    manning_friction_slope,
    minor_head_loss,
    specific_energy,
    velocity_head,
)


def test_velocity_calculation() -> None:
    assert cross_section_velocity(discharge=10.0, area=2.5) == pytest.approx(4.0)
    assert cross_section_velocity(discharge=0.0, area=2.5) == pytest.approx(0.0)
    assert cross_section_velocity(discharge=-5.0, area=2.5) == pytest.approx(-2.0)

    with pytest.raises(InvalidInputError, match="area"):
        cross_section_velocity(discharge=1.0, area=0.0)
    with pytest.raises(InvalidInputError, match="area"):
        cross_section_velocity(discharge=1.0, area=-1.0)
    with pytest.raises(InvalidInputError):
        cross_section_velocity(discharge=math.nan, area=1.0)


def test_velocity_head_calculation() -> None:
    v = 4.0
    expected = (4.0 * 4.0) / (2.0 * GRAVITATIONAL_ACCELERATION)
    assert velocity_head(velocity=v) == pytest.approx(expected)
    assert velocity_head(velocity=0.0) == 0.0
    assert velocity_head(velocity=-v) == pytest.approx(expected)

    with pytest.raises(InvalidInputError, match="g"):
        velocity_head(velocity=v, g=0.0)
    with pytest.raises(InvalidInputError, match="g"):
        velocity_head(velocity=v, g=-9.8)


def test_specific_energy_calculation() -> None:
    hv = 0.5
    y = 1.2
    assert specific_energy(depth=y, velocity_head=hv) == pytest.approx(1.7)

    with pytest.raises(InvalidInputError, match="depth"):
        specific_energy(depth=-0.1, velocity_head=hv)
    with pytest.raises(InvalidInputError, match="velocity_head"):
        specific_energy(depth=y, velocity_head=-0.1)


def test_froude_number_analytical_and_critical_flow() -> None:
    # In a rectangular channel of width B, critical depth yc = (q^2 / g)^(1/3)
    b = 2.0
    q = 6.0  # discharge
    q_unit = q / b  # 3.0 m^2/s
    g = GRAVITATIONAL_ACCELERATION
    yc = (q_unit**2 / g) ** (1.0 / 3.0)
    area_c = b * yc
    top_width_c = b

    # At critical depth, Fr must be exactly 1.0
    fr_critical = froude_number(discharge=q, area=area_c, top_width=top_width_c, g=g)
    assert fr_critical == pytest.approx(1.0, rel=1e-12)

    # Subcritical flow (y > yc -> Fr < 1)
    fr_subcritical = froude_number(discharge=q, area=b * (yc * 1.5), top_width=b, g=g)
    assert fr_subcritical < 1.0

    # Supercritical flow (y < yc -> Fr > 1)
    fr_supercritical = froude_number(discharge=q, area=b * (yc * 0.7), top_width=b, g=g)
    assert fr_supercritical > 1.0


def test_froude_number_closed_conduit_failure() -> None:
    with pytest.raises(InvalidInputError, match="top_width"):
        froude_number(discharge=5.0, area=2.0, top_width=0.0)
    with pytest.raises(InvalidInputError, match="top_width"):
        froude_number(discharge=5.0, area=2.0, top_width=-1.0)


def test_manning_discharge_and_friction_slope_consistency() -> None:
    # Benchmark rectangular channel
    # Width = 2.0 m, depth = 1.0 m -> Area = 2.0 m², Perimeter = 4.0 m, Hydraulic Radius = 0.5 m
    area = 2.0
    r = 0.5
    s0 = 0.002
    n = 0.015

    q = manning_discharge(area=area, hydraulic_radius=r, slope=s0, roughness=n)
    expected_q = (1.0 / n) * area * (r ** (2.0 / 3.0)) * math.sqrt(s0)
    assert q == pytest.approx(expected_q)

    # Normal slope: solving friction slope for this discharge should return s0 exactly
    sf = manning_friction_slope(discharge=q, area=area, hydraulic_radius=r, roughness=n)
    assert sf == pytest.approx(s0, rel=1e-12)

    # Zero values
    assert manning_discharge(area=0.0, hydraulic_radius=r, slope=s0, roughness=n) == 0.0
    assert manning_discharge(area=area, hydraulic_radius=0.0, slope=s0, roughness=n) == 0.0
    assert manning_discharge(area=area, hydraulic_radius=r, slope=0.0, roughness=n) == 0.0
    assert manning_friction_slope(discharge=0.0, area=area, hydraulic_radius=r, roughness=n) == 0.0


@pytest.mark.parametrize(
    "kwargs",
    [
        {"area": -1.0, "hydraulic_radius": 0.5, "slope": 0.001, "roughness": 0.013},
        {"area": 2.0, "hydraulic_radius": -0.5, "slope": 0.001, "roughness": 0.013},
        {"area": 2.0, "hydraulic_radius": 0.5, "slope": -0.001, "roughness": 0.013},
        {"area": 2.0, "hydraulic_radius": 0.5, "slope": 0.001, "roughness": 0.0},
        {"area": 2.0, "hydraulic_radius": 0.5, "slope": 0.001, "roughness": -0.013},
    ],
)
def test_manning_discharge_invalid_inputs(kwargs: dict[str, float]) -> None:
    with pytest.raises(InvalidInputError):
        manning_discharge(**kwargs)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"discharge": 1.0, "area": 0.0, "hydraulic_radius": 0.5, "roughness": 0.013},
        {"discharge": 1.0, "area": 1.0, "hydraulic_radius": 0.0, "roughness": 0.013},
        {"discharge": 1.0, "area": 1.0, "hydraulic_radius": 0.5, "roughness": 0.0},
        {"discharge": 1.0, "area": 1.0, "hydraulic_radius": 0.5, "roughness": -0.013},
    ],
)
def test_manning_friction_slope_invalid_inputs(kwargs: dict[str, float]) -> None:
    with pytest.raises(InvalidInputError):
        manning_friction_slope(**kwargs)


def test_head_loss_calculations() -> None:
    assert friction_head_loss(length=50.0, friction_slope=0.004) == pytest.approx(0.2)
    assert minor_head_loss(loss_coefficient=0.5, velocity_head=0.4) == pytest.approx(0.2)

    with pytest.raises(InvalidInputError):
        friction_head_loss(length=-1.0, friction_slope=0.001)
    with pytest.raises(InvalidInputError):
        friction_head_loss(length=10.0, friction_slope=-0.001)
    with pytest.raises(InvalidInputError):
        minor_head_loss(loss_coefficient=-0.5, velocity_head=0.4)
    with pytest.raises(InvalidInputError):
        minor_head_loss(loss_coefficient=0.5, velocity_head=-0.4)
