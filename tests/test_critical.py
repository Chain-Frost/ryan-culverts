"""Analytical, energy-minimization, and contract tests for critical depth."""

import math

import pytest

from culvert_solver import (
    GRAVITATIONAL_ACCELERATION,
    CircularGeometry,
    InvalidInputError,
    RectangularGeometry,
    calculate_critical_depth,
)


def test_rectangular_critical_depth_analytical() -> None:
    # Width = 2.0 m, Rise = 2.0 m, Q = 6.0 m³/s
    # Fixed independently from HDS-5 critical-flow relationships using
    # b=2.0 m, Q=6.0 m³/s, and g=9.80665 m/s².
    box = RectangularGeometry(span=2.0, rise=2.0)
    q = 6.0
    expected_yc = 0.9717933987105833
    expected_specific_energy = 1.457690098065875

    result = calculate_critical_depth(box, discharge=q)
    assert result.depth == pytest.approx(expected_yc, rel=1e-12)
    assert result.froude_number == pytest.approx(1.0, rel=1e-10)
    assert not result.is_submerged
    assert result.specific_energy == pytest.approx(expected_specific_energy, rel=1e-12)


def test_rectangular_critical_depth_submerged_crown() -> None:
    # Small box with large flow: critical depth exceeds rise
    box = RectangularGeometry(span=1.0, rise=1.0)
    g = GRAVITATIONAL_ACCELERATION
    q = 10.0
    expected_yc = (q**2 / g) ** (1.0 / 3.0)  # > 2.0 m

    result = calculate_critical_depth(box, discharge=q)
    assert result.depth == pytest.approx(expected_yc, rel=1e-12)
    assert result.is_submerged
    assert math.isnan(result.froude_number)


def test_circular_critical_depth_known_half_depth_solution() -> None:
    # Circular pipe of diameter D = 1.0 m.
    # When yc = 0.5 m (half full): Area = pi/8, Top width = 1.0 m.
    # At critical flow Fr = 1.0: Q = sqrt(g * A³ / T).
    d = 1.0
    pipe = CircularGeometry(diameter=d)
    g = GRAVITATIONAL_ACCELERATION
    area_half = math.pi / 8.0
    top_width_half = 1.0
    q_target = math.sqrt(g * (area_half**3) / top_width_half)

    result = calculate_critical_depth(pipe, discharge=q_target)
    assert result.depth == pytest.approx(0.5, abs=1e-6)
    assert result.froude_number == pytest.approx(1.0, rel=1e-6)
    assert not result.is_submerged
    assert result.convergence is not None
    assert result.convergence.root == result.depth
    assert result.convergence.iterations > 0


def test_circular_critical_depth_energy_minimization() -> None:
    # Specific energy must be at a local minimum at yc
    d = 1.5
    pipe = CircularGeometry(diameter=d)
    g = GRAVITATIONAL_ACCELERATION
    q = 2.5

    result = calculate_critical_depth(pipe, discharge=q)
    yc = result.depth
    ec = result.specific_energy
    assert result.froude_number == pytest.approx(1.0, rel=1e-6)

    # Check that E(yc - delta) > Ec and E(yc + delta) > Ec
    delta = 0.005
    for y_perturbed in (yc - delta, yc + delta):
        a = pipe.area(y_perturbed)
        v = q / a
        hv = (v * v) / (2.0 * g)
        e_perturbed = y_perturbed + hv
        assert e_perturbed > ec


def test_zero_discharge_critical_depth() -> None:
    box = RectangularGeometry(span=2.0, rise=1.0)
    result = calculate_critical_depth(box, discharge=0.0)
    assert result.depth == 0.0
    assert result.specific_energy == 0.0
    assert result.froude_number == 0.0
    assert not result.is_submerged
    assert result.convergence is None


@pytest.mark.parametrize("val", [-1.0, math.nan, math.inf])
def test_invalid_discharge_fails(val: float) -> None:
    pipe = CircularGeometry(diameter=1.0)
    with pytest.raises(InvalidInputError):
        calculate_critical_depth(pipe, discharge=val)


@pytest.mark.parametrize("g_val", [0.0, -9.8, math.nan])
def test_invalid_gravity_fails(g_val: float) -> None:
    pipe = CircularGeometry(diameter=1.0)
    with pytest.raises(InvalidInputError):
        calculate_critical_depth(pipe, discharge=1.0, g=g_val)
