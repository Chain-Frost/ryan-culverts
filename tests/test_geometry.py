"""Analytical and boundary contract tests for hydraulic cross-section geometries."""

import math
from dataclasses import FrozenInstanceError

import pytest

from culvert_solver import (
    CircularGeometry,
    CrossSectionGeometry,
    InvalidInputError,
    RectangularGeometry,
)

# --- Circular Geometry Tests ---


def test_circular_creation_and_immutability() -> None:
    c = CircularGeometry(diameter=1.2)
    assert isinstance(c, CrossSectionGeometry)
    assert c.diameter == 1.2
    assert c.span == 1.2
    assert c.rise == 1.2
    assert c.area_full == pytest.approx(math.pi * 1.2**2 / 4.0)
    assert c.wetted_perimeter_full == pytest.approx(math.pi * 1.2)
    assert c.hydraulic_radius_full == pytest.approx(1.2 / 4.0)

    with pytest.raises(FrozenInstanceError):
        field = "diameter"
        setattr(c, field, 1.5)


def test_circular_from_mm() -> None:
    c = CircularGeometry.from_mm(1200)
    assert c.diameter == pytest.approx(1.2)


@pytest.mark.parametrize("val", [0, -1.0, math.nan, math.inf, -math.inf, True])
def test_circular_invalid_diameter(val: float) -> None:
    with pytest.raises(InvalidInputError):
        CircularGeometry(diameter=val)


def test_circular_zero_depth() -> None:
    c = CircularGeometry(diameter=1.0)
    assert c.area(0.0) == 0.0
    assert c.wetted_perimeter(0.0) == 0.0
    assert c.top_width(0.0) == 0.0
    assert c.hydraulic_radius(0.0) == 0.0
    assert not c.is_full(0.0)
    with pytest.raises(InvalidInputError, match="zero depth"):
        c.hydraulic_depth(0.0)


@pytest.mark.parametrize("y", [-0.01, -1.0, math.nan, math.inf])
def test_circular_invalid_depth(y: float) -> None:
    c = CircularGeometry(diameter=1.0)
    with pytest.raises(InvalidInputError):
        c.area(y)
    with pytest.raises(InvalidInputError):
        c.wetted_perimeter(y)
    with pytest.raises(InvalidInputError):
        c.top_width(y)
    with pytest.raises(InvalidInputError):
        c.hydraulic_radius(y)
    with pytest.raises(InvalidInputError):
        c.hydraulic_depth(y)
    with pytest.raises(InvalidInputError):
        c.is_full(y)


def test_circular_half_depth() -> None:
    d = 2.0
    c = CircularGeometry(diameter=d)
    y = d / 2.0  # 1.0 m

    assert c.area(y) == pytest.approx(math.pi * d**2 / 8.0)
    assert c.wetted_perimeter(y) == pytest.approx(math.pi * d / 2.0)
    assert c.top_width(y) == pytest.approx(d)
    assert c.hydraulic_radius(y) == pytest.approx(d / 4.0)
    assert c.hydraulic_depth(y) == pytest.approx(math.pi * d / 8.0)
    assert not c.is_full(y)


def test_circular_quarter_and_three_quarter_symmetry() -> None:
    d = 1.0
    c = CircularGeometry(diameter=d)
    y1 = 0.25 * d
    y2 = 0.75 * d

    # Quarter depth analytical theta = 2*acos(0.5) = 2*pi/3
    theta1 = 2.0 * math.pi / 3.0
    expected_area1 = (d**2 / 8.0) * (theta1 - math.sin(theta1))
    assert c.area(y1) == pytest.approx(expected_area1)
    assert c.wetted_perimeter(y1) == pytest.approx(d * theta1 / 2.0)
    assert c.top_width(y1) == pytest.approx(2.0 * math.sqrt(y1 * (d - y1)))

    # Three-quarter depth symmetry
    assert c.area(y1) + c.area(y2) == pytest.approx(c.area_full)
    assert c.wetted_perimeter(y1) + c.wetted_perimeter(y2) == pytest.approx(c.wetted_perimeter_full)
    assert c.top_width(y1) == pytest.approx(c.top_width(y2))


@pytest.mark.parametrize("depth_factor", [1.0, 1.2, 2.5])
def test_circular_full_and_surcharged(depth_factor: float) -> None:
    d = 1.5
    c = CircularGeometry(diameter=d)
    y = depth_factor * d

    assert c.is_full(y)
    assert c.area(y) == pytest.approx(c.area_full)
    assert c.wetted_perimeter(y) == pytest.approx(c.wetted_perimeter_full)
    assert c.top_width(y) == 0.0
    assert c.hydraulic_radius(y) == pytest.approx(d / 4.0)
    with pytest.raises(InvalidInputError, match="crown"):
        c.hydraulic_depth(y)


# --- Rectangular Box Geometry Tests ---


def test_rectangular_creation_and_immutability() -> None:
    box = RectangularGeometry(span=2.4, rise=1.2)
    assert isinstance(box, CrossSectionGeometry)
    assert box.span == 2.4
    assert box.rise == 1.2
    assert box.area_full == pytest.approx(2.4 * 1.2)
    assert box.wetted_perimeter_full == pytest.approx(2.0 * (2.4 + 1.2))
    assert box.hydraulic_radius_full == pytest.approx((2.4 * 1.2) / (2.0 * (2.4 + 1.2)))
    assert "span=2.4" in repr(box)
    assert box == RectangularGeometry(span=2.4, rise=1.2)
    assert box != RectangularGeometry(span=2.0, rise=1.2)
    assert box != "not-a-geometry"

    with pytest.raises(AttributeError):
        field = "span"
        setattr(box, field, 3.0)


def test_rectangular_from_mm() -> None:
    box = RectangularGeometry.from_mm(span_mm=2400, rise_mm=1200)
    assert box.span == pytest.approx(2.4)
    assert box.rise == pytest.approx(1.2)


@pytest.mark.parametrize("s,r", [(0, 1), (-1, 1), (1, 0), (1, -1), (math.nan, 1), (1, math.inf)])
def test_rectangular_invalid_dimensions(s: float, r: float) -> None:
    with pytest.raises(InvalidInputError):
        RectangularGeometry(span=s, rise=r)


def test_rectangular_zero_depth() -> None:
    box = RectangularGeometry(span=2.0, rise=1.0)
    assert box.area(0.0) == 0.0
    assert box.wetted_perimeter(0.0) == 0.0
    assert box.top_width(0.0) == 0.0
    assert box.hydraulic_radius(0.0) == 0.0
    assert not box.is_full(0.0)
    with pytest.raises(InvalidInputError, match="zero depth"):
        box.hydraulic_depth(0.0)


@pytest.mark.parametrize("y", [-0.01, -2.0, math.nan, math.inf])
def test_rectangular_invalid_depth(y: float) -> None:
    box = RectangularGeometry(span=2.0, rise=1.0)
    with pytest.raises(InvalidInputError):
        box.area(y)
    with pytest.raises(InvalidInputError):
        box.wetted_perimeter(y)
    with pytest.raises(InvalidInputError):
        box.top_width(y)
    with pytest.raises(InvalidInputError):
        box.hydraulic_radius(y)
    with pytest.raises(InvalidInputError):
        box.hydraulic_depth(y)
    with pytest.raises(InvalidInputError):
        box.is_full(y)


def test_rectangular_partial_depth() -> None:
    box = RectangularGeometry(span=2.5, rise=1.5)
    y = 0.6

    assert not box.is_full(y)
    assert box.area(y) == pytest.approx(2.5 * 0.6)
    assert box.wetted_perimeter(y) == pytest.approx(2.5 + 2.0 * 0.6)
    assert box.top_width(y) == pytest.approx(2.5)
    assert box.hydraulic_radius(y) == pytest.approx((2.5 * 0.6) / (2.5 + 1.2))
    assert box.hydraulic_depth(y) == pytest.approx(0.6)


@pytest.mark.parametrize("depth_factor", [1.0, 1.1, 3.0])
def test_rectangular_full_and_surcharged(depth_factor: float) -> None:
    box = RectangularGeometry(span=2.0, rise=1.0)
    y = depth_factor * 1.0

    assert box.is_full(y)
    assert box.area(y) == pytest.approx(box.area_full)
    assert box.wetted_perimeter(y) == pytest.approx(box.wetted_perimeter_full)
    assert box.top_width(y) == 0.0
    assert box.hydraulic_radius(y) == pytest.approx(box.hydraulic_radius_full)
    with pytest.raises(InvalidInputError, match="crown"):
        box.hydraulic_depth(y)
