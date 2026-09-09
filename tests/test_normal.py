"""Analytical, branch-selection, and contract tests for uniform-flow normal depth."""

import math

import pytest

from culvert_solver import (
    CircularGeometry,
    InvalidInputError,
    RectangularGeometry,
    calculate_normal_depth,
)


def test_rectangular_normal_depth_benchmark() -> None:
    # Benchmark box: span = 2.4 m, rise = 1.2 m
    box = RectangularGeometry(span=2.4, rise=1.2)
    s0 = 0.002
    n = 0.013
    # Fixed independent SI Manning fixture: A=1.44 m², R=0.4 m,
    # K=0.7817522735793332 m^(8/3), and Q=2.6893095773667723 m³/s.
    target_y = 0.6
    area = 1.44
    conveyance = 0.7817522735793332
    q = 2.6893095773667723

    result = calculate_normal_depth(box, discharge=q, slope=s0, roughness=n)
    assert result.depth == pytest.approx(target_y, abs=1e-6)
    assert result.velocity == pytest.approx(q / area, rel=1e-12)
    assert result.conveyance == pytest.approx(conveyance, rel=1e-12)
    assert not result.is_full
    assert not result.capacity_exceeded
    assert result.convergence is not None
    assert result.convergence.root == result.depth
    assert result.convergence.iterations > 0


def test_rectangular_normal_depth_capacity_exceeded() -> None:
    box = RectangularGeometry(span=1.0, rise=1.0)
    s0 = 0.001
    n = 0.013
    # Huge discharge exceeding gravity capacity of 1x1 box
    q = 50.0

    result = calculate_normal_depth(box, discharge=q, slope=s0, roughness=n)
    assert result.depth == 1.0
    assert result.is_full
    assert result.capacity_exceeded
    assert math.isnan(result.froude_number)


def test_circular_normal_depth_half_depth_benchmark() -> None:
    # Pipe diameter D = 1.2 m, target depth = 0.6 m (half depth)
    pipe = CircularGeometry(diameter=1.2)
    s0 = 0.0015
    n = 0.012
    target_y = 0.6
    a = math.pi * (1.2**2) / 8.0
    r = 1.2 / 4.0
    k_target = a * (r ** (2.0 / 3.0))
    q = (1.0 / n) * k_target * math.sqrt(s0)

    result = calculate_normal_depth(pipe, discharge=q, slope=s0, roughness=n)
    assert result.depth == pytest.approx(target_y, abs=1e-6)
    assert result.conveyance == pytest.approx(k_target, rel=1e-6)
    assert not result.is_full
    assert not result.capacity_exceeded
    assert result.convergence is not None
    assert result.convergence.root == result.depth


def test_circular_normal_depth_stable_branch_selection() -> None:
    # Full-pipe conveyance K_full occurs at full depth y=D, but open-channel conveyance
    # also equals K_full at y ≈ 0.82 * D. The solver must return the stable lower branch.
    d = 1.0
    pipe = CircularGeometry(diameter=d)
    s0 = 0.001
    n = 0.013
    k_full = pipe.area_full * (pipe.hydraulic_radius_full ** (2.0 / 3.0))
    q_full = (1.0 / n) * k_full * math.sqrt(s0)

    result = calculate_normal_depth(pipe, discharge=q_full, slope=s0, roughness=n)
    # The normal depth on the open-channel branch must be strictly below 0.938 * D
    assert result.depth < 0.938 * d
    # Specifically, it should be approximately 0.82 * D
    assert result.depth == pytest.approx(0.82 * d, abs=0.03)
    assert not result.is_full
    assert not result.capacity_exceeded


def test_circular_normal_depth_capacity_exceeded() -> None:
    pipe = CircularGeometry(diameter=1.0)
    s0 = 0.001
    n = 0.013
    # Discharge exceeding max open-channel conveyance (~1.0757 * Q_full)
    q_excessive = 100.0

    result = calculate_normal_depth(pipe, discharge=q_excessive, slope=s0, roughness=n)
    assert result.depth == 1.0
    assert result.is_full
    assert result.capacity_exceeded
    assert math.isnan(result.froude_number)


def test_zero_discharge_normal_depth() -> None:
    box = RectangularGeometry(span=2.0, rise=1.0)
    result = calculate_normal_depth(box, discharge=0.0, slope=0.002, roughness=0.013)
    assert result.depth == 0.0
    assert result.velocity == 0.0
    assert result.conveyance == 0.0
    assert not result.is_full
    assert not result.capacity_exceeded
    assert result.convergence is None


def test_zero_slope_with_positive_discharge_fails() -> None:
    box = RectangularGeometry(span=2.0, rise=1.0)
    with pytest.raises(InvalidInputError, match="zero slope"):
        calculate_normal_depth(box, discharge=1.0, slope=0.0, roughness=0.013)


@pytest.mark.parametrize(
    ("discharge", "slope", "roughness"),
    [
        (-1.0, 0.001, 0.013),
        (1.0, -0.001, 0.013),
        (1.0, 0.001, 0.0),
        (1.0, 0.001, -0.013),
    ],
)
def test_invalid_parameters_fail(discharge: float, slope: float, roughness: float) -> None:
    pipe = CircularGeometry(diameter=1.0)
    with pytest.raises(InvalidInputError):
        calculate_normal_depth(pipe, discharge=discharge, slope=slope, roughness=roughness)
