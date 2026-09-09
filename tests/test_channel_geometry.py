"""Geometry contracts for prismatic open-channel sections."""

import math
from collections.abc import Callable

import pytest

from culvert_solver import InvalidInputError, RectangularChannel, TrapezoidalChannel


def test_rectangular_and_asymmetric_trapezoidal_geometry() -> None:
    rectangle = RectangularChannel(bottom_width=5.0)
    assert rectangle.area(1.2) == pytest.approx(6.0)
    assert rectangle.wetted_perimeter(1.2) == pytest.approx(7.4)
    assert rectangle.top_width(0.0) == pytest.approx(5.0)

    trapezoid = TrapezoidalChannel(4.0, 3.0, 2.0)
    assert trapezoid.area(1.2) == pytest.approx(8.4)
    assert trapezoid.wetted_perimeter(1.2) == pytest.approx(
        4.0 + 1.2 * math.sqrt(10.0) + 1.2 * math.sqrt(5.0)
    )
    assert trapezoid.top_width(1.2) == pytest.approx(10.0)


def test_zero_bottom_width_represents_triangular_section() -> None:
    section = TrapezoidalChannel(0.0, 2.0, 2.0)
    assert section.area(1.5) == pytest.approx(4.5)
    assert section.top_width(1.5) == pytest.approx(6.0)


@pytest.mark.parametrize(
    "factory",
    [
        lambda: RectangularChannel(0.0),
        lambda: RectangularChannel(-1.0),
        lambda: TrapezoidalChannel(1.0, -1.0, 2.0),
        lambda: TrapezoidalChannel(1.0, 2.0, -1.0),
        lambda: TrapezoidalChannel(0.0, 0.0, 0.0),
    ],
)
def test_invalid_channel_geometry_fails(factory: Callable[[], object]) -> None:
    with pytest.raises(InvalidInputError):
        factory()


def test_negative_depth_fails() -> None:
    with pytest.raises(InvalidInputError, match="depth must be nonnegative"):
        RectangularChannel(2.0).area(-0.1)
