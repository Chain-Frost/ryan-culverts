"""Tests for hydraulic-jump momentum and sequent-depth relations."""

import math

import pytest

from culvert_solver import (
    CircularGeometry,
    InvalidInputError,
    RectangularGeometry,
    calculate_critical_depth,
    calculate_sequent_depth,
    froude_number,
    hydrostatic_pressure_moment,
    momentum_function,
)


def test_rectangular_pressure_moment_is_analytical() -> None:
    """Simpson integration reproduces the exact rectangular pressure term."""
    geometry = RectangularGeometry(span=2.4, rise=1.5)
    depth = 0.8

    assert hydrostatic_pressure_moment(geometry, depth) == pytest.approx(
        geometry.span * depth**2 / 2.0,
        rel=1e-14,
    )


def test_rectangular_sequent_depth_matches_closed_form() -> None:
    """The general momentum root matches the rectangular jump equation."""
    geometry = RectangularGeometry(span=2.0, rise=2.0)
    discharge = 2.0
    y1 = 0.25
    fr1 = froude_number(
        discharge,
        geometry.area(y1),
        geometry.top_width(y1),
    )
    expected = 0.5 * y1 * (math.sqrt(1.0 + 8.0 * fr1**2) - 1.0)

    assert calculate_sequent_depth(geometry, discharge, y1) == pytest.approx(
        expected,
        abs=1e-7,
    )


def test_circular_sequent_depth_has_equal_momentum() -> None:
    """Circular conjugate sections conserve the implemented momentum function."""
    geometry = CircularGeometry(diameter=1.2)
    discharge = 1.0
    y1 = 0.414

    y2 = calculate_sequent_depth(geometry, discharge, y1)

    assert y2 is not None
    assert y2 > calculate_critical_depth(geometry, discharge).depth
    assert momentum_function(geometry, discharge, y2) == pytest.approx(
        momentum_function(geometry, discharge, y1),
        rel=1e-7,
    )


def test_sequent_depth_rejects_non_supercritical_input() -> None:
    """A depth on the subcritical branch cannot be supplied as the jump approach."""
    geometry = CircularGeometry(diameter=1.2)
    critical = calculate_critical_depth(geometry, 1.0).depth

    with pytest.raises(InvalidInputError, match="below critical depth"):
        calculate_sequent_depth(geometry, 1.0, critical)
