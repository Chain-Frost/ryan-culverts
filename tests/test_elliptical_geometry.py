"""Analytical and solver-compatibility tests for elliptical culvert geometry."""

import math

import pytest

import culvert_solver.hydraulics.normal as normal_depth_module
from culvert_solver import (
    GRAVITATIONAL_ACCELERATION,
    CrossSectionGeometry,
    HorizontalEllipseGeometry,
    InvalidInputError,
    VerticalEllipseGeometry,
    calculate_critical_depth,
    calculate_normal_depth,
)


@pytest.mark.parametrize(
    ("geometry", "expected_quarter_perimeter"),
    [
        (HorizontalEllipseGeometry(span=2.4, rise=1.2), 2.2041439063591807),
        (VerticalEllipseGeometry(span=1.2, rise=2.4), 1.6919134922465608),
    ],
)
def test_ellipse_geometry_identities(
    geometry: HorizontalEllipseGeometry | VerticalEllipseGeometry,
    expected_quarter_perimeter: float,
) -> None:
    assert isinstance(geometry, CrossSectionGeometry)
    assert geometry.area_full == pytest.approx(math.pi * 2.4 * 1.2 / 4.0)
    assert geometry.wetted_perimeter_full == pytest.approx(5.813068932328606, abs=1e-10)

    quarter = 0.25 * geometry.rise
    half = 0.5 * geometry.rise
    three_quarters = 0.75 * geometry.rise

    assert geometry.area(quarter) == pytest.approx(0.44221309149915243, abs=1e-12)
    assert geometry.wetted_perimeter(quarter) == pytest.approx(
        expected_quarter_perimeter,
        abs=2e-10,
    )
    assert geometry.area(half) == pytest.approx(0.5 * geometry.area_full)
    assert geometry.wetted_perimeter(half) == pytest.approx(0.5 * geometry.wetted_perimeter_full)
    assert geometry.top_width(half) == pytest.approx(geometry.span)
    assert geometry.area(quarter) + geometry.area(three_quarters) == pytest.approx(geometry.area_full)
    assert geometry.wetted_perimeter(quarter) + geometry.wetted_perimeter(three_quarters) == pytest.approx(
        geometry.wetted_perimeter_full, abs=4e-10
    )
    assert geometry.top_width(quarter) == pytest.approx(geometry.top_width(three_quarters))


def test_ellipse_from_mm_and_orientation_contracts() -> None:
    horizontal = HorizontalEllipseGeometry.from_mm(span_mm=2400, rise_mm=1200)
    vertical = VerticalEllipseGeometry.from_mm(span_mm=1200, rise_mm=2400)

    assert horizontal == HorizontalEllipseGeometry(span=2.4, rise=1.2)
    assert vertical == VerticalEllipseGeometry(span=1.2, rise=2.4)
    assert horizontal != vertical

    with pytest.raises(InvalidInputError, match="span > rise"):
        HorizontalEllipseGeometry(span=1.2, rise=1.2)
    with pytest.raises(InvalidInputError, match="rise > span"):
        VerticalEllipseGeometry(span=2.0, rise=1.0)


@pytest.mark.parametrize(
    ("span", "rise"),
    [
        (0.0, 1.0),
        (-1.0, 1.0),
        (2.0, 0.0),
        (2.0, -1.0),
        (math.nan, 1.0),
        (2.0, math.inf),
    ],
)
def test_ellipse_rejects_invalid_dimensions(span: float, rise: float) -> None:
    with pytest.raises(InvalidInputError):
        HorizontalEllipseGeometry(span=span, rise=rise)


@pytest.mark.parametrize(
    "geometry",
    [
        HorizontalEllipseGeometry(span=2.4, rise=1.2),
        VerticalEllipseGeometry(span=1.2, rise=2.4),
    ],
)
def test_ellipse_depth_boundaries(
    geometry: HorizontalEllipseGeometry | VerticalEllipseGeometry,
) -> None:
    assert geometry.area(0.0) == 0.0
    assert geometry.wetted_perimeter(0.0) == 0.0
    assert geometry.top_width(0.0) == 0.0
    assert geometry.area(2.0 * geometry.rise) == pytest.approx(geometry.area_full)
    assert geometry.wetted_perimeter(2.0 * geometry.rise) == pytest.approx(geometry.wetted_perimeter_full)
    assert geometry.top_width(2.0 * geometry.rise) == 0.0
    assert geometry.is_full(geometry.rise)
    with pytest.raises(InvalidInputError):
        geometry.area(-0.01)
    with pytest.raises(InvalidInputError, match="crown"):
        geometry.hydraulic_depth(geometry.rise)


@pytest.mark.parametrize(
    "geometry",
    [
        HorizontalEllipseGeometry(span=2.4, rise=1.2),
        VerticalEllipseGeometry(span=1.2, rise=2.4),
    ],
)
def test_ellipse_critical_depth_uses_common_geometry_contract(
    geometry: HorizontalEllipseGeometry | VerticalEllipseGeometry,
) -> None:
    result = calculate_critical_depth(geometry, discharge=1.0)

    assert 0.0 < result.depth < geometry.rise
    assert not result.is_submerged
    assert result.froude_number == pytest.approx(1.0, rel=1e-7)
    area = geometry.area(result.depth)
    top_width = geometry.top_width(result.depth)
    residual = GRAVITATIONAL_ACCELERATION * area**3 - top_width
    assert residual == pytest.approx(0.0, abs=2e-6)


@pytest.mark.parametrize(
    "geometry",
    [
        HorizontalEllipseGeometry(span=2.4, rise=1.2),
        VerticalEllipseGeometry(span=1.2, rise=2.4),
    ],
)
def test_ellipse_normal_depth_uses_rising_conveyance_branch(
    geometry: HorizontalEllipseGeometry | VerticalEllipseGeometry,
) -> None:
    target_depth = 0.90 * geometry.rise
    roughness = 0.013
    slope = 0.005
    area = geometry.area(target_depth)
    radius = geometry.hydraulic_radius(target_depth)
    discharge = area * radius ** (2.0 / 3.0) * math.sqrt(slope) / roughness

    result = calculate_normal_depth(
        geometry,
        discharge=discharge,
        slope=slope,
        roughness=roughness,
    )

    assert not result.is_full
    assert not result.capacity_exceeded
    assert result.depth == pytest.approx(target_depth, abs=2e-6)


def test_ellipse_normal_depth_peak_is_cached_by_dimensions() -> None:
    peak = normal_depth_module._ellipse_max_conveyance_depth_for_dimensions
    peak.cache_clear()
    geometry = HorizontalEllipseGeometry(span=2.4, rise=1.2)

    first_depth = normal_depth_module._ellipse_max_conveyance_depth(geometry)
    first_info = peak.cache_info()
    second_depth = normal_depth_module._ellipse_max_conveyance_depth(
        HorizontalEllipseGeometry(span=2.4, rise=1.2)
    )
    second_info = peak.cache_info()

    assert second_depth == first_depth
    assert first_info.misses == 1
    assert first_info.hits == 0
    assert second_info.misses == 1
    assert second_info.hits == 1
