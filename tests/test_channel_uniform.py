"""Independent Manning fixtures for open-channel normal depth."""

import pytest

from culvert_solver import (
    InvalidInputError,
    RectangularChannel,
    TrapezoidalChannel,
    calculate_channel_normal_depth,
)


@pytest.mark.parametrize(
    ("section", "discharge", "slope", "roughness", "expected_depth"),
    [
        (RectangularChannel(5.0), 4.211434583596904, 0.001, 0.03, 1.0),
        (TrapezoidalChannel(3.0, 2.0, 2.0), 3.2256777519932003, 0.0015, 0.03, 0.8),
        (TrapezoidalChannel(4.0, 3.0, 2.0), 9.26246172103823, 0.002, 0.035, 1.2),
        (TrapezoidalChannel(0.0, 1.0, 2.0), 2.342083113322061, 0.003, 0.025, 1.1),
    ],
)
def test_normal_depth_independent_fixtures(
    section: RectangularChannel | TrapezoidalChannel,
    discharge: float,
    slope: float,
    roughness: float,
    expected_depth: float,
) -> None:
    result = calculate_channel_normal_depth(section, discharge, slope, roughness)
    assert result.depth == pytest.approx(expected_depth, abs=1e-7)
    assert result.convergence is not None


def test_asymmetric_fixture_reports_section_factor_and_true_conveyance() -> None:
    result = calculate_channel_normal_depth(
        TrapezoidalChannel(4.0, 3.0, 2.0),
        discharge=9.26246172103823,
        friction_slope=0.002,
        roughness=0.035,
    )
    assert result.section_factor == pytest.approx(7.249022916530912, rel=1e-9)
    assert result.conveyance == pytest.approx(207.11494047231177, rel=1e-9)
    assert result.froude_number == pytest.approx(0.3841909755604328, rel=1e-9)


def test_normal_depth_expands_small_initial_bracket() -> None:
    result = calculate_channel_normal_depth(
        RectangularChannel(1.0),
        discharge=10.0,
        friction_slope=0.0005,
        roughness=0.04,
        initial_upper_depth=0.05,
    )
    assert result.depth > 0.05


def test_zero_discharge_returns_dry_section() -> None:
    result = calculate_channel_normal_depth(RectangularChannel(2.0), 0.0, 0.0, 0.03)
    assert result.depth == result.area == result.velocity == 0.0
    assert result.convergence is None


@pytest.mark.parametrize(
    ("discharge", "slope", "roughness"),
    [(-1.0, 0.001, 0.03), (1.0, -0.001, 0.03), (1.0, 0.001, 0.0)],
)
def test_invalid_uniform_flow_inputs_fail(discharge: float, slope: float, roughness: float) -> None:
    with pytest.raises(InvalidInputError):
        calculate_channel_normal_depth(RectangularChannel(2.0), discharge, slope, roughness)


def test_positive_flow_with_zero_friction_slope_fails() -> None:
    with pytest.raises(InvalidInputError, match="zero friction_slope"):
        calculate_channel_normal_depth(RectangularChannel(2.0), 1.0, 0.0, 0.03)
